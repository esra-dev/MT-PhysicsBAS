# Phase 2 Results Evidence Notes

Stage: `8`
Created: `2026-06-17T15:10:00Z`
Scope: evidence extraction only. This file is not polished thesis prose.

## Control Record

| item | evidence |
|---|---|
| Protocol read | [DIRECT] `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L13-L18`; `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L23-L47`; `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L130-L157`. |
| Stage 7 methods read | [DIRECT] `local-sha256:8602e69ecd785f3a5818c18ff55fe38e79c2984e416a0d4136e1d68c7a43ac1b:paper_notes/PHASE2_METHODS.md:L1-L155`. |
| Final-result input extraction | [DERIVED] `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138` was archived by `git archive -o paper_notes\stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f.tar 22a448be5d9829751badd341904e36ed582f091f phase2/27547019772-20260615-183138`, extracted into `paper_notes/stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f`, and hashed as `TREE-SHA256-V1=11ce481791cf90a067709ed66fb30a388a993dd7c39fea48dba64c835eb06907`, `file_count=362`, `byte_count=9866470`; tar SHA-256 `283e3c3a3c6d143ac19efb1631dde8ad6cd929a8724614d1d52cc1b85453c858`. |
| Stage 8 extraction script | [DERIVED] `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L1-L488`; exact command: `node paper_notes\phase2_extract_results.mjs --root paper_notes\stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f --out paper_notes\PHASE2_TABLES.csv`; Node.js `22.14.0`. |
| Stage 8 extracted table | [DERIVED] `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`; contains `521` data rows; verification statuses: `306` deterministic-from-raw rows, `99` deterministic/exact-test rows, `116` direct analysis-output bootstrap rows not independently resampled. |

## Source Anchors

| id | label | immutable locator |
|---|---|---|
| S8-P2-FINAL-CI | Final v5 CI table | [DIRECT] `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19`. |
| S8-P2-FINAL-PAIRED | Final v5 paired table | [DIRECT] `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| S8-P2-RAW-VERIFY | Stage 8 raw-row verification table | [DERIVED] `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`; script and command in Control Record. |
| S8-P2-ACTIONS | Fresh run/action/job evidence | [DIRECT] `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:L1-L10`; `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:L1-L243`. |
| S8-P2-METHODS | Final v5 method authority | [DIRECT] `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L1-L40`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L55-L92`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L243-L316`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L360-L404`. |

## Audit History

Do not use this chronology as manuscript narrative by default.

