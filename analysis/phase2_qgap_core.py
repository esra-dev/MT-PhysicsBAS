"""Synthetic core for the frozen Phase-2 start-state Q-gap retrospective.

This module intentionally has no artifact-discovery or real-data execution
logic.  It provides the deterministic pieces that can be frozen and tested
before any rescued Q-table is read:

* strict sparse two-decimal Q-table parsing and label remapping;
* declarative settled-state physics and Java-compatible mixed-radix encoding;
* exhaustive shortest-survivor-route Q-gap evaluation; and
* the deterministic, greedy detector-opportunity descriptor.

The detector rollout is a model-based descriptor, not a replay of the
stochastic adaptation agent.  It uses the combined serialized Q-table,
lowest-runtime-index tie breaking, no diagnostic probes, no learning, and no
blacklisting.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from analysis.transition_checker import check_scenario
except ImportError:  # pragma: no cover - direct script-style import
    from transition_checker import check_scenario


TWO_PLACES = Decimal("0.01")
ZERO_Q = Decimal("0.00")
DO_NOTHING = "DO_NOTHING"


class QGapCoreError(ValueError):
    """Base exception for an invalid frozen-core input."""


class QTableFormatError(QGapCoreError):
    """Raised when a serialized Q-table violates its strict data contract."""


class FaultMode(str, Enum):
    HEALTHY = "healthy"
    DEAD = "dead"
    INVERTED = "inverted"


class SlotKind(str, Enum):
    ZONE_RANK = "zone_rank"
    ACTUATOR_BIT = "actuator_bit"
    SUNSHINE_RANK = "sunshine_rank"


class ScenarioClassification(str, Enum):
    ANALYZED = "ANALYZED"
    NO_RERANKING_NEEDED = "NO_RERANKING_NEEDED"
    UNREACHABLE = "UNREACHABLE"


class DetectorEvidence(str, Enum):
    NONE = "NONE"
    DEAD = "DEAD"
    INVERTED = "INVERTED"


@dataclass(frozen=True)
class StateSlotSpec:
    name: str
    kind: SlotKind
    domain_size: int
    zone_index: Optional[int] = None
    component: Optional[str] = None


@dataclass(frozen=True)
class ActuatorSpec:
    """Declarative actuator metadata and its nominal physical contribution."""

    component: str
    state_key: str
    off_label: str
    on_label: str
    primary_zones: Tuple[int, ...]
    fixed_effects: Tuple[Decimal, ...]
    sunshine_effects: Tuple[Decimal, ...]
    cross_zone_targets: Tuple[int, ...] = ()
    iv_gated: bool = False
    kg_silent: bool = False


@dataclass(frozen=True)
class ActionSpec:
    label: str
    component: Optional[str]
    target_value: Optional[bool]


@dataclass(frozen=True)
class ProfileSpec:
    """Finite parent topology plus deterministic nominal physics."""

    name: str
    zone_names: Tuple[str, ...]
    goal_ranks: Tuple[int, ...]
    ambient_levels: Tuple[Decimal, ...]
    actuators: Tuple[ActuatorSpec, ...]
    state_slots: Tuple[StateSlotSpec, ...]
    light_rank_bounds: Tuple[Decimal, ...] = (
        Decimal("50"),
        Decimal("100"),
        Decimal("300"),
    )
    sunshine_rank_bounds: Tuple[Decimal, ...] = (
        Decimal("50"),
        Decimal("200"),
        Decimal("600"),
    )
    do_nothing_label: str = DO_NOTHING

    def __post_init__(self) -> None:
        n_zones = len(self.zone_names)
        if n_zones == 0:
            raise QGapCoreError(f"{self.name}: at least one zone is required")
        if len(self.goal_ranks) != n_zones or len(self.ambient_levels) != n_zones:
            raise QGapCoreError(f"{self.name}: zone/goal/ambient lengths differ")
        if len(set(self.zone_names)) != n_zones:
            raise QGapCoreError(f"{self.name}: duplicate zone name")

        components = [act.component for act in self.actuators]
        if len(set(components)) != len(components):
            raise QGapCoreError(f"{self.name}: duplicate actuator component")
        labels = list(self.action_labels)
        if len(set(labels)) != len(labels):
            raise QGapCoreError(f"{self.name}: duplicate action label")

        for actuator in self.actuators:
            if len(actuator.fixed_effects) != n_zones:
                raise QGapCoreError(
                    f"{self.name}/{actuator.component}: fixed-effect width mismatch")
            if len(actuator.sunshine_effects) != n_zones:
                raise QGapCoreError(
                    f"{self.name}/{actuator.component}: sunshine-effect width mismatch")
            for zone in actuator.primary_zones + actuator.cross_zone_targets:
                if zone < 0 or zone >= n_zones:
                    raise QGapCoreError(
                        f"{self.name}/{actuator.component}: invalid zone {zone}")

        bit_slots: List[str] = []
        sunshine_slots = 0
        for slot in self.state_slots:
            if slot.domain_size <= 0:
                raise QGapCoreError(f"{self.name}/{slot.name}: invalid domain size")
            if slot.kind == SlotKind.ZONE_RANK:
                if slot.zone_index is None or not 0 <= slot.zone_index < n_zones:
                    raise QGapCoreError(
                        f"{self.name}/{slot.name}: invalid zone-rank slot")
            elif slot.kind == SlotKind.ACTUATOR_BIT:
                if slot.component not in components:
                    raise QGapCoreError(
                        f"{self.name}/{slot.name}: unknown actuator component")
                bit_slots.append(str(slot.component))
            elif slot.kind == SlotKind.SUNSHINE_RANK:
                sunshine_slots += 1
        if sorted(bit_slots) != sorted(components):
            raise QGapCoreError(
                f"{self.name}: state slots must contain each actuator exactly once")
        if sunshine_slots > 1:
            raise QGapCoreError(f"{self.name}: multiple sunshine-rank slots")

    @property
    def action_specs(self) -> Tuple[ActionSpec, ...]:
        actions: List[ActionSpec] = []
        for actuator in self.actuators:
            actions.append(ActionSpec(actuator.off_label, actuator.component, False))
            actions.append(ActionSpec(actuator.on_label, actuator.component, True))
        actions.append(ActionSpec(self.do_nothing_label, None, None))
        return tuple(actions)

    @property
    def action_labels(self) -> Tuple[str, ...]:
        return tuple(action.label for action in self.action_specs)

    @property
    def domain_sizes(self) -> Tuple[int, ...]:
        return tuple(slot.domain_size for slot in self.state_slots)

    @property
    def state_count(self) -> int:
        product = 1
        for domain in self.domain_sizes:
            product *= domain
        return product

    @property
    def has_sunshine_slot(self) -> bool:
        return any(slot.kind == SlotKind.SUNSHINE_RANK for slot in self.state_slots)

    def actuator(self, component: str) -> ActuatorSpec:
        for actuator in self.actuators:
            if actuator.component == component:
                return actuator
        raise QGapCoreError(f"{self.name}: unknown component {component!r}")

    def action(self, label: str) -> ActionSpec:
        for action in self.action_specs:
            if action.label == label:
                return action
        raise QGapCoreError(f"{self.name}: unknown action label {label!r}")

    def actuator_index(self, component: str) -> int:
        for index, actuator in enumerate(self.actuators):
            if actuator.component == component:
                return index
        raise QGapCoreError(f"{self.name}: unknown component {component!r}")


@dataclass(frozen=True)
class SettledState:
    """Hashable physical state; zone levels/ranks are derived, never trusted."""

    actuator_bits: Tuple[int, ...]
    sunshine: Decimal


def discretize_rank(value: Decimal, bounds: Sequence[Decimal]) -> int:
    """Match ``LabEnvironment.discretize``: first strict upper bound wins."""
    for rank, upper in enumerate(bounds):
        if value < upper:
            return rank
    return len(bounds)


def mixed_radix_strides(domain_sizes: Sequence[int]) -> Tuple[int, ...]:
    """Build the right-to-left strides used by ``QLearner``."""
    if not domain_sizes or any(domain <= 0 for domain in domain_sizes):
        raise QGapCoreError("domain sizes must be a non-empty positive sequence")
    strides = [0] * len(domain_sizes)
    product = 1
    for index in range(len(domain_sizes) - 1, -1, -1):
        strides[index] = product
        product *= int(domain_sizes[index])
    return tuple(strides)


def encode_state_vector(
    values: Sequence[int],
    domain_sizes: Sequence[int],
    *,
    clamp_like_java: bool = False,
) -> int:
    """Encode a mixed-radix vector, optionally applying Java's clamp behavior."""
    if len(values) != len(domain_sizes):
        raise QGapCoreError("state vector and domain sizes have different lengths")
    strides = mixed_radix_strides(domain_sizes)
    index = 0
    for position, (raw_value, domain, stride) in enumerate(
            zip(values, domain_sizes, strides)):
        value = int(raw_value)
        if clamp_like_java:
            value = max(0, min(value, int(domain) - 1))
        elif value < 0 or value >= int(domain):
            raise QGapCoreError(
                f"state slot {position}={value} outside [0,{int(domain) - 1}]")
        index += value * stride
    return index


