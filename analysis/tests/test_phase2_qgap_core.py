"""Synthetic-only tests for the frozen Phase-2 Q-gap core."""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from phase2_qgap_core import (  # noqa: E402
    DetectorEvidence,
    FaultMode,
    FiniteSettledModel,
    LAB2_SPEC,
    LAB3_SPEC,
    LABMON2_SPEC,
    LABMON_SPEC,
    PROFILE_SPECS,
    QTableFormatError,
    ScenarioClassification,
    SparseQTable,
    build_cell_model,
    encode_state_vector,
    evaluate_detector_observation,
    evaluate_start_state_qgap,
    fault_action_labels,
    load_frozen_cell_specs,
    mixed_radix_strides,
    parse_qtable_csv,
    run_detector_opportunity_rollout,
)


SPEC_PATH = Path(__file__).resolve().parents[1] / "phase2_qgap_spec.json"


def scenario_for(spec, **overrides):
    row = {actuator.state_key: False for actuator in spec.actuators}
    if spec.has_sunshine_slot:
        row["Sunshine"] = 0
    row.update(overrides)
    return row


def qtable_with_rows(spec, rows):
    lines = ["StateIndex," + ",".join(spec.action_labels)]
    for state_index, values in rows.items():
        cells = [values.get(label, "0.00") for label in spec.action_labels]
        lines.append(f"{state_index}," + ",".join(cells))
    return parse_qtable_csv(
        "\n".join(lines) + "\n", spec.action_labels, spec.state_count)


def test_frozen_json_contract_matches_core_and_effective_degraded_goals():
    cells = load_frozen_cell_specs(SPEC_PATH)
    assert cells["labmon_f1dead"].analysis_goal_ranks == (2,)
    assert cells["lab3_f2dead_lowsun"].analysis_goal_ranks == (2, 2)
    assert cells["labmon2_f2dead_lowsun"].analysis_goal_ranks == (2, 2)

    # The raw scenario level is stale by construction.  Settled faulty physics
    # uses +260 for the monitor, so 315 must become 285 (rank 2).
    model = build_cell_model(
        cells["labmon_f1dead"],
        scenario_for(
            LABMON_SPEC,
            Z1Level=315,
            Z1Monitor=True,
        ),
        apply_unavailable_actions=True,
    )
    assert model.settled_levels(model.initial_state()) == (Decimal("285"),)
    assert model.zone_ranks(model.initial_state()) == (2,)
    assert model.is_goal(model.initial_state())


@pytest.mark.parametrize("spec", PROFILE_SPECS.values(), ids=lambda spec: spec.name)
def test_profile_mixed_radix_state_contract(spec):
    assert mixed_radix_strides(spec.domain_sizes)[-1] == 1
    maximum = tuple(domain - 1 for domain in spec.domain_sizes)
    assert encode_state_vector(maximum, spec.domain_sizes) == spec.state_count - 1

    all_on = scenario_for(
        spec,
        **{actuator.state_key: True for actuator in spec.actuators},
    )
    if spec.has_sunshine_slot:
        all_on["Sunshine"] = 900
    model = FiniteSettledModel.from_scenario(spec, all_on)
    assert model.state_index(model.initial_state()) == spec.state_count - 1


def test_java_clamp_compatibility_is_explicit():
    assert encode_state_vector(
        (-1, 8), (4, 2), clamp_like_java=True) == 1
    with pytest.raises(ValueError, match="outside"):
        encode_state_vector((-1, 8), (4, 2))


