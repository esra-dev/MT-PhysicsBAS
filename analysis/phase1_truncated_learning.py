#!/usr/bin/env python3
"""Retrospective truncated-curve analysis for Phase-1/Phase-1b trajectories.

This module deliberately does not run or configure a learner. It reads the
immutable 3,000-episode metric files, validates their hashes against the
committed archive inventories, and summarizes pre-specified episode prefixes.
The output is exploratory and cannot alter a registered campaign verdict.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EXPECTED_SEEDS = tuple(range(1, 21))


@dataclass(frozen=True)
class EpisodeMetrics:
    goals: tuple[int, ...]
    scenario_ids: tuple[str, ...]


@dataclass(frozen=True)
class SourceFile:
    campaign: str
    mode: str
    run_id: str
    seed: int
    profile: str
    arm: str
    path: Path
    relative_inventory_path: str
    size: int
    sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _float_text(value: float | None) -> str:
    if value is None:
        return ""
    if not math.isfinite(value):
        raise ValueError(f"refusing to serialize non-finite value: {value}")
    if value == 0:
        return "0"
    return format(value, ".12g")


def _quantile_linear(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    h = (len(ordered) - 1) * probability
    lower = math.floor(h)
    upper = math.ceil(h)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (h - lower) * (ordered[upper] - ordered[lower])


def bootstrap_mean_interval(
    values: Iterable[float], *, iterations: int, seed: int
) -> tuple[float, float]:
    data = tuple(float(v) for v in values)
    if not data:
        raise ValueError("bootstrap requires at least one value")
    rng = random.Random(seed)
    n = len(data)
    means = [sum(data[rng.randrange(n)] for _ in range(n)) / n
             for _ in range(iterations)]
    return _quantile_linear(means, 0.025), _quantile_linear(means, 0.975)


def stable_bootstrap_seed(base_seed: int, *labels: object) -> int:
    material = "\x1f".join([str(base_seed), *(str(label) for label in labels)])
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")


def read_episode_metrics(path: Path, horizon: int) -> EpisodeMetrics:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Episode", "GoalReached", "ScenarioId"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        goals: list[int] = []
        scenarios: list[str] = []
        for expected_episode, row in enumerate(reader):
            episode_text = str(row.get("Episode", "")).strip()
            # QLearner appends a human-readable "# Summary" footer after the
            # fixed episode rows. It is not part of the trajectory.
            if episode_text.startswith("#"):
                if len(goals) != horizon:
                    raise ValueError(
                        f"{path}: summary footer after {len(goals)} rows; "
                        f"expected {horizon}"
                    )
                break
            try:
                episode = int(episode_text)
                goal = int(row["GoalReached"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}: invalid episode/goal row {row}") from exc
            if episode != expected_episode:
                raise ValueError(
                    f"{path}: expected contiguous Episode={expected_episode}, got {episode}"
                )
            if goal not in (0, 1):
                raise ValueError(f"{path}: GoalReached must be 0/1, got {goal}")
            goals.append(goal)
            scenarios.append(str(row["ScenarioId"]).strip())
    if len(goals) != horizon:
        raise ValueError(f"{path}: expected {horizon} rows, got {len(goals)}")
    if any(not scenario for scenario in scenarios):
        raise ValueError(f"{path}: empty ScenarioId")
    return EpisodeMetrics(tuple(goals), tuple(scenarios))


def prefix_auc(metrics: EpisodeMetrics, budget: int, scenario_count: int) -> float:
    if budget <= 0 or budget > len(metrics.goals):
        raise ValueError(f"budget {budget} outside 1..{len(metrics.goals)}")
    prefix_scenarios = metrics.scenario_ids[:budget]
    counts: dict[str, int] = {}
    for scenario in prefix_scenarios:
        counts[scenario] = counts.get(scenario, 0) + 1
    # The source campaigns use deterministic cyclic scenario schedules. Some
    # profiles (notably Lab 2 with 11 scenarios) do not divide either the
    # selected prefixes or the fixed 3,000-episode horizon exactly. Retain the
    # intended budgets while requiring the strongest possible cyclic balance:
    # every scenario occurs and counts differ by at most one.
    spread = max(counts.values()) - min(counts.values()) if counts else 0
    if len(counts) != scenario_count or spread > 1:
        raise ValueError(
            f"budget {budget} does not contain a near-balanced "
            f"{scenario_count}-scenario cyclic prefix: "
            f"{counts}"
        )
    return sum(metrics.goals[:budget]) / budget


def trailing_training_goal_rate(
    metrics: EpisodeMetrics, budget: int, window: int
) -> float:
    if budget <= 0 or budget > len(metrics.goals):
        raise ValueError(f"budget {budget} outside 1..{len(metrics.goals)}")
    if window <= 0 or window > budget:
        raise ValueError(f"window {window} outside 1..{budget}")
    return sum(metrics.goals[budget - window:budget]) / window


def endpoint_value(
    metrics: EpisodeMetrics, endpoint: dict[str, Any], budget: int,
    scenario_count: int,
) -> float:
    name = str(endpoint["name"])
    if name == "prefix_auc_goal":
        return prefix_auc(metrics, budget, scenario_count)
    if name == "trailing_training_goal_rate":
        return trailing_training_goal_rate(metrics, budget, int(endpoint["window"]))
    raise ValueError(f"unknown endpoint {name}")


def _read_inventory(path: Path) -> dict[str, tuple[int, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"path", "bytes", "sha256"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"{path}: invalid inventory header")
        rows: dict[str, tuple[int, str]] = {}
        for row in reader:
            key = str(row["path"]).replace("\\", "/")
            rows[key] = (int(row["bytes"]), str(row["sha256"]).lower())
    return rows


class InputResolver:
    def __init__(
        self,
        spec: dict[str, Any],
        campaign_roots: dict[str, Path],
        inventory_roots: dict[str, Path],
    ) -> None:
        self.spec = spec
        self.campaign_roots = campaign_roots
        self.inventory_roots = inventory_roots
        self._inventories: dict[tuple[str, str], dict[str, tuple[int, str]]] = {}
        self._metrics_cache: dict[tuple[str, str, int, str, str], EpisodeMetrics] = {}
        self.source_files: dict[Path, SourceFile] = {}

    def _run_spec(self, campaign: str, mode: str, seed: int) -> dict[str, Any]:
        runs = self.spec["campaigns"][campaign]["runs"].get(mode)
        if not runs:
            raise ValueError(f"no run mapping for {campaign}/{mode}")
        matches = [run for run in runs if int(run["seeds"][0]) <= seed <= int(run["seeds"][1])]
        if len(matches) != 1:
            raise ValueError(f"expected one run for {campaign}/{mode}/seed{seed}, got {matches}")
        return matches[0]

    def _inventory(
        self, campaign: str, run_id: str
    ) -> tuple[dict[str, tuple[int, str]], str]:
        campaign_spec = self.spec["campaigns"][campaign]
        style = campaign_spec["inventory_style"]
        key = (campaign, run_id if style == "per_run" else "campaign")
        if key not in self._inventories:
            root = self.inventory_roots[campaign]
            if style == "campaign":
                inventory_path = root / campaign_spec["inventory"]
            elif style == "per_run":
                inventory_path = root / f"run_{run_id}" / campaign_spec["inventory"]
            else:
                raise ValueError(f"unknown inventory style: {style}")
            self._inventories[key] = _read_inventory(inventory_path)
        prefix = f"run_{run_id}/" if style == "campaign" else ""
        return self._inventories[key], prefix

    def resolve(
        self, campaign: str, mode: str, seed: int, profile: str, arm: str
    ) -> EpisodeMetrics:
        cache_key = (campaign, mode, seed, profile, arm)
        if cache_key in self._metrics_cache:
            return self._metrics_cache[cache_key]
        run_spec = self._run_spec(campaign, mode, seed)
        run_id = str(run_spec["run_id"])
        relative = (
            Path("benchmark") / f"results_seed{seed}" / profile
            / f"training_stereo_{arm}" / f"metrics_stereotypes_{arm}_{profile}.csv"
        )
        run_root = self.campaign_roots[campaign] / f"run_{run_id}"
        path = run_root / relative
        if not path.is_file():
            raise FileNotFoundError(
                f"missing raw metric file {path}; download the Phase-1b inputs first"
            )

        inventory, prefix = self._inventory(campaign, run_id)
        inventory_key = prefix + relative.as_posix()
        if inventory_key not in inventory:
            raise ValueError(f"{path}: absent from committed inventory ({inventory_key})")
        expected_size, expected_hash = inventory[inventory_key]
        actual_size = path.stat().st_size
        actual_hash = _sha256(path)
        if (actual_size, actual_hash) != (expected_size, expected_hash):
            raise ValueError(
                f"{path}: inventory mismatch; expected {expected_size}/{expected_hash}, "
                f"got {actual_size}/{actual_hash}"
            )

        marker = (
            run_root / "benchmark" / f"results_seed{seed}" / profile
            / f"training_stereo_{arm}" / "TRAINING_OK.json"
        )
        marker_data = json.loads(marker.read_text(encoding="utf-8-sig"))
        expected_marker = {
            "status": "ok",
            "profile": profile,
            "stereotype": arm,
            "run_seed": seed,
            "run_mode": mode,
            "fixed_horizon_episodes": int(self.spec["training_horizon"]),
        }
        for field, expected in expected_marker.items():
            actual = marker_data.get(field)
            if str(actual).lower() != str(expected).lower():
                raise ValueError(
                    f"{marker}: {field} expected {expected!r}, got {actual!r}"
                )

        metrics = read_episode_metrics(path, int(self.spec["training_horizon"]))
        self._metrics_cache[cache_key] = metrics
        self.source_files[path] = SourceFile(
            campaign=campaign,
            mode=mode,
            run_id=run_id,
            seed=seed,
            profile=profile,
            arm=arm,
            path=path,
            relative_inventory_path=inventory_key,
            size=actual_size,
            sha256=actual_hash,
        )
        return metrics


def _direct_seed_rows(
    spec: dict[str, Any], resolver: InputResolver
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    budgets = [int(v) for v in spec["budgets"]]
    endpoints = list(spec["endpoints"])
    for profile, profile_spec in spec["profiles"].items():
        campaign = profile_spec["campaign"]
        scenario_count = int(profile_spec["scenario_count"])
        for contrast, contrast_spec in profile_spec["direct_contrasts"].items():
            for seed in EXPECTED_SEEDS:
                left_ref = contrast_spec["left"]
                right_ref = contrast_spec["right"]
                left = resolver.resolve(
                    campaign, left_ref["mode"], seed, profile, left_ref["arm"]
                )
                right = resolver.resolve(
                    campaign, right_ref["mode"], seed, profile, right_ref["arm"]
                )
                if left.scenario_ids != right.scenario_ids:
                    raise ValueError(
                        f"{profile}/{contrast}/seed{seed}: paired arms do not use "
                        "the same scenario sequence"
                    )
                for endpoint in endpoints:
                    for budget in budgets:
                        left_value = endpoint_value(
                            left, endpoint, budget, scenario_count
                        )
                        right_value = endpoint_value(
                            right, endpoint, budget, scenario_count
                        )
                        rows.append({
                            "profile": profile,
                            "contrast": contrast,
                            "endpoint": endpoint["name"],
                            "budget": budget,
                            "seed": seed,
                            "left_value": left_value,
                            "right_value": right_value,
                            "paired_difference": left_value - right_value,
                        })
    return rows


def add_derived_rows(spec: dict[str, Any], direct_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    derived = spec["derived_contrast"]
    by_key = {
        (row["profile"], row["contrast"], row["endpoint"], row["budget"], row["seed"]): row
        for row in direct_rows
    }
    out = list(direct_rows)
    for profile in spec["profiles"]:
        for endpoint in spec["endpoints"]:
            endpoint_name = endpoint["name"]
            for budget in spec["budgets"]:
                for seed in EXPECTED_SEEDS:
                    left = by_key[(
                        profile, derived["left"], endpoint_name, budget, seed
                    )]
                    right = by_key[(
                        profile, derived["right"], endpoint_name, budget, seed
                    )]
                    out.append({
                        "profile": profile,
                        "contrast": derived["name"],
                        "endpoint": endpoint_name,
                        "budget": budget,
                        "seed": seed,
                        "left_value": left["paired_difference"],
                        "right_value": right["paired_difference"],
                        "paired_difference": (
                            left["paired_difference"] - right["paired_difference"]
                        ),
                    })
    return sorted(out, key=lambda r: (
        r["profile"], r["contrast"], r["endpoint"], r["budget"], r["seed"]
    ))


def summarize_rows(spec: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((
            row["profile"], row["contrast"], row["endpoint"], row["budget"]
        ), []).append(row)
    bootstrap = spec["bootstrap"]
    reference = float(spec["historical_auc_reference"]["value"])
    summaries: list[dict[str, Any]] = []
    for (profile, contrast, endpoint, budget), group in sorted(groups.items()):
        if sorted(int(row["seed"]) for row in group) != list(EXPECTED_SEEDS):
            raise ValueError(f"incomplete seed group: {profile}/{contrast}/{budget}")
        diffs = [float(row["paired_difference"]) for row in group]
        ci_lo, ci_hi = bootstrap_mean_interval(
            diffs,
            iterations=int(bootstrap["iterations"]),
            seed=stable_bootstrap_seed(
                int(bootstrap["base_seed"]), profile, contrast, endpoint, budget
            ),
        )
        has_reference = contrast == "kg_vs_baseline" and endpoint == "prefix_auc_goal"
        summaries.append({
            "profile": profile,
            "contrast": contrast,
            "endpoint": endpoint,
            "budget": budget,
            "n_paired": len(group),
            "mean_left_value": sum(float(row["left_value"]) for row in group) / len(group),
            "mean_right_value": sum(float(row["right_value"]) for row in group) / len(group),
            "mean_paired_difference": sum(diffs) / len(diffs),
            "mean_cumulative_excess_goals": (
                budget * sum(diffs) / len(diffs)
                if endpoint == "prefix_auc_goal" else None
            ),
            "median_paired_difference": _quantile_linear(diffs, 0.5),
            "bootstrap_ci_low_descriptive": ci_lo,
            "bootstrap_ci_high_descriptive": ci_hi,
            "positive_seed_count": sum(value > 0 for value in diffs),
            "zero_seed_count": sum(value == 0 for value in diffs),
            "negative_seed_count": sum(value < 0 for value in diffs),
            "historical_auc_reference": reference if has_reference else None,
            "mean_crosses_historical_reference": (
                (sum(diffs) / len(diffs)) >= reference if has_reference else None
            ),
        })
    return summaries


def assess_profiles(spec: dict[str, Any], summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in summaries:
        if row["endpoint"] != "prefix_auc_goal":
            continue
        groups.setdefault((row["profile"], row["contrast"]), []).append(row)
    horizon = int(spec["training_horizon"])
    assessments: list[dict[str, Any]] = []
    for (profile, contrast), group in sorted(groups.items()):
        ordered = sorted(group, key=lambda row: int(row["budget"]))
        short = [row for row in ordered if int(row["budget"]) < horizon]
        full = next(row for row in ordered if int(row["budget"]) == horizon)
        max_short = max(short, key=lambda row: float(row["mean_paired_difference"]))
        descriptive_positive = [
            str(row["budget"]) for row in short
            if float(row["bootstrap_ci_low_descriptive"]) > 0
        ]
        reference_crossings = [
            str(row["budget"]) for row in short
            if row["mean_crosses_historical_reference"] is True
        ]
        means = [float(row["mean_paired_difference"]) for row in ordered]
        monotone = all(means[i] >= means[i + 1] - 1e-15 for i in range(len(means) - 1))
        if contrast == "kg_vs_baseline" and reference_crossings:
            signal = "plausible_short_budget_signal_above_historical_anchor"
        elif descriptive_positive and float(max_short["mean_paired_difference"]) > float(full["mean_paired_difference"]):
            signal = "plausible_positive_short_budget_signal_below_reference"
        else:
            signal = "no_clear_positive_short_budget_signal"
        assessments.append({
            "profile": profile,
            "contrast": contrast,
            "assessment_endpoint": "prefix_auc_goal",
            "shortest_budget": int(ordered[0]["budget"]),
            "shortest_budget_mean_difference": float(ordered[0]["mean_paired_difference"]),
            "max_short_budget": int(max_short["budget"]),
            "max_short_budget_mean_difference": float(max_short["mean_paired_difference"]),
            "full_horizon_mean_difference": float(full["mean_paired_difference"]),
            "mean_curve_monotone_nonincreasing": monotone,
            "short_budgets_with_descriptive_ci_above_zero": ";".join(descriptive_positive),
            "short_budgets_crossing_historical_reference": ";".join(reference_crossings),
            "screening_label": signal,
        })
    return assessments


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: (
                    _float_text(row.get(field))
                    if isinstance(row.get(field), float) or row.get(field) is None
                    else str(row.get(field)).lower()
                    if isinstance(row.get(field), bool)
                    else row.get(field, "")
                )
                for field in fields
            })


def _write_outputs(
    spec: dict[str, Any], spec_path: Path, out: Path, resolver: InputResolver,
    seed_rows: list[dict[str, Any]], summaries: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "prefix_seed_differences.csv", seed_rows, [
        "profile", "contrast", "endpoint", "budget", "seed", "left_value", "right_value",
        "paired_difference",
    ])
    _write_csv(out / "prefix_summary.csv", summaries, [
        "profile", "contrast", "endpoint", "budget", "n_paired", "mean_left_value",
        "mean_right_value", "mean_paired_difference", "mean_cumulative_excess_goals",
        "median_paired_difference",
        "bootstrap_ci_low_descriptive", "bootstrap_ci_high_descriptive",
        "positive_seed_count", "zero_seed_count", "negative_seed_count",
        "historical_auc_reference", "mean_crosses_historical_reference",
    ])
    _write_csv(out / "profile_assessment.csv", assessments, [
        "profile", "contrast", "assessment_endpoint", "shortest_budget", "shortest_budget_mean_difference",
        "max_short_budget", "max_short_budget_mean_difference",
        "full_horizon_mean_difference", "mean_curve_monotone_nonincreasing",
        "short_budgets_with_descriptive_ci_above_zero",
        "short_budgets_crossing_historical_reference", "screening_label",
    ])
    source_rows = [
        {
            "campaign": source.campaign,
            "mode": source.mode,
            "run_id": source.run_id,
            "seed": source.seed,
            "profile": source.profile,
            "arm": source.arm,
            "inventory_path": source.relative_inventory_path,
            "bytes": source.size,
            "sha256": source.sha256,
        }
        for source in sorted(
            resolver.source_files.values(),
            key=lambda s: (s.campaign, s.mode, s.seed, s.profile, s.arm),
        )
    ]
    _write_csv(out / "input_file_manifest.csv", source_rows, [
        "campaign", "mode", "run_id", "seed", "profile", "arm",
        "inventory_path", "bytes", "sha256",
    ])
    metadata = {
        "analysis_version": spec["version"],
        "classification": spec["classification"],
        "spec_sha256": _sha256(spec_path),
        "training_horizon": spec["training_horizon"],
        "budgets": spec["budgets"],
        "endpoints": spec["endpoints"],
        "estimand": spec["estimand"],
        "limitations": spec["limitations"],
        "historical_auc_reference": spec["historical_auc_reference"],
        "input_file_count": len(source_rows),
        "seed_row_count": len(seed_rows),
        "summary_row_count": len(summaries),
        "new_training_runs": 0,
        "registered_outputs_modified": False,
    }
    (out / "analysis_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    inventory_rows = []
    for path in sorted(out.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name != "SHA256SUMS.csv":
            inventory_rows.append({
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            })
    _write_csv(out / "SHA256SUMS.csv", inventory_rows, ["path", "bytes", "sha256"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec", type=Path, default=Path("analysis/phase1_truncated_learning_spec.json")
    )
    parser.add_argument("--phase1-root", type=Path, default=Path("phase1_v2_corrected"))
    parser.add_argument(
        "--phase1b-input-root", type=Path, default=Path(".phase1b_truncation_inputs")
    )
    parser.add_argument(
        "--phase1b-inventory-root", type=Path, default=Path("phase1b_corrected")
    )
    parser.add_argument(
        "--out", type=Path,
        default=Path("phase1_truncated_learning_exploratory/analysis"),
    )
    args = parser.parse_args(argv)

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if spec["classification"] != "retrospective_exploratory_outcome_sighted":
        raise ValueError("spec must retain the exploratory, outcome-sighted classification")
    budgets = [int(value) for value in spec["budgets"]]
    if budgets != sorted(set(budgets)) or budgets[-1] != int(spec["training_horizon"]):
        raise ValueError("budgets must be sorted, unique, and end at the training horizon")

    resolver = InputResolver(
        spec,
        campaign_roots={"phase1": args.phase1_root, "phase1b": args.phase1b_input_root},
        inventory_roots={
            "phase1": args.phase1_root,
            "phase1b": args.phase1b_inventory_root,
        },
    )
    direct_rows = _direct_seed_rows(spec, resolver)
    seed_rows = add_derived_rows(spec, direct_rows)
    summaries = summarize_rows(spec, seed_rows)
    assessments = assess_profiles(spec, summaries)
    _write_outputs(
        spec, args.spec, args.out, resolver, seed_rows, summaries, assessments
    )
    print(
        f"wrote exploratory prefix analysis: {len(resolver.source_files)} inputs, "
        f"{len(seed_rows)} seed rows, {len(summaries)} summaries -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
