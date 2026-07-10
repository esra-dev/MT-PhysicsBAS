# Phase 1 Results Evidence

Evidence-extraction product only. Do not convert this file into thesis prose
without checking the cited primary locators.

## Source Anchors

| Source id | Label | Product scope | Source locator |
|---|---|---|---|
| S6P1-PROTOCOL | [DIRECT] | AUDIT HISTORY; MANUSCRIPT EVIDENCE | local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L13-L18; local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L23-L47; local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L130-L157 |
| S6P1-METHODS | [DIRECT] | MANUSCRIPT EVIDENCE | local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L47-L151 |
| S6P1-TABLES | [DERIVED] | AUDIT HISTORY; MANUSCRIPT EVIDENCE | Output: local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481. Script: local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520. Exact command: `node paper_notes/phase1_extract_tables.mjs paper_notes/PHASE1_TABLES.csv`. Inputs: local-tree-sha256:75a9c8ccea76c0bd52cef6cd0dad34bf2f4ffe8c13501690b59f8cbe186b52a9:phase1_xzone_asis; local-tree-sha256:e9d706b2f7828bb65bdb9d091269681b0f9acddd263c7d438777340b8a5b5343:phase1_xzone_bumped; local-tree-sha256:f80a117fac11c1db5ce3d545b04a4e418590f97c66d3ccc8ff44c6c8cc71152e:phase1_xzone_bumped_s11_20; local-tree-sha256:7c114de88374bb003264a994a50db753edc89113258a4a9a1d7f64831911c638:phase1_xzone_ablation |
| S6P1-ACTIONS-SNAPSHOT | [DIRECT] | AUDIT HISTORY | local-sha256:865583cb352036e55a15a71b74a5057cde62c49cf4abbce5eeb9694ba7b86456:paper_notes/ACTIONS_RUNS_20260617T074205Z.csv:rows 85,88,89,92,93,94,97,99,100,102,104; named columns databaseId, workflowName, event, status, conclusion, headBranch, headSha, createdAt, updatedAt, url |
| S6P1-ACTIONS-STAGE6 | [DIRECT] | AUDIT HISTORY | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:L1-L12 |
| S6P1-LOCAL-ROOTS | [DIRECT] | AUDIT HISTORY; MANUSCRIPT EVIDENCE | local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 5-8; named columns row_id,path,provenance_class,verification_status,content_hash,file_count,byte_count,classification_basis,limitations |
| S6P1-GIT-AUDIT | [DIRECT] | AUDIT HISTORY | local-sha256:6d6d994bb1a4a73680f18b3fcb52136d53279fbe0611f2543e945e34e9b1be27:paper_notes/GIT_AUDIT_20260617T074205Z.txt:L31-L32; local-sha256:6d6d994bb1a4a73680f18b3fcb52136d53279fbe0611f2543e945e34e9b1be27:paper_notes/GIT_AUDIT_20260617T074205Z.txt:L45-L54; local-sha256:6d6d994bb1a4a73680f18b3fcb52136d53279fbe0611f2543e945e34e9b1be27:paper_notes/GIT_AUDIT_20260617T074205Z.txt:L142-L145 |
| S6P1-ORIGIN-RESULTS | [DERIVED] | AUDIT HISTORY | local-sha256:0ba4c44ae05443c525fed6bf5c66ae582da6413178c149e263e8e56bf6242e61:paper_notes/PHASE1_ORIGIN_RESULTS_STAGE6.txt:L1-L79. Exact command in file line 2. |
| S6P1-BASELINE-MANIFEST | [DIRECT] | AUDIT HISTORY | origin/results@791626314fb47d5324ba3336daed5906ef2e53b1:results-20260611-123741-phase1_baseline-7ac37a1/RUN_MANIFEST.json:L2-L18 |

## AUDIT HISTORY

Chronology is provenance-only. Do not copy this sequence into manuscript
Evaluation unless a reproducibility appendix needs it.

