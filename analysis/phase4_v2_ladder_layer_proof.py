#!/usr/bin/env python3
"""Operational proof of treatment delivery for the Phase-4 knowledge ladder.

Registered in THESIS_STATE_REPORT.md Addendum 2026-11-13b ("Operational proof
of delivery", item 3, plug-invariance): in the ``ql_true`` initial Q-tables of
lab4, lab4dual, and lab4chain, the ON column of every power-gated action has
the same value in any two states that differ only in the state bit of its
upstream switch. The property holds when no power gate is bound (redundancy
and Brick layers) and cannot hold under the full layer, where Rule 2 writes a
well while the switch is off.

The gated actions and their upstream switch slots are read from the FULL
reference registry (``config/golden_registry/registry_<lab>.csv``: rows with
``hasIV=true`` whose ``ivIdx`` is not the sunshine slot). The state layout is
read from the lab knowledge graph. The archived tables are the combined
(sum over zones) initial tables of each training cell:
``benchmark/results_seed<N>/<lab>/training_stereo_true/qtable_initial_stereotypes_true_<lab>.csv``.

With ``--reference-roots`` the script also writes a cell-by-cell comparison of
the initial tables of the arm with those of a reference arm (the archived
full-KG campaign), for the three dependency labs and lab5. That comparison is
an additional consistency check added after the registered proof; it reports
in which columns and under which gate and sunshine conditions the tables
differ.

Output is deterministic (sorted keys, no timestamps).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

LAB_TTL = {
    "lab4": "src/resources/building_4_smartplug.ttl",
    "lab4dual": "src/resources/building_8_dualplug.ttl",
    "lab4chain": "src/resources/building_9_chainplug.ttl",
}
# Labs of the optional table comparison: the dependency labs plus lab5.
ALL_TTL = {**LAB_TTL, "lab5": "src/resources/building_5_energy.ttl"}
SLOT = re.compile(
    r"ws:stateVecIndex\s+(\d+)\s*;\s*ws:stateDomainSize\s+(\d+)\s*;"
    r"\s*ws:stateSlotRole\s+\"([a-z_]+)\"")


def _layout(repo: Path, lab: str) -> dict:
    """State-slot layout from the lab KG (mixed radix, slot 0 most significant)."""
    slots: dict[int, tuple[int, str]] = {}
    for line in (repo / ALL_TTL[lab]).read_text(encoding="utf-8").splitlines():
        match = SLOT.search(line)
        if match:
            slots[int(match.group(1))] = (int(match.group(2)), match.group(3))
    if sorted(slots) != list(range(len(slots))):
        raise ValueError(f"{lab}: state slots are not contiguous: {sorted(slots)}")
    sizes = [slots[i][0] for i in range(len(slots))]
    strides = [0] * len(sizes)
    product = 1
    for index in range(len(sizes) - 1, -1, -1):
        strides[index] = product
        product *= sizes[index]
    sun = [i for i in slots if slots[i][1] == "sunshine"]
    if len(sun) != 1:
        raise ValueError(f"{lab}: expected exactly one sunshine slot")
    return {"sizes": sizes, "strides": strides, "sun_slot": sun[0], "n_states": product}


def _gated_actions(repo: Path, lab: str, sun_slot: int) -> dict[str, dict[str, int]]:
    """ON-column label -> {own_slot, gate_slot} for every power-gated action."""
    gated: dict[str, dict[str, int]] = {}
    golden = repo / "config" / "golden_registry" / f"registry_{lab}.csv"
    lines = [l for l in golden.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    for row in csv.DictReader(lines):
        if row["hasIV"] == "true" and int(row["ivIdx"]) != sun_slot:
            gated[row["label"]] = {"own_slot": int(row["svBit"]), "gate_slot": int(row["ivIdx"])}
    return gated


def _digit(state: int, layout: dict, slot: int) -> int:
    return (state // layout["strides"][slot]) % layout["sizes"][slot]


def _load(path: Path) -> tuple[list[str], dict[int, list[str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return rows[0][1:], {int(row[0]): row[1:] for row in rows[1:]}


def _seed_tables(roots: list[Path], lab: str) -> dict[int, Path]:
    tables: dict[int, Path] = {}
    for root in roots:
        for seed_dir in sorted((root / "benchmark").glob("results_seed*")):
            seed = int(seed_dir.name.replace("results_seed", ""))
            path = seed_dir / lab / "training_stereo_true" / f"qtable_initial_stereotypes_true_{lab}.csv"
            if path.is_file():
                if seed in tables:
                    raise SystemExit(f"duplicate initial table for {lab} seed {seed}")
                tables[seed] = path
    return tables


def _check_table(path: Path, layout: dict, gated: dict[str, dict[str, int]]) -> dict:
    columns, table = _load(path)
    if len(table) != layout["n_states"]:
        raise SystemExit(f"{path}: {len(table)} states, layout expects {layout['n_states']}")
    result = {}
    for label, slots in sorted(gated.items()):
        col = columns.index(label)
        stride = layout["strides"][slots["gate_slot"]]
        pairs = differ = 0
        gate_off_self_off: Counter[str] = Counter()
        gate_on_self_off: Counter[str] = Counter()
        for state, values in table.items():
            if _digit(state, layout, slots["gate_slot"]) != 0:
                continue
            partner = table[state + stride]
            pairs += 1
            if values[col] != partner[col]:
                differ += 1
            if _digit(state, layout, slots["own_slot"]) == 0:
                gate_off_self_off[values[col]] += 1
                gate_on_self_off[partner[col]] += 1
        result[label] = {
            "gate_slot": slots["gate_slot"],
            "own_slot": slots["own_slot"],
            "state_pairs": pairs,
            "pairs_that_differ": differ,
            "gate_invariant": differ == 0,
            "values_gate_off_action_off": {k: gate_off_self_off[k] for k in sorted(gate_off_self_off, key=float)},
            "values_gate_on_action_off": {k: gate_on_self_off[k] for k in sorted(gate_on_self_off, key=float)},
        }
    return result


def run(repo: Path, roots: list[Path], arm: str) -> dict:
    out: dict = {"arm": arm, "roots": [root.name for root in roots], "labs": {}}
    for lab in LAB_TTL:
        layout = _layout(repo, lab)
        gated = _gated_actions(repo, lab, layout["sun_slot"])
        tables = _seed_tables(roots, lab)
        if not tables:
            out["labs"][lab] = {"status": "no_initial_tables"}
            continue
        hashes = {seed: hashlib.sha256(path.read_bytes()).hexdigest() for seed, path in tables.items()}
        first_seed = min(tables)
        per_action = _check_table(tables[first_seed], layout, gated)
        # Every other seed must give the same verdict per action.
        consistent = True
        for seed, path in sorted(tables.items()):
            if seed == first_seed or hashes[seed] == hashes[first_seed]:
                continue
            other = _check_table(path, layout, gated)
            if any(other[a]["gate_invariant"] != per_action[a]["gate_invariant"] for a in per_action):
                consistent = False
        out["labs"][lab] = {
            "status": "ok",
            "seeds": sorted(tables),
            "n_states": layout["n_states"],
            "distinct_table_sha256": len(set(hashes.values())),
            "first_seed": first_seed,
            "first_seed_sha256": hashes[first_seed],
            "gated_actions": per_action,
            "all_gated_columns_invariant": all(v["gate_invariant"] for v in per_action.values()),
            "verdict_consistent_across_seeds": consistent,
        }
    labs_ok = [v for v in out["labs"].values() if v.get("status") == "ok"]
    out["all_gated_columns_invariant"] = bool(labs_ok) and all(v["all_gated_columns_invariant"] for v in labs_ok)
    return out


def compare(repo: Path, roots: list[Path], reference_roots: list[Path], arm: str) -> dict:
    """Where do the initial tables of an arm differ from those of the reference arm?

    For every lab and the first seed present in both arms, each differing cell
    is attributed to its column and to the condition it occurs under: the state
    of the upstream switch (power-gated columns only) and the sunshine rank.
    """
    out: dict = {"arm": arm, "roots": [root.name for root in roots],
                 "reference_roots": [root.name for root in reference_roots], "labs": {}}
    for lab in ALL_TTL:
        layout = _layout(repo, lab)
        gated = _gated_actions(repo, lab, layout["sun_slot"])
        mine, reference = _seed_tables(roots, lab), _seed_tables(reference_roots, lab)
        seeds = sorted(set(mine) & set(reference))
        if not seeds:
            out["labs"][lab] = {"status": "no_common_seed"}
            continue
        columns, table = _load(mine[seeds[0]])
        ref_columns, ref_table = _load(reference[seeds[0]])
        if columns != ref_columns or table.keys() != ref_table.keys():
            raise SystemExit(f"{lab}: initial tables of the two arms have different shapes")
        different: dict[str, Counter[str]] = {}
        confined = True
        for state, values in table.items():
            sun = _digit(state, layout, layout["sun_slot"])
            for index, label in enumerate(columns):
                if values[index] == ref_table[state][index]:
                    continue
                gate = _digit(state, layout, gated[label]["gate_slot"]) if label in gated else None
                condition = f"sun_rank={sun}" if gate is None else f"gate={gate} sun_rank={sun}"
                different.setdefault(label, Counter())[condition] += 1
                if not (gate == 0 or sun == 0):
                    confined = False
        out["labs"][lab] = {
            "status": "ok",
            "seed_compared": seeds[0],
            "seeds_in_both_arms": seeds,
            "n_states": layout["n_states"],
            "distinct_table_sha256_this_arm": len(
                {hashlib.sha256(mine[s].read_bytes()).hexdigest() for s in seeds}),
            "distinct_table_sha256_reference": len(
                {hashlib.sha256(reference[s].read_bytes()).hexdigest() for s in seeds}),
            "columns_identical": sorted(label for label in columns if label not in different),
            "columns_different": {
                label: {"cells": sum(counts.values()), "by_condition": dict(sorted(counts.items()))}
                for label, counts in sorted(different.items())},
            "every_difference_at_gate_off_or_sun_rank_0": confined,
        }
    labs_ok = [v for v in out["labs"].values() if v.get("status") == "ok"]
    out["every_difference_at_gate_off_or_sun_rank_0"] = bool(labs_ok) and all(
        v["every_difference_at_gate_off_or_sun_rank_0"] for v in labs_ok)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--roots", nargs="+", type=Path, required=True, help="run folders of ONE arm")
    parser.add_argument("--arm", required=True, help="label written into the output, e.g. A2_brick")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference-roots", nargs="+", type=Path, default=None,
                        help="run folders of the reference arm for the optional table comparison")
    parser.add_argument("--compare-out", type=Path, default=None)
    args = parser.parse_args()
    result = run(args.repo, args.roots, args.arm)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8",
                        newline="\n")
    print(f"{args.arm}: all gated columns invariant = {result['all_gated_columns_invariant']}")
    if args.reference_roots:
        if args.compare_out is None:
            parser.error("--reference-roots needs --compare-out")
        comparison = compare(args.repo, args.roots, args.reference_roots, args.arm)
        args.compare_out.parent.mkdir(parents=True, exist_ok=True)
        args.compare_out.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
        print(f"{args.arm}: every table difference at gate off or sun rank 0 = "
              f"{comparison['every_difference_at_gate_off_or_sun_rank_0']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
