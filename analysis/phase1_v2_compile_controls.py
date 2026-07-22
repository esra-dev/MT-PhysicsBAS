#!/usr/bin/env python3
"""Compile all corrected within-mode controls/descriptives with source run IDs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _discover(campaign: Path) -> dict[str, tuple[int, Path]]:
    found: dict[str, tuple[int, Path]] = {}
    for provenance in campaign.glob("run_*/analysis/out/workflow_inputs.json"):
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        found[payload["run_mode"]] = (int(payload["run_id"]), provenance.parents[2])
    expected = {
        "phase1_v2_kg_only", "phase1_v2_redundancy_only",
        "phase1_v2_baseline", "phase1_v2_pbrs_only",
    }
    if set(found) != expected:
        raise ValueError(f"mode set differs: {sorted(found)}")
    return found


def _classification(mode: str, profile: str, metric: str, domain: str) -> str:
    primary = {
        ("phase1_v2_kg_only", "lab2", "auc_goal", "training"),
        ("phase1_v2_redundancy_only", "lab2", "auc_goal", "training"),
        ("phase1_v2_kg_only", "lab3", "mean_first_goal_presentations", "training"),
        ("phase1_v2_kg_only", "lab3", "avg_cycling", "benchmark"),
    }
    if (mode, profile, metric, domain) in primary:
        return "registered_primary_member"
    if mode in {"phase1_v2_baseline", "phase1_v2_pbrs_only"}:
        return "registered_control"
    if metric == "avg_legacy_wallclock_energy":
        return "legacy_diagnostic_not_evidence"
    return "registered_descriptive"


def compile_controls(campaign: Path, output: Path) -> int:
    rows: list[dict[str, str | int]] = []
    for mode, (run_id, root) in sorted(_discover(campaign).items()):
        analysis = root / "analysis" / "out"
        with (analysis / "learning_speed_tests.csv").open(
                encoding="utf-8", newline="") as handle:
            for source in csv.DictReader(handle):
                rows.append({
                    "source_run_id": run_id,
                    "run_mode": mode,
                    "domain": "training",
                    "profile": source["profile"],
                    "metric": source["metric"],
                    "contrast": "ql_true_minus_ql_false",
                    "classification": _classification(
                        mode, source["profile"], source["metric"], "training"),
                    "n_paired": source["n_paired"],
                    "mean_difference": source["mean_diff_true_minus_false"],
                    "median_difference": source["median_diff_true_minus_false"],
                    "ci_lo_bootstrap": source["ci_lo"],
                    "ci_hi_bootstrap": source["ci_hi"],
                    "p_signflip_two_sided": source["p_signflip_two_sided"],
                    "p_sign_exact_two_sided": source["p_sign_exact_two_sided"],
                    "paired_rank_biserial": source["paired_rank_biserial"],
                    "context_q": source["q_signflip_bh"],
                    "context_family_m": source["bh_family_m"],
                })
        with (analysis / "paired_tests.csv").open(
                encoding="utf-8", newline="") as handle:
            for source in csv.DictReader(handle):
                if source["mode_a"] != "ql_true" or source["mode_b"] != "ql_false":
                    continue
                rows.append({
                    "source_run_id": run_id,
                    "run_mode": mode,
                    "domain": "benchmark",
                    "profile": source["profile"],
                    "metric": source["metric"],
                    "contrast": "ql_true_minus_ql_false",
                    "classification": _classification(
                        mode, source["profile"], source["metric"], "benchmark"),
                    "n_paired": source["n_paired"],
                    "mean_difference": source["mean_diff"],
                    "median_difference": source["median_diff"],
                    "ci_lo_bootstrap": source["ci_lo"],
                    "ci_hi_bootstrap": source["ci_hi"],
                    "p_signflip_two_sided": source["p_signflip_two_sided"],
                    "p_sign_exact_two_sided": source["p_sign_exact_two_sided"],
                    "paired_rank_biserial": source["paired_rank_biserial"],
                    "context_q": source["q_signflip_bh"],
                    "context_family_m": source["bh_family_m"],
                })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    count = compile_controls(args.campaign, args.out)
    print(f"Wrote {count} corrected control/descriptive rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
