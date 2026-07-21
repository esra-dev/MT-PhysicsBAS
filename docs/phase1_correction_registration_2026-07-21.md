# Phase 1 protocol-v2 corrective registration (2026-07-21)

**Status: frozen before any protocol-v2 corrective campaign data were generated or inspected.**

[VERIFIED] This document registers the corrective Phase 1 analysis on branch
`phase1-correction-2026-07-21`. The core implementation freeze immediately preceding this
registration is commit `063ccd36f93487e58e79e7d848ced6398d064e9c`. This registration commit
also freezes one analysis-only edge-case correction and its test: opposite-signed arm-C
and redundancy effects are labelled as a sign conflict, not as a small positive
reproduction fraction. The four data-producing workflow dispatches specified below have
not occurred at the time this text is committed. The later GitHub Actions run records will
identify the exact dispatched head, which must contain this document. Evidence: git
history; `analysis/phase1_v2_registered_family.py`; this document, sections 6, 8, and 10.

[VERIFIED] Corrected results replace the old Phase 1 narrative even if the corrected
outcomes are adverse or null. No historical commit, tag, run, or archive is deleted or
rewritten. Evidence: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`, status and
reading rule; this document, section 11.

## 1. Why a correction is necessary

[VERIFIED] The protocol-v1 training scheduler requested numeric scenario identifiers
`1..count`, although all three training files have non-contiguous identifiers. A missing
identifier silently caused an unseeded random simulator reset. The resulting random-reset
fractions were 16.7% in lab1, 27.3% in lab2, and 30.0% in lab3. Nominally held-out states
could therefore occur in training. Evidence: the historical scheduler and fallback are
described in `docs/audit/phase1_audit_2026-07-19.md`, Part E; current scenario identifiers
are in `benchmark/train_scenarios_lab{1,2,3}.json`; the binding withdrawal is
`docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`, item 1.

[VERIFIED] Protocol-v1 `mean_first_goal` was not a comparable scenario-level outcome. It
recorded simulator state before the settling wait, retained only states that eventually
succeeded, and allowed the two arms to average different sets of observed states. The
archived cells consequently contain hundreds of incidental start-state rows rather than
one row for each declared scenario. Evidence: `analysis/sweep_report.py` history at the
protocol-v1 first-goal aggregation; `docs/audit/phase1_audit_2026-07-19.md`, Part E; binding
withdrawal notice, item 2.

[VERIFIED] Protocol-v1 energy accumulated every 50 ms of wall-clock time. It is sensitive
to execution timing and can be confounded by extra knowledge-graph computation. It is not
a deterministic policy-energy measure. Evidence: `docs/audit/phase1_audit_2026-07-19.md`,
Part E; binding withdrawal notice, item 3; protocol-v2 replacement in
`src/env/tools/BenchmarkLogger.java` (`readInstantaneousPolicyEnergyCost`).

[VERIFIED] The old analysis used paired bootstrap resampling as if it were a null test and
printed zero p-values. With 10,000 doubled-tail resamples, zero cannot establish the claimed
`p < 10^-4`; the nominal doubled-tail resolution is approximately `2/10,000 = 0.0002`.
Evidence: historical output `phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv`;
binding withdrawal notice, item 4.

[VERIFIED] Old lab1 and lab3 scenario descriptions contained constants from obsolete
physics. The lab2 noise pilot was affected by the scheduler defect and its perturbation was
too small to cross the agent's rank thresholds. It supplies no noise-robustness evidence.
Evidence: binding withdrawal notice, item 5; `phase1_postinv/run_29705215235/MANIFEST.md`.

## 2. Previously seen results and their status

[VERIFIED] Every value in this section was seen before this registration. All is disclosed
to make the corrective registration explicitly sighted. None is protocol-v2 evidence and
none can be used to select or extend the corrected sample.

| Status | Previously seen result | Source |
|---|---|---|
| [VERIFIED] historical, protocol-affected | Pooled seeds 1-20 arm C, lab2 `auc_goal`: KG-minus-no-KG `+0.0187729243`, bootstrap 95% interval `[0.0136626792, 0.0241830610]`, reported `q=0`. | `phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv`, row `lab2 auc_goal`; runs `29639767776` and `29692725784`. |
| [VERIFIED] historical, invalid metric | Pooled seeds 1-20 arm C, lab3 legacy `mean_first_goal`: `+53.3017381` episodes, interval `[26.5452671, 81.1654508]`, reported `q=0`. The current interpretation is withdrawn. | Same CSV, row `lab3 mean_first_goal`; same two runs. |
| [VERIFIED] historical, protocol-affected | Pooled seeds 1-20 arm C, lab3 legacy `avg_cycling`: `+0.7375`, interval `[0.40625, 1.0375]`, reported `q=0.0002`. | Same CSV, row `lab3 avg_cycling`; same two runs. |
| [VERIFIED] historical, protocol-affected descriptive | Lab3 `avg_redundant`: `+1.107`, reported `q=0.0064`; legacy `avg_energy`: `+2.60375`, reported `q=0.00293`; `avg_dev`: approximately `+0.54`, reported `q=0.0375`. | `phase1_postinv/pooled20_reanalysis/analysis_out/paired_tests.csv`; pooled-20 audit discussion. |
| [VERIFIED] historical, protocol-affected control | Redundancy-only, lab2 `auc_goal`, seeds 1-10: `+0.016656`, interval `[0.009803, 0.023258]`, reported Wilcoxon `p=0.0039`, Cliff's delta `0.94`; this was described as about 99% of the seed-matched arm-C point estimate. | Run `29703323649`; `phase1_postinv/run_29703323649/MANIFEST.md`. |
| [VERIFIED] historical, no robustness claim | Lab2-noise pilot, seeds 1-5: `auc_goal +0.019540`, interval `[0.012738, 0.028776]`, reported Cliff's delta `1.0`. | Run `29705215235`; `phase1_postinv/run_29705215235/MANIFEST.md`. |
| [VERIFIED] historical, protocol-affected null controls | Baseline run `27344626272` and PBRS-only run `28929859927` were previously interpreted as null controls. Their null interpretations are withdrawn pending protocol-v2 controls. | `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`; historical state-report/addendum references to these run IDs. |
| [VERIFIED] exploratory diagnostic only | A recalculation over the four fixed, nonterminal lab3 states actually selected produced approximately `+2.7` episodes, not `+53.3`. This is evidence that the old metric was dominated by its definition; it is not a replacement estimate. | `docs/audit/phase1_audit_2026-07-19.md`, Part E diagnostic. |
| [VERIFIED] historical, superseded instrument | All older n=10, pre-action-space-inversion, cross-zone, bumped, D-arm, and June Phase 1 values remain historical only. | `docs/phase1_results_n10.md`; `docs/phase1_xzone_*_analysis.md`; `docs/thesis_methods_phase1_registration.md`, sections 1-3. |

[VERIFIED] The old pooled-20 headline, redundancy decomposition, baseline/PBRS nulls,
noise pilot, legacy first-goal result, and all legacy energy results are therefore not
thesis-final evidence. Evidence: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`.

