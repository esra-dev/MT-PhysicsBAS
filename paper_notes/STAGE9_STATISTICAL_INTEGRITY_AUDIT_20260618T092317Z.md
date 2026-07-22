# Stage 9 Statistical Integrity Audit

Stage: `9`
Created: `2026-06-18T09:23:17Z`
Scope: evidence extraction only. This file is not polished thesis prose.

## Control Record

| item | label | evidence record |
|---|---|---|
| Protocol discipline | [DIRECT] | Evidence extraction requires separate audit-history and manuscript-evidence products, explicit source locators, derived-result commands, experiment records, and unresolved gap records. Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236`. |
| Stage 8R2 handoff read | [DIRECT] | Stage 8R2 required Stage 9 to read the Phase 2 methods/results bundle, Phase 1 results bundle, ledgers, evidence gaps, committed Phase 2 CI/paired CSVs, dirty phase-change docs, and advisor note. Locator: `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L117-L144`. |
| Dirty-doc context read | [DIRECT] | The dirty phase-change docs were read as history/routing context only and are not primary numeric evidence. Locators: `local-sha256:6885096decf6080cafec4f2c17f01197d18e7e400bc0fa5ccb9c6b0e65136943:docs/PHASE1_TO_PHASE2_CHANGES.md:L1-L1579`; `local-sha256:0d30b28c54c818173f40e817480682d62c67b267bfbf018d6dd9233ee311a4e4:docs/PHASE2_TO_PHASE3_CHANGES.md:L1-L709`; advisor note `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L1-L25`. |
| Stage 9 extraction command | [DERIVED] | Stage 9 generated `21` data rows in `STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`. Output locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:L1-L22`. Script: `local-sha256:4a676e702609ccb35915a8698c1ecca458d7d1afb7ae3d3723d6c219c0d848e8:paper_notes/stage9_statistical_integrity_audit.mjs:L1-L300`. Exact command: `node paper_notes/stage9_statistical_integrity_audit.mjs paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`. |
| Read-only git audit | [DERIVED] | Stage 9 recorded read-only `git log`, `git show`, and `git diff --stat` outputs without branch switching. Locator: `local-sha256:698680a425a28a7c5f7e854f69b33772bf34c17fdf79da2db980f2f3b4f56ef4:paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt:L1-L30`. |

## Source Anchors

| anchor | label | source locator |
|---|---|---|
| S9-PROTOCOL | [DIRECT] | `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236` |
| S9-AUDIT-TABLE | [DERIVED] | `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:L1-L22`; script `local-sha256:4a676e702609ccb35915a8698c1ecca458d7d1afb7ae3d3723d6c219c0d848e8:paper_notes/stage9_statistical_integrity_audit.mjs:L1-L300`; command `node paper_notes/stage9_statistical_integrity_audit.mjs paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`. |
| S9-GIT | [DERIVED] | `local-sha256:698680a425a28a7c5f7e854f69b33772bf34c17fdf79da2db980f2f3b4f56ef4:paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt:L1-L30`. |
| S9-P2-METHOD | [DIRECT] | Analysis method source: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L1-L44`; helpers/imports and well-posed scope: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L54-L92`; paired comparison logic: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L243-L325`; CLI default iterations: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L359-L408`. |
| S9-P1-METHOD | [DIRECT] | Phase 1 analysis helper definitions: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L315-L346`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L440-L539`; Phase 1 extraction status: `local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L360-L475`. |
| S9-P2-RESULTS | [DIRECT] | Final Phase 2 CI CSV: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19`; final paired CSV: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| S9-P1-RESULTS | [DERIVED] | Phase 1 table: `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`; R2 routing table: `local-sha256:a6004ae672bfbb32c746d907e4c1855ec54c540d98063c06d6339258411a06b0:paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv:L1-L15`. |

## AUDIT HISTORY

| record | label | evidence |
|---|---|---|
| S9-AH-001 | [DIRECT] | Current git audit observation is branch `phase3-process-dynamics`, HEAD `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`, and `origin/results` ref `0372ecd5864fa6555ebfce7d05e05d9aaab96994`. Locator: `S9-GIT`, lines `1-4`. |
| S9-AH-002 | [DIRECT] | Phase 2 selected result commit `22a448be5d9829751badd341904e36ed582f091f` adds the two aggregate statistical CSVs used here: `phase2_recovery_ci.csv` has `19` lines in the git show stat, and `phase2_recovery_paired.csv` has `12` lines in the git show stat. Locator: `S9-GIT`, lines `18-22`. |
| S9-AH-003 | [DERIVED] | Diffing selected Phase 2 result commit `22a448be5d9829751badd341904e36ed582f091f` to current `origin/results` `0372ecd5864fa6555ebfce7d05e05d9aaab96994` for the selected Phase 2 CI and paired CSV paths produced `NO OUTPUT`; Stage 9 does not infer more than no diff-stat output for those selected paths. Locator: `S9-GIT`, lines `24-25`. |
| S9-AH-004 | [SUPERSEDED] | The older v5 job-inventory limitation remains superseded: Stage 9 table row `S9T-016` records `all_jobs=242`, `adapt=180`, `clean=60`, `aggregate=1`, and `compile=1`; remaining workflow-provenance gaps are dispatch inputs and artifact ZIP identity. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 17; named columns evidence_id=S9T-016,value,statistical_integrity_status,notes`. |

