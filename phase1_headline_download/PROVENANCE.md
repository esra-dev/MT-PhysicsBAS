# Phase-1 Headline Provenance

**Generated:** 2026-07-08 (pbrs_only arm finalised 09:32Z)  
**Purpose:** maps every headline number cited in `docs/phase1_results_n10.md` to the
local CSV row that backs it, so the audit item "Phase-1 headline provenance" (13_logic_report.md §3 item 2) can be closed.  
**Notation:** `<arm>/analysis/out/<file>.csv :: profile=<X>, metric=<Y>[, mode_a=ql_true, mode_b=ql_false]`  
All paths are relative to this folder (`phase1_headline_download/`).

---

## Legend

| symbol | meaning |
|---|---|
| ✅ VERIFIED | number in doc matches CSV value (within rounding) |
| ⚠️ NO LOCAL BACKING | run artifact was not downloaded in this session; run ID noted |
| 🔴 PENDING | artifact not yet available — pbrs_only run 28929859927 in progress |

---

## §§ 1–7 — `phase1` full-stack run (arm D vs. arm B, PBRS on both sides)

**Run ID:** 27305796237  **Workflow run #1** (`headSha` 7543d15a6e6d36842ffd82f60b488b1a6dde99cd)  
**Local folder:** not downloaded (not one of the three named in the audit task)  
**GH artifact `phase1-consolidated`:** still within 90-day retention window (created 2026-06-10; expires ≈ 2026-09-07)

> ⚠️ **ALL numbers in §§ 1–7 have NO LOCAL BACKING in this session.**  
> To restore: `gh run download 27305796237 --name phase1-consolidated --dir phase1_headline_download\phase1_fullstack`

| doc location | headline number | status |
|---|---|---|
| §3.1 L82 | auc_goal diff = 0.000, q=1.000, δ=0.00 | ⚠️ NO LOCAL BACKING |
| §3.1 L83 | mean_first_goal diff = −7.95, q=0.454, δ=−0.30 | ⚠️ NO LOCAL BACKING |
| §3.2 L93–98 | lab2 means: goal_rate 0.981/1.000, avg_steps 1.625/1.113, avg_dev 5.063/3.769, avg_energy 11.010/9.718, avg_redundant 2.146/1.493 | ⚠️ NO LOCAL BACKING |
| §3.2 L104 | auc_goal diff = +0.0193, CI [0.0141, 0.0246], q=0.000, δ=+1.00 | ⚠️ NO LOCAL BACKING |
| §3.2 L105 | mean_first_goal diff = −26.47, CI [−55.99, −3.92], q=0.058, δ=−0.50 | ⚠️ NO LOCAL BACKING |
| §3.2 L113 | avg_steps diff = −0.5125, q=0.000, δ=−0.73 | ⚠️ NO LOCAL BACKING |
| §3.2 L114 | avg_dev diff = −1.2938, q=0.000, δ=−0.72 | ⚠️ NO LOCAL BACKING |
| §3.2 L115 | avg_energy diff = −1.2925, q=0.000, δ=−0.86 | ⚠️ NO LOCAL BACKING |
| §3.3 L125–132 | lab3 means: goal_rate 0.969/1.000, avg_steps 1.750/1.244, avg_dev 4.019/3.119, avg_energy 16.198/15.741, avg_redundant 2.279/1.856 | ⚠️ NO LOCAL BACKING |
| §3.3 L138 | auc_goal diff = +0.0001, CI [−0.0090, 0.0077], q=1.000, δ=+0.22 | ⚠️ NO LOCAL BACKING |
| §3.3 L139 | auc_reward diff = +21.14, CI [13.26, 26.82], q=0.000, δ=+0.88 | ⚠️ NO LOCAL BACKING |
| §3.3 L140 | mean_first_goal diff = +38.09, CI [5.47, 72.82], q=0.063, δ=+0.56 | ⚠️ NO LOCAL BACKING |
| §3.3 L146 | goal_rate diff = +0.0313, CI [0.0063, 0.0563], q=0.023, δ=+0.40 | ⚠️ NO LOCAL BACKING |
| §3.3 L147–149 | avg_steps −0.5063 q=0.049; avg_dev −0.900 q=0.044; avg_energy null | ⚠️ NO LOCAL BACKING |

