#!/usr/bin/env python3
"""Registered Phase-4 protocol-v2 KNOWLEDGE-LADDER analysis (frozen before data).

Registered in THESIS_STATE_REPORT.md Addendum 2026-11-13b. The ladder is

    A0 tabula rasa -> A1 redundancy rule -> A2 Brick structure -> A3 full KG

A0 is the ``ql_false`` arm of every run. A3 is the archived ``phase4_v2``
campaign. A1 (``phase4_v2_redundancy_only``) and A2 (``phase4_v2_brick_only``)
are the two control dispatches. Every arm's treatment effect is its within-run
paired ``ql_true - ql_false`` seed difference; a RUNG INCREMENT is the by-seed
difference of two arms' treatment effects.

Estimands are the frozen Phase-4 ones (``phase4_v2_registered_family``):
``avg_redundant`` = mean over a seed's benchmark rows of
(WastedSteps + ActuatorCyclingCount), lower is better; ``energy_compliance``
on lab5, higher is better.

Registered families (Benjamini-Hochberg within each family, n = 20 seeds):

  Family R, m = 3  "beyond the redundancy rule"
      lab4, lab4dual, lab4chain ``avg_redundant``: (A3 effect) - (A1 effect)
  Family S, m = 3  "beyond Brick structure"
      lab4, lab4dual, lab4chain ``avg_redundant``: (A3 effect) - (A2 effect)
  Secondary, single member, outside both families
      lab5 ``energy_compliance``: (A3 effect) - (A2 effect)

Pre-committed category per member, applied to the 95% paired bootstrap
interval of the increment (``avg_redundant``: a negative increment means the
upper arm removes more redundant actions):

      interval entirely on the favourable side of zero  -> ``adds``
      interval entirely on the unfavourable side        -> ``costs``
      interval contains zero                            -> ``null``

For Family R the frozen one-third / two-thirds share rule of the Phase-1
redundancy control is applied in addition: share = A1 mean effect / A3 mean
effect. Everything else written here is DESCRIPTIVE and carries no threshold.

Comparability gate (reported, not a test): the ``ql_false`` cells of a control
run are compared seed by seed with the archived A3 campaign's ``ql_false``
cells on the registered estimand.

Usage:
  python analysis/phase4_v2_knowledge_ladder.py \
      --full-roots phase4_v2_corrected/run_29926341581 phase4_v2_corrected/run_29926354783 \
      --brick-roots phase4_v2_ladder/run_<brick> \
      --redundancy-roots phase4_v2_ladder/run_<redundancy> \
      --out phase4_v2_ladder/analysis/registered
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import phase4_v2_registered_family as p4
    from analysis.phase1_v2_registered_family import _decomposition
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps  # type: ignore
    import phase4_v2_registered_family as p4  # type: ignore
    from phase1_v2_registered_family import _decomposition  # type: ignore


SEEDS = p4.SEEDS
DEPENDENCY_LABS = ("lab4", "lab4dual", "lab4chain")
ENERGY_LAB = "lab5"
BOOTSTRAP_ITERS = 10_000
BOOTSTRAP_BASE_SEED = 20261114

# Benchmark columns reported descriptively (mean over a seed's rows).
BENCH_COLUMNS = (
    ("goal_rate", "GoalReached"),
    ("avg_steps", "Steps"),
    ("avg_wasted", "WastedSteps"),
    ("avg_cycling", "ActuatorCyclingCount"),
    ("avg_policy_energy", "PolicyEnergyCost"),
    ("avg_deviation", "CumIlluminanceDeviation"),
)
# Direction of "better" for the category rule: -1 = lower is better.
FAVOURABLE_SIGN = {"avg_redundant": -1, "energy_compliance": +1}

FIELDS = [
    "registered_test", "family", "lab", "metric", "n_paired",
    "mean_upper_arm_effect", "mean_lower_arm_effect",
    "mean_increment", "median_increment", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided", "p_sign_exact_two_sided", "paired_rank_biserial",
    "n_positive", "n_tie", "n_negative",
    "q_signflip_bh", "bh_family_m", "registered_category",
    "share_lower_of_upper", "share_category",
]
DESC_FIELDS = [
    "row", "lab", "metric", "n_paired", "mean", "median",
    "ci_lo_bootstrap", "ci_hi_bootstrap", "p_signflip_two_sided",
    "paired_rank_biserial", "n_positive", "n_tie", "n_negative",
]
COMPARABILITY_FIELDS = [
    "control_arm", "lab", "metric", "n_seeds", "n_seeds_identical",
    "max_abs_difference", "mean_archived_ql_false", "mean_control_ql_false",
]


def _has_cells(roots: list[Path], lab: str) -> bool:
    return any((root / "benchmark" / f"results_seed{SEEDS[0]}" / lab).is_dir() for root in roots)


def _column_mean(cell: Path, mode: str, column: str) -> float:
    rows = p4._csv_rows(cell / f"benchmark_results_{mode}.csv")
    if not rows:
        raise SystemExit(f"{cell}: no benchmark rows")
    return sum(float(row[column]) for row in rows) / len(rows)


def _values(roots: list[Path], lab: str, mode: str, metric: str, lab5_tools) -> dict[int, float]:
    out: dict[int, float] = {}
    for seed in SEEDS:
        cell = p4._cell_dir(roots, seed, lab, mode)
        if metric == "avg_redundant":
            out[seed] = p4._avg_redundant(cell, mode)
        elif metric == "energy_compliance":
            weights, budgets, default_budget = lab5_tools
            out[seed] = p4._energy_compliance(cell, mode, weights, budgets, default_budget)
        else:
            out[seed] = _column_mean(cell, mode, dict(BENCH_COLUMNS)[metric])
    return out


def _effect(roots: list[Path], lab: str, metric: str, lab5_tools) -> dict[int, float]:
    on = _values(roots, lab, "ql_true", metric, lab5_tools)
    off = _values(roots, lab, "ql_false", metric, lab5_tools)
    return {seed: on[seed] - off[seed] for seed in SEEDS}


def _increment(upper: dict[int, float], lower: dict[int, float]) -> dict[int, float]:
    return {seed: upper[seed] - lower[seed] for seed in SEEDS}


def _summary(values: dict[int, float], rng_index: int) -> dict:
    diffs = [values[seed] for seed in SEEDS]
    zeros = [0.0] * len(diffs)
    rng = random.Random(BOOTSTRAP_BASE_SEED + rng_index)
    boots = []
    for _ in range(BOOTSTRAP_ITERS):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    return {
        "n_paired": len(diffs),
        "mean": sum(diffs) / len(diffs),
        "median": eps.median(diffs),
        "ci_lo_bootstrap": boots[int(0.025 * BOOTSTRAP_ITERS)],
        "ci_hi_bootstrap": boots[min(BOOTSTRAP_ITERS - 1, int(0.975 * BOOTSTRAP_ITERS))],
        "p_signflip_two_sided": eps.paired_signflip_p(diffs, zeros),
        "p_sign_exact_two_sided": eps.exact_sign_p(diffs, zeros),
        "paired_rank_biserial": eps.paired_rank_biserial(diffs, zeros),
        "n_positive": sum(1 for d in diffs if d > 0),
        "n_tie": sum(1 for d in diffs if d == 0),
        "n_negative": sum(1 for d in diffs if d < 0),
    }


def _category(metric: str, lo: float, hi: float) -> str:
    """adds / costs / null on the 95% interval, in the metric's own direction."""
    sign = FAVOURABLE_SIGN[metric]
    if (sign < 0 and hi < 0) or (sign > 0 and lo > 0):
        return "adds"
    if (sign < 0 and lo > 0) or (sign > 0 and hi < 0):
        return "costs"
    return "null"


