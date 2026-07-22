#!/usr/bin/env python3
"""
Agent Decision Explainer  —  MT-Esra thesis demo
=================================================

Narrates, step by step, what a benchmark agent saw, what it did, and *why*,
using ONLY ground-truth data from a real benchmark step-log CSV
(``bench_step_log_<mode>.csv`` written by ``BenchmarkLogger``). No action labels
are guessed: the CSV already contains the human-readable ``ActionLabel`` the
agent executed, the per-zone target ranks, the outdoor ``SunshineRank``, the full
actuator state, and the before/after illuminance ranks.

Intended for the supervisor demo: run it on a stereotype run (``ql_true``) and an
uninformed run (``ql_false``) for the same scenario and show the difference in
behaviour, decision by decision.

Usage
-----
    # one arm, one scenario
    python analysis/demo_decision_explainer.py \
        --csv tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_true/bench_step_log_ql_true.csv \
        --scenario 7

    # side-by-side stereotype vs naive for the same scenario
    python analysis/demo_decision_explainer.py \
        --true  tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_true/bench_step_log_ql_true.csv \
        --false tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_false/bench_step_log_ql_false.csv \
        --scenario 7

    # let the tool pick the most illustrative scenario (true reaches goal, uses a blind)
    python analysis/demo_decision_explainer.py \
        --true  .../ql_true/bench_step_log_ql_true.csv \
        --false .../ql_false/bench_step_log_ql_false.csv --auto

    # write a markdown transcript for the slides
    python analysis/demo_decision_explainer.py --true ... --false ... --auto --md docs/demo_walkthrough_custom9.md

The script is intentionally dependency-free (standard library only).
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

RANK_NAME = {0: "dark", 1: "dim", 2: "medium", 3: "bright"}
SUN_NAME = {0: "night/none", 1: "low sun", 2: "medium sun", 3: "bright sun"}

# Energy cost per activation, mirrors simulator_flow_custom9.json "apply_action" node.
ENERGY_COST = {
    "Z1Light": 100, "Z2Light": 100, "Z3Light": 100, "Z4Light": 100,
    "Z1Blinds": 5, "Z2Blinds": 5, "Z3Blinds": 5, "Z4Blinds": 5,
    "Spotlight": 250, "SpotlightCD": 250, "CorridorLight": 80,
}


def rank(v: str) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def short_action(label: str) -> Tuple[str, Optional[bool]]:
    """'http://example.org/was#SetZ1Light=true' -> ('Z1Light', True)."""
    if not label:
        return ("DO_NOTHING", None)
    tail = label.rsplit("#", 1)[-1]
    name, _, val = tail.partition("=")
    name = name[3:] if name.startswith("Set") else name
    if val == "":
        return (name, None)
    return (name, val.strip().lower() == "true")


def explain_action(actuator: str, on: Optional[bool], sun: int) -> str:
    """Plain-language stereotype reasoning for the chosen action."""
    if actuator == "DO_NOTHING" or on is None:
        return "holds (no actuator change) — believes the target is met or no useful move remains."
    verb = "switches ON" if on else "switches OFF"
    if actuator.endswith("Light") and actuator.startswith("Z"):
        z = actuator[1]
        return (f"{verb} the Zone-{z} task light — a *Causes* stereotype "
                f"(lamp → light, always positive). Reliable but costs energy (100).")
    if actuator.endswith("Blinds"):
        z = actuator[1]
        if on:
            if sun >= 3:
                return (f"{verb} the Zone-{z} blind — *Mediates* stereotype: with **{SUN_NAME[sun]}** "
                        f"the blind harvests free daylight (energy ~5). This is exactly where the "
                        f"blind/sun stereotype is supposed to win.")
            if sun >= 1:
                return (f"{verb} the Zone-{z} blind — *Mediates* stereotype fires because the sun rank "
                        f"({sun}) ≥ ivMinRank (1), but at **{SUN_NAME[sun]}** the daylight gain is small "
                        f"and may not reach the target. (This is the custom9 mis-firing case.)")
            return (f"{verb} the Zone-{z} blind at **{SUN_NAME[sun]}** — the IV is starved, so the "
                    f"stereotype should discourage this. Opening it does ~nothing.")
        return f"{verb} the Zone-{z} blind (closing daylight)."
    if actuator == "CorridorLight":
        return f"{verb} the corridor light — a cheap shared *Causes* source (+150 lux to all zones)."
    if actuator in ("Spotlight", "SpotlightCD"):
        return (f"{verb} {actuator} — NOTE: this actuator is **disabled** in custom9, so the move is a "
                f"no-op. Choosing it is wasted effort (a symptom of a non-converged policy).")
    return f"{verb} {actuator}."


def load_rows(path: str) -> List[Dict[str, str]]:
    with io.open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def scenario_rows(rows: List[Dict[str, str]], scenario: int, run: Optional[int] = None
                  ) -> List[Dict[str, str]]:
    out = [r for r in rows if int(r["ScenarioId"]) == scenario]
    if run is None and out:
        run = min(int(r["RunId"]) for r in out)
    return [r for r in out if int(r["RunId"]) == run]


def goal_reached(r: Dict[str, str]) -> bool:
    return all(rank(r[f"Z{z}After"]) == rank(r[f"Z{z}Target"]) for z in range(1, 5))


def summarise(rows: List[Dict[str, str]]) -> Dict[str, object]:
    """Per-scenario summary: steps-to-goal, energy, final ranks, distinct actions."""
    if not rows:
        return {"reached": False, "steps": None, "energy": 0, "final": None, "n_steps": 0}
    energy = 0
    reached_step = None
    prev_state: Dict[str, bool] = {}
    for i, r in enumerate(rows):
        state = parse_actuator_state(r["ActuatorState"])
        for name, val in state.items():
            if prev_state.get(name) is False and val is True:
                energy += ENERGY_COST.get(name, 0)
        prev_state = state
        if reached_step is None and goal_reached(r):
            reached_step = i
    last = rows[-1]
    final = tuple(rank(last[f"Z{z}After"]) for z in range(1, 5))
    target = tuple(rank(last[f"Z{z}Target"]) for z in range(1, 5))
    return {
        "reached": reached_step is not None,
        "steps": reached_step,
        "energy": energy,
        "final": final,
        "target": target,
        "n_steps": len(rows),
    }


def parse_actuator_state(s: str) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for kv in s.split(";"):
        k, _, v = kv.partition("=")
        if k:
            out[k.strip()] = v.strip().lower() == "true"
    return out


def render_scenario(rows: List[Dict[str, str]], title: str, out) -> Dict[str, object]:
    if not rows:
        print(f"\n### {title}\n\n_(no rows for this scenario)_\n", file=out)
        return summarise(rows)
    first = rows[0]
    target = tuple(rank(first[f"Z{z}Target"]) for z in range(1, 5))
    sun = rank(first["SunshineRank"])
    print(f"\n### {title}\n", file=out)
    print(f"- **Scenario {first['ScenarioId']}**, outdoor light = **{SUN_NAME.get(sun, sun)}** "
          f"(rank {sun})", file=out)
    print(f"- **Goal**: Z1={RANK_NAME[target[0]]}({target[0]}), Z2={RANK_NAME[target[1]]}({target[1]}), "
          f"Z3={RANK_NAME[target[2]]}({target[2]}), Z4={RANK_NAME[target[3]]}({target[3]})", file=out)
    print(file=out)
    prev_state: Dict[str, bool] = {}
    last_label = None
    for i, r in enumerate(rows):
        actuator, on = short_action(r["ActionLabel"])
        before = tuple(rank(r[f"Z{z}Before"]) for z in range(1, 5))
        after = tuple(rank(r[f"Z{z}After"]) for z in range(1, 5))
        state = parse_actuator_state(r["ActuatorState"])
        sun_i = rank(r["SunshineRank"])
        # Collapse the bench agent's repeated "settling" rows (same action, no change).
        if r["ActionLabel"] == last_label and before == after:
            prev_state = state
            continue
        last_label = r["ActionLabel"]
        moved = "→".join(str(x) for x in after) if after != before else "no rank change"
        reached = " ✅ **all targets met**" if goal_reached(r) else ""
        flags = []
        if r.get("WasMasked", "0") not in ("0", "", "false"):
            flags.append("masked")
        if r.get("CrossZoneInterference", "0") not in ("0", "", "false"):
            flags.append("cross-zone-bleed")
        if r.get("StuckFired", "0") not in ("0", "", "false"):
            flags.append("anti-stuck")
        flag_s = f"  _[{', '.join(flags)}]_" if flags else ""
        print(f"- **t{i}** `{actuator}{'' if on is None else ('=ON' if on else '=OFF')}` "
              f"→ {explain_action(actuator, on, sun_i)}", file=out)
        print(f"    - ranks {before} → **{after}** ({moved}){reached}{flag_s}", file=out)
        prev_state = state
    s = summarise(rows)
    energy = s["energy"]
    if s["reached"]:
        print(f"\n  **Result:** reached goal at step {s['steps']}, energy spent ≈ {energy}.", file=out)
    else:
        print(f"\n  **Result:** did NOT reach goal in {s['n_steps']} steps "
              f"(final {s['final']} vs target {s['target']}), energy spent ≈ {energy}.", file=out)
    return s


def pick_auto(true_rows, false_rows) -> int:
    """Pick the scenario that best illustrates the thesis:
    ql_true reaches the goal (ideally using a blind) and ql_false does not."""
    scen_ids = sorted({int(r["ScenarioId"]) for r in true_rows})
    best = None
    for sid in scen_ids:
        tr = scenario_rows(true_rows, sid)
        fr = scenario_rows(false_rows, sid)
        ts, fs = summarise(tr), summarise(fr)
        used_blind = any("Blinds=true" in r["ActionLabel"] or
                         short_action(r["ActionLabel"])[0].endswith("Blinds")
                         for r in tr)
        score = 0
        if ts["reached"]:
            score += 4
        if not fs["reached"]:
            score += 2
        if used_blind:
            score += 2
        if ts["reached"] and fs["reached"] and ts["steps"] is not None and fs["steps"] is not None:
            score += 1 if ts["steps"] < fs["steps"] else 0
        if best is None or score > best[0]:
            best = (score, sid)
    return best[1] if best else (scen_ids[0] if scen_ids else 1)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="single step-log CSV")
    ap.add_argument("--true", dest="true_csv", help="ql_true step-log CSV")
    ap.add_argument("--false", dest="false_csv", help="ql_false step-log CSV")
    ap.add_argument("--scenario", type=int, help="scenario id to narrate")
    ap.add_argument("--auto", action="store_true", help="auto-pick the most illustrative scenario")
    ap.add_argument("--md", help="write a markdown transcript to this path (else stdout)")
    args = ap.parse_args(argv)

    # Force UTF-8 on the console so emoji/box characters print on Windows cp1252.
    if not args.md:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    out = io.StringIO() if args.md else sys.stdout

    print("# Agent Decision Walkthrough\n", file=out)
    print("_Generated by `analysis/demo_decision_explainer.py` from real benchmark step-logs._\n",
          file=out)

    if args.csv:
        rows = load_rows(args.csv)
        sid = args.scenario or sorted({int(r["ScenarioId"]) for r in rows})[0]
        render_scenario(scenario_rows(rows, sid), f"Run: {args.csv}", out)

    if args.true_csv and args.false_csv:
        tr_all = load_rows(args.true_csv)
        fr_all = load_rows(args.false_csv)
        sid = args.scenario or (pick_auto(tr_all, fr_all) if args.auto else
                                sorted({int(r["ScenarioId"]) for r in tr_all})[0])
        print(f"\n## Side-by-side on scenario {sid}\n", file=out)
        ts = render_scenario(scenario_rows(tr_all, sid),
                             "🟢 Stereotype-informed learner (`ql_true`)", out)
        fs = render_scenario(scenario_rows(fr_all, sid),
                             "⚪ Naive learner (`ql_false`)", out)
        print("\n## Verdict for this scenario\n", file=out)
        print(f"| | reached goal | step | energy |", file=out)
        print(f"|---|---|---|---|", file=out)
        print(f"| `ql_true` (stereotype) | {ts['reached']} | {ts['steps']} | {ts['energy']} |", file=out)
        print(f"| `ql_false` (naive) | {fs['reached']} | {fs['steps']} | {fs['energy']} |", file=out)

    if args.md:
        with io.open(args.md, "w", encoding="utf-8") as fh:
            fh.write(out.getvalue())
        print(f"wrote {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
