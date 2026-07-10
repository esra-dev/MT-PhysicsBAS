# 20 — Extracted Results (figures + paired-stats tables)


**Generated:** by `analysis/audit_results_figures.py` — every value below is read verbatim from a canonical final-run CSV indexed in `docs/_audit/05_results_index.md`. Long floats are truncated to 4 significant figures for display only; the cited CSV holds the exact value. All content is **[NEW] era** (phase-based approach).


Figures live in `docs/_audit/figures/`; each figure prints its source path in its bottom-left corner.


## 1. Phase 1 — KG acceleration on clean labs [NEW era]


### 1.1 Run 27336756264 (kg_only headline)

Arm C vs arm A (KG isolated, PBRS off), seeds 1–10, labs lab1–lab3 (lab3 = old spill physics: lamp 150 lux / blind 0.40·sun).


**Learning-speed paired tests (ql_true − ql_false, seed-paired):**

| profile | metric | metric_tier | direction | n_paired | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab1 | auc_goal | primary | higher_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab1 | auc_reward | secondary | higher_better | 10 | 0.06004 | -0.9927 | 1.05 | 0.8884 | 0.5566 | 0.04 | 1 | 12 |
| lab1 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab1 | mean_first_goal | secondary | lower_better | 10 | -11.25 | -28.35 | 5.85 | 0.1954 | 0.2109 | -0.23 | 0.335 | 12 |
| lab2 | auc_goal | primary | higher_better | 10 | 0.01707 | 0.01264 | 0.02262 | 0 | 0.001953 | 1 | 0 | 12 |
| lab2 | auc_reward | secondary | higher_better | 10 | 3.466 | -0.936 | 8.248 | 0.136 | 0.2754 | 0.2 | 0.272 | 12 |
| lab2 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab2 | mean_first_goal | secondary | lower_better | 10 | -32.03 | -60.6 | -4.4 | 0.0234 | 0.1934 | -0.52 | 0.0702 | 12 |
| lab3 | auc_goal | primary | higher_better | 10 | -0.007019 | -0.01509 | 0.00135 | 0.1032 | 0.1934 | -0.45 | 0.2477 | 12 |
| lab3 | auc_reward | secondary | higher_better | 10 | 15.95 | 11.01 | 20.84 | 0 | 0.001953 | 0.96 | 0 | 12 |
| lab3 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab3 | mean_first_goal | secondary | lower_better | 10 | 42.57 | 24.67 | 62.59 | 0 | 0.001953 | 0.74 | 0 | 12 |

Source: `phase1_headline_download/kg_only/analysis/out/learning_speed_tests.csv`


**Benchmark paired tests, ql_true vs ql_false (confirmatory family):**

| profile | metric | n_paired | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|
| lab1 | goal_rate | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | goal_rate | 10 | 0.0375 | 0.0125 | 0.0625 | 0.0028 | 0.0625 | 0.5 | 0.006533 | 42 |
| lab3 | goal_rate | 10 | -0.00625 | -0.025 | 0.0125 | 0.7704 | 1 | -0.1 | 1 | 42 |
| lab1 | avg_steps | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_steps | 10 | -0.9563 | -1.494 | -0.4313 | 0 | 0.003906 | -0.87 | 0 | 42 |
| lab3 | avg_steps | 10 | 0.2062 | -0.2 | 0.6125 | 0.339 | 0.2461 | 0.36 | 0.5933 | 42 |
| lab1 | avg_dev | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_dev | 10 | -2.85 | -4.444 | -1.306 | 0 | 0.003906 | -0.89 | 0 | 42 |
| lab3 | avg_dev | 10 | 0.375 | -0.1562 | 0.9314 | 0.1838 | 0.2969 | 0.32 | 0.3676 | 42 |
| lab1 | avg_energy | 10 | -0.0325 | -0.135 | 0.0575 | 0.5246 | 0.7344 | -0.28 | 0.816 | 42 |
| lab2 | avg_energy | 10 | -1.961 | -3.164 | -0.7825 | 0.0004 | 0.01367 | -0.8 | 0.0009882 | 42 |
| lab3 | avg_energy | 10 | 0.9362 | -1.164 | 2.581 | 0.3334 | 0.08398 | 0.66 | 0.5933 | 42 |
| lab1 | avg_wasted | 10 | -0.005 | -0.0375 | 0.03 | 0.751 | 0.5781 | -0.16 | 1 | 42 |
| lab2 | avg_wasted | 10 | -0.965 | -1.496 | -0.4537 | 0 | 0.001953 | -0.91 | 0 | 42 |
| lab3 | avg_wasted | 10 | 0.1875 | -0.2137 | 0.5887 | 0.3684 | 0.2207 | 0.34 | 0.6189 | 42 |
| lab1 | avg_cycling | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_cycling | 10 | -0.2437 | -0.325 | -0.1562 | 0 | 0.003906 | -0.87 | 0 | 42 |
| lab3 | avg_cycling | 10 | 0.325 | 0.05 | 0.6687 | 0.009 | 0.05469 | 0.52 | 0.01989 | 42 |
| lab1 | avg_redundant | 10 | -0.005 | -0.0375 | 0.03 | 0.751 | 0.5781 | -0.16 | 1 | 42 |
| lab2 | avg_redundant | 10 | -1.209 | -1.8 | -0.64 | 0 | 0.001953 | -0.91 | 0 | 42 |
| lab3 | avg_redundant | 10 | 0.5125 | -0.1263 | 1.236 | 0.1332 | 0.1855 | 0.36 | 0.2797 | 42 |

