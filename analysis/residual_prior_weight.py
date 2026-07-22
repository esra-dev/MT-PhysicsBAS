"""Residual-prior quantification for the decay-horizon (E) footnote.

Computes the end-of-training residual stereotype-prior weight per (state, action)
cell from the training visit-count sidecars (qtable_final_*_visits.csv) of

  (a) the arm-C run of record  phase1_postinv/run_29639767776/  (root convenience
      copies = last-aggregated training cell per lab/arm; per-seed sidecars are
      pruned from the archive), and
  (b) phase1_xzone_mid/ (run 28941204656, phase1_kg_xzone = arm C + cross-zone
      bonus), which retains per-seed sidecars under benchmark/results_seed*/.

Formula (QLearner.greedyAction, identical at both run heads e631877 / 79da114):

    w(s,a) = w_ep * min(1, PRIOR_FADE_VISITS / v(s,a))        [v=0 -> cellMul=1]
    w_ep   = 1 - min(1, N_train / E) * (1 - floor)

Both runs: N_train = 3000, E = 10000, floor = 0, scale = 1, adaptive trust OFF
=> w_ep = 0.70 exactly, and w(s,a) > 0.5  <=>  v(s,a) <= 34.
At E <= N_train the residual is identically 0 (floor reached at/before the end),
so no computation is needed for the E=750/E=3000 sweep points.

Population note: the sidecars record TRAINING visits of the table the benchmark
runs on; per-seed bench step logs for the run of record are pruned (archive
MANIFEST) and trace_bench_*.jsonl files are empty, so "states" below means
states visited during training (the sidecar rows) -- the benchmark-relevant
superset of the greedy corridor -- not states logged during bench episodes.

Output: analysis/out/residual_prior_weight.csv + a console table.
"""

import csv
import hashlib
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W_EP = 0.70          # 1 - 3000/10000 * (1 - 0.0)
FADE = 25            # -Dstereo.priorFadeVisits default at both heads
THRESH = 0.5
N_STATES = {"lab1": 8, "lab2": 1024, "lab3": 2048}
SEEDS = range(1, 11)
LABS = ["lab1", "lab2", "lab3"]


def cell_w(v: int) -> float:
    if v <= 0:
        return W_EP
    return W_EP * min(1.0, FADE / v)


def read_sidecar(path: Path):
    """-> list of (state_idx, [visits per action])"""
    rows = []
    with open(path, newline="") as f:
        r = csv.reader(f)
        header = next(r)
        for line in r:
            if not line:
                continue
            rows.append((int(line[0]), [int(x) for x in line[1:]]))
    return header[1:], rows


