"""Aggregate Phase-2 fault-recovery artefacts into a CI table + paired tests.

Phase 2 (fault detection / blacklist / re-learn) writes, per faulty profile x
adapt-mode cell, a one-row-per-run CSV:

    recovery_stereotypes_<true|false><qtable_suffix>.csv
        DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes

where <true> == ql_true (KG-primed) and <false> == ql_false (tabula-rasa).
RecoveryEpisodes = ReconvergeEpisode - DetectEpisode (lower == faster
re-alignment after the fault); -1 means "did not re-converge within the budget"
or a degenerate single-actuator lab (e.g. lab1_f1dead) where the last actuator
is protected from blacklisting.

The headline Phase-2 claim is:  recovery(ql_true) < recovery(ql_false)
-- the KG prior lets the agent re-align over the surviving components faster
than a learner that must rediscover structure from scratch.

This script:
  * discovers recovery CSVs for every configured faulty profile (root + any
    archived seed subdirectories under --root),
  * treats each CSV row as one independent replica,
  * reports per (profile, arm) mean + bootstrap 95% CI for RecoveryEpisodes and
    DetectEpisode, plus detection/reconvergence rates,
  * runs a paired bootstrap (ql_true - ql_false) per profile with Benjamini-
    Hochberg q-values across the profile family (reusing sweep_report.py's
    pre-registered helpers / RNG seed 0xC1).

Outputs (under analysis/out/):
    phase2_recovery_ci.csv      -- one row per (profile, arm)
    phase2_recovery_paired.csv  -- one row per (profile, metric) paired diff

Usage:
    python analysis/phase2_recovery.py
    python analysis/phase2_recovery.py --root . --out analysis/out
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Reuse the pre-registered statistical helpers (deterministic RNG seed 0xC1,
# bootstrap CIs, paired bootstrap diff, Wilcoxon, Cliff's delta, BH-FDR) so the
# Phase-2 numbers use exactly the same methodology as the Phase-1 sweep. The
# import has no side effects: sweep_report guards its CLI behind __main__.
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))
try:
    from analysis.sweep_report import (  # type: ignore
        _bootstrap_ci, _paired_bootstrap_diff, _wilcoxon_p,
        _cliffs_delta, _bh_qvalues,
    )
except Exception:  # pragma: no cover - fallback when run outside the package
    from sweep_report import (  # type: ignore
        _bootstrap_ci, _paired_bootstrap_diff, _wilcoxon_p,
        _cliffs_delta, _bh_qvalues,
    )

# adapt-mode -> the boolean string embedded in the artefact filename.
_ARMS = (("ql_true", "true"), ("ql_false", "false"))

# Metrics compared per profile. Both are "lower is better".
_METRICS = ("RecoveryEpisodes", "DetectEpisode")


def load_phase2_config(cfg_path: Path) -> dict:
    """Return the phase2 block from run_config.json (suffix map + profiles)."""
    if not cfg_path.is_file():
        raise SystemExit(f"Missing config: {cfg_path}")
    # utf-8-sig transparently strips a UTF-8 BOM if present (run_config.json is
    # BOM-encoded so the PowerShell runners parse it under Windows PS 5.1).
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    p2 = cfg.get("phase2")
    if not p2:
        raise SystemExit(f"{cfg_path} has no 'phase2' block")
    return p2


def find_recovery_rows(root: Path, bool_str: str, suffix: str) -> list[dict]:
    """All rows from recovery_stereotypes_<bool><suffix>.csv under root.

    Searches the root directory and (recursively) any archived seed
    subdirectories, so multi-replica runs aggregate automatically. Each CSV row
    is one replica observation.
    """
    fname = f"recovery_stereotypes_{bool_str}{suffix}.csv"
    paths = []
    direct = root / fname
    if direct.is_file():
        paths.append(direct)
    # Archived/seeded copies (e.g. phase2_seed3/recovery_*.csv). Avoid double-
    # counting the direct hit.
    for p in sorted(root.rglob(fname)):
        if p.resolve() != direct.resolve():
            paths.append(p)

    rows: list[dict] = []
    for p in paths:
        try:
            with p.open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    rows.append(r)
        except Exception as exc:  # noqa: BLE001 - best-effort aggregation
            print(f"  [!!] could not read {p}: {exc}", file=sys.stderr)
    return rows


def _as_int(row: dict, key: str):
    raw = row.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(float(str(raw).strip()))
    except ValueError:
        return None


def collect_arm(rows: list[dict]) -> dict:
    """Reduce raw recovery rows into per-arm metric lists + rates."""
    detect_all = [_as_int(r, "DetectEpisode") for r in rows]
    recov_all = [_as_int(r, "ReconvergeEpisode") for r in rows]
    recovery_all = [_as_int(r, "RecoveryEpisodes") for r in rows]
    defects = sorted({(r.get("DefectComponent") or "").strip()
                      for r in rows if (r.get("DefectComponent") or "").strip()})

    n_runs = len(rows)
    # Detection succeeded when DetectEpisode >= 0.
    detected = [d for d in detect_all if d is not None and d >= 0]
    # Re-convergence succeeded when RecoveryEpisodes >= 0 (>=0 implies both
    # detect and reconverge episodes were recorded).
    reconverged = [v for v in recovery_all if v is not None and v >= 0]

    return {
        "n_runs": n_runs,
        "defects": defects,
        # Per-metric value lists used for CIs / pairing (success-only).
        "DetectEpisode": detected,
        "RecoveryEpisodes": reconverged,
        "n_detected": len(detected),
        "n_reconverged": len(reconverged),
        "detection_rate": (len(detected) / n_runs) if n_runs else float("nan"),
        "reconverge_rate": (len(reconverged) / n_runs) if n_runs else float("nan"),
        "_reconverge_episodes": [v for v in recov_all if v is not None and v >= 0],
    }


def write_ci_table(per_cell: dict, out_dir: Path, iters: int) -> int:
    """phase2_recovery_ci.csv: one row per (profile, arm)."""
    rows = []
    for (profile, mode), arm in sorted(per_cell.items()):
        row = {
            "profile": profile,
            "mode": mode,
            "n_runs": arm["n_runs"],
            "defect_component": ";".join(arm["defects"]) if arm["defects"] else "",
            "detection_rate": round(arm["detection_rate"], 4)
                if arm["detection_rate"] == arm["detection_rate"] else "",
            "reconverge_rate": round(arm["reconverge_rate"], 4)
                if arm["reconverge_rate"] == arm["reconverge_rate"] else "",
            "n_detected": arm["n_detected"],
            "n_reconverged": arm["n_reconverged"],
        }
        for metric in _METRICS:
            mean, lo, hi = _bootstrap_ci(
                [float(v) for v in arm[metric]], iters=iters)
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci_lo"] = lo
            row[f"{metric}_ci_hi"] = hi
        rows.append(row)

    out_path = out_dir / "phase2_recovery_ci.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    cols = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_paired_table(per_cell: dict, profiles: list[str],
                       out_dir: Path, iters: int) -> int:
    """phase2_recovery_paired.csv: ql_true vs ql_false per profile x metric.

    Pairs replicas by index (run i of ql_true vs run i of ql_false). mean_diff
    < 0 means ql_true is FASTER (fewer episodes) -- the headline direction.
    Benjamini-Hochberg q-values are computed across the profile family for each
    metric independently.
    """
    rows: list[dict] = []
    metric_pidx: dict = {}  # metric -> list of (row_idx, p_value)

    for metric in _METRICS:
        metric_pidx.setdefault(metric, [])
        for profile in profiles:
            ta = per_cell.get((profile, "ql_true"))
            fa = per_cell.get((profile, "ql_false"))
            if not ta or not fa:
                continue
            a = [float(v) for v in ta[metric]]
            b = [float(v) for v in fa[metric]]
            n_pair = min(len(a), len(b))
            if n_pair == 0:
                continue
            a, b = a[:n_pair], b[:n_pair]
            raw_diff = (sum(a) / len(a)) - (sum(b) / len(b))
            if n_pair >= 2:
                mean_d, lo, hi, p_boot, p_pos, p_neg = _paired_bootstrap_diff(
                    a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
            else:
                mean_d, lo, hi = raw_diff, float("nan"), float("nan")
                p_boot = p_pos = p_neg = p_wil = delta = float("nan")
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
                "p_bootstrap": p_boot,
                "p_bootstrap_one_sided_true_faster": p_pos,
                "p_wilcoxon": p_wil,
                "cliffs_delta": delta,
                "ql_true_faster": (mean_d < 0) if mean_d == mean_d else "",
            })
            metric_pidx[metric].append((row_idx, p_boot))

    # BH per metric family.
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

    out_path = out_dir / "phase2_recovery_paired.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    cols = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _fmt(x) -> str:
    if isinstance(x, float):
        if x != x:
            return "  nan"
        return f"{x:6.1f}"
    return str(x)


def print_summary(per_cell: dict, profiles: list[str]) -> None:
    print("\n=== Phase 2 recovery summary (lower = faster) ===")
    header = f"{'profile':<16}{'arm':<10}{'n':>3}  {'det%':>5} {'recv%':>6}  {'detectEp':>9} {'recovEp':>9}"
    print(header)
    print("-" * len(header))
    for profile in profiles:
        for mode, _bool in _ARMS:
            arm = per_cell.get((profile, mode))
            if not arm:
                continue
            det_mean, _, _ = _bootstrap_ci([float(v) for v in arm["DetectEpisode"]])
            rec_mean, _, _ = _bootstrap_ci([float(v) for v in arm["RecoveryEpisodes"]])
            det_pct = arm["detection_rate"] * 100 if arm["detection_rate"] == arm["detection_rate"] else float("nan")
            rec_pct = arm["reconverge_rate"] * 100 if arm["reconverge_rate"] == arm["reconverge_rate"] else float("nan")
            print(f"{profile:<16}{mode:<10}{arm['n_runs']:>3}  "
                  f"{_fmt(det_pct):>5} {_fmt(rec_pct):>6}  "
                  f"{_fmt(det_mean):>9} {_fmt(rec_mean):>9}")
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".",
                        help="directory holding recovery_stereotypes_*.csv (default: .)")
    parser.add_argument("--config", default="config/run_config.json",
                        help="run_config.json with the phase2 block")
    parser.add_argument("--out", default="analysis/out",
                        help="output directory (default: analysis/out)")
    parser.add_argument("--iters", type=int, default=10000,
                        help="bootstrap iterations (default: 10000)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    p2 = load_phase2_config(Path(args.config))
    profiles = list(p2.get("adapt_profiles", []))
    suffix_map = p2.get("qtable_suffix_map", {})

    per_cell: dict = {}
    found_any = False
    for profile in profiles:
        suffix = suffix_map.get(profile)
        if suffix is None:
            print(f"  [!!] no qtable_suffix for {profile}; skipping", file=sys.stderr)
            continue
        for mode, bool_str in _ARMS:
            rows = find_recovery_rows(root, bool_str, suffix)
            if rows:
                found_any = True
            per_cell[(profile, mode)] = collect_arm(rows)

    if not found_any:
        print(f"No recovery_stereotypes_*.csv found under {root}.\n"
              f"Run the Phase-2 orchestrator first:  .\\run_phase2_adapt.ps1",
              file=sys.stderr)
        return 1

    n_ci = write_ci_table(per_cell, out_dir, args.iters)
    n_paired = write_paired_table(per_cell, profiles, out_dir, args.iters)
    print_summary(per_cell, profiles)
    print(f"Wrote {n_ci} rows -> {out_dir / 'phase2_recovery_ci.csv'}")
    print(f"Wrote {n_paired} rows -> {out_dir / 'phase2_recovery_paired.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
