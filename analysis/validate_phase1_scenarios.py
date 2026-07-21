#!/usr/bin/env python3
"""Fail if Phase-1 scenario IDs or declared lux disagree with current physics."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def expected_levels(lab: str, row: dict) -> dict[str, float]:
    sun = float(row.get("Sunshine", 0))
    z1_light = bool(row.get("Z1Light", False))
    if lab == "lab1":
        return {"Z1Level": 25 + (400 if z1_light else 0)}
    z2_light = bool(row.get("Z2Light", False))
    z1_blind = bool(row.get("Z1Blinds", False))
    z2_blind = bool(row.get("Z2Blinds", False))
    if lab == "lab2":
        return {
            "Z1Level": 25 + (400 if z1_light else 0) + (0.50 * sun if z1_blind else 0),
            "Z2Level": 25 + (400 if z2_light else 0) + (0.50 * sun if z2_blind else 0),
        }
    if lab == "lab3":
        spotlight = bool(row.get("Spotlight", False))
        shared = 150 if spotlight else 0
        return {
            "Z1Level": 25 + (400 if z1_light else 0) + (100 if z2_light else 0)
            + (0.50 * sun if z1_blind else 0) + (0.30 * sun if z2_blind else 0) + shared,
            "Z2Level": 25 + (400 if z2_light else 0) + (100 if z1_light else 0)
            + (0.50 * sun if z2_blind else 0) + (0.30 * sun if z1_blind else 0) + shared,
        }
    raise ValueError(f"Unknown Phase-1 lab: {lab}")


def validate_file(path: Path, lab: str) -> list[str]:
    errors: list[str] = []
    rows = json.loads(path.read_text(encoding="utf-8"))
    ids: set[int] = set()
    scenario_count = 0
    for row in rows:
        if "id" not in row:
            errors.append(f"{path}: scenario entry is missing integer id")
            continue
        scenario_count += 1
        scenario_id = row["id"]
        if not isinstance(scenario_id, int):
            errors.append(f"{path}: non-integer id {scenario_id!r}")
        elif scenario_id in ids:
            errors.append(f"{path}: duplicate id {scenario_id}")
        ids.add(scenario_id)
        for key, expected in expected_levels(lab, row).items():
            actual = float(row[key])
            if abs(actual - expected) > 1e-9:
                errors.append(
                    f"{path}: id {scenario_id} {key}={actual:g}, expected {expected:g}"
                )
    if not scenario_count:
        errors.append(f"{path}: no scenarios")

    text = path.read_text(encoding="utf-8")
    stale = {
        "lab1": ("0.10*Sunshine", "sun alone"),
        "lab3": ("Z2Light?50", "0.25*Sun", "= 700/zone", "700 each"),
    }.get(lab, ())
    for token in stale:
        if token in text:
            errors.append(f"{path}: stale physics text {token!r}")
    return errors


def validate_all(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    simulator_tokens = {
        "lab1": ("var z1 = 25", "(z1light ? 400 : 0)"),
        "lab2": ("var z1 = 25", "(z1b ? 0.50 * sun : 0)",
                 "var z2 = 25", "(z2b ? 0.50 * sun : 0)"),
        "lab3": ("var z1 = 25", "(z2l ? 100", "(z2b ? 0.30 * sun",
                 "var z2 = 25", "(z1l ? 100", "(z1b ? 0.30 * sun"),
    }
    for lab in ("lab1", "lab2", "lab3"):
        simulator = root / "simulator" / f"simulator_flow_{lab}.json"
        simulator_text = simulator.read_text(encoding="utf-8")
        for token in simulator_tokens[lab]:
            if token not in simulator_text:
                errors.append(
                    f"{simulator}: expected current physics token is missing: {token!r}")
        for prefix in ("scenarios", "train_scenarios"):
            errors.extend(validate_file(root / "benchmark" / f"{prefix}_{lab}.json", lab))
    return errors


def main() -> int:
    errors = validate_all()
    if errors:
        print("Phase-1 scenario validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Phase-1 scenario validation passed (6 files; IDs unique; lux matches physics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
