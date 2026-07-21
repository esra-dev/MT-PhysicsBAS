from pathlib import Path

from analysis.validate_phase1_scenarios import expected_levels, validate_all


def test_all_committed_phase1_scenarios_match_current_physics():
    assert validate_all() == []


def test_lab3_current_coupling_constants():
    row = {
        "Sunshine": 900,
        "Z1Light": False,
        "Z2Light": False,
        "Z1Blinds": True,
        "Z2Blinds": True,
        "Spotlight": False,
    }
    assert expected_levels("lab3", row) == {"Z1Level": 745.0, "Z2Level": 745.0}


def test_training_protocol_settles_before_recording_start_state():
    source = Path("src/agt/illuminance_controller_agent_ql.asl").read_text(
        encoding="utf-8")
    start = source.index("setScenarioLabStateByPosition")
    settle = source.index(".wait(250)", start)
    observe = source.index("readLabStatus(ZLStart", settle)
    record = source.index("beginEpisodeForScenario", observe)
    assert start < settle < observe < record
