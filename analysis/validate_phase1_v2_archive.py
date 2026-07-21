#!/usr/bin/env python3
"""Validate corrected Phase-1 per-seed data before inference or publication."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


LABS = ("lab1", "lab2", "lab3")
STEREOS = ("true", "false")
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def _data_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if row and not next(iter(row.values()), "").startswith("#")]


def validate(root: Path, expected_seeds: range = range(1, 21)) -> list[str]:
    errors: list[str] = []
    for seed in expected_seeds:
        seed_root = root / "benchmark" / f"results_seed{seed}"
        if not seed_root.is_dir():
            errors.append(f"missing seed root: {seed_root}")
            continue
        for lab in LABS:
            manifests: dict[str, dict] = {}
            first_goal_rows: dict[str, list[tuple[int, int]]] = {}
            for stereo in STEREOS:
                cell = seed_root / lab / f"training_stereo_{stereo}"
                manifest_path = cell / "TRAINING_OK.json"
                if not manifest_path.is_file():
                    errors.append(f"missing manifest: {manifest_path}")
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                manifests[stereo] = manifest
                for key, expected in (
                    ("protocol_version", "phase1-v2"),
                    ("fixed_horizon_episodes", 3000),
                    ("paired_rng_version", "common-seed-v1"),
                    ("metric_schema", "phase1-benchmark-v2"),
                    ("scenario_fallback_count", 0),
                ):
                    if manifest.get(key) != expected:
                        errors.append(f"{manifest_path}: {key}={manifest.get(key)!r}, expected {expected!r}")

                suffix = f"_{lab}"
                metrics = cell / f"metrics_stereotypes_{stereo}{suffix}.csv"
                if not metrics.is_file():
                    errors.append(f"missing metrics: {metrics}")
                else:
                    rows = _data_rows(metrics)
                    if len(rows) != 3000:
                        errors.append(f"{metrics}: {len(rows)} episodes, expected 3000")
                    if rows and "ScenarioId" not in rows[0]:
                        errors.append(f"{metrics}: missing ScenarioId")
                    declared = [int(value) for value in manifest.get("ordered_scenario_ids", [])]
                    if rows and declared:
                        actual_cycle = [int(row["ScenarioId"]) for row in rows]
                        expected_cycle = [declared[index % len(declared)]
                                          for index in range(len(rows))]
                        if actual_cycle != expected_cycle:
                            errors.append(f"{metrics}: scenario sequence is not the declared ordered cycle")
                    if manifest.get("run_seed") != seed:
                        errors.append(
                            f"{manifest_path}: run_seed={manifest.get('run_seed')!r}, expected {seed}")

                first_goal = cell / f"first_goal_stereotypes_{stereo}{suffix}.csv"
                if not first_goal.is_file():
                    errors.append(f"missing first-goal file: {first_goal}")
                else:
                    rows = _data_rows(first_goal)
                    declared = [int(value) for value in manifest.get("ordered_scenario_ids", [])]
                    ids = [int(row["ScenarioId"]) for row in rows]
                    presentations = [int(row["Presentations"]) for row in rows]
                    first_goal_rows[stereo] = list(zip(ids, presentations))
                    if ids != declared:
                        errors.append(f"{first_goal}: rows {ids} != declared {declared}")
                    expected_presentations = [
                        3000 // len(declared) + (1 if index < 3000 % len(declared) else 0)
                        for index in range(len(declared))
                    ] if declared else []
                    if presentations != expected_presentations:
                        errors.append(
                            f"{first_goal}: presentations {presentations} != expected {expected_presentations}")
                    if any(row.get("ProtocolVersion") != "phase1-v2" for row in rows):
                        errors.append(f"{first_goal}: non-v2 row")

            if set(manifests) == set(STEREOS):
                if manifests["true"].get("scenario_schedule_sha256") != \
                        manifests["false"].get("scenario_schedule_sha256"):
                    errors.append(f"{seed_root}/{lab}: scenario schedule hashes differ between arms")
            if set(first_goal_rows) == set(STEREOS) and \
                    first_goal_rows["true"] != first_goal_rows["false"]:
                errors.append(f"{seed_root}/{lab}: first-goal scenario rows differ between arms")

            benchmark_catalog = json.loads(
                (SOURCE_ROOT / "benchmark" / f"scenarios_{lab}.json").read_text(
                    encoding="utf-8"))
            benchmark_ids = [int(row["id"]) for row in benchmark_catalog]
            for mode in ("rule_based", "ql_false", "ql_true"):
                bench = seed_root / lab / mode / f"benchmark_results_{mode}.csv"
                if not bench.is_file():
                    errors.append(f"missing benchmark: {bench}")
                    continue
                rows = _data_rows(bench)
                required = {"MetricSchema", "PolicyEnergyCost", "LegacyWallClockTotalEnergyCost"}
                if rows and not required.issubset(rows[0]):
                    errors.append(f"{bench}: missing v2 columns {sorted(required - set(rows[0]))}")
                if any(row.get("MetricSchema") != "phase1-benchmark-v2" for row in rows):
                    errors.append(f"{bench}: non-v2 metric row")
                expected_pairs = {(scenario_id, run_id)
                                  for scenario_id in benchmark_ids for run_id in range(1, 6)}
                actual_pairs = {(int(row["ScenarioId"]), int(row["RunId"])) for row in rows}
                if len(rows) != len(expected_pairs) or actual_pairs != expected_pairs:
                    errors.append(f"{bench}: scenario/run rows do not equal declared IDs x runs 1..5")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("Phase-1 v2 archive validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Phase-1 v2 archive validation passed (20 seeds × 3 labs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
