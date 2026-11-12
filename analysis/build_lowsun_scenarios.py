#!/usr/bin/env python3
"""Derive the pinned-low-sun Phase-2 scenario files from their clean parents.

Round-2 audit finding R2-001/R2-002 (docs/final_state/AUDIT_RESOLUTION.md):
the `*_lowsun` profiles pinned `Sunshine = 100` only inside the simulator's
episode-reset sampler, which the protocol-v2 explicit scenario starts bypass.
Every adaptation episode therefore started from the parent's scenario file,
whose schedule spans sun ranks {0, 100, 400, 900}, so the registered low-sun
manipulation was never delivered.

This script carries the manipulation at scenario level: it copies the parent
training schedule (same ids, same order, same actuator start states) and pins
`Sunshine` to 100 lux in every scenario, recomputing the declared zone levels
with the CLEAN lab physics so the declared and settled start states agree.
The schedule hash (comma-joined ids) is unchanged by construction; the file
hash is what distinguishes the delivered low-sun treatment.

Usage:
  python analysis/build_lowsun_scenarios.py            # write both files
  python analysis/build_lowsun_scenarios.py --check    # verify committed files
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOWSUN_LUX = 100

# (parent file, derived file, physics lab)
DERIVATIONS = (
    ("benchmark/train_scenarios_lab3.json",
     "benchmark/train_scenarios_lab3_lowsun.json", "lab3"),
    ("benchmark/train_scenarios_labmon2.json",
     "benchmark/train_scenarios_labmon2_lowsun.json", "labmon2"),
)

FIELD_ORDER = {
    "lab3": ("id", "Z1Level", "Z2Level", "Z1Light", "Z2Light", "Z1Blinds",
             "Z2Blinds", "Spotlight", "Sunshine"),
    "labmon2": ("id", "Z1Level", "Z2Level", "Z1Light", "Z2Light", "Z1Monitor",
                "Z2Monitor", "Z1Blinds", "Z2Blinds", "Sunshine"),
}


def clean_levels(lab: str, row: dict) -> dict[str, float]:
    """Clean (fault-free) physics of the parent lab, mirroring
    analysis/validate_phase1_scenarios.py for lab3 and the labmon2 flow."""
    sun = float(row["Sunshine"])
    z1l, z2l = bool(row.get("Z1Light")), bool(row.get("Z2Light"))
    z1b, z2b = bool(row.get("Z1Blinds")), bool(row.get("Z2Blinds"))
    if lab == "lab3":
        shared = 150 if bool(row.get("Spotlight")) else 0
        return {
            "Z1Level": 25 + (400 if z1l else 0) + (100 if z2l else 0)
            + (0.50 * sun if z1b else 0) + (0.30 * sun if z2b else 0) + shared,
            "Z2Level": 25 + (400 if z2l else 0) + (100 if z1l else 0)
            + (0.50 * sun if z2b else 0) + (0.30 * sun if z1b else 0) + shared,
        }
    if lab == "labmon2":
        z1m, z2m = bool(row.get("Z1Monitor")), bool(row.get("Z2Monitor"))
        return {
            "Z1Level": 25 + (400 if z1l else 0) + (200 if z1m else 0)
            + (0.50 * sun if z1b else 0),
            "Z2Level": 25 + (400 if z2l else 0) + (200 if z2m else 0)
            + (0.50 * sun if z2b else 0),
        }
    raise ValueError(f"unknown lab {lab!r}")


def _number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


def _describe(lab: str, row: dict) -> str:
    on = [key for key in FIELD_ORDER[lab]
          if key not in ("id", "Z1Level", "Z2Level", "Sunshine") and row.get(key)]
    start = "all off" if not on else "on: " + ", ".join(on)
    return (f"pinned sun={LOWSUN_LUX} (rank 1); start {start}; parent id {row['id']}")


def derive(parent_rows: list[dict], lab: str, parent_name: str) -> list[dict]:
    derived: list[dict] = []
    for index, parent in enumerate(parent_rows):
        row = {key: parent[key] for key in FIELD_ORDER[lab] if key in parent}
        row["Sunshine"] = LOWSUN_LUX
        for key, value in clean_levels(lab, row).items():
            row[key] = _number(value)
        ordered: dict = {}
        if index == 0:
            ordered["comment"] = (
                f"{lab} LOW-SUN training schedule, derived from {parent_name} by "
                "analysis/build_lowsun_scenarios.py: identical ids, order and "
                f"actuator start states; Sunshine pinned to {LOWSUN_LUX} lux in "
                "every scenario (declared levels recomputed with the clean "
                "physics). Delivers the registered Phase-2 low-sun manipulation "
                "at scenario level (audit R2-001/R2-002); the flow reset-sampler "
                "pin alone was bypassed by protocol-v2 explicit scenario starts.")
        for key in FIELD_ORDER[lab]:
            ordered[key] = row[key]
        ordered["description"] = _describe(lab, row)
        derived.append(ordered)
    return derived


def render(rows: list[dict], lab: str) -> str:
    lines = ["["]
    for index, row in enumerate(rows):
        lines.append("  {")
        if "comment" in row:
            lines.append(f'    "comment": {json.dumps(row["comment"])},')
        fields = ", ".join(f'"{key}": {json.dumps(row[key])}'
                           for key in FIELD_ORDER[lab])
        lines.append(f"    {fields},")
        lines.append(f'    "description": {json.dumps(row["description"])}')
        lines.append("  }" + ("," if index < len(rows) - 1 else ""))
    lines.append("]")
    return "\n".join(lines) + "\n"


def build_all() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for parent_rel, derived_rel, lab in DERIVATIONS:
        parent_path = ROOT / parent_rel
        parent_rows = json.loads(parent_path.read_text(encoding="utf-8-sig"))
        rows = derive(parent_rows, lab, parent_rel)
        outputs[ROOT / derived_rel] = render(rows, lab)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if a committed derived file differs")
    args = parser.parse_args()
    mismatches = []
    for path, text in build_all().items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                mismatches.append(str(path))
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")
    if mismatches:
        print("derived low-sun scenario files are stale:")
        for item in mismatches:
            print(f"- {item}")
        return 1
    if args.check:
        print("derived low-sun scenario files match their generator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