def stats_for(path: Path, lab: str):
    actions, rows = read_sidecar(path)
    n_actions = len(actions)
    all_w, state_median_w, backbone_w, backbone_v = [], [], [], []
    total_visits = 0
    n_states_any_faded = 0       # >=1 cell with w <= THRESH (v >= 35)
    n_states_backbone_faded = 0  # most-visited action faded (vmax >= 35)
    for _, visits in rows:
        ws = [cell_w(v) for v in visits]
        all_w.extend(ws)
        state_median_w.append(statistics.median(ws))
        vmax = max(visits)
        backbone_v.append(vmax)
        backbone_w.append(cell_w(vmax))
        total_visits += sum(visits)
        if any(w <= THRESH for w in ws):
            n_states_any_faded += 1
        if cell_w(vmax) <= THRESH:
            n_states_backbone_faded += 1
    n_states_visited = len(rows)
    return {
        "n_actions": n_actions,
        "states_visited": n_states_visited,
        "state_space": N_STATES[lab],
        "cells": n_states_visited * n_actions,
        "total_visits": total_visits,
        "median_cell_w": statistics.median(all_w),
        "pct_cells_w_gt": 100.0 * sum(w > THRESH for w in all_w) / len(all_w),
        "pct_states_w_gt": 100.0 * sum(w > THRESH for w in state_median_w) / n_states_visited,
        "median_backbone_w": statistics.median(backbone_w),
        "median_backbone_v": statistics.median(backbone_v),
        "n_states_any_faded": n_states_any_faded,
        "n_states_backbone_faded": n_states_backbone_faded,
    }


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main():
    out_rows = []

    # --- (a) arm-C run of record: root convenience sidecars (single cell) -----
    armc = ROOT / "phase1_postinv" / "run_29639767776"
    for lab in LABS:
        for arm in ["true", "false"]:
            p = armc / f"qtable_final_stereotypes_{arm}_{lab}_visits.csv"
            s = stats_for(p, lab)
            s.update(dataset="armC_29639767776_root", lab=lab, arm=arm, seed="last-aggregated")
            out_rows.append(s)

    # --- (b) xzone_mid: per-seed sidecars ------------------------------------
    xz = ROOT / "phase1_xzone_mid"
    per_seed = {}
    for lab in LABS:
        for arm in ["true", "false"]:
            mode = "ql_true" if arm == "true" else "ql_false"
            for seed in SEEDS:
                p = (xz / "benchmark" / f"results_seed{seed}" / lab / mode /
                     f"qtable_final_stereotypes_{arm}_{lab}_visits.csv")
                s = stats_for(p, lab)
                s.update(dataset="xzone_mid_28941204656", lab=lab, arm=arm, seed=seed)
                out_rows.append(s)
                per_seed.setdefault((lab, arm), []).append(s)

    # sanity 1: the same-arm sidecar is byte-identical across the three mode
    # dirs of a seed (they are provenance copies of one training cell)
    for lab in ["lab2", "lab3"]:
        hs = {m: md5(xz / "benchmark" / "results_seed1" / lab / m /
                     f"qtable_final_stereotypes_true_{lab}_visits.csv")
              for m in ["ql_true", "ql_false", "rule_based"]}
        assert len(set(hs.values())) == 1, f"seed1 {lab} copies differ: {hs}"

    # sanity 2: which seed do the root convenience copies equal?
    for lab in LABS:
        root_h = md5(xz / f"qtable_final_stereotypes_true_{lab}_visits.csv")
        match = [s for s in SEEDS
                 if md5(xz / "benchmark" / f"results_seed{s}" / lab / "ql_true" /
                        f"qtable_final_stereotypes_true_{lab}_visits.csv") == root_h]
        print(f"xzone root sidecar {lab} (KG arm) matches seed(s): {match}")

    # --- write CSV ------------------------------------------------------------
    outdir = ROOT / "analysis" / "out"
    outdir.mkdir(exist_ok=True)
    cols = ["dataset", "lab", "arm", "seed", "n_actions", "states_visited",
            "state_space", "cells", "total_visits", "median_cell_w",
            "pct_cells_w_gt", "pct_states_w_gt", "median_backbone_w",
            "median_backbone_v", "n_states_any_faded", "n_states_backbone_faded"]
    with open(outdir / "residual_prior_weight.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({k: r[k] for k in cols} for r in out_rows)

    # --- console summary ------------------------------------------------------
    def fmt(v, nd=3):
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)

    print(f"\nw(s,a) = {W_EP} * min(1, {FADE}/v);  w > {THRESH} <=> v < {FADE * W_EP / THRESH:.1f}"
          f" (i.e. v <= 34)\n")
    hdr = (f"{'dataset':26} {'lab':5} {'arm':5} {'seed':6} {'st.vis':>7} {'totV':>7} {'medW':>6} "
           f"{'%cells>':>8} {'%states>':>9} {'bbW':>6} {'bbV':>6} {'anyFad':>7} {'bbFad':>6}")
    print(hdr)
    for r in out_rows:
        if r["dataset"].startswith("armC"):
            print(f"{r['dataset']:26} {r['lab']:5} {r['arm']:5} {str(r['seed'])[:6]:6} "
                  f"{r['states_visited']:>7} {r['total_visits']:>7} {fmt(r['median_cell_w']):>6} "
                  f"{fmt(r['pct_cells_w_gt'], 1):>8} {fmt(r['pct_states_w_gt'], 1):>9} "
                  f"{fmt(r['median_backbone_w']):>6} {fmt(r['median_backbone_v'], 0):>6} "
                  f"{r['n_states_any_faded']:>7} {r['n_states_backbone_faded']:>6}")
    print()
    for (lab, arm), ss in per_seed.items():
        agg = {}
        for k in ["states_visited", "total_visits", "median_cell_w", "pct_cells_w_gt",
                  "pct_states_w_gt", "median_backbone_w", "median_backbone_v",
                  "n_states_any_faded", "n_states_backbone_faded"]:
            vals = [s[k] for s in ss]
            agg[k] = (statistics.median(vals), min(vals), max(vals))
        print(f"xzone_mid {lab} arm={arm}: "
              f"st.vis={agg['states_visited'][0]:.0f} [{agg['states_visited'][1]}-{agg['states_visited'][2]}]  "
              f"totV={agg['total_visits'][0]:.0f} [{agg['total_visits'][1]}-{agg['total_visits'][2]}]  "
              f"medW={agg['median_cell_w'][0]:.3f} [{agg['median_cell_w'][1]:.3f}-{agg['median_cell_w'][2]:.3f}]  "
              f"%cells>{THRESH}={agg['pct_cells_w_gt'][0]:.1f} [{agg['pct_cells_w_gt'][1]:.1f}-{agg['pct_cells_w_gt'][2]:.1f}]  "
              f"%states>{THRESH}={agg['pct_states_w_gt'][0]:.1f} [{agg['pct_states_w_gt'][1]:.1f}-{agg['pct_states_w_gt'][2]:.1f}]  "
              f"bbW={agg['median_backbone_w'][0]:.3f} [{agg['median_backbone_w'][1]:.3f}-{agg['median_backbone_w'][2]:.3f}]  "
              f"bbV={agg['median_backbone_v'][0]:.0f}  "
              f"anyFad={agg['n_states_any_faded'][0]:.0f} [{agg['n_states_any_faded'][1]}-{agg['n_states_any_faded'][2]}]  "
              f"bbFad={agg['n_states_backbone_faded'][0]:.0f} [{agg['n_states_backbone_faded'][1]}-{agg['n_states_backbone_faded'][2]}]")


if __name__ == "__main__":
    main()