def _member(name: str, family: str, lab: str, metric: str,
            upper: dict[int, float], lower: dict[int, float], rng_index: int) -> dict:
    stats = _summary(_increment(upper, lower), rng_index)
    upper_mean = sum(upper[s] for s in SEEDS) / len(SEEDS)
    lower_mean = sum(lower[s] for s in SEEDS) / len(SEEDS)
    return {
        "registered_test": name,
        "family": family,
        "lab": lab,
        "metric": metric,
        "n_paired": stats["n_paired"],
        "mean_upper_arm_effect": upper_mean,
        "mean_lower_arm_effect": lower_mean,
        "mean_increment": stats["mean"],
        "median_increment": stats["median"],
        "ci_lo_bootstrap": stats["ci_lo_bootstrap"],
        "ci_hi_bootstrap": stats["ci_hi_bootstrap"],
        "p_signflip_two_sided": stats["p_signflip_two_sided"],
        "p_sign_exact_two_sided": stats["p_sign_exact_two_sided"],
        "paired_rank_biserial": stats["paired_rank_biserial"],
        "n_positive": stats["n_positive"],
        "n_tie": stats["n_tie"],
        "n_negative": stats["n_negative"],
        "q_signflip_bh": "",
        "bh_family_m": "",
        "registered_category": _category(metric, stats["ci_lo_bootstrap"], stats["ci_hi_bootstrap"]),
        "share_lower_of_upper": "",
        "share_category": "",
    }


