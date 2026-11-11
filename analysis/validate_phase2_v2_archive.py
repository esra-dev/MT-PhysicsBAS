#!/usr/bin/env python3
"""Validate corrected Phase-2 (protocol phase2-v2) per-seed data before inference.

Layout expected under <root> (the downloaded phase2-consolidated artifact):
  recovery_root/seed<N>/recovery_stereotypes_<bool>_<profile>.csv
  recovery_root/seed<N>/metrics_adapted_stereotypes_<bool>_<profile>.csv
  recovery_root/seed<N>/ADAPT_OK_stereotypes_<bool>_<profile>.json
  _artifacts/clean/clean-<parent>-stereo-<bool>-seed-<N>/**/TRAINING_OK.json

Every adapt cell must carry an ADAPT_OK gate manifest (see
docs/audit/gate_manifest_schema.md) whose scenario schedule matches the
committed scenario file, and a recovery row stamped by fault-detector-v2 under
protocol phase2-v2. Paired arms must share the scenario schedule. Parent
training cells must carry protocol phase1-v2 TRAINING_OK manifests with zero
scenario fallbacks.

Treatment-delivery gate (round-2 audit R2-001/R2-002, 2026-11): the schedule
hash covers scenario IDs only, so a pinned-sun scenario file derived from its
parent hashes identically. Manifests written since 2026-11 additionally carry
``scenario_file_sha256``, ``scenario_sunshine_values`` and
``lowsun_pin_delivered``; whenever present they are checked against the
committed scenario file. With ``require_treatment_delivery=True`` (CLI
``--require-treatment-delivery``) every ``*_lowsun`` cell MUST carry those keys
and MUST have been started from a schedule whose every scenario pins
``Sunshine = 100``. The 2026-07 runs of record fail that stricter gate by
construction (their low-sun manipulation was not delivered), which is why the
default stays permissive for the historical reproducers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "phase2-v2"
DETECTOR = "fault-detector-v2"
METRIC_SCHEMA = "phase2-recovery-v2"
PARENT_PROTOCOL = "phase1-v2"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if row and not next(iter(row.values()), "").startswith("#")]


def _schedule(scenario_rel: str) -> tuple[list[int], str]:
    rows = _json(SOURCE_ROOT / scenario_rel)
    ids = [int(row["id"]) for row in rows if isinstance(row, dict) and "id" in row]
    digest = hashlib.sha256(",".join(str(i) for i in ids).encode("utf-8")).hexdigest()
    return ids, digest


LOWSUN_LUX = 100.0


def _treatment(scenario_rel: str) -> tuple[str, list[float]]:
    """(file SHA-256, sorted unique Sunshine values) of a committed scenario file."""
    path = SOURCE_ROOT / scenario_rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = _json(path)
    values = sorted({float(row["Sunshine"]) for row in rows
                     if isinstance(row, dict) and "id" in row and "Sunshine" in row})
    return digest, values


def _is_lowsun(profile: str) -> bool:
    return profile.endswith("_lowsun")


def _schedule_and_treatment(scenario_rel: str) -> tuple[list[int], str, str, list[float]]:
    """(ordered ids, schedule hash, file hash, sorted Sunshine values)."""
    ids, schedule_hash = _schedule(scenario_rel)
    file_hash, sun = _treatment(scenario_rel)
    return ids, schedule_hash, file_hash, sun


def _config():
    return json.loads((SOURCE_ROOT / "config" / "run_config.json")
                      .read_text(encoding="utf-8-sig"))


def validate(root: Path, profiles: list[str], seeds: list[int],
             require_parents: bool = True,
             require_treatment_delivery: bool = False) -> list[str]:
    errors: list[str] = []
    cfg = _config()["phase2"]
    scenario_map = cfg.get("train_scenarios_map", {})
    parent_map = cfg.get("parent_profile", {})

    for seed in seeds:
        seed_root = root / "recovery_root" / f"seed{seed}"
        if not seed_root.is_dir():
            errors.append(f"missing seed root: {seed_root}")
            continue
        for profile in profiles:
            scenario_rel = scenario_map.get(profile)
            if not scenario_rel:
                errors.append(f"config phase2.train_scenarios_map has no entry for {profile}")
                continue
            config_rel = scenario_rel
            _, _, _, config_sun = _schedule_and_treatment(config_rel)
            if require_treatment_delivery and _is_lowsun(profile) \
                    and config_sun != [LOWSUN_LUX]:
                errors.append(f"{config_rel}: low-sun profile {profile} maps to a "
                              f"schedule with Sunshine values {config_sun}; every "
                              f"scenario must pin {LOWSUN_LUX:g}")
            arm_hash: dict[str, str] = {}
            for bool_name, mode in (("true", "ql_true"), ("false", "ql_false")):
                cell = f"stereotypes_{bool_name}_{profile}"
                manifest_path = seed_root / f"ADAPT_OK_{cell}.json"
                recovery_path = seed_root / f"recovery_{cell}.csv"
                metrics_path = seed_root / f"metrics_adapted_{cell}.csv"
                if not manifest_path.is_file():
                    errors.append(f"missing gate manifest: {manifest_path}")
                    continue
                manifest = _json(manifest_path)
                has_evidence = "scenario_file_sha256" in manifest
                # Which committed scenario file must this cell match? Manifests
                # carrying treatment-delivery evidence (2026-11+) and every cell
                # under the strict gate must match the CURRENT config map. Legacy
                # manifests are matched against the committed file they recorded,
                # so the 2026-07 archives (whose *_lowsun cells recorded the
                # parent's mixed-sun schedule) keep reproducing under the default
                # gate while remaining honestly classified as undelivered.
                scenario_rel = config_rel
                if not has_evidence and not require_treatment_delivery:
                    recorded = manifest.get("train_scenarios_file")
                    if recorded and (SOURCE_ROOT / recorded).is_file():
                        scenario_rel = recorded
                try:
                    declared_ids, declared_hash, declared_file_hash, declared_sun = \
                        _schedule_and_treatment(scenario_rel)
                except (OSError, ValueError, KeyError) as exc:
                    errors.append(f"{manifest_path}: cannot read scenario file "
                                  f"{scenario_rel}: {exc}")
                    continue
                for key, expected in (
                    ("status", "ok"),
                    ("protocol_version", PROTOCOL),
                    ("detector_version", DETECTOR),
                    ("metric_schema", METRIC_SCHEMA),
                    ("settled_start_state", True),
                    ("scenario_fallback_count", 0),
                    ("profile", profile),
                    ("mode", mode),
                    ("run_seed", seed),
                    ("train_scenarios_file", scenario_rel),
                    ("scenario_schedule_sha256", declared_hash),
                ):
                    if manifest.get(key) != expected:
                        errors.append(f"{manifest_path}: {key}={manifest.get(key)!r}, "
                                      f"expected {expected!r}")
                if [int(v) for v in manifest.get("ordered_scenario_ids", [])] != declared_ids:
                    errors.append(f"{manifest_path}: ordered_scenario_ids differ from "
                                  f"{scenario_rel}")
                if not manifest.get("parent_qtable_sha256"):
                    errors.append(f"{manifest_path}: empty parent_qtable_sha256 (cold start?)")
                arm_hash[bool_name] = manifest.get("scenario_schedule_sha256", "")

                # Treatment-delivery evidence (present on manifests since 2026-11).
                if require_treatment_delivery and _is_lowsun(profile) and not has_evidence:
                    errors.append(f"{manifest_path}: low-sun cell without treatment-delivery "
                                  "evidence (scenario_file_sha256/scenario_sunshine_values/"
                                  "lowsun_pin_delivered); the low-sun manipulation cannot be "
                                  "shown to have been delivered")
                if has_evidence:
                    if manifest.get("scenario_file_sha256") != declared_file_hash:
                        errors.append(f"{manifest_path}: scenario_file_sha256 differs from the "
                                      f"committed {scenario_rel}")
                    recorded_sun = sorted(float(v) for v in
                                          manifest.get("scenario_sunshine_values", []))
                    if recorded_sun != declared_sun:
                        errors.append(f"{manifest_path}: scenario_sunshine_values={recorded_sun} "
                                      f"differ from the committed file's {declared_sun}")
                    if _is_lowsun(profile):
                        delivered = manifest.get("lowsun_pin_delivered")
                        if delivered is not True or recorded_sun != [LOWSUN_LUX]:
                            errors.append(f"{manifest_path}: low-sun pin NOT delivered "
                                          f"(lowsun_pin_delivered={delivered!r}, "
                                          f"Sunshine values {recorded_sun})")
                    elif manifest.get("lowsun_pin_delivered") is not None:
                        errors.append(f"{manifest_path}: lowsun_pin_delivered set on a "
                                      "non-low-sun profile")

                if not recovery_path.is_file():
                    errors.append(f"missing recovery CSV: {recovery_path}")
                else:
                    rows = _csv_rows(recovery_path)
                    if not rows:
                        errors.append(f"{recovery_path}: no rows")
                    else:
                        last = rows[-1]
                        if last.get("DetectorVersion") != DETECTOR:
                            errors.append(f"{recovery_path}: DetectorVersion="
                                          f"{last.get('DetectorVersion')!r}")
                        if last.get("ProtocolVersion") != PROTOCOL:
                            errors.append(f"{recovery_path}: ProtocolVersion="
                                          f"{last.get('ProtocolVersion')!r}")
                        if "BlacklistEvents" not in last:
                            errors.append(f"{recovery_path}: missing BlacklistEvents column")

                if not metrics_path.is_file():
                    errors.append(f"missing adapt metrics: {metrics_path}")
                else:
                    expected_rows = manifest.get("adapt_episodes_effective")
                    actual_rows = len(_csv_rows(metrics_path))
                    if isinstance(expected_rows, int) and expected_rows != actual_rows:
                        errors.append(f"{metrics_path}: {actual_rows} episode rows, "
                                      f"manifest says {expected_rows}")

            if len(arm_hash) == 2 and arm_hash["true"] != arm_hash["false"]:
                errors.append(f"{seed_root}/{profile}: scenario schedules differ between arms")

            if require_parents:
                parent = parent_map.get(profile)
                if not parent:
                    errors.append(f"config phase2.parent_profile has no entry for {profile}")
                    continue
                for bool_name in ("true", "false"):
                    clean_dir = (root / "_artifacts" / "clean"
                                 / f"clean-{parent}-stereo-{bool_name}-seed-{seed}")
                    matches = list(clean_dir.glob("**/TRAINING_OK.json"))
                    if not matches:
                        errors.append(f"missing parent TRAINING_OK under {clean_dir}")
                        continue
                    parent_manifest = _json(matches[0])
                    if parent_manifest.get("protocol_version") != PARENT_PROTOCOL:
                        errors.append(f"{matches[0]}: parent protocol_version="
                                      f"{parent_manifest.get('protocol_version')!r}, "
                                      f"expected {PARENT_PROTOCOL!r}")
                    if parent_manifest.get("scenario_fallback_count") != 0:
                        errors.append(f"{matches[0]}: parent scenario_fallback_count != 0")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--profiles", required=True,
                        help="comma-separated adapt profiles archived in this run")
    parser.add_argument("--seeds", default="1-20",
                        help="seed range 'a-b' or comma list (default: %(default)s)")
    parser.add_argument("--no-parents", action="store_true",
                        help="skip parent TRAINING_OK checks (partial archives)")
    parser.add_argument("--require-treatment-delivery", action="store_true",
                        help="every *_lowsun cell must carry treatment-delivery evidence "
                             "showing Sunshine pinned to 100 in every scenario")
    args = parser.parse_args()
    profiles = [name.strip() for name in args.profiles.split(",") if name.strip()]
    if "-" in args.seeds and "," not in args.seeds:
        lo, hi = args.seeds.split("-", 1)
        seeds = list(range(int(lo), int(hi) + 1))
    else:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    errors = validate(args.root, profiles, seeds, require_parents=not args.no_parents,
                      require_treatment_delivery=args.require_treatment_delivery)
    if errors:
        print("Phase-2 v2 archive validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Phase-2 v2 archive validation passed "
          f"({len(seeds)} seeds x {len(profiles)} profiles x 2 arms).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