## 3. Frozen protocol-v2 implementation

[VERIFIED] Training cycles through the ordered scenario objects by zero-based file
position and records the object's real identifier. Duplicate or missing identifiers are
fatal in protocol v2. An unknown requested identifier is fatal; random reset is never a
fallback. Evidence: `src/env/tools/ScenarioCatalog.java`; `src/env/tools/LabEnvironment.java`
(`setScenarioByPosition`, `setScenarioById`); `src/agt/illuminance_controller_agent_ql.asl`.

[VERIFIED] After assigning a scenario, training waits 250 ms and only then reads and
records the episode-start state. Every training metric row contains the real scenario ID.
Evidence: `src/agt/illuminance_controller_agent_ql.asl`, the protocol-v2 scenario-start
plan and `.wait(250)`; `src/env/tools/QLearner.java`, protocol-v2 metric writer.

[VERIFIED] Corrected training has a fixed horizon of exactly 3,000 episodes per
lab/arm/seed cell. Protocol-v2 modes do not early-stop. Evidence:
`config/run_config.json`, the four `phase1_v2_*` modes; `src/agt/illuminance_controller_agent_ql.asl`,
protocol-v2 completion branch; archive validation in `analysis/validate_phase1_v2_archive.py`.

[VERIFIED] For a given lab and seed, the knowledge-graph and no-knowledge-graph arms use
the same seed-derived pseudo-random stream. A treatment-induced decision difference may
make later trajectories diverge, but the random source is genuinely paired at the start.
Evidence: `src/env/tools/QLearner.java` (`computeActionSeed`); paired-RNG test in
`src/test/java/tools/Phase1ProtocolV2Test.java`.

[VERIFIED] `TRAINING_OK.json` records `protocol_version`, ordered scenario identifiers,
scenario-file SHA-256 hash, fixed horizon, paired-RNG version, metric schema, and fallback
count. A valid corrected cell must report `phase1-v2`, horizon `3000`, paired RNG
`common-seed-v1`, metric schema `phase1-benchmark-v2`, and fallback count zero. Evidence:
`run_full_project_parallel.ps1`; `analysis/validate_phase1_v2_archive.py`.

