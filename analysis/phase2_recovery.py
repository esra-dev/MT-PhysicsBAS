"""Aggregate Phase-2 fault-recovery artefacts into a CI table + paired tests.

Phase 2 (fault detection / blacklist / re-learn) writes, per faulty profile x
adapt-mode cell, a one-row-per-run CSV:

    recovery_stereotypes_<true|false><qtable_suffix>.csv
        DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes,
        SecondaryDetectEpisode,RecoveredGoalRate

where <true> == ql_true (KG-primed) and <false> == ql_false (tabula-rasa).
RecoveryEpisodes = ReconvergeEpisode - DetectEpisode (lower == faster
re-alignment after the fault); -1 means "did not re-converge within the budget"
or a degenerate single-actuator lab (e.g. lab1_f1dead) where the last actuator
is protected from blacklisting. RecoveredGoalRate (Phase 2.2) is the fraction of
greedy (epsilon=0) evaluation episodes the FINAL policy reaches the goal in: it
separates a policy that merely STOPPED CHANGING (stable) from one that actually
REACHES the goal (goal-reaching).

The headline Phase-2 claim is:  recovery(ql_true) < recovery(ql_false)
-- the KG prior lets the agent re-align over the surviving components faster
than a learner that must rediscover structure from scratch. The recovery-SPEED
contrast is only WELL-POSED where a deterministic post-fault survivor path
exists (see _WELL_POSED_RECOVERY); ill-posed cells (lone actuator / sun-gated
survivor) are reported descriptively and excluded from the recovery BH family,
but remain in the DETECTION family.

This script:
  * discovers recovery CSVs for every configured faulty profile (root + any
    archived seed subdirectories under --root),
  * treats each per-seed CSV as ONE independent replica keyed by the seed
    token in its path (pre_registration.md §9.7: pairing is by seed key,
    never by list position),
  * reports per (profile, arm) mean + bootstrap 95% CI for RecoveryEpisodes and
    DetectEpisode, plus detection/reconvergence rates,
  * runs a paired bootstrap (ql_true - ql_false) per profile, pairing
    ql_true/ql_false by seed and emitting a seeds_paired column, with
    Benjamini-Hochberg q-values over the FROZEN §9.5/§9.6 families (reusing
    sweep_report.py's pre-registered helpers / RNG seed 0xC1).

BH families are frozen by enumeration in pre_registration.md §9 (recovery
m=8 Tier-1 cells, detection m=8 non-degenerate cells; DetectEpisode==0
degenerate cells are excluded from the detection family). q-values are only
computed when EVERY registered family member is present -- a partial (single
CI run) invocation emits q=nan and carries no confirmatory claim (§9.8).

Outputs (under analysis/out/):
    phase2_recovery_ci.csv      -- one row per (profile, arm)
    phase2_recovery_paired.csv  -- one row per (profile, metric) paired diff

Usage:
    python analysis/phase2_recovery.py                    # single-run (CI) mode
    python analysis/phase2_recovery.py --root . --out analysis/out
    python analysis/phase2_recovery.py --registered \
        --out analysis/out_phase2_registered              # pooled §9 analysis
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

# Cells where a DETERMINISTIC post-fault survivor path exists, so "does KG
# recover faster?" is a WELL-POSED question: a fixed greedy policy can actually
# reach the goal after the fault (lab3 keeps the shared Spotlight +150 to both
# zones plus the cross-zone lamp bleed, reaching rank-3 without relying on the
# stochastic sun). Only these enter the RecoveryEpisodes BH family. Everywhere
# else the lone actuator is protected (lab1_f1dead) or the only survivor is the
# sun-gated blind (lab2_*, lab3_f2*), so a *stable* greedy policy need not be
# *goal-reaching* and a recovery-SPEED comparison is ill-posed (it previously
# produced misleading significant "KG slower" rows). Ill-posed cells are still
# reported descriptively and stay in the DETECTION family.
#
# Phase 2 extension — additional well-posed cells:
#   • lab3_f1dead_z2 / lab3_f1inv_z2 — symmetric Z2-lamp faults; the target zone
#     is still reachable deterministically via the shared Spotlight + surviving
#     lamp cross-zone spill (same argument as lab3_f1dead/f1inv).
#   • lab3_f1bdead / lab3_f1binv / lab2_f1bdead / lab2_f1binv — BLIND (Mediates)
#     faults. After the blind is blacklisted the TASK LAMP survives as a
#     deterministic rank-3 lever (lab2: +400; lab3: +400 own + spotlight/spill),
#     so the recovered greedy policy is genuinely goal-reaching (sun-independent)
#     and a recovery-SPEED contrast is well-posed. (Note lab2 LAMP faults stay
#     ill-posed because there the only survivor is the sun-gated blind; a lab2
#     BLIND fault is the reverse — the lamp survives — hence well-posed.)
_WELL_POSED_RECOVERY = (
    "lab3_f1dead", "lab3_f1inv",
    "lab3_f1dead_z2", "lab3_f1inv_z2",
    "lab3_f1bdead", "lab3_f1binv",
    "lab2_f1bdead", "lab2_f1binv",
    # Phase 2.5b — monitor emergency-fallback lab. The primary lamp is the ONLY
    # rank-3 lever, so once it is blacklisted the nominal goal (rank 3) is
    # UNREACHABLE. The adapt agent proves this with a deterministic reachability
    # probe, lowers the EFFECTIVE goal to the closest achievable rank (rank 2 via
    # the monitor, 25+260=285 lux, sun-independent) and notifies the user. The
    # recovery-SPEED contrast is well-posed against that effective best-effort
    # goal: RecoveredGoalRate here measures best-effort (rank-2) attainment.
    "labmon_f1dead",
    # Phase 2.5b — lab3 MULTI-SURVIVOR degraded cell. BOTH task lamps are dead and
    # the sun is pinned to rank 1 (100 lux), so the nominal rank-3 goal is
    # UNREACHABLE in BOTH zones on every episode (per-zone ceiling 25 + spotlight
    # 150 + blinds 50+40 = 265 = rank 2). After the two lamps are blacklisted the
    # survivors are Z1Blinds, Z2Blinds and the Spotlight (3 actuators), so the
    # reachability probe has 8 combos and BOTH zones degrade to rank 2. Unlike
    # labmon (single survivor), here the Spotlight — REDUNDANT in the clean lab —
    # becomes the essential best-effort lever, giving the KG's structural prior a
    # multi-actuator triage where a recovery-SPEED contrast can actually show up.
    "lab3_f2dead_lowsun",
    # Phase 2.5 — labmon2 DUAL-ZONE MULTI-SURVIVOR monitor fallback (NO spotlight).
    # BOTH primary lamps are dead and the sun is pinned to rank 1 (100 lux), so the
    # nominal rank-3 goal is UNREACHABLE in BOTH zones on every episode (per-zone
    # ceiling 25 + monitor 200 + blind 50 = 275 = rank 2). After the two lamps are
    # blacklisted the survivors are Z1Monitor, Z2Monitor, Z1Blinds, Z2Blinds (4
    # actuators → 16 probe combos), and BOTH zones degrade to rank 2. The MONITOR
    # (Causes light, rank 2 alone) is the essential best-effort lever in each zone,
    # giving the KG's structural prior a multi-actuator triage without a spotlight.
    "labmon2_f2dead_lowsun",
)

# Minimum greedy goal-rate (RecoveredGoalRate) for a re-converged policy to
# count as goal-reaching rather than merely stable.
_GOAL_REACHING_THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Frozen registration (pre_registration.md §9). The BH families below are
# frozen BY ENUMERATION: m never changes with the data, and a cell whose
# realized tier flips is kept in the family and reported as a deviation
# (§9.5/§9.6). Do not edit without a registered amendment.
# ---------------------------------------------------------------------------

# §9.5 — the ONE pooled Tier-1 RecoveryEpisodes family (m = 8).
_REGISTERED_TIER1_FAMILY = (
    "lab3_f1dead", "lab3_f1dead_z2", "lab3_f1bdead", "lab3_f1binv",
    "lab2_f1bdead", "labmon_f1dead", "lab3_f2dead_lowsun",
    "labmon2_f2dead_lowsun",
)

# §9.6 — the DetectEpisode family (m = 8): cells whose DetectEpisode is NOT
# identically 0 in both arms. Degenerate instant-detection cells (DetectEpisode
# == 0 for every replica in both arms) are a constant, not evidence of parity,
# and are excluded (reported descriptively only).
_REGISTERED_DETECTION_FAMILY = (
    "lab3_f1dead", "lab3_f1inv", "lab3_f1dead_z2", "lab3_f1inv_z2",
    "lab3_f1bdead", "lab3_f1binv", "lab2_f1bdead", "lab2_f1binv",
)

_METRIC_FAMILY = {
    "RecoveryEpisodes": _REGISTERED_TIER1_FAMILY,
    "DetectEpisode": _REGISTERED_DETECTION_FAMILY,
}

# §9.7 — run of record per cell: the latest green CI run of the final
# instrument (instant blacklist + policy-stability window 50 + RecoveredGoalRate
# certification). Paths are relative to --root (repo root). Used by
# --registered; earlier iterations (v1-v5) and superseded cells are history.
#
# REGISTERED AMENDMENT (2026-07-12, action-space inversion): the WoT-contract
# action-space inversion (commits 6fffd41..6c727b6, docs/ACTION_SPACE_INVERSION.md)
# changed the instrument for BOTH arms, so every cell was re-run post-inversion
# on commit 6c727b6 and the table below was re-pointed wholesale. Families
# (§9.5/§9.6) are UNCHANGED. The full pre-inversion table is preserved verbatim
# as _RUN_OF_RECORD_PRE_INVERSION for audit. Post-inversion runs of record:
#   29148475671 (Run 1A, 8 profiles, seeds 1-10)
#   29151540231 (Run 1B, 7 profiles, seeds 1-10)
#   29155539633 (Run 2, labmon/lowsun confirmatory, seeds 1-10)
#   29157197853 (Run 3, Phase-2.6 KG-silent variants, seeds 1-10; descriptive
#                only -- not members of any frozen family)
#   29163456132 (Run 1C, lab3_f1dead one-shot replication, fresh seeds 11-20;
#                run of record for lab3_f1dead per the §9.9 protocol, with the
#                Run-1A seeds-1-10 measurement reported alongside)
# Local layout: phase2_postinv/run_<id>/recovery_root, recovered from each
# run's phase2-consolidated artifact (the 'results' branch copies were
# clobbered by a Phase-4 -OverwriteResultsBranch publish on 2026-07-12).
_RUN_OF_RECORD = {
    # 29148475671 (Run 1A, commit 6c727b6)
    "lab1_f1dead": "phase2_postinv/run_29148475671/recovery_root",
    "lab2_f1dead": "phase2_postinv/run_29148475671/recovery_root",
    "lab2_f1inv": "phase2_postinv/run_29148475671/recovery_root",
    "lab2_f2dead": "phase2_postinv/run_29148475671/recovery_root",
    "lab2_f2inv": "phase2_postinv/run_29148475671/recovery_root",
    "lab3_f1inv": "phase2_postinv/run_29148475671/recovery_root",
    "lab3_f2dead": "phase2_postinv/run_29148475671/recovery_root",
    # 29163456132 (Run 1C, §9.9 one-shot replication, seeds 11-20)
    "lab3_f1dead": "phase2_postinv/run_29163456132/recovery_root",
    # 29151540231 (Run 1B, commit 6c727b6)
    "lab3_f2inv": "phase2_postinv/run_29151540231/recovery_root",
    "lab3_f1dead_z2": "phase2_postinv/run_29151540231/recovery_root",
    "lab3_f1inv_z2": "phase2_postinv/run_29151540231/recovery_root",
    "lab3_f1bdead": "phase2_postinv/run_29151540231/recovery_root",
    "lab3_f1binv": "phase2_postinv/run_29151540231/recovery_root",
    "lab2_f1bdead": "phase2_postinv/run_29151540231/recovery_root",
    "lab2_f1binv": "phase2_postinv/run_29151540231/recovery_root",
    # 29155539633 (Run 2, commit 6c727b6)
    "labmon_f1dead": "phase2_postinv/run_29155539633/recovery_root",
    "lab3_f2dead_lowsun": "phase2_postinv/run_29155539633/recovery_root",
    "labmon2_f2dead_lowsun": "phase2_postinv/run_29155539633/recovery_root",
    # 29157197853 (Run 3, Phase-2.6 KG-silent variants; descriptive only)
    "labmon_infoonly_f1dead": "phase2_postinv/run_29157197853/recovery_root",
    "labmon_nostereo_f1dead": "phase2_postinv/run_29157197853/recovery_root",
    "labmon2_infoonly_f2dead_lowsun": "phase2_postinv/run_29157197853/recovery_root",
    "labmon2_nostereo_f2dead_lowsun": "phase2_postinv/run_29157197853/recovery_root",
}

# Pre-inversion table (runs of record up to and including §9.9), preserved
# verbatim for audit. Superseded 2026-07-12 by the amendment above.
_RUN_OF_RECORD_PRE_INVERSION = {
    # 28590019536 (Phase 2.3, commit b2adca1)
    "lab1_f1dead": "phase2_results_v6/recovery_root",
    "lab2_f1dead": "phase2_results_v6/recovery_root",
    "lab2_f1inv": "phase2_results_v6/recovery_root",
    "lab2_f2dead": "phase2_results_v6/recovery_root",
    "lab2_f2inv": "phase2_results_v6/recovery_root",
    "lab3_f2dead": "phase2_results_v6/recovery_root",
    "lab3_f2inv": "phase2_results_v6/recovery_root",
    # 28913465680 (§9.9 registered one-shot replication, seeds 11-20, commit
    # b9bf4cb; replaces 28745352239 as lab3_f1dead's run of record -- the ext
    # measurement (delta=-67.4, q=0.053) stays reported alongside per §9.9)
    "lab3_f1dead": "phase2_lab3f1dead_replication/run_28913465680/recovery_root",
    # 28745352239 (Phase 2.4, commit 282acc4; supersedes v6's lab3_f1inv
    # -- the probe-augmented monitoring regime changed the instrument)
    "lab3_f1inv": "phase2_ext_results/recovery_root",
    "lab3_f1dead_z2": "phase2_ext_results/recovery_root",
    "lab3_f1inv_z2": "phase2_ext_results/recovery_root",
    "lab3_f1bdead": "phase2_ext_results/recovery_root",
    "lab3_f1binv": "phase2_ext_results/recovery_root",
    "lab2_f1bdead": "phase2_ext_results/recovery_root",
    # 28750100413 (PHASE1_TO_PHASE2_CHANGES.md §21.9 run of record)
    "lab2_f1binv": "phase2_binv_backfill/phase2-consolidated/recovery_root",
    # 28863439179 (Phase 2.5 labmon)
    "labmon_f1dead": "labmon_ci_results/phase2-consolidated/recovery_root",
    # 28866807391 / 28884717500 (Phase 2.5b lowsun)
    "lab3_f2dead_lowsun": "phase2_lowsun_results/run_28866807391/recovery_root",
    "labmon2_f2dead_lowsun": "phase2_lowsun_results/run_28884717500/recovery_root",
}

# Seed token from a path component (§9.7). Same idea as
# phase4_energy.py::_seed_token, widened to the layouts Phase-2 artefacts use:
# seed3, results_seed3, adapt-<profile>-<mode>-seed-3.
_SEED_RE = re.compile(r"seed[._-]?(\d+)$", re.IGNORECASE)


def _seed_token(path: Path) -> str:
    for part in path.parts:
        m = _SEED_RE.search(part)
        if m:
            return f"seed{m.group(1)}"
    return "root"


def _seed_sort_key(tok: str):
    m = re.fullmatch(r"seed(\d+)", tok)
    return (0, int(m.group(1))) if m else (1, tok)


# ---------------------------------------------------------------------------
# Two-tier recovery reporting (Phase 2.4).
#
# _WELL_POSED_RECOVERY gates whether a recovery-SPEED contrast is *defined* (a
# deterministic post-fault survivor path exists). Within that set we further
# stratify by whether the recovered policy is actually GOAL-REACHING, because a
# well-posed cell can still be futile in practice. Concretely, lab3 physics is
#   z1 = 25 + (z1l?400) + (z2l?150) + (z1b?0.5*sun) + (z2b?0.4*sun) + (sp?150)
# so after a DEAD Z1 lamp is blacklisted, {Z2Light,Spotlight} still gives
# z1 = 25+150+150 = 325 > 300 = rank 3 (sun-independent) -> both arms reach goal
# (~0.9-1.0). An INVERTED Z1 lamp has the SAME survivor path on paper, but its
# -400 contribution keeps dragging the zone in the states the re-learner
# revisits, so NEITHER arm reliably reaches the goal (~0.3). A BLIND fault
# leaves the deterministic +400 task lamp, so both arms reach goal.
#
# Tier-1 (CONFIRMATORY): well-posed AND goal-reaching in BOTH arms
#   (per-arm goal_reaching_rate >= _GOAL_REACHING_THRESHOLD). "Recovered" here
#   means "re-reaches the target", so a recovery-SPEED comparison is meaningful.
#   The RecoveryEpisodes BH-FDR family is restricted to these cells.
# Tier-2 (DESCRIPTIVE): well-posed but NOT reliably goal-reaching in both arms
#   (the inverted-lamp cells; partially-posed lab2_f1binv). Reported with full
#   statistics but EXCLUDED from the recovery BH family -- their number is
#   time-to-stable-but-futile-policy, not time-to-recovery.
#
# The stratifier is task ACHIEVABILITY, a property of the ENVIRONMENT: it agrees
# across both arms (ql_true and ql_false classify identically), so conditioning
# on it does NOT bias the KG-vs-vanilla contrast (it is not a treatment
# selector). Cells outside _WELL_POSED_RECOVERY are 'ill_posed'.
def classify_recovery_tier(profile: str, per_cell: dict) -> str:
    """'confirmatory' | 'descriptive' | 'ill_posed' for a profile."""
    if profile not in _WELL_POSED_RECOVERY:
        return "ill_posed"
    t = per_cell.get((profile, "ql_true"))
    f = per_cell.get((profile, "ql_false"))
    grt = t["goal_reaching_rate"] if t else float("nan")
    grf = f["goal_reaching_rate"] if f else float("nan")
    both_goal = (grt == grt and grf == grf
                 and grt >= _GOAL_REACHING_THRESHOLD
                 and grf >= _GOAL_REACHING_THRESHOLD)
    return "confirmatory" if both_goal else "descriptive"


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


def find_recovery_rows(root: Path, bool_str: str, suffix: str) -> list[tuple[str, dict]]:
    """(seed_token, row) replicas from recovery_stereotypes_<bool><suffix>.csv.

    Searches the root directory and (recursively) any archived seed
    subdirectories. One replica per (run, seed) -- pre_registration.md §9.7:
    the seed token comes from the artefact path, duplicate copies of the same
    seed under one root (e.g. a consolidated recovery_root/ next to raw
    adapt-*-seed-N artefact dirs) are dropped with a warning, and a multi-row
    CSV keeps only its first row.
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

    out: list[tuple[str, dict]] = []
    seen: set[str] = set()
    for p in paths:
        tok = _seed_token(p.relative_to(root) if p.is_relative_to(root) else p)
        if tok in seen:
            print(f"  [!!] duplicate replica {tok} for {fname} at {p}; "
                  f"keeping first occurrence", file=sys.stderr)
            continue
        try:
            with p.open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        except Exception as exc:  # noqa: BLE001 - best-effort aggregation
            print(f"  [!!] could not read {p}: {exc}", file=sys.stderr)
            continue
        if not rows:
            continue
        if len(rows) > 1:
            print(f"  [!!] {p} has {len(rows)} rows; keeping the first "
                  f"(one replica per (run, seed), §9.7)", file=sys.stderr)
        seen.add(tok)
        out.append((tok, rows[0]))
    return out