Source: `phase1_headline_download/kg_only/analysis/out/paired_tests.csv`


### 1.2 Run 28941204656 (xzone-mid)

Intermediate-bleed rerun on current lab3 physics (lamp 100 lux / blind 0.30·sun, commit ad3cb3b), `cross_zone_bonus = 3.0`, seeds 1–10.


**Learning-speed paired tests (ql_true − ql_false, seed-paired):**

| profile | metric | metric_tier | direction | n_paired | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab1 | auc_goal | primary | higher_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab1 | auc_reward | secondary | higher_better | 10 | -0.2821 | -0.8978 | 0.3932 | 0.3924 | 0.375 | -0.18 | 0.7848 | 12 |
| lab1 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab1 | mean_first_goal | secondary | lower_better | 10 | -12.9 | -27.9 | 0.6 | 0.0654 | 0.3125 | -0.35 | 0.157 | 12 |
| lab2 | auc_goal | primary | higher_better | 10 | 0.02124 | 0.01527 | 0.02811 | 0 | 0.001953 | 1 | 0 | 12 |
| lab2 | auc_reward | secondary | higher_better | 10 | 5.965 | 1.942 | 9.995 | 0.0036 | 0.04883 | 0.54 | 0.0108 | 12 |
| lab2 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab2 | mean_first_goal | secondary | lower_better | 10 | -4.038 | -35.07 | 26.55 | 0.8086 | 0.7695 | -0.3 | 1 | 12 |
| lab3 | auc_goal | primary | higher_better | 10 | -0.0004502 | -0.005485 | 0.005502 | 0.822 | 0.6953 | -0.12 | 1 | 12 |
| lab3 | auc_reward | secondary | higher_better | 10 | 12.66 | 8.762 | 16.69 | 0 | 0.001953 | 0.88 | 0 | 12 |
| lab3 | episodes_to_threshold | secondary_censored | lower_better | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 12 |
| lab3 | mean_first_goal | secondary | lower_better | 10 | 23.95 | 7.679 | 39.95 | 0.0036 | 0.02734 | 0.28 | 0.0108 | 12 |

Source: `phase1_xzone_mid/analysis/out/learning_speed_tests.csv`


**Benchmark paired tests, ql_true vs ql_false (confirmatory family):**