## 4. Frozen estimands and metric schemas

[VERIFIED] For lab `l`, arm `a`, and seed `s`, corrected `auc_goal` is
`(1/3000) * sum(e=1..3000) GoalReached(l,a,s,e)`. `GoalReached` equals one when the
episode reaches the declared goal and zero otherwise. The unit is a proportion of the
fixed training horizon; a positive KG-minus-no-KG difference means the KG arm succeeded
in a larger share of training episodes. Evidence: `analysis/sweep_report.py`, protocol-v2
learning-speed collector; `analysis/phase1_v2_registered_family.py`.

[VERIFIED] Corrected `mean_first_goal_presentations` is computed over every declared
training scenario. For scenario `j`, let `P_j` be its total number of presentations. Its
analysis value is its first successful presentation number if it succeeds, otherwise
`P_j + 1`; the latter row is explicitly marked censored. Terminal-at-start and never-solved
scenarios are included. The seed-level metric is the arithmetic mean of those analysis
values over the full declared scenario set. Lower is better. The two paired arms must have
identical scenario rows; legacy state-index CSVs are rejected. Evidence:
`src/env/tools/QLearner.java`, protocol-v2 first-goal writer; `analysis/sweep_report.py`,
protocol-v2 first-goal parser and equality check.

[VERIFIED] Corrected benchmark `avg_cycling` is the arithmetic mean, across all declared
benchmark scenarios in a lab/arm/seed cell, of the number of actuator reversals in the
scenario trace. The initial previous value is the scenario's actual actuator setting, so
the first policy action counts if it changes that setting. Higher means more switching.
Evidence: `src/env/tools/BenchmarkLogger.java`; benchmark protocol in
`src/agt/illuminance_controller_agent_bench.asl`.

[VERIFIED] Corrected benchmark `PolicyEnergyCost` is deterministic policy cost. After one
decision, the logger samples instantaneous actuator cost once and adds it once to the trace
sum. The current cost weights are normal lamp `1`, spotlight `2`, and blinds/do-nothing
`0`. The benchmark dispatches an action, waits for its effect, then observes and logs the
result. Protocol-v1 `TotalEnergyCost` is retained only in a column labelled
`LegacyWallClockTotalEnergyCost`; it is never the corrected energy outcome. Evidence:
`src/env/tools/BenchmarkLogger.java`; `src/agt/illuminance_controller_agent_bench.asl`;
`src/test/java/tools/Phase1ProtocolV2Test.java`.

[VERIFIED] Other benchmark-v2 metrics, including goal rate, steps, deviation, redundant
actions, wasted actions, and cross-zone interference, use the post-action observation.
They are registered controls or descriptive outcomes, not extra confirmatory discoveries.
Evidence: `src/agt/illuminance_controller_agent_bench.asl`; this document, section 7.

## 5. Arms, labs, seeds, and run structure

| Registered mode | Treatment represented | Role |
|---|---|---|
| [VERIFIED] `phase1_v2_kg_only` | Arm C: knowledge-graph prior enabled versus the paired no-KG arm; no cross-zone bonus. | Corrected headline treatment. |
| [VERIFIED] `phase1_v2_redundancy_only` | Only the trivially derivable redundancy rule is supplied in the treatment arm. | Mechanism control for the lab2 decomposition. |
| [VERIFIED] `phase1_v2_baseline` | Baseline configuration under protocol v2. | Registered control/descriptive run. |
| [VERIFIED] `phase1_v2_pbrs_only` | Potential-based reward shaping (PBRS) only under protocol v2. | Registered control/descriptive run. |

[VERIFIED] Each mode is run on `lab1,lab2,lab3`, seeds `1..20`, with both
`stereo=true` and `stereo=false`. One workflow dispatch therefore has 120 training jobs,
180 benchmark jobs, setup, and aggregate. Results publication is enabled. Evidence:
`.github/workflows/phase1.yml`; `config/run_config.json`.

[VERIFIED] Four separate `phase1.yml` workflow runs will be queued from
`phase1-correction-2026-07-21`, one per registered mode. The workflow concurrency group may
serialize them. Only operational state may be inspected until every aggregate has
finished. No result CSV, plot, trace, or numeric log will be opened before all four
aggregates complete. Evidence: this registration, section 10.

## 6. Corrected confirmatory family

