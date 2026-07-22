"""
analysis/audit_results_figures.py — Audit figures + extracted stats tables (NEW era only).

Reads ONLY the canonical final-run CSVs indexed in docs/_audit/05_results_index.md and
produces:

  docs/_audit/figures/*.png          (source path printed inside every figure)
  docs/_audit/20_results_extracted.md (Markdown tables; every cell from a real CSV)

Canonical inputs (per docs/_audit/05_results_index.md §7):

  Phase 1 headline  run 27336756264  phase1_headline_download/kg_only/
                    per-seed curves:  benchmark/results_seed<N>/<lab>/training_stereo_<tag>/
                                      metrics_stereotypes_<tag>_<lab>.csv
                    stats:            analysis/out/{learning_speed_tests,learning_speed_table,
                                      paired_tests}.csv
  Phase 1 xzone-mid run 28941204656  phase1_xzone_mid/            (current lab3 physics)
  Phase 2 registered pooled          analysis/out_phase2_registered/
                                     {phase2_recovery_ci,phase2_recovery_paired}.csv
  Phase 3 n=10      run 27621106006  phase3_download_n10/phase3-consolidated/analysis/out/
                                     {phase3_delay_accuracy,phase3_compliance_ci,
                                      phase3_compliance_paired}.csv
  Phase 4 n=20      run 27905392725  phase4_n20_download/phase4-consolidated/analysis/out/
                                     {phase4_energy_ci,phase4_energy_paired,
                                      phase4_llm_summary}.csv

No value is computed from anything other than these files. Missing files are skipped
and the skip is recorded in 20_results_extracted.md.

Usage:  python analysis/audit_results_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
FIG_DIR = REPO / "docs" / "_audit" / "figures"
MD_PATH = REPO / "docs" / "_audit" / "20_results_extracted.md"

# ---------------------------------------------------------------- palette ---
# dataviz reference palette (validated: CVD worst adjacent dE 24.2, PASS).
# Fixed slot order — never re-assigned per figure.
C_QL_TRUE = "#2a78d6"   # slot 1 blue   — KG-primed arm (ql_true / stereo true)
C_QL_FALSE = "#1baf7a"  # slot 2 aqua   — baseline arm  (ql_false)
C_RULE = "#eda100"      # slot 3 yellow — rule_based
C_LLM = "#008300"       # slot 4 green  — LLM baseline
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
SURFACE = "#fcfcfb"

ARM_LABEL = {"ql_true": "QL + KG (ql_true)", "ql_false": "QL baseline (ql_false)",
             "rule_based": "rule-based", "llm": "LLM baseline"}
ARM_COLOR = {"ql_true": C_QL_TRUE, "ql_false": C_QL_FALSE,
             "rule_based": C_RULE, "llm": C_LLM}

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

SKIPPED: list[str] = []
MD: list[str] = []


def _exists(path: Path, what: str) -> bool:
    if path.exists():
        return True
    SKIPPED.append(f"{what}: `{path.relative_to(REPO)}` MISSING — skipped")
    return False


def _despine(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _src_note(fig, *paths: Path):
    txt = "Source: " + "  ·  ".join(p.relative_to(REPO).as_posix() for p in paths)
    fig.text(0.01, 0.005, txt, fontsize=6.5, color=MUTED, ha="left", va="bottom")


def _save(fig, name: str):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / name
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out.relative_to(REPO)}")


def _fmt(v) -> str:
    """Display formatting only — underlying CSV values are untouched."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "nan"
    if isinstance(v, (bool, np.bool_)):
        return str(bool(v))
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    f = float(v)
    if f == int(f) and abs(f) < 1e6:
        return str(int(f))
    return f"{f:.4g}"


def _md_table(df: pd.DataFrame, cols: list[str], header_map: dict[str, str] | None = None) -> str:
    header_map = header_map or {}
    heads = [header_map.get(c, c) for c in cols]
    lines = ["| " + " | ".join(heads) + " |",
             "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            cells.append(str(v) if isinstance(v, str) else _fmt(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _boot_band(mat: np.ndarray, n_boot: int = 1000, seed: int = 12345):
    """mat: (n_seeds, n_episodes). Returns mean, lo, hi (95% bootstrap CI of the mean)."""
    rng = np.random.default_rng(seed)
    n = mat.shape[0]
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = mat[idx].mean(axis=1)          # (n_boot, n_episodes)
    return mat.mean(axis=0), np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)