| result generation | status | evidence record |
|---|---|---|
| v1, run `27470382799`, result commit `cd30e5d2ed15afabab97589ba2eea53fbf6e6cb0` | [SUPERSEDED] | Initial result table has `5` runs per row and includes `SetSpotlight` in lab3 inverted true-arm rows: `origin/results@cd30e5d2ed15afabab97589ba2eea53fbf6e6cb0:phase2/27470382799-20260613-180052/analysis_out/phase2_recovery_ci.csv:row 15; named columns profile=lab3_f1inv; mode=ql_true; n_runs=5; defect_component=http://example.org/was#SetSpotlight;http://example.org/was#SetZ1Light`; `origin/results@cd30e5d2ed15afabab97589ba2eea53fbf6e6cb0:phase2/27470382799-20260613-180052/analysis_out/phase2_recovery_ci.csv:row 19; named columns profile=lab3_f2inv; mode=ql_true; n_runs=5; defect_component=http://example.org/was#SetSpotlight;http://example.org/was#SetZ1Light;http://example.org/was#SetZ2Light`. |
| v2, run `27499405083`, result commit `105be2b1bb8dc7472ded394c165bd4c76a76935a` | [SUPERSEDED] | Policy-stability result table has `10` runs per row but still includes `SetSpotlight` in lab3_f2inv true arm: `origin/results@105be2b1bb8dc7472ded394c165bd4c76a76935a:phase2/27499405083-20260614-170453/analysis_out/phase2_recovery_ci.csv:row 19; named columns profile=lab3_f2inv; mode=ql_true; n_runs=10; defect_component=http://example.org/was#SetSpotlight;http://example.org/was#SetZ1Light;http://example.org/was#SetZ2Light`. |
| v3, run `27507087176`, result commit `bf8adefacc0f9f738e359079c7619f04427fe565` | [SUPERSEDED] | Goal-rate-certified result table adds `well_posed_recovery` and greedy goal-rate columns, but lab3_f2inv true arm still includes `SetSpotlight`: `origin/results@bf8adefacc0f9f738e359079c7619f04427fe565:phase2/27507087176-20260614-221944/analysis_out/phase2_recovery_ci.csv:row 19; named columns profile=lab3_f2inv; mode=ql_true; n_runs=10; defect_component=http://example.org/was#SetSpotlight;http://example.org/was#SetZ2Light`. |
| v4, run `27529585379`, result commit `e9b9e3529cd71fce3ad9dfe5fa29c64793898b2e` | [SUPERSEDED] | Primary-attribution confirmation still leaves `SetSpotlight` in lab3_f2inv true arm: `origin/results@e9b9e3529cd71fce3ad9dfe5fa29c64793898b2e:phase2/27529585379-20260615-112824/analysis_out/phase2_recovery_ci.csv:row 19; named columns profile=lab3_f2inv; mode=ql_true; n_runs=10; defect_component=http://example.org/was#SetSpotlight;http://example.org/was#SetZ1Light;http://example.org/was#SetZ2Light`. |
| v5, run `27547019772`, result commit `22a448be5d9829751badd341904e36ed582f091f` | [DIRECT] | Final selected v5 table has no `SetSpotlight` rows; lab3_f2dead and lab3_f2inv rows report only `SetZ1Light;SetZ2Light`: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:rows 16-19; named columns profile,mode,n_runs,defect_component,detection_rate,n_detected`. |

## Workflow Evidence

| item | label | evidence |
|---|---|---|
| Run status | [DIRECT] Run `27547019772` is `completed` with conclusion `success`, event `workflow_dispatch`, head SHA `985c7a18558b6d5cb96c018a395b0aae6389f410`, attempt `2`, created `2026-06-15T12:43:10Z`, updated `2026-06-15T18:31:44Z`. Locator: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 2; named columns recordType=run; key=run_metadata; value`. |
| Complete job inventory | [DIRECT] Fresh Stage 8 capture reports `242` jobs: `180` adapt, `60` clean, `1` aggregate, `1` compile. Locators: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:rows 3-7; named columns recordType=job_count,key,value`; job-row ranges: `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:rows 2-243; named columns jobClass,jobName,jobId,status,conclusion`. |
| Aggregate job proof | [DIRECT] Aggregate job `81495756019`, `Aggregate recovery & publish`, completed success from `2026-06-15T18:31:10Z` to `2026-06-15T18:31:43Z`. Locators: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 8; named columns recordType=aggregate_job,key,value`; `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:row 182; named columns jobId,jobName,jobClass,status,conclusion,startedAt,completedAt,url`. |
| Consolidated artifact metadata | [DIRECT] Artifact `phase2-consolidated`, ID `7647220538`, size `1896365`, digest `sha256:8be79a29338d49ca54a869b6e610fbec2a7fc074cc375a74b1658344657ae102`, created `2026-06-15T18:31:38Z`, expires `2026-09-13T17:41:10Z`, run artifact total `243`. Locator: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 9; named columns recordType=artifact,key,value`. |
| Artifact ZIP identity | [UNRESOLVED] ZIP byte identity remains NOT VERIFIED: `gh auth token` returned no OAuth token and curl failed with exit `35` before a usable archive was produced; scratch directory is empty. Locator: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 10; named columns recordType=download_attempt,key,value`. |

## Experiment Record