def _as_int(row: dict, key: str):
    raw = row.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(float(str(raw).strip()))
    except ValueError:
        return None


def _as_float(row: dict, key: str):
    raw = row.get(key)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(str(raw).strip())
    except ValueError:
        return None


def collect_arm(replicas: list[tuple[str, dict]]) -> dict:
    """Reduce (seed, row) replicas into per-arm metric lists, maps + rates."""
    rows = [r for _, r in replicas]
    # Per-seed success-filtered metric maps -- the §9.7 pairing structures.
    detect_by_seed: dict[str, float] = {}
    recovery_by_seed: dict[str, float] = {}
    for seed, r in replicas:
        d = _as_int(r, "DetectEpisode")
        v = _as_int(r, "RecoveryEpisodes")
        if d is not None and d >= 0:
            detect_by_seed[seed] = float(d)
        if v is not None and v >= 0:
            recovery_by_seed[seed] = float(v)

    detect_all = [_as_int(r, "DetectEpisode") for r in rows]
    recov_all = [_as_int(r, "ReconvergeEpisode") for r in rows]
    recovery_all = [_as_int(r, "RecoveryEpisodes") for r in rows]
    goalrate_all = [_as_float(r, "RecoveredGoalRate") for r in rows]
    # Phase 2.5b — graceful-degradation columns (absent on older CSVs -> None).
    degraded_all = [_as_int(r, "DegradedMode") for r in rows]
    best_effort_all = [_as_int(r, "BestEffortRank") for r in rows]
    nominal_all = [_as_int(r, "NominalGoal") for r in rows]
    defects = sorted({(r.get("DefectComponent") or "").strip()
                      for r in rows if (r.get("DefectComponent") or "").strip()})

    n_runs = len(rows)
    # Detection succeeded when DetectEpisode >= 0.
    detected = [d for d in detect_all if d is not None and d >= 0]
    # Re-convergence succeeded when RecoveryEpisodes >= 0 (>=0 implies both
    # detect and reconverge episodes were recorded).
    reconverged = [v for v in recovery_all if v is not None and v >= 0]
    # Phase 2.2 greedy goal-rate of the FINAL policy (>=0; -1 == not measured).
    goal_rates = [g for g in goalrate_all if g is not None and g >= 0.0]
    # Goal-reaching recovery == re-converged AND final greedy policy reaches the
    # goal at >= threshold (separates "stable" from "stable AND goal-reaching").
    goal_reaching = [
        v for v, g in zip(recovery_all, goalrate_all)
        if v is not None and v >= 0
        and g is not None and g >= _GOAL_REACHING_THRESHOLD
    ]

    # Phase 2.5b — best-effort degradation summary. A cell is "degraded" when the
    # adapt agent proved the nominal goal unreachable and lowered the effective
    # goal. best_effort_rank / nominal_goal report the (modal) ranks involved.
    degraded_flags = [d for d in degraded_all if d is not None]
    n_degraded = sum(1 for d in degraded_flags if d == 1)
    best_efforts = [b for b, d in zip(best_effort_all, degraded_all)
                    if d == 1 and b is not None]
    nominals = [n for n in nominal_all if n is not None]
    _mode = lambda xs: max(set(xs), key=xs.count) if xs else None

    return {
        "n_runs": n_runs,
        "defects": defects,
        # Per-metric value lists used for CIs (success-only).
        "DetectEpisode": detected,
        "RecoveryEpisodes": reconverged,
        # Per-seed success-only maps used for PAIRING (§9.7 seed-keyed).
        "DetectEpisode_by_seed": detect_by_seed,
        "RecoveryEpisodes_by_seed": recovery_by_seed,
        "n_detected": len(detected),
        "n_reconverged": len(reconverged),
        "detection_rate": (len(detected) / n_runs) if n_runs else float("nan"),
        "reconverge_rate": (len(reconverged) / n_runs) if n_runs else float("nan"),
        "_reconverge_episodes": [v for v in recov_all if v is not None and v >= 0],
        # Phase 2.2 goal-rate certification.
        "RecoveredGoalRate": goal_rates,
        "goal_rate_mean": (sum(goal_rates) / len(goal_rates)) if goal_rates else float("nan"),
        "n_goal_reaching": len(goal_reaching),
        "goal_reaching_rate": (len(goal_reaching) / n_runs) if n_runs else float("nan"),
        # Phase 2.5b best-effort degradation summary.
        "n_degraded": n_degraded,
        "degraded_rate": (n_degraded / n_runs) if n_runs else float("nan"),
        "best_effort_rank": _mode(best_efforts),
        "nominal_goal": _mode(nominals),
    }


