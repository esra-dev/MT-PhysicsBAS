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

Treatment-delivery gates (round-1 audit AUD-001, added 2026-11). The archived
2026-07 "extended" runs executed effective frozen KG because the three
extended knobs never reached the JVM. Two optional gates make that failure
mode detectable from the archive alone:

- ``require_effective_props``: every TRAINING_OK must carry
  ``stereo_effective_props`` (the knob values the JVM reported) equal to the
  mode's registered values — the ``phase1b_v2_extended`` overrides from
  config/run_config.json for the extended mode, all 0.0 for every other mode;
- ``divergence_against``: for the extended mode, the stereo-true initial
  Q-table of ``labrel16`` and ``labband`` must DIFFER byte-wise from the
  frozen-KG archive's table for the same seed (identical tables mean the
  extended treatment did nothing to the initial policy, as in 2026-07).
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
MODE_EXTENDED = "phase1b_v2_extended"
LABREL_PROFILES = ("labrel0", "labrel4", "labrel8", "labrel16")
PROFILES = LABREL_PROFILES + ("labrel8s", "labband", "lab4chain3")
# Knobs whose effective JVM values must be reported by every training cell.
EFFECTIVE_PROP_KEYS = ("stereo.irrelevantDvPrior", "stereo.bandMirrorInit",
                       "stereo.bandMirrorPrior")
# Profiles whose stereo-true initial Q-table MUST diverge between the extended
# and frozen modes (decoys classified EXPLICIT_OTHER_DV receive the irrelevance
# prior; labband receives the band-mirror init term).
DIVERGENCE_PROFILES = ("labrel16", "labband")
SOURCE_ROOT = Path(__file__).resolve().parents[1]
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


def registered_effective_props(mode: str) -> dict[str, float]:
    """Knob values a cell of ``mode`` must report (config-driven for extended)."""
    expected = {key: 0.0 for key in EFFECTIVE_PROP_KEYS}
    if mode == MODE_EXTENDED:
        config = json.loads((SOURCE_ROOT / "config" / "run_config.json")
                            .read_text(encoding="utf-8-sig"))
        overrides = config["profiles"][MODE_EXTENDED]["learning_overrides"]
        expected["stereo.irrelevantDvPrior"] = float(overrides["stereo_irrelevant_dv_prior"])
        expected["stereo.bandMirrorInit"] = float(overrides["stereo_band_mirror_init"])
        expected["stereo.bandMirrorPrior"] = float(overrides["stereo_band_mirror_prior"])
    return expected


def _check_effective_props(root: Path, mode: str, seeds: list[int],
                           errors: list[str]) -> None:
    expected = registered_effective_props(mode)
    for seed in seeds:
        for profile in PROFILES:
            for stereo in ("true", "false"):
                manifest_path = (root / "benchmark" / f"results_seed{seed}" / profile
                                 / f"training_stereo_{stereo}" / "TRAINING_OK.json")
                if not manifest_path.is_file():
                    continue  # absence is reported by the per-cell gates
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                effective = manifest.get("stereo_effective_props")
                if not isinstance(effective, dict):
                    errors.append(f"{manifest_path}: missing stereo_effective_props "
                                  "(treatment delivery not evidenced)")
                    continue
                for key, value in expected.items():
                    if key not in effective:
                        errors.append(f"{manifest_path}: stereo_effective_props lacks {key}")
                    elif float(effective[key]) != value:
                        errors.append(f"{manifest_path}: {key} effective "
                                      f"{effective[key]!r} != registered {value!r} "
                                      f"for {mode}")


def _initial_q(root: Path, seed: int, profile: str) -> Path:
    return (root / "benchmark" / f"results_seed{seed}" / profile
            / "training_stereo_true" / f"qtable_initial_stereotypes_true_{profile}.csv")


def _check_initial_q_divergence(root: Path, seeds: list[int],
                                frozen_roots: list[Path],
                                errors: list[str]) -> None:
    for seed in seeds:
        for profile in DIVERGENCE_PROFILES:
            mine = _initial_q(root, seed, profile)
            if not mine.is_file():
                errors.append(f"missing extended initial Q-table: {mine}")
                continue
            theirs = [path for path in (_initial_q(Path(f), seed, profile)
                                        for f in frozen_roots) if path.is_file()]
            if len(theirs) != 1:
                errors.append(f"expected exactly one frozen initial Q-table for seed {seed} "
                              f"{profile} under {frozen_roots}; found {len(theirs)}")
                continue
            if mine.read_bytes() == theirs[0].read_bytes():
                errors.append(f"{mine}: byte-identical to the frozen-KG table {theirs[0]} — "
                              "the extended treatment did not change the initial policy")


def validate(root: Path, seeds: list[int] | None = None,
             stage: str = "confirmatory",
             require_effective_props: bool = False,
             divergence_against: list[Path] | None = None) -> list[str]:
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
    mode = payload.get("run_mode") if payload else None
    if require_effective_props:
        if mode in MODES:
            _check_effective_props(root, mode, declared, errors)
        else:
            errors.append(f"{root}: cannot check effective props without a Phase-1b run_mode")
    if divergence_against:
        if mode != MODE_EXTENDED:
            errors.append(f"{root}: initial-Q divergence gate applies to {MODE_EXTENDED} "
                          f"archives only (run_mode={mode!r})")
        else:
            _check_initial_q_divergence(root, declared,
                                        [Path(p) for p in divergence_against], errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--stage", choices=STAGES, default="confirmatory")
    parser.add_argument("--seeds", default=None,
                        help="comma-separated expected seed list (default: "
                             "the workflow_inputs.json seeds)")
    parser.add_argument("--require-effective-props", action="store_true",
                        help="every TRAINING_OK must report the mode's registered "
                             "stereotype knob values (treatment-delivery gate)")
    parser.add_argument("--divergence-against", nargs="+", type=Path, default=None,
                        help="frozen-KG run archive(s); the extended archive's labrel16/"
                             "labband stereo-true initial Q-tables must differ per seed")
    args = parser.parse_args()
    seeds = None
    if args.seeds:
        seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    errors = validate(args.root, seeds=seeds, stage=args.stage,
                      require_effective_props=args.require_effective_props,
                      divergence_against=args.divergence_against)
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
