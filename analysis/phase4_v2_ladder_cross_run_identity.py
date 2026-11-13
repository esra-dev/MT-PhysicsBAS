#!/usr/bin/env python3
"""Cross-run comparability record for the Phase-4 knowledge ladder.

The ladder increments (THESIS_STATE_REPORT.md Addendum 2026-11-13b) subtract
treatment effects measured in different workflow runs dispatched from
different commits. This script records how much of what those runs are
supposed to share is in fact identical: it compares, seed by seed, every file
of the tabula-rasa training cell and of the ``ql_false`` and ``rule_based``
benchmark cells of a control run with the same file in the archived full-KG
campaign, by SHA-256, and names the benchmark columns in which cells differ.

Output is deterministic (sorted keys, no timestamps).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SHARED_CELLS = ("training_stereo_false", "ql_false", "rule_based")
BENCH_POLICIES = ("ql_false", "rule_based")
WALLCLOCK_COLUMN = "LegacyWallClockTotalEnergyCost"
# Per-cell files that record wall-clock time or the dispatched run mode and are
# therefore expected to differ between two runs of the same configuration.
EXPECTED_TO_DIFFER = re.compile(r"^(TRAINING_OK\.json|bench_step_log_.*\.csv|iv_stats_.*\.json)$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_dirs(roots: list[Path]) -> dict[int, Path]:
    out: dict[int, Path] = {}
    for root in roots:
        for seed_dir in sorted((root / "benchmark").glob("results_seed*")):
            seed = int(seed_dir.name.replace("results_seed", ""))
            if seed in out:
                raise SystemExit(f"seed {seed} present in two roots")
            out[seed] = seed_dir
    return out


def build(reference_roots: list[Path], other_roots: list[Path], labs: list[str]) -> dict:
    ref, oth = _seed_dirs(reference_roots), _seed_dirs(other_roots)
    seeds = sorted(set(ref) & set(oth))
    table: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    columns: dict[str, dict[str, int]] = {}
    missing: list[str] = []
    for seed in seeds:
        for lab in labs:
            for cell in SHARED_CELLS:
                other_cell = oth[seed] / lab / cell
                ref_cell = ref[seed] / lab / cell
                if not other_cell.is_dir() or not ref_cell.is_dir():
                    missing.append(f"seed{seed}/{lab}/{cell}")
                    continue
                for path in sorted(p for p in other_cell.iterdir() if p.is_file()):
                    if "stereotypes_true" in path.name:
                        continue  # copy of the knowledge arm's training files: differs by design
                    kind = f"{cell}/{path.name.replace('_' + lab, '')}"
                    twin = ref_cell / path.name
                    if not twin.is_file():
                        table[kind][lab]["absent_in_reference"] += 1
                    elif _sha(path) == _sha(twin):
                        table[kind][lab]["identical"] += 1
                    else:
                        table[kind][lab]["different"] += 1
            for policy in BENCH_POLICIES:
                a = oth[seed] / lab / policy / f"benchmark_results_{policy}.csv"
                b = ref[seed] / lab / policy / f"benchmark_results_{policy}.csv"
                if not a.is_file() or not b.is_file():
                    continue
                with a.open(encoding="utf-8-sig", newline="") as ha, b.open(encoding="utf-8-sig", newline="") as hb:
                    rows_a, rows_b = list(csv.DictReader(ha)), list(csv.DictReader(hb))
                if len(rows_a) != len(rows_b):
                    raise SystemExit(f"row count differs: {a}")
                bucket = columns.setdefault(f"{policy}/{lab}", {})
                for row_a, row_b in zip(rows_a, rows_b):
                    for name, value in row_a.items():
                        if value != row_b.get(name):
                            bucket[name] = bucket.get(name, 0) + 1

    def identical(kind: str) -> bool:
        return all(table[kind][lab]["different"] == 0 and table[kind][lab]["absent_in_reference"] == 0
                   and table[kind][lab]["identical"] > 0 for lab in labs)

    learning_kinds = [f"training_stereo_false/{name}" for name in (
        "metrics_stereotypes_false.csv", "qtable_initial_stereotypes_false.csv",
        "qtable_final_stereotypes_false.csv", "first_goal_stereotypes_false.csv",
        "coverage_stereotypes_false.csv")]
    non_wallclock = {key: sorted(n for n in names if n != WALLCLOCK_COLUMN) for key, names in columns.items()}
    # A benchmark result file whose only differing column is the wall-clock
    # diagnostic differs as a file but not in any analysed quantity.
    wallclock_only = {
        f"{policy}/benchmark_results_{policy}.csv" for policy in BENCH_POLICIES
        if all(not names for key, names in non_wallclock.items() if key.startswith(policy + "/"))}
    unexpected = sorted(
        kind for kind, by_lab in table.items()
        if any(counts["different"] for counts in by_lab.values())
        and not EXPECTED_TO_DIFFER.match(kind.split("/", 1)[1])
        and kind not in wallclock_only)
    return {
        "reference_roots": [r.name for r in reference_roots],
        "other_roots": [r.name for r in other_roots],
        "labs": labs,
        "seeds_compared": seeds,
        "cells_missing": missing,
        "check_tabula_rasa_training_identical_all_labs_all_seeds":
            bool(seeds) and not missing and all(identical(kind) for kind in learning_kinds),
        "check_ql_false_and_rule_based_benchmarks_differ_only_in_wallclock_column":
            bool(columns) and all(not names for names in non_wallclock.values()),
        "file_kinds_with_unexpected_differences": unexpected,
        "benchmark_result_columns_with_differing_cells":
            {key: dict(sorted(names.items())) for key, names in sorted(columns.items())},
        "files_identical_or_different_by_cell_kind_and_lab": {
            kind: {lab: dict(sorted(counts.items())) for lab, counts in sorted(by_lab.items())}
            for kind, by_lab in sorted(table.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-roots", nargs="+", type=Path, required=True,
                        help="archived phase4_v2 run folders")
    parser.add_argument("--other-roots", nargs="+", type=Path, required=True,
                        help="run folders of one control arm")
    parser.add_argument("--labs", required=True, help="comma-separated lab list")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.reference_roots, args.other_roots, [l for l in args.labs.split(",") if l])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    checks = {key: value for key, value in report.items() if key.startswith("check_")}
    for key, value in sorted(checks.items()):
        print(f"{value!s:5} {key}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
