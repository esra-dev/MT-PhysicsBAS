# Pre-Registration of Hypotheses

**Project:** MT-Esra — Stereotype-Guided Q-Learning for Smart-Building Lighting Control
**Author:** Esra D.
**Date committed:** 2026-05-24
**Status:** locked *before* the paper-mode multi-seed sweep produces any aggregated CI output.

This document fixes the hypotheses, statistical tests, and decision rules **in advance** of running the
paper sweep so that the results section of the thesis / IEEE paper distinguishes confirmatory analyses
from exploratory ones. Any analysis not described below that ends up in the paper is to be reported
explicitly as exploratory.

Reference for the methodology: Munafò et al., "A manifesto for reproducible science," *Nature Human Behaviour*, 2017.

---

## 1. Design at a glance

- **Independent variables**
  - `mode ∈ {rule_based, ql_false, ql_true}`
  - `profile ∈ {custom2 (W1), custom3 (W2), custom4 (W3), custom5 (W4), custom6 (W5), custom7 (W6), custom8 (clean)}`
  - `seed ∈ {1, 2, 3, 4, 5}` — independent replicas
- **Configuration under test (main run, "full system")**
  - `reward_shaping = "pbrs"` (E2 on)
  - `adaptive_trust = true` (E3 on)
  - `stereo_prior_scale = 5.0`
  - `reward_clip = 50.0`
  - all other knobs at the `paper` defaults in `config/run_config.json`
- **Dependent variables (metrics)**, computed per scenario then averaged per (profile, mode, seed):
  - `goal_rate` (primary)
  - `avg_steps` (secondary)
  - `avg_dev` (cumulative illuminance deviation)
  - `avg_energy`
  - `avg_wasted`
- **Replication**: 5 seeds for the main sweep, 3 seeds for each ablation.

## 2. Statistical methods (locked)

For every (profile, metric) cell we compute:

1. **Mean and 95 % bootstrap confidence interval** across seeds (10 000 resamples, `numpy.random.default_rng(0xC1)` for determinism). Implemented in `analysis/sweep_report.py::aggregate_seeds`.
2. **Paired bootstrap p-value** for `ql_true − ql_false` and `ql_true − rule_based`, two-sided, 10 000 resamples. Pairing is by seed (same training seed produces both `ql_true` and `ql_false` outcomes on the same scenario set).
3. **Wilcoxon signed-rank** test as a non-parametric backup (`scipy.stats.wilcoxon`, two-sided).
4. **Cliff's δ** as an effect size (negligible < 0.147, small < 0.33, medium < 0.474, else large).
5. **Multiple-comparisons correction**: Benjamini–Hochberg q-values across the family of `(7 profiles × 5 metrics × 2 mode-pairs) = 70` tests per analysis (main, ablation A, B, C separately).

Significance threshold: **q ≤ 0.05** for the corrected results; raw p-values reported alongside for transparency.

## 3. Confirmatory hypotheses

Each hypothesis names: (a) the population it applies to, (b) the metric, (c) the test, (d) the rejection criterion.

### H1 — E1 + full system, clean lab

> On `custom8`, `ql_true` mean `goal_rate` is **at least as high as** `ql_false`.

- Test: paired bootstrap on `goal_rate` over 5 seeds, one-sided ( H_A: μ_diff ≥ 0 ).
- Pre-registered prediction: 95 % CI of the paired difference is **non-negative**, i.e. lower bound ≥ 0.
- Falsified if: CI strictly below zero (i.e. `ql_true` is significantly worse).
- This is the headline ordering the project is built to recover.

### H2 — E2 PBRS speeds up learning

> With PBRS on, the mean **episodes-to-first-goal** (per the existing `first_goal_stereotypes_*` CSV) is lower than with PBRS off, on **every profile**.

- Test: paired Wilcoxon over 3 seeds × 7 profiles = 21 paired observations, one-sided ( H_A: episodes_PBRS < episodes_noPBRS ).
- Pre-registered prediction: q ≤ 0.05.
- Falsified if: q > 0.05 or median difference ≥ 0.
- Uses the data from the **noPBRS ablation** vs the **main run**.

### H3 — E3 adaptive trust avoids prior collapse on wrong-ontology labs

