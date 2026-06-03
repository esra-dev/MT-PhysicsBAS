"""
midterm_results.py — Slide 7 figures + ablation table.

⚠️  SLIDE-ONLY SNAPSHOT, NOT FOR THESIS FIGURES (Audit Step 6 S6-8).

    This script is the May-22 midterm slide deck snapshot. It reads
    single-seed CSVs from the project root (legacy layout) and renders three
    quick-look panels. Use it ONLY to regenerate the midterm slides.

    For thesis figures use:
      * `analysis/learning_curves.py` — multi-seed reward curves with CIs
      * `analysis/sweep_report.py --seeds-mode` — paired tests, BH q-values,
        bootstrap CIs, summary_table_ci.csv, paired_tests.csv
      * `analysis/sweep_report.py --first-goal-root …` — H2 table (S6-3)

    Outputs are routed to `analysis/out/slides/` so they cannot overwrite
    thesis artefacts in `analysis/out/`.

Three panels, all driven by artefacts already on disk:
  Panel 1: training reward curve (2-zone lab)            -> panel1_reward_curve.png
  Panel 2: bench goal-rate bar chart (3 modes, 2-zone)   -> panel2_goal_rate.png
  Panel 3: weakness fingerprint heatmap (custom2..7)     -> panel3_weakness_heatmap.png

Plus an ablation table printed to stdout (paste into the slide as text).

Inputs:
  Panel 1 :  metrics_stereotypes_<true|false>.csv  (project root)
  Panel 2 :  benchmark_results_<rule_based|ql_false|ql_true>.csv  (project root)
  Panel 3 :  benchmark/results/<profile>/<mode>/trace_bench_<mode>.jsonl

Outputs go under analysis/out/slides/.
"""

from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
# Audit Step 6 S6-8: midterm slide artefacts must never overwrite thesis
# figures rendered into analysis/out/ by sweep_report.py / learning_curves.py.
OUT  = ROOT / "analysis" / "out" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

# Audit Step 6 §5.1: W6 has no canonical fingerprint tag in trace_bench JSONL
# (see analysis/sweep_report.py WEAKNESSES and dashboard/src/lib/weakness.js).
# Midterm slide retained the duplicate w6_unmodelled label for visual parity
# with the slide deck — it counts the same rows as w1_unmodelled. Do NOT use
# this heatmap for thesis reporting.
WEAK  = ["w1_unmodelled", "w2_inversion", "w3_delayed",
         "w4_dropped",    "w5_topology",  "w6_unmodelled"]
PROFS = ["custom2", "custom3", "custom4", "custom5", "custom6", "custom7"]
MODES = ["rule_based", "ql_false", "ql_true"]


# ---------------------------------------------------------------------------
# Panel 1 — Training reward curve
# ---------------------------------------------------------------------------
def load_metrics(path: Path) -> tuple[list[int], list[float]]:
    eps, rew = [], []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                eps.append(int(r["Episode"]))
                rew.append(float(r.get("RewardZ1", 0) or 0)
                           + float(r.get("RewardZ2", 0) or 0))
            except (KeyError, ValueError):
                continue
    return eps, rew


def smooth(y: list[float], w: int = 50) -> np.ndarray:
    arr = np.array(y, dtype=float)
    if len(arr) < w:
        return arr
    return np.convolve(arr, np.ones(w) / w, mode="valid")


def panel1() -> None:
    paths = {
        "ql_false (no stereotypes)": ROOT / "metrics_stereotypes_false.csv",
        "ql_true (stereotypes)":     ROOT / "metrics_stereotypes_true.csv",
    }
    plt.figure(figsize=(8, 4))
    plotted = 0
    for label, p in paths.items():
        if not p.is_file():
            print(f"  [panel1] missing {p.name} — skipped")
            continue
        eps, rew = load_metrics(p)
        if not rew:
            continue
        sm = smooth(rew, w=50)
        plt.plot(eps[:len(sm)], sm, label=label, linewidth=1.5)
        plotted += 1
    if plotted == 0:
        print("  [panel1] no metrics files found — skipping figure")
        plt.close()
        return
    plt.xlabel("Episode")
    plt.ylabel("Reward Z1+Z2 (50-episode moving avg)")
    plt.title("Training reward — 2-zone custom lab")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out = OUT / "panel1_reward_curve.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  [panel1] {out}")


