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

## Knowledge-ladder control arm: Brick structure without the Elementary layer

Registered in `docs/_audit/THESIS_STATE_REPORT.md`, Addendum 2026-11-10, before dispatch;
reported in Addendum 2026-11-13. Run `42834963612` (mode `phase1_v2_brick_only`, commit
`140906f2`) repeats arm C with one change: the knowledge arm's reasoner reads the WoT
contract, Brick topology, and SOSA/QUDT observation typing, and no Elementary mechanism
triple. The only Elementary construct that differs between the two arms in Phase 1 is the
independent-variable gate on the blinds ("opening a blind adds light only when the sun is
up"). The arms form a ladder: A0 tabula rasa, A1 redundancy only, A2 Brick structure, A3
full KG (arm C). A rung increment is the by-seed difference of two arms' paired
`ql_true − ql_false` effects.

### Validity of the fifth run

Run `42834963612` passes the same protocol gate as the four campaign runs: 120 training
cells, 180 benchmark cells, exactly 3,000 episodes per cell, zero scenario fallbacks, and
zero schedule mismatches. All 302 workflow jobs of run `42834963612` concluded successfully.
The downloaded artifact of run `42834963612` reproduces the digest recorded by GitHub, and
its 4,978-row inventory verifies without error. Source:
`phase1_v2_corrected/run_42834963612/ARCHIVE_MANIFEST.md`.

Treatment delivery is evidenced in `phase1_v2_corrected/run_42834963612/verification/`. The
initial Q-tables of the Brick arm and of arm C differ only on the two blind-activation
columns and only at sun rank 0: 256 cells on lab2 and 512 cells on lab3 in the combined
tables. In the Brick arm those columns do not depend on the sun rank. All 120 training job
logs of run `42834963612` report `knowledgeLayer=BRICK` and no other layer.

The two arms come from different commits, so their comparability was checked directly. In
all three labs and all 20 seeds, the tabula-rasa training cells of run `42834963612` are
byte-identical to those of run `29848584965` (episode metrics, initial and final Q-tables,
first-goal rows). The `ql_false` and `rule_based` benchmark files differ only in the
excluded wall-clock energy diagnostic. On lab1, which has no blinds, the knowledge-arm
training cells are byte-identical as well. Source:
`phase1_v2_corrected/run_42834963612/verification/cross_run_identity_vs_run_29848584965.json`.

### Registered ladder family

Both members are the Elementary increment A3 − A2 on `auc_goal`, paired by seed, n = 20.
Statistics are those of the primary family above; q-values use the frozen
Benjamini–Hochberg family of two. The pre-committed category is read from the 95% bootstrap
interval: above zero is `elementary_adds`, below zero is `elementary_costs`, otherwise
`null`. Source:
`phase1_v2_corrected/analysis/registered/phase1_v2_knowledge_ladder_family.csv`.

| Ladder member | Mean increment | Median | 95% bootstrap CI | Sign-flip p | Exact sign p | BH q | Paired rank-biserial | Registered category |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1. lab2 `auc_goal`, A3 − A2 | 0.000000 | 0.000000 | [0.000000, 0.000000] | 1.0000 | 1.0000 | 1.0000 | 0.000 | `null`: Brick structure reproduces arm C's lab2 effect. |
| 2. lab3 `auc_goal`, A3 − A2 | +0.003850 | +0.002667 | [+0.001533, +0.006683] | 0.004292 | 0.06357 | 0.008583 | +0.695 | `elementary_adds`: the gate adds training success beyond Brick structure. |

Ladder member 1 is an exact tie in every one of the 20 seeds. The Brick arm's own lab2
effect is `+0.003700` with interval `[+0.002700, +0.004917]`, the same as arm C, so the
descriptive Brick share of arm C's lab2 effect is `1.0`. The endpoint is saturated for both
knowledge arms: `ql_true` training success is `1.000000` in all 20 seeds of the Brick arm
and in all 20 seeds of arm C, against `0.996300` for tabula rasa. Ladder member 1 therefore
shows that the Elementary gate was not needed to reach the lab2 ceiling; it cannot show
whether the gate would help on a harder lab2 endpoint. Source:
`phase1_v2_corrected/analysis/registered/phase1_v2_knowledge_ladder.json`.

Ladder member 2 has 14 positive seeds, one tie, and five negative seeds. Its reading needs
the absolute levels: on lab3 both knowledge arms train worse than tabula rasa. Mean
training success is `0.990917` for the Brick arm, `0.994767` for arm C, and `0.997067` for
tabula rasa, which corresponds to 27.25, 15.70, and 8.80 failed episodes out of 3,000. The
Elementary gate recovers part of a loss that the structural priors cause; it does not make
the knowledge arm better than no knowledge on lab3.

### Registered ladder descriptives

These rows carry no threshold. Source:
`phase1_v2_corrected/analysis/registered/phase1_v2_knowledge_ladder_descriptives.csv`.

| Ladder descriptive (paired, n = 20) | lab2 | lab3 |
|---|---:|---:|
| A1 redundancy `auc_goal` effect | +0.002583 | +0.002400 |
| A2 Brick `auc_goal` effect | +0.003700 | −0.006150 |
| A3 full-KG `auc_goal` effect | +0.003700 | −0.002300 |
| Rung A2 − A1 `auc_goal` | +0.001117 | −0.008550 |
| A2 Brick benchmark goal rate | +0.04875 | −0.02875 |
| A2 Brick benchmark policy energy | −1.22125 | +1.67000 |
| A2 Brick benchmark cycling | −0.36000 | +1.17500 |
| Rung A3 − A2 benchmark goal rate | 0.00000 | +0.01500 |
| Rung A3 − A2 benchmark policy energy | −0.05875 | −0.59562 |
| Rung A3 − A2 benchmark cycling | −0.02312 | −1.10125 |
| Rung A3 − A2 benchmark wasted steps | 0.00000 | +0.72750 |

On lab2 the rung A2 − A1 equals registered member 3 of the primary family (`+0.001117`,
interval `[+0.000767, +0.001467]`): the part of arm C's lab2 advantage that redundancy does
not reproduce is carried entirely by Brick structure. No lab2 benchmark increment of the
rung A3 − A2 has an interval that excludes zero.

On lab3 the rung A2 − A1 is `−0.008550` with interval `[−0.011317, −0.006233]`, negative in
every seed that differs: adding structural priors to the redundancy rule lowers training
success. The registered question whether the Brick arm reproduces arm C's lab3
policy-energy cost has the answer yes, and more: the Brick arm's cost is `+1.67000`
(interval `[+1.24186, +2.08564]`) against arm C's `+1.07438`. The cost is therefore not
attributable to the Elementary gate; the gate lowers it by `0.59562` (interval
`[−0.90500, −0.26437]`). The gate also removes most of the Brick arm's extra actuator
cycling (`−1.10125`, interval `[−1.26000, −0.90750]`) and raises wasted steps (`+0.72750`,
interval `[+0.47062, +0.98189]`). The lab3 benchmark goal-rate increment `+0.01500` has an
interval that spans zero. All lab1 ladder rows are exactly zero, as registered for the
saturated control.

### Deviations and limits of the ladder arm

1. The registered delivery signature read "no −50 cell on any blind-ON column at sun rank
   0". No knowledge arm can satisfy that wording, because the registry-derived redundancy
   rule writes the same value when a blind is already open. The signature was restated
   after data contact as conditional on the blind being closed; the restated signature
   holds in every table of run `42834963612`, and the literal count is reported beside it
   in `phase1_v2_corrected/run_42834963612/verification/elementary_layer_off_proof.json`.
2. The registered log line `knowledge layer = BRICK` is written by a logger that the job
   log does not capture. The learner's progress line carries the same information and is
   the evidence used for run `42834963612`.
3. The analysis ran from a tree that merges the registration commit into the later main
   branch. The registered analysis files (`analysis/phase1_v2_knowledge_ladder.py`,
   `analysis/sweep_report.py`, `analysis/phase1_v2_registered_family.py`) are byte-identical
   to their versions at the registration commit, and the ladder script ran once.
4. The registration was written with the four-arm results of this report known. Only the
   Brick arm's own effect and the two increments were unseen.
5. The increment isolates one Elementary construct, the blind gate. It says nothing about
   coupling classes, power gates, or cost annotations, which Phase 1 does not consume.

## What Phase 1 now supports

Phase 1 supports a small lab2 learning advantage for the bundled KG-prior arm inside this
discrete simulator. About 70% of the mean advantage is reproduced by an ontology-free
redundancy rule, while a smaller residual arm-C advantage remains. The knowledge-ladder arm
shows that this residual is carried by Brick structure: on lab2 the Elementary layer adds
no training success beyond it, at an endpoint that both knowledge arms saturate. On lab3
the Elementary gate adds training success beyond Brick structure, while both knowledge arms
remain below tabula rasa. Phase 1 does not support the old lab3 first-goal regression or
the old cycling headline. It does reveal a small adverse lab3 full-horizon training-success
difference and a descriptive deterministic policy-energy cost for arm C, and the ladder arm
attributes that cost to the structural priors, not to the Elementary gate. Phase 1
therefore does not show that physics knowledge makes clean learning faster than no
knowledge: on lab2 structure alone reaches the ceiling, and on lab3 the gate only reduces a
loss relative to tabula rasa. None of these simulator results proves that RDF/SPARQL is the
cheapest way to represent the information or that a real building would benefit.

The analysis-execution deviations discovered after archive download are fully disclosed in
`docs/phase1_correction_analysis_deviation_2026-07-22.md`. Neither changed an input row,
registered formula, statistical family, or interpretation rule.