## MANUSCRIPT EVIDENCE

| item | label | evidence-use boundary |
|---|---|---|
| Phase 2 deterministic and exact checks | [DERIVED] | Stage 9 reproduces the Stage 8/R2 partition for the Phase 2 R2 table: `521` data rows, `306` deterministic-from-raw rows, `99` deterministic-or-exact-test rows, and `0` check-failed rows. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 2-6; named columns evidence_id,metric,value,statistical_integrity_status`. |
| Phase 2 bootstrap boundary | [UNRESOLVED] | Phase 2 still has `116` rows marked `DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED`: `72` final-CI rows and `44` final-paired rows. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 3,7-8; named columns evidence_id,metric,value,statistical_integrity_status`. |
| Phase 2 recovery-family scope | [DIRECT] | Phase 2 `RecoveryEpisodes` paired-family size is `2` and includes only `lab3_f1dead` and `lab3_f1inv`; `DetectEpisode` paired-family size is `9`. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 9-10; named columns evidence_id,metric,value,notes`; direct paired CSV: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| Phase 2 BH nuance | [INTERPRETATION] | Stage 8/R2 verifies BH arithmetic from aggregate bootstrap p-values, but the bootstrap p-values themselves remain direct analysis outputs. Therefore BH q-values should be reported as analysis-output-derived values whose arithmetic was checked, not as independently resampled p-value evidence. Sources: `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L279-L299`; `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 3,7-8`. |
| Phase 1 deterministic checks | [DERIVED] | Phase 1 table has `480` data rows, with `348` mean rows matching raw data, `132` mean-difference rows matching raw data, and `0` mismatch/not-found rows. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-14; named columns evidence_id,metric,value,statistical_integrity_status`. |
| Phase 1 resampling boundary | [UNRESOLVED] | Phase 1 still has `348` rows whose CI was copied from analysis CSVs and `132` rows whose p/q/CI fields were copied from analysis CSVs; Stage 9 did not independently reproduce Stage 6 bootstrap/statistical resampling. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 15-16; named columns evidence_id,metric,value,statistical_integrity_status`. |
| Research status | [UNRESOLVED] | Formal post-pivot preregistration remains `NOT FOUND`; do not promote Phase 1 or Phase 2 result interpretation to `PRE_REGISTERED_CONFIRMATORY`. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 20; named columns evidence_id=S9T-019,value=NOT FOUND,statistical_integrity_status=DO_NOT_PROMOTE_TO_PREREGISTERED_CONFIRMATORY`. |

## Experiment Records