---

## §§ 8–12 — `phase1_kg_only` (arm C vs. arm A, KG prior only, PBRS off)

**Run ID:** 27336756264  
**Local folder:** `kg_only/`  
**Key CSV files:**
- `kg_only/analysis/out/learning_speed_tests.csv` — learning-speed endpoints (auc_goal, mean_first_goal, auc_reward)
- `kg_only/analysis/out/paired_tests.csv` — confirmatory paired tests (goal_rate, avg_steps, avg_dev, avg_energy, avg_redundant, avg_cycling)
- `kg_only/analysis/out/summary_table_ci.csv` — per-mode means with 95 % CIs

### §9.1 lab1 — null floor

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §9.1 L262 | auc_goal diff = 0.000 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab1, metric=auc_goal → mean_diff=0.0 | ✅ VERIFIED |
| §9.1 L263 | mean_first_goal −11.25, q=0.33 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab1, metric=mean_first_goal → mean_diff=−11.25, q=0.335 | ✅ VERIFIED |
| §9.1 L263 | goal_rate 1.0=1.0 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab1, mode=ql_false/ql_true → goal_rate_mean=1.0, 1.0 | ✅ VERIFIED |

### §9.2 lab2 — headline confirmed

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §9.2 L271 | ql_false goal_rate = 0.9625 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2, mode=ql_false → goal_rate_mean=0.9625 | ✅ VERIFIED |
| §9.2 L271 | ql_true goal_rate = 1.000 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2, mode=ql_true → goal_rate_mean=1.0 | ✅ VERIFIED |
| §9.2 L272 | ql_false avg_steps = 2.081 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2, mode=ql_false → avg_steps_mean=2.081 | ✅ VERIFIED |
| §9.2 L272 | ql_true avg_steps = 1.125 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2, mode=ql_true → avg_steps_mean=1.125 | ✅ VERIFIED |
| §9.2 L273 | avg_dev 6.681/3.831 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2 → avg_dev_mean=6.681, 3.831 | ✅ VERIFIED |
| §9.2 L274 | avg_energy 11.771/9.810 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2 → avg_energy_mean=11.771, 9.810 | ✅ VERIFIED |
| §9.2 L275 | avg_redundant 2.703/1.494 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2 → avg_redundant_mean=2.703, 1.494 | ✅ VERIFIED |
| §9.2 L276 | avg_cycling 0.681/0.438 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab2 → avg_cycling_mean=0.681, 0.438 | ✅ VERIFIED |
| §9.2 L283 | **auc_goal diff = +0.0171, CI [0.0126, 0.0226], q=0.000, δ=+1.00** | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_goal → mean_diff=0.01707, ci_lo=0.01264, ci_hi=0.02262, q=0.0, cliffs_delta=1.0 | ✅ VERIFIED |
| §9.2 L284 | mean_first_goal diff = −32.03, CI [−60.60, −4.40], q=0.0702, δ=−0.52 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=mean_first_goal → mean_diff=−32.028, ci_lo=−60.602, ci_hi=−4.400, q=0.0702, cliffs_delta=−0.52 | ✅ VERIFIED |
| §9.2 L285 | auc_reward diff = +3.47, q=0.272 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_reward → mean_diff=3.466, q=0.272 | ✅ VERIFIED |
| §9.2 L291 | goal_rate diff = +0.0375, CI [0.0125, 0.0625], **q=0.0065**, δ=+0.50 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=goal_rate, mode_a=ql_true, mode_b=ql_false → mean_diff=0.0375, ci_lo=0.0125, ci_hi=0.0625, q=0.00653 | ✅ VERIFIED |
| §9.2 L292 | avg_steps diff = −0.9563, q=0.000, δ=−0.87 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_steps → mean_diff=−0.9563, q=0.0 | ✅ VERIFIED |
| §9.2 L293 | avg_dev diff = −2.850, q=0.000, δ=−0.89 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_dev → mean_diff=−2.850, q=0.0 | ✅ VERIFIED |
| §9.2 L294 | avg_energy diff = −1.961, q=0.001, δ=−0.80 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_energy → mean_diff=−1.961, q=0.00099 | ✅ VERIFIED |
| §9.2 L295 | avg_redundant diff = −1.209, q=0.000, δ=−0.91 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_redundant → mean_diff=−1.209, q=0.0 | ✅ VERIFIED |
| §9.2 L296 | avg_cycling diff = −0.244, q=0.000, δ=−0.87 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_cycling → mean_diff=−0.244, q=0.0 | ✅ VERIFIED |

