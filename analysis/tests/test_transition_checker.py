"""Unit tests for the generic exhaustive transition/reachability checker.

Covers the Stage-0 mandated cases: multiple equal shortest paths, unreachable
goals, cycles, and a planted unintended shortcut.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transition_checker import (  # noqa: E402
    check_scenario,
    certificate_passes,
    result_to_certificate,
)


class GraphModel:
    """Tiny explicit-graph model: edges[state] = [(action, next_state), ...]."""

    def __init__(self, init, edges, goals):
        self._init = init
        self._edges = edges
        self._goals = set(goals)

    def initial_state(self):
        return self._init

    def actions(self, state):
        return [a for a, _ in self._edges.get(state, [])]

    def step(self, state, action):
        for a, t in self._edges[state]:
            if a == action:
                return t
        raise KeyError(action)

    def is_goal(self, state):
        return state in self._goals


def test_multiple_equal_shortest_paths_all_enumerated():
    # A -> B -> D and A -> C -> D, both length 2.
    m = GraphModel("A", {
        "A": [("ab", "B"), ("ac", "C")],
        "B": [("bd", "D")],
        "C": [("cd", "D")],
    }, goals={"D"})
    r = check_scenario(m, horizon=10)
    assert r.solvable
    assert r.shortest_path_length == 2
    assert r.shortest_sequence_count == 2
    assert sorted(r.shortest_sequences) == [["ab", "bd"], ["ac", "cd"]]


def test_unreachable_goal_fails_certificate():
    m = GraphModel("A", {"A": [("loop", "A")]}, goals={"Z"})
    r = check_scenario(m, horizon=50)
    assert not r.solvable
    cert = result_to_certificate(r, {"scenario": "unreachable"})
    ok, reason = certificate_passes(cert)
    assert not ok and "unreachable" in reason


def test_cycle_does_not_break_counting():
    # A <-> B cycle plus A -> G. Shortest = 1, exactly one sequence.
    m = GraphModel("A", {
        "A": [("ab", "B"), ("ag", "G")],
        "B": [("ba", "A")],
        "G": [("stay", "G")],
    }, goals={"G"})
    r = check_scenario(m, horizon=20)
    assert r.solvable
    assert r.shortest_path_length == 1
    assert r.shortest_sequence_count == 1
    assert r.shortest_sequences == [["ag"]]
    # cycle states are all reachable
    assert r.reachable_state_count == 3


def test_planted_shortcut_detected_by_mechanism_check():
    # Intended route: chain on1 -> on2 -> goal (length 2, uses both).
    # Planted shortcut: a single "magic" action reaches goal in 1 step.
    m = GraphModel("s0", {
        "s0": [("on1", "s1"), ("magic", "G")],
        "s1": [("on2", "G")],
        "G": [("stay", "G")],
    }, goals={"G"})
    r = check_scenario(m, horizon=10,
                      intended_mechanism=["on1", "on2"],
                      intended_shortest_length=2)
    assert r.shortest_path_length == 1
    kinds = {s["kind"] for s in r.shortcuts}
    assert "shorter_than_intended" in kinds
    cert = result_to_certificate(r, {"scenario": "planted"})
    ok, _ = certificate_passes(cert)
    assert not ok


def test_equal_length_route_missing_mechanism_is_flagged():
    # Two length-2 routes; only one uses the intended mechanism.
    m = GraphModel("A", {
        "A": [("on1", "B"), ("other", "C")],
        "B": [("on2", "G")],
        "C": [("cheat", "G")],
    }, goals={"G"})
    r = check_scenario(m, horizon=10,
                      intended_mechanism=["on1", "on2"],
                      intended_shortest_length=2)
    assert r.shortest_sequence_count == 2
    assert r.mechanism_in_every_shortest_route is False
    kinds = {s["kind"] for s in r.shortcuts}
    assert "equal_length_without_intended_mechanism" in kinds


def test_goal_at_start_is_length_zero():
    m = GraphModel("G", {"G": [("stay", "G")]}, goals={"G"})
    r = check_scenario(m, horizon=5)
    assert r.solvable and r.shortest_path_length == 0
    assert r.shortest_sequence_count == 1 and r.shortest_sequences == [[]]


def test_certificate_hash_is_deterministic():
    m = GraphModel("A", {"A": [("ag", "G")], "G": [("stay", "G")]}, goals={"G"})
    r1 = check_scenario(m, horizon=5)
    r2 = check_scenario(m, horizon=5)
    c1 = result_to_certificate(r1, {"scenario": "x"})
    c2 = result_to_certificate(r2, {"scenario": "x"})
    assert c1["certificate_sha256"] == c2["certificate_sha256"]
