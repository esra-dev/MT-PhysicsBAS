#!/usr/bin/env python3
"""Rebuild the registered Phase-1 protocol-v2 KNOWLEDGE-LADDER family.

Registered in THESIS_STATE_REPORT.md Addendum 2026-11-10 (Brick-only control
arm). The ladder is

    A0 tabula rasa  ->  A1 redundancy-only  ->  A2 Brick-structure  ->  A3 full KG

where every arm's own treatment effect is its within-run paired
``ql_true - ql_false`` seed difference, and a RUNG INCREMENT is the paired
(by seed) difference of two arms' treatment effects.

Registered primary family (m = 2, Benjamini-Hochberg within the family):

    1. lab2 ``auc_goal``: (A3 effect) - (A2 effect)   "Elementary increment"
    2. lab3 ``auc_goal``: (A3 effect) - (A2 effect)

Everything else written here (A2's own effects on lab1/lab2/lab3, the
A2 - A1 increment, benchmark descriptives) is DESCRIPTIVE and carries no
threshold. Pre-committed interpretation per primary member, applied to the
95% paired bootstrap interval of the increment: ``elementary_adds`` when the
interval lies above zero, ``elementary_costs`` when it lies below zero, and
``null`` otherwise. No one-third / two-thirds share rule is registered for
this family because the comparator (A2) may legitimately carry the whole
A3 effect; the share ``brick_share = A2 / A3`` is reported for the text only.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from analysis import sweep_report as sr
    from analysis.phase1_v2_registered_family import (
        EXPECTED_SEEDS, _effect, _row, _speed,
    )
except ImportError:  # direct `python analysis/phase1_v2_knowledge_ladder.py`
    import sweep_report as sr  # type: ignore
    from phase1_v2_registered_family import (  # type: ignore
        EXPECTED_SEEDS, _effect, _row, _speed,
    )


LABS = ("lab1", "lab2", "lab3")
BENCH_METRICS = ("goal_rate", "avg_steps", "avg_policy_energy",
                 "avg_wasted", "avg_cycling", "avg_redundant")


def _increment(a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
    return {seed: a[seed] - b[seed] for seed in EXPECTED_SEEDS}


def _category(lo: float, hi: float) -> str:
    if lo > 0:
        return "elementary_adds"
    if hi < 0:
        return "elementary_costs"
    return "null"


def _bench_effect(root: Path, profile: str, metric: str) -> dict[int, float] | None:
    seeds = sorted(sr.find_seed_roots(root / "benchmark"), key=lambda item: item[0])
    values = sr._collect_per_seed_values(seeds).get(metric)
    if not values:
        return None
    on = values.get((profile, "ql_true"), {})
    off = values.get((profile, "ql_false"), {})
    if any(seed not in on or seed not in off for seed in EXPECTED_SEEDS):
        return None
    return {seed: float(on[seed]) - float(off[seed]) for seed in EXPECTED_SEEDS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm-c-root", type=Path, required=True,
                        help="phase1_v2_kg_only archive (A3)")
    parser.add_argument("--brick-root", type=Path, required=True,
                        help="phase1_v2_brick_only archive (A2)")
    parser.add_argument("--redundancy-root", type=Path,
                        help="phase1_v2_redundancy_only archive (A1); descriptive ladder only")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bootstrap-iters", type=int, default=10_000)
    args = parser.parse_args()

    c_on, c_off = _speed(args.arm_c_root)
    b_on, b_off = _speed(args.brick_root)

    # ── Registered primary family (m = 2) ────────────────────────────────
    primary = []
    increments: dict[str, dict[int, float]] = {}
    for idx, lab in enumerate(("lab2", "lab3"), start=1):
        c_eff = _effect(c_on, c_off, lab, "auc_goal")
        b_eff = _effect(b_on, b_off, lab, "auc_goal")
        increments[lab] = _increment(c_eff, b_eff)
        primary.append(_row(f"{idx}_arm_c_minus_brick_{lab}_auc_goal",
                            "auc_goal_treatment_effect_difference",
                            increments[lab], args.bootstrap_iters))
    q_values = sr._bh_qvalues([row["p_signflip_two_sided"] for row in primary])
    for row, q_value in zip(primary, q_values):
        row["q_signflip_bh_m2"] = q_value
        row["bh_family_m"] = 2
        row["registered_category"] = _category(row["ci_lo_bootstrap"], row["ci_hi_bootstrap"])

    # ── Descriptive ladder ───────────────────────────────────────────────
    descriptive = []
    r_on = r_off = None
    if args.redundancy_root is not None:
        r_on, r_off = _speed(args.redundancy_root)
    for lab in LABS:
        c_eff = _effect(c_on, c_off, lab, "auc_goal")
        b_eff = _effect(b_on, b_off, lab, "auc_goal")
        descriptive.append(_row(f"A3_full_kg_{lab}_auc_goal", "auc_goal", c_eff, args.bootstrap_iters))
        descriptive.append(_row(f"A2_brick_{lab}_auc_goal", "auc_goal", b_eff, args.bootstrap_iters))
        if r_on is not None and r_off is not None:
            r_eff = _effect(r_on, r_off, lab, "auc_goal")
            descriptive.append(_row(f"A1_redundancy_{lab}_auc_goal", "auc_goal", r_eff, args.bootstrap_iters))
            descriptive.append(_row(f"A2_minus_A1_{lab}_auc_goal",
                                    "auc_goal_treatment_effect_difference",
                                    _increment(b_eff, r_eff), args.bootstrap_iters))
        descriptive.append(_row(f"A2_brick_{lab}_mean_first_goal_presentations",
                                "mean_first_goal_presentations",
                                _effect(b_on, b_off, lab, "mean_first_goal_presentations"),
                                args.bootstrap_iters))
        for metric in BENCH_METRICS:
            b_bench = _bench_effect(args.brick_root, lab, metric)
            c_bench = _bench_effect(args.arm_c_root, lab, metric)
            if b_bench is not None:
                descriptive.append(_row(f"A2_brick_{lab}_bench_{metric}", metric,
                                        b_bench, args.bootstrap_iters))
            if b_bench is not None and c_bench is not None:
                descriptive.append(_row(f"A3_minus_A2_{lab}_bench_{metric}",
                                        f"{metric}_treatment_effect_difference",
                                        _increment(c_bench, b_bench), args.bootstrap_iters))
    for row in descriptive:
        row["registered_category"] = "descriptive"

    # ── Write ────────────────────────────────────────────────────────────
    args.out.mkdir(parents=True, exist_ok=True)
    fieldnames = list(primary[0].keys())
    with (args.out / "phase1_v2_knowledge_ladder_family.csv").open(
            "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(primary)
    desc_fields = list(descriptive[0].keys()) if descriptive else fieldnames
    with (args.out / "phase1_v2_knowledge_ladder_descriptives.csv").open(
            "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=desc_fields)
        writer.writeheader()
        writer.writerows(descriptive)

    shares = {}
    for lab in ("lab2", "lab3"):
        c_mean = next(r for r in descriptive if r["registered_test"] == f"A3_full_kg_{lab}_auc_goal")["mean_paired_difference"]
        b_mean = next(r for r in descriptive if r["registered_test"] == f"A2_brick_{lab}_auc_goal")["mean_paired_difference"]
        shares[lab] = {
            "arm_c_mean_effect": c_mean,
            "brick_mean_effect": b_mean,
            "brick_share_of_arm_c": (b_mean / c_mean) if c_mean != 0 else None,
            "elementary_increment_mean": c_mean - b_mean,
            "registered_category": next(
                r for r in primary if r["registered_test"].endswith(f"{lab}_auc_goal")
            )["registered_category"],
        }
    (args.out / "phase1_v2_knowledge_ladder.json").write_text(
        json.dumps({
            "rule": "per primary member: 95% paired-bootstrap CI of (A3 effect - A2 effect) "
                    "above 0 => elementary_adds; below 0 => elementary_costs; else null. "
                    "brick_share is descriptive only.",
            "family": "m=2 (lab2, lab3 auc_goal), BH within family",
            **shares,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
