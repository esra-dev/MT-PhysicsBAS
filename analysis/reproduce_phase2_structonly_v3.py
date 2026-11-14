#!/usr/bin/env python3
"""Rebuild the Phase-2 structure-only campaign tables from the committed archives.

Mirrors analysis/reproduce_phase2_lowsun_v3.py for the 2026-11 campaign root
``phase2_v3_structonly/``: every ``run_*`` archive must pass the corrected-
protocol archive gates WITH both strict gates enabled —

- the knowledge-layer delivery gate (every adapt cell recorded AND log-verified
  ``brick`` as its layer), and
- the low-sun treatment-delivery gate (the two ``*_lowsun`` cells carry the
  pinned-schedule evidence) —

then the frozen structure-only family analysis is re-run against the archived
full-layer comparators and canonically byte-compared against the committed
tables under ``<campaign>/analysis/registered/``.

The comparator archives have their own reproducers and are not re-validated
here: ``analysis/reproduce_phase2_v2.py`` covers ``phase2_v2_corrected/`` and
``analysis/reproduce_phase2_lowsun_v3.py`` covers ``phase2_v3_lowsun/``. This
script reads their raw per-seed files directly, so a corrupted comparator
fails the byte comparison rather than passing silently.

Usage:
  python analysis/reproduce_phase2_structonly_v3.py phase2_v3_structonly
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

try:
    from analysis import phase2_structonly_v3_family as family
    from analysis import validate_phase2_v2_archive as archive_validator
    from analysis.reproduce_phase2_v2 import _compare, _run_inputs
except ImportError:  # executed as a script from the repo root
    import phase2_structonly_v3_family as family  # type: ignore
    import validate_phase2_v2_archive as archive_validator  # type: ignore
    from reproduce_phase2_v2 import _compare, _run_inputs  # type: ignore


KNOWLEDGE_LAYER = "brick"
REGISTERED_TABLES = ("phase2_structonly_v3_wrongblame_family.csv",
                     "phase2_structonly_v3_detection_family.csv",
                     "phase2_structonly_v3_recovery_family.csv",
                     "phase2_structonly_v3_per_seed.csv")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_root", type=Path, nargs="?",
                        default=Path("phase2_v3_structonly"))
    parser.add_argument("--record-base", type=Path, default=Path("."),
                        help="directory against which the frozen comparator roots resolve")
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
        recorded_layer = inputs.get("knowledge_layer")
        if recorded_layer != KNOWLEDGE_LAYER:
            print(f"{run_dir}: workflow_inputs.json records knowledge_layer="
                  f"{recorded_layer!r}, expected {KNOWLEDGE_LAYER!r}", file=sys.stderr)
            return 1
        errors = archive_validator.validate(run_dir, profiles, seeds,
                                            require_treatment_delivery=True,
                                            require_knowledge_layer=KNOWLEDGE_LAYER)
        if errors:
            print(f"{run_dir}: archive validation FAILED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"{run_dir}: archive + knowledge-layer + treatment-delivery gates pass "
              f"({len(seeds)} seeds x {len(profiles)} profiles).")
    with tempfile.TemporaryDirectory(prefix="phase2-structonly-v3-reproduce-") as tmp:
        rebuilt = Path(tmp)
        family.run(run_dirs, args.record_base, rebuilt)
        committed = root / "analysis" / "registered"
        for name in REGISTERED_TABLES:
            _compare(committed / name, rebuilt / name)
    print("All Phase-2 structure-only v3 canonical numeric CSVs are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
