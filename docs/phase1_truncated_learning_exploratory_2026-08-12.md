# Exploratory truncated learning curves from the corrected Phase 1 record

> **Status (2026-08-12): retrospective, outcome-sighted, and exploratory.**
> This analysis reuses immutable Phase 1 and Phase 1b training trajectories.
> It launched zero training runs, modifies no registered output, supplies no
> p-values or confirmatory verdict, and cannot change the registered Phase 1b
> conclusion. Its sole decision purpose is to ask whether proposal P-1 has a
> plausible short-budget signal worth testing after thesis submission.

## Question and answer

The existing trajectories contain a plausible P-1 signal in `lab2` and
`lab4chain3`, but not in `labrel8`. At a 150-episode prefix, the mean paired
KG-minus-baseline `prefix_auc_goal` difference is +0.0490 in `lab2` and
+0.0533 in `lab4chain3`; their descriptive paired-bootstrap intervals are
[+0.0343, +0.0653] and [+0.0407, +0.0683]. The corresponding `labrel8`
difference is only +0.00067, with a descriptive interval starting at zero.

This is a screening result, not the P-1 experiment. The source learners were
configured for a 3,000-episode horizon. Their exploration and stereotype-prior
schedules therefore differ from learners prospectively configured to stop at
150, 300, 750, or 1,500 episodes. No intermediate Q-tables were archived, so
the greedy benchmark policy at each prefix cannot be reconstructed.

## Sources and integrity controls

The analysis uses 20 paired seeds per contrast:

- corrected Phase 1 `lab2`: KG-only runs `29848584965` and redundancy-only
  runs `29848587274`, with true and false arms paired within their original
  registered runs;
- corrected Phase 1b `labrel8` and `lab4chain3`: baseline runs `30199243656`
  and `30199247467`, redundancy-only runs `30199251189` and `30199254246`,
  and frozen-KG runs `30199257204` and `30199260042`.

Every one of the 200 source metric files is checked byte-for-byte and by
SHA-256 against the committed corrected-archive inventories. The reader also
requires the fixed 3,000-row horizon, contiguous episode numbers, binary goal
values, the expected profile/mode/seed marker, identical paired scenario
sequences, and near-balanced deterministic scenario prefixes. Near-balanced
means that all scenarios are present and their counts differ by at most one;
this is necessary because the 11-scenario `lab2` cycle divides neither the
selected budgets nor 3,000 exactly.

## Exploratory estimands

For budget B:

- `prefix_auc_goal(B)` is the mean `GoalReached` value over episodes 0 through
  B-1. The arm difference is formed within seed before aggregation.
- `trailing_training_goal_rate(B)` is the mean over the final 100 episodes of
  that prefix. It describes the training stream and is not a greedy-policy
  benchmark.

Budgets are 150, 300, 750, 1,500, and 3,000 episodes. Intervals are
non-inferential 95% paired-bootstrap descriptions with 10,000 resamples. The
historical `auc_goal` scale anchor 0.0111 is displayed only as context; it was
not registered as a threshold for these post-hoc prefixes. “Above anchor”
below therefore does not mean that a confirmatory criterion passed.

## KG-minus-baseline prefix result

