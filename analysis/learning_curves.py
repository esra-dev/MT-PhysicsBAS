"""
analysis/learning_curves.py — Multi-seed learning curves with 95% bootstrap bands.

For each profile, render per-zone reward learning curves for stereo=true vs
stereo=false, with one curve per condition and a shaded 95% bootstrap band
across seeds. Outputs both PNG (for the thesis) and PGF (for the LaTeX paper).

Inputs
------
Discovers per-seed roots beneath ``--root`` matching ``results_seed<N>``.
Within each root it expects training metrics CSVs at::

    <root>/<profile>/training_stereo_<stereo>/metrics_stereotypes_<stereo>_<profile>.csv

with columns: Episode, Steps, RewardZ1, RewardZ2, GoalReached, Epsilon, ...
If those nested files are not present, falls back to the top-level repo files
``metrics_stereotypes_<stereo>_<profile>.csv`` (single-seed mode).

Usage
-----
    python analysis/learning_curves.py --root . --out analysis/out
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


SEED_DIR_RE = re.compile(r"^results_seed(\d+)$")
METRIC_FILE_RE = re.compile(r"metrics_stereotypes_(true|false)_([^.]+)\.csv$")
REWARD_COLS = ("RewardZ1", "RewardZ2")


def find_seed_roots(root: Path) -> list[tuple[int, Path]]:
    """Discover results_seed<N> directories under root, root/benchmark, or root itself."""
    candidates = [root, root / "benchmark"]
    out: list[tuple[int, Path]] = []
    seen: set[Path] = set()
    for c in candidates:
        if not c.is_dir():
            continue
        for p in sorted(c.iterdir()):
            if not p.is_dir():
                continue
            m = SEED_DIR_RE.match(p.name)
            if m and p not in seen:
                out.append((int(m.group(1)), p))
                seen.add(p)
    return out


def _load_metric_csv(path: Path) -> dict[str, list[float]]:
    """Return {col: [values]} for the CSV, or {} on failure."""
    if not path.is_file():
        return {}
    cols: dict[str, list[float]] = defaultdict(list)
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                for k, v in row.items():
                    if v is None or v == "":
                        continue
                    try:
                        cols[k].append(float(v))
                    except ValueError:
                        pass
    except OSError:
        return {}
    return dict(cols)


def _discover_metrics(root: Path) -> dict[tuple[str, str], Path]:
    """Return {(profile, stereo): metric_csv_path} for a given seed root.

    Searches nested training output first, then the seed-root-relative
    top-level files (matches what run_full_project.ps1 emits).
    """
    out: dict[tuple[str, str], Path] = {}
    # Nested: <root>/<profile>/training_stereo_<bool>/metrics_*.csv
    if root.is_dir():
        for prof_dir in sorted(root.iterdir()):
            if not prof_dir.is_dir():
                continue
            for stereo in ("true", "false"):
                train_dir = prof_dir / f"training_stereo_{stereo}"
                if not train_dir.is_dir():
                    continue
                candidate = train_dir / f"metrics_stereotypes_{stereo}_{prof_dir.name}.csv"
                if candidate.is_file():
                    out[(prof_dir.name, stereo)] = candidate
    # Top-level fallback
    if root.is_dir():
        for p in sorted(root.glob("metrics_stereotypes_*.csv")):
            m = METRIC_FILE_RE.search(p.name)
            if not m:
                continue
            stereo, prof = m.group(1), m.group(2)
            out.setdefault((prof, stereo), p)
    return out


def _bootstrap_band(series_by_seed: list[list[float]],
                    iters: int = 2000) -> tuple[list[float], list[float], list[float]]:
    """Return (mean, lo, hi) per episode index across seeds (truncated to min length)."""
    if not series_by_seed:
        return ([], [], [])
    try:
        import numpy as np  # type: ignore
    except ImportError:
        return ([], [], [])
    n_min = min(len(s) for s in series_by_seed)
    if n_min == 0:
        return ([], [], [])
    mat = np.asarray([s[:n_min] for s in series_by_seed], dtype=float)  # (S, T)
    s = mat.shape[0]
    if s < 2:
        mean = mat.mean(axis=0).tolist()
        return (mean, mean, mean)
    rng = np.random.default_rng(0xC1)
    boots = np.empty((iters, n_min), dtype=float)
    for i in range(iters):
        idx = rng.integers(0, s, size=s)
        boots[i] = mat[idx].mean(axis=0)
    mean = mat.mean(axis=0)
    lo = np.quantile(boots, 0.025, axis=0)
    hi = np.quantile(boots, 0.975, axis=0)
    return (mean.tolist(), lo.tolist(), hi.tolist())


def _smooth(values: list[float], window: int = 25) -> list[float]:
    if not values or window <= 1:
        return values
    try:
        import numpy as np  # type: ignore
        arr = np.asarray(values, dtype=float)
        # Same-length moving average with edge handling via cumulative sums.
        c = np.cumsum(np.insert(arr, 0, 0.0))
        if arr.size >= window:
            smoothed = c[window:] - c[:-window]
            head = arr[: window - 1].cumsum() / np.arange(1, window)
            tail = smoothed / window
            return np.concatenate([head, tail]).tolist()
        # Audit Step 6 \u00a75.2: denom only meaningful on this short-input branch.
        denom = np.minimum(np.arange(1, arr.size + 1), window)
        return (arr.cumsum() / denom).tolist()
    except ImportError:
        out = []
        s = 0.0
        for i, v in enumerate(values):
            s += v
            if i >= window:
                s -= values[i - window]
            out.append(s / min(i + 1, window))
        return out


def _render_panel(ax, episodes, mean, lo, hi, label: str, color: str, smooth_window: int) -> None:
    m = _smooth(mean, smooth_window)
    l = _smooth(lo, smooth_window)
    h = _smooth(hi, smooth_window)
    ax.plot(episodes[: len(m)], m, label=label, color=color, linewidth=1.5)
    if l and h:
        ax.fill_between(episodes[: len(m)], l, h, color=color, alpha=0.2, linewidth=0)


def render_curves(seed_roots: list[tuple[int, Path]],
                  out_dir: Path,
                  smooth_window: int = 25,
                  also_pgf: bool = True) -> int:
    """Write PNG + PGF panels per profile, returning the number of profiles drawn."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: F401
    except ImportError:
        print("learning_curves: matplotlib not available; skipping", file=sys.stderr)
        return 0

    # series[profile][stereo][reward_col] -> list of per-seed series
    series: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for seed, root in seed_roots:
        files = _discover_metrics(root)
        for (prof, stereo), path in files.items():
            cols = _load_metric_csv(path)
            for rcol in REWARD_COLS:
                if rcol in cols:
                    series[prof][stereo][rcol].append(cols[rcol])

    if not series:
        print("learning_curves: no metric CSVs discovered under seed roots", file=sys.stderr)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    drawn = 0
    for prof in sorted(series.keys()):
        fig, axes = plt.subplots(1, len(REWARD_COLS), figsize=(10, 3.6), sharex=True)
        if len(REWARD_COLS) == 1:
            axes = [axes]
        any_drawn = False
        for ax, rcol in zip(axes, REWARD_COLS):
            for stereo, color in (("true", "#1f77b4"), ("false", "#d62728")):
                runs = series[prof].get(stereo, {}).get(rcol, [])
                if not runs:
                    continue
                mean, lo, hi = _bootstrap_band(runs)
                if not mean:
                    continue
                episodes = list(range(len(mean)))
                label = f"stereo={stereo} (n={len(runs)})"
                _render_panel(ax, episodes, mean, lo, hi, label, color, smooth_window)
                any_drawn = True
            ax.set_title(f"{prof} — {rcol}")
            ax.set_xlabel("Episode")
            ax.set_ylabel("Reward")
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        if any_drawn:
            png_path = out_dir / f"learning_curve_{prof}.png"
            fig.savefig(png_path, dpi=150)
            if also_pgf:
                try:
                    fig.savefig(out_dir / f"learning_curve_{prof}.pgf")
                except Exception as exc:  # pragma: no cover - backend-dependent
                    print(f"learning_curves: PGF export failed for {prof}: {exc}",
                          file=sys.stderr)
            drawn += 1
        plt.close(fig)
    return drawn


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".",
                   help="search base; looks for results_seed* here and under ./benchmark")
    p.add_argument("--out", default="analysis/out",
                   help="output directory for PNG/PGF figures")
    p.add_argument("--smooth", type=int, default=25,
                   help="moving-average window for visual smoothing")
    p.add_argument("--no-pgf", action="store_true",
                   help="skip PGF export (PNG only)")
    args = p.parse_args(argv)

    root = Path(args.root)
    seed_roots = find_seed_roots(root)
    if not seed_roots:
        # Single-seed fallback: treat root itself as the only seed source.
        seed_roots = [(1, root)]
        print(f"learning_curves: no results_seed* found under {root.resolve()}; "
              f"falling back to single-seed mode", file=sys.stderr)
    else:
        print(f"learning_curves: discovered {len(seed_roots)} seed root(s): "
              + ", ".join(f"seed={s}" for s, _ in seed_roots))
    drawn = render_curves(seed_roots, Path(args.out),
                          smooth_window=args.smooth,
                          also_pgf=not args.no_pgf)
    print(f"learning_curves: drew {drawn} profile panel(s) -> {Path(args.out).resolve()}")
    return 0 if drawn > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
