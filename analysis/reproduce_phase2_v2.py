#!/usr/bin/env python3
"""Rebuild the corrected Phase-2 registered tables from committed archives.

Validates every corrected run archive (gate manifests, schedule identity,
detector/protocol stamps, parent provenance), reruns the frozen registered
analysis, and compares the result against the committed CSVs using the same
12-significant-digit canonical numeric serialization as
analysis/reproduce_phase1_v2.py (the helper is copied, not imported — Phase-1
analysis files stay byte-frozen).

Usage:
  python analysis/reproduce_phase2_v2.py phase2_v2_corrected
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import tempfile
from pathlib import Path

try:
    from analysis import phase2_v2_registered_family as family
    from analysis import validate_phase2_v2_archive as archive_validator
except ImportError:  # executed as a script from the repo root
    import phase2_v2_registered_family as family
    import validate_phase2_v2_archive as archive_validator


FLOAT_TEXT = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
REGISTERED_TABLES = ("phase2_v2_registered_family.csv", "phase2_v2_detection_family.csv")


def _canonical_csv_bytes(path: Path) -> bytes:
    """Serialize numeric CSV cells identically across Python/OS float repr details."""
    output = io.StringIO(newline="")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        writer = csv.writer(output, lineterminator="\n")
        for row in reader:
            canonical: list[str] = []
            for value in row:
                if FLOAT_TEXT.fullmatch(value) and ("." in value or "e" in value.lower()):
                    rendered = format(float(value), ".12g")
                    canonical.append("0" if rendered == "-0" else rendered)
                else:
                    canonical.append(value)
            writer.writerow(canonical)
    return output.getvalue().encode("utf-8")


def _compare(expected: Path, actual: Path) -> None:
    if not expected.is_file():
        raise FileNotFoundError(f"committed result table missing: {expected}")
    if not actual.is_file():
        raise FileNotFoundError(f"rebuild did not produce: {actual}")
    if _canonical_csv_bytes(expected) != _canonical_csv_bytes(actual):
        raise ValueError(f"canonical byte comparison failed: {expected} != {actual}")


def _run_inputs(run_dir: Path) -> dict:
    path = run_dir / "analysis" / "out" / "workflow_inputs.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing workflow inputs: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_root", type=Path, nargs="?",
                        default=Path("phase2_v2_corrected"))
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
        errors = archive_validator.validate(run_dir, profiles, seeds)
        if errors:
            print(f"{run_dir}: archive validation FAILED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"{run_dir}: archive gates pass "
              f"({len(seeds)} seeds x {len(profiles)} profiles).")

    with tempfile.TemporaryDirectory(prefix="phase2-v2-reproduce-") as tmp:
        rebuilt = Path(tmp)
        family.run(run_dirs, rebuilt)
        committed = root / "analysis" / "registered"
        for name in REGISTERED_TABLES:
            _compare(committed / name, rebuilt / name)
    print("All corrected Phase-2 canonical numeric CSVs are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
