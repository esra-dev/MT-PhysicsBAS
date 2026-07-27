#!/usr/bin/env python3
"""Validate an exact registered Phase-1b workflow dispatch.

Amendment A1 split each confirmatory mode into seed halves 1..10 and 11..20
because the original 280-cell training matrix exceeded GitHub's 256-job
limit. A valid dispatch therefore contains all seven Phase-1b profiles and
exactly one frozen seed block. Duplicate profile/seed tokens are rejected
before matrix materialisation, which also guarantees unique Cartesian cells.
"""

from __future__ import annotations

import argparse
import itertools


MODES = {
    "phase1b_v2_baseline",
    "phase1b_v2_redundancy_only",
    "phase1b_v2_kg_frozen",
    "phase1b_v2_extended",
}
PROFILES = {
    "labrel0",
    "labrel4",
    "labrel8",
    "labrel16",
    "labrel8s",
    "labband",
    "lab4chain3",
}
PILOT_SEEDS = set(range(1001, 1011))
CONFIRMATORY_SEED_BLOCKS = (set(range(1, 11)), set(range(11, 21)))


def _tokens(raw: str, label: str) -> list[str]:
    values = raw.split(",")
    if not values or any(value == "" for value in values):
        raise ValueError(f"{label} must be a non-empty comma-separated list")
    if any(value != value.strip() for value in values):
        raise ValueError(f"{label} tokens must not contain surrounding whitespace")
    if len(values) != len(set(values)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        raise ValueError(f"duplicate {label} token(s): {duplicates}")
    return values


def _seed_tokens(raw: str) -> list[int]:
    values = _tokens(raw, "seed")
    seeds: list[int] = []
    for value in values:
        if not value.isdecimal():
            raise ValueError(f"seed is not a non-negative integer: {value!r}")
        seeds.append(int(value))
    if len(seeds) != len(set(seeds)):
        duplicates = sorted({seed for seed in seeds if seeds.count(seed) > 1})
        raise ValueError(f"duplicate numeric seed(s): {duplicates}")
    return seeds


def _require_unique_tuples(label: str, rows: list[tuple]) -> None:
    if len(rows) != len(set(rows)):
        raise ValueError(f"duplicate {label} matrix tuple detected")


def validate_dispatch(mode: str, stage: str, profiles_raw: str,
                      seeds_raw: str) -> dict[str, int | str]:
    if mode not in MODES:
        raise ValueError(f"unregistered Phase-1b mode: {mode!r}")
    if stage not in {"pilot", "confirmatory"}:
        raise ValueError("phase1b_stage must be 'pilot' or 'confirmatory'")

    profiles = _tokens(profiles_raw, "profile")
    profile_set = set(profiles)
    if profile_set != PROFILES:
        raise ValueError(
            "Phase-1b profile set mismatch; "
            f"missing={sorted(PROFILES - profile_set)}, "
            f"extra={sorted(profile_set - PROFILES)}")

    seeds = _seed_tokens(seeds_raw)
    seed_set = set(seeds)
    if stage == "pilot":
        if seed_set != PILOT_SEEDS:
            raise ValueError(
                "pilot dispatch must contain exactly seeds 1001..1010")
        seed_block = "1001-1010"
    else:
        if seed_set == CONFIRMATORY_SEED_BLOCKS[0]:
            seed_block = "1-10"
        elif seed_set == CONFIRMATORY_SEED_BLOCKS[1]:
            seed_block = "11-20"
        else:
            raise ValueError(
                "confirmatory dispatch must contain exactly amendment-A1 "
                "seed block 1..10 or 11..20")

    train = list(itertools.product(profiles, ("true", "false"), seeds))
    benchmark = list(itertools.product(
        profiles, ("rule_based", "ql_false", "ql_true"), seeds))
    _require_unique_tuples("training", train)
    _require_unique_tuples("benchmark", benchmark)

    return {
        "mode": mode,
        "stage": stage,
        "seed_block": seed_block,
        "profiles": len(profiles),
        "seeds": len(seeds),
        "training_tuples": len(train),
        "benchmark_tuples": len(benchmark),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--seeds", required=True)
    args = parser.parse_args(argv)
    summary = validate_dispatch(
        args.mode, args.stage, args.profiles, args.seeds)
    print(
        "Phase-1b dispatch valid: "
        f"mode={summary['mode']} stage={summary['stage']} "
        f"seed_block={summary['seed_block']} "
        f"profiles={summary['profiles']} seeds={summary['seeds']} "
        f"train={summary['training_tuples']} "
        f"benchmark={summary['benchmark_tuples']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
