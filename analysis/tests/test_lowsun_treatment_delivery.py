"""Treatment-delivery guards for the Phase-2 low-sun cells (audit R2-001/R2-002).

The 2026-07 `*_lowsun` cells never ran at low sun: the pin lived only in the
simulator's episode-reset sampler, which the protocol-v2 explicit scenario
starts bypass, and the profiles mapped to their parents' mixed-sun schedules.
These tests make every link of the corrected chain a local/CI failure:

- the derived low-sun scenario files equal their generator's output and keep
  the parent's ids/order/start states while pinning Sunshine = 100;
- config/run_config.json and src/agt/lab_profiles.asl name the SAME file for
  every low-sun profile (the agent reads the ASL, the manifests the config);
- the archive validator rejects a low-sun cell without delivery evidence, a
  cell whose evidence shows the parent's sun values, and a manifest whose file
  hash does not match the committed scenario file.
"""

import hashlib
import json
import re

import pytest

from analysis import build_lowsun_scenarios as gen
from analysis import validate_phase2_v2_archive as v2
from analysis.validate_phase1_scenarios import validate_file as validate_physics

ROOT = gen.ROOT
LOWSUN_PROFILES = (
    "lab3_f2dead_lowsun",
    "labmon2_f2dead_lowsun",
    "labmon2_infoonly_f2dead_lowsun",
    "labmon2_nostereo_f2dead_lowsun",
)


def _config():
    return json.loads((ROOT / "config" / "run_config.json").read_text(encoding="utf-8-sig"))


def _asl_train_scenarios(profile):
    text = (ROOT / "src" / "agt" / "lab_profiles.asl").read_text(encoding="utf-8")
    match = re.search(r'lab_profile\("' + re.escape(profile)
                      + r'",[\s\S]*?train_scenarios\("([^"]+)"\)', text)
    assert match, f"no train_scenarios(...) for {profile} in lab_profiles.asl"
    return match.group(1)


# ---------------------------------------------------------------- files -----

def test_derived_lowsun_files_match_generator():
    for path, text in gen.build_all().items():
        assert path.is_file(), f"missing derived file {path}"
        assert path.read_text(encoding="utf-8") == text, f"stale derived file {path}"


@pytest.mark.parametrize("parent_rel, derived_rel, lab", gen.DERIVATIONS)
def test_lowsun_file_pins_sun_and_preserves_schedule(parent_rel, derived_rel, lab):
    parent = json.loads((ROOT / parent_rel).read_text(encoding="utf-8-sig"))
    derived = json.loads((ROOT / derived_rel).read_text(encoding="utf-8-sig"))
    assert [row["id"] for row in derived] == [row["id"] for row in parent]
    assert {row["Sunshine"] for row in derived} == {gen.LOWSUN_LUX}
    actuators = [key for key in gen.FIELD_ORDER[lab]
                 if key not in ("id", "Z1Level", "Z2Level", "Sunshine")]
    for p_row, d_row in zip(parent, derived):
        for key in actuators:
            assert d_row[key] == p_row[key], f"{derived_rel} id {d_row['id']} {key}"
        for key, value in gen.clean_levels(lab, d_row).items():
            assert float(d_row[key]) == pytest.approx(value)


def test_lab3_lowsun_file_passes_committed_physics_validator():
    assert validate_physics(ROOT / "benchmark" / "train_scenarios_lab3_lowsun.json",
                            "lab3") == []


# ------------------------------------------------------------- mappings -----

@pytest.mark.parametrize("profile", LOWSUN_PROFILES)
def test_lowsun_profile_maps_to_pinned_file_in_config_and_asl(profile):
    cfg_rel = _config()["phase2"]["train_scenarios_map"][profile]
    assert cfg_rel.endswith("_lowsun.json"), cfg_rel
    assert _asl_train_scenarios(profile) == cfg_rel
    _, sun_values = v2._treatment(cfg_rel)
    assert sun_values == [v2.LOWSUN_LUX]


def test_non_lowsun_profiles_keep_parent_schedules():
    scenario_map = _config()["phase2"]["train_scenarios_map"]
    for profile, rel in scenario_map.items():
        if not profile.endswith("_lowsun"):
            assert not rel.endswith("_lowsun.json"), f"{profile} -> {rel}"
            assert _asl_train_scenarios(profile) == rel


# ------------------------------------------------------ archive validator ---