| profile | metric | n_paired | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|
| lab1 | goal_rate | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | goal_rate | 10 | 0.025 | 0 | 0.05 | 0.0556 | 0.25 | 0.3 | 0.08982 | 42 |
| lab3 | goal_rate | 10 | 0.00625 | -0.01875 | 0.03125 | 0.8236 | 1 | 0.04 | 1 | 42 |
| lab1 | avg_steps | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_steps | 10 | -0.5813 | -1.131 | -0.125 | 0.0016 | 0.03125 | -0.55 | 0.003733 | 42 |
| lab3 | avg_steps | 10 | -0.01875 | -0.5312 | 0.5 | 0.94 | 0.7539 | 0.2 | 1 | 42 |
| lab1 | avg_dev | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_dev | 10 | -1.488 | -2.725 | -0.3875 | 0.0002 | 0.01172 | -0.55 | 0.00056 | 42 |
| lab3 | avg_dev | 10 | 0.075 | -0.4562 | 0.6312 | 0.8098 | 0.9375 | 0.2 | 1 | 42 |
| lab1 | avg_energy | 10 | 0.015 | -0.055 | 0.0875 | 0.6758 | 0.6152 | 0.13 | 0.9787 | 42 |
| lab2 | avg_energy | 10 | -1.468 | -2.569 | -0.5375 | 0 | 0.003906 | -0.63 | 0 | 42 |
| lab3 | avg_energy | 10 | 2.072 | 0.6125 | 3.473 | 0.0056 | 0.02734 | 0.64 | 0.01176 | 42 |
| lab1 | avg_wasted | 10 | 0.0175 | 0.0025 | 0.03 | 0.0228 | 0.09375 | 0.45 | 0.04163 | 42 |
| lab2 | avg_wasted | 10 | -0.59 | -1.148 | -0.1275 | 0.0008 | 0.03711 | -0.58 | 0.0021 | 42 |
| lab3 | avg_wasted | 10 | -0.0175 | -0.5325 | 0.5062 | 0.9366 | 0.7344 | 0.17 | 1 | 42 |
| lab1 | avg_cycling | 10 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 42 |
| lab2 | avg_cycling | 10 | -0.225 | -0.5062 | -0.04375 | 0.0034 | 0.04688 | -0.45 | 0.007516 | 42 |
| lab3 | avg_cycling | 10 | 0.575 | 0.25 | 0.925 | 0 | 0.003906 | 0.76 | 0 | 42 |
| lab1 | avg_redundant | 10 | 0.0175 | 0.0025 | 0.03 | 0.0228 | 0.09375 | 0.45 | 0.04163 | 42 |
| lab2 | avg_redundant | 10 | -0.815 | -1.636 | -0.1962 | 0.001 | 0.02734 | -0.56 | 0.002471 | 42 |
| lab3 | avg_redundant | 10 | 0.5575 | -0.1312 | 1.324 | 0.1258 | 0.3125 | 0.34 | 0.1957 | 42 |

Source: `phase1_xzone_mid/analysis/out/paired_tests.csv`


## 2. Phase 2 — registered pooled fault-recovery analysis [NEW era]

Pooled `--registered` analysis over the §9.7 runs of record (runs 28590019536, 28745352239, 28750100413, 28863439179, 28866807391, 28884717500, 28913465680); frozen families per `docs/pre_registration.md` §9. `in_registered_family = True` rows form the Tier-1 BH family (m = 8).


**Paired recovery / detection tests (ql_true − ql_false, seed-paired):**

