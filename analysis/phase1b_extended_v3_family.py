#!/usr/bin/env python3
"""Registered analysis of the Phase-1b extended-KG re-execution (campaign v3, 2026-11).

Round-1 audit finding AUD-001 established that the 2026-07 "extended" runs
executed effective frozen KG: the three extended knobs were dropped by the
Gradle forwarding allow-list, so the intended M2/M4 (and exploratory M5)
contrasts were never measured. This script analyses the re-executed extended
arm (two seed-half archives under ``phase1b_extended_v3/``) against the
UNCHANGED archived frozen-KG and baseline arms of the 2026-07 campaign, as
registered in docs/phase1b_extended_rerun_registration_2026-11-11.md:

- member definitions, per-seed statistics, exact tests, bootstrap convention
  and zero-guards are imported from the frozen analysis/phase1b_report.py
  (M2 ``labrel_incremental_slope``: within-seed OLS slope over K in
  {0,4,8,16} of extended-minus-frozen ``auc_goal``; M4
  ``labband_extended_vs_frozen_auc``; M5 ``labband_extended_vs_baseline_dev``);
- a NEW two-member Benjamini-Hochberg family {M2, M4} (m = 2); M5 stays
  exploratory (no q) as in the original registration;
- bootstrap seeds reuse the original family offsets (M2 -> 1, M4 -> 3,
  M5 -> 4) so the CI convention is identical to the frozen report;
- a primitives table of the per-seed ``auc_goal`` / ``avg_dev`` inputs so the
  contrast can be audited cell by cell.

The staged archive layout is the one analysis/phase1b_report.py reads
(``<root>/<mode>/benchmark/results_seed<N>/<profile>/...``); staging from
``run_<id>/`` archives is done by analysis/reproduce_phase1b_extended_v3.py.

Usage:
  python analysis/phase1b_extended_v3_family.py --roots <staged-root> --out <dir>
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import phase1b_report as report
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps  # type: ignore
    import phase1b_report as report  # type: ignore


SEEDS = tuple(range(1, 21))
# (member, registered_test, metric, predicted, bootstrap offset in the frozen FAMILY)
MEMBERS = (
    ("M2", "labrel_incremental_slope", "auc_goal_slope_per_K", "positive", 1),
    ("M4", "labband_extended_vs_frozen_auc", "auc_goal", "positive", 3),
    ("M5", "labband_extended_vs_baseline_dev", "avg_dev", "negative", 4),
)
CONFIRMATORY = ("M2", "M4")
SESOI = {"M2": 0.000694, "M4": 0.0111, "M5": -0.0616}

FIELDS = [
    "member", "registered_test", "metric", "n_paired", "seeds_paired",
    "mean_paired_statistic", "median_paired_statistic", "ci_lo_bootstrap",
    "ci_hi_bootstrap", "p_signflip_two_sided", "p_sign_exact_two_sided",
    "paired_rank_biserial", "q_signflip_bh", "bh_family_m", "predicted_direction",
    "sesoi", "comparator_modes",
]
PRIMITIVE_FIELDS = ["member_input", "mode", "profile", "seed", "metric", "value"]


def _write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def _require_seeds(index: report.ArchiveIndex, mode: str) -> None:
    have = tuple(index.mode_seeds(mode))
    if have != SEEDS:
        raise SystemExit(f"{mode}: archived seeds {have} != registered {SEEDS}")


def member_diffs(index: report.ArchiveIndex) -> dict[str, list[float]]:
    seeds = list(SEEDS)
    return {
        "M2": report._labrel_slopes(index, seeds, report.MODE_EXTENDED, report.MODE_FROZEN),
        "M4": report._band_auc_diff(index, seeds, report.MODE_EXTENDED, report.MODE_FROZEN),
        "M5": report._band_dev_diff(index, seeds, report.MODE_EXTENDED, report.MODE_BASELINE),
    }


def build_rows(index: report.ArchiveIndex, bootstrap_iters: int) -> list[dict]:
    diffs_by_member = member_diffs(index)
    rows: list[dict] = []
    p_values: dict[str, float] = {}
    for member, name, metric, predicted, offset in MEMBERS:
        diffs = diffs_by_member[member]
        zeros = [0.0] * len(diffs)
        p = report._guard_nonzero(f"{member} p_signflip", eps.paired_signflip_p(diffs, zeros))
        lo, hi = report._bootstrap_ci(diffs, offset, bootstrap_iters)
        comparator = ("extended-minus-frozen" if member in ("M2", "M4")
                      else "extended-minus-baseline")
        rows.append({
            "member": member, "registered_test": name, "metric": metric,
            "n_paired": len(diffs), "seeds_paired": ";".join(str(s) for s in SEEDS),
            "mean_paired_statistic": sum(diffs) / len(diffs),
            "median_paired_statistic": eps.median(diffs),
            "ci_lo_bootstrap": lo, "ci_hi_bootstrap": hi,
            "p_signflip_two_sided": p,
            "p_sign_exact_two_sided": report._guard_nonzero(
                f"{member} p_sign", eps.exact_sign_p(diffs, zeros)),
            "paired_rank_biserial": eps.paired_rank_biserial(diffs, zeros),
            "bh_family_m": "exploratory", "q_signflip_bh": "",
            "predicted_direction": predicted, "sesoi": SESOI[member],
            "comparator_modes": comparator,
        })
        p_values[member] = p
    confirmatory = [row for row in rows if row["member"] in CONFIRMATORY]
    for row, q in zip(confirmatory, eps.bh_qvalues([p_values[r["member"]] for r in confirmatory])):
        row["bh_family_m"] = len(confirmatory)
        row["q_signflip_bh"] = report._guard_nonzero(f"{row['member']} q_bh", q)
    return rows


def primitive_rows(index: report.ArchiveIndex) -> list[dict]:
    rows: list[dict] = []
    for seed in SEEDS:
        for mode in (report.MODE_EXTENDED, report.MODE_FROZEN):
            for profile in report.LABREL_PROFILES:
                rows.append({"member_input": "M2", "mode": mode, "profile": profile,
                             "seed": seed, "metric": "auc_goal",
                             "value": index.auc_goal(mode, seed, profile)})
            rows.append({"member_input": "M4", "mode": mode, "profile": report.BAND_PROFILE,
                         "seed": seed, "metric": "auc_goal",
                         "value": index.auc_goal(mode, seed, report.BAND_PROFILE)})
        for mode in (report.MODE_EXTENDED, report.MODE_BASELINE):
            rows.append({"member_input": "M5", "mode": mode, "profile": report.BAND_PROFILE,
                         "seed": seed, "metric": "avg_dev",
                         "value": index.required_benchmark_metric(
                             mode, seed, report.BAND_PROFILE, "avg_dev")})
    return rows


def run(roots: list[Path], out_dir: Path, bootstrap_iters: int = report.BOOTSTRAP_ITERS) -> None:
    index = report.ArchiveIndex(roots)
    for mode in (report.MODE_EXTENDED, report.MODE_FROZEN, report.MODE_BASELINE):
        _require_seeds(index, mode)
    rows = build_rows(index, bootstrap_iters)
    _write(out_dir / "phase1b_extended_v3_registered_family.csv", rows, FIELDS)
    _write(out_dir / "phase1b_extended_v3_primitives.csv", primitive_rows(index), PRIMITIVE_FIELDS)
    print(f"Wrote {len(rows)} member rows and the primitives table to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="+", type=Path, required=True,
                        help="staged root(s) containing <mode>/benchmark/results_seed<N>/ trees")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bootstrap-iters", type=int, default=report.BOOTSTRAP_ITERS)
    args = parser.parse_args()
    run(args.roots, args.out, args.bootstrap_iters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