### Visible Phase 1 Actions Runs

| Run | Label | Branch/head | Status | Artifact/job count | Evidence status | Source locator |
|---|---|---|---|---|---|---|
| 27305796237 | [SUPERSEDED] | `main` @ `7543d15a6e6d36842ffd82f60b488b1a6dde99cd` | success | artifacts `152`, jobs `152` | Early clean-lab run, superseded by later method/result variants. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 2; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27336756264 | [SUPERSEDED] | `main` @ `55c01063165bf06f53dd6359c20fcb8940af5cc0` | success | artifacts `152`, jobs `152` | Factorial/KG-only lineage, superseded for final clean-lab result authority. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 3; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27339902999 | [DIRECT] | `main` @ `55c01063165bf06f53dd6359c20fcb8940af5cc0` | failure | artifacts `60`, jobs `63` | Failed run retained in AUDIT HISTORY only. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 4; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27342571251 | [SUPERSEDED] | `main` @ `7ac37a10fe3b3c23bc2b54159c40142fd367e821` | success | artifacts `102`, jobs `102` | Init-bonus/baseline lineage, not final cross-zone authority. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 5; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27344626272 | [SUPERSEDED] | `main` @ `7ac37a10fe3b3c23bc2b54159c40142fd367e821` | success | artifacts `152`, jobs `152` | `phase1_baseline` result root was committed to `origin/results`; superseded for final cross-zone results. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 6; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount; origin/results@791626314fb47d5324ba3336daed5906ef2e53b1:results-20260611-123741-phase1_baseline-7ac37a1/RUN_MANIFEST.json:L2-L18 |
| 27347962788 | [DIRECT] | `main` @ `7ac37a10fe3b3c23bc2b54159c40142fd367e821` | failure | artifacts `151`, jobs `152` | Failed run retained in AUDIT HISTORY only. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 7; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27440842780 | [SUPERSEDED] | `kg-crosszone-coupling` @ `866297d54750c91f4595962f9c975d2f1704f629` | success | artifacts `152`, jobs `152` | As-is cross-zone magnitude control; lab3 negative result superseded by bumped physics for final result authority, but retained as A/B control. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 8; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27461188614 | [DIRECT] | `kg-crosszone-coupling-bump` @ `8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1` | success | artifacts `152`, jobs `152` | Primary bumped targeted seed block. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 9; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |
| 27462446044 | [DIRECT] | `kg-crosszone-coupling-bump` @ `8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1` | success | artifacts `154`, jobs `152` | Independent bumped targeted replication seed block; earlier local prose that states `152` artifacts for this run is superseded for this count. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 10; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount,notes |
| 27463565168 | [DIRECT] | `kg-crosszone-ablation` @ `c633718766afb0c77f8fabd942f6e0aecdfa923d` | failure | artifacts `NOT FOUND`, jobs `NOT FOUND` | Failed ablation pre-run; Stage 6 API count query was rate-limited before counts were captured. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 11; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount,notes |
| 27464846574 | [DIRECT] | `kg-crosszone-ablation` @ `e8d63e09be504f1dc206737ca8feb05299fe1031` | success | artifacts `152`, jobs `152` | Untargeted cross-zone mechanism ablation. | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:row 12; named columns runId,headBranch,headSha,conclusion,artifactCount,jobCount |

### Result-Set Authority

