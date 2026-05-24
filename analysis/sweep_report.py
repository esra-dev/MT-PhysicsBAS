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


# ---------------------------------------------------------------------------
# Multi-seed aggregation (research extension: bootstrap 95% CIs across seeds).
#
# run_full_project_parallel.ps1 -Seeds 1,2,3,4,5 produces a sibling directory
# benchmark/results_seed<N> per seed. This function discovers them, summarises
# each (profile, mode) cell per seed, then aggregates with a non-parametric
# bootstrap to get mean ± 95% CI. No assumption of normality (seed counts as
# low as 3 are fine with bootstrap).
# ---------------------------------------------------------------------------

_METRIC_KEYS = ("goal_rate", "avg_steps", "avg_dev", "avg_energy", "avg_wasted")


def find_seed_roots(parent: Path) -> list[tuple[int, Path]]:
    """Return [(seed, dir), ...] for benchmark/results_seed<N> siblings."""
    parent = Path(parent)
    if not parent.is_dir():
        return []
    out: list[tuple[int, Path]] = []
    pat = re.compile(r"^results_seed(\d+)$")
    for p in sorted(parent.iterdir()):
        if not p.is_dir():
            continue
        m = pat.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    return out


def _bootstrap_ci(values: list[float], iters: int = 10000,
                  alpha: float = 0.05) -> tuple[float, float, float]:
    """Return (mean, ci_lo, ci_hi). Uses numpy if available, else stdlib."""
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    mean = sum(values) / len(values)
    if len(values) == 1:
        return (mean, mean, mean)
    try:
        import numpy as np  # type: ignore
        rng = np.random.default_rng(0xC1)  # deterministic CIs
        arr = np.asarray(values, dtype=float)
        boots = rng.choice(arr, size=(iters, arr.size), replace=True).mean(axis=1)
        lo = float(np.quantile(boots, alpha / 2))
        hi = float(np.quantile(boots, 1 - alpha / 2))
        return (mean, lo, hi)
    except Exception:
        # Stdlib fallback (slower for large iters).
        import random
        random.seed(0xC1)
        n = len(values)
        boots = [sum(random.choice(values) for _ in range(n)) / n
                 for _ in range(iters)]
        boots.sort()
        lo_idx = max(0, int((alpha / 2) * iters))
        hi_idx = min(iters - 1, int((1 - alpha / 2) * iters))
        return (mean, boots[lo_idx], boots[hi_idx])


def aggregate_seeds(seed_roots: list[tuple[int, Path]],
                    out_dir: Path,
                    iters: int = 10000) -> int:
    """Write summary_table_ci.csv with per-(profile,mode) mean+CI across seeds."""
    # per_seed[(profile, mode)][metric] -> list of values across seeds
    per_seed: dict = defaultdict(lambda: defaultdict(list))
    seed_count: dict = defaultdict(int)
    for seed, root in seed_roots:
        for prof, mode, cell_dir in find_cells(root):
            bench_csv = cell_dir / f"benchmark_results_{mode}.csv"
            summ = summarise_benchmark(bench_csv)
            if not summ:
                continue
            seed_count[(prof, mode)] += 1
            for k in _METRIC_KEYS:
                if k in summ:
                    per_seed[(prof, mode)][k].append(float(summ[k]))

    rows = []
    for (prof, mode), metrics in sorted(per_seed.items()):
        row = {
            "profile": prof,
            "mode": mode,
            "n_seeds": seed_count[(prof, mode)],
        }
        for k in _METRIC_KEYS:
            vals = metrics.get(k, [])
            mean, lo, hi = _bootstrap_ci(vals, iters=iters)
            row[f"{k}_mean"]  = mean
            row[f"{k}_ci_lo"] = lo
            row[f"{k}_ci_hi"] = hi
        rows.append(row)

    out_path = out_dir / "summary_table_ci.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    cols = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


# ---------------------------------------------------------------------------
# Paired statistical tests across seeds (research extension; pre-registered).
#
# For each profile x metric and each compared mode pair (typically
# ql_true vs ql_false and ql_true vs rule_based), pair the per-seed values
# by seed id and report:
#   - paired bootstrap mean-difference 95% CI and two-sided p-value
#   - Wilcoxon signed-rank two-sided p-value (scipy if available)
#   - Cliff's delta effect size
#   - Benjamini-Hochberg q-values across the (profile x metric x pair) family
# Output: paired_tests.csv under out_dir.
# ---------------------------------------------------------------------------