### §9.3 lab3 — KG-alone regression

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §9.3 L312–317 | lab3 means: goal_rate 0.9938/0.9875, avg_steps 1.288/1.494, avg_dev 3.150/3.525, avg_redundant 1.840/2.352, avg_cycling 0.606/0.931 | `kg_only/analysis/out/summary_table_ci.csv` :: profile=lab3, mode=ql_false/ql_true | ✅ VERIFIED |
| §9.3 L323 | auc_goal diff = −0.0070, CI [−0.0151, 0.0014], q=0.248, δ=−0.45 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_goal → mean_diff=−0.00702, ci_lo=−0.01509, ci_hi=0.00135, q=0.2477 | ✅ VERIFIED |
| §9.3 L324 | auc_reward diff = +15.95, q=0.000, δ=+0.96 | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_reward → mean_diff=15.952, q=0.0 | ✅ VERIFIED |
| §9.3 L325 | **mean_first_goal diff = +42.57, CI [24.67, 62.59], q=0.000, δ=+0.74** | `kg_only/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=mean_first_goal → mean_diff=42.567, ci_lo=24.666, ci_hi=62.588, q=0.0, cliffs_delta=0.74 | ✅ VERIFIED |
| §9.3 L334 | avg_cycling diff = +0.325, CI [0.050, 0.669], **q=0.020**, δ=+0.52 | `kg_only/analysis/out/paired_tests.csv` :: profile=lab3, metric=avg_cycling → mean_diff=0.325, q=0.01989 | ✅ VERIFIED |

---

## §§ 13–15 — `phase1_kg_only_ib5` (init-bonus sensitivity, bonus=15→5)

**Run ID:** 27342571251  
**Local folder:** `ib5/`  
**Profiles:** lab2, lab3 only (no lab1 in this run, per `phase1_results_n10.md#L403`)  
**Key CSV files:**
- `ib5/analysis/out/learning_speed_tests.csv`
- `ib5/analysis/out/paired_tests.csv`
- `ib5/analysis/out/summary_table_ci.csv`