| Result source | Label | Role | Authority status | Source locator |
|---|---|---|---|---|
| Result tags `results-20260610-214349-phase1-7543d15`, `results-20260611-100516-phase1_kg_only-55c0106`, `results-20260611-114056-phase1_kg_only_ib5-7ac37a1`, `results-20260611-123741-phase1_baseline-7ac37a1` | [SUPERSEDED] | Historical source-code/result-lineage tags. | Audit only; tags point at source commits and do not contain the later cross-zone analysis roots. | local-sha256:6d6d994bb1a4a73680f18b3fcb52136d53279fbe0611f2543e945e34e9b1be27:paper_notes/GIT_AUDIT_20260617T074205Z.txt:L142-L145 |
| `origin/results` commit `791626314fb47d5324ba3336daed5906ef2e53b1` | [SUPERSEDED] | Committed `phase1_baseline` result root. | Audit only for final Phase 1 cross-zone findings; manifest says `runMode=phase1_baseline`, profiles `lab1/lab2/lab3`, benchmark modes `rule_based/ql_false/ql_true`, source SHA `7ac37a10fe3b3c23bc2b54159c40142fd367e821`, artifact count `74`. | origin/results@791626314fb47d5324ba3336daed5906ef2e53b1:results-20260611-123741-phase1_baseline-7ac37a1/RUN_MANIFEST.json:L2-L18 |
| `origin/results` current tree | [UNRESOLVED] | Search for later cross-zone roots. | `phase1_xzone_*` and run-ID-named cross-zone roots were `NOT FOUND`; only the `results-20260611-123741-phase1_baseline-7ac37a1` root matched the Phase 1 search pattern. | local-sha256:0ba4c44ae05443c525fed6bf5c66ae582da6413178c149e263e8e56bf6242e61:paper_notes/PHASE1_ORIGIN_RESULTS_STAGE6.txt:L1-L79 |
| `phase1_xzone_asis` | [SUPERSEDED] | As-is cross-zone magnitude control. | Retain as A/B control and limitation evidence; do not use as final bumped lab3 performance authority. | local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:row 5; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations |
| `phase1_xzone_bumped` | [DIRECT] | Primary bumped targeted run, seeds `1..10`. | Active Stage 6 manuscript evidence, with local-root and ZIP-verification limitations. | local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:row 6; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations |
| `phase1_xzone_bumped_s11_20` | [DIRECT] | Independent bumped targeted replication, seeds `11..20`. | Active Stage 6 replication evidence, with local-root and ZIP-verification limitations. | local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:row 7; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations |
| `phase1_xzone_ablation` | [DIRECT] | Untargeted cross-zone mechanism ablation. | Active Stage 6 mechanism evidence, with local-root and ZIP-verification limitations. | local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:row 8; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations |

### Derived Extraction Record

| Record | Label | Evidence |
|---|---|---|
| S6P1-DERIVE-001 | [DERIVED] | `PHASE1_TABLES.csv` rows `P1T-0001` through `P1T-0480` were generated by `node paper_notes/phase1_extract_tables.mjs paper_notes/PHASE1_TABLES.csv`. The table records deterministic recomputation status from raw benchmark/training CSVs; all included final-policy means, final-policy paired mean differences, learning-speed condition means, and learning-speed paired mean differences are marked either `MEAN_MATCH_FROM_RAW` or `MEAN_DIFF_MATCH_FROM_RAW`. Source: local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481; script: local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520. |
| S6P1-DERIVE-002 | [UNRESOLVED] | Bootstrap confidence intervals, bootstrap p-values, Wilcoxon p-values, Cliff's delta, and BH q-values were read from the Phase 1 analysis CSVs and were not independently resampled in Stage 6. Each `PHASE1_TABLES.csv` row names the analysis CSV row and marks this limitation in `notes`. Example source: local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 210; named columns table_row_id=P1T-0209,source_locator,value,ci_lo,ci_hi,p_value,q_bootstrap_bh,notes |

## MANUSCRIPT EVIDENCE

### Experiment Records

