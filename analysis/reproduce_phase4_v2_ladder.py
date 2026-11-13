#!/usr/bin/env python3
"""Reproduce the registered Phase-4 knowledge-ladder tables from the archives.

Re-validates every control-run archive under the ladder campaign root with the
Phase-4 archive validator (labs and seeds as recorded in each run's
``workflow_inputs.json``), rebuilds the frozen analysis
(``analysis/phase4_v2_knowledge_ladder.py``) into a temporary directory, and
compares the rebuilt tables with the committed ones (canonical numeric CSV
bytes; parsed JSON).

Usage:
  python analysis/reproduce_phase4_v2_ladder.py [phase4_v2_ladder] \
      [--full-root phase4_v2_corrected]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

try:
    from analysis import phase4_v2_knowledge_ladder as ladder
    from analysis import reproduce_phase4_v2 as base
    from analysis import validate_phase4_v2_archive as archive_validator
except ImportError:  # executed as a script from the repo root
    import phase4_v2_knowledge_ladder as ladder  # type: ignore
    import reproduce_phase4_v2 as base  # type: ignore
    import validate_phase4_v2_archive as archive_validator  # type: ignore

TABLES = ("phase4_v2_knowledge_ladder_family.csv",
          "phase4_v2_knowledge_ladder_descriptives.csv",
          "phase4_v2_knowledge_ladder_comparability.csv")
SUMMARY = "phase4_v2_knowledge_ladder.json"
ARM_OF_MODE = {"phase4_v2_brick_only": "brick", "phase4_v2_redundancy_only": "redundancy"}


def _inputs(run_dir: Path) -> dict:
    data = json.loads((run_dir / "analysis" / "out" / "workflow_inputs.json").read_text(encoding="utf-8-sig"))
    seeds = data["seeds"]
    data["seeds"] = [int(s) for s in seeds] if isinstance(seeds, list) \
        else [int(s) for s in str(seeds).split(",") if s.strip()]
    profiles = data["profiles"]
    data["profiles"] = list(profiles) if isinstance(profiles, list) \
        else [p for p in str(profiles).split(",") if p.strip()]
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_root", type=Path, nargs="?", default=Path("phase4_v2_ladder"))
    parser.add_argument("--full-root", type=Path, default=Path("phase4_v2_corrected"),
                        help="archived phase4_v2 campaign root (A3)")
    args = parser.parse_args()

    full_roots = sorted(p for p in args.full_root.glob("run_*") if p.is_dir())
    arms: dict[str, list[Path]] = {"brick": [], "redundancy": []}
    for run_dir in sorted(p for p in args.campaign_root.glob("run_*") if p.is_dir()):
        inputs = _inputs(run_dir)
        arm = ARM_OF_MODE.get(inputs["run_mode"])
        if arm is None:
            print(f"{run_dir}: unexpected run_mode {inputs['run_mode']}", file=sys.stderr)
            return 1
        errors = archive_validator.validate(run_dir, expected_seeds=inputs["seeds"],
                                            labs=tuple(inputs["profiles"]))
        if errors:
            print(f"{run_dir}: archive validation FAILED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        arms[arm].append(run_dir)
        print(f"{run_dir}: archive gates pass ({arm}; {len(inputs['seeds'])} seeds x "
              f"{len(inputs['profiles'])} labs).")
    if not full_roots or not arms["brick"] or not arms["redundancy"]:
        print("missing archives: need the full-KG campaign and both control arms", file=sys.stderr)
        return 1

    committed = args.campaign_root / "analysis" / "registered"
    with tempfile.TemporaryDirectory(prefix="phase4-v2-ladder-reproduce-") as tmp:
        rebuilt = Path(tmp)
        ladder.run(full_roots, arms["brick"], arms["redundancy"], rebuilt)
        for name in TABLES:
            base._compare(committed / name, rebuilt / name)
        if json.loads((committed / SUMMARY).read_text(encoding="utf-8")) != \
                json.loads((rebuilt / SUMMARY).read_text(encoding="utf-8")):
            raise ValueError(f"summary differs: {committed / SUMMARY}")
    print("All Phase-4 knowledge-ladder tables are byte-equivalent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
