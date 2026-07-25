"""Tests for analysis/phase1b_report.py (Phase-1b registered m=6 family).

Synthetic archive trees are fabricated under tmp_path with the minimal CSV
files the readers need (header-by-name, tolerant readers). Uses stdlib +
numpy + pytest only.
"""

import csv

import numpy as np
import pytest

from analysis import phase1b_report as pr


# ---------------------------------------------------------------------------
# Synthetic archive tree helpers
# ---------------------------------------------------------------------------

EPISODES = 20  # auc_goal granularity of 0.05

AUC = {
    pr.MODE_BASELINE: {"labrel0": 0.2, "labrel4": 0.2, "labrel8": 0.2,
                       "labrel16": 0.2, "labrel8s": 0.2, "labband": 0.4,
                       "lab4chain3": 0.2},
    pr.MODE_FROZEN: {"labrel0": 0.2, "labrel4": 0.3, "labrel8": 0.4,
                     "labrel16": 0.6, "labrel8s": 0.3, "labband": 0.5,
                     "lab4chain3": 0.3},
    pr.MODE_EXTENDED: {"labrel0": 0.25, "labrel4": 0.35, "labrel8": 0.45,
                       "labrel16": 0.65, "labrel8s": 0.35, "labband": 0.7,
                       "lab4chain3": 0.35},
    pr.MODE_REDUNDANCY: {"labrel0": 0.25, "labrel4": 0.25, "labrel8": 0.25,
                         "labrel16": 0.25, "labrel8s": 0.25, "labband": 0.45,
                         "lab4chain3": 0.25},
}
DEV = {pr.MODE_BASELINE: 80.0, pr.MODE_FROZEN: 70.0,
       pr.MODE_EXTENDED: 50.0, pr.MODE_REDUNDANCY: 75.0}
# 4 benchmark rows per cell; 0.75 -> [1,1,1,0], 0.5 -> [1,1,0,0]
GOAL_RATE = {pr.MODE_BASELINE: 0.5, pr.MODE_FROZEN: 0.75,
             pr.MODE_EXTENDED: 0.75, pr.MODE_REDUNDANCY: 0.5}
CHAIN_TIME = {pr.MODE_BASELINE: 5, pr.MODE_FROZEN: 2,
              pr.MODE_EXTENDED: 3, pr.MODE_REDUNDANCY: 4}


def _write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _goals_for_auc(auc):
    ones = round(auc * EPISODES)
    return [1] * ones + [0] * (EPISODES - ones)


def _default_fg(mode, profile):
    if profile == pr.CHAIN_PROFILE:
        t = CHAIN_TIME[mode]
        return [(i, 10, 0, t) for i in range(4)]
    return [(i, 10, 0, 3 + i) for i in range(4)]


def _bench_rows(mode):
    goals = [1, 1, 1, 0] if GOAL_RATE[mode] == 0.75 else [1, 1, 0, 0]
    return [[g, 10, DEV[mode], 1.0, 2.0, 5.0] for g in goals]


def make_cell(root, mode, seed, profile, auc, fg_entries, bench_rows):
    cell = root / mode / f"results_seed{seed}" / profile
    training = cell / "training_stereo_true"
    _write_csv(training / f"metrics_stereotypes_true_{profile}.csv",
               ["Episode", "GoalReached", "RewardZ1", "RewardZ2"],
               [[i + 1, g, 0.1, 0.2]
                for i, g in enumerate(_goals_for_auc(auc))])
    _write_csv(training / f"first_goal_stereotypes_true_{profile}.csv",
               ["ProtocolVersion", "ScenarioId", "Presentations", "Censored",
                "AnalysisPresentation"],
               [["phase1-v2", sid, pres, cen, ap]
                for sid, pres, cen, ap in fg_entries])
    _write_csv(cell / "ql_true" / "benchmark_results_ql_true.csv",
               ["GoalReached", "Steps", "CumIlluminanceDeviation",
                "WastedSteps", "ActuatorCyclingCount", "PolicyEnergyCost"],
               bench_rows)


