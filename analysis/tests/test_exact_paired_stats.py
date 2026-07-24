"""Pin analysis/exact_paired_stats.py to the frozen Phase-1 v2 machinery.

The module is a copy, not an import, of the Phase-1 implementations (those
files are byte-frozen for reproduce_phase1_v2.py). These tests (1) compare the
copy against the Phase-1 originals on random data and (2) pin archived Phase-1
registered-family values as literals, so any drift in either copy is caught.
"""
import random

from analysis import exact_paired_stats as eps
from analysis import sweep_report


def test_all_positive_n20_hits_exact_floor():
    a = [float(i + 1) for i in range(20)]
    b = [0.0] * 20
    assert eps.paired_signflip_p(a, b) == 2 / 2**20 == 1.9073486328125e-06
    assert eps.exact_sign_p(a, b) == 2 / 2**20
    assert eps.paired_rank_biserial(a, b) == 1.0


def test_matches_frozen_phase1_implementation_on_random_data():
    rng = random.Random(20260722)
    for _ in range(25):
        n = rng.randint(2, 14)
        a = [rng.uniform(-1, 1) for _ in range(n)]
        b = [rng.uniform(-1, 1) for _ in range(n)]
        if rng.random() < 0.3 and n > 2:  # inject exact ties
            b[0] = a[0]
            b[1] = a[1]
        assert eps.paired_signflip_p(a, b) == sweep_report._paired_signflip_p(a, b)
        assert eps.exact_sign_p(a, b) == sweep_report._exact_sign_test_p(a, b)
        assert eps.paired_rank_biserial(a, b) == sweep_report._paired_rank_biserial(a, b)


def test_bh_reproduces_archived_phase1_v2_family_q_values():
    # p-values and q-values are literals from the committed
    # phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv.
    ps = [1.9073486328125e-06, 0.000102996826171875, 3.0517578125e-05,
          0.304351806640625, 0.1719818115234375]
    expected_qs = [9.5367431640625e-06, 0.000171661376953125,
                   7.62939453125e-05, 0.304351806640625, 0.21497726440429688]
    assert eps.bh_qvalues(ps) == expected_qs
    assert eps.bh_qvalues(ps) == sweep_report._bh_qvalues(ps)


def test_exact_sign_p_17_of_20_positive():
    # 17/20 positive pairs: 2 * P(X <= 3 | n=20, 0.5) = 0.0025768280029296875,
    # the value in archived registered-family row 2.
    a = [1.0] * 17 + [-1.0] * 3
    b = [0.0] * 20
    assert eps.exact_sign_p(a, b) == 0.0025768280029296875


def test_ties_and_zero_diffs():
    assert eps.paired_signflip_p([1.0, 2.0], [1.0, 2.0]) == 1.0
    assert eps.paired_rank_biserial([1.0, 2.0], [1.0, 2.0]) == 0.0
    assert eps.exact_sign_p([1.0, 2.0], [1.0, 2.0]) == 1.0


def test_rank_biserial_simple_case():
    # diffs [3, -1, 2]: abs ranks 3->3, 1->1, 2->2; (3+2 - 1) / 6
    assert eps.paired_rank_biserial([3.0, -1.0, 2.0], [0.0, 0.0, 0.0]) == (5 - 1) / 6


def test_monte_carlo_path_above_20_pairs_never_zero():
    a = [float(i + 1) for i in range(21)]
    b = [0.0] * 21
    p = eps.paired_signflip_p(a, b)
    assert 0.0 < p <= 1.0
    # Plus-one correction floor: at least 1/(mc_iters+1).
    assert p >= 1 / 1_000_001