| experiment | label | confirmatory status | research question | prior expectation | baseline | treatment | variables and controls | metrics and statistical method | unexpected result/follow-up | evidence locator |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-P1-BUMP | [DIRECT] | POST_HOC_EXPLORATORY | Clean-lab KG acceleration route. | Advisor expected faster/better learning with physics/KG priming, fewer redundant actions, and comparable success. | `ql_false` in bumped targeted run. | `ql_true` in bumped targeted run. | Same bumped targeted configuration and seed block routed by Stage 6/R2 products. | Deterministic means and mean differences match raw data; CI/p/q/Cliff fields remain analysis-CSV sourced. | Lab3 binary-goal and reward evidence remain separated; stale lab3 magnitude documentation remains unresolved. | `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L44-L49`; Stage 9 rows `S9T-010` through `S9T-015`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-16`. |
| EXP-P1-REPL | [DIRECT] | POST_HOC_EXPLORATORY | Fresh-seed clean-lab replication route. | Same Phase 1 prior expectation as EXP-P1-BUMP. | `ql_false` in fresh-seed bumped run. | `ql_true` in fresh-seed bumped run. | Fresh seed block routed by Stage 6/R2 products. | Same Stage 6 extraction and Stage 9 deterministic/resampling boundary as EXP-P1-BUMP. | Replication route is manuscript evidence but not a new preregistered confirmatory test. | `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L48-L48`; Stage 9 rows `S9T-010` through `S9T-015`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-16`. |
| EXP-P1-ABL | [DIRECT] | POST_HOC_EXPLORATORY | Untargeted mechanism/ablation route. | Targeted structural knowledge expected to outperform untargeted control. | Untargeted cross-zone ablation condition. | Targeted bumped cross-zone condition used as comparison route. | Mechanism evidence only; not a formal confirmatory causal test. | Same Stage 6 extraction and Stage 9 deterministic/resampling boundary as Phase 1 table. | Mechanism language remains exploratory. | `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L49-L49`; Stage 9 rows `S9T-010` through `S9T-015`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-16`. |
| EXP-P2-V5 | [DIRECT] | ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY | Fault-adaptation route: clean-trained agents enter weakness labs, detect unexpected behavior, discard defective artifact, relearn, and realign faster with physics/KG. | Advisor expected faster realignment with physics knowledge. | `ql_false`. | `ql_true`. | Profiles/modes/config fixed by selected v5 source; recovery-speed paired inference restricted to well-posed cells. | Phase 2 analysis uses bootstrap CI, paired bootstrap, Wilcoxon, Cliff's delta, and BH q-values; Stage 8/R2 checked deterministic/exact arithmetic, not NumPy bootstrap resampling. | `lab3_f1dead` supports faster KG recovery; `lab3_f1inv` does not; detection latency evidence is descriptive. | Advisor source: `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L14-L19`; method source `S9-P2-METHOD`; result source `S9-P2-RESULTS`; Stage 9 rows `S9T-001` through `S9T-009`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 2-10`. |

## Table Specifications

| table id | product | specification |
|---|---|---|
| T-S9-STAT-1 | MANUSCRIPT EVIDENCE | Statistical-integrity matrix with columns: phase, table, data-row count, deterministic/raw rows, exact-test rows, bootstrap-output rows, failed-check rows, and manuscript-use boundary. Data source: Stage 9 rows `S9T-001` through `S9T-015`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 2-16`. |
| T-S9-STAT-2 | MANUSCRIPT EVIDENCE | Phase 2 statistical-provenance table for `RecoveryEpisodes` and `DetectEpisode`: include family size, raw/deterministic fields, exact Wilcoxon/Cliff/BH arithmetic status, and bootstrap field status. Data sources: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`; Stage 9 rows `S9T-006` through `S9T-009`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 7-10`. |
| T-S9-GAP-1 | AUDIT HISTORY; MANUSCRIPT EVIDENCE | Carried-forward gap table: dispatch input payload, artifact ZIP identity, Phase 1/Phase 2 resampling reproduction, formal preregistration, lab3 stale-magnitude documentation, dirty-doc numeric-source limits. Data sources: Stage 9 rows `S9T-017` through `S9T-020`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 18-21`. |

## Figure Specifications