# =====================================================================
# Phase 1 — learning curves from per-seed training metrics
# =====================================================================

def load_phase1_seed_matrix(dl_root: Path, lab: str, stereo_tag: str):
    """Stack per-seed metrics CSVs -> dict of (n_seeds, n_episodes) arrays."""
    frames = []
    for seed_dir in sorted(dl_root.glob("benchmark/results_seed*")):
        p = (seed_dir / lab / f"training_stereo_{stereo_tag}"
             / f"metrics_stereotypes_{stereo_tag}_{lab}.csv")
        if p.exists():
            frames.append(pd.read_csv(p))
    if not frames:
        return None
    n_ep = min(len(f) for f in frames)
    out = {}
    for col in ("GoalReached", "WastedByPenalty", "WastedByNoEffect"):
        out[col] = np.stack([f[col].to_numpy(dtype=float)[:n_ep] for f in frames])
    out["n_seeds"] = len(frames)
    return out


def phase1_curves(dl_root: Path, run_id: str, run_label: str, labs: list[str],
                  fname_prefix: str):
    ls_table = dl_root / "analysis" / "out" / "learning_speed_table.csv"
    have_ls = _exists(ls_table, f"{run_label} learning_speed_table")
    ls = pd.read_csv(ls_table) if have_ls else None

    for lab in labs:
        data = {}
        for tag, arm in (("true", "ql_true"), ("false", "ql_false")):
            m = load_phase1_seed_matrix(dl_root, lab, tag)
            if m is None:
                SKIPPED.append(f"{run_label} {lab} stereo={tag}: no per-seed "
                               f"metrics under `{dl_root.relative_to(REPO)}/benchmark/` — figure skipped")
            data[arm] = m
        if data["ql_true"] is None or data["ql_false"] is None:
            continue

        n_ep = min(data[a]["GoalReached"].shape[1] for a in data)
        win = max(10, n_ep // 60)

        fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.1))
        fig.suptitle(f"Phase 1 [{run_label}, run {run_id}] — {lab}: "
                     f"QL + KG vs QL baseline (n = {data['ql_true']['n_seeds']} seeds)",
                     fontsize=10.5, fontweight="bold", x=0.01, ha="left")

        # (a) rolling goal rate
        ax = axes[0]
        for arm in ("ql_true", "ql_false"):
            g = data[arm]["GoalReached"][:, :n_ep]
            roll = pd.DataFrame(g.T).rolling(win, min_periods=1).mean().to_numpy().T
            mean, lo, hi = _boot_band(roll)
            x = np.arange(n_ep)
            ax.plot(x, mean, color=ARM_COLOR[arm], lw=2, label=ARM_LABEL[arm])
            ax.fill_between(x, lo, hi, color=ARM_COLOR[arm], alpha=0.18, lw=0)
        ax.set_title(f"Goal rate (rolling {win}-ep mean)")
        ax.set_xlabel("training episode")
        ax.set_ylabel("goal rate")
        ax.set_ylim(-0.02, 1.05)
        ax.legend(loc="lower right", fontsize=8)
        _despine(ax)

        # (b) rolling wasted/redundant actions per episode
        ax = axes[1]
        for arm in ("ql_true", "ql_false"):
            w = (data[arm]["WastedByPenalty"][:, :n_ep]
                 + data[arm]["WastedByNoEffect"][:, :n_ep])
            roll = pd.DataFrame(w.T).rolling(win, min_periods=1).mean().to_numpy().T
            mean, lo, hi = _boot_band(roll)
            x = np.arange(n_ep)
            ax.plot(x, mean, color=ARM_COLOR[arm], lw=2, label=ARM_LABEL[arm])
            ax.fill_between(x, lo, hi, color=ARM_COLOR[arm], alpha=0.18, lw=0)
        ax.set_title("Redundant actions / episode\n(WastedByPenalty + WastedByNoEffect)")
        ax.set_xlabel("training episode")
        ax.set_ylabel("wasted actions")
        _despine(ax)

        # (c) mean first-goal episode with 95% CI (from learning_speed_table.csv)
        ax = axes[2]
        if ls is not None:
            rows = ls[(ls["profile"] == lab) & (ls["metric"] == "mean_first_goal")]
            ypos, labels = [], []
            for i, arm in enumerate(("ql_true", "ql_false")):
                r = rows[rows["condition"] == arm]
                if r.empty:
                    continue
                r = r.iloc[0]
                err = [[r["mean"] - r["ci_lo"]], [r["ci_hi"] - r["mean"]]]
                ax.barh(i, r["mean"], xerr=err, color=ARM_COLOR[arm], height=0.55,
                        error_kw=dict(ecolor=INK2, capsize=3, lw=1))
                ax.text(r["ci_hi"] + 0.02 * max(rows["ci_hi"]), i, _fmt(r["mean"]),
                        va="center", ha="left", fontsize=8.5, color=INK)
                ypos.append(i)
                labels.append(ARM_LABEL[arm])
            ax.set_yticks(ypos)
            ax.set_yticklabels(labels, fontsize=8)
            ax.invert_yaxis()
            ax.set_title("Mean first-goal episode (95% CI)")
            ax.set_xlabel("episode (lower = faster)")
            _despine(ax)
        else:
            ax.set_axis_off()

        _src_note(fig,
                  dl_root / "benchmark" / "results_seed<N>" / lab / "training_stereo_<tag>"
                  / f"metrics_stereotypes_<tag>_{lab}.csv",
                  ls_table)
        fig.tight_layout(rect=(0, 0.03, 1, 0.93))
        _save(fig, f"{fname_prefix}_{lab}_curves.png")


