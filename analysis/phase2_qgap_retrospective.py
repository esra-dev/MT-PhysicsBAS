"""Deterministic Phase-2 start-state Q-gap proxy retrospective.

The artifact checker owns discovery, provenance, and immutable joins.  This
module consumes only its checked ``InputRecord`` objects and performs the
frozen descriptive computation.  All Q comparisons use ``Decimal`` values;
all aggregates, ranks, orderings, and screening gates use ``Fraction`` values.
Binary floating point is introduced only for plotting and human-readable
display columns.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

try:
    from analysis.phase2_qgap_core import (
        ScenarioClassification,
        SparseQTable,
        build_cell_model,
        evaluate_start_state_qgap,
        get_profile_spec,
        load_frozen_cell_specs,
        load_qtable,
        run_detector_opportunity_rollout,
    )
except ImportError:  # pragma: no cover - direct script-style import
    from phase2_qgap_core import (  # type: ignore
        ScenarioClassification,
        SparseQTable,
        build_cell_model,
        evaluate_start_state_qgap,
        get_profile_spec,
        load_frozen_cell_specs,
        load_qtable,
        run_detector_opportunity_rollout,
    )

try:
    from analysis.validate_phase2_qgap_inputs import validate_inputs
except ImportError:  # pragma: no cover - permits isolated synthetic import
    try:
        from validate_phase2_qgap_inputs import validate_inputs  # type: ignore
    except ImportError:  # pragma: no cover - replaced by focused tests
        validate_inputs = None  # type: ignore[assignment]


SCHEMA_VERSION = "phase2-qgap-retrospective-results-v1"
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20_260_727
BOOTSTRAP_SAMPLE_SIZE = 20
BOOTSTRAP_PERCENTILE_METHOD = (
    "linear interpolation: h=(n-1)*p, i=floor(h), "
    "x_i+(h-i)*(x_(i+1)-x_i)"
)
DETECTOR_HORIZON = 20
DISPLAY_PLACES = Decimal("0.000001")
EXACT_TWO_CENTS = Fraction(1, 50)

OUTPUT_NAMES = (
    "source_manifest.json",
    "qgap_scenario_rows.csv",
    "qgap_seed_rows.csv",
    "qgap_cell_summary.csv",
    "detector_opportunity_rows.csv",
    "ordering_assessment.csv",
    "qgap_vs_recovery.png",
    "detectability_audit.png",
    "PHASE2_QGAP_RETROSPECTIVE_RESULTS.md",
    "SHA256SUMS.csv",
)

SCENARIO_FIELDS = (
    "run_id",
    "seed",
    "arm",
    "filename_boolean",
    "faulty_profile",
    "parent_profile",
    "parent_qtable_sha256",
    "scenario_schedule_sha256",
    "scenario_order",
    "scenario_id",
    "classification",
    "state_index",
    "settled_levels",
    "settled_ranks",
    "state_vector",
    "shortest_path_length",
    "shortest_sequence_count",
    "shortest_first_actions",
    "faulty_actions",
    "max_faulty_q",
    "max_survivor_q",
    "faulty_maximizers",
    "survivor_maximizers",
    "relevant_maximum_tied",
    "signed_gap",
    "signed_gap_is_zero",
    "burden",
    "zone_sum_max_faulty_q",
    "zone_sum_max_survivor_q",
    "zone_sum_signed_gap",
    "zone_sum_burden",
    "zone_sum_faulty_maximizers",
    "zone_sum_survivor_maximizers",
    "zone_sum_relevant_maximum_tied",
    "combined_greedy_maximizers",
    "combined_greedy_action",
    "zone_sum_greedy_maximizers",
    "zone_sum_greedy_action",
    "any_value_discrepancy",
    "faulty_max_value_discrepancy",
    "survivor_max_value_discrepancy",
    "faulty_maximizer_set_discrepancy",
    "survivor_maximizer_set_discrepancy",
    "greedy_tie_set_discrepancy",
    "greedy_action_discrepancy",
    "combined_zone_sum_max_abs_difference",
)

DETECTOR_FIELDS = (
    "run_id",
    "seed",
    "arm",
    "faulty_profile",
    "parent_profile",
    "scenario_order",
    "scenario_id",
    "component",
    "component_opportunity",
    "first_opportunity_step",
    "any_fault_component_opportunity",
    "all_fault_components_opportunity",
    "rollout_action_count",
    "terminated_at_goal",
    "detection_occurrence",
    "detect_episode_recorded",
    "detect_episode_censored",
    "detect_episode_value",
    "censoring_horizon",
)

SEED_FIELDS = (
    "run_id",
    "seed",
    "arm",
    "faulty_profile",
    "parent_profile",
    "scenario_count",
    "analyzed_count",
    "no_reranking_needed_count",
    "unreachable_count",
    "G_exact",
    "G",
    "signed_gap_median_exact",
    "signed_gap_median",
    "signed_gap_mean_exact",
    "signed_gap_mean",
    "tie_rate_exact",
    "tie_rate",
    "faulty_max_tie_rate_exact",
    "faulty_max_tie_rate",
    "survivor_max_tie_rate_exact",
    "survivor_max_tie_rate",
    "exact_zero_rate_exact",
    "exact_zero_rate",
    "reachable_fraction_exact",
    "reachable_fraction",
    "analyzed_fraction_exact",
    "analyzed_fraction",
    "mean_shortest_route_length_exact",
    "mean_shortest_route_length",
    "median_shortest_route_length_exact",
    "median_shortest_route_length",
    "min_shortest_route_length",
    "max_shortest_route_length",
    "shortest_route_count_distribution",
    "detector_opportunity_fraction_exact",
    "detector_opportunity_fraction",
    "detector_all_components_fraction_exact",
    "detector_all_components_fraction",
    "detector_component_fractions_exact",
    "detection_occurrence",
    "detect_episode_recorded",
    "detect_episode_censored",
    "detect_episode_value",
    "recovery_episodes_recorded",
    "recovery_censored",
    "recovery_value",
    "censoring_horizon",
    "deltaG_exact",
    "deltaG",
    "delta_signed_gap_median_exact",
    "delta_signed_gap_median",
    "deltaRecovery",
)

ORDERING_FIELDS = (
    "row_type",
    "panel",
    "metric",
    "omitted",
    "cell_1",
    "cell_2",
    "n_cells",
    "defined",
    "value_exact",
    "value",
    "predictor_difference_exact",
    "outcome_difference_exact",
    "ordering",
    "concordant",
    "bootstrap_defined_replicates",
    "bootstrap_median_exact",
    "bootstrap_median",
    "bootstrap_ci_low_exact",
    "bootstrap_ci_low",
    "bootstrap_ci_high_exact",
    "bootstrap_ci_high",
    "passed",
    "reason",
)

_ARM_SUMMARY_SUFFIXES = (
    "record_count",
    "G_defined_seed_count",
    "G_mean_exact",
    "G_mean",
    "G_median_exact",
    "G_median",
    "G_min_exact",
    "G_min",
    "G_max_exact",
    "G_max",
    "burden_scenario_mean_exact",
    "burden_scenario_mean",
    "burden_scenario_median_exact",
    "burden_scenario_median",
    "burden_scenario_min_exact",
    "burden_scenario_min",
    "burden_scenario_max_exact",
    "burden_scenario_max",
    "signed_gap_scenario_mean_exact",
    "signed_gap_scenario_mean",
    "signed_gap_scenario_median_exact",
    "signed_gap_scenario_median",
    "signed_gap_scenario_min_exact",
    "signed_gap_scenario_min",
    "signed_gap_scenario_max_exact",
    "signed_gap_scenario_max",
    "signed_gap_median_mean_exact",
    "signed_gap_median_mean",
    "signed_gap_mean_mean_exact",
    "signed_gap_mean_mean",
    "tie_rate_mean_exact",
    "tie_rate_mean",
    "faulty_max_tie_rate_mean_exact",
    "faulty_max_tie_rate_mean",
    "survivor_max_tie_rate_mean_exact",
    "survivor_max_tie_rate_mean",
    "exact_zero_rate_mean_exact",
    "exact_zero_rate_mean",
    "reachable_fraction_mean_exact",
    "reachable_fraction_mean",
    "analyzed_fraction_mean_exact",
    "analyzed_fraction_mean",
    "no_reranking_needed_fraction_mean_exact",
    "no_reranking_needed_fraction_mean",
    "unreachable_fraction_mean_exact",
    "unreachable_fraction_mean",
    "route_length_mean_exact",
    "route_length_mean",
    "route_length_median_exact",
    "route_length_median",
    "route_length_min",
    "route_length_max",
    "route_count_distribution",
    "detector_opportunity_mean_exact",
    "detector_opportunity_mean",
    "detector_all_components_mean_exact",
    "detector_all_components_mean",
    "detector_component_fractions_exact",
    "detection_occurrence_count",
    "detect_censor_count",
    "detect_episode_mean_exact",
    "detect_episode_mean",
    "recovery_censor_count",
    "recovery_mean_exact",
    "recovery_mean",
)

CELL_FIELDS = (
    "faulty_profile",
    "parent_profile",
    "panels",
    "paired_seed_count",
) + tuple(
    f"{arm}_{suffix}"
    for arm in ("KG", "TR")
    for suffix in _ARM_SUMMARY_SUFFIXES
) + (
    "deltaG_defined_seed_count",
    "cell_deltaG_exact",
    "cell_deltaG",
    "deltaG_median_exact",
    "deltaG_median",
    "deltaG_min_exact",
    "deltaG_min",
    "deltaG_max_exact",
    "deltaG_max",
    "cell_delta_signed_gap_median_exact",
    "cell_delta_signed_gap_median",
    "cell_deltaRecovery_exact",
    "cell_deltaRecovery",
    "bootstrap_resamples",
    "bootstrap_rng_seed",
    "bootstrap_percentile_method",
    "deltaG_bootstrap_median_exact",
    "deltaG_bootstrap_median",
    "deltaG_bootstrap_ci_low_exact",
    "deltaG_bootstrap_ci_low",
    "deltaG_bootstrap_ci_high_exact",
    "deltaG_bootstrap_ci_high",
    "delta_signed_gap_median_bootstrap_median_exact",
    "delta_signed_gap_median_bootstrap_median",
    "delta_signed_gap_median_bootstrap_ci_low_exact",
    "delta_signed_gap_median_bootstrap_ci_low",
    "delta_signed_gap_median_bootstrap_ci_high_exact",
    "delta_signed_gap_median_bootstrap_ci_high",
    "deltaRecovery_bootstrap_median_exact",
    "deltaRecovery_bootstrap_median",
    "deltaRecovery_bootstrap_ci_low_exact",
    "deltaRecovery_bootstrap_ci_low",
    "deltaRecovery_bootstrap_ci_high_exact",
    "deltaRecovery_bootstrap_ci_high",
)


class RetrospectiveError(RuntimeError):
    """Raised when checked inputs cannot satisfy the analysis contract."""


@dataclass(frozen=True)
class CensoredOutcome:
    recorded: int
    value: int
    censored: bool


@dataclass(frozen=True)
class SpearmanResult:
    """Exact rank covariance components plus a display-only rho."""

    n: int
    covariance: Fraction
    variance_x: Fraction
    variance_y: Fraction
    reason: str = ""

    @property
    def defined(self) -> bool:
        return (
            self.n >= 2
            and self.variance_x > 0
            and self.variance_y > 0
        )

    @property
    def rho(self) -> Optional[float]:
        if not self.defined:
            return None
        denominator = math.sqrt(float(self.variance_x * self.variance_y))
        return float(self.covariance) / denominator


@dataclass(frozen=True)
class SeedAggregate:
    run_id: int
    seed: int
    arm: str
    cell: str
    parent: str
    scenario_count: int
    analyzed_count: int
    terminal_count: int
    unreachable_count: int
    g: Optional[Fraction]
    signed_median: Optional[Fraction]
    signed_mean: Optional[Fraction]
    tie_rate: Optional[Fraction]
    zero_rate: Optional[Fraction]
    reachable_fraction: Fraction
    analyzed_fraction: Fraction
    route_mean: Optional[Fraction]
    route_median: Optional[Fraction]
    route_min: Optional[int]
    route_max: Optional[int]
    route_count_distribution: str
    burden_values: tuple[Fraction, ...]
    signed_gap_values: tuple[Fraction, ...]
    route_lengths: tuple[int, ...]
    detector_fraction: Fraction
    detector_all_fraction: Fraction
    detector_component_fractions: str
    faulty_max_tie_rate: Optional[Fraction]
    survivor_max_tie_rate: Optional[Fraction]
    detection_occurrence: int
    detect_recorded: int
    detect: CensoredOutcome
    recovery: CensoredOutcome
    censoring_horizon: int


@dataclass(frozen=True)
class PairedSeed:
    cell: str
    parent: str
    seed: int
    kg: SeedAggregate
    tr: SeedAggregate
    delta_g: Optional[Fraction]
    delta_signed_median: Optional[Fraction]
    delta_recovery: Fraction


@dataclass(frozen=True)
class BootstrapSummary:
    defined_replicates: int
    median: Optional[Fraction]
    low: Optional[Fraction]
    high: Optional[Fraction]


@dataclass(frozen=True)
class BootstrapFloatSummary:
    defined_replicates: int
    median: Optional[float]
    low: Optional[float]
    high: Optional[float]


@dataclass(frozen=True)
class BootstrapResults:
    cell_metrics: Mapping[tuple[str, str], BootstrapSummary]
    associations: Mapping[tuple[str, str], BootstrapFloatSummary]
    concordance_counts: Mapping[str, BootstrapSummary]


def decimal_to_fraction(value: Decimal) -> Fraction:
    """Convert an exact serialized-Q value without a float round trip."""
    if not value.is_finite():
        raise RetrospectiveError("non-finite Decimal cannot be aggregated")
    sign, digits, exponent = value.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    if exponent >= 0:
        return Fraction(coefficient * (10 ** exponent), 1)
    return Fraction(coefficient, 10 ** (-exponent))


def _mean(values: Sequence[Fraction]) -> Fraction:
    if not values:
        raise RetrospectiveError("mean requested for an empty sequence")
    return sum(values, Fraction(0, 1)) / len(values)


def _median(values: Sequence[Fraction]) -> Fraction:
    if not values:
        raise RetrospectiveError("median requested for an empty sequence")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _exact(value: Optional[Fraction]) -> str:
    if value is None:
        return ""
    return f"{value.numerator}/{value.denominator}"


def _display(value: Optional[Fraction]) -> str:
    if value is None:
        return ""
    decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
    return format(decimal_value.quantize(DISPLAY_PLACES, rounding=ROUND_HALF_EVEN), "f")


def _display_float(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.6f}"


def _bool(value: Optional[bool]) -> str:
    if value is None:
        return ""
    return "1" if value else "0"


def average_ranks(values: Sequence[Fraction]) -> tuple[Fraction, ...]:
    """Return one-based average ranks, retaining exact ties."""
    if not values:
        return ()
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks: list[Fraction] = [Fraction(0, 1)] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        rank = Fraction((start + 1) + end, 2)
        for position in range(start, end):
            ranks[indexed[position][0]] = rank
        start = end
    return tuple(ranks)


def spearman_exact(
    x_values: Sequence[Fraction],
    y_values: Sequence[Fraction],
) -> SpearmanResult:
    """Spearman rank association with average ties and explicit degeneracy."""
    if len(x_values) != len(y_values):
        raise RetrospectiveError("Spearman vectors have different lengths")
    n = len(x_values)
    if n < 2:
        return SpearmanResult(n, Fraction(0), Fraction(0), Fraction(0),
                              "fewer_than_two_cells")
    ranks_x = average_ranks(x_values)
    ranks_y = average_ranks(y_values)
    mean_x = _mean(ranks_x)
    mean_y = _mean(ranks_y)
    covariance = sum(
        ((rx - mean_x) * (ry - mean_y)
         for rx, ry in zip(ranks_x, ranks_y)),
        Fraction(0, 1),
    )
    variance_x = sum(((rank - mean_x) ** 2 for rank in ranks_x), Fraction(0))
    variance_y = sum(((rank - mean_y) ** 2 for rank in ranks_y), Fraction(0))
    if variance_x == 0:
        reason = "constant_predictor"
    elif variance_y == 0:
        reason = "constant_outcome"
    else:
        reason = ""
    return SpearmanResult(n, covariance, variance_x, variance_y, reason)


def spearman_at_least(result: SpearmanResult, threshold: Fraction) -> bool:
    """Compare rho to a non-negative threshold without rounding rho."""
    if threshold < 0:
        raise RetrospectiveError("only non-negative rho thresholds are supported")
    if not result.defined or result.covariance < 0:
        return False
    return (
        result.covariance * result.covariance
        >= threshold * threshold * result.variance_x * result.variance_y
    )


def strict_pair_concordance(
    predictor_1: Fraction,
    predictor_2: Fraction,
    outcome_1: Fraction,
    outcome_2: Fraction,
) -> tuple[bool, str]:
    """Treat either exact tie as nonconcordant."""
    dx = predictor_1 - predictor_2
    dy = outcome_1 - outcome_2
    if dx == 0 and dy == 0:
        return False, "tie_both"
    if dx == 0:
        return False, "tie_predictor"
    if dy == 0:
        return False, "tie_outcome"
    if (dx > 0) == (dy > 0):
        return True, "concordant"
    return False, "discordant"


def gate_two_exact(cell_mean_deltas: Sequence[Fraction]) -> tuple[bool, str]:
    """Apply the frozen three-level/exact-two-cent separation screen."""
    levels = sorted(set(cell_mean_deltas))
    if len(levels) < 3:
        return False, f"distinct_levels={len(levels)}"
    gaps = tuple(right - left for left, right in zip(levels, levels[1:]))
    if any(gap < EXACT_TWO_CENTS for gap in gaps):
        smallest = min(gaps)
        return False, f"minimum_adjacent_gap={_exact(smallest)}"
    return True, f"distinct_levels={len(levels)};minimum_adjacent_gap={_exact(min(gaps))}"


def linear_percentile(
    values: Sequence[Fraction],
    probability: Fraction,
) -> Fraction:
    """Sorted linear percentile, matching NumPy ``method='linear'``."""
    if not values:
        raise RetrospectiveError("percentile requested for an empty sequence")
    if probability < 0 or probability > 1:
        raise RetrospectiveError("percentile probability must be in [0,1]")
    ordered = sorted(values)
    h = Fraction(len(ordered) - 1, 1) * probability
    index = h.numerator // h.denominator
    remainder = h - index
    if index == len(ordered) - 1:
        return ordered[index]
    return ordered[index] + remainder * (ordered[index + 1] - ordered[index])


def _bootstrap_summary(values: Sequence[Fraction]) -> BootstrapSummary:
    if not values:
        return BootstrapSummary(0, None, None, None)
    return BootstrapSummary(
        len(values),
        linear_percentile(values, Fraction(1, 2)),
        linear_percentile(values, Fraction(1, 40)),
        linear_percentile(values, Fraction(39, 40)),
    )


def _linear_percentile_float(values: Sequence[float], probability: Fraction) -> float:
    if not values:
        raise RetrospectiveError("percentile requested for an empty sequence")
    ordered = sorted(values)
    h = Fraction(len(ordered) - 1, 1) * probability
    index = h.numerator // h.denominator
    remainder = float(h - index)
    if index == len(ordered) - 1:
        return ordered[index]
    return ordered[index] + remainder * (ordered[index + 1] - ordered[index])


def _bootstrap_float_summary(values: Sequence[float]) -> BootstrapFloatSummary:
    if not values:
        return BootstrapFloatSummary(0, None, None, None)
    return BootstrapFloatSummary(
        len(values),
        _linear_percentile_float(values, Fraction(1, 2)),
        _linear_percentile_float(values, Fraction(1, 40)),
        _linear_percentile_float(values, Fraction(39, 40)),
    )


def censor_outcome(recorded: int, horizon: int) -> CensoredOutcome:
    """Apply the exact joined-cell administrative bound independently."""
    if horizon < 0:
        raise RetrospectiveError("censoring horizon must be non-negative")
    value = int(recorded)
    return CensoredOutcome(value, horizon + 1 if value < 0 else value, value < 0)


def _fraction_json(values: Iterable[int]) -> str:
    counts: dict[int, int] = {}
    for value in values:
        counts[int(value)] = counts.get(int(value), 0) + 1
    return json.dumps(
        {str(key): counts[key] for key in sorted(counts)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _scenario_id(row: Mapping[str, Any]) -> int:
    for key in ("id", "scenario_id", "ScenarioID", "ScenarioId", "Scenario"):
        if key in row:
            try:
                return int(row[key])
            except (TypeError, ValueError) as exc:
                raise RetrospectiveError(f"invalid scenario identifier {row[key]!r}") from exc
    raise RetrospectiveError("scenario row has no identifier")


def _join(values: Iterable[Any]) -> str:
    return "|".join(str(value) for value in values)


def _dec(value: Optional[Decimal]) -> str:
    return "" if value is None else format(value, "f")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_bytes(document: Any) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def _relative_inventory_path(path: Path, root: Path, scope: str) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError as exc:
        raise RetrospectiveError(
            f"{scope} inventory path lies outside its root: {path}"
        ) from exc


def _inventory_entry(path: Path, root: Path, scope: str) -> dict[str, Any]:
    content = Path(path).read_bytes()
    return {
        "scope": scope,
        "path": _relative_inventory_path(path, root, scope),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _git_blob_inventory_entry(
    repo_root: Path,
    relative_path: str,
    blob_oid: str,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(Path(repo_root)),
                "cat-file",
                "blob",
                str(blob_oid),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RetrospectiveError(
            f"cannot read pinned Git blob {blob_oid} for {relative_path}"
        ) from exc
    content = completed.stdout
    return {
        "scope": "git_blob",
        "path": Path(relative_path).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "git_blob_oid": str(blob_oid),
    }


def _deduplicate_inventory(
    entries: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in entries:
        entry = dict(raw)
        key = (str(entry["scope"]), str(entry["path"]))
        previous = unique.get(key)
        if previous is not None and previous != entry:
            raise RetrospectiveError(
                f"conflicting inventory entries for {key[0]}:{key[1]}"
            )
        unique[key] = entry
    return [unique[key] for key in sorted(unique)]


def _enriched_source_manifest_bytes(
    *,
    repo_root: Path,
    source_root: Path,
    spec_path: Path,
    source_manifest_path: Path,
    records: Sequence[Any],
    spec: Mapping[str, Any],
) -> bytes:
    """Preserve rescue fields and replace deterministic inventory extensions."""
    try:
        document = json.loads(
            Path(source_manifest_path).read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrospectiveError(f"cannot enrich source manifest: {exc}") from exc
    if document.get("schema_version") != "phase2-qgap-source-manifest-v1":
        raise RetrospectiveError("unexpected source-manifest schema")

    validated_entries: list[dict[str, Any]] = []
    consumed_entries: list[dict[str, Any]] = []
    for record in records:
        direct_consumed = (
            Path(record.manifest_path),
            Path(record.recovery_path),
            Path(record.combined_qtable_path),
            *(Path(path) for path in record.zone_qtable_paths),
        )
        for path in direct_consumed:
            consumed_entries.append(
                _inventory_entry(path, source_root, "source")
            )
        for path in record.parent_qtable_paths:
            validated_entries.append(
                _inventory_entry(Path(path), source_root, "source")
            )
        validated_entries.append(
            _inventory_entry(Path(record.manifest_path), source_root, "source")
        )
        validated_entries.append(
            _inventory_entry(Path(record.recovery_path), source_root, "source")
        )

    consumed_entries.append(_inventory_entry(spec_path, repo_root, "repo"))
    source_blob_oids = spec.get("source_blob_oids")
    if not isinstance(source_blob_oids, dict):
        raise RetrospectiveError("frozen spec lacks pinned source blob OIDs")
    pinned_source_blobs: list[dict[str, Any]] = []
    for relative_path, blob_oid in sorted(source_blob_oids.items()):
        entry = _git_blob_inventory_entry(
            repo_root, str(relative_path), str(blob_oid)
        )
        pinned_source_blobs.append(entry)
        validated_entries.append(entry)
        if (
            str(relative_path) == "config/run_config.json"
            or str(relative_path).startswith("config/golden_registry/")
            or str(relative_path).startswith("benchmark/train_scenarios_")
        ):
            consumed_entries.append(entry)

    historical_references: list[dict[str, Any]] = []
    raw_artifacts = spec.get("source_artifacts")
    if not isinstance(raw_artifacts, list):
        raise RetrospectiveError("frozen spec lacks source artifact declarations")
    for artifact in sorted(raw_artifacts, key=lambda item: int(item["run_id"])):
        path = (
            repo_root
            / "phase2_v2_corrected"
            / f"run_{int(artifact['run_id'])}"
            / "SHA256SUMS.csv"
        )
        entry = _inventory_entry(path, repo_root, "repo")
        historical_references.append(entry)
        validated_entries.append(entry)

    # Replacement, not append, makes enrichment idempotent on reproduction.
    document["validated_files"] = _deduplicate_inventory(validated_entries)
    document["consumed_files"] = _deduplicate_inventory(consumed_entries)
    document["pinned_source_blobs"] = pinned_source_blobs
    document["historical_inventory_references"] = historical_references
    document["analysis_contract"] = {
        "schema_version": SCHEMA_VERSION,
        "frozen_spec_sha256": _hash_file(spec_path),
        "primary_quantity": "start-state Q-gap proxy",
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_rng_seed": BOOTSTRAP_SEED,
        "bootstrap_draws_per_replicate": BOOTSTRAP_SAMPLE_SIZE,
        "bootstrap_percentile_method": BOOTSTRAP_PERCENTILE_METHOD,
    }
    return _canonical_json_bytes(document)


def _record_sort_key(record: Any) -> tuple[Any, ...]:
    return (
        int(record.run_id),
        int(record.seed),
        0 if str(record.arm) == "KG" else 1,
        str(record.faulty_profile),
    )


def _load_record_qtables(
    record: Any,
    cache: dict[tuple[str, tuple[str, ...], int], SparseQTable],
) -> tuple[SparseQTable, tuple[SparseQTable, ...]]:
    profile = get_profile_spec(str(record.parent_profile))
    labels = tuple(str(label) for label in record.action_labels)
    if labels != profile.action_labels:
        raise RetrospectiveError(
            f"{record.faulty_profile}: checked action labels differ from frozen runtime order"
        )

    def cached(path: Path) -> SparseQTable:
        key = (str(Path(path).resolve()), labels, profile.state_count)
        if key not in cache:
            cache[key] = load_qtable(Path(path), labels, profile.state_count)
        return cache[key]

    combined = cached(Path(record.combined_qtable_path))
    zones = tuple(cached(Path(path)) for path in record.zone_qtable_paths)
    if len(zones) != len(profile.zone_names):
        raise RetrospectiveError(
            f"{record.faulty_profile}: expected {len(profile.zone_names)} logical zone tables, "
            f"got {len(zones)}"
        )
    return combined, zones


def _zone_sum_row(
    zone_tables: Sequence[SparseQTable],
    state_index: int,
) -> tuple[Decimal, ...]:
    if not zone_tables:
        raise RetrospectiveError("zone-table sum requested without zone tables")
    width = len(zone_tables[0].action_labels)
    rows = tuple(table.row(state_index) for table in zone_tables)
    return tuple(
        sum((row[action] for row in rows), Decimal("0.00"))
        for action in range(width)
    )


def _process_records(
    records: Sequence[Any],
    cell_specs: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[SeedAggregate]]:
    """Compute scenario/component rows and exact seed-arm aggregates."""
    scenario_rows: list[dict[str, Any]] = []
    detector_rows: list[dict[str, Any]] = []
    seed_aggregates: list[SeedAggregate] = []
    cache: dict[tuple[str, tuple[str, ...], int], SparseQTable] = {}

    for record in sorted(records, key=_record_sort_key):
        cell_name = str(record.faulty_profile)
        try:
            cell = cell_specs[cell_name]
        except KeyError as exc:
            raise RetrospectiveError(
                f"checked record references undeclared cell {cell_name!r}"
            ) from exc
        if str(record.parent_profile) != cell.parent_profile:
            raise RetrospectiveError(
                f"{cell_name}: checked parent differs from frozen cell mapping"
            )
        ordered_ids = tuple(int(value) for value in record.ordered_scenario_ids)
        raw_scenarios = tuple(record.scenario_rows)
        actual_ids = tuple(_scenario_id(row) for row in raw_scenarios)
        if actual_ids != ordered_ids:
            raise RetrospectiveError(
                f"{cell_name}: checked scenario rows are not in frozen ID order"
            )
        if not raw_scenarios:
            raise RetrospectiveError(f"{cell_name}: no ordered scenarios")

        combined, zone_tables = _load_record_qtables(record, cache)
        horizon = int(record.adapt_episodes_effective)
        detect = censor_outcome(int(record.detect_episode), horizon)
        recovery = censor_outcome(int(record.recovery_episodes), horizon)
        detection_occurrence = int(int(record.detect_episode) >= 0)

        burdens: list[Fraction] = []
        signed_gaps: list[Fraction] = []
        tied: list[int] = []
        faulty_max_tied: list[int] = []
        survivor_max_tied: list[int] = []
        zero_gaps: list[int] = []
        route_lengths: list[int] = []
        route_counts: list[int] = []
        class_counts = {
            ScenarioClassification.ANALYZED: 0,
            ScenarioClassification.NO_RERANKING_NEEDED: 0,
            ScenarioClassification.UNREACHABLE: 0,
        }
        detector_any: list[int] = []
        detector_all: list[int] = []
        detector_components: dict[str, list[int]] = {
            component: [] for component in cell.fault_components
        }

        for order, (scenario_id, scenario) in enumerate(
            zip(ordered_ids, raw_scenarios), start=1
        ):
            survivor_model = build_cell_model(
                cell, scenario, apply_unavailable_actions=True
            )
            result = evaluate_start_state_qgap(
                survivor_model, combined, cell.unavailable_actions
            )
            class_counts[result.classification] += 1
            initial = survivor_model.initial_state()
            state_index = survivor_model.state_index(initial)
            if state_index != result.state_index:
                raise RetrospectiveError(f"{cell_name}: inconsistent settled state index")
            combined_row = combined.row(state_index)
            zone_row = _zone_sum_row(zone_tables, state_index)
            max_abs_difference = max(
                abs(combined_value - zone_value)
                for combined_value, zone_value in zip(combined_row, zone_row)
            )
            combined_global_max = max(combined_row)
            zone_global_max = max(zone_row)
            combined_greedy_maximizers = tuple(
                label
                for label, value in zip(combined.action_labels, combined_row)
                if value == combined_global_max
            )
            zone_greedy_maximizers = tuple(
                label
                for label, value in zip(combined.action_labels, zone_row)
                if value == zone_global_max
            )
            combined_greedy_action = combined_greedy_maximizers[0]
            zone_greedy_action = zone_greedy_maximizers[0]

            zone_max_faulty: Optional[Decimal] = None
            zone_max_survivor: Optional[Decimal] = None
            zone_signed: Optional[Decimal] = None
            zone_burden: Optional[Decimal] = None
            zone_faulty_maximizers: tuple[str, ...] = ()
            zone_survivor_maximizers: tuple[str, ...] = ()
            zone_relevant_tied: Optional[bool] = None
            faulty_value_discrepancy: Optional[bool] = None
            survivor_value_discrepancy: Optional[bool] = None
            faulty_set_discrepancy: Optional[bool] = None
            survivor_set_discrepancy: Optional[bool] = None
            if result.classification == ScenarioClassification.ANALYZED:
                action_index = {
                    label: index for index, label in enumerate(combined.action_labels)
                }
                zone_max_faulty = max(
                    zone_row[action_index[label]]
                    for label in result.faulty_action_labels
                )
                zone_max_survivor = max(
                    zone_row[action_index[label]]
                    for label in result.shortest_first_actions
                )
                zone_signed = zone_max_faulty - zone_max_survivor
                zone_burden = max(Decimal("0.00"), zone_signed)
                faulty_set = set(result.faulty_action_labels)
                survivor_set = set(result.shortest_first_actions)
                zone_faulty_maximizers = tuple(
                    label
                    for label in combined.action_labels
                    if label in faulty_set
                    and zone_row[action_index[label]] == zone_max_faulty
                )
                zone_survivor_maximizers = tuple(
                    label
                    for label in combined.action_labels
                    if label in survivor_set
                    and zone_row[action_index[label]] == zone_max_survivor
                )
                zone_relevant_tied = (
                    len(zone_faulty_maximizers) > 1
                    or len(zone_survivor_maximizers) > 1
                )
                faulty_value_discrepancy = (
                    result.max_faulty_q != zone_max_faulty
                )
                survivor_value_discrepancy = (
                    result.max_survivor_q != zone_max_survivor
                )
                faulty_set_discrepancy = (
                    result.faulty_maximizers != zone_faulty_maximizers
                )
                survivor_set_discrepancy = (
                    result.survivor_maximizers != zone_survivor_maximizers
                )
                if result.burden is None or result.signed_gap is None:
                    raise RetrospectiveError(
                        f"{cell_name}: analyzed scenario lacks exact gap values"
                    )
                burdens.append(decimal_to_fraction(result.burden))
                signed_gaps.append(decimal_to_fraction(result.signed_gap))
                tied.append(int(bool(result.relevant_maximum_tied)))
                faulty_max_tied.append(int(len(result.faulty_maximizers) > 1))
                survivor_max_tied.append(
                    int(len(result.survivor_maximizers) > 1)
                )
                zero_gaps.append(int(bool(result.signed_gap_is_zero)))
                route_lengths.append(int(result.shortest_path_length))
                route_counts.append(int(result.shortest_sequence_count))

            detector_model = build_cell_model(
                cell, scenario, apply_unavailable_actions=False
            )
            detector = run_detector_opportunity_rollout(
                detector_model,
                combined,
                cell.fault_components,
                horizon=DETECTOR_HORIZON,
            )
            detector_any.append(int(detector.any_fault_component_opportunity))
            detector_all.append(int(detector.all_fault_components_opportunity))
            for component in cell.fault_components:
                detector_components[component].append(
                    int(detector.opportunity_by_component[component])
                )

            scenario_rows.append(
                {
                    "run_id": int(record.run_id),
                    "seed": int(record.seed),
                    "arm": str(record.arm),
                    "filename_boolean": str(record.filename_boolean),
                    "faulty_profile": cell_name,
                    "parent_profile": str(record.parent_profile),
                    "parent_qtable_sha256": str(record.parent_qtable_sha256),
                    "scenario_schedule_sha256": str(record.scenario_schedule_sha256),
                    "scenario_order": order,
                    "scenario_id": scenario_id,
                    "classification": (
                        "REACHABLE_NONTERMINAL"
                        if result.classification == ScenarioClassification.ANALYZED
                        else result.classification.value
                    ),
                    "state_index": state_index,
                    "settled_levels": _join(
                        format(value, "f")
                        for value in survivor_model.settled_levels(initial)
                    ),
                    "settled_ranks": _join(survivor_model.zone_ranks(initial)),
                    "state_vector": _join(survivor_model.state_vector(initial)),
                    "shortest_path_length": (
                        "" if result.shortest_path_length is None
                        else result.shortest_path_length
                    ),
                    "shortest_sequence_count": result.shortest_sequence_count,
                    "shortest_first_actions": _join(result.shortest_first_actions),
                    "faulty_actions": _join(result.faulty_action_labels),
                    "max_faulty_q": _dec(result.max_faulty_q),
                    "max_survivor_q": _dec(result.max_survivor_q),
                    "faulty_maximizers": _join(result.faulty_maximizers),
                    "survivor_maximizers": _join(result.survivor_maximizers),
                    "relevant_maximum_tied": _bool(result.relevant_maximum_tied),
                    "signed_gap": _dec(result.signed_gap),
                    "signed_gap_is_zero": _bool(result.signed_gap_is_zero),
                    "burden": _dec(result.burden),
                    "zone_sum_max_faulty_q": _dec(zone_max_faulty),
                    "zone_sum_max_survivor_q": _dec(zone_max_survivor),
                    "zone_sum_signed_gap": _dec(zone_signed),
                    "zone_sum_burden": _dec(zone_burden),
                    "zone_sum_faulty_maximizers": _join(
                        zone_faulty_maximizers
                    ),
                    "zone_sum_survivor_maximizers": _join(
                        zone_survivor_maximizers
                    ),
                    "zone_sum_relevant_maximum_tied": _bool(
                        zone_relevant_tied
                    ),
                    "combined_greedy_maximizers": _join(
                        combined_greedy_maximizers
                    ),
                    "combined_greedy_action": combined_greedy_action,
                    "zone_sum_greedy_maximizers": _join(
                        zone_greedy_maximizers
                    ),
                    "zone_sum_greedy_action": zone_greedy_action,
                    "any_value_discrepancy": int(max_abs_difference != 0),
                    "faulty_max_value_discrepancy": _bool(
                        faulty_value_discrepancy
                    ),
                    "survivor_max_value_discrepancy": _bool(
                        survivor_value_discrepancy
                    ),
                    "faulty_maximizer_set_discrepancy": _bool(
                        faulty_set_discrepancy
                    ),
                    "survivor_maximizer_set_discrepancy": _bool(
                        survivor_set_discrepancy
                    ),
                    "greedy_tie_set_discrepancy": int(
                        combined_greedy_maximizers != zone_greedy_maximizers
                    ),
                    "greedy_action_discrepancy": int(
                        combined_greedy_action != zone_greedy_action
                    ),
                    "combined_zone_sum_max_abs_difference": _dec(
                        max_abs_difference
                    ),
                }
            )

            for component in cell.fault_components:
                detector_rows.append(
                    {
                        "run_id": int(record.run_id),
                        "seed": int(record.seed),
                        "arm": str(record.arm),
                        "faulty_profile": cell_name,
                        "parent_profile": str(record.parent_profile),
                        "scenario_order": order,
                        "scenario_id": scenario_id,
                        "component": component,
                        "component_opportunity": int(
                            detector.opportunity_by_component[component]
                        ),
                        "first_opportunity_step": (
                            ""
                            if detector.first_opportunity_step[component] is None
                            else detector.first_opportunity_step[component]
                        ),
                        "any_fault_component_opportunity": int(
                            detector.any_fault_component_opportunity
                        ),
                        "all_fault_components_opportunity": int(
                            detector.all_fault_components_opportunity
                        ),
                        "rollout_action_count": len(detector.action_trace),
                        "terminated_at_goal": int(detector.terminated_at_goal),
                        "detection_occurrence": detection_occurrence,
                        "detect_episode_recorded": int(record.detect_episode),
                        "detect_episode_censored": int(detect.censored),
                        "detect_episode_value": detect.value,
                        "censoring_horizon": horizon,
                    }
                )

        total = len(raw_scenarios)
        analyzed = class_counts[ScenarioClassification.ANALYZED]
        terminal = class_counts[ScenarioClassification.NO_RERANKING_NEEDED]
        unreachable = class_counts[ScenarioClassification.UNREACHABLE]
        if analyzed:
            g: Optional[Fraction] = _mean(burdens)
            signed_median: Optional[Fraction] = _median(signed_gaps)
            signed_mean: Optional[Fraction] = _mean(signed_gaps)
            tie_rate: Optional[Fraction] = Fraction(sum(tied), analyzed)
            faulty_tie_rate: Optional[Fraction] = Fraction(
                sum(faulty_max_tied), analyzed
            )
            survivor_tie_rate: Optional[Fraction] = Fraction(
                sum(survivor_max_tied), analyzed
            )
            zero_rate: Optional[Fraction] = Fraction(sum(zero_gaps), analyzed)
            route_mean: Optional[Fraction] = Fraction(sum(route_lengths), analyzed)
            route_median: Optional[Fraction] = _median(
                tuple(Fraction(value) for value in route_lengths)
            )
            route_min: Optional[int] = min(route_lengths)
            route_max: Optional[int] = max(route_lengths)
        else:
            g = signed_median = signed_mean = tie_rate = zero_rate = None
            faulty_tie_rate = survivor_tie_rate = None
            route_mean = route_median = None
            route_min = route_max = None

        seed_aggregates.append(
            SeedAggregate(
                run_id=int(record.run_id),
                seed=int(record.seed),
                arm=str(record.arm),
                cell=cell_name,
                parent=str(record.parent_profile),
                scenario_count=total,
                analyzed_count=analyzed,
                terminal_count=terminal,
                unreachable_count=unreachable,
                g=g,
                signed_median=signed_median,
                signed_mean=signed_mean,
                tie_rate=tie_rate,
                zero_rate=zero_rate,
                reachable_fraction=Fraction(analyzed + terminal, total),
                analyzed_fraction=Fraction(analyzed, total),
                route_mean=route_mean,
                route_median=route_median,
                route_min=route_min,
                route_max=route_max,
                route_count_distribution=_fraction_json(route_counts),
                burden_values=tuple(burdens),
                signed_gap_values=tuple(signed_gaps),
                route_lengths=tuple(route_lengths),
                detector_fraction=Fraction(sum(detector_any), total),
                detector_all_fraction=Fraction(sum(detector_all), total),
                detector_component_fractions=json.dumps(
                    {
                        component: _exact(
                            Fraction(sum(detector_components[component]), total)
                        )
                        for component in sorted(detector_components)
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                faulty_max_tie_rate=faulty_tie_rate,
                survivor_max_tie_rate=survivor_tie_rate,
                detection_occurrence=detection_occurrence,
                detect_recorded=int(record.detect_episode),
                detect=detect,
                recovery=recovery,
                censoring_horizon=horizon,
            )
        )

    return scenario_rows, detector_rows, seed_aggregates


def _pair_seed_aggregates(
    aggregates: Sequence[SeedAggregate],
) -> tuple[list[PairedSeed], dict[tuple[str, int, str], SeedAggregate]]:
    by_key: dict[tuple[str, int, str], SeedAggregate] = {}
    for aggregate in aggregates:
        key = (aggregate.cell, aggregate.seed, aggregate.arm)
        if key in by_key:
            raise RetrospectiveError(f"duplicate seed-arm aggregate {key}")
        by_key[key] = aggregate

    paired: list[PairedSeed] = []
    cell_seeds = sorted({(row.cell, row.seed, row.parent) for row in aggregates})
    for cell, seed, parent in cell_seeds:
        kg = by_key.get((cell, seed, "KG"))
        tr = by_key.get((cell, seed, "TR"))
        if kg is None or tr is None:
            raise RetrospectiveError(
                f"{cell}/seed {seed}: both KG and TR records are required"
            )
        if kg.run_id != tr.run_id:
            raise RetrospectiveError(
                f"{cell}/seed {seed}: KG/TR records come from different runs"
            )
        if kg.parent != tr.parent or kg.parent != parent:
            raise RetrospectiveError(
                f"{cell}/seed {seed}: KG/TR parent profiles differ"
            )
        delta_g = None if kg.g is None or tr.g is None else kg.g - tr.g
        delta_signed = (
            None
            if kg.signed_median is None or tr.signed_median is None
            else kg.signed_median - tr.signed_median
        )
        paired.append(
            PairedSeed(
                cell,
                parent,
                seed,
                kg,
                tr,
                delta_g,
                delta_signed,
                Fraction(kg.recovery.value - tr.recovery.value, 1),
            )
        )
    return paired, by_key


def _seed_output_rows(
    aggregates: Sequence[SeedAggregate],
    paired: Sequence[PairedSeed],
) -> list[dict[str, Any]]:
    pair_map = {(row.cell, row.seed): row for row in paired}
    output: list[dict[str, Any]] = []
    for row in sorted(
        aggregates,
        key=lambda item: (
            item.cell,
            item.seed,
            0 if item.arm == "KG" else 1,
            item.run_id,
        ),
    ):
        pair = pair_map[(row.cell, row.seed)]
        output.append(
            {
                "run_id": row.run_id,
                "seed": row.seed,
                "arm": row.arm,
                "faulty_profile": row.cell,
                "parent_profile": row.parent,
                "scenario_count": row.scenario_count,
                "analyzed_count": row.analyzed_count,
                "no_reranking_needed_count": row.terminal_count,
                "unreachable_count": row.unreachable_count,
                "G_exact": _exact(row.g),
                "G": _display(row.g),
                "signed_gap_median_exact": _exact(row.signed_median),
                "signed_gap_median": _display(row.signed_median),
                "signed_gap_mean_exact": _exact(row.signed_mean),
                "signed_gap_mean": _display(row.signed_mean),
                "tie_rate_exact": _exact(row.tie_rate),
                "tie_rate": _display(row.tie_rate),
                "faulty_max_tie_rate_exact": _exact(row.faulty_max_tie_rate),
                "faulty_max_tie_rate": _display(row.faulty_max_tie_rate),
                "survivor_max_tie_rate_exact": _exact(
                    row.survivor_max_tie_rate
                ),
                "survivor_max_tie_rate": _display(
                    row.survivor_max_tie_rate
                ),
                "exact_zero_rate_exact": _exact(row.zero_rate),
                "exact_zero_rate": _display(row.zero_rate),
                "reachable_fraction_exact": _exact(row.reachable_fraction),
                "reachable_fraction": _display(row.reachable_fraction),
                "analyzed_fraction_exact": _exact(row.analyzed_fraction),
                "analyzed_fraction": _display(row.analyzed_fraction),
                "mean_shortest_route_length_exact": _exact(row.route_mean),
                "mean_shortest_route_length": _display(row.route_mean),
                "median_shortest_route_length_exact": _exact(row.route_median),
                "median_shortest_route_length": _display(row.route_median),
                "min_shortest_route_length": (
                    "" if row.route_min is None else row.route_min
                ),
                "max_shortest_route_length": (
                    "" if row.route_max is None else row.route_max
                ),
                "shortest_route_count_distribution": row.route_count_distribution,
                "detector_opportunity_fraction_exact": _exact(
                    row.detector_fraction
                ),
                "detector_opportunity_fraction": _display(row.detector_fraction),
                "detector_all_components_fraction_exact": _exact(
                    row.detector_all_fraction
                ),
                "detector_all_components_fraction": _display(
                    row.detector_all_fraction
                ),
                "detector_component_fractions_exact": (
                    row.detector_component_fractions
                ),
                "detection_occurrence": row.detection_occurrence,
                "detect_episode_recorded": row.detect_recorded,
                "detect_episode_censored": int(row.detect.censored),
                "detect_episode_value": row.detect.value,
                "recovery_episodes_recorded": row.recovery.recorded,
                "recovery_censored": int(row.recovery.censored),
                "recovery_value": row.recovery.value,
                "censoring_horizon": row.censoring_horizon,
                "deltaG_exact": _exact(pair.delta_g) if row.arm == "KG" else "",
                "deltaG": _display(pair.delta_g) if row.arm == "KG" else "",
                "delta_signed_gap_median_exact": (
                    _exact(pair.delta_signed_median) if row.arm == "KG" else ""
                ),
                "delta_signed_gap_median": (
                    _display(pair.delta_signed_median) if row.arm == "KG" else ""
                ),
                "deltaRecovery": (
                    _display(pair.delta_recovery) if row.arm == "KG" else ""
                ),
            }
        )
    return output


def _paired_cell_means(
    paired: Sequence[PairedSeed],
) -> dict[str, dict[str, Fraction]]:
    grouped: dict[str, list[PairedSeed]] = {}
    for row in paired:
        grouped.setdefault(row.cell, []).append(row)
    result: dict[str, dict[str, Fraction]] = {}
    for cell, rows in grouped.items():
        delta_g = [row.delta_g for row in rows if row.delta_g is not None]
        delta_s = [
            row.delta_signed_median
            for row in rows
            if row.delta_signed_median is not None
        ]
        metrics: dict[str, Fraction] = {
            "deltaRecovery": _mean([row.delta_recovery for row in rows])
        }
        if len(delta_g) == len(rows):
            metrics["deltaG"] = _mean(delta_g)  # type: ignore[arg-type]
        if len(delta_s) == len(rows):
            metrics["delta_signed_gap_median"] = _mean(  # type: ignore[arg-type]
                delta_s
            )
        result[cell] = metrics
    return result


def _association_for_cells(
    cells: Sequence[str],
    cell_means: Mapping[str, Mapping[str, Fraction]],
    predictor: str,
) -> SpearmanResult:
    missing = [
        cell
        for cell in cells
        if cell not in cell_means
        or predictor not in cell_means[cell]
        or "deltaRecovery" not in cell_means[cell]
    ]
    if missing:
        return SpearmanResult(
            0,
            Fraction(0),
            Fraction(0),
            Fraction(0),
            "missing_cells:" + "|".join(missing),
        )
    return spearman_exact(
        [cell_means[cell][predictor] for cell in cells],
        [cell_means[cell]["deltaRecovery"] for cell in cells],
    )


def _concordance_count(
    cells: Sequence[str],
    cell_means: Mapping[str, Mapping[str, Fraction]],
    predictor: str = "deltaG",
) -> Optional[int]:
    if any(
        cell not in cell_means
        or predictor not in cell_means[cell]
        or "deltaRecovery" not in cell_means[cell]
        for cell in cells
    ):
        return None
    count = 0
    for left_index, left in enumerate(cells):
        for right in cells[left_index + 1 :]:
            concordant, _ = strict_pair_concordance(
                cell_means[left][predictor],
                cell_means[right][predictor],
                cell_means[left]["deltaRecovery"],
                cell_means[right]["deltaRecovery"],
            )
            count += int(concordant)
    return count


def bootstrap_descriptors(
    paired: Sequence[PairedSeed],
    panels: Mapping[str, Sequence[str]],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    rng_seed: int = BOOTSTRAP_SEED,
) -> BootstrapResults:
    """Run the frozen shared paired-seed bootstrap.

    One RNG instance is created.  Each replicate consumes exactly twenty
    successive ``randrange(20)`` calls, then reuses those seed IDs for every
    cell, arm-derived metric, association, and concordance count.
    """
    if resamples <= 0:
        raise RetrospectiveError("bootstrap resamples must be positive")
    by_cell: dict[str, dict[int, PairedSeed]] = {}
    for row in paired:
        if row.seed in by_cell.setdefault(row.cell, {}):
            raise RetrospectiveError(
                f"duplicate paired seed {row.cell}/{row.seed} in bootstrap"
            )
        by_cell[row.cell][row.seed] = row
    required_seeds = set(range(1, BOOTSTRAP_SAMPLE_SIZE + 1))
    complete_cells = {
        cell: rows
        for cell, rows in by_cell.items()
        if set(rows) == required_seeds
        and all(
            row.delta_g is not None and row.delta_signed_median is not None
            for row in rows.values()
        )
    }

    cell_distributions: dict[tuple[str, str], list[Fraction]] = {
        (cell, metric): []
        for cell in sorted(complete_cells)
        for metric in ("deltaG", "delta_signed_gap_median", "deltaRecovery")
    }
    association_distributions: dict[tuple[str, str], list[float]] = {
        (panel_name, predictor): []
        for panel_name in panels
        for predictor in ("deltaG", "delta_signed_gap_median")
    }
    concordance_distributions: dict[str, list[Fraction]] = {
        panel_name: []
        for panel_name in ("B_reranking", "C_sighted_reference")
        if panel_name in panels
    }

    rng = random.Random(rng_seed)
    for _ in range(resamples):
        sampled_seeds = tuple(
            rng.randrange(BOOTSTRAP_SAMPLE_SIZE) + 1
            for _ in range(BOOTSTRAP_SAMPLE_SIZE)
        )
        replicate_means: dict[str, dict[str, Fraction]] = {}
        for cell, seed_rows in complete_cells.items():
            sampled = [seed_rows[seed] for seed in sampled_seeds]
            delta_g_values = [row.delta_g for row in sampled]
            delta_s_values = [row.delta_signed_median for row in sampled]
            # ``complete_cells`` proves both optional fields are present.
            delta_g_mean = _mean(delta_g_values)  # type: ignore[arg-type]
            delta_s_mean = _mean(delta_s_values)  # type: ignore[arg-type]
            recovery_mean = _mean([row.delta_recovery for row in sampled])
            replicate_means[cell] = {
                "deltaG": delta_g_mean,
                "delta_signed_gap_median": delta_s_mean,
                "deltaRecovery": recovery_mean,
            }
            cell_distributions[(cell, "deltaG")].append(delta_g_mean)
            cell_distributions[(cell, "delta_signed_gap_median")].append(
                delta_s_mean
            )
            cell_distributions[(cell, "deltaRecovery")].append(recovery_mean)

        for panel_name, panel_cells in panels.items():
            for predictor in ("deltaG", "delta_signed_gap_median"):
                association = _association_for_cells(
                    tuple(panel_cells), replicate_means, predictor
                )
                if association.defined:
                    rho = association.rho
                    if rho is not None:
                        association_distributions[(panel_name, predictor)].append(
                            rho
                        )
        for panel_name in concordance_distributions:
            count = _concordance_count(
                tuple(panels[panel_name]), replicate_means
            )
            if count is not None:
                concordance_distributions[panel_name].append(Fraction(count, 1))

    return BootstrapResults(
        {
            key: _bootstrap_summary(values)
            for key, values in cell_distributions.items()
        },
        {
            key: _bootstrap_float_summary(values)
            for key, values in association_distributions.items()
        },
        {
            key: _bootstrap_summary(values)
            for key, values in concordance_distributions.items()
        },
    )


def _merge_route_distributions(rows: Sequence[SeedAggregate]) -> str:
    counts: dict[int, int] = {}
    for row in rows:
        document = json.loads(row.route_count_distribution)
        for key, value in document.items():
            route_count = int(key)
            counts[route_count] = counts.get(route_count, 0) + int(value)
    return json.dumps(
        {str(key): counts[key] for key in sorted(counts)},
        sort_keys=True,
        separators=(",", ":"),
    )


def _four_summary_values(
    values: Sequence[Fraction],
) -> tuple[Optional[Fraction], Optional[Fraction], Optional[Fraction], Optional[Fraction]]:
    if not values:
        return None, None, None, None
    return _mean(values), _median(values), min(values), max(values)


def _parse_exact(text: str) -> Fraction:
    numerator, denominator = str(text).split("/", 1)
    return Fraction(int(numerator), int(denominator))


def _arm_summary(rows: Sequence[SeedAggregate], arm: str) -> dict[str, Any]:
    selected = [row for row in rows if row.arm == arm]
    g_values = [row.g for row in selected if row.g is not None]
    g_mean, g_median, g_min, g_max = _four_summary_values(
        g_values  # type: ignore[arg-type]
    )
    signed_medians = [
        row.signed_median for row in selected if row.signed_median is not None
    ]
    signed_means = [
        row.signed_mean for row in selected if row.signed_mean is not None
    ]
    tie_rates = [row.tie_rate for row in selected if row.tie_rate is not None]
    faulty_tie_rates = [
        row.faulty_max_tie_rate
        for row in selected
        if row.faulty_max_tie_rate is not None
    ]
    survivor_tie_rates = [
        row.survivor_max_tie_rate
        for row in selected
        if row.survivor_max_tie_rate is not None
    ]
    zero_rates = [row.zero_rate for row in selected if row.zero_rate is not None]
    pooled_burdens = [
        value for row in selected for value in row.burden_values
    ]
    pooled_signed = [
        value for row in selected for value in row.signed_gap_values
    ]
    pooled_routes = [
        value for row in selected for value in row.route_lengths
    ]
    burden_mean, burden_median, burden_min, burden_max = _four_summary_values(
        pooled_burdens
    )
    signed_mean, signed_median, signed_min, signed_max = _four_summary_values(
        pooled_signed
    )
    component_values: dict[str, list[Fraction]] = {}
    for selected_row in selected:
        document = json.loads(selected_row.detector_component_fractions)
        for component, exact_value in document.items():
            component_values.setdefault(str(component), []).append(
                _parse_exact(str(exact_value))
            )
    component_summary = json.dumps(
        {
            component: _exact(_mean(values))
            for component, values in sorted(component_values.items())
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    exact_values: dict[str, Optional[Fraction]] = {
        "G_mean": g_mean,
        "G_median": g_median,
        "G_min": g_min,
        "G_max": g_max,
        "burden_scenario_mean": burden_mean,
        "burden_scenario_median": burden_median,
        "burden_scenario_min": burden_min,
        "burden_scenario_max": burden_max,
        "signed_gap_scenario_mean": signed_mean,
        "signed_gap_scenario_median": signed_median,
        "signed_gap_scenario_min": signed_min,
        "signed_gap_scenario_max": signed_max,
        "signed_gap_median_mean": (
            _mean(signed_medians) if signed_medians else None  # type: ignore[arg-type]
        ),
        "signed_gap_mean_mean": (
            _mean(signed_means) if signed_means else None  # type: ignore[arg-type]
        ),
        "tie_rate_mean": (
            _mean(tie_rates) if tie_rates else None  # type: ignore[arg-type]
        ),
        "faulty_max_tie_rate_mean": (
            _mean(faulty_tie_rates)  # type: ignore[arg-type]
            if faulty_tie_rates
            else None
        ),
        "survivor_max_tie_rate_mean": (
            _mean(survivor_tie_rates)  # type: ignore[arg-type]
            if survivor_tie_rates
            else None
        ),
        "exact_zero_rate_mean": (
            _mean(zero_rates) if zero_rates else None  # type: ignore[arg-type]
        ),
        "reachable_fraction_mean": (
            _mean([row.reachable_fraction for row in selected])
            if selected
            else None
        ),
        "analyzed_fraction_mean": (
            _mean([row.analyzed_fraction for row in selected])
            if selected
            else None
        ),
        "no_reranking_needed_fraction_mean": (
            _mean(
                [
                    Fraction(row.terminal_count, row.scenario_count)
                    for row in selected
                ]
            )
            if selected
            else None
        ),
        "unreachable_fraction_mean": (
            _mean(
                [
                    Fraction(row.unreachable_count, row.scenario_count)
                    for row in selected
                ]
            )
            if selected
            else None
        ),
        "route_length_mean": (
            _mean([Fraction(value) for value in pooled_routes])
            if pooled_routes
            else None
        ),
        "route_length_median": (
            _median([Fraction(value) for value in pooled_routes])
            if pooled_routes
            else None
        ),
        "detector_opportunity_mean": (
            _mean([row.detector_fraction for row in selected])
            if selected
            else None
        ),
        "detector_all_components_mean": (
            _mean([row.detector_all_fraction for row in selected])
            if selected
            else None
        ),
        "detect_episode_mean": (
            _mean([Fraction(row.detect.value) for row in selected])
            if selected
            else None
        ),
        "recovery_mean": (
            _mean([Fraction(row.recovery.value) for row in selected])
            if selected
            else None
        ),
    }
    output: dict[str, Any] = {
        f"{arm}_record_count": len(selected),
        f"{arm}_G_defined_seed_count": len(g_values),
        f"{arm}_route_length_min": (
            min(pooled_routes) if pooled_routes else ""
        ),
        f"{arm}_route_length_max": (
            max(pooled_routes) if pooled_routes else ""
        ),
        f"{arm}_route_count_distribution": _merge_route_distributions(selected),
        f"{arm}_detector_component_fractions_exact": component_summary,
        f"{arm}_detection_occurrence_count": sum(
            row.detection_occurrence for row in selected
        ),
        f"{arm}_detect_censor_count": sum(
            int(row.detect.censored) for row in selected
        ),
        f"{arm}_recovery_censor_count": sum(
            int(row.recovery.censored) for row in selected
        ),
    }
    for name, value in exact_values.items():
        output[f"{arm}_{name}_exact"] = _exact(value)
        output[f"{arm}_{name}"] = _display(value)
    return output


def _cell_summary_rows(
    aggregates: Sequence[SeedAggregate],
    paired: Sequence[PairedSeed],
    panels: Mapping[str, Sequence[str]],
    bootstrap: BootstrapResults,
) -> list[dict[str, Any]]:
    by_cell_aggregates: dict[str, list[SeedAggregate]] = {}
    by_cell_paired: dict[str, list[PairedSeed]] = {}
    for row in aggregates:
        by_cell_aggregates.setdefault(row.cell, []).append(row)
    for row in paired:
        by_cell_paired.setdefault(row.cell, []).append(row)

    output: list[dict[str, Any]] = []
    for cell in sorted(by_cell_aggregates):
        rows = by_cell_aggregates[cell]
        pairs = sorted(by_cell_paired[cell], key=lambda item: item.seed)
        parents = {row.parent for row in rows}
        if len(parents) != 1:
            raise RetrospectiveError(f"{cell}: multiple parent profiles")
        delta_g = [row.delta_g for row in pairs if row.delta_g is not None]
        delta_s = [
            row.delta_signed_median
            for row in pairs
            if row.delta_signed_median is not None
        ]
        delta_recovery = [row.delta_recovery for row in pairs]
        g_mean, g_median, g_min, g_max = _four_summary_values(
            delta_g  # type: ignore[arg-type]
        )
        cell_delta_s = (
            _mean(delta_s) if len(delta_s) == len(pairs) and pairs else None  # type: ignore[arg-type]
        )
        cell_delta_recovery = _mean(delta_recovery) if pairs else None
        row: dict[str, Any] = {
            "faulty_profile": cell,
            "parent_profile": next(iter(parents)),
            "panels": _join(
                panel_name
                for panel_name, members in panels.items()
                if cell in members
            ),
            "paired_seed_count": len(pairs),
            "deltaG_defined_seed_count": len(delta_g),
            "cell_deltaG_exact": _exact(g_mean),
            "cell_deltaG": _display(g_mean),
            "deltaG_median_exact": _exact(g_median),
            "deltaG_median": _display(g_median),
            "deltaG_min_exact": _exact(g_min),
            "deltaG_min": _display(g_min),
            "deltaG_max_exact": _exact(g_max),
            "deltaG_max": _display(g_max),
            "cell_delta_signed_gap_median_exact": _exact(cell_delta_s),
            "cell_delta_signed_gap_median": _display(cell_delta_s),
            "cell_deltaRecovery_exact": _exact(cell_delta_recovery),
            "cell_deltaRecovery": _display(cell_delta_recovery),
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_rng_seed": BOOTSTRAP_SEED,
            "bootstrap_percentile_method": BOOTSTRAP_PERCENTILE_METHOD,
        }
        row.update(_arm_summary(rows, "KG"))
        row.update(_arm_summary(rows, "TR"))
        for metric, prefix in (
            ("deltaG", "deltaG"),
            ("delta_signed_gap_median", "delta_signed_gap_median"),
            ("deltaRecovery", "deltaRecovery"),
        ):
            summary = bootstrap.cell_metrics.get(
                (cell, metric), BootstrapSummary(0, None, None, None)
            )
            for label, value in (
                ("median", summary.median),
                ("ci_low", summary.low),
                ("ci_high", summary.high),
            ):
                row[f"{prefix}_bootstrap_{label}_exact"] = _exact(value)
                row[f"{prefix}_bootstrap_{label}"] = _display(value)
        output.append(row)
    return output


def _spearman_exact_description(result: SpearmanResult) -> str:
    if not result.defined:
        return ""
    return (
        f"cov={_exact(result.covariance)};"
        f"var_x={_exact(result.variance_x)};"
        f"var_y={_exact(result.variance_y)}"
    )


def _spearman_row(
    *,
    panel: str,
    metric: str,
    cells: Sequence[str],
    cell_means: Mapping[str, Mapping[str, Fraction]],
    omitted: str = "",
) -> tuple[dict[str, Any], SpearmanResult]:
    result = _association_for_cells(cells, cell_means, metric)
    direction = ""
    if result.defined:
        if result.covariance > 0:
            direction = "positive"
        elif result.covariance < 0:
            direction = "negative"
        else:
            direction = "zero"
    return (
        {
            "row_type": "SPEARMAN",
            "panel": panel,
            "metric": metric,
            "omitted": omitted,
            "n_cells": len(cells),
            "defined": int(result.defined),
            "value_exact": _spearman_exact_description(result),
            "value": _display_float(result.rho),
            "ordering": direction,
            "reason": result.reason,
        },
        result,
    )


def _ordering_and_gate_rows(
    aggregates: Sequence[SeedAggregate],
    paired: Sequence[PairedSeed],
    panels: Mapping[str, Sequence[str]],
    bootstrap: BootstrapResults,
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, SpearmanResult]]:
    cell_means = _paired_cell_means(paired)
    rows: list[dict[str, Any]] = []
    associations: dict[str, SpearmanResult] = {}

    association_requests = (
        ("B_reranking", "deltaG", tuple(panels.get("B_reranking", ()))),
        (
            "B_reranking",
            "delta_signed_gap_median",
            tuple(panels.get("B_reranking", ())),
        ),
        (
            "A_registered_context_confounded",
            "deltaG",
            tuple(panels.get("A_registered_context", ())),
        ),
        (
            "A_registered_context_confounded",
            "delta_signed_gap_median",
            tuple(panels.get("A_registered_context", ())),
        ),
        (
            "C_sighted_reference",
            "deltaG",
            tuple(panels.get("C_sighted_reference", ())),
        ),
    )
    for panel_name, metric, cells in association_requests:
        panel_lookup = (
            "A_registered_context"
            if panel_name == "A_registered_context_confounded"
            else panel_name
        )
        row, result = _spearman_row(
            panel=panel_name,
            metric=metric,
            cells=cells,
            cell_means=cell_means,
        )
        rows.append(row)
        associations[f"{panel_lookup}:{metric}"] = result

    panel_b = tuple(panels.get("B_reranking", ()))
    for omitted_cell in panel_b:
        kept = tuple(cell for cell in panel_b if cell != omitted_cell)
        row, result = _spearman_row(
            panel="B_reranking_leave_one_cell_out",
            metric="deltaG",
            cells=kept,
            cell_means=cell_means,
            omitted=omitted_cell,
        )
        rows.append(row)
        associations[f"B_LO_CELL:{omitted_cell}"] = result

    parent_by_cell = {
        row.cell: row.parent
        for row in paired
    }
    panel_b_parents = tuple(
        dict.fromkeys(parent_by_cell[cell] for cell in panel_b if cell in parent_by_cell)
    )
    for omitted_parent in panel_b_parents:
        kept = tuple(
            cell
            for cell in panel_b
            if parent_by_cell.get(cell) != omitted_parent
        )
        row, result = _spearman_row(
            panel="B_reranking_leave_one_parent_out",
            metric="deltaG",
            cells=kept,
            cell_means=cell_means,
            omitted=omitted_parent,
        )
        if len(kept) < 3:
            result = SpearmanResult(
                len(kept), Fraction(0), Fraction(0), Fraction(0),
                "fewer_than_three_cells"
            )
            row.update(
                {
                    "defined": 0,
                    "value_exact": "",
                    "value": "",
                    "ordering": "",
                    "reason": result.reason,
                }
            )
        rows.append(row)
        associations[f"B_LO_PARENT:{omitted_parent}"] = result

    adverse = {
        "lab3_f1dead",
        "lab3_f1dead_z2",
        "lab3_f2dead_lowsun",
    }
    trimmed_cells = tuple(
        cell
        for cell in panels.get("A_registered_context", ())
        if cell not in adverse
    )
    trimmed_row, trimmed_result = _spearman_row(
        panel="A_without_detector_censored_cells",
        metric="deltaG",
        cells=trimmed_cells,
        cell_means=cell_means,
        omitted=_join(sorted(adverse)),
    )
    rows.append(trimmed_row)
    associations["A_TRIMMED:deltaG"] = trimmed_result

    concordance_counts: dict[str, Optional[int]] = {}
    for panel_name in ("B_reranking", "C_sighted_reference"):
        cells = tuple(panels.get(panel_name, ()))
        count = 0
        complete = True
        for left_index, left in enumerate(cells):
            for right in cells[left_index + 1 :]:
                if (
                    left not in cell_means
                    or right not in cell_means
                    or "deltaG" not in cell_means[left]
                    or "deltaG" not in cell_means[right]
                ):
                    complete = False
                    rows.append(
                        {
                            "row_type": "PAIR",
                            "panel": panel_name,
                            "metric": "deltaG_vs_deltaRecovery",
                            "cell_1": left,
                            "cell_2": right,
                            "defined": 0,
                            "concordant": 0,
                            "reason": "missing_cell_metric",
                        }
                    )
                    continue
                dx = cell_means[left]["deltaG"] - cell_means[right]["deltaG"]
                dy = (
                    cell_means[left]["deltaRecovery"]
                    - cell_means[right]["deltaRecovery"]
                )
                concordant, ordering = strict_pair_concordance(
                    cell_means[left]["deltaG"],
                    cell_means[right]["deltaG"],
                    cell_means[left]["deltaRecovery"],
                    cell_means[right]["deltaRecovery"],
                )
                count += int(concordant)
                rows.append(
                    {
                        "row_type": "PAIR",
                        "panel": panel_name,
                        "metric": "deltaG_vs_deltaRecovery",
                        "cell_1": left,
                        "cell_2": right,
                        "defined": 1,
                        "predictor_difference_exact": _exact(dx),
                        "outcome_difference_exact": _exact(dy),
                        "ordering": ordering,
                        "concordant": int(concordant),
                        "reason": "",
                    }
                )
        concordance_counts[panel_name] = count if complete else None

    for (panel_name, metric), summary in sorted(bootstrap.associations.items()):
        rows.append(
            {
                "row_type": "BOOTSTRAP",
                "panel": panel_name,
                "metric": f"spearman_{metric}",
                "defined": int(summary.defined_replicates > 0),
                "bootstrap_defined_replicates": summary.defined_replicates,
                "bootstrap_median": _display_float(summary.median),
                "bootstrap_ci_low": _display_float(summary.low),
                "bootstrap_ci_high": _display_float(summary.high),
                "reason": (
                    f"undefined_replicates="
                    f"{BOOTSTRAP_RESAMPLES - summary.defined_replicates};"
                    f"percentile_method={BOOTSTRAP_PERCENTILE_METHOD}"
                ),
            }
        )
    for panel_name, summary in sorted(bootstrap.concordance_counts.items()):
        rows.append(
            {
                "row_type": "BOOTSTRAP",
                "panel": panel_name,
                "metric": "pairwise_concordance_count",
                "defined": int(summary.defined_replicates > 0),
                "bootstrap_defined_replicates": summary.defined_replicates,
                "bootstrap_median_exact": _exact(summary.median),
                "bootstrap_median": _display(summary.median),
                "bootstrap_ci_low_exact": _exact(summary.low),
                "bootstrap_ci_low": _display(summary.low),
                "bootstrap_ci_high_exact": _exact(summary.high),
                "bootstrap_ci_high": _display(summary.high),
                "reason": (
                    f"undefined_replicates="
                    f"{BOOTSTRAP_RESAMPLES - summary.defined_replicates};"
                    f"percentile_method={BOOTSTRAP_PERCENTILE_METHOD}"
                ),
            }
        )
    rows.append(
        {
            "row_type": "BOOTSTRAP_CONTRACT",
            "metric": "shared_paired_seed_resampling",
            "value_exact": (
                f"resamples={BOOTSTRAP_RESAMPLES};seed={BOOTSTRAP_SEED};"
                f"draws_per_replicate={BOOTSTRAP_SAMPLE_SIZE}"
            ),
            "reason": BOOTSTRAP_PERCENTILE_METHOD,
        }
    )

    reference = tuple(panels.get("C_sighted_reference", ()))
    aggregate_by_cell = {
        cell: [row for row in aggregates if row.cell == cell]
        for cell in reference
    }
    gate_1_parts: list[str] = []
    gate_1 = True
    for cell in reference:
        cell_rows = aggregate_by_cell[cell]
        exact_count = len(cell_rows) == 40
        all_analyzed = exact_count and all(row.analyzed_count >= 1 for row in cell_rows)
        any_nonzero = any(row.g is not None and row.g != 0 for row in cell_rows)
        cell_pass = exact_count and all_analyzed and any_nonzero
        gate_1 &= cell_pass
        gate_1_parts.append(
            f"{cell}:records={len(cell_rows)},"
            f"all_analyzed={int(all_analyzed)},nonzero={int(any_nonzero)}"
        )

    reference_means = [
        cell_means[cell]["deltaG"]
        for cell in reference
        if cell in cell_means and "deltaG" in cell_means[cell]
    ]
    if len(reference_means) == len(reference):
        gate_2, gate_2_reason = gate_two_exact(reference_means)
    else:
        gate_2 = False
        gate_2_reason = "missing_reference_cell_metric"

    panel_b_primary = associations.get(
        "B_reranking:deltaG",
        SpearmanResult(0, Fraction(0), Fraction(0), Fraction(0), "missing_panel"),
    )
    gate_3 = spearman_at_least(panel_b_primary, Fraction(7, 10))
    gate_3_reason = (
        f"rho={_display_float(panel_b_primary.rho)};threshold=0.70"
        if panel_b_primary.defined
        else panel_b_primary.reason
    )

    reference_count = concordance_counts.get("C_sighted_reference")
    gate_4 = reference_count is not None and reference_count >= 5
    gate_4_reason = (
        "undefined"
        if reference_count is None
        else f"concordant_pairs={reference_count}/6"
    )

    signed_result = associations.get(
        "B_reranking:delta_signed_gap_median",
        SpearmanResult(0, Fraction(0), Fraction(0), Fraction(0), "missing_panel"),
    )
    leave_one_results = [
        result
        for key, result in associations.items()
        if key.startswith("B_LO_CELL:")
    ]
    gate_5 = (
        signed_result.defined
        and signed_result.covariance >= 0
        and len(leave_one_results) == len(panel_b)
        and all(result.defined and result.covariance >= 0 for result in leave_one_results)
    )
    gate_5_reason = (
        f"signed_defined={int(signed_result.defined)};"
        f"signed_nonnegative={int(signed_result.defined and signed_result.covariance >= 0)};"
        f"leave_one_nonnegative="
        f"{sum(int(result.defined and result.covariance >= 0) for result in leave_one_results)}"
        f"/{len(panel_b)}"
    )

    gate_6 = trimmed_result.defined and trimmed_result.covariance > 0
    gate_6_reason = (
        f"rho={_display_float(trimmed_result.rho)};direction=positive_required"
        if trimmed_result.defined
        else trimmed_result.reason
    )
    gates = {
        "gate_1": gate_1,
        "gate_2": gate_2,
        "gate_3": gate_3,
        "gate_4": gate_4,
        "gate_5": gate_5,
        "gate_6": gate_6,
    }
    gate_reasons = {
        "gate_1": ";".join(gate_1_parts),
        "gate_2": gate_2_reason,
        "gate_3": gate_3_reason,
        "gate_4": gate_4_reason,
        "gate_5": gate_5_reason,
        "gate_6": gate_6_reason,
    }
    for index in range(1, 7):
        name = f"gate_{index}"
        rows.append(
            {
                "row_type": "GATE",
                "metric": name,
                "defined": 1,
                "passed": int(gates[name]),
                "reason": gate_reasons[name],
            }
        )
    rows.append(
        {
            "row_type": "DECISION",
            "metric": "all_six_gates",
            "defined": 1,
            "passed": int(all(gates.values())),
            "reason": (
                "drafting_only" if all(gates.values()) else "defer_or_descope"
            ),
        }
    )
    return rows, gates, associations


def _plot_limits(values: Sequence[float]) -> tuple[float, float]:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return -1.0, 1.0
    low = min(finite)
    high = max(finite)
    if low == high:
        padding = max(0.05, abs(low) * 0.08, 0.01)
    else:
        padding = max((high - low) * 0.10, 0.01)
    return low - padding, high + padding


def _configure_matplotlib() -> Any:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        matplotlib.rcParams.update(
            {
                "font.family": "DejaVu Sans",
                "font.size": 8,
                "axes.titlesize": 9,
                "axes.labelsize": 8,
                "legend.fontsize": 7,
                "figure.dpi": 100,
                "savefig.dpi": 160,
                "axes.grid": True,
                "grid.alpha": 0.25,
                "axes.unicode_minus": False,
            }
        )
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RetrospectiveError("matplotlib is required for frozen figures") from exc
    return plt


def _save_qgap_figure(
    path: Path,
    paired: Sequence[PairedSeed],
    aggregates: Sequence[SeedAggregate],
    panels: Mapping[str, Sequence[str]],
    associations: Mapping[str, SpearmanResult],
    bootstrap: BootstrapResults,
) -> None:
    plt = _configure_matplotlib()
    means = _paired_cell_means(paired)
    all_cells = sorted(means)
    palette = plt.get_cmap("tab10")
    colors = {
        cell: palette(index % 10)
        for index, cell in enumerate(all_cells)
    }
    aggregate_groups: dict[tuple[str, str], list[SeedAggregate]] = {}
    for aggregate in aggregates:
        aggregate_groups.setdefault((aggregate.cell, aggregate.arm), []).append(
            aggregate
        )
    figure, axes = plt.subplots(1, 3, figsize=(15.0, 6.4))
    requests = (
        (
            axes[0],
            "B_reranking",
            "deltaG",
            "Panel B — start-state Q-gap proxy",
            associations.get("B_reranking:deltaG"),
        ),
        (
            axes[1],
            "B_reranking",
            "delta_signed_gap_median",
            "Panel B — signed-gap median sensitivity",
            associations.get("B_reranking:delta_signed_gap_median"),
        ),
        (
            axes[2],
            "A_registered_context",
            "deltaG",
            "Confounded sensitivity — includes detector censoring",
            associations.get("A_registered_context:deltaG"),
        ),
    )
    for axis, panel_name, predictor, title, association in requests:
        legend_handles = []
        legend_labels = []
        cells = tuple(panels.get(panel_name, ()))
        points = [
            (
                cell,
                float(means[cell][predictor]),
                float(means[cell]["deltaRecovery"]),
            )
            for cell in cells
            if cell in means
            and predictor in means[cell]
            and "deltaRecovery" in means[cell]
        ]
        for cell, x_value, y_value in points:
            x_bootstrap = bootstrap.cell_metrics.get((cell, predictor))
            y_bootstrap = bootstrap.cell_metrics.get((cell, "deltaRecovery"))
            x_error = None
            y_error = None
            if (
                x_bootstrap is not None
                and x_bootstrap.low is not None
                and x_bootstrap.high is not None
            ):
                x_error = [[
                    max(0.0, x_value - float(x_bootstrap.low)),
                ], [
                    max(0.0, float(x_bootstrap.high) - x_value),
                ]]
            if (
                y_bootstrap is not None
                and y_bootstrap.low is not None
                and y_bootstrap.high is not None
            ):
                y_error = [[
                    max(0.0, y_value - float(y_bootstrap.low)),
                ], [
                    max(0.0, float(y_bootstrap.high) - y_value),
                ]]
            point_artist = axis.errorbar(
                [x_value],
                [y_value],
                xerr=x_error,
                yerr=y_error,
                fmt="o",
                color=colors.get(cell, "#333333"),
                markersize=5.5,
                markeredgecolor="black",
                markeredgewidth=0.4,
                elinewidth=0.75,
                capsize=2,
                zorder=3,
            )
            kg_rows = aggregate_groups.get((cell, "KG"), [])
            tr_rows = aggregate_groups.get((cell, "TR"), [])
            reach_context = ""
            if kg_rows and tr_rows:
                kg_reach = _mean([row.reachable_fraction for row in kg_rows])
                tr_reach = _mean([row.reachable_fraction for row in tr_rows])
                kg_routes = [
                    row.route_mean for row in kg_rows if row.route_mean is not None
                ]
                tr_routes = [
                    row.route_mean for row in tr_rows if row.route_mean is not None
                ]
                route_text = "undefined"
                if kg_routes and tr_routes:
                    route_text = (
                        f"{float(_mean(kg_routes)):.2f}/"
                        f"{float(_mean(tr_routes)):.2f}"
                    )
                reach_context = (
                    f"\nreach K/T={float(kg_reach):.2f}/{float(tr_reach):.2f}"
                    f"; route K/T={route_text}"
                )
            legend_handles.append(point_artist)
            legend_labels.append(cell + reach_context.replace("\n", "; "))
        axis.set_title(title)
        axis.set_xlabel(
            "Mean Δ start-state Q-gap proxy"
            if predictor == "deltaG"
            else "Mean Δ signed-gap median"
        )
        axis.set_ylabel("Mean Δ censored recovery episodes")
        axis.set_xlim(_plot_limits([point[1] for point in points]))
        axis.set_ylim(_plot_limits([point[2] for point in points]))
        rho_text = (
            "ρ=undefined"
            if association is None or not association.defined
            else f"ρ={association.rho:.3f}"
        )
        bootstrap_key = (panel_name, predictor)
        rho_bootstrap = bootstrap.associations.get(bootstrap_key)
        stability_text = ""
        if (
            rho_bootstrap is not None
            and rho_bootstrap.low is not None
            and rho_bootstrap.high is not None
        ):
            stability_text = (
                f"\n95% seed stability "
                f"[{rho_bootstrap.low:.3f}, {rho_bootstrap.high:.3f}]"
                f"\ndefined {rho_bootstrap.defined_replicates}/"
                f"{BOOTSTRAP_RESAMPLES}"
            )
        axis.text(
            0.02,
            0.98,
            rho_text + stability_text,
            transform=axis.transAxes,
            va="top",
            ha="left",
            fontsize=6.5,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
        )
        axis.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.20),
            frameon=False,
            fontsize=5.5,
            handlelength=1.3,
            handletextpad=0.5,
            borderaxespad=0.0,
        )
    figure.suptitle(
        "Descriptive cell ordering; error bars are paired-seed 95% stability intervals",
        fontsize=10,
    )
    figure.tight_layout(rect=(0.0, 0.27, 1.0, 0.95))
    figure.savefig(
        path,
        format="png",
        dpi=160,
        metadata={"Software": "phase2_qgap_retrospective"},
    )
    plt.close(figure)


def _detector_plot_series(
    aggregates: Sequence[SeedAggregate],
    detector_rows: Sequence[Mapping[str, Any]],
    panels: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Build visible any/all/component descriptor series for Panel A."""
    panel_cells = tuple(panels.get("A_registered_context", ()))
    output: list[dict[str, Any]] = []
    for cell in panel_cells:
        for arm in ("KG", "TR"):
            outcome_rows = [
                row for row in aggregates if row.cell == cell and row.arm == arm
            ]
            raw_rows = [
                row
                for row in detector_rows
                if str(row["faulty_profile"]) == cell and str(row["arm"]) == arm
            ]
            if not outcome_rows or not raw_rows:
                continue
            detection_fraction = Fraction(
                sum(row.detection_occurrence for row in outcome_rows),
                len(outcome_rows),
            )
            detect_mean = _mean(
                [Fraction(row.detect.value) for row in outcome_rows]
            )
            censor_count = sum(int(row.detect.censored) for row in outcome_rows)
            scenario_keys = sorted(
                {
                    (
                        int(row["run_id"]),
                        int(row["seed"]),
                        int(row["scenario_order"]),
                    )
                    for row in raw_rows
                }
            )
            by_scenario = {
                key: next(
                    row
                    for row in raw_rows
                    if (
                        int(row["run_id"]),
                        int(row["seed"]),
                        int(row["scenario_order"]),
                    )
                    == key
                )
                for key in scenario_keys
            }
            any_fraction = Fraction(
                sum(
                    int(row["any_fault_component_opportunity"])
                    for row in by_scenario.values()
                ),
                len(by_scenario),
            )
            output.append(
                {
                    "cell": cell,
                    "arm": arm,
                    "descriptor": "any",
                    "component": "",
                    "opportunity_fraction": any_fraction,
                    "detection_fraction": detection_fraction,
                    "detect_episode_mean": detect_mean,
                    "detect_censor_count": censor_count,
                }
            )
            components = sorted({str(row["component"]) for row in raw_rows})
            if len(components) > 1:
                all_fraction = Fraction(
                    sum(
                        int(row["all_fault_components_opportunity"])
                        for row in by_scenario.values()
                    ),
                    len(by_scenario),
                )
                output.append(
                    {
                        "cell": cell,
                        "arm": arm,
                        "descriptor": "all",
                        "component": "",
                        "opportunity_fraction": all_fraction,
                        "detection_fraction": detection_fraction,
                        "detect_episode_mean": detect_mean,
                        "detect_censor_count": censor_count,
                    }
                )
                for component in components:
                    component_rows = [
                        row for row in raw_rows if str(row["component"]) == component
                    ]
                    output.append(
                        {
                            "cell": cell,
                            "arm": arm,
                            "descriptor": "component",
                            "component": component,
                            "opportunity_fraction": Fraction(
                                sum(
                                    int(row["component_opportunity"])
                                    for row in component_rows
                                ),
                                len(component_rows),
                            ),
                            "detection_fraction": detection_fraction,
                            "detect_episode_mean": detect_mean,
                            "detect_censor_count": censor_count,
                        }
                    )
    return output


