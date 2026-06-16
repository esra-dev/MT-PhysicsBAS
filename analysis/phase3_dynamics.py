"""Aggregate Phase-3 process-dynamics artefacts into a CI table + paired tests.

Phase 3 (response-delay learning / time-bounded exploitation) writes, per slow
profile x planner-mode cell, TWO artefacts:

    dynamics_delays_<true|false>_<profile>.csv
        action_label,action_value,samples,delay_ticks,delay_seconds,
        std_ticks,response_class
        -- the LEARNED per-actuator response delay (the probe phase is identical
           in both modes, so this measures delay-learning ACCURACY).

    timebounded_results_<true|false>_<profile>.csv
        profile,mode,goal_id,zone,target_rank,deadline_sec,chosen_label,
        believed_delay_sec,learned_delay_sec,actual_delay_sec,energy_cost,met
        -- one row per time-bounded goal; met==1 iff the target rank was reached
           within the deadline (the planner EXPLOITS the learned delay).

where <true> == ql_true (KG-primed planner: uses the learned delay) and
<false> == ql_false (tabula-rasa planner: assumes zero delay).

The two headline Phase-3 claims are:

  (1) DELAY-LEARNING ACCURACY -- the agent recovers the motorized blind's
      ground-truth response delay (config phase3.blind_delay_ticks, e.g. 12
      ticks = 60 s) from probing alone, and cleanly separates the instantaneous
      lamp/spotlight from the delayed blind.

  (2) DEADLINE COMPLIANCE -- compliance(ql_true) > compliance(ql_false),
      especially on TIGHT goals (deadline < blind delay): the KG-primed planner
      reaches for the fast lamp when the deadline is tight and the cheap blind
      when it is loose, while the tabula-rasa planner always grabs the cheapest
      actuator (the slow blind) and misses every tight deadline. ql_true should
      ALSO spend energy only when a tight deadline forces the lamp (it uses the
      free blind whenever the deadline admits it).

This script:
  * discovers both artefact families for every configured slow profile (root +
    any archived seed subdirectories under --root),
  * treats each timebounded CSV as one independent replica (its 6 goals reduce
    to per-replica compliance + energy scalars),
  * reports per (profile, arm) mean + bootstrap 95% CI for overall / tight /
    loose compliance and total energy, plus a delay-accuracy table (learned vs
    ground-truth blind ticks, instantaneous vs delayed class means),
  * runs a paired bootstrap (ql_true - ql_false) per profile with Benjamini-
    Hochberg q-values across the profile family (reusing sweep_report.py's
    pre-registered helpers / RNG seed 0xC1 when available).

Outputs (under analysis/out/):
    phase3_delay_accuracy.csv   -- one row per (profile, arm): learned vs truth
    phase3_compliance_ci.csv    -- one row per (profile, arm): compliance+energy
    phase3_compliance_paired.csv -- one row per (profile, metric) paired diff

Usage:
    python analysis/phase3_dynamics.py
    python analysis/phase3_dynamics.py --root . --out analysis/out
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Reuse the pre-registered statistical helpers (deterministic RNG seed 0xC1,
# bootstrap CIs, paired bootstrap diff, Wilcoxon, Cliff's delta, BH-FDR) so the
# Phase-3 numbers use exactly the same methodology as the Phase-1 sweep and the
# Phase-2 recovery analysis. The import has no side effects: sweep_report guards
# its CLI behind __main__. Fall back to light-weight local implementations if
# the module is unavailable (keeps the script runnable in isolation).
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
try:
    from analysis.sweep_report import (  # type: ignore
        _bootstrap_ci, _paired_bootstrap_diff, _wilcoxon_p,
        _cliffs_delta, _bh_qvalues,
    )
except Exception:  # pragma: no cover - fallback when run outside the package
    try:
        from sweep_report import (  # type: ignore
            _bootstrap_ci, _paired_bootstrap_diff, _wilcoxon_p,
            _cliffs_delta, _bh_qvalues,
        )
    except Exception:  # pragma: no cover - minimal deterministic fallbacks
        import random as _random

        def _mean(xs):
            return (sum(xs) / len(xs)) if xs else float("nan")

        def _bootstrap_ci(xs, iters=10000, alpha=0.05):
            xs = [float(x) for x in xs]
            if not xs:
                return float("nan"), float("nan"), float("nan")
            if len(xs) == 1:
                return xs[0], xs[0], xs[0]
            rng = _random.Random(0xC1)
            means = []
            n = len(xs)
            for _ in range(iters):
                means.append(_mean([xs[rng.randrange(n)] for _ in range(n)]))
            means.sort()
            lo = means[int((alpha / 2) * iters)]
            hi = means[int((1 - alpha / 2) * iters)]
            return _mean(xs), lo, hi

        def _paired_bootstrap_diff(a, b, iters=10000, alpha=0.05):
            d = [float(x) - float(y) for x, y in zip(a, b)]
            if not d:
                nan = float("nan")
                return nan, nan, nan, nan, nan, nan
            if len(d) == 1:
                return d[0], float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
            rng = _random.Random(0xC1)
            means = []
            n = len(d)
            for _ in range(iters):
                means.append(_mean([d[rng.randrange(n)] for _ in range(n)]))
            means.sort()
            lo = means[int((alpha / 2) * iters)]
            hi = means[int((1 - alpha / 2) * iters)]
            p_pos = sum(1 for m in means if m <= 0) / iters
            p_neg = sum(1 for m in means if m >= 0) / iters
            p_boot = 2 * min(p_pos, p_neg)
            return _mean(d), lo, hi, p_boot, p_pos, p_neg

        def _wilcoxon_p(a, b):
            return float("nan")

        def _cliffs_delta(a, b):
            return float("nan")

        def _bh_qvalues(ps):
            m = len(ps)
            order = sorted(range(m), key=lambda i: ps[i])
            q = [float("nan")] * m
            prev = 1.0
            for rank, i in enumerate(reversed(order), start=1):
                k = m - rank + 1
                val = ps[i] * m / k if ps[i] == ps[i] else float("nan")
                if val == val:
                    prev = min(prev, val)
                q[i] = prev
            return q


# planner-mode -> the boolean string embedded in the artefact filename.
_ARMS = (("ql_true", "true"), ("ql_false", "false"))

# Compliance metrics compared per profile. All are "higher is better" EXCEPT
# energy, which is "lower is better" -- orientation is handled when we decide
# `ql_true_better` per row.
_COMPLIANCE_METRICS = ("overall_compliance", "tight_compliance", "loose_compliance")
_ENERGY_METRIC = "total_energy"


def load_phase3_config(cfg_path: Path) -> dict:
    """Return the phase3 block from run_config.json (profiles + timing)."""
    if not cfg_path.is_file():
        raise SystemExit(f"Missing config: {cfg_path}")
    # utf-8-sig transparently strips a UTF-8 BOM if present (run_config.json is
    # BOM-encoded so the PowerShell runners parse it under Windows PS 5.1).
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    p3 = cfg.get("phase3")
    if not p3:
        raise SystemExit(f"{cfg_path} has no 'phase3' block")
    return p3


def find_csv_paths(root: Path, fname: str) -> list[Path]:
    """The root copy of `fname` plus any archived seed copies under root."""
    paths: list[Path] = []
    direct = root / fname
    if direct.is_file():
        paths.append(direct)
    for p in sorted(root.rglob(fname)):
        if not paths or p.resolve() != paths[0].resolve():
            if p.resolve() not in {q.resolve() for q in paths}:
                paths.append(p)
    return paths


def _as_float(value) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def collect_delays(root: Path, bool_str: str, profile: str,
                   ground_truth_ticks: int) -> dict:
    """Average the learned per-actuator delays across replicas + summarise.

    Returns the slowest-actuator (== the motorized blind) learned ticks vs the
    ground truth, plus instantaneous/delayed class means -- the delay-learning
    ACCURACY headline.
    """
    fname = f"dynamics_delays_{bool_str}_{profile}.csv"
    paths = find_csv_paths(root, fname)
    # label -> list of per-replica (ticks, seconds, class)
    by_label: dict[str, list[tuple]] = {}
    for p in paths:
        try:
            with p.open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    label = (r.get("action_label") or "").strip()
                    ticks = _as_float(r.get("delay_ticks"))
                    secs = _as_float(r.get("delay_seconds"))
                    cls = (r.get("response_class") or "").strip()
                    if label and ticks is not None:
                        by_label.setdefault(label, []).append((ticks, secs, cls))
        except Exception as exc:  # noqa: BLE001 - best-effort aggregation
            print(f"  [!!] could not read {p}: {exc}", file=sys.stderr)

    actuators = []
    for label, samples in sorted(by_label.items()):
        ticks_list = [t for t, _s, _c in samples]
        secs_list = [s for _t, s, _c in samples if s is not None]
        # The modal class across replicas (they are deterministic, so this is
        # just the class; the list form tolerates the rare boundary flip).
        classes = [c for _t, _s, c in samples if c]
        modal_cls = max(set(classes), key=classes.count) if classes else ""
        actuators.append({
            "label": label,
            "n_replicas": len(samples),
            "mean_ticks": sum(ticks_list) / len(ticks_list),
            "mean_seconds": (sum(secs_list) / len(secs_list)) if secs_list else float("nan"),
            "response_class": modal_cls,
        })

    delayed = [a for a in actuators if a["response_class"] == "delayed"]
    instant = [a for a in actuators if a["response_class"] == "instantaneous"]
    # The slowest actuator is the motorized blind we annotated with the
    # ground-truth delay; compare its learned ticks to the truth.
    slowest = max(actuators, key=lambda a: a["mean_ticks"]) if actuators else None

    def _mean_ticks(group):
        return (sum(a["mean_ticks"] for a in group) / len(group)) if group else float("nan")

    slow_ticks = slowest["mean_ticks"] if slowest else float("nan")
    abs_err = abs(slow_ticks - ground_truth_ticks) if slow_ticks == slow_ticks else float("nan")
    rel_err = (abs_err / ground_truth_ticks * 100.0) if (ground_truth_ticks and abs_err == abs_err) else float("nan")

    return {
        "n_actuators": len(actuators),
        "n_instantaneous": len(instant),
        "n_delayed": len(delayed),
        "slowest_label": slowest["label"] if slowest else "",
        "slowest_learned_ticks": slow_ticks,
        "ground_truth_ticks": ground_truth_ticks,
        "abs_err_ticks": abs_err,
        "rel_err_pct": rel_err,
        "mean_instant_ticks": _mean_ticks(instant),
        "mean_delayed_ticks": _mean_ticks(delayed),
        "actuators": actuators,
    }


def collect_compliance(root: Path, bool_str: str, profile: str,
                       tight_threshold_sec: float) -> dict:
    """Reduce each timebounded CSV (one replica = its goals) into scalars.

    A goal is TIGHT when its deadline is below the blind's ground-truth delay
    (only an instantaneous actuator can meet it) and LOOSE otherwise (the cheap
    blind also qualifies).
    """
    fname = f"timebounded_results_{bool_str}_{profile}.csv"
    paths = find_csv_paths(root, fname)

    overall, tight, loose, energy, actual = [], [], [], [], []
    n_goals_total = 0
    for p in paths:
        try:
            with p.open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        except Exception as exc:  # noqa: BLE001
            print(f"  [!!] could not read {p}: {exc}", file=sys.stderr)
            continue
        if not rows:
            continue
        n_met = n_tot = n_tight_met = n_tight = n_loose_met = n_loose = 0
        e_sum = 0.0
        a_vals = []
        for r in rows:
            met = _as_float(r.get("met"))
            deadline = _as_float(r.get("deadline_sec"))
            ecost = _as_float(r.get("energy_cost"))
            adelay = _as_float(r.get("actual_delay_sec"))
            if met is None or deadline is None:
                continue
            is_met = met >= 0.5
            n_tot += 1
            if is_met:
                n_met += 1
            if deadline < tight_threshold_sec:
                n_tight += 1
                if is_met:
                    n_tight_met += 1
            else:
                n_loose += 1
                if is_met:
                    n_loose_met += 1
            if ecost is not None:
                e_sum += ecost
            if adelay is not None and adelay >= 0:
                a_vals.append(adelay)
        if n_tot == 0:
            continue
        n_goals_total = max(n_goals_total, n_tot)
        overall.append(n_met / n_tot)
        if n_tight:
            tight.append(n_tight_met / n_tight)
        if n_loose:
            loose.append(n_loose_met / n_loose)
        energy.append(e_sum)
        actual.append(sum(a_vals) / len(a_vals) if a_vals else float("nan"))

    return {
        "n_replicas": len(overall),
        "n_goals_total": n_goals_total,
        "overall_compliance": overall,
        "tight_compliance": tight,
        "loose_compliance": loose,
        "total_energy": energy,
        "mean_actual_delay": actual,
    }


def write_delay_table(per_delay: dict, out_dir: Path) -> int:
    """phase3_delay_accuracy.csv: one row per (profile, arm)."""
    rows = []
    for (profile, mode), d in sorted(per_delay.items()):
        rows.append({
            "profile": profile,
            "mode": mode,
            "n_actuators": d["n_actuators"],
            "n_instantaneous": d["n_instantaneous"],
            "n_delayed": d["n_delayed"],
            "slowest_label": d["slowest_label"],
            "slowest_learned_ticks": round(d["slowest_learned_ticks"], 4)
                if d["slowest_learned_ticks"] == d["slowest_learned_ticks"] else "",
            "ground_truth_ticks": d["ground_truth_ticks"],
            "abs_err_ticks": round(d["abs_err_ticks"], 4)
                if d["abs_err_ticks"] == d["abs_err_ticks"] else "",
            "rel_err_pct": round(d["rel_err_pct"], 2)
                if d["rel_err_pct"] == d["rel_err_pct"] else "",
            "mean_instant_ticks": round(d["mean_instant_ticks"], 4)
                if d["mean_instant_ticks"] == d["mean_instant_ticks"] else "",
            "mean_delayed_ticks": round(d["mean_delayed_ticks"], 4)
                if d["mean_delayed_ticks"] == d["mean_delayed_ticks"] else "",
        })
    out_path = out_dir / "phase3_delay_accuracy.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_compliance_ci(per_cell: dict, out_dir: Path, iters: int) -> int:
    """phase3_compliance_ci.csv: one row per (profile, arm)."""
    rows = []
    for (profile, mode), arm in sorted(per_cell.items()):
        row = {
            "profile": profile,
            "mode": mode,
            "n_replicas": arm["n_replicas"],
            "n_goals_total": arm["n_goals_total"],
        }
        for metric in (*_COMPLIANCE_METRICS, _ENERGY_METRIC, "mean_actual_delay"):
            vals = [float(v) for v in arm[metric] if v == v]
            mean, lo, hi = _bootstrap_ci(vals, iters=iters)
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci_lo"] = lo
            row[f"{metric}_ci_hi"] = hi
        rows.append(row)
    out_path = out_dir / "phase3_compliance_ci.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_compliance_paired(per_cell: dict, profiles: list[str],
                            out_dir: Path, iters: int) -> int:
    """phase3_compliance_paired.csv: ql_true vs ql_false per profile x metric.

    For compliance metrics mean_diff (ql_true - ql_false) > 0 means ql_true is
    BETTER (meets more goals); for energy lower is better, so the orientation is
    flipped when deciding `ql_true_better`. Benjamini-Hochberg q-values are
    computed across the profile family per metric.
    """
    rows: list[dict] = []
    metric_pidx: dict = {}
    metrics = (*_COMPLIANCE_METRICS, _ENERGY_METRIC)

    for metric in metrics:
        metric_pidx.setdefault(metric, [])
        for profile in profiles:
            ta = per_cell.get((profile, "ql_true"))
            fa = per_cell.get((profile, "ql_false"))
            if not ta or not fa:
                continue
            a = [float(v) for v in ta[metric] if v == v]
            b = [float(v) for v in fa[metric] if v == v]
            n_pair = min(len(a), len(b))
            if n_pair == 0:
                continue
            a, b = a[:n_pair], b[:n_pair]
            if n_pair >= 2:
                mean_d, lo, hi, p_boot, p_pos, p_neg = _paired_bootstrap_diff(
                    a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
            else:
                mean_d = (sum(a) / len(a)) - (sum(b) / len(b))
                lo = hi = p_boot = p_pos = p_neg = p_wil = delta = float("nan")
            lower_is_better = (metric == _ENERGY_METRIC)
            better = ""
            if mean_d == mean_d:
                better = (mean_d < 0) if lower_is_better else (mean_d > 0)
            row_idx = len(rows)
            rows.append({
                "profile": profile,
                "metric": metric,
                "n_paired": n_pair,
                "ql_true_mean": (sum(a) / len(a)) if a else float("nan"),
                "ql_false_mean": (sum(b) / len(b)) if b else float("nan"),
                "mean_diff_true_minus_false": mean_d,
                "ci_lo": lo,
                "ci_hi": hi,
                "lower_is_better": lower_is_better,
                "p_bootstrap": p_boot,
                "p_wilcoxon": p_wil,
                "cliffs_delta": delta,
                "ql_true_better": better,
            })
            metric_pidx[metric].append((row_idx, p_boot))

    for pidx in metric_pidx.values():
        if not pidx:
            continue
        idxs = [i for i, _ in pidx]
        ps = [p for _, p in pidx]
        qs = _bh_qvalues(ps)
        for i, q in zip(idxs, qs):
            rows[i]["q_bootstrap_bh"] = q
            rows[i]["bh_family_m"] = len(idxs)
    for r in rows:
        r.setdefault("q_bootstrap_bh", float("nan"))
        r.setdefault("bh_family_m", 0)

    out_path = out_dir / "phase3_compliance_paired.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _fmt(x) -> str:
    if isinstance(x, float):
        if x != x:
            return "  nan"
        return f"{x:6.2f}"
    return str(x)


def print_summary(per_cell: dict, per_delay: dict, profiles: list[str],
                  ground_truth_ticks: int) -> None:
    print("\n=== Phase 3 delay-learning accuracy (learned vs ground-truth blind ticks) ===")
    header = (f"{'profile':<12}{'arm':<10}{'inst':>5}{'del':>4}  "
              f"{'slowest':>16} {'learn_t':>8} {'truth_t':>8} {'err_t':>7}")
    print(header)
    print("-" * len(header))
    for profile in profiles:
        for mode, _b in _ARMS:
            d = per_delay.get((profile, mode))
            if not d:
                continue
            print(f"{profile:<12}{mode:<10}{d['n_instantaneous']:>5}{d['n_delayed']:>4}  "
                  f"{d['slowest_label']:>16} {_fmt(d['slowest_learned_ticks']):>8} "
                  f"{_fmt(float(ground_truth_ticks)):>8} {_fmt(d['abs_err_ticks']):>7}")

    print("\n=== Phase 3 deadline compliance (higher = better; energy lower = better) ===")
    header2 = (f"{'profile':<12}{'arm':<10}{'n':>3}  {'all%':>6} {'tight%':>7} "
               f"{'loose%':>7} {'energy':>7}")
    print(header2)
    print("-" * len(header2))
    for profile in profiles:
        for mode, _b in _ARMS:
            arm = per_cell.get((profile, mode))
            if not arm:
                continue
            o, _, _ = _bootstrap_ci([float(v) for v in arm["overall_compliance"]])
            t, _, _ = _bootstrap_ci([float(v) for v in arm["tight_compliance"]])
            l, _, _ = _bootstrap_ci([float(v) for v in arm["loose_compliance"]])
            e, _, _ = _bootstrap_ci([float(v) for v in arm["total_energy"]])
            o = o * 100 if o == o else float("nan")
            t = t * 100 if t == t else float("nan")
            l = l * 100 if l == l else float("nan")
            print(f"{profile:<12}{mode:<10}{arm['n_replicas']:>3}  "
                  f"{_fmt(o):>6} {_fmt(t):>7} {_fmt(l):>7} {_fmt(e):>7}")
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".",
                        help="directory holding the Phase-3 CSVs (default: .)")
    parser.add_argument("--config", default="config/run_config.json",
                        help="run_config.json with the phase3 block")
    parser.add_argument("--out", default="analysis/out",
                        help="output directory (default: analysis/out)")
    parser.add_argument("--iters", type=int, default=10000,
                        help="bootstrap iterations (default: 10000)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    p3 = load_phase3_config(Path(args.config))
    profiles = list(p3.get("dynamics_profiles", []))
    seconds_per_tick = float(p3.get("seconds_per_tick", 5.0))
    ground_truth_ticks = int(p3.get("blind_delay_ticks", 12))
    # A goal is "tight" when its deadline is below the blind's ground-truth delay
    # in seconds: only an instantaneous actuator can meet it.
    tight_threshold_sec = ground_truth_ticks * seconds_per_tick

    per_cell: dict = {}
    per_delay: dict = {}
    found_any = False
    for profile in profiles:
        for mode, bool_str in _ARMS:
            comp = collect_compliance(root, bool_str, profile, tight_threshold_sec)
            delay = collect_delays(root, bool_str, profile, ground_truth_ticks)
            if comp["n_replicas"] > 0 or delay["n_actuators"] > 0:
                found_any = True
            per_cell[(profile, mode)] = comp
            per_delay[(profile, mode)] = delay

    if not found_any:
        print(f"No Phase-3 CSVs (dynamics_delays_* / timebounded_results_*) found "
              f"under {root}.\nRun the Phase-3 orchestrator first:  "
              f".\\run_phase3_dynamics.ps1", file=sys.stderr)
        return 1

    n_delay = write_delay_table(per_delay, out_dir)
    n_ci = write_compliance_ci(per_cell, out_dir, args.iters)
    n_paired = write_compliance_paired(per_cell, profiles, out_dir, args.iters)
    print_summary(per_cell, per_delay, profiles, ground_truth_ticks)
    print(f"Wrote {n_delay} rows -> {out_dir / 'phase3_delay_accuracy.csv'}")
    print(f"Wrote {n_ci} rows -> {out_dir / 'phase3_compliance_ci.csv'}")
    print(f"Wrote {n_paired} rows -> {out_dir / 'phase3_compliance_paired.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