| profile | metric | recovery_tier | in family | n_paired | ql_true_mean | ql_false_mean | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab3_f1dead | RecoveryEpisodes | confirmatory | True | 10 | 149.4 | 270.5 | -121.1 | -201.6 | -51.8 | 0.0002 | 0.01367 | -0.72 | 0.0002667 | 8 |
| lab3_f1inv | RecoveryEpisodes | descriptive | False | 10 | 1538 | 1592 | -54 | -651 | 538.3 | 0.8606 | 0.7695 | 0.14 | nan | 0 |
| lab3_f1dead_z2 | RecoveryEpisodes | confirmatory | True | 10 | 151.3 | 247 | -95.7 | -141.2 | -55.2 | 0 | 0.003906 | -0.84 | 0 | 8 |
| lab3_f1inv_z2 | RecoveryEpisodes | descriptive | False | 9 | 1425 | 1585 | -160.7 | -915.1 | 567.3 | 0.6954 | 0.7344 | 0.01235 | nan | 0 |
| lab3_f1bdead | RecoveryEpisodes | confirmatory | True | 10 | 62.1 | 488.6 | -426.5 | -1183 | -19.3 | 0.0012 | 0.02734 | -0.55 | 0.0012 | 8 |
| lab3_f1binv | RecoveryEpisodes | confirmatory | True | 9 | 112 | 1021 | -908.9 | -2139 | -48 | 0.0008 | 0.02734 | -0.4691 | 0.0009143 | 8 |
| lab2_f1bdead | RecoveryEpisodes | confirmatory | True | 10 | 70.8 | 297.5 | -226.7 | -328.7 | -142.5 | 0 | 0.001953 | -0.92 | 0 | 8 |
| lab2_f1binv | RecoveryEpisodes | descriptive | False | 9 | 290.4 | 333.8 | -43.33 | -151.1 | 73.89 | 0.456 | 0.4258 | -0.3333 | nan | 0 |
| labmon_f1dead | RecoveryEpisodes | confirmatory | True | 10 | 53 | 59.2 | -6.2 | -8.5 | -4.2 | 0 | 0.001953 | -0.86 | 0 | 8 |
| lab3_f2dead_lowsun | RecoveryEpisodes | confirmatory | True | 10 | 69.4 | 134.3 | -64.9 | -97.31 | -34.4 | 0 | 0.003906 | -0.88 | 0 | 8 |
| labmon2_f2dead_lowsun | RecoveryEpisodes | confirmatory | True | 10 | 218.4 | 366.9 | -148.5 | -208.1 | -78.7 | 0 | 0.005859 | -0.75 | 0 | 8 |
| lab1_f1dead | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab2_f1dead | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab2_f1inv | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab2_f2dead | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab2_f2inv | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab3_f1dead | DetectEpisode | nan | True | 10 | 3.8 | 2.1 | 1.7 | -1.2 | 5.3 | 0.3278 | 0.5625 | 0.09 | 0.4371 | 8 |
| lab3_f1inv | DetectEpisode | nan | True | 10 | 3.9 | 0.9 | 3 | 1 | 5.2 | 0.0006 | 0.03125 | 0.53 | 0.0048 | 8 |
| lab3_f2dead | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab3_f2inv | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab3_f1dead_z2 | DetectEpisode | nan | True | 10 | 0.9 | 1.3 | -0.4 | -1.6 | 0.8 | 0.5848 | 0.6562 | -0.25 | 0.6092 | 8 |
| lab3_f1inv_z2 | DetectEpisode | nan | True | 10 | 0.9 | 3.9 | -3 | -7.7 | -0.2 | 0.021 | 0.09375 | -0.32 | 0.084 | 8 |
| lab3_f1bdead | DetectEpisode | nan | True | 10 | 8 | 6.9 | 1.1 | 0 | 2.7 | 0.2042 | 0.5 | 0.2 | 0.3277 | 8 |
| lab3_f1binv | DetectEpisode | nan | True | 9 | 7.444 | 7.222 | 0.2222 | 0 | 0.5556 | 0.2048 | 0.5 | 0.1111 | 0.3277 | 8 |
| lab2_f1bdead | DetectEpisode | nan | True | 10 | 6 | 6.7 | -0.7 | -3.2 | 1.9 | 0.6092 | 0.6875 | -0.19 | 0.6092 | 8 |
| lab2_f1binv | DetectEpisode | nan | True | 10 | 7.6 | 6.1 | 1.5 | 0 | 3.2 | 0.0546 | 0.2188 | 0.12 | 0.1456 | 8 |
| labmon_f1dead | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| lab3_f2dead_lowsun | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |
| labmon2_f2dead_lowsun | DetectEpisode | nan | False | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | nan | 0 |

Source: `analysis/out_phase2_registered/phase2_recovery_paired.csv`


**Per-cell means with 95% bootstrap CI:**

