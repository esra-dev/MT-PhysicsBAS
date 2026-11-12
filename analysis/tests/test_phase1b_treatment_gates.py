"""Tests for the Phase-1b treatment-delivery gates added after audit AUD-001.

Reuses the synthetic-archive helpers of test_validate_phase1b_archive.py and
adds `stereo_effective_props` and initial Q-table fixtures.
"""

import json

from analysis import validate_phase1b_archive as vpa
from analysis.tests.test_validate_phase1b_archive import build_run

SEEDS = list(range(1, 11))


def _set_effective(run_root, seeds, values, arms=("true", "false")):
    for seed in seeds:
        for profile in vpa.PROFILES:
            for arm in arms:
                path = (run_root / "benchmark" / f"results_seed{seed}" / profile
                        / f"training_stereo_{arm}" / "TRAINING_OK.json")
                manifest = json.loads(path.read_text(encoding="utf-8"))
                manifest["stereo_effective_props"] = dict(values)
                path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _write_initial_q(run_root, seeds, content_by_profile):
    for seed in seeds:
        for profile, content in content_by_profile.items():
            path = (run_root / "benchmark" / f"results_seed{seed}" / profile
                    / "training_stereo_true"
                    / f"qtable_initial_stereotypes_true_{profile}.csv")
            path.write_text(content, encoding="utf-8")


EXTENDED = {"stereo.irrelevantDvPrior": 2.0, "stereo.bandMirrorInit": 5.0,
            "stereo.bandMirrorPrior": 2.0}
OFF = {key: 0.0 for key in EXTENDED}


def test_registered_effective_props_follow_config():
    assert vpa.registered_effective_props("phase1b_v2_extended") == EXTENDED
    assert vpa.registered_effective_props("phase1b_v2_kg_frozen") == OFF


def test_effective_props_gate_is_opt_in_and_rejects_missing(tmp_path):
    run = build_run(tmp_path, "1", "phase1b_v2_extended", SEEDS)
    assert vpa.validate(run, stage="confirmatory") == []
    errors = vpa.validate(run, stage="confirmatory", require_effective_props=True)
    assert errors and all("missing stereo_effective_props" in e for e in errors)


def test_effective_props_gate_rejects_frozen_values_in_extended_archive(tmp_path):
    """Exactly the 2026-07 failure: an 'extended' archive whose JVM ran 0.0."""
    run = build_run(tmp_path, "1", "phase1b_v2_extended", SEEDS)
    _set_effective(run, SEEDS, OFF)
    errors = vpa.validate(run, stage="confirmatory", require_effective_props=True)
    assert errors and all("!= registered" in e for e in errors)


def test_effective_props_gate_accepts_registered_values(tmp_path):
    run = build_run(tmp_path, "1", "phase1b_v2_extended", SEEDS)
    _set_effective(run, SEEDS, EXTENDED)
    assert vpa.validate(run, stage="confirmatory", require_effective_props=True) == []


def test_effective_props_gate_requires_zero_for_frozen_mode(tmp_path):
    run = build_run(tmp_path, "1", "phase1b_v2_kg_frozen", SEEDS)
    _set_effective(run, SEEDS, EXTENDED)
    errors = vpa.validate(run, stage="confirmatory", require_effective_props=True)
    assert errors and all("!= registered" in e for e in errors)
    _set_effective(run, SEEDS, OFF)
    assert vpa.validate(run, stage="confirmatory", require_effective_props=True) == []


def test_divergence_gate_rejects_identical_initial_q(tmp_path):
    frozen = build_run(tmp_path / "frozen", "2", "phase1b_v2_kg_frozen", SEEDS)
    extended = build_run(tmp_path / "ext", "3", "phase1b_v2_extended", SEEDS)
    same = {p: f"{p}\n0,0,0\n" for p in vpa.DIVERGENCE_PROFILES}
    _write_initial_q(frozen, SEEDS, same)
    _write_initial_q(extended, SEEDS, same)
    errors = vpa.validate(extended, stage="confirmatory", divergence_against=[frozen])
    assert errors and all("byte-identical to the frozen-KG table" in e for e in errors)
    assert len(errors) == len(SEEDS) * len(vpa.DIVERGENCE_PROFILES)


def test_divergence_gate_accepts_diverging_initial_q(tmp_path):
    frozen = build_run(tmp_path / "frozen", "2", "phase1b_v2_kg_frozen", SEEDS)
    extended = build_run(tmp_path / "ext", "3", "phase1b_v2_extended", SEEDS)
    _write_initial_q(frozen, SEEDS, {p: f"{p}\n0,0,0\n" for p in vpa.DIVERGENCE_PROFILES})
    _write_initial_q(extended, SEEDS, {p: f"{p}\n-2,0,0\n" for p in vpa.DIVERGENCE_PROFILES})
    assert vpa.validate(extended, stage="confirmatory", divergence_against=[frozen]) == []


def test_divergence_gate_refuses_non_extended_archive(tmp_path):
    frozen = build_run(tmp_path / "frozen", "2", "phase1b_v2_kg_frozen", SEEDS)
    errors = vpa.validate(frozen, stage="confirmatory", divergence_against=[frozen])
    assert any("applies to phase1b_v2_extended archives only" in e for e in errors)


def test_divergence_gate_reports_missing_tables(tmp_path):
    frozen = build_run(tmp_path / "frozen", "2", "phase1b_v2_kg_frozen", SEEDS)
    extended = build_run(tmp_path / "ext", "3", "phase1b_v2_extended", SEEDS)
    errors = vpa.validate(extended, stage="confirmatory", divergence_against=[frozen])
    assert errors and all("missing extended initial Q-table" in e for e in errors)
