#!/usr/bin/env python3
"""Validate corrected Phase-3 (protocol phase3-v2) per-replica data.

Layout expected under <root> (the downloaded phase3-consolidated artifact):
  dynamics_root/rep<N>/DYNAMICS_OK_<bool>_<profile>.json
  dynamics_root/rep<N>/timebounded_results_<bool>_<profile>.csv
  dynamics_root/rep<N>/dynamics_delays_<bool>_<profile>.csv

Every cell must carry a DYNAMICS_OK gate manifest (energy meter tick-v1,
correct ground-truth constants) and a time-bounded CSV whose rows are stamped
energy_meter=tick-v1 with tick_energy/tick_span columns.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "phase3-v2"
ENERGY_METER = "tick-v1"


def _config():
    cfg = json.loads((SOURCE_ROOT / "config" / "run_config.json")
                     .read_text(encoding="utf-8-sig"))
    return cfg["phase3"]


def validate(root: Path, profiles: list[str], replicas: list[int]) -> list[str]:
    errors: list[str] = []
    p3 = _config()
    expected_ticks = int(p3["blind_delay_ticks"])
    expected_spt = float(p3["seconds_per_tick"])
    for replica in replicas:
        rep_root = root / "dynamics_root" / f"rep{replica}"
        if not rep_root.is_dir():
            errors.append(f"missing replica root: {rep_root}")
            continue
        for profile in profiles:
            for bool_name, mode in (("true", "ql_true"), ("false", "ql_false")):
                manifest_path = rep_root / f"DYNAMICS_OK_{bool_name}_{profile}.json"
                results_path = rep_root / f"timebounded_results_{bool_name}_{profile}.csv"
                delays_path = rep_root / f"dynamics_delays_{bool_name}_{profile}.csv"
                if not manifest_path.is_file():
                    errors.append(f"missing gate manifest: {manifest_path}")
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                for key, expected in (
                    ("status", "ok"),
                    ("protocol_version", PROTOCOL),
                    ("energy_meter", ENERGY_METER),
                    ("profile", profile),
                    ("mode", mode),
                    ("replica", replica),
                    ("blind_delay_ticks", expected_ticks),
                    ("seconds_per_tick", expected_spt),
                ):
                    if manifest.get(key) != expected:
                        errors.append(f"{manifest_path}: {key}={manifest.get(key)!r}, "
                                      f"expected {expected!r}")
                for path in (results_path, delays_path):
                    if not path.is_file():
                        errors.append(f"missing data file: {path}")
                if results_path.is_file():
                    with results_path.open(encoding="utf-8-sig", newline="") as handle:
                        rows = list(csv.DictReader(handle))
                    if not rows:
                        errors.append(f"{results_path}: no rows")
                    else:
                        required = {"tick_energy", "tick_span", "energy_meter",
                                    "energy_cost_wallclock_legacy"}
                        missing = required - set(rows[0])
                        if missing:
                            errors.append(f"{results_path}: missing v2 columns {sorted(missing)}")
                        elif any(row.get("energy_meter") != ENERGY_METER for row in rows):
                            errors.append(f"{results_path}: non-{ENERGY_METER} row")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--profiles", default="lab2_slow,lab3_slow")
    parser.add_argument("--replicas", default="1-10")
    args = parser.parse_args()
    profiles = [name.strip() for name in args.profiles.split(",") if name.strip()]
    if "-" in args.replicas and "," not in args.replicas:
        lo, hi = args.replicas.split("-", 1)
        replicas = list(range(int(lo), int(hi) + 1))
    else:
        replicas = [int(r) for r in args.replicas.split(",") if r.strip()]
    errors = validate(args.root, profiles, replicas)
    if errors:
        print("Phase-3 v2 archive validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Phase-3 v2 archive validation passed "
          f"({len(replicas)} replicas x {len(profiles)} profiles x 2 arms).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
