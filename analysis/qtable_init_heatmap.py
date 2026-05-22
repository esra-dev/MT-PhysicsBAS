"""
qtable_init_heatmap.py — Slide 6 visual.

Render side-by-side heatmaps of the *initial* Q-tables for the 2-zone custom
lab, with stereotype priors OFF vs ON.  This visualises the symbolic prior
that the StereotypeReasoner imprints on the Q-table before any training step.

Inputs (produced at training start by saveQTable in QLearner.java):
    qtable_initial_stereotypes_false.csv
    qtable_initial_stereotypes_true.csv
  Both expected at the project root.  CSV format:
    header row  : state_index, action_0_label, action_1_label, ...
    data rows   : <state idx>, <Q-value for each action>

Output:
    analysis/out/qtable_init_heatmap.png
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "analysis" / "out"


def load_qtable(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"{path} is empty")
    header = rows[0]
    action_labels = header[1:]
    data = np.array([[float(x) for x in r[1:]] for r in rows[1:]], dtype=float)
    return action_labels, data


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p_off = ROOT / "qtable_initial_stereotypes_false.csv"
    p_on  = ROOT / "qtable_initial_stereotypes_true.csv"
    if not p_off.is_file() or not p_on.is_file():
        print(f"[!] Missing Q-table CSVs at project root.\n"
              f"    Expected: {p_off.name}, {p_on.name}\n"
              f"    Run `gradlew taskQl` once with use_stereotypes(false) and once with (true)\n"
              f"    on the 2-zone profile (active_profile(\"custom\"))." , file=sys.stderr)
        sys.exit(1)

    labels_off, q_off = load_qtable(p_off)
    labels_on,  q_on  = load_qtable(p_on)

    vmax = max(abs(q_off).max(), abs(q_on).max(), 1.0)
    vmin = -vmax

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, q, t, labels in [
        (axes[0], q_off, "use_stereotypes = False  (zero init)",         labels_off),
        (axes[1], q_on,  "use_stereotypes = True   (ontology priors)",   labels_on),
    ]:
        im = ax.imshow(q, aspect="auto", cmap="RdBu", vmin=vmin, vmax=vmax)
        ax.set_title(t)
        ax.set_xlabel("action")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=80, fontsize=7)

    axes[0].set_ylabel("state index")
    fig.colorbar(im, ax=axes, label="Q init value", shrink=0.8)
    fig.suptitle("Initial Q-table — stereotype priors imprint negative penalties "
                 "on impossible / wasteful actions", y=1.02, fontsize=11)

    out = OUT_DIR / "qtable_init_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"[ok] {out}")


if __name__ == "__main__":
    main()
