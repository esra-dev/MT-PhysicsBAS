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

> On weakness labs `custom2..custom7`, `ql_true` mean `goal_rate` is **not significantly worse than** `ql_false`.

- Test: per-profile paired bootstrap on `goal_rate` over 5 seeds. Required: 95 % CI of `ql_true − ql_false` includes 0 **or** is strictly positive, for **every** profile in `custom2..custom7`.
- Pre-registered prediction: zero profiles in this set show a CI strictly below zero.
- Falsified if: at least one profile in `custom2..custom7` has `ql_true` strictly below `ql_false` (CI does not include zero).
- This is the safety claim: ontology priors do not hurt when wrong.

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

---

*Commit this file before the first `summary_table_ci.csv` is produced by CI. `git log docs/pre_registration.md` must show a timestamp earlier than any commit on the `results` branch containing paper-sweep aggregated outputs.*