@dataclass(frozen=True)
class SparseQTable:
    """Combined Q-values in frozen runtime action-label order."""

    action_labels: Tuple[str, ...]
    n_states: int
    rows: Mapping[int, Tuple[Decimal, ...]]

    def __post_init__(self) -> None:
        if self.n_states <= 0:
            raise QTableFormatError("n_states must be positive")
        if not self.action_labels or len(set(self.action_labels)) != len(self.action_labels):
            raise QTableFormatError("expected action labels must be non-empty and unique")
        normalized: Dict[int, Tuple[Decimal, ...]] = {}
        for state_index, row in self.rows.items():
            if not 0 <= int(state_index) < self.n_states:
                raise QTableFormatError(f"state index out of range: {state_index}")
            if int(state_index) in normalized:
                raise QTableFormatError(f"duplicate state index: {state_index}")
            values = tuple(row)
            if len(values) != len(self.action_labels):
                raise QTableFormatError(
                    f"state {state_index}: expected {len(self.action_labels)} Q-values")
            for value in values:
                if not isinstance(value, Decimal) or not value.is_finite():
                    raise QTableFormatError(
                        f"state {state_index}: Q-values must be finite Decimal values")
                if value.as_tuple().exponent != -2:
                    raise QTableFormatError(
                        f"state {state_index}: Q-value {value!s} is not serialized at 2dp")
            normalized[int(state_index)] = values
        object.__setattr__(self, "rows", MappingProxyType(normalized))

    def row(self, state_index: int) -> Tuple[Decimal, ...]:
        if not 0 <= int(state_index) < self.n_states:
            raise QGapCoreError(f"Q-table state index out of range: {state_index}")
        present = self.rows.get(int(state_index))
        if present is not None:
            return present
        return tuple(ZERO_Q for _ in self.action_labels)

    def value(self, state_index: int, action_label: str) -> Decimal:
        try:
            action_index = self.action_labels.index(action_label)
        except ValueError as exc:
            raise QGapCoreError(f"Q-table has no action {action_label!r}") from exc
        return self.row(state_index)[action_index]

    def greedy_action(
        self,
        state_index: int,
        allowed_actions: Optional[Iterable[str]] = None,
    ) -> str:
        """Argmax with exact Decimal comparison and lowest runtime-index ties."""
        allowed = (set(self.action_labels) if allowed_actions is None
                   else set(allowed_actions))
        if not allowed:
            raise QGapCoreError("greedy action requested from an empty action set")
        unknown = allowed.difference(self.action_labels)
        if unknown:
            raise QGapCoreError(f"unknown allowed action(s): {sorted(unknown)}")
        values = self.row(state_index)
        best_label: Optional[str] = None
        best_value: Optional[Decimal] = None
        for index, label in enumerate(self.action_labels):
            if label not in allowed:
                continue
            value = values[index]
            if best_value is None or value > best_value:
                best_label = label
                best_value = value
        if best_label is None:  # guarded by non-empty ``allowed``
            raise QGapCoreError("no greedy action found")
        return best_label


def _validate_expected_labels(expected_action_labels: Sequence[str]) -> Tuple[str, ...]:
    labels = tuple(str(label) for label in expected_action_labels)
    if not labels or any(not label for label in labels):
        raise QTableFormatError("expected action labels must be non-empty")
    if len(set(labels)) != len(labels):
        raise QTableFormatError("duplicate expected action label")
    return labels


