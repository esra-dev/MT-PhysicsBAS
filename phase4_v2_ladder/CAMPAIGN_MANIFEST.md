# Phase-4 knowledge-ladder control campaign

Registration: `docs/_audit/THESIS_STATE_REPORT.md`, Addendum 2026-11-13b, committed in
`ee656178` before the dispatches. Report: the same file, Addendum 2026-11-14. This manifest
is the canonical text for the tables, the validity evidence, and the labelled notes.

## Question

The archived Phase-4 campaign shows that the knowledge arm executes fewer redundant
actions than the tabula-rasa arm on the three dependency labs. It has no arm that removes
part of the knowledge. This campaign adds two such arms and asks how much of the reduction
remains when the reasoner keeps only the ontology-free redundancy rule, and when it keeps
Brick structure but no gate and no cost annotation.

## Arms and runs

| Arm | What the reasoner keeps | Run mode | Archives (seeds 1–10; seeds 11–20) | Labs |
|---|---|---|---|---|
| A0 | nothing (`ql_false`) | part of every run | every archive below | all |
| A1 | redundancy rule | `phase4_v2_redundancy_only` | `run_43494955158/`; `run_43494975441/` | lab4, lab4dual, lab4chain |
| A2 | Brick structure, no gate, no cost | `phase4_v2_brick_only` | `run_43494914019/`; `run_43494933613/` | lab4, lab4dual, lab4chain, lab5 |
| A3 | full knowledge graph | `phase4_v2` | `../phase4_v2_corrected/run_29926341581/`; `../phase4_v2_corrected/run_29926354783/` | lab4, lab4dual, lab4chain, lab5 |

The four control runs were dispatched from `ee656178` on 2026-11-13 and concluded
successfully on the first attempt (708 of 708 jobs). The A3 arm is the archived campaign of
2026-07-22 (head `90e53f8b`); it was not run again.

An arm effect is the within-run paired difference `ql_true − ql_false`, by seed. A rung
increment is the by-seed difference of two arm effects. `avg_redundant` is the mean over
the benchmark scenarios of a seed of wasted steps plus actuator cycling count; lower is
better. `energy_compliance` is the share of lab5 benchmark scenarios in which the goal is
reached and the steady-state power stays within the energy budget; higher is better.
n = 20 seeds everywhere.

## Reproduction

`python analysis/reproduce_phase4_v2_ladder.py phase4_v2_ladder --full-root phase4_v2_corrected`
re-validates the four control archives, reruns the frozen script
`analysis/phase4_v2_knowledge_ladder.py`, and compares its output with the four committed
files in `analysis/registered/` (canonical numeric bytes for the CSV files, parsed content
for the JSON file). It needs the extracted artifacts of all six runs; the committed
`SHA256SUMS.csv` inventories verify a restored copy (see the run manifests).

## Registered outcome

Source: `analysis/registered/phase4_v2_knowledge_ladder_family.csv`. The interval is the
95 % paired bootstrap interval of the increment; p is the two-sided exact sign-flip p; q is
Benjamini–Hochberg within the family of three.

### Family R — beyond the redundancy rule (A3 − A1, `avg_redundant`)

| Lab | A3 effect | A1 effect | Increment | 95 % interval | p sign-flip | p sign | q | Rank-biserial | Seeds − / 0 / + | Category | Share A1 / A3 | Share label |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab4 | −0.695000 | −0.390000 | −0.305000 | [−0.449375, −0.186875] | 1.907e-06 | 1.907e-06 | 5.722e-06 | −1.000 | 20 / 0 / 0 | `adds` | 0.5612 | partial |
| lab4dual | −0.745000 | −0.292500 | −0.452500 | [−0.552500, −0.352500] | 3.815e-06 | 3.815e-06 | 5.722e-06 | −1.000 | 19 / 1 / 0 | `adds` | 0.3926 | partial |
| lab4chain | −0.734375 | −0.438750 | −0.295625 | [−0.410625, −0.182500] | 1.030e-04 | 0.0026 | 1.030e-04 | −0.900 | 17 / 0 / 3 | `adds` | 0.5974 | partial |

All three members are `adds`. Licensed wording, per lab: "the full knowledge graph removes
more redundant actions than the ontology-free redundancy rule alone." Under the frozen
one-third / two-thirds rule the redundancy rule reproduces a partial share of the full
arm's reduction on every lab.

### Family S — beyond Brick structure (A3 − A2, `avg_redundant`)