def write_ci_table(per_cell: dict, out_dir: Path, iters: int) -> int:
    """phase2_recovery_ci.csv: one row per (profile, arm)."""
    rows = []
    for (profile, mode), arm in sorted(per_cell.items()):
        row = {
            "profile": profile,
            "mode": mode,
            "n_runs": arm["n_runs"],
            "source_run": arm.get("source", ""),
            "defect_component": ";".join(arm["defects"]) if arm["defects"] else "",
            "well_posed_recovery": profile in _WELL_POSED_RECOVERY,
            "recovery_tier": classify_recovery_tier(profile, per_cell),
            "detection_rate": round(arm["detection_rate"], 4)
                if arm["detection_rate"] == arm["detection_rate"] else "",
            "reconverge_rate": round(arm["reconverge_rate"], 4)
                if arm["reconverge_rate"] == arm["reconverge_rate"] else "",
            "n_detected": arm["n_detected"],
            "n_reconverged": arm["n_reconverged"],
            "greedy_goal_rate_mean": round(arm["goal_rate_mean"], 4)
                if arm["goal_rate_mean"] == arm["goal_rate_mean"] else "",
            "n_goal_reaching": arm["n_goal_reaching"],
            "goal_reaching_rate": round(arm["goal_reaching_rate"], 4)
                if arm["goal_reaching_rate"] == arm["goal_reaching_rate"] else "",
            # Phase 2.5b — best-effort degradation (blank when no cell degraded).
            "degraded_rate": round(arm["degraded_rate"], 4)
                if arm["degraded_rate"] == arm["degraded_rate"] else "",
            "n_degraded": arm["n_degraded"],
            "best_effort_rank": arm["best_effort_rank"]
                if arm["best_effort_rank"] is not None else "",
            "nominal_goal": arm["nominal_goal"]
                if arm["nominal_goal"] is not None else "",
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
                       out_dir: Path, iters: int,
                       registered: bool = False) -> int:
    """phase2_recovery_paired.csv: ql_true vs ql_false per profile x metric.

    Pairs replicas BY SEED KEY (pre_registration.md §9.7): seed s of ql_true
    vs seed s of ql_false, over the seeds valid in both arms; the seeds used
    are emitted in seeds_paired. mean_diff < 0 means ql_true is FASTER (fewer
    episodes) -- the headline direction. Rows are EMITTED for every well-posed
    recovery cell and every detection cell, but Benjamini-Hochberg q-values
    are computed ONLY over the frozen §9.5/§9.6 enumerated families (recovery
    m=8 Tier-1 cells; detection m=8 non-degenerate cells), and ONLY when every
    family member is present -- a partial invocation (single CI run) emits
    q=nan and carries no confirmatory claim (§9.8). Tier-2 DESCRIPTIVE and
    ill-posed/degenerate cells carry no q-value. The per-row recovery_tier
    column records the realized classification; a registered cell whose
    realized tier deviates stays in the family (m frozen) and is flagged.
    """
    rows: list[dict] = []
    # metric -> list of (row_idx, p_value, profile) for registered family rows
    metric_pidx: dict = {}

    for metric in _METRICS:
        metric_pidx.setdefault(metric, [])
        for profile in profiles:
            # Recovery-SPEED is only DEFINED on well-posed cells (a deterministic
            # post-fault survivor exists); detection rows are emitted everywhere.
            if metric == "RecoveryEpisodes" and profile not in _WELL_POSED_RECOVERY:
                continue
            ta = per_cell.get((profile, "ql_true"))
            fa = per_cell.get((profile, "ql_false"))
            if not ta or not fa:
                continue
            tmap = ta[f"{metric}_by_seed"]
            fmap = fa[f"{metric}_by_seed"]
            seeds_common = sorted(set(tmap) & set(fmap), key=_seed_sort_key)
            n_pair = len(seeds_common)
            if n_pair == 0:
                continue
            a = [tmap[s] for s in seeds_common]
            b = [fmap[s] for s in seeds_common]
            raw_diff = (sum(a) / len(a)) - (sum(b) / len(b))
            if n_pair >= 2:
                mean_d, lo, hi, p_boot, p_pos, p_neg = _paired_bootstrap_diff(
                    a, b, iters=iters)
                p_wil = _wilcoxon_p(a, b)
                delta = _cliffs_delta(a, b)
            else:
                mean_d, lo, hi = raw_diff, float("nan"), float("nan")
                p_boot = p_pos = p_neg = p_wil = delta = float("nan")
            tier = (classify_recovery_tier(profile, per_cell)
                    if metric == "RecoveryEpisodes" else "")
            in_family = profile in _METRIC_FAMILY[metric]
            if metric == "RecoveryEpisodes" and in_family and tier != "confirmatory":
                print(f"  [!!] REGISTERED DEVIATION: {profile} realized tier "
                      f"'{tier}' != confirmatory; cell stays in the frozen "
                      f"family (m unchanged, §9.5)", file=sys.stderr)
            if metric == "RecoveryEpisodes" and not in_family and tier == "confirmatory":
                print(f"  [!!] {profile} classifies confirmatory but is NOT in "
                      f"the frozen §9.5 family; no q-value emitted",
                      file=sys.stderr)
            row_idx = len(rows)
            rows.append({
                "profile": profile,
                "metric": metric,
                "recovery_tier": tier,
                "in_registered_family": in_family,
                "n_paired": n_pair,
                "seeds_paired": ";".join(seeds_common),
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
            if in_family:
                metric_pidx[metric].append((row_idx, p_boot, profile))

    # BH over the frozen families -- only in --registered mode (the §9.7
    # run-of-record analysis set) and only when the full family is present.
    for metric, pidx in metric_pidx.items():
        if not registered:
            print(f"  [--] {metric}: q_bootstrap_bh only computed by the "
                  f"pooled --registered invocation over the §9.7 analysis "
                  f"set; this run carries no confirmatory claim "
                  f"(pre_registration.md §9.8)", file=sys.stderr)
            continue
        family = _METRIC_FAMILY[metric]
        present = {prof for _, _, prof in pidx}
        missing = [prof for prof in family if prof not in present]
        if missing:
            print(f"  [--] {metric}: registered family incomplete "
                  f"(missing {', '.join(missing)}); q_bootstrap_bh not "
                  f"computed -- no confirmatory claim from this invocation "
                  f"(pre_registration.md §9.8)", file=sys.stderr)
            continue
        qs = _bh_qvalues([p for _, p, _ in pidx])
        for (i, _, _), q in zip(pidx, qs):
            rows[i]["q_bootstrap_bh"] = q
            rows[i]["bh_family_m"] = len(pidx)
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
    print("\n=== Phase 2 recovery summary (lower = faster; goal% = greedy goal-rate) ===")
    header = (f"{'profile':<23}{'arm':<10}{'n':>3}  {'det%':>5} {'recv%':>6} "
              f"{'goal%':>6}  {'detectEp':>9} {'recovEp':>9}  tier")
    print(header)
    print("-" * len(header))
    _TIER_ABBR = {"confirmatory": "conf", "descriptive": "desc", "ill_posed": "ill"}
    for profile in profiles:
        tier = _TIER_ABBR.get(classify_recovery_tier(profile, per_cell), "?")
        for mode, _bool in _ARMS:
            arm = per_cell.get((profile, mode))
            if not arm:
                continue
            det_mean, _, _ = _bootstrap_ci([float(v) for v in arm["DetectEpisode"]])
            rec_mean, _, _ = _bootstrap_ci([float(v) for v in arm["RecoveryEpisodes"]])
            det_pct = arm["detection_rate"] * 100 if arm["detection_rate"] == arm["detection_rate"] else float("nan")
            rec_pct = arm["reconverge_rate"] * 100 if arm["reconverge_rate"] == arm["reconverge_rate"] else float("nan")
            goal_pct = arm["goal_rate_mean"] * 100 if arm["goal_rate_mean"] == arm["goal_rate_mean"] else float("nan")
            print(f"{profile:<23}{mode:<10}{arm['n_runs']:>3}  "
                  f"{_fmt(det_pct):>5} {_fmt(rec_pct):>6} {_fmt(goal_pct):>6}  "
                  f"{_fmt(det_mean):>9} {_fmt(rec_mean):>9}  {tier}")
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
    parser.add_argument("--registered", action="store_true",
                        help="pooled pre_registration.md §9 analysis: read each "
                             "profile from its §9.7 run-of-record folder "
                             "(relative to --root) instead of one shared root")
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
        if args.registered:
            rel = _RUN_OF_RECORD.get(profile)
            if rel is None:
                print(f"  [!!] {profile}: no §9.7 run of record; skipping",
                      file=sys.stderr)
                continue
            profile_root = root / rel
            if not profile_root.is_dir():
                print(f"  [!!] {profile}: run-of-record folder missing "
                      f"({profile_root}); skipping", file=sys.stderr)
                continue
        else:
            profile_root = root
        for mode, bool_str in _ARMS:
            replicas = find_recovery_rows(profile_root, bool_str, suffix)
            if replicas:
                found_any = True
            arm = collect_arm(replicas)
            arm["source"] = (rel if args.registered else "")
            per_cell[(profile, mode)] = arm

    if not found_any:
        print(f"No recovery_stereotypes_*.csv found under {root}.\n"
              f"Run the Phase-2 orchestrator first:  .\\run_phase2_adapt.ps1",
              file=sys.stderr)
        return 1

    n_ci = write_ci_table(per_cell, out_dir, args.iters)
    n_paired = write_paired_table(per_cell, profiles, out_dir, args.iters,
                                  registered=args.registered)
    print_summary(per_cell, profiles)
    print(f"Wrote {n_ci} rows -> {out_dir / 'phase2_recovery_ci.csv'}")
    print(f"Wrote {n_paired} rows -> {out_dir / 'phase2_recovery_paired.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