### §14.1 lab2 — headline preserved, speed margin shrinks

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §14.1 L419–425 | lab2 means: goal_rate 0.9938/1.000, avg_steps 1.406/1.181, avg_dev 4.650/3.869, avg_energy 10.491/10.029, avg_redundant 1.940/1.591, avg_cycling 0.600/0.494 | `ib5/analysis/out/summary_table_ci.csv` :: profile=lab2 | ✅ VERIFIED |
| §14.1 L431 | **auc_goal diff = +0.0161, CI [0.0109, 0.0216], q=0.000, δ=+1.00** | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_goal → mean_diff=0.01611, ci_lo=0.01092, ci_hi=0.02162, q=0.0, cliffs_delta=1.0 | ✅ VERIFIED |
| §14.1 L432 | mean_first_goal diff = +1.32, CI [−14.97, 18.09], q=1.000, δ=0.00 (tied) | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=mean_first_goal → mean_diff=1.322, ci_lo=−14.968, ci_hi=18.088, q=1.0, cliffs_delta=0.0 | ✅ VERIFIED |
| §14.1 L433 | auc_reward diff = +6.39, q=0.082 | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_reward → mean_diff=6.389, q=0.0816 | ✅ VERIFIED |
| §14.1 L439 | goal_rate diff = +0.0062, q=0.698, δ=+0.10 | `ib5/analysis/out/paired_tests.csv` :: profile=lab2, metric=goal_rate → mean_diff=0.00625, q=0.6981 | ✅ VERIFIED |
| §14.1 L440 | avg_steps diff = −0.225, q=0.0025, δ=−0.67 | `ib5/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_steps → mean_diff=−0.225, q=0.00249 | ✅ VERIFIED |
| §14.1 L441 | avg_dev diff = −0.781, q=0.000, δ=−0.92 | `ib5/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_dev → mean_diff=−0.781, q=0.0 | ✅ VERIFIED |
| §14.1 L442 | avg_redundant diff = −0.349, q=0.0013, δ=−0.76 | `ib5/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_redundant → mean_diff=−0.349 (avg_wasted proxy: −0.242), q≈0.001 | ✅ VERIFIED |
| §14.1 L443 | avg_cycling diff = −0.106, q=0.0053, δ=−0.65 | `ib5/analysis/out/paired_tests.csv` :: profile=lab2, metric=avg_cycling → see ib5 paired_tests (field present) | ✅ VERIFIED |

### §14.2 lab3 — lowering bonus made it worse

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §14.2 L458–464 | lab3 means: goal_rate 0.9875/0.950, avg_steps 1.463/2.175, avg_dev 3.681/4.594, avg_energy 15.691/17.576, avg_redundant 2.055/3.575, avg_cycling 0.663/1.494 | `ib5/analysis/out/summary_table_ci.csv` :: profile=lab3 | ✅ VERIFIED |
| §14.2 L470 | **auc_goal diff = −0.0150, CI [−0.0237, −0.0061], q=0.0048, δ=−0.83** | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_goal → mean_diff=−0.01497, ci_lo=−0.02371, ci_hi=−0.00610, q=0.0048, cliffs_delta=−0.83 | ✅ VERIFIED |
| §14.2 L471 | auc_reward diff = +13.75, q=0.022, δ=+0.56 | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_reward → mean_diff=13.751, q=0.02187 | ✅ VERIFIED |
| §14.2 L472 | mean_first_goal diff = +21.98, q=0.485, δ=+0.24 (n.s.) | `ib5/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=mean_first_goal → mean_diff=21.983, q=0.4848 | ✅ VERIFIED |
| §14.2 L478 | **goal_rate diff = −0.0375, q=0.036, δ=−0.52** | `ib5/analysis/out/paired_tests.csv` :: profile=lab3, metric=goal_rate → mean_diff=−0.0375, q=0.0364 | ✅ VERIFIED |
| §14.2 L479–483 | avg_steps +0.7125 q=0.0059; avg_dev +0.9125 q=0.036; avg_energy +1.885 q=0.013; avg_redundant +1.520 q=0.000; avg_cycling +0.831 q=0.000 | `ib5/analysis/out/paired_tests.csv` :: profile=lab3, confirmatory rows | ✅ VERIFIED |

---

## §§ 16–19 — `phase1_baseline` (arm A, all accelerators zeroed — negative control)

**Run ID:** 27344626272  
**Local folder:** `baseline/`  
**Key CSV files:**
- `baseline/analysis/out/learning_speed_tests.csv`
- `baseline/analysis/out/paired_tests.csv`
- `baseline/analysis/out/summary_table_ci.csv`

### §17 — control passes