| Experiment | Label | Research question | Prior expectation | Baseline/control | Treatment | Variables and controls | Metrics/statistics | Unexpected or follow-up | Status | Result handling |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-P1-ASIS | [SUPERSEDED] | Does the cross-zone KG prior help before simulator magnitude bump? | KG should help where cross-zone structure is learnable. | `ql_false` in as-is lab3, same seeds. | `ql_true` with `phase1_kg_xzone` as-is magnitude. | Same run mode and seeds; cross-zone magnitude remains pre-bump. | Learning-speed and final-policy metrics from analysis CSV rows in `P1-ASIS`. | Lab3 primary `auc_goal` is worse for KG and cycling is worse; this motivates the bumped A/B. | POST_HOC_EXPLORATORY | Use only as historical control and limitation evidence. |
| EXP-P1-BUMP | [DIRECT] | Does bumped cross-zone physics remove the as-is lab3 penalty while preserving the lab2 anchor? | Lab2 anchor should remain; lab3 penalty should reduce when cross-zone effects become rank-moving. | `ql_false` within `phase1_xzone_bumped`. | `ql_true` within `phase1_xzone_bumped`. | Same seed block recorded in EV-P1-RES-001; same workflow; bumped lab3 simulator; PBRS and adaptive trust off per Stage 5 methods. | `summary_table_ci`, `paired_tests`, `learning_speed_tests`; bootstrap/BH values from analysis rows. | Lab2 remains strong; lab3 `auc_goal` is no longer BH-significant while `auc_reward` remains positive. | POST_HOC_EXPLORATORY | Primary active Phase 1 result set. |
| EXP-P1-REPL | [DIRECT] | Does the bumped targeted pattern replicate on fresh seeds? | Lab2 anchor should replicate; lab3 reward advantage should persist. | `ql_false` within `phase1_xzone_bumped_s11_20`. | `ql_true` within `phase1_xzone_bumped_s11_20`. | Fresh seed block recorded in EV-P1-RES-005; same bumped targeted configuration. | Same analysis CSV families and Stage 6 deterministic recomputation table. | Lab2 `auc_goal` and lab3 `auc_reward` replicate; lab3 `auc_goal` remains non-significant. | POST_HOC_EXPLORATORY | Active replication evidence. |
| EXP-P1-ABL | [DIRECT] | Is lab3 reward benefit larger when the cross-zone bonus is KG-targeted rather than untargeted? | Targeted structural knowledge should outperform an equal-budget random target control. | Untargeted `phase1_kg_xzone_rand` and comparison to targeted `phase1_xzone_bumped`. | KG-targeted cross-zone bonus in `phase1_xzone_bumped`. | Bumped simulator; seeds `1..10`; same bonus magnitude; ablation changes target correctness. | `learning_speed_tests` plus final-policy rows; compare targeted and untargeted rows, not pooled prose. | Untargeted lab3 `auc_reward` remains positive but is smaller than targeted; exact ratio is not used as a manuscript claim here. | POST_HOC_EXPLORATORY | Active mechanism evidence, not standalone primary anchor. |

### Key Numeric Evidence

All rows below are ql_true minus ql_false unless stated otherwise. Negative values
are favorable only for lower-is-better metrics; higher-is-better/lower-is-better
directions are recorded in `PHASE1_TABLES.csv`.