> On weakness labs `{custom2, custom3, custom4, custom5}`, `ql_true` mean `goal_rate` is **not significantly worse than** `ql_false`.

- Test: per-profile paired bootstrap on `goal_rate` over 5 seeds. Required: 95 % CI of `ql_true − ql_false` includes 0 **or** is strictly positive, for **every** profile in the confirmatory set `{custom2, custom3, custom4, custom5}`.
- Pre-registered prediction: zero profiles in this set show a CI strictly below zero.
- Falsified if: at least one profile in `{custom2, custom3, custom4, custom5}` has `ql_true` strictly below `ql_false` (CI does not include zero).
- This is the safety claim: ontology priors do not hurt when wrong.
- **Amendment 2026-06-03 (audit Step 5, S5-6 / S5-7):** `custom7` is **demoted to exploratory** because W6 mutates only `ZnTemp` and the QLearner reward function uses no temperature term ([src/env/tools/QLearner.java](src/env/tools/QLearner.java) `computeZoneReward`), so W6 has **zero channel into `goal_rate`** — it is a null test by construction. `custom6` is **demoted to exploratory and the expectation is parity, not recovery**, because W5 (Partition23 toggles every 5 ticks) makes the MDP non-Markov from the agent's POV — the partition state is not in the observation vector and the toggle period (5) is shorter than the bench horizon (20), so neither QL variant can learn the dynamics. BH correction is applied across the reduced confirmatory set (4 profiles, not 6).

### H4 — Adaptive trust is **necessary** for H3 (Ablation B)

> Without adaptive trust (`adaptive_trust = false`), `ql_true` is significantly **worse** than `ql_false` on **at least one** of `custom2..custom7`.

- Test: per-profile paired bootstrap on `goal_rate`, ablation-B data (3 seeds). Look for any profile where the CI of `ql_true − ql_false` is strictly below zero (q ≤ 0.05 after BH correction across the 6 profiles).
- Pre-registered prediction: ≥ 1 profile shows the regression.
- Falsified if: zero profiles show the regression (in which case adaptive trust is empirically redundant, even if theoretically motivated).

### H5 — Sanity: zero prior collapses ql_true onto ql_false (Ablation C)

> With `stereo_prior_scale = 0.0`, `ql_true` and `ql_false` are **statistically indistinguishable** on every (profile, metric) cell.

- Test: per-(profile, metric) paired bootstrap, ablation-C data (3 seeds). Required: 0 cells of 35 (7 × 5) reject the null at q ≤ 0.05.
- Pre-registered prediction: 0 cells reject.
- Falsified if: ≥ 1 cell rejects (which would indicate a hidden code-path divergence between `ql_true` and `ql_false`, independent of the prior).
- This is a **code-integrity** check, not a research claim.

## 4. Decisions on outcomes

| Outcome of H1 | Outcome of H3 | Paper framing |
|---|---|---|
| Confirmed | Confirmed | "Stereotypes help when calibrated and never hurt." (positive) |
| Confirmed | Falsified  | "Stereotypes help on the clean lab; adaptive trust is insufficient on labs X, Y." (mixed; investigate) |
| Falsified | Confirmed | "A safe recipe for ontology priors in RL: indistinguishable from `ql_false` everywhere." (defensive) |
| Falsified | Falsified  | "Stereotype priors as currently formalised are not net-positive on this domain." (honest negative) |

All four outcomes are publishable. The choice of framing follows the actual numbers, not author preference.

## 5. Exploratory analyses (acknowledged, not pre-registered)

The following will be reported in the paper but **labelled exploratory**:

- Cross-profile learning curves with bootstrap confidence bands (`analysis/learning_curves.py`).
- Weakness-fire heatmap (`analysis/weakness_per_lab.py`) normalised per seed.
- Per-zone calibration trajectories (`actionCalSum / actionCalN` over training time), if logged.
- Any interaction effects between `stereo_prior_scale` and `adaptive_trust_floor` discovered post-hoc.

## 6. Deviation policy

If during analysis we discover that a pre-registered test is **technically inappropriate** (e.g. severe non-normality, ties in Wilcoxon), the deviation will be:

1. Reported in a "Deviations" subsection of the paper's Results.
2. Replaced by a clearly justified alternative test.
3. The original pre-registered result reported alongside, so reviewers can audit.

