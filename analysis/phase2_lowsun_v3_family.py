#!/usr/bin/env python3
"""Registered analysis of the Phase-2 low-sun re-execution (campaign v3, 2026-11).

Round-2 audit findings R2-001/R2-002 established that the two registered
low-sun Tier-1 cells (`lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun`) never
received their low-sun treatment in the 2026-07 corrected campaign. This
script analyses their re-execution with the treatment delivered at scenario
level (`benchmark/train_scenarios_*_lowsun.json`), exactly as registered in
docs/phase2_lowsun_rerun_registration_2026-11-11.md:

- the SAME frozen estimands and statistics as the corrected campaign
  (analysis/phase2_v2_registered_family.py: last-row outcome, censoring at
  adapt_episodes_effective + 1, exact paired sign-flip, exact sign test,
  rank-biserial, fixed-seed 10,000-draw bootstrap CI, no p/q of zero);
- two NEW two-member BH families (recovery and detection; m = 2) over the two
  re-executed cells only. The original m = 8 family tables are left untouched:
  their rows for these two cells describe the delivered full-sun condition and
  remain classified as such in the dossier.
- a per-seed primitives table (including BestEffortRank / RankShortfall when
  the recovery CSV carries them) so the delivered-treatment signature can be
  audited directly: under pinned sun 100 with both lamps dead the nominal goal
  is unreachable, so BestEffortRank must never be 3 in lab3.

Usage:
  python analysis/phase2_lowsun_v3_family.py --roots phase2_v3_lowsun/run_<id> [...] \
      --out phase2_v3_lowsun/analysis/registered
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from analysis import phase2_v2_registered_family as base
except ImportError:  # executed as a script from the repo root
    import phase2_v2_registered_family as base  # type: ignore


LOWSUN_FAMILY = ("lab3_f2dead_lowsun", "labmon2_f2dead_lowsun")
Q_FIELD = "q_signflip_bh_m2"
FIELDS = [Q_FIELD if field == "q_signflip_bh_m8" else field for field in base.FIELDS]
PRIMITIVE_FIELDS = ["registered_cell", "arm", "seed", "RecoveryEpisodes", "DetectEpisode",
                    "ReconvergeEpisode", "BestEffortRank", "RankShortfall",
                    "NominalGoal", "BlacklistEvents", "adapt_episodes_effective",
                    "scenario_file_sha256", "lowsun_pin_delivered"]


def _write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def _primitives(roots: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for profile in LOWSUN_FAMILY:
        for bool_name, arm in (("true", "ql_true"), ("false", "ql_false")):
            for seed in base.SEEDS:
                name = f"stereotypes_{bool_name}_{profile}"
                matches = [root / "recovery_root" / f"seed{seed}" / f"recovery_{name}.csv"
                           for root in roots]
                matches = [m for m in matches if m.is_file()]
                if len(matches) != 1:
                    raise SystemExit(f"expected one recovery file for {profile}/{arm}/seed{seed}, "
                                     f"found {len(matches)}")
                last = base._csv_rows(matches[0])[-1]
                manifest = base._json(matches[0].parent / f"ADAPT_OK_{name}.json")
                row = {"registered_cell": profile, "arm": arm, "seed": seed,
                       "adapt_episodes_effective": manifest.get("adapt_episodes_effective"),
                       "scenario_file_sha256": manifest.get("scenario_file_sha256", ""),
                       "lowsun_pin_delivered": manifest.get("lowsun_pin_delivered", "")}
                for key in PRIMITIVE_FIELDS:
                    if key in last and key not in row:
                        row[key] = last[key]
                rows.append(row)
    return rows


def run(roots: list[Path], out_dir: Path) -> None:
    recovery = base._family_rows(roots, LOWSUN_FAMILY, "RecoveryEpisodes", Q_FIELD)
    detection = base._family_rows(roots, LOWSUN_FAMILY, "DetectEpisode", Q_FIELD)
    _write(out_dir / "phase2_lowsun_v3_recovery_family.csv", recovery, FIELDS)
    _write(out_dir / "phase2_lowsun_v3_detection_family.csv", detection, FIELDS)
    _write(out_dir / "phase2_lowsun_v3_per_seed.csv", _primitives(roots), PRIMITIVE_FIELDS)
    print(f"Wrote {len(recovery)} recovery rows, {len(detection)} detection rows and the "
          f"per-seed primitives to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="+", type=Path, required=True,
                        help="low-sun re-execution run archive roots (each containing recovery_root/)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.roots, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
