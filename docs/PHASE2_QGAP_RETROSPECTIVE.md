# Phase 2b-A start-state Q-gap proxy retrospective

Protocol revision: `2026-07-27d`
Freeze date: `2026-07-27`

**DESCRIPTIVE/SIGHTED — NOT A PREREGISTRATION**

Revision `d` is a pre-execution implementation clarification committed before
any real proxy output: it makes Gate 1's non-degeneracy test explicitly
per-cell and pins the bootstrap percentile interpolation rule. It does not
change panel membership, the proxy, the detector descriptor, outcomes, or any
threshold.

This document freezes a retrospective, hypothesis-generating mechanism-proxy
audit before the start-state Q-gap proxy is computed on the real corrected
Phase-2-v2 artifacts. The corrected recovery and detection outcomes were
already known when this protocol was written. Nothing produced under this
protocol is a prospective test, a causal estimate, or evidence from held-out
lab designs.

The quantity below is always called the **start-state Q-gap proxy**. It is
evaluated at the settled scenario start, before detection. The source artifacts
do not contain the complete state trace needed to reconstruct the state at
which a component was actually detected and blacklisted.

## 1. Scope and fixed interpretation

Phase 2b-A asks two separate descriptive questions:

1. Does a deterministic clean-policy rollout create an observation at which
   detector v2 could charge evidence to the faulty component?
2. Conditional on the registered record in which detection occurred, does the
   clean policy's start-state preference for actions later removed by the fault
   order recovery burden across cells?

`DetectorOpportunity` answers the first question. The start-state Q-gap proxy
answers the second. They must remain separate in every table, figure, memo, and
thesis statement. A failure to detect must never be redescribed as slow
re-ranking.

This phase does not:

- run Q-learning, adaptation, or benchmark jobs;
- change learner, reasoner, detector, simulator, scenario, reward, ontology, or
  action-registry code;
- dispatch seeds 21--40;
- use `phase2_postinv`, pre-inversion, withdrawn, or protocol-v1 data;
- revive `labiv`, `labmag`, `lab4chain4`, `lab5r`, or the wrong-direction-KG
  ladder;
- compute hypothesis-test p-values or multiplicity adjustments;
- select cells, exclusions, proxy variants, or thresholds after viewing the
  real proxy values.

The governing arm names are:

- KG: `ql_true`;
- TR: `ql_false`.

## 2. Sighted outcome disclosure

The corrected registered Tier-1 outcome was known at freeze time: **2
supported, 3 adverse, and 3 null**. The labels below are inherited registered
Phase-2 result labels; they are not new inferences from this audit.

| Registered result label | Cells |
|---|---|
| supported | `lab2_f1bdead`, `labmon2_f2dead_lowsun` |
| adverse, detector-censoring driven | `lab3_f1dead`, `lab3_f1dead_z2`, `lab3_f2dead_lowsun` |
| null | `lab3_f1bdead`, `lab3_f1binv`, `labmon_f1dead` |

In particular, the three adverse cross-coupled lab3 dead-lamp cells are not
clean observations of post-detection recovery: detector-v2 censoring in the KG
arm dominates their registered record.

## 3. Authoritative source-artifact contract

Only the following four corrected Phase-2-v2 source artifacts are admissible.
All were created on `2026-07-23`. The earliest GitHub expiry is
`2026-10-21 11:06:14 UTC`; `2026-10-20` is the conservative internal rescue
deadline, not the GitHub expiry.

| Dispatch | Run ID | Seeds | Artifact ID | Registered ZIP SHA-256 |
|---|---:|---:|---:|---|
| A1 | `30001857104` | 1--10 | `8572943960` | `0391dcdc7f35a1e2f7589797a789ec0011bedd5e970327ddcbff7122658b4639` |
| A2 | `30001867521` | 11--20 | `8573028167` | `26ff1cc4e6ff52368871d58d3ef54b69602539ad724c5910a8a8ffdd731804f8` |
| B1 | `30001878310` | 1--10 | `8581672322` | `f53e13f0bbb16a7afea38360b004444068bba92e8a29885eb53203b98df1df31` |
| B2 | `30001888910` | 11--20 | `8580725637` | `22ef5fbaf2aa9ed8a473641c6237eeaeb22db87918b20953519d3f9cfe291235` |

