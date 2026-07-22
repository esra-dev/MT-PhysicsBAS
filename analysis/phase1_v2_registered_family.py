#!/usr/bin/env python3
"""Rebuild the registered Phase-1 protocol-v2 m=5 family from committed raw data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from analysis import sweep_report as sr
except ImportError:  # direct `python analysis/phase1_v2_registered_family.py`
    import sweep_report as sr  # type: ignore


EXPECTED_SEEDS = list(range(1, 21))


def _ordered_seed_roots(root: Path) -> list[tuple[int, Path]]:
    """Return the declared seed set in numeric order, independent of path sorting."""
    seeds = sorted(sr.find_seed_roots(root / "benchmark"), key=lambda item: item[0])
    actual = [seed for seed, _ in seeds]
    if actual != EXPECTED_SEEDS:
        raise ValueError(f"Expected seeds 1..20 under {root}, got {actual}")
    return seeds


def _decomposition(c_mean: float, r_mean: float) -> dict:
    """Apply the frozen one-third/two-thirds rule without hiding sign conflicts."""
    if c_mean == 0:
        return {
            "redundancy_share": None,
            "category": "undefined_arm_c_zero",
        }
    proportion = r_mean / c_mean
    if c_mean * r_mean < 0:
        category = "opposite_signs_not_reproduction"
    elif proportion < 1 / 3:
        category = "less_than_one_third"
    elif proportion <= 2 / 3:
        category = "between_one_third_and_two_thirds"
    else:
        category = "more_than_two_thirds"
    return {
        "redundancy_share": proportion,
        "category": category,
    }


def _speed(root: Path) -> tuple[dict, dict]:
    seeds = _ordered_seed_roots(root)
    return (
        sr._collect_learning_speed_by_cell(seeds, True, 100, 0.5, "phase1-v2"),
        sr._collect_learning_speed_by_cell(seeds, False, 100, 0.5, "phase1-v2"),
    )


def _effect(on: dict, off: dict, profile: str, metric: str) -> dict[int, float]:
    values: dict[int, float] = {}
    for seed in EXPECTED_SEEDS:
        if seed not in on.get(profile, {}) or seed not in off.get(profile, {}):
            raise ValueError(f"Missing {profile}/{metric}/seed{seed}")
        if metric == "mean_first_goal_presentations":
            if on[profile][seed].get("_first_goal_scenario_ids") != \
                    off[profile][seed].get("_first_goal_scenario_ids"):
                raise ValueError(f"First-goal scenarios differ for {profile}/seed{seed}")
        values[seed] = float(on[profile][seed][metric]) - float(off[profile][seed][metric])
    return values


def _cycling(root: Path) -> dict[int, float]:
    seeds = _ordered_seed_roots(root)
    values = sr._collect_per_seed_values(seeds)["avg_cycling"]
    on = values[("lab3", "ql_true")]
    off = values[("lab3", "ql_false")]
    return {seed: float(on[seed]) - float(off[seed]) for seed in EXPECTED_SEEDS}


def _row(name: str, metric: str, diffs: dict[int, float], iters: int) -> dict:
    values = [diffs[seed] for seed in EXPECTED_SEEDS]
    zeros = [0.0] * len(values)
    mean, lo, hi, *_ = sr._paired_bootstrap_diff(values, zeros, iters=iters)
    return {
        "registered_test": name,
        "metric": metric,
        "n_paired": len(values),
        "seeds_paired": ";".join(map(str, EXPECTED_SEEDS)),
        "mean_paired_difference": mean,
        "median_paired_difference": sr._median(values),
        "ci_lo_bootstrap": lo,
        "ci_hi_bootstrap": hi,
        "p_signflip_two_sided": sr._paired_signflip_p(values, zeros),
        "p_sign_exact_two_sided": sr._exact_sign_test_p(values, zeros),
        "paired_rank_biserial": sr._paired_rank_biserial(values, zeros),
        "cliffs_delta_unpaired_descriptive": sr._cliffs_delta(values, zeros),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm-c-root", type=Path, required=True)
    parser.add_argument("--redundancy-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bootstrap-iters", type=int, default=10_000)
    args = parser.parse_args()

    c_on, c_off = _speed(args.arm_c_root)
    r_on, r_off = _speed(args.redundancy_root)
    c_lab2 = _effect(c_on, c_off, "lab2", "auc_goal")
    r_lab2 = _effect(r_on, r_off, "lab2", "auc_goal")
    effect_difference = {seed: c_lab2[seed] - r_lab2[seed] for seed in EXPECTED_SEEDS}
    c_lab3_fg = _effect(c_on, c_off, "lab3", "mean_first_goal_presentations")

    rows = [
        _row("1_arm_c_lab2_auc_goal", "auc_goal", c_lab2, args.bootstrap_iters),
        _row("2_redundancy_lab2_auc_goal", "auc_goal", r_lab2, args.bootstrap_iters),
        _row("3_arm_c_minus_redundancy_lab2", "auc_goal_treatment_effect_difference",
             effect_difference, args.bootstrap_iters),
        _row("4_arm_c_lab3_mean_first_goal_presentations",
             "mean_first_goal_presentations", c_lab3_fg, args.bootstrap_iters),
        _row("5_arm_c_lab3_avg_cycling", "avg_cycling", _cycling(args.arm_c_root),
             args.bootstrap_iters),
    ]
    q_values = sr._bh_qvalues([row["p_signflip_two_sided"] for row in rows])
    for row, q_value in zip(rows, q_values):
        row["q_signflip_bh_m5"] = q_value
        row["bh_family_m"] = 5

    c_mean = rows[0]["mean_paired_difference"]
    r_mean = rows[1]["mean_paired_difference"]
    decomposition = _decomposition(c_mean, r_mean)

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "phase1_v2_registered_family.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "phase1_v2_decomposition.json").write_text(
        json.dumps({
            "rule": "redundancy share of arm-C lab2 mean effect: <1/3 little; 1/3..2/3 partial; >2/3 most",
            "arm_c_mean_effect": c_mean,
            "redundancy_mean_effect": r_mean,
            **decomposition,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