We will **not** silently swap tests to chase significance.

### 6.1 Registered deviations (post-hoc, audit Step 0, 2026-06-03)

The Step 0 sanity audit (replicability + H5 ablation) surfaced two source-code defects
that would have invalidated any downstream paired-bootstrap inference. Both were fixed
**before** the next paper sweep produces aggregated CI outputs. Recording them here per
§6 so the thesis Results section can refer back.

- **S0-3 — `QLearner.initWithStereotypes()` ignored `STEREO_PRIOR_SCALE`.**
  File: `src/env/tools/QLearner.java`, lines ~267-283. The original initialiser unconditionally
  injected stereotype-derived Q-values whenever `useStereotypes = true`, even when
  `stereo.priorScale = 0.0`. This meant the H5 ablation (Ablation C, zero prior collapses
  `ql_true` onto `ql_false`) was **structurally untestable** in all prior runs: setting
  scale=0 had no effect on initial Q. Fix adds a three-branch dispatch:
  `useStereotypes && scale > 0` → stereotype init; `useStereotypes && scale == 0` → zero-fill
  (H5 ablation path); `!useStereotypes` → zero-fill. Marker comment `// S0-3 (audit Finding 6/7)`.
  Impact on prior results: ablation-C cells in any pre-fix summary table are not interpretable;
  H1/H3/H4 main-sweep cells are unaffected (they run at scale=5.0, in which branch behaviour
  is unchanged).

- **S0-4 — `runFullSweep` Gradle task did not forward `-Plearning.*` properties to the
  benchmark JVM.** File: `build.gradle`, lines ~232-252. The project-level
  `tasks.withType(JavaExec).configureEach { doFirst { ... systemProperty ... } }` block
  forwards `_httpKeys` (which includes `learning.*`) to *registered* JavaExec tasks
  (`taskQl`, `taskBench`). `runFullSweep`'s inner `project.javaexec { ... }` closure is **not**
  a registered task and was not covered, so any `-Plearning.stereo_prior_scale=…`,
  `-Pstereo.priorScale=…`, `-Preward.shaping=…`, `-Pstereo.adaptiveTrust*=…`,
  `-Preward.clip=…` passed on the CLI silently fell on the floor at benchmark time.
  Fix iterates `_httpKeys` inside the `runFullSweep` `javaexec` closure with the same
  guard pattern. Marker comment `// S0-4 (audit Finding 5)`. Impact on prior results:
  benchmark-phase metrics in any pre-fix paper sweep were computed with the JVM's compiled
  defaults, not the requested CLI overrides. Training-phase metrics are unaffected (training
  uses `taskQl`, which was always covered).

### 6.2 Step 0 replicability gate — methodology deviation

The pre-registration implicitly assumed bit-identical reproducibility for a fixed seed.
Probe B (run same seed twice, diff metric CSVs) returned non-zero diffs because:
(a) the Node-RED simulator (`simulator/simulator_flow_custom*.json`) calls `Math.random()`
per tick for sunshine perturbation and per scenario reset — unseeded, JS engine-local;
(b) JVM/CArtAgO timing jitter at tick=0.2s in paper mode can reorder agent perception
events relative to environment ticks for boundary cases.

Bit-identical Probe B is therefore physically impossible without rewriting the simulator
RNG. Step 0 was completed under a relaxed protocol:

- **Probe B was replaced by a degenerate-case dev-mode check.** Six dev-mode runs of `custom8`
  (3 within-seed reps at seed=7, 3 between-seed runs at seeds=1,2,3) produced **bit-identical**
  `mean(GoalReached)` for both `ql_true` and `ql_false` arms (artifacts:
  `tmp_step0_optB/goal_rates.txt`, `tmp_step0_optB/verdict.txt`, dated 2026-06-03). This
  establishes that the JaCaMo→Gradle→QLearner stack is deterministic in dev mode and that
  the Node-RED non-determinism is amplitude-bounded at 50-episode/0.05s-tick scale.
