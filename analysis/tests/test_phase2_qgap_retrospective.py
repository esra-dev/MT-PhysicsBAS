from __future__ import annotations

import csv
import hashlib
import json
import random
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from analysis import phase2_qgap_retrospective as qr
from analysis.phase2_qgap_core import get_profile_spec


REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "analysis" / "phase2_qgap_spec.json"


def test_exact_two_cent_gate_uses_rationals_without_rounding():
    passed, reason = qr.gate_two_exact(
        [Fraction(0), Fraction(1, 50), Fraction(1, 25)]
    )
    assert passed
    assert "minimum_adjacent_gap=1/50" in reason

    failed, reason = qr.gate_two_exact(
        [Fraction(0), Fraction(19, 1000), Fraction(1, 25)]
    )
    assert not failed
    assert "minimum_adjacent_gap=19/1000" in reason


@pytest.mark.parametrize(
    "predictor,outcome,reason",
    [
        ((1, 1), (1, 2), "tie_predictor"),
        ((1, 2), (1, 1), "tie_outcome"),
        ((1, 1), (2, 2), "tie_both"),
    ],
)
def test_pairwise_ties_are_nonconcordant(predictor, outcome, reason):
    concordant, actual = qr.strict_pair_concordance(
        Fraction(predictor[0]),
        Fraction(predictor[1]),
        Fraction(outcome[0]),
        Fraction(outcome[1]),
    )
    assert not concordant
    assert actual == reason


def test_constant_spearman_vector_is_undefined_not_zero():
    result = qr.spearman_exact(
        [Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(1), Fraction(2), Fraction(3)],
    )
    assert not result.defined
    assert result.rho is None
    assert result.reason == "constant_predictor"


def test_linear_percentile_matches_frozen_interpolation():
    assert qr.linear_percentile(
        [Fraction(0), Fraction(10)], Fraction(1, 4)
    ) == Fraction(5, 2)
    assert qr.BOOTSTRAP_PERCENTILE_METHOD.startswith(
        "linear interpolation: h=(n-1)*p"
    )


def _paired_rows() -> list[SimpleNamespace]:
    rows = []
    for cell, multiplier in (("a", 1), ("b", 10)):
        for seed in range(1, 21):
            rows.append(
                SimpleNamespace(
                    cell=cell,
                    seed=seed,
                    delta_g=Fraction(seed * multiplier),
                    delta_signed_median=Fraction((21 - seed) * multiplier),
                    delta_recovery=Fraction(seed * 2 * multiplier),
                )
            )
    return rows


def test_bootstrap_is_reproducible_and_reuses_one_shared_seed_draw():
    panels = {
        "B_reranking": ("a", "b"),
        "C_sighted_reference": ("a", "b"),
    }
    first = qr.bootstrap_descriptors(
        _paired_rows(), panels, resamples=25, rng_seed=qr.BOOTSTRAP_SEED
    )
    second = qr.bootstrap_descriptors(
        _paired_rows(), panels, resamples=25, rng_seed=qr.BOOTSTRAP_SEED
    )
    assert first == second

    one = qr.bootstrap_descriptors(
        _paired_rows(), panels, resamples=1, rng_seed=qr.BOOTSTRAP_SEED
    )
    rng = random.Random(qr.BOOTSTRAP_SEED)
    seeds = [rng.randrange(20) + 1 for _ in range(20)]
    expected = Fraction(sum(seeds), 20)
    assert one.cell_metrics[("a", "deltaG")].median == expected
    assert one.cell_metrics[("b", "deltaG")].median == expected * 10


def test_bootstrap_consumes_exactly_twenty_randrange_calls_per_replicate(
    monkeypatch,
):
    calls = []
    instances = []

    class SpyRandom:
        def __init__(self, seed):
            instances.append(seed)

        def randrange(self, upper):
            calls.append(upper)
            return (len(calls) - 1) % upper

    monkeypatch.setattr(qr.random, "Random", SpyRandom)
    qr.bootstrap_descriptors(
        _paired_rows(),
        {
            "B_reranking": ("a", "b"),
            "C_sighted_reference": ("a", "b"),
        },
        resamples=3,
        rng_seed=qr.BOOTSTRAP_SEED,
    )
    assert instances == [qr.BOOTSTRAP_SEED]
    assert calls == [20] * 60


def test_cell_specific_censor_bound_is_independent_by_outcome():
    assert qr.censor_outcome(-1, 4000) == qr.CensoredOutcome(-1, 4001, True)
    assert qr.censor_outcome(17, 4000) == qr.CensoredOutcome(17, 17, False)
    detect = qr.censor_outcome(3, 9)
    recovery = qr.censor_outcome(-1, 9)
    assert not detect.censored and detect.value == 3
    assert recovery.censored and recovery.value == 10