| field | record |
|---|---|
| Research question | [DIRECT] Clean-trained agents are moved into faulty/weakness labs; expected effect is faster realignment with physics/KG knowledge. Locator: `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L14-L19`. |
| Prior expectation | [DIRECT] Physics/KG guidance should realign faster. Locator: `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L15-L17`. |
| Baseline and treatment | [DIRECT] Baseline `ql_false`; treatment `ql_true`. Locators: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L244-L245`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/illuminance_controller_agent_adapt.asl:L84-L104`. |
| Variables and controls | [DIRECT] Profiles, modes, seeds, parent profiles, clean-source suffixes, simulator flows, qtable suffixes, state-vector dimensions, detector thresholds, and recovery criteria are recorded in Stage 7 method evidence. Locators: `local-sha256:8602e69ecd785f3a5818c18ff55fe38e79c2984e416a0d4136e1d68c7a43ac1b:paper_notes/PHASE2_METHODS.md:L101-L117`. |
| Metrics and statistics | [DIRECT] CI rows include detection, reconvergence, greedy goal-rate, recovery episode, and detection episode metrics; paired rows compare KG and naive arms. Locators: `S8-P2-FINAL-CI`; `S8-P2-FINAL-PAIRED`; analysis method locators in `S8-P2-METHODS`. |
| Research status | [UNRESOLVED] Formal Phase 2 preregistration remains `NOT FOUND`; classify Stage 8 result interpretation as `ENGINEERING_VALIDATION` and, where used for scientific finding, `POST_HOC_EXPLORATORY`, not `PRE_REGISTERED_CONFIRMATORY`. Locators: `local-sha256:8602e69ecd785f3a5818c18ff55fe38e79c2984e416a0d4136e1d68c7a43ac1b:paper_notes/PHASE2_METHODS.md:L25-L27`; `local-sha256:1f6c1881a8a9b991b17fadf5070015272d106a880630299049146df83ee6bb64:paper_notes/EVIDENCE_GAPS.md:L585-L619`. |

## Manuscript Evidence: Results

| finding candidate | label | evidence record |
|---|---|---|
| Detection recall in final v5 | [DERIVED] Every final v5 profile/mode cell has `detection_rate=1.0` and `n_detected=10` over `n_runs=10`; Stage 8 recomputed these from raw recovery rows. Direct aggregate locator: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:rows 2-19; named columns profile,mode,n_runs,detection_rate,n_detected`. Verification locators: `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:rows 5,21,37,53,69,85,101,117,133,149,165,181,197,213,229,245,261,277; named columns profile,mode,metric=detection_rate,value=1.0,verification_status=VERIFIED_DETERMINISTIC_FROM_RAW`. |
| Component-attribution false positives in final v5 | [DERIVED] Across the `18` final v5 cells, aggregate detected component sets match expected injected fault component sets and `unexpected_component_row_count=0` in every cell. Locator: `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:rows 433-519; named columns record_type=final_raw_cell_verification,profile,mode,metric,value,verification_status`; script/command in Control Record. |
| Goal-reaching recovery scope | [DIRECT] Only `lab3_f1dead` and `lab3_f1inv` are marked `well_posed_recovery=True`; rows for lab1, lab2, lab3_f2dead, and lab3_f2inv are descriptive/provisional for recovery-speed inference. Locator: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:rows 2-19; named columns profile,mode,well_posed_recovery`. |
| Recovery success, well-posed cells | [DIRECT] `lab3_f1dead`: ql_false `n_reconverged=10`, `n_goal_reaching=10`, `RecoveryEpisodes_mean=363.4`; ql_true `n_reconverged=10`, `n_goal_reaching=10`, `RecoveryEpisodes_mean=150.5`. `lab3_f1inv`: ql_false `n_reconverged=10`, `n_goal_reaching=3`, `RecoveryEpisodes_mean=318.8`; ql_true `n_reconverged=9`, `n_goal_reaching=1`, `RecoveryEpisodes_mean=364.55555555555554`. Locator: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:rows 12-15; named columns profile,mode,n_reconverged,n_goal_reaching,RecoveryEpisodes_mean`. |
| KG-vs-naive recovery speed, lab3_f1dead | [DERIVED] In the well-posed `lab3_f1dead` recovery comparison, `n_paired=10`, ql_true mean `150.5`, ql_false mean `363.4`, mean difference ql_true-minus-ql_false `-212.9`, Wilcoxon p `0.00390625`, Cliff's delta `-0.86`, q_bootstrap_bh `0.0`, and `ql_true_faster=True`; bootstrap CI `[-271.9,-148.3]` and bootstrap p `0.0` are direct analysis outputs not independently resampled. Locators: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:row 2; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,ci_lo,ci_hi,p_bootstrap,p_wilcoxon,cliffs_delta,q_bootstrap_bh`; verification rows `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:rows 290-302`. |
| KG-vs-naive recovery speed, lab3_f1inv | [DERIVED] In the well-posed `lab3_f1inv` recovery comparison, `n_paired=9`, ql_true mean `364.55555555555554`, ql_false mean `332.77777777777777`, mean difference `31.77777777777778`, Wilcoxon p `0.49609375`, Cliff's delta `0.2345679012345679`, q_bootstrap_bh `0.6496`, and `ql_true_faster=False`; bootstrap CI `[-137.22222222222223,174.55833333333328]` and bootstrap p `0.6496` are direct analysis outputs not independently resampled. Locators: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:row 3; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,ci_lo,ci_hi,p_bootstrap,p_wilcoxon,cliffs_delta,q_bootstrap_bh`; verification rows `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:rows 303-315`. |
| Detection speed KG-vs-naive differences | [DERIVED] Detection-time differences are mixed: ql_true is faster in lab2_f1dead (`-2.2`), lab2_f1inv (`-1.4`), lab2_f2dead (`-2.1`), lab2_f2inv (`-1.5`), and lab3_f2dead (`-1.1`); ql_true is slower in lab1_f1dead (`0.3`), lab3_f1dead (`16.9`), lab3_f1inv (`126.2`), and lab3_f2inv (`3.6`). Locators: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:rows 4-12; named columns profile,metric,mean_diff_true_minus_false,p_wilcoxon,q_bootstrap_bh`; verification rows `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:rows 319,332,345,358,371,384,397,410,423; named columns metric,value,verification_status`. |

## Result Interpretation Boundaries

| interpretation | label | boundary |
|---|---|---|
| Headline recovery claim | [INTERPRETATION] The supported final-result claim is narrow: KG-primed recovery is faster than naive in `lab3_f1dead`, but not in `lab3_f1inv`. Evidence is engineering-validation/post-hoc-exploratory, and bootstrap fields remain direct analysis outputs. Source rows: paired rows `2-3` in `S8-P2-FINAL-PAIRED`; verification rows `290-315` in `S8-P2-RAW-VERIFY`. |
| Detection accuracy | [INTERPRETATION] Final v5 shows complete detection in the tested injected-fault matrix (`18` cells, `10` runs per cell), and Stage 8 finds no unexpected component attribution rows. This is detection recall/attribution sanity for the tested cases, not proof of general fault-detection accuracy outside the injected profiles. Source rows: CI rows `2-19` in `S8-P2-FINAL-CI`; verification rows `433-519` in `S8-P2-RAW-VERIFY`. |
| Provisional cells | [UNRESOLVED] Recovery-speed inference for `well_posed_recovery=False` cells is descriptive/provisional because the analysis script excludes those profiles from the RecoveryEpisodes paired family. Source: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L55-L92`; final CI rows `2-11` and `16-19` in `S8-P2-FINAL-CI`. |
| Resampling | [UNRESOLVED] Stage 8 independently verified deterministic means/counts, exact Wilcoxon p-values, Cliff's delta, and BH q-values from aggregate p-values; it did not independently reproduce NumPy bootstrap CIs or bootstrap p-values. Source: verification-status counts in `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`; script boundary `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L1-L16`. |

