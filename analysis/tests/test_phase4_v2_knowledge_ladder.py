"""Unit test for the frozen Phase-4 knowledge-ladder analysis.

Builds three tiny synthetic archives (full KG, Brick, redundancy) with known
per-seed values and checks the pre-committed category rule, the direction
convention (lower avg_redundant is better), the reused one-third/two-thirds
share rule, the Benjamini-Hochberg family sizes, and the comparability table.
"""
import csv
from pathlib import Path

from analysis import phase4_v2_knowledge_ladder as ladder

HEADER = ["ScenarioId", "RunId", "AgentType", "MetricSchema", "GoalReached", "Steps",
          "CumIlluminanceDeviation", "WastedSteps", "ActuatorCyclingCount", "PolicyEnergyCost"]


def _write_cell(root: Path, seed: int, lab: str, mode: str, redundant: float) -> None:
    cell = root / "benchmark" / f"results_seed{seed}" / lab / mode
    cell.mkdir(parents=True, exist_ok=True)
    with (cell / f"benchmark_results_{mode}.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        # Two rows whose (WastedSteps + ActuatorCyclingCount) average to `redundant`.
        writer.writerow([1, 1, mode, "phase1-benchmark-v2", 1, 3, 0.0, redundant, 0, 1.0])
        writer.writerow([2, 1, mode, "phase1-benchmark-v2", 1, 3, 0.0, 0, redundant, 1.0])


def _archive(root: Path, ql_true_by_lab: dict) -> Path:
    for lab, value in ql_true_by_lab.items():
        for seed in ladder.SEEDS:
            on = value(seed) if callable(value) else value
            _write_cell(root, seed, lab, "ql_true", on)
            _write_cell(root, seed, lab, "ql_false", 2.0)
    return root


def test_categories_shares_and_family_sizes(tmp_path, monkeypatch):
    monkeypatch.setattr(ladder, "BOOTSTRAP_ITERS", 400)
    # Effects (ql_true - 2.0): A3 = -1.0 on every lab.
    full = _archive(tmp_path / "full", {"lab4": 1.0, "lab4dual": 1.0, "lab4chain": 1.0})
    # A2: equal to A3 on lab4 (null), better than A3 on lab4dual (costs),
    # alternating around A3 on lab4chain (null).
    brick = _archive(tmp_path / "brick", {
        "lab4": 1.0, "lab4dual": 0.8,
        "lab4chain": lambda seed: 1.0 + (0.1 if seed % 2 else -0.1)})
    # A1: effect -0.5 / -0.9 / -0.2 -> shares 0.5 / 0.9 / 0.2.
    redundancy = _archive(tmp_path / "red", {"lab4": 1.5, "lab4dual": 1.1, "lab4chain": 1.8})

    out = tmp_path / "out"
    summary = ladder.run([full], [brick], [redundancy], out)

    with (out / "phase4_v2_knowledge_ladder_family.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["registered_test"]: row for row in csv.DictReader(handle)}
    assert len(rows) == 6  # no lab5 cells -> secondary not run
    assert summary["secondary_lab5_energy_compliance"] == "not_run_no_lab5_cells"

    # Family R: full KG removes more redundant actions than the rule alone -> adds.
    for lab, share_category in (("lab4", "between_one_third_and_two_thirds"),
                                ("lab4dual", "more_than_two_thirds"),
                                ("lab4chain", "less_than_one_third")):
        row = rows[f"A3_minus_A1_{lab}_avg_redundant"]
        assert row["family"] == "R" and row["bh_family_m"] == "3"
        assert float(row["mean_increment"]) < 0
        assert row["registered_category"] == "adds"
        assert row["share_category"] == share_category
        assert row["n_negative"] == "20" and row["n_positive"] == "0"

    # Family S: equal / Brick better / symmetric noise.
    assert rows["A3_minus_A2_lab4_avg_redundant"]["registered_category"] == "null"
    assert rows["A3_minus_A2_lab4_avg_redundant"]["n_tie"] == "20"
    assert rows["A3_minus_A2_lab4dual_avg_redundant"]["registered_category"] == "costs"
    assert float(rows["A3_minus_A2_lab4dual_avg_redundant"]["mean_increment"]) > 0
    assert rows["A3_minus_A2_lab4chain_avg_redundant"]["registered_category"] == "null"
    for lab in ("lab4", "lab4dual", "lab4chain"):
        assert rows[f"A3_minus_A2_{lab}_avg_redundant"]["bh_family_m"] == "3"
        assert rows[f"A3_minus_A2_{lab}_avg_redundant"]["share_category"] == ""

    # Tabula-rasa cells are identical across the synthetic archives.
    assert summary["tabula_rasa_identical_in_all_seeds"] is True
    with (out / "phase4_v2_knowledge_ladder_comparability.csv").open(encoding="utf-8", newline="") as handle:
        comp = list(csv.DictReader(handle))
    assert len(comp) == 6
    assert all(row["n_seeds_identical"] == "20" for row in comp)


def test_category_direction_convention():
    # avg_redundant: lower is better.
    assert ladder._category("avg_redundant", -0.3, -0.1) == "adds"
    assert ladder._category("avg_redundant", 0.1, 0.3) == "costs"
    assert ladder._category("avg_redundant", -0.1, 0.1) == "null"
    assert ladder._category("avg_redundant", 0.0, 0.0) == "null"
    # energy_compliance: higher is better.
    assert ladder._category("energy_compliance", 0.01, 0.07) == "adds"
    assert ladder._category("energy_compliance", -0.07, -0.01) == "costs"
    assert ladder._category("energy_compliance", -0.01, 0.07) == "null"