| Evidence id | Label | Run/root | Profile | Metric | Value and statistical fields | Source locator | Recompute status | Manuscript handling |
|---|---|---|---|---|---|---|---|---|
| EV-P1-RES-001 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab2 | `auc_goal` | value `0.01973991330443482`; CI `[0.014654884961653902,0.024458569523174385]`; q `0.0`; Cliff's delta `1.0`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 210; named columns table_row_id=P1T-0209,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-002 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab2 | `avg_steps` | value `-0.9`; CI `[-1.55,-0.325]`; q `0.0`; Cliff's delta `-0.71`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 189; named columns table_row_id=P1T-0188,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-003 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab2 | `avg_redundant` | value `-0.9825000000000002`; CI `[-1.59003125,-0.39871875000000045]`; q `0.0`; Cliff's delta `-0.72`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 204; named columns table_row_id=P1T-0203,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-004 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab2 | `goal_rate` | value `0.04375`; CI `[0.0125,0.08125]`; q `0.009046153846153846`; Cliff's delta `0.5`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 186; named columns table_row_id=P1T-0185,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-005 | [DIRECT] | `27462446044` / `P1-BUMP-S11-20` | lab2 | `auc_goal` | value `0.018189396465488505`; CI `[0.010586862287429144,0.02734286428809604]`; q `0.0`; Cliff's delta `1.0`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 330; named columns table_row_id=P1T-0329,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-006 | [DIRECT] | `27462446044` / `P1-BUMP-S11-20` | lab2 | `auc_reward` | value `7.67062354118039`; CI `[2.1563012670890274,12.909165555185055]`; q `0.0328`; Cliff's delta `0.6`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 331; named columns table_row_id=P1T-0330,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-007 | [SUPERSEDED] | `27440842780` / `P1-ASIS` | lab3 | `auc_goal` | value `-0.008852950983661201`; CI `[-0.014354784928309416,-0.003034344781593867]`; q `0.0072`; Cliff's delta `-0.67`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 94; named columns table_row_id=P1T-0093,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-008 | [SUPERSEDED] | `27440842780` / `P1-ASIS` | lab3 | `avg_cycling` | value `0.3375`; CI `[0.05625,0.66875]`; q `0.0252`; Cliff's delta `0.5`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 82; named columns table_row_id=P1T-0081,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-009 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab3 | `auc_goal` | value `-0.003751250416805607`; CI `[-0.008019756585528526,0.0006673057685895593]`; q `0.29579999999999995`; Cliff's delta `-0.4`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 214; named columns table_row_id=P1T-0213,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-010 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab3 | `avg_cycling` | value `-0.0375`; CI `[-0.11875,0.0375]`; q `0.6222222222222222`; Cliff's delta `-0.19`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 202; named columns table_row_id=P1T-0201,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-011 | [DIRECT] | `27461188614` / `P1-BUMP-S1-10` | lab3 | `auc_reward` | value `14.258352784261419`; CI `[11.233294014671557,17.19568772924308]`; q `0.0`; Cliff's delta `1.0`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 215; named columns table_row_id=P1T-0214,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-012 | [DIRECT] | `27462446044` / `P1-BUMP-S11-20` | lab3 | `auc_reward` | value `18.85043347782594`; CI `[16.213371123707905,21.188305685228407]`; q `0.0`; Cliff's delta `1.0`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 335; named columns table_row_id=P1T-0334,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-013 | [DIRECT] | `27464846574` / `P1-ABLATION-UNTARGETED` | lab3 | `auc_reward` | value `9.164321440480162`; CI `[4.290295098366126,13.607277425808606]`; q `0.0`; Cliff's delta `0.58`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 455; named columns table_row_id=P1T-0454,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |
| EV-P1-RES-014 | [DIRECT] | `27464846574` / `P1-ABLATION-UNTARGETED` | lab3 | `auc_goal` | value `-0.0063521173724574555`; CI `[-0.01193731243747912,-0.0007835945315104783]`; q `0.05079999999999999`; Cliff's delta `-0.58`. | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 454; named columns table_row_id=P1T-0453,root_id,run_id,profile,metric,value,ci_lo,ci_hi,q_bootstrap_bh,cliffs_delta,source_locator |

### Evidence Records