_PAIRED_COMPARISONS = (
    ("ql_true", "ql_false"),
    ("ql_true", "rule_based"),
    ("ql_false", "rule_based"),
)


def _collect_per_seed_values(
    seed_roots: list[tuple[int, Path]]
) -> dict:
    """Return per_metric[(profile, mode)] = {seed: value}."""
    out: dict = defaultdict(lambda: defaultdict(dict))
    for seed, root in seed_roots:
        for prof, mode, cell_dir in find_cells(root):
            bench_csv = cell_dir / f"benchmark_results_{mode}.csv"
            summ = summarise_benchmark(bench_csv)
            if not summ:
                continue
            for k in _METRIC_KEYS:
                if k in summ:
                    out[k][(prof, mode)][seed] = float(summ[k])
    return out


def _paired_bootstrap_diff(a: list[float], b: list[float],
                           iters: int = 10000) -> tuple[float, float, float, float]:
    """Return (mean_diff, ci_lo, ci_hi, p_two_sided) for the paired mean
    of (a - b). Pair-wise resampling with a deterministic RNG."""
    if len(a) != len(b) or len(a) < 2:
        return (float("nan"),) * 4  # type: ignore
    diffs = [ai - bi for ai, bi in zip(a, b)]
    mean = sum(diffs) / len(diffs)
    try:
        import numpy as np  # type: ignore
        rng = np.random.default_rng(0xC1)
        d = np.asarray(diffs, dtype=float)
        n = d.size
        idx = rng.integers(0, n, size=(iters, n))
        boots = d[idx].mean(axis=1)
        lo = float(np.quantile(boots, 0.025))
        hi = float(np.quantile(boots, 0.975))
        # Two-sided bootstrap p-value: fraction of resamples whose sign
        # disagrees with the observed mean, doubled.
        if mean >= 0:
            p_one = float((boots <= 0).mean())
        else:
            p_one = float((boots >= 0).mean())
        p = min(1.0, 2.0 * p_one)
        return (mean, lo, hi, p)
    except Exception:
        import random
        random.seed(0xC1)
        n = len(diffs)
        boots = []
        for _ in range(iters):
            s = 0.0
            for _ in range(n):
                s += diffs[random.randrange(n)]
            boots.append(s / n)
        boots.sort()
        lo = boots[max(0, int(0.025 * iters))]
        hi = boots[min(iters - 1, int(0.975 * iters))]
        if mean >= 0:
            p_one = sum(1 for x in boots if x <= 0) / iters
        else:
            p_one = sum(1 for x in boots if x >= 0) / iters
        return (mean, lo, hi, min(1.0, 2.0 * p_one))