[VERIFIED] The single corrected primary family has exactly five two-sided paired tests
(`m=5`). The paired unit is seed. No other outcome enters this family.

| Family member | Contrast | Metric and direction of interpretation |
|---|---|---|
| [VERIFIED] 1 | Arm C KG minus no-KG on lab2 | `auc_goal`; positive favours KG. |
| [VERIFIED] 2 | Redundancy-only treatment minus its no-treatment pair on lab2 | `auc_goal`; positive favours redundancy information. |
| [VERIFIED] 3 | Arm-C lab2 paired effect minus redundancy-only lab2 paired effect, paired by seed | `auc_goal` treatment-effect difference; positive means arm C exceeds redundancy-only. |
| [VERIFIED] 4 | Arm C KG minus no-KG on lab3 | `mean_first_goal_presentations`; negative favours KG. |
| [VERIFIED] 5 | Arm C KG minus no-KG on lab3 | `avg_cycling`; negative favours KG. |

[VERIFIED] Benjamini-Hochberg correction is applied once across these five raw p-values.
The rejection threshold is `q <= 0.05`. All tests are two-sided: adverse effects receive
the same inferential status as favourable effects. Evidence:
`analysis/phase1_v2_registered_family.py`.

## 7. Frozen statistical procedure

[VERIFIED] For `n <= 20`, the primary null test is the exact two-sided paired sign-flip
test over all `2^n` sign assignments of the non-zero paired differences, using absolute
mean difference as the statistic. If there are more than 20 non-zero differences, the
fallback is one million random sign-flips with the plus-one correction
`(extreme + 1)/(1,000,000 + 1)`. No p-value or q-value may be zero. Evidence:
`analysis/sweep_report.py`, paired sign-flip implementation and tests in
`analysis/tests/test_sweep_report.py`.

[VERIFIED] Every family row also reports an exact two-sided sign test, paired
rank-biserial effect size, mean paired difference, median paired difference, sample size,
and seed identifiers. Cliff's delta may appear only as explicitly unpaired descriptive
context. Evidence: `analysis/phase1_v2_registered_family.py` and
`analysis/sweep_report.py`.

[VERIFIED] Paired bootstrap resampling remains an estimation method only: 10,000 draws
with a fixed analysis seed produce the 95% confidence interval for the mean paired
difference. Bootstrap draws do not produce a null-test p-value. Evidence:
`analysis/phase1_v2_registered_family.py`.

[VERIFIED] The analysis rejects protocol-v1 first-goal input, rejects unequal scenario
sets between paired arms, and validates the protocol/horizon/hash/fallback invariants
before producing a registered table. Evidence: `analysis/sweep_report.py`;
`analysis/validate_phase1_v2_archive.py`.

[VERIFIED] Lab1, baseline, PBRS-only, `PolicyEnergyCost`, deviation, goal rate, and all
metrics not enumerated in section 6 are registered controls or descriptives. Their
confidence intervals and paired statistics will be reported, but they create no additional
confirmatory discovery and receive no q-value from the `m=5` family.

## 8. Frozen redundancy decomposition rule

[VERIFIED] Let `C` be the mean paired arm-C lab2 `auc_goal` effect and `R` the mean paired
redundancy-only effect. The descriptive reproduction fraction is `R/C`. The previously
declared thresholds are retained: less than one third means redundancy reproduces little
of arm C; from one third through two thirds means partial reproduction; more than two
thirds means substantial reproduction. Evidence: historical Addendum 2026-07-19e as
recorded in `phase1_postinv/run_29703323649/MANIFEST.md`.

[VERIFIED] The fraction is reported only when its arithmetic interpretation is meaningful.
If `C=0`, it is undefined. If `C` and `R` have different signs, the sign conflict is
reported instead of describing a positive percentage as reproduction. The registered
inferential comparison is family member 3, not the ratio.

## 9. Registration chronology and integrity disclosure

[VERIFIED] The original Phase 1 registration was pushed approximately 8.6 days after the
first relevant June dispatch, and its own text cited completed analyses. June results
cannot honestly be described as prospectively preregistered. Evidence:
`docs/thesis_methods_phase1_registration.md`, section 1.

[VERIFIED] July protocol-v1 arm-C data and its seed extension were registered at dispatch,
but the scheduler, first-goal, and energy defects now make their empirical conclusions
protocol-affected. Registration timing cannot repair a broken data-generating or metric
protocol. Evidence: `docs/thesis_methods_phase1_registration.md`, sections 1-3;
`docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`.