def parse_qtable_csv(
    text: str,
    expected_action_labels: Sequence[str],
    n_states: int,
) -> SparseQTable:
    """Parse a strict saver-format Q-table and remap columns by action label."""
    labels = _validate_expected_labels(expected_action_labels)
    if n_states <= 0:
        raise QTableFormatError("n_states must be positive")

    try:
        reader = csv.reader(io.StringIO(text.lstrip("\ufeff")), strict=True)
        raw_rows = list(reader)
    except csv.Error as exc:
        raise QTableFormatError(f"invalid CSV: {exc}") from exc
    while raw_rows and not raw_rows[0]:
        raw_rows.pop(0)
    if not raw_rows:
        raise QTableFormatError("Q-table is empty")

    header = raw_rows[0]
    if not header or header[0] != "StateIndex":
        raise QTableFormatError("first header cell must be 'StateIndex'")
    serialized_labels = tuple(header[1:])
    if not serialized_labels or any(not label for label in serialized_labels):
        raise QTableFormatError("serialized action labels must be non-empty")
    if len(set(serialized_labels)) != len(serialized_labels):
        raise QTableFormatError("duplicate serialized action label")
    missing = set(labels).difference(serialized_labels)
    extra = set(serialized_labels).difference(labels)
    if missing or extra:
        raise QTableFormatError(
            f"action-label mismatch: missing={sorted(missing)}, extra={sorted(extra)}")

    source_index = {label: index for index, label in enumerate(serialized_labels)}
    remap = tuple(source_index[label] for label in labels)
    parsed: Dict[int, Tuple[Decimal, ...]] = {}
    expected_width = len(serialized_labels) + 1
    for line_number, raw in enumerate(raw_rows[1:], start=2):
        if not raw:
            continue
        if len(raw) != expected_width:
            raise QTableFormatError(
                f"line {line_number}: expected {expected_width} fields, got {len(raw)}")
        token = raw[0]
        if not token.isdigit():
            raise QTableFormatError(
                f"line {line_number}: invalid StateIndex {token!r}")
        state_index = int(token)
        if state_index < 0 or state_index >= n_states:
            raise QTableFormatError(
                f"line {line_number}: StateIndex {state_index} outside [0,{n_states - 1}]")
        if state_index in parsed:
            raise QTableFormatError(
                f"line {line_number}: duplicate StateIndex {state_index}")

        source_values: List[Decimal] = []
        for column_number, value_text in enumerate(raw[1:], start=2):
            try:
                value = Decimal(value_text)
            except InvalidOperation as exc:
                raise QTableFormatError(
                    f"line {line_number}, column {column_number}: "
                    f"invalid Q-value {value_text!r}") from exc
            if not value.is_finite():
                raise QTableFormatError(
                    f"line {line_number}, column {column_number}: non-finite Q-value")
            if value.as_tuple().exponent != -2:
                raise QTableFormatError(
                    f"line {line_number}, column {column_number}: "
                    f"{value_text!r} is not serialized at exactly 2dp")
            source_values.append(value)
        parsed[state_index] = tuple(source_values[index] for index in remap)

    return SparseQTable(labels, n_states, parsed)


def load_qtable(
    path: Path,
    expected_action_labels: Sequence[str],
    n_states: int,
) -> SparseQTable:
    """Read a Q-table from an explicitly supplied path; no discovery is done."""
    return parse_qtable_csv(
        Path(path).read_text(encoding="utf-8-sig"),
        expected_action_labels,
        n_states,
    )


