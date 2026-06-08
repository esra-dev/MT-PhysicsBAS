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

# Canonical fingerprint tags emitted by QLearner.classifyWeaknesses() and
# logged into trace_bench_*.jsonl. W6 has no fingerprint tag in the JSONL — the
# README (§Note on W6) and dashboard/src/lib/weakness.js confirm that W6 is
# detected post-hoc from BenchmarkLogger.UnmodelledZoneEffect + ComfortDeviation,
# not from a `w6_*` member of `weaknessFired`. Audit Step 6 §5.1 / S6-6.
WEAKNESSES = [
    "w1_unmodelled",
    "w2_inversion",
    "w3_delayed",
    "w4_dropped",
    "w5_topology",
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
        plotted = 0
        for mode, (eps, rew) in sorted(modes.items()):
            if eps:
                ax.plot(eps, rew, label=mode, linewidth=1.2)
                plotted += 1
        ax.set_xlabel("episode")
        ax.set_ylabel("reward (z1+z2)")
        ax.set_title(f"Learning curve — {prof}")
        # Only draw a legend when at least one labelled curve exists; calling
        # ax.legend() with no labelled artists emits a UserWarning that the
        # run_full_project.ps1 Phase 5 wrapper escalates to a fatal error.
        if plotted:
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
    """Return (mean, ci_lo, ci_hi). Uses numpy if available, else stdlib.

    Audit Step 6 S6-5: when n < 2, the bootstrap is undefined; return NaN CIs
    rather than a zero-width (mean, mean, mean) tuple, which would silently
    print as "mean ± 0" in summary_table_ci.csv if an ablation seed crashes.
    """
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    mean = sum(values) / len(values)
    if len(values) < 2:
        return (mean, float("nan"), float("nan"))
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

# Pre-reg §2 step 5 locks the BH family at 7 profiles × 5 metrics × 2 mode-pairs
# = 70 tests per analysis. The first two pairs are *confirmatory* (gate H1, H3,
# H4). The third pair (ql_false vs rule_based) is *exploratory* per pre-reg §5
# and must be BH-corrected within its own family so it does not inflate m for
# the confirmatory tests. Audit Step 6 S6-1 / §5.3.
_CONFIRMATORY_PAIRS = (
    ("ql_true", "ql_false"),
    ("ql_true", "rule_based"),
)
_EXPLORATORY_PAIRS = (
    ("ql_false", "rule_based"),
)
_PAIRED_COMPARISONS = _CONFIRMATORY_PAIRS + _EXPLORATORY_PAIRS


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
                           iters: int = 10000
                           ) -> tuple[float, float, float, float, float, float]:
    """Return (mean_diff, ci_lo, ci_hi, p_two_sided, p_one_sided_pos,
    p_one_sided_neg) for the paired mean of (a - b). Pair-wise resampling
    with a deterministic RNG seed (pre-reg §2 step 1 uses 0xC1).

    * p_two_sided  — convention used since the May-22 sweep: doubled-tail
      anchored on the observed mean's sign.
    * p_one_sided_pos — P(boots ≤ 0); evidence *against* H_A: μ_diff > 0
      (used for pre-reg H1: "ql_true ≥ ql_false on clean lab" — small value
      supports H_A). Audit Step 6 S6-2.
    * p_one_sided_neg — P(boots ≥ 0); evidence *against* H_A: μ_diff < 0
      (quantifies how strongly mode_a is worse than mode_b — answers Open
      Question 4).
    """
    if len(a) != len(b) or len(a) < 2:
        return (float("nan"),) * 6  # type: ignore
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
        p_one_pos = float((boots <= 0).mean())
        p_one_neg = float((boots >= 0).mean())
        # Two-sided: anchored on observed sign (legacy convention; documented
        # in pre-reg §6 deviation S6-2).
        p_one_anchor = p_one_pos if mean >= 0 else p_one_neg
        p = min(1.0, 2.0 * p_one_anchor)
        return (mean, lo, hi, p, p_one_pos, p_one_neg)
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
        p_one_pos = sum(1 for x in boots if x <= 0) / iters
        p_one_neg = sum(1 for x in boots if x >= 0) / iters
        p_one_anchor = p_one_pos if mean >= 0 else p_one_neg
        return (mean, lo, hi, min(1.0, 2.0 * p_one_anchor), p_one_pos, p_one_neg)


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
    """Write paired_tests.csv with per (profile, metric, mode_a vs mode_b) rows.

    Audit Step 6 S6-1: rows carry a ``family`` column (``confirmatory`` /
    ``exploratory``). BH q-values are computed **independently per family** so
    the confirmatory denominator matches pre-reg §2 (7 profiles × 5 metrics
    × 2 mode-pairs = 70) and the exploratory pair (ql_false vs rule_based)
    cannot inflate m for the confirmatory tests.
    Audit Step 6 S6-2: ``p_bootstrap_one_sided_positive`` and
    ``p_bootstrap_one_sided_negative`` are reported alongside the legacy
    two-sided ``p_bootstrap`` so pre-reg §3 (H1/H2 one-sided) can be tested
    directly without re-resampling.
    """
    per_metric = _collect_per_seed_values(seed_roots)

    def _family_of(mode_a: str, mode_b: str) -> str:
        return ("confirmatory"
                if (mode_a, mode_b) in _CONFIRMATORY_PAIRS
                else "exploratory")

    rows: list[dict] = []
    # Per-family p-value buckets keyed by row index so BH stays vector-aligned.
    family_pvals: dict = defaultdict(list)
    for metric, by_cell in per_metric.items():
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
                (mean_d, lo, hi, p_boot,
                 p_one_pos, p_one_neg) = _paired_bootstrap_diff(
                    a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
                family = _family_of(mode_a, mode_b)
                row_idx = len(rows)
                rows.append({
                    "profile": prof,
                    "metric": metric,
                    "mode_a": mode_a,
                    "mode_b": mode_b,
                    "family": family,
                    "n_paired": len(seeds_common),
                    "seeds_paired": ";".join(str(s) for s in seeds_common),
                    "mean_diff": mean_d,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "p_bootstrap": p_boot,
                    "p_bootstrap_one_sided_positive": p_one_pos,
                    "p_bootstrap_one_sided_negative": p_one_neg,
                    "p_wilcoxon": p_wil,
                    "cliffs_delta": delta,
                })
                family_pvals[family].append((row_idx, p_boot))

    # BH per family (pre-reg §2 step 5: family size 70 for confirmatory).
    for rows_in_family in family_pvals.values():
        if not rows_in_family:
            continue
        idxs = [i for i, _ in rows_in_family]
        ps = [p for _, p in rows_in_family]
        qs = _bh_qvalues(ps)
        for i, q in zip(idxs, qs):
            rows[i]["q_bootstrap_bh"] = q
            rows[i]["bh_family_m"] = len(idxs)
    for r in rows:
        r.setdefault("q_bootstrap_bh", float("nan"))
        r.setdefault("bh_family_m", 0)

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


# ── H2 (episodes-to-first-goal, PBRS on vs off) — Audit Step 6 S6-3 ──
def _read_first_goal_mean(path: Path) -> float | None:
    """Mean of FirstGoalEpisode column in a first_goal_stereotypes_*.csv.

    The file has header `StartStateIndex,FirstGoalEpisode` and may carry
    trailing `# ...` comment lines (see QLearner.java L1282+). Returns the
    arithmetic mean across all data rows, or None when the file is missing
    / empty / unreadable.
    """
    if not path.is_file():
        return None
    vals: list[float] = []
    try:
        with path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                idx = (row.get("StartStateIndex") or "").strip()
                if not idx or idx.startswith("#"):
                    continue
                v = (row.get("FirstGoalEpisode") or "").strip()
                if not v:
                    continue
                try:
                    vals.append(float(v))
                except ValueError:
                    continue
    except OSError:
        return None
    if not vals:
        return None
    return sum(vals) / len(vals)


def _collect_first_goal_by_cell(seed_roots: list[tuple[int, Path]],
                                stereo: bool) -> dict:
    """Return {profile: {seed: mean_first_goal_episode}}.

    The first-goal CSV is a *training* artefact, archived by
    ``run_full_project.ps1`` under ``<profile>/training_stereo_<stereo>/`` (the
    ``ql_<stereo>/`` dirs hold *benchmark* artefacts and never contain
    ``first_goal_*``). Earlier revisions read ``ql_<stereo>/`` and so silently
    produced empty first_goal tables; we read ``training_stereo_<stereo>/``
    first and fall back to the legacy ``ql_<stereo>/`` path for old trees.
    """
    stag = "true" if stereo else "false"
    candidates = (f"training_stereo_{stag}", f"ql_{stag}")
    out: dict = defaultdict(dict)
    for seed, root in seed_roots:
        if not root.is_dir():
            continue
        for prof_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            prof = prof_dir.name
            for mode in candidates:
                csv_path = (prof_dir / mode
                            / f"first_goal_stereotypes_{stag}_{prof}.csv")
                mean = _read_first_goal_mean(csv_path)
                if mean is not None:
                    out[prof][seed] = mean
                    break
    return out


def aggregate_first_goal(seed_roots: list[tuple[int, Path]],
                         ablation_roots: list[tuple[int, Path]] | None,
                         out_dir: Path,
                         iters: int = 10000) -> int:
    """Write first_goal_table.csv + first_goal_wilcoxon.csv for H2 (S6-3).

    Pairing semantics: PBRS-on is read from ``seed_roots`` (the main sweep),
    PBRS-off from ``ablation_roots`` (typically a sibling
    ``results_ablation_a_seed<N>/`` tree produced by a PBRS-off run). Cells are
    joined by (profile, seed); the per-cell scalar is the **mean
    FirstGoalEpisode** across start states. Wilcoxon and BH (across profiles)
    are computed only when ablation_roots is provided; otherwise the table
    still records PBRS-on means with bootstrap CIs.
    """
    on = _collect_first_goal_by_cell(seed_roots, stereo=True)
    off: dict = {}
    if ablation_roots:
        # Pre-reg H2: PBRS-off ablation. Try ql_true first (still stereotyped
        # for state-abstraction parity), fall back to ql_false if absent.
        off = _collect_first_goal_by_cell(ablation_roots, stereo=True)
        if not any(off.values()):
            off = _collect_first_goal_by_cell(ablation_roots, stereo=False)

    profiles = sorted(set(on.keys()) | set(off.keys()))
    table_rows: list[dict] = []
    for prof in profiles:
        on_vals = [on.get(prof, {}).get(s) for s in sorted(on.get(prof, {}).keys())]
        off_vals = [off.get(prof, {}).get(s) for s in sorted(off.get(prof, {}).keys())]
        on_vals = [v for v in on_vals if v is not None]
        off_vals = [v for v in off_vals if v is not None]
        for label, vals in (("pbrs_on", on_vals), ("pbrs_off", off_vals)):
            if not vals:
                continue
            mean, lo, hi = _bootstrap_ci(vals, iters=iters)
            table_rows.append({
                "profile": prof,
                "condition": label,
                "n_seeds": len(vals),
                "mean_first_goal": mean,
                "ci_lo": lo,
                "ci_hi": hi,
            })

    table_path = out_dir / "first_goal_table.csv"
    if table_rows:
        cols = list(table_rows[0].keys())
        with table_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in table_rows:
                w.writerow(r)
    else:
        table_path.write_text("", encoding="utf-8")

    # Paired Wilcoxon per profile (BH across profiles).
    wilc_path = out_dir / "first_goal_wilcoxon.csv"
    if not ablation_roots:
        wilc_path.write_text("", encoding="utf-8")
        return len(table_rows)

    wrows: list[dict] = []
    ps: list[float] = []
    for prof in profiles:
        seeds_common = sorted(set(on.get(prof, {}).keys())
                              & set(off.get(prof, {}).keys()))
        if len(seeds_common) < 2:
            continue
        a = [on[prof][s] for s in seeds_common]
        b = [off[prof][s] for s in seeds_common]
        (mean_d, lo, hi, p_boot,
         p_one_pos, p_one_neg) = _paired_bootstrap_diff(a, b, iters=iters)
        p_wil = _wilcoxon_p(a, b)
        delta = _cliffs_delta(a, b)
        wrows.append({
            "profile": prof,
            "n_paired": len(seeds_common),
            "seeds_paired": ";".join(str(s) for s in seeds_common),
            "mean_diff_on_minus_off": mean_d,
            "ci_lo": lo,
            "ci_hi": hi,
            "p_bootstrap": p_boot,
            "p_bootstrap_one_sided_negative": p_one_neg,
            "p_wilcoxon": p_wil,
            "cliffs_delta": delta,
        })
        ps.append(p_wil)

    if wrows:
        qs = _bh_qvalues(ps)
        for r, q in zip(wrows, qs):
            r["q_wilcoxon_bh"] = q
            r["bh_family_m"] = len(qs)
        cols = list(wrows[0].keys())
        with wilc_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in wrows:
                w.writerow(r)
    else:
        wilc_path.write_text("", encoding="utf-8")
    return len(table_rows)


# ---------------------------------------------------------------------------
# Learning-speed analysis (PRIMARY outcome; pre-reg revision after Sweep 17).
#
# The thesis claim is that stereotype-informed Q-learning *learns faster /
# more efficiently*, not that it reaches a higher final plateau. Sweep 17
# measured only the final benchmark goal_rate and so could not see a speed
# advantage. These functions read the per-episode TRAINING metrics
# (metrics_stereotypes_<stereo>_<profile>.csv) and derive three speed metrics
# per (profile, seed, stereo):
#   * auc_goal              — normalised area under the per-episode goal curve
#                             (= fraction of training episodes that reached
#                             goal). Higher ⇒ solved earlier and more often.
#   * episodes_to_threshold — first episode at which the trailing rolling goal
#                             rate reaches THRESHOLD. Lower ⇒ faster. Right-
#                             censored at the training horizon when never hit.
#   * mean_first_goal       — mean FirstGoalEpisode across start states (reuses
#                             the first-goal CSV). Lower ⇒ faster.
# The stereotype effect is the *paired* (stereo=True − stereo=False) contrast
# within the same seed, reusing the same bootstrap / Wilcoxon / Cliff's-delta /
# BH machinery as paired_tests(). This is the comparison the empty
# first_goal_wilcoxon.csv was supposed to carry but could not, because it was
# wired to a non-existent PBRS-off ablation tree.
_LEARNING_SPEED_DIRECTION = {
    "auc_goal": "higher_better",
    "auc_reward": "higher_better",
    "episodes_to_threshold": "lower_better",
    "mean_first_goal": "lower_better",
}

# Pre-declared metric tier (Sweep-18 amendment; see pre_registration §6.6).
# auc_goal is the PRIMARY learning-speed metric: it is bounded, never
# censored, and equals the fraction of training episodes solved. The absolute
# episodes_to_threshold metric is retained but demoted to secondary because
# its fixed goal-rate threshold can be right-censored at the horizon for every
# arm (as happened in Sweep-18, where the training goal-rate plateaus below
# the threshold); a ``censored_frac`` column flags this so a degenerate run is
# never misread as a statistical tie. The threshold is deliberately NOT tuned
# post-hoc to the observed plateau (that would be HARKing); instead censoring
# is reported honestly and AUC carries the directional claim.
_LEARNING_SPEED_TIER = {
    "auc_goal": "primary",
    "auc_reward": "secondary",
    "episodes_to_threshold": "secondary_censored",
    "mean_first_goal": "secondary",
}


def _load_episode_metrics(path: Path) -> tuple[list[float], list[float]]:
    """Return (goals, rewards) ordered by Episode from a training metrics CSV.

    goals[i]   = GoalReached (0.0/1.0) for the i-th episode.
    rewards[i] = RewardZ1 + RewardZ2 for the i-th episode.
    Returns ([], []) when the file is missing/empty/unreadable.
    """
    if not path.is_file():
        return [], []
    rows: list[tuple[int, float, float]] = []
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ep_s = (row.get("Episode") or "").strip()
                if not ep_s or ep_s.startswith("#"):
                    continue
                try:
                    ep = int(float(ep_s))
                    goal = float((row.get("GoalReached") or "0").strip() or 0.0)
                    rz1 = float((row.get("RewardZ1") or "0").strip() or 0.0)
                    rz2 = float((row.get("RewardZ2") or "0").strip() or 0.0)
                except ValueError:
                    continue
                rows.append((ep, goal, rz1 + rz2))
    except OSError:
        return [], []
    if not rows:
        return [], []
    rows.sort(key=lambda t: t[0])
    goals = [g for _, g, _ in rows]
    rewards = [r for _, _, r in rows]
    return goals, rewards


def _auc_normalised(series: list[float]) -> float:
    """Trapezoidal area under ``series`` vs episode index, normalised to [min,
    max] episode span so the value is the *mean height* of the curve and is
    comparable across runs of different length. For a 0/1 goal series this
    equals the fraction of episodes solved; the trapezoidal form is used so
    reward curves (continuous) are handled identically."""
    n = len(series)
    if n == 0:
        return float("nan")
    if n == 1:
        return float(series[0])
    area = 0.0
    for i in range(n - 1):
        area += 0.5 * (series[i] + series[i + 1])
    return area / (n - 1)


def _episodes_to_threshold(goals: list[float], window: int,
                           thresh: float) -> tuple[float, bool]:
    """First episode index (0-based) at which the trailing rolling mean of
    ``goals`` over ``window`` episodes is ≥ ``thresh``. Returns
    (episode, censored). When the threshold is never reached the value is
    right-censored at ``len(goals)`` and ``censored=True``."""
    n = len(goals)
    if n == 0:
        return float("nan"), True
    w = max(1, min(window, n))
    run = 0.0
    for i in range(n):
        run += goals[i]
        if i >= w:
            run -= goals[i - w]
        denom = float(min(i + 1, w))
        if i + 1 >= w and (run / denom) >= thresh:
            return float(i), False
    return float(n), True


def _collect_learning_speed_by_cell(seed_roots: list[tuple[int, Path]],
                                    stereo: bool,
                                    window: int,
                                    thresh: float) -> dict:
    """Return {profile: {seed: {metric: value}}} for one stereotype arm.

    Reads ``<seed_root>/<profile>/training_stereo_<stereo>/`` (training
    artefacts), falling back to the legacy ``ql_<stereo>/`` layout.
    """
    stag = "true" if stereo else "false"
    candidates = (f"training_stereo_{stag}", f"ql_{stag}")
    out: dict = defaultdict(dict)
    for seed, root in seed_roots:
        if not root.is_dir():
            continue
        for prof_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            prof = prof_dir.name
            metrics = None
            fg_dir = None
            for mode in candidates:
                cand = (prof_dir / mode
                        / f"metrics_stereotypes_{stag}_{prof}.csv")
                if cand.is_file():
                    metrics = cand
                    fg_dir = prof_dir / mode
                    break
            if metrics is None:
                continue
            goals, rewards = _load_episode_metrics(metrics)
            if not goals:
                continue
            ep_thr, censored = _episodes_to_threshold(goals, window, thresh)
            cell: dict = {
                "auc_goal": _auc_normalised(goals),
                "auc_reward": _auc_normalised(rewards),
                "episodes_to_threshold": ep_thr,
                # Not a scored metric; carried alongside so the paired test can
                # report what fraction of cells were right-censored.
                "_episodes_to_threshold_censored": 1.0 if censored else 0.0,
            }
            fg_path = (fg_dir
                       / f"first_goal_stereotypes_{stag}_{prof}.csv")
            fg_mean = _read_first_goal_mean(fg_path)
            if fg_mean is not None:
                cell["mean_first_goal"] = fg_mean
            out[prof][seed] = cell
    return out


def learning_speed_tests(seed_roots: list[tuple[int, Path]],
                         out_dir: Path,
                         iters: int = 10000,
                         window: int = 100,
                         thresh: float = 0.5) -> int:
    """Write learning_speed_table.csv + learning_speed_tests.csv.

    PRIMARY outcome: the paired (stereo=True − stereo=False) contrast per
    profile for each learning-speed metric, using the same paired bootstrap,
    Wilcoxon, Cliff's-delta and BH machinery as paired_tests(). A
    ``direction`` column and a ``p_one_sided_favorable`` column make the
    directional hypothesis (faster learning under stereotypes) testable
    without re-resampling: for higher-is-better metrics the favourable tail is
    P(boots ≤ 0); for lower-is-better metrics it is P(boots ≥ 0).
    """
    on = _collect_learning_speed_by_cell(seed_roots, True, window, thresh)
    off = _collect_learning_speed_by_cell(seed_roots, False, window, thresh)
    metrics = list(_LEARNING_SPEED_DIRECTION.keys())
    profiles = sorted(set(on.keys()) | set(off.keys()))

    # Per-condition descriptive table (mean + bootstrap CI across seeds).
    table_rows: list[dict] = []
    for prof in profiles:
        for label, data in (("ql_true", on), ("ql_false", off)):
            cells = data.get(prof, {})
            for metric in metrics:
                vals = [c[metric] for c in cells.values() if metric in c]
                if not vals:
                    continue
                mean, lo, hi = _bootstrap_ci(vals, iters=iters)
                table_rows.append({
                    "profile": prof,
                    "condition": label,
                    "metric": metric,
                    "metric_tier": _LEARNING_SPEED_TIER[metric],
                    "direction": _LEARNING_SPEED_DIRECTION[metric],
                    "n_seeds": len(vals),
                    "mean": mean,
                    "ci_lo": lo,
                    "ci_hi": hi,
                })
    table_path = out_dir / "learning_speed_table.csv"
    if table_rows:
        cols = list(table_rows[0].keys())
        with table_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in table_rows:
                w.writerow(r)
    else:
        table_path.write_text("", encoding="utf-8")

    # Paired stereotype contrast (ql_true − ql_false), BH across the family.
    rows: list[dict] = []
    ps: list[float] = []
    for prof in profiles:
        for metric in metrics:
            on_cells = on.get(prof, {})
            off_cells = off.get(prof, {})
            seeds_common = sorted(
                {s for s, c in on_cells.items() if metric in c}
                & {s for s, c in off_cells.items() if metric in c})
            if len(seeds_common) < 2:
                continue
            a = [on_cells[s][metric] for s in seeds_common]   # stereo on
            b = [off_cells[s][metric] for s in seeds_common]  # stereo off
            (mean_d, lo, hi, p_boot,
             p_one_pos, p_one_neg) = _paired_bootstrap_diff(a, b, iters=iters)
            p_wil = _wilcoxon_p(a, b)
            delta = _cliffs_delta(a, b)
            direction = _LEARNING_SPEED_DIRECTION[metric]
            # Favourable tail: higher_better ⇒ H_A μ_diff>0 ⇒ evidence against
            # is P(boots≤0)=p_one_pos; lower_better ⇒ H_A μ_diff<0 ⇒ p_one_neg.
            p_fav = p_one_pos if direction == "higher_better" else p_one_neg
            # Censoring fraction: only meaningful for episodes_to_threshold.
            # Counts (arm,seed) cells right-censored at the horizon over the
            # paired seeds; a high value means the contrast is degenerate and
            # must NOT be read as a tie (see _LEARNING_SPEED_TIER).
            if metric == "episodes_to_threshold":
                cens = [on_cells[s].get("_episodes_to_threshold_censored", 0.0)
                        for s in seeds_common]
                cens += [off_cells[s].get("_episodes_to_threshold_censored", 0.0)
                         for s in seeds_common]
                censored_frac: object = (sum(cens) / len(cens)
                                         if cens else "")
            else:
                censored_frac = ""
            rows.append({
                "profile": prof,
                "metric": metric,
                "metric_tier": _LEARNING_SPEED_TIER[metric],
                "direction": direction,
                "censored_frac": censored_frac,
                "n_paired": len(seeds_common),
                "seeds_paired": ";".join(str(s) for s in seeds_common),
                "mean_diff_true_minus_false": mean_d,
                "ci_lo": lo,
                "ci_hi": hi,
                "p_bootstrap": p_boot,
                "p_one_sided_favorable": p_fav,
                "p_wilcoxon": p_wil,
                "cliffs_delta": delta,
            })
            ps.append(p_boot)

    tests_path = out_dir / "learning_speed_tests.csv"
    if rows:
        qs = _bh_qvalues(ps)
        for r, q in zip(rows, qs):
            r["q_bootstrap_bh"] = q
            r["bh_family_m"] = len(qs)
        cols = list(rows[0].keys())
        with tests_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)
    else:
        tests_path.write_text("", encoding="utf-8")
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


