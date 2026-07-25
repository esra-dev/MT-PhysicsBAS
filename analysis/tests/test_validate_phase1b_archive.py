"""Tests for analysis/validate_phase1b_archive.py and analysis/reproduce_phase1b.py.

Synthetic run archives are fabricated under tmp_path with fabricated
TRAINING_OK.json manifests plus the minimal metrics/first-goal/benchmark CSVs
the Phase-1 v2 per-cell gates read. Uses stdlib + pytest only.
"""

import csv
import json

import pytest

from analysis import reproduce_phase1b as rp
from analysis import validate_phase1b_archive as vpa
from analysis import validate_phase1_v2_archive as v2


# ---------------------------------------------------------------------------
# Synthetic archive tree helpers
# ---------------------------------------------------------------------------

MASTER_SHA = "a" * 64  # shared master schedule of the four labrel rungs
ORDERED_IDS = [1, 2]
EPISODES = 3000

_CATALOG_IDS: dict[str, list[int]] = {}


def _catalog_ids(profile):
    """Scenario IDs from the real committed benchmark catalogs (as the
    Phase-1 v2 per-cell gates read them)."""
    if profile not in _CATALOG_IDS:
        catalog = json.loads(
            (v2.SOURCE_ROOT / "benchmark" / f"scenarios_{profile}.json")
            .read_text(encoding="utf-8"))
        _CATALOG_IDS[profile] = [int(row["id"]) for row in catalog]
    return _CATALOG_IDS[profile]


def _schedule_sha(profile):
    if profile in vpa.LABREL_PROFILES:
        return MASTER_SHA
    return profile.ljust(64, "f")


def _write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _manifest_path(run_root, seed, profile, arm):
    return (run_root / "benchmark" / f"results_seed{seed}" / profile
            / f"training_stereo_{arm}" / "TRAINING_OK.json")


def make_cell(run_root, mode, seed, profile, arm):
    cell = run_root / "benchmark" / f"results_seed{seed}" / profile
    training = cell / f"training_stereo_{arm}"
    training.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "ok",
        "profile": profile,
        "stereotype": arm,
        "run_seed": seed,
        "run_mode": mode,
        "protocol_version": "phase1-v2",
        "ordered_scenario_ids": ORDERED_IDS,
        "scenario_schedule_sha256": _schedule_sha(profile),
        "fixed_horizon_episodes": EPISODES,
        "paired_rng_version": "common-seed-v1",
        "metric_schema": "phase1-benchmark-v2",
        "scenario_fallback_count": 0,
    }
    (training / "TRAINING_OK.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    _write_csv(training / f"metrics_stereotypes_{arm}_{profile}.csv",
               ["Episode", "GoalReached", "ScenarioId"],
               [[i + 1, i % 2, ORDERED_IDS[i % len(ORDERED_IDS)]]
                for i in range(EPISODES)])
    per_scenario = EPISODES // len(ORDERED_IDS)
    _write_csv(training / f"first_goal_stereotypes_{arm}_{profile}.csv",
               ["ProtocolVersion", "ScenarioId", "Presentations", "Censored",
                "AnalysisPresentation"],
               [["phase1-v2", sid, per_scenario, 0, 3.0]
                for sid in ORDERED_IDS])


def make_benchmarks(run_root, seed, profile):
    cell = run_root / "benchmark" / f"results_seed{seed}" / profile
    for mode in ("rule_based", "ql_false", "ql_true"):
        rows = [[sid, run, "phase1-benchmark-v2", 1.0, 2.0, 1]
                for sid in _catalog_ids(profile) for run in range(1, 6)]
        _write_csv(cell / mode / f"benchmark_results_{mode}.csv",
                   ["ScenarioId", "RunId", "MetricSchema", "PolicyEnergyCost",
                    "LegacyWallClockTotalEnergyCost", "GoalReached"],
                   rows)


