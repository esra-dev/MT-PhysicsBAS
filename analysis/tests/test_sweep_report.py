"""Unit tests for analysis/sweep_report.py statistical helpers.

These cover the building blocks that drive the multi-seed CI table and the
paired_tests.csv output. They are deliberately self-contained (no Gradle/CI
artefacts required) and use deterministic RNGs so results are reproducible.

Run with:
    python -m pytest analysis/tests -q
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Make the parent ``analysis`` package importable when invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from analysis import sweep_report as sr  # noqa: E402  (path-tweak above)


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def test_bootstrap_ci_single_value_is_degenerate():
    # Audit Step 6 S6-5: n<2 → NaN CI, not zero-width.
    mean, lo, hi = sr._bootstrap_ci([7.5], iters=500)
    assert mean == 7.5
    assert math.isnan(lo) and math.isnan(hi)


def test_bootstrap_ci_constant_series_has_zero_width():
    mean, lo, hi = sr._bootstrap_ci([3.0] * 5, iters=500)
    assert mean == lo == hi == 3.0


def test_bootstrap_ci_brackets_true_mean():
    rng_sample = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, lo, hi = sr._bootstrap_ci(rng_sample, iters=2000)
    assert math.isclose(mean, 3.0, abs_tol=1e-9)
    assert lo <= mean <= hi
    # 95% CI on n=5 of [1..5] should be roughly within (1, 5).
    assert 1.0 <= lo <= 3.0 <= hi <= 5.0


# ---------------------------------------------------------------------------
# Paired bootstrap diff
# ---------------------------------------------------------------------------

def test_paired_bootstrap_diff_detects_clear_effect():
    a = [10.0, 11.0, 9.0, 12.0, 10.5]
    b = [1.0, 2.0, 0.5, 3.0, 1.5]
    # Audit Step 6 S6-2: 6-tuple return (mean_d, lo, hi, p2, p1_pos, p1_neg).
    mean_d, lo, hi, p, p_pos, p_neg = sr._paired_bootstrap_diff(a, b, iters=2000)
    assert mean_d > 5.0
    assert lo > 0  # CI excludes zero -> significant
    assert hi > lo
    assert p < 0.05
    # mean_d > 0 → evidence against H_A:μ>0 should be small.
    assert p_pos < 0.05
    assert p_neg > 0.5


def test_paired_bootstrap_diff_no_effect_keeps_p_large():
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [1.1, 1.9, 3.05, 3.95, 5.05]
    mean_d, lo, hi, p, _p_pos, _p_neg = sr._paired_bootstrap_diff(a, b, iters=2000)
    assert abs(mean_d) < 0.1
    assert lo <= 0 <= hi   # CI straddles zero
    assert p > 0.3


def test_paired_bootstrap_returns_nan_for_short_input():
    out = sr._paired_bootstrap_diff([1.0], [2.0])
    assert all(math.isnan(x) for x in out)


# ---------------------------------------------------------------------------
# Cliff's delta
# ---------------------------------------------------------------------------

def test_cliffs_delta_extremes():
    # Strictly larger
    assert sr._cliffs_delta([5, 6, 7], [1, 2, 3]) == pytest.approx(1.0)
    # Strictly smaller
    assert sr._cliffs_delta([1, 2, 3], [5, 6, 7]) == pytest.approx(-1.0)
    # Identical -> ties only -> 0
    assert sr._cliffs_delta([1, 2, 3], [1, 2, 3]) == pytest.approx(0.0)


def test_cliffs_delta_partial_overlap():
    a = [3, 4, 5]
    b = [2, 4, 6]
    # pairs: 3>2, 3<4, 3<6, 4=2(>), 4=4(tie), 4<6, 5>2, 5>4, 5<6
    # gt count: (3,2),(4,2),(5,2),(5,4) -> 4
    # lt count: (3,4),(3,6),(4,6),(5,6) -> 4
    # delta = (4-4)/9 = 0
    assert sr._cliffs_delta(a, b) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Benjamini-Hochberg
# ---------------------------------------------------------------------------

def test_bh_qvalues_are_monotone_and_bounded():
    ps = [0.001, 0.01, 0.03, 0.05, 0.2, 0.4]
    q = sr._bh_qvalues(ps)
    assert all(0.0 <= x <= 1.0 for x in q)
    # BH adjusted values for sorted [0.001,0.01,0.03,0.05,0.2,0.4] with m=6
    # are non-decreasing in the sorted order.
    sorted_q = [q[i] for i in sorted(range(len(ps)), key=lambda i: ps[i])]
    for prev, cur in zip(sorted_q, sorted_q[1:]):
        assert cur + 1e-12 >= prev


def test_bh_qvalues_preserves_nan():
    q = sr._bh_qvalues([0.01, float("nan"), 0.5])
    assert math.isnan(q[1])
    assert 0.0 <= q[0] <= 1.0
    assert 0.0 <= q[2] <= 1.0


# ---------------------------------------------------------------------------
# Seed-root discovery
# ---------------------------------------------------------------------------

def test_find_seed_roots(tmp_path):
    parent = tmp_path / "benchmark"
    parent.mkdir()
    for n in (1, 2, 7):
        (parent / f"results_seed{n}").mkdir()
    (parent / "results").mkdir()           # should be ignored
    (parent / "results_seedXX").mkdir()    # malformed; ignored
    out = sr.find_seed_roots(parent)
    assert [s for s, _ in out] == [1, 2, 7]
