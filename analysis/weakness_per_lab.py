"""
weakness_per_lab.py — Slide 6 evidence, one figure per weakness.

For each weakness lab (custom2..custom7) this script:

  1. Runs the *rule-based* benchmark in isolation
     (`gradlew runFullSweep -Pprofiles=<p> -Pmodes=rule_based`).
     The Gradle task automatically patches `active_profile/1` in
     `src/agt/lab_profiles.asl` and `bench_mode/1` in the bench agent,
     and restores both files afterwards.

  2. Snapshots the resulting CSV artefacts the moment they are produced
     (the next profile's run would overwrite them at project root).

  3. Picks the most striking scenario where the rule-based agent FAILED
     (GoalReached = 0) and the weakness fingerprint fired.

  4. Renders one self-contained PNG per profile:

        analysis/out/weakness/<profile>_weakness.png

     showing Z1 + Z2 illuminance trajectories with target lines, the
     dispatched actions, and a callout marking the failure step.

The script is fully self-contained — it does NOT rely on any prior sweep
output. The only runtime prerequisite is that the matching Node-RED
simulator is running on its assigned port:

    custom2 → 1882   custom3 → 1883   custom4 → 1884
    custom5 → 1885   custom6 → 1886   custom7 → 1887

Use --use-existing to skip the Gradle runs and reuse a previous
analysis/out/weakness/<profile>_step_log.csv snapshot (useful for
tweaking the figures without re-running the bench).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Force UTF-8 stdout/stderr so characters like '≥' and '→' don't blow up on
# Windows consoles that default to cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:        # pylint: disable=broad-except
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "analysis" / "out" / "weakness"

# ---------------------------------------------------------------------------
# Row helpers (rich CSV schema)
#   ScenarioId,RunId,Step,Z1Before..Z4Before,Z1Target..Z4Target,ActionLabel,
#   Z1After..Z4After,WasMasked,CrossZoneInterference,Z1Temp..Z4Temp,
#   SunshineRank,ActuatorState
# Empty cells are valid (profile uses fewer zones / older logger).
# ---------------------------------------------------------------------------
def _int(r: dict, key: str):
    v = r.get(key, "")
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None

def _float(r: dict, key: str):
    v = r.get(key, "")
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None

def _delta(r: dict, z: int):
    a = _int(r, f"Z{z}After")
    b = _int(r, f"Z{z}Before")
    if a is None or b is None:
        return 0
    return a - b

def _zones_present(r: dict) -> list[int]:
    return [z for z in (1, 2, 3, 4) if _int(r, f"Z{z}Before") is not None]

def _actuators(r: dict) -> dict[str, bool]:
    s = (r.get("ActuatorState") or "").strip()
    out: dict[str, bool] = {}
    if not s:
        return out
    for kv in s.split(";"):
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        out[k.strip()] = v.strip().lower() == "true"
    return out

def _label(r: dict) -> str:
    return (r.get("ActionLabel") or "").strip()

def _is_light_on_action(label: str) -> bool:
    return "Light=true" in label

def _is_blind_open_action(label: str) -> bool:
    # Blinds vocabulary varies (Blind, Blinds). value=true means "open".
    return ("Blind" in label) and ("=true" in label)

_TARGET_ZONE_RE = re.compile(r"SetZ(\d)")

def _action_target_zone(label: str) -> int | None:
    """Return zone index N if label is SetZN<something>=..., else None."""
    m = _TARGET_ZONE_RE.search(label or "")
    return int(m.group(1)) if m else None

def _on_lamp_count(row) -> int:
    return sum(1 for k, v in _actuators(row).items() if v and "Light" in k)

def _fmt_deltas(row, zones) -> str:
    parts = []
    for z in zones:
        b = _int(row, f"Z{z}Before")
        a = _int(row, f"Z{z}After")
        if b is None or a is None:
            continue
        arrow = "=" if a == b else ("\u2191" if a > b else "\u2193")
        parts.append(f"Z{z} {b}{arrow}{a}")
    return ", ".join(parts)

# ---------------------------------------------------------------------------
# Per-weakness configuration. Predicates take (row, prev_row, scenario_rows,
# step_index) and return True when this row demonstrates the weakness.
# ---------------------------------------------------------------------------
def _pred_w1(row, prev, scen, i):
    # custom2: corridor-light bleed. Agent's action targets ONE zone (or no
    # zone at all), yet TWO OR MORE OTHER zones' lux changed in the same
    # step. That can only be the unmodelled corridor light leaking across
    # zone boundaries.
    label = _label(row)
    tgt = _action_target_zone(label)
    others_moved = sum(1 for z in _zones_present(row)
                       if z != tgt and _delta(row, z) != 0)
    return others_moved >= 2

def _pred_w2(row, prev, scen, i):
    # custom3: sign inversion. Action sets a zone's lamp ON (SetZkLight=true)
    # but the SAME zone did not rise (delta <= 0). The simulator inverts the
    # response on at least one zone, so the lamp command makes things darker
    # or has zero effect even though the zone is below target.
    label = _label(row)
    if not _is_light_on_action(label):
        return False
    tgt = _action_target_zone(label)
    if tgt is None:
        return False
    before = _int(row, f"Z{tgt}Before")
    target_rank = _int(row, f"Z{tgt}Target")
    if before is None or target_rank is None:
        return False
    if before >= target_rank:
        return False  # zone already at/over target; no inversion claim
    return _delta(row, tgt) <= 0

def _pred_w3(row, prev, scen, i):
    # custom4: same Light=true command three steps in a row, no immediate
    # effect on this step, but later step shows the zone climbing.
    label = _label(row)
    if not _is_light_on_action(label):
        return False
    if any(_delta(row, z) != 0 for z in _zones_present(row)):
        return False  # only flag when this step had no effect (ramp signature)
    # Look ahead 1–3 steps for any zone climbing while same lamp still ON.
    actuators_now = _actuators(row)
    on_lamps = {k for k, v in actuators_now.items() if v and "Light" in k}
    if not on_lamps:
        return False
    for j in range(i + 1, min(i + 4, len(scen))):
        future = scen[j]
        future_acts = _actuators(future)
        if not on_lamps.issubset({k for k, v in future_acts.items() if v}):
            continue
        if any(_delta(future, z) > 0 for z in _zones_present(future)):
            return True
    return False

def _pred_w4(row, prev, scen, i):
    # custom5: power-budget silent drop. Light=ON dispatched while >=2 other
    # lamps are already ON, and the targeted zone did not rise. Also accept
    # any BLOCKED:Light=true label.
    label = _label(row)
    if label.startswith("BLOCKED:") and "Light=true" in label:
        return True
    if not _is_light_on_action(label):
        return False
    tgt = _action_target_zone(label)
    # Count lamps already ON BEFORE this action (use prev row when available).
    base = prev if prev is not None else row
    on_before = _on_lamp_count(base)
    if on_before < 2:
        return False
    if tgt is not None:
        return _delta(row, tgt) <= 0
    return all(_delta(row, z) <= 0 for z in _zones_present(row))

def _pred_w5(row, prev, scen, i):
    # custom6: cross-zone interference flag AND ≥2 zones changed in same step.
    if _int(row, "CrossZoneInterference") != 1:
        return False
    moved = sum(1 for z in _zones_present(row) if _delta(row, z) != 0)
    return moved >= 2

def _pred_w6(row, prev, scen, i):
    # custom7: Light=true AND any zone temperature rose by >= 0.05 since prev.
    if not _is_light_on_action(_label(row)):
        return False
    if prev is None:
        return False
    for z in (1, 2, 3, 4):
        t_now = _float(row, f"Z{z}Temp")
        t_prev = _float(prev, f"Z{z}Temp")
        if t_now is not None and t_prev is not None and (t_now - t_prev) >= 0.05:
            return True
    return False

# ---------------------------------------------------------------------------
# Data-driven callout builders. Each takes (hit_row, prev_row, scen_rows)
# and returns a multi-line string explaining what the data shows.
# ---------------------------------------------------------------------------
def _explain_w1(hit, prev, scen):
    label = _label(hit)
    tgt = _action_target_zone(label)
    zones = _zones_present(hit)
    moved_others = [z for z in zones if z != tgt and _delta(hit, z) != 0]
    deltas = _fmt_deltas(hit, moved_others) or _fmt_deltas(hit, zones)
    tgt_str = f"Z{tgt}" if tgt is not None else "no zone"
    return (f"Action {label or 'idle'} targets {tgt_str}, "
            f"but {len(moved_others)} other zones moved: {deltas}.\n"
            f"→ Hidden corridor-light bleed couples zones the ontology "
            f"believes are isolated.")

def _explain_w2(hit, prev, scen):
    label = _label(hit)
    tgt = _action_target_zone(label)
    b = _int(hit, f"Z{tgt}Before") if tgt else None
    a = _int(hit, f"Z{tgt}After")  if tgt else None
    tr = _int(hit, f"Z{tgt}Target") if tgt else None
    sun = _int(hit, "SunshineRank")
    sun_s = f" (sun={sun})" if sun is not None else ""
    return (f"Agent set Z{tgt} lamp ON{sun_s}; Z{tgt} went {b}→{a} "
            f"(target {tr}).\n"
            f"→ Lamp ON did NOT raise the zone — simulator inverts/cancels "
            f"the response.")

def _explain_w3(hit, prev, scen):
    label = _label(hit)
    deltas = _fmt_deltas(hit, _zones_present(hit))
    return (f"Action {label}: {deltas}.\n"
            f"→ Lamp ON had no immediate effect; ramp + hysteresis delay "
            f"the change for several steps.")

def _explain_w4(hit, prev, scen):
    label = _label(hit)
    tgt = _action_target_zone(label)
    base = prev if prev is not None else hit
    on_n = _on_lamp_count(base)
    deltas = _fmt_deltas(hit, _zones_present(hit))
    return (f"Action {label} with {on_n} lamps already ON: {deltas}.\n"
            f"→ Global power cap silently dropped the command — "
            f"no lux gain on Z{tgt}.")

def _explain_w5(hit, prev, scen):
    zones = _zones_present(hit)
    moved = [z for z in zones if _delta(hit, z) != 0]
    return (f"Action {_label(hit)}; {len(moved)} zones moved together: "
            f"{_fmt_deltas(hit, moved)}.\n"
            f"→ Partition reconfiguration couples zones the agent treats "
            f"as isolated.")

def _explain_w6(hit, prev, scen):
    pieces = []
    if prev is not None:
        for z in (1, 2, 3, 4):
            tn = _float(hit, f"Z{z}Temp")
            tp = _float(prev, f"Z{z}Temp")
            if tn is not None and tp is not None and (tn - tp) >= 0.05:
                pieces.append(f"Z{z} {tp:.2f}→{tn:.2f}°C")
    delta_s = ", ".join(pieces) if pieces else "temperature climbing"
    return (f"Action {_label(hit)}; {delta_s}.\n"
            f"→ Lamp also heats the room — thermal side-effect absent "
            f"from the ontology.")

WEAK = {
    "custom2": {
        "title":   "W1 Hidden corridor-light bleed",
        "pred":    _pred_w1,
        "explain": _explain_w1,
    },
    "custom3": {
        "title":   "W2 Sign inversion / cancelled lamp response",
        "pred":    _pred_w2,
        "explain": _explain_w2,
    },
    "custom4": {
        "title":   "W3 Ramp + hysteresis",
        "pred":    _pred_w3,
        "explain": _explain_w3,
    },
    "custom5": {
        "title":   "W4 Power-budget silent drop",
        "pred":    _pred_w4,
        "explain": _explain_w4,
    },
    "custom6": {
        "title":   "W5 Topology change (every 5 ticks)",
        "pred":    _pred_w5,
        "explain": _explain_w5,
    },
    "custom7": {
        "title":   "W6 Heat coupling (lamps warm the room)",
        "pred":    _pred_w6,
        "explain": _explain_w6,
    },
}

ALL_PROFILES = list(WEAK.keys())


# ---------------------------------------------------------------------------
# Step 1 — Run the rule-based bench for one profile via Gradle
# ---------------------------------------------------------------------------
def _gradlew_cmd() -> list[str]:
    if os.name == "nt":
        return [str(ROOT / "gradlew.bat")]
    return [str(ROOT / "gradlew")]


def run_rule_based_bench(profile: str) -> None:
    cmd = _gradlew_cmd() + [
        "runFullSweep",
        f"-Pprofiles={profile}",
        "-Pmodes=rule_based",
        "--console=plain",
    ]
    print(f"  [run] {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT))
    if res.returncode != 0:
        raise RuntimeError(
            f"gradlew runFullSweep failed for profile={profile} "
            f"(exit code {res.returncode}). Is the Node-RED simulator for "
            f"{profile} running on its assigned port?")


# ---------------------------------------------------------------------------
# Step 2 — Snapshot the bench artefacts before the next profile overwrites
# ---------------------------------------------------------------------------
def snapshot_artefacts(profile: str) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    src_step    = ROOT / "bench_step_log_rule_based.csv"
    src_summary = ROOT / "benchmark_results_rule_based.csv"
    dst_step    = OUT / f"{profile}_step_log.csv"
    dst_summary = OUT / f"{profile}_summary.csv"
    if src_step.is_file():
        shutil.copyfile(src_step, dst_step)
    if src_summary.is_file():
        shutil.copyfile(src_summary, dst_summary)
    return dst_step, dst_summary


# ---------------------------------------------------------------------------
# Step 3 — Pick a striking failed scenario
# ---------------------------------------------------------------------------
def _failed_scenarios(summary_csv: Path) -> set[tuple[str, str]]:
    """Return the (ScenarioId, RunId) pairs where GoalReached == 0."""
    fail = set()
    if not summary_csv.is_file():
        return fail
    with summary_csv.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("GoalReached", "1").strip() == "0":
                fail.add((r["ScenarioId"], r["RunId"]))
    return fail


def pick_scenario(profile: str, step_csv: Path, summary_csv: Path
                 ) -> tuple[list[dict], dict, str]:
    """
    Choose one (scenario, run) to plot using a tiered strategy:
      1. failed AND predicate fired ≥2 times
      2. failed AND predicate fired ≥1 time
      3. predicate fired (any goal status)
      4. any failed scenario (use first row as 'hit')
      5. scenario 1 (last-resort fallback)
    Returns (rows_for_chosen_scenario, weakness_step_row, source_label).
    """
    pred = WEAK[profile]["pred"]
    if not step_csv.is_file():
        raise RuntimeError(f"bench_step_log not found at {step_csv}")
    with step_csv.open(encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))
    if not all_rows:
        raise RuntimeError(f"{step_csv} is empty")

    by_scen: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in all_rows:
        by_scen[(r["ScenarioId"], r["RunId"])].append(r)
    for k in by_scen:
        by_scen[k].sort(key=lambda r: int(r["Step"]))

    fired: dict[tuple[str, str], list[dict]] = {}
    for k, rows in by_scen.items():
        hits = []
        for i, r in enumerate(rows):
            prev = rows[i - 1] if i > 0 else None
            if pred(r, prev, rows, i):
                hits.append(r)
        if hits:
            # Prefer hits at step >= 2 (avoid step-0 anchor); preserve order.
            hits.sort(key=lambda r: (0, int(r["Step"])) if int(r["Step"]) >= 2
                                    else (1, int(r["Step"])))
            fired[k] = hits
    failed = _failed_scenarios(summary_csv)

    # Tier 1: failed AND ≥2 hits
    for k, hits in fired.items():
        if k in failed and len(hits) >= 2:
            return by_scen[k], hits[0], "failed × predicate fired ≥2"
    # Tier 2: failed AND ≥1 hit
    for k, hits in fired.items():
        if k in failed:
            return by_scen[k], hits[0], "failed × predicate fired ≥1"
    # Tier 3: any predicate hit
    for k, hits in fired.items():
        return by_scen[k], hits[0], "predicate fired (goal reached)"
    # Tier 4: any failed scenario
    for k in by_scen:
        if k in failed:
            return by_scen[k], by_scen[k][0], "failed scenario, no predicate match"
    # Tier 5
    k = next(iter(by_scen))
    return by_scen[k], by_scen[k][0], "no fingerprint match — showing first scenario"


# ---------------------------------------------------------------------------
# Step 4 — Render one PNG per profile
# ---------------------------------------------------------------------------
def render(profile: str, rows: list[dict], hit: dict, source: str) -> Path:
    cfg = WEAK[profile]
    steps = [int(r["Step"]) for r in rows]
    zones = sorted(set().union(*[set(_zones_present(r)) for r in rows]))
    if not zones:
        zones = [1, 2]

    colours = {1: "#1f77b4", 2: "#d62728", 3: "#2ca02c", 4: "#9467bd"}
    # Vertical jitter so overlapping zone traces remain visible.
    jitter = {1: -0.12, 2: -0.04, 3: +0.04, 4: +0.12}
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    # --- Top panel: per-zone lux trajectories (after the action) ----------
    for z in zones:
        after  = [_int(r, f"Z{z}After") for r in rows]
        target = _int(rows[0], f"Z{z}Target")
        if any(v is not None for v in after):
            ys = [(v + jitter[z]) if v is not None else float("nan")
                  for v in after]
            ax1.plot(steps, ys, "-o", color=colours[z], markersize=3,
                     label=f"Z{z} lux rank")
            if target is not None:
                ax1.axhline(target + jitter[z], color=colours[z],
                            linestyle=":", alpha=0.6,
                            label=f"Z{z} target {target}")
    ax1.set_ylabel("Lux rank (jittered)")
    ax1.grid(alpha=0.3)
    ax1.legend(loc="upper right", fontsize=8, ncol=2)

    # --- Bottom panel: temperature (custom7) or actuator stem (others) ----
    if profile == "custom7":
        # Only plot zones whose temperature actually moves; static zones at
        # 35 °C swamp the y-axis and hide the climb of interest.
        moving = []
        for z in zones:
            temps = [_float(r, f"Z{z}Temp") for r in rows]
            ts = [t for t in temps if t is not None]
            if ts and (max(ts) - min(ts)) >= 0.05:
                moving.append((z, temps))
        if not moving:
            moving = [(z, [_float(r, f"Z{z}Temp") for r in rows])
                      for z in zones]
        for z, temps in moving:
            ax2.plot(steps,
                     [v if v is not None else float("nan") for v in temps],
                     "-^", color=colours[z], markersize=3, label=f"Z{z} temp")
        ax2.axhspan(19.0, 23.0, color="green", alpha=0.10,
                    label="comfort 19–23°C")
        # Auto-fit y around moving zones plus comfort band.
        all_t = [t for _, ts in moving for t in ts if t is not None]
        if all_t:
            lo = min(min(all_t) - 1.0, 18.0)
            hi = max(max(all_t) + 1.0, 24.0)
            ax2.set_ylim(lo, hi)
        ax2.set_ylabel("Temperature (°C)")
        ax2.legend(loc="upper right", fontsize=8, ncol=2)
    else:
        # Stem of actuator changes per step (any key whose value flipped).
        keys = sorted({k for r in rows for k in _actuators(r).keys()})
        ymap = {k: i for i, k in enumerate(keys)}
        prev_state: dict[str, bool] = {}
        for s, r in zip(steps, rows):
            cur = _actuators(r)
            for k, v in cur.items():
                if prev_state.get(k) != v:
                    colour = "#2ca02c" if v else "#7f7f7f"
                    ax2.scatter([s], [ymap[k]], color=colour,
                                marker="^" if v else "v", s=40,
                                edgecolors="black", linewidths=0.4)
            prev_state = cur
        if keys:
            ax2.set_yticks(list(ymap.values()))
            ax2.set_yticklabels(keys, fontsize=8)
        ax2.set_ylabel("Actuator toggles")
        ax2.grid(axis="x", alpha=0.3)
        on_h  = mpatches.Patch(color="#2ca02c", label="turned ON")
        off_h = mpatches.Patch(color="#7f7f7f", label="turned OFF")
        ax2.legend(handles=[on_h, off_h], loc="upper right", fontsize=8)
    ax2.set_xlabel("Step")

    # Highlight the failure step on both axes.
    fail_step = int(hit["Step"])
    for ax in (ax1, ax2):
        ax.axvline(fail_step, color="red", linewidth=1.2, alpha=0.6)

    # Data-driven callout.
    hit_idx = next((i for i, r in enumerate(rows) if r is hit), None)
    prev_hit = rows[hit_idx - 1] if hit_idx and hit_idx > 0 else None
    explain = cfg["explain"]
    explain_text = (explain(hit, prev_hit, rows) if callable(explain)
                    else str(explain))
    callout = f"Step {fail_step}: {explain_text}"
    ax1.text(0.02, 0.97, callout, transform=ax1.transAxes,
             fontsize=9, verticalalignment="top",
             bbox=dict(boxstyle="round", facecolor="#fff3cd", edgecolor="#cc8800"))

    fig.suptitle(f"{profile}: {cfg['title']}\n"
                 f"Rule-based agent — scenario {hit['ScenarioId']}, "
                 f"run {hit['RunId']}  ({source})",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    OUT.mkdir(parents=True, exist_ok=True)
    out_png = OUT / f"{profile}_weakness.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profiles", default=",".join(ALL_PROFILES),
                    help="Comma-separated list of weakness profiles to process")
    ap.add_argument("--use-existing", action="store_true",
                    help="Skip Gradle; reuse existing analysis/out/weakness/*_step_log.csv")
    args = ap.parse_args(argv)

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    unknown  = [p for p in profiles if p not in WEAK]
    if unknown:
        sys.exit(f"unknown profile(s): {unknown}; valid: {ALL_PROFILES}")

    print("=" * 78)
    print(" Per-weakness rule-based failure demos for slide 6")
    print("=" * 78)

    summary_lines: list[str] = []
    for profile in profiles:
        print(f"\n--- {profile} : {WEAK[profile]['title']} ---")
        try:
            if not args.use_existing:
                run_rule_based_bench(profile)
                step_csv, summary_csv = snapshot_artefacts(profile)
            else:
                step_csv    = OUT / f"{profile}_step_log.csv"
                summary_csv = OUT / f"{profile}_summary.csv"
                if not step_csv.is_file():
                    print(f"  [skip] {step_csv} missing — re-run without --use-existing")
                    continue

            rows, hit, source = pick_scenario(profile, step_csv, summary_csv)
            png = render(profile, rows, hit, source)
            print(f"  [ok] {png}  ({source})")
            summary_lines.append(
                f"  {profile:<8} step {hit['Step']:>3} "
                f"action={hit['ActionLabel']:<28} → {png.name}"
            )
        except Exception as exc:        # pylint: disable=broad-except
            print(f"  [error] {profile}: {exc}")

    print("\n" + "=" * 78)
    print(" Summary")
    print("=" * 78)
    for line in summary_lines:
        print(line)
    print(f"\nFigures written to: {OUT}")


if __name__ == "__main__":
    main()