def test_qtable_label_remap_sparse_zero_rows_and_decimal_values():
    table = parse_qtable_csv(
        "StateIndex,B,DO_NOTHING,A\n"
        "2,1.25,-0.50,3.00\n",
        ("A", "B", "DO_NOTHING"),
        4,
    )
    assert table.row(2) == (
        Decimal("3.00"), Decimal("1.25"), Decimal("-0.50"))
    assert table.row(0) == (
        Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    assert table.greedy_action(2) == "A"


def test_exact_two_decimal_tie_uses_lowest_runtime_index_after_remap():
    table = parse_qtable_csv(
        "StateIndex,B,A\n0,2.00,2.00\n", ("A", "B"), 1)
    assert table.greedy_action(0) == "A"


@pytest.mark.parametrize(
    "text,match",
    [
        ("StateIndex,A,A\n0,1.00,2.00\n", "duplicate serialized"),
        ("StateIndex,A,C\n0,1.00,2.00\n", "action-label mismatch"),
        ("StateIndex,A,B\n0,1.00,2.00\n0,3.00,4.00\n", "duplicate StateIndex"),
        ("StateIndex,A,B\n2,1.00,2.00\n", "outside"),
        ("StateIndex,A,B\n0,1.00\n", "expected 3 fields"),
        ("StateIndex,A,B\n0,1.0,2.00\n", "exactly 2dp"),
        ("StateIndex,A,B\n0,NaN,2.00\n", "non-finite"),
        ("StateIndex,A,B\n0,Infinity,2.00\n", "non-finite"),
    ],
)
def test_qtable_rejects_ambiguous_or_invalid_serialization(text, match):
    with pytest.raises(QTableFormatError, match=match):
        parse_qtable_csv(text, ("A", "B"), 2)


def test_terminal_and_unreachable_scenario_classes_are_separate():
    blind_fault_actions = fault_action_labels(LAB2_SPEC, ("Z1Blinds",))
    terminal_model = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Z1Light=True, Z2Light=True),
        fault_modes={"Z1Blinds": FaultMode.DEAD},
        unavailable_actions=blind_fault_actions,
    )
    terminal = evaluate_start_state_qgap(
        terminal_model, qtable_with_rows(LAB2_SPEC, {}),
        blind_fault_actions)
    assert terminal.classification == ScenarioClassification.NO_RERANKING_NEEDED
    assert terminal.burden is None

    lamp_fault_actions = fault_action_labels(LABMON_SPEC, ("Z1Light",))
    unreachable_model = FiniteSettledModel.from_scenario(
        LABMON_SPEC,
        scenario_for(LABMON_SPEC),
        fault_modes={"Z1Light": FaultMode.DEAD},
        unavailable_actions=lamp_fault_actions,
        goal_ranks=(3,),
    )
    unreachable = evaluate_start_state_qgap(
        unreachable_model, qtable_with_rows(LABMON_SPEC, {}),
        lamp_fault_actions)
    assert unreachable.classification == ScenarioClassification.UNREACHABLE
    assert unreachable.signed_gap is None


def test_multifault_qgap_uses_every_shortest_first_action():
    cells = load_frozen_cell_specs(SPEC_PATH)
    cell = cells["labmon2_f2dead_lowsun"]
    model = build_cell_model(
        cell,
        scenario_for(LABMON2_SPEC, Sunshine=400),
        apply_unavailable_actions=True,
    )
    state_index = model.state_index(model.initial_state())
    table = qtable_with_rows(LABMON2_SPEC, {
        state_index: {
            "SetZ1Light=ON": "5.00",
            "SetZ2Light=ON": "4.50",
            "SetZ1Blinds=ON": "3.00",
            "SetZ1Monitor=ON": "2.50",
            "SetZ2Blinds=ON": "2.75",
            "SetZ2Monitor=ON": "2.25",
        },
    })
    result = evaluate_start_state_qgap(
        model, table, cell.unavailable_actions)
    assert result.classification == ScenarioClassification.ANALYZED
    assert result.shortest_path_length == 2
    assert result.shortest_sequence_count == 8
    assert set(result.shortest_first_actions) == {
        "SetZ1Blinds=ON", "SetZ1Monitor=ON",
        "SetZ2Blinds=ON", "SetZ2Monitor=ON",
    }
    assert result.signed_gap == Decimal("2.00")
    assert result.burden == Decimal("2.00")
    assert result.faulty_maximizers == ("SetZ1Light=ON",)
    assert result.survivor_maximizers == ("SetZ1Blinds=ON",)
    assert result.relevant_maximum_tied is False
    assert result.signed_gap_is_zero is False


def test_qgap_exposes_exact_maximizer_tie_sets_for_rate_aggregation():
    cells = load_frozen_cell_specs(SPEC_PATH)
    cell = cells["labmon2_f2dead_lowsun"]
    model = build_cell_model(
        cell,
        scenario_for(LABMON2_SPEC, Sunshine=400),
        apply_unavailable_actions=True,
    )
    state_index = model.state_index(model.initial_state())
    table = qtable_with_rows(LABMON2_SPEC, {
        state_index: {
            "SetZ1Light=ON": "5.00",
            "SetZ2Light=ON": "5.00",
            "SetZ1Blinds=ON": "3.00",
            "SetZ2Blinds=ON": "3.00",
        },
    })
    result = evaluate_start_state_qgap(
        model, table, cell.unavailable_actions)
    assert result.faulty_maximizers == (
        "SetZ1Light=ON", "SetZ2Light=ON")
    assert result.survivor_maximizers == (
        "SetZ1Blinds=ON", "SetZ2Blinds=ON")
    assert result.relevant_maximum_tied is True
    assert result.signed_gap_is_zero is False


def test_qgap_complete_reachability_does_not_apply_detector_horizon_20():
    class LongChainModel:
        spec = SimpleNamespace(
            action_labels=("FAULT", "advance"),
            state_count=22,
        )
        unavailable_actions = frozenset({"FAULT"})

        def initial_state(self):
            return 0

        def state_index(self, state):
            return state

        def is_goal(self, state):
            return state == 21

        def actions(self, _state):
            return ["advance"]

        def step(self, state, action):
            assert action == "advance"
            return min(21, state + 1)

        def complete_reachability_horizon(self):
            return 21

    table = SparseQTable(
        ("FAULT", "advance"),
        22,
        {0: (Decimal("5.00"), Decimal("3.00"))},
    )
    result = evaluate_start_state_qgap(
        LongChainModel(), table, ("FAULT",))
    assert result.classification == ScenarioClassification.ANALYZED
    assert result.shortest_path_length == 21
    assert result.shortest_first_actions == ("advance",)


