#!/usr/bin/env python3
"""Registered analysis of the Phase-2 structure-only fault-detection campaign
(campaign ``phase2_v3_structonly``, 2026-11-14).

Registered in docs/phase2_structonly_registration_2026-11-14.md. The campaign
re-runs four archived fault cells with the adaptation step's knowledge layer
switched to BRICK (building structure without the Elementary physics layer) in
BOTH arms, and compares each (cell, arm) series against the SAME cell and arm
in the full-layer runs of record, paired by seed:

- the comparator for ``lab2_f1bdead`` and ``lab3_f1bdead`` is the 2026-07
  corrected campaign (``phase2_v2_corrected/run_*``, head 19f4f3ff);
- the comparator for ``lab3_f2dead_lowsun`` and ``labmon2_f2dead_lowsun`` is
  the delivered low-sun re-execution (``phase2_v3_lowsun/run_43099277363``,
  head 77e7791f) — NOT the superseded mixed-sun rows of the corrected
  campaign.

Three frozen m=8 families (4 cells x 2 arms), BH within each family:
  - WrongBlameEvents (PRIMARY, registered prediction): the number of
    BlacklistEvents entries in the LAST recovery row that name a component
    OTHER than the injected fault(s). No censoring; a missing/empty
    BlacklistEvents field counts 0.
  - DetectEpisode: censored at adapt_episodes_effective + 1 as in the
    corrected campaign (never-detected kept, never dropped).
  - RecoveryEpisodes: same censoring rule.

Paired difference = structonly − record per seed; two-sided exact sign-flip
test, exact sign test, paired rank-biserial, fixed-seed 10,000-draw bootstrap
CI (base seed 20261114; distinct stream per family and member); no p/q can be
zero.

Usage:
  python analysis/phase2_structonly_v3_family.py \
      --structonly-roots phase2_v3_structonly/run_<id> [...] \
      --record-base . \
      --out phase2_v3_structonly/analysis/registered
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import phase2_v2_registered_family as base
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps  # type: ignore
    import phase2_v2_registered_family as base  # type: ignore


SEEDS = base.SEEDS  # 1..20, frozen
ARMS = (("true", "ql_true"), ("false", "ql_false"))
STRUCTONLY_CELLS = (
    "lab2_f1bdead", "lab3_f1bdead", "lab3_f2dead_lowsun", "labmon2_f2dead_lowsun",
)

# Frozen comparator mapping: the archive roots (relative to --record-base) that
# hold each cell's FULL-layer run of record. The low-sun cells map ONLY to the
# delivered low-sun campaign so the superseded mixed-sun rows of the corrected
# campaign can never be loaded by mistake (the loader fails on != 1 match).
RECORD_ROOTS = {
    "lab2_f1bdead": (
        "phase2_v2_corrected/run_30001857104", "phase2_v2_corrected/run_30001867521",
        "phase2_v2_corrected/run_30001878310", "phase2_v2_corrected/run_30001888910",
    ),
    "lab3_f1bdead": (
        "phase2_v2_corrected/run_30001857104", "phase2_v2_corrected/run_30001867521",
        "phase2_v2_corrected/run_30001878310", "phase2_v2_corrected/run_30001888910",
    ),
    "lab3_f2dead_lowsun": ("phase2_v3_lowsun/run_43099277363",),
    "labmon2_f2dead_lowsun": ("phase2_v3_lowsun/run_43099277363",),
}

# Frozen ground truth: the component(s) the faulty flow actually breaks
# (simulator/generate_faulty_flows.ps1). Matched against the URI fragment of
# each BlacklistEvents entry; every other blacklisted component is a WRONG
# blame of a healthy component.
INJECTED_COMPONENTS = {
    "lab2_f1bdead": ("SetZ1Blinds",),
    "lab3_f1bdead": ("SetZ1Blinds",),
    "lab3_f2dead_lowsun": ("SetZ1Light", "SetZ2Light"),
    "labmon2_f2dead_lowsun": ("SetZ1Light", "SetZ2Light"),
}

BOOTSTRAP_ITERS = 10_000
BOOTSTRAP_BASE_SEED = 20261114
Q_FIELD = "q_signflip_bh_m8"

FIELDS = [
    "registered_cell", "arm", "metric", "n_paired", "seeds_paired",
    "mean_structonly", "mean_record", "mean_paired_difference",
    "median_paired_difference", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided", "p_sign_exact_two_sided", "paired_rank_biserial",
    Q_FIELD, "bh_family_m", "censored_structonly", "censored_record",
]

PRIMITIVE_FIELDS = [
    "registered_cell", "arm", "seed", "source", "DefectComponent",
    "DetectEpisode", "ReconvergeEpisode", "RecoveryEpisodes",
    "WrongBlameEvents", "BlacklistEvents", "BestEffortRank", "RankShortfall",
    "DegradedMode", "adapt_episodes_effective", "knowledge_layer",
    "knowledge_layer_delivered", "scenario_file_sha256", "lowsun_pin_delivered",
]


def _fragment(token: str) -> str:
    """URI fragment of a blacklist-event component ('...#SetZ1Blinds' -> 'SetZ1Blinds')."""
    return token.split("#")[-1].split("/")[-1]


def wrong_blame_count(blacklist_events: str | None, injected: tuple[str, ...]) -> int:
    """Number of 'uri@episode' entries naming a component outside ``injected``."""
    if not blacklist_events:
        return 0
    count = 0
    for event in blacklist_events.split(";"):
        event = event.strip()
        if not event:
            continue
        component = _fragment(event.split("@", 1)[0].strip())
        if component not in injected:
            count += 1
    return count


def _resolve(roots: list[Path], profile: str, bool_name: str, seed: int) -> Path:
    name = f"stereotypes_{bool_name}_{profile}"
    matches = [root / "recovery_root" / f"seed{seed}" / f"recovery_{name}.csv"
               for root in roots]
    matches = [m for m in matches if m.is_file()]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one recovery file for {profile}/{bool_name}/"
                         f"seed{seed}; found {len(matches)}: {[str(m) for m in matches]}")
    return matches[0]


def _last_row_and_manifest(roots: list[Path], profile: str, bool_name: str,
                           seed: int) -> tuple[dict, dict]:
    recovery_path = _resolve(roots, profile, bool_name, seed)
    rows = base._csv_rows(recovery_path)
    if not rows:
        raise SystemExit(f"{recovery_path}: no recovery rows")
    manifest_path = recovery_path.parent / f"ADAPT_OK_stereotypes_{bool_name}_{profile}.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing gate manifest for {recovery_path}")
    return rows[-1], base._json(manifest_path)


def _outcome(roots: list[Path], profile: str, bool_name: str, seed: int,
             metric: str) -> tuple[float, bool]:
    """(value, censored) for one record under the frozen estimand rules."""
    last, manifest = _last_row_and_manifest(roots, profile, bool_name, seed)
    if metric == "WrongBlameEvents":
        return float(wrong_blame_count(last.get("BlacklistEvents", ""),
                                       INJECTED_COMPONENTS[profile])), False
    value = int(last[metric])
    if value < 0:
        return float(int(manifest["adapt_episodes_effective"]) + 1), True
    return float(value), False


def _record_roots(record_base: Path, profile: str) -> list[Path]:
    roots = [record_base / rel for rel in RECORD_ROOTS[profile]]
    missing = [str(root) for root in roots if not root.is_dir()]
    if missing:
        raise SystemExit(f"missing comparator archive root(s) for {profile}: {missing}")
    return roots


def _family_rows(structonly_roots: list[Path], record_base: Path, metric: str,
                 family_index: int) -> list[dict]:
    rows: list[dict] = []
    p_values: list[float] = []
    member_index = 0
    for profile in STRUCTONLY_CELLS:
        for bool_name, arm in ARMS:
            struct_vals, record_vals = [], []
            censored_struct = censored_record = 0
            for seed in SEEDS:
                value, censored = _outcome(structonly_roots, profile, bool_name,
                                           seed, metric)
                struct_vals.append(value)
                censored_struct += int(censored)
                value, censored = _outcome(_record_roots(record_base, profile),
                                           profile, bool_name, seed, metric)
                record_vals.append(value)
                censored_record += int(censored)
            diffs = [a - b for a, b in zip(struct_vals, record_vals)]
            mean_diff = sum(diffs) / len(diffs)
            rng = random.Random(BOOTSTRAP_BASE_SEED + family_index * 100 + member_index)
            boots = []
            for _ in range(BOOTSTRAP_ITERS):
                sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
                boots.append(sum(sample) / len(sample))
            boots.sort()
            ci_lo = boots[int(0.025 * BOOTSTRAP_ITERS)]
            ci_hi = boots[min(BOOTSTRAP_ITERS - 1, int(0.975 * BOOTSTRAP_ITERS))]
            p = eps.paired_signflip_p(struct_vals, record_vals)
            p_values.append(p)
            rows.append({
                "registered_cell": profile,
                "arm": arm,
                "metric": metric,
                "n_paired": len(diffs),
                "seeds_paired": ";".join(str(s) for s in SEEDS),
                "mean_structonly": sum(struct_vals) / len(struct_vals),
                "mean_record": sum(record_vals) / len(record_vals),
                "mean_paired_difference": mean_diff,
                "median_paired_difference": eps.median(diffs),
                "ci_lo_bootstrap": ci_lo,
                "ci_hi_bootstrap": ci_hi,
                "p_signflip_two_sided": p,
                "p_sign_exact_two_sided": eps.exact_sign_p(struct_vals, record_vals),
                "paired_rank_biserial": eps.paired_rank_biserial(struct_vals, record_vals),
                "bh_family_m": len(STRUCTONLY_CELLS) * len(ARMS),
                "censored_structonly": censored_struct,
                "censored_record": censored_record,
            })
            member_index += 1
    for row, q in zip(rows, eps.bh_qvalues(p_values)):
        row[Q_FIELD] = q
    return rows


def _primitives(structonly_roots: list[Path], record_base: Path) -> list[dict]:
    rows: list[dict] = []
    for profile in STRUCTONLY_CELLS:
        for bool_name, arm in ARMS:
            for seed in SEEDS:
                for source, roots in (("structonly", structonly_roots),
                                      ("record", _record_roots(record_base, profile))):
                    last, manifest = _last_row_and_manifest(roots, profile,
                                                            bool_name, seed)
                    row = {
                        "registered_cell": profile, "arm": arm, "seed": seed,
                        "source": source,
                        "WrongBlameEvents": wrong_blame_count(
                            last.get("BlacklistEvents", ""),
                            INJECTED_COMPONENTS[profile]),
                        "adapt_episodes_effective": manifest.get("adapt_episodes_effective"),
                        "knowledge_layer": manifest.get("knowledge_layer", ""),
                        "knowledge_layer_delivered": manifest.get("knowledge_layer_delivered", ""),
                        "scenario_file_sha256": manifest.get("scenario_file_sha256", ""),
                        "lowsun_pin_delivered": manifest.get("lowsun_pin_delivered", ""),
                    }
                    for key in PRIMITIVE_FIELDS:
                        if key in last and key not in row:
                            row[key] = last[key]
                    rows.append(row)
    return rows


def _write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def run(structonly_roots: list[Path], record_base: Path, out_dir: Path) -> None:
    wrongblame = _family_rows(structonly_roots, record_base, "WrongBlameEvents", 0)
    detection = _family_rows(structonly_roots, record_base, "DetectEpisode", 1)
    recovery = _family_rows(structonly_roots, record_base, "RecoveryEpisodes", 2)
    _write(out_dir / "phase2_structonly_v3_wrongblame_family.csv", wrongblame, FIELDS)
    _write(out_dir / "phase2_structonly_v3_detection_family.csv", detection, FIELDS)
    _write(out_dir / "phase2_structonly_v3_recovery_family.csv", recovery, FIELDS)
    _write(out_dir / "phase2_structonly_v3_per_seed.csv",
           _primitives(structonly_roots, record_base), PRIMITIVE_FIELDS)
    print(f"Wrote {len(wrongblame)} wrong-blame, {len(detection)} detection and "
          f"{len(recovery)} recovery rows plus the per-seed primitives to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structonly-roots", nargs="+", type=Path, required=True,
                        help="structure-only run archive roots (each containing recovery_root/)")
    parser.add_argument("--record-base", type=Path, default=Path("."),
                        help="directory against which the frozen comparator roots resolve "
                             "(default: the repository root)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.structonly_roots, args.record_base, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
