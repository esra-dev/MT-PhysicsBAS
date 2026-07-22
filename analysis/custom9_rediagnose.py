#!/usr/bin/env python3
"""
custom9 re-diagnosis: is the headline negative driven by the night-dominated
benchmark mix?  (audit follow-up, 2026-06-08)

Tests the corrected hypothesis (the "training sun-coverage gap" was disproven):
the custom9 benchmark set is night-heavy (sun rank 0), and at night the
blind/sun stereotype lever has *no* leverage, so a blind-biased prior cannot
help and may waste exploration. If true, the informed-minus-naive goal-rate
gap should be ~0 (or negative) on rank-0 scenarios but *positive* on the
higher sun ranks where the lever actually exists -- and re-weighting the sun
ranks uniformly should move the overall gap in the favourable direction.

Uses ONLY the existing n=10 benchmark CSVs (no new compute). Dependency-free.

Run:
    python analysis/custom9_rediagnose.py
    python analysis/custom9_rediagnose.py --md docs/custom9_rediagnosis.md
"""

from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS = os.path.join(ROOT, "benchmark", "scenarios_custom9.json")
SWEEP_GLOB = os.path.join(
    ROOT, "tmp_sweep_n10_results", "benchmark", "results_seed*", "custom9"
)
SUN_BOUNDS = (50.0, 150.0, 500.0)  # custom9 sunshine_bounds
SUN_NAME = {0: "night/none", 1: "low", 2: "medium", 3: "bright"}


def sun_rank(lux: float) -> int:
    if lux < SUN_BOUNDS[0]:
        return 0
    if lux < SUN_BOUNDS[1]:
        return 1
    if lux < SUN_BOUNDS[2]:
        return 2
    return 3


def load_scenario_sun() -> Dict[int, int]:
    with io.open(SCENARIOS, "r", encoding="utf-8-sig") as fh:
        arr = json.load(fh)
    out: Dict[int, int] = {}
    for obj in arr:
        if "id" in obj and "Sunshine" in obj:
            out[int(obj["id"])] = sun_rank(float(obj["Sunshine"]))
    return out