| profile | mode | n_runs | recovery_tier | RecoveryEpisodes_mean | RecoveryEpisodes_ci_lo | RecoveryEpisodes_ci_hi | DetectEpisode_mean | DetectEpisode_ci_lo | DetectEpisode_ci_hi | greedy_goal_rate_mean | source_run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lab1_f1dead | ql_false | 10 | ill_posed | 107.2 | 94 | 122.7 | 0 | 0 | 0 | 0 | phase2_results_v6/recovery_root |
| lab1_f1dead | ql_true | 10 | ill_posed | 177.8 | 149.7 | 210.1 | 0 | 0 | 0 | 0 | phase2_results_v6/recovery_root |
| lab2_f1bdead | ql_false | 10 | confirmatory | 297.5 | 209.6 | 402.1 | 6.7 | 5 | 8 | 0.74 | phase2_ext_results/recovery_root |
| lab2_f1bdead | ql_true | 10 | confirmatory | 70.8 | 57.7 | 84.9 | 6 | 4.3 | 7.5 | 1 | phase2_ext_results/recovery_root |
| lab2_f1binv | ql_false | 10 | descriptive | 333.8 | 281.1 | 383.7 | 6.1 | 4.3 | 7.7 | 0.45 | phase2_binv_backfill/phase2-consolidated/recovery_root |
| lab2_f1binv | ql_true | 10 | descriptive | 268.9 | 150 | 408.9 | 7.6 | 7.3 | 7.9 | 0.65 | phase2_binv_backfill/phase2-consolidated/recovery_root |
| lab2_f1dead | ql_false | 10 | ill_posed | 303.8 | 259.8 | 344.5 | 0 | 0 | 0 | 0.045 | phase2_results_v6/recovery_root |
| lab2_f1dead | ql_true | 10 | ill_posed | 489.7 | 421.8 | 583.4 | 0 | 0 | 0 | 0.07 | phase2_results_v6/recovery_root |
| lab2_f1inv | ql_false | 10 | ill_posed | 225 | nan | nan | 0 | 0 | 0 | 0.015 | phase2_results_v6/recovery_root |
| lab2_f1inv | ql_true | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.03 | phase2_results_v6/recovery_root |
| lab2_f2dead | ql_false | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.06 | phase2_results_v6/recovery_root |
| lab2_f2dead | ql_true | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.095 | phase2_results_v6/recovery_root |
| lab2_f2inv | ql_false | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.01 | phase2_results_v6/recovery_root |
| lab2_f2inv | ql_true | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.015 | phase2_results_v6/recovery_root |
| lab3_f1bdead | ql_false | 10 | confirmatory | 488.6 | 82.8 | 1246 | 6.9 | 5.3 | 8 | 1 | phase2_ext_results/recovery_root |
| lab3_f1bdead | ql_true | 10 | confirmatory | 62.1 | 54.9 | 70.5 | 8 | 8 | 8 | 0.99 | phase2_ext_results/recovery_root |
| lab3_f1binv | ql_false | 10 | confirmatory | 962.7 | 180 | 2073 | 7.3 | 6.1 | 8 | 0.97 | phase2_ext_results/recovery_root |
| lab3_f1binv | ql_true | 9 | confirmatory | 112 | 89.11 | 135.1 | 7.444 | 6.333 | 8 | 0.95 | phase2_ext_results/recovery_root |
| lab3_f1dead | ql_false | 10 | confirmatory | 270.5 | 209.9 | 344.1 | 2.1 | 0.8 | 3.6 | 0.945 | phase2_lab3f1dead_replication/run_28913465680/recovery_root |
| lab3_f1dead | ql_true | 10 | confirmatory | 149.4 | 126.3 | 177 | 3.8 | 1 | 7.2 | 0.91 | phase2_lab3f1dead_replication/run_28913465680/recovery_root |
| lab3_f1dead_z2 | ql_false | 10 | confirmatory | 247 | 209.3 | 283.8 | 1.3 | 0.5 | 2.3 | 0.94 | phase2_ext_results/recovery_root |
| lab3_f1dead_z2 | ql_true | 10 | confirmatory | 151.3 | 132.6 | 170.5 | 0.9 | 0 | 2 | 0.845 | phase2_ext_results/recovery_root |
| lab3_f1inv | ql_false | 10 | descriptive | 1592 | 1219 | 1877 | 0.9 | 0 | 1.9 | 0.265 | phase2_ext_results/recovery_root |
| lab3_f1inv | ql_true | 10 | descriptive | 1538 | 1047 | 1943 | 3.9 | 2 | 6 | 0.295 | phase2_ext_results/recovery_root |
| lab3_f1inv_z2 | ql_false | 10 | descriptive | 1585 | 1123 | 1980 | 3.9 | 0.9 | 8.5 | 0.375 | phase2_ext_results/recovery_root |
| lab3_f1inv_z2 | ql_true | 10 | descriptive | 1447 | 990 | 1844 | 0.9 | 0 | 1.9 | 0.325 | phase2_ext_results/recovery_root |
| lab3_f2dead | ql_false | 10 | ill_posed | 2861 | 2621 | 3125 | 0 | 0 | 0 | 0.37 | phase2_results_v6/recovery_root |
| lab3_f2dead | ql_true | 10 | ill_posed | 2168 | 1918 | 2416 | 0 | 0 | 0 | 0.36 | phase2_results_v6/recovery_root |
| lab3_f2dead_lowsun | ql_false | 10 | confirmatory | 134.3 | 107.6 | 163.1 | 0 | 0 | 0 | 1 | phase2_lowsun_results/run_28866807391/recovery_root |
| lab3_f2dead_lowsun | ql_true | 10 | confirmatory | 69.4 | 59 | 80.2 | 0 | 0 | 0 | 1 | phase2_lowsun_results/run_28866807391/recovery_root |
| lab3_f2inv | ql_false | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.195 | phase2_results_v6/recovery_root |
| lab3_f2inv | ql_true | 10 | ill_posed | nan | nan | nan | 0 | 0 | 0 | 0.2 | phase2_results_v6/recovery_root |
| labmon2_f2dead_lowsun | ql_false | 10 | confirmatory | 366.9 | 341.9 | 392.1 | 0 | 0 | 0 | 0.925 | phase2_lowsun_results/run_28884717500/recovery_root |
| labmon2_f2dead_lowsun | ql_true | 10 | confirmatory | 218.4 | 165.9 | 279.4 | 0 | 0 | 0 | 0.99 | phase2_lowsun_results/run_28884717500/recovery_root |
| labmon_f1dead | ql_false | 10 | confirmatory | 59.2 | 57.6 | 61.2 | 0 | 0 | 0 | 1 | labmon_ci_results/phase2-consolidated/recovery_root |
| labmon_f1dead | ql_true | 10 | confirmatory | 53 | 51.4 | 55 | 0 | 0 | 0 | 1 | labmon_ci_results/phase2-consolidated/recovery_root |

