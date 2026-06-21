"""Phase-4 energy-budget compliance + dependency analysis (the one metric the
generic sweep_report does NOT compute).

Phase 4 adds two strictly-clean labs to the Phase-1 clean ladder:

  * lab4 (smart-plug AND-gate) — the Z1 ceiling lamp emits light only when both
    its switch AND SmartPlug_Z1 are ON. The dependency headline (KG-primed agent
    toggles the plug first → reaches goals with fewer redundant actions) is
    already told by sweep_report's goal_rate / avg_redundant. lab4 carries NO
    per-scenario energy budget, so this script reports goal_rate only for it.

  * lab5 (energy) — each zone has TWO directly-actionable lamps with IDENTICAL
    +400 lux output but different ws:energyCost (efficient = 1, inefficient = 4).
    Energy is NOT in the Q-reward, so only the KG-primed arm (reading
    ws:energyCost via the non-fading energy prior) prefers the cheap lamp /
    zero-energy blinds. The NEW headline metric is ENERGY-BUDGET COMPLIANCE:

        compliant(scenario) = GoalReached AND steady_power <= energyBudget

    where steady_power is the deterministic per-tick power of the FINAL actuator
    configuration recorded in bench_step_log_<mode>.csv, scored with the
    per-actuator weights from run_config phase4.power_formula
    (Z1Eff*1 + Z1Ineff*4 + Z2Eff*1 + Z2Ineff*4 + Spotlight*2) and the
    per-scenario energyBudget from benchmark/scenarios_lab5.json (default 2).

The thesis claim (advisor: "the Q-learning agent with more knowledge learns
better ... avoids redundant actions, maybe even more successfully") is tested as
the within-lab paired delta ql_true (KG-primed) − ql_false (tabula-rasa) across
seeds, using the SAME pre-registered statistics as Phase 1 / Phase 3: bootstrap
95% CIs, paired bootstrap mean-difference, Wilcoxon signed-rank, Cliff's delta,
and Benjamini-Hochberg q-values. rule_based is reported as a reference ceiling
but is not part of the confirmatory paired family.

Inputs (discovered under --root, CI seed layout):
    <root>/results_seed<N>/<profile>/<mode>/bench_step_log_<mode>.csv
    <root>/results_seed<N>/<profile>/<mode>/benchmark_results_<mode>.csv
Falls back to a flat single-profile layout (<root>/bench_step_log_<mode>.csv)
when exactly one profile is in scope (local smoke runs).

Outputs (under analysis/out/):
    phase4_energy_ci.csv     — one row per (profile, mode): per-metric mean + CI
    phase4_energy_paired.csv — one row per (profile, metric): ql_true − ql_false

Usage:
    python analysis/phase4_energy.py
    python analysis/phase4_energy.py --root benchmark --out analysis/out
    python analysis/phase4_energy.py --root . --profile lab5   # local smoke
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Reuse the pre-registered statistical helpers (deterministic RNG seed 0xC1,
# bootstrap CIs, paired bootstrap diff, Wilcoxon, Cliff's delta, BH-FDR) so the
# Phase-4 numbers use exactly the same methodology as Phase 1 / Phase 3. The
# import has no side effects (sweep_report guards its CLI behind __main__).
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
            means, n = [], len(xs)
            for _ in range(iters):
                means.append(_mean([xs[rng.randrange(n)] for _ in range(n)]))
            means.sort()
            return _mean(xs), means[int((alpha / 2) * iters)], means[int((1 - alpha / 2) * iters)]

        def _paired_bootstrap_diff(a, b, iters=10000, alpha=0.05):
            d = [float(x) - float(y) for x, y in zip(a, b)]
            if not d:
                nan = float("nan")
                return nan, nan, nan, nan, nan, nan
            if len(d) == 1:
                return d[0], float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
            rng = _random.Random(0xC1)
            means, n = [], len(d)
            for _ in range(iters):
                means.append(_mean([d[rng.randrange(n)] for _ in range(n)]))
            means.sort()
            lo = means[int((alpha / 2) * iters)]
            hi = means[int((1 - alpha / 2) * iters)]
            p_pos = sum(1 for m in means if m <= 0) / iters
            p_neg = sum(1 for m in means if m >= 0) / iters
            return _mean(d), lo, hi, 2 * min(p_pos, p_neg), p_pos, p_neg

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


# planner arms; the paired confirmatory test is ql_true vs ql_false only.
_ARMS = ("rule_based", "ql_false", "ql_true")
_PAIR = ("ql_true", "ql_false")

# Higher-is-better metrics first, then lower-is-better. Orientation is applied
# when deciding `ql_true_better` and when choosing the BH/Cliff sign.
_HIGHER_BETTER = ("goal_rate", "energy_compliance")
_LOWER_BETTER = ("mean_steady_power", "over_budget_rate")
_PAIRED_METRICS = _HIGHER_BETTER + _LOWER_BETTER

_SEED_RE = re.compile(r"^results_seed(\d+)$")


def load_phase4_config(cfg_path: Path) -> dict:
    """Return the phase4 block from run_config.json (profiles, modes, power)."""
    if not cfg_path.is_file():
        raise SystemExit(f"Missing config: {cfg_path}")
    # utf-8-sig transparently strips a UTF-8 BOM (run_config.json is BOM-encoded
    # so the PowerShell runners parse it under Windows PS 5.1).
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    p4 = cfg.get("phase4")
    if not p4:
        raise SystemExit(f"{cfg_path} has no 'phase4' block")
    return p4


def parse_power_formula(formula: str) -> dict[str, float]:
    """`Z1Eff*1 + Z1Ineff*4 + Spotlight*2` -> {Z1Eff:1.0, Z1Ineff:4.0, ...}."""
    weights: dict[str, float] = {}
    for term in (formula or "").split("+"):
        term = term.strip()
        if not term:
            continue
        name, sep, w = term.partition("*")
        name = name.strip()
        if not name:
            continue
        try:
            weights[name] = float(w.strip()) if sep else 1.0
        except ValueError:
            weights[name] = 1.0
    return weights


def load_scenario_budgets(scen_path: Path, default_budget) -> dict[int, float]:
    """{scenario_id: energyBudget} for scenarios that declare one (lab5)."""
    if not scen_path.is_file():
        return {}
    try:
        rows = json.loads(scen_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [!!] could not read {scen_path}: {exc}", file=sys.stderr)
        return {}
    budgets: dict[int, float] = {}
    for r in rows:
        if not isinstance(r, dict) or "id" not in r:
            continue  # comment-only entries have no id
        if "energyBudget" in r and r["energyBudget"] is not None:
            try:
                budgets[int(r["id"])] = float(r["energyBudget"])
            except (TypeError, ValueError):
                continue
    return budgets


def parse_actuator_state(s: str) -> dict[str, bool]:
    """`Z1Eff=true;Z1Ineff=false;...` -> {Z1Eff:True, Z1Ineff:False, ...}.

    Mirrors BenchmarkLogger.buildActuatorString (fragment=true|false) and the
    parser in demo_decision_explainer.py.
    """
    out: dict[str, bool] = {}
    for kv in (s or "").split(";"):
        k, _, v = kv.partition("=")
        k = k.strip()
        if k:
            out[k] = v.strip().lower() == "true"
    return out


def steady_power(state: dict[str, bool], weights: dict[str, float]) -> float:
    """Per-tick power of an actuator configuration under the power formula."""
    return sum(w for name, w in weights.items() if state.get(name, False))


def _seed_token(path: Path) -> str:
    for part in path.parts:
        m = _SEED_RE.match(part)
        if m:
            return f"seed{m.group(1)}"
    return "root"


def find_replicas(root: Path, profile: str, mode: str,
                  allow_flat: bool) -> list[tuple[str, Path, Path | None]]:
    """One (seed_token, step_log, benchmark_results|None) per independent replica.

    Prefers the CI seed layout (<root>/.../results_seed<N>/<profile>/<mode>/);
    de-duplicates the bare `results/` mirror of seed 1 when explicit
    results_seed<N> roots exist. Falls back to a flat <root>/bench_step_log_*.csv
    only when exactly one profile is in scope (local smoke).
    """
    fname_steps = f"bench_step_log_{mode}.csv"
    by_seed: dict[str, Path] = {}
    for step_p in sorted(root.rglob(fname_steps)):
        parts = step_p.parts
        if len(parts) >= 3 and parts[-2] == mode and parts[-3] == profile:
            tok = _seed_token(step_p)
            by_seed.setdefault(tok, step_p)  # first match per seed wins

    explicit = {k: v for k, v in by_seed.items() if k != "root"}
    chosen = explicit if explicit else by_seed

    if not chosen and allow_flat:
        flat = root / fname_steps
        if flat.is_file():
            chosen = {"root": flat}

    out: list[tuple[str, Path, Path | None]] = []
    for tok, step_p in sorted(chosen.items()):
        res_p = step_p.parent / f"benchmark_results_{mode}.csv"
        out.append((tok, step_p, res_p if res_p.is_file() else None))
    return out


def _final_states(step_path: Path) -> dict[tuple[str, str], dict[str, bool]]:
    """{(ScenarioId, RunId): final ActuatorState} (row with the max Step)."""
    best_step: dict[tuple[str, str], int] = {}
    state: dict[tuple[str, str], dict[str, bool]] = {}
    try:
        with step_path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                sid = (r.get("ScenarioId") or "").strip()
                rid = (r.get("RunId") or "").strip()
                if not sid:
                    continue
                try:
                    step = int(float(r.get("Step") or 0))
                except ValueError:
                    step = 0
                key = (sid, rid)
                if key not in best_step or step >= best_step[key]:
                    best_step[key] = step
                    state[key] = parse_actuator_state(r.get("ActuatorState") or "")
    except Exception as exc:  # noqa: BLE001
        print(f"  [!!] could not read {step_path}: {exc}", file=sys.stderr)
    return state


def _goal_flags(res_path: Path | None) -> dict[tuple[str, str], bool]:
    """{(ScenarioId, RunId): GoalReached} from benchmark_results_<mode>.csv."""
    flags: dict[tuple[str, str], bool] = {}
    if res_path is None:
        return flags
    try:
        with res_path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                sid = (r.get("ScenarioId") or "").strip()
                rid = (r.get("RunId") or "").strip()
                if not sid:
                    continue
                flags[(sid, rid)] = (r.get("GoalReached") or "").strip() == "1"
    except Exception as exc:  # noqa: BLE001
        print(f"  [!!] could not read {res_path}: {exc}", file=sys.stderr)
    return flags


def replica_scalars(step_path: Path, res_path: Path | None,
                    weights: dict[str, float], budgets: dict[int, float],
                    default_budget, has_budget: bool) -> dict | None:
    """Reduce one replica's CSVs to per-replica compliance scalars."""
    states = _final_states(step_path)
    goals = _goal_flags(res_path)
    keys = sorted(set(states) | set(goals))
    if not keys:
        return None

    n = 0
    n_goal = 0
    n_compliant = 0
    n_goal_over = 0
    power_sum = 0.0
    for key in keys:
        sid, _rid = key
        reached = goals.get(key, False)
        st = states.get(key, {})
        power = steady_power(st, weights)
        n += 1
        power_sum += power
        if reached:
            n_goal += 1
        if has_budget:
            try:
                budget = budgets.get(int(sid), float(default_budget))
            except (TypeError, ValueError):
                budget = float(default_budget)
            within = power <= budget + 1e-9
            if reached and within:
                n_compliant += 1
            if reached and not within:
                n_goal_over += 1

    goal_rate = n_goal / n if n else float("nan")
    if has_budget:
        energy_compliance = n_compliant / n if n else float("nan")
        over_budget_rate = (n_goal_over / n_goal) if n_goal else 0.0
        mean_power = power_sum / n if n else float("nan")
    else:
        # Dependency lab (no budget): compliance collapses to goal reach; the
        # power-based metrics are not applicable (the AND-gated lamp is not a
        # linear sum of raw actuator states).
        energy_compliance = goal_rate
        over_budget_rate = float("nan")
        mean_power = float("nan")

    return {
        "n_pairs": n,
        "goal_rate": goal_rate,
        "energy_compliance": energy_compliance,
        "mean_steady_power": mean_power,
        "over_budget_rate": over_budget_rate,
    }