def build_tree(root, seeds=(1, 2, 3), chain_fg_overrides=None,
               auc_overrides=None):
    chain_fg_overrides = chain_fg_overrides or {}
    auc_overrides = auc_overrides or {}
    for mode in pr.MODES:
        for seed in seeds:
            for profile in pr.PROFILES:
                auc = auc_overrides.get((mode, profile, seed),
                                        AUC[mode][profile])
                if profile == pr.CHAIN_PROFILE and mode in chain_fg_overrides:
                    fg = chain_fg_overrides[mode]
                else:
                    fg = _default_fg(mode, profile)
                make_cell(root, mode, seed, profile, auc, fg,
                          _bench_rows(mode))


def _run(root, out, extra=()):
    pr.main(["--roots", str(root), "--out", str(out),
             "--rmst-horizon", "10", "--bootstrap-iters", "50", *extra])


def _read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _family_by_member(out):
    rows = _read_rows(out / "phase1b_registered_family.csv")
    return {row["member"]: row for row in rows}, rows


# ---------------------------------------------------------------------------
# Pure-function unit tests
# ---------------------------------------------------------------------------

def test_rmst_no_censoring_equals_plain_mean():
    times = [3.0, 4.0, 5.0, 6.0]
    assert pr.rmst(times, [False] * 4, 10) == pytest.approx(np.mean(times))


def test_rmst_censored_scenarios_contribute_exactly_horizon():
    # Two censored cells (their recorded times are irrelevant) contribute H.
    value = pr.rmst([2.0, 99.0, 11.0, 4.0], [False, True, True, False], 10)
    assert value == pytest.approx((2.0 + 10.0 + 10.0 + 4.0) / 4)


def test_rmst_all_censored_equals_horizon():
    assert pr.rmst([11.0, 11.0, 11.0], [True, True, True], 7) == pytest.approx(7.0)


def test_rmst_uncensored_time_above_horizon_is_clipped():
    assert pr.rmst([12.0, 2.0], [False, False], 10) == pytest.approx(6.0)


def test_ols_slope_hand_computed_four_point_example():
    # xs mean 7; Sxy = 26, Sxx = 140 -> slope = 13/70.
    assert pr.ols_slope([0.0, 4.0, 8.0, 16.0], [1.0, 2.0, 3.0, 4.0]) \
        == pytest.approx(13.0 / 70.0)
    # Perfectly linear K-slope example used by the pipeline tests.
    assert pr.ols_slope([0.0, 4.0, 8.0, 16.0], [0.0, 0.1, 0.2, 0.4]) \
        == pytest.approx(0.025)


def test_centred_residual_variance_matches_numpy_ddof1():
    values = [0.1, 0.4, 0.3, 0.9]
    assert pr.centred_residual_variance(values) \
        == pytest.approx(float(np.var(values, ddof=1)))


# ---------------------------------------------------------------------------
# Full-pipeline tests on synthetic archives
# ---------------------------------------------------------------------------

