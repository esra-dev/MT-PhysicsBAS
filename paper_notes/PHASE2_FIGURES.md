# Phase 2 Figure Evidence Specifications

Stage: `8R2`
Created: `2026-06-18T09:05:33Z`
Scope: figure specifications only. No rendered bitmap/vector figures were produced in this pass.

## Source Anchors

| anchor | label | scope | source locator |
|---|---|---|---|
| FIG-P2-RESULTS-BASE | [DIRECT] | Stage 8 base figure plan and result records. | `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L60-L99` |
| FIG-P2-TABLE-R2 | [DERIVED] | R2 duplicate long-format result table. | `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv:L1-L522`; exact command: `node paper_notes\phase2_extract_results.mjs --root paper_notes\stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f --out paper_notes\PHASE2_TABLES_R2_20260618T090000Z.csv`; script: `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L1-L488`. |
| FIG-P2-CI | [DIRECT] | Final v5 CI table. | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19` |
| FIG-P2-PAIRED | [DIRECT] | Final v5 paired table. | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12` |
| FIG-P2-METHODS | [DIRECT] | Well-posed recovery and paired-family scope. | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L78-L92`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L243-L325` |
| FIG-P2-GAPS | [UNRESOLVED] | Artifact/input/bootstrap/preregistration limits. | `local-sha256:7f227812c0e62ffa1902de172a5040399e964297ebc590a35f3d57f3450244aa:paper_notes/EVIDENCE_GAPS.md:L637-L672`; `local-sha256:7f227812c0e62ffa1902de172a5040399e964297ebc590a35f3d57f3450244aa:paper_notes/EVIDENCE_GAPS.md:L791-L820` |

## Figure Specifications

| figure id | label | product | status | purpose | data rows | encoding | required caveat |
|---|---|---|---|---|---|---|---|
| FIG-P2-001 | [DERIVED] | MANUSCRIPT EVIDENCE | ACTIVE | Detection and component-attribution matrix for the final v5 tested fault matrix. | Final CI rows `2-19`: `FIG-P2-CI`; verification rows `433-519`: `FIG-P2-TABLE-R2`, named columns `record_type,profile,mode,metric,value,verification_status`. | Grid with profile rows and mode columns. Use symbols or compact text for `detection_rate=1.0`, `n_detected=10`, expected component-set match, and unexpected component count. | This is tested-matrix detection recall and attribution sanity, not general detection accuracy outside the injected profiles. |
| FIG-P2-002 | [DERIVED] | MANUSCRIPT EVIDENCE | ACTIVE | Well-posed KG-vs-naive recovery-speed contrast. | Paired rows `2-3`: `FIG-P2-PAIRED`; verification rows `290-315`: `FIG-P2-TABLE-R2`. | Forest/point-interval plot. X-axis: ql_true minus ql_false `RecoveryEpisodes`; y-axis: `lab3_f1dead`, `lab3_f1inv`; vertical zero line; marker labels include `n_paired`, Wilcoxon p, Cliff's delta, and BH q. | Mark bootstrap intervals and bootstrap p-values as direct analysis outputs not independently resampled; report Phase 2 as `ENGINEERING_VALIDATION`/`POST_HOC_EXPLORATORY`. |
| FIG-P2-003 | [DERIVED] | MANUSCRIPT EVIDENCE | ACTIVE | Detection-latency KG-vs-naive map across all final v5 profiles. | Paired DetectEpisode rows `4-12`: `FIG-P2-PAIRED`; verification rows `319,332,345,358,371,384,397,410,423`: `FIG-P2-TABLE-R2`. | Heatmap or signed bar chart of `mean_diff_true_minus_false`. Lower is faster for ql_true; use a diverging scale around zero and annotate `p_wilcoxon` and `q_bootstrap_bh`. | Detection-latency results are descriptive engineering-validation evidence; do not make them the headline recovery-speed claim. |
| FIG-P2-004 | [DIRECT] | MANUSCRIPT EVIDENCE | ACTIVE | Recovery-success and goal-reaching certification boundary. | Final CI rows `2-19`: `FIG-P2-CI`, named columns `profile,mode,well_posed_recovery,n_reconverged,n_goal_reaching,greedy_goal_rate_mean,RecoveryEpisodes_mean`. | Small-multiple table or tile chart with row facets for profile and columns for mode; encode well-posedness, reconvergence count, and goal-reaching count separately. | Keep stable-but-futile cells separate from genuine recovery; recovery-speed inference is restricted to well-posed cells by `FIG-P2-METHODS`. |
| FIG-P2-005 | [SUPERSEDED] | AUDIT HISTORY | ACTIVE_FOR_AUDIT | Supersession timeline for v1 through v5 result authority. | Stage 8 audit-history table: `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L27-L37`; R2 git audit sequence: `local-sha256:54bc472e7fa3ecdcbe15e2743ded077e196056cdbe373b78abc325464a03429c:paper_notes/PHASE2_GIT_AUDIT_R2_20260618T090000Z.txt:L5-L32`. | Timeline with result generation labels v1, v2, v3, v4, v5; mark `SetSpotlight` false-positive attribution as removed only in v5. | Audit-history figure only; do not use the chronology as the manuscript result narrative unless placed in a reproducibility appendix. |
| FIG-P2-006 | [UNRESOLVED] | AUDIT HISTORY; MANUSCRIPT EVIDENCE | OPEN_LIMITATIONS | Evidence-limitations panel for Phase 2 provenance and statistics. | `FIG-P2-GAPS`; Stage 8 unresolved rows: `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L102-L119`. | Checklist/table with columns `gap`, `status`, `allowed claim boundary`, and `next action`. | Preserve exact dispatch-input, artifact ZIP, independent bootstrap-resampling, formal preregistration, lab3 stale-magnitude, and dirty-doc numeric-source limits. |

## Rendering Boundary

| record | label | note | source locator |
|---|---|---|---|
| FIG-P2-RENDER-001 | [UNRESOLVED] | Rendered bitmap/vector figures were not generated in Stage 8R2. | `local-sha256:7f227812c0e62ffa1902de172a5040399e964297ebc590a35f3d57f3450244aa:paper_notes/EVIDENCE_GAPS.md:L791-L820` |
| FIG-P2-RENDER-002 | [DERIVED] | This file is a standalone figure-specification product. It does not replace the Stage 8 base `PHASE2_RESULTS.md` figure-spec table. | `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L90-L99`; `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv:L1-L522` |
