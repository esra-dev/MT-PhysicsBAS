"""The labrel relevance-ladder rungs must share ONE scenario schedule.

The four stateless rungs (labrel0/4/8/16) hold state count, goal, physics,
and the scenario schedule fixed while only the action count varies. Preflight
requires per-profile scenario file names, so each rung carries its own copy —
these tests pin every copy byte-identical to the master
(benchmark/scenarios_labrel.json), so the schedules can never drift apart.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark"
RUNGS = ("labrel0", "labrel4", "labrel8", "labrel16")


def test_benchmark_copies_are_byte_identical_to_master():
    master = (BENCH / "scenarios_labrel.json").read_bytes()
    for rung in RUNGS:
        copy = (BENCH / f"scenarios_{rung}.json").read_bytes()
        assert copy == master, f"scenarios_{rung}.json drifted from the master schedule"


def test_train_copies_are_byte_identical_to_master():
    master = (BENCH / "train_scenarios_labrel.json").read_bytes()
    for rung in RUNGS:
        copy = (BENCH / f"train_scenarios_{rung}.json").read_bytes()
        assert copy == master, f"train_scenarios_{rung}.json drifted from the master schedule"
