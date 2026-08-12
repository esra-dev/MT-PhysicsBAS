# Phase 2b-A start-state Q-gap proxy decision memo (2026-08-12)

Basis: the descriptive, sighted Phase-2b-A audit in
`phase2b_qgap/analysis/`, reproduced byte-for-byte from the four immutable
corrected Phase-2-v2 source artifacts. This memo applies the six screening
conditions frozen before real start-state Q-gap proxy computation. It does not
make a confirmatory or causal claim.

## Decision

**C2 prospective recovery ordering: DEFER.** Do not draft, register, or
dispatch C2 before thesis submission. Do not train seeds 21–40, reuse
seeds 1–20 as fresh parents, or substitute a sighted cell set.

`labiv` and `labmag` are also **DEFERRED**, without ranking either candidate.
No threshold is relaxed and no alternative predictor is selected after seeing
the retrospective outcome.

## What C1 found

The primary Panel-B association between cell-mean `deltaG` and censored
`deltaRecovery` was negative (`ρ = −0.737865`; paired-seed stability interval
`[-0.948683, −0.210819]`), opposite to the frozen positive prediction. The
signed-gap-median sensitivity was positive (`ρ = +0.600000`; stability
interval `[+0.200000, +1.000000]`). The change of direction across frozen
summaries prevents a stable mechanism ordering.

All four Panel-B leave-one-cell-out primary associations were negative. The
four-cell sighted reference set supplied four distinct `deltaG` levels and a
minimum adjacent separation of `11833/28000` (about `0.422607`) serialized-Q
units, but only four of its six pairwise orderings were concordant.

Detectability remained a separate stage. In each of the three corrected
detector-censored adverse dead-lamp cells, the KG arm had zero deterministic
`DetectorOpportunity` and zero detections across 20 seeds. The TR arm had
nonzero opportunity and observed detection fractions of `0.55`, `1.00`, and
`1.00`. This supports the qualitative policy-dependent observability account;
it does not turn a detection failure into a post-detection recovery result.

## Frozen screening conditions

| Gate | Result | Frozen assessment |
|---:|---|---|
| 1 | PASS | All four reference cells have verified artifacts; every seed-arm record has an analysed reachable scenario; every cell has a nonzero primary proxy value. |
| 2 | PASS | Four distinct reference levels; minimum adjacent gap `11833/28000`, above `0.02`. |
| 3 | FAIL | Panel-B primary `ρ = −0.737865`, below the required `+0.70`. |
| 4 | FAIL | `4/6` reference-cell pairs concordant; `5/6` required. |
| 5 | FAIL | The signed sensitivity changes direction and all four leave-one-cell-out primary associations are negative. |
| 6 | FAIL | After removing the three detector-censored cells, the Panel-A association remains negative (`ρ = −0.564288`). |

Because all six conditions had to pass, conditions 3–6 independently block
C2. Passing artifact integrity and predictor-spread checks is not evidence for
the proposed recovery ordering.

## Consequence for the thesis programme

Phase 2b-A ends as a bounded mechanism-proxy audit. It adds two useful limits
to the thesis interpretation: policy-dependent detector opportunity helps
describe the adverse dead-lamp cells, while the available pre-fault
start-state Q-gap proxy does not robustly order post-detection recovery across
the clean-detection cells. It remains a proxy because the archives contain no
complete trace of the exact blacklisting state.

The Phase-1b conclusion is unchanged: its confirmed effects remain 8–70 times
below their registered SESOIs. No new learner campaign is authorised.

## Audit pointers

- Frozen protocol: `docs/PHASE2_QGAP_RETROSPECTIVE.md`
- Machine-readable specification: `analysis/phase2_qgap_spec.json`
- Results report: `phase2b_qgap/analysis/PHASE2_QGAP_RETROSPECTIVE_RESULTS.md`
- Gate rows: `phase2b_qgap/analysis/ordering_assessment.csv`
- Checksums: `phase2b_qgap/analysis/SHA256SUMS.csv`
- Reproducer: `analysis/reproduce_phase2_qgap.py`