## Table Specifications

| table id | product | specification |
|---|---|---|
| T-P2-RESULT-1 | Manuscript Evidence | Detection and component-attribution table: profile, mode, n_runs, detection_rate, n_detected, defect_component, aggregate_defect_set_matches_expected, unexpected_component_row_count. Sources: `S8-P2-FINAL-CI`; `S8-P2-RAW-VERIFY`. |
| T-P2-RESULT-2 | Manuscript Evidence | Well-posed recovery table: profile, mode, n_reconverged, n_goal_reaching, greedy_goal_rate_mean, RecoveryEpisodes_mean, RecoveryEpisodes CI, with `well_posed_recovery=True` filter. Source: final CI rows `12-15` in `S8-P2-FINAL-CI`; note bootstrap-CI limitation. |
| T-P2-RESULT-3 | Manuscript Evidence | KG-vs-naive paired recovery table: profile, n_paired, ql_true_mean, ql_false_mean, mean_diff_true_minus_false, CI, p_bootstrap, p_wilcoxon, cliffs_delta, q_bootstrap_bh, ql_true_faster. Source: final paired rows `2-3` in `S8-P2-FINAL-PAIRED`; verification rows `290-315` in `S8-P2-RAW-VERIFY`. |
| T-P2-AUDIT-1 | Audit History | Supersession table: v1, v2, v3, v4, v5 result commit, run ID, source-head change, `SetSpotlight` rows, and final authority flag. Sources: Audit History table above. |