The source implementation commit is `19f4f3ff`. Each immutable ZIP is verified
before extraction. Extraction is to:

```text
phase2b_qgap/source/run_<run_id>/phase2-consolidated/
```

The immutable ZIPs remain outside Git or in an approved archival store. No
digest check may be skipped.

### 3.1 Required files and provenance

For every adaptation cell:

- `ADAPT_OK_stereotypes_<arm>_<profile>.json` supplies run seed, parent
  profile, scenario-schedule hash, parent file set, and parent-Q-table hash;
- `qtable_final_stereotypes_<arm>_<parent>.csv` supplies the primary serialized
  combined clean Q-table;
- the matching per-zone Q-tables, visits file, and trust file are retained and
  hash-validated as provenance sidecars;
- `recovery_stereotypes_<arm>_<profile>.csv` supplies the registered
  `RecoveryEpisodes`, detection, reconvergence, and censoring fields;
- `config/run_config.json`, the relevant `config/golden_registry/registry_*.csv`,
  and the exact ordered training-scenario file supply configuration, actions,
  dimensions, and start-state inputs.

The immutable outcome join key is:

```text
(run_id, seed, arm, faulty_profile, parent_profile,
 parent_qtable_sha256, scenario_schedule_sha256)
```

Every join must be one-to-one. Duplicate, ambiguous, absent, filename-only, or
hash-inconsistent matches are fatal. A same-seed Q-table from another run or
with another parent hash is inadmissible. No input path may contain `postinv`,
`pre_inversion`, or a withdrawn run ID.

`source_manifest.json` records the GitHub run, artifact ID, registered artifact
digest, local ZIP digest, source commit, retrieval timestamp, extraction
inventory, and the validated hashes of every consumed or retained file.

## 4. Frozen panels

### 4.1 Panel A: corrected registered Tier-1 context

Panel A contains all eight registered cells, in this fixed order:

1. `lab3_f1dead`
2. `lab3_f1dead_z2`
3. `lab3_f1bdead`
4. `lab3_f1binv`
5. `lab2_f1bdead`
6. `labmon_f1dead`
7. `lab3_f2dead_lowsun`
8. `labmon2_f2dead_lowsun`

Panel A is the full corrected context. Its Q-gap/recovery association is shown
only as a visibly labelled detector-confounded sensitivity.

### 4.2 Panel B: re-ranking panel

Panel B contains the registered cells for which both arms detected the injected
fault in all 20 corrected seeds:

1. `lab3_f1bdead`
2. `lab3_f1binv`
3. `lab2_f1bdead`
4. `labmon2_f2dead_lowsun`

Membership is frozen from the corrected detector record, not from proxy values.
The non-registered recovery cell `lab2_f1binv` is reported separately and is
never silently pooled into Panel B.

### 4.3 Panel C: sighted C2 gate/reference set

Panel C contains:

1. `lab2_f1bdead`
2. `lab2_f1binv`
3. `lab3_f1binv`
4. `labmon2_f2dead_lowsun`

These cells are sighted references, not a held-out experimental set. The audit
may order them or reject a later experiment; it may not add a favorable sighted
cell. If all gates in Section 11 pass, a later experiment must use separately
selected, never-run cells.

## 5. Explicit fault-to-action mapping

`F_c` is fixed by the table below, not inferred by parsing a profile name. Each
component contributes both registered action polarities. A dead or inverted
component therefore removes the same two action labels from the survivor-route
model.