class FiniteSettledModel:
    """Deterministic finite model satisfying ``transition_checker``'s API."""

    def __init__(
        self,
        spec: ProfileSpec,
        initial_state: SettledState,
        *,
        fault_modes: Optional[Mapping[str, FaultMode | str]] = None,
        unavailable_actions: Iterable[str] = (),
        goal_ranks: Optional[Sequence[int]] = None,
    ) -> None:
        self.spec = spec
        self._validate_state(initial_state)
        self._initial_state = initial_state

        normalized_faults: Dict[str, FaultMode] = {}
        for component, raw_mode in (fault_modes or {}).items():
            spec.actuator(component)  # validates component
            try:
                mode = raw_mode if isinstance(raw_mode, FaultMode) else FaultMode(raw_mode)
            except ValueError as exc:
                raise QGapCoreError(
                    f"{spec.name}/{component}: invalid fault mode {raw_mode!r}") from exc
            if mode != FaultMode.HEALTHY:
                normalized_faults[component] = mode
        self.fault_modes = MappingProxyType(normalized_faults)

        effective_goal = (
            tuple(int(rank) for rank in goal_ranks)
            if goal_ranks is not None
            else spec.goal_ranks
        )
        if len(effective_goal) != len(spec.zone_names):
            raise QGapCoreError(f"{spec.name}: goal-rank width mismatch")
        maximum_rank = len(spec.light_rank_bounds)
        if any(rank < 0 or rank > maximum_rank for rank in effective_goal):
            raise QGapCoreError(f"{spec.name}: goal rank outside state domain")
        self.goal_ranks = effective_goal

        unavailable = frozenset(str(label) for label in unavailable_actions)
        unknown = unavailable.difference(spec.action_labels)
        if unknown:
            raise QGapCoreError(f"unknown unavailable action(s): {sorted(unknown)}")
        if spec.do_nothing_label in unavailable:
            raise QGapCoreError("DO_NOTHING may not be unavailable")
        self.unavailable_actions = unavailable

    @classmethod
    def from_scenario(
        cls,
        spec: ProfileSpec,
        scenario: Mapping[str, object],
        *,
        fault_modes: Optional[Mapping[str, FaultMode | str]] = None,
        unavailable_actions: Iterable[str] = (),
        goal_ranks: Optional[Sequence[int]] = None,
    ) -> "FiniteSettledModel":
        bits: List[int] = []
        for actuator in spec.actuators:
            if actuator.state_key not in scenario:
                raise QGapCoreError(
                    f"{spec.name}: scenario missing {actuator.state_key!r}")
            raw = scenario[actuator.state_key]
            if not isinstance(raw, bool):
                raise QGapCoreError(
                    f"{spec.name}: {actuator.state_key} must be a boolean")
            bits.append(1 if raw else 0)

        sunshine = Decimal("0")
        if spec.has_sunshine_slot:
            if "Sunshine" not in scenario:
                raise QGapCoreError(f"{spec.name}: scenario missing 'Sunshine'")
            try:
                sunshine = Decimal(str(scenario["Sunshine"]))
            except InvalidOperation as exc:
                raise QGapCoreError(
                    f"{spec.name}: invalid Sunshine {scenario['Sunshine']!r}") from exc
            if not sunshine.is_finite():
                raise QGapCoreError(f"{spec.name}: Sunshine must be finite")

        return cls(
            spec,
            SettledState(tuple(bits), sunshine),
            fault_modes=fault_modes,
            unavailable_actions=unavailable_actions,
            goal_ranks=goal_ranks,
        )

    def _validate_state(self, state: SettledState) -> None:
        if len(state.actuator_bits) != len(self.spec.actuators):
            raise QGapCoreError(
                f"{self.spec.name}: state has wrong actuator-bit width")
        if any(bit not in (0, 1) for bit in state.actuator_bits):
            raise QGapCoreError(f"{self.spec.name}: actuator bits must be 0/1")
        if not isinstance(state.sunshine, Decimal) or not state.sunshine.is_finite():
            raise QGapCoreError(f"{self.spec.name}: sunshine must be finite Decimal")

    def initial_state(self) -> SettledState:
        return self._initial_state

    def actions(self, state: SettledState) -> List[str]:
        self._validate_state(state)
        return [
            label for label in self.spec.action_labels
            if label not in self.unavailable_actions
        ]

    def step(self, state: SettledState, action_label: str) -> SettledState:
        self._validate_state(state)
        if action_label in self.unavailable_actions:
            raise QGapCoreError(f"action is unavailable: {action_label}")
        action = self.spec.action(action_label)
        if action.component is None:
            return state
        bits = list(state.actuator_bits)
        bits[self.spec.actuator_index(action.component)] = (
            1 if action.target_value else 0)
        return SettledState(tuple(bits), state.sunshine)

    def fault_mode(self, component: str) -> FaultMode:
        self.spec.actuator(component)
        return self.fault_modes.get(component, FaultMode.HEALTHY)

    def settled_levels(self, state: SettledState) -> Tuple[Decimal, ...]:
        self._validate_state(state)
        levels = list(self.spec.ambient_levels)
        for index, actuator in enumerate(self.spec.actuators):
            if state.actuator_bits[index] == 0:
                continue
            mode = self.fault_mode(actuator.component)
            multiplier = {
                FaultMode.HEALTHY: Decimal("1"),
                FaultMode.DEAD: Decimal("0"),
                FaultMode.INVERTED: Decimal("-1"),
            }[mode]
            for zone in range(len(levels)):
                contribution = (
                    actuator.fixed_effects[zone]
                    + actuator.sunshine_effects[zone] * state.sunshine
                )
                levels[zone] += multiplier * contribution
        return tuple(levels)

    def zone_ranks(self, state: SettledState) -> Tuple[int, ...]:
        return tuple(
            discretize_rank(level, self.spec.light_rank_bounds)
            for level in self.settled_levels(state)
        )

    def sunshine_rank(self, state: SettledState) -> int:
        return discretize_rank(state.sunshine, self.spec.sunshine_rank_bounds)

    def state_vector(self, state: SettledState) -> Tuple[int, ...]:
        ranks = self.zone_ranks(state)
        vector: List[int] = []
        for slot in self.spec.state_slots:
            if slot.kind == SlotKind.ZONE_RANK:
                vector.append(ranks[int(slot.zone_index)])
            elif slot.kind == SlotKind.ACTUATOR_BIT:
                vector.append(
                    state.actuator_bits[self.spec.actuator_index(str(slot.component))])
            elif slot.kind == SlotKind.SUNSHINE_RANK:
                vector.append(self.sunshine_rank(state))
            else:  # pragma: no cover - Enum construction prevents this
                raise QGapCoreError(f"unknown slot kind: {slot.kind}")
        return tuple(vector)

    def state_index(self, state: SettledState) -> int:
        return encode_state_vector(self.state_vector(state), self.spec.domain_sizes)

    def is_goal(self, state: SettledState) -> bool:
        return self.zone_ranks(state) == self.goal_ranks

    def complete_reachability_horizon(self) -> int:
        """A proof-complete shortest-path bound for the fixed-sun bit state.

        Sunshine is immutable within a scenario and settled zone ranks are pure
        functions of the actuator bits.  There are therefore exactly
        ``2 ** n_actuators`` possible physical states.  A shortest successful
        path never repeats a state, so ``N - 1`` transitions are sufficient to
        decide reachability without imposing an experimental step horizon.
        """
        return (1 << len(self.spec.actuators)) - 1

    def with_unavailable_actions(
        self,
        unavailable_actions: Iterable[str],
    ) -> "FiniteSettledModel":
        return FiniteSettledModel(
            self.spec,
            self._initial_state,
            fault_modes=self.fault_modes,
            unavailable_actions=unavailable_actions,
            goal_ranks=self.goal_ranks,
        )


def fault_action_labels(
    spec: ProfileSpec,
    components: Sequence[str],
) -> Tuple[str, ...]:
    """Return both polarities of each component in runtime action order."""
    if not components:
        raise QGapCoreError("at least one faulty component is required")
    if len(set(components)) != len(components):
        raise QGapCoreError("duplicate faulty component")
    requested = set(components)
    for component in requested:
        spec.actuator(component)
    labels: List[str] = []
    for actuator in spec.actuators:
        if actuator.component in requested:
            labels.extend((actuator.off_label, actuator.on_label))
    return tuple(labels)


@dataclass(frozen=True)
class ScenarioQGapResult:
    classification: ScenarioClassification
    state_index: int
    shortest_path_length: Optional[int]
    shortest_sequence_count: int
    shortest_first_actions: Tuple[str, ...]
    faulty_action_labels: Tuple[str, ...]
    max_faulty_q: Optional[Decimal]
    max_survivor_q: Optional[Decimal]
    faulty_maximizers: Tuple[str, ...]
    survivor_maximizers: Tuple[str, ...]
    relevant_maximum_tied: Optional[bool]
    signed_gap: Optional[Decimal]
    signed_gap_is_zero: Optional[bool]
    burden: Optional[Decimal]


