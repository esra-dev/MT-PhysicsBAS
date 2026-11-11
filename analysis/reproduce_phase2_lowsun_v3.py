#!/usr/bin/env python3
"""Rebuild the Phase-2 low-sun re-execution tables from the committed archives.

Mirrors analysis/reproduce_phase2_v2.py for the 2026-11 campaign root
``phase2_v3_lowsun/``: every ``run_*`` archive must pass the corrected-protocol
archive gates WITH the treatment-delivery gate enabled (every ``*_lowsun`` cell
carries evidence that its schedule pinned Sunshine = 100), then the frozen
low-sun family analysis is re-run and canonically byte-compared against the
committed tables under ``<campaign>/analysis/registered/``.

Usage:
  python analysis/reproduce_phase2_lowsun_v3.py phase2_v3_lowsun
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

try:
    from analysis import phase2_lowsun_v3_family as family
    from analysis import validate_phase2_v2_archive as archive_validator
    from analysis.reproduce_phase2_v2 import _compare, _run_inputs
except ImportError:  # executed as a script from the repo root
    import phase2_lowsun_v3_family as family  # type: ignore
    import validate_phase2_v2_archive as archive_validator  # type: ignore
    from reproduce_phase2_v2 import _compare, _run_inputs  # type: ignore


REGISTERED_TABLES = ("phase2_lowsun_v3_recovery_family.csv",
                     "phase2_lowsun_v3_detection_family.csv",
                     "phase2_lowsun_v3_per_seed.csv")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_root", type=Path, nargs="?",
                        default=Path("phase2_v3_lowsun"))
    args = parser.parse_args()
    root = args.campaign_root
    run_dirs = sorted(path for path in root.glob("run_*") if path.is_dir())
    if not run_dirs:
        print(f"No run_* archives under {root}", file=sys.stderr)
        return 1
    for run_dir in run_dirs:
        inputs = _run_inputs(run_dir)
        profiles = [p.strip() for p in str(inputs["profiles"]).split(",") if p.strip()] \
            if isinstance(inputs["profiles"], str) else list(inputs["profiles"])
        seeds = [int(s) for s in inputs["seeds"]] if isinstance(inputs["seeds"], list) \
            else [int(s) for s in str(inputs["seeds"]).split(",") if s.strip()]
        errors = archive_validator.validate(run_dir, profiles, seeds,
                                            require_treatment_delivery=True)
        if errors:
            print(f"{run_dir}: archive validation FAILED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"{run_dir}: archive + treatment-delivery gates pass "
              f"({len(seeds)} seeds x {len(profiles)} profiles).")
    with tempfile.TemporaryDirectory(prefix="phase2-lowsun-v3-reproduce-") as tmp:
        rebuilt = Path(tmp)
        family.run(run_dirs, rebuilt)
        committed = root / "analysis" / "registered"
        for name in REGISTERED_TABLES:
            _compare(committed / name, rebuilt / name)
    print("All Phase-2 low-sun v3 canonical numeric CSVs are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
