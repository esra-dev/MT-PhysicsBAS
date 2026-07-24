#!/usr/bin/env python3
"""Registered Phase-4 protocol-v2 confirmatory analysis (frozen before data).

Frozen m=4 family (from the registered expectations in
docs/PHASE4_DEPENDENCY_LADDER.md §5, restated in the Phase-4 correction
registration):
  1. lab4      avg_redundant        (ql_true − ql_false; negative = KG better)
  2. lab4dual  avg_redundant
  3. lab4chain avg_redundant
  4. lab5      energy_compliance    (ql_true − ql_false; positive = KG better)

Estimands (frozen):
  - avg_redundant per (lab, arm, seed) = mean over that seed's benchmark rows
    of (WastedSteps + ActuatorCyclingCount), from benchmark_results_<mode>.csv
    (metric schema phase1-benchmark-v2; 16 scenarios x 5 runs = 80 rows).
  - energy_compliance per (lab5, arm, seed) = phase4_energy.replica_scalars on
    that seed's bench_step_log/benchmark_results (deterministic steady power
    from the final ActuatorState x run_config phase4.power_formula, against
    the per-scenario budgets), i.e. the fraction of rows that reach the goal
    within budget.
  - Statistics: exact two-sided paired sign-flip (n=20), exact sign test,
    paired rank-biserial, 10,000-draw bootstrap CI (fixed seeds), BH within
    the m=4 family. No p/q can be zero (floor 2/2^20).
  - Ladder-growth secondary (OUTSIDE the BH family, single ordered
    hypothesis): per-seed d(lab4chain) − d(lab4) under a two-sided exact
    sign-flip test, with d(lab4dual) − d(lab4) and d(lab4chain) − d(lab4dual)
    reported descriptively.
  - Duplicate cells across archive roots are fatal; a seed pair is never
    dropped.

Usage:
  python analysis/phase4_v2_registered_family.py --roots phase4_v2_corrected/run_A phase4_v2_corrected/run_B \
      --out phase4_v2_corrected/analysis/registered
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import phase4_energy
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps
    import phase4_energy


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SEEDS = tuple(range(1, 21))
BOOTSTRAP_ITERS = 10_000
BOOTSTRAP_BASE_SEED = 20260723

FAMILY = (
    ("lab4", "avg_redundant"),
    ("lab4dual", "avg_redundant"),
    ("lab4chain", "avg_redundant"),
    ("lab5", "energy_compliance"),
)
LADDER = ("lab4", "lab4dual", "lab4chain")

FIELDS = [
    "registered_cell", "metric", "n_paired", "seeds_paired",
    "mean_ql_true", "mean_ql_false", "mean_paired_difference",
    "median_paired_difference", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided", "p_sign_exact_two_sided", "paired_rank_biserial",
    "q_signflip_bh_m4", "bh_family_m",
]
LADDER_FIELDS = [
    "contrast", "role", "n_paired", "mean_difference_of_differences",
    "median_difference_of_differences", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided", "paired_rank_biserial",
]


def _cell_dir(roots: list[Path], seed: int, profile: str, mode: str) -> Path:
    matches = []
    for root in roots:
        candidate = root / "benchmark" / f"results_seed{seed}" / profile / mode
        if candidate.is_dir():
            matches.append(candidate)
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one cell dir for {profile}/{mode}/seed{seed}; "
            f"found {len(matches)}: {[str(m) for m in matches]}")
    return matches[0]


def _csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if row and not next(iter(row.values()), "").startswith("#")]


def _avg_redundant(cell: Path, mode: str) -> float:
    rows = _csv_rows(cell / f"benchmark_results_{mode}.csv")
    if not rows:
        raise SystemExit(f"{cell}: no benchmark rows")
    total = 0.0
    for row in rows:
        if row.get("MetricSchema") != "phase1-benchmark-v2":
            raise SystemExit(f"{cell}: non-v2 benchmark row")
        total += float(row["WastedSteps"]) + float(row["ActuatorCyclingCount"])
    return total / len(rows)


def _lab5_tools():
    cfg = phase4_energy.load_phase4_config(SOURCE_ROOT / "config" / "run_config.json")
    weights = phase4_energy.parse_power_formula(cfg["power_formula"])
    default_budget = cfg.get("energy_budget_default")
    budgets = phase4_energy.load_scenario_budgets(
        SOURCE_ROOT / "benchmark" / "scenarios_lab5.json", default_budget)
    return weights, budgets, default_budget


def _energy_compliance(cell: Path, mode: str, weights, budgets, default_budget) -> float:
    step = cell / f"bench_step_log_{mode}.csv"
    res = cell / f"benchmark_results_{mode}.csv"
    scalars = phase4_energy.replica_scalars(step, res if res.is_file() else None,
                                            weights, budgets, default_budget,
                                            has_budget=True)
    if scalars is None:
        raise SystemExit(f"{cell}: no step-log pairs for energy compliance")
    return float(scalars["energy_compliance"])


def _stats_row(name: str, metric: str, true_vals: list[float],
               false_vals: list[float], index: int) -> tuple[dict, float]:
    diffs = [a - b for a, b in zip(true_vals, false_vals)]
    rng = random.Random(BOOTSTRAP_BASE_SEED + index)
    boots = []
    for _ in range(BOOTSTRAP_ITERS):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    p = eps.paired_signflip_p(true_vals, false_vals)
    row = {
        "registered_cell": name,
        "metric": metric,
        "n_paired": len(diffs),
        "seeds_paired": ";".join(str(s) for s in SEEDS),
        "mean_ql_true": sum(true_vals) / len(true_vals),
        "mean_ql_false": sum(false_vals) / len(false_vals),
        "mean_paired_difference": sum(diffs) / len(diffs),
        "median_paired_difference": eps.median(diffs),
        "ci_lo_bootstrap": boots[int(0.025 * BOOTSTRAP_ITERS)],
        "ci_hi_bootstrap": boots[min(BOOTSTRAP_ITERS - 1, int(0.975 * BOOTSTRAP_ITERS))],
        "p_signflip_two_sided": p,
        "p_sign_exact_two_sided": eps.exact_sign_p(true_vals, false_vals),
        "paired_rank_biserial": eps.paired_rank_biserial(true_vals, false_vals),
        "bh_family_m": len(FAMILY),
    }
    return row, p


def run(roots: list[Path], out_dir: Path) -> None:
    weights, budgets, default_budget = _lab5_tools()
    per_seed_diffs: dict[str, list[float]] = {}
    rows: list[dict] = []
    p_values: list[float] = []
    for index, (profile, metric) in enumerate(FAMILY):
        true_vals, false_vals = [], []
        for seed in SEEDS:
            for mode, bucket in (("ql_true", true_vals), ("ql_false", false_vals)):
                cell = _cell_dir(roots, seed, profile, mode)
                if metric == "avg_redundant":
                    bucket.append(_avg_redundant(cell, mode))
                else:
                    bucket.append(_energy_compliance(cell, mode, weights,
                                                     budgets, default_budget))
        row, p = _stats_row(profile, metric, true_vals, false_vals, index)
        rows.append(row)
        p_values.append(p)
        per_seed_diffs[profile] = [a - b for a, b in zip(true_vals, false_vals)]
    for row, q in zip(rows, eps.bh_qvalues(p_values)):
        row["q_signflip_bh_m4"] = q

    ladder_rows: list[dict] = []
    contrasts = [
        (f"{LADDER[2]}_minus_{LADDER[0]}", "registered_ordered_secondary",
         LADDER[2], LADDER[0]),
        (f"{LADDER[1]}_minus_{LADDER[0]}", "descriptive", LADDER[1], LADDER[0]),
        (f"{LADDER[2]}_minus_{LADDER[1]}", "descriptive", LADDER[2], LADDER[1]),
    ]
    for offset, (label, role, hi, lo) in enumerate(contrasts):
        dd = [a - b for a, b in zip(per_seed_diffs[hi], per_seed_diffs[lo])]
        rng = random.Random(BOOTSTRAP_BASE_SEED + 100 + offset)
        boots = []
        for _ in range(BOOTSTRAP_ITERS):
            sample = [dd[rng.randrange(len(dd))] for _ in dd]
            boots.append(sum(sample) / len(sample))
        boots.sort()
        ladder_rows.append({
            "contrast": label,
            "role": role,
            "n_paired": len(dd),
            "mean_difference_of_differences": sum(dd) / len(dd),
            "median_difference_of_differences": eps.median(dd),
            "ci_lo_bootstrap": boots[int(0.025 * BOOTSTRAP_ITERS)],
            "ci_hi_bootstrap": boots[min(BOOTSTRAP_ITERS - 1, int(0.975 * BOOTSTRAP_ITERS))],
            "p_signflip_two_sided": eps.paired_signflip_p(
                per_seed_diffs[hi], per_seed_diffs[lo]),
            "paired_rank_biserial": eps.paired_rank_biserial(
                per_seed_diffs[hi], per_seed_diffs[lo]),
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, fieldnames, table in (
            ("phase4_v2_registered_family.csv", FIELDS, rows),
            ("phase4_v2_ladder_trend.csv", LADDER_FIELDS, ladder_rows)):
        with (out_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(table)
    print(f"Wrote {len(rows)} family rows and {len(ladder_rows)} ladder rows to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.roots, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