def _descriptive(row: str, lab: str, metric: str, values: dict[int, float], rng_index: int) -> dict:
    stats = _summary(values, rng_index)
    return {
        "row": row, "lab": lab, "metric": metric, "n_paired": stats["n_paired"],
        "mean": stats["mean"], "median": stats["median"],
        "ci_lo_bootstrap": stats["ci_lo_bootstrap"], "ci_hi_bootstrap": stats["ci_hi_bootstrap"],
        "p_signflip_two_sided": stats["p_signflip_two_sided"],
        "paired_rank_biserial": stats["paired_rank_biserial"],
        "n_positive": stats["n_positive"], "n_tie": stats["n_tie"], "n_negative": stats["n_negative"],
    }


def _comparability(arm: str, lab: str, metric: str, archived: dict[int, float],
                   control: dict[int, float]) -> dict:
    gaps = [abs(archived[s] - control[s]) for s in SEEDS]
    return {
        "control_arm": arm, "lab": lab, "metric": metric, "n_seeds": len(SEEDS),
        "n_seeds_identical": sum(1 for g in gaps if g == 0),
        "max_abs_difference": max(gaps),
        "mean_archived_ql_false": sum(archived[s] for s in SEEDS) / len(SEEDS),
        "mean_control_ql_false": sum(control[s] for s in SEEDS) / len(SEEDS),
    }