## Figure Specifications

| figure id | product | specification |
|---|---|---|
| F-P2-RESULT-1 | Manuscript Evidence | Point/interval plot for well-posed RecoveryEpisodes paired differences: `lab3_f1dead` and `lab3_f1inv`, x-axis profile, y-axis ql_true minus ql_false episodes, zero reference line, markers for mean difference, intervals from paired CSV. Label bootstrap interval as analysis-output, not independently resampled. Source: final paired rows `2-3`. |
| F-P2-RESULT-2 | Manuscript Evidence | Heatmap/table for detection latency differences across all profiles: profile rows, value mean_diff_true_minus_false from DetectEpisode paired rows, sign-colored lower-is-better scale, with q_bootstrap_bh and p_wilcoxon as annotations. Source: final paired rows `4-12`; verification rows listed under detection-speed finding. |
| F-P2-AUDIT-1 | Audit History | Supersession timeline v1 -> v2 -> v3 -> v4 -> v5, marking `SetSpotlight` attribution rows as removed only in v5. Source: Audit History table above. |

## Evidence Gaps Carried Forward

| gap | label | record |
|---|---|---|
| Artifact ZIP byte identity | [UNRESOLVED] Artifact metadata is recorded, but no ZIP byte verification was completed because no GitHub OAuth token is configured and the ZIP download failed. Locator: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 10`. |
| Exact workflow_dispatch inputs | [UNRESOLVED] Run event is `workflow_dispatch`, but exact dispatch input payload remains `NOT FOUND`; Stage 8 did not locate an API field exposing it. Locator: `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:row 2`; workflow source defaults remain method evidence only. |
| Independent bootstrap resampling | [UNRESOLVED] Stage 8 independently checked deterministic values, Wilcoxon, Cliff's delta, and BH q-values, but not NumPy bootstrap CIs or bootstrap p-values. Locator: `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`. |
| Formal Phase 2 preregistration | [UNRESOLVED] Formal preregistration or registered-deviation locator remains `NOT FOUND`. Use `ENGINEERING_VALIDATION` and `POST_HOC_EXPLORATORY` labels for Phase 2 result interpretation. Locator: `local-sha256:8602e69ecd785f3a5818c18ff55fe38e79c2984e416a0d4136e1d68c7a43ac1b:paper_notes/PHASE2_METHODS.md:L25-L27`. |

## Handoff

Completed:
- [DIRECT] Supersession established: v1-v4 are audit history; v5 run `27547019772` / result commit `22a448be5d9829751badd341904e36ed582f091f` is final Phase 2 result authority.
- [DIRECT] Fresh Actions evidence captured for run status, `242` jobs, aggregate job `81495756019`, artifact `7647220538`, and artifact count `243`.
- [DERIVED] Final v5 deterministic metrics, attribution checks, exact Wilcoxon p-values, Cliff's delta, and BH q-values verified from committed raw recovery rows into `PHASE2_TABLES.csv`.
- [INTERPRETATION] Manuscript evidence boundary set: strong recovery-speed support only for `lab3_f1dead`; `lab3_f1inv` does not support faster KG recovery; non-well-posed cells stay descriptive/provisional.

Unresolved:
- [UNRESOLVED] Artifact ZIP byte identity remains NOT VERIFIED.
- [UNRESOLVED] Exact workflow_dispatch inputs remain NOT FOUND.
- [UNRESOLVED] NumPy bootstrap CI/p-value resampling remains not independently reproduced.
- [UNRESOLVED] Formal Phase 2 preregistration remains NOT FOUND.

Next stage must read:
- `paper_notes/00_PROTOCOL.md`
- `paper_notes/PHASE2_METHODS.md`
- `paper_notes/PHASE2_RESULTS.md`
- `paper_notes/PHASE2_TABLES.csv`
- `paper_notes/PHASE2_ACTIONS_STAGE8.csv`
- `paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv`
- `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv`
- `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv`
- `paper_notes/SOURCE_LEDGER.csv`
- `paper_notes/CLAIM_LEDGER.csv`
- `paper_notes/RUN_LEDGER.csv`
- `paper_notes/EVIDENCE_GAPS.md`