def load_results(arm: str) -> List[Tuple[int, int]]:
    """Return (scenarioId, goalReached) over all seeds for one arm."""
    rows: List[Tuple[int, int]] = []
    pattern = os.path.join(SWEEP_GLOB, arm, f"benchmark_results_{arm}.csv")
    files = sorted(glob.glob(pattern))
    for f in files:
        with io.open(f, "r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((int(r["ScenarioId"]), int(r["GoalReached"])))
    return rows, files


def per_rank_rate(rows, scen_sun) -> Dict[int, Tuple[float, int]]:
    hits = defaultdict(int)
    tot = defaultdict(int)
    for sid, goal in rows:
        rk = scen_sun.get(sid)
        if rk is None:
            continue
        tot[rk] += 1
        hits[rk] += goal
    return {rk: (hits[rk] / tot[rk], tot[rk]) for rk in sorted(tot)}


def overall_rate(rows, scen_sun) -> Tuple[float, int]:
    hits = sum(g for s, g in rows if s in scen_sun)
    tot = sum(1 for s, g in rows if s in scen_sun)
    return (hits / tot if tot else 0.0, tot)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", help="write the report to this markdown file")
    args = ap.parse_args()

    out = io.open(args.md, "w", encoding="utf-8") if args.md else None
    if out is None:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    def emit(s=""):
        print(s, file=out if out else sys.stdout)

    scen_sun = load_scenario_sun()
    true_rows, true_files = load_results("ql_true")
    false_rows, false_files = load_results("ql_false")

    if not true_files or not false_files:
        emit("ERROR: no benchmark CSVs found under " + SWEEP_GLOB)
        return 2

    tr = per_rank_rate(true_rows, scen_sun)
    fr = per_rank_rate(false_rows, scen_sun)
    t_overall, t_n = overall_rate(true_rows, scen_sun)
    f_overall, f_n = overall_rate(false_rows, scen_sun)

    # benchmark scenario mix (how many distinct scenarios per rank)
    mix = defaultdict(int)
    for sid, rk in scen_sun.items():
        mix[rk] += 1
    mix_tot = sum(mix.values())

    emit("# custom9 re-diagnosis — night-dominated benchmark hypothesis")
    emit()
    emit(f"_Computed from {len(true_files)} ql_true + {len(false_files)} ql_false "
         f"benchmark CSVs (n=10 seeds × 5 runs × scenarios). No new compute._")
    emit()
    emit("## Benchmark scenario mix by sun rank")
    emit()
    emit("| Sun rank | scenarios | share |")
    emit("|---|---:|---:|")
    for rk in sorted(mix):
        emit(f"| {rk} ({SUN_NAME[rk]}) | {mix[rk]} | {mix[rk]/mix_tot:.0%} |")
    emit()
    emit("## Goal-rate per sun rank: informed (ql_true) vs naive (ql_false)")
    emit()
    emit("| Sun rank | n (true/false) | ql_true | ql_false | Δ (true−false) |")
    emit("|---|---|---:|---:|---:|")
    per_rank_delta = {}
    for rk in sorted(set(tr) | set(fr)):
        t_rate, t_cnt = tr.get(rk, (0.0, 0))
        f_rate, f_cnt = fr.get(rk, (0.0, 0))
        d = t_rate - f_rate
        per_rank_delta[rk] = d
        emit(f"| {rk} ({SUN_NAME[rk]}) | {t_cnt}/{f_cnt} | {t_rate:.3f} | "
             f"{f_rate:.3f} | {d:+.3f} |")
    emit()

    # observed overall gap vs uniform-reweighted gap
    obs_gap = t_overall - f_overall
    ranks = sorted(per_rank_delta)
    uniform_gap = sum(per_rank_delta[rk] for rk in ranks) / len(ranks)

    emit("## Observed vs sun-rank-uniform re-weighting")
    emit()
    emit(f"- **Observed overall goal-rate** (night-heavy mix): "
         f"ql_true={t_overall:.3f}, ql_false={f_overall:.3f}, "
         f"Δ={obs_gap:+.3f}  (N_true={t_n}, N_false={f_n})")
    emit(f"- **Sun-rank-uniform re-weighted Δ** (each rank weighted equally): "
         f"**{uniform_gap:+.3f}**")
    emit()
    n0 = per_rank_delta.get(0, 0.0)
    hi = [per_rank_delta[r] for r in ranks if r >= 2]
    hi_mean = sum(hi) / len(hi) if hi else 0.0
    emit("## Verdict")
    emit()
    emit(f"- Δ at **rank 0 (night)** = {n0:+.3f} — this is the regime where the "
         f"blind/sun lever has no leverage.")
    emit(f"- Mean Δ at **ranks ≥ 2 (medium+bright)** = {hi_mean:+.3f} — where the "
         f"lever exists.")
    if uniform_gap > obs_gap:
        emit(f"- Re-weighting sun ranks uniformly moves Δ from {obs_gap:+.3f} to "
             f"{uniform_gap:+.3f} (**favourable shift**), consistent with the "
             f"night-dominated-benchmark hypothesis.")
    else:
        emit(f"- Re-weighting does NOT improve Δ ({obs_gap:+.3f} → {uniform_gap:+.3f}); "
             f"the night-mix hypothesis is NOT supported — look elsewhere "
             f"(convergence, prior mis-fire at all ranks).")
    emit()
    emit("> Goal-rate here is a per-(scenario,run) terminal-success rate, not the "
         "AUC-of-learning-curve primary metric. It isolates *where in sun space* the "
         "prior helps or hurts at benchmark time; it does not replace the "
         "pre-registered AUC analysis.")

    if out:
        out.close()
        print(f"wrote {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
