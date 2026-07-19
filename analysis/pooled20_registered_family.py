#!/usr/bin/env python3
"""Registered m=3 BH post-step for the Plan B pooled-20 reanalysis.

Addendum 2026-07-18c §2 registers a confirmatory family of exactly three
cells for the arm-C headline seed extension (seeds 1-10 from run 29639767776
pooled with seeds 11-20 from run 29692725784):

    1. lab2 auc_goal            (learning_speed_tests.csv)
    2. lab3 mean_first_goal     (learning_speed_tests.csv)
    3. lab3 avg_cycling, ql_true vs ql_false (paired_tests.csv)

sweep_report.py computes the estimator, deterministic paired bootstrap
(seed 0xC1) and per-file BH families over ALL cells it finds; this script
extracts the three registered rows from a pooled-20 sweep_report output
directory and re-applies sweep_report's own _bh_qvalues within the
registered m=3 family only. No other statistic is touched or recomputed.

Guards: every registered row must be present with n_paired == 20 and
seeds_paired == 1;...;20, otherwise the script aborts (the registration
admits no partial family).

Usage:
    python analysis/pooled20_registered_family.py \
        --pooled-out <dir with learning_speed_tests.csv + paired_tests.csv> \
        --out <output csv path>
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep_report import _bh_qvalues  # noqa: E402  (registered BH machinery)

EXPECTED_SEEDS = ";".join(str(s) for s in range(1, 21))

# (label, source file, row-match predicate, columns to carry through)
REGISTERED = [
    ("lab2 auc_goal",
     "learning_speed_tests.csv",
     lambda r: r["profile"] == "lab2" and r["metric"] == "auc_goal",
     ("mean_diff_true_minus_false", "ci_lo", "ci_hi", "p_bootstrap",
      "p_wilcoxon", "cliffs_delta")),
    ("lab3 mean_first_goal",
     "learning_speed_tests.csv",
     lambda r: r["profile"] == "lab3" and r["metric"] == "mean_first_goal",
     ("mean_diff_true_minus_false", "ci_lo", "ci_hi", "p_bootstrap",
      "p_wilcoxon", "cliffs_delta")),
    ("lab3 avg_cycling (ql_true - ql_false)",
     "paired_tests.csv",
     lambda r: (r["profile"] == "lab3" and r["metric"] == "avg_cycling"
                and r["mode_a"] == "ql_true" and r["mode_b"] == "ql_false"),
     ("mean_diff", "ci_lo", "ci_hi", "p_bootstrap",
      "p_wilcoxon", "cliffs_delta")),
]


def _find_row(pooled_out: Path, fname: str, pred) -> dict:
    with (pooled_out / fname).open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if pred(r)]
    if len(rows) != 1:
        raise SystemExit(f"ABORT: expected exactly 1 matching row in {fname}, "
                         f"found {len(rows)}")
    return rows[0]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pooled-out", required=True,
                    help="sweep_report output dir for the pooled-20 tree")
    ap.add_argument("--out", required=True, help="output csv path")
    args = ap.parse_args(argv)
    pooled_out = Path(args.pooled_out)

    out_rows = []
    for label, fname, pred, cols in REGISTERED:
        r = _find_row(pooled_out, fname, pred)
        if int(r["n_paired"]) != 20 or r["seeds_paired"] != EXPECTED_SEEDS:
            raise SystemExit(f"ABORT: {label}: n_paired={r['n_paired']} "
                             f"seeds={r['seeds_paired']} != registered "
                             f"20-seed family")
        row = {"cell": label, "source_file": fname,
               "n_paired": r["n_paired"], "seeds_paired": r["seeds_paired"],
               "mean_diff": r[cols[0]]}
        for c in cols[1:]:
            row[c] = r[c]
        out_rows.append(row)

    qs = _bh_qvalues([float(r["p_bootstrap"]) for r in out_rows])
    for row, q in zip(out_rows, qs):
        row["q_bootstrap_bh_m3"] = q
        row["bh_family_m"] = 3

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    for row in out_rows:
        print(f"{row['cell']}: diff={row['mean_diff']} "
              f"[{row['ci_lo']}, {row['ci_hi']}] p={row['p_bootstrap']} "
              f"q_m3={row['q_bootstrap_bh_m3']} delta={row['cliffs_delta']}")
    print(f"pooled20_registered_family: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
