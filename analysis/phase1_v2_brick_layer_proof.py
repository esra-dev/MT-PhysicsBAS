#!/usr/bin/env python3
"""Operational proof that the Elementary layer was off in the Brick-only arm.

Registered in THESIS_STATE_REPORT.md Addendum 2026-11-10 ("Operational proof
the Elementary layer was off"). The proof compares the initial Q-tables of the
``ql_true`` arm of the Brick-only run with those of the full-KG arm-C run.

Two table sources are used:

* the per-zone seed-1 tables published on the results branch (the form the
  registration names), supplied through ``--brick-zone-dir`` / ``--arm-c-zone-dir``;
* the combined (sum over zones) tables of all 20 seeds in the two archives.

The registration worded the criterion as "no -50 cell on any blind-ON column
at sun rank 0". Read literally that is not satisfiable by any arm: Rule 1
(redundancy, registry-derived, active in every knowledge arm) also writes -50
into a blind-ON cell whenever that blind is already open. The script therefore
reports the literal criterion AND the criterion restricted to states in which
the blind is closed, where a -50 can only come from the Elementary IV gate.
It also reports a wording-independent property: without an IV gate the
blind-ON columns cannot depend on the sun rank at all.

Output is deterministic (sorted keys, no timestamps).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

LAB_TTL = {
    "lab2": "src/resources/building_2_intermediate.ttl",
    "lab3": "src/resources/building_3_complex.ttl",
}
SLOT = re.compile(
    r"ws:stateVecIndex\s+(\d+)\s*;\s*ws:stateDomainSize\s+(\d+)\s*;"
    r"\s*ws:stateSlotRole\s+\"([a-z_]+)\"")
BONUS_VALUES = ("7.50", "15.00", "22.50")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _layout(repo: Path, lab: str) -> dict[str, object]:
    """State-slot layout from the lab KG (mixed radix, slot 0 most significant)."""
    slots: dict[int, tuple[int, str]] = {}
    for line in (repo / LAB_TTL[lab]).read_text(encoding="utf-8").splitlines():
        match = SLOT.search(line)
        if match:
            slots[int(match.group(1))] = (int(match.group(2)), match.group(3))
    if sorted(slots) != list(range(len(slots))):
        raise ValueError(f"{lab}: state slots are not contiguous: {sorted(slots)}")
    sizes = [slots[i][0] for i in range(len(slots))]
    strides = [0] * len(sizes)
    product = 1
    for index in range(len(sizes) - 1, -1, -1):
        strides[index] = product
        product *= sizes[index]
    sun = [i for i in slots if slots[i][1] == "sunshine"]
    if len(sun) != 1:
        raise ValueError(f"{lab}: expected exactly one sunshine slot")
    return {"sizes": sizes, "strides": strides, "sun_slot": sun[0],
            "n_states": product}


def _blind_bits(repo: Path, lab: str) -> dict[str, int]:
    """Column label -> state-vector slot of that blind, from the FULL golden."""
    bits: dict[str, int] = {}
    golden = repo / "config/golden_registry" / f"registry_{lab}.csv"
    for line in golden.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("key,"):
            continue
        cells = line.split(",")
        label, sv_bit = cells[1], int(cells[3])
        if label.endswith("Blinds=ON"):
            bits[label] = sv_bit
    return bits


def _digit(state: int, layout: dict[str, object], slot: int) -> int:
    return (state // layout["strides"][slot]) % layout["sizes"][slot]  # type: ignore[index]


def _load(path: Path) -> tuple[list[str], dict[int, list[str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return rows[0][1:], {int(row[0]): row[1:] for row in rows[1:]}


def _dist(values: list[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: counts[key] for key in sorted(counts, key=float)}


def _compare(columns: list[str], brick: dict[int, list[str]],
             arm_c: dict[int, list[str]], layout: dict[str, object],
             bits: dict[str, int], well: str) -> dict[str, object]:
    sun_slot = layout["sun_slot"]
    blind_cols = {j: label for j, label in enumerate(columns) if label in bits}
    diff_cols: Counter[str] = Counter()
    diff_sun: Counter[int] = Counter()
    arm_c_in_diff: list[str] = []
    brick_in_diff: list[str] = []
    for state in brick:
        for j, label in enumerate(columns):
            if brick[state][j] != arm_c[state][j]:
                diff_cols[label] += 1
                diff_sun[_digit(state, layout, sun_slot)] += 1
                arm_c_in_diff.append(arm_c[state][j])
                brick_in_diff.append(brick[state][j])

    closed_sun0_brick: list[str] = []
    closed_sun0_arm_c: list[str] = []
    open_sun0_same = True
    literal_minus_well = 0
    sun_invariant = True
    sun_stride = layout["strides"][sun_slot]  # type: ignore[index]
    for state in brick:
        sun = _digit(state, layout, sun_slot)
        for j, label in blind_cols.items():
            is_open = _digit(state, layout, bits[label]) == 1
            if sun == 0:
                if brick[state][j] == well:
                    literal_minus_well += 1
                if is_open:
                    open_sun0_same &= brick[state][j] == arm_c[state][j]
                else:
                    closed_sun0_brick.append(brick[state][j])
                    closed_sun0_arm_c.append(arm_c[state][j])
            base = state - sun * sun_stride
            sun_invariant &= brick[state][j] == brick[base + sun_stride][j]

    return {
        "differing_cells": sum(diff_cols.values()),
        "differing_cells_by_column": dict(sorted(diff_cols.items())),
        "differing_cells_by_sun_rank": {str(k): v for k, v in sorted(diff_sun.items())},
        "check_differences_only_on_blind_on_columns":
            set(diff_cols) <= set(bits),
        "check_differences_only_at_sun_rank_0": set(diff_sun) <= {0},
        "arm_c_values_in_differing_cells": _dist(arm_c_in_diff),
        "brick_values_in_differing_cells": _dist(brick_in_diff),
        "registered_literal_criterion": {
            "text": f"no {well} cell on any blind-ON column at sun rank 0",
            "brick_cells_equal_to_well": literal_minus_well,
            "holds": literal_minus_well == 0,
        },
        "restated_criterion_blind_closed": {
            "text": (f"no {well} cell on a blind-ON column at sun rank 0 in "
                     "states where that blind is closed (non-redundant)"),
            "brick_values": _dist(closed_sun0_brick),
            "arm_c_values": _dist(closed_sun0_arm_c),
            "holds": well not in closed_sun0_brick,
        },
        "check_blind_open_cells_identical_between_arms": open_sun0_same,
        "check_brick_has_rule5_bonus_values_blind_closed_sun0":
            all(value in closed_sun0_brick for value in BONUS_VALUES),
        "check_brick_blind_on_columns_do_not_depend_on_sun_rank": sun_invariant,
    }


def _archives(campaign: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for provenance in sorted(campaign.glob("*/analysis/out/workflow_inputs.json")):
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        found[payload["run_mode"]] = provenance.parents[2]
    return found


def build(repo: Path, campaign: Path, brick_zone_dir: Path,
          arm_c_zone_dir: Path) -> dict[str, object]:
    archives = _archives(campaign)
    brick_root = archives["phase1_v2_brick_only"]
    arm_c_root = archives["phase1_v2_kg_only"]
    report: dict[str, object] = {
        "registration": "THESIS_STATE_REPORT.md Addendum 2026-11-10",
        "brick_archive": brick_root.name,
        "arm_c_archive": arm_c_root.name,
        "labs": {},
    }
    all_ok = True
    for lab in ("lab2", "lab3"):
        layout = _layout(repo, lab)
        bits = _blind_bits(repo, lab)
        name = f"qtable_initial_stereotypes_true_{lab}"
        entry: dict[str, object] = {
            "state_layout": layout,
            "check_sunshine_is_least_significant_slot":
                layout["strides"][layout["sun_slot"]] == 1,  # type: ignore[index]
            "blind_on_columns": bits,
        }

        # Combined tables of every seed in both archives.
        hashes = {"brick": set(), "arm_c": set()}
        for arm, root in (("brick", brick_root), ("arm_c", arm_c_root)):
            for path in sorted(root.glob(
                    f"benchmark/results_seed*/{lab}/training_stereo_true/{name}.csv")):
                hashes[arm].add(_sha256(path))
        seed1 = f"benchmark/results_seed1/{lab}/training_stereo_true/{name}.csv"
        columns, brick_combined = _load(brick_root / seed1)
        columns_c, arm_c_combined = _load(arm_c_root / seed1)
        if columns != columns_c or brick_combined.keys() != arm_c_combined.keys():
            raise ValueError(f"{lab}: combined tables are not aligned")
        entry["combined_tables_all_seeds"] = {
            "brick_sha256": sorted(hashes["brick"]),
            "arm_c_sha256": sorted(hashes["arm_c"]),
            "check_identical_across_20_seeds":
                len(hashes["brick"]) == 1 and len(hashes["arm_c"]) == 1,
            "comparison": _compare(columns, brick_combined, arm_c_combined,
                                   layout, bits, "-100.00"),
        }

        # Per-zone seed-1 tables (the form the registration names).
        zones: dict[str, object] = {}
        zone_sum_ok = True
        sums = {"brick": {s: [0.0] * len(columns) for s in brick_combined},
                "arm_c": {s: [0.0] * len(columns) for s in brick_combined}}
        for zone in ("zone1", "zone2"):
            brick_path = brick_zone_dir / f"{name}_{zone}.csv"
            arm_c_path = arm_c_zone_dir / f"{name}_{zone}.csv"
            zone_columns, brick_zone = _load(brick_path)
            _, arm_c_zone = _load(arm_c_path)
            if zone_columns != columns:
                raise ValueError(f"{lab} {zone}: column mismatch")
            for state in brick_zone:
                for j in range(len(columns)):
                    sums["brick"][state][j] += float(brick_zone[state][j])
                    sums["arm_c"][state][j] += float(arm_c_zone[state][j])
            zones[zone] = {
                "brick_sha256": _sha256(brick_path),
                "arm_c_sha256": _sha256(arm_c_path),
                "comparison": _compare(columns, brick_zone, arm_c_zone,
                                       layout, bits, "-50.00"),
            }
        for arm, combined in (("brick", brick_combined), ("arm_c", arm_c_combined)):
            for state in combined:
                for j in range(len(columns)):
                    zone_sum_ok &= abs(sums[arm][state][j] - float(combined[state][j])) < 0.005
        entry["per_zone_tables_seed1"] = zones
        entry["check_zone_tables_sum_to_archived_seed1_combined_table"] = zone_sum_ok

        checks = [entry["check_sunshine_is_least_significant_slot"],
                  entry["combined_tables_all_seeds"]["check_identical_across_20_seeds"],  # type: ignore[index]
                  zone_sum_ok]
        for comparison in ([entry["combined_tables_all_seeds"]["comparison"]]  # type: ignore[index]
                           + [zones[z]["comparison"] for z in zones]):  # type: ignore[index]
            checks += [
                comparison["check_differences_only_on_blind_on_columns"],
                comparison["check_differences_only_at_sun_rank_0"],
                comparison["restated_criterion_blind_closed"]["holds"],
                comparison["check_blind_open_cells_identical_between_arms"],
                comparison["check_brick_blind_on_columns_do_not_depend_on_sun_rank"],
            ]
        entry["all_checks_pass"] = all(checks)
        all_ok &= entry["all_checks_pass"]
        report["labs"][lab] = entry  # type: ignore[index]
    report["elementary_layer_off"] = all_ok
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--brick-zone-dir", type=Path, required=True)
    parser.add_argument("--arm-c-zone-dir", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.repo, args.campaign, args.brick_zone_dir, args.arm_c_zone_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"elementary_layer_off={report['elementary_layer_off']} -> {args.out}")
    return 0 if report["elementary_layer_off"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