- **σ_within / σ_between gate (Option β) was not evaluated at paper scale.** The dev-mode
  attempt collapsed to σ_within = σ_between = 0 (degenerate, gate undefined). Mining
  sweep #13 archives for σ_between was not possible: the per-seed paper-mode benchmark
  CSVs were overwritten by consolidation and the schema carries no `RunSeed` column. A
  paper-mode re-run to establish σ_within (~9 h) was deferred.
- **H5 (Ablation C) was not run prior to this commit.** The Probe A v3 script
  (`run_step0_probeA_v3.ps1`) is committed and will produce the H5 verdict in a future
  paper sweep with `-SigmaWithinTol` set from the paper-mode σ_within when measured.
- **Consequence for confirmatory inference.** All paired-bootstrap CIs in the upcoming sweep
  are reported with the caveat that paper-mode replicability is gated empirically by
  *between-seed* variance only (the bootstrap distribution itself), not by an independent
  σ_within measurement. Any CI whose half-width is comparable to plausible timing noise
  (~0.02-0.05 in `goal_rate` units, estimated from dev-mode bounds) should be flagged
  exploratory rather than confirmatory.

Artifacts: see `memories/repo/audit-step-0-sanity.md` (§§1-12) for the full audit trail
including the falsified Probe B variants, source diffs for S0-3/S0-4, and the
script-syntax verification log.

### 6.3 Registered deviations (post-hoc, audit Step 1 + 1b, 2026-06-03)

The Step 1 (knowledge-graph) audit identified the Cecconi-style Mediates vs. Causes
distinction as modelled-but-discarded by the QLearner consumer: every stereotype prior
was applied as an unconditional Causes-shaped term, so the IV gate that the ontology
encodes for `BlindStereotype` (sunshine ≥ rank 1) never fired at prior-application time.
This produced a permanent positive bias on blind actions even at `Sunshine = 0`, where
the simulator delivers no light through blinds. The fixes below restore the
prior path to operational fidelity with the ontology contract and remove a body of
declared-but-dead vocabulary. All fixes were applied under `gradlew build` + 25/25
unit-test pass (commit anchor in `memories/repo/audit-step-1-knowledge-graph.md` §
"Step 2 — implementation status").

- **KG-1 — Removed unconditional `elem:increases elem:luminiscence` claim from
  `ws:pm_daylight_ingress`.** File: `src/resources/lab-ontology.ttl` (BlindStereotype
  mechanism block). Blinds now declare only the Mediates structure (IV =
  `ws:outdoorIlluminance`, MV = `ws:blindApertureRatio`, DV = `elem:luminiscence`).
  Forces the QLearner to compute the blind sign from the IV gate instead of from the
  Causes shortcut.
- **KG-2 — `StereotypeReasoner` implements Mediates (Option B, learning-first).**
  File: `src/env/tools/StereotypeReasoner.java`. New `ActionInfo.ivMinRank` field
  populated from SPARQL; `QLearner.greedyAction` suppresses the blind prior when the
  current sunshine rank is below `ivMinRank`. Operational counterpart of KG-1.
- **KG-3 — Declared `elem:increases` as `owl:ObjectProperty`** with comment restricting
  it to Causes mechanisms. File: `src/resources/lab-ontology.ttl` (vocabulary-bridges
  block). Documents the project-local extension to Ramanathan's vocabulary.
- **KG-4 — Materialised `ws:rankBound_1/2/3` triples** on `ws:sensedIlluminance`
  ({50, 100, 300}) and `ws:sensedOutdoorIlluminance` ({50, 200, 600}). File:
  `src/resources/lab-ontology.ttl`. Removes the runtime-calibration drift risk in which
  fallback bounds were seed-dependent and bench rank evaluation could silently change
  per replica.
- **KG-5 — Deleted dead `elem:ResponseDynamic`/`elem:hasResponseDynamic` block.** File:
  `src/resources/lab-ontology.ttl`. The W3-delayed-response override mechanism existed
  only in TTL with zero Java consumers; deletion replaced with an audit-trail comment
  so future W3 work re-introduces both layers together.
- **KG-7 — Added `lab:Spotlight brick:feeds {Z1,Z2} sensors`** and analogous arcs for
  `lab:SpotlightCD` → {Z3, Z4}. File: `src/resources/lab-ontology-custom2.ttl`. Lets the
  bench-side `CROSS_ZONE_FEEDS_QUERY` enumerate shared luminaires symmetrically; aids
  W5 topology audits.