| Evidence id | Label | Claim status | Evidence record |
|---|---|---|---|
| EV-P1-RESULT-001 | [INTERPRETATION] | ACTIVE | Lab2 is the Phase 1 manuscript anchor because the primary bumped run shows favorable `auc_goal`, `avg_steps`, `avg_redundant`, and `goal_rate`, and the fresh-seed replication repeats favorable `auc_goal`. Numeric support: EV-P1-RES-001 through EV-P1-RES-006. Research status: POST_HOC_EXPLORATORY. |
| EV-P1-RESULT-002 | [INTERPRETATION] | ACTIVE | The as-is lab3 negative primary result is superseded for final lab3 performance claims by the bumped simulator result, but retained as the A/B control and limitation. Numeric support: EV-P1-RES-007 through EV-P1-RES-011. Research status: POST_HOC_EXPLORATORY. |
| EV-P1-RESULT-003 | [INTERPRETATION] | ACTIVE | Bumped lab3 supports a reward-trajectory claim more strongly than a binary goal-trajectory claim: `auc_reward` is favorable in the primary bumped run and replication, while bumped `auc_goal` remains non-significant in both seed blocks. Numeric support: EV-P1-RES-009, EV-P1-RES-011, EV-P1-RES-012, and local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:row 334; named columns table_row_id=P1T-0333,root_id,profile,metric,value,q_bootstrap_bh. |
| EV-P1-RESULT-004 | [INTERPRETATION] | ACTIVE | The untargeted ablation is mechanism evidence, not the primary anchor: untargeted lab3 `auc_reward` remains favorable but is smaller than the targeted bumped row recorded in EV-P1-RES-011. Numeric support: EV-P1-RES-011 and EV-P1-RES-013. |
| EV-P1-RESULT-005 | [UNRESOLVED] | ACTIVE | Exact workflow_dispatch inputs remain `NOT FOUND` for all visible Phase 1 workflow runs, and artifact ZIP byte identity remains `NOT VERIFIED`; Stage 6 recorded live artifact/job counts where available but did not download artifacts. Source: local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:L1-L12. |
| EV-P1-RESULT-006 | [UNRESOLVED] | ACTIVE | Lab3 stale magnitude documentation remains unresolved for scenario/TTL comments and scenario initial rows; Stage 6 result notes do not use those rows as result evidence. Source: local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L85-L89; local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L188-L193. |

## Handoff

Completed in Stage 6:

- [DERIVED] Produced `paper_notes/PHASE1_TABLES.csv` with row-level links to Phase 1 analysis CSVs and deterministic raw-data recomputation status.
- [DIRECT] Captured compact live/API Phase 1 Actions run metadata in `paper_notes/PHASE1_ACTIONS_STAGE6.csv`, with dispatch inputs still `NOT FOUND` and artifact ZIP identity still `NOT VERIFIED`.
- [INTERPRETATION] Selected `phase1_xzone_bumped`, `phase1_xzone_bumped_s11_20`, and `phase1_xzone_ablation` as the active Phase 1 result evidence set, with `phase1_xzone_asis` retained as superseded A/B control evidence.
- [SUPERSEDED] Marked early Phase 1 result tags and `origin/results` `phase1_baseline` as audit history for final Phase 1 result claims.

Unresolved issues:

- [UNRESOLVED] Artifact ZIP byte identity remains unverified for all local Phase 1 roots.
- [UNRESOLVED] Exact workflow_dispatch inputs remain `NOT FOUND`.
- [UNRESOLVED] Stage 6 did not independently recompute bootstrap intervals, p-values, Wilcoxon values, Cliff's delta, or BH q-values; these remain analysis-CSV sourced.
- [UNRESOLVED] Lab3 stale TTL/scenario magnitude documentation remains open; use simulator JSON and selected result CSVs, not stale scenario rows, for Phase 1 results.

Next stage must read, in order:

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/PHASE1_METHODS.md`
3. `paper_notes/PHASE1_RESULTS.md`
4. `paper_notes/PHASE1_TABLES.csv`
5. `paper_notes/PHASE1_FIGURES.md`
6. `paper_notes/PHASE1_ACTIONS_STAGE6.csv`
7. `paper_notes/PHASE1_ORIGIN_RESULTS_STAGE6.txt`
8. `paper_notes/SOURCE_LEDGER.csv`
9. `paper_notes/CLAIM_LEDGER.csv`
10. `paper_notes/RUN_LEDGER.csv`
11. `paper_notes/EVIDENCE_GAPS.md`