def evaluate_start_state_qgap(
    model: FiniteSettledModel,
    qtable: SparseQTable,
    faulty_actions: Sequence[str],
) -> ScenarioQGapResult:
    """Evaluate one settled scenario with proof-complete finite reachability."""
    if qtable.action_labels != model.spec.action_labels:
        raise QGapCoreError("Q-table/runtime action orders differ")
    if qtable.n_states != model.spec.state_count:
        raise QGapCoreError("Q-table/profile state counts differ")
    faulty = tuple(faulty_actions)
    if not faulty or len(set(faulty)) != len(faulty):
        raise QGapCoreError("faulty action labels must be non-empty and unique")
    unknown = set(faulty).difference(model.spec.action_labels)
    if unknown:
        raise QGapCoreError(f"unknown faulty action(s): {sorted(unknown)}")
    if set(faulty) != set(model.unavailable_actions):
        raise QGapCoreError(
            "model unavailable actions must exactly equal the faulty action set")

    initial = model.initial_state()
    state_index = model.state_index(initial)
    if model.is_goal(initial):
        return ScenarioQGapResult(
            ScenarioClassification.NO_RERANKING_NEEDED,
            state_index,
            0,
            1,
            (),
            faulty,
            None,
            None,
            (),
            (),
            None,
            None,
            None,
            None,
        )

    complete_horizon = model.complete_reachability_horizon()
    if complete_horizon < 0:
        raise QGapCoreError("complete reachability horizon must be non-negative")
    checked = check_scenario(model, horizon=complete_horizon)
    if not checked.solvable:
        return ScenarioQGapResult(
            ScenarioClassification.UNREACHABLE,
            state_index,
            None,
            0,
            (),
            faulty,
            None,
            None,
            (),
            (),
            None,
            None,
            None,
            None,
        )

    first_actions = tuple(checked.shortest_first_actions)
    if not first_actions:
        raise QGapCoreError("reachable non-terminal scenario has no shortest first action")
    row = qtable.row(state_index)
    action_index = {
        label: index for index, label in enumerate(qtable.action_labels)
    }
    max_faulty = max(row[action_index[label]] for label in faulty)
    max_survivor = max(row[action_index[label]] for label in first_actions)
    faulty_set = set(faulty)
    survivor_set = set(first_actions)
    faulty_maximizers = tuple(
        label for label in qtable.action_labels
        if label in faulty_set and row[action_index[label]] == max_faulty
    )
    survivor_maximizers = tuple(
        label for label in qtable.action_labels
        if label in survivor_set and row[action_index[label]] == max_survivor
    )
    signed = max_faulty - max_survivor
    burden = max(ZERO_Q, signed)
    return ScenarioQGapResult(
        ScenarioClassification.ANALYZED,
        state_index,
        checked.shortest_path_length,
        checked.shortest_sequence_count,
        first_actions,
        faulty,
        max_faulty,
        max_survivor,
        faulty_maximizers,
        survivor_maximizers,
        len(faulty_maximizers) > 1 or len(survivor_maximizers) > 1,
        signed,
        signed == ZERO_Q,
        burden,
    )


@dataclass(frozen=True)
class DetectorObservation:
    action_label: str
    component: Optional[str]
    falsifiable: bool
    evidence: DetectorEvidence
    masked: bool
    reason: str
    claimed_zones: Tuple[int, ...] = ()

    @property
    def is_opportunity(self) -> bool:
        return self.evidence in (DetectorEvidence.DEAD, DetectorEvidence.INVERTED)


def masking_cofeeder_present(
    model: FiniteSettledModel,
    before: SettledState,
    zone: int,
    self_component: str,
) -> bool:
    """Mirror detector-v2's static active co-feeder maskability predicate."""
    if zone < 0 or zone >= len(model.spec.zone_names):
        raise QGapCoreError(f"invalid zone index: {zone}")
    model.spec.actuator(self_component)
    for index, actuator in enumerate(model.spec.actuators):
        if actuator.component == self_component:
            continue
        feeds_zone = (
            zone in actuator.primary_zones
            or zone in actuator.cross_zone_targets
        )
        if feeds_zone and before.actuator_bits[index] == 1:
            return True
    return False


def evaluate_detector_observation(
    model: FiniteSettledModel,
    before: SettledState,
    action_label: str,
    after: Optional[SettledState] = None,
) -> DetectorObservation:
    """Apply detector-v2's pre-first-blacklist static logic to one transition.

    Detector v2 blacklists on the first chargeable anomaly, so suspect anomaly
    counters cannot precede that first opportunity.  The descriptor therefore
    fixes blacklist, contaminated-zone, and suspect history empty on every
    transition, including transitions inspected after an earlier descriptor
    opportunity; it does not synthesize post-opportunity runtime state.
    """
    action = model.spec.action(action_label)
    if action.component is None:
        return DetectorObservation(
            action_label, None, False, DetectorEvidence.NONE, False, "do_nothing")
    actuator = model.spec.actuator(action.component)
    if actuator.kg_silent:
        return DetectorObservation(
            action_label, action.component, False, DetectorEvidence.NONE,
            False, "kg_silent")
    if len(actuator.primary_zones) > 1:
        return DetectorObservation(
            action_label, action.component, False, DetectorEvidence.NONE,
            False, "multi_zone")

    if actuator.iv_gated:
        if action.target_value is not True:
            return DetectorObservation(
                action_label, action.component, False, DetectorEvidence.NONE,
                False, "iv_close")
        if model.sunshine_rank(before) < 2:
            return DetectorObservation(
                action_label, action.component, False, DetectorEvidence.NONE,
                False, "iv_below_minimum")

    after_state = model.step(before, action_label) if after is None else after
    model._validate_state(after_state)
    bit_index = model.spec.actuator_index(action.component)
    before_bit = before.actuator_bits[bit_index]
    after_bit = after_state.actuator_bits[bit_index]
    expected_bit = 1 if action.target_value else 0
    bit_prediction = expected_bit - before_bit
    if bit_prediction == 0:
        return DetectorObservation(
            action_label, action.component, False, DetectorEvidence.NONE,
            False, "redundant")

    bit_observed = after_bit - before_bit
    if bit_observed == 0:
        return DetectorObservation(
            action_label, action.component, True, DetectorEvidence.DEAD,
            False, "command_dropped")
    if bit_observed != bit_prediction:
        return DetectorObservation(
            action_label, action.component, False, DetectorEvidence.NONE,
            False, "unexpected_bit_transition")

    before_ranks = model.zone_ranks(before)
    after_ranks = model.zone_ranks(after_state)
    predicted_direction = 1 if action.target_value else -1
    claimed = 0
    no_response = 0
    opposite = 0
    ambiguous = False
    claimed_zones: List[int] = []
    for zone in actuator.primary_zones:
        maximum_rank = len(model.spec.light_rank_bounds)
        if predicted_direction > 0 and before_ranks[zone] >= maximum_rank:
            continue
        if predicted_direction < 0 and before_ranks[zone] <= 0:
            continue
        observed_direction = after_ranks[zone] - before_ranks[zone]
        if observed_direction != 0 and observed_direction * predicted_direction < 0:
            claimed += 1
            opposite += 1
            claimed_zones.append(zone)
        elif observed_direction == 0:
            if masking_cofeeder_present(
                    model, before, zone, action.component):
                ambiguous = True
                continue
            claimed += 1
            no_response += 1
            claimed_zones.append(zone)
        else:
            claimed += 1
            claimed_zones.append(zone)

    if opposite > 0:
        return DetectorObservation(
            action_label, action.component, True, DetectorEvidence.INVERTED,
            False, "opposite_rank_response", tuple(claimed_zones))
    if ambiguous:
        return DetectorObservation(
            action_label, action.component, True, DetectorEvidence.NONE,
            True, "active_cofeeder_mask", tuple(claimed_zones))
    if claimed == 0:
        return DetectorObservation(
            action_label, action.component, False, DetectorEvidence.NONE,
            False, "no_falsifiable_zone")
    if no_response == claimed:
        return DetectorObservation(
            action_label, action.component, True, DetectorEvidence.DEAD,
            False, "unmasked_no_response", tuple(claimed_zones))
    return DetectorObservation(
        action_label, action.component, True, DetectorEvidence.NONE,
        False, "correct_rank_response", tuple(claimed_zones))


