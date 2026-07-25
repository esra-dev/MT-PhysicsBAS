# Phase-1b pilot & power-analysis protocol

Status: **BINDING — committed before any pilot seed is dispatched.**
Branch: `phase1b-labs-2026-07`. Companion code: `analysis/phase1b_power.py`
(frozen procedure), `analysis/phase1b_report.py --pilot-diagnostics`
(allow-listed pilot reader).

## 1. Pilot block

- Pilot-only seed block: **{1001, 1002, …, 1010}**, permanently disjoint from
  every confirmatory seed. All Phase-1b profiles × all four `phase1b_v2_*`
  arms.
- Every pilot artifact is stored under `phase1b_pilot/` and labelled
  `PILOT_ONLY`. Pilot data are never pooled with confirmatory results.
- Pilot inspection is limited to: protocol failures, runtime and artifact
  size, per-cell censoring fractions, metric degeneracy (zero variance),
  and the centred-residual variance inputs required by §3. The pilot summary
  tool (`phase1b_report.py --pilot-diagnostics`) emits ONLY this allow-listed
  report and refuses to produce arm-labelled means, effect directions,
  p-values, comparative learning curves, or directional plots.
- The pilot may NOT be used to select labs, family members, hypotheses,
  predicted directions, coefficients, or learner hyperparameters. Any
  implementation, physics, scenario, metric, or test change after the pilot
  invalidates its power inputs; the protocol must then be amended and a new
  disjoint pilot block used.

## 2. Smallest effect sizes of interest (SESOI, frozen)

Scale anchor A = 3 × the corrected Phase-1 v2 lab2 net KG effect on
`auc_goal` (+0.0037), i.e. **A = 0.0111** — the smallest per-lab `auc_goal`
advantage we consider thesis-relevant for a *dedicated* knowledge-necessity
lab (a channel that cannot beat 3× the incidental lab2 effect on a lab built
for it is not worth a chapter claim). Pooled-scale anchors use the pilot's
arm-blind POOLED mean of a metric (pooling all arms; no arm labels), which is
on the §1 allow-list.

| Member | Statistic (per seed) | SESOI | Predicted direction |
|---|---|---|---|
| M1 `labrel_stateless_frozen_slope` | OLS slope over K∈{0,4,8,16} of (frozen−baseline) `auc_goal` | A/16 per decoy = **0.000694/decoy** (advantage ≥ A at K=16) | positive |
| M2 `labrel_incremental_slope` | OLS slope over K of (extended−frozen) `auc_goal` | **0.000694/decoy** | positive |
| M3 `labrel8s_fragmentation_did` | DiD of (frozen−baseline) `auc_goal`, labrel8s vs labrel8 | **0.0111** (= A) | positive (KG advantage larger under fragmentation) |
| M4 `labband_extended_vs_frozen_auc` | (extended−frozen) `auc_goal` on labband | **0.0111** (= A) | positive |
| M5 `labband_extended_vs_baseline_dev` | (extended−baseline) mean `CumIlluminanceDeviation` | **−10% of the pooled labband deviation mean** | negative |
| M6 `chain3_frozen_vs_baseline_rmst` | (frozen−baseline) RMST at horizon H (or goal-rate if §4 triggers) | **−5% of H** (RMST) / **+0.10** (goal rate) | negative (RMST) / positive (goal rate) |

## 3. Frozen power procedure

Candidate paired confirmatory sample sizes: **N ∈ {20, 30, 40}**.

For each member m and each candidate N:
1. Estimate the per-seed statistic's SD `s_m` from the pilot as the SD of the
   **centred paired residuals** (each cell's own mean subtracted before any
   cross-arm combination, so no effect direction or arm-labelled mean is
   visible; computed by `--pilot-diagnostics`).
2. Simulate 10,000 replicates (fixed RNG seed 0x1B5EED) of the FULL
   six-member family: member m draws N per-seed statistics from
   Normal(SESOI_m, s_m²) — the effect is FIXED to the SESOI, never to any
   observed pilot mean. Within the simulation each replicate's p-value uses
   the frozen CLT approximation of the exact paired sign-flip randomisation
   test, p = 2·Φ(−|Σd| / √(Σd²)) (`analysis/phase1b_power.py`); the
   CONFIRMATORY analysis itself uses the exact machinery
   (`analysis/exact_paired_stats.paired_signflip_p`) — the approximation is
   for power simulation tractability only and is frozen here.
3. Apply the frozen six-member BH procedure at q = 0.05 to each replicate.
4. Power_m(N) = fraction of replicates in which member m is BH-rejected in
   the predicted direction.

**Selection rule (frozen):** choose the smallest N ∈ {20, 30, 40} with
Power_m(N) ≥ 0.80 for every retained member. If no N ≤ 40 achieves 0.80 for
some member, that member is either (a) omitted from the confirmatory family
before registration, with the omission and its reason recorded, or (b)
prospectively relabelled exploratory in the registration. A low-powered null
is never reported as evidence of no effect. The confirmatory family size m
used by BH in the analysis equals the number of retained confirmatory
members and is frozen in the registration.

Censoring inputs: the pilot censoring fractions feed the §4 rule check and
the RMST simulation truncation; they are not effect estimates.

## 4. Frozen censoring rule (M6 endpoint switch)

If, pooled across pilot (and later confirmatory) seeds, **more than 25% of
(scenario × seed) first-success cells are censored in either arm** of
lab4chain3, member M6's endpoint switches from RMST to benchmark goal rate.
The emitted family CSV records the fractions and the endpoint actually used.
Ordinary uncensored first-goal means are never primary under substantial
censoring. (Rule implemented in `analysis/phase1b_report.py`; unit-tested for
no-, one-arm-, and all-censored cases.)

## 5. Registration gate

The confirmatory registration (frozen N, seeds 1..N, modes, coefficients,
endpoints, family, dispatch list, archive paths) is committed only AFTER this
power analysis has run on the pilot diagnostics and BEFORE any confirmatory
seed is dispatched. Pilot seeds are rejected by the confirmatory workflow
gate; duplicate mode/seed/profile tuples are rejected.
