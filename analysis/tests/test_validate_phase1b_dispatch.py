"""Tests for the exact Phase-1b workflow-dispatch gate."""

import pytest

from analysis.validate_phase1b_dispatch import (
    CONFIRMATORY_SEED_BLOCKS,
    MODES,
    PILOT_SEEDS,
    PROFILES,
    validate_dispatch,
)


PROFILES_CSV = ",".join(sorted(PROFILES))


@pytest.mark.parametrize("mode", sorted(MODES))
@pytest.mark.parametrize("seeds", CONFIRMATORY_SEED_BLOCKS)
def test_registered_confirmatory_halves_pass(mode, seeds):
    result = validate_dispatch(
        mode, "confirmatory", PROFILES_CSV,
        ",".join(str(seed) for seed in sorted(seeds)))
    assert result["training_tuples"] == 140
    assert result["benchmark_tuples"] == 210


def test_registered_pilot_block_passes():
    result = validate_dispatch(
        "phase1b_v2_extended", "pilot", PROFILES_CSV,
        ",".join(str(seed) for seed in sorted(PILOT_SEEDS)))
    assert result["seed_block"] == "1001-1010"


@pytest.mark.parametrize(
    ("profiles", "seeds", "message"),
    [
        (PROFILES_CSV + ",labrel0", "1,2,3,4,5,6,7,8,9,10",
         "duplicate profile"),
        (PROFILES_CSV, "1,2,3,4,5,6,7,8,9,01", "duplicate numeric seed"),
        (PROFILES_CSV, "1,2,3,4,5,6,7,8,9,9", "duplicate seed"),
        (PROFILES_CSV, "1,2,3,4,5,6,7,8,9", "exactly"),
        (PROFILES_CSV, ",".join(str(seed) for seed in range(1, 21)), "exactly"),
        (PROFILES_CSV.replace("labband", "lab1"), "1,2,3,4,5,6,7,8,9,10",
         "profile set mismatch"),
    ],
)
def test_nonregistered_or_duplicate_dispatches_fail(profiles, seeds, message):
    with pytest.raises(ValueError, match=message):
        validate_dispatch(
            "phase1b_v2_baseline", "confirmatory", profiles, seeds)


def test_unregistered_mode_and_stage_fail():
    with pytest.raises(ValueError, match="unregistered"):
        validate_dispatch(
            "phase1b_v2_typo", "confirmatory", PROFILES_CSV,
            "1,2,3,4,5,6,7,8,9,10")
    with pytest.raises(ValueError, match="phase1b_stage"):
        validate_dispatch(
            "phase1b_v2_baseline", "", PROFILES_CSV,
            "1,2,3,4,5,6,7,8,9,10")