def _make_cell(root, seed, profile, bool_name, mode, scenario_rel, *,
               evidence=True, sun_values=None, file_hash=None, delivered=None):
    seed_root = root / "recovery_root" / f"seed{seed}"
    seed_root.mkdir(parents=True, exist_ok=True)
    ids, schedule_hash = v2._schedule(scenario_rel)
    true_hash, true_sun = v2._treatment(scenario_rel)
    cell = f"stereotypes_{bool_name}_{profile}"
    manifest = {
        "status": "ok", "protocol_version": v2.PROTOCOL, "detector_version": v2.DETECTOR,
        "metric_schema": v2.METRIC_SCHEMA, "settled_start_state": True,
        "scenario_fallback_count": 0, "profile": profile, "mode": mode, "run_seed": seed,
        "adapt_episodes_effective": 2, "train_scenarios_file": scenario_rel,
        "ordered_scenario_ids": ids, "scenario_schedule_sha256": schedule_hash,
        "parent_qtable_sha256": "f" * 64,
    }
    if evidence:
        manifest["scenario_file_sha256"] = file_hash or true_hash
        manifest["scenario_sunshine_values"] = sun_values if sun_values is not None else true_sun
        manifest["lowsun_pin_delivered"] = delivered
    (seed_root / f"ADAPT_OK_{cell}.json").write_text(json.dumps(manifest), encoding="utf-8")
    (seed_root / f"recovery_{cell}.csv").write_text(
        "DetectorVersion,ProtocolVersion,BlacklistEvents,RecoveryEpisodes,DetectEpisode\n"
        f"{v2.DETECTOR},{v2.PROTOCOL},1,5,1\n", encoding="utf-8")
    (seed_root / f"metrics_adapted_{cell}.csv").write_text(
        "Episode,GoalReached\n1,0\n2,1\n", encoding="utf-8")


def _both_arms(root, profile, scenario_rel, **kwargs):
    for bool_name, mode in (("true", "ql_true"), ("false", "ql_false")):
        _make_cell(root, 1, profile, bool_name, mode, scenario_rel, **kwargs)


def test_validator_accepts_delivered_lowsun_cell(tmp_path):
    rel = "benchmark/train_scenarios_lab3_lowsun.json"
    _both_arms(tmp_path, "lab3_f2dead_lowsun", rel, delivered=True)
    errors = v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False,
                         require_treatment_delivery=True)
    assert errors == []


def test_validator_rejects_lowsun_cell_without_evidence_when_required(tmp_path):
    rel = "benchmark/train_scenarios_lab3_lowsun.json"
    _both_arms(tmp_path, "lab3_f2dead_lowsun", rel, evidence=False)
    assert v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False) == []
    errors = v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False,
                         require_treatment_delivery=True)
    assert errors and all("treatment-delivery evidence" in e for e in errors)


def test_validator_rejects_parent_schedule_sun_values(tmp_path):
    """A manifest that records the 2026-07 situation (mixed sun) must fail."""
    rel = "benchmark/train_scenarios_lab3_lowsun.json"
    _both_arms(tmp_path, "lab3_f2dead_lowsun", rel,
               sun_values=[0.0, 100.0, 400.0, 900.0], delivered=False)
    errors = v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False)
    assert any("low-sun pin NOT delivered" in e for e in errors)
    assert any("scenario_sunshine_values" in e for e in errors)


def test_validator_rejects_file_hash_mismatch(tmp_path):
    rel = "benchmark/train_scenarios_lab3_lowsun.json"
    _both_arms(tmp_path, "lab3_f2dead_lowsun", rel, delivered=True,
               file_hash=hashlib.sha256(b"other").hexdigest())
    errors = v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False)
    assert any("scenario_file_sha256 differs" in e for e in errors)


def test_validator_rejects_lowsun_profile_mapped_to_mixed_sun_file(tmp_path, monkeypatch):
    """If the config ever regresses to the parent's file, the strict gate fails
    even when the manifest honestly records what was delivered."""
    cfg = _config()
    cfg["phase2"]["train_scenarios_map"]["lab3_f2dead_lowsun"] = "benchmark/train_scenarios_lab3.json"
    monkeypatch.setattr(v2, "_config", lambda: cfg)
    rel = "benchmark/train_scenarios_lab3.json"
    _both_arms(tmp_path, "lab3_f2dead_lowsun", rel, delivered=False)
    errors = v2.validate(tmp_path, ["lab3_f2dead_lowsun"], [1], require_parents=False,
                         require_treatment_delivery=True)
    assert any("every scenario must pin" in e for e in errors)


def test_non_lowsun_cell_with_evidence_passes_and_flag_must_be_null(tmp_path):
    rel = "benchmark/train_scenarios_lab3.json"
    _both_arms(tmp_path, "lab3_f1dead", rel, delivered=None)
    assert v2.validate(tmp_path, ["lab3_f1dead"], [1], require_parents=False,
                       require_treatment_delivery=True) == []
    _both_arms(tmp_path, "lab3_f1dead", rel, delivered=True)
    errors = v2.validate(tmp_path, ["lab3_f1dead"], [1], require_parents=False)
    assert any("non-low-sun profile" in e for e in errors)