def write_workflow_inputs(run_root, run_id, mode, seeds):
    out = run_root / "analysis" / "out" / "workflow_inputs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "workflow": ".github/workflows/phase1.yml",
        "run_id": run_id,
        "head_sha": "0" * 40,
        "ref": "refs/heads/phase1b-labs-2026-07",
        "run_mode": mode,
        "profiles": list(vpa.PROFILES),
        "seeds": list(seeds),
        "publish_results": True,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_run(campaign, run_id, mode, seeds):
    run_root = campaign / f"run_{run_id}"
    write_workflow_inputs(run_root, run_id, mode, seeds)
    for seed in seeds:
        for profile in vpa.PROFILES:
            for arm in ("true", "false"):
                make_cell(run_root, mode, seed, profile, arm)
            make_benchmarks(run_root, seed, profile)
    return run_root


def _set_schedule_sha(run_root, seed, profile, sha, arms=("true", "false")):
    for arm in arms:
        path = _manifest_path(run_root, seed, profile, arm)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["scenario_schedule_sha256"] = sha
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# validate(): stage / seed-block gates
# ---------------------------------------------------------------------------

def test_good_pilot_tree_passes_stage_pilot(tmp_path):
    run_root = build_run(tmp_path, 100, "phase1b_v2_baseline", [1001])
    assert vpa.validate(run_root, stage="pilot") == []


def test_good_confirmatory_tree_passes_stage_confirmatory(tmp_path):
    run_root = build_run(tmp_path, 101, "phase1b_v2_kg_frozen", [1])
    assert vpa.validate(run_root, stage="confirmatory") == []


def test_pilot_seed_inside_confirmatory_tree_fails(tmp_path):
    run_root = build_run(tmp_path, 102, "phase1b_v2_baseline", [1001])
    errors = vpa.validate(run_root, stage="confirmatory")
    assert any("pilot-block seed 1001" in error for error in errors)


def test_confirmatory_seed_inside_pilot_tree_fails(tmp_path):
    run_root = build_run(tmp_path, 103, "phase1b_v2_baseline", [1])
    errors = vpa.validate(run_root, stage="pilot")
    assert any("outside the pilot block" in error for error in errors)


def test_confirmatory_seed_outside_1_to_40_fails(tmp_path):
    run_root = build_run(tmp_path, 104, "phase1b_v2_extended", [41])
    errors = vpa.validate(run_root, stage="confirmatory")
    assert any("outside the confirmatory block" in error for error in errors)


def test_unknown_stage_raises(tmp_path):
    with pytest.raises(ValueError, match="stage"):
        vpa.validate(tmp_path, stage="exploratory")


# ---------------------------------------------------------------------------
# validate(): schedule-identity invariants
# ---------------------------------------------------------------------------

def test_labrel_rung_with_divergent_schedule_sha_fails(tmp_path):
    run_root = build_run(tmp_path, 105, "phase1b_v2_baseline", [1001])
    # Both arms rewritten identically: the paired-arm gate stays green and
    # ONLY the labrel master-schedule invariant fires.
    _set_schedule_sha(run_root, 1001, "labrel16", "b" * 64)
    errors = vpa.validate(run_root, stage="pilot")
    assert any("labrel rungs do not share one master scenario schedule"
               in error for error in errors)
    assert not any("differ between arms" in error for error in errors)


def test_paired_arm_schedule_sha_mismatch_fails(tmp_path):
    run_root = build_run(tmp_path, 106, "phase1b_v2_baseline", [1001])
    _set_schedule_sha(run_root, 1001, "labrel8", "c" * 64, arms=("false",))
    errors = vpa.validate(run_root, stage="pilot")
    assert any("labrel8" in error and "hashes differ between arms" in error
               for error in errors)


def test_non_labrel_profiles_do_not_need_the_master_schedule(tmp_path):
    run_root = build_run(tmp_path, 107, "phase1b_v2_baseline", [1001])
    # The builder already gives labrel8s/labband/lab4chain3 their own hashes.
    manifest = json.loads(_manifest_path(run_root, 1001, "labband", "true")
                          .read_text(encoding="utf-8"))
    assert manifest["scenario_schedule_sha256"] != MASTER_SHA
    assert vpa.validate(run_root, stage="pilot") == []


