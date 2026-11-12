#!/usr/bin/env python3
"""Fail-closed validation and immutable discovery for Phase-2b Q-gap inputs.

This module intentionally stops at metadata, provenance, and CSV-header
validation.  It does not parse Q values or calculate any retrospective
quantity.  Callers receive an ordered, immutable record for every frozen
``(run, seed, arm, cell)`` join and therefore never have to rediscover input
files by globbing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import locale
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any
from zipfile import BadZipFile, ZipFile


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_CLEAN_DIR_RE = re.compile(
    r"^clean-(?P<profile>.+)-stereo-(?P<boolean>true|false)-seed-(?P<seed>[0-9]+)$"
)
_REQUIRED_JOIN_FIELDS = (
    "run_id",
    "seed",
    "arm",
    "faulty_profile",
    "parent_profile",
    "parent_qtable_sha256",
    "scenario_schedule_sha256",
)
_PROTOCOL_REVISION = "2026-07-27d"


class InputValidationError(ValueError):
    """Raised when any frozen input contract is absent, duplicate, or invalid."""


@dataclass(frozen=True, slots=True)
class InputRecord:
    """One immutable, fully resolved Phase-2b input join."""

    run_id: int
    seed: int
    arm: str
    filename_boolean: str
    mode: str
    faulty_profile: str
    parent_profile: str
    manifest: Mapping[str, object]
    manifest_path: Path
    recovery_row: Mapping[str, str]
    recovery_path: Path
    detect_episode: int
    reconverge_episode: int
    recovery_episodes: int
    detector_version: str
    protocol_version: str
    adapt_episodes_effective: int
    ordered_scenario_ids: tuple[int, ...]
    scenario_rows: tuple[Mapping[str, object], ...]
    scenario_schedule_sha256: str
    combined_qtable_path: Path
    parent_qtable_paths: tuple[Path, ...]
    zone_qtable_paths: tuple[Path, ...]
    action_labels: tuple[str, ...]
    runtime_action_indices: tuple[int, ...]
    parent_qtable_sha256: str
    join_key: tuple[int, int, str, str, str, str, str]


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Validated records in deterministic run/seed/KG/TR/profile order."""

    records: tuple[InputRecord, ...]


@dataclass(frozen=True, slots=True)
class _ParentMetadata:
    scenario_file: str
    ordered_ids: tuple[int, ...]
    scenario_rows: tuple[Mapping[str, object], ...]
    schedule_sha256: str
    action_labels: tuple[str, ...]
    runtime_indices: tuple[int, ...]
    zone_count: int


def _fail(message: str) -> None:
    raise InputValidationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _as_int(value: object, context: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"{context}: expected an integer, got {value!r}")
    if minimum is not None and value < minimum:
        _fail(f"{context}: expected an integer >= {minimum}, got {value}")
    return value