def test_dead_evidence_is_masked_by_active_primary_cofeeder():
    masked_model = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Z1Blinds=True, Sunshine=100),
        fault_modes={"Z1Light": FaultMode.DEAD},
    )
    masked = evaluate_detector_observation(
        masked_model, masked_model.initial_state(), "SetZ1Light=ON")
    assert masked.masked
    assert masked.evidence == DetectorEvidence.NONE

    unmasked_model = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Sunshine=100),
        fault_modes={"Z1Light": FaultMode.DEAD},
    )
    unmasked = evaluate_detector_observation(
        unmasked_model, unmasked_model.initial_state(), "SetZ1Light=ON")
    assert not unmasked.masked
    assert unmasked.evidence == DetectorEvidence.DEAD


def test_cross_zone_cofeeder_masks_dead_evidence():
    model = FiniteSettledModel.from_scenario(
        LAB3_SPEC,
        scenario_for(LAB3_SPEC, Z2Light=True),
        fault_modes={"Z1Light": FaultMode.DEAD},
    )
    observation = evaluate_detector_observation(
        model, model.initial_state(), "SetZ1Light=ON")
    assert observation.masked
    assert observation.reason == "active_cofeeder_mask"


def test_inverted_evidence_bypasses_active_cofeeder_mask():
    model = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Z1Blinds=True, Sunshine=400),
        fault_modes={"Z1Light": FaultMode.INVERTED},
    )
    observation = evaluate_detector_observation(
        model, model.initial_state(), "SetZ1Light=ON")
    assert observation.evidence == DetectorEvidence.INVERTED
    assert not observation.masked


def test_iv_fault_requires_open_and_sun_rank_two():
    low_sun = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Sunshine=100),
        fault_modes={"Z1Blinds": FaultMode.DEAD},
    )
    assert evaluate_detector_observation(
        low_sun, low_sun.initial_state(),
        "SetZ1Blinds=ON").reason == "iv_below_minimum"

    adequate_sun = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Sunshine=400),
        fault_modes={"Z1Blinds": FaultMode.DEAD},
    )
    assert evaluate_detector_observation(
        adequate_sun, adequate_sun.initial_state(),
        "SetZ1Blinds=ON").evidence == DetectorEvidence.DEAD
    assert evaluate_detector_observation(
        adequate_sun,
        adequate_sun.step(adequate_sun.initial_state(), "SetZ1Blinds=ON"),
        "SetZ1Blinds=OFF",
    ).reason == "iv_close"


def test_shared_multizone_action_is_not_adjudicated():
    model = FiniteSettledModel.from_scenario(
        LAB3_SPEC,
        scenario_for(LAB3_SPEC),
        fault_modes={"Spotlight": FaultMode.DEAD},
    )
    observation = evaluate_detector_observation(
        model, model.initial_state(), "SetSpotlight=ON")
    assert observation.reason == "multi_zone"
    assert not observation.is_opportunity


def test_zero_row_rollout_uses_lowest_index_and_does_not_inject_probe():
    model = FiniteSettledModel.from_scenario(
        LAB2_SPEC,
        scenario_for(LAB2_SPEC, Sunshine=400),
        fault_modes={"Z1Blinds": FaultMode.DEAD},
    )
    result = run_detector_opportunity_rollout(
        model, qtable_with_rows(LAB2_SPEC, {}), ("Z1Blinds",), horizon=3)
    assert result.action_trace == ("SetZ1Blinds=OFF",) * 3
    assert result.opportunity_by_component["Z1Blinds"] is False
    assert result.any_fault_component_opportunity is False


def test_rollout_reports_each_multifault_component_and_primary_any_aggregate():
    cells = load_frozen_cell_specs(SPEC_PATH)
    cell = cells["labmon2_f2dead_lowsun"]
    model = build_cell_model(
        cell,
        scenario_for(LABMON2_SPEC),
        apply_unavailable_actions=False,
    )
    initial_index = model.state_index(model.initial_state())
    after_z1 = model.step(model.initial_state(), "SetZ1Light=ON")
    after_z1_index = model.state_index(after_z1)
    table = qtable_with_rows(LABMON2_SPEC, {
        initial_index: {"SetZ1Light=ON": "2.00"},
        after_z1_index: {"SetZ2Light=ON": "2.00"},
    })
    result = run_detector_opportunity_rollout(
        model, table, cell.fault_components, horizon=2)
    assert result.opportunity_by_component == {
        "Z1Light": True, "Z2Light": True}
    assert result.first_opportunity_step == {
        "Z1Light": 1, "Z2Light": 2}
    assert result.any_fault_component_opportunity
    assert result.all_fault_components_opportunity