| Lab | A3 effect | A2 effect | Increment | 95 % interval | p sign-flip | p sign | q | Rank-biserial | Seeds − / 0 / + | Category |
|---|---|---|---|---|---|---|---|---|---|---|
| lab4 | −0.695000 | −0.654375 | −0.040625 | [−0.065625, −0.012500] | 0.0171 | 0.0074 | 0.0256 | −0.675 | 13 / 5 / 2 | `adds` |
| lab4dual | −0.745000 | −0.691250 | −0.053750 | [−0.090000, −0.017500] | 0.0112 | 0.0063 | 0.0256 | −0.769 | 11 / 8 / 1 | `adds` |
| lab4chain | −0.734375 | −0.718750 | −0.015625 | [−0.034375, +0.003125] | 0.2500 | 0.3750 | 0.2500 | −0.733 | 4 / 15 / 1 | `null` |

- lab4 and lab4dual are `adds`. Licensed wording: "on this lab the gate annotations remove
  redundant actions that Brick structure alone does not." The wording says gate
  annotations, because the power gate and the blind sunshine gate are removed together.
- lab4chain is `null`. Licensed wording: "Brick structure reproduces the full arm's
  reduction on this lab." The reduction on lab4chain must not be attributed to the gate
  annotations.

### Secondary member — lab5 `energy_compliance` (A3 − A2)

A3 effect +0.043125, A2 effect −0.031875, increment
+0.075000, 95 % interval [+0.043750, +0.106250], sign-flip p 6.714e-04, sign p
0.0023, rank-biserial +0.882; 15 seeds positive, 3 tied,
2 negative. Category `adds`. Licensed wording: "the compliance gain requires the cost
annotation; the structure-only agent does not show it."

## Registered descriptives (no thresholds)

Source: `analysis/registered/phase4_v2_knowledge_ladder_descriptives.csv`. Each cell is the
mean arm effect with its 95 % paired bootstrap interval.

### Arm effects on `avg_redundant`

| Lab | A0 level | A1 effect | A2 effect | A3 effect | A2 − A1 increment | Reduction relative to the A0 level, A1 / A2 / A3 | A2 effect / A3 effect |
|---|---|---|---|---|---|---|---|
| lab4 | 1.582500 | −0.390000 [−0.708125, −0.096875] | −0.654375 [−0.951250, −0.403750] | −0.695000 [−0.988750, −0.443750] | −0.264375 [−0.413125, −0.148750] | 24.6 % / 41.4 % / 43.9 % | 0.9415 |
| lab4dual | 1.876875 | −0.292500 [−0.571250, −0.040000] | −0.691250 [−0.900000, −0.488750] | −0.745000 [−0.966875, −0.528750] | −0.398750 [−0.514375, −0.285000] | 15.6 % / 36.8 % / 39.7 % | 0.9279 |
| lab4chain | 1.668750 | −0.438750 [−0.621250, −0.252500] | −0.718750 [−0.870625, −0.560000] | −0.734375 [−0.888125, −0.587500] | −0.280000 [−0.400000, −0.164375] | 26.3 % / 43.1 % / 44.0 % | 0.9787 |

The last two columns are ratios of the registered descriptives. They are not registered
quantities and carry no test.

### Components and side effects on the dependency labs

| Quantity | Lab | A1 effect | A2 effect | A3 effect |
|---|---|---|---|---|
| wasted steps | lab4 | −0.535000 [−0.824375, −0.302500] | −0.551875 [−0.838125, −0.319375] | −0.551875 [−0.846875, −0.315625] |
| wasted steps | lab4dual | −0.479375 [−0.671875, −0.306875] | −0.535625 [−0.723125, −0.373750] | −0.535625 [−0.720000, −0.372500] |
| wasted steps | lab4chain | −0.478125 [−0.618125, −0.357500] | −0.528750 [−0.667500, −0.409375] | −0.528750 [−0.666875, −0.405625] |
| actuator cycling | lab4 | +0.145000 [+0.016250, +0.292500] | −0.102500 [−0.170625, −0.038125] | −0.143125 [−0.215625, −0.077500] |
| actuator cycling | lab4dual | +0.186875 [+0.060625, +0.317500] | −0.155625 [−0.239375, −0.075625] | −0.209375 [−0.291250, −0.131250] |
| actuator cycling | lab4chain | +0.039375 [−0.087500, +0.173125] | −0.190000 [−0.266875, −0.113750] | −0.205625 [−0.284375, −0.133125] |
| goal rate | lab4 | +0.013125 [−0.002500, +0.030625] | +0.018750 [+0.005625, +0.034375] | +0.018750 [+0.005625, +0.034375] |
| goal rate | lab4dual | +0.011875 [+0.003125, +0.022500] | +0.016250 [+0.007500, +0.026875] | +0.016250 [+0.007500, +0.026875] |
| goal rate | lab4chain | +0.013750 [+0.007500, +0.020625] | +0.015000 [+0.008125, +0.022500] | +0.015000 [+0.008125, +0.022500] |
| policy energy | lab4 | −0.608125 [−1.201250, −0.030000] | −0.503750 [−0.998750, −0.071250] | −0.553750 [−1.053750, −0.123750] |
| policy energy | lab4dual | −0.631875 [−1.104375, −0.221875] | −0.646250 [−0.985000, −0.336250] | −0.906875 [−1.303750, −0.535625] |
| policy energy | lab4chain | −0.745000 [−1.073750, −0.430625] | −0.761250 [−1.025000, −0.509375] | −0.795625 [−1.058125, −0.543750] |
| deviation | lab4 | −0.842500 [−1.250000, −0.422500] | −1.281875 [−1.631875, −0.931250] | −1.331875 [−1.672500, −0.983125] |
| deviation | lab4dual | −0.680000 [−1.351250, −0.059375] | −2.133125 [−2.654375, −1.632500] | −2.240625 [−2.770000, −1.731250] |
| deviation | lab4chain | −0.675625 [−1.012500, −0.329375] | −1.433125 [−1.703125, −1.163750] | −1.461250 [−1.725000, −1.196875] |

