import json
from pathlib import Path


MODES = (
    "phase1_v2_kg_only",
    "phase1_v2_redundancy_only",
    "phase1_v2_baseline",
    "phase1_v2_pbrs_only",
)


def test_corrected_modes_lock_protocol_and_horizon():
    config = json.loads(Path("config/run_config.json").read_text(encoding="utf-8-sig"))
    for name in MODES:
        mode = config["profiles"][name]
        assert mode["protocol_version"] == "phase1-v2"
        assert mode["metric_schema"] == "phase1-benchmark-v2"
        assert mode["num_episodes"] == 3000
        assert mode["max_steps_per_episode"] == 20


def test_corrected_factorial_controls_are_explicit():
    config = json.loads(Path("config/run_config.json").read_text(encoding="utf-8-sig"))
    profiles = config["profiles"]
    assert profiles["phase1_v2_kg_only"]["learning_overrides"] == {
        "reward_shaping": "none", "adaptive_trust": False,
    }
    assert profiles["phase1_v2_redundancy_only"]["learning_overrides"] == {
        "reward_shaping": "none", "adaptive_trust": False,
        "stereo_redundancy_only": True,
    }
    assert profiles["phase1_v2_baseline"]["learning_overrides"] == {
        "stereo_prior_scale": 0.0, "stereo_init_bonus": 0.0,
        "reward_shaping": "none", "adaptive_trust": False,
    }
    assert profiles["phase1_v2_pbrs_only"]["learning_overrides"] == {
        "stereo_prior_scale": 0.0, "stereo_init_bonus": 0.0,
        "reward_shaping": "pbrs", "adaptive_trust": False,
    }