| figure id | product | specification |
|---|---|---|
| F-S9-STAT-1 | MANUSCRIPT EVIDENCE | Evidence-status stacked bar or matrix: Phase 1 and Phase 2 as rows; deterministic/raw, exact-test, bootstrap-output-not-resampled, and failed-check categories as columns. Use counts from `T-S9-STAT-1`; mark bootstrap-output segments as `[UNRESOLVED]`. |
| F-S9-STAT-2 | MANUSCRIPT EVIDENCE | Phase 2 paired-result provenance diagram: raw recovery rows -> deterministic means/differences -> exact Wilcoxon/Cliff arithmetic -> bootstrap p/CI from original analysis output -> BH arithmetic. Annotate that BH arithmetic is checked but inherits bootstrap-p source limits. |
| F-S9-AUDIT-1 | AUDIT HISTORY | Workflow provenance status panel: job inventory closed/superseded; dispatch inputs and artifact ZIP identity open. Data source: Stage 9 rows `S9T-016` through `S9T-018`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 17-19`. |

## Evidence Gaps Carried Forward

| gap | label | record |
|---|---|---|
| Exact workflow_dispatch input payloads | [UNRESOLVED] | Phase 2 input payload is `NOT FOUND` in Stage 9 row `S9T-018`; Phase 1 equivalent remains carried from Stage 6/6R2 and Stage 8R2. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 19; named columns evidence_id=S9T-018,value=NOT FOUND`. |
| Artifact ZIP byte identity | [UNRESOLVED] | Phase 2 artifact ZIP byte identity remains `NOT VERIFIED`; Phase 1 artifact ZIP identity also remains unresolved from prior stages. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 18; named columns evidence_id=S9T-017,value,statistical_integrity_status`. |
| Independent bootstrap resampling | [UNRESOLVED] | Stage 9 did not independently reproduce Stage 6 Phase 1 bootstrap/statistical resampling or Stage 8 Phase 2 NumPy bootstrap CI/bootstrap-p resampling. Locators: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 3,7-8,15-16; named columns evidence_id,metric,value,statistical_integrity_status`. |
| Formal post-pivot preregistration | [UNRESOLVED] | Formal post-pivot preregistration remains `NOT FOUND`; do not call Phase 1 or Phase 2 final claims preregistered confirmatory. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 20; named columns evidence_id=S9T-019,value=NOT FOUND`. |
| Lab3 stale magnitude and dirty-doc numeric limits | [UNRESOLVED] | Lab3 stale-magnitude documentation and dirty-doc numeric-source limits remain active; manuscript numeric claims must cite primary result rows or derived tables, not dirty prose docs. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 21; named columns evidence_id=S9T-020,value=ACTIVE,statistical_integrity_status`. |

## Handoff

Completed:
- [DIRECT] Read the Stage 9 required file list from Stage 8R2, including protocol, Phase 1/Phase 2 result notes, tables, figure specs, Actions captures, ledgers, evidence gaps, committed Phase 2 CI/paired CSVs, dirty phase-change docs, and advisor note. Locator: `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L117-L144`.
- [DERIVED] Created `paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv` with `21` data rows. Locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:L1-L22`.
- [DERIVED] Created `paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt` from read-only git commands. Locator: `local-sha256:698680a425a28a7c5f7e854f69b33772bf34c17fdf79da2db980f2f3b4f56ef4:paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt:L1-L30`.
- [SUPERSEDED] Kept the older v5 job-inventory limitation closed/superseded; did not reopen it.

Unresolved:
- [UNRESOLVED] Exact Phase 1/Phase 2 workflow_dispatch input payloads remain `NOT FOUND`.
- [UNRESOLVED] Phase 1/Phase 2 artifact ZIP byte identity remains not verified.
- [UNRESOLVED] Stage 6 Phase 1 and Stage 8 Phase 2 bootstrap resampling remain not independently reproduced.
- [UNRESOLVED] Formal post-pivot preregistration remains `NOT FOUND`.
- [UNRESOLVED] Lab3 stale-magnitude documentation and dirty-doc numeric-source limits remain active.

Next stage must read:
- `paper_notes/00_PROTOCOL.md`
- `paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md`
- `paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`
- `paper_notes/stage9_statistical_integrity_audit.mjs`
- `paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt`
- `paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md`
- `paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv`
- `paper_notes/PHASE2_RESULTS.md`
- `paper_notes/PHASE2_TABLES.csv`
- `paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md`
- `paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv`
- `paper_notes/PHASE1_RESULTS.md`
- `paper_notes/PHASE1_TABLES.csv`
- `paper_notes/SOURCE_LEDGER.csv`
- `paper_notes/CLAIM_LEDGER.csv`
- `paper_notes/RUN_LEDGER.csv`
- `paper_notes/EVIDENCE_GAPS.md`