def write_paired_latex_table(paired_csv: Path, out_tex: Path) -> bool:
    """Render paired_tests.csv as a LaTeX tabular with BH q-values (S6-7).

    Columns: Profile, Metric, A vs B, family, n, mean diff [CI], p_boot,
    q_BH. Only emits the confirmatory family by default to keep the table
    paper-sized.
    """
    if not paired_csv.is_file():
        return False
    rows = list(csv.DictReader(paired_csv.open(encoding="utf-8")))
    rows = [r for r in rows if r.get("family") == "confirmatory"]
    if not rows:
        return False
    lines = [
        "% Auto-generated by analysis/sweep_report.py. Do not edit by hand.",
        "\\begin{tabular}{lllrlrr}",
        "\\toprule",
        "Profile & Metric & A vs B & n & mean diff [95\\% CI] & p & q (BH) \\\\",
        "\\midrule",
    ]
    for r in rows:
        try:
            mean_d = float(r["mean_diff"])
            lo = float(r["ci_lo"])
            hi = float(r["ci_hi"])
            cell = f"${mean_d:.3f}_{{[{lo:.3f},{hi:.3f}]}}$"
        except (TypeError, ValueError, KeyError):
            cell = "--"
        try:
            p = f"{float(r['p_bootstrap']):.4f}"
        except (TypeError, ValueError, KeyError):
            p = "--"
        try:
            q = f"{float(r['q_bootstrap_bh']):.4f}"
        except (TypeError, ValueError, KeyError):
            q = "--"
        mode_a = r["mode_a"].replace("_", "\\_")
        mode_b = r["mode_b"].replace("_", "\\_")
        lines.append(
            " & ".join([
                r["profile"],
                r["metric"].replace("_", "\\_"),
                f"{mode_a} vs {mode_b}",
                r["n_paired"],
                cell, p, q,
            ]) + " \\\\"
        )
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
    parser.add_argument("--family-tag", default=None,
                        help="Audit Step 6 S6-4: route outputs to "
                             "<out>/<family-tag>/ so main vs ablation_a/b/c "
                             "stat artefacts never overwrite each other. "
                             "Convention: 'main', 'ablation_a' (PBRS off), "
                             "'ablation_b' (no stereotypes), 'ablation_c' "
                             "(random Q-init).")
    parser.add_argument("--first-goal-root", default=None,
                        help="Audit Step 6 S6-3: parent dir containing "
                             "results_seed<N>/ for the PBRS-off ablation. "
                             "When set, first_goal_table.csv and "
                             "first_goal_wilcoxon.csv (H2) are written.")
    parser.add_argument("--speed-window", type=int, default=100,
                        help="rolling window (episodes) for the "
                             "episodes-to-threshold learning-speed metric "
                             "(default 100)")
    parser.add_argument("--speed-threshold", type=float, default=0.5,
                        help="rolling goal-rate threshold defining 'learned' "
                             "for the episodes-to-threshold metric "
                             "(default 0.5)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    if args.family_tag:
        out_dir = out_dir / args.family_tag
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
            # Audit Step 6 S6-3: H2 episodes-to-first-goal aggregation.
            ablation_roots: list[tuple[int, Path]] = []
            if args.first_goal_root:
                ab_parent = Path(args.first_goal_root)
                ablation_roots = find_seed_roots(ab_parent)
                if not ablation_roots:
                    print(f"sweep_report: --first-goal-root {ab_parent} "
                          f"contains no results_seed*/ — H2 wilcoxon skipped",
                          file=sys.stderr)
            n_fg = aggregate_first_goal(seed_roots,
                                        ablation_roots or None,
                                        out_dir,
                                        iters=args.ci_bootstrap_iters)
            print(f"sweep_report: wrote {n_fg} first-goal table rows "
                  f"(H2; ablation_roots={len(ablation_roots)})")
            # PRIMARY outcome: learning-speed stereotype contrast
            # (ql_true vs ql_false), paired per seed across the same tree.
            n_ls = learning_speed_tests(seed_roots, out_dir,
                                        iters=args.ci_bootstrap_iters,
                                        window=args.speed_window,
                                        thresh=args.speed_threshold)
            print(f"sweep_report: wrote {n_ls} learning-speed test rows "
                  f"to learning_speed_tests.csv "
                  f"(window={args.speed_window}, "
                  f"threshold={args.speed_threshold})")
            if write_latex_table(out_dir / "summary_table_ci.csv",
                                 out_dir / "summary_table_ci.tex"):
                print("sweep_report: summary_table_ci.tex written "
                      "(\\input{}-ready)")
            if write_paired_latex_table(out_dir / "paired_tests.csv",
                                        out_dir / "paired_tests.tex"):
                print("sweep_report: paired_tests.tex written "
                      "(\\input{}-ready, q-values included)")
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
