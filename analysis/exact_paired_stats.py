#!/usr/bin/env python3
"""Exact paired statistics for the corrected Phase-2/3/4 confirmatory analyses.

This module is a deliberate, dependency-free COPY of the frozen Phase-1 v2
statistical machinery in analysis/sweep_report.py: the exact two-sided paired
sign-flip test, the exact binomial sign test, the matched-pairs rank-biserial
correlation, and Benjamini-Hochberg q-values. It is copied rather than
imported or refactored because the Phase-1 analysis files are byte-frozen —
analysis/reproduce_phase1_v2.py must keep rebuilding the archived Phase-1
outputs byte-identically, so nothing here may ever require touching those
modules. analysis/tests/test_exact_paired_stats.py pins this copy against the
Phase-1 implementation and against archived Phase-1 registered-family values.
"""

from __future__ import annotations

import math


def paired_signflip_p(a: list[float], b: list[float],
                      mc_iters: int = 1_000_000) -> float:
    """Two-sided paired randomisation test of a zero mean difference.

    All 2^n sign assignments are enumerated for n<=20. Above 20, a fixed-seed
    one-million-draw Monte Carlo estimate uses the plus-one correction, so the
    returned p-value can never be zero.
    """
    if len(a) != len(b) or len(a) < 2:
        return float("nan")
    diffs = [float(x) - float(y) for x, y in zip(a, b) if float(x) != float(y)]
    if not diffs:
        return 1.0
    observed = abs(sum(diffs))
    tolerance = 1e-12
    n = len(diffs)
    if n <= 20:
        total = 1 << n
        try:
            # Vectorise in bounded chunks. This preserves exact enumeration
            # while avoiding an O(n*2^n) Python loop for every metric.
            import numpy as np  # type: ignore
            values = np.asarray(diffs, dtype=float)
            extreme = 0
            chunk = 65_536
            bit_positions = np.arange(n, dtype=np.uint64)
            for start in range(0, total, chunk):
                masks = np.arange(start, min(start + chunk, total), dtype=np.uint64)
                bits = ((masks[:, None] >> bit_positions) & 1).astype(np.int8)
                signs = (bits * 2 - 1).astype(float)
                signed_sums = signs @ values
                extreme += int(np.count_nonzero(
                    np.abs(signed_sums) + tolerance >= observed))
            return extreme / total
        except Exception:
            # Gray-code enumeration changes one sign per assignment, reducing
            # the stdlib fallback to O(2^n).
            signed_sum = -sum(diffs)
            extreme = int(abs(signed_sum) + tolerance >= observed)
            previous_gray = 0
            for index in range(1, total):
                gray = index ^ (index >> 1)
                changed = gray ^ previous_gray
                bit = changed.bit_length() - 1
                if gray & changed:
                    signed_sum += 2.0 * diffs[bit]
                else:
                    signed_sum -= 2.0 * diffs[bit]
                if abs(signed_sum) + tolerance >= observed:
                    extreme += 1
                previous_gray = gray
            return extreme / total

    import random
    rng = random.Random(0x51F1F)
    extreme = 0
    for _ in range(mc_iters):
        signed_sum = sum(value if rng.getrandbits(1) else -value for value in diffs)
        if abs(signed_sum) + tolerance >= observed:
            extreme += 1
    return (extreme + 1) / (mc_iters + 1)


def exact_sign_p(a: list[float], b: list[float]) -> float:
    """Exact two-sided binomial sign test; ties are removed."""
    signs = [1 if x > y else -1 for x, y in zip(a, b) if x != y]
    n = len(signs)
    if n == 0:
        return 1.0
    k = min(sum(s > 0 for s in signs), sum(s < 0 for s in signs))
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def paired_rank_biserial(a: list[float], b: list[float]) -> float:
    """Matched-pairs rank-biserial correlation; zeros are removed."""
    diffs = [float(x) - float(y) for x, y in zip(a, b) if float(x) != float(y)]
    if not diffs:
        return 0.0
    order = sorted(range(len(diffs)), key=lambda i: abs(diffs[i]))
    ranks = [0.0] * len(diffs)
    pos = 0
    while pos < len(order):
        end = pos + 1
        while end < len(order) and abs(diffs[order[end]]) == abs(diffs[order[pos]]):
            end += 1
        average_rank = ((pos + 1) + end) / 2.0
        for j in range(pos, end):
            ranks[order[j]] = average_rank
        pos = end
    positive = sum(rank for rank, diff in zip(ranks, diffs) if diff > 0)
    negative = sum(rank for rank, diff in zip(ranks, diffs) if diff < 0)
    return (positive - negative) / (positive + negative)


def bh_qvalues(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted q-values; NaNs preserved."""
    indexed = [(i, p) for i, p in enumerate(pvalues) if not (p != p)]
    if not indexed:
        return [float("nan")] * len(pvalues)
    indexed.sort(key=lambda t: t[1])
    m = len(indexed)
    q = [float("nan")] * len(pvalues)
    prev = 1.0
    # Iterate from largest p to smallest to enforce monotonicity.
    for rank in range(m, 0, -1):
        i, p = indexed[rank - 1]
        adj = p * m / rank
        prev = min(prev, adj)
        q[i] = min(1.0, prev)
    return q


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return float("nan")
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0
