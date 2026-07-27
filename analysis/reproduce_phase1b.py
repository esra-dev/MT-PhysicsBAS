#!/usr/bin/env python3
"""Rebuild and byte-compare the Phase-1b registered result tables.

Mirrors ``analysis/reproduce_phase1_v2.py``: discover the run archives under
a campaign directory, validate each with the confirmatory-stage Phase-1b
gates, verify the SHA-256 inventory when one is present, re-run
``analysis/phase1b_report.py`` over the four mode roots into a scratch
directory using its explicit historical-serialization switch, and
canonically byte-compare the rebuilt
``phase1b_registered_family.csv`` and ``phase1b_supporting.csv`` against the
committed tables in ``<campaign>/analysis/registered/``.

The switch preserves the archive's original blank M1-M4 direction metadata
and its superseded final-rank overshoot proxy solely for byte verification.
Normal report output contains the registered directions and marks the actual
within-episode overshoot event outcome as unmeasured. No statistic changes.

Seed-half amendment (2026-07-26, dispatch record amendment A1): the
registered 280-cell train matrix (7 profiles x 2 arms x 20 seeds) exceeds
the CI platform's 256-jobs-per-matrix limit, so each mode is dispatched as
TWO seed-half runs (1-10 and 11-20), mirroring the established Phase-4
two-seed-halves convention. Discovery therefore accepts ONE OR TWO archives
per mode; a mode's halves must have disjoint seed sets, every mode's seed
UNION must be identical, and staging refuses colliding results_seed trees.
More than two archives for a mode remains fatal.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from analysis.phase1_archive_inventory import verify_inventory
    from analysis.reproduce_phase1_v2 import _canonical_csv_bytes, _compare
    from analysis.validate_phase1b_archive import validate
except ImportError:  # executed as a script from the repo root
    from phase1_archive_inventory import verify_inventory  # type: ignore
    from reproduce_phase1_v2 import _canonical_csv_bytes, _compare  # type: ignore
    from validate_phase1b_archive import validate  # type: ignore

__all__ = ["reproduce", "_discover", "_canonical_csv_bytes", "_compare"]

REQUIRED_MODES = {
    "phase1b_v2_baseline",
    "phase1b_v2_redundancy_only",
    "phase1b_v2_kg_frozen",
    "phase1b_v2_extended",
}
REGISTERED_TABLES = (
    "phase1b_registered_family.csv",
    "phase1b_supporting.csv",
)
REPORT_SCRIPT = Path(__file__).resolve().parent / "phase1b_report.py"


def _discover(campaign: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for provenance in sorted(campaign.glob("*/analysis/out/workflow_inputs.json")):
        payload = json.loads(provenance.read_text(encoding="utf-8"))
        mode = payload["run_mode"]
        found.setdefault(mode, []).append(provenance.parents[2])
    for mode, archives in found.items():
        if len(archives) > 2:
            raise ValueError(
                f"duplicate archive for {mode}: {len(archives)} runs found; "
                "at most two seed-half runs are registered per mode")
    missing = REQUIRED_MODES - set(found)
    extra = set(found) - REQUIRED_MODES
    if missing or extra:
        raise ValueError(f"archive modes mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    return found


def _workflow_seeds(archive: Path) -> list[int]:
    payload = json.loads((archive / "analysis/out/workflow_inputs.json")
                         .read_text(encoding="utf-8"))
    return sorted(int(seed) for seed in payload["seeds"])


def _link_or_copy(source: Path, target: Path) -> None:
    if target.exists():
        raise ValueError(
            f"staging collision at {target}: two archives supplied the same "
            "results_seed tree (overlapping seed halves?)")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def _stage_mode_root(archive: Path, mode_root: Path) -> None:
    """Expose one run archive under its mode name for phase1b_report.py.

    The report resolves cells as <root>/<mode>/[benchmark/]results_seed<N>/,
    while run archives are named run_<id>/, so the results_seed trees are
    hard-linked (copied when linking is impossible) into a mode-named root.
    """
    staged = False
    for parent, destination in ((archive / "benchmark", mode_root / "benchmark"),
                                (archive, mode_root)):
        if not parent.is_dir():
            continue
        for seed_dir in sorted(parent.glob("results_seed*")):
            if not seed_dir.is_dir():
                continue
            staged = True
            for source in sorted(path for path in seed_dir.rglob("*")
                                 if path.is_file()):
                _link_or_copy(source,
                              destination / seed_dir.name
                              / source.relative_to(seed_dir))
    if not staged:
        raise ValueError(f"no results_seed directories found under {archive}")


def reproduce(campaign: Path, work: Path,
              rmst_horizon: int | None = None) -> None:
    archives = _discover(campaign)

    seeds_by_mode: dict[str, tuple[int, ...]] = {}
    for mode, halves in sorted(archives.items()):
        union: list[int] = []
        for archive in halves:
            errors = validate(archive, stage="confirmatory")
            if errors:
                raise ValueError(f"{mode} archive validation failed:\n" + "\n".join(errors))
            half_seeds = _workflow_seeds(archive)
            overlap = set(union) & set(half_seeds)
            if overlap:
                raise ValueError(
                    f"{mode}: seed halves overlap on {sorted(overlap)}")
            union.extend(half_seeds)
            # Verify ONLY the curation-time root inventory. The archive may
            # also carry the workflow's own analysis/out/SHA256SUMS.csv,
            # whose paths are relative to the CI runner's tree, not the
            # archive root — that file is itself hash-covered by the root
            # inventory, which preserves its evidentiary value without
            # re-interpreting its paths.
            inventory = archive / "SHA256SUMS.csv"
            if inventory.is_file():
                errors = verify_inventory(archive, inventory)
                if errors:
                    raise ValueError(f"{mode} inventory failed:\n" + "\n".join(errors))
        seeds_by_mode[mode] = tuple(sorted(union))
    if len(set(seeds_by_mode.values())) != 1:
        raise ValueError(f"seed blocks differ across modes: {seeds_by_mode}")

    roots = work / "modes"
    for mode, halves in sorted(archives.items()):
        for archive in halves:
            _stage_mode_root(archive, roots / mode)

    rebuilt = work / "registered"
    command = [
        sys.executable, str(REPORT_SCRIPT),
        "--roots", str(roots),
        "--out", str(rebuilt),
        "--legacy-archive-format",
    ]
    if rmst_horizon is not None:
        command += ["--rmst-horizon", str(rmst_horizon)]
    subprocess.run(command, check=True)

    expected_registered = campaign / "analysis/registered"
    for filename in REGISTERED_TABLES:
        _compare(expected_registered / filename, rebuilt / filename)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--rmst-horizon", type=int, default=None,
                        help="passed through to phase1b_report.py (default: "
                             "its frozen 3000 // scenario_count horizon)")
    args = parser.parse_args()
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        reproduce(args.campaign, args.work_dir, rmst_horizon=args.rmst_horizon)
    else:
        with tempfile.TemporaryDirectory(prefix="phase1b-reproduce-") as temp:
            reproduce(args.campaign, Path(temp),
                      rmst_horizon=args.rmst_horizon)
    print("All Phase-1b registered result tables are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
