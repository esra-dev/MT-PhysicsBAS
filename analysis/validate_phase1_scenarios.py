#!/usr/bin/env python3
"""Fail if Phase-1/Phase-4 scenario IDs or declared lux disagree with physics."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE1_LABS = ("lab1", "lab2", "lab3")
PHASE4_LABS = ("lab4", "lab4dual", "lab4chain", "lab5")
# Phase 1b (branch phase1b-labs-2026-07). "labrel" is the shared scenario
# unit for the four stateless rungs (labrel0/4/8/16 alias one scenario pair);
# their four flows are fingerprinted individually below.
PHASE1B_LABS = ("labrel", "labrel8s", "labband", "lab4chain3")
ALL_LABS = PHASE1_LABS + PHASE4_LABS + PHASE1B_LABS


def expected_levels(lab: str, row: dict) -> dict[str, float]:
    sun = float(row.get("Sunshine", 0))
    z1_light = bool(row.get("Z1Light", False))
    if lab == "lab1":
        return {"Z1Level": 25 + (400 if z1_light else 0)}
    if lab in ("labrel", "labrel8s"):
        # One zone, one true lamp; decoys have no lux effect by construction.
        return {"Z1Level": 25 + (400 if z1_light else 0)}
    if lab == "labband":
        daylight = 0.50 * sun if bool(row.get("Z1Blinds", False)) else 0.0
        if bool(row.get("Awning", False)):
            daylight *= 0.25
        return {"Z1Level": 25 + (400 if bool(row.get("StrongLamp", False)) else 0)
                + (150 if bool(row.get("WeakLamp", False)) else 0) + daylight}
    if lab == "lab4chain3":
        lit = (z1_light and bool(row.get("PlugZ1", False))
               and bool(row.get("Breaker", False)))
        return {"Z1Level": 25 + (400 if lit else 0)}
    z2_light = bool(row.get("Z2Light", False))
    z1_blind = bool(row.get("Z1Blinds", False))
    z2_blind = bool(row.get("Z2Blinds", False))
    if lab == "lab2":
        return {
            "Z1Level": 25 + (400 if z1_light else 0) + (0.50 * sun if z1_blind else 0),
            "Z2Level": 25 + (400 if z2_light else 0) + (0.50 * sun if z2_blind else 0),
        }
    spotlight = bool(row.get("Spotlight", False))
    shared = 150 if spotlight else 0
    if lab == "lab3":
        return {
            "Z1Level": 25 + (400 if z1_light else 0) + (100 if z2_light else 0)
            + (0.50 * sun if z1_blind else 0) + (0.30 * sun if z2_blind else 0) + shared,
            "Z2Level": 25 + (400 if z2_light else 0) + (100 if z1_light else 0)
            + (0.50 * sun if z2_blind else 0) + (0.30 * sun if z1_blind else 0) + shared,
        }
    if lab in PHASE4_LABS:
        # Phase-4 physics (simulator_flow_lab4/lab4dual/lab4chain/lab5.json):
        # AND-gated lamps, 150-lux cross-lamp coupling, 0.40-sun foreign blind.
        if lab == "lab5":
            z1_on = bool(row.get("Z1Eff", False)) or bool(row.get("Z1Ineff", False))
            z2_on = bool(row.get("Z2Eff", False)) or bool(row.get("Z2Ineff", False))
        else:
            plug1 = bool(row.get("PlugZ1", False))
            if lab == "lab4":
                z1_on = z1_light and plug1
                z2_on = z2_light
            elif lab == "lab4dual":
                z1_on = z1_light and plug1
                z2_on = z2_light and bool(row.get("PlugZ2", False))
            else:  # lab4chain: breaker -> plug -> lamp
                z1_on = z1_light and plug1 and bool(row.get("MasterSwitch", False))
                z2_on = z2_light
        return {
            "Z1Level": 25 + (400 if z1_on else 0) + (150 if z2_on else 0)
            + (0.50 * sun if z1_blind else 0) + (0.40 * sun if z2_blind else 0) + shared,
            "Z2Level": 25 + (400 if z2_on else 0) + (150 if z1_on else 0)
            + (0.50 * sun if z2_blind else 0) + (0.40 * sun if z1_blind else 0) + shared,
        }
    raise ValueError(f"Unknown lab: {lab}")


def validate_file(path: Path, lab: str) -> list[str]:
    errors: list[str] = []
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
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
        "lab4": ("z1l && plug", "0.50 * sun", "0.40 * sun", "sp ? 150 : 0"),
        "lab4dual": ("z1l && plug1", "z2l && plug2", "0.40 * sun"),
        "lab4chain": ("z1l && plug && master", "0.40 * sun"),
        "lab5": ("z1eff || z1ineff", "z2eff || z2ineff", "0.40 * sun",
                 "(z1ineff ? 4 : 0)"),
        # Phase 1b fingerprints (must match the committed flows verbatim).
        "labrel": ("z1 = 25 + (z1l ? 400 : 0)",),
        "labrel8s": ("z1 = 25 + (z1l ? 400 : 0)",),
        "labband": ("daylight = (Z1Blinds ? 0.50 * Sunshine : 0)",
                    "daylight *= 0.25", "(strong ? 400 : 0)", "? 150 : 0"),
        "lab4chain3": ("z1l && plug && breaker",
                       "(lamp_effective ? 400 : 0)"),
    }
    # scenario unit -> list of flow files sharing that physics
    phase1b_flows = {
        "labrel": ["simulator_flow_labrel0.json", "simulator_flow_labrel4.json",
                   "simulator_flow_labrel8.json", "simulator_flow_labrel16.json"],
        "labrel8s": ["simulator_flow_labrel8s.json"],
        "labband": ["simulator_flow_labband.json"],
        "lab4chain3": ["simulator_flow_lab4chain3.json"],
    }
    for lab in ALL_LABS:
        if lab in PHASE1B_LABS:
            flow_files = [root / "simulator" / f for f in phase1b_flows[lab]]
        else:
            flow_files = [root / "simulator" / f"simulator_flow_{lab}.json"]
        for simulator in flow_files:
            simulator_text = simulator.read_text(encoding="utf-8")
            for token in simulator_tokens[lab]:
                if token not in simulator_text:
                    errors.append(
                        f"{simulator}: expected current physics token is missing: {token!r}")
        for prefix in ("scenarios", "train_scenarios"):
            errors.extend(validate_file(root / "benchmark" / f"{prefix}_{lab}.json", lab))
    dashboard = root / "dashboard" / "src" / "lib" / "physics.js"
    dashboard_text = dashboard.read_text(encoding="utf-8")
    dashboard_required = (
        "Z1 = 25 + (Z1Light ? 400 : 0)",
        "return { Z1: 25 + contrib(s.Z1Light, 400, f.Z1Light) }",
        "(Z2Light?100)",
        "(Z2Blinds?0.30·Sun)",
    )
    for token in dashboard_required:
        if token not in dashboard_text:
            errors.append(f"{dashboard}: expected current physics token is missing: {token!r}")
    for token in ("0.10·Sun", "0.10 * sun"):
        if token in dashboard_text:
            errors.append(f"{dashboard}: stale lab1 physics token {token!r}")
    return errors


def main() -> int:
    errors = validate_all()
    if errors:
        print("Phase-1 scenario validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Scenario/dashboard validation passed for labs "
          f"{', '.join(ALL_LABS)} (IDs unique; lux matches physics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
