#!/usr/bin/env python3
"""Rebuild and byte-compare every corrected Phase-1 numeric result table."""

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
    from analysis.phase1_archive_inventory import verify_inventory
    from analysis.validate_phase1_v2_archive import validate
except ImportError:
    from phase1_archive_inventory import verify_inventory  # type: ignore
    from validate_phase1_v2_archive import validate  # type: ignore


REQUIRED_MODES = {
    "phase1_v2_kg_only",
    "phase1_v2_redundancy_only",
    "phase1_v2_baseline",
    "phase1_v2_pbrs_only",
}
NUMERIC_TABLES = (
    "summary_table_ci.csv",
    "paired_tests.csv",
    "learning_speed_table.csv",
    "learning_speed_tests.csv",
)
FLOAT_TEXT = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def _discover(campaign: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for provenance in campaign.glob("*/analysis/out/workflow_inputs.json"):
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        mode = payload["run_mode"]
        if mode in found:
            raise ValueError(f"duplicate archive for {mode}")
        found[mode] = provenance.parents[2]
    missing = REQUIRED_MODES - set(found)
    extra = set(found) - REQUIRED_MODES
    if missing or extra:
        raise ValueError(f"archive modes mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    return found


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
    expected_bytes = (_canonical_csv_bytes(expected) if expected.suffix == ".csv"
                      else expected.read_bytes())
    actual_bytes = (_canonical_csv_bytes(actual) if actual.suffix == ".csv"
                    else actual.read_bytes())
    if expected_bytes != actual_bytes:
        raise ValueError(f"canonical byte comparison failed: {expected} != {actual}")


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def reproduce(campaign: Path, work: Path) -> None:
    archives = _discover(campaign)
    for mode, archive in sorted(archives.items()):
        errors = validate(archive)
        if errors:
            raise ValueError(f"{mode} archive validation failed:\n" + "\n".join(errors))
        inventory = archive / "analysis/out/SHA256SUMS.csv"
        if inventory.is_file():
            errors = verify_inventory(archive, inventory)
            if errors:
                raise ValueError(f"{mode} inventory failed:\n" + "\n".join(errors))

        rebuilt = work / mode / "analysis/out"
        _run([
            sys.executable, "analysis/sweep_report.py",
            "--root", str(archive / "benchmark/results"),
            "--out", str(rebuilt),
            "--seeds-mode",
            "--ci-bootstrap-iters", "10000",
            "--protocol-version", "phase1-v2",
        ])
        for filename in NUMERIC_TABLES:
            _compare(archive / "analysis/out" / filename, rebuilt / filename)

    registered = work / "registered"
    _run([
        sys.executable, "analysis/phase1_v2_registered_family.py",
        "--arm-c-root", str(archives["phase1_v2_kg_only"]),
        "--redundancy-root", str(archives["phase1_v2_redundancy_only"]),
        "--out", str(registered),
    ])
    expected_registered = campaign / "analysis/registered"
    _compare(expected_registered / "phase1_v2_registered_family.csv",
             registered / "phase1_v2_registered_family.csv")
    _compare(expected_registered / "phase1_v2_decomposition.json",
             registered / "phase1_v2_decomposition.json")

    compiled = work / "phase1_v2_controls_and_descriptives.csv"
    _run([
        sys.executable, "analysis/phase1_v2_compile_controls.py", str(campaign),
        "--out", str(compiled),
    ])
    _compare(campaign / "analysis/phase1_v2_controls_and_descriptives.csv", compiled)

    protocol_summary = work / "phase1_v2_protocol_gate_summary.json"
    _run([
        sys.executable, "analysis/phase1_v2_protocol_summary.py", str(campaign),
        "--out", str(protocol_summary),
    ])
    _compare(campaign / "analysis/phase1_v2_protocol_gate_summary.json",
             protocol_summary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        reproduce(args.campaign, args.work_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="phase1-v2-reproduce-") as temp:
            reproduce(args.campaign, Path(temp))
    print("All corrected Phase-1 canonical numeric CSVs are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
