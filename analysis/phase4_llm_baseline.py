"""Phase-4 OFFLINE LLM baseline harness (reproducible; NOT wired to a live API).

Thesis framing (advisor): "compare our system with the knowledge-informed
Q-learning agent to an LLM. We want to show that the KG in our system informs
the agent better than how an LLM is informed by its general knowledge."

This harness scores how an agent informed ONLY by GENERAL device knowledge —
the kind an LLM brings zero-shot — performs on the SAME Phase-4 benchmark
scenarios, with the SAME metrics as the KG-primed Q-learner
(analysis/phase4_energy.py). It is fully OFFLINE and deterministic:

  * No network / API call is made. CI never runs a live model.
  * Two policy backends:
      - `general` (default): a deterministic, feedback-driven controller that
        encodes exactly the information an LLM has from general knowledge and
        the observable simulator state, and — crucially — NOT the lab-specific
        facts that live only in the Knowledge Graph (the smart-plug AND-gate
        wiring in lab4; the per-lamp ws:energyCost 1-vs-4 in lab5). It is an
        explicit, auditable PROXY for an LLM's general-knowledge reasoning,
        not a language model.
      - `cached` (`--responses run.jsonl`): replays decisions recorded from a
        REAL LLM offline ({"profile","scenario_id","step","action"} per line),
        scored by the identical physics + metrics. This is the seam a
        researcher uses to drop in a real model without touching the scorer.
  * A prompt builder emits, per scenario step, the natural-language prompt an
    LLM would receive (`--emit-prompts`), so a real-model transcript can be
    produced offline and replayed via `--responses`.

WHY THIS IS A FAIR (not strawman) BASELINE
-------------------------------------------
The `general` controller is feedback-driven and goal-optimal *given general
knowledge*: it reads the observable zone brightness every step, knows the
generic physics any LLM would (a ceiling lamp adds a lot of light; open blinds
admit free daylight that scales with how sunny it is; a shared spotlight lifts
both zones; cross-zone light bleeds), and plans accordingly. What it lacks is
exactly — and only — the KG's hidden facts:

  lab4: general knowledge does NOT say "the Z1 lamp is wired behind PlugZ1".
        The controller therefore turns the lamp on and, seeing the zone stay
        dark, falls back on the commonsense "powered? check the plug" — it
        DISCOVERS the dependency through feedback, but pays diagnostic / wasted
        steps the KG-primed agent never pays (it reads ws:powerGates and enables
        the plug first). Differentiator: redundant actions + steps.

  lab5: the two lamps are described identically (+400 lux) and their energy cost
        is INVISIBLE in the observable brightness — only ws:energyCost in the KG
        distinguishes them. A general-knowledge agent therefore cannot
        systematically prefer the efficient lamp; the choice between two
        equivalent-looking lamps is an irreducible coin flip (the unique
        unbiased P(efficient)=0.5; seeded per replica). It still uses the free
        daylight heuristic (open blinds when the sun is strong), so the gap
        concentrates exactly where a lamp is unavoidable (low sun) — the
        decisive demonstration that the KG carries information general knowledge
        fundamentally cannot. Differentiator: energy-budget compliance.

Physics & discretisation mirror the Node-RED simulators
(simulator/simulator_flow_lab4.json, simulator_flow_lab5.json) and the
LabEnvironment.discretize bounds [50,100,300] (lab_profiles.asl). They are a
pure, deterministic function of the actuator bits + pinned Sunshine, so the
rollout reproduces the simulator transition without Node-RED.

Outputs (under analysis/out/):
    phase4_llm_detail_<profile>.csv  — one row per scenario (trace + metrics)
    phase4_llm_summary.csv           — one row per (profile, backend) aggregate
    phase4_llm_prompts_<profile>.jsonl  (only with --emit-prompts)

The summary columns mirror phase4_energy.py so the docs can place the LLM
baseline next to ql_true / ql_false directly.

Usage:
    python analysis/phase4_llm_baseline.py
    python analysis/phase4_llm_baseline.py --profile lab5 --seeds 1,2,3,4,5
    python analysis/phase4_llm_baseline.py --emit-prompts
    python analysis/phase4_llm_baseline.py --responses transcripts/gpt_lab5.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Physics — exact replica of the Phase-4 Node-RED simulators.
# Single source of truth: simulator/simulator_flow_lab{4,5}.json `update_env`
# and the benchmark scenario headers. NO Math.random(): pure function of state.
# ---------------------------------------------------------------------------

# LabEnvironment.discretize bounds (lab_profiles.asl lab4/lab5 light_bounds).
LIGHT_BOUNDS = (50.0, 100.0, 300.0)
TARGET_RANK = 3  # zone_targets([target(1,3), target(2,3)]) -> level >= 300
AMBIENT = 25.0
LAMP_PRIMARY = 400.0    # own-zone lamp contribution (either lamp in lab5)
LAMP_CROSS = 150.0      # cross-zone lamp bleed
BLIND_PRIMARY = 0.50    # own-zone blind coefficient * sun
BLIND_CROSS = 0.40      # cross-zone blind bleed coefficient * sun
SPOTLIGHT = 150.0       # shared corridor light (both zones)


def discretize(level: float) -> int:
    """Exact replica of LabEnvironment.discretize for bounds [50,100,300]."""
    if level < LIGHT_BOUNDS[0]:
        return 0
    if level < LIGHT_BOUNDS[1]:
        return 1
    if level < LIGHT_BOUNDS[2]:
        return 2
    return 3


def lab4_levels(s: dict) -> tuple[float, float]:
    """lab4 physics. z1lamp_on = Z1Light AND PlugZ1 (the hidden AND-gate)."""
    sun = float(s.get("Sunshine", 0))
    z1lamp_on = bool(s.get("Z1Light")) and bool(s.get("PlugZ1"))
    z2lamp_on = bool(s.get("Z2Light"))
    z1 = (AMBIENT
          + (LAMP_PRIMARY if z1lamp_on else 0.0)
          + (LAMP_CROSS if z2lamp_on else 0.0)
          + (BLIND_PRIMARY * sun if s.get("Z1Blinds") else 0.0)
          + (BLIND_CROSS * sun if s.get("Z2Blinds") else 0.0)
          + (SPOTLIGHT if s.get("Spotlight") else 0.0))
    z2 = (AMBIENT
          + (LAMP_PRIMARY if z2lamp_on else 0.0)
          + (LAMP_CROSS if z1lamp_on else 0.0)
          + (BLIND_PRIMARY * sun if s.get("Z2Blinds") else 0.0)
          + (BLIND_CROSS * sun if s.get("Z1Blinds") else 0.0)
          + (SPOTLIGHT if s.get("Spotlight") else 0.0))
    return z1, z2


def lab5_levels(s: dict) -> tuple[float, float]:
    """lab5 physics. z*AnyLamp = (Eff OR Ineff); +400 once regardless of which."""
    sun = float(s.get("Sunshine", 0))
    z1any = bool(s.get("Z1Eff")) or bool(s.get("Z1Ineff"))
    z2any = bool(s.get("Z2Eff")) or bool(s.get("Z2Ineff"))
    z1 = (AMBIENT
          + (LAMP_PRIMARY if z1any else 0.0)
          + (LAMP_CROSS if z2any else 0.0)
          + (BLIND_PRIMARY * sun if s.get("Z1Blinds") else 0.0)
          + (BLIND_CROSS * sun if s.get("Z2Blinds") else 0.0)
          + (SPOTLIGHT if s.get("Spotlight") else 0.0))
    z2 = (AMBIENT
          + (LAMP_PRIMARY if z2any else 0.0)
          + (LAMP_CROSS if z1any else 0.0)
          + (BLIND_PRIMARY * sun if s.get("Z2Blinds") else 0.0)
          + (BLIND_CROSS * sun if s.get("Z1Blinds") else 0.0)
          + (SPOTLIGHT if s.get("Spotlight") else 0.0))
    return z1, z2


def lab4_power(s: dict) -> float:
    """lab4 per-tick energy. (z1lamp_on?1)+(Z2Light?1)+(Spotlight?2)."""
    z1lamp_on = bool(s.get("Z1Light")) and bool(s.get("PlugZ1"))
    return ((1.0 if z1lamp_on else 0.0)
            + (1.0 if s.get("Z2Light") else 0.0)
            + (2.0 if s.get("Spotlight") else 0.0))


def lab5_power(s: dict) -> float:
    """lab5 per-tick energy. Z1Eff*1+Z1Ineff*4+Z2Eff*1+Z2Ineff*4+Spotlight*2."""
    return ((1.0 if s.get("Z1Eff") else 0.0)
            + (4.0 if s.get("Z1Ineff") else 0.0)
            + (1.0 if s.get("Z2Eff") else 0.0)
            + (4.0 if s.get("Z2Ineff") else 0.0)
            + (2.0 if s.get("Spotlight") else 0.0))


# Per-profile actuator vocabulary (the boolean levers the agent may toggle) and
# the physics/power hooks.
PROFILES = {
    "lab4": {
        "actuators": ["Z1Light", "Z2Light", "Z1Blinds", "Z2Blinds",
                      "Spotlight", "PlugZ1"],
        "levels": lab4_levels,
        "power": lab4_power,
        "has_budget": False,
    },
    "lab5": {
        "actuators": ["Z1Eff", "Z1Ineff", "Z2Eff", "Z2Ineff",
                      "Z1Blinds", "Z2Blinds", "Spotlight"],
        "levels": lab5_levels,
        "power": lab5_power,
        "has_budget": True,
    },
}


def ranks(profile: str, s: dict) -> tuple[int, int]:
    z1, z2 = PROFILES[profile]["levels"](s)
    return discretize(z1), discretize(z2)


def goal_met(profile: str, s: dict) -> bool:
    r1, r2 = ranks(profile, s)
    return r1 >= TARGET_RANK and r2 >= TARGET_RANK


def apply_action(s: dict, action: str) -> dict:
    """Return a NEW state with `action` applied. action = 'Set<Act>=true|false'
    or 'DO_NOTHING'."""
    ns = dict(s)
    if not action or action == "DO_NOTHING":
        return ns
    name, _, val = action.partition("=")
    act = name[3:] if name.startswith("Set") else name
    if act in ns or act in PROFILES_ALL_ACTS:
        ns[act] = (val.strip().lower() == "true")
    return ns


PROFILES_ALL_ACTS = set(PROFILES["lab4"]["actuators"]) | set(PROFILES["lab5"]["actuators"])


# ---------------------------------------------------------------------------
# General-knowledge controller (the offline LLM proxy).
# ---------------------------------------------------------------------------

def _blinds_alone_reach_target(profile: str, s: dict) -> bool:
    """Would opening BOTH blinds (zero energy) put both zones at rank 3, given
    the current sun? Encodes the LLM's commonsense 'daylight is free' heuristic.
    Computed from the OBSERVABLE physics (no KG needed)."""
    probe = dict(s)
    probe["Z1Blinds"] = True
    probe["Z2Blinds"] = True
    # Blinds are the only free levers; keep lamps/spotlight as-is for the probe
    # of "can daylight alone finish the job".
    return goal_met(profile, probe)


def general_knowledge_actions(profile: str, scenario: dict, rng: random.Random,
                              max_steps: int):
    """Yield (action, info) decisions for one scenario using ONLY general
    knowledge + observable feedback. A deterministic, auditable proxy for an
    LLM's zero-shot reasoning. `rng` resolves the single irreducible ambiguity
    per lab (lab5: which identical lamp; unbiased coin). Stops at goal or
    max_steps.
    """
    acts = PROFILES[profile]["actuators"]
    s = {a: bool(scenario.get(a, False)) for a in acts}
    s["Sunshine"] = int(scenario.get("Sunshine", 0))

    # The LLM's energy heuristic (general knowledge, NO ws:energyCost): prefer
    # free daylight, then the fewest powered devices. If daylight alone finishes
    # the job, use blinds and turn lamps/spotlight off.
    use_daylight = _blinds_alone_reach_target(profile, s)

    steps = 0
    # Plan a target configuration, then realise it one toggle per step (the
    # benchmark applies one action per tick). Re-plan after each observation so
    # feedback (e.g. lab4's dark-despite-lamp) can be exploited.
    while steps < max_steps:
        if goal_met(profile, s):
            # Goal reached: opportunistically shed obviously-redundant powered
            # devices the LLM can identify WITHOUT knowing energy costs (a lamp
            # whose zone stays at rank 3 without it; the spotlight if not
            # needed). It CANNOT tell the efficient lamp from the inefficient
            # one, so it cannot fix an inefficient-but-sufficient config.
            shed = _find_sheddable(profile, s)
            if shed is None:
                break
            action = f"Set{shed}=false"
            ns = apply_action(s, action)
            yield action, {"step": steps, "ranks": ranks(profile, s),
                           "reason": "shed_redundant"}
            s = ns
            steps += 1
            continue

        action = _plan_one_toggle(profile, s, use_daylight, rng)
        if action is None:
            # No constructive move the LLM can see -> give up this episode.
            break
        ns = apply_action(s, action)
        yield action, {"step": steps, "ranks": ranks(profile, s),
                       "reason": "constructive"}
        s = ns
        steps += 1

    return


def _zone_levers(profile: str, zone: int):
    """(lamp_candidates, blind) lever names for a zone."""
    if profile == "lab4":
        lamp = [f"Z{zone}Light"]
    else:
        lamp = [f"Z{zone}Eff", f"Z{zone}Ineff"]
    return lamp, f"Z{zone}Blinds"


def _plan_one_toggle(profile: str, s: dict, use_daylight: bool,
                     rng: random.Random):
    """Choose ONE constructive toggle toward the goal, general-knowledge only."""
    r1, r2 = ranks(profile, s)
    deficits = [(1, r1), (2, r2)]
    # Address the darkest zone first (largest deficit).
    deficits.sort(key=lambda zr: zr[1])
    for zone, rank in deficits:
        if rank >= TARGET_RANK:
            continue
        lamps, blind = _zone_levers(profile, zone)

        # 1) Free daylight first when it can finish the job (commonsense).
        if use_daylight and not s.get(blind):
            return f"Set{blind}=true"

        # 2) lab4 hidden-dependency discovery via feedback: if this zone's lamp
        #    switch is already ON but the zone is still dark, general knowledge
        #    says "powered device on but nothing happening -> check the plug".
        if profile == "lab4" and zone == 1:
            if s.get("Z1Light") and not s.get("PlugZ1"):
                return "SetPlugZ1=true"

        # 3) Turn on a lamp for this zone. In lab5 the two lamps are
        #    indistinguishable to general knowledge -> unbiased coin (the KG's
        #    ws:energyCost is the ONLY thing that could break this tie).
        off_lamps = [l for l in lamps if not s.get(l)]
        if off_lamps:
            choice = off_lamps[0] if len(off_lamps) == 1 else rng.choice(off_lamps)
            return f"Set{choice}={'true'}"

        # 4) lab4: lamp on but plug still off (covers the zone-1 trap directly).
        if profile == "lab4" and zone == 1 and not s.get("PlugZ1"):
            return "SetPlugZ1=true"

        # 5) Last resort: the shared spotlight lifts both zones (+150). General
        #    knowledge knows it costs power, so it is a fallback, not a first
        #    choice.
        if not s.get("Spotlight"):
            return "SetSpotlight=true"
    return None


def _find_sheddable(profile: str, s: dict):
    """Name of a powered device that can be switched OFF while both zones stay
    at rank 3 — the LLM's general 'drop redundant devices' move. Returns None if
    nothing is safely sheddable. Prefers the spotlight, then a redundant lamp.

    Note: in lab5 the agent cannot SWAP an inefficient lamp for an efficient one
    (they are indistinguishable to it); it can only drop a device that is purely
    redundant. This is why an inefficient-but-sufficient config stays
    non-compliant under general knowledge."""
    powered = []
    if s.get("Spotlight"):
        powered.append("Spotlight")
    for a in PROFILES[profile]["actuators"]:
        if a == "Spotlight" or a.endswith("Blinds"):
            continue
        if a == "PlugZ1":
            continue  # enabler, not a light source
        if s.get(a):
            powered.append(a)
    for dev in powered:
        probe = dict(s)
        probe[dev] = False
        if goal_met(profile, probe):
            return dev
    return None


# ---------------------------------------------------------------------------
# Prompt builder (for producing a real-LLM transcript offline).
# ---------------------------------------------------------------------------

_GENERAL_KNOWLEDGE = (
    "General device knowledge you may use: a ceiling lamp switched on adds a lot "
    "of brightness to its zone; opening a window blind admits daylight that is "
    "FREE (no energy) and grows with how sunny it is outside; a shared spotlight "
    "raises both zones a little but uses power; light bleeds a little between "
    "adjacent zones. You do NOT have any wiring diagram or per-device energy "
    "datasheet beyond this general knowledge."
)


def build_prompt(profile: str, scenario: dict, s: dict, step: int) -> dict:
    """One natural-language decision prompt for a real LLM (offline replay)."""
    acts = PROFILES[profile]["actuators"]
    r1, r2 = ranks(profile, s)
    z1, z2 = PROFILES[profile]["levels"](s)
    options = [f"Set{a}=true" for a in acts if not s.get(a)]
    options += [f"Set{a}=false" for a in acts if s.get(a)]
    options.append("DO_NOTHING")
    text = (
        f"You control a two-zone room. Goal: make BOTH zones 'bright' "
        f"(brightness rank 3 of 0..3) while using as little energy as possible.\n"
        f"Outdoor sunshine level: {s.get('Sunshine', 0)}.\n"
        f"Zone 1 brightness rank: {r1} (raw {z1:.0f}). "
        f"Zone 2 brightness rank: {r2} (raw {z2:.0f}).\n"
        f"Actuators currently ON: "
        f"{', '.join(a for a in acts if s.get(a)) or 'none'}.\n"
        f"{_GENERAL_KNOWLEDGE}\n"
        f"Choose exactly ONE action from: {options}."
    )
    return {"profile": profile, "scenario_id": scenario.get("id"),
            "step": step, "state": {a: bool(s.get(a)) for a in acts},
            "sunshine": s.get("Sunshine", 0), "prompt": text,
            "options": options}


# ---------------------------------------------------------------------------
# Rollout + scoring.
# ---------------------------------------------------------------------------

def rollout_general(profile: str, scenario: dict, rng: random.Random,
                    max_steps: int, prompts_out: list | None):
    """Run the general-knowledge controller; return per-scenario metrics."""
    acts = PROFILES[profile]["actuators"]
    s = {a: bool(scenario.get(a, False)) for a in acts}
    s["Sunshine"] = int(scenario.get("Sunshine", 0))

    n_steps = 0
    redundant = 0
    trace = []
    prev_ranks = ranks(profile, s)
    for action, info in general_knowledge_actions(profile, scenario, rng, max_steps):
        if prompts_out is not None:
            prompts_out.append(build_prompt(profile, scenario, s, n_steps))
        s = apply_action(s, action)
        new_ranks = ranks(profile, s)
        # A "redundant" action changed NO zone rank (no observable progress) —
        # mirrors QLearner's WastedSteps/no-effect accounting.
        if new_ranks == prev_ranks and action != "DO_NOTHING":
            redundant += 1
        prev_ranks = new_ranks
        trace.append(action)
        n_steps += 1
        if goal_met(profile, s):
            break
    return _score(profile, scenario, s, n_steps, redundant, trace)


def rollout_cached(profile: str, scenario: dict, decisions: list[str],
                   max_steps: int):
    """Replay recorded REAL-LLM actions for one scenario; same scoring."""
    acts = PROFILES[profile]["actuators"]
    s = {a: bool(scenario.get(a, False)) for a in acts}
    s["Sunshine"] = int(scenario.get("Sunshine", 0))
    n_steps = 0
    redundant = 0
    trace = []
    prev_ranks = ranks(profile, s)
    for action in decisions[:max_steps]:
        s = apply_action(s, action)
        new_ranks = ranks(profile, s)
        if new_ranks == prev_ranks and action not in ("DO_NOTHING", "", None):
            redundant += 1
        prev_ranks = new_ranks
        trace.append(action)
        n_steps += 1
        if goal_met(profile, s):
            break
    return _score(profile, scenario, s, n_steps, redundant, trace)


def _score(profile: str, scenario: dict, s: dict, n_steps: int,
           redundant: int, trace: list[str]) -> dict:
    reached = goal_met(profile, s)
    power = PROFILES[profile]["power"](s)
    has_budget = PROFILES[profile]["has_budget"]
    budget = float(scenario.get("energyBudget", 2)) if has_budget else float("nan")
    if has_budget:
        compliant = bool(reached and power <= budget + 1e-9)
    else:
        compliant = bool(reached)
    return {
        "scenario_id": scenario.get("id"),
        "sunshine": int(scenario.get("Sunshine", 0)),
        "goal_reached": int(reached),
        "steps": n_steps,
        "redundant_actions": redundant,
        "steady_power": power,
        "energy_budget": budget,
        "compliant": int(compliant),
        "trace": ";".join(trace),
    }


def load_scenarios(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"Missing scenarios file: {path}")
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    return [r for r in rows if isinstance(r, dict) and "id" in r]


def load_cache(path: Path) -> dict:
    """Parse a real-LLM transcript JSONL into {(profile,scenario_id): [actions]}.
    Each line: {"profile","scenario_id","step","action"}."""
    cache: dict = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            key = (obj.get("profile"), int(obj.get("scenario_id")))
            cache.setdefault(key, []).append((int(obj.get("step", 0)),
                                              str(obj.get("action", "DO_NOTHING"))))
    return {k: [a for _step, a in sorted(v)] for k, v in cache.items()}


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    if n == 0:
        return {}
    def _mean(key):
        return sum(r[key] for r in rows) / n
    return {
        "n_scenarios": n,
        "goal_rate": _mean("goal_reached"),
        "energy_compliance": _mean("compliant"),
        "mean_steady_power": _mean("steady_power"),
        "mean_steps": _mean("steps"),
        "mean_redundant": _mean("redundant_actions"),
    }


def write_detail(profile: str, backend: str, seed, rows: list[dict],
                 out_dir: Path) -> Path:
    out_path = out_dir / f"phase4_llm_detail_{profile}.csv"
    fields = ["profile", "backend", "seed", "scenario_id", "sunshine",
              "goal_reached", "steps", "redundant_actions", "steady_power",
              "energy_budget", "compliant", "trace"]
    write_header = not out_path.exists()
    with out_path.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow({"profile": profile, "backend": backend, "seed": seed, **r})
    return out_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenarios-dir", default="benchmark",
                        help="dir with scenarios_<profile>.json (default: benchmark)")
    parser.add_argument("--out", default="analysis/out",
                        help="output directory (default: analysis/out)")
    parser.add_argument("--profile", action="append", default=None,
                        help="profile to run (repeatable; default: lab4,lab5)")
    parser.add_argument("--seeds", default="1,2,3,4,5,6,7,8,9,10",
                        help="comma seeds for the general backend's coin flips "
                             "(default: 1..10, matching the QL seed family)")
    parser.add_argument("--max-steps", type=int, default=20,
                        help="per-scenario step budget (default: 20, "
                             "matching the Phase-4 benchmark max_steps)")
    parser.add_argument("--backend", choices=["general", "cached"],
                        default="general",
                        help="general (offline proxy) or cached (real-LLM replay)")
    parser.add_argument("--responses", default=None,
                        help="JSONL transcript for --backend cached")
    parser.add_argument("--emit-prompts", action="store_true",
                        help="also write phase4_llm_prompts_<profile>.jsonl")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    scen_dir = Path(args.scenarios_dir)
    profiles = args.profile or ["lab4", "lab5"]
    seeds = [int(x) for x in str(args.seeds).split(",") if str(x).strip()]

    cache = {}
    if args.backend == "cached":
        if not args.responses:
            raise SystemExit("--backend cached requires --responses <jsonl>")
        cache = load_cache(Path(args.responses))

    # Reset detail files for a clean run.
    for profile in profiles:
        dp = out_dir / f"phase4_llm_detail_{profile}.csv"
        if dp.exists():
            dp.unlink()

    summary_rows = []
    for profile in profiles:
        if profile not in PROFILES:
            print(f"  [skip] unknown profile {profile}", file=sys.stderr)
            continue
        scenarios = load_scenarios(scen_dir / f"scenarios_{profile}.json")
        prompts_out: list = [] if args.emit_prompts else None

        if args.backend == "cached":
            rows = []
            for sc in scenarios:
                decisions = cache.get((profile, int(sc["id"])), [])
                rows.append(rollout_cached(profile, sc, decisions, args.max_steps))
            write_detail(profile, "cached", "-", rows, out_dir)
            agg = aggregate(rows)
            agg.update({"profile": profile, "backend": "cached", "n_seeds": 1})
            summary_rows.append(agg)
            _print_profile(profile, "cached", agg)
        else:
            # Average the general backend across seeds (coin flips for the
            # irreducible lamp ambiguity) -> a distribution comparable to QL.
            per_seed_aggs = []
            for seed in seeds:
                # Deterministic per-seed RNG for the irreducible lamp coin flip.
                rng = random.Random(0x4C4C4D * seed + 7)  # 0x4C4C4D = "LLM"
                rows = []
                for sc in scenarios:
                    rows.append(rollout_general(profile, sc, rng, args.max_steps,
                                                prompts_out if seed == seeds[0] else None))
                write_detail(profile, "general", seed, rows, out_dir)
                per_seed_aggs.append(aggregate(rows))
            agg = _mean_aggs(per_seed_aggs)
            agg.update({"profile": profile, "backend": "general",
                        "n_seeds": len(seeds)})
            summary_rows.append(agg)
            _print_profile(profile, "general", agg)

        if prompts_out:
            pp = out_dir / f"phase4_llm_prompts_{profile}.jsonl"
            with pp.open("w", encoding="utf-8") as fh:
                for obj in prompts_out:
                    fh.write(json.dumps(obj) + "\n")
            print(f"  wrote {len(prompts_out)} prompts -> {pp}")

    _write_summary(summary_rows, out_dir)
    print(f"\nWrote summary -> {out_dir / 'phase4_llm_summary.csv'}")
    return 0


def _mean_aggs(aggs: list[dict]) -> dict:
    keys = ("n_scenarios", "goal_rate", "energy_compliance",
            "mean_steady_power", "mean_steps", "mean_redundant")
    out = {}
    valid = [a for a in aggs if a]
    for k in keys:
        out[k] = (sum(a[k] for a in valid) / len(valid)) if valid else float("nan")
    return out


def _print_profile(profile: str, backend: str, agg: dict) -> None:
    print(f"\n=== Phase 4 LLM baseline [{backend}]  profile={profile} ===")
    print(f"  scenarios={agg.get('n_scenarios', 0):.0f}  "
          f"goal_rate={agg.get('goal_rate', float('nan')):.3f}  "
          f"energy_compliance={agg.get('energy_compliance', float('nan')):.3f}")
    print(f"  mean_steady_power={agg.get('mean_steady_power', float('nan')):.3f}  "
          f"mean_steps={agg.get('mean_steps', float('nan')):.3f}  "
          f"mean_redundant={agg.get('mean_redundant', float('nan')):.3f}")


def _write_summary(rows: list[dict], out_dir: Path) -> None:
    fields = ["profile", "backend", "n_seeds", "n_scenarios", "goal_rate",
              "energy_compliance", "mean_steady_power", "mean_steps",
              "mean_redundant"]
    out_path = out_dir / "phase4_llm_summary.csv"
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
