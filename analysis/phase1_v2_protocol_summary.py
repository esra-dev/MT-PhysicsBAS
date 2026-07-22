#!/usr/bin/env python3
"""Summarize corrected archive completion gates without recomputing outcomes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def summarize_run(root: Path) -> dict:
    provenance = json.loads(
        (root / "analysis/out/workflow_inputs.json").read_text(encoding="utf-8")
    )
    manifests: dict[tuple[int, str, str], dict] = {}
    censored = 0
    terminal_scenarios = 0
    first_goal_rows = 0
    for path in root.glob(
            "benchmark/results_seed*/lab*/training_stereo_*/TRAINING_OK.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        seed = int(payload["run_seed"])
        profile = payload["profile"]
        stereo = str(payload["stereotype"]).lower()
        manifests[(seed, profile, stereo)] = payload
        first_goal = path.parent / f"first_goal_stereotypes_{stereo}_{profile}.csv"
        with first_goal.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if (not row.get("ScenarioId") or
                        (row.get("ProtocolVersion") or "").startswith("#")):
                    continue
                first_goal_rows += 1
                censored += int(row["Censored"].lower() == "true")
                terminal_scenarios += int(int(row["TerminalAtStartPresentations"]) > 0)

    expected_keys = {
        (seed, profile, stereo)
        for seed in range(1, 21)
        for profile in ("lab1", "lab2", "lab3")
        for stereo in ("true", "false")
    }
    if set(manifests) != expected_keys:
        raise ValueError(f"training cell set mismatch in {root}")
    pair_mismatches = 0
    for seed in range(1, 21):
        for profile in ("lab1", "lab2", "lab3"):
            on = manifests[(seed, profile, "true")]
            off = manifests[(seed, profile, "false")]
            if (on["ordered_scenario_ids"] != off["ordered_scenario_ids"] or
                    on["scenario_schedule_sha256"] != off["scenario_schedule_sha256"]):
                pair_mismatches += 1

    benchmark_files = list(root.glob(
        "benchmark/results_seed*/lab*/*/benchmark_results_*.csv"))
    return {
        "run_id": provenance["run_id"],
        "run_mode": provenance["run_mode"],
        "head_sha": provenance["head_sha"],
        "training_cells": len(manifests),
        "benchmark_cells": len(benchmark_files),
        "fixed_horizons": sorted({m["fixed_horizon_episodes"] for m in manifests.values()}),
        "protocol_versions": sorted({m["protocol_version"] for m in manifests.values()}),
        "metric_schemas": sorted({m["metric_schema"] for m in manifests.values()}),
        "paired_rng_versions": sorted({m["paired_rng_version"] for m in manifests.values()}),
        "scenario_fallback_count": sum(m["scenario_fallback_count"] for m in manifests.values()),
        "schedule_pair_mismatches": pair_mismatches,
        "first_goal_rows": first_goal_rows,
        "first_goal_censored_rows": censored,
        "first_goal_terminal_at_start_rows": terminal_scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summaries = [summarize_run(path) for path in sorted(args.campaign.glob("run_*"))]
    payload = {
        "protocol_version": "phase1-v2",
        "all_gates_pass": all(
            item["training_cells"] == 120
            and item["benchmark_cells"] == 180
            and item["fixed_horizons"] == [3000]
            and item["protocol_versions"] == ["phase1-v2"]
            and item["metric_schemas"] == ["phase1-benchmark-v2"]
            and item["paired_rng_versions"] == ["common-seed-v1"]
            and item["scenario_fallback_count"] == 0
            and item["schedule_pair_mismatches"] == 0
            for item in summaries
        ),
        "runs": summaries,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(f"Wrote protocol gate summary for {len(summaries)} runs; pass={payload['all_gates_pass']}")
    return 0 if payload["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
