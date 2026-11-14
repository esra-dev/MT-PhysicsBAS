"""Tests for the Phase-4 knowledge-ladder helper scripts and the committed table.

Covers the proof-of-delivery script (gate invariance and the optional table
comparison), the cross-run comparability script, and the internal consistency
of the committed registered family table (category rule, BH within family).
"""
import csv
from pathlib import Path

from analysis import phase4_v2_ladder_cross_run_identity as identity
from analysis import phase4_v2_ladder_layer_proof as proof

ROOT = Path(__file__).resolve().parents[2]
FAMILY = ROOT / "phase4_v2_ladder" / "analysis" / "registered" / "phase4_v2_knowledge_ladder_family.csv"

# Two binary slots, slot 0 most significant: slot 0 is the upstream switch,
# slot 1 the gated actuator itself.
LAYOUT = {"sizes": [2, 2], "strides": [2, 1], "sun_slot": 1, "n_states": 4}
GATED = {"SetLamp=ON": {"own_slot": 1, "gate_slot": 0}}


def _table(path: Path, lamp_on_column: list[str]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["state", "SetLamp=ON", "DO_NOTHING"])
        for state, value in enumerate(lamp_on_column):
            writer.writerow([state, value, "0.00"])
    return path


def test_gate_invariant_table_is_recognised(tmp_path):
    # States 0,1 have the switch off; states 2,3 the switch on. Equal values in
    # each pair (0,2) and (1,3) mean the column ignores the switch.
    result = proof._check_table(_table(tmp_path / "q.csv", ["22.50", "-50.00", "22.50", "-50.00"]),
                                LAYOUT, GATED)
    assert result["SetLamp=ON"]["gate_invariant"] is True
    assert result["SetLamp=ON"]["state_pairs"] == 2
    assert result["SetLamp=ON"]["pairs_that_differ"] == 0


def test_gate_dependent_table_is_recognised(tmp_path):
    result = proof._check_table(_table(tmp_path / "q.csv", ["-50.00", "-50.00", "22.50", "-50.00"]),
                                LAYOUT, GATED)
    assert result["SetLamp=ON"]["gate_invariant"] is False
    assert result["SetLamp=ON"]["pairs_that_differ"] == 1
    assert result["SetLamp=ON"]["values_gate_off_action_off"] == {"-50.00": 1}
    assert result["SetLamp=ON"]["values_gate_on_action_off"] == {"22.50": 1}


def _run_tree(root: Path, wallclock: str, steps: str) -> Path:
    for cell, files in (
            ("training_stereo_false", {
                "metrics_stereotypes_false_lab4.csv": "ep,goal\n1,1\n",
                "qtable_initial_stereotypes_false_lab4.csv": "state,a\n0,0.00\n",
                "qtable_final_stereotypes_false_lab4.csv": "state,a\n0,1.00\n",
                "first_goal_stereotypes_false_lab4.csv": "scenario,ep\n1,1\n",
                "coverage_stereotypes_false_lab4.csv": "state,visits\n0,3\n",
                # A copy of the knowledge-arm file must be skipped by the comparison.
                "metrics_stereotypes_true_lab4.csv": f"ep,goal\n1,{steps}\n"}),
            ("ql_false", {"benchmark_results_ql_false.csv":
                          f"ScenarioId,Steps,LegacyWallClockTotalEnergyCost\n1,{steps},{wallclock}\n"}),
            ("rule_based", {"benchmark_results_rule_based.csv":
                            f"ScenarioId,Steps,LegacyWallClockTotalEnergyCost\n1,3,{wallclock}\n"})):
        folder = root / "benchmark" / "results_seed1" / "lab4" / cell
        folder.mkdir(parents=True)
        for name, content in files.items():
            (folder / name).write_text(content, encoding="utf-8", newline="\n")
    return root


def test_identity_accepts_wallclock_only_differences(tmp_path):
    reference = _run_tree(tmp_path / "ref", wallclock="1.5", steps="3")
    other = _run_tree(tmp_path / "other", wallclock="9.9", steps="3")
    report = identity.build([reference], [other], ["lab4"])
    assert report["seeds_compared"] == [1]
    assert report["check_tabula_rasa_training_identical_all_labs_all_seeds"] is True
    assert report["check_ql_false_and_rule_based_benchmarks_differ_only_in_wallclock_column"] is True
    assert report["file_kinds_with_unexpected_differences"] == []
    assert report["benchmark_result_columns_with_differing_cells"]["ql_false/lab4"] == {
        "LegacyWallClockTotalEnergyCost": 1}


def test_identity_flags_a_difference_in_an_analysed_column(tmp_path):
    reference = _run_tree(tmp_path / "ref", wallclock="1.5", steps="3")
    other = _run_tree(tmp_path / "other", wallclock="1.5", steps="4")
    report = identity.build([reference], [other], ["lab4"])
    assert report["check_ql_false_and_rule_based_benchmarks_differ_only_in_wallclock_column"] is False
    assert report["file_kinds_with_unexpected_differences"] == ["ql_false/benchmark_results_ql_false.csv"]


def _bh(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(p_values)
    running = 1.0
    for rank in range(len(order), 0, -1):
        index = order[rank - 1]
        running = min(running, p_values[index] * len(p_values) / rank)
        adjusted[index] = running
    return adjusted


def test_committed_family_table_is_internally_consistent():
    with FAMILY.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["family"] for row in rows] == ["R"] * 3 + ["S"] * 3 + ["secondary"]
    for row in rows:
        assert row["n_paired"] == "20"
        assert int(row["n_positive"]) + int(row["n_tie"]) + int(row["n_negative"]) == 20
        lo, hi = float(row["ci_lo_bootstrap"]), float(row["ci_hi_bootstrap"])
        if row["metric"] == "energy_compliance":  # higher is better
            expected = "adds" if lo > 0 else "costs" if hi < 0 else "null"
        else:  # avg_redundant: lower is better
            expected = "adds" if hi < 0 else "costs" if lo > 0 else "null"
        assert row["registered_category"] == expected, row["registered_test"]
        increment = float(row["mean_upper_arm_effect"]) - float(row["mean_lower_arm_effect"])
        assert abs(increment - float(row["mean_increment"])) < 1e-12
    for family, size in (("R", "3"), ("S", "3"), ("secondary", "1")):
        members = [row for row in rows if row["family"] == family]
        assert {row["bh_family_m"] for row in members} == {size}
        adjusted = _bh([float(row["p_signflip_two_sided"]) for row in members])
        for row, q in zip(members, adjusted):
            assert abs(float(row["q_signflip_bh"]) - q) < 1e-15, row["registered_test"]
    for row in rows:
        if row["family"] == "R":
            share = float(row["mean_lower_arm_effect"]) / float(row["mean_upper_arm_effect"])
            assert abs(share - float(row["share_lower_of_upper"])) < 1e-12
        else:
            assert row["share_lower_of_upper"] == "" and row["share_category"] == ""