Source: `analysis/out_phase2_registered/phase2_recovery_ci.csv`


## 3. Phase 3 — process-dynamics / response-delay learning [NEW era]

Canonical run 27621106006 (n = 10 replicas, 8 probes/actuator), profiles `lab2_slow`, `lab3_slow`.


**Learned delay vs ground truth:**

| profile | mode | n_actuators | n_instantaneous | n_delayed | slowest_label | slowest_learned_ticks | ground_truth_ticks | abs_err_ticks | rel_err_pct |
|---|---|---|---|---|---|---|---|---|---|
| lab2_slow | ql_false | 4 | 2 | 2 | SetZ2Blinds=ON | 12.11 | 12 | 0.1125 | 0.94 |
| lab2_slow | ql_true | 4 | 2 | 2 | SetZ1Blinds=ON | 12.19 | 12 | 0.1875 | 1.56 |
| lab3_slow | ql_false | 5 | 3 | 2 | SetZ1Blinds=ON | 12.21 | 12 | 0.2125 | 1.77 |
| lab3_slow | ql_true | 5 | 3 | 2 | SetZ1Blinds=ON | 12.21 | 12 | 0.2125 | 1.77 |

Source: `phase3_download_n10/phase3-consolidated/analysis/out/phase3_delay_accuracy.csv`


**Temporal-goal compliance paired tests (ql_true − ql_false):**

| profile | metric | n_paired | ql_true_mean | ql_false_mean | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab2_slow | overall_compliance | 10 | 1 | 0.5 | 0.5 | 0.5 | 0.5 | 0 | 0.001953 | 1 | 0 | 2 |
| lab3_slow | overall_compliance | 10 | 1 | 0.5 | 0.5 | 0.5 | 0.5 | 0 | 0.001953 | 1 | 0 | 2 |
| lab2_slow | tight_compliance | 10 | 1 | 0 | 1 | 1 | 1 | 0 | 0.001953 | 1 | 0 | 2 |
| lab3_slow | tight_compliance | 10 | 1 | 0 | 1 | 1 | 1 | 0 | 0.001953 | 1 | 0 | 2 |
| lab2_slow | loose_compliance | 10 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 2 |
| lab3_slow | loose_compliance | 10 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 2 |
| lab2_slow | total_energy | 10 | 3.2 | 0 | 3.2 | 3 | 3.5 | 0 | 0.001953 | 1 | 0 | 2 |
| lab3_slow | total_energy | 10 | 3.3 | 0 | 3.3 | 3 | 3.6 | 0 | 0.001953 | 1 | 0 | 2 |

Source: `phase3_download_n10/phase3-consolidated/analysis/out/phase3_compliance_paired.csv`


**Compliance / energy means with 95% CI:**

| profile | mode | n_replicas | overall_compliance_mean | tight_compliance_mean | loose_compliance_mean | total_energy_mean | mean_actual_delay_mean |
|---|---|---|---|---|---|---|---|
| lab2_slow | ql_false | 10 | 0.5 | 0 | 1 | 0 | 60.58 |
| lab2_slow | ql_true | 10 | 1 | 1 | 1 | 3.2 | 33.33 |
| lab3_slow | ql_false | 10 | 0.5 | 0 | 1 | 0 | 60.58 |
| lab3_slow | ql_true | 10 | 1 | 1 | 1 | 3.3 | 33.08 |

