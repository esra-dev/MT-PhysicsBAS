#!/usr/bin/env python3
"""Cross-run comparability record for two Phase-1 protocol-v2 archives.

The knowledge-ladder increment (Addendum 2026-11-10) subtracts treatment
effects measured in two workflow runs dispatched from different commits. That
is only meaningful if everything the two runs are supposed to share is in fact
identical. This script compares the two archives file by file through their
committed SHA-256 inventories and reports, per (cell kind, file kind, lab),
how many files are byte-identical. It then names the columns in which the
benchmark result CSVs differ.

Output is deterministic (sorted keys, no timestamps).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CELL = re.compile(r"^benchmark/results_seed(\d+)/(lab\d+)/([^/]+)/(.+)$")
POLICIES = ("ql_false", "rule_based", "ql_true")


def _inventory(archive: Path) -> dict[str, str]:
    with (archive / "analysis/out/SHA256SUMS.csv").open(encoding="utf-8", newline="") as handle:
        return {row["path"]: row["sha256"] for row in csv.DictReader(handle)}


def _kind(filename: str, lab: str) -> str:
    return filename.replace(f"_{lab}", "")


def build(reference: Path, other: Path) -> dict[str, object]:
    ref, oth = _inventory(reference), _inventory(other)
    table: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    for path, digest in sorted(oth.items()):
        match = CELL.match(path)
        if not match or path not in ref:
            continue
        _, lab, cell, filename = match.groups()
        key = f"{cell}/{_kind(filename, lab)}"
        table[key][lab]["identical" if ref[path] == digest else "different"] += 1

    columns: dict[str, dict[str, int]] = {}
    for policy in POLICIES:
        for path in sorted(other.glob(
                f"benchmark/results_seed*/lab*/{policy}/benchmark_results_{policy}.csv")):
            lab = path.parts[-3]
            twin = reference / path.relative_to(other)
            with path.open(encoding="utf-8", newline="") as a, \
                    twin.open(encoding="utf-8", newline="") as b:
                rows_a, rows_b = list(csv.DictReader(a)), list(csv.DictReader(b))
            if len(rows_a) != len(rows_b):
                raise ValueError(f"row count differs: {path}")
            bucket = columns.setdefault(f"{policy}/{lab}", {})
            for row_a, row_b in zip(rows_a, rows_b):
                for name, value in row_a.items():
                    if value != row_b.get(name):
                        bucket[name] = bucket.get(name, 0) + 1

    def all_identical(key: str, labs: tuple[str, ...]) -> bool:
        return all(table[key][lab]["different"] == 0 and table[key][lab]["identical"] > 0
                   for lab in labs)

    labs = ("lab1", "lab2", "lab3")
    learning_false = [f"training_stereo_false/{name}" for name in (
        "metrics_stereotypes_false.csv", "qtable_initial_stereotypes_false.csv",
        "qtable_final_stereotypes_false.csv", "first_goal_stereotypes_false.csv",
        "coverage_stereotypes_false.csv", "learned_stereotypes_false.ttl")]
    learning_true_lab1 = [f"training_stereo_true/{name}" for name in (
        "metrics_stereotypes_true.csv", "qtable_initial_stereotypes_true.csv",
        "qtable_final_stereotypes_true.csv", "first_goal_stereotypes_true.csv")]
    non_wallclock = {
        key: sorted(name for name in names if name != "LegacyWallClockTotalEnergyCost")
        for key, names in columns.items()}
    return {
        "reference_archive": reference.name,
        "other_archive": other.name,
        "same_inventory_path_set": set(ref) == set(oth),
        "check_tabula_rasa_training_identical_all_labs_all_seeds":
            all(all_identical(key, labs) for key in learning_false),
        "check_lab1_knowledge_arm_training_identical_all_seeds":
            all(all_identical(key, ("lab1",)) for key in learning_true_lab1),
        "check_ql_false_and_rule_based_benchmarks_differ_only_in_wallclock_column":
            all(not non_wallclock[key] for key in non_wallclock
                if not key.startswith("ql_true/")),
        "check_lab1_ql_true_benchmark_differs_only_in_wallclock_column":
            not non_wallclock.get("ql_true/lab1", []),
        "benchmark_result_columns_with_differing_cells":
            {key: dict(sorted(names.items())) for key, names in sorted(columns.items())},
        "files_identical_or_different_by_cell_kind_and_lab": {
            key: {lab: dict(sorted(counts.items())) for lab, counts in sorted(by_lab.items())}
            for key, by_lab in sorted(table.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--other", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.reference, args.other)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    checks = {key: value for key, value in report.items() if key.startswith("check_")}
    for key, value in sorted(checks.items()):
        print(f"{value!s:5} {key}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