# ---------------------------------------------------------------------------
# validate(): workflow_inputs and per-cell v2 gates
# ---------------------------------------------------------------------------

def test_missing_workflow_inputs_is_reported(tmp_path):
    run_root = build_run(tmp_path, 108, "phase1b_v2_baseline", [1001])
    (run_root / "analysis" / "out" / "workflow_inputs.json").unlink()
    errors = vpa.validate(run_root, seeds=[1001], stage="pilot")
    assert any("missing provenance" in error for error in errors)


def test_unknown_run_mode_and_seed_mismatch_are_reported(tmp_path):
    run_root = build_run(tmp_path, 109, "phase1b_v2_baseline", [1001])
    write_workflow_inputs(run_root, 109, "phase1b_v2_borked", [1001, 1002])
    errors = vpa.validate(run_root, seeds=[1001], stage="pilot")
    assert any("is not a Phase-1b mode" in error for error in errors)
    assert any("seeds=" in error for error in errors)


def test_training_ok_run_mode_must_match_workflow_mode(tmp_path):
    run_root = build_run(tmp_path, 110, "phase1b_v2_baseline", [1001])
    write_workflow_inputs(run_root, 110, "phase1b_v2_extended", [1001])
    errors = vpa.validate(run_root, stage="pilot")
    assert any("run_mode='phase1b_v2_baseline' != workflow run_mode "
               "'phase1b_v2_extended'" in error for error in errors)


def test_v2_training_gates_apply_per_cell(tmp_path):
    run_root = build_run(tmp_path, 111, "phase1b_v2_baseline", [1001])
    path = _manifest_path(run_root, 1001, "lab4chain3", "true")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["protocol_version"] = "phase1-v1"
    manifest["scenario_fallback_count"] = 3
    path.write_text(json.dumps(manifest), encoding="utf-8")
    errors = vpa.validate(run_root, stage="pilot")
    assert any("protocol_version='phase1-v1'" in error for error in errors)
    assert any("scenario_fallback_count=3" in error for error in errors)


def test_undeclared_seed_directory_is_reported(tmp_path):
    run_root = build_run(tmp_path, 112, "phase1b_v2_baseline", [1001])
    (run_root / "benchmark" / "results_seed1002").mkdir()
    errors = vpa.validate(run_root, stage="pilot")
    assert any("not declared in workflow_inputs.json seeds" in error
               for error in errors)


# ---------------------------------------------------------------------------
# reproduce: discovery of the four mode archives
# ---------------------------------------------------------------------------

def _provenance_only_run(campaign, run_id, mode):
    write_workflow_inputs(campaign / f"run_{run_id}", run_id, mode, [1])


def test_missing_mode_dir_fails_reproduce_discovery(tmp_path):
    campaign = tmp_path / "phase1b_corrected"
    modes = sorted(rp.REQUIRED_MODES)
    for run_id, mode in enumerate(modes[:-1], start=200):
        _provenance_only_run(campaign, run_id, mode)
    with pytest.raises(ValueError, match="archive modes mismatch"):
        rp._discover(campaign)


def test_duplicate_mode_dir_fails_reproduce_discovery(tmp_path):
    campaign = tmp_path / "phase1b_corrected"
    for run_id, mode in enumerate(sorted(rp.REQUIRED_MODES), start=300):
        _provenance_only_run(campaign, run_id, mode)
    _provenance_only_run(campaign, 399, "phase1b_v2_baseline")
    with pytest.raises(ValueError, match="duplicate archive"):
        rp._discover(campaign)


def test_complete_campaign_discovery_maps_modes_to_run_dirs(tmp_path):
    campaign = tmp_path / "phase1b_corrected"
    for run_id, mode in enumerate(sorted(rp.REQUIRED_MODES), start=400):
        _provenance_only_run(campaign, run_id, mode)
    found = rp._discover(campaign)
    assert set(found) == rp.REQUIRED_MODES
    assert all(path.name.startswith("run_") for path in found.values())