def phase1_tables():
    MD.append("\n## 1. Phase 1 — KG acceleration on clean labs [NEW era]\n")

    for run_label, run_id, folder, note in (
        ("kg_only headline", "27336756264", REPO / "phase1_headline_download" / "kg_only",
         "Arm C vs arm A (KG isolated, PBRS off), seeds 1–10, labs lab1–lab3 "
         "(lab3 = old spill physics: lamp 150 lux / blind 0.40·sun)."),
        ("xzone-mid", "28941204656", REPO / "phase1_xzone_mid",
         "Intermediate-bleed rerun on current lab3 physics (lamp 100 lux / blind "
         "0.30·sun, commit ad3cb3b), `cross_zone_bonus = 3.0`, seeds 1–10."),
    ):
        MD.append(f"\n### 1.{1 if 'headline' in run_label else 2} Run {run_id} ({run_label})\n\n{note}\n")

        lst = folder / "analysis" / "out" / "learning_speed_tests.csv"
        if _exists(lst, f"{run_label} learning_speed_tests"):
            df = pd.read_csv(lst)
            MD.append("\n**Learning-speed paired tests (ql_true − ql_false, seed-paired):**\n")
            MD.append(_md_table(df, ["profile", "metric", "metric_tier", "direction",
                                     "n_paired", "mean_diff_true_minus_false",
                                     "ci_lo", "ci_hi", "p_bootstrap", "p_wilcoxon",
                                     "cliffs_delta", "q_bootstrap_bh", "bh_family_m"],
                                {"mean_diff_true_minus_false": "Δ (true−false)",
                                 "cliffs_delta": "Cliff's δ", "q_bootstrap_bh": "BH q"}))
            MD.append(f"\nSource: `{lst.relative_to(REPO).as_posix()}`\n")

        pt = folder / "analysis" / "out" / "paired_tests.csv"
        if _exists(pt, f"{run_label} paired_tests"):
            df = pd.read_csv(pt)
            df = df[(df["mode_a"] == "ql_true") & (df["mode_b"] == "ql_false")]
            MD.append("\n**Benchmark paired tests, ql_true vs ql_false (confirmatory family):**\n")
            MD.append(_md_table(df, ["profile", "metric", "n_paired", "mean_diff",
                                     "ci_lo", "ci_hi", "p_bootstrap", "p_wilcoxon",
                                     "cliffs_delta", "q_bootstrap_bh", "bh_family_m"],
                                {"mean_diff": "Δ (true−false)", "cliffs_delta": "Cliff's δ",
                                 "q_bootstrap_bh": "BH q"}))
            MD.append(f"\nSource: `{pt.relative_to(REPO).as_posix()}`\n")


# =====================================================================
# Phase 2 — registered pooled recovery + detection
# =====================================================================