def test_pairing_rejects_cross_run_kg_tr_records():
    rows = [
        SimpleNamespace(
            cell="cell", seed=1, arm="KG", parent="parent", run_id=1
        ),
        SimpleNamespace(
            cell="cell", seed=1, arm="TR", parent="parent", run_id=2
        ),
    ]
    with pytest.raises(qr.RetrospectiveError, match="different runs"):
        qr._pair_seed_aggregates(rows)


def test_multi_fault_detector_plot_series_exposes_any_all_and_components():
    aggregates = [
        SimpleNamespace(
            cell="multi",
            arm="KG",
            detection_occurrence=1,
            detect=qr.CensoredOutcome(2, 2, False),
        )
    ]
    base = {
        "run_id": 1,
        "seed": 1,
        "arm": "KG",
        "faulty_profile": "multi",
        "scenario_order": 1,
        "any_fault_component_opportunity": 1,
        "all_fault_components_opportunity": 0,
    }
    detector_rows = [
        {**base, "component": "A", "component_opportunity": 1},
        {**base, "component": "B", "component_opportunity": 0},
    ]
    series = qr._detector_plot_series(
        aggregates,
        detector_rows,
        {"A_registered_context": ("multi",)},
    )
    descriptors = {
        (row["descriptor"], row["component"]) for row in series
    }
    assert descriptors == {
        ("any", ""),
        ("all", ""),
        ("component", "A"),
        ("component", "B"),
    }


def test_checksum_inventory_covers_exactly_other_nine_outputs(tmp_path):
    for index, name in enumerate(qr.OUTPUT_NAMES[:-1]):
        (tmp_path / name).write_bytes(f"content-{index}\n".encode())
    qr._write_checksum_inventory(tmp_path)
    with (tmp_path / "SHA256SUMS.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert [row["path"] for row in rows] == sorted(qr.OUTPUT_NAMES[:-1])
    assert "SHA256SUMS.csv" not in {row["path"] for row in rows}
    for row in rows:
        content = (tmp_path / row["path"]).read_bytes()
        assert int(row["bytes"]) == len(content)
        assert row["sha256"] == hashlib.sha256(content).hexdigest()


def _write_qtable(path: Path, *, faulty_value: str) -> None:
    labels = get_profile_spec("labmon").action_labels
    path.write_text(
        "StateIndex," + ",".join(labels) + "\n"
        f"0,0.00,{faulty_value},0.00,0.00,0.00\n",
        encoding="utf-8",
        newline="\n",
    )


def _synthetic_records(source_root: Path) -> tuple[SimpleNamespace, ...]:
    source_root.mkdir(parents=True, exist_ok=True)
    combined = source_root / "combined.csv"
    zone = source_root / "zone_1.csv"
    visits = source_root / "visits.csv"
    trust = source_root / "trust.csv"
    manifest_path = source_root / "ADAPT_OK.json"
    recovery_path = source_root / "recovery.csv"
    _write_qtable(combined, faulty_value="1.00")
    _write_qtable(zone, faulty_value="0.99")
    visits.write_text("visits\n", encoding="utf-8", newline="\n")
    trust.write_text("trust\n", encoding="utf-8", newline="\n")
    manifest_path.write_text("{}\n", encoding="utf-8", newline="\n")
    recovery_path.write_text("recovery\n", encoding="utf-8", newline="\n")
    labels = get_profile_spec("labmon").action_labels
    records = []
    for seed in range(1, 21):
        for arm in ("KG", "TR"):
            detect_episode = -1 if arm == "KG" else 3
            recovery_episodes = 7 if arm == "KG" else -1
            records.append(
                SimpleNamespace(
                    run_id=30001857104,
                    seed=seed,
                    arm=arm,
                    filename_boolean="true" if arm == "KG" else "false",
                    mode="ql_true" if arm == "KG" else "ql_false",
                    faulty_profile="labmon_f1dead",
                    parent_profile="labmon",
                    manifest={},
                    manifest_path=manifest_path,
                    recovery_row={},
                    recovery_path=recovery_path,
                    detect_episode=detect_episode,
                    reconverge_episode=-1,
                    recovery_episodes=recovery_episodes,
                    detector_version="fault-detector-v2",
                    protocol_version="phase2-v2",
                    adapt_episodes_effective=10,
                    ordered_scenario_ids=(1,),
                    scenario_rows=(
                        {
                            "id": 1,
                            "Z1Light": False,
                            "Z1Monitor": False,
                        },
                    ),
                    scenario_schedule_sha256="a" * 64,
                    combined_qtable_path=combined,
                    parent_qtable_paths=(combined, zone, visits, trust),
                    zone_qtable_paths=(zone,),
                    action_labels=labels,
                    runtime_action_indices=tuple(range(len(labels))),
                    parent_qtable_sha256="b" * 64,
                    join_key=(
                        30001857104,
                        seed,
                        arm,
                        "labmon_f1dead",
                        "labmon",
                        "b" * 64,
                        "a" * 64,
                    ),
                )
            )
    return tuple(records)


def _source_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "phase2-qgap-source-manifest-v1",
                "source_commit": "19f4f3ff55f2b7ecebc015f85c6df0e55e44d7c9",
                "artifacts": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def test_enriched_source_manifest_is_idempotent_and_covers_parent_set(tmp_path):
    source_root = tmp_path / "source"
    records = _synthetic_records(source_root)
    manifest_path = source_root / "source_manifest.json"
    _source_manifest(manifest_path)
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    first = qr._enriched_source_manifest_bytes(
        repo_root=REPO_ROOT,
        source_root=source_root,
        spec_path=SPEC_PATH,
        source_manifest_path=manifest_path,
        records=records,
        spec=spec,
    )
    manifest_path.write_bytes(first)
    second = qr._enriched_source_manifest_bytes(
        repo_root=REPO_ROOT,
        source_root=source_root,
        spec_path=SPEC_PATH,
        source_manifest_path=manifest_path,
        records=records,
        spec=spec,
    )
    assert first == second
    document = json.loads(first)
    assert document["schema_version"] == "phase2-qgap-source-manifest-v1"
    source_paths = {
        row["path"]
        for row in document["validated_files"]
        if row["scope"] == "source"
    }
    assert {"combined.csv", "zone_1.csv", "visits.csv", "trust.csv"} <= source_paths
    pinned = document["pinned_source_blobs"][0]
    blob_bytes = qr.subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "cat-file",
            "blob",
            pinned["git_blob_oid"],
        ],
        check=True,
        stdout=qr.subprocess.PIPE,
    ).stdout
    assert pinned["scope"] == "git_blob"
    assert pinned["sha256"] == hashlib.sha256(blob_bytes).hexdigest()


