"""Phase-1b frozen power-analysis procedure (docs/PHASE1B_POWER_PROTOCOL.md §3).

Consumes ONLY allow-listed pilot diagnostics (centred-residual SDs, pooled
scale anchors, censoring fractions — never arm-labelled means or effects) and
simulates the full six-member family at the frozen SESOIs to pick the
smallest adequate confirmatory N ∈ {20, 30, 40}.

Frozen details:
  * effects are FIXED to the SESOIs — pilot means never enter;
  * replicate p-values use the CLT approximation of the exact paired
    sign-flip randomisation test: p = 2*Phi(-|sum d| / sqrt(sum d^2)) —
    the same statistic the confirmatory analysis computes exactly;
  * six-member BH at q = 0.05, rejection counted only in the predicted
    direction; RNG seed 0x1B5EED; 10,000 replicates per (member, N).

Input CSV (produced by hand from the --pilot-diagnostics report, one row per
member): member,sd,pooled_scale,censor_frac_frozen,censor_frac_baseline
  - sd: centred paired-residual SD of the member's per-seed statistic
  - pooled_scale: arm-blind pooled mean of the member's metric (only used by
    M5/M6 relative SESOIs; 0/empty otherwise)
  - censor fractions: only used for M6's endpoint switch (rule: >0.25 in
    either arm => goal-rate endpoint; sd must then be the goal-rate residual
    SD and pooled_scale is ignored).

Usage:
  python analysis/phase1b_power.py --pilot-csv phase1b_pilot/power_inputs.csv \
      --out phase1b_pilot/power_report.txt
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exact_paired_stats import bh_qvalues  # noqa: E402

CANDIDATE_N = (20, 30, 40)
REPLICATES = 10_000
ALPHA = 0.05
SEED = 0x1B5EED

# anchor A = 3 x corrected Phase-1 v2 lab2 net auc_goal effect (+0.0037)
ANCHOR_A = 0.0111

MEMBERS = [
    # (name, sesoi_fn(pooled_scale, horizon), predicted_sign)
    ("labrel_stateless_frozen_slope",  lambda ps, h: ANCHOR_A / 16.0, +1),
    ("labrel_incremental_slope",       lambda ps, h: ANCHOR_A / 16.0, +1),
    ("labrel8s_fragmentation_did",     lambda ps, h: ANCHOR_A,        +1),
    ("labband_extended_vs_frozen_auc", lambda ps, h: ANCHOR_A,        +1),
    ("labband_extended_vs_baseline_dev", lambda ps, h: -0.10 * ps,    -1),
    ("chain3_frozen_vs_baseline_rmst", lambda ps, h: -0.05 * h,       -1),
]

CHAIN3_GOALRATE_SESOI = 0.10  # used when the censoring rule switches M6


def _phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def signflip_p_clt(diffs) -> float:
    s = sum(diffs)
    ss = math.sqrt(sum(d * d for d in diffs))
    if ss == 0.0:
        return 1.0
    z = abs(s) / ss
    return max(2.0 * _phi(-z), 1e-300)


def simulate(rows: dict, rmst_horizon: float, out_lines: list) -> dict:
    rng = random.Random(SEED)
    m6 = rows["chain3_frozen_vs_baseline_rmst"]
    m6_switch = (m6["censor_frac_frozen"] > 0.25
                 or m6["censor_frac_baseline"] > 0.25)
    powers = {}
    for n in CANDIDATE_N:
        reject_counts = {name: 0 for name, _, _ in MEMBERS}
        for _ in range(REPLICATES):
            ps, signs, names = [], [], []
            for name, sesoi_fn, sign in MEMBERS:
                r = rows[name]
                if name == "chain3_frozen_vs_baseline_rmst" and m6_switch:
                    sesoi, sign = CHAIN3_GOALRATE_SESOI, +1
                else:
                    sesoi = sesoi_fn(r["pooled_scale"], rmst_horizon)
                diffs = [rng.gauss(sesoi, r["sd"]) for _ in range(n)]
                p = signflip_p_clt(diffs)
                mean = sum(diffs) / n
                ps.append(p)
                signs.append(1 if (mean > 0) == (sign > 0) else 0)
                names.append(name)
            qs = bh_qvalues(ps)
            for name, q, right_dir in zip(names, qs, signs):
                if q <= ALPHA and right_dir:
                    reject_counts[name] += 1
        powers[n] = {k: v / REPLICATES for k, v in reject_counts.items()}
        out_lines.append("N=%d: %s" % (n, "  ".join(
            "%s=%.3f" % (k.split("_")[0] + ":" + k, v)
            for k, v in powers[n].items())))
    return {"powers": powers, "m6_endpoint": "goal_rate" if m6_switch else "rmst"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-csv", required=True)
    ap.add_argument("--rmst-horizon", type=float, required=True,
                    help="frozen presentation censoring horizon H for M6")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = {}
    with open(args.pilot_csv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["member"].strip()] = {
                "sd": float(r["sd"]),
                "pooled_scale": float(r.get("pooled_scale") or 0.0),
                "censor_frac_frozen": float(r.get("censor_frac_frozen") or 0.0),
                "censor_frac_baseline": float(r.get("censor_frac_baseline") or 0.0),
            }
    missing = [name for name, _, _ in MEMBERS if name not in rows]
    if missing:
        print("missing member rows: %s" % missing)
        return 1

    lines = ["Phase-1b frozen power analysis (protocol docs/PHASE1B_POWER_PROTOCOL.md)",
             "replicates=%d alpha=%.2f seed=%#x anchor_A=%.4f" %
             (REPLICATES, ALPHA, SEED, ANCHOR_A)]
    result = simulate(rows, args.rmst_horizon, lines)
    lines.append("M6 endpoint: %s" % result["m6_endpoint"])

    chosen = None
    for n in CANDIDATE_N:
        if all(p >= 0.80 for p in result["powers"][n].values()):
            chosen = n
            break
    if chosen is None:
        lines.append("NO candidate N <= 40 powers every member at 0.80.")
        lines.append("Per protocol: under-powered members must be omitted or "
                     "prospectively relabelled exploratory BEFORE registration:")
        for name in result["powers"][CANDIDATE_N[-1]]:
            p40 = result["powers"][CANDIDATE_N[-1]][name]
            lines.append("  %s: power(N=40)=%.3f %s"
                         % (name, p40, "OK" if p40 >= 0.80 else "UNDER-POWERED"))
    else:
        lines.append("SELECTED confirmatory N = %d (smallest with all members >= 0.80)"
                     % chosen)

    body = "\n".join(lines) + "\n"
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