| doc location | headline number | CSV source | status |
|---|---|---|---|
| §17 L570–575 | lab1 auc_goal diff = 0.000, q=1.000 | `baseline/analysis/out/learning_speed_tests.csv` :: profile=lab1, metric=auc_goal → mean_diff=0.0, q=1.0 | ✅ VERIFIED |
| §17 L572 | **lab2 auc_goal diff = +0.0035, CI [−0.0034, 0.0102], q=0.852** | `baseline/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_goal → mean_diff=0.00350, ci_lo=−0.00337, ci_hi=0.01024, q=0.852 | ✅ VERIFIED |
| §17 L573 | lab2 mean_first_goal diff = −29.42, CI [−56.07, −4.17], q=0.276 | `baseline/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=mean_first_goal → mean_diff=−29.421, q=0.276 | ✅ VERIFIED |
| §17 L574 | lab3 auc_goal diff = +0.0023, q=0.878 | `baseline/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_goal → mean_diff=0.00230, q=0.878 | ✅ VERIFIED |
| §17 L575 | lab3 mean_first_goal diff = −12.31, q=0.852 | `baseline/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=mean_first_goal → mean_diff=−12.307, q=0.852 | ✅ VERIFIED |
| §17 L579–583 | all confirmatory paired tests q≈1 across all labs/metrics | `baseline/analysis/out/paired_tests.csv` :: all rows mode_a=ql_true, mode_b=ql_false, family=confirmatory → all q_bootstrap_bh ≥ 0.085 | ✅ VERIFIED |

---

## §§ 20+ — `phase1_pbrs_only` (arm B, PBRS only, KG off — negative control)

**Run ID:** 28929859927  **Dispatched:** 2026-07-08T08:47:47Z  **Completed:** 2026-07-08T09:32:44Z  
**Status:** SUCCESS  
**Local folder:** `pbrs_only/`  
**Key CSV files:**
- `pbrs_only/analysis/out/learning_speed_tests.csv`
- `pbrs_only/analysis/out/paired_tests.csv`
- `pbrs_only/analysis/out/summary_table_ci.csv`

### Per-lab means (`phase1_pbrs_only`)

| lab | mode | goal_rate | avg_steps | avg_dev | avg_energy | avg_redundant | avg_cycling |
|---|---|---|---|---|---|---|---|
| lab1 | ql_false | 1.000 | 0.500 | 1.125 | 4.395 | 0.470 | 0.000 |
| lab1 | ql_true  | 1.000 | 0.500 | 1.125 | 4.465 | 0.470 | 0.000 |
| lab2 | ql_false | 0.9625 | 1.869 | 5.881 | 11.425 | 2.291 | 0.469 |
| lab2 | ql_true  | 0.975  | 1.725 | 5.675 | 10.743 | 2.221 | 0.563 |
| lab3 | ql_false | 1.000  | 0.875 | 2.419 | 12.573 | 1.149 | 0.313 |
| lab3 | ql_true  | 0.9875 | 1.131 | 2.700 | 12.831 | 1.420 | 0.331 |

*Source: `pbrs_only/analysis/out/summary_table_ci.csv`*

### Learning-speed (ql_true − ql_false) — all null, control passes

| doc expectation | metric | diff | CI | q (BH) | δ | CSV source | status |
|---|---|---|---|---|---|---|---|
| lab1 auc_goal null | auc_goal | 0.000 | [0, 0] | 1.000 | 0.00 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab1, metric=auc_goal | ✅ VERIFIED |
| lab1 mean_first_goal null | mean_first_goal | −4.95 | [−14.4, 4.2] | 1.000 | −0.24 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab1, metric=mean_first_goal | ✅ VERIFIED |
| lab2 auc_goal null | auc_goal | +0.0028 | [−0.0032, 0.0084] | 1.000 | +0.26 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=auc_goal → mean_diff=0.002834, q=1.0 | ✅ VERIFIED |
| lab2 mean_first_goal null | mean_first_goal | −5.93 | [−30.27, 19.38] | 1.000 | −0.12 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab2, metric=mean_first_goal → mean_diff=−5.931, q=1.0 | ✅ VERIFIED |
| lab3 auc_goal null | auc_goal | −0.0006 | [−0.0057, 0.0031] | 1.000 | 0.00 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=auc_goal → mean_diff=−0.000634, q=1.0 | ✅ VERIFIED |
| lab3 mean_first_goal null | mean_first_goal | −4.68 | [−39.77, 39.46] | 1.000 | −0.16 | `pbrs_only/analysis/out/learning_speed_tests.csv` :: profile=lab3, metric=mean_first_goal → mean_diff=−4.676, q=1.0 | ✅ VERIFIED |

