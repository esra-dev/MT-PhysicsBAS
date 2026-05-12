"""Aggregate `runFullSweep` artefacts into headline charts and tables.

Inputs (produced by build.gradle::runFullSweep):
    benchmark/results/<profile>/<mode>/
        benchmark_results_<mode>.csv
        metrics_stereotypes_<true|false>[ _zoneN ].csv
        trace_bench_<mode>.jsonl
        learned_stereotypes_<true|false>.ttl     (ql_true cells only)
        iv_stats_stereotypes_<true|false>.json

Outputs (under analysis/out/):
    summary_table.csv          — one row per (profile, mode) cell
    weakness_heatmap.csv       — rows=profiles, cols=weaknesses, values=fire counts
    weakness_heatmap.png       — matplotlib heatmap (if matplotlib available)
    learning_curve_<profile>.png — per-profile reward curves across modes
    fire_density_<profile>.png — per-profile per-step weakness fire density

Usage:
    python analysis/sweep_report.py
    python analysis/sweep_report.py --root benchmark/results --out analysis/out
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

WEAKNESSES = [
    "w1_unmodelled",
    "w2_inversion",
    "w3_delayed",
    "w4_dropped",
    "w5_topology",
    "w6_unmodelled",  # heat — best-effort heuristic
]


def _try_import_plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: F401
        return plt
    except Exception:
        return None


def find_cells(root: Path):
    """Yield (profile, mode, dir) for every populated sweep cell."""
    if not root.is_dir():
        return
    for profile_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for mode_dir in sorted(p for p in profile_dir.iterdir() if p.is_dir()):
            yield profile_dir.name, mode_dir.name, mode_dir


def summarise_benchmark(csv_path: Path) -> dict:
    if not csv_path.is_file():
        return {}
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    if not rows:
        return {}
    n = len(rows)
    goals = sum(1 for r in rows if r.get("GoalReached") == "1")
    return {
        "scenarios": n,
        "goal_rate": goals / n,
        "avg_steps": sum(float(r["Steps"]) for r in rows) / n,
        "avg_dev": sum(float(r["CumIlluminanceDeviation"]) for r in rows) / n,
        "avg_energy": sum(float(r["TotalEnergyCost"]) for r in rows) / n,
        "avg_wasted": sum(float(r["WastedSteps"]) for r in rows) / n,
    }


def count_weaknesses(jsonl_path: Path) -> Counter:
    counts: Counter = Counter()
    if not jsonl_path.is_file():
        return counts
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for tag in obj.get("weaknessFired") or []:
                counts[str(tag)] += 1
    return counts


def fire_density_per_step(jsonl_path: Path) -> dict:
    """Return {weakness: [count_at_step_0, count_at_step_1, ...]}."""
    by_step: dict = defaultdict(lambda: defaultdict(int))
    max_step = 0
    if not jsonl_path.is_file():
        return {}
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            step = int(obj.get("step", 0))
            max_step = max(max_step, step)
            for tag in obj.get("weaknessFired") or []:
                by_step[str(tag)][step] += 1
    series = {}
    for tag, m in by_step.items():
        series[tag] = [m.get(i, 0) for i in range(max_step + 1)]
    return series


METRICS_RE = re.compile(r"^metrics_stereotypes_(true|false)(?:_zone\d+)?\.csv$")


def find_metrics_file(cell_dir: Path) -> Path | None:
    """Pick the (non-zone-split) aggregate metrics file if present."""
    candidates = [p for p in cell_dir.iterdir()
                  if p.is_file() and METRICS_RE.match(p.name)]
    if not candidates:
        return None
    # Prefer the file without "_zone" suffix.
    for p in candidates:
        if "_zone" not in p.name:
            return p
    return candidates[0]


def read_learning_curve(metrics_path: Path) -> tuple[list, list]:
    if not metrics_path or not metrics_path.is_file():
        return [], []
    eps, rewards = [], []
    with metrics_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                eps.append(int(row["Episode"]))
                rz1 = float(row.get("RewardZ1", 0) or 0)
                rz2 = float(row.get("RewardZ2", 0) or 0)
                rewards.append(rz1 + rz2)
            except (KeyError, ValueError):
                continue
    return eps, rewards


def write_summary(out_dir: Path, summary_rows: list[dict]):
    out_path = out_dir / "summary_table.csv"
    if not summary_rows:
        out_path.write_text("", encoding="utf-8")
        return
    cols = list(summary_rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in summary_rows:
            w.writerow(r)


def write_weakness_heatmap(out_dir: Path, profiles: list, matrix: dict):
    out_path = out_dir / "weakness_heatmap.csv"
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["profile"] + WEAKNESSES)
        for prof in profiles:
            row = [prof] + [matrix.get(prof, {}).get(wk, 0) for wk in WEAKNESSES]
            w.writerow(row)


def plot_weakness_heatmap(out_dir: Path, profiles: list, matrix: dict, plt):
    if plt is None or not profiles:
        return
    import numpy as np  # type: ignore
    data = np.array([[matrix.get(p, {}).get(wk, 0) for wk in WEAKNESSES]
                     for p in profiles], dtype=float)
    fig, ax = plt.subplots(figsize=(1.4 * len(WEAKNESSES) + 2,
                                    0.5 * len(profiles) + 2))
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(WEAKNESSES)))
    ax.set_xticklabels(WEAKNESSES, rotation=30, ha="right")
    ax.set_yticks(range(len(profiles)))
    ax.set_yticklabels(profiles)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, int(data[i, j]), ha="center", va="center",
                    color="white" if data[i, j] > data.max() / 2 else "black",
                    fontsize=8)
    fig.colorbar(im, ax=ax, label="weakness fire count")
    ax.set_title("Weakness fingerprint fires per (profile × weakness)")
    fig.tight_layout()
    fig.savefig(out_dir / "weakness_heatmap.png", dpi=150)
    plt.close(fig)


def plot_learning_curves(out_dir: Path, curves: dict, plt):
    if plt is None:
        return
    by_profile: dict = defaultdict(dict)
    for (prof, mode), (eps, rew) in curves.items():
        by_profile[prof][mode] = (eps, rew)
    for prof, modes in by_profile.items():
        if not modes:
            continue
        fig, ax = plt.subplots(figsize=(7, 4))
        for mode, (eps, rew) in sorted(modes.items()):
            if eps:
                ax.plot(eps, rew, label=mode, linewidth=1.2)
        ax.set_xlabel("episode")
        ax.set_ylabel("reward (z1+z2)")
        ax.set_title(f"Learning curve — {prof}")
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / f"learning_curve_{prof}.png", dpi=150)
        plt.close(fig)


def plot_fire_density(out_dir: Path, density: dict, plt):
    if plt is None:
        return
    by_profile: dict = defaultdict(dict)
    for (prof, mode), series in density.items():
        if series:
            by_profile[prof][mode] = series
    for prof, modes in by_profile.items():
        if not modes:
            continue
        fig, ax = plt.subplots(figsize=(7, 4))
        for mode, series in sorted(modes.items()):
            for tag, counts in series.items():
                ax.plot(range(len(counts)), counts,
                        label=f"{mode}:{tag}", linewidth=0.9, alpha=0.8)
        ax.set_xlabel("step")
        ax.set_ylabel("fires (count)")
        ax.set_title(f"Weakness fire density — {prof}")
        if any(modes.values()):
            ax.legend(fontsize=7, ncol=2)
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / f"fire_density_{prof}.png", dpi=150)
        plt.close(fig)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="benchmark/results",
                        help="sweep results root (default: benchmark/results)")
    parser.add_argument("--out", default="analysis/out",
                        help="report output directory (default: analysis/out)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    matrix: dict = defaultdict(dict)
    profiles_seen: list = []
    curves: dict = {}
    density: dict = {}

    for prof, mode, cell_dir in find_cells(root):
        if prof not in profiles_seen:
            profiles_seen.append(prof)

        bench_csv = cell_dir / f"benchmark_results_{mode}.csv"
        bench_summary = summarise_benchmark(bench_csv)

        jsonl = cell_dir / f"trace_bench_{mode}.jsonl"
        wcounts = count_weaknesses(jsonl)
        for tag, n in wcounts.items():
            matrix[prof][tag] = matrix[prof].get(tag, 0) + n

        metrics_path = find_metrics_file(cell_dir)
        eps, rew = read_learning_curve(metrics_path) if metrics_path else ([], [])
        curves[(prof, mode)] = (eps, rew)

        density[(prof, mode)] = fire_density_per_step(jsonl)

        row = {"profile": prof, "mode": mode}
        row.update(bench_summary)
        for wk in WEAKNESSES:
            row[wk] = wcounts.get(wk, 0)
        summary_rows.append(row)

    write_summary(out_dir, summary_rows)
    write_weakness_heatmap(out_dir, profiles_seen, matrix)

    plt = _try_import_plt()
    plot_weakness_heatmap(out_dir, profiles_seen, matrix, plt)
    plot_learning_curves(out_dir, curves, plt)
    plot_fire_density(out_dir, density, plt)

    print(f"sweep_report: {len(summary_rows)} cells processed.")
    print(f"sweep_report: outputs in {out_dir.resolve()}")
    if plt is None:
        print("sweep_report: matplotlib not available — CSV only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