def collect_arm(root: Path, profile: str, mode: str, weights: dict[str, float],
                budgets: dict[int, float], default_budget, has_budget: bool,
                allow_flat: bool) -> dict[str, list[float]]:
    """Per-arm metric -> [one scalar per replica]."""
    series: dict[str, list[float]] = {m: [] for m in _PAIRED_METRICS}
    series["_n_pairs"] = []
    for _tok, step_p, res_p in find_replicas(root, profile, mode, allow_flat):
        sc = replica_scalars(step_p, res_p, weights, budgets,
                             default_budget, has_budget)
        if sc is None:
            continue
        for m in _PAIRED_METRICS:
            series[m].append(sc[m])
        series["_n_pairs"].append(sc["n_pairs"])
    return series


def write_ci_table(per_cell: dict, out_dir: Path, iters: int) -> int:
    """phase4_energy_ci.csv: one row per (profile, mode)."""
    rows = []
    for (profile, mode), arm in sorted(per_cell.items()):
        n_rep = len(arm.get("goal_rate", []))
        row = {
            "profile": profile,
            "mode": mode,
            "n_replicas": n_rep,
            "mean_scenarios": (sum(arm["_n_pairs"]) / len(arm["_n_pairs"]))
                if arm.get("_n_pairs") else float("nan"),
        }
        for metric in _PAIRED_METRICS:
            vals = [float(v) for v in arm.get(metric, []) if v == v]
            mean, lo, hi = _bootstrap_ci(vals, iters=iters)
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci_lo"] = lo
            row[f"{metric}_ci_hi"] = hi
        rows.append(row)
    out_path = out_dir / "phase4_energy_ci.csv"
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return 0
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_paired_table(per_cell: dict, profiles: list[str], out_dir: Path,
                       iters: int, has_budget_map: dict[str, bool]) -> int:
    """phase4_energy_paired.csv: ql_true vs ql_false per (profile, metric).

    BH q-values are computed across the whole Phase-4 confirmatory paired family
    (every emitted row), recorded per row as bh_family_m.
    """
    rows: list[dict] = []
    for profile in profiles:
        ta = per_cell.get((profile, "ql_true"))
        fa = per_cell.get((profile, "ql_false"))
        if not ta or not fa:
            continue
        for metric in _PAIRED_METRICS:
            # Skip the non-applicable power metrics for the dependency lab.
            if not has_budget_map.get(profile, False) and metric in _LOWER_BETTER:
                continue
            a = [float(v) for v in ta.get(metric, []) if v == v]
            b = [float(v) for v in fa.get(metric, []) if v == v]
            n_pair = min(len(a), len(b))
            if n_pair == 0:
                continue
            a, b = a[:n_pair], b[:n_pair]
            if n_pair >= 2:
                mean_d, lo, hi, p_boot, _pp, _pn = _paired_bootstrap_diff(a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
            else:
                mean_d = (sum(a) / len(a)) - (sum(b) / len(b))
                lo = hi = p_boot = p_wil = delta = float("nan")
            lower_is_better = metric in _LOWER_BETTER
            better = ""
            if mean_d == mean_d:
                better = (mean_d < 0) if lower_is_better else (mean_d > 0)
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

    ps = [r["p_bootstrap"] for r in rows]
    qs = _bh_qvalues(ps) if ps else []
    for r, q in zip(rows, qs):
        r["q_bootstrap_bh"] = q
        r["bh_family_m"] = len(rows)

    out_path = out_dir / "phase4_energy_paired.csv"
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
        return "   nan" if x != x else f"{x:6.3f}"
    return str(x)


def print_summary(per_cell: dict, profiles: list[str],
                  has_budget_map: dict[str, bool]) -> None:
    print("\n=== Phase 4 energy-budget compliance "
          "(goal_rate & compliance higher=better; power & over_budget lower=better) ===")
    header = (f"{'profile':<8}{'arm':<11}{'n':>3}  {'goal%':>7} {'compl%':>7} "
              f"{'power':>7} {'over%':>7}")
    print(header)
    print("-" * len(header))
    for profile in profiles:
        for mode in _ARMS:
            arm = per_cell.get((profile, mode))
            if not arm:
                continue
            n_rep = len(arm.get("goal_rate", []))
            g, _, _ = _bootstrap_ci([float(v) for v in arm["goal_rate"] if v == v])
            c, _, _ = _bootstrap_ci([float(v) for v in arm["energy_compliance"] if v == v])
            p, _, _ = _bootstrap_ci([float(v) for v in arm["mean_steady_power"] if v == v])
            o, _, _ = _bootstrap_ci([float(v) for v in arm["over_budget_rate"] if v == v])
            g = g * 100 if g == g else float("nan")
            c = c * 100 if c == c else float("nan")
            o = o * 100 if o == o else float("nan")
            print(f"{profile:<8}{mode:<11}{n_rep:>3}  {_fmt(g):>7} {_fmt(c):>7} "
                  f"{_fmt(p):>7} {_fmt(o):>7}")
        if not has_budget_map.get(profile, False):
            print(f"  ({profile}: dependency lab, no energy budget — "
                  f"compliance == goal_rate; see sweep_report goal_rate/redundant)")
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".",
                        help="directory holding the Phase-4 benchmark trees "
                             "(default: .; CI uses 'benchmark')")
    parser.add_argument("--config", default="config/run_config.json",
                        help="run_config.json with the phase4 block")
    parser.add_argument("--scenarios-dir", default="benchmark",
                        help="directory with scenarios_<profile>.json (default: benchmark)")
    parser.add_argument("--out", default="analysis/out",
                        help="output directory (default: analysis/out)")
    parser.add_argument("--profile", action="append", default=None,
                        help="restrict to this profile (repeatable); "
                             "default: phase4_profiles from config")
    parser.add_argument("--iters", type=int, default=10000,
                        help="bootstrap iterations (default: 10000)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    scen_dir = Path(args.scenarios_dir)

    p4 = load_phase4_config(Path(args.config))
    profiles = args.profile or list(p4.get("phase4_profiles", ["lab4", "lab5"]))
    weights = parse_power_formula(p4.get("power_formula", ""))
    default_budget = p4.get("energy_budget_default", 2)
    allow_flat = (len(profiles) == 1)

    per_cell: dict = {}
    has_budget_map: dict[str, bool] = {}
    found_any = False
    for profile in profiles:
        budgets = load_scenario_budgets(scen_dir / f"scenarios_{profile}.json",
                                        default_budget)
        has_budget = bool(budgets)
        has_budget_map[profile] = has_budget
        for mode in _ARMS:
            arm = collect_arm(root, profile, mode, weights, budgets,
                             default_budget, has_budget, allow_flat)
            if arm.get("goal_rate"):
                found_any = True
            per_cell[(profile, mode)] = arm

    if not found_any:
        print(f"No Phase-4 benchmark CSVs (bench_step_log_* / benchmark_results_*) "
              f"found under {root} for profiles {profiles}.\n"
              f"Run the Phase-4 workflow first (.github/workflows/phase4.yml) or "
              f"a local smoke:  ./run_full_project.ps1 -RunMode phase4 "
              f"-OnlyProfiles lab5", file=sys.stderr)
        # Still emit empty outputs so downstream steps do not crash.
        write_ci_table(per_cell, out_dir, args.iters)
        write_paired_table(per_cell, profiles, out_dir, args.iters, has_budget_map)
        return 0

    n_ci = write_ci_table(per_cell, out_dir, args.iters)
    n_pair = write_paired_table(per_cell, profiles, out_dir, args.iters, has_budget_map)
    print_summary(per_cell, profiles, has_budget_map)
    print(f"Wrote {n_ci} CI rows -> {out_dir / 'phase4_energy_ci.csv'}")
    print(f"Wrote {n_pair} paired rows -> {out_dir / 'phase4_energy_paired.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
