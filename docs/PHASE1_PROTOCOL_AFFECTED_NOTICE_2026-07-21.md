# Phase 1 protocol-affected evidence notice (2026-07-21)

**Status: binding withdrawal notice, committed before the Phase 1 protocol-v2 rerun.**

**Completion update (2026-07-22):** the registered correction campaign has completed.
Current evidence is `docs/phase1_results_v2.md`; the future-tense chronology below is
retained exactly as the pre-data withdrawal record.

The existing Phase 1 numerical results are historical, protocol-affected findings. They
must not be presented as thesis-final evidence. In particular, this notice withdraws the
current interpretation of the pooled-20 `mean_first_goal` difference of +53.30 episodes,
all legacy `avg_energy` results, the pooled-20 headline conclusions, the
redundancy-only control result, and the baseline/PBRS-only null results.

The reasons are material, not cosmetic:

1. The training scheduler requested integer IDs from 1 through the number of scenarios,
   although the scenario files use non-contiguous IDs. A missing ID silently invoked an
   unseeded random reset. This affected 16.7% of lab1, 27.3% of lab2, and 30.0% of lab3
   training episodes and could expose nominally held-out benchmark states during training.
2. Legacy `mean_first_goal` grouped the pre-settling simulator state, included only states
   that eventually succeeded, and could average different state sets in the two arms. It
   therefore did not estimate a comparable scenario-level time-to-first-success outcome.
3. Legacy `avg_energy` accumulated on a 50 ms wall-clock timer. It was timing-dependent
   and could be confounded by different computation time between arms.
4. The paired bootstrap was used as though it were a null test and could print `p=0`.
   Existing zero p/q values and claimed Monte Carlo bounds are not valid final reporting.
5. The lab1 and lab3 scenario descriptions contain constants from obsolete simulator
   physics. The lab2 noise pilot was scheduler-affected and its noise was
   observation-subthreshold; it supports no noise-robustness claim.

The correction campaign is defined by the pre-data registration that will be committed on
this branch after protocol-v2 code and tests are frozen and before any corrected experiment
is dispatched. Corrected results replace the historical narrative regardless of whether
they are favourable, adverse, or null. Historical files, commits, tags, and run archives
remain available for provenance and are not being rewritten.

**Reading rule:** until a document is rewritten with protocol-v2 results, every Phase 1
number in it must be read as superseded/protocol-affected unless it is explicitly a code or
configuration constant rather than an empirical result.
