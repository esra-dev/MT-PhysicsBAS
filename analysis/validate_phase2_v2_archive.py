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


def _config():
    return json.loads((SOURCE_ROOT / "config" / "run_config.json")
                      .read_text(encoding="utf-8-sig"))


def validate(root: Path, profiles: list[str], seeds: list[int],
             require_parents: bool = True) -> list[str]:
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
            declared_ids, declared_hash = _schedule(scenario_rel)
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
    args = parser.parse_args()
    profiles = [name.strip() for name in args.profiles.split(",") if name.strip()]
    if "-" in args.seeds and "," not in args.seeds:
        lo, hi = args.seeds.split("-", 1)
        seeds = list(range(int(lo), int(hi) + 1))
    else:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    errors = validate(args.root, profiles, seeds, require_parents=not args.no_parents)
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
