"""Exhaustive deterministic transition/reachability checker (Phase 1b, Stage 0).

Builds the COMPLETE reachable state graph of a deterministic, finite MDP-like
model for one scenario and emits a hashable certificate reporting:

  * solvability within the horizon;
  * shortest path length (first passage to goal);
  * every shortest action sequence, or an exact count plus canonical
    lexicographic representatives when enumeration exceeds the cap;
  * all reachable states and all reachable terminal (absorbing) states;
  * whether the intended mechanism (a set of required action tokens) appears
    in every successful shortest route;
  * any unintended equal-length or shorter shortcut relative to the declared
    intended route length / mechanism.

Registration cites the certificate hash. A failed or ambiguous certificate
blocks the campaign (see docs/please refer to the Phase-1b registration).

The model interface is deliberately tiny so per-profile bindings stay
declarative:

    model.initial_state()          -> hashable state
    model.actions(state)           -> ordered list of action names
    model.step(state, action)      -> hashable next state (deterministic)
    model.is_goal(state)           -> bool

States must be hashable and JSON-serialisable via ``state_to_json`` (default:
str()).
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, Hashable, List, Optional, Sequence, Set, Tuple

ENUMERATION_CAP = 1000  # exact count always reported; sequences listed only under cap
REPRESENTATIVE_COUNT = 10


@dataclass
class CheckerResult:
    solvable: bool
    shortest_path_length: Optional[int]
    shortest_sequence_count: int
    shortest_sequences: Optional[List[List[str]]]  # None when count > cap
    canonical_representatives: List[List[str]]
    reachable_state_count: int
    reachable_states: List[str]
    reachable_terminal_states: List[str]
    goal_states_reached: List[str]
    intended_mechanism: List[str]
    mechanism_in_every_shortest_route: Optional[bool]
    intended_shortest_length: Optional[int]
    shortcuts: List[dict] = field(default_factory=list)
    ambiguous: bool = False
    ambiguity_reason: Optional[str] = None


def _first_passage_layers(model, horizon: int):
    """BFS layering over non-goal states; goal entry is absorbing for counting.

    Returns (dist, parents) where dist maps state -> first-visit depth and
    parents maps (state, depth) -> list of (prev_state, action) pairs along
    shortest walks that have not touched the goal before ``depth``.
    """
    init = model.initial_state()
    dist: Dict[Hashable, int] = {init: 0}
    parents: Dict[Tuple[Hashable, int], List[Tuple[Hashable, str]]] = {}
    frontier = [init]
    depth = 0
    goal_depth: Optional[int] = None
    goal_states: Set[Hashable] = set()
    if model.is_goal(init):
        return dist, parents, 0, {init}
    while frontier and depth < horizon and goal_depth is None:
        nxt: List[Hashable] = []
        for s in frontier:
            for a in model.actions(s):
                t = model.step(s, a)
                if t not in dist:
                    dist[t] = depth + 1
                    nxt.append(t)
                if dist[t] == depth + 1:
                    parents.setdefault((t, depth + 1), []).append((s, a))
                    if model.is_goal(t):
                        goal_depth = depth + 1
                        goal_states.add(t)
        depth += 1
        frontier = nxt
    if goal_depth is not None:
        goal_states = {s for s in dist if dist[s] == goal_depth and model.is_goal(s)}
    return dist, parents, goal_depth, goal_states


def _full_reachability(model, horizon: int):
    """Complete reachable graph within horizon (goal NOT absorbing)."""
    init = model.initial_state()
    dist: Dict[Hashable, int] = {init: 0}
    q = deque([init])
    edges: Dict[Hashable, List[Tuple[str, Hashable]]] = {}
    while q:
        s = q.popleft()
        if dist[s] >= horizon:
            continue
        outs = []
        for a in model.actions(s):
            t = model.step(s, a)
            outs.append((a, t))
            if t not in dist:
                dist[t] = dist[s] + 1
                q.append(t)
        edges[s] = outs
    terminals = [s for s in dist if all(t == s for _, t in edges.get(s, [])) and edges.get(s)]
    return dist, edges, terminals


def _count_and_enumerate(model, parents, goal_states, goal_depth,
                         cap: int = ENUMERATION_CAP,
                         reps: int = REPRESENTATIVE_COUNT):
    """Exact count of shortest first-passage sequences; enumerate under cap.

    Counting walks backwards from goal states through the layered parent DAG:
    each (state, depth) node's sequence count is the sum over its parents at
    depth-1. The layered keying makes revisited states in cyclic graphs safe.
    """
    if goal_depth is None:
        return 0, [], []
    if goal_depth == 0:
        return 1, [[]], [[]]

    counts: Dict[Tuple[Hashable, int], int] = {}

    def count(node: Tuple[Hashable, int]) -> int:
        s, d = node
        if d == 0:
            return 1
        if node in counts:
            return counts[node]
        total = 0
        for (ps, _a) in parents.get(node, []):
            total += count((ps, d - 1))
        counts[node] = total
        return total

    total = sum(count((g, goal_depth)) for g in goal_states)

    sequences: List[List[str]] = []

    def walk(node: Tuple[Hashable, int], suffix: List[str]):
        s, d = node
        if d == 0:
            sequences.append(list(suffix))
            return
        for (ps, a) in sorted(parents.get(node, []), key=lambda pa: pa[1]):
            if len(sequences) >= max(cap, reps):
                return
            walk((ps, d - 1), [a] + suffix)

    for g in sorted(goal_states, key=str):
        walk((g, goal_depth), [])
        if len(sequences) >= max(cap, reps):
            break
    sequences.sort()
    if total <= cap:
        # under the cap the walk enumerated everything
        full = sequences[:total]
        return total, full, full[:reps]
    return total, None, sequences[:reps]


def check_scenario(model,
                   horizon: int,
                   intended_mechanism: Sequence[str] = (),
                   intended_shortest_length: Optional[int] = None,
                   state_to_json: Callable[[Hashable], str] = str) -> CheckerResult:
    dist, parents, goal_depth, goal_states = _first_passage_layers(model, horizon)
    full_dist, _edges, terminals = _full_reachability(model, horizon)

    count, seqs, reps = _count_and_enumerate(model, parents, goal_states, goal_depth)

    mechanism = list(intended_mechanism)
    mech_ok: Optional[bool] = None
    shortcuts: List[dict] = []
    ambiguous = False
    ambiguity_reason = None

    routes_for_mech = seqs if seqs is not None else reps
    if goal_depth is not None and mechanism:
        if seqs is None:
            ambiguous = True
            ambiguity_reason = (
                "shortest-sequence count %d exceeds enumeration cap %d; "
                "mechanism coverage verified only on canonical representatives"
                % (count, ENUMERATION_CAP))
        mech_ok = all(all(tok in route for tok in mechanism) for route in routes_for_mech)
        for route in routes_for_mech:
            missing = [tok for tok in mechanism if tok not in route]
            if missing:
                shortcuts.append({
                    "kind": "equal_length_without_intended_mechanism",
                    "route": route,
                    "missing_mechanism_tokens": missing,
                })
    if goal_depth is not None and intended_shortest_length is not None:
        if goal_depth < intended_shortest_length:
            for route in (routes_for_mech or []):
                shortcuts.append({
                    "kind": "shorter_than_intended",
                    "intended_length": intended_shortest_length,
                    "observed_length": goal_depth,
                    "route": route,
                })
            if not routes_for_mech:
                shortcuts.append({
                    "kind": "shorter_than_intended",
                    "intended_length": intended_shortest_length,
                    "observed_length": goal_depth,
                    "route": None,
                })
        elif goal_depth > intended_shortest_length:
            ambiguous = True
            ambiguity_reason = (
                "observed shortest length %d exceeds intended %d; "
                "physics or scenario mismatch" % (goal_depth, intended_shortest_length))

    return CheckerResult(
        solvable=goal_depth is not None,
        shortest_path_length=goal_depth,
        shortest_sequence_count=count,
        shortest_sequences=seqs,
        canonical_representatives=reps,
        reachable_state_count=len(full_dist),
        reachable_states=sorted(state_to_json(s) for s in full_dist),
        reachable_terminal_states=sorted(state_to_json(s) for s in terminals),
        goal_states_reached=sorted(state_to_json(s) for s in goal_states),
        intended_mechanism=mechanism,
        mechanism_in_every_shortest_route=mech_ok,
        intended_shortest_length=intended_shortest_length,
        shortcuts=shortcuts,
        ambiguous=ambiguous,
        ambiguity_reason=ambiguity_reason,
    )


def result_to_certificate(result: CheckerResult, meta: dict) -> dict:
    """Wrap a CheckerResult in a deterministic, self-hashed certificate dict."""
    body = {"meta": meta, "result": {
        "solvable": result.solvable,
        "shortest_path_length": result.shortest_path_length,
        "shortest_sequence_count": result.shortest_sequence_count,
        "shortest_sequences": result.shortest_sequences,
        "canonical_representatives": result.canonical_representatives,
        "reachable_state_count": result.reachable_state_count,
        "reachable_states": result.reachable_states,
        "reachable_terminal_states": result.reachable_terminal_states,
        "goal_states_reached": result.goal_states_reached,
        "intended_mechanism": result.intended_mechanism,
        "mechanism_in_every_shortest_route": result.mechanism_in_every_shortest_route,
        "intended_shortest_length": result.intended_shortest_length,
        "shortcuts": result.shortcuts,
        "ambiguous": result.ambiguous,
        "ambiguity_reason": result.ambiguity_reason,
    }}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["certificate_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return body


def certificate_passes(cert: dict) -> Tuple[bool, str]:
    r = cert["result"]
    if not r["solvable"]:
        return False, "goal unreachable within horizon"
    if r["ambiguous"]:
        return False, "ambiguous: %s" % r["ambiguity_reason"]
    if r["shortcuts"]:
        return False, "unintended shortcut(s) present: %d" % len(r["shortcuts"])
    if r["intended_mechanism"] and not r["mechanism_in_every_shortest_route"]:
        return False, "intended mechanism absent from some shortest route"
    return True, "ok"
