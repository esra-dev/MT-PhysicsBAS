# Post-hoc robustness and reference summaries (2026-11-13)

Status: **unregistered, descriptive**. Nothing here replaces a registered analysis, and no
registered table or script was changed. The three tables are written by
`analysis/posthoc_robustness_summary.py` from the committed registered tables and the raw
archives. The Phase-2 and Phase-4 raw CSVs are gitignored, so the script takes the
directory that holds the downloaded archives:

```text
python analysis/posthoc_robustness_summary.py --hydrated-archive-root <dir with phase2_v2_corrected and phase4_v2_corrected>
```

The script stops if a stored Benjamini–Hochberg q differs from its recomputation, if a
rebuilt mean differs from the registered table, or if the label controls are not symmetric.

## 1. Multiplicity under dependence

The Benjamini–Hochberg procedure used in every registered family controls the false
discovery rate for independent or positively dependent test statistics. Several families
test metrics on the same runs. As a sensitivity check, each family was re-adjusted with the
Benjamini–Yekutieli procedure, which holds under arbitrary dependence
(`q_BY = min(1, c(m) · q_BH)`, `c(m) = 1 + 1/2 + … + 1/m`).

Result: of 38 registered members in nine families, 22 are significant at .05 under
Benjamini–Hochberg, and the same 22 are significant under Benjamini–Yekutieli. No verdict
changes. The two closest members are the delivered low-sun `labmon2_f2dead_lowsun` cells
(recovery `q_BY = 0.04687`, detection `q_BY = 0.04688`). Table:
`docs/audit/registered_multiplicity_sensitivity.csv`.

## 2. How many seeds carry each effect size

The matched-pairs rank-biserial correlation drops tied seeds, so a value of ±1.0 can rest
on few seeds. `docs/audit/registered_sign_counts.csv` lists positive, tied, and negative
seeds for the 31 registered members whose raw files are available (Phase 1, the knowledge
ladder, Phase 2, the delivered low-sun cells, Phase 4). Phase 1b is not included; its raw
files are outside this tree.

Points that change how a number should be read:

- `lab3_f1dead` recovery and detection, and the delivered `lab3_f2dead_lowsun` cells:
  rank-biserial `+1.0` from 11 seeds; the other nine are ties in which both arms are
  censored.
- Detection `lab3_f1inv`: rank-biserial `−1.0` from a single differing seed (sign-flip
  `p = 1`). Five further detection members have no differing seed at all.
- Delivered low-sun `labmon2_f2dead_lowsun` recovery: the registered mean difference is
  adverse (`+1087.8` episodes), but only seven seeds are positive and 13 are negative. The
  adverse mean is carried by the knowledge-arm runs that never detect the fault; in the
  other 13 seeds the knowledge arm recovers faster. Its rank-biserial is `+0.029`.
- Phase-4 `lab5` energy compliance: 13 positive, five tied, two negative.
- Phase-1 ladder member 1 (lab2): no seed differs.

## 3. Reference contrasts that no registration covers

Training success (`auc_goal`), paired by seed, n = 20, exact sign-flip p uncorrected.
The PBRS run enables potential-based reward shaping under both labels; its potential is the
negative distance to the goal and uses no knowledge-graph content.

| Contrast | lab2 | lab3 |
|---|---:|---:|
| PBRS − tabula rasa | −0.000250 (0 positive, 18 tied, 2 negative; p = 0.5) | 0.000000 (20 tied) |
| Full KG − PBRS | +0.003950 (20 positive; p = 1.907×10⁻⁶) | −0.002300 (5 / 1 / 14; p = 0.002331) |
| Brick structure − PBRS | +0.003950 (20 positive; p = 1.907×10⁻⁶) | −0.006150 (2 / 0 / 18; p = 8.774×10⁻⁵) |
| Redundancy only − PBRS | +0.002833 (17 / 0 / 3; p = 1.030×10⁻⁴) | +0.002400 (18 / 0 / 2; p = 5.531×10⁻⁵) |

Reward shaping with this potential gives no training-success benefit over plain tabula
rasa on either lab. The knowledge arms' positions relative to PBRS are therefore the same
as relative to tabula rasa.

Benchmark levels from the arm-C run (mean over 20 seeds; rule-based controller as
reference):

| Lab | Policy | Goal rate | Steps | Policy energy | Redundant actions |
|---|---|---:|---:|---:|---:|
| lab2 | rule-based | 1.0000 | 0.938 | 1.625 | 0.938 |
| lab2 | knowledge arm | 1.0000 | 1.126 | 1.569 | 1.126 |
| lab2 | tabula rasa | 0.9513 | 2.460 | 2.849 | 2.460 |
| lab3 | rule-based | 1.0000 | 0.875 | 1.688 | 0.875 |
| lab3 | knowledge arm | 0.9625 | 1.932 | 3.484 | 1.932 |
| lab3 | tabula rasa | 0.9762 | 1.599 | 2.410 | 1.599 |

The rule-based controller reaches every benchmark goal in fewer steps than both learners in
lab2 and lab3. On lab2 the knowledge arm matches its goal rate and uses slightly less
policy energy. All three policies are identical on lab1. The rule-based policy may import a
learned overlay when one is present, so it is not a pure static-knowledge baseline. Table:
`docs/audit/phase1_v2_posthoc_reference_contrasts.csv`.
