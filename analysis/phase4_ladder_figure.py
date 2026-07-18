"""
analysis/phase4_ladder_figure.py — the dependency-ladder efficiency-delta figure.

Reads the registered ``paired_tests.csv`` of the post-inversion confirmatory
Phase-4 run (run of record 29193486193, seeds 1..20) and renders the three
``ql_true − ql_false`` benchmark efficiency deltas along the dependency ladder:

    lab4      1 smart-plug gate,   depth 1
    lab4dual  2 smart-plug gates,  depth 1   (parallel breadth)
    lab4chain 1 gate,              depth 2   (breaker -> plug -> lamp, serial depth)

Three efficiency metrics are shown side by side per cell — ``avg_redundant``
(the registered primary), ``avg_steps`` and ``avg_wasted`` — each as the
seed-paired mean Δ with its 95% bootstrap CI. All deltas are negative (the
KG-primed arm is more efficient); the registered ladder prediction is that the
magnitude grows from lab4 to lab4dual and from lab4 to lab4chain.

Palette: dataviz reference categorical slots 1/2/3 (blue/aqua/yellow); validated
CVD worst-adjacent ΔE 47.2 (PASS). Every bar is direct-labelled, satisfying the
relief rule for the two sub-3:1 slots.

Usage
-----
    python analysis/phase4_ladder_figure.py
    python analysis/phase4_ladder_figure.py --paired <path/to/paired_tests.csv> --out <dir>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PAIRED = REPO / "phase4_postinv" / "run_29193486193" / "analysis" / "out" / "paired_tests.csv"
DEFAULT_OUT = REPO / "docs" / "_audit" / "figures"

# dataviz reference palette (validated: CVD worst adjacent ΔE 47.2, PASS in light).
C_REDUNDANT = "#2a78d6"   # slot 1 blue   — avg_redundant (registered primary)
C_STEPS = "#1baf7a"       # slot 2 aqua   — avg_steps
C_WASTED = "#eda100"      # slot 3 yellow — avg_wasted
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
SURFACE = "#fcfcfb"

# ladder cells left->right (increasing dependency structure) and their label rows
LADDER = [
    ("lab4", "lab4", "1 gate · depth 1"),
    ("lab4dual", "lab4dual", "2 gates · depth 1"),
    ("lab4chain", "lab4chain", "1 gate · depth 2"),
]
METRICS = [
    ("avg_redundant", "avg_redundant (primary)", C_REDUNDANT),
    ("avg_steps", "avg_steps", C_STEPS),
    ("avg_wasted", "avg_wasted", C_WASTED),
]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "legend.frameon": False,
})


def _row(df: pd.DataFrame, profile: str, metric: str) -> pd.Series:
    m = df[(df["profile"] == profile) & (df["metric"] == metric)
           & (df["mode_a"] == "ql_true") & (df["mode_b"] == "ql_false")]
    if len(m) != 1:
        raise SystemExit(f"expected exactly one row for {profile}/{metric} ql_true-ql_false, got {len(m)}")
    return m.iloc[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paired", type=Path, default=DEFAULT_PAIRED)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--run-id", default="29193486193")
    args = ap.parse_args()

    if not args.paired.exists():
        raise SystemExit(f"paired_tests.csv not found: {args.paired}")
    df = pd.read_csv(args.paired)

    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    n_cells, n_metrics = len(LADDER), len(METRICS)
    group_w = 0.82
    bar_w = group_w / n_metrics

    for gi, (prof, _, _) in enumerate(LADDER):
        for mi, (metric, _, color) in enumerate(METRICS):
            r = _row(df, prof, metric)
            d = float(r["mean_diff"])
            lo, hi = float(r["ci_lo"]), float(r["ci_hi"])
            x = gi + (mi - (n_metrics - 1) / 2) * bar_w
            err = [[d - lo], [hi - d]]
            ax.bar(x, d, width=bar_w * 0.9, color=color,
                   yerr=err, error_kw=dict(ecolor=INK2, capsize=2.5, lw=0.9))
            ax.text(x, lo - 0.05, f"{d:+.2f}", ha="center", va="top",
                    fontsize=7.3, color=INK, fontweight="bold")

    ax.axhline(0, color=BASE, lw=1.0)
    ax.set_xticks(range(n_cells))
    ax.set_xticklabels([f"{lbl}\n{sub}" for _, lbl, sub in LADDER], fontsize=9)
    ax.set_ylabel("Δ  ql_true − ql_false   (lower = KG-primed better)")
    ax.set_title("Phase 4 dependency ladder — KG efficiency gain grows with the dependency structure")
    fig.text(0.012, 0.945,
             f"run {args.run_id} · n = 20 seeds · benchmark means, seed-paired · error bars 95% bootstrap CI",
             fontsize=7.5, color=MUTED, ha="left", va="top")

    # headroom for the ↓ annotation and value labels
    ymin = min(float(_row(df, p, m)["ci_lo"]) for p, _, _ in LADDER for m, _, _ in METRICS)
    ax.set_ylim(ymin - 0.35, 0.28)

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in METRICS]
    ax.legend(handles, [lbl for _, lbl, _ in METRICS], loc="lower left",
              fontsize=8, ncols=3, columnspacing=1.0, bbox_to_anchor=(0.0, -0.005))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    src = args.paired.relative_to(REPO).as_posix() if args.paired.is_relative_to(REPO) else str(args.paired)
    fig.text(0.012, 0.005, f"Source: {src}", fontsize=6.5, color=MUTED, ha="left", va="bottom")

    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / "p4_ladder_efficiency_deltas.png"
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
