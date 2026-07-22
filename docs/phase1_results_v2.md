# Phase 1 corrected results — protocol v2

Status: **current thesis evidence**. These results replace every protocol-v1 Phase 1
number, including the pooled-20 headline, `+53.30 mean_first_goal`, legacy energy,
redundancy-control, baseline, and PBRS conclusions.

## Validity gates

All four workflows completed successfully on registered commit
`d3442385c91fbe11a5714bd15ca83add8f81f115`: arm C run `29848584965`, redundancy-only
run `29848587274`, baseline run `29848589682`, and PBRS-only run `29848592010`. Each
archive contains 120 training cells and 180 benchmark cells: labs 1–3, seeds 1–20, two
training labels, and three benchmark policies. Every training cell completed exactly
3,000 episodes under `phase1-v2` and `phase1-benchmark-v2`; the paired labels have zero
scenario-schedule mismatches and zero random fallbacks. Each run has 1,080 first-goal
scenario rows, including 440 terminal-at-start rows; none was censored in the realized
campaign. Source: `phase1_v2_corrected/analysis/phase1_v2_protocol_gate_summary.json`.

Every artifact-level SHA-256 inventory passes. Rebuilding the four per-mode analyses and
the registered family from the committed raw archives produces byte-identical canonical
numeric CSVs. Source: `phase1_v2_corrected/CAMPAIGN_MANIFEST.md` and the successful command
`python analysis/reproduce_phase1_v2.py phase1_v2_corrected`.

## Registered primary family

All differences below are paired `ql_true − ql_false` seed differences except member 3,
which is arm C's paired difference minus redundancy-only's paired difference. Positive
`auc_goal` is favorable; positive first-goal presentations or cycling is unfavorable.
Bootstrap intervals estimate the mean; p-values are exact two-sided paired sign-flip tests;
q-values use the frozen Benjamini–Hochberg family of five. The exact sign test is reported
separately because it discards magnitude. Source:
`phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv`.

| Member | Mean difference | Median | 95% bootstrap CI | Sign-flip p | Exact sign p | BH q | Paired rank-biserial | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1. Arm-C lab2 `auc_goal` | +0.003700 | +0.003500 | [+0.002700, +0.004917] | 1.907×10⁻⁶ | 1.907×10⁻⁶ | 9.537×10⁻⁶ | +1.000 | Supported: small KG-arm training-success advantage. |
| 2. Redundancy lab2 `auc_goal` | +0.002583 | +0.002000 | [+0.001500, +0.003833] | 1.030×10⁻⁴ | 0.002577 | 1.717×10⁻⁴ | +0.914 | Supported: cheap redundancy shaping reproduces most of the arm-C mean. |
| 3. Arm C minus redundancy, lab2 | +0.001117 | +0.001000 | [+0.000767, +0.001467] | 3.052×10⁻⁵ | 3.052×10⁻⁵ | 7.629×10⁻⁵ | +1.000 | Supported: arm C retains a smaller advantage beyond redundancy. |
| 4. Arm-C lab3 `mean_first_goal_presentations` | +0.110 | 0.000 | [−0.060, +0.305] | 0.3044 | 1.0000 | 0.3044 | +0.257 | Not supported: no first-goal regression or benefit. |
| 5. Arm-C lab3 `avg_cycling` | +0.07375 | +0.08125 | [−0.02313, +0.17375] | 0.1720 | 0.6476 | 0.2150 | +0.379 | Not supported: no cycling difference. |

The frozen decomposition ratio is `0.0025833 / 0.0037000 = 0.6982`. That exceeds the
predeclared two-thirds threshold, so the binding category is **“redundancy reproduces most
of arm C's lab2 mean effect.”** Member 3 nevertheless shows that the residual arm-C effect
is positive and nonzero in this simulator. The honest conclusion is therefore “mostly
cheap redundancy information, with a smaller additional bundled KG-prior effect,” not
“the ontology alone caused the entire advantage.” Source:
`phase1_v2_corrected/analysis/registered/phase1_v2_decomposition.json`.