def test_run_rejects_old_protocol_revision_before_input_check(
    tmp_path, monkeypatch
):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec["protocol_revision"] = "2026-07-27c"
    old_spec = tmp_path / "old.json"
    old_spec.write_text(json.dumps(spec), encoding="utf-8")
    called = False

    def checker(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError

    monkeypatch.setattr(qr, "validate_inputs", checker)
    with pytest.raises(qr.RetrospectiveError, match="2026-07-27d"):
        qr.run(
            REPO_ROOT,
            tmp_path,
            old_spec,
            tmp_path / "manifest.json",
            tmp_path / "out",
            require_zips=False,
        )
    assert not called


def test_full_synthetic_run_is_byte_deterministic_and_censor_rows_are_exact(
    tmp_path, monkeypatch
):
    source_root = tmp_path / "source"
    records = _synthetic_records(source_root)
    manifest_path = source_root / "source_manifest.json"
    _source_manifest(manifest_path)
    monkeypatch.setattr(
        qr,
        "validate_inputs",
        lambda **_kwargs: SimpleNamespace(records=records),
    )
    first = qr.run(
        REPO_ROOT,
        source_root,
        SPEC_PATH,
        manifest_path,
        tmp_path / "out_a",
        require_zips=False,
    )
    second = qr.run(
        REPO_ROOT,
        source_root,
        SPEC_PATH,
        manifest_path,
        tmp_path / "out_b",
        require_zips=False,
    )
    assert tuple(path.name for path in first) == qr.OUTPUT_NAMES
    assert tuple(path.name for path in second) == qr.OUTPUT_NAMES
    for left, right in zip(first, second):
        assert left.read_bytes() == right.read_bytes(), left.name

    with (tmp_path / "out_a" / "qgap_seed_rows.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    kg = next(row for row in rows if row["seed"] == "1" and row["arm"] == "KG")
    tr = next(row for row in rows if row["seed"] == "1" and row["arm"] == "TR")
    assert (kg["detection_occurrence"], kg["detect_episode_value"]) == ("0", "11")
    assert (kg["recovery_censored"], kg["recovery_value"]) == ("0", "7")
    assert (tr["detection_occurrence"], tr["detect_episode_value"]) == ("1", "3")
    assert (tr["recovery_censored"], tr["recovery_value"]) == ("1", "11")

    with (tmp_path / "out_a" / "qgap_scenario_rows.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        scenario = next(csv.DictReader(handle))
    assert scenario["any_value_discrepancy"] == "1"
    assert scenario["faulty_max_value_discrepancy"] == "1"
    assert scenario["combined_zone_sum_max_abs_difference"] == "0.01"
    assert scenario["classification"] == "REACHABLE_NONTERMINAL"

    report = (
        tmp_path / "out_a" / "PHASE2_QGAP_RETROSPECTIVE_RESULTS.md"
    ).read_text(encoding="utf-8").lower()
    for forbidden in ("significant", "validated", "causal", "p-value", "bh"):
        assert forbidden not in report