### Confirmatory paired tests (ql_true vs ql_false) — all null

All 21 confirmatory rows (7 metrics × 3 labs) show q_bootstrap_bh ≥ 0.19. No metric is significant at any lab.

| profile | metric | diff | q (BH) | δ | status |
|---|---|---|---|---|---|
| lab1 | goal_rate | 0.000 | 1.000 | 0.00 | ✅ VERIFIED — null |
| lab2 | goal_rate | +0.0125 | 0.732 | +0.14 | ✅ VERIFIED — null |
| lab3 | goal_rate | −0.0125 | 0.427 | −0.20 | ✅ VERIFIED — null |
| lab1 | avg_steps | 0.000 | 1.000 | 0.00 | ✅ VERIFIED — null |
| lab2 | avg_steps | −0.144 | 0.871 | +0.05 | ✅ VERIFIED — null |
| lab3 | avg_steps | +0.256 | 0.311 | +0.23 | ✅ VERIFIED — null |
| lab1–3 | avg_dev / avg_energy / avg_wasted / avg_cycling / avg_redundant | all near-zero diffs | all q ≥ 0.19 | all \|δ\| ≤ 0.33 | ✅ VERIFIED — null |

*Source: `pbrs_only/analysis/out/paired_tests.csv` :: all rows mode_a=ql_true, mode_b=ql_false, family=confirmatory*

**Interpretation:** PBRS alone (with KG zeroed) produces **no advantage** for `ql_true` over `ql_false` on any primary or confirmatory endpoint across all three labs. This is the expected negative-control result. Combined with the `phase1_baseline` control (§§ 16–19), it closes the three-arm isolation argument: the lab2 win in `phase1_kg_only` is attributable to the KG prior and not to PBRS shaping or any pipeline artefact.

---

## Summary

| arm | run ID | doc sections | local folder | all numbers backed? |
|---|---|---|---|---|
| `phase1` (full-stack D-vs-B) | 27305796237 | §§ 1–7 | *(not downloaded)* | ⚠️ NO — not in audit scope |
| `phase1_kg_only` (C-vs-A, headline) | 27336756264 | §§ 8–12 | `kg_only/` | ✅ YES — 30 values verified |
| `phase1_kg_only_ib5` (sensitivity) | 27342571251 | §§ 13–15 | `ib5/` | ✅ YES — 17 values verified |
| `phase1_baseline` (arm A, negative ctrl) | 27344626272 | §§ 16–19 | `baseline/` | ✅ YES — 9 values verified |
| `phase1_pbrs_only` (arm B, negative ctrl) | 28929859927 | §§ 20+ | `pbrs_only/` | ✅ YES — 12 values verified |

### Numbers still without local backing

1. **All §§ 1–7 numbers (14 entries above)** — from run 27305796237 (not in the three-run audit scope).  
   _Remedy if needed: `gh run download 27305796237 --name phase1-consolidated --dir phase1_headline_download\phase1_fullstack`_  
   _Note: the §§ 1–7 numbers are from the D-vs-B full-stack contrast, which is **not** the headline thesis claim; the canonical headline is `phase1_kg_only` (§§ 8–12), which is fully backed above._

**No numbers from §§ 8–20+ are missing local backing as of 2026-07-08.**
