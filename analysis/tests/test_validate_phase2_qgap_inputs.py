"""Synthetic fail-closed tests for Phase-2b Q-gap input discovery."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from analysis.validate_phase2_qgap_inputs import (
    InputValidationError,
    validate_inputs,
)


RUN_ID = 10101
ARTIFACT_ID = 20202
PROFILE = "fixture_f1dead"
PARENT = "fixture"
ACTIONS = ("SetLamp=OFF", "SetLamp=ON", "DO_NOTHING")
CREATED_AT = "2026-07-23T00:00:00Z"
EXPIRES_AT = "2026-10-21T00:00:00Z"
JOIN_FIELDS = [
    "run_id",
    "seed",
    "arm",
    "faulty_profile",
    "parent_profile",
    "parent_qtable_sha256",
    "scenario_schedule_sha256",
]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _runner_digest(root: Path, names: list[str]) -> str:
    lines = [f"{name}:{_sha256(root / name)}" for name in names]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _qtable_text(labels: tuple[str, ...] = ACTIONS) -> str:
    return "StateIndex," + ",".join(labels) + "\n0,0.00,0.00,0.00\n"


@dataclass
class SyntheticInputs:
    repo_root: Path
    source_root: Path
    extraction_root: Path
    spec_path: Path
    source_manifest_path: Path
    zip_root: Path

    def manifest_path(self, boolean: str) -> Path:
        return (
            self.extraction_root
            / "recovery_root"
            / "seed1"
            / f"ADAPT_OK_stereotypes_{boolean}_{PROFILE}.json"
        )

    def recovery_path(self, boolean: str) -> Path:
        return (
            self.extraction_root
            / "recovery_root"
            / "seed1"
            / f"recovery_stereotypes_{boolean}_{PROFILE}.csv"
        )

    def clean_root(self, boolean: str) -> Path:
        return (
            self.extraction_root
            / "_artifacts"
            / "clean"
            / f"clean-{PARENT}-stereo-{boolean}-seed-1"
        )

    def sync(self, *, update_parent_hashes: bool = False) -> None:
        if update_parent_hashes:
            for boolean in ("true", "false"):
                manifest_path = self.manifest_path(boolean)
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["parent_qtable_sha256"] = _runner_digest(
                    self.clean_root(boolean), manifest["parent_qtable_files"]
                )
                _write_json(manifest_path, manifest)

        files = sorted(
            (path for path in self.extraction_root.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(self.extraction_root).as_posix(),
        )
        inventory_path = (
            self.repo_root
            / "phase2_v2_corrected"
            / f"run_{RUN_ID}"
            / "SHA256SUMS.csv"
        )
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        with inventory_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("file", "sha256"))
            for path in files:
                writer.writerow(
                    (path.relative_to(self.extraction_root).as_posix(), _sha256(path))
                )

        zip_name = f"phase2-consolidated_run_{RUN_ID}_artifact_{ARTIFACT_ID}.zip"
        zip_path = self.zip_root / zip_name
        self.zip_root.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(self.extraction_root).as_posix())
        with ZipFile(zip_path) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            lines = sorted(
                f"{info.filename},{info.file_size},{info.compress_size}" for info in infos
            )
            entry_digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

        zip_digest = _sha256(zip_path)
        zip_size = zip_path.stat().st_size
        extracted_bytes = sum(path.stat().st_size for path in files)

        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        artifact = spec["source_artifacts"][0]
        artifact["sha256"] = zip_digest
        artifact["size_bytes"] = zip_size
        _write_json(self.spec_path, spec)

        manifest = json.loads(self.source_manifest_path.read_text(encoding="utf-8"))
        source_artifact = manifest["artifacts"][0]
        source_artifact.update(
            {
                "github_digest_sha256": zip_digest,
                "local_zip_sha256": zip_digest,
                "zip_size_bytes": zip_size,
                "extraction_inventory": {
                    "file_count": len(files),
                    "uncompressed_bytes": extracted_bytes,
                    "zip_entry_inventory_sha256": entry_digest,
                    "extracted_file_count": len(files),
                    "extracted_bytes": extracted_bytes,
                },
            }
        )
        _write_json(self.source_manifest_path, manifest)


def _make_fixture(tmp_path: Path) -> SyntheticInputs:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    _run(repo, "config", "user.name", "Fixture")
    _run(repo, "config", "user.email", "fixture@example.invalid")

    scenario_rel = "benchmark/train_scenarios_fixture.json"
    golden_rel = "config/golden_registry/registry_fixture.csv"
    simulator_rel = "simulator/simulator_flow_fixture.json"
    config_rel = "config/run_config.json"
    scenarios = [
        {"id": 1, "Z1Level": 25, "Lamp": False},
        {"id": 2, "Z1Level": 425, "Lamp": True},
    ]
    _write_json(repo / scenario_rel, scenarios)
    _write_text(
        repo / golden_rel,
        "# synthetic action registry\n"
        "key,label,actionIndex\n"
        "nothing,DO_NOTHING,2\n"
        "off,SetLamp=OFF,0\n"
        "on,SetLamp=ON,1\n",
    )
    _write_json(repo / simulator_rel, {"fixture": True})
    _write_json(
        repo / config_rel,
        {
            "phase2": {
                "train_scenarios_map": {PROFILE: scenario_rel},
                "parent_profile": {PROFILE: PARENT},
                "simulator_flow_map": {PROFILE: Path(simulator_rel).name},
            }
        },
    )
    _run(repo, "add", config_rel, golden_rel, scenario_rel, simulator_rel)
    _run(repo, "commit", "-q", "-m", "fixture sources")
    commit = _run(repo, "rev-parse", "HEAD")
    source_paths = (config_rel, golden_rel, scenario_rel, simulator_rel)
    source_oids = {path: _run(repo, "rev-parse", f"{commit}:{path}") for path in source_paths}

    schedule = hashlib.sha256(b"1,2").hexdigest()
    source_root = repo / "phase2b_qgap" / "source"
    extraction = source_root / f"run_{RUN_ID}" / "phase2-consolidated"
    _write_json(
        extraction / "analysis" / "out" / "workflow_inputs.json",
        {
            "head_sha": commit,
            "profiles": [PROFILE],
            "run_id": RUN_ID,
            "run_mode": "phase1_v2_kg_only",
            "seeds": [1],
        },
    )
    parent_names_by_boolean: dict[str, list[str]] = {}
    for boolean, mode in (("true", "ql_true"), ("false", "ql_false")):
        clean = (
            extraction
            / "_artifacts"
            / "clean"
            / f"clean-{PARENT}-stereo-{boolean}-seed-1"
        )
        names = [
            f"qtable_final_stereotypes_{boolean}_{PARENT}_trust.csv",
            f"qtable_final_stereotypes_{boolean}_{PARENT}_zone1.csv",
            f"qtable_final_stereotypes_{boolean}_{PARENT}_visits.csv",
            f"qtable_final_stereotypes_{boolean}_{PARENT}.csv",
        ]
        parent_names_by_boolean[boolean] = names
        _write_text(clean / names[0], "ActionLabel,SunBucket,Sum,N\n")
        _write_text(clean / names[1], _qtable_text())
        _write_text(clean / names[2], _qtable_text())
        _write_text(clean / names[3], _qtable_text())
        gate = {
            "status": "ok",
            "protocol_version": "phase2-v2",
            "detector_version": "fault-detector-v2",
            "metric_schema": "phase2-recovery-v2",
            "settled_start_state": True,
            "scenario_fallback_count": 0,
            "profile": PROFILE,
            "parent_profile": PARENT,
            "mode": mode,
            "run_seed": 1,
            "adapt_episodes_effective": 2,
            "adapt_episodes_override": 0,
            "train_scenarios_file": scenario_rel,
            "ordered_scenario_ids": [1, 2],
            "scenario_schedule_sha256": schedule,
            "parent_qtable_files": names,
            "parent_qtable_sha256": _runner_digest(clean, names),
        }
        seed_root = extraction / "recovery_root" / "seed1"
        _write_json(
            seed_root / f"ADAPT_OK_stereotypes_{boolean}_{PROFILE}.json", gate
        )
        _write_text(
            seed_root / f"recovery_stereotypes_{boolean}_{PROFILE}.csv",
            "# synthetic recovery outcome\n"
            "DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes,"
            "BlacklistEvents,DetectorVersion,ProtocolVersion\n"
            "Lamp,1,2,1,Lamp@1,fault-detector-v2,phase2-v2\n",
        )

    spec_path = repo / "control" / "phase2_qgap_spec.json"
    spec = {
        "schema_version": "phase2-qgap-retrospective-v1",
        "protocol_revision": "2026-07-27d",
        "source_commit": commit,
        "source_blob_oids": source_oids,
        "source_artifacts": [
            {
                "dispatch": "A1",
                "run_id": RUN_ID,
                "seeds": [1],
                "artifact_id": ARTIFACT_ID,
                "artifact_name": "phase2-consolidated",
                "size_bytes": 1,
                "sha256": "0" * 64,
                "created_at_utc": CREATED_AT,
                "expires_at_utc": EXPIRES_AT,
            }
        ],
        "artifact_rescue": {
            "local_zip_name_template": (
                "phase2-consolidated_run_{run_id}_artifact_{artifact_id}.zip"
            ),
            "extraction_template": (
                "phase2b_qgap/source/run_{run_id}/phase2-consolidated"
            ),
        },
        "forbidden_input_markers": ["postinv", "pre_inversion", "withdrawn"],
        "join_key": JOIN_FIELDS,
        "arms": {
            "KG": {"manifest_mode": "ql_true", "filename_boolean": "true"},
            "TR": {"manifest_mode": "ql_false", "filename_boolean": "false"},
        },
        "dispatch_groups": {
            "A": {"runs": [RUN_ID], "profiles": [PROFILE]},
        },
        "state_contract": {
            "parents": {
                PARENT: {
                    "scenario_file": scenario_rel,
                    "ordered_scenario_ids": [1, 2],
                    "scenario_schedule_sha256": schedule,
                    "golden_registry": golden_rel,
                    "state_labels": ["Z1Level", "Lamp"],
                    "action_labels": list(ACTIONS),
                }
            }
        },
        "cells": {
            PROFILE: {
                "dispatch_group": "A",
                "parent_profile": PARENT,
                "simulator_flow": simulator_rel,
            }
        },
        "qtable_contract": {
            "combined_filename_template": (
                "qtable_final_stereotypes_{filename_boolean}_{parent_profile}.csv"
            )
        },
        "outcome_contract": {
            "detector_version": "fault-detector-v2",
            "protocol_version": "phase2-v2",
        },
    }
    _write_json(spec_path, spec)

    source_manifest_path = repo / "control" / "source_manifest.json"
    extraction_rel = extraction.relative_to(repo).as_posix()
    source_manifest = {
        "schema_version": "phase2-qgap-source-manifest-v1",
        "source_commit": commit,
        "artifacts": [
            {
                "dispatch": "A1",
                "run_id": RUN_ID,
                "artifact_id": ARTIFACT_ID,
                "artifact_name": "phase2-consolidated",
                "head_sha": commit,
                "created_at_utc": CREATED_AT,
                "expires_at_utc": EXPIRES_AT,
                "zip_basename": (
                    f"phase2-consolidated_run_{RUN_ID}_artifact_{ARTIFACT_ID}.zip"
                ),
                "github_digest_sha256": "0" * 64,
                "local_zip_sha256": "0" * 64,
                "zip_size_bytes": 1,
                "extraction_root": extraction_rel,
                "extraction_inventory": {},
            }
        ],
        "validation": {
            "parent_file_set_hash_mismatches": 0,
            "missing_or_ambiguous_manifest_files": 0,
            "missing_recovery_csvs": 0,
        },
    }
    _write_json(source_manifest_path, source_manifest)
    fixture = SyntheticInputs(
        repo_root=repo,
        source_root=source_root,
        extraction_root=extraction,
        spec_path=spec_path,
        source_manifest_path=source_manifest_path,
        zip_root=tmp_path / "zips",
    )
    fixture.sync()
    return fixture


def _validate(fixture: SyntheticInputs):
    return validate_inputs(
        fixture.repo_root,
        fixture.source_root,
        fixture.spec_path,
        fixture.source_manifest_path,
        zip_root=fixture.zip_root,
    )


def test_valid_fixture_returns_ordered_deeply_immutable_records(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    result = _validate(fixture)

    assert len(result.records) == 2
    assert tuple(record.arm for record in result.records) == ("KG", "TR")
    record = result.records[0]
    assert record.join_key[:5] == (RUN_ID, 1, "KG", PROFILE, PARENT)
    assert record.ordered_scenario_ids == (1, 2)
    assert tuple(row["id"] for row in record.scenario_rows) == (1, 2)
    assert record.action_labels == ACTIONS
    assert record.runtime_action_indices == (0, 1, 2)
    assert tuple(path.name for path in record.parent_qtable_paths) == tuple(
        record.manifest["parent_qtable_files"]
    )
    assert tuple(path.name for path in record.zone_qtable_paths) == (
        f"qtable_final_stereotypes_true_{PARENT}_zone1.csv",
    )
    assert record.detect_episode == 1
    assert record.reconverge_episode == 2
    assert record.recovery_episodes == 1
    with pytest.raises(TypeError):
        record.manifest["status"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        record.scenario_rows[0]["id"] = 99  # type: ignore[index]


def test_duplicate_semantic_joins_are_fatal(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    spec = json.loads(fixture.spec_path.read_text(encoding="utf-8"))
    spec["dispatch_groups"]["A"]["profiles"].append(PROFILE)
    _write_json(fixture.spec_path, spec)

    with pytest.raises(InputValidationError, match="duplicate"):
        _validate(fixture)


def test_protocol_revision_drift_is_fatal(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    spec = json.loads(fixture.spec_path.read_text(encoding="utf-8"))
    spec["protocol_revision"] = "2026-07-27c"
    _write_json(fixture.spec_path, spec)

    with pytest.raises(InputValidationError, match="protocol_revision"):
        _validate(fixture)


def test_multiple_recovery_rows_are_fatal(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    path = fixture.recovery_path("true")
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("Lamp,2,3,1,Lamp@2,fault-detector-v2,phase2-v2\n")
    fixture.sync()

    with pytest.raises(InputValidationError, match="exactly one"):
        _validate(fixture)


def test_direct_child_basename_ambiguity_is_fatal(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    combined = fixture.clean_root("true") / f"qtable_final_stereotypes_true_{PARENT}.csv"
    ambiguous = (
        fixture.extraction_root
        / "_artifacts"
        / "clean"
        / "clean-decoy-stereo-true-seed-1"
        / combined.name
    )
    ambiguous.parent.mkdir(parents=True)
    shutil.copyfile(combined, ambiguous)
    fixture.sync()

    with pytest.raises(InputValidationError, match="ambiguous direct parent basename"):
        _validate(fixture)


def test_parent_manifest_order_is_preserved_and_hash_is_exact(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    valid = _validate(fixture).records[0]
    declared = tuple(valid.manifest["parent_qtable_files"])
    assert tuple(path.name for path in valid.parent_qtable_paths) == declared

    path = fixture.manifest_path("true")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["parent_qtable_files"] = list(reversed(manifest["parent_qtable_files"]))
    _write_json(path, manifest)
    fixture.sync(update_parent_hashes=False)

    with pytest.raises(InputValidationError, match="manifest-ordered parent file set"):
        _validate(fixture)


def test_forbidden_marker_in_source_path_is_fatal(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    _write_text(fixture.extraction_root / "withdrawn_copy.csv", "forbidden\n")

    with pytest.raises(InputValidationError, match="forbidden input marker"):
        _validate(fixture)


def test_combined_header_must_match_golden_runtime_order(tmp_path: Path):
    fixture = _make_fixture(tmp_path)
    combined = fixture.clean_root("true") / f"qtable_final_stereotypes_true_{PARENT}.csv"
    _write_text(combined, _qtable_text(("SetLamp=OFF", "UNKNOWN", "DO_NOTHING")))
    fixture.sync(update_parent_hashes=True)

    with pytest.raises(InputValidationError, match="action header differs"):
        _validate(fixture)


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("created_at_utc", "2026-07-24T00:00:00Z", "created_at_utc"),
        ("expires_at_utc", "2026-10-22T00:00:00Z", "expires_at_utc"),
        ("zip_basename", "renamed.zip", "ZIP basename"),
    ],
)
def test_source_archive_metadata_must_match_frozen_spec(
    tmp_path: Path,
    field: str,
    replacement: str,
    message: str,
):
    fixture = _make_fixture(tmp_path)
    source_manifest = json.loads(
        fixture.source_manifest_path.read_text(encoding="utf-8")
    )
    source_manifest["artifacts"][0][field] = replacement
    _write_json(fixture.source_manifest_path, source_manifest)

    with pytest.raises(InputValidationError, match=message):
        _validate(fixture)
