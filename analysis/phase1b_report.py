#!/usr/bin/env python3
"""Registered Phase-1b confirmatory analysis (frozen family) + supporting outcomes.

Registration 2026-07-26 §4: the confirmatory BH family is the five RETAINED
members M1-M4, M6 (m=5); M5 was prospectively relabelled EXPLORATORY by the
frozen power rule BEFORE any confirmatory dispatch. M5 is still computed and
reported identically (mean, CI, exact p-values) but carries
bh_family_m="exploratory" and no confirmatory q.

Archive layout (identical file conventions to the Phase-1 v2 runs, with the
Phase-1b mode as the top-level directory):

    <root>/<mode>/results_seed<N>/<profile>/
        training_stereo_<true|false>/metrics_stereotypes_<arm>_<profile>.csv
        training_stereo_<true|false>/first_goal_stereotypes_<arm>_<profile>.csv
        ql_<true|false>/benchmark_results_ql_<arm>.csv

where <mode> is one of phase1b_v2_baseline, phase1b_v2_redundancy_only,
phase1b_v2_kg_frozen, phase1b_v2_extended. A legacy <root>/<mode>/benchmark/
results_seed<N>/ nesting is also accepted. The stereo-true arm of each mode is
the arm of record; the stereo-false arm is retained as a within-mode control
(descriptive only).

Frozen member enumeration (FAMILY below; membership never changes with data):
  M1 labrel_stateless_frozen_slope    per-seed OLS slope over K in {0,4,8,16}
                                      of auc_goal[labrelK, kg_frozen] -
                                      auc_goal[labrelK, baseline]
  M2 labrel_incremental_slope         same with extended - kg_frozen
  M3 labrel8s_fragmentation_did       ((kg_frozen-baseline)@labrel8s) -
                                      ((kg_frozen-baseline)@labrel8) on auc_goal
  M4 labband_extended_vs_frozen_auc   auc_goal[labband, extended] -
                                      auc_goal[labband, kg_frozen]
  M5 labband_extended_vs_baseline_dev avg CumIlluminanceDeviation[labband,
                                      extended] - [labband, baseline]
                                      (predicted negative)
  M6 chain3_frozen_vs_baseline_rmst   RMST[lab4chain3, kg_frozen] -
                                      RMST[lab4chain3, baseline] (predicted
                                      negative). FROZEN CENSORING RULE: if the
                                      pooled (scenario x seed) censoring
                                      fraction exceeds 25% in EITHER arm the
                                      member switches to benchmark goal rate
                                      (kg_frozen - baseline, predicted
                                      positive) and endpoint="goal_rate" is
                                      recorded together with both censoring
                                      fractions; otherwise endpoint="rmst".

Statistics: exact two-sided paired sign-flip test on the per-seed member
statistic (null: zero mean), exact sign test, matched-pairs rank-biserial,
fixed-seed 10,000-draw bootstrap 95% CI, Benjamini-Hochberg over exactly the
five RETAINED sign-flip p-values. No p or q may ever be reported as 0 (the exact
enumeration floors at 2/2^n; a hard guard refuses to emit a zero anyway).

Pilot-blinding contract: --pilot-diagnostics emits ONLY the allow-listed
diagnostic report (artifact completeness, per-cell censoring fractions,
centred-residual paired-difference variances, degeneracy flags) and REFUSES to
write the family CSV, arm-labelled means, effect directions, or p-values.

Usage:
  python analysis/phase1b_report.py --roots <dir> [<dir>...] --out <dir> \
      [--rmst-horizon <int>] [--bootstrap-iters <int>] [--pilot-diagnostics]
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

try:
    from analysis import exact_paired_stats as eps
    from analysis import sweep_report as sr
except ImportError:  # executed as a script from the repo root
    import exact_paired_stats as eps  # type: ignore
    import sweep_report as sr  # type: ignore


MODE_BASELINE = "phase1b_v2_baseline"
MODE_REDUNDANCY = "phase1b_v2_redundancy_only"
MODE_FROZEN = "phase1b_v2_kg_frozen"
MODE_EXTENDED = "phase1b_v2_extended"
MODES = (MODE_BASELINE, MODE_REDUNDANCY, MODE_FROZEN, MODE_EXTENDED)
# Modes that the frozen family reads; redundancy_only feeds SUPPORTING only.
FAMILY_MODES = (MODE_BASELINE, MODE_FROZEN, MODE_EXTENDED)

LABREL_KS = (0, 4, 8, 16)
LABREL_PROFILES = tuple(f"labrel{k}" for k in LABREL_KS)
FRAG_PROFILE = "labrel8s"
BAND_PROFILE = "labband"
CHAIN_PROFILE = "lab4chain3"
PROFILES = LABREL_PROFILES + (FRAG_PROFILE, BAND_PROFILE, CHAIN_PROFILE)

ARM_OF_RECORD = "true"
ARMS = ("true", "false")

# Fixed registered training horizon; the default RMST censoring horizon H is
# the per-scenario presentation count of this fixed horizon,
# i.e. FIXED_TRAINING_EPISODES // scenario_count.
FIXED_TRAINING_EPISODES = 3000
CENSORING_SWITCH_FRACTION = 0.25  # frozen: switch endpoint when frac > 25%

BOOTSTRAP_ITERS = 10_000
BOOTSTRAP_BASE_SEED = 20260725  # fixed-seed convention mirrors phase4_v2_registered_family
SUPPORTING_BOOTSTRAP_OFFSET = 200

# Accepted ProtocolVersion values for the v2 first-goal tracker files.
FIRST_GOAL_PROTOCOLS = ("phase1-v2", "phase1b-v2")

# Frozen enumeration: (member_id, registered_test, metric, predicted_direction).
# Membership never changes with data; the confirmatory BH family is
# FAMILY minus EXPLORATORY_MEMBERS (registration 2026-07-26 §4).
FAMILY = (
    ("M1", "labrel_stateless_frozen_slope", "auc_goal_slope_per_K", "positive"),
    ("M2", "labrel_incremental_slope", "auc_goal_slope_per_K", "positive"),
    ("M3", "labrel8s_fragmentation_did", "auc_goal_did", "positive"),
    ("M4", "labband_extended_vs_frozen_auc", "auc_goal", "positive"),
    ("M5", "labband_extended_vs_baseline_dev", "avg_dev", "negative"),
    # (M5 is computed identically but reported as EXPLORATORY — see
    #  EXPLORATORY_MEMBERS below and registration 2026-07-26 §4.)
    ("M6", "chain3_frozen_vs_baseline_rmst", "rmst_first_success", "negative"),
)

# Registration 2026-07-26 §4: prospectively exploratory members (frozen power
# rule). They stay in FAMILY (computed + reported identically) but are outside
# the confirmatory BH family.
EXPLORATORY_MEMBERS = {"M5"}

FAMILY_FIELDS = [
    "member", "registered_test", "metric", "endpoint", "n_paired",
    "seeds_paired", "mean_paired_statistic", "median_paired_statistic",
    "ci_lo_bootstrap", "ci_hi_bootstrap", "p_signflip_two_sided",
    "p_sign_exact_two_sided", "paired_rank_biserial",
    "q_signflip_bh", "bh_family_m", "predicted_direction",
    "censoring_fraction_kg_frozen", "censoring_fraction_baseline",
    "rmst_horizon",
]

SUPPORTING_FIELDS = [
    "row_type", "name", "profile", "mode", "arm", "seed", "metric",
    "presentation", "value", "n", "ci_lo_bootstrap", "ci_hi_bootstrap",
    "p_signflip_two_sided_uncorrected", "endpoint", "note",
]

PILOT_FIELDS = ["row_type", "name", "mode", "profile", "arm", "seed",
                "detail", "value"]


# ---------------------------------------------------------------------------
# Pure statistics helpers
# ---------------------------------------------------------------------------

def rmst(times: list[float], censored_flags: list[bool],
         horizon: float) -> float:
    """Presentation-indexed restricted mean time to first success.

    Mean over scenarios of min(first_success_presentation, horizon); censored
    scenarios contribute exactly ``horizon``.
    """
    if len(times) != len(censored_flags):
        raise ValueError("times and censored_flags must have equal length")
    if not times:
        return float("nan")
    total = 0.0
    for value, censored in zip(times, censored_flags):
        total += float(horizon) if censored else min(float(value), float(horizon))
    return total / len(times)


def ols_slope(xs: list[float], ys: list[float]) -> float:
    """Least-squares slope of ys on xs (used for the within-seed K-slopes)."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("need at least two (x, y) points")
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    sxx = sum((x - x_mean) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("degenerate x values: zero variance")
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    return sxy / sxx


def centred_residual_variance(values: list[float]) -> float:
    """Sample variance of (values - mean(values)); direction-free by design."""
    n = len(values)
    if n < 2:
        return float("nan")
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / (n - 1)


def _bootstrap_ci(diffs: list[float], seed_offset: int,
                  iters: int) -> tuple[float, float]:
    """Fixed-seed percentile bootstrap CI of the mean, mirroring the
    phase4_v2_registered_family convention (random.Random(BASE + index))."""
    if len(diffs) < 2:
        return float("nan"), float("nan")
    rng = random.Random(BOOTSTRAP_BASE_SEED + seed_offset)
    boots = []
    for _ in range(iters):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        boots.append(sum(sample) / len(sample))
    boots.sort()
    lo = boots[int(0.025 * iters)]
    hi = boots[min(iters - 1, int(0.975 * iters))]
    return lo, hi


# ---------------------------------------------------------------------------
# Archive readers (conventions mirror analysis/sweep_report.py; pure shared
# functions are imported from it, never re-implemented, except where noted)
# ---------------------------------------------------------------------------

def _read_first_goal_v2(path: Path) -> list[dict]:
    """Read a protocol-v2 first-goal tracker file, keeping per-scenario rows.

    Mirrors sweep_report._read_first_goal_details (frozen), which only returns
    the mean; the RMST endpoint additionally needs the per-scenario Censored
    flags, so this local reader keeps every row. Columns are read by name:
    {ProtocolVersion, ScenarioId, Presentations, Censored, AnalysisPresentation}.
    """
    rows: list[dict] = []
    seen: set[int] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {"ProtocolVersion", "ScenarioId", "Presentations",
                    "Censored", "AnalysisPresentation"}
        if not required.issubset(fields):
            raise SystemExit(
                f"{path}: not a protocol-v2 first-goal file "
                f"(missing {sorted(required - fields)})")
        for row in reader:
            protocol = (row.get("ProtocolVersion") or "").strip()
            if not protocol or protocol.startswith("#"):
                continue  # trailing comment lines, as in the v1 files
            if protocol not in FIRST_GOAL_PROTOCOLS:
                raise SystemExit(
                    f"{path}: unexpected first-goal protocol {protocol!r}")
            scenario_id = int((row.get("ScenarioId") or "").strip())
            if scenario_id in seen:
                raise SystemExit(f"{path}: duplicate scenario {scenario_id}")
            seen.add(scenario_id)
            censored_text = (row.get("Censored") or "").strip().lower()
            rows.append({
                "scenario_id": scenario_id,
                "presentations": int(float((row.get("Presentations") or "").strip())),
                "censored": censored_text in ("1", "true", "yes"),
                "analysis_presentation": float(
                    (row.get("AnalysisPresentation") or "").strip()),
            })
    if not rows:
        raise SystemExit(f"{path}: empty first-goal file")
    return rows


class ArchiveIndex:
    """Locates and caches per-cell primitives across one or more archive roots."""

    def __init__(self, roots: list[Path]):
        self.roots = [Path(root) for root in roots]
        self._cache: dict = {}

    # -- layout ------------------------------------------------------------

    def mode_seeds(self, mode: str) -> list[int]:
        seeds: set[int] = set()
        for root in self.roots:
            for parent in (root / mode, root / mode / "benchmark"):
                for seed, _ in sr.find_seed_roots(parent):
                    seeds.add(seed)
        return sorted(seeds)

    def cell_dir(self, mode: str, seed: int, profile: str,
                 required: bool = True) -> Path | None:
        matches = []
        for root in self.roots:
            for parent in (root / mode, root / mode / "benchmark"):
                candidate = parent / f"results_seed{seed}" / profile
                if candidate.is_dir():
                    matches.append(candidate)
        if len(matches) > 1:
            raise SystemExit(
                f"duplicate cell {mode}/results_seed{seed}/{profile} across "
                f"roots: {[str(m) for m in matches]}")
        if not matches:
            if required:
                raise SystemExit(
                    f"missing required cell {mode}/results_seed{seed}/{profile} "
                    f"under roots {[str(r) for r in self.roots]}")
            return None
        return matches[0]

    def _arm_file(self, cell: Path, profile: str, arm: str,
                  stem: str) -> Path | None:
        """training_stereo_<arm>/ first, legacy ql_<arm>/ fallback (mirrors
        sweep_report._collect_learning_speed_by_cell)."""
        for mode_dir in (f"training_stereo_{arm}", f"ql_{arm}"):
            candidate = cell / mode_dir / f"{stem}_stereotypes_{arm}_{profile}.csv"
            if candidate.is_file():
                return candidate
        return None

    # -- primitives --------------------------------------------------------

    def auc_goal(self, mode: str, seed: int, profile: str,
                 arm: str = ARM_OF_RECORD, required: bool = True) -> float | None:
        key = ("auc", mode, seed, profile, arm)
        if key not in self._cache:
            self._cache[key] = self._auc_goal(mode, seed, profile, arm, required)
        value = self._cache[key]
        if value is None and required:
            raise SystemExit(
                f"missing training metrics for {mode}/seed{seed}/{profile}/"
                f"stereo_{arm}")
        return value

    def _auc_goal(self, mode, seed, profile, arm, required):
        cell = self.cell_dir(mode, seed, profile, required=required)
        if cell is None:
            return None
        path = self._arm_file(cell, profile, arm, "metrics")
        if path is None:
            return None
        # auc_goal = mean of the 0/1 GoalReached column over the fixed
        # training horizon (sweep_report._auc_normalised on protocol-v2 data).
        goals, _ = sr._load_episode_metrics(path)
        if not goals:
            return None
        return sr._auc_normalised(goals)

    def first_goal(self, mode: str, seed: int, profile: str,
                   arm: str = ARM_OF_RECORD,
                   required: bool = True) -> list[dict] | None:
        key = ("fg", mode, seed, profile, arm)
        if key not in self._cache:
            cell = self.cell_dir(mode, seed, profile, required=required)
            path = None if cell is None else self._arm_file(
                cell, profile, arm, "first_goal")
            self._cache[key] = None if path is None else _read_first_goal_v2(path)
        value = self._cache[key]
        if value is None and required:
            raise SystemExit(
                f"missing first-goal file for {mode}/seed{seed}/{profile}/"
                f"stereo_{arm}")
        return value

    def benchmark_summary(self, mode: str, seed: int, profile: str,
                          arm: str = ARM_OF_RECORD) -> dict:
        key = ("bench", mode, seed, profile, arm)
        if key not in self._cache:
            cell = self.cell_dir(mode, seed, profile, required=False)
            summary: dict = {}
            if cell is not None:
                bench = cell / f"ql_{arm}" / f"benchmark_results_ql_{arm}.csv"
                summary = sr.summarise_benchmark(bench)
            self._cache[key] = summary
        return self._cache[key]

    def benchmark_rows(self, mode: str, seed: int, profile: str,
                       arm: str = ARM_OF_RECORD) -> list[dict]:
        cell = self.cell_dir(mode, seed, profile, required=False)
        if cell is None:
            return []
        bench = cell / f"ql_{arm}" / f"benchmark_results_ql_{arm}.csv"
        if not bench.is_file():
            return []
        with bench.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def required_benchmark_metric(self, mode: str, seed: int, profile: str,
                                  metric: str) -> float:
        summary = self.benchmark_summary(mode, seed, profile)
        if metric not in summary:
            raise SystemExit(
                f"missing benchmark metric {metric} for {mode}/seed{seed}/"
                f"{profile}/ql_{ARM_OF_RECORD}")
        return float(summary[metric])


# ---------------------------------------------------------------------------
# Member statistics (per-seed vectors; arm of record only)
# ---------------------------------------------------------------------------

def _labrel_slopes(index: ArchiveIndex, seeds: list[int], hi_mode: str,
                   lo_mode: str) -> list[float]:
    slopes = []
    xs = [float(k) for k in LABREL_KS]
    for seed in seeds:
        deltas = [index.auc_goal(hi_mode, seed, profile)
                  - index.auc_goal(lo_mode, seed, profile)
                  for profile in LABREL_PROFILES]
        slopes.append(ols_slope(xs, deltas))
    return slopes


def _fragmentation_did(index: ArchiveIndex, seeds: list[int], hi_mode: str,
                       lo_mode: str) -> list[float]:
    out = []
    for seed in seeds:
        frag = index.auc_goal(hi_mode, seed, FRAG_PROFILE) \
            - index.auc_goal(lo_mode, seed, FRAG_PROFILE)
        base = index.auc_goal(hi_mode, seed, "labrel8") \
            - index.auc_goal(lo_mode, seed, "labrel8")
        out.append(frag - base)
    return out


def _band_auc_diff(index: ArchiveIndex, seeds: list[int], hi_mode: str,
                   lo_mode: str) -> list[float]:
    return [index.auc_goal(hi_mode, seed, BAND_PROFILE)
            - index.auc_goal(lo_mode, seed, BAND_PROFILE) for seed in seeds]


def _band_dev_diff(index: ArchiveIndex, seeds: list[int], hi_mode: str,
                   lo_mode: str) -> list[float]:
    return [index.required_benchmark_metric(hi_mode, seed, BAND_PROFILE, "avg_dev")
            - index.required_benchmark_metric(lo_mode, seed, BAND_PROFILE, "avg_dev")
            for seed in seeds]


def _chain_first_goal(index: ArchiveIndex, seeds: list[int],
                      mode: str) -> dict[int, list[dict]]:
    return {seed: index.first_goal(mode, seed, CHAIN_PROFILE) for seed in seeds}


def _chain_horizon(cells: dict[int, list[dict]],
                   override: int | None) -> int:
    counts = {len(rows) for rows in cells.values()}
    if len(counts) != 1:
        raise SystemExit(
            f"inconsistent {CHAIN_PROFILE} scenario counts across cells: "
            f"{sorted(counts)}")
    if override is not None:
        return int(override)
    scenario_count = counts.pop()
    # Default frozen horizon H = per-scenario presentation count of the fixed
    # 3000-episode training horizon.
    return FIXED_TRAINING_EPISODES // scenario_count


def _censoring_fraction(cells: dict[int, list[dict]]) -> float:
    total = sum(len(rows) for rows in cells.values())
    censored = sum(1 for rows in cells.values() for row in rows
                   if row["censored"])
    return censored / total if total else float("nan")


def _cell_rmst(rows: list[dict], horizon: int) -> float:
    return rmst([row["analysis_presentation"] for row in rows],
                [row["censored"] for row in rows], horizon)


def _chain_endpoint(index: ArchiveIndex, seeds: list[int], hi_mode: str,
                    lo_mode: str, horizon_override: int | None) -> dict:
    """Apply the frozen M6 censoring rule and return the per-seed diffs."""
    hi_cells = _chain_first_goal(index, seeds, hi_mode)
    lo_cells = _chain_first_goal(index, seeds, lo_mode)
    horizon = _chain_horizon({**hi_cells, **{-s: r for s, r in lo_cells.items()}},
                             horizon_override)
    frac_hi = _censoring_fraction(hi_cells)
    frac_lo = _censoring_fraction(lo_cells)
    if frac_hi > CENSORING_SWITCH_FRACTION or frac_lo > CENSORING_SWITCH_FRACTION:
        diffs = [index.required_benchmark_metric(hi_mode, seed, CHAIN_PROFILE,
                                                 "goal_rate")
                 - index.required_benchmark_metric(lo_mode, seed, CHAIN_PROFILE,
                                                   "goal_rate")
                 for seed in seeds]
        endpoint, predicted = "goal_rate", "positive"
    else:
        diffs = [_cell_rmst(hi_cells[seed], horizon)
                 - _cell_rmst(lo_cells[seed], horizon) for seed in seeds]
        endpoint, predicted = "rmst", "negative"
    return {
        "diffs": diffs,
        "endpoint": endpoint,
        "predicted_direction": predicted,
        "censoring_fraction_hi": frac_hi,
        "censoring_fraction_lo": frac_lo,
        "rmst_horizon": horizon,
    }


def _member_diffs(index: ArchiveIndex, seeds: list[int],
                  rmst_horizon: int | None,
                  hi_lo_override: tuple[str, str] | None = None) -> dict[str, dict]:
    """Per-seed statistic vectors for all six members.

    ``hi_lo_override`` replaces every member's contrast arm pair (used for the
    supporting redundancy_only-minus-baseline analogues); the default uses the
    registered mode pairs.
    """
    def pair(default_hi: str, default_lo: str) -> tuple[str, str]:
        return hi_lo_override if hi_lo_override else (default_hi, default_lo)

    out: dict[str, dict] = {}
    hi, lo = pair(MODE_FROZEN, MODE_BASELINE)
    out["M1"] = {"diffs": _labrel_slopes(index, seeds, hi, lo)}
    hi, lo = pair(MODE_EXTENDED, MODE_FROZEN)
    out["M2"] = {"diffs": _labrel_slopes(index, seeds, hi, lo)}
    hi, lo = pair(MODE_FROZEN, MODE_BASELINE)
    out["M3"] = {"diffs": _fragmentation_did(index, seeds, hi, lo)}
    hi, lo = pair(MODE_EXTENDED, MODE_FROZEN)
    out["M4"] = {"diffs": _band_auc_diff(index, seeds, hi, lo)}
    hi, lo = pair(MODE_EXTENDED, MODE_BASELINE)
    out["M5"] = {"diffs": _band_dev_diff(index, seeds, hi, lo)}
    hi, lo = pair(MODE_FROZEN, MODE_BASELINE)
    out["M6"] = _chain_endpoint(index, seeds, hi, lo, rmst_horizon)
    return out


# ---------------------------------------------------------------------------
# Family CSV
# ---------------------------------------------------------------------------

def _guard_nonzero(label: str, value: float) -> float:
    if value == 0.0:
        raise SystemExit(
            f"refusing to report {label} = 0; the exact tests floor at "
            "2/2^n and a zero indicates a computation error")
    return value


def build_family_rows(index: ArchiveIndex, seeds: list[int],
                      rmst_horizon: int | None,
                      bootstrap_iters: int) -> list[dict]:
    members = _member_diffs(index, seeds, rmst_horizon)
    zeros_cache: dict[int, list[float]] = {}
    rows: list[dict] = []
    p_values: list[float] = []
    for family_index, (member, name, metric, predicted) in enumerate(FAMILY):
        info = members[member]
        diffs = info["diffs"]
        zeros = zeros_cache.setdefault(len(diffs), [0.0] * len(diffs))
        p = _guard_nonzero(f"{member} p_signflip",
                           eps.paired_signflip_p(diffs, zeros))
        lo, hi = _bootstrap_ci(diffs, family_index, bootstrap_iters)
        row = {
            "member": member,
            "registered_test": name,
            "metric": metric,
            "endpoint": info.get("endpoint", metric),
            "n_paired": len(diffs),
            "seeds_paired": ";".join(str(seed) for seed in seeds),
            "mean_paired_statistic": sum(diffs) / len(diffs),
            "median_paired_statistic": eps.median(diffs),
            "ci_lo_bootstrap": lo,
            "ci_hi_bootstrap": hi,
            "p_signflip_two_sided": p,
            "p_sign_exact_two_sided": _guard_nonzero(
                f"{member} p_sign", eps.exact_sign_p(diffs, zeros)),
            "paired_rank_biserial": eps.paired_rank_biserial(diffs, zeros),
            "bh_family_m": len(FAMILY),
            "predicted_direction": info.get("predicted_direction", predicted),
            "censoring_fraction_kg_frozen":
                info.get("censoring_fraction_hi", ""),
            "censoring_fraction_baseline":
                info.get("censoring_fraction_lo", ""),
            "rmst_horizon": info.get("rmst_horizon", ""),
        }
        rows.append(row)
        p_values.append(p)
    # Registration 2026-07-26 §4: M5 is prospectively EXPLORATORY (frozen
    # power rule: under-powered at every candidate N). The confirmatory BH
    # family is the five RETAINED members; M5's p-values are reported but it
    # receives no confirmatory q and does not influence the retained q's.
    retained = [(row, p) for row, p in zip(rows, p_values)
                if row["member"] not in EXPLORATORY_MEMBERS]
    for row in rows:
        if row["member"] in EXPLORATORY_MEMBERS:
            row["bh_family_m"] = "exploratory"
            row["q_signflip_bh"] = ""
    for (row, _p), q in zip(retained,
                            eps.bh_qvalues([p for _row, p in retained])):
        row["bh_family_m"] = len(retained)
        row["q_signflip_bh"] = _guard_nonzero(
            f"{row['member']} q_bh", q)
    return rows


# ---------------------------------------------------------------------------
# Supporting CSV (registered secondary outcomes; OUTSIDE the BH family)
# ---------------------------------------------------------------------------

def _supporting_row(**kwargs) -> dict:
    row = {field: "" for field in SUPPORTING_FIELDS}
    row.update(kwargs)
    return row


def _redundancy_contrast_rows(index: ArchiveIndex, seeds: list[int],
                              rmst_horizon: int | None,
                              bootstrap_iters: int) -> list[dict]:
    if not index.mode_seeds(MODE_REDUNDANCY):
        return [_supporting_row(
            row_type="redundancy_contrast", name="all_members",
            note="redundancy_only cells missing; contrasts not computable")]
    members = _member_diffs(index, seeds, rmst_horizon,
                            hi_lo_override=(MODE_REDUNDANCY, MODE_BASELINE))
    rows = []
    for offset, (member, name, metric, _) in enumerate(FAMILY):
        info = members[member]
        diffs = info["diffs"]
        zeros = [0.0] * len(diffs)
        lo, hi = _bootstrap_ci(diffs, SUPPORTING_BOOTSTRAP_OFFSET + offset,
                               bootstrap_iters)
        note = "redundancy_only minus baseline analogue"
        if member == "M2":
            note += "; identical construction to the M1 analogue"
        rows.append(_supporting_row(
            row_type="redundancy_contrast",
            name=f"{member}_{name}_redundancy_only_analogue",
            metric=metric,
            value=sum(diffs) / len(diffs),
            n=len(diffs),
            ci_lo_bootstrap=lo,
            ci_hi_bootstrap=hi,
            p_signflip_two_sided_uncorrected=_guard_nonzero(
                f"supporting {member} p",
                eps.paired_signflip_p(diffs, zeros)),
            endpoint=info.get("endpoint", metric),
            note=note))
    return rows


def _mean_over_seeds(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _descriptive_rows(index: ArchiveIndex, seeds: list[int],
                      rmst_horizon: int | None,
                      legacy_archive_format: bool = False) -> list[dict]:
    rows: list[dict] = []
    rung_profiles = LABREL_PROFILES + (FRAG_PROFILE,)
    for mode in MODES:
        mode_seed_list = index.mode_seeds(mode)
        if not mode_seed_list:
            continue
        # Per-rung auc_goal descriptives (both arms; stereo-false is the
        # within-mode control).
        for profile in rung_profiles:
            for arm in ARMS:
                values = [v for v in (index.auc_goal(mode, s, profile, arm=arm,
                                                     required=False)
                                      for s in mode_seed_list) if v is not None]
                if values:
                    rows.append(_supporting_row(
                        row_type="rung_descriptive", profile=profile,
                        mode=mode, arm=arm, metric="auc_goal",
                        value=_mean_over_seeds(values), n=len(values)))
        # First-success curve data (pooled ECDF over scenario x seed cells).
        for profile in PROFILES:
            cells = [index.first_goal(mode, s, profile, required=False)
                     for s in mode_seed_list]
            cells = [c for c in cells if c]
            if not cells:
                continue
            total = sum(len(c) for c in cells)
            times = sorted(row["analysis_presentation"]
                           for c in cells for row in c if not row["censored"])
            for t in sorted(set(times)):
                rows.append(_supporting_row(
                    row_type="first_success_curve", profile=profile,
                    mode=mode, arm=ARM_OF_RECORD,
                    metric="cum_success_fraction", presentation=t,
                    value=sum(1 for v in times if v <= t) / total, n=total))
        # Benchmark descriptives: deterministic PolicyEnergyCost + cycling.
        for profile in PROFILES:
            energies, cyclings = [], []
            for s in mode_seed_list:
                summary = index.benchmark_summary(mode, s, profile)
                if "avg_policy_energy" in summary:
                    energies.append(float(summary["avg_policy_energy"]))
                if "avg_cycling" in summary:
                    cyclings.append(float(summary["avg_cycling"]))
            if energies:
                rows.append(_supporting_row(
                    row_type="policy_energy", profile=profile, mode=mode,
                    arm=ARM_OF_RECORD, metric="avg_policy_energy_mean",
                    value=_mean_over_seeds(energies), n=len(energies)))
            if cyclings:
                rows.append(_supporting_row(
                    row_type="cycling", profile=profile, mode=mode,
                    arm=ARM_OF_RECORD, metric="avg_cycling_mean",
                    value=_mean_over_seeds(cyclings), n=len(cyclings)))
        if legacy_archive_format:
            # Historical 2026-07-27 archive serialization. This compatibility
            # path exists only so reproduce_phase1b.py can byte-check the
            # immutable archived CSV; new reports must state that the
            # registered within-episode overshoot event outcome was unmeasured.
            rows.append(_legacy_overshoot_proxy_row(index, mode,
                                                    mode_seed_list))
        else:
            rows.append(_unmeasured_overshoot_row(mode))
        # Per-cell primitives for the arm of record.
        rows.extend(_cell_primitive_rows(index, mode, mode_seed_list,
                                         rmst_horizon))
    return [row for row in rows if row]


def _unmeasured_overshoot_row(mode: str) -> dict:
    return _supporting_row(
        row_type="unmeasured_outcome",
        name="labband_overshoot_events",
        profile=BAND_PROFILE,
        mode=mode,
        arm=ARM_OF_RECORD,
        metric="within_episode_overshoot_event_count",
        value="NA",
        note="REGISTERED BUT UNMEASURED: benchmark outputs contain no "
             "within-episode rank trajectory, so overshoot event counts "
             "cannot be derived from the run-of-record artifacts")


def _legacy_overshoot_proxy_row(index: ArchiveIndex, mode: str,
                                seeds: list[int]) -> dict | None:
    """Recreate the immutable archive's superseded final-rank proxy row."""
    pooled_rows: list[dict] = []
    for seed in seeds:
        pooled_rows.extend(index.benchmark_rows(mode, seed, BAND_PROFILE))
    if not pooled_rows:
        return None
    fields = list(pooled_rows[0].keys())
    pairs = [(f, "TargetRank" + f[len("FinalRank"):]) for f in fields
             if f.startswith("FinalRank")
             and ("TargetRank" + f[len("FinalRank"):]) in fields]
    if not pairs:
        return _supporting_row(
            row_type="overshoot_proxy", profile=BAND_PROFILE, mode=mode,
            arm=ARM_OF_RECORD, metric="final_rank_above_target_fraction",
            value="NA",
            note="no FinalRank/TargetRank columns in benchmark CSV; "
                 "deviation-above-band not derivable")
    overshoot = 0
    for row in pooled_rows:
        if any(float(row[final] or 0) > float(row[target] or 0)
               for final, target in pairs):
            overshoot += 1
    return _supporting_row(
        row_type="overshoot_proxy", profile=BAND_PROFILE, mode=mode,
        arm=ARM_OF_RECORD, metric="final_rank_above_target_fraction",
        value=overshoot / len(pooled_rows), n=len(pooled_rows))


def _cell_primitive_rows(index: ArchiveIndex, mode: str, seeds: list[int],
                         rmst_horizon: int | None) -> list[dict]:
    rows: list[dict] = []
    for profile in PROFILES:
        for seed in seeds:
            auc = index.auc_goal(mode, seed, profile, required=False)
            if auc is not None:
                rows.append(_supporting_row(
                    row_type="cell_primitive", profile=profile, mode=mode,
                    arm=ARM_OF_RECORD, seed=seed, metric="auc_goal",
                    value=auc))
            fg = index.first_goal(mode, seed, profile, required=False)
            if fg:
                mean_first = _mean_over_seeds(
                    [row["analysis_presentation"] for row in fg])
                rows.append(_supporting_row(
                    row_type="cell_primitive", profile=profile, mode=mode,
                    arm=ARM_OF_RECORD, seed=seed,
                    metric="mean_first_success_presentation",
                    value=mean_first))
                horizon = (rmst_horizon if rmst_horizon is not None
                           else FIXED_TRAINING_EPISODES // len(fg))
                rows.append(_supporting_row(
                    row_type="cell_primitive", profile=profile, mode=mode,
                    arm=ARM_OF_RECORD, seed=seed, metric="rmst",
                    value=_cell_rmst(fg, horizon), note=f"H={horizon}"))
            summary = index.benchmark_summary(mode, seed, profile)
            for source, label in (("avg_dev", "avg_dev"),
                                  ("avg_cycling", "avg_cycling"),
                                  ("avg_wasted", "avg_wasted"),
                                  ("avg_policy_energy", "avg_policy_energy"),
                                  ("goal_rate", "benchmark_goal_rate")):
                if source in summary:
                    rows.append(_supporting_row(
                        row_type="cell_primitive", profile=profile, mode=mode,
                        arm=ARM_OF_RECORD, seed=seed, metric=label,
                        value=float(summary[source])))
    return rows


# ---------------------------------------------------------------------------
# Pilot-safe diagnostics (allow-listed; NEVER emits arm-labelled means,
# effect directions, p-values, or the family CSV)
# ---------------------------------------------------------------------------

def build_pilot_rows(index: ArchiveIndex, rmst_horizon: int | None) -> list[dict]:
    rows: list[dict] = []
    seeds_by_mode = {mode: index.mode_seeds(mode) for mode in MODES}
    for mode, seeds in seeds_by_mode.items():
        rows.append({"row_type": "completeness", "name": "n_seed_dirs",
                     "mode": mode, "profile": "", "arm": "", "seed": "",
                     "detail": "", "value": len(seeds)})
    for mode, seeds in seeds_by_mode.items():
        for seed in seeds:
            for profile in PROFILES:
                cell = index.cell_dir(mode, seed, profile, required=False)
                for arm in ARMS:
                    present = {
                        "training_metrics": bool(
                            cell and index._arm_file(cell, profile, arm,
                                                     "metrics")),
                        "first_goal": bool(
                            cell and index._arm_file(cell, profile, arm,
                                                     "first_goal")),
                        "benchmark": bool(
                            cell and (cell / f"ql_{arm}"
                                      / f"benchmark_results_ql_{arm}.csv"
                                      ).is_file()),
                    }
                    for detail, flag in present.items():
                        rows.append({
                            "row_type": "artifact_presence", "name": "",
                            "mode": mode, "profile": profile, "arm": arm,
                            "seed": seed, "detail": detail,
                            "value": int(flag)})
                    if present["first_goal"]:
                        fg = index.first_goal(mode, seed, profile, arm=arm,
                                              required=False)
                        frac = (sum(1 for r in fg if r["censored"]) / len(fg)
                                if fg else float("nan"))
                        rows.append({
                            "row_type": "censoring_fraction", "name": "",
                            "mode": mode, "profile": profile, "arm": arm,
                            "seed": seed, "detail": "cell_censored_fraction",
                            "value": frac})
    # Centred-residual paired-difference variances per family member: each
    # per-seed vector has its own mean subtracted first, so no effect
    # direction or arm-labelled mean is visible in the output.
    seeds = _family_seed_set(index, strict=False)
    for member, name, metric, _ in FAMILY:
        detail, value = "", ""
        if seeds and len(seeds) >= 2:
            try:
                info = _member_diffs(index, seeds, rmst_horizon)[member]
                diffs = info["diffs"]
                value = centred_residual_variance(diffs)
                detail = f"n={len(diffs)}"
                if member == "M6":
                    detail += f";endpoint={info['endpoint']}"
                rows.append({
                    "row_type": "degeneracy_flag", "name": f"{member}_{name}",
                    "mode": "", "profile": "", "arm": "", "seed": "",
                    "detail": "zero_variance_paired_differences",
                    "value": int(value == 0.0)})
            except SystemExit as exc:
                detail, value = f"incomplete: {exc}", ""
        else:
            detail = "fewer than 2 complete seeds"
        rows.append({
            "row_type": "centred_residual_variance", "name": f"{member}_{name}",
            "mode": "", "profile": "", "arm": "", "seed": "",
            "detail": detail, "value": value})
    # Metric degeneracy flags: zero across-seed variance of auc_goal per cell
    # family (a flag only; no means are emitted).
    for mode, seeds_m in seeds_by_mode.items():
        for profile in PROFILES:
            for arm in ARMS:
                values = [v for v in (index.auc_goal(mode, s, profile, arm=arm,
                                                     required=False)
                                      for s in seeds_m) if v is not None]
                if len(values) >= 2:
                    rows.append({
                        "row_type": "degeneracy_flag", "name": "",
                        "mode": mode, "profile": profile, "arm": arm,
                        "seed": "", "detail": "zero_variance_auc_goal",
                        "value": int(centred_residual_variance(values) == 0.0)})
    return rows


# ---------------------------------------------------------------------------
# Canonical output (matches the existing builders' conventions:
# format(x, ".12g"), "-0" -> "0", "\n" line endings)
# ---------------------------------------------------------------------------

def _canonical(value) -> str:
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, float):
        rendered = format(value, ".12g")
        return "0" if rendered == "-0" else rendered
    if value is None:
        return ""
    return str(value)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames,
                                lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _canonical(row.get(key, ""))
                             for key in fieldnames})


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _family_seed_set(index: ArchiveIndex, strict: bool = True) -> list[int]:
    seed_sets = {mode: index.mode_seeds(mode) for mode in FAMILY_MODES}
    reference = seed_sets[MODE_BASELINE]
    if strict:
        for mode, seeds in seed_sets.items():
            if seeds != reference:
                raise SystemExit(
                    f"seed sets differ across family modes: {mode} has "
                    f"{seeds}, {MODE_BASELINE} has {reference}")
        if len(reference) < 2:
            raise SystemExit(
                f"need at least 2 seeds; found {reference} under "
                f"{MODE_BASELINE}")
        redundancy = index.mode_seeds(MODE_REDUNDANCY)
        if redundancy and redundancy != reference:
            raise SystemExit(
                f"{MODE_REDUNDANCY} seed set {redundancy} differs from "
                f"family seed set {reference}")
        return reference
    common = None
    for seeds in seed_sets.values():
        common = set(seeds) if common is None else common & set(seeds)
    return sorted(common or [])