def _save_detectability_figure(
    path: Path,
    aggregates: Sequence[SeedAggregate],
    detector_rows: Sequence[Mapping[str, Any]],
    panels: Mapping[str, Sequence[str]],
) -> None:
    plt = _configure_matplotlib()
    from matplotlib.lines import Line2D

    all_cells = sorted({row.cell for row in aggregates})
    palette = plt.get_cmap("tab10")
    colors = {
        cell: palette(index % 10)
        for index, cell in enumerate(all_cells)
    }
    series = _detector_plot_series(aggregates, detector_rows, panels)
    figure, axes = plt.subplots(1, 2, figsize=(14.0, 7.0))
    for axis, outcome_key, outcome_label in (
        (axes[0], "detection_fraction", "Observed detection fraction across seeds"),
        (
            axes[1],
            "detect_episode_mean",
            "Mean censored DetectEpisode",
        ),
    ):
        for item in series:
            descriptor = str(item["descriptor"])
            arm = str(item["arm"])
            marker = "o" if arm == "KG" else "s"
            opportunity = float(item["opportunity_fraction"])
            outcome = float(item[outcome_key])
            if descriptor == "component":
                marker = "x"
                facecolor = colors[item["cell"]]
                edgecolor = colors[item["cell"]]
                size = 34
            elif descriptor == "all":
                facecolor = "none"
                edgecolor = colors[item["cell"]]
                size = 48
            else:
                facecolor = colors[item["cell"]]
                edgecolor = "black"
                size = 45
            if descriptor == "component":
                axis.scatter(
                    [opportunity],
                    [outcome],
                    color=colors[item["cell"]],
                    marker=marker,
                    s=size,
                    linewidths=0.9,
                    zorder=3,
                )
            else:
                axis.scatter(
                    [opportunity],
                    [outcome],
                    facecolors=facecolor,
                    edgecolors=edgecolor,
                    marker=marker,
                    s=size,
                    linewidths=0.7,
                    zorder=3,
                )
        axis.set_xlim(-0.05, 1.05)
        axis.set_xlabel("Mean scenario DetectorOpportunity fraction")
        axis.set_ylabel(outcome_label)
        axis.set_title(
            "Occurrence and censoring"
            if outcome_key == "detection_fraction"
            else "Censored detection timing"
        )
    axes[0].plot(
        [0, 1],
        [0, 1],
        color="#777777",
        linewidth=0.8,
        linestyle="--",
        label="identity reference",
        zorder=1,
    )
    axes[0].set_ylim(-0.05, 1.05)
    detect_values = [float(item["detect_episode_mean"]) for item in series]
    axes[1].set_ylim(_plot_limits(detect_values))
    censored_items = [
        item
        for item in series
        if item["descriptor"] == "any" and item["detect_censor_count"] > 0
    ]
    censor_text = "Nonzero censor counts:\n" + "\n".join(
        f"{item['cell']} {item['arm']}: c={item['detect_censor_count']}"
        for item in censored_items
    )
    axes[1].text(
        0.98,
        0.98,
        censor_text,
        transform=axes[1].transAxes,
        va="top",
        ha="right",
        fontsize=6.0,
        bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
    )
    cell_handles = [
        Line2D(
            [],
            [],
            color=colors[cell],
            marker="o",
            linestyle="None",
            markersize=5,
            label=cell,
        )
        for cell in panels.get("A_registered_context", ())
        if cell in colors
    ]
    encoding_handles = [
        Line2D([], [], color="black", marker="o", linestyle="None", label="KG"),
        Line2D([], [], color="black", marker="s", linestyle="None", label="TR"),
        Line2D(
            [],
            [],
            color="black",
            marker="o",
            markerfacecolor="black",
            linestyle="None",
            label="filled = ANY",
        ),
        Line2D(
            [],
            [],
            color="black",
            marker="o",
            markerfacecolor="none",
            linestyle="None",
            label="open = ALL",
        ),
        Line2D(
            [],
            [],
            color="black",
            marker="x",
            linestyle="None",
            label="x = component",
        ),
    ]
    figure.legend(
        handles=cell_handles + encoding_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=5,
        frameon=False,
        fontsize=6.4,
        handletextpad=0.4,
        columnspacing=1.2,
    )
    figure.suptitle(
        "Panel A DetectorOpportunity: ANY, ALL, and multi-fault components",
        fontsize=10,
    )
    figure.tight_layout(rect=(0.0, 0.14, 1.0, 0.95))
    figure.savefig(
        path,
        format="png",
        dpi=160,
        metadata={"Software": "phase2_qgap_retrospective"},
    )
    plt.close(figure)