## Registered controls

The baseline and PBRS-only label controls are exactly equal for all 12 learning contrasts
and all 21 corrected benchmark contrasts in each mode. Their only nonzero differences are
the three explicitly obsolete `avg_legacy_wallclock_energy` rows per mode; all six legacy
intervals include zero. This is direct evidence that label/wiring asymmetry is absent in
the corrected metrics and direct evidence that the old wall-clock accumulator remains
timing-noisy even when policies are identical. It is not used as corrected energy evidence.
Source: runs `29848589682` and `29848592010`, consolidated in
`phase1_v2_corrected/analysis/phase1_v2_controls_and_descriptives.csv`.

Lab1 is a saturated null control: arm C and redundancy-only both have zero `auc_goal` and
zero first-goal-presentation differences. Source: runs `29848584965` and `29848587274`,
`analysis/out/learning_speed_tests.csv`, lab1 rows.

## Registered descriptives

These outcomes were registered as controls or descriptives, not additional confirmatory
discoveries. Their intervals and within-file q-values describe the realized campaign but
do not enlarge the frozen family of five.

Arm C on lab2 is consistently favorable at benchmark: goal rate `+0.04875` (95% CI
`[+0.02750,+0.07250]`), steps `−1.33375` (`[−1.73752,−0.96250]`), deviation `−3.67313`
(`[-4.78189,−2.62683]`), deterministic policy energy `−1.28000`
(`[−1.68312,−0.91623]`), wasted actions `−0.95063`, cycling `−0.38312`, and total redundant
actions `−1.33375`. Its first success is also `0.3818` scenario presentations earlier on
average. Source: run `29848584965`, `analysis/out/paired_tests.csv` and
`analysis/out/learning_speed_tests.csv`.

Arm C on lab3 has a small adverse full-horizon `auc_goal` difference of `−0.002300`
(`[-0.003467,−0.001067]`; within-mode q `0.00699`). This does **not** contradict the
registered first-goal null: one measures success across all 3,000 episodes, while the other
measures the first successful presentation of each declared scenario. Final benchmark goal
rate is `−0.01375` (`[-0.03375,+0.006875]`), cycling is the registered null above, and
redundant actions are `+0.3325` (`[-0.0631,+0.7256]`). Deterministic policy energy is an
unfavorable `+1.0744` policy-cost units (`[+0.5981,+1.5394]`; within-file q `0.00122`). This
energy result is credible as a deterministic trace metric but remains a registered
descriptive, uses arbitrary `1/2/0` actuator weights, and is not watt-hours. Source: run
`29848584965`, `analysis/out/learning_speed_tests.csv` and `analysis/out/paired_tests.csv`.

Redundancy-only on lab3 behaves differently from arm C: `auc_goal` is `+0.002400`, mean
first-goal presentations are `−0.140`, benchmark goal rate is `+0.020625`, and deterministic
policy energy is `−0.290` with an interval spanning zero. This contrast is descriptive but
shows plainly that the arm-C lab3 energy cost is not an inevitable consequence of merely
suppressing repeated actuator settings. Source: run `29848587274`, the same two analysis
tables.

## What Phase 1 now supports

Phase 1 supports a small lab2 learning advantage for the bundled KG-prior arm inside this
discrete simulator. About 70% of the mean advantage is reproduced by an ontology-free
redundancy rule, while a smaller residual arm-C advantage remains. It does not support the
old lab3 first-goal regression or the old cycling headline. It does reveal a small adverse
lab3 full-horizon training-success difference and a descriptive deterministic policy-energy
cost for arm C. None of these simulator results proves that RDF/SPARQL is the cheapest way
to represent the information or that a real building would benefit.

The analysis-execution deviations discovered after archive download are fully disclosed in
`docs/phase1_correction_analysis_deviation_2026-07-22.md`. Neither changed an input row,
registered formula, statistical family, or interpretation rule.
