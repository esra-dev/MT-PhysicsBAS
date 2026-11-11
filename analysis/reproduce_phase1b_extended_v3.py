#!/usr/bin/env python3
"""Validate, stage and byte-reproduce the Phase-1b extended-KG re-execution.

Inputs:
  <campaign>     ``phase1b_extended_v3/`` — one or two seed-half ``run_<id>/``
                 archives of run_mode ``phase1b_v2_extended`` (2026-11, with
                 corrected property forwarding) plus the committed tables under
                 ``<campaign>/analysis/registered/``.
  --comparator   the 2026-07 ``phase1b_corrected/`` campaign WITH its raw
                 per-cell files (metrics, first-goal, benchmark CSVs, initial
                 Q-tables). Those raw files are gitignored, so the comparator
                 must be the locally archived copy (e.g.
                 ``.worktrees/phase1b-finish/phase1b_corrected``); its
                 ``SHA256SUMS.csv`` inventories are verified before use.

Gates (all fatal):
  - every extended archive passes the confirmatory Phase-1b gates PLUS the
    effective-props gate (every TRAINING_OK reports 2.0/5.0/2.0) PLUS the
    initial-Q divergence gate against the comparator's frozen archives;
  - comparator baseline/frozen (and redundancy, if present) archives pass the
    confirmatory gates and their SHA-256 inventories;
  - seed halves are disjoint and every mode's seed union is 1..20.
Then analysis/phase1b_extended_v3_family.py is re-run over the staged modes
and canonically byte-compared with the committed tables.

Usage:
  python analysis/reproduce_phase1b_extended_v3.py phase1b_extended_v3 \
      --comparator ../phase1b-finish/phase1b_corrected
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

try:
    from analysis import phase1b_extended_v3_family as family
    from analysis.phase1_archive_inventory import verify_inventory
    from analysis.reproduce_phase1_v2 import _compare
    from analysis.reproduce_phase1b import _stage_mode_root, _workflow_seeds
    from analysis.validate_phase1b_archive import MODE_EXTENDED, validate
except ImportError:  # executed as a script from the repo root
    import phase1b_extended_v3_family as family  # type: ignore
    from phase1_archive_inventory import verify_inventory  # type: ignore
    from reproduce_phase1_v2 import _compare  # type: ignore
    from reproduce_phase1b import _stage_mode_root, _workflow_seeds  # type: ignore
    from validate_phase1b_archive import MODE_EXTENDED, validate  # type: ignore


MODE_FROZEN = "phase1b_v2_kg_frozen"
MODE_BASELINE = "phase1b_v2_baseline"
COMPARATOR_MODES = (MODE_BASELINE, MODE_FROZEN)
REGISTERED_TABLES = ("phase1b_extended_v3_registered_family.csv",
                     "phase1b_extended_v3_primitives.csv")
REGISTERED_SEEDS = tuple(range(1, 21))


def _discover(campaign: Path, wanted: tuple[str, ...]) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for provenance in sorted(campaign.glob("run_*/analysis/out/workflow_inputs.json")):
        mode = json.loads(provenance.read_text(encoding="utf-8-sig"))["run_mode"]
        if mode in wanted:
            found.setdefault(mode, []).append(provenance.parents[2])
    for mode in wanted:
        halves = found.get(mode, [])
        if not 1 <= len(halves) <= 2:
            raise ValueError(f"{campaign}: expected one or two {mode} archives, found {len(halves)}")
    return found


def _check_seed_union(mode: str, halves: list[Path]) -> None:
    union: list[int] = []
    for half in halves:
        seeds = _workflow_seeds(half)
        if set(union) & set(seeds):
            raise ValueError(f"{mode}: seed halves overlap")
        union.extend(seeds)
    if tuple(sorted(union)) != REGISTERED_SEEDS:
        raise ValueError(f"{mode}: seed union {sorted(union)} != registered 1..20")


def reproduce(campaign: Path, comparator: Path, work: Path) -> None:
    extended = _discover(campaign, (MODE_EXTENDED,))[MODE_EXTENDED]
    comparator_archives = _discover(comparator, COMPARATOR_MODES)
    frozen = comparator_archives[MODE_FROZEN]

    for mode, halves in comparator_archives.items():
        _check_seed_union(mode, halves)
        for half in halves:
            errors = validate(half, stage="confirmatory")
            if errors:
                raise ValueError(f"comparator {mode} {half} failed gates:\n" + "\n".join(errors))
            inventory = half / "SHA256SUMS.csv"
            if not inventory.is_file():
                raise ValueError(f"comparator {half}: missing SHA256SUMS.csv")
            errors = verify_inventory(half, inventory)
            if errors:
                raise ValueError(f"comparator {half} inventory failed:\n" + "\n".join(errors))
            print(f"comparator {mode} {half.name}: gates + inventory pass")

    _check_seed_union(MODE_EXTENDED, extended)
    for half in extended:
        errors = validate(half, stage="confirmatory", require_effective_props=True,
                          divergence_against=frozen)
        if errors:
            raise ValueError(f"extended {half} failed gates:\n" + "\n".join(errors))
        inventory = half / "SHA256SUMS.csv"
        if inventory.is_file():
            errors = verify_inventory(half, inventory)
            if errors:
                raise ValueError(f"extended {half} inventory failed:\n" + "\n".join(errors))
        print(f"extended {half.name}: gates (effective props, initial-Q divergence) pass")

    roots = work / "modes"
    for half in extended:
        _stage_mode_root(half, roots / MODE_EXTENDED)
    for mode, halves in comparator_archives.items():
        for half in halves:
            _stage_mode_root(half, roots / mode)

    rebuilt = work / "registered"
    family.run([roots], rebuilt)
    for name in REGISTERED_TABLES:
        _compare(campaign / "analysis" / "registered" / name, rebuilt / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path, nargs="?", default=Path("phase1b_extended_v3"))
    parser.add_argument("--comparator", type=Path, required=True,
                        help="2026-07 phase1b_corrected campaign with raw per-cell files")
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        reproduce(args.campaign, args.comparator, args.work_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="phase1b-ext-v3-") as temp:
            reproduce(args.campaign, args.comparator, Path(temp))
    print("All Phase-1b extended v3 registered tables are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