def phase2_figures_tables():
    ci_p = REPO / "analysis" / "out_phase2_registered" / "phase2_recovery_ci.csv"
    pr_p = REPO / "analysis" / "out_phase2_registered" / "phase2_recovery_paired.csv"
    if not (_exists(ci_p, "Phase 2 registered CI") and _exists(pr_p, "Phase 2 registered paired")):
        return
    ci = pd.read_csv(ci_p)
    pr = pd.read_csv(pr_p)

    rec_q = {r["profile"]: r for _, r in
             pr[pr["metric"] == "RecoveryEpisodes"].iterrows()}

    # --- recovery bars, split by registered tier -------------------------
    tiers = ci[["profile", "recovery_tier"]].drop_duplicates().set_index("profile")["recovery_tier"]
    conf = sorted(p for p in tiers.index if tiers[p] == "confirmatory")
    rest = sorted(p for p in tiers.index if tiers[p] != "confirmatory")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 0.42 * max(len(conf), len(rest)) + 1.8),
                             sharex=False)
    fig.suptitle("Phase 2 [registered pooled, §9.7 runs of record] — recovery episodes "
                 "(mean ± 95% bootstrap CI, n = 10 seeds/cell)",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    for ax, profs, title in ((axes[0], conf, "Tier-1 confirmatory family (m = 8)"),
                             (axes[1], rest, "Descriptive / ill-posed cells (no BH q)")):
        yc = np.arange(len(profs))
        nan_by_prof: dict[str, list[str]] = {}
        for off, arm in ((-0.19, "ql_true"), (0.19, "ql_false")):
            sub = ci[ci["mode"] == arm].set_index("profile")
            means = np.array([sub.loc[p, "RecoveryEpisodes_mean"] for p in profs])
            los = np.array([sub.loc[p, "RecoveryEpisodes_ci_lo"] for p in profs])
            his = np.array([sub.loc[p, "RecoveryEpisodes_ci_hi"] for p in profs])
            # NaN mean = no run re-converged (n_reconverged = 0 in the CSV) —
            # annotate rather than leave an invisible bar; NaN CI = single run.
            err = [np.nan_to_num(means - los), np.nan_to_num(his - means)]
            ax.barh(yc + off, np.nan_to_num(means), xerr=err, height=0.34,
                    color=ARM_COLOR[arm], label=ARM_LABEL[arm],
                    error_kw=dict(ecolor=INK2, capsize=2, lw=0.9))
            for p, m in zip(profs, means):
                if np.isnan(m):
                    nan_by_prof.setdefault(p, []).append(arm)
        for p, arms in nan_by_prof.items():
            which = ("neither arm" if len(arms) == 2 else ARM_LABEL[arms[0]])
            ax.text(20, profs.index(p), f"{which}: no re-convergence in any run "
                    f"(NaN in CSV)", va="center", ha="left", fontsize=6.8, color=MUTED)
        labels = []
        for p in profs:
            q = rec_q.get(p)
            qs = ""
            if q is not None and not pd.isna(q["q_bootstrap_bh"]):
                qs = f"  (q={_fmt(q['q_bootstrap_bh'])})"
            labels.append(p + qs)
        ax.set_yticks(yc)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.set_xlabel("episodes to re-converge (lower = faster)")
        _despine(ax)
    axes[0].legend(loc="lower right", fontsize=8)
    _src_note(fig, ci_p, pr_p)
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    _save(fig, "p2_recovery_bars.png")

    # --- detection latency (non-degenerate cells only) --------------------
    piv = ci.pivot(index="profile", columns="mode",
                   values=["DetectEpisode_mean", "DetectEpisode_ci_lo", "DetectEpisode_ci_hi"])
    nondeg = [p for p in piv.index
              if (piv.loc[p, ("DetectEpisode_mean", "ql_true")] > 0
                  or piv.loc[p, ("DetectEpisode_mean", "ql_false")] > 0)]
    nondeg = sorted(nondeg)
    det_q = {r["profile"]: r for _, r in pr[pr["metric"] == "DetectEpisode"].iterrows()}

    fig, ax = plt.subplots(figsize=(7.5, 0.5 * len(nondeg) + 1.6))
    fig.suptitle("Phase 2 [registered pooled] — detection latency, non-degenerate cells\n"
                 "(cells with DetectEpisode ≡ 0 in both arms excluded per §9.6)",
                 fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    yc = np.arange(len(nondeg))
    for off, arm in ((-0.19, "ql_true"), (0.19, "ql_false")):
        means = piv.loc[nondeg, ("DetectEpisode_mean", arm)].to_numpy()
        los = piv.loc[nondeg, ("DetectEpisode_ci_lo", arm)].to_numpy()
        his = piv.loc[nondeg, ("DetectEpisode_ci_hi", arm)].to_numpy()
        ax.barh(yc + off, means, xerr=[means - los, his - means], height=0.34,
                color=ARM_COLOR[arm], label=ARM_LABEL[arm],
                error_kw=dict(ecolor=INK2, capsize=2, lw=0.9))
    labels = []
    for p in nondeg:
        q = det_q.get(p)
        qs = ""
        if q is not None and not pd.isna(q["q_bootstrap_bh"]):
            qs = f"  (q={_fmt(q['q_bootstrap_bh'])})"
        labels.append(p + qs)
    ax.set_yticks(yc)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("episodes until fault detected (lower = faster)")
    ax.legend(loc="lower right", fontsize=8)
    _despine(ax)
    _src_note(fig, ci_p, pr_p)
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    _save(fig, "p2_detection_bars.png")

    # --- tables -----------------------------------------------------------
    MD.append("\n## 2. Phase 2 — registered pooled fault-recovery analysis [NEW era]\n\n"
              "Pooled `--registered` analysis over the §9.7 runs of record "
              "(runs 28590019536, 28745352239, 28750100413, 28863439179, 28866807391, "
              "28884717500, 28913465680); frozen families per `docs/pre_registration.md` §9. "
              "`in_registered_family = True` rows form the Tier-1 BH family (m = 8).\n")
    MD.append("\n**Paired recovery / detection tests (ql_true − ql_false, seed-paired):**\n")
    MD.append(_md_table(pr, ["profile", "metric", "recovery_tier", "in_registered_family",
                             "n_paired", "ql_true_mean", "ql_false_mean",
                             "mean_diff_true_minus_false", "ci_lo", "ci_hi",
                             "p_bootstrap", "p_wilcoxon", "cliffs_delta",
                             "q_bootstrap_bh", "bh_family_m"],
                        {"mean_diff_true_minus_false": "Δ (true−false)",
                         "cliffs_delta": "Cliff's δ", "q_bootstrap_bh": "BH q",
                         "in_registered_family": "in family"}))
    MD.append(f"\nSource: `{pr_p.relative_to(REPO).as_posix()}`\n")

    MD.append("\n**Per-cell means with 95% bootstrap CI:**\n")
    MD.append(_md_table(ci, ["profile", "mode", "n_runs", "recovery_tier",
                             "RecoveryEpisodes_mean", "RecoveryEpisodes_ci_lo",
                             "RecoveryEpisodes_ci_hi", "DetectEpisode_mean",
                             "DetectEpisode_ci_lo", "DetectEpisode_ci_hi",
                             "greedy_goal_rate_mean", "source_run"]))
    MD.append(f"\nSource: `{ci_p.relative_to(REPO).as_posix()}`\n")


# =====================================================================
# Phase 3 — learned delays vs truth + temporal-goal compliance
# =====================================================================

def phase3_figures_tables():
    base = REPO / "phase3_download_n10" / "phase3-consolidated" / "analysis" / "out"
    acc_p, ci_p, pr_p = (base / "phase3_delay_accuracy.csv",
                         base / "phase3_compliance_ci.csv",
                         base / "phase3_compliance_paired.csv")
    ok = all(_exists(p, f"Phase 3 {p.name}") for p in (acc_p, ci_p, pr_p))
    if not ok:
        return
    acc, ci, pr = pd.read_csv(acc_p), pd.read_csv(ci_p), pd.read_csv(pr_p)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.4))
    fig.suptitle("Phase 3 [run 27621106006, n = 10 replicas] — learned response delay vs truth, "
                 "and temporal-goal compliance", fontsize=10.5, fontweight="bold",
                 x=0.01, ha="left")

    # (a) learned slowest-actuator delay vs ground truth
    ax = axes[0]
    cells = list(acc.itertuples())
    xs = np.arange(len(cells))
    truth = acc["ground_truth_ticks"].iloc[0]
    for i, r in enumerate(cells):
        ax.bar(i, r.slowest_learned_ticks, width=0.6, color=ARM_COLOR[r.mode])
        ax.text(i, r.slowest_learned_ticks + 0.12,
                f"{_fmt(r.slowest_learned_ticks)}\n({_fmt(r.rel_err_pct)}% err)",
                ha="center", fontsize=7.5, color=INK2)
    ax.axhline(truth, color=INK, lw=1.2, ls="--",
               label=f"ground truth = {_fmt(truth)} ticks")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{r.profile}\n{r.mode}" for r in cells], fontsize=8)
    ax.set_ylabel("slowest learned delay (ticks)")
    ax.set_ylim(0, truth + 3.4)
    ax.set_title("Learned slowest-actuator delay vs ground truth")
    ax.legend(loc="upper left", fontsize=8)
    _despine(ax)

    # (b) compliance grouped bars
    ax = axes[1]
    metrics = [("tight_compliance", "tight"), ("overall_compliance", "overall"),
               ("loose_compliance", "loose")]
    profs = list(ci["profile"].unique())
    group_w, bar_w = 1.0, 0.19
    xticks, xlabels = [], []
    for gi, (prof) in enumerate(profs):
        for mi, (mcol, mlab) in enumerate(metrics):
            for ai, arm in enumerate(("ql_true", "ql_false")):
                r = ci[(ci["profile"] == prof) & (ci["mode"] == arm)].iloc[0]
                x = gi * (len(metrics) + 0.8) + mi + (ai - 0.5) * (bar_w + 0.02)
                m = r[f"{mcol}_mean"]
                err = [[m - r[f"{mcol}_ci_lo"]], [r[f"{mcol}_ci_hi"] - m]]
                ax.bar(x, m, width=bar_w, color=ARM_COLOR[arm],
                       yerr=err, error_kw=dict(ecolor=INK2, capsize=2, lw=0.9))
                if m == 0:
                    ax.text(x, 0.015, "0", ha="center", va="bottom",
                            fontsize=7, color=MUTED)
            xticks.append(gi * (len(metrics) + 0.8) + mi)
            xlabels.append(f"{mlab}\n{prof}")
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=7.5)
    ax.set_ylabel("deadline compliance")
    ax.set_ylim(0, 1.32)
    ax.set_title("Temporal-goal compliance (mean ± 95% CI)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ARM_COLOR[a]) for a in ("ql_true", "ql_false")]
    ax.legend(handles, [ARM_LABEL["ql_true"], ARM_LABEL["ql_false"]],
              loc="upper right", fontsize=8, ncols=2)
    _despine(ax)

    _src_note(fig, acc_p, ci_p)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    _save(fig, "p3_delay_and_compliance.png")

    MD.append("\n## 3. Phase 3 — process-dynamics / response-delay learning [NEW era]\n\n"
              "Canonical run 27621106006 (n = 10 replicas, 8 probes/actuator), profiles "
              "`lab2_slow`, `lab3_slow`.\n")
    MD.append("\n**Learned delay vs ground truth:**\n")
    MD.append(_md_table(acc, ["profile", "mode", "n_actuators", "n_instantaneous", "n_delayed",
                              "slowest_label", "slowest_learned_ticks", "ground_truth_ticks",
                              "abs_err_ticks", "rel_err_pct"]))
    MD.append(f"\nSource: `{acc_p.relative_to(REPO).as_posix()}`\n")
    MD.append("\n**Temporal-goal compliance paired tests (ql_true − ql_false):**\n")
    MD.append(_md_table(pr, ["profile", "metric", "n_paired", "ql_true_mean", "ql_false_mean",
                             "mean_diff_true_minus_false", "ci_lo", "ci_hi", "p_bootstrap",
                             "p_wilcoxon", "cliffs_delta", "q_bootstrap_bh", "bh_family_m"],
                        {"mean_diff_true_minus_false": "Δ (true−false)",
                         "cliffs_delta": "Cliff's δ", "q_bootstrap_bh": "BH q"}))
    MD.append(f"\nSource: `{pr_p.relative_to(REPO).as_posix()}`\n")
    MD.append("\n**Compliance / energy means with 95% CI:**\n")
    MD.append(_md_table(ci, ["profile", "mode", "n_replicas", "overall_compliance_mean",
                             "tight_compliance_mean", "loose_compliance_mean",
                             "total_energy_mean", "mean_actual_delay_mean"]))
    MD.append(f"\nSource: `{ci_p.relative_to(REPO).as_posix()}`\n")


# =====================================================================
# Phase 4 — energy compliance / steady power + KG-QL vs LLM
# =====================================================================

def phase4_figures_tables():
    base = REPO / "phase4_n20_download" / "phase4-consolidated" / "analysis" / "out"
    ci_p, pr_p, llm_p = (base / "phase4_energy_ci.csv", base / "phase4_energy_paired.csv",
                         base / "phase4_llm_summary.csv")
    ok = all(_exists(p, f"Phase 4 {p.name}") for p in (ci_p, pr_p, llm_p))
    if not ok:
        return
    ci, pr, llm = pd.read_csv(ci_p), pd.read_csv(pr_p), pd.read_csv(llm_p)

    # --- (a) energy compliance + steady power ------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.4))
    fig.suptitle("Phase 4 [run 27905392725, n = 20 seeds] — energy-budget compliance and "
                 "steady-state power", fontsize=10.5, fontweight="bold", x=0.01, ha="left")

    ax = axes[0]
    modes = ["ql_true", "ql_false", "rule_based"]
    profs = list(ci["profile"].unique())
    for gi, prof in enumerate(profs):
        for mi, mode in enumerate(modes):
            r = ci[(ci["profile"] == prof) & (ci["mode"] == mode)].iloc[0]
            x = gi * (len(modes) + 1) + mi
            m = r["energy_compliance_mean"]
            err = [[m - r["energy_compliance_ci_lo"]], [r["energy_compliance_ci_hi"] - m]]
            ax.bar(x, m, width=0.7, color=ARM_COLOR[mode],
                   yerr=err, error_kw=dict(ecolor=INK2, capsize=2, lw=0.9))
            ax.text(x, r["energy_compliance_ci_hi"] + 0.025, _fmt(m), ha="center",
                    va="bottom", fontsize=7.5, color=INK)
    ax.set_xticks([gi * (len(modes) + 1) + 1 for gi in range(len(profs))])
    ax.set_xticklabels(profs)
    ax.set_ylabel("energy compliance")
    ax.set_ylim(0, 1.35)
    ax.set_title("Energy-budget compliance (mean ± 95% CI)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ARM_COLOR[m]) for m in modes]
    ax.legend(handles, [ARM_LABEL[m] for m in modes], loc="upper right",
              fontsize=7.5, ncols=3, columnspacing=0.9)
    _despine(ax)

    ax = axes[1]
    sub = ci[ci["profile"] == "lab5"]
    for mi, mode in enumerate(modes):
        r = sub[sub["mode"] == mode].iloc[0]
        m = r["mean_steady_power_mean"]
        if pd.isna(m):
            continue
        err = [[m - r["mean_steady_power_ci_lo"]], [r["mean_steady_power_ci_hi"] - m]]
        ax.bar(mi, m, width=0.6, color=ARM_COLOR[mode],
               yerr=err, error_kw=dict(ecolor=INK2, capsize=2, lw=0.9))
        ax.text(mi, m + 0.06, _fmt(m), ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels([ARM_LABEL[m] for m in modes], fontsize=8)
    ax.set_ylabel("mean steady power (units)")
    ax.set_title("lab5 steady-state power (lower = better; lab4 = nan in CSV)")
    _despine(ax)

    _src_note(fig, ci_p)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    _save(fig, "p4_energy_steady_power.png")

    # --- (b) KG-QL vs LLM ---------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.2))
    fig.suptitle("Phase 4 [run 27905392725] — KG-primed QL (ql_true) vs offline LLM baseline "
                 "(backend `general`)", fontsize=10.5, fontweight="bold", x=0.01, ha="left")
    metrics = [("goal_rate", "goal rate", "goal_rate"),
               ("energy_compliance", "energy compliance", "energy_compliance"),
               ("mean_steady_power", "mean steady power (lower better)", "mean_steady_power")]
    for ax, (ci_col, title, llm_col) in zip(axes, metrics):
        profs = ["lab4", "lab5"]
        for gi, prof in enumerate(profs):
            kq = ci[(ci["profile"] == prof) & (ci["mode"] == "ql_true")].iloc[0]
            lr = llm[llm["profile"] == prof].iloc[0]
            vals = [(kq[f"{ci_col}_mean"], "ql_true"), (lr[llm_col], "llm")]
            for ai, (v, arm) in enumerate(vals):
                if pd.isna(v):
                    ax.text(gi * 3 + ai, 0.06, "n/a\n(nan in CSV)", fontsize=7,
                            ha="center", va="bottom", color=MUTED)
                    continue
                ax.bar(gi * 3 + ai, v, width=0.7, color=ARM_COLOR[arm])
                ax.text(gi * 3 + ai, v, f" {_fmt(v)}", ha="center", va="bottom",
                        fontsize=8, color=INK)
        ax.set_xticks([0.5, 3.5])
        ax.set_xticklabels(profs)
        if ci_col == "mean_steady_power":
            ax.margins(y=0.18)
        else:
            ax.set_ylim(0, 1.42)
        ax.set_title(title, fontsize=9)
        _despine(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=ARM_COLOR[a]) for a in ("ql_true", "llm")]
    axes[0].legend(handles, ["KG-QL (ql_true)", "LLM baseline"], loc="upper right",
                   fontsize=7.5, ncols=2, columnspacing=0.9)
    _src_note(fig, ci_p, llm_p)
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    _save(fig, "p4_kg_vs_llm.png")

    # --- tables -------------------------------------------------------------
    MD.append("\n## 4. Phase 4 — energy-aware goals + KG-QL vs LLM [NEW era]\n\n"
              "Canonical run 27905392725 (n = 20 seeds), profiles `lab4`, `lab5`; "
              "LLM baseline backend `general` (offline).\n")
    MD.append("\n**Energy paired tests (ql_true − ql_false, seed-paired):**\n")
    MD.append(_md_table(pr, ["profile", "metric", "n_paired", "ql_true_mean", "ql_false_mean",
                             "mean_diff_true_minus_false", "ci_lo", "ci_hi", "p_bootstrap",
                             "p_wilcoxon", "cliffs_delta", "q_bootstrap_bh", "bh_family_m"],
                        {"mean_diff_true_minus_false": "Δ (true−false)",
                         "cliffs_delta": "Cliff's δ", "q_bootstrap_bh": "BH q"}))
    MD.append(f"\nSource: `{pr_p.relative_to(REPO).as_posix()}`\n")
    MD.append("\n**Per-(profile, mode) means with 95% CI:**\n")
    MD.append(_md_table(ci, ["profile", "mode", "n_replicas", "goal_rate_mean",
                             "energy_compliance_mean", "energy_compliance_ci_lo",
                             "energy_compliance_ci_hi", "mean_steady_power_mean",
                             "over_budget_rate_mean"]))
    MD.append(f"\nSource: `{ci_p.relative_to(REPO).as_posix()}`\n")
    MD.append("\n**LLM baseline summary:**\n")
    MD.append(_md_table(llm, ["profile", "backend", "n_seeds", "n_scenarios", "goal_rate",
                              "energy_compliance", "mean_steady_power", "mean_steps",
                              "mean_redundant"]))
    MD.append(f"\nSource: `{llm_p.relative_to(REPO).as_posix()}`\n")


# =====================================================================

def main() -> int:
    print("Audit figures — reading canonical final-run CSVs only")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    MD.append("# 20 — Extracted Results (figures + paired-stats tables)\n")
    MD.append(f"\n**Generated:** by `analysis/audit_results_figures.py` — every value below "
              f"is read verbatim from a canonical final-run CSV indexed in "
              f"`docs/_audit/05_results_index.md`. Long floats are truncated to 4 "
              f"significant figures for display only; the cited CSV holds the exact value. "
              f"All content is **[NEW] era** (phase-based approach).\n")
    MD.append("\nFigures live in `docs/_audit/figures/`; each figure prints its source "
              "path in its bottom-left corner.\n")

    # Phase 1 figures
    kg_only = REPO / "phase1_headline_download" / "kg_only"
    if _exists(kg_only, "Phase 1 kg_only download folder"):
        phase1_curves(kg_only, "27336756264", "kg_only headline",
                      ["lab1", "lab2", "lab3"], "p1_kgonly")
    xmid = REPO / "phase1_xzone_mid"
    if _exists(xmid, "Phase 1 xzone_mid download folder"):
        phase1_curves(xmid, "28941204656", "xzone-mid (current lab3 physics)",
                      ["lab3"], "p1_xzonemid")
    phase1_tables()

    phase2_figures_tables()
    phase3_figures_tables()
    phase4_figures_tables()

    MD.append("\n## 5. Figure index\n")
    for png in sorted(FIG_DIR.glob("*.png")):
        MD.append(f"- `docs/_audit/figures/{png.name}`")
    if SKIPPED:
        MD.append("\n## 6. Skipped (missing sources)\n")
        for s in SKIPPED:
            MD.append(f"- {s}")
    else:
        MD.append("\n## 6. Skipped (missing sources)\n\nNone — all canonical sources present.")

    MD_PATH.write_text("\n".join(MD) + "\n", encoding="utf-8")
    print(f"  wrote {MD_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
