#!/usr/bin/env python3
"""Validate corrected Phase-4 (protocol phase1-v2, run-mode phase4_v2) archives.

Thin wrapper over analysis/validate_phase1_v2_archive.py with the Phase-4 lab
set. The archive layout is identical (benchmark/results_seed<N>/<lab>/...):
TRAINING_OK gate manifests with zero scenario fallbacks, declared-cycle
scenario schedules, paired-arm schedule identity, first-goal presentation
rows, and v2 benchmark schema columns for every declared scenario x run.
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from analysis import validate_phase1_v2_archive as base
except ImportError:  # executed as a script from the repo root
    import validate_phase1_v2_archive as base


PHASE4_LABS = ("lab4", "lab4dual", "lab4chain", "lab5")


def validate(root: Path, expected_seeds=range(1, 21),
             labs: tuple[str, ...] = PHASE4_LABS) -> list[str]:
    return base.validate(root, expected_seeds=expected_seeds, labs=labs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--seeds", default="1-20",
                        help="seed range 'a-b' or comma list (default: %(default)s)")
    args = parser.parse_args()
    if "-" in args.seeds and "," not in args.seeds:
        lo, hi = args.seeds.split("-", 1)
        seeds = range(int(lo), int(hi) + 1)
    else:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    errors = validate(args.root, expected_seeds=seeds)
    if errors:
        print("Phase-4 v2 archive validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Phase-4 v2 archive validation passed "
          f"({len(list(seeds))} seeds x {len(PHASE4_LABS)} labs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
