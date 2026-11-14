"""Delivery guards for the Phase-2 structure-only campaign (2026-11-14).

The campaign's treatment is one flag: the adaptation step runs with
``-Pstereo.knowledgeLayer=brick`` in both arms, while everything else stays
exactly as in the runs of record. These tests make every link of that chain a
local/CI failure:

- ``run_phase2_adapt.ps1`` accepts ``-KnowledgeLayer``, forwards the Gradle
  flag only for non-default layers, and records + log-verifies the layer in
  every ADAPT_OK manifest;
- ``.github/workflows/phase2.yml`` exposes the input, validates it pre-matrix,
  passes it to the orchestrator and into the workflow provenance;
- the archive validator rejects any cell whose manifest did not record AND
  log-verify the required layer;
- the frozen analysis constants (cells, arms, comparator mapping, injected
  ground-truth components) match the repository they describe.
"""

import json
import re
import sys

import pytest

from analysis import phase2_structonly_v3_family as fam
from analysis import validate_phase2_v2_archive as v2
from analysis import write_workflow_provenance as prov

ROOT = v2.SOURCE_ROOT


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ------------------------------------------------------------- orchestrator --

def test_ps1_accepts_and_validates_knowledge_layer():
    text = _text("run_phase2_adapt.ps1")
    assert re.search(r'\[string\]\$KnowledgeLayer\s*=\s*"full"', text)
    assert '@("full", "brick", "redundancy") -notcontains $KnowledgeLayer' in text


def test_ps1_forwards_gradle_flag_only_for_non_default_layer():
    text = _text("run_phase2_adapt.ps1")
    assert re.search(r'if \(\$KnowledgeLayer -ne "full"\) \{ \$gArgs \+= '
                     r'"-Pstereo\.knowledgeLayer=\$KnowledgeLayer" \}', text)


def test_ps1_records_and_log_verifies_layer_in_manifest():
    text = _text("run_phase2_adapt.ps1")
    assert "knowledge_layer          = $KnowledgeLayer" in text
    assert "knowledge_layer_delivered = $deliveredLayer" in text
    assert "StereotypeReasoner: knowledge layer = " in text
    assert "Knowledge-layer treatment NOT verified" in text


def test_gradle_forwards_the_stereo_knowledge_layer_property():
    # taskAdapt is a JavaExec; the shared forwarding allow-list must carry the
    # flag into the adapt JVM as a system property.
    text = _text("build.gradle")
    assert "'stereo.knowledgeLayer'" in text
    assert re.search(r"task taskAdapt \(type: JavaExec", text)


# ----------------------------------------------------------------- workflow --

def test_workflow_exposes_and_passes_knowledge_layer():
    text = _text(".github/workflows/phase2.yml")
    assert "knowledge_layer:" in text
    assert "KNOWLEDGE_LAYER: ${{ github.event.inputs.knowledge_layer || 'full' }}" in text
    assert "-KnowledgeLayer ${{ env.KNOWLEDGE_LAYER }}" in text
    assert '--knowledge-layer "$KNOWLEDGE_LAYER"' in text
    assert "full|brick|redundancy" in text  # fail-fast validation in setup


# --------------------------------------------------------------- provenance --

def _run_prov(tmp_path, extra):
    out = tmp_path / "workflow_inputs.json"
    argv = ["prog", "--out", str(out), "--run-id", "1", "--sha", "deadbeef",
            "--ref", "refs/heads/x", "--run-mode", "phase1_v2_kg_only",
            "--profiles", "lab2_f1bdead", "--seeds", "1,2",
            "--publish-results", "true"] + extra
    old = sys.argv
    sys.argv = argv
    try:
        assert prov.main() == 0
    finally:
        sys.argv = old
    return json.loads(out.read_text(encoding="utf-8"))


def test_provenance_omits_layer_by_default(tmp_path):
    payload = _run_prov(tmp_path, [])
    assert "knowledge_layer" not in payload


def test_provenance_records_layer_when_passed(tmp_path):
    payload = _run_prov(tmp_path, ["--knowledge-layer", "BRICK"])
    assert payload["knowledge_layer"] == "brick"


# ---------------------------------------------------------- archive validator --

def _layer_errors(errors):
    return [e for e in errors if "knowledge-layer delivery gate" in e]


def _fake_cell(tmp_path, manifest_extra):
    seed_root = tmp_path / "recovery_root" / "seed7"
    seed_root.mkdir(parents=True)
    scenario_rel = json.loads((ROOT / "config" / "run_config.json")
                              .read_text(encoding="utf-8-sig"))["phase2"][
                                  "train_scenarios_map"]["lab2_f1bdead"]
    ids, schedule_hash, file_hash, sun = v2._schedule_and_treatment(scenario_rel)
    for bool_name, mode in (("true", "ql_true"), ("false", "ql_false")):
        manifest = {
            "status": "ok", "protocol_version": "phase2-v2",
            "detector_version": "fault-detector-v2",
            "metric_schema": "phase2-recovery-v2",
            "settled_start_state": True, "scenario_fallback_count": 0,
            "profile": "lab2_f1bdead", "mode": mode, "run_seed": 7,
            "adapt_episodes_effective": 10,
            "train_scenarios_file": scenario_rel,
            "ordered_scenario_ids": ids,
            "scenario_schedule_sha256": schedule_hash,
            "parent_qtable_sha256": "abc",
        }
        manifest.update(manifest_extra)
        name = f"stereotypes_{bool_name}_lab2_f1bdead"
        (seed_root / f"ADAPT_OK_{name}.json").write_text(
            json.dumps(manifest), encoding="utf-8")
        (seed_root / f"recovery_{name}.csv").write_text(
            "DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes,"
            "SecondaryDetectEpisode,RecoveredGoalRate,NominalGoal,BestEffortRank,"
            "RankShortfall,DegradedMode,BlacklistEvents,DetectorVersion,ProtocolVersion\n"
            "x,1,2,1,-1,1.0,3,3,0,0,,fault-detector-v2,phase2-v2\n",
            encoding="utf-8")
        (seed_root / f"metrics_adapted_{name}.csv").write_text(
            "Episode\n" + "\n".join(str(i) for i in range(10)) + "\n",
            encoding="utf-8")
    return tmp_path