- **KG-8 — Removed duplicate `ws:zoneIndex` declaration** from `wot-mappings.ttl` (the
  canonical declaration lives in `lab-ontology.ttl`).
- **KG-9 — Materialised `ws:pm_daylight_ingress ws:ivMinRank 1`** triple. File:
  `src/resources/lab-ontology.ttl`. Makes the IV gate a reviewable design constant
  rather than a Java-side magic number; supports KG-2.

**Deferred (not yet applied):**

- **KG-6 — `RadiatorStereotype`/`TemperatureSensorStereotype` deletion** is reversible
  but destructive of declared-but-inert vocabulary. Held for explicit confirmation; no
  runtime impact (DV illuminance filter already excludes these from action discovery).

**Impact on prior results.** Any benchmark output produced **before** 2026-06-03 used
the unconditional Causes prior for blinds. The H1 inversion observed in pre-fix
`benchmark_results_ql_true.csv` on `custom8` (`ql_true − ql_false = −0.073`, q = 0.000)
was computed under that defect. Re-runs from this commit onward are the canonical
reference for H1/H3 confirmatory inference; pre-fix CIs are reported in the paper as
"pre-prior-fix baseline, exploratory" alongside the post-fix confirmatory cells.

### 6.4 Registered deviations (post-hoc, audit Step 1b, 2026-06-03)

The Step 1b reachability audit ([audit-step-1b-bench-reachability.md](../memories/repo/audit-step-1b-bench-reachability.md))
proved 100 % of the 28 held-out scenarios in `benchmark/scenarios_custom8.json` are
reachable in ≤ 8 actuator toggles under `exec_max_steps(20)` via a single sun-invariant
target vector. The positive-control lab `custom9` skeletoned in §8 of that memo was
therefore **not built**; the ≥80 % reachability gate it would unlock is already
satisfied.

- **B-1 — Removed dead `Z[1-4]Level` initial values from
  `benchmark/scenarios_custom8.json`.** Simulator `compute_levels`
  (`simulator/simulator_flow_custom8.json` L171) recomputes per-zone illuminance from
  scratch every 200 ms tick from actuator booleans + Sunshine; preset levels never
  reached the agent. Added `_doc` array as first list element documenting Sunshine
  pinning (`SunshinePinned = true` via L252 of the flow), the field removal, and the
  universal target vector. `LabEnvironment.extractScenarioKV` ignores non-primitive
  JSON values, so `_doc` is read as documentation only.
- **B-2 (informational) — `exec_max_steps(20)` retained.** Step 1b §6 S1b-3 proposed an
  optional one-off raise to 30 as a diagnostic; not applied because permanently
  changing the budget would invalidate cross-comparison with all prior
  `benchmark_results_*.csv`. Any future diagnostic re-sweep at budget 30 must be
  flagged exploratory and reported alongside the budget-20 reference cells.

**Impact on prior results.** None. The cleanup removes dead inputs and adds in-file
documentation; the schema accepted by `setScenarioLabState` is unchanged for every
field consumed at runtime.

---

### 6.5 Registered deviations (post-hoc, audit Step 6, statistics layer)

Audit Step 6 reviewed `analysis/sweep_report.py`, `analysis/learning_curves.py`,
and `analysis/midterm_results.py`. Two stat-layer choices were not explicit in §2/§3
of this document and are recorded here so the paper can cite them as registered.

- **D6-1 — Paired-bootstrap pairing is by training seed only (pre-S0-4 sweeps).**
  `_collect_per_seed_values` (sweep_report.py) pairs cells by the seed in the
  `results_seed<N>/` directory name, which is the *training* seed. In sweeps that
  predate the S0-4 fix to `runFullSweep`, the bench JVM ran with a fixed
  `RUN_SEED=0`, so the resulting paired differences capture *training-seed Q-table
  variance only*, not bench-side stochasticity. Sweeps run after the S0-4 fix
  propagate the training seed to the bench JVM and so capture both components.
  The paper must report which sweep version produced the headline numbers and, if
  using pre-S0-4 data, characterise the missing variance with at least one
  post-S0-4 comparison sweep. Files affected: `analysis/sweep_report.py`
  (`paired_tests`, `_paired_bootstrap_diff`), `analysis/out/paired_tests.csv`
  column `seeds_paired`.