def _wilcoxon_p(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return float("nan")
    try:
        from scipy.stats import wilcoxon  # type: ignore
        diffs = [ai - bi for ai, bi in zip(a, b)]
        if all(d == 0 for d in diffs):
            return 1.0
        # zero_method="wilcox" drops zeros (standard); "two-sided" is default.
        res = wilcoxon(diffs, zero_method="wilcox", alternative="two-sided")
        return float(res.pvalue)
    except Exception:
        return float("nan")


def _cliffs_delta(a: list[float], b: list[float]) -> float:
    """Cliff's delta = (#a>b - #a<b) / (|a|*|b|). Range [-1, 1]."""
    if not a or not b:
        return float("nan")
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    return (gt - lt) / (len(a) * len(b))


def _bh_qvalues(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted q-values; NaNs preserved."""
    indexed = [(i, p) for i, p in enumerate(pvalues) if not (p != p)]
    if not indexed:
        return [float("nan")] * len(pvalues)
    indexed.sort(key=lambda t: t[1])
    m = len(indexed)
    q = [float("nan")] * len(pvalues)
    prev = 1.0
    # Iterate from largest p to smallest to enforce monotonicity.
    for rank in range(m, 0, -1):
        i, p = indexed[rank - 1]
        adj = p * m / rank
        prev = min(prev, adj)
        q[i] = min(1.0, prev)
    return q


def paired_tests(seed_roots: list[tuple[int, Path]],
                 out_dir: Path,
                 iters: int = 10000) -> int:
    """Write paired_tests.csv with per (profile, metric, mode_a vs mode_b) rows."""
    per_metric = _collect_per_seed_values(seed_roots)
    rows: list[dict] = []
    pvals: list[float] = []
    for metric, by_cell in per_metric.items():
        # gather profiles present
        profiles = sorted({prof for (prof, _mode) in by_cell.keys()})
        for prof in profiles:
            for mode_a, mode_b in _PAIRED_COMPARISONS:
                ka, kb = (prof, mode_a), (prof, mode_b)
                if ka not in by_cell or kb not in by_cell:
                    continue
                seeds_common = sorted(set(by_cell[ka]) & set(by_cell[kb]))
                if len(seeds_common) < 2:
                    continue
                a = [by_cell[ka][s] for s in seeds_common]
                b = [by_cell[kb][s] for s in seeds_common]
                mean_d, lo, hi, p_boot = _paired_bootstrap_diff(a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
                rows.append({
                    "profile": prof,
                    "metric": metric,
                    "mode_a": mode_a,
                    "mode_b": mode_b,
                    "n_paired": len(seeds_common),
                    "mean_diff": mean_d,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "p_bootstrap": p_boot,
                    "p_wilcoxon": p_wil,
                    "cliffs_delta": delta,
                })
                pvals.append(p_boot if p_boot == p_boot else float("nan"))
    # Multiple-comparisons correction (BH) over the bootstrap p-values family.
    qvals = _bh_qvalues(pvals)
    for r, q in zip(rows, qvals):
        r["q_bootstrap_bh"] = q

    out_path = out_dir / "paired_tests.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    cols = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


def write_latex_table(summary_csv: Path, out_tex: Path) -> bool:
    """Render summary_table_ci.csv as a minimal LaTeX tabular for \\input{}."""
    if not summary_csv.is_file():
        return False
    rows = list(csv.DictReader(summary_csv.open(encoding="utf-8")))
    if not rows:
        return False
    metric_cols = [c for c in rows[0].keys() if c.endswith("_mean")]
    lines = [
        "% Auto-generated by analysis/sweep_report.py. Do not edit by hand.",
        "\\begin{tabular}{ll" + "r" * len(metric_cols) + "}",
        "\\toprule",
        "Profile & Mode & "
        + " & ".join(c.removesuffix("_mean").replace("_", "\\_") for c in metric_cols)
        + " \\\\",
        "\\midrule",
    ]
    for r in rows:
        cells = [r["profile"], r["mode"].replace("_", "\\_")]
        for c in metric_cols:
            base = c.removesuffix("_mean")
            mean = r.get(c, "")
            lo = r.get(f"{base}_ci_lo", "")
            hi = r.get(f"{base}_ci_hi", "")
            try:
                cells.append(
                    f"${float(mean):.3f}_{{[{float(lo):.3f},{float(hi):.3f}]}}$"
                )
            except (TypeError, ValueError):
                cells.append("--")
        lines.append(" & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    out_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="benchmark/results",
                        help="sweep results root (default: benchmark/results)")
    parser.add_argument("--out", default="analysis/out",
                        help="report output directory (default: analysis/out)")
    parser.add_argument("--seeds-mode", action="store_true",
                        help="aggregate across sibling results_seed<N>/ dirs "
                             "with bootstrap 95%% CIs (written to "
                             "summary_table_ci.csv). Also runs the standard "
                             "single-root report on the first seed found.")
    parser.add_argument("--ci-bootstrap-iters", type=int, default=10000,
                        help="bootstrap iterations for CIs (default 10000)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Multi-seed aggregation (additive) ─────────────────────────────
    if args.seeds_mode:
        parent = Path(args.root).parent if Path(args.root).name == "results" \
                 else Path(args.root)
        seed_roots = find_seed_roots(parent)
        if not seed_roots:
            print(f"sweep_report: --seeds-mode but no results_seed* under "
                  f"{parent.resolve()}", file=sys.stderr)
        else:
            n = aggregate_seeds(seed_roots, out_dir,
                                iters=args.ci_bootstrap_iters)
            print(f"sweep_report: aggregated {len(seed_roots)} seed(s) "
                  f"-> {n} (profile, mode) rows with 95% CIs "
                  f"({args.ci_bootstrap_iters} bootstrap iters)")
            print(f"sweep_report: summary_table_ci.csv written to {out_dir.resolve()}")
            n_pairs = paired_tests(seed_roots, out_dir,
                                   iters=args.ci_bootstrap_iters)
            print(f"sweep_report: wrote {n_pairs} paired-test rows "
                  f"to paired_tests.csv")
            if write_latex_table(out_dir / "summary_table_ci.csv",
                                 out_dir / "summary_table_ci.tex"):
                print("sweep_report: summary_table_ci.tex written "
                      "(\\input{}-ready)")
        # Run the per-cell report against the first seed for sanity charts.
        if seed_roots:
            root = seed_roots[0][1]
        else:
            root = Path(args.root)
    else:
        root = Path(args.root)

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
