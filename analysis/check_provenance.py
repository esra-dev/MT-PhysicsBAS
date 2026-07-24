#!/usr/bin/env python3
"""Validate the current Phase-1 protocol-v2 provenance chain.

This is deliberately a small, standard-library-only CI gate.  It checks that the
public summary, the registered analysis, and all four permanent archives identify
the same pre-data commit and workflow inputs, and that no impossible zero p/q value
has entered the registered family.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "phase1-v2"
HEAD_SHA = "d3442385c91fbe11a5714bd15ca83add8f81f115"
RUNS = {
    "29848584965": "phase1_v2_kg_only",
    "29848587274": "phase1_v2_redundancy_only",
    "29848589682": "phase1_v2_baseline",
    "29848592010": "phase1_v2_pbrs_only",
}
EXPECTED_TESTS = {
    "1_arm_c_lab2_auc_goal": 0.0037,
    "2_redundancy_lab2_auc_goal": 0.002583333333333315,
    "3_arm_c_minus_redundancy_lab2": 0.0011166666666666825,
    "4_arm_c_lab3_mean_first_goal_presentations": 0.11,
    "5_arm_c_lab3_avg_cycling": 0.07375,
}
HISTORICAL_DOCS = (
    "docs/phase1_results_n10.md",
    "docs/phase1_xzone_asis_analysis.md",
    "docs/phase1_xzone_bumped_analysis.md",
    "docs/phase1_xzone_replication_s11_20_analysis.md",
    "docs/phase1_xzone_ablation_analysis.md",
    "docs/PHASE1_TO_PHASE2_CHANGES.md",
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    archive_root = root / "phase1_v2_corrected"
    for run_id, mode in RUNS.items():
        rel = Path(f"phase1_v2_corrected/run_{run_id}/analysis/out/workflow_inputs.json")
        path = root / rel
        require(path.is_file(), f"missing {rel.as_posix()}")
        if not path.is_file():
            continue
        data = _json(path)
        require(str(data.get("run_id")) == run_id, f"{rel}: wrong run_id")
        require(data.get("run_mode") == mode, f"{rel}: wrong run_mode")
        require(data.get("head_sha") == HEAD_SHA, f"{rel}: wrong head_sha")
        require(data.get("workflow") == ".github/workflows/phase1.yml", f"{rel}: wrong workflow")
        require(data.get("ref") == "refs/heads/phase1-correction-2026-07-21", f"{rel}: wrong ref")
        require(data.get("profiles") == ["lab1", "lab2", "lab3"], f"{rel}: wrong profiles")
        require(data.get("seeds") == list(range(1, 21)), f"{rel}: wrong seeds")
        require(data.get("publish_results") is True, f"{rel}: results were not published")

    family_path = archive_root / "analysis/registered/phase1_v2_registered_family.csv"
    require(family_path.is_file(), "missing registered family CSV")
    family: list[dict[str, str]] = []
    if family_path.is_file():
        with family_path.open(encoding="utf-8", newline="") as handle:
            family = list(csv.DictReader(handle))
        require(len(family) == 5, "registered family must contain exactly five tests")
        require({row.get("registered_test") for row in family} == set(EXPECTED_TESTS),
                "registered test names differ from the frozen family")
        for row in family:
            name = row.get("registered_test", "")
            require(row.get("n_paired") == "20", f"{name}: n_paired is not 20")
            require(row.get("bh_family_m") == "5", f"{name}: BH family is not m=5")
            for field in ("p_signflip_two_sided", "p_sign_exact_two_sided", "q_signflip_bh_m5"):
                try:
                    value = float(row[field])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{name}: invalid {field}")
                    continue
                require(math.isfinite(value) and 0.0 < value <= 1.0,
                        f"{name}: {field} must be finite and in (0, 1]")
            if name in EXPECTED_TESTS:
                try:
                    actual = float(row["mean_paired_difference"])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{name}: invalid mean_paired_difference")
                else:
                    require(math.isclose(actual, EXPECTED_TESTS[name], rel_tol=0.0, abs_tol=1e-15),
                            f"{name}: registered mean changed ({actual!r})")

    decomp_path = archive_root / "analysis/registered/phase1_v2_decomposition.json"
    require(decomp_path.is_file(), "missing registered decomposition JSON")
    if decomp_path.is_file():
        decomp = _json(decomp_path)
        require(decomp.get("category") == "more_than_two_thirds",
                "registered decomposition category changed")
        require(math.isclose(float(decomp.get("redundancy_share", -1)),
                             0.6981981981981937, rel_tol=0.0, abs_tol=1e-15),
                "registered decomposition share changed")

    summary_path = archive_root / "analysis/phase1_v2_protocol_gate_summary.json"
    require(summary_path.is_file(), "missing protocol gate summary")
    if summary_path.is_file():
        summary = _json(summary_path)
        require(summary.get("protocol_version") == PROTOCOL, "protocol summary has wrong version")
        require(summary.get("all_gates_pass") is True, "protocol summary does not pass all gates")
        rows = summary.get("runs", [])
        require(len(rows) == 4, "protocol summary must contain four runs")
        for row in rows:
            rid = str(row.get("run_id"))
            require(rid in RUNS, f"protocol summary has unexpected run {rid}")
            if rid in RUNS:
                require(row.get("run_mode") == RUNS[rid], f"run {rid}: summary mode mismatch")
            require(row.get("head_sha") == HEAD_SHA, f"run {rid}: summary SHA mismatch")
            require(row.get("training_cells") == 120, f"run {rid}: expected 120 training cells")
            require(row.get("benchmark_cells") == 180, f"run {rid}: expected 180 benchmark cells")
            require(row.get("fixed_horizons") == [3000], f"run {rid}: horizon is not 3000")
            require(row.get("scenario_fallback_count") == 0, f"run {rid}: random fallback occurred")
            require(row.get("schedule_pair_mismatches") == 0, f"run {rid}: paired schedules differ")
            require(row.get("protocol_versions") == [PROTOCOL], f"run {rid}: wrong protocol marker")
            require(row.get("metric_schemas") == ["phase1-benchmark-v2"],
                    f"run {rid}: wrong benchmark schema")
            require(row.get("paired_rng_versions") == ["common-seed-v1"],
                    f"run {rid}: wrong paired RNG marker")

    dashboard_path = root / "dashboard/public/data/phase1.json"
    require(dashboard_path.is_file(), "missing dashboard Phase-1 data")
    if dashboard_path.is_file():
        dashboard = _json(dashboard_path)
        require(dashboard.get("protocol_version") == PROTOCOL, "dashboard is not protocol v2")
        require(dashboard.get("status") == "current thesis evidence", "dashboard status is not current")
        require(dashboard.get("head_sha") == HEAD_SHA, "dashboard SHA differs from archives")
        require(set(map(str, dashboard.get("runs", {}).values())) == set(RUNS),
                "dashboard run IDs differ from the corrected campaign")
        dashboard_family = dashboard.get("registered_family", [])
        require(len(dashboard_family) == 5, "dashboard must expose five registered tests")
        require("registered_pooled20" not in dashboard,
                "dashboard still exposes the withdrawn pooled-20 schema")
        require(all(float(row.get("p", 0)) > 0 and float(row.get("q", 0)) > 0
                    for row in dashboard_family), "dashboard contains p/q=0")

    physics_path = root / "dashboard/src/lib/physics.js"
    require(physics_path.is_file(), "missing dashboard physics implementation")
    if physics_path.is_file():
        physics = physics_path.read_text(encoding="utf-8")
        lab1 = physics.split("lab1:", 1)[-1].split("lab2:", 1)[0]
        lab3 = physics.split("lab3:", 1)[-1].split("lab4:", 1)[0]
        require("0.10 * sun" not in lab1 and "0.1 * sun" not in lab1,
                "dashboard lab1 still has obsolete sunshine coupling")
        require("0.3 * sun" in lab3 and "(Z2Light?100)" in lab3,
                "dashboard lab3 does not encode current +100 lux / 0.30-sun coupling")

    for rel in HISTORICAL_DOCS:
        path = root / rel
        require(path.is_file(), f"missing {rel}")
        if path.is_file():
            head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:20]).lower()
            require("historical" in head and "protocol-affected" in head,
                    f"{rel}: historical protocol-affected banner missing from first 20 lines")

    for rel in (
        "docs/phase1_results_v2.md",
        "docs/thesis_methods_phase1_registration.md",
        "docs/paper_results_section.md",
        "docs/_audit/THESIS_STATE_REPORT.md",
        "docs/audit/phase1_audit_2026-07-19.md",
    ):
        path = root / rel
        require(path.is_file(), f"missing current document {rel}")
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            require("phase1-v2" in text or "protocol v2" in text or "protocol-v2" in text,
                    f"{rel}: current protocol-v2 source is not identified")

    errors.extend(check_phase34(root))
    errors.extend(check_phase2(root))
    return errors


# Phase-2 corrected-campaign pins (2026-07-24). Round-3 runs of record; the
# two documented pre-data failure rounds are in the dispatch record.
PHASE2_HEAD = "19f4f3ff55f2b7ecebc015f85c6df0e55e44d7c9"
PHASE2_RUNS = {
    "30001857104": list(range(1, 11)),
    "30001867521": list(range(11, 21)),
    "30001878310": list(range(1, 11)),
    "30001888910": list(range(11, 21)),
}
PHASE2_EXPECTED = {
    "lab3_f1dead": 2066.4,
    "lab3_f1dead_z2": 3512.0,
    "lab3_f1bdead": -19.95,
    "lab3_f1binv": -16.45,
    "lab2_f1bdead": -92.65,
    "labmon_f1dead": -218.6,
    "lab3_f2dead_lowsun": 3654.15,
    "labmon2_f2dead_lowsun": -168.75,
}


def check_phase2(root: Path) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for run_id, seeds in PHASE2_RUNS.items():
        inputs_path = root / f"phase2_v2_corrected/run_{run_id}/analysis/out/workflow_inputs.json"
        require(inputs_path.is_file(), f"missing workflow inputs for phase2 run {run_id}")
        if not inputs_path.is_file():
            continue
        data = _json(inputs_path)
        require(str(data.get("run_id")) == run_id, f"phase2 run {run_id}: wrong run_id")
        require(data.get("run_mode") == "phase1_v2_kg_only", f"phase2 run {run_id}: wrong run_mode")
        require(data.get("head_sha") == PHASE2_HEAD, f"phase2 run {run_id}: wrong head_sha")
        require(data.get("seeds") == seeds, f"phase2 run {run_id}: wrong seeds")

    family_path = root / "phase2_v2_corrected/analysis/registered/phase2_v2_registered_family.csv"
    require(family_path.is_file(), "missing phase2 registered family CSV")
    if family_path.is_file():
        with family_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        require({row.get("registered_cell") for row in rows} == set(PHASE2_EXPECTED),
                "phase2 registered cells differ from the frozen Tier-1 family")
        for row in rows:
            cell = row.get("registered_cell", "")
            require(row.get("n_paired") == "20", f"phase2 {cell}: n_paired is not 20")
            for field in ("p_signflip_two_sided", "q_signflip_bh_m8"):
                try:
                    value = float(row[field])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"phase2 {cell}: invalid {field}")
                    continue
                require(math.isfinite(value) and 0.0 < value <= 1.0,
                        f"phase2 {cell}: {field} must be finite and in (0, 1]")
            if cell in PHASE2_EXPECTED:
                try:
                    actual = float(row["mean_paired_difference"])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"phase2 {cell}: invalid mean_paired_difference")
                else:
                    require(math.isclose(actual, PHASE2_EXPECTED[cell], rel_tol=0.0, abs_tol=1e-15),
                            f"phase2 {cell}: registered mean changed ({actual!r})")

    dashboard_path = root / "dashboard/public/data/phase2.json"
    require(dashboard_path.is_file(), "missing dashboard phase2.json")
    if dashboard_path.is_file():
        data = _json(dashboard_path)
        require(data.get("protocol_version") == "phase2-v2", "dashboard phase2.json: wrong protocol")
        require(data.get("detector_version") == "fault-detector-v2",
                "dashboard phase2.json: wrong detector version")
        require(data.get("false_positive_blacklist_events") == 0,
                "dashboard phase2.json: nonzero false-positive count")
        for key in ("ci", "paired"):
            require(key not in data, f"dashboard phase2.json: withdrawn key {key!r} present")
    return errors


# Phase-3/4 corrected-campaign pins (2026-07-22). Same contract as the Phase-1
# pins above: committed workflow inputs must identify the registered dispatch,
# the registered family means are frozen, and the dashboard must expose only
# corrected data.
PHASE34_HEAD = "90e53f8b087fc390a7ad51a0187b81c89c21c64e"
PHASE34_REF = "refs/heads/phase234-correction-2026-07-22"
PHASE3_RUN = "29926328852"
PHASE4_RUNS = {"29926341581": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
               "29926354783": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}
PHASE4_EXPECTED = {
    "lab4": -0.6950000000000001,
    "lab4dual": -0.7450000000000001,
    "lab4chain": -0.734375,
    "lab5": 0.043125000000000024,
}


def check_phase34(root: Path) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    p3_inputs = root / f"phase3_v2_corrected/run_{PHASE3_RUN}/analysis/out/workflow_inputs.json"
    require(p3_inputs.is_file(), f"missing {p3_inputs.name} for phase3 run {PHASE3_RUN}")
    if p3_inputs.is_file():
        data = _json(p3_inputs)
        require(str(data.get("run_id")) == PHASE3_RUN, "phase3 workflow inputs: wrong run_id")
        require(data.get("head_sha") == PHASE34_HEAD, "phase3 workflow inputs: wrong head_sha")
        require(data.get("ref") == PHASE34_REF, "phase3 workflow inputs: wrong ref")

    for run_id, seeds in PHASE4_RUNS.items():
        inputs_path = root / f"phase4_v2_corrected/run_{run_id}/analysis/out/workflow_inputs.json"
        require(inputs_path.is_file(), f"missing workflow inputs for phase4 run {run_id}")
        if not inputs_path.is_file():
            continue
        data = _json(inputs_path)
        require(str(data.get("run_id")) == run_id, f"phase4 run {run_id}: wrong run_id")
        require(data.get("run_mode") == "phase4_v2", f"phase4 run {run_id}: wrong run_mode")
        require(data.get("head_sha") == PHASE34_HEAD, f"phase4 run {run_id}: wrong head_sha")
        require(data.get("ref") == PHASE34_REF, f"phase4 run {run_id}: wrong ref")
        require(data.get("seeds") == seeds, f"phase4 run {run_id}: wrong seeds")

    family_path = root / "phase4_v2_corrected/analysis/registered/phase4_v2_registered_family.csv"
    require(family_path.is_file(), "missing phase4 registered family CSV")
    if family_path.is_file():
        with family_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        require({row.get("registered_cell") for row in rows} == set(PHASE4_EXPECTED),
                "phase4 registered cells differ from the frozen family")
        for row in rows:
            cell = row.get("registered_cell", "")
            for field in ("p_signflip_two_sided", "q_signflip_bh_m4"):
                try:
                    value = float(row[field])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"phase4 {cell}: invalid {field}")
                    continue
                require(math.isfinite(value) and 0.0 < value <= 1.0,
                        f"phase4 {cell}: {field} must be finite and in (0, 1]")
            if cell in PHASE4_EXPECTED:
                try:
                    actual = float(row["mean_paired_difference"])
                except (KeyError, TypeError, ValueError):
                    errors.append(f"phase4 {cell}: invalid mean_paired_difference")
                else:
                    require(math.isclose(actual, PHASE4_EXPECTED[cell], rel_tol=0.0, abs_tol=1e-15),
                            f"phase4 {cell}: registered mean changed ({actual!r})")

    for name, expected_keys, forbidden in (
            ("phase3.json", {"protocol_version": "phase3-v2"}, ("llm",)),
            ("phase4.json", {"run_mode": "phase4_v2"}, ("llm_summary", "llm_detail_lab5", "summary"))):
        path = root / "dashboard" / "public" / "data" / name
        require(path.is_file(), f"missing dashboard {name}")
        if path.is_file():
            data = _json(path)
            for key, expected in expected_keys.items():
                require(data.get(key) == expected, f"dashboard {name}: {key} != {expected}")
            for key in forbidden:
                require(key not in data, f"dashboard {name}: withdrawn key {key!r} present")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print(f"PROVENANCE CHECK FAILED - {len(errors)} violation(s):")
        for error in errors:
            print(f"  {error}")
        return 1
    print("provenance check OK (4 corrected runs, registered family, dashboard, docs, physics)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