def _results_markdown(
    *,
    spec: Mapping[str, Any],
    paired: Sequence[PairedSeed],
    aggregates: Sequence[SeedAggregate],
    panels: Mapping[str, Sequence[str]],
    gates: Mapping[str, bool],
    associations: Mapping[str, SpearmanResult],
) -> str:
    means = _paired_cell_means(paired)
    lines = [
        "# Phase 2b-A start-state Q-gap proxy retrospective",
        "",
        "Status: descriptive and sighted.",
        "",
        "The predictor in every table and figure is a start-state Q-gap proxy. "
        "It is not an exact post-detection burden or an adaptation replay.",
        "",
        "Known corrected Tier-1 outcomes were disclosed before computation: "
        "2 supported, 3 adverse, and 3 null; the three adverse cells are "
        "detector-censoring driven.",
        "",
        "## Cell ordering",
        "",
        "| Cell | Mean Δ start-state Q-gap proxy | Mean Δ censored recovery | Mean Δ signed-gap median |",
        "|---|---:|---:|---:|",
    ]
    ordered_cells: list[str] = []
    for panel_name in (
        "A_registered_context",
        "C_sighted_reference",
        "nonregistered_recovery_descriptive",
    ):
        for cell in panels.get(panel_name, ()):
            if cell not in ordered_cells:
                ordered_cells.append(cell)
    for cell in ordered_cells:
        metrics = means.get(cell, {})
        lines.append(
            f"| `{cell}` | {_display(metrics.get('deltaG')) or 'undefined'} "
            f"| {_display(metrics.get('deltaRecovery')) or 'undefined'} "
            f"| {_display(metrics.get('delta_signed_gap_median')) or 'undefined'} |"
        )

    lines.extend(
        [
            "",
            "## Rank descriptors",
            "",
            "| Analysis | Spearman rho | Direction |",
            "|---|---:|---|",
        ]
    )
    for key, label in (
        ("B_reranking:deltaG", "Panel B, mean burden"),
        (
            "B_reranking:delta_signed_gap_median",
            "Panel B, signed-gap median sensitivity",
        ),
        ("A_registered_context:deltaG", "Panel A, confounded sensitivity"),
        (
            "A_TRIMMED:deltaG",
            "Panel A after removing the three detector-censored cells",
        ),
    ):
        result = associations.get(key)
        if result is None or not result.defined:
            rho = "undefined"
            direction = result.reason if result is not None else "missing"
        else:
            rho = f"{result.rho:.6f}"
            direction = (
                "positive"
                if result.covariance > 0
                else "negative"
                if result.covariance < 0
                else "zero"
            )
        lines.append(f"| {label} | {rho} | {direction} |")

    lines.extend(
        [
            "",
            "## Per-arm Q and route context",
            "",
            "| Cell | Arm | Burden mean / median / range | Signed gap mean / median / range | F tie / R tie | Reach / terminal / unreachable | Route mean / median / range | Route-count distribution |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for cell in ordered_cells:
        cell_aggregates = [
            row for row in aggregates if row.cell == cell
        ]
        for arm in ("KG", "TR"):
            summary = _arm_summary(cell_aggregates, arm)
            burden = (
                f"{summary[f'{arm}_burden_scenario_mean']} / "
                f"{summary[f'{arm}_burden_scenario_median']} / "
                f"[{summary[f'{arm}_burden_scenario_min']}, "
                f"{summary[f'{arm}_burden_scenario_max']}]"
            )
            signed = (
                f"{summary[f'{arm}_signed_gap_scenario_mean']} / "
                f"{summary[f'{arm}_signed_gap_scenario_median']} / "
                f"[{summary[f'{arm}_signed_gap_scenario_min']}, "
                f"{summary[f'{arm}_signed_gap_scenario_max']}]"
            )
            ties = (
                f"{summary[f'{arm}_faulty_max_tie_rate_mean']} / "
                f"{summary[f'{arm}_survivor_max_tie_rate_mean']}"
            )
            classes = (
                f"{summary[f'{arm}_reachable_fraction_mean']} / "
                f"{summary[f'{arm}_no_reranking_needed_fraction_mean']} / "
                f"{summary[f'{arm}_unreachable_fraction_mean']}"
            )
            routes = (
                f"{summary[f'{arm}_route_length_mean']} / "
                f"{summary[f'{arm}_route_length_median']} / "
                f"[{summary[f'{arm}_route_length_min']}, "
                f"{summary[f'{arm}_route_length_max']}]"
            )
            lines.append(
                f"| `{cell}` | {arm} | {burden} | {signed} | {ties} "
                f"| {classes} | {routes} "
                f"| `{summary[f'{arm}_route_count_distribution']}` |"
            )

    lines.extend(
        [
            "",
            "## Detectability context",
            "",
            "| Cell | Arm | ANY | ALL | Per component | Detection fraction | Mean censored DetectEpisode | Detect censors | Recovery censors |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for cell in panels.get("A_registered_context", ()):
        for arm in ("KG", "TR"):
            selected = [
                row
                for row in aggregates
                if row.cell == cell and row.arm == arm
            ]
            if not selected:
                continue
            arm_summary = _arm_summary(selected, arm)
            lines.append(
                f"| `{cell}` | {arm} "
                f"| {_display(_mean([row.detector_fraction for row in selected]))} "
                f"| {_display(_mean([row.detector_all_fraction for row in selected]))} "
                f"| `{arm_summary[f'{arm}_detector_component_fractions_exact']}` "
                f"| {_display(Fraction(sum(row.detection_occurrence for row in selected), len(selected)))} "
                f"| {_display(_mean([Fraction(row.detect.value) for row in selected]))} "
                f"| {sum(int(row.detect.censored) for row in selected)} "
                f"| {sum(int(row.recovery.censored) for row in selected)} |"
            )

    lines.extend(
        [
            "",
            "## Six screening gates",
            "",
            "| Gate | Result |",
            "|---:|---|",
        ]
    )
    for index in range(1, 7):
        passed = gates[f"gate_{index}"]
        lines.append(f"| {index} | {'PASS' if passed else 'FAIL'} |")
    lines.extend(
        [
            "",
            (
                "All six gates pass; the only permitted next action is drafting "
                "a separate prospective plan."
                if all(gates.values())
                else "At least one gate fails; the later campaign is deferred or descoped."
            ),
            "",
            "## Bootstrap and interpretation limits",
            "",
            f"Exactly {BOOTSTRAP_RESAMPLES:,} paired-seed replicates used one "
            f"`random.Random({BOOTSTRAP_SEED})` instance. Each replicate used "
            "20 successive `randrange(20)` draws shared across every cell and "
            "outcome. Percentiles use sorted " + BOOTSTRAP_PERCENTILE_METHOD + ".",
            "",
            "Undefined bootstrap rank replicates are excluded only from their "
            "finite percentile vector and their count remains in "
            "`ordering_assessment.csv`.",
            "",
            "Resampling seeds does not create independent lab designs. Cells "
            "sharing a physical design or parent topology are not independent "
            "mechanism replications.",
            "",
            "Combined serialized Q-values are primary. Summed logical-zone "
            "values are retained only as a serialization diagnostic.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_checksum_inventory(out_dir: Path) -> None:
    rows = []
    for name in sorted(OUTPUT_NAMES[:-1]):
        path = out_dir / name
        content = path.read_bytes()
        rows.append(
            {
                "path": name,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    _write_csv(out_dir / "SHA256SUMS.csv", ("path", "bytes", "sha256"), rows)


def run(
    repo_root: Path,
    source_root: Path,
    spec_path: Path,
    source_manifest_path: Path,
    out_dir: Path,
    zip_root: Optional[Path] = None,
    require_zips: bool = True,
) -> tuple[Path, ...]:
    """Execute the frozen computation from checker-owned immutable records."""
    if validate_inputs is None:
        raise RetrospectiveError(
            "analysis.validate_phase2_qgap_inputs is unavailable"
        )
    repo_root = Path(repo_root)
    source_root = Path(source_root)
    spec_path = Path(spec_path)
    source_manifest_path = Path(source_manifest_path)
    out_dir = Path(out_dir)
    zip_root = None if zip_root is None else Path(zip_root)

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrospectiveError(f"cannot load frozen specification: {exc}") from exc
    if spec.get("schema_version") != "phase2-qgap-retrospective-v1":
        raise RetrospectiveError("unexpected frozen specification schema")
    if spec.get("protocol_revision") != "2026-07-27d":
        raise RetrospectiveError(
            "frozen specification must declare protocol_revision 2026-07-27d"
        )
    raw_panels = spec.get("panels")
    if not isinstance(raw_panels, dict):
        raise RetrospectiveError("frozen specification has no panel mapping")
    panels: dict[str, tuple[str, ...]] = {}
    for panel_name, members in raw_panels.items():
        if not isinstance(members, list):
            raise RetrospectiveError(f"panel {panel_name!r} is not a list")
        panels[str(panel_name)] = tuple(str(member) for member in members)

    checked = validate_inputs(
        repo_root=repo_root,
        source_root=source_root,
        spec_path=spec_path,
        source_manifest_path=source_manifest_path,
        zip_root=zip_root,
        require_zips=require_zips,
    )
    records = tuple(checked.records)
    if not records:
        raise RetrospectiveError("input checker returned no records")
    cell_specs = load_frozen_cell_specs(spec_path)
    scenario_rows, detector_rows, aggregates = _process_records(
        records, cell_specs
    )
    paired, _ = _pair_seed_aggregates(aggregates)
    bootstrap = bootstrap_descriptors(
        paired,
        panels,
        resamples=BOOTSTRAP_RESAMPLES,
        rng_seed=BOOTSTRAP_SEED,
    )
    seed_rows = _seed_output_rows(aggregates, paired)
    cell_rows = _cell_summary_rows(aggregates, paired, panels, bootstrap)
    ordering_rows, gates, associations = _ordering_and_gate_rows(
        aggregates, paired, panels, bootstrap
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    output_source_manifest = out_dir / "source_manifest.json"
    enriched_manifest = _enriched_source_manifest_bytes(
        repo_root=repo_root,
        source_root=source_root,
        spec_path=spec_path,
        source_manifest_path=source_manifest_path,
        records=records,
        spec=spec,
    )
    _write_bytes(output_source_manifest, enriched_manifest)
    _write_csv(
        out_dir / "qgap_scenario_rows.csv",
        SCENARIO_FIELDS,
        scenario_rows,
    )
    _write_csv(out_dir / "qgap_seed_rows.csv", SEED_FIELDS, seed_rows)
    _write_csv(out_dir / "qgap_cell_summary.csv", CELL_FIELDS, cell_rows)
    _write_csv(
        out_dir / "detector_opportunity_rows.csv",
        DETECTOR_FIELDS,
        detector_rows,
    )
    _write_csv(
        out_dir / "ordering_assessment.csv",
        ORDERING_FIELDS,
        ordering_rows,
    )
    previous_mpl_config = os.environ.get("MPLCONFIGDIR")
    with tempfile.TemporaryDirectory(
        dir=out_dir, prefix=".phase2-qgap-mpl-"
    ) as mpl_config:
        os.environ["MPLCONFIGDIR"] = mpl_config
        try:
            _save_qgap_figure(
                out_dir / "qgap_vs_recovery.png",
                paired,
                aggregates,
                panels,
                associations,
                bootstrap,
            )
            _save_detectability_figure(
                out_dir / "detectability_audit.png",
                aggregates,
                detector_rows,
                panels,
            )
        finally:
            if previous_mpl_config is None:
                os.environ.pop("MPLCONFIGDIR", None)
            else:
                os.environ["MPLCONFIGDIR"] = previous_mpl_config
    markdown = _results_markdown(
        spec=spec,
        paired=paired,
        aggregates=aggregates,
        panels=panels,
        gates=gates,
        associations=associations,
    )
    _write_bytes(
        out_dir / "PHASE2_QGAP_RETROSPECTIVE_RESULTS.md",
        markdown.encode("utf-8"),
    )
    _write_checksum_inventory(out_dir)
    return tuple(out_dir / name for name in OUTPUT_NAMES)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the frozen Phase-2 start-state Q-gap proxy retrospective"
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--spec", dest="spec_path", type=Path, required=True)
    parser.add_argument(
        "--source-manifest",
        dest="source_manifest_path",
        type=Path,
        required=True,
    )
    parser.add_argument("--out", dest="out_dir", type=Path, required=True)
    parser.add_argument("--zip-root", type=Path)
    parser.add_argument(
        "--no-require-zips",
        action="store_true",
        help="permit a checked extracted source tree without local ZIP checks",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    outputs = run(
        repo_root=args.repo_root,
        source_root=args.source_root,
        spec_path=args.spec_path,
        source_manifest_path=args.source_manifest_path,
        out_dir=args.out_dir,
        zip_root=args.zip_root,
        require_zips=not args.no_require_zips,
    )
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
