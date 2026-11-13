#!/usr/bin/env python3
"""Post-hoc robustness and reference summaries (2026-11-13). UNREGISTERED.

Nothing here replaces a registered analysis and no registered file is touched.
The script reads the committed registered tables and raw archives and writes
three descriptive CSVs under docs/audit/:

1. registered_multiplicity_sensitivity.csv
   Benjamini-Hochberg controls the false discovery rate for independent (or
   positively dependent) test statistics. Several registered families test
   metrics on the same runs. As a sensitivity check, every family is
   re-adjusted with the Benjamini-Yekutieli procedure, which holds under
   arbitrary dependence: q_BY = min(1, c(m) * q_BH), c(m) = sum_{i=1..m} 1/i.

2. registered_sign_counts.csv
   The matched-pairs rank-biserial correlation drops tied seeds, so a value of
   +-1.0 can rest on few seeds. For each registered member whose raw files are
   in this tree, the per-seed paired differences are rebuilt with the
   registered loaders and the numbers of positive, tied, and negative seeds
   are reported beside the stored effect size.

3. phase1_v2_posthoc_reference_contrasts.csv
   Cross-arm contrasts that no registration covers: reward shaping (PBRS)
   against plain tabula rasa, and each knowledge arm against PBRS, on
   training success; plus the rule-based controller's benchmark levels as a
   reference row. Descriptive only.

Output is deterministic. Run from the repository root:
    python analysis/posthoc_robustness_summary.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import phase1_v2_registered_family as p1
    from analysis import phase2_lowsun_v3_family as p2low
    from analysis import phase2_v2_registered_family as p2
    from analysis import phase4_v2_registered_family as p4
    from analysis import sweep_report as sr
except ImportError:  # direct `python analysis/posthoc_robustness_summary.py`
    import exact_paired_stats as eps  # type: ignore
    import phase1_v2_registered_family as p1  # type: ignore
    import phase2_lowsun_v3_family as p2low  # type: ignore
    import phase2_v2_registered_family as p2  # type: ignore
    import phase4_v2_registered_family as p4  # type: ignore
    import sweep_report as sr  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05
P1 = ROOT / "phase1_v2_corrected"
RUNS = {"arm_c": "run_29848584965", "redundancy": "run_29848587274",
        "baseline": "run_29848589682", "pbrs": "run_29848592010", "brick": "run_42834963612"}
# (family label, table, member column, stored BH-q column)
FAMILIES = (
    ("phase1_primary", "phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv",
     "registered_test", "q_signflip_bh_m5"),
    ("phase1_knowledge_ladder",
     "phase1_v2_corrected/analysis/registered/phase1_v2_knowledge_ladder_family.csv",
     "registered_test", "q_signflip_bh_m2"),
    ("phase1b_2026_07", "phase1b_corrected/analysis/registered/phase1b_registered_family.csv",
     "member", "q_signflip_bh"),
    ("phase1b_extended_v3",
     "phase1b_extended_v3/analysis/registered/phase1b_extended_v3_registered_family.csv",
     "member", "q_signflip_bh"),
    ("phase2_recovery", "phase2_v2_corrected/analysis/registered/phase2_v2_registered_family.csv",
     "registered_cell", "q_signflip_bh_m8"),
    ("phase2_detection", "phase2_v2_corrected/analysis/registered/phase2_v2_detection_family.csv",
     "registered_cell", "q_signflip_bh_m8"),
    ("phase2_lowsun_recovery",
     "phase2_v3_lowsun/analysis/registered/phase2_lowsun_v3_recovery_family.csv",
     "registered_cell", "q_signflip_bh_m2"),
    ("phase2_lowsun_detection",
     "phase2_v3_lowsun/analysis/registered/phase2_lowsun_v3_detection_family.csv",
     "registered_cell", "q_signflip_bh_m2"),
    ("phase4", "phase4_v2_corrected/analysis/registered/phase4_v2_registered_family.csv",
     "registered_cell", "q_signflip_bh_m4"),
)
NOTES = {("phase1b_2026_07", "M2"): "2026-07 manipulation-failure diagnostic, not a treatment result",
         ("phase1b_2026_07", "M4"): "2026-07 manipulation-failure diagnostic, not a treatment result"}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: float) -> str:
    return format(value, ".12g")


# ------------------------------------------------------------ 1. multiplicity
def multiplicity() -> list[dict]:
    out: list[dict] = []
    for label, rel, member_col, q_col in FAMILIES:
        rows = [row for row in _read(ROOT / rel) if row["bh_family_m"].strip().isdigit()]
        m = int(rows[0]["bh_family_m"])
        if len(rows) != m or any(int(row["bh_family_m"]) != m for row in rows):
            raise SystemExit(f"{label}: family size does not match bh_family_m")
        p_values = [float(row["p_signflip_two_sided"]) for row in rows]
        bh = eps.bh_qvalues(p_values)
        harmonic = sum(1.0 / i for i in range(1, m + 1))
        for row, p_value, q_bh in zip(rows, p_values, bh):
            stored = float(row[q_col])
            if abs(stored - q_bh) > 1e-9 * max(1.0, abs(stored)):
                raise SystemExit(f"{label}/{row[member_col]}: stored BH q differs from recomputation")
            q_by = min(1.0, harmonic * q_bh)
            out.append({
                "family": label, "member": row[member_col], "family_m": m,
                "p_signflip_two_sided": _fmt(p_value), "q_bh": _fmt(q_bh),
                "by_factor_c_m": _fmt(harmonic), "q_by": _fmt(q_by),
                "significant_bh_05": q_bh <= ALPHA, "significant_by_05": q_by <= ALPHA,
                "verdict_changes": (q_bh <= ALPHA) != (q_by <= ALPHA),
                "note": NOTES.get((label, row[member_col]), ""),
            })
    return out


# ------------------------------------------------------------- 2. sign counts
def _count(family: str, member: str, diffs: list[float], table_row: dict[str, str],
           mean_col: str) -> dict:
    mean = sum(diffs) / len(diffs)
    stored = float(table_row[mean_col])
    if abs(mean - stored) > 1e-9 * max(1.0, abs(stored)):
        raise SystemExit(f"{family}/{member}: rebuilt mean {mean!r} != stored {stored!r}")
    positive = sum(value > 0 for value in diffs)
    negative = sum(value < 0 for value in diffs)
    return {
        "family": family, "member": member, "n_paired": len(diffs),
        "n_positive": positive, "n_tied": len(diffs) - positive - negative,
        "n_negative": negative, "n_seeds_that_differ": positive + negative,
        "mean_paired_difference": _fmt(stored),
        "paired_rank_biserial": _fmt(float(table_row["paired_rank_biserial"])),
    }


def _table(rel: str, member_col: str) -> dict[str, dict[str, str]]:
    return {row[member_col]: row for row in _read(ROOT / rel)}


def sign_counts(hydrated: Path) -> list[dict]:
    """`hydrated` holds the Phase-2 and Phase-4 raw archives. Their recovery
    and benchmark CSVs are gitignored, so a fresh checkout has only the
    manifests; pass the directory that contains the downloaded archives."""
    out: list[dict] = []
    seeds = p1.EXPECTED_SEEDS

    c_on, c_off = p1._speed(P1 / RUNS["arm_c"])
    r_on, r_off = p1._speed(P1 / RUNS["redundancy"])
    b_on, b_off = p1._speed(P1 / RUNS["brick"])
    c_lab2 = p1._effect(c_on, c_off, "lab2", "auc_goal")
    r_lab2 = p1._effect(r_on, r_off, "lab2", "auc_goal")
    primary = {
        "1_arm_c_lab2_auc_goal": c_lab2,
        "2_redundancy_lab2_auc_goal": r_lab2,
        "3_arm_c_minus_redundancy_lab2": {s: c_lab2[s] - r_lab2[s] for s in seeds},
        "4_arm_c_lab3_mean_first_goal_presentations":
            p1._effect(c_on, c_off, "lab3", "mean_first_goal_presentations"),
        "5_arm_c_lab3_avg_cycling": p1._cycling(P1 / RUNS["arm_c"]),
    }
    table = _table(FAMILIES[0][1], "registered_test")
    for member, diffs in primary.items():
        out.append(_count("phase1_primary", member, [diffs[s] for s in seeds], table[member],
                          "mean_paired_difference"))

    table = _table(FAMILIES[1][1], "registered_test")
    for index, lab in enumerate(("lab2", "lab3"), start=1):
        full = p1._effect(c_on, c_off, lab, "auc_goal")
        brick = p1._effect(b_on, b_off, lab, "auc_goal")
        member = f"{index}_arm_c_minus_brick_{lab}_auc_goal"
        out.append(_count("phase1_knowledge_ladder", member, [full[s] - brick[s] for s in seeds],
                          table[member], "mean_paired_difference"))

    def phase2(label: str, rel: str, roots: list[Path], family: tuple[str, ...], metric: str):
        table = _table(rel, "registered_cell")
        for cell in family:
            diffs = [p2._load_cell(roots, cell, "true", s, metric)[0]
                     - p2._load_cell(roots, cell, "false", s, metric)[0] for s in p2.SEEDS]
            out.append(_count(label, cell, diffs, table[cell], "mean_paired_difference"))

    v2_roots = sorted((hydrated / "phase2_v2_corrected").glob("run_*"))
    low_roots = sorted((ROOT / "phase2_v3_lowsun").glob("run_*"))
    phase2("phase2_recovery", FAMILIES[4][1], v2_roots, p2.TIER1_FAMILY, "RecoveryEpisodes")
    phase2("phase2_detection", FAMILIES[5][1], v2_roots, p2.DETECTION_FAMILY, "DetectEpisode")
    phase2("phase2_lowsun_recovery", FAMILIES[6][1], low_roots, p2low.LOWSUN_FAMILY,
           "RecoveryEpisodes")
    phase2("phase2_lowsun_detection", FAMILIES[7][1], low_roots, p2low.LOWSUN_FAMILY,
           "DetectEpisode")

    p4_roots = sorted((hydrated / "phase4_v2_corrected").glob("run_*"))
    weights, budgets, default_budget = p4._lab5_tools()
    table = _table(FAMILIES[8][1], "registered_cell")
    for profile, metric in p4.FAMILY:
        diffs = []
        for seed in p4.SEEDS:
            values = []
            for mode in ("ql_true", "ql_false"):
                cell = p4._cell_dir(p4_roots, seed, profile, mode)
                values.append(p4._avg_redundant(cell, mode) if metric == "avg_redundant"
                              else p4._energy_compliance(cell, mode, weights, budgets,
                                                         default_budget))
            diffs.append(values[0] - values[1])
        out.append(_count("phase4", profile, diffs, table[profile], "mean_paired_difference"))
    return out


# ------------------------------------------------------ 3. reference contrasts
def _contrast(name: str, lab: str, a: list[float], b: list[float]) -> dict:
    diffs = [x - y for x, y in zip(a, b)]
    positive = sum(value > 0 for value in diffs)
    negative = sum(value < 0 for value in diffs)
    return {
        "row_type": "posthoc_contrast", "contrast": name, "lab": lab, "metric": "auc_goal",
        "n_paired": len(diffs), "mean_first": _fmt(sum(a) / len(a)),
        "mean_second": _fmt(sum(b) / len(b)),
        "mean_paired_difference": _fmt(sum(diffs) / len(diffs)),
        "median_paired_difference": _fmt(eps.median(diffs)),
        "n_positive": positive, "n_tied": len(diffs) - positive - negative,
        "n_negative": negative,
        "p_signflip_two_sided_uncorrected": _fmt(eps.paired_signflip_p(a, b)),
        "paired_rank_biserial": _fmt(eps.paired_rank_biserial(a, b)),
        "status": "post-hoc, unregistered, descriptive; no multiplicity correction",
    }


def reference_contrasts() -> list[dict]:
    seeds = p1.EXPECTED_SEEDS
    speed = {arm: p1._speed(P1 / run) for arm, run in RUNS.items()}
    out: list[dict] = []
    for lab in ("lab2", "lab3"):
        def level(arm: str, label_on: bool) -> list[float]:
            cells = speed[arm][0 if label_on else 1][lab]
            return [float(cells[s]["auc_goal"]) for s in seeds]

        tabula_rasa = level("baseline", False)
        # Guards: every run's ql_false label must be the same tabula-rasa learner,
        # except in the PBRS run, where both labels carry reward shaping.
        for arm in ("arm_c", "redundancy", "brick"):
            if level(arm, False) != tabula_rasa:
                raise SystemExit(f"{lab}: ql_false of {arm} differs from the baseline run")
        if level("baseline", True) != tabula_rasa or level("pbrs", True) != level("pbrs", False):
            raise SystemExit(f"{lab}: label controls are not symmetric")
        pbrs = level("pbrs", False)
        out.append(_contrast("pbrs_minus_tabula_rasa", lab, pbrs, tabula_rasa))
        for arm, label in (("arm_c", "full_kg"), ("brick", "brick_structure"),
                           ("redundancy", "redundancy_only")):
            out.append(_contrast(f"{label}_minus_pbrs", lab, level(arm, True), pbrs))

    arm_c_seeds = p1._ordered_seed_roots(P1 / RUNS["arm_c"])
    per_seed = sr._collect_per_seed_values(arm_c_seeds)
    for lab in ("lab1", "lab2", "lab3"):
        for policy in ("rule_based", "ql_true", "ql_false"):
            for metric in ("goal_rate", "avg_steps", "avg_policy_energy", "avg_redundant"):
                values = per_seed.get(metric, {}).get((lab, policy))
                if not values:
                    raise SystemExit(f"missing benchmark values for {lab}/{policy}/{metric}")
                levels = [float(values[s]) for s in seeds]
                out.append({
                    "row_type": "benchmark_level", "contrast": policy, "lab": lab,
                    "metric": metric, "n_paired": len(levels),
                    "mean_first": _fmt(sum(levels) / len(levels)), "mean_second": "",
                    "mean_paired_difference": "", "median_paired_difference": "",
                    "n_positive": "", "n_tied": "", "n_negative": "",
                    "p_signflip_two_sided_uncorrected": "", "paired_rank_biserial": "",
                    "status": "descriptive level from the arm-C run (29848584965), mean over 20 seeds",
                })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "audit")
    parser.add_argument("--hydrated-archive-root", type=Path, default=ROOT,
                        help="directory containing the downloaded phase2_v2_corrected and "
                             "phase4_v2_corrected raw archives (their raw CSVs are gitignored)")
    args = parser.parse_args()

    rows = multiplicity()
    _write(args.out / "registered_multiplicity_sensitivity.csv", list(rows[0].keys()), rows)
    changed = [f"{row['family']}/{row['member']}" for row in rows if row["verdict_changes"]]
    print(f"multiplicity: {len(rows)} registered members in {len(FAMILIES)} families; "
          f"verdicts that change under Benjamini-Yekutieli: {changed or 'none'}")

    rows = sign_counts(args.hydrated_archive_root)
    _write(args.out / "registered_sign_counts.csv", list(rows[0].keys()), rows)
    print(f"sign counts: {len(rows)} registered members rebuilt from raw files")

    rows = reference_contrasts()
    _write(args.out / "phase1_v2_posthoc_reference_contrasts.csv", list(rows[0].keys()), rows)
    print(f"reference contrasts: {len(rows)} descriptive rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