# ---------------------------------------------------------------------------
# Panel 2 — Bench goal-rate bar chart
# ---------------------------------------------------------------------------
def panel2() -> dict:
    results: dict = {}
    for m in MODES:
        p = ROOT / f"benchmark_results_{m}.csv"
        if not p.is_file():
            print(f"  [panel2] missing {p.name} — skipped")
            continue
        rows = list(csv.DictReader(p.open(encoding="utf-8")))
        if not rows:
            continue
        n = len(rows)
        results[m] = {
            "n":            n,
            "goal_rate":    sum(int(r["GoalReached"]) for r in rows) / n,
            "avg_dev":      st.mean(float(r["CumIlluminanceDeviation"]) for r in rows),
            "avg_cycling":  st.mean(int(r["ActuatorCyclingCount"])     for r in rows),
            "avg_energy":   st.mean(float(r["TotalEnergyCost"])        for r in rows),
            "avg_steps":    st.mean(float(r["Steps"])                  for r in rows),
        }
    if not results:
        print("  [panel2] no benchmark CSVs found — skipping figure")
        return results
    plt.figure(figsize=(5.2, 4))
    keys = list(results.keys())
    vals = [results[k]["goal_rate"] for k in keys]
    plt.bar(keys, vals, color=["steelblue", "tomato", "seagreen"][:len(keys)])
    plt.ylabel("Goal rate"); plt.ylim(0, 1.05)
    plt.title("Bench: 2-zone custom lab\n(20 scenarios × N runs)")
    for i, v in enumerate(vals):
        plt.text(i, v + 0.02, f"{v:.0%}", ha="center", fontsize=10)
    plt.tight_layout()
    out = OUT / "panel2_goal_rate.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  [panel2] {out}")
    return results


# ---------------------------------------------------------------------------
# Panel 3 — Weakness fingerprint heatmap
# ---------------------------------------------------------------------------
def panel3() -> None:
    matrix = np.zeros((len(PROFS), len(WEAK)), dtype=int)
    any_data = False
    for i, prof in enumerate(PROFS):
        for mode in MODES:
            jf = ROOT / "benchmark" / "results" / prof / mode / f"trace_bench_{mode}.jsonl"
            if not jf.is_file():
                continue
            with jf.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for tag in obj.get("weaknessFired") or []:
                        if tag in WEAK:
                            matrix[i, WEAK.index(tag)] += 1
                            any_data = True
    if not any_data:
        print("  [panel3] no JSONL traces found yet — skipping heatmap")
        return
    plt.figure(figsize=(8, 4))
    im = plt.imshow(matrix, aspect="auto", cmap="viridis")
    plt.xticks(range(len(WEAK)), WEAK, rotation=30, ha="right")
    plt.yticks(range(len(PROFS)), PROFS)
    mx = matrix.max() if matrix.max() > 0 else 1
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(j, i, int(matrix[i, j]), ha="center", va="center",
                     color="white" if matrix[i, j] > mx / 2 else "black",
                     fontsize=8)
    plt.colorbar(im, label="fingerprint fires (sum over modes)")
    plt.title("W1–W6 fingerprint fires per profile (all modes summed)")
    plt.tight_layout()
    out = OUT / "panel3_weakness_heatmap.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  [panel3] {out}")


# ---------------------------------------------------------------------------
# Ablation table
# ---------------------------------------------------------------------------
def ablation_table(results: dict) -> None:
    if not results:
        return
    print()
    print("=" * 78)
    print(" Ablation table (paste onto slide 7)")
    print("=" * 78)
    print(f"{'Mode':<12} {'GoalRate':>9} {'AvgDev':>9} {'AvgCycling':>12} "
          f"{'AvgEnergy':>10} {'AvgSteps':>9}")
    print("-" * 78)
    for m, d in results.items():
        print(f"{m:<12} {d['goal_rate']:>8.0%} {d['avg_dev']:>9.1f} "
              f"{d['avg_cycling']:>12.2f} {d['avg_energy']:>10.1f} "
              f"{d['avg_steps']:>9.2f}")
    print("-" * 78)


def main() -> None:
    print("Generating midterm result panels …")
    panel1()
    res = panel2()
    panel3()
    ablation_table(res)
    print(f"\nDone. Figures in {OUT}")


if __name__ == "__main__":
    main()
