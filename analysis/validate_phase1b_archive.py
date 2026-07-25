#!/usr/bin/env python3
"""Validate a Phase-1b run archive before inference or publication.

A Phase-1b campaign archive (``phase1b_corrected/``) holds one
``run_<actions_run_id>/`` directory per dispatched arm.  Each run directory
contains ``analysis/out/workflow_inputs.json`` (written by
``analysis/write_workflow_provenance.py``) and
``benchmark/results_seed<N>/<profile>/...`` training + benchmark artifacts in
exactly the Phase-1 v2 file conventions.

This validator applies, per (seed, profile, stereo-arm) cell, the same
TRAINING_OK gates as ``analysis/validate_phase1_v2_archive.py`` (protocol
phase1-v2, 3000-episode fixed horizon, common-seed-v1 pairing, benchmark-v2
metric schema, zero scenario fallbacks, run_seed match, paired-arm schedule
identity, declared scenario cycling, first-goal presentation counts, v2
benchmark columns) and then adds the Phase-1b-specific invariants:

- workflow_inputs.json mode/seed consistency (a known Phase-1b run_mode, the
  registered profile set, seeds matching both the caller and the on-disk
  results_seed directories);
- labrel schedule identity: labrel0/4/8/16 share ONE master training schedule,
  so their scenario_schedule_sha256 must be identical within every seed;
- seed-block sanity by stage: pilot archives may only use seeds 1001..1010,
  confirmatory archives may only use seeds 1..40 and must never contain a
  pilot-block seed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from analysis.validate_phase1_v2_archive import validate as validate_v2_cells
except ImportError:  # executed as a script from the repo root
    from validate_phase1_v2_archive import validate as validate_v2_cells  # type: ignore


MODES = (
    "phase1b_v2_baseline",
    "phase1b_v2_redundancy_only",
    "phase1b_v2_kg_frozen",
    "phase1b_v2_extended",
)
LABREL_PROFILES = ("labrel0", "labrel4", "labrel8", "labrel16")
PROFILES = LABREL_PROFILES + ("labrel8s", "labband", "lab4chain3")
STAGES = ("pilot", "confirmatory")
PILOT_SEED_BLOCK = range(1001, 1011)
CONFIRMATORY_SEED_BLOCK = range(1, 41)


def _load_workflow_inputs(root: Path, errors: list[str]) -> dict | None:
    provenance = root / "analysis" / "out" / "workflow_inputs.json"
    if not provenance.is_file():
        errors.append(f"missing provenance: {provenance}")
        return None
    return json.loads(provenance.read_text(encoding="utf-8-sig"))


def _check_workflow_inputs(root: Path, payload: dict,
                           expected_seeds: list[int] | None,
                           errors: list[str]) -> list[int]:
    provenance = root / "analysis" / "out" / "workflow_inputs.json"
    mode = payload.get("run_mode")
    if mode not in MODES:
        errors.append(
            f"{provenance}: run_mode={mode!r} is not a Phase-1b mode {MODES}")
    profiles = payload.get("profiles")
    if profiles is not None and sorted(profiles) != sorted(PROFILES):
        errors.append(
            f"{provenance}: profiles={profiles!r}, expected the registered "
            f"Phase-1b set {sorted(PROFILES)}")
    seeds = [int(value) for value in payload.get("seeds", [])]
    if not seeds:
        errors.append(f"{provenance}: empty seeds list")
    if sorted(set(seeds)) != sorted(seeds):
        errors.append(f"{provenance}: duplicate seeds {seeds}")
    if expected_seeds is not None and sorted(seeds) != sorted(expected_seeds):
        errors.append(
            f"{provenance}: seeds={sorted(seeds)} != expected "
            f"{sorted(expected_seeds)}")
    return sorted(seeds)


def _check_seed_block(root: Path, seeds: list[int], stage: str,
                      errors: list[str]) -> None:
    provenance = root / "analysis" / "out" / "workflow_inputs.json"
    for seed in seeds:
        if stage == "pilot":
            if seed not in PILOT_SEED_BLOCK:
                errors.append(
                    f"{provenance}: seed {seed} outside the pilot block "
                    f"{PILOT_SEED_BLOCK.start}..{PILOT_SEED_BLOCK.stop - 1}")
        else:
            if seed in PILOT_SEED_BLOCK:
                errors.append(
                    f"{provenance}: pilot-block seed {seed} in a confirmatory "
                    "archive")
            elif seed not in CONFIRMATORY_SEED_BLOCK:
                errors.append(
                    f"{provenance}: seed {seed} outside the confirmatory "
                    f"block {CONFIRMATORY_SEED_BLOCK.start}.."
                    f"{CONFIRMATORY_SEED_BLOCK.stop - 1}")


def _check_seed_dirs(root: Path, seeds: list[int], errors: list[str]) -> None:
    bench_root = root / "benchmark"
    if not bench_root.is_dir():
        return  # the per-cell gates already report every missing seed root
    expected = {f"results_seed{seed}" for seed in seeds}
    actual = {entry.name for entry in bench_root.iterdir()
              if entry.is_dir() and entry.name.startswith("results_seed")}
    for name in sorted(actual - expected):
        errors.append(
            f"{bench_root / name}: seed directory not declared in "
            "workflow_inputs.json seeds")


def _read_manifest(root: Path, seed: int, profile: str) -> dict | None:
    """Prefer the stereo-true arm; paired-arm hash identity is gated separately."""
    for stereo in ("true", "false"):
        manifest = (root / "benchmark" / f"results_seed{seed}" / profile
                    / f"training_stereo_{stereo}" / "TRAINING_OK.json")
        if manifest.is_file():
            return json.loads(manifest.read_text(encoding="utf-8-sig"))
    return None


def _check_run_mode_consistency(root: Path, payload: dict, seeds: list[int],
                                errors: list[str]) -> None:
    mode = payload.get("run_mode")
    if mode not in MODES:
        return
    for seed in seeds:
        for profile in PROFILES:
            manifest = _read_manifest(root, seed, profile)
            if manifest is None or "run_mode" not in manifest:
                continue  # absence is reported by the per-cell gates
            if manifest["run_mode"] != mode:
                errors.append(
                    f"{root}/benchmark/results_seed{seed}/{profile}: "
                    f"TRAINING_OK run_mode={manifest['run_mode']!r} != "
                    f"workflow run_mode {mode!r}")


def _check_labrel_schedule_identity(root: Path, seeds: list[int],
                                    errors: list[str]) -> None:
    for seed in seeds:
        hashes: dict[str, str | None] = {}
        for profile in LABREL_PROFILES:
            manifest = _read_manifest(root, seed, profile)
            if manifest is not None:
                hashes[profile] = manifest.get("scenario_schedule_sha256")
        if len(hashes) >= 2 and len(set(hashes.values())) > 1:
            detail = ", ".join(f"{profile}={value}"
                               for profile, value in sorted(hashes.items()))
            errors.append(
                f"{root}/benchmark/results_seed{seed}: labrel rungs do not "
                f"share one master scenario schedule ({detail})")


def validate(root: Path, seeds: list[int] | None = None,
             stage: str = "confirmatory") -> list[str]:
    """Return every gate violation for one Phase-1b run archive (empty = pass)."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}, got {stage!r}")
    root = Path(root)
    errors: list[str] = []
    payload = _load_workflow_inputs(root, errors)
    if payload is None:
        if seeds is None:
            return errors  # nothing further can be checked without a seed list
        declared = sorted(int(seed) for seed in seeds)
    else:
        declared = _check_workflow_inputs(root, payload, seeds, errors)
        if seeds is not None:
            declared = sorted(int(seed) for seed in seeds)
    _check_seed_block(root, declared, stage, errors)
    _check_seed_dirs(root, declared, errors)
    # Per (seed, profile, stereo-arm) cells: the SAME gates as Phase-1 v2,
    # including paired-arm scenario_schedule_sha256 identity per profile.
    errors.extend(validate_v2_cells(root, expected_seeds=declared,
                                    labs=PROFILES))
    if payload is not None:
        _check_run_mode_consistency(root, payload, declared, errors)
    _check_labrel_schedule_identity(root, declared, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--stage", choices=STAGES, default="confirmatory")
    parser.add_argument("--seeds", default=None,
                        help="comma-separated expected seed list (default: "
                             "the workflow_inputs.json seeds)")
    args = parser.parse_args()
    seeds = None
    if args.seeds:
        seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    errors = validate(args.root, seeds=seeds, stage=args.stage)
    if errors:
        print(f"Phase-1b archive validation FAILED ({args.stage}):")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Phase-1b archive validation passed ({args.stage}, "
          f"{len(PROFILES)} profiles).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
