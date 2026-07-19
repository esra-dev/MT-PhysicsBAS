#!/usr/bin/env python3
"""Prepare static JSON data for the MT-Esra phase demo dashboard.

Reads real benchmark/analysis outputs from the repo and writes compact JSON
files into dashboard/public/data/. Stdlib only. Run from anywhere:

    python dashboard/scripts/prepare_data.py
"""
import csv
import json
import math
import shutil
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

# Phase-1 confirmatory source: the post-inversion arm-C run of record
# (THESIS_STATE_REPORT.md §5.2). Never point this back at
# phase1_headline_download/ — that archive is the superseded pre-inversion
# run 27336756264 (checked by analysis/check_provenance.py).
PHASE1_RUN_ID = "29639767776"
PHASE1_SRC = ROOT / "phase1_postinv" / f"run_{PHASE1_RUN_ID}" / "analysis" / "out"
# Registered pooled-20 primary (Plan B): seeds 1-10 of the run of record merged
# with the registered seeds-11-20 extension run 29692725784, BH within the
# registered m=3 family only (THESIS_STATE_REPORT.md Addendum 2026-07-19c).
# For the three registered cells these are the citable values; the n=10 tables
# stay as the run-29639767776 record.
POOLED20_CSV = (ROOT / "phase1_postinv" / "pooled20_reanalysis"
                / "pooled20_registered_family.csv")
PHASE1_PROVENANCE = {
    "run_id": PHASE1_RUN_ID,
    "commit": "e631877",
    "profile": "phase1_kg_only (factorial arm C: KG prior ON, PBRS OFF, trust OFF)",
    "instrument": "post-inversion (action-space inversion of 2026-07-10)",
    "cross_zone_bonus": 0.0,
    "lab3_physics": "cross-zone spill +100 lux / 0.30*Sun (current; retuned 2026-07-08)",
    "source": "phase1_postinv/run_29639767776/analysis/out",
    "supersedes": "pre-inversion run 27336756264 (phase1_headline_download/kg_only)",
    "registered_primary": ("pooled-20 (seeds 1-10 run 29639767776 + registered "
                           "extension seeds 11-20 run 29692725784, head 02ed6c1; "
                           "BH within the registered m=3 family; "
                           "THESIS_STATE_REPORT.md Addendum 2026-07-19c)"),
    "pooled20_source": "phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv",
    "n10_role": ("run-of-record descriptive tables; for the three registered "
                 "cells the citable values are the registered_pooled20 rows"),
}

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


def build_phase1():
    kg = PHASE1_SRC
    obj = {
        "_provenance": PHASE1_PROVENANCE,
        "learning_speed": read_csv_rows(kg / "learning_speed_tests.csv"),
        "summary_ci": read_csv_rows(kg / "summary_table_ci.csv"),
        "paired": read_csv_rows(kg / "paired_tests.csv"),
        "registered_pooled20": read_csv_rows(POOLED20_CSV),
    }
    json.dump(obj, open(OUT / "phase1.json", "w"), separators=(",", ":"))
    img = OUT / "img"
    img.mkdir(exist_ok=True)
    for lab in ("lab1", "lab2", "lab3"):
        src = kg / f"learning_curve_{lab}.png"
        if src.exists():
            shutil.copy(src, img / f"p1_curve_{lab}.png")
    print("phase1.json + curves written")


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


if __name__ == "__main__":
    build_replays()
    build_training()
    build_phase1()
    build_phase2()
    build_phase3()
    build_phase4()
    print("done ->", OUT)