Source: `phase3_download_n10/phase3-consolidated/analysis/out/phase3_compliance_ci.csv`


## 4. Phase 4 — energy-aware goals + KG-QL vs LLM [NEW era]

Canonical run 27905392725 (n = 20 seeds), profiles `lab4`, `lab5`; LLM baseline backend `general` (offline).


**Energy paired tests (ql_true − ql_false, seed-paired):**

| profile | metric | n_paired | ql_true_mean | ql_false_mean | Δ (true−false) | ci_lo | ci_hi | p_bootstrap | p_wilcoxon | Cliff's δ | BH q | bh_family_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lab4 | goal_rate | 20 | 1 | 0.9769 | 0.02312 | 0.009375 | 0.03938 | 0.0002 | 0.01406 | 0.35 | 0.00024 | 6 |
| lab4 | energy_compliance | 20 | 1 | 0.9769 | 0.02312 | 0.009375 | 0.03938 | 0.0002 | 0.01406 | 0.35 | 0.00024 | 6 |
| lab5 | goal_rate | 20 | 0.9906 | 0.975 | 0.01562 | -0.003125 | 0.03438 | 0.1474 | 0.1317 | 0.2075 | 0.1474 | 6 |
| lab5 | energy_compliance | 20 | 0.7844 | 0.6831 | 0.1012 | 0.06561 | 0.1381 | 0 | 0.0009286 | 0.6875 | 0 | 6 |
| lab5 | mean_steady_power | 20 | 1.148 | 1.539 | -0.3912 | -0.5988 | -0.1831 | 0.0002 | 0.003782 | -0.4725 | 0.00024 | 6 |
| lab5 | over_budget_rate | 20 | 0.2079 | 0.2982 | -0.09033 | -0.1313 | -0.05074 | 0 | 0.0009162 | -0.6425 | 0 | 6 |

Source: `phase4_n20_download/phase4-consolidated/analysis/out/phase4_energy_paired.csv`


**Per-(profile, mode) means with 95% CI:**

| profile | mode | n_replicas | goal_rate_mean | energy_compliance_mean | energy_compliance_ci_lo | energy_compliance_ci_hi | mean_steady_power_mean | over_budget_rate_mean |
|---|---|---|---|---|---|---|---|---|
| lab4 | ql_false | 20 | 0.9769 | 0.9769 | 0.9606 | 0.9906 | nan | nan |
| lab4 | ql_true | 20 | 1 | 1 | 1 | 1 | nan | nan |
| lab4 | rule_based | 20 | 1 | 1 | 1 | 1 | nan | nan |
| lab5 | ql_false | 20 | 0.975 | 0.6831 | 0.6481 | 0.72 | 1.539 | 0.2982 |
| lab5 | ql_true | 20 | 0.9906 | 0.7844 | 0.7688 | 0.8 | 1.148 | 0.2079 |
| lab5 | rule_based | 20 | 1 | 1 | 1 | 1 | 0.875 | 0 |

Source: `phase4_n20_download/phase4-consolidated/analysis/out/phase4_energy_ci.csv`


**LLM baseline summary:**

| profile | backend | n_seeds | n_scenarios | goal_rate | energy_compliance | mean_steady_power | mean_steps | mean_redundant |
|---|---|---|---|---|---|---|---|---|
| lab4 | general | 20 | 16 | 1 | 1 | 1.562 | 1.125 | 0.375 |
| lab5 | general | 20 | 16 | 1 | 0.5563 | 3.416 | 0.6875 | 0.0625 |

Source: `phase4_n20_download/phase4-consolidated/analysis/out/phase4_llm_summary.csv`


## 5. Figure index

- `docs/_audit/figures/p1_kgonly_lab1_curves.png`
- `docs/_audit/figures/p1_kgonly_lab2_curves.png`
- `docs/_audit/figures/p1_kgonly_lab3_curves.png`
- `docs/_audit/figures/p1_xzonemid_lab3_curves.png`
- `docs/_audit/figures/p2_detection_bars.png`
- `docs/_audit/figures/p2_recovery_bars.png`
- `docs/_audit/figures/p3_delay_and_compliance.png`
- `docs/_audit/figures/p4_energy_steady_power.png`
- `docs/_audit/figures/p4_kg_vs_llm.png`

## 6. Skipped (missing sources)

None — all canonical sources present.