@dataclass(frozen=True)
class DetectorRolloutResult:
    opportunity_by_component: Mapping[str, bool]
    first_opportunity_step: Mapping[str, Optional[int]]
    any_fault_component_opportunity: bool
    action_trace: Tuple[str, ...]
    observation_trace: Tuple[DetectorObservation, ...]
    terminated_at_goal: bool
    final_state_index: int

    @property
    def any_fault_opportunity(self) -> bool:
        """Short alias retained for callers that do not emit schema fields."""
        return self.any_fault_component_opportunity

    @property
    def all_fault_components_opportunity(self) -> bool:
        return all(self.opportunity_by_component.values())


def run_detector_opportunity_rollout(
    model: FiniteSettledModel,
    qtable: SparseQTable,
    faulty_components: Sequence[str],
    *,
    horizon: int = 20,
) -> DetectorRolloutResult:
    """Run the frozen no-learning/no-probe/no-blacklist greedy descriptor."""
    if horizon < 0:
        raise QGapCoreError("horizon must be non-negative")
    if model.unavailable_actions:
        raise QGapCoreError(
            "detector-opportunity rollout must run before any action blacklist")
    if qtable.action_labels != model.spec.action_labels:
        raise QGapCoreError("Q-table/runtime action orders differ")
    if qtable.n_states != model.spec.state_count:
        raise QGapCoreError("Q-table/profile state counts differ")
    components = tuple(faulty_components)
    if not components or len(set(components)) != len(components):
        raise QGapCoreError("faulty components must be non-empty and unique")
    for component in components:
        model.spec.actuator(component)
        if model.fault_mode(component) == FaultMode.HEALTHY:
            raise QGapCoreError(
                f"component {component!r} is not faulty in the supplied model")

    opportunities: Dict[str, bool] = {component: False for component in components}
    first_steps: Dict[str, Optional[int]] = {
        component: None for component in components
    }
    actions: List[str] = []
    observations: List[DetectorObservation] = []
    state = model.initial_state()
    terminated_at_goal = model.is_goal(state)
    for step_number in range(1, horizon + 1):
        if model.is_goal(state):
            terminated_at_goal = True
            break
        state_index = model.state_index(state)
        action_label = qtable.greedy_action(state_index, model.actions(state))
        after = model.step(state, action_label)
        observation = evaluate_detector_observation(
            model, state, action_label, after)
        actions.append(action_label)
        observations.append(observation)
        if (
            observation.component in opportunities
            and observation.is_opportunity
        ):
            component = str(observation.component)
            opportunities[component] = True
            if first_steps[component] is None:
                first_steps[component] = step_number
        state = after
    else:
        terminated_at_goal = model.is_goal(state)

    frozen_opportunities = MappingProxyType(dict(opportunities))
    frozen_first_steps = MappingProxyType(dict(first_steps))
    return DetectorRolloutResult(
        frozen_opportunities,
        frozen_first_steps,
        any(opportunities.values()),
        tuple(actions),
        tuple(observations),
        terminated_at_goal,
        model.state_index(state),
    )


def _decimals(*values: str) -> Tuple[Decimal, ...]:
    return tuple(Decimal(value) for value in values)


def _zone_slot(name: str, zone: int) -> StateSlotSpec:
    return StateSlotSpec(name, SlotKind.ZONE_RANK, 4, zone_index=zone)


def _bit_slot(component: str) -> StateSlotSpec:
    return StateSlotSpec(
        component, SlotKind.ACTUATOR_BIT, 2, component=component)


def _sun_slot() -> StateSlotSpec:
    return StateSlotSpec("Sunshine", SlotKind.SUNSHINE_RANK, 4)


LAB2_SPEC = ProfileSpec(
    name="lab2",
    zone_names=("Z1", "Z2"),
    goal_ranks=(3, 3),
    ambient_levels=_decimals("25", "25"),
    actuators=(
        ActuatorSpec(
            "Z1Blinds", "Z1Blinds", "SetZ1Blinds=OFF", "SetZ1Blinds=ON",
            (0,), _decimals("0", "0"), _decimals("0.50", "0"),
            iv_gated=True,
        ),
        ActuatorSpec(
            "Z1Light", "Z1Light", "SetZ1Light=OFF", "SetZ1Light=ON",
            (0,), _decimals("400", "0"), _decimals("0", "0"),
        ),
        ActuatorSpec(
            "Z2Blinds", "Z2Blinds", "SetZ2Blinds=OFF", "SetZ2Blinds=ON",
            (1,), _decimals("0", "0"), _decimals("0", "0.50"),
            iv_gated=True,
        ),
        ActuatorSpec(
            "Z2Light", "Z2Light", "SetZ2Light=OFF", "SetZ2Light=ON",
            (1,), _decimals("0", "400"), _decimals("0", "0"),
        ),
    ),
    state_slots=(
        _zone_slot("Z1Level", 0),
        _zone_slot("Z2Level", 1),
        _bit_slot("Z1Light"),
        _bit_slot("Z2Light"),
        _bit_slot("Z1Blinds"),
        _bit_slot("Z2Blinds"),
        _sun_slot(),
    ),
)