| Faulty profile | Parent topology | Fault mode | Faulty component(s) | Exact `F_c` action labels |
|---|---|---|---|---|
| `lab3_f1dead` | `lab3` | dead | `SetZ1Light` | `SetZ1Light=OFF`; `SetZ1Light=ON` |
| `lab3_f1dead_z2` | `lab3` | dead | `SetZ2Light` | `SetZ2Light=OFF`; `SetZ2Light=ON` |
| `lab3_f1bdead` | `lab3` | dead | `SetZ1Blinds` | `SetZ1Blinds=OFF`; `SetZ1Blinds=ON` |
| `lab3_f1binv` | `lab3` | inverted | `SetZ1Blinds` | `SetZ1Blinds=OFF`; `SetZ1Blinds=ON` |
| `lab2_f1bdead` | `lab2` | dead | `SetZ1Blinds` | `SetZ1Blinds=OFF`; `SetZ1Blinds=ON` |
| `lab2_f1binv` | `lab2` | inverted | `SetZ1Blinds` | `SetZ1Blinds=OFF`; `SetZ1Blinds=ON` |
| `labmon_f1dead` | `labmon` | dead | `SetZ1Light` | `SetZ1Light=OFF`; `SetZ1Light=ON` |
| `lab3_f2dead_lowsun` | `lab3` | dead + dead | `SetZ1Light`, `SetZ2Light` | `SetZ1Light=OFF`; `SetZ1Light=ON`; `SetZ2Light=OFF`; `SetZ2Light=ON` |
| `labmon2_f2dead_lowsun` | `labmon2` | dead + dead | `SetZ1Light`, `SetZ2Light` | `SetZ1Light=OFF`; `SetZ1Light=ON`; `SetZ2Light=OFF`; `SetZ2Light=ON` |

Before analysis, the implementation asserts that every listed label occurs
exactly once in the matching registered action golden and that the full
combined-Q header matches that golden by label. The golden's `actionIndex`
governs tie-breaking; CSV column position does not.

## 6. Settled faulty start state

For each ordered training scenario, reconstruct the start state from the exact
scenario inputs and registered topology. The reconstruction is deterministic:

1. Load primitive scenario inputs and component states.
2. Apply the cell's fault semantics to the physical model.
3. Perform the registered settle operation.
4. Recompute physical illuminance and every derived zone level/rank under the
   **faulty** physics.
5. Encode the resulting ranks, sunshine rank, and component booleans using the
   registered state-vector slot metadata.

Clean, pre-fault, or recovery-log `StartLevel`/level/rank fields must not be
trusted or copied. In particular, settled levels are recomputed after the fault
is applied even when a logged clean level is available.

The route goal is the effective goal used by the registered degraded-mode
recovery design: rank 2 in every zone for `labmon_f1dead`,
`lab3_f2dead_lowsun`, and `labmon2_f2dead_lowsun`; rank 3 in every zone for
the other six cells. This is frozen per cell in
`analysis/phase2_qgap_spec.json`. It is not selected from the Q-gap result.

For state-vector values `v_0, ..., v_(k-1)` and registered domain sizes
`d_0, ..., d_(k-1)`, define:

```text
stride_j = product(d_m for m = j+1, ..., k-1)
state_index = sum(v_j * stride_j for j = 0, ..., k-1)
```

Thus the last slot has stride 1, matching `QLearner.stateVecToIndex`. Every
value must satisfy `0 <= v_j < d_j`; out-of-domain values are fatal rather than
silently clamped by the analysis. A fixture must compare reconstructed vectors
and indices against the Java encoding.

## 7. Frozen start-state Q-gap proxy

For each `(cell c, arm a, seed i, ordered scenario s)`:

1. Construct the settled faulty start state as in Section 6.
2. In the faulty transition model, make every action in `F_c` unavailable.
3. Exhaustively enumerate all shortest first-passage paths from the start state
   to the registered goal. Goal entry ends a candidate path.
4. Let `R_c(s)` be the union of first-action labels over all shortest successful
   survivor paths.
5. Read the primary serialized combined clean Q-value by state index and exact
   action label.

The route search covers the complete finite reachable state graph; the
20-transition horizon in Section 8 applies only to `DetectorOpportunity`.
Implementation limits may cap how many full route strings are printed, but
must not approximate reachability, shortest distance, the exact shortest-path
count, or the union of shortest-path first actions.

For reachable, non-terminal starts:

```text
qFault(c,a,i,s) = max(Q_a,i(s,x) for x in F_c)
qRoute(c,a,i,s) = max(Q_a,i(s,x) for x in R_c(s))

signedGap(c,a,i,s) = qFault(c,a,i,s) - qRoute(c,a,i,s)
burden(c,a,i,s) = max(0, signedGap(c,a,i,s))
```

A positive signed gap means that the best action removed by the fault outranks
the best first action on any shortest surviving route at the settled start.
Zero burden means no forced downward re-ranking at that start. This definition
does not claim that the same gap remains at the later detection state.

### 7.1 Scenario classifications and exclusions

Each ordered scenario appears exactly once and receives exactly one class:

- `NO_RERANKING_NEEDED`: the settled faulty start already satisfies the goal.
  Report it and exclude it from gap aggregation.
- `UNREACHABLE`: no surviving goal-reaching path exists. Report it and exclude
  it from gap aggregation. Reachability remains a separate descriptor.
- `REACHABLE_NONTERMINAL`: at least one surviving path reaches the goal.
  Include it once with equal weight by ordered scenario ID.

There is no scenario-frequency weighting, recovery-outcome weighting,
best-route selection, deletion of zero Q rows, or hidden cell deletion. The
analysis reports shortest route length, shortest-route count, and the complete
first-action set `R_c(s)` for every included scenario.

### 7.2 Primary and sensitivity aggregates

For the `n_c` reachable, non-terminal ordered scenarios:

```text
G(c,a,i) = (1 / n_c) * sum_s burden(c,a,i,s)
S(c,a,i) = median_s signedGap(c,a,i,s)

deltaG(c,i) = G(c,KG,i) - G(c,TR,i)
deltaS(c,i) = S(c,KG,i) - S(c,TR,i)

deltaRecovery(c,i) =
    registeredCensoredRecovery(c,KG,i)
    - registeredCensoredRecovery(c,TR,i)
```

`G` (mean non-negative burden) and `deltaG` are primary. `S` (median signed
gap) and `deltaS` are the frozen signed sensitivity. Both are always reported
side by side; neither is selected after viewing recovery.

At cell level:

```text
cellDeltaG(c) = mean_i deltaG(c,i)
cellDeltaS(c) = mean_i deltaS(c,i)
cellDeltaRecovery(c) = mean_i deltaRecovery(c,i)
```

`registeredCensoredRecovery` mirrors the corrected registered analysis
exactly. If `RecoveryEpisodes` is negative, use the exact joined
`ADAPT_OK.adapt_episodes_effective + 1` and retain an explicit censor flag;
otherwise use the recorded value. A negative `DetectEpisode` likewise maps to
that cell-specific administrative bound for detect-episode summaries, and
`detection_occurrence` is zero exactly when `DetectEpisode < 0`. Censored seed
pairs are never dropped. This is the registered administrative-censoring
estimand, not an imputation of an observed recovery time.

The descriptive prediction is a positive ordering:
larger `cellDeltaG` corresponds to larger `cellDeltaRecovery` (slower KG
recovery relative to TR). Recovery is taken unchanged from the exact joined
registered row except for that already-registered censoring transformation.
Censor flags and bounds are always reported.

### 7.3 Exact serialized-Q arithmetic

Combined and per-zone Q-tables are serialized to two decimal places. The
analysis must:

- parse each Q token directly as `Decimal`, with context precision 28;
- reject non-finite values and any token with more than two fractional digits;
- represent an omitted saver row as exact `Decimal("0.00")` for every action;
- use exact decimal comparisons for maxima and ties;
- compute `signedGap` and `burden` in exact integer hundredths;
- retain aggregate numerators and denominators rather than rounding scenario
  means before arm differences, ranks, or gates;
- compare the `0.02` gate by exact rational cross-multiplication;
- use `ROUND_HALF_EVEN` only for explicitly labelled display columns.

For example, an aggregate may have sub-cent digits because it is the mean of
several exact-cent observations. Those digits describe averaging, not
additional Q-table measurement precision. Binary floating point may be used
only after exact values, ties, orderings, and gates have been fixed, such as for
plot coordinates. Canonical CSVs retain the exact-cent inputs and rational
aggregate numerator/denominator.

