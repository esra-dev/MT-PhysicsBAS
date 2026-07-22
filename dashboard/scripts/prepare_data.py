#!/usr/bin/env python3
"""Prepare static JSON data for the MT-Esra phase demo dashboard.

Reads real benchmark/analysis outputs from the repo and writes compact JSON
files into dashboard/public/data/. Stdlib only. Run from anywhere:

    python dashboard/scripts/prepare_data.py
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dashboard" / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# lab -> directory that holds the bench step logs / results for all modes
BENCH_DIRS = {
    "lab1": ROOT / "benchmark" / "results_full_seed1" / "lab1" / "ql_true",
    "lab2": ROOT / "benchmark" / "results_full_seed1" / "lab2" / "ql_true",
    "lab3": ROOT / "benchmark" / "results_full_seed1" / "lab3" / "ql_true",
    "lab4": ROOT / "benchmark" / "results" / "lab4" / "ql_true",
    "lab5": ROOT / "benchmark" / "results" / "lab5" / "ql_true",
}
TRAIN_DIRS = {
    "lab1": ROOT / "benchmark" / "results_full_seed1" / "lab1",
    "lab2": ROOT / "benchmark" / "results_full_seed1" / "lab2",
    "lab3": ROOT / "benchmark" / "results_full_seed1" / "lab3",
    "lab4": ROOT / "benchmark" / "results" / "lab4",
    "lab5": ROOT / "benchmark" / "results" / "lab5",
}
MODES = ["ql_true", "ql_false", "rule_based"]

# Phase-1 confirmatory source: the protocol-v2 corrected campaign. Every value
# in dashboard/public/data/phase1.json is derived from a committed
# phase1_v2_corrected/ file; CI regenerates the JSON and fails on any byte
# difference, and analysis/check_provenance.py validates the same file
# independently. Protocol-v1 sources (run 29639767776 and the pooled-20
# reanalysis) are withdrawn and must never feed this builder again.
PHASE1_V2 = ROOT / "phase1_v2_corrected"
PHASE1_FAMILY_CSV = PHASE1_V2 / "analysis" / "registered" / "phase1_v2_registered_family.csv"
PHASE1_DECOMP_JSON = PHASE1_V2 / "analysis" / "registered" / "phase1_v2_decomposition.json"
PHASE1_GATES_JSON = PHASE1_V2 / "analysis" / "phase1_v2_protocol_gate_summary.json"
PHASE1_CONTROLS_CSV = PHASE1_V2 / "analysis" / "phase1_v2_controls_and_descriptives.csv"
PHASE1_ARM_C_OUT = PHASE1_V2 / "run_29848584965" / "analysis" / "out"
PHASE1_RUN_KEYS = {
    "phase1_v2_kg_only": "arm_c",
    "phase1_v2_redundancy_only": "redundancy_only",
    "phase1_v2_baseline": "baseline",
    "phase1_v2_pbrs_only": "pbrs_only",
}
PHASE1_FAMILY_NAMES = {
    "1_arm_c_lab2_auc_goal": "Arm-C lab2 auc_goal",
    "2_redundancy_lab2_auc_goal": "Redundancy lab2 auc_goal",
    "3_arm_c_minus_redundancy_lab2": "Arm C minus redundancy, lab2",
    "4_arm_c_lab3_mean_first_goal_presentations": "Arm-C lab3 first-goal presentations",
    "5_arm_c_lab3_avg_cycling": "Arm-C lab3 cycling",
}
PHASE1_DECOMP_CATEGORIES = {
    "more_than_two_thirds": "more than two thirds: redundancy reproduces most of arm C",
    "between_one_third_and_two_thirds":
        "between one third and two thirds: redundancy reproduces part of arm C",
    "less_than_one_third": "less than one third: redundancy does not reproduce arm C",
}
PHASE1_LAB_HEADLINES = {
    "lab1": "Saturated null control",
    "lab2": "Small learning benefit, mostly redundancy-derived",
    "lab3": "First-goal and cycling null; adverse training/energy descriptives",
}
PHASE1_BENCH_KEYS = {
    "lab2": (
        ("benchmark_goal_rate", "goal_rate"),
        ("benchmark_steps", "avg_steps"),
        ("benchmark_deviation", "avg_dev"),
        ("benchmark_policy_energy", "avg_policy_energy"),
        ("benchmark_cycling", "avg_cycling"),
    ),
    "lab3": (
        ("benchmark_goal_rate", "goal_rate"),
        ("benchmark_policy_energy", "avg_policy_energy"),
        ("benchmark_cycling", "avg_cycling"),
        ("benchmark_redundant", "avg_redundant"),
    ),
}
LEGACY_ENERGY_METRIC = "avg_legacy_wallclock_energy"

# The replay / early-training traces are local single-seed demo recordings
# from 2026-06-10 — pre-inversion action registry and, for lab3, the original
# spill physics (+50 lux / 0.25*Sun, superseded 2026-07-08 by +100 / 0.30*Sun).
# Illustrative only; never confirmatory evidence.
TRACE_PROVENANCE = {
    "recorded": "2026-06-10, local single-seed demo traces (benchmark/ tree)",
    "instrument": "pre-inversion action registry (action-space inversion of 2026-07-10)",
    "lab3_physics": "original spill +50 lux / 0.25*Sun (superseded 2026-07-08 by +100 / 0.30*Sun)",
    "role": "illustrative replay only - not confirmatory evidence",
}


def fnum(x):
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def short_action(label):
    if label == "DO_NOTHING":
        return {"comp": None, "on": None, "text": "do nothing"}
    # http://example.org/was#SetZ1Light=true -> Z1Light / true
    tail = label.split("#Set", 1)[-1]
    comp, _, val = tail.partition("=")
    on = val == "true"
    return {"comp": comp, "on": on, "text": f"{comp} {'ON' if on else 'OFF'}"}


def parse_actuators(s):
    out = {}
    if not s:
        return out
    for part in s.split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            out[k] = v == "true"
    return out


def build_replays():
    replays = {}
    for lab, bdir in BENCH_DIRS.items():
        scenarios_file = ROOT / "benchmark" / f"scenarios_{lab}.json"
        scen_meta = {s["id"]: s for s in json.load(open(scenarios_file))}
        lab_obj = {"scenarios": {}}
        for mode in MODES:
            step_file = bdir / f"bench_step_log_{mode}.csv"
            res_file = bdir / f"benchmark_results_{mode}.csv"
            if not step_file.exists():
                continue
            outcomes = {}
            if res_file.exists():
                for row in csv.DictReader(open(res_file)):
                    key = int(row["ScenarioId"])
                    if key in outcomes:  # keep run 1 only
                        continue
                    outcomes[key] = {
                        "goal": row["GoalReached"] == "1",
                        "steps": int(row["Steps"]),
                        "energy": fnum(row["TotalEnergyCost"]),
                        "wasted": fnum(row.get("WastedSteps")),
                    }
            by_scen = {}
            for row in csv.DictReader(open(step_file)):
                sid, rid = int(row["ScenarioId"]), int(row["RunId"])
                if rid != 1:
                    continue
                zb = [fnum(row.get(f"Z{i}Before")) for i in (1, 2)]
                za = [fnum(row.get(f"Z{i}After")) for i in (1, 2)]
                by_scen.setdefault(sid, []).append({
                    "step": int(row["Step"]),
                    "action": short_action(row["ActionLabel"]),
                    "before": [int(v) if v is not None else None for v in zb],
                    "after": [int(v) if v is not None else None for v in za],
                    "sun": int(row["SunshineRank"]),
                    "act": parse_actuators(row["ActuatorState"]),
                    "targets": [
                        int(float(row["Z1Target"])) if row.get("Z1Target") else None,
                        int(float(row["Z2Target"])) if row.get("Z2Target") else None,
                    ],
                })
            for sid in sorted(set(by_scen) | set(outcomes)):
                steps = sorted(by_scen.get(sid, []), key=lambda s: s["step"])
                sc = lab_obj["scenarios"].setdefault(str(sid), {})
                meta = scen_meta.get(sid, {})
                sc.setdefault("desc", meta.get("description", ""))
                init = {k: v for k, v in meta.items()
                        if k not in ("id", "comment", "description")}
                sc.setdefault("init", init)
                sc.setdefault("modes", {})[mode] = {
                    "steps": steps,
                    "outcome": outcomes.get(sid),
                }
        lab_obj["_provenance"] = TRACE_PROVENANCE
        replays[lab] = lab_obj
        n = len(lab_obj["scenarios"])
        print(f"replay {lab}: {n} scenarios")
    for lab, obj in replays.items():
        json.dump(obj, open(OUT / f"replay_{lab}.json", "w"), separators=(",", ":"))


def build_training():
    out = {}
    for lab, tdir in TRAIN_DIRS.items():
        out[lab] = {}
        for arm, sub in (("ql_true", "training_stereo_true"),
                         ("ql_false", "training_stereo_false")):
            f = tdir / sub / f"metrics_stereotypes_{arm.replace('ql_', '').replace('true', 'true', 1)}_{lab}.csv"
            f = tdir / sub / ("metrics_stereotypes_true_%s.csv" % lab if arm == "ql_true"
                              else "metrics_stereotypes_false_%s.csv" % lab)
            if not f.exists():
                continue
            eps, first_goal = [], None
            for line in open(f):
                line = line.strip()
                if not line or line.startswith("Episode"):
                    continue
                if line.startswith("#"):
                    if "FirstGoalEpisode" in line:
                        first_goal = fnum(line.split(",")[-1])
                    continue
                p = line.split(",")
                eps.append({"ep": int(p[0]), "steps": int(p[1]),
                            "goal": p[4] == "1", "eps": fnum(p[5])})
            out[lab][arm] = {"episodes": eps, "firstGoal": first_goal}
    out["_provenance"] = TRACE_PROVENANCE
    json.dump(out, open(OUT / "training.json", "w"), separators=(",", ":"))
    print("training.json written")


def read_csv_rows(path):
    return list(csv.DictReader(open(path)))


def build_phase1(out_dir=None):
    """Derive the protocol-v2 Phase-1 dashboard summary from the corrected
    archives. Fails loudly on any inconsistency instead of guessing."""
    out_dir = OUT if out_dir is None else out_dir
    gates = json.load(open(PHASE1_GATES_JSON, encoding="utf-8"))
    run_rows = gates["runs"]
    head_shas = {row["head_sha"] for row in run_rows}
    if len(head_shas) != 1:
        raise SystemExit("phase1 gate summary: inconsistent head_sha across runs")

    runs = {}
    for mode, key in PHASE1_RUN_KEYS.items():
        matches = [row["run_id"] for row in run_rows if row["run_mode"] == mode]
        if len(matches) != 1:
            raise SystemExit(f"phase1 gate summary: expected exactly one {mode} run")
        runs[key] = matches[0]

    family = []
    for row in read_csv_rows(PHASE1_FAMILY_CSV):
        q = float(row["q_signflip_bh_m5"])
        family.append({
            "name": PHASE1_FAMILY_NAMES[row["registered_test"]],
            "mean": float(row["mean_paired_difference"]),
            "median": float(row["median_paired_difference"]),
            "ci_lo": float(row["ci_lo_bootstrap"]),
            "ci_hi": float(row["ci_hi_bootstrap"]),
            "p": float(row["p_signflip_two_sided"]),
            "q": q,
            "rank_biserial": float(row["paired_rank_biserial"]),
            "verdict": "supported" if q <= 0.05 else "null",
        })
    if len(family) != len(PHASE1_FAMILY_NAMES):
        raise SystemExit("phase1 registered family: unexpected row count")

    decomp = json.load(open(PHASE1_DECOMP_JSON, encoding="utf-8"))
    decomposition = {
        "redundancy_share": float(decomp["redundancy_share"]),
        "category": PHASE1_DECOMP_CATEGORIES[decomp["category"]],
    }

    learning = read_csv_rows(PHASE1_ARM_C_OUT / "learning_speed_tests.csv")
    paired = read_csv_rows(PHASE1_ARM_C_OUT / "paired_tests.csv")

    def learn(lab, metric):
        values = [row["mean_diff_true_minus_false"] for row in learning
                  if row["profile"] == lab and row["metric"] == metric]
        if len(values) != 1:
            raise SystemExit(f"learning_speed_tests: expected one {lab}/{metric} row")
        return float(values[0])

    def bench(lab, metric):
        values = [row["mean_diff"] for row in paired
                  if row["profile"] == lab and row["metric"] == metric
                  and row["mode_a"] == "ql_true" and row["mode_b"] == "ql_false"]
        if len(values) != 1:
            raise SystemExit(f"paired_tests: expected one {lab}/{metric} row")
        return float(values[0])

    labs = {}
    for lab in ("lab1", "lab2", "lab3"):
        entry = {
            "headline": PHASE1_LAB_HEADLINES[lab],
            "auc_goal": learn(lab, "auc_goal"),
            "first_goal_presentations": learn(lab, "mean_first_goal_presentations"),
        }
        for out_key, metric in PHASE1_BENCH_KEYS.get(lab, ()):
            entry[out_key] = bench(lab, metric)
        labs[lab] = entry

    control_rows = read_csv_rows(PHASE1_CONTROLS_CSV)

    def control_counts(mode):
        corrected = sum(1 for row in control_rows
                        if row["run_mode"] == mode
                        and row["metric"] != LEGACY_ENERGY_METRIC
                        and float(row["mean_difference"]) != 0.0)
        legacy = sum(1 for row in control_rows
                     if row["run_mode"] == mode
                     and row["metric"] == LEGACY_ENERGY_METRIC
                     and float(row["mean_difference"]) != 0.0)
        return corrected, legacy

    baseline_nonzero, baseline_legacy = control_counts("phase1_v2_baseline")
    pbrs_nonzero, pbrs_legacy = control_counts("phase1_v2_pbrs_only")
    if baseline_legacy != pbrs_legacy:
        raise SystemExit("control modes disagree on legacy wall-clock row counts")

    def gate_value(src_key):
        values = {row[src_key] for row in run_rows}
        if len(values) != 1:
            raise SystemExit(f"phase1 gate summary: runs disagree on {src_key}")
        return values.pop()

    horizons = {tuple(row["fixed_horizons"]) for row in run_rows}
    if len(horizons) != 1 or len(next(iter(horizons))) != 1:
        raise SystemExit("phase1 gate summary: unexpected training horizon set")
    protocol_gates = {
        "training_cells_per_run": gate_value("training_cells"),
        "benchmark_cells_per_run": gate_value("benchmark_cells"),
        "episodes_per_training_cell": next(iter(horizons))[0],
        "fallback_count": gate_value("scenario_fallback_count"),
        "paired_schedule_mismatches": gate_value("schedule_pair_mismatches"),
        "first_goal_rows_per_run": gate_value("first_goal_rows"),
        "censored_first_goal_rows_per_run": gate_value("first_goal_censored_rows"),
    }

    obj = {
        "protocol_version": gates["protocol_version"],
        "status": "current thesis evidence",
        "head_sha": head_shas.pop(),
        "runs": runs,
        "registered_family": family,
        "decomposition": decomposition,
        "labs": labs,
        "controls": {
            "baseline_corrected_contrasts_nonzero": baseline_nonzero,
            "pbrs_corrected_contrasts_nonzero": pbrs_nonzero,
            "legacy_wallclock_rows_nonzero_per_control_mode": baseline_legacy,
            "note": ("Only the withdrawn wall-clock diagnostic varies between "
                     "otherwise identical labels."),
        },
        "protocol_gates": protocol_gates,
        "source": "phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "phase1.json", "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2)
        handle.write("\n")
    print("phase1.json written (protocol v2, derived from phase1_v2_corrected/)")


def build_phase2():
    reg = ROOT / "analysis" / "out_phase2_registered"
    obj = {
        "ci": read_csv_rows(reg / "phase2_recovery_ci.csv"),
        "paired": read_csv_rows(reg / "phase2_recovery_paired.csv"),
    }
    json.dump(obj, open(OUT / "phase2.json", "w"), separators=(",", ":"))
    print("phase2.json written")


def build_phase3():
    a = ROOT / "analysis" / "out"
    obj = {
        "delay": read_csv_rows(a / "phase3_delay_accuracy.csv"),
        "compliance": read_csv_rows(a / "phase3_compliance_ci.csv"),
    }
    json.dump(obj, open(OUT / "phase3.json", "w"), separators=(",", ":"))
    print("phase3.json written")


def build_phase4():
    a = ROOT / "analysis" / "out"
    summary = [r for r in read_csv_rows(a / "summary_table.csv")
               if r["profile"] in ("lab4", "lab5") and r["mode"] in MODES]
    llm_detail = []
    f = a / "phase4_llm_detail_lab5.csv"
    if f.exists():
        llm_detail = [r for r in read_csv_rows(f) if r["seed"] == "1"]
    obj = {
        "summary": summary,
        "llm_summary": read_csv_rows(a / "phase4_llm_summary.csv"),
        "llm_detail_lab5": llm_detail,
    }
    json.dump(obj, open(OUT / "phase4.json", "w"), separators=(",", ":"))
    print("phase4.json written")


BUILDERS = {
    "replays": build_replays,
    "training": build_training,
    "phase1": build_phase1,
    "phase2": build_phase2,
    "phase3": build_phase3,
    "phase4": build_phase4,
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Prepare dashboard JSON data.")
    parser.add_argument("--only", choices=sorted(BUILDERS), action="append",
                        help="build only the named dataset(s); default: all")
    args = parser.parse_args()
    for name in (args.only or list(BUILDERS)):
        BUILDERS[name]()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