| Profile | Budget | KG mean | Baseline mean | Paired difference | Descriptive 95% interval | Mean excess goals through B |
|---|---:|---:|---:|---:|---:|---:|
| `lab2` | 150 | 1.0000 | 0.9510 | +0.0490 | [+0.0343, +0.0653] | +7.35 |
| `lab2` | 300 | 1.0000 | 0.9708 | +0.0292 | [+0.0193, +0.0420] | +8.75 |
| `lab2` | 750 | 1.0000 | 0.9871 | +0.0129 | [+0.0087, +0.0179] | +9.65 |
| `lab2` | 1,500 | 1.0000 | 0.9932 | +0.0068 | [+0.0048, +0.0093] | +10.20 |
| `lab2` | 3,000 | 1.0000 | 0.9963 | +0.0037 | [+0.0027, +0.0049] | +11.10 |
| `lab4chain3` | 150 | 1.0000 | 0.9467 | +0.0533 | [+0.0407, +0.0683] | +8.00 |
| `lab4chain3` | 300 | 1.0000 | 0.9732 | +0.0268 | [+0.0203, +0.0343] | +8.05 |
| `lab4chain3` | 750 | 1.0000 | 0.9893 | +0.0107 | [+0.0082, +0.0137] | +8.05 |
| `lab4chain3` | 1,500 | 1.0000 | 0.9946 | +0.0054 | [+0.0041, +0.0069] | +8.05 |
| `lab4chain3` | 3,000 | 1.0000 | 0.9973 | +0.0027 | [+0.0021, +0.0034] | +8.05 |
| `labrel8` | 150 | 1.0000 | 0.9993 | +0.00067 | [0, +0.00167] | +0.10 |
| `labrel8` | 300 | 1.0000 | 0.9997 | +0.00033 | [0, +0.00083] | +0.10 |
| `labrel8` | 750 | 1.0000 | 0.9999 | +0.00013 | [0, +0.00033] | +0.10 |
| `labrel8` | 1,500 | 1.0000 | 0.9999 | +0.00007 | [0, +0.00017] | +0.10 |
| `labrel8` | 3,000 | 1.0000 | 1.0000 | +0.00003 | [0, +0.00008] | +0.10 |

The `lab2` prefix mean remains above the historical 0.0111 anchor through B =
750; `lab4chain3` remains above it through B = 300. These are observed prefix
locations, not estimated crossover budgets. `labrel8` never approaches the
anchor.

## What the curve shape means

The KG arm has `GoalReached = 1` from episode 0 in all three profiles and all
20 seeds. The apparent inverse relation between normalised AUC advantage and
budget is therefore primarily arithmetic dilution of a small, finite number
of baseline failures. The cumulative interpretation is more revealing:
`lab4chain3` reaches its final mean advantage of 8.05 avoided failures by
episode 300, while `lab2` rises gradually to 11.10 by episode 3,000.

The trailing 100-episode training-rate contrast reinforces that reading. At B
= 150 it is +0.0155 in `lab2` (descriptive interval [+0.0090, +0.0235]) and
+0.0095 in `lab4chain3` ([+0.0025, +0.0190]). By B = 300 the chain contrast is
exactly zero in all 20 seeds; `lab2` is +0.0085, with 13 ties and seven
positive seeds. `labrel8` is exactly zero at both prefixes. The evidence is a
small early failure-avoidance head start, not sustained separation in an
asymptotic policy.

## Redundancy decomposition at 150 episodes

| Profile | KG−baseline | Redundancy−baseline | KG−redundancy |
|---|---:|---:|---:|
| `lab2` | +0.0490 | +0.0310 | +0.0180 |
| `lab4chain3` | +0.0533 | +0.0170 | +0.0363 |
| `labrel8` | +0.00067 | −0.00067 | +0.00133 |

The ontology-free redundancy control reproduces about 63% of the 150-episode
`lab2` head start and about 32% of the `lab4chain3` head start. P-1 would
therefore still require the mimic arm; the full KG-minus-baseline contrast
cannot be attributed wholly to qualitative mechanism knowledge.

## Decision

P-1 has enough archival short-budget signal to remain a credible post-thesis
prospective experiment for `lab2` and `lab4chain3`. It does not have archival
support in `labrel8`. This does **not** reopen the pre-submission campaign
boundary: implement and dispatch nothing from the proposal menu before thesis
submission.

If the timebox is reopened later, P-1 should use fresh, disjoint paired seeds
and learners truly configured for each total budget. The registration must
freeze whether epsilon and prior fading are functions of absolute episode or
fraction of total budget, retain the redundancy control, and distinguish
normalised AUC from cumulative failures avoided. It must not promote the
observed prefix/anchor locations into prospective crossover hypotheses without
a separately justified threshold and power calculation.

## Reproduction

```powershell
powershell -File scripts/download_phase1b_truncation_inputs.ps1
python analysis/phase1_truncated_learning.py
python -m pytest analysis/tests/test_phase1_truncated_learning.py -q
```

Machine-readable outputs are under
`phase1_truncated_learning_exploratory/analysis/`. `input_file_manifest.csv`
binds the analysis inputs to corrected archive hashes and `SHA256SUMS.csv`
binds the generated outputs.