### 7.4 Combined table is the frozen primary proxy

The primary Q source for both the Q-gap proxy and `DetectorOpportunity` is:

```text
qtable_final_stereotypes_<arm>_<parent>.csv
```

This is the combined clean table as serialized. The runtime reload path
reconstructs action values from separately rounded per-zone files, so its sum
can occasionally differ from the separately rounded combined file. That fact
does not change this frozen proxy definition.

The analysis validates and preserves every per-zone sidecar, computes the
per-zone re-sum as a diagnostic, and reports value, tie-set, and greedy-action
discrepancies. It must not substitute the per-zone sum for the combined-table
primary value or silently resolve discrepancies in favor of the observed
outcome.

## 8. Separate `DetectorOpportunity` descriptor

`DetectorOpportunity` is a deterministic model descriptor, not a replay of
stochastic adaptation.

For every `(cell, arm, seed, ordered scenario)`:

1. Start from the settled faulty state.
2. Load the same primary serialized combined clean Q-table used in Section 7.
3. Run at most 20 faulty-simulator transitions with zero learning and zero
   exploration. Before each action, stop if the settled state already meets
   the effective analysis goal, matching the registered episode boundary.
4. At each step, select the applicable action with maximum combined Q at the
   current encoded state. Resolve exact-Q ties by the lowest registered
   `actionIndex`.
5. Apply the action in the faulty simulator, settle, and evaluate the exact
   detector-v2 **pre-first-blacklist static** chargeability and
   structural-maskability predicate from source commit `19f4f3ff` on the
   resulting observation.
6. Record whether an unmasked, chargeable observation of each injected faulty
   component occurred at least once within the 20 transitions.

The rollout is strictly **Q-only greedy**:

- no Q update;
- no exploration;
- no ontology/runtime prior term;
- no active diagnostic probe;
- no probe scheduling;
- no virtual blacklist or removal of a suspected action;
- no warm restart;
- no stochastic adaptation state.

Faulty actions remain available to the rollout because the question is whether
the clean policy creates detector evidence before blacklisting. After an
opportunity is first observed, the rollout continues until the next goal
boundary or the 20-action horizon.

The detector predicate is not approximated by a generic state change. The
implementation reuses the detector-v2 rules for component attribution,
expected-versus-observed direction, dead/no-response evidence, inverted
evidence, IV/structural maskability, and whether the observation is chargeable.
Blacklist state, contaminated-zone state, and fault-suspect history are fixed
empty for every descriptor transition. This is the precise pre-first-blacklist
boundary: detector v2 blacklists on its first chargeable anomaly, so an anomaly
counter cannot already be suspect before that first opportunity. Continuing
the deliberately no-blacklist descriptor after an opportunity does not create
synthetic suspect history and is not a replay of later runtime adjudication.

For a single-fault scenario, the primary scenario flag is that component's
flag. For a multi-fault scenario, emit:

- one opportunity flag and first-opportunity step per faulty component;
- `detector_opportunity_any`, the logical OR across faulty components;
- `detector_opportunity_all_components`, the logical AND across components.

`detector_opportunity_any` is the primary scenario descriptor because the
registered `DetectEpisode` records the first detected faulty component.
`detector_opportunity_all_components` is descriptive only and cannot replace
the primary flag.

The seed/arm/cell summary is the equal-weight fraction of ordered scenarios
with `detector_opportunity_any`. Per-component fractions and the
all-components fraction are reported separately. Compare these descriptors
only with detection occurrence, censoring, and `DetectEpisode`; never fold them
into `G`, change Panel B membership, or relabel recovery.

## 9. Frozen summaries and stability analyses

All summaries preserve the arm pairing by seed.

For each cell and arm, report:

