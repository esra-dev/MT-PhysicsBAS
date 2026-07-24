#!/usr/bin/env python3
"""Rebuild the corrected Phase-3 tables from committed archives.

Validates each corrected run archive (DYNAMICS_OK gate manifests, tick-v1
energy stamps), reruns the frozen aggregate (analysis/phase3_dynamics.py at
the registration head), and compares the outputs against the committed tables
using the 12-significant-digit canonical numeric serialization (helper copied
from the Phase-1 pattern; Phase-1 analysis files stay byte-frozen).

Usage:
  python analysis/reproduce_phase3_v2.py phase3_v2_corrected
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from analysis import validate_phase3_v2_archive as archive_validator
except ImportError:  # executed as a script from the repo root
    import validate_phase3_v2_archive as archive_validator


ROOT = Path(__file__).resolve().parents[1]
FLOAT_TEXT = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
TABLES = ("phase3_delay_accuracy.csv", "phase3_compliance_ci.csv",
          "phase3_compliance_paired.csv")


def _canonical_csv_bytes(path: Path) -> bytes:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_root", type=Path, nargs="?",
                        default=Path("phase3_v2_corrected"))
    args = parser.parse_args()
    root = args.campaign_root
    run_dirs = sorted(path for path in root.glob("run_*") if path.is_dir())
    if not run_dirs:
        print(f"No run_* archives under {root}", file=sys.stderr)
        return 1

    for run_dir in run_dirs:
        inputs_path = run_dir / "analysis" / "out" / "workflow_inputs.json"
        inputs = json.loads(inputs_path.read_text(encoding="utf-8-sig"))
        profiles = [p.strip() for p in str(inputs["profiles"]).split(",") if p.strip()] \
            if isinstance(inputs["profiles"], str) else list(inputs["profiles"])
        replicas = [int(s) for s in inputs["seeds"]] if isinstance(inputs["seeds"], list) \
            else [int(s) for s in str(inputs["seeds"]).split(",") if s.strip()]
        errors = archive_validator.validate(run_dir, profiles, replicas)
        if errors:
            print(f"{run_dir}: archive validation FAILED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"{run_dir}: archive gates pass "
              f"({len(replicas)} replicas x {len(profiles)} profiles).")

        with tempfile.TemporaryDirectory(prefix="phase3-v2-reproduce-") as tmp:
            out_dir = Path(tmp)
            result = subprocess.run(
                [sys.executable, str(ROOT / "analysis" / "phase3_dynamics.py"),
                 "--root", str(run_dir / "dynamics_root"),
                 "--out", str(out_dir)],
                capture_output=True, text=True)
            if result.returncode != 0:
                print(result.stdout, file=sys.stderr)
                print(result.stderr, file=sys.stderr)
                return 1
            for name in TABLES:
                _compare(run_dir / "analysis" / "out" / name, out_dir / name)
    print("All corrected Phase-3 canonical numeric CSVs are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
