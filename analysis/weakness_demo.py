"""
weakness_demo.py — Slide 4 evidence.

For every weakness lab (custom2..custom7) walk the *rule-based* per-step log
and print 3 striking rows that demonstrate the injected weakness in action.

Inputs (produced by `taskBench` with bench_mode("rule_based") for each profile):
    benchmark/results/<profile>/rule_based/bench_step_log_rule_based.csv
  Falls back to the project-root `bench_step_log_rule_based.csv` if the
  per-profile copy is missing (single-profile run).

Output:
    Plain-text terminal output. Take a screenshot of the terminal.
"""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _zone_delta(row: dict, zone: int) -> int:
    """Return Z<zone>After - Z<zone>Before, 0 if the columns are absent."""
    b = row.get(f"Z{zone}Before")
    a = row.get(f"Z{zone}After")
    if b is None or a is None or b == "" or a == "":
        return 0
    try:
        return int(a) - int(b)
    except ValueError:
        return 0


def _is_light_on_action(row: dict) -> bool:
    label = row.get("ActionLabel", "")
    return "Light=true" in label or "Light=True" in label


def _is_blind_action(row: dict) -> bool:
    return "Blind" in row.get("ActionLabel", "")


# -- Per-weakness predicate: returns True if the row is a striking example -----
WEAK = {
    "custom2": (
        "W1 Hidden corridor-light bleed (zones brighten with no actuator change)",
        lambda r: r.get("ActionLabel") == "DO_NOTHING"
                  and (_zone_delta(r, 1) > 0 or _zone_delta(r, 2) > 0
                       or _zone_delta(r, 3) > 0 or _zone_delta(r, 4) > 0),
    ),
    "custom3": (
        "W2 Sign inversion (open-blinds DARKENS the zone at high sun)",
        lambda r: _is_blind_action(r) and (
            _zone_delta(r, 1) < 0 or _zone_delta(r, 2) < 0
            or _zone_delta(r, 3) < 0 or _zone_delta(r, 4) < 0),
    ),
    "custom4": (
        "W3 Ramp + hysteresis (Light=ON dispatched, no immediate brightening)",
        lambda r: _is_light_on_action(r) and (
            _zone_delta(r, 1) == 0 and _zone_delta(r, 2) == 0
            and _zone_delta(r, 3) == 0 and _zone_delta(r, 4) == 0),
    ),
    "custom5": (
        "W4 Power-budget drop (low-priority lamp ON command silently ignored)",
        lambda r: _is_light_on_action(r) and (
            _zone_delta(r, 1) == 0 and _zone_delta(r, 2) == 0
            and _zone_delta(r, 3) == 0 and _zone_delta(r, 4) == 0),
    ),
    "custom6": (
        "W5 Topology change (cross-zone interference appears intermittently)",
        lambda r: int(r.get("CrossZoneInterference", "0") or 0) == 1,
    ),
    "custom7": (
        "W6 Heat coupling (every Light=ON action also raises temperature)",
        lambda r: _is_light_on_action(r),
    ),
}


def _candidate_logs(profile: str) -> list[Path]:
    return [
        ROOT / "benchmark" / "results" / profile / "rule_based"
             / "bench_step_log_rule_based.csv",
        ROOT / "bench_step_log_rule_based.csv",   # fallback
    ]


def _format_row(r: dict) -> str:
    zones = []
    for z in (1, 2, 3, 4):
        b = r.get(f"Z{z}Before")
        a = r.get(f"Z{z}After")
        t = r.get(f"Z{z}Target")
        if b is None:
            continue
        zones.append(f"Z{z} {b}->{a} (tgt {t})")
    return (f"  scen={r['ScenarioId']:>3} step={r['Step']:>3}  "
            + "  ".join(zones)
            + f"  | action={r.get('ActionLabel','?')}")


def main() -> None:
    print("=" * 78)
    print(" Weakness demo — striking failures of the rule-based agent")
    print("=" * 78)
    for profile, (title, pred) in WEAK.items():
        log = next((p for p in _candidate_logs(profile) if p.is_file()), None)
        print(f"\n--- {profile}: {title} ---")
        if log is None:
            print(f"  [skip] no bench_step_log_rule_based.csv found for {profile}")
            continue
        with log.open(encoding="utf-8") as fh:
            rows = [r for r in csv.DictReader(fh) if pred(r)]
        if not rows:
            print(f"  [empty] no rows matched the predicate in {log}")
            continue
        for r in rows[:3]:
            print(textwrap.shorten(_format_row(r), width=160))
        print(f"  ({len(rows)} matching rows total in {log.name})")


if __name__ == "__main__":
    main()
