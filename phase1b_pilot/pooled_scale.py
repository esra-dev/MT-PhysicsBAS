"""Arm-blind pooled scale anchors from the pilot (allow-listed by
docs/PHASE1B_POWER_PROTOCOL.md §2: "Pooled-scale anchors use the pilot's
arm-blind POOLED mean of a metric (pooling all arms; no arm labels)").

Pools EVERY (mode, arm, seed) cell of the metric into one flat list before
averaging — no per-arm or per-mode grouping ever occurs, so no effect
direction or arm-labelled mean is visible.
"""
import csv
import glob
import os
import sys

root = sys.argv[1]  # phase1b_pilot/staged
vals_dev = []
for path in glob.glob(os.path.join(root, "*", "benchmark", "results_seed*",
                                   "labband", "ql_*", "benchmark_results_*.csv")):
    with open(path, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            v = row.get("CumIlluminanceDeviation")
            if v not in (None, ""):
                vals_dev.append(float(v))
print("labband pooled CumIlluminanceDeviation: n=%d mean=%.6f"
      % (len(vals_dev), sum(vals_dev) / len(vals_dev)))