LAB3_SPEC = ProfileSpec(
    name="lab3",
    zone_names=("Z1", "Z2"),
    goal_ranks=(3, 3),
    ambient_levels=_decimals("25", "25"),
    actuators=(
        ActuatorSpec(
            "Spotlight", "Spotlight", "SetSpotlight=OFF", "SetSpotlight=ON",
            (0, 1), _decimals("150", "150"), _decimals("0", "0"),
        ),
        ActuatorSpec(
            "Z1Blinds", "Z1Blinds", "SetZ1Blinds=OFF", "SetZ1Blinds=ON",
            (0,), _decimals("0", "0"), _decimals("0.50", "0.30"),
            cross_zone_targets=(1,), iv_gated=True,
        ),
        ActuatorSpec(
            "Z1Light", "Z1Light", "SetZ1Light=OFF", "SetZ1Light=ON",
            (0,), _decimals("400", "100"), _decimals("0", "0"),
            cross_zone_targets=(1,),
        ),
        ActuatorSpec(
            "Z2Blinds", "Z2Blinds", "SetZ2Blinds=OFF", "SetZ2Blinds=ON",
            (1,), _decimals("0", "0"), _decimals("0.30", "0.50"),
            cross_zone_targets=(0,), iv_gated=True,
        ),
        ActuatorSpec(
            "Z2Light", "Z2Light", "SetZ2Light=OFF", "SetZ2Light=ON",
            (1,), _decimals("100", "400"), _decimals("0", "0"),
            cross_zone_targets=(0,),
        ),
    ),
    state_slots=(
        _zone_slot("Z1Level", 0),
        _zone_slot("Z2Level", 1),
        _bit_slot("Z1Light"),
        _bit_slot("Z2Light"),
        _bit_slot("Z1Blinds"),
        _bit_slot("Z2Blinds"),
        _bit_slot("Spotlight"),
        _sun_slot(),
    ),
)


LABMON_SPEC = ProfileSpec(
    name="labmon",
    zone_names=("Z1",),
    goal_ranks=(3,),
    ambient_levels=_decimals("25"),
    actuators=(
        ActuatorSpec(
            "Z1Light", "Z1Light", "SetZ1Light=OFF", "SetZ1Light=ON",
            (0,), _decimals("400"), _decimals("0"),
        ),
        ActuatorSpec(
            "Z1Monitor", "Z1Monitor", "SetZ1Monitor=OFF", "SetZ1Monitor=ON",
            (0,), _decimals("260"), _decimals("0"),
        ),
    ),
    state_slots=(
        _zone_slot("Z1Level", 0),
        _bit_slot("Z1Light"),
        _bit_slot("Z1Monitor"),
    ),
)


LABMON2_SPEC = ProfileSpec(
    name="labmon2",
    zone_names=("Z1", "Z2"),
    goal_ranks=(3, 3),
    ambient_levels=_decimals("25", "25"),
    actuators=(
        ActuatorSpec(
            "Z1Blinds", "Z1Blinds", "SetZ1Blinds=OFF", "SetZ1Blinds=ON",
            (0,), _decimals("0", "0"), _decimals("0.50", "0"),
            iv_gated=True,
        ),
        ActuatorSpec(
            "Z1Light", "Z1Light", "SetZ1Light=OFF", "SetZ1Light=ON",
            (0,), _decimals("400", "0"), _decimals("0", "0"),
        ),
        ActuatorSpec(
            "Z1Monitor", "Z1Monitor", "SetZ1Monitor=OFF", "SetZ1Monitor=ON",
            (0,), _decimals("200", "0"), _decimals("0", "0"),
        ),
        ActuatorSpec(
            "Z2Blinds", "Z2Blinds", "SetZ2Blinds=OFF", "SetZ2Blinds=ON",
            (1,), _decimals("0", "0"), _decimals("0", "0.50"),
            iv_gated=True,
        ),
        ActuatorSpec(
            "Z2Light", "Z2Light", "SetZ2Light=OFF", "SetZ2Light=ON",
            (1,), _decimals("0", "400"), _decimals("0", "0"),
        ),
        ActuatorSpec(
            "Z2Monitor", "Z2Monitor", "SetZ2Monitor=OFF", "SetZ2Monitor=ON",
            (1,), _decimals("0", "200"), _decimals("0", "0"),
        ),
    ),
    state_slots=(
        _zone_slot("Z1Level", 0),
        _zone_slot("Z2Level", 1),
        _bit_slot("Z1Light"),
        _bit_slot("Z2Light"),
        _bit_slot("Z1Monitor"),
        _bit_slot("Z2Monitor"),
        _bit_slot("Z1Blinds"),
        _bit_slot("Z2Blinds"),
        _sun_slot(),
    ),
)


PROFILE_SPECS: Mapping[str, ProfileSpec] = MappingProxyType({
    spec.name: spec
    for spec in (LAB2_SPEC, LAB3_SPEC, LABMON_SPEC, LABMON2_SPEC)
})


def get_profile_spec(name: str) -> ProfileSpec:
    try:
        return PROFILE_SPECS[name]
    except KeyError as exc:
        raise QGapCoreError(f"unknown profile spec {name!r}") from exc


@dataclass(frozen=True)
class CellAnalysisSpec:
    """Frozen cell-level overrides layered on a parent topology."""

    name: str
    parent_profile: str
    fault_components: Tuple[str, ...]
    fault_mode: FaultMode
    unavailable_actions: Tuple[str, ...]
    analysis_goal_ranks: Tuple[int, ...]

    @property
    def fault_modes(self) -> Mapping[str, FaultMode]:
        return MappingProxyType({
            component: self.fault_mode for component in self.fault_components
        })


def _json_decimal_tuple(values: Sequence[object]) -> Tuple[Decimal, ...]:
    try:
        converted = tuple(Decimal(str(value)) for value in values)
    except InvalidOperation as exc:
        raise QGapCoreError(f"invalid decimal sequence: {values!r}") from exc
    if any(not value.is_finite() for value in converted):
        raise QGapCoreError(f"non-finite decimal sequence: {values!r}")
    return converted