Reading of the two components of `avg_redundant`:

- **Wasted steps.** The mean effect is the same in A2 and A3 on every lab, and A1 reaches
  96.9 %, 89.5 %, and 90.4 % of it (lab4, lab4dual, lab4chain).
- **Actuator cycling.** A2 and A3 reduce cycling. A1 does not: its cycling effect is
  positive on lab4 and lab4dual with an interval above zero, and indistinguishable from
  zero on lab4chain. The mean increment of family S lies entirely in this component.

### lab5

| Quantity | A2 effect | p sign-flip | A3 effect | p sign-flip |
|---|---|---|---|---|
| energy compliance | −0.031875 [−0.069375, +0.003750] | 0.1202 | +0.043125 [+0.015625, +0.070625] | 0.0094 |
| goal rate | −0.022500 [−0.037500, −0.006250] | 0.0166 | −0.008750 [−0.025000, +0.009375] | 0.5078 |
| steps | +0.523125 [+0.254375, +0.773750] | 0.0020 | +0.177500 [−0.120000, +0.465000] | 0.2541 |
| wasted steps | −0.172500 [−0.371250, −0.005625] | 0.1200 | +0.161250 [−0.185625, +0.490000] | 0.4180 |
| actuator cycling | +0.695625 [+0.526250, +0.868750] | 3.815e-06 | +0.016250 [−0.049375, +0.077500] | 0.6374 |
| policy energy | +1.796250 [+0.908125, +2.695625] | 0.0012 | −0.631250 [−1.280000, −0.141875] | 0.0188 |
| deviation | +0.836875 [+0.574375, +1.070625] | 4.578e-05 | +0.575625 [+0.304375, +0.833750] | 9.880e-04 |

Without the cost annotation the structure-only arm shows no compliance gain, and it
cycles actuators more, spends more policy energy, takes more steps, and reaches the goal
slightly less often than tabula rasa. These are descriptive rows.

Absolute compliance levels are not quoted in this manifest. The registered scripts score a
benchmark scenario-run that has no step row, because the goal already holds at its
declared start, as if every actuator were off. That fallback raises the absolute level of
every arm by the same amount per seed and cancels in every paired effect and increment.
The `mean_archived_ql_false` and `mean_control_ql_false` columns of the comparability table
carry that fallback for lab5; they document identity between the campaigns and must not
be cited as compliance levels.

### Training success (`auc_goal`, mean of ten seeds per dispatch)

Source: `analysis/out/learning_speed_table.csv` of each run.

| Lab | Arm | Seeds 1–10 | Seeds 11–20 |
|---|---|---|---|
| lab4 | A0 tabula rasa | 0.998200 | 0.997833 |
| lab4 | A1 redundancy rule | 0.999700 | 0.999700 |
| lab4 | A2 Brick structure | 0.998100 | 0.999233 |
| lab4 | A3 full KG | 0.998900 | 0.999333 |
| lab4dual | A0 tabula rasa | 0.995033 | 0.992700 |
| lab4dual | A1 redundancy rule | 0.998767 | 0.998533 |
| lab4dual | A2 Brick structure | 0.999933 | 0.999867 |
| lab4dual | A3 full KG | 0.999967 | 0.999800 |
| lab4chain | A0 tabula rasa | 0.995200 | 0.996100 |
| lab4chain | A1 redundancy rule | 0.998933 | 0.998700 |
| lab4chain | A2 Brick structure | 0.999367 | 0.999567 |
| lab4chain | A3 full KG | 0.999400 | 0.999667 |
| lab5 | A0 tabula rasa | 0.998333 | 0.997967 |
| lab5 | A2 Brick structure | 0.997500 | 0.997433 |
| lab5 | A3 full KG | 0.998700 | 0.998800 |