def run(full_roots: list[Path], brick_roots: list[Path], redundancy_roots: list[Path],
        out_dir: Path) -> dict:
    lab5_tools = p4._lab5_tools() if _has_cells(brick_roots, ENERGY_LAB) else None
    arms = {"A3_full_kg": full_roots, "A2_brick": brick_roots, "A1_redundancy": redundancy_roots}

    effects: dict[tuple[str, str, str], dict[int, float]] = {}
    for arm, roots in arms.items():
        for lab in DEPENDENCY_LABS:
            effects[(arm, lab, "avg_redundant")] = _effect(roots, lab, "avg_redundant", lab5_tools)

    family: list[dict] = []
    index = 0
    for fam, lower_arm, tag in (("R", "A1_redundancy", "A3_minus_A1"), ("S", "A2_brick", "A3_minus_A2")):
        members = []
        for lab in DEPENDENCY_LABS:
            index += 1
            members.append(_member(f"{tag}_{lab}_avg_redundant", fam, lab, "avg_redundant",
                                   effects[("A3_full_kg", lab, "avg_redundant")],
                                   effects[(lower_arm, lab, "avg_redundant")], index))
        for row, q in zip(members, eps.bh_qvalues([m["p_signflip_two_sided"] for m in members])):
            row["q_signflip_bh"] = q
            row["bh_family_m"] = len(members)
            if fam == "R":
                share = _decomposition(row["mean_upper_arm_effect"], row["mean_lower_arm_effect"])
                row["share_lower_of_upper"] = "" if share["redundancy_share"] is None else share["redundancy_share"]
                row["share_category"] = share["category"]
        family.extend(members)

    secondary_status = "not_run_no_lab5_cells"
    if lab5_tools is not None:
        index += 1
        full5 = _effect(full_roots, ENERGY_LAB, "energy_compliance", lab5_tools)
        brick5 = _effect(brick_roots, ENERGY_LAB, "energy_compliance", lab5_tools)
        effects[("A3_full_kg", ENERGY_LAB, "energy_compliance")] = full5
        effects[("A2_brick", ENERGY_LAB, "energy_compliance")] = brick5
        row = _member("A3_minus_A2_lab5_energy_compliance", "secondary", ENERGY_LAB,
                      "energy_compliance", full5, brick5, index)
        row["bh_family_m"] = 1
        row["q_signflip_bh"] = row["p_signflip_two_sided"]
        family.append(row)
        secondary_status = row["registered_category"]

    # ── Descriptives (no thresholds) ─────────────────────────────────────
    descriptives: list[dict] = []
    d_index = 1000
    for lab in DEPENDENCY_LABS:
        for arm in arms:
            d_index += 1
            descriptives.append(_descriptive(f"{arm}_effect", lab, "avg_redundant",
                                             effects[(arm, lab, "avg_redundant")], d_index))
        d_index += 1
        descriptives.append(_descriptive(
            "A2_minus_A1_increment", lab, "avg_redundant",
            _increment(effects[("A2_brick", lab, "avg_redundant")],
                       effects[("A1_redundancy", lab, "avg_redundant")]), d_index))
        for metric, _column in BENCH_COLUMNS:
            for arm, roots in arms.items():
                d_index += 1
                descriptives.append(_descriptive(f"{arm}_effect", lab, metric,
                                                 _effect(roots, lab, metric, lab5_tools), d_index))
    if lab5_tools is not None:
        for arm in ("A3_full_kg", "A2_brick"):
            d_index += 1
            descriptives.append(_descriptive(f"{arm}_effect", ENERGY_LAB, "energy_compliance",
                                             effects[(arm, ENERGY_LAB, "energy_compliance")], d_index))
            for metric, _column in BENCH_COLUMNS:
                d_index += 1
                descriptives.append(_descriptive(f"{arm}_effect", ENERGY_LAB, metric,
                                                 _effect(arms[arm], ENERGY_LAB, metric, lab5_tools), d_index))

    # ── Comparability of the tabula-rasa arm across runs ─────────────────
    comparability: list[dict] = []
    for arm in ("A2_brick", "A1_redundancy"):
        for lab in DEPENDENCY_LABS:
            comparability.append(_comparability(
                arm, lab, "avg_redundant",
                _values(full_roots, lab, "ql_false", "avg_redundant", lab5_tools),
                _values(arms[arm], lab, "ql_false", "avg_redundant", lab5_tools)))
    if lab5_tools is not None:
        comparability.append(_comparability(
            "A2_brick", ENERGY_LAB, "energy_compliance",
            _values(full_roots, ENERGY_LAB, "ql_false", "energy_compliance", lab5_tools),
            _values(brick_roots, ENERGY_LAB, "ql_false", "energy_compliance", lab5_tools)))

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, fieldnames, table in (
            ("phase4_v2_knowledge_ladder_family.csv", FIELDS, family),
            ("phase4_v2_knowledge_ladder_descriptives.csv", DESC_FIELDS, descriptives),
            ("phase4_v2_knowledge_ladder_comparability.csv", COMPARABILITY_FIELDS, comparability)):
        with (out_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(table)

    summary = {
        "registration": "docs/_audit/THESIS_STATE_REPORT.md Addendum 2026-11-13b",
        "rule": "per member: 95% paired-bootstrap interval of the rung increment entirely on the "
                "favourable side of zero => adds; entirely on the unfavourable side => costs; "
                "else null. avg_redundant: lower is better. energy_compliance: higher is better.",
        "family_R": {row["lab"]: {"category": row["registered_category"],
                                  "mean_increment": row["mean_increment"],
                                  "share_category": row["share_category"],
                                  "share_lower_of_upper": row["share_lower_of_upper"]}
                     for row in family if row["family"] == "R"},
        "family_S": {row["lab"]: {"category": row["registered_category"],
                                  "mean_increment": row["mean_increment"]}
                     for row in family if row["family"] == "S"},
        "secondary_lab5_energy_compliance": secondary_status,
        "tabula_rasa_identical_in_all_seeds": all(
            row["n_seeds_identical"] == row["n_seeds"] for row in comparability),
    }
    (out_dir / "phase4_v2_knowledge_ladder.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(family)} registered rows, {len(descriptives)} descriptive rows and "
          f"{len(comparability)} comparability rows to {out_dir}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-roots", nargs="+", type=Path, required=True,
                        help="archived phase4_v2 run folders (A3 and its own A0)")
    parser.add_argument("--brick-roots", nargs="+", type=Path, required=True,
                        help="phase4_v2_brick_only run folders (A2)")
    parser.add_argument("--redundancy-roots", nargs="+", type=Path, required=True,
                        help="phase4_v2_redundancy_only run folders (A1)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.full_roots, args.brick_roots, args.redundancy_roots, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