def _as_str(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{context}: expected a non-empty string, got {value!r}")
    return value


def _as_mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{context}: expected a JSON object")
    return value


def _as_list(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(f"{context}: expected a JSON array")
    return value


def _unique(values: list[Any] | tuple[Any, ...], context: str) -> None:
    seen: set[Any] = set()
    for value in values:
        try:
            duplicate = value in seen
        except TypeError:
            _fail(f"{context}: contains a non-scalar entry {value!r}")
        if duplicate:
            _fail(f"{context}: duplicate entry {value!r}")
        seen.add(value)


def _json_pairs(context: str):
    def hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail(f"{context}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    return hook


def _load_json_bytes(data: bytes, context: str) -> Any:
    try:
        text = data.decode("utf-8-sig")
        return json.loads(text, object_pairs_hook=_json_pairs(context))
    except InputValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(f"{context}: invalid UTF-8 JSON: {exc}")


def _load_json(path: Path) -> Any:
    _require(path.is_file(), f"missing JSON file: {path}")
    try:
        return _load_json_bytes(path.read_bytes(), str(path))
    except OSError as exc:
        _fail(f"{path}: could not read JSON: {exc}")


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path, cache: dict[Path, str] | None = None) -> str:
    resolved = path.resolve()
    if cache is not None and resolved in cache:
        return cache[resolved]
    digest = hashlib.sha256()
    try:
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        _fail(f"{path}: could not hash file: {exc}")
    result = digest.hexdigest()
    if cache is not None:
        cache[resolved] = result
    return result


def _normal_relative_path(value: object, context: str) -> str:
    text = _as_str(value, context)
    _require("\\" not in text, f"{context}: paths must use forward slashes: {text!r}")
    path = PurePosixPath(text)
    _require(not path.is_absolute(), f"{context}: absolute path is forbidden: {text!r}")
    _require(
        text == path.as_posix() and all(part not in ("", ".", "..") for part in path.parts),
        f"{context}: non-normal relative path is forbidden: {text!r}",
    )
    return text


def _check_forbidden(text: str, markers: tuple[str, ...], context: str) -> None:
    lowered = text.casefold()
    for marker in markers:
        if marker in lowered:
            _fail(f"{context}: forbidden input marker {marker!r} in {text!r}")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _run_git(repo_root: Path, args: list[str], context: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        _fail(f"{context}: could not run git: {exc}")
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        _fail(f"{context}: git failed: {detail or 'unknown error'}")
    return completed.stdout


def _validate_source_blobs(
    repo_root: Path,
    spec: dict[str, Any],
    markers: tuple[str, ...],
) -> tuple[str, dict[str, bytes]]:
    source_commit = _as_str(spec.get("source_commit"), "spec.source_commit")
    resolved_commit = (
        _run_git(
            repo_root,
            ["rev-parse", "--verify", f"{source_commit}^{{commit}}"],
            "spec.source_commit",
        )
        .decode("ascii", errors="strict")
        .strip()
    )
    _require(
        resolved_commit == source_commit,
        f"spec.source_commit: expected canonical full commit {source_commit!r}, "
        f"git resolved {resolved_commit!r}",
    )

    declared = _as_mapping(spec.get("source_blob_oids"), "spec.source_blob_oids")
    _require(declared, "spec.source_blob_oids: must not be empty")
    normalized: list[str] = []
    blobs: dict[str, bytes] = {}
    for raw_path, raw_oid in declared.items():
        rel = _normal_relative_path(raw_path, f"spec.source_blob_oids[{raw_path!r}]")
        _check_forbidden(rel, markers, "spec.source_blob_oids")
        normalized.append(rel.casefold())
        oid = _as_str(raw_oid, f"spec.source_blob_oids[{rel!r}]")
        _require(_OID_RE.fullmatch(oid) is not None, f"{rel}: invalid Git blob OID {oid!r}")
        actual_oid = (
            _run_git(
                repo_root,
                ["rev-parse", "--verify", f"{source_commit}:{rel}"],
                f"source blob {rel}",
            )
            .decode("ascii", errors="strict")
            .strip()
        )
        _require(actual_oid == oid, f"{rel}: Git blob OID {actual_oid}, expected {oid}")
        blobs[rel] = _run_git(repo_root, ["show", f"{source_commit}:{rel}"], f"source blob {rel}")
    _unique(normalized, "spec.source_blob_oids normalized paths")
    return source_commit, blobs


def _csv_matrix(data: bytes, context: str, *, comments: bool) -> tuple[list[str], list[list[str]]]:
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        _fail(f"{context}: invalid UTF-8 CSV: {exc}")
    selected = [
        line
        for line in lines
        if line.strip() and not (comments and line.lstrip().startswith("#"))
    ]
    _require(selected, f"{context}: empty CSV")
    try:
        matrix = list(csv.reader(selected))
    except csv.Error as exc:
        _fail(f"{context}: invalid CSV: {exc}")
    header = matrix[0]
    _require(header and all(header), f"{context}: empty CSV header field")
    _unique(header, f"{context} header")
    width = len(header)
    for row_number, row in enumerate(matrix[1:], start=2):
        _require(
            len(row) == width,
            f"{context}: row {row_number} has {len(row)} fields, expected {width}",
        )
    return header, matrix[1:]


def _csv_dict_rows(path: Path, *, comments: bool = True) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    _require(path.is_file(), f"missing CSV file: {path}")
    try:
        header, rows = _csv_matrix(path.read_bytes(), str(path), comments=comments)
    except OSError as exc:
        _fail(f"{path}: could not read CSV: {exc}")
    return tuple(header), [dict(zip(header, row, strict=True)) for row in rows]


def _golden_metadata(data: bytes, context: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    header, rows = _csv_matrix(data, context, comments=True)
    required = {"label", "actionIndex"}
    _require(required.issubset(header), f"{context}: missing golden columns {sorted(required - set(header))}")
    label_col = header.index("label")
    index_col = header.index("actionIndex")
    entries: list[tuple[int, str]] = []
    for row_number, row in enumerate(rows, start=2):
        label = row[label_col]
        _require(label != "", f"{context}: row {row_number} has an empty label")
        try:
            index = int(row[index_col])
        except ValueError:
            _fail(f"{context}: row {row_number} has invalid actionIndex {row[index_col]!r}")
        entries.append((index, label))
    _require(entries, f"{context}: golden registry has no action rows")
    _unique([label for _, label in entries], f"{context} labels")
    _unique([index for index, _ in entries], f"{context} actionIndex values")
    entries.sort()
    indices = tuple(index for index, _ in entries)
    _require(
        indices == tuple(range(len(entries))),
        f"{context}: runtime action indices must be contiguous from zero, got {indices}",
    )
    return tuple(label for _, label in entries), indices


def _qtable_header(path: Path, context: str) -> tuple[str, ...]:
    _require(path.is_file(), f"{context}: missing Q-table {path}")
    try:
        header, _ = _csv_matrix(path.read_bytes(), str(path), comments=True)
    except OSError as exc:
        _fail(f"{path}: could not read Q-table header: {exc}")
    _require(header[0] == "StateIndex", f"{context}: first header must be 'StateIndex'")
    labels = tuple(header[1:])
    _require(labels, f"{context}: Q-table has no action labels")
    return labels


def _validate_spec_structure(
    spec: dict[str, Any],
) -> tuple[tuple[str, ...], dict[str, str], dict[int, dict[str, Any]]]:
    _require(
        spec.get("schema_version") == "phase2-qgap-retrospective-v1",
        "spec.schema_version: expected 'phase2-qgap-retrospective-v1'",
    )
    _require(
        spec.get("protocol_revision") == _PROTOCOL_REVISION,
        f"spec.protocol_revision: expected {_PROTOCOL_REVISION!r}",
    )
    join_fields = tuple(
        _as_str(item, "spec.join_key entry")
        for item in _as_list(spec.get("join_key"), "spec.join_key")
    )
    _require(join_fields == _REQUIRED_JOIN_FIELDS, f"spec.join_key must equal {_REQUIRED_JOIN_FIELDS}")

    raw_markers = [
        _as_str(value, "spec.forbidden_input_markers entry").casefold()
        for value in _as_list(spec.get("forbidden_input_markers"), "spec.forbidden_input_markers")
    ]
    _unique(raw_markers, "spec.forbidden_input_markers")
    _require(raw_markers, "spec.forbidden_input_markers must not be empty")

    arms = _as_mapping(spec.get("arms"), "spec.arms")
    _require(set(arms) == {"KG", "TR"}, "spec.arms must contain exactly KG and TR")
    seen_modes: list[str] = []
    seen_booleans: list[str] = []
    for arm in ("KG", "TR"):
        arm_spec = _as_mapping(arms[arm], f"spec.arms.{arm}")
        seen_modes.append(_as_str(arm_spec.get("manifest_mode"), f"spec.arms.{arm}.manifest_mode"))
        boolean = _as_str(
            arm_spec.get("filename_boolean"), f"spec.arms.{arm}.filename_boolean"
        )
        _require(boolean in {"true", "false"}, f"spec.arms.{arm}: invalid filename_boolean")
        seen_booleans.append(boolean)
    _unique(seen_modes, "spec arm manifest modes")
    _unique(seen_booleans, "spec arm filename booleans")

    artifacts = _as_list(spec.get("source_artifacts"), "spec.source_artifacts")
    _require(artifacts, "spec.source_artifacts must not be empty")
    by_run: dict[int, dict[str, Any]] = {}
    dispatches: list[str] = []
    artifact_ids: list[int] = []
    for index, raw in enumerate(artifacts):
        item = _as_mapping(raw, f"spec.source_artifacts[{index}]")
        run_id = _as_int(item.get("run_id"), f"spec.source_artifacts[{index}].run_id", minimum=1)
        _require(run_id not in by_run, f"spec.source_artifacts: duplicate run_id {run_id}")
        by_run[run_id] = item
        dispatches.append(_as_str(item.get("dispatch"), f"source artifact {run_id} dispatch"))
        artifact_ids.append(
            _as_int(item.get("artifact_id"), f"source artifact {run_id} artifact_id", minimum=1)
        )
        seeds = [
            _as_int(value, f"source artifact {run_id} seed", minimum=1)
            for value in _as_list(item.get("seeds"), f"source artifact {run_id} seeds")
        ]
        _require(seeds, f"source artifact {run_id}: empty seeds")
        _unique(seeds, f"source artifact {run_id} seeds")
        digest = _as_str(item.get("sha256"), f"source artifact {run_id} sha256")
        _require(_SHA256_RE.fullmatch(digest) is not None, f"source artifact {run_id}: invalid sha256")
        _as_int(item.get("size_bytes"), f"source artifact {run_id} size_bytes", minimum=1)
        _as_str(item.get("created_at_utc"), f"source artifact {run_id} created_at_utc")
        _as_str(item.get("expires_at_utc"), f"source artifact {run_id} expires_at_utc")
    _unique(dispatches, "spec source artifact dispatches")
    _unique(artifact_ids, "spec source artifact IDs")
    return tuple(raw_markers), {arm: seen_booleans[i] for i, arm in enumerate(("KG", "TR"))}, by_run


def _parent_metadata(
    spec: dict[str, Any],
    blobs: dict[str, bytes],
) -> dict[str, _ParentMetadata]:
    state_contract = _as_mapping(spec.get("state_contract"), "spec.state_contract")
    parents = _as_mapping(state_contract.get("parents"), "spec.state_contract.parents")
    result: dict[str, _ParentMetadata] = {}
    for parent, raw_parent in parents.items():
        parent_spec = _as_mapping(raw_parent, f"spec.state_contract.parents.{parent}")
        scenario_file = _normal_relative_path(
            parent_spec.get("scenario_file"), f"parent {parent} scenario_file"
        )
        _require(
            scenario_file in blobs,
            f"parent {parent}: scenario_file {scenario_file!r} is not source-blob pinned",
        )
        rows_raw = _load_json_bytes(blobs[scenario_file], f"{scenario_file}@source_commit")
        rows = _as_list(rows_raw, f"{scenario_file}@source_commit")
        ids: list[int] = []
        frozen_rows: list[Mapping[str, object]] = []
        for row_index, raw_row in enumerate(rows):
            row = _as_mapping(raw_row, f"{scenario_file} row {row_index + 1}")
            scenario_id = _as_int(row.get("id"), f"{scenario_file} row {row_index + 1} id")
            ids.append(scenario_id)
            frozen_rows.append(_freeze(row))  # type: ignore[arg-type]
        _require(ids, f"{scenario_file}: no scenario IDs")
        _unique(ids, f"{scenario_file} scenario IDs")
        declared_ids = tuple(
            _as_int(value, f"parent {parent} ordered_scenario_ids")
            for value in _as_list(
                parent_spec.get("ordered_scenario_ids"),
                f"parent {parent} ordered_scenario_ids",
            )
        )
        _require(tuple(ids) == declared_ids, f"parent {parent}: scenario ID order differs from source blob")
        schedule = _sha256_bytes(",".join(str(value) for value in ids).encode("utf-8"))
        declared_schedule = _as_str(
            parent_spec.get("scenario_schedule_sha256"),
            f"parent {parent} scenario_schedule_sha256",
        )
        _require(schedule == declared_schedule, f"parent {parent}: scenario schedule digest mismatch")

        golden = _normal_relative_path(
            parent_spec.get("golden_registry"), f"parent {parent} golden_registry"
        )
        _require(golden in blobs, f"parent {parent}: golden registry {golden!r} is not source-blob pinned")
        golden_labels, runtime_indices = _golden_metadata(
            blobs[golden], f"{golden}@source_commit"
        )
        declared_labels = tuple(
            _as_str(value, f"parent {parent} action label")
            for value in _as_list(parent_spec.get("action_labels"), f"parent {parent} action_labels")
        )
        _unique(list(declared_labels), f"parent {parent} action_labels")
        _require(
            golden_labels == declared_labels,
            f"parent {parent}: action golden order/labels differ from frozen action_labels",
        )
        state_labels = [
            _as_str(value, f"parent {parent} state label")
            for value in _as_list(parent_spec.get("state_labels"), f"parent {parent} state_labels")
        ]
        zones = sorted(
            int(match.group(1))
            for label in state_labels
            if (match := re.fullmatch(r"Z([1-9][0-9]*)Level", label))
        )
        _require(zones and zones == list(range(1, max(zones) + 1)), f"parent {parent}: invalid zone levels")
        result[parent] = _ParentMetadata(
            scenario_file=scenario_file,
            ordered_ids=declared_ids,
            scenario_rows=tuple(frozen_rows),
            schedule_sha256=schedule,
            action_labels=declared_labels,
            runtime_indices=runtime_indices,
            zone_count=max(zones),
        )
    return result


def _validate_dispatch_and_config(
    spec: dict[str, Any],
    blobs: dict[str, bytes],
    source_artifacts: dict[int, dict[str, Any]],
) -> tuple[dict[int, tuple[str, ...]], dict[str, str]]:
    config_path = "config/run_config.json"
    _require(config_path in blobs, f"{config_path}: required source blob is missing")
    config = _as_mapping(_load_json_bytes(blobs[config_path], f"{config_path}@source_commit"), config_path)
    phase2 = _as_mapping(config.get("phase2"), f"{config_path}.phase2")
    scenario_map = _as_mapping(phase2.get("train_scenarios_map"), "run_config phase2.train_scenarios_map")
    parent_map = _as_mapping(phase2.get("parent_profile"), "run_config phase2.parent_profile")
    flow_map = _as_mapping(phase2.get("simulator_flow_map"), "run_config phase2.simulator_flow_map")

    cells = _as_mapping(spec.get("cells"), "spec.cells")
    dispatch_groups = _as_mapping(spec.get("dispatch_groups"), "spec.dispatch_groups")
    group_profiles: dict[str, tuple[str, ...]] = {}
    run_to_group: dict[int, str] = {}
    all_profiles: list[str] = []
    for group_name, raw_group in dispatch_groups.items():
        group = _as_mapping(raw_group, f"spec.dispatch_groups.{group_name}")
        profiles = tuple(
            _as_str(value, f"dispatch group {group_name} profile")
            for value in _as_list(group.get("profiles"), f"dispatch group {group_name} profiles")
        )
        _unique(list(profiles), f"dispatch group {group_name} profiles")
        group_profiles[group_name] = profiles
        all_profiles.extend(profiles)
        runs = [
            _as_int(value, f"dispatch group {group_name} run", minimum=1)
            for value in _as_list(group.get("runs"), f"dispatch group {group_name} runs")
        ]
        _unique(runs, f"dispatch group {group_name} runs")
        for run_id in runs:
            _require(run_id in source_artifacts, f"dispatch group {group_name}: unknown run {run_id}")
            _require(run_id not in run_to_group, f"run {run_id}: duplicate dispatch-group ownership")
            run_to_group[run_id] = group_name
    _unique(all_profiles, "dispatch profile ownership")
    _require(set(all_profiles) == set(cells), "dispatch profiles must equal the frozen cell set")
    _require(set(run_to_group) == set(source_artifacts), "every source run must have one dispatch-group owner")

    parent_for_cell: dict[str, str] = {}
    parents = _as_mapping(
        _as_mapping(spec.get("state_contract"), "spec.state_contract").get("parents"),
        "spec.state_contract.parents",
    )
    for profile, raw_cell in cells.items():
        cell = _as_mapping(raw_cell, f"spec.cells.{profile}")
        group = _as_str(cell.get("dispatch_group"), f"cell {profile} dispatch_group")
        _require(profile in group_profiles.get(group, ()), f"cell {profile}: dispatch ownership mismatch")
        parent = _as_str(cell.get("parent_profile"), f"cell {profile} parent_profile")
        _require(parent in parents, f"cell {profile}: unknown parent profile {parent!r}")
        parent_for_cell[profile] = parent
        _require(parent_map.get(profile) == parent, f"cell {profile}: run_config parent_profile mismatch")
        expected_scenario = _as_str(
            _as_mapping(parents[parent], f"parent {parent}").get("scenario_file"),
            f"parent {parent} scenario_file",
        )
        _require(
            scenario_map.get(profile) == expected_scenario,
            f"cell {profile}: run_config training-scenario ownership mismatch",
        )
        simulator_flow = _normal_relative_path(
            cell.get("simulator_flow"), f"cell {profile} simulator_flow"
        )
        _require(simulator_flow in blobs, f"cell {profile}: simulator flow is not source-blob pinned")
        configured_flow = flow_map.get(profile)
        _require(
            isinstance(configured_flow, str)
            and PurePosixPath(configured_flow).name == PurePosixPath(simulator_flow).name,
            f"cell {profile}: run_config simulator-flow ownership mismatch",
        )

    run_profiles: dict[int, tuple[str, ...]] = {}
    for run_id, artifact in source_artifacts.items():
        dispatch = _as_str(artifact.get("dispatch"), f"source artifact {run_id} dispatch")
        group = run_to_group[run_id]
        _require(
            dispatch.startswith(group),
            f"source artifact {run_id}: dispatch {dispatch!r} does not belong to group {group!r}",
        )
        run_profiles[run_id] = group_profiles[group]
    return run_profiles, parent_for_cell


def _tree_files(root: Path) -> tuple[Path, ...]:
    try:
        return tuple(
            sorted(
                (path.resolve() for path in root.rglob("*") if path.is_file()),
                key=lambda path: path.relative_to(root).as_posix(),
            )
        )
    except OSError as exc:
        _fail(f"{root}: could not enumerate extracted files: {exc}")


def _inventory_rows(path: Path) -> list[tuple[str, str]]:
    header, rows = _csv_dict_rows(path, comments=False)
    _require(set(header) == {"file", "sha256"}, f"{path}: inventory header must be file,sha256")
    result: list[tuple[str, str]] = []
    normalized: list[str] = []
    for index, row in enumerate(rows, start=2):
        rel = _normal_relative_path(row["file"], f"{path} row {index} file")
        digest = row["sha256"]
        _require(_SHA256_RE.fullmatch(digest) is not None, f"{path} row {index}: invalid SHA-256")
        result.append((rel, digest))
        normalized.append(rel.casefold())
    _unique(normalized, f"{path} inventory paths")
    return result


def _validate_extraction_and_zip(
    *,
    repo_root: Path,
    extraction_root: Path,
    artifact: dict[str, Any],
    source_entry: dict[str, Any],
    zip_root: Path | None,
    require_zips: bool,
    markers: tuple[str, ...],
    hash_cache: dict[Path, str],
) -> None:
    files = _tree_files(extraction_root)
    relative = tuple(path.relative_to(extraction_root).as_posix() for path in files)
    for rel in relative:
        _check_forbidden(rel, markers, f"source run {artifact['run_id']}")

    inventory = _as_mapping(source_entry.get("extraction_inventory"), "source extraction_inventory")
    expected_count = _as_int(inventory.get("extracted_file_count"), "extracted_file_count", minimum=0)
    expected_bytes = _as_int(inventory.get("extracted_bytes"), "extracted_bytes", minimum=0)
    _require(len(files) == expected_count, f"{extraction_root}: extracted file-count mismatch")
    actual_bytes = sum(path.stat().st_size for path in files)
    _require(actual_bytes == expected_bytes, f"{extraction_root}: extracted byte-count mismatch")
    _require(
        _as_int(inventory.get("file_count"), "zip file_count", minimum=0) == expected_count,
        f"{extraction_root}: ZIP/extracted file counts differ",
    )
    _require(
        _as_int(inventory.get("uncompressed_bytes"), "zip uncompressed_bytes", minimum=0)
        == expected_bytes,
        f"{extraction_root}: ZIP/extracted byte totals differ",
    )

    historical = repo_root / "phase2_v2_corrected" / f"run_{artifact['run_id']}" / "SHA256SUMS.csv"
    _require(historical.is_file(), f"missing historical SHA-256 inventory: {historical}")
    historical_rows = _inventory_rows(historical)
    _require(
        {rel for rel, _ in historical_rows} == set(relative),
        f"{historical}: inventory paths do not exactly match the extracted tree",
    )
    for rel, expected_digest in historical_rows:
        actual_digest = _sha256_file(extraction_root / PurePosixPath(rel), hash_cache)
        _require(
            actual_digest == expected_digest,
            f"{extraction_root / PurePosixPath(rel)}: historical SHA-256 mismatch",
        )

    if not require_zips:
        return
    _require(zip_root is not None, "zip_root is required when require_zips=True")
    zip_basename = _as_str(source_entry.get("zip_basename"), "source artifact zip_basename")
    _require(Path(zip_basename).name == zip_basename, f"invalid zip_basename {zip_basename!r}")
    _check_forbidden(zip_basename, markers, "source artifact ZIP")
    zip_path = zip_root.resolve() / zip_basename
    _require(zip_path.is_file(), f"missing immutable source ZIP: {zip_path}")
    expected_zip_size = _as_int(source_entry.get("zip_size_bytes"), "source zip_size_bytes", minimum=1)
    _require(zip_path.stat().st_size == expected_zip_size, f"{zip_path}: ZIP size mismatch")
    zip_digest = _sha256_file(zip_path, hash_cache)
    for field in ("github_digest_sha256", "local_zip_sha256"):
        expected = _as_str(source_entry.get(field), f"source artifact {field}")
        _require(zip_digest == expected, f"{zip_path}: {field} mismatch")
    _require(zip_digest == artifact["sha256"], f"{zip_path}: frozen artifact SHA-256 mismatch")

    try:
        with ZipFile(zip_path) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
    except (OSError, BadZipFile) as exc:
        _fail(f"{zip_path}: invalid ZIP: {exc}")
    zip_paths: list[str] = []
    entry_rows: list[tuple[str, int, int]] = []
    zip_bytes = 0
    for info in infos:
        rel = _normal_relative_path(info.filename, f"{zip_path} entry")
        _check_forbidden(rel, markers, f"{zip_path} entry")
        zip_paths.append(rel)
        zip_bytes += info.file_size
        entry_rows.append((rel, info.file_size, info.compress_size))
    _unique([value.casefold() for value in zip_paths], f"{zip_path} entry paths")
    expected_entry_digest = _as_str(
        inventory.get("zip_entry_inventory_sha256"), "zip_entry_inventory_sha256"
    )

    def digest_for(rows: list[tuple[str, int, int]]) -> str:
        return _sha256_bytes(
            "\n".join(f"{name},{size},{compressed}" for name, size, compressed in rows)
            .encode("utf-8")
        )

    # The rescue manifest was emitted by PowerShell Sort-Object, whose path
    # collation follows the host culture.  Accept that exact collation and
    # ordinal path collation; the ZIP SHA, entry set, sizes, and historical
    # per-file SHA inventory remain independently exact.
    inventory_digests = {digest_for(sorted(entry_rows, key=lambda row: row[0]))}
    previous_collation = locale.setlocale(locale.LC_COLLATE)
    try:
        locale.setlocale(locale.LC_COLLATE, "")
        inventory_digests.add(
            digest_for(sorted(entry_rows, key=lambda row: locale.strxfrm(row[0])))
        )
    except locale.Error:
        pass
    finally:
        locale.setlocale(locale.LC_COLLATE, previous_collation)
    _require(
        expected_entry_digest in inventory_digests,
        f"{zip_path}: ZIP entry-inventory digest mismatch",
    )
    _require(len(infos) == expected_count, f"{zip_path}: ZIP entry count mismatch")
    _require(zip_bytes == expected_bytes, f"{zip_path}: ZIP uncompressed byte total mismatch")
    _require(
        tuple(sorted(zip_paths)) == relative,
        f"{zip_path}: ZIP entries do not exactly match the extracted tree",
    )


def _validate_source_manifest(
    *,
    repo_root: Path,
    source_root: Path,
    source_manifest: dict[str, Any],
    source_commit: str,
    source_artifacts: dict[int, dict[str, Any]],
    zip_name_template: str,
    extraction_template: str,
    zip_root: Path | None,
    require_zips: bool,
    markers: tuple[str, ...],
    hash_cache: dict[Path, str],
) -> dict[int, Path]:
    _require(
        source_manifest.get("schema_version") == "phase2-qgap-source-manifest-v1",
        "source manifest schema_version mismatch",
    )
    _require(source_manifest.get("source_commit") == source_commit, "source manifest commit mismatch")
    raw_entries = _as_list(source_manifest.get("artifacts"), "source manifest artifacts")
    entries: dict[int, dict[str, Any]] = {}
    for index, raw in enumerate(raw_entries):
        entry = _as_mapping(raw, f"source manifest artifact {index}")
        run_id = _as_int(entry.get("run_id"), f"source manifest artifact {index} run_id", minimum=1)
        _require(run_id not in entries, f"source manifest: duplicate run_id {run_id}")
        entries[run_id] = entry
    _require(set(entries) == set(source_artifacts), "source manifest runs differ from frozen source artifacts")

    extraction_roots: dict[int, Path] = {}
    for run_id, artifact in source_artifacts.items():
        entry = entries[run_id]
        for field in (
            "dispatch",
            "artifact_id",
            "artifact_name",
            "created_at_utc",
            "expires_at_utc",
        ):
            _require(
                entry.get(field) == artifact.get(field),
                f"source manifest run {run_id}: {field} differs from frozen spec",
            )
        _require(entry.get("head_sha") == source_commit, f"source manifest run {run_id}: head_sha mismatch")
        frozen_digest = _as_str(artifact.get("sha256"), f"source artifact {run_id} sha256")
        _require(
            entry.get("github_digest_sha256") == frozen_digest
            and entry.get("local_zip_sha256") == frozen_digest,
            f"source manifest run {run_id}: ZIP digests differ from frozen spec",
        )
        _require(
            entry.get("zip_size_bytes") == artifact.get("size_bytes"),
            f"source manifest run {run_id}: ZIP size differs from frozen spec",
        )
        try:
            expected_zip_basename = zip_name_template.format(
                run_id=run_id,
                artifact_id=artifact["artifact_id"],
            )
            expected_extraction_rel = extraction_template.format(
                run_id=run_id,
                artifact_id=artifact["artifact_id"],
                artifact_name=artifact["artifact_name"],
            )
        except (KeyError, ValueError) as exc:
            _fail(f"spec.artifact_rescue template is invalid: {exc}")
        _require(
            entry.get("zip_basename") == expected_zip_basename,
            f"source manifest run {run_id}: ZIP basename differs from frozen template",
        )
        extraction_rel = _normal_relative_path(
            entry.get("extraction_root"), f"source manifest run {run_id} extraction_root"
        )
        _require(
            extraction_rel == expected_extraction_rel,
            f"source manifest run {run_id}: extraction root differs from frozen template",
        )
        _check_forbidden(extraction_rel, markers, f"source manifest run {run_id}")
        extraction = (repo_root / PurePosixPath(extraction_rel)).resolve()
        expected = (source_root / f"run_{run_id}" / _as_str(artifact.get("artifact_name"), "artifact_name")).resolve()
        _require(extraction == expected, f"source manifest run {run_id}: extraction-root ownership mismatch")
        _require(_is_within(extraction, source_root), f"source manifest run {run_id}: extraction escapes source_root")
        _require(extraction.is_dir(), f"missing extraction root: {extraction}")
        extraction_roots[run_id] = extraction
        _validate_extraction_and_zip(
            repo_root=repo_root,
            extraction_root=extraction,
            artifact=artifact,
            source_entry=entry,
            zip_root=zip_root,
            require_zips=require_zips,
            markers=markers,
            hash_cache=hash_cache,
        )

    validation = source_manifest.get("validation")
    if validation is not None:
        validation_map = _as_mapping(validation, "source manifest validation")
        for field in (
            "parent_file_set_hash_mismatches",
            "missing_or_ambiguous_manifest_files",
            "missing_recovery_csvs",
        ):
            if field in validation_map:
                _require(validation_map[field] == 0, f"source manifest validation.{field} must be zero")
    return extraction_roots


def _validate_workflow_inputs(
    extraction: Path,
    artifact: dict[str, Any],
    source_commit: str,
    profiles: tuple[str, ...],
) -> None:
    path = extraction / "analysis" / "out" / "workflow_inputs.json"
    workflow = _as_mapping(_load_json(path), str(path))
    run_id = artifact["run_id"]
    _require(workflow.get("run_id") == run_id, f"{path}: run_id ownership mismatch")
    _require(workflow.get("head_sha") == source_commit, f"{path}: head_sha mismatch")
    seeds = _as_list(workflow.get("seeds"), f"{path} seeds")
    expected_seeds = _as_list(artifact.get("seeds"), f"source artifact {run_id} seeds")
    _require(seeds == expected_seeds, f"{path}: seed ownership/order mismatch")
    _unique(seeds, f"{path} seeds")
    workflow_profiles = [
        _as_str(value, f"{path} profile")
        for value in _as_list(workflow.get("profiles"), f"{path} profiles")
    ]
    _unique(workflow_profiles, f"{path} profiles")
    missing = set(profiles) - set(workflow_profiles)
    _require(not missing, f"{path}: missing frozen dispatch profiles {sorted(missing)}")
    _require(workflow.get("run_mode") == "phase1_v2_kg_only", f"{path}: unexpected run_mode")


def _resolve_parent_files(
    *,
    extraction: Path,
    manifest: dict[str, Any],
    parent: str,
    boolean: str,
    seed: int,
    metadata: _ParentMetadata,
    qtable_template: str,
    markers: tuple[str, ...],
    hash_cache: dict[Path, str],
) -> tuple[tuple[Path, ...], Path, tuple[Path, ...], str]:
    raw_names = _as_list(manifest.get("parent_qtable_files"), "ADAPT_OK.parent_qtable_files")
    names: list[str] = []
    for index, raw in enumerate(raw_names):
        name = _as_str(raw, f"ADAPT_OK.parent_qtable_files[{index}]")
        _require(Path(name).name == name and "/" not in name and "\\" not in name, f"invalid parent basename {name!r}")
        _check_forbidden(name, markers, "ADAPT_OK.parent_qtable_files")
        names.append(name)
    _require(names, "ADAPT_OK.parent_qtable_files must not be empty")
    _unique([name.casefold() for name in names], "ADAPT_OK.parent_qtable_files")

    clean_root = extraction / "_artifacts" / "clean"
    _require(clean_root.is_dir(), f"missing clean-artifact root: {clean_root}")
    candidates: dict[str, list[Path]] = {}
    for directory in clean_root.iterdir():
        if not directory.is_dir():
            continue
        match = _CLEAN_DIR_RE.fullmatch(directory.name)
        if not match:
            continue
        if match.group("boolean") != boolean or int(match.group("seed")) != seed:
            continue
        for child in directory.iterdir():
            if child.is_file():
                candidates.setdefault(child.name, []).append(child.resolve())

    resolved: list[Path] = []
    for name in names:
        matches = candidates.get(name, [])
        _require(matches, f"missing direct parent basename {name!r} for seed {seed}/{boolean}")
        _require(
            len(matches) == 1,
            f"ambiguous direct parent basename {name!r} for seed {seed}/{boolean}: {matches}",
        )
        resolved.append(matches[0])

    digest_lines = [
        f"{name}:{_sha256_file(path, hash_cache)}"
        for name, path in zip(names, resolved, strict=True)
    ]
    actual_digest = _sha256_bytes("\n".join(digest_lines).encode("utf-8"))
    declared_digest = _as_str(manifest.get("parent_qtable_sha256"), "ADAPT_OK.parent_qtable_sha256")
    _require(_SHA256_RE.fullmatch(declared_digest) is not None, "invalid ADAPT_OK.parent_qtable_sha256")
    _require(
        actual_digest == declared_digest,
        "ADAPT_OK.parent_qtable_sha256 does not match the exact manifest-ordered parent file set",
    )

    try:
        combined_name = qtable_template.format(
            filename_boolean=boolean, parent_profile=parent
        )
    except (KeyError, ValueError) as exc:
        _fail(f"spec.qtable_contract.combined_filename_template is invalid: {exc}")
    logical_names = {
        combined_name,
        f"qtable_final_stereotypes_{boolean}_{parent}_trust.csv",
        f"qtable_final_stereotypes_{boolean}_{parent}_visits.csv",
        *(
            f"qtable_final_stereotypes_{boolean}_{parent}_zone{zone}.csv"
            for zone in range(1, metadata.zone_count + 1)
        ),
    }
    for name in logical_names:
        _require(name in names, f"ADAPT_OK parent set is missing required sidecar {name!r}")

    combined = resolved[names.index(combined_name)]
    expected_dir = f"clean-{parent}-stereo-{boolean}-seed-{seed}"
    _require(combined.parent.name == expected_dir, f"combined Q-table is not in {expected_dir}")
    zone_paths = tuple(
        resolved[names.index(f"qtable_final_stereotypes_{boolean}_{parent}_zone{zone}.csv")]
        for zone in range(1, metadata.zone_count + 1)
    )
    _require(
        _qtable_header(combined, "combined Q-table") == metadata.action_labels,
        f"{combined}: action header differs from registered golden/runtime order",
    )
    for zone_path in zone_paths:
        _require(
            _qtable_header(zone_path, "zone Q-table") == metadata.action_labels,
            f"{zone_path}: action header differs from registered golden/runtime order",
        )
    return tuple(resolved), combined, zone_paths, declared_digest


def _recovery_row(path: Path, detector: str, protocol: str) -> tuple[Mapping[str, str], int, int, int]:
    header, rows = _csv_dict_rows(path, comments=True)
    required = {
        "DetectEpisode",
        "ReconvergeEpisode",
        "RecoveryEpisodes",
        "BlacklistEvents",
        "DetectorVersion",
        "ProtocolVersion",
    }
    _require(required.issubset(header), f"{path}: missing recovery columns {sorted(required - set(header))}")
    _require(
        len(rows) == 1,
        f"{path}: exactly one non-comment recovery data row is required, found {len(rows)}",
    )
    row = rows[0]
    _require(row["DetectorVersion"] == detector, f"{path}: DetectorVersion mismatch")
    _require(row["ProtocolVersion"] == protocol, f"{path}: ProtocolVersion mismatch")

    def parse(field: str) -> int:
        try:
            return int(row[field])
        except ValueError:
            _fail(f"{path}: {field} is not an integer: {row[field]!r}")

    frozen = MappingProxyType(dict(row))
    return frozen, parse("DetectEpisode"), parse("ReconvergeEpisode"), parse("RecoveryEpisodes")


def _build_record(
    *,
    run_id: int,
    seed: int,
    arm: str,
    profile: str,
    parent: str,
    extraction: Path,
    arm_spec: dict[str, Any],
    metadata: _ParentMetadata,
    spec: dict[str, Any],
    markers: tuple[str, ...],
    hash_cache: dict[Path, str],
) -> InputRecord:
    boolean = _as_str(arm_spec.get("filename_boolean"), f"arm {arm} filename_boolean")
    mode = _as_str(arm_spec.get("manifest_mode"), f"arm {arm} manifest_mode")
    seed_root = extraction / "recovery_root" / f"seed{seed}"
    _require(seed_root.is_dir(), f"missing seed root: {seed_root}")
    manifest_path = (
        seed_root / f"ADAPT_OK_stereotypes_{boolean}_{profile}.json"
    ).resolve()
    recovery_path = (
        seed_root / f"recovery_stereotypes_{boolean}_{profile}.csv"
    ).resolve()
    manifest = _as_mapping(_load_json(manifest_path), str(manifest_path))

    outcome = _as_mapping(spec.get("outcome_contract"), "spec.outcome_contract")
    detector = _as_str(outcome.get("detector_version"), "spec.outcome_contract.detector_version")
    protocol = _as_str(outcome.get("protocol_version"), "spec.outcome_contract.protocol_version")
    expected_fields: tuple[tuple[str, object], ...] = (
        ("status", "ok"),
        ("protocol_version", protocol),
        ("detector_version", detector),
        ("metric_schema", "phase2-recovery-v2"),
        ("settled_start_state", True),
        ("scenario_fallback_count", 0),
        ("profile", profile),
        ("parent_profile", parent),
        ("mode", mode),
        ("run_seed", seed),
        ("train_scenarios_file", metadata.scenario_file),
        ("scenario_schedule_sha256", metadata.schedule_sha256),
    )
    for field, expected in expected_fields:
        _require(
            manifest.get(field) == expected,
            f"{manifest_path}: {field}={manifest.get(field)!r}, expected {expected!r}",
        )
    ordered = tuple(
        _as_int(value, f"{manifest_path} ordered_scenario_ids")
        for value in _as_list(manifest.get("ordered_scenario_ids"), f"{manifest_path} ordered_scenario_ids")
    )
    _require(ordered == metadata.ordered_ids, f"{manifest_path}: ordered scenario rows mismatch")
    adapt_episodes = _as_int(
        manifest.get("adapt_episodes_effective"),
        f"{manifest_path} adapt_episodes_effective",
        minimum=0,
    )

    qtable_contract = _as_mapping(spec.get("qtable_contract"), "spec.qtable_contract")
    qtable_template = _as_str(
        qtable_contract.get("combined_filename_template"),
        "spec.qtable_contract.combined_filename_template",
    )
    parent_paths, combined, zone_paths, parent_digest = _resolve_parent_files(
        extraction=extraction,
        manifest=manifest,
        parent=parent,
        boolean=boolean,
        seed=seed,
        metadata=metadata,
        qtable_template=qtable_template,
        markers=markers,
        hash_cache=hash_cache,
    )
    recovery, detect, reconverge, recovery_episodes = _recovery_row(
        recovery_path, detector, protocol
    )
    join_key = (
        run_id,
        seed,
        arm,
        profile,
        parent,
        parent_digest,
        metadata.schedule_sha256,
    )
    return InputRecord(
        run_id=run_id,
        seed=seed,
        arm=arm,
        filename_boolean=boolean,
        mode=mode,
        faulty_profile=profile,
        parent_profile=parent,
        manifest=_freeze(manifest),  # type: ignore[arg-type]
        manifest_path=manifest_path,
        recovery_row=recovery,
        recovery_path=recovery_path,
        detect_episode=detect,
        reconverge_episode=reconverge,
        recovery_episodes=recovery_episodes,
        detector_version=detector,
        protocol_version=protocol,
        adapt_episodes_effective=adapt_episodes,
        ordered_scenario_ids=metadata.ordered_ids,
        scenario_rows=metadata.scenario_rows,
        scenario_schedule_sha256=metadata.schedule_sha256,
        combined_qtable_path=combined,
        parent_qtable_paths=parent_paths,
        zone_qtable_paths=zone_paths,
        action_labels=metadata.action_labels,
        runtime_action_indices=metadata.runtime_indices,
        parent_qtable_sha256=parent_digest,
        join_key=join_key,
    )


def validate_inputs(
    repo_root: Path,
    source_root: Path,
    spec_path: Path,
    source_manifest_path: Path,
    zip_root: Path | None = None,
    require_zips: bool = True,
) -> ValidationResult:
    """Validate all frozen inputs and return immutable, uniquely joined records.

    No partial result is returned.  The first contract failure raises
    :class:`InputValidationError`.
    """

    repo_root = repo_root.resolve()
    source_root = source_root.resolve()
    spec_path = spec_path.resolve()
    source_manifest_path = source_manifest_path.resolve()
    zip_root = zip_root.resolve() if zip_root is not None else None
    _require(repo_root.is_dir(), f"missing repository root: {repo_root}")
    _require(source_root.is_dir(), f"missing source root: {source_root}")
    _require(_is_within(source_root, repo_root), f"source_root must be inside repo_root: {source_root}")

    spec = _as_mapping(_load_json(spec_path), str(spec_path))
    markers, _, source_artifacts = _validate_spec_structure(spec)
    for path in (spec_path, source_manifest_path):
        _check_forbidden(path.name, markers, "input control path")
    source_commit, blobs = _validate_source_blobs(repo_root, spec, markers)
    parent_metadata = _parent_metadata(spec, blobs)
    run_profiles, parent_for_cell = _validate_dispatch_and_config(spec, blobs, source_artifacts)

    source_manifest = _as_mapping(_load_json(source_manifest_path), str(source_manifest_path))
    rescue = _as_mapping(spec.get("artifact_rescue"), "spec.artifact_rescue")
    zip_name_template = _as_str(
        rescue.get("local_zip_name_template"),
        "spec.artifact_rescue.local_zip_name_template",
    )
    extraction_template = _as_str(
        rescue.get("extraction_template"),
        "spec.artifact_rescue.extraction_template",
    )
    hash_cache: dict[Path, str] = {}
    extraction_roots = _validate_source_manifest(
        repo_root=repo_root,
        source_root=source_root,
        source_manifest=source_manifest,
        source_commit=source_commit,
        source_artifacts=source_artifacts,
        zip_name_template=zip_name_template,
        extraction_template=extraction_template,
        zip_root=zip_root,
        require_zips=require_zips,
        markers=markers,
        hash_cache=hash_cache,
    )

    arms = _as_mapping(spec.get("arms"), "spec.arms")
    records: list[InputRecord] = []
    semantic_keys: set[tuple[int, int, str, str]] = set()
    joins: set[tuple[int, int, str, str, str, str, str]] = set()
    for run_id in sorted(source_artifacts):
        artifact = source_artifacts[run_id]
        profiles = run_profiles[run_id]
        extraction = extraction_roots[run_id]
        _validate_workflow_inputs(extraction, artifact, source_commit, profiles)
        seeds = [
            _as_int(value, f"source artifact {run_id} seed", minimum=1)
            for value in _as_list(artifact.get("seeds"), f"source artifact {run_id} seeds")
        ]
        for seed in seeds:
            for arm in ("KG", "TR"):
                arm_spec = _as_mapping(arms[arm], f"spec.arms.{arm}")
                for profile in profiles:
                    semantic = (run_id, seed, arm, profile)
                    _require(semantic not in semantic_keys, f"duplicate semantic input join: {semantic}")
                    semantic_keys.add(semantic)
                    parent = parent_for_cell[profile]
                    record = _build_record(
                        run_id=run_id,
                        seed=seed,
                        arm=arm,
                        profile=profile,
                        parent=parent,
                        extraction=extraction,
                        arm_spec=arm_spec,
                        metadata=parent_metadata[parent],
                        spec=spec,
                        markers=markers,
                        hash_cache=hash_cache,
                    )
                    _require(record.join_key not in joins, f"duplicate immutable join_key: {record.join_key}")
                    joins.add(record.join_key)
                    records.append(record)

    expected_records = sum(
        len(_as_list(artifact.get("seeds"), f"source artifact {run_id} seeds"))
        * len(run_profiles[run_id])
        * 2
        for run_id, artifact in source_artifacts.items()
    )
    _require(len(records) == expected_records, "validated record cardinality mismatch")
    records.sort(
        key=lambda record: (
            record.run_id,
            record.seed,
            0 if record.arm == "KG" else 1,
            record.faulty_profile,
        )
    )
    return ValidationResult(records=tuple(records))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--zip-root", type=Path)
    parser.add_argument("--no-require-zips", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_inputs(
            args.repo_root,
            args.source_root,
            args.spec,
            args.source_manifest,
            zip_root=args.zip_root,
            require_zips=not args.no_require_zips,
        )
    except InputValidationError as exc:
        print(f"Phase-2b Q-gap input validation FAILED: {exc}")
        return 1
    print(f"Phase-2b Q-gap input validation passed ({len(result.records)} immutable joins).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