Training success is at or above 0.99 in every arm and lab. The ladder therefore separates
the arms on the quality of the learned policy, not on whether the goal is reached during
training.

## Validity evidence

Per run: `run_<id>/ARCHIVE_MANIFEST.md` and `run_<id>/verification/`.

1. **Archives.** Each downloaded ZIP reproduces the digest that GitHub reports, every
   extracted file equals its ZIP member, and the Phase-4 archive validator passes for all
   four runs (280 training cells, 420 benchmark cells, fixed 3000-episode horizon, zero
   scenario fallbacks).
2. **Treatment delivered.** All 280 gate manifests record the dispatched run mode. All 280
   training jobs log the intended layer in every progress line and no other layer. In both
   control arms the ON column of every power-gated action is invariant to the state of its
   upstream switch; in the archived full-KG tables half of the state pairs differ
   (`verification/gate_invariance_reference_full_kg.json`).
3. **Only the intended cells differ (additional check).** The initial Q-tables of the A2
   arm equal the archived A3 tables in every cell except the gated ON columns while the
   upstream switch is off and the blind ON columns at sunshine rank 0.
4. **Comparability across the two campaigns.** The tabula-rasa training cells of all four
   control runs are byte-identical to the archived cells in every lab and seed. The
   `ql_false` value of each registered estimand is identical in 20 of 20 seeds for every
   lab and both control arms
   (`analysis/registered/phase4_v2_knowledge_ladder_comparability.csv`).
5. **Analysis.** The frozen script is byte-identical to its committed version in
   `ee656178` and ran once on 2026-11-13 after the archives were validated. The reproducer
   rebuilds all four registered files.

## Notes and labelled deviations

- **No deviation from the registered analysis, families, or decision rule.**
- **Helper scripts.** `analysis/phase4_v2_ladder_layer_proof.py`,
  `analysis/phase4_v2_ladder_cross_run_identity.py`, and
  `analysis/reproduce_phase4_v2_ladder.py` were written after the registration commit and
  before the runs finished. They are not part of the registered analysis. Two changes
  were made after data contact: the comparability script no longer lists a benchmark file
  as an unexpected difference when its only differing column is the wall-clock diagnostic,
  and the proof script gained the table comparison of item 3 above. Neither changes a
  registered number.
- **Proof of delivery, item 3 of the registration.** The registration names the seed-1
  initial tables. The proof was run on the combined initial tables of all seeds of each
  run; they are identical across seeds.
- **Expectation stated in the registration.** A1 was expected to reproduce a substantial
  part of the reduction, A3 − A2 to be negative with unknown size, and the A2 effect on
  lab5 to be near zero. The outcome agrees: A1 reproduces 39.3 % to 59.7 %, A3 − A2 is
  negative on all three labs, and the interval of the A2 effect on lab5 includes zero.

## Consequence for the wording of Phase 4

- The reduction in redundant actions on the dependency labs must not be attributed to
  dependency knowledge as a whole. An agent that knows only Brick structure obtains
  94.2 %, 92.8 %, and 97.9 % of the full arm's mean reduction (lab4, lab4dual, lab4chain).
- The gate annotations add a further reduction that is supported on lab4 and lab4dual
  (−0.040625 and −0.053750 redundant actions per scenario) and not
  detectable on lab4chain.
- The redundancy rule alone reproduces a partial share. What Brick structure adds beyond
  it is mainly fewer actuator cycles: the rule alone already removes most of the wasted
  steps (see the component table).
- On lab5 the compliance gain depends on the cost annotation.
- `ws:powerGates`, `ws:energyCost`, and `ws:ivMinRank` are project annotations, not terms of
  the published Elementary ontology. An `adds` outcome is evidence for those annotations.

## Limits

- The power gate and the blind sunshine gate are removed together in A2; their
  contributions are not separated.
- A3 was measured in July from another commit. The tabula-rasa cells and the knowledge-arm
  initial tables agree as described above; the A3 learning runs were not repeated.
- Three labs, one simulator, 20 seeds, and benchmark scenarios fixed per lab.
- A1 was not run on lab5, because the redundancy layer still reads the cost annotation.
- Family S contains small increments with many tied seeds (5, 8, and 15 of 20).
- The `results` branch holds only the seed-1 legacy files of each dispatch. The complete
  data exist in the GitHub Actions artifacts, which GitHub retains until 2027-02-11, and
  in extracted local copies.