def load_frozen_cell_specs(path: Path) -> Mapping[str, CellAnalysisSpec]:
    """Load and cross-check the declarative Stage-2 JSON core contract.

    Only the topology/action/physics/cell declarations are consumed.  Artifact
    locations and outcomes remain outside this synthetic core.
    """
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QGapCoreError(f"cannot load frozen spec {path}: {exc}") from exc

    if document.get("schema_version") != "phase2-qgap-retrospective-v1":
        raise QGapCoreError("unexpected frozen-spec schema_version")
    state_contract = document.get("state_contract")
    action_metadata = document.get("action_metadata")
    raw_cells = document.get("cells")
    if not isinstance(state_contract, dict) or not isinstance(action_metadata, dict):
        raise QGapCoreError("frozen spec lacks state/action contracts")
    if not isinstance(raw_cells, dict):
        raise QGapCoreError("frozen spec lacks cell declarations")
    raw_parents = state_contract.get("parents")
    if not isinstance(raw_parents, dict):
        raise QGapCoreError("frozen spec lacks parent declarations")

    for profile_name, profile in PROFILE_SPECS.items():
        raw_parent = raw_parents.get(profile_name)
        raw_actions = action_metadata.get(profile_name)
        if not isinstance(raw_parent, dict) or not isinstance(raw_actions, dict):
            raise QGapCoreError(
                f"frozen spec lacks declarations for parent {profile_name}")
        expected_state_labels = tuple(slot.name for slot in profile.state_slots)
        if tuple(raw_parent.get("state_labels", ())) != expected_state_labels:
            raise QGapCoreError(f"{profile_name}: frozen state labels drifted")
        if tuple(raw_parent.get("domains", ())) != profile.domain_sizes:
            raise QGapCoreError(f"{profile_name}: frozen domains drifted")
        if tuple(raw_parent.get("strides", ())) != mixed_radix_strides(
                profile.domain_sizes):
            raise QGapCoreError(f"{profile_name}: frozen strides drifted")
        if raw_parent.get("n_states") != profile.state_count:
            raise QGapCoreError(f"{profile_name}: frozen state count drifted")
        if tuple(raw_parent.get("action_labels", ())) != profile.action_labels:
            raise QGapCoreError(f"{profile_name}: frozen action order drifted")

        if set(raw_actions) != {act.component for act in profile.actuators}:
            raise QGapCoreError(f"{profile_name}: frozen action components drifted")
        for actuator in profile.actuators:
            declared = raw_actions[actuator.component]
            expected_metadata = {
                "affected_zones": list(actuator.primary_zones),
                "cross_zones": list(actuator.cross_zone_targets),
                "iv_gated": actuator.iv_gated,
                "state_label": actuator.state_key,
            }
            if declared != expected_metadata:
                raise QGapCoreError(
                    f"{profile_name}/{actuator.component}: action metadata drifted")

    cells: Dict[str, CellAnalysisSpec] = {}
    for cell_name, raw_cell in raw_cells.items():
        if not isinstance(raw_cell, dict):
            raise QGapCoreError(f"{cell_name}: cell declaration must be an object")
        parent_name = str(raw_cell.get("parent_profile", ""))
        profile = get_profile_spec(parent_name)
        raw_components = raw_cell.get("fault_components")
        if not isinstance(raw_components, list) or not raw_components:
            raise QGapCoreError(f"{cell_name}: invalid fault_components")
        components = tuple(str(component) for component in raw_components)
        if len(set(components)) != len(components):
            raise QGapCoreError(f"{cell_name}: duplicate fault component")
        for component in components:
            profile.actuator(component)
        try:
            mode = FaultMode(str(raw_cell.get("fault_kind")))
        except ValueError as exc:
            raise QGapCoreError(f"{cell_name}: invalid fault_kind") from exc
        unavailable = tuple(str(label) for label in raw_cell.get(
            "unavailable_actions", ()))
        if unavailable != fault_action_labels(profile, components):
            raise QGapCoreError(f"{cell_name}: unavailable action mapping drifted")
        goals = tuple(int(rank) for rank in raw_cell.get(
            "analysis_goal_ranks", ()))
        if len(goals) != len(profile.zone_names):
            raise QGapCoreError(f"{cell_name}: analysis goal width mismatch")

        physics = raw_cell.get("physics")
        if not isinstance(physics, dict):
            raise QGapCoreError(f"{cell_name}: missing physics declaration")
        if _json_decimal_tuple(physics.get("ambient", ())) != profile.ambient_levels:
            raise QGapCoreError(f"{cell_name}: ambient physics drifted")
        raw_fixed = physics.get("constant_effects", {})
        raw_sun = physics.get("sun_effects", {})
        if not isinstance(raw_fixed, dict) or not isinstance(raw_sun, dict):
            raise QGapCoreError(f"{cell_name}: malformed effect declarations")
        multiplier = {
            FaultMode.HEALTHY: Decimal("1"),
            FaultMode.DEAD: Decimal("0"),
            FaultMode.INVERTED: Decimal("-1"),
        }
        for actuator in profile.actuators:
            component_mode = mode if actuator.component in components else FaultMode.HEALTHY
            factor = multiplier[component_mode]
            expected_fixed = tuple(value * factor for value in actuator.fixed_effects)
            expected_sun = tuple(
                value * factor for value in actuator.sunshine_effects)
            declared_fixed = _json_decimal_tuple(
                raw_fixed.get(
                    actuator.component,
                    [0] * len(profile.zone_names),
                )
            )
            declared_sun = _json_decimal_tuple(
                raw_sun.get(
                    actuator.component,
                    [0] * len(profile.zone_names),
                )
            )
            if declared_fixed != expected_fixed:
                raise QGapCoreError(
                    f"{cell_name}/{actuator.component}: constant physics drifted")
            if declared_sun != expected_sun:
                raise QGapCoreError(
                    f"{cell_name}/{actuator.component}: sunshine physics drifted")

        cells[cell_name] = CellAnalysisSpec(
            cell_name,
            parent_name,
            components,
            mode,
            unavailable,
            goals,
        )
    return MappingProxyType(cells)


def build_cell_model(
    cell: CellAnalysisSpec,
    scenario: Mapping[str, object],
    *,
    apply_unavailable_actions: bool,
) -> FiniteSettledModel:
    """Build either the survivor model or the pre-blacklist detector model."""
    profile = get_profile_spec(cell.parent_profile)
    unavailable = cell.unavailable_actions if apply_unavailable_actions else ()
    return FiniteSettledModel.from_scenario(
        profile,
        scenario,
        fault_modes=cell.fault_modes,
        unavailable_actions=unavailable,
        goal_ranks=cell.analysis_goal_ranks,
    )