def run(roots: list[Path], out_dir: Path, rmst_horizon: int | None = None,
        bootstrap_iters: int = BOOTSTRAP_ITERS,
        pilot_diagnostics: bool = False,
        legacy_archive_format: bool = False) -> None:
    index = ArchiveIndex(roots)
    out_dir.mkdir(parents=True, exist_ok=True)

    if pilot_diagnostics:
        # Pilot-blinding contract: ONLY the allow-listed diagnostics are
        # written. The family CSV, arm-labelled means, effect directions and
        # p-values are refused outright.
        rows = build_pilot_rows(index, rmst_horizon)
        _write_csv(out_dir / "phase1b_pilot_diagnostics.csv", PILOT_FIELDS, rows)
        print("pilot-diagnostics mode: wrote phase1b_pilot_diagnostics.csv; "
              "REFUSED to write phase1b_registered_family.csv, "
              "phase1b_supporting.csv, arm-labelled means, effect directions, "
              "or p-values (registration pilot-blinding contract)")
        return

    seeds = _family_seed_set(index, strict=True)
    family_rows = build_family_rows(index, seeds, rmst_horizon, bootstrap_iters)
    if legacy_archive_format:
        # The run-of-record family CSV was committed with M1-M4's registered
        # directions accidentally blank. Preserve that historical byte stream
        # only for archive verification; normal output is corrected above.
        for row in family_rows:
            if row["member"] in {"M1", "M2", "M3", "M4"}:
                row["predicted_direction"] = ""
    supporting_rows = _redundancy_contrast_rows(index, seeds, rmst_horizon,
                                                bootstrap_iters)
    supporting_rows.extend(_descriptive_rows(
        index, seeds, rmst_horizon,
        legacy_archive_format=legacy_archive_format))
    _write_csv(out_dir / "phase1b_registered_family.csv", FAMILY_FIELDS,
               family_rows)
    _write_csv(out_dir / "phase1b_supporting.csv", SUPPORTING_FIELDS,
               supporting_rows)
    print(f"Wrote {len(family_rows)} family rows "
          f"(BH m={len(FAMILY) - len(EXPLORATORY_MEMBERS)}, "
          f"{len(EXPLORATORY_MEMBERS)} exploratory) and "
          f"{len(supporting_rows)} supporting rows to {out_dir}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--rmst-horizon", type=int, default=None,
                        help="frozen RMST censoring horizon H; default = "
                             "3000 // scenario_count")
    parser.add_argument("--bootstrap-iters", type=int, default=BOOTSTRAP_ITERS)
    parser.add_argument("--pilot-diagnostics", action="store_true",
                        help="emit only the allow-listed pilot diagnostics; "
                             "refuse the family CSV and any effect/p output")
    parser.add_argument(
        "--legacy-archive-format", action="store_true",
        help="recreate the immutable 2026-07-27 CSV serialization, including "
             "its blank M1-M4 direction fields and superseded overshoot proxy; "
             "used only by reproduce_phase1b.py")
    args = parser.parse_args(argv)
    run(args.roots, args.out, rmst_horizon=args.rmst_horizon,
        bootstrap_iters=args.bootstrap_iters,
        pilot_diagnostics=args.pilot_diagnostics,
        legacy_archive_format=args.legacy_archive_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