- scenario and seed counts;
- mean, median, and range of burden and signed gap;
- exact maximum-action tie rates for `F_c` and `R_c(s)`;
- reachable, `NO_RERANKING_NEEDED`, and `UNREACHABLE` fractions;
- shortest survivor-route mean, median, range, and route-count distribution;
- `DetectorOpportunity` any, all-components, and per-component fractions;
- registered detection and censor counts and `DetectEpisode` summaries;
- registered recovery summaries.

For cell-level ordering, compute Spearman rank correlation with average ranks
for ties. It is an effect descriptor only. A constant vector produces
`undefined`, not zero.

The following are fixed:

- primary Panel-B Spearman between `cellDeltaG` and
  `cellDeltaRecovery`;
- the same association for `cellDeltaS`;
- a clearly labelled detector-confounded Panel-A sensitivity;
- all six pairwise Panel-B orderings;
- all six pairwise Panel-C candidate/reference orderings.

A pair is concordant only when the strict signs of the predictor difference and
recovery difference agree. A reversal is discordant. A tie in either quantity
is reported as tied and does not count as concordant.

### 9.1 Paired-seed bootstrap

Run exactly 10,000 bootstrap replicates with one Python standard-library
`random.Random(20260727)` instance. For each replicate, make exactly 20
successive `rng.randrange(20)` calls and map index `j` to seed ID `j + 1`.
Use that same draw across cells, retaining the KG and TR observations for each
drawn seed as a pair. Recompute cell means, Spearman descriptors, and pairwise
concordance counts. Report bootstrap medians and 2.5/97.5 percentiles as
descriptive stability intervals, not test results.

For each finite bootstrap descriptor and percentile `p` in `{0.025, 0.975}`,
sort the 10,000 replicate values, set `h = (n - 1) * p` and
`i = floor(h)`, and return
`x[i] + (h - i) * (x[i + 1] - x[i])`. Undefined replicate descriptors remain
counted and reported; only the finite values enter this fixed linear
interpolation.

The report must state prominently that resampling seeds does not create eight
independent lab designs. Seeds sharing a physical cell or parent topology are
not independent mechanism replications.

### 9.2 Frozen sensitivities

Report:

- primary mean burden beside the median signed-gap sensitivity;
- leave-one-Panel-B-cell-out Spearman and ordering;
- leave-one-parent-profile-out Spearman and ordering where at least three
  non-degenerate cells remain;
- Panel A with and without the three detector-censored adverse cells;
- combined-table versus summed-per-zone discrepancies as a Q-source
  diagnostic only;
- reachability and shortest-route length beside every association display.

Undefined or degenerate sensitivities remain visible with their reason. They
are not dropped or replaced.

## 10. Required outputs and figures

The real-data script will write only under `phase2b_qgap/analysis/`:

- `source_manifest.json`
- `qgap_scenario_rows.csv`
- `qgap_seed_rows.csv`
- `qgap_cell_summary.csv`
- `detector_opportunity_rows.csv`
- `ordering_assessment.csv`
- `qgap_vs_recovery.png`
- `detectability_audit.png`
- `PHASE2_QGAP_RETROSPECTIVE_RESULTS.md`
- `SHA256SUMS.csv`

`qgap_vs_recovery.png` shows Panel B as the primary descriptive panel, the
frozen signed-gap sensitivity, uncertainty/stability summaries, reachability,
and route-length context. Any Panel-A overlay or companion facet is explicitly
labelled detector-confounded.

`detectability_audit.png` compares registered detection/censoring and
`DetectEpisode` with `DetectorOpportunity` across Panel A, including
per-component and any/all-component distinctions for multi-fault cells.

The results report presents detection versus `DetectorOpportunity` in Panel A
and Q-gap versus recovery in Panel B. It contains no causal language,
hypothesis-test vocabulary, hidden deletion, or claim that the start-state
proxy is the actual post-detection gap.

## 11. Six fixed gates for a later C2 draft

These are screening gates, not statistical evidence. A later C2 plan may be
drafted only if **all six** pass:

1. For each of the four Panel-C sighted reference cells, all source artifacts
   are verified, every one of its 40 seed-arm records has at least one
   `REACHABLE_NONTERMINAL` scenario, and at least one of its 40 primary `G`
   values is nonzero. Non-degeneracy is evaluated per cell, not only after
   pooling the reference set.