def test_family_csv_frozen_enumeration_and_hand_computed_values(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    build_tree(root)
    _run(root, out)
    by_member, rows = _family_by_member(out)

    # BH family size is exactly m=6, never data-dependent.
    assert len(rows) == 6
    assert [row["member"] for row in rows] == ["M1", "M2", "M3", "M4", "M5", "M6"]
    assert all(row["bh_family_m"] == "6" for row in rows)
    assert all(row["n_paired"] == "3" for row in rows)

    # Hand-computed member statistics (constant across the 3 seeds).
    assert float(by_member["M1"]["mean_paired_statistic"]) == pytest.approx(0.025)
    assert float(by_member["M2"]["mean_paired_statistic"]) == pytest.approx(0.0)
    # DiD: (0.3-0.2)@labrel8s - (0.4-0.2)@labrel8 = -0.1
    assert float(by_member["M3"]["mean_paired_statistic"]) == pytest.approx(-0.1)
    assert float(by_member["M4"]["mean_paired_statistic"]) == pytest.approx(0.2)
    assert float(by_member["M5"]["mean_paired_statistic"]) == pytest.approx(-30.0)
    # M6 rmst endpoint: kg_frozen rmst 2, baseline rmst 5 -> -3.
    assert by_member["M6"]["endpoint"] == "rmst"
    assert float(by_member["M6"]["mean_paired_statistic"]) == pytest.approx(-3.0)
    assert float(by_member["M6"]["censoring_fraction_kg_frozen"]) == 0.0
    assert float(by_member["M6"]["censoring_fraction_baseline"]) == 0.0
    assert by_member["M6"]["rmst_horizon"] == "10"

    # No emitted p or q is ever 0 (M2 has all-zero diffs -> p = 1).
    for row in rows:
        for column in ("p_signflip_two_sided", "p_sign_exact_two_sided",
                       "q_signflip_bh_m6"):
            assert float(row[column]) > 0.0, (row["member"], column)
    assert float(by_member["M2"]["p_signflip_two_sided"]) == 1.0
    # n=3 identical-sign diffs -> exact enumeration p = 2/2^3.
    assert float(by_member["M1"]["p_signflip_two_sided"]) == pytest.approx(0.25)


def test_supporting_csv_redundancy_contrasts_and_overshoot_note(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    build_tree(root)
    _run(root, out)
    rows = _read_rows(out / "phase1b_supporting.csv")

    contrasts = [row for row in rows if row["row_type"] == "redundancy_contrast"]
    assert len(contrasts) == 6
    by_name = {row["name"]: row for row in contrasts}
    # M1 analogue: redundancy-baseline D_K = 0.05 constant -> slope 0.
    m1 = by_name["M1_labrel_stateless_frozen_slope_redundancy_only_analogue"]
    assert float(m1["value"]) == pytest.approx(0.0)
    # M4 analogue: labband 0.45 - 0.40 = 0.05.
    m4 = by_name["M4_labband_extended_vs_frozen_auc_redundancy_only_analogue"]
    assert float(m4["value"]) == pytest.approx(0.05)
    for row in contrasts:
        assert float(row["p_signflip_two_sided_uncorrected"]) > 0.0

    # Overshoot proxy: no FinalRank/TargetRank columns in the fabricated
    # benchmark CSVs -> NA with an explanatory note.
    overshoot = [row for row in rows if row["row_type"] == "overshoot_proxy"]
    assert overshoot and all(row["value"] == "NA" for row in overshoot)
    assert "not derivable" in overshoot[0]["note"]

    # Per-rung descriptives and cell primitives exist for the arm of record.
    rungs = [row for row in rows if row["row_type"] == "rung_descriptive"]
    assert {(row["profile"], row["mode"]) for row in rungs} >= {
        ("labrel8", pr.MODE_FROZEN), ("labrel8s", pr.MODE_BASELINE)}
    assert any(row["row_type"] == "cell_primitive" and row["metric"] == "rmst"
               for row in rows)
    assert any(row["row_type"] == "policy_energy" for row in rows)
    assert any(row["row_type"] == "cycling" for row in rows)


def test_censoring_rule_switches_m6_to_goal_rate_above_25_percent(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    # kg_frozen arm: 2 of 4 scenarios censored in every seed -> pooled 50%.
    censored_fg = [(0, 10, 1, 11), (1, 10, 1, 11), (2, 10, 0, 2), (3, 10, 0, 2)]
    build_tree(root, chain_fg_overrides={pr.MODE_FROZEN: censored_fg})
    _run(root, out)
    by_member, _ = _family_by_member(out)
    m6 = by_member["M6"]
    assert m6["endpoint"] == "goal_rate"
    assert float(m6["censoring_fraction_kg_frozen"]) == pytest.approx(0.5)
    assert float(m6["censoring_fraction_baseline"]) == pytest.approx(0.0)
    # Benchmark goal rates: kg_frozen 0.75 - baseline 0.5 = +0.25.
    assert float(m6["mean_paired_statistic"]) == pytest.approx(0.25)
    assert m6["predicted_direction"] == "positive"


def test_censoring_at_exactly_25_percent_keeps_rmst(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    # kg_frozen arm: exactly 1 of 4 scenarios censored (25%, not > 25%).
    boundary_fg = [(0, 10, 1, 11), (1, 10, 0, 2), (2, 10, 0, 2), (3, 10, 0, 2)]
    build_tree(root, chain_fg_overrides={pr.MODE_FROZEN: boundary_fg})
    _run(root, out)
    by_member, _ = _family_by_member(out)
    m6 = by_member["M6"]
    assert m6["endpoint"] == "rmst"
    assert float(m6["censoring_fraction_kg_frozen"]) == pytest.approx(0.25)
    # kg_frozen rmst = (10+2+2+2)/4 = 4; baseline rmst = 5 -> -1.
    assert float(m6["mean_paired_statistic"]) == pytest.approx(-1.0)
    assert m6["predicted_direction"] == "negative"


def test_did_hand_computed_example_via_pipeline(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    # Perturb labrel8s kg_frozen for seed 2 only: auc 0.5 instead of 0.3.
    build_tree(root, auc_overrides={(pr.MODE_FROZEN, "labrel8s", 2): 0.5})
    _run(root, out)
    by_member, _ = _family_by_member(out)
    # Seeds 1,3: (0.3-0.2)-(0.4-0.2) = -0.1; seed 2: (0.5-0.2)-(0.4-0.2) = 0.1.
    assert float(by_member["M3"]["mean_paired_statistic"]) \
        == pytest.approx((-0.1 + 0.1 - 0.1) / 3)


def test_pilot_diagnostics_refuses_family_output(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    # Seed-varying labrel16 kg_frozen auc so the M1 slope variance is nonzero.
    overrides = {(pr.MODE_FROZEN, "labrel16", 1): 0.6,
                 (pr.MODE_FROZEN, "labrel16", 2): 0.65,
                 (pr.MODE_FROZEN, "labrel16", 3): 0.7}
    build_tree(root, auc_overrides=overrides)
    _run(root, out, extra=("--pilot-diagnostics",))

    # The family and supporting CSVs are refused outright.
    assert not (out / "phase1b_registered_family.csv").exists()
    assert not (out / "phase1b_supporting.csv").exists()
    diag_path = out / "phase1b_pilot_diagnostics.csv"
    assert diag_path.exists()

    text = diag_path.read_text(encoding="utf-8")
    # No arm-labelled means, effect directions, or p/q values leak.
    for forbidden in ("p_signflip", "p_sign_exact", "q_signflip",
                      "mean_paired", "mean_ql", "predicted_direction",
                      "mean_paired_statistic", "ci_lo", "ci_hi"):
        assert forbidden not in text, forbidden

    rows = _read_rows(diag_path)
    variance_rows = {row["name"]: row for row in rows
                     if row["row_type"] == "centred_residual_variance"}
    m1_row = variance_rows["M1_labrel_stateless_frozen_slope"]
    # Hand computation: per-seed slopes via an independent fit (numpy),
    # then the ddof=1 variance of the centred residuals.
    xs = [0.0, 4.0, 8.0, 16.0]
    slopes = []
    for d16 in (0.4, 0.45, 0.5):
        slopes.append(float(np.polyfit(xs, [0.0, 0.1, 0.2, d16], 1)[0]))
    expected = float(np.var(slopes, ddof=1))
    assert float(m1_row["value"]) == pytest.approx(expected)

    # Allow-listed content is present.
    assert any(row["row_type"] == "censoring_fraction" for row in rows)
    assert any(row["row_type"] == "artifact_presence" for row in rows)
    assert any(row["row_type"] == "degeneracy_flag" for row in rows)
    # M2 diffs are all zero in this tree -> flagged degenerate.
    m2_flags = [row for row in rows
                if row["row_type"] == "degeneracy_flag"
                and row["name"].startswith("M2_")]
    assert m2_flags and m2_flags[0]["value"] == "1"


def test_canonical_float_formatting_and_line_endings(tmp_path):
    root = tmp_path / "archive"
    out = tmp_path / "out"
    build_tree(root)
    _run(root, out)
    raw = (out / "phase1b_registered_family.csv").read_bytes()
    assert b"\r" not in raw  # "\n" line endings only
    text = raw.decode("utf-8")
    assert "-0," not in text and not text.endswith("-0\n")
    # canonical helper behaviour
    assert pr._canonical(-0.0) == "0"
    assert pr._canonical(0.1 + 0.2) == format(0.1 + 0.2, ".12g")
