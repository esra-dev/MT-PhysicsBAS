#!/usr/bin/env python3
"""Registered Phase-2 protocol-v2 confirmatory analysis (frozen before data).

Computes the two frozen m=8 families over the corrected campaign archives:
  - Tier-1 RecoveryEpisodes family (pre_registration.md §9.5, unchanged),
  - DetectEpisode family (§9.6, unchanged membership; detector v2 makes it a
    NEW instrument — results are not comparable to the withdrawn record).

Estimand rules (frozen):
  - One outcome per (cell, arm, seed) from the LAST row of the cell's recovery
    CSV. A negative RecoveryEpisodes/DetectEpisode (never reconverged / never
    detected) is censored at adapt_episodes_effective + 1 (from the cell's
    ADAPT_OK manifest) and counted; a seed pair is NEVER dropped (the withdrawn
    protocol-v1 analysis silently dropped non-recovered pairs, e.g. n=9/9/4
    rows in the record).
  - Paired difference = ql_true - ql_false per seed; two-sided exact sign-flip
    test (analysis/exact_paired_stats.py), exact sign test, paired
    rank-biserial, 10,000-draw bootstrap CI on the mean, BH within each m=8
    family separately. No p/q can be zero (exact floor 2/2^20).
  - Duplicate cell files across archive roots are a fatal error (no
    first-copy-wins selection).

Usage:
  python analysis/phase2_v2_registered_family.py --roots phase2_v2_corrected/run_A phase2_v2_corrected/run_B ... \
      --out phase2_v2_corrected/analysis/registered
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps


SEEDS = tuple(range(1, 21))
BOOTSTRAP_ITERS = 10_000
BOOTSTRAP_BASE_SEED = 20260722

# Frozen family membership — copied verbatim from analysis/phase2_recovery.py
# (_REGISTERED_TIER1_FAMILY / _REGISTERED_DETECTION_FAMILY). Do not edit
# without a registered amendment.
TIER1_FAMILY = (
    "lab3_f1dead", "lab3_f1dead_z2", "lab3_f1bdead", "lab3_f1binv",
    "lab2_f1bdead", "labmon_f1dead", "lab3_f2dead_lowsun",
    "labmon2_f2dead_lowsun",
)
DETECTION_FAMILY = (
    "lab3_f1dead", "lab3_f1inv", "lab3_f1dead_z2", "lab3_f1inv_z2",
    "lab3_f1bdead", "lab3_f1binv", "lab2_f1bdead", "lab2_f1binv",
)

FIELDS = [
    "registered_cell", "metric", "n_paired", "seeds_paired",
    "mean_ql_true", "mean_ql_false", "mean_paired_difference",
    "median_paired_difference", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided", "p_sign_exact_two_sided", "paired_rank_biserial",
    "q_signflip_bh_m8", "bh_family_m",
    "censored_ql_true", "censored_ql_false",
]


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if row and not next(iter(row.values()), "").startswith("#")]


def _load_cell(roots: list[Path], profile: str, bool_name: str, seed: int,
               metric: str) -> tuple[float, bool]:
    """Return (censored outcome value, censored flag) for one cell."""
    name = f"stereotypes_{bool_name}_{profile}"
    matches = []
    for root in roots:
        candidate = root / "recovery_root" / f"seed{seed}" / f"recovery_{name}.csv"
        if candidate.is_file():
            matches.append(candidate)
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one recovery file for {profile}/{bool_name}/seed{seed}; "
            f"found {len(matches)}: {[str(m) for m in matches]}")
    recovery_path = matches[0]
    manifest_path = recovery_path.parent / f"ADAPT_OK_{name}.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing gate manifest for {recovery_path}")
    manifest = _json(manifest_path)
    horizon = int(manifest["adapt_episodes_effective"])
    rows = _csv_rows(recovery_path)
    if not rows:
        raise SystemExit(f"{recovery_path}: no recovery rows")
    value = int(rows[-1][metric])
    if value < 0:
        return float(horizon + 1), True
    return float(value), False


def _family_rows(roots: list[Path], family: tuple[str, ...], metric: str,
                 q_field: str) -> list[dict]:
    rows: list[dict] = []
    p_values: list[float] = []
    for index, profile in enumerate(family):
        true_vals, false_vals = [], []
        censored_true = censored_false = 0
        for seed in SEEDS:
            value, censored = _load_cell(roots, profile, "true", seed, metric)
            true_vals.append(value)
            censored_true += int(censored)
            value, censored = _load_cell(roots, profile, "false", seed, metric)
            false_vals.append(value)
            censored_false += int(censored)
        diffs = [a - b for a, b in zip(true_vals, false_vals)]
        mean_diff = sum(diffs) / len(diffs)
        rng = random.Random(BOOTSTRAP_BASE_SEED + index)
        boots = []
        for _ in range(BOOTSTRAP_ITERS):
            sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
            boots.append(sum(sample) / len(sample))
        boots.sort()
        ci_lo = boots[int(0.025 * BOOTSTRAP_ITERS)]
        ci_hi = boots[min(BOOTSTRAP_ITERS - 1, int(0.975 * BOOTSTRAP_ITERS))]
        p = eps.paired_signflip_p(true_vals, false_vals)
        p_values.append(p)
        rows.append({
            "registered_cell": profile,
            "metric": metric,
            "n_paired": len(diffs),
            "seeds_paired": ";".join(str(s) for s in SEEDS),
            "mean_ql_true": sum(true_vals) / len(true_vals),
            "mean_ql_false": sum(false_vals) / len(false_vals),
            "mean_paired_difference": mean_diff,
            "median_paired_difference": eps.median(diffs),
            "ci_lo_bootstrap": ci_lo,
            "ci_hi_bootstrap": ci_hi,
            "p_signflip_two_sided": p,
            "p_sign_exact_two_sided": eps.exact_sign_p(true_vals, false_vals),
            "paired_rank_biserial": eps.paired_rank_biserial(true_vals, false_vals),
            "bh_family_m": len(family),
            "censored_ql_true": censored_true,
            "censored_ql_false": censored_false,
        })
    for row, q in zip(rows, eps.bh_qvalues(p_values)):
        row[q_field] = q
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDS})


def run(roots: list[Path], out_dir: Path) -> None:
    tier1 = _family_rows(roots, TIER1_FAMILY, "RecoveryEpisodes", "q_signflip_bh_m8")
    detection = _family_rows(roots, DETECTION_FAMILY, "DetectEpisode", "q_signflip_bh_m8")
    _write(out_dir / "phase2_v2_registered_family.csv", tier1)
    _write(out_dir / "phase2_v2_detection_family.csv", detection)
    print(f"Wrote {len(tier1)} Tier-1 rows and {len(detection)} detection rows to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", type=Path, required=True,
                        help="corrected run archive roots (each containing recovery_root/)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.roots, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