def test_validator_rejects_cell_without_layer_evidence(tmp_path):
    root = _fake_cell(tmp_path, {})
    errors = v2.validate(root, ["lab2_f1bdead"], [7], require_parents=False,
                         require_knowledge_layer="brick")
    assert len(_layer_errors(errors)) == 4  # 2 keys x 2 arms


def test_validator_rejects_requested_but_undelivered_layer(tmp_path):
    root = _fake_cell(tmp_path, {"knowledge_layer": "brick",
                                 "knowledge_layer_delivered": "full"})
    errors = v2.validate(root, ["lab2_f1bdead"], [7], require_parents=False,
                         require_knowledge_layer="brick")
    assert len(_layer_errors(errors)) == 2  # delivered key, both arms


def test_validator_accepts_recorded_and_delivered_layer(tmp_path):
    root = _fake_cell(tmp_path, {"knowledge_layer": "brick",
                                 "knowledge_layer_delivered": "brick"})
    errors = v2.validate(root, ["lab2_f1bdead"], [7], require_parents=False,
                         require_knowledge_layer="brick")
    assert not _layer_errors(errors)
    # without the gate the same archive raises no layer errors either
    errors = v2.validate(root, ["lab2_f1bdead"], [7], require_parents=False)
    assert not _layer_errors(errors)


# ------------------------------------------------------- frozen analysis ----

def test_wrong_blame_count_rules():
    injected = ("SetZ1Light", "SetZ2Light")
    assert fam.wrong_blame_count("", injected) == 0
    assert fam.wrong_blame_count(None, injected) == 0
    assert fam.wrong_blame_count(
        "http://example.org/was#SetZ1Light@4;http://example.org/was#SetZ2Light@9",
        injected) == 0
    assert fam.wrong_blame_count(
        "http://example.org/was#SetZ1Blinds@0", injected) == 1
    assert fam.wrong_blame_count(
        "http://example.org/was#SetZ1Blinds@0;http://example.org/was#SetZ1Light@2;"
        "http://example.org/was#SetZ2Blinds@5", injected) == 2
    # a blind cell: the dead blind itself is NOT a wrong blame
    assert fam.wrong_blame_count(
        "http://example.org/was#SetZ1Blinds@3", ("SetZ1Blinds",)) == 0


def test_frozen_cells_and_comparator_mapping():
    assert fam.STRUCTONLY_CELLS == ("lab2_f1bdead", "lab3_f1bdead",
                                    "lab3_f2dead_lowsun", "labmon2_f2dead_lowsun")
    assert fam.ARMS == (("true", "ql_true"), ("false", "ql_false"))
    assert tuple(fam.SEEDS) == tuple(range(1, 21))
    for cell, roots in fam.RECORD_ROOTS.items():
        for rel in roots:
            assert (ROOT / rel).is_dir(), f"missing comparator archive {rel}"
    # the low-sun cells must never resolve into the superseded mixed-sun rows
    for cell in ("lab3_f2dead_lowsun", "labmon2_f2dead_lowsun"):
        assert fam.RECORD_ROOTS[cell] == ("phase2_v3_lowsun/run_43099277363",)


@pytest.mark.parametrize("cell", fam.STRUCTONLY_CELLS)
def test_comparator_archives_hold_exactly_one_record_per_seed(cell):
    # The recovery CSVs are gitignored (committed archives carry manifests and
    # metrics only), so this check runs only where the complete extracted
    # archives are present — as for every campaign reproducer since protocol v2.
    roots = [ROOT / rel for rel in fam.RECORD_ROOTS[cell]]
    for seed in (1, 20):
        for bool_name, _arm in fam.ARMS:
            try:
                fam._resolve(roots, cell, bool_name, seed)  # SystemExit on != 1
            except SystemExit as exc:
                if "found 0" in str(exc):
                    pytest.skip("comparator raw files not in this checkout "
                                "(gitignored recovery CSVs); run in a complete "
                                "archive tree")
                raise


def test_injected_components_match_the_faulty_flow_generator():
    text = _text("simulator/generate_faulty_flows.ps1")
    blind = re.compile(r"'z1b \? 0\.50 \* sun', 'z1b \? 0'")
    for cell in ("lab2_f1bdead", "lab3_f1bdead"):
        assert fam.INJECTED_COMPONENTS[cell] == ("SetZ1Blinds",)
        block = text[text.index(f"simulator_flow_{cell}.json"):]
        assert blind.search(block[:400]), f"{cell}: generator does not kill z1b"
    for cell in ("lab3_f2dead_lowsun", "labmon2_f2dead_lowsun"):
        assert fam.INJECTED_COMPONENTS[cell] == ("SetZ1Light", "SetZ2Light")
        block = text[text.index(f"simulator_flow_{cell}.json"):][:600]
        assert "'z1l ? 400', 'z1l ? 0'" in block, f"{cell}: generator does not kill z1l"
        assert "'z2l ? 400', 'z2l ? 0'" in block, f"{cell}: generator does not kill z2l"