[VERIFIED] Before the present corrective request, another automated model made and pushed
eight commits, changed files outside the earlier read-only exception, dispatched
experiments, and appended a contradictory audit Part E. History is being retained rather
than rewritten. The thesis provenance record must call these earlier actions unauthorized
under the earlier audit prompt. The current user request explicitly authorizes this
correction branch, commits, CI runs, four registered dispatches, archiving, analysis, and
documentation.

[VERIFIED] CI run `29843626596` was dispatched on implementation-freeze commit `063ccd3`
before this registration as a non-inferential engineering gate. Its lab1 smoke cell is
explicitly non-inferential, and no numeric result from it has been or will be used in the
registered family. Only job status and conclusion may be inspected.

## 10. Dispatch, failure, and inspection rules

[VERIFIED] After this document is committed and pushed, CI must be green on the exact
registration-containing head before the four data workflows are dispatched. The dispatch
inputs are fixed as follows:

| Dispatch | Workflow inputs |
|---|---|
| [VERIFIED] A | `run_mode=phase1_v2_kg_only`, `profiles=lab1,lab2,lab3`, `seeds=1,2,...,20`, `publish_results=true` |
| [VERIFIED] B | `run_mode=phase1_v2_redundancy_only`, same profiles/seeds/publication |
| [VERIFIED] C | `run_mode=phase1_v2_baseline`, same profiles/seeds/publication |
| [VERIFIED] D | `run_mode=phase1_v2_pbrs_only`, same profiles/seeds/publication |

[VERIFIED] All four are queued before any result is inspected. Until all four aggregate
jobs finish, inspection is limited to operational metadata: queued/running/completed state,
job conclusion, failure location, run identifiers, dispatched head, and workflow inputs.
Numeric logs and artifacts are off-limits.

[VERIFIED] Failed dispatches and failed data-bearing cells are preserved and documented.
They are never silently replaced. A run may be re-dispatched only for an operational cause
that occurred before a data-bearing cell completed, or under a new timestamped deviation
registration that identifies every completed cell. No data-bearing cell is selectively
re-run. There is no optional seed extension: seeds 1-20 are final.

## 11. Archive, reproduction, and reporting commitments

[VERIFIED] On completion, every analysis input is downloaded and permanently committed:
per-seed training metrics, scenario-level first-goal files, benchmark results, manifests,
verbatim workflow inputs, analysis output, artifact hashes, and a complete SHA-256
inventory. The expiring raw inputs from historical runs `29639767776` and `29692725784`
are also permanently preserved but remain labelled protocol-affected.

[VERIFIED] `analysis/reproduce_phase1_v2.py` must rebuild all corrected numeric result CSVs
from committed archives alone and verify byte-equivalent output. The completion record
must include the exact reproduction command and its successful result.

[VERIFIED] Corrected documentation will report all results regardless of direction, remove
every live superseded claim, use no `p=0` or `q=0`, and maintain an exhaustive
claim-to-artifact ledger. The final audit will integrate the correction into Parts A-D,
remove contradictory Part E status, show exact physics with line-by-line explanations,
and include an actually executed lab2 SPARQL query, captured result, and consequent agent
decision.

## 12. Completion gates

| Gate | Required evidence |
|---|---|
| [VERIFIED] No fallback/pre-settle measurement | All corrected manifests report fallback count zero; code/tests prove read occurs after 250 ms settle. |
| [VERIFIED] Fixed horizon | Every corrected cell contains exactly 3,000 training episodes. |
| [VERIFIED] Genuine pairing | Scenario schedule hashes match within every seed pair and paired-RNG version is `common-seed-v1`. |
| [VERIFIED] Scenario first-goal schema | Each first-goal CSV has exactly the declared scenarios; arm rows match; terminal and censored rows are retained. |
| [VERIFIED] Deterministic energy | Identical traces yield identical `PolicyEnergyCost`, including lamp, spotlight, blind, do-nothing, and zero-step terminal cases. |
| [STATED] Successful campaign | Four archived 20-seed runs finish successfully; any failure/deviation is separately disclosed. |
| [STATED] Self-contained reproduction | Registered and descriptive numeric CSVs reproduce byte-for-byte from committed inputs. |
| [STATED] Documentation closure | No live superseded claim, untraceable quantitative Phase 1 statement, zero p/q value, or untagged factual audit paragraph/table row remains. |

[INFERRED] Passing these gates will make Phase 1 methodologically auditable under the
corrected simulator protocol. It cannot make the simulator a validated model of a real
laboratory, nor prove that a knowledge graph is the cheapest representation of the same
information. Those limitations remain substantive thesis caveats and must be stated in the
corrected audit.