- **D6-2 — Two-sided bootstrap p-value uses anchored-on-sign convention.**
  `_paired_bootstrap_diff` returns
  `p_bootstrap = 2 · P(boots ≤ 0)` when `mean_diff ≥ 0`, else
  `2 · P(boots ≥ 0)`, rather than `2 · min(P(boots ≤ 0), P(boots ≥ 0))`. The two
  agree when the observed mean has the same sign as the bootstrap median, which
  is the regime for every confirmatory pre-reg cell, but can disagree near zero.
  To make pre-reg §3 H1/H2 one-sided tests directly available without re-resampling,
  `paired_tests.csv` now also carries `p_bootstrap_one_sided_positive`
  (= `P(boots ≤ 0)`, evidence against H_A: μ_diff > 0) and
  `p_bootstrap_one_sided_negative` (= `P(boots ≥ 0)`). H1 (PBRS-on reduces
  episodes-to-first-goal) is read from `p_bootstrap_one_sided_negative`; the
  paper should cite the one-sided column for H1/H2 and the two-sided column for
  H3/H4/H5.

- **D6-3 — BH families are bucketed by `family` column, not globally.**
  `paired_tests.csv` now carries a `family` column with two values:
  `confirmatory` (`ql_true` vs `ql_false`, `ql_true` vs `rule_based`) and
  `exploratory` (`ql_false` vs `rule_based`). `_bh_qvalues` is applied
  **independently** to each family. The confirmatory denominator is therefore
  `m = 7 profiles × 5 metrics × 2 mode-pairs = 70` exactly as committed in §2
  step 5, and the exploratory `ql_false vs rule_based` comparison cannot inflate
  m for the confirmatory tests. The `bh_family_m` column records the denominator
  actually used per row.

- **D6-4 — H2 (episodes-to-first-goal, PBRS on vs off) aggregator added.**
  `analysis/sweep_report.py::aggregate_first_goal()` reads the existing
  `first_goal_stereotypes_<bool>_<profile>.csv` artefacts and joins by
  (profile, seed) across the main sweep root (PBRS on) and a sibling root
  supplied via `--first-goal-root` (PBRS off). It emits `first_goal_table.csv`
  (per-profile, per-condition mean + bootstrap CI) and `first_goal_wilcoxon.csv`
  (per-profile paired Wilcoxon, BH across 7 profiles). H2 was uncomputable from
  `analysis/out/` before this change. The PBRS-off ablation sweep producing the
  `--first-goal-root` input is registered as **Ablation A**; the orchestration
  script is not yet committed and must be added before the H2 verdict is cited.

- **D6-5 — Output routing isolates stat families per ablation.**
  `--family-tag <name>` routes every artefact to `analysis/out/<name>/`.
  Reserved tags: `main` (headline sweep), `ablation_a` (PBRS off, H2),
  `ablation_b` (no stereotypes, H4), `ablation_c` (random Q-init, H5).
  Mixing ablations under the same `analysis/out/` root is now an explicit error
  of the operator, not a silent overwrite.

- **D6-6 — `analysis/midterm_results.py` is slide-only.** Outputs are routed to
  `analysis/out/slides/`. The script reads single-seed CSVs from the project
  root (legacy layout) and is retained for slide regeneration only. Thesis
  figures come from `learning_curves.py` (multi-seed) and `sweep_report.py
  --seeds-mode` (paired tests with BH q-values).

**Impact on prior results.** None for `summary_table_ci.csv` cell means or CIs.
`paired_tests.csv` gains new columns (`family`, `seeds_paired`,
`p_bootstrap_one_sided_positive`, `p_bootstrap_one_sided_negative`,
`q_bootstrap_bh`, `bh_family_m`) and the BH q-value column is now per-family;
any previously cited `q_bootstrap_bh` value computed across the union of
confirmatory + exploratory pairs must be recomputed.

---

*Commit this file before the first `summary_table_ci.csv` is produced by CI. `git log docs/pre_registration.md` must show a timestamp earlier than any commit on the `results` branch containing paper-sweep aggregated outputs.*