2. Panel-C `cellDeltaG` has at least three distinct ordered levels, and every
   adjacent non-tied level is separated by at least exact `0.02` serialized-Q
   units.
3. Panel-B Spearman between `cellDeltaG` and `cellDeltaRecovery` is at least
   `+0.70`.
4. At least five of the six Panel-C pairwise orderings are concordant; tied
   pairs do not count.
5. The association direction does not reverse under the frozen median
   signed-gap sensitivity or any leave-one-Panel-B-cell-out analysis.
6. The ordering is not produced solely by the three detector-censored Panel-A
   cells: after removing those cells, the remaining registered cells must
   retain a defined positive predictor/recovery rank direction.

Any failed, undefined, unverifiable, or degenerate gate means defer or descope
C2 and stop after thesis integration. No threshold may be relaxed after the
results are viewed. Passing all gates authorizes only drafting a separate
prospective C2 plan; it does not authorize registration or dispatch.

## 12. Constraints on any later C2 plan

C2 is not part of Phase 2b-A. If all gates pass and the thesis timebox permits
drafting, the separate plan must:

1. Freeze a complete universe of never-run fault profiles on one common
   existing topology and one scenario schedule before candidate proxy
   computation. Reward, detector, action count, state encoding, and unrelated
   physics remain fixed.
2. Apply outcome-blind reachability, absence-of-shortcut, and identical
   `DetectorOpportunity` feasibility filters. Retain every rejection and
   reason.
3. Determine `N` by prospective power simulation with `N >= 4`. Select a
   size-`N` subset deterministically by maximum minimum adjacent mean
   `deltaG` separation, then maximum total range, then lexicographic canonical
   profile IDs. Require at least four ordered levels and exact `0.02` minimum
   adjacent separation.
4. Train fresh clean parents for both arms on disjoint seeds 21--40. Hash each
   parent and warm-start each later adaptation from its exact same-seed parent.
   Existing seed-1--20 parents remain design/screening data only.
5. For the already-selected cells, compute fresh-parent proxy values and freeze
   the predicted ordering and all ties before any faulty adaptation. Reapply
   the detector-opportunity requirement. If spread or detectability fails,
   cancel rather than replace a cell.
6. Use a two-stage model: `DetectorOpportunity` addresses detection and
   `DetectEpisode`; the start-state Q-gap proxy addresses recovery conditional
   on detection. Treat cluster-aware seed-level association as secondary to
   held-out cell ordering and pairwise concordance.
7. Freeze a wall-clock and compute-budget limit before drafting. If clean
   training plus adaptation does not fit, stop rather than weaken the held-out
   design.

Neither `labiv` nor `labmag` is ranked or dispatched by this protocol.

## 13. Implementation and verification gates

Before any real-data execution:

- the Phase-1b and corrected Phase-2/3/4 thesis integration must already exist;
- this protocol, the machine-readable spec, implementation, and synthetic
  fixtures must be committed;
- tests must cover action-label remapping, omitted all-zero rows, multiple
  shortest routes, terminal starts, unreachable starts, multi-fault action
  sets, exact two-decimal ties, detector masking, inverted evidence, and
  duplicate joins;
- the combined-Q header must match the action golden;
- reconstructed state vectors and indices must match Java stride encoding;
- all agent, detector, and simulator runtime code must remain byte-unchanged.

Before reporting:

- all four ZIP digests and all parent file-set hashes must match;
- every outcome join must be exact and one-to-one;
- transition, reachability, and detector-opportunity fixtures must pass;
- the real-data analysis commit must descend from the protocol-freeze commit;
- a clean temporary reproduction must rebuild canonical CSVs and figures
  byte-equivalently;
- `SHA256SUMS.csv` must cover every other canonical output;
- a dated decision memo must record proceed-to-draft, defer, or descope.

Real corrected data must not be executed merely to test or refine this
protocol. Failures are repaired against synthetic fixtures, followed by a new
documented freeze before the single real-data analysis run.
