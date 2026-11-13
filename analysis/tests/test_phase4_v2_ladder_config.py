"""Phase-4 knowledge-ladder control profiles (Addendum 2026-11-13b).

Each control arm must be the registered `phase4_v2` profile with exactly one
additional learning override, so that a difference between an archived
`phase4_v2` cell and a ladder cell can only come from that override.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FULL = "phase4_v2"
CONTROLS = {
    "phase4_v2_redundancy_only": {"stereo_redundancy_only": True},
    "phase4_v2_brick_only": {"stereo_knowledge_layer": "brick"},
}


def _profiles():
    text = (ROOT / "config" / "run_config.json").read_text(encoding="utf-8-sig")
    return json.loads(text)["profiles"]


def test_ladder_controls_differ_from_phase4_v2_by_one_override_only():
    profiles = _profiles()
    full = profiles[FULL]
    for name, extra in CONTROLS.items():
        control = profiles[name]
        assert set(control) == set(full), name
        for key, value in full.items():
            if key in ("note", "learning_overrides"):
                continue
            assert control[key] == value, (name, key)
        expected = dict(full["learning_overrides"])
        expected.update(extra)
        assert control["learning_overrides"] == expected, name
        assert len(control["learning_overrides"]) == len(full["learning_overrides"]) + 1, name


def test_ladder_controls_keep_the_corrected_protocol():
    profiles = _profiles()
    for name in (FULL, *CONTROLS):
        mode = profiles[name]
        assert mode["protocol_version"] == "phase1-v2"
        assert mode["metric_schema"] == "phase1-benchmark-v2"
        assert mode["num_episodes"] == 3000
        assert mode["max_steps_per_episode"] == 20
        assert mode["learning_overrides"]["reward_shaping"] == "none"
        assert mode["learning_overrides"]["adaptive_trust"] is False
        assert mode["learning_overrides"]["stereo_energy_prior_weight"] == 2.0


def test_ladder_controls_do_not_set_both_layer_switches():
    profiles = _profiles()
    for name in CONTROLS:
        overrides = profiles[name]["learning_overrides"]
        assert not ("stereo_redundancy_only" in overrides and "stereo_knowledge_layer" in overrides), name
