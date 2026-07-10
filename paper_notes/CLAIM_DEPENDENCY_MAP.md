# Stage 3 Claim Dependency Map

Evidence-extraction product only. Not thesis prose.

## Locator Register

| ID | Immutable source locator |
|---|---|
| PIVOT-CORE | `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L8-L12` |
| PIVOT-P1 | `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L13-L23` |
| PIVOT-P2 | `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L24-L47` |
| PIVOT-P3 | `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L48-L57` |
| P1-IMPLEMENTATION | `main@7ac37a10fe3b3c23bc2b54159c40142fd367e821:config/run_config.json:L49-L148`; `main@55c01063165bf06f53dd6359c20fcb8940af5cc0:config/run_config.json:L49-L131`; `main@7ac37a10fe3b3c23bc2b54159c40142fd367e821:.github/workflows/phase1.yml:L1-L35` |
| P2-IMPLEMENTATION | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L242-L313`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L940-L1090`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L1140-L1248`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/illuminance_controller_agent_adapt.asl:L180-L420` |
| P2-ANALYSIS | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L1-L25`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L78-L92`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L243-L254` |
| P2-CI | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:rows 2-19; named columns profile,mode,n_runs,defect_component,well_posed_recovery,detection_rate,reconverge_rate,n_detected,n_reconverged,greedy_goal_rate_mean,n_goal_reaching,goal_reaching_rate,RecoveryEpisodes_mean,DetectEpisode_mean` |
| P2-PAIRED | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:rows 2-12; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,p_bootstrap,p_wilcoxon,cliffs_delta,ql_true_faster,q_bootstrap_bh,bh_family_m` |
| P3-IMPLEMENTATION | `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L322-L365`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L13-L60`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L165-L230`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L1-L83`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L400-L469` |
| P3-ANALYSIS | `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L1-L55`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L66-L79`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L193-L259`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L262-L329`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L394-L471` |
| P3-WORKFLOW-RUNHEAD | `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L39-L70`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L185-L213`; `origin/main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L263-L341` |
| P3-N10-PLAN | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:docs/PHASE2_TO_PHASE3_CHANGES.md:L621-L666`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L46-L70` |
| P3-RUN | `local-sha256:4d200a0a2ba6e505c7df67e1069dc127710d6b946a697d4c7e1b8e3b8345e505:paper_notes/ACTIONS_SELECTED_RUNS_20260616T133627Z.csv:row 4; named columns runId,event,status,conclusion,headSha,runAttempt,createdAt,updatedAt,url`; `local-sha256:0e849b3f1501c74b1f4f7edc632e34d541ffdbb9875290ff64a356b31040d05c:paper_notes/ACTIONS_ARTIFACTS_20260616T133627Z.csv:row 165; named columns runId,artifactName,artifactId,sizeInBytes,digest` |
| P3-DELAY | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:rows 2-5; named columns profile,mode,n_actuators,n_instantaneous,n_delayed,slowest_label,slowest_learned_ticks,ground_truth_ticks,abs_err_ticks,rel_err_pct,mean_instant_ticks,mean_delayed_ticks` |
| P3-CI | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:rows 2-5; named columns profile,mode,n_replicas,n_goals_total,overall_compliance_mean,tight_compliance_mean,loose_compliance_mean,total_energy_mean,mean_actual_delay_mean` |
| P3-PAIRED | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:rows 2-9; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,ci_lo,ci_hi,lower_is_better,p_bootstrap,p_wilcoxon,cliffs_delta,ql_true_better,q_bootstrap_bh,bh_family_m` |
| PREREG-SEARCH | `local-sha256:054ec14d3ece1950cb8f00bcb739728481e1d8c7a50120579c554172faf95cab:paper_notes/POST_PIVOT_PREREG_SEARCH_20260615.txt:L1-L49`; script `local-sha256:886e5cef4787945fe0ba8d7f82ca4375b590dfce874be3cefd3feb0c89410d7d:paper_notes/STAGE2_SEARCH_POST_PIVOT_PREREG.ps1`; command `./paper_notes/STAGE2_SEARCH_POST_PIVOT_PREREG.ps1 -OutputPath ./paper_notes/POST_PIVOT_PREREG_SEARCH_20260615.txt` |

## Claim Nodes

| Claim ID | Label | Product scope | Claim text | Dependencies | Evidence status | Research status | Source locators |
|---|---|---|---|---|---|---|---|
| C-ROOT | [INTERPRETATION] | MANUSCRIPT_EVIDENCE | Final paper can be structured around a three-part research problem: KG priors for clean learning acceleration, KG priors as fault/anomaly detectors, and learned temporal dynamics written back to the KG. | C-P1-REQ; C-P2-REQ; C-P3-REQ | Active synthesis; not a result claim. | NOT_APPLICABLE | PIVOT-CORE |
| C-PREREG-GAP | [UNRESOLVED] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | Formal post-pivot preregistration is NOT FOUND under the Stage 2 search scope. | none | Active limitation. | UNRESOLVED | PREREG-SEARCH |
| C-P1-REQ | [DIRECT] | MANUSCRIPT_EVIDENCE | Pivot requirement asks for a clean-lab comparison of a KG-primed Q-learner against Q-learning without additional knowledge. | none | Requirement source only. | NOT_APPLICABLE | PIVOT-P1 |
| C-P1-IMPL | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 1 implementation provides clean profiles `lab1`, `lab2`, `lab3`, stereo modes `true,false`, and factorial controls for KG/PBRS/adaptive-trust separation. | C-P1-REQ | Implemented design support. | POST_HOC_EXPLORATORY | P1-IMPLEMENTATION; PREREG-SEARCH |
| C-P1-EFFECT | [UNRESOLVED] | MANUSCRIPT_EVIDENCE | Numeric Phase 1 effect claims must not be promoted by Stage 3 until final row-level Phase 1 result extraction identifies authoritative rows for speed, success, redundancy, and energy. | C-P1-IMPL | NOT FOUND in this Stage 3 pass as a final row-level extraction. | UNRESOLVED | P1-IMPLEMENTATION; PREREG-SEARCH |
| C-P2-REQ | [DIRECT] | MANUSCRIPT_EVIDENCE | Pivot requirement asks the agent to detect unexpected faulty behavior, discard/blacklist the affected actuator, alert, and re-learn with and without physics knowledge. | none | Requirement source only. | NOT_APPLICABLE | PIVOT-P2 |
| C-P2-IMPL | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 2 implementation has a fault detector, component blacklisting, targeted warm restart, and recovery logging over nine faulty profiles and two modes. | C-P2-REQ | Implemented design support. | ENGINEERING_VALIDATION | P2-IMPLEMENTATION; P2-ANALYSIS |
| C-P2-DETECTION | [DIRECT] | MANUSCRIPT_EVIDENCE | Final Phase 2 v5 CI rows report `detection_rate=1.0` and `n_detected=10` for every listed profile/mode row in rows 2-19. | C-P2-IMPL | Row-level result support. | ENGINEERING_VALIDATION | P2-CI |
| C-P2-RECOVERY-WIN | [DIRECT] | MANUSCRIPT_EVIDENCE | In the well-posed `lab3_f1dead` recovery row, `ql_true_mean=150.5`, `ql_false_mean=363.4`, `mean_diff_true_minus_false=-212.9`, `p_bootstrap=0.0`, `p_wilcoxon=0.00390625`, `cliffs_delta=-0.86`, and `q_bootstrap_bh=0.0`. | C-P2-IMPL; C-P2-DETECTION | Row-level result support. | ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY_INTERPRETATION | P2-PAIRED: row 2; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,p_bootstrap,p_wilcoxon,cliffs_delta,ql_true_faster,q_bootstrap_bh,bh_family_m |
| C-P2-BOUNDARY | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 2 analysis restricts recovery-speed inference to `lab3_f1dead` and `lab3_f1inv`; other cells remain descriptive for recovery speed. | C-P2-IMPL | Analysis-method support. | ENGINEERING_VALIDATION | P2-ANALYSIS |
| C-P2-INVERTED-BOUNDARY | [DIRECT] | MANUSCRIPT_EVIDENCE | In the `lab3_f1inv` DetectEpisode row, `ql_true_mean=144.8`, `ql_false_mean=18.6`, `mean_diff_true_minus_false=126.2`, `p_bootstrap=0.0`, `p_wilcoxon=0.001953125`, `cliffs_delta=1.0`, and `ql_true_faster=False`. | C-P2-BOUNDARY | Row-level result support; discussion boundary condition. | ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY_INTERPRETATION | P2-PAIRED: row 10; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,p_bootstrap,p_wilcoxon,cliffs_delta,ql_true_faster,q_bootstrap_bh,bh_family_m |
| C-P3-REQ | [DIRECT] | MANUSCRIPT_EVIDENCE | Pivot requirement asks the learner to learn temporal/process dynamics such as response delays and add them to the KG for time-bounded goals. | none | Requirement source only. | NOT_APPLICABLE | PIVOT-P3 |
| C-P3-IMPL | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 3 implementation adds dedicated slow profiles, a DynamicsLearner, a dynamics agent, Phase 3 workflow, and analysis for delay accuracy and deadline compliance. | C-P3-REQ | Implemented design support. | ENGINEERING_VALIDATION | P3-IMPLEMENTATION; P3-ANALYSIS; P3-WORKFLOW-RUNHEAD |
| C-P3-N10-STATUS | [UNRESOLVED] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | Phase 3 run `27621106006` completed successfully and has n10 result rows, but exact workflow_dispatch inputs are NOT FOUND. | C-P3-IMPL; C-PREREG-GAP | Completed run with dispatch-input limitation. | CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN | P3-RUN; P3-N10-PLAN; P3-CI |
| C-P3-DELAY-ACCURACY | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 3 delay rows report `ground_truth_ticks=12` and `abs_err_ticks` from `0.1125` through `0.2125` across the four profile/mode rows. | C-P3-IMPL; C-P3-N10-STATUS | Row-level result support. | CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN | P3-DELAY |
| C-P3-COMPLIANCE | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 3 paired compliance rows report `ql_true_better=True` for overall compliance and tight compliance in both slow profiles, with `p_wilcoxon=0.001953125`, `cliffs_delta=1.0`, and `q_bootstrap_bh=0.0` in rows 2-5. | C-P3-IMPL; C-P3-N10-STATUS; C-P3-DELAY-ACCURACY | Row-level result support. | CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN | P3-PAIRED: rows 2-5; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,p_wilcoxon,cliffs_delta,ql_true_better,q_bootstrap_bh |
| C-P3-ENERGY-COST | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 3 paired energy rows report `lower_is_better=True`, `ql_true_mean=3.2` for `lab2_slow`, `ql_true_mean=3.3` for `lab3_slow`, `ql_false_mean=0.0` for both rows, and `ql_true_better=False`. | C-P3-COMPLIANCE | Row-level result support; critical-discussion caveat. | CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN | P3-PAIRED: rows 8-9; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,lower_is_better,ql_true_better |
| C-P3-QTABLE-SCOPE | [DIRECT] | MANUSCRIPT_EVIDENCE | Phase 3 workflow states there is no Q-table training phase; the dynamics agent learns timing and plans against deadlines. | C-P3-IMPL | Implementation-scope caveat. | ENGINEERING_VALIDATION | P3-WORKFLOW-RUNHEAD |
| C-P3-UNIMPLEMENTED-SUPERSEDED | [SUPERSEDED] | AUDIT_HISTORY | The earlier Stage 1 status that Phase 3 implementation/results were NOT FOUND is no longer authoritative after Phase 3 implementation and n10 results were located. | C-P3-IMPL; C-P3-N10-STATUS | Supersession record. | NOT_APPLICABLE | Superseded claim `CLM-S1-006`; P3-IMPLEMENTATION; P3-RUN; P3-DELAY; P3-CI; P3-PAIRED |

## Dependency Adjacency

| Parent claim | Required child claims | Blocking gaps |
|---|---|---|
| C-ROOT | C-P1-IMPL; C-P2-IMPL; C-P3-IMPL; C-PREREG-GAP | C-P1-EFFECT remains unresolved for numeric Phase 1 results. |
| C-P1-IMPL | C-P1-REQ | Formal post-pivot preregistration NOT FOUND. |
| C-P1-EFFECT | C-P1-IMPL | Authoritative Phase 1 row-level numeric result extraction remains NOT FOUND in Stage 3. |
| C-P2-RECOVERY-WIN | C-P2-REQ; C-P2-IMPL; C-P2-DETECTION; C-P2-BOUNDARY | Generalizing recovery speed beyond well-posed cells is blocked by analysis restriction and result rows. |
| C-P2-INVERTED-BOUNDARY | C-P2-IMPL; C-P2-BOUNDARY | Must be placed in Discussion, not used as support for a universal faster-detection claim. |
| C-P3-COMPLIANCE | C-P3-REQ; C-P3-IMPL; C-P3-N10-STATUS; C-P3-DELAY-ACCURACY | Exact workflow_dispatch inputs NOT FOUND; no formal external preregistration. |
| C-P3-ENERGY-COST | C-P3-COMPLIANCE | Blocks any unqualified "energy saving" claim for Phase 3 aggregate results. |
| C-P3-QTABLE-SCOPE | C-P3-IMPL | Blocks wording that Phase 3 learned delays through temporal-difference Q-value credit assignment. |

## Figure And Table Dependencies

| Artifact ID | Product scope | Required claim nodes | Data source rows | Notes |
|---|---|---|---|---|
| TABLE-RQ-01 | MANUSCRIPT_EVIDENCE | C-ROOT; C-P1-IMPL; C-P2-IMPL; C-P3-IMPL | No numeric result rows required. | Candidate table of research questions, hypotheses, variables, controls, status. |
| TABLE-P2-01 | MANUSCRIPT_EVIDENCE | C-P2-DETECTION; C-P2-RECOVERY-WIN; C-P2-BOUNDARY; C-P2-INVERTED-BOUNDARY | P2-CI rows 2-19; P2-PAIRED rows 2-12. | Must separate detection family from recovery-speed family. |
| TABLE-P3-01 | MANUSCRIPT_EVIDENCE | C-P3-DELAY-ACCURACY | P3-DELAY rows 2-5. | Delay accuracy table: learned ticks vs ground truth ticks. |
| FIG-P3-01 | MANUSCRIPT_EVIDENCE | C-P3-COMPLIANCE; C-P3-ENERGY-COST | P3-CI rows 2-5; P3-PAIRED rows 2-9. | Display compliance and energy as separate panels or separate tables. |
| FIG-AUDIT-01 | AUDIT_HISTORY | C-P3-UNIMPLEMENTED-SUPERSEDED; C-PREREG-GAP | P3-N10-PLAN; P3-RUN; PREREG-SEARCH. | Audit-only supersession and provenance flow. |

## Claims Not Yet Safe For Manuscript

| Unsafe claim | Label | Reason | Required next evidence |
|---|---|---|---|
| "Post-pivot Phase 1 and Phase 2 were formally preregistered." | [UNRESOLVED] | Formal post-pivot preregistration NOT FOUND under Stage 2 search scope. | External/advisor protocol source or repository commit with immutable locator. |
| "Phase 1 numeric speedup is final and row-verified." | [UNRESOLVED] | Stage 3 did not complete authoritative row-level Phase 1 result extraction. | Select final Phase 1 run set; cite CSV rows or derived analysis chain. |
| "Phase 2 KG detects every fault faster." | [SUPERSEDED] | Final rows include `lab3_f1inv` DetectEpisode where `ql_true_faster=False`. | Scope detection claim by fault type and profile. |
| "Phase 2 recovery speed advantage generalizes across all faulty labs." | [UNRESOLVED] | Analysis restricts recovery-speed family to well-posed `lab3_f1dead` and `lab3_f1inv`. | Additional deterministic-survivor fault profiles or bounded manuscript claim. |
| "Phase 3 saves energy overall." | [DIRECT] but unsafe as positive claim | Energy rows show `ql_true_better=False` for lower-is-better energy metric. | Present as deadline-compliance cost, not energy saving. |
| "Phase 3 modifies Q-learning to learn temporal-difference delay dynamics." | [DIRECT] but unsafe | Workflow states no Q-table training; implementation uses probe/KG/planner loop. | Phrase as response-delay probing and KG writeback. |

## Stage 3 Refresh Dependency Delta - 20260617T080755Z

### Refresh Locator Register

| Token | Locator |
|---|---|
| S0R2-WORKTREE | `local-sha256:cb539c624bb31ce1e1b6b940d9a7a5182614e9b6563a37b0418304ddb6600ffa:paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md:L1-L59` |
| S0R2-TREE | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:L1-L31` |
| S0R2-FILE | `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:L1-L17` |
| S1R2-REPO | `local-sha256:8c5e22009f03f60539415cdcf3549b98c38b5a36cd7577631bdaa86d60e5bce1:paper_notes/REPOSITORY_MAP.md:L1-L304` |
| S2R-ACTIONS | `local-sha256:865583cb352036e55a15a71b74a5057cde62c49cf4abbce5eeb9694ba7b86456:paper_notes/ACTIONS_RUNS_20260617T074205Z.csv:L1-L126` |
| S2R-SUMMARY | `local-sha256:b469ae75fcbf835d02fe24b4e318118fa4c73b899baca7e9872c1f19451ef556:paper_notes/ACTIONS_SUMMARY_20260617T074205Z.csv:L1-L18` |
| S2R-CHRON | `local-sha256:149749f9916c34566c12fbc2357566f9ad02d0ea4cf372f1715f93ab6c4d363c:paper_notes/CHRONOLOGY.md:L1-L467` |
| S2R-HANDOFF | `local-sha256:5b19d9863b7dc1379a4060cbbbf7c3294df8282c1969de9879548c13a97d899a:paper_notes/STAGE2_REFRESH_HANDOFF_20260617T074205Z.md:L1-L82` |

### Refresh Claim Nodes

| Node | Label | Product scope | Claim | Depends on | Current dependency effect | Research status | Source locators |
|---|---|---|---|---|---|---|---|
| C-S3R-INPUTS | [DIRECT] | AUDIT_HISTORY | Stage 3R read the Stage 0R2, Stage 1R2, and Stage 2R refresh inputs before revising claim structure. | none | Adds current-routing context to the prior Stage 3 products. | NOT_APPLICABLE | S0R2-WORKTREE; S0R2-TREE; S0R2-FILE; S1R2-REPO; S2R-ACTIONS; S2R-CHRON; S2R-HANDOFF |
| C-S3R-AUTHORITY | [INTERPRETATION] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | Stage 2R does not change candidate final authority: Phase 2 v5 and Phase 3 n10 remain the current result authorities, while local roots remain support-only until artifact ZIP identity is verified. | C-P2-DETECTION; C-P3-N10-STATUS | Confirms current manuscript routing; no new result claim is created. | NOT_APPLICABLE | S0R2-TREE; S2R-ACTIONS; S2R-CHRON |
| C-S3R-P3-IMPLEMENTED | [DIRECT] | MANUSCRIPT_EVIDENCE | Current Stage 3R routing treats Phase 3 response-delay learning as implemented; the earlier unimplemented/NOT FOUND claim remains superseded audit history. | C-P3-IMPL; C-P3-N10-STATUS; C-P3-UNIMPLEMENTED-SUPERSEDED | Blocks any current manuscript outline that presents Phase 3 only as future work. | ENGINEERING_VALIDATION | P3-IMPLEMENTATION; P3-RESULT-DELAY; P3-RESULT-PAIRED; S2R-ACTIONS |
| C-S3R-DIRTY-DOC-GATE | [UNRESOLVED] | AUDIT_HISTORY | Dirty stage-specific documentation may guide extraction but cannot be used as the primary source for numeric manuscript values. | C-S3R-INPUTS | Forces primary CSV/Actions/committed-source citations for every number. | UNRESOLVED | S0R2-FILE; S2R-HANDOFF |
| C-S3R-RUNTIME-GATE | [UNRESOLVED] | AUDIT_HISTORY | Root-level Phase 3 runtime CSV/TTL files lack exact command, run, and artifact identity. | C-S3R-INPUTS | Prefer committed `origin/results` rows for Phase 3 manuscript evidence. | UNRESOLVED | S0R2-FILE; S2R-HANDOFF |
| C-S3R-NO-NEW-EXPERIMENT | [DIRECT] | AUDIT_HISTORY | Stage 3R is claim-structure reconciliation only; no workflow dispatch, experiment run, result-value analysis, effect-size analysis, or statistical-test analysis is performed in this pass. | C-S3R-INPUTS | Preserves separation between model/map updates and evaluation extraction. | NOT_APPLICABLE | S2R-HANDOFF; `STAGE3-REFRESH-20260617T080755Z` run-ledger row |

### Refresh Dependency Adjacency

| Node | Requires | Blocking / routing note |
|---|---|---|
| C-ROOT | C-S3R-INPUTS; C-S3R-AUTHORITY; C-P1-IMPL; C-P2-IMPL; C-P3-IMPL | Stage 3R does not add a fourth RQ. |
| C-P1-EFFECT | C-S3R-DIRTY-DOC-GATE; C-S3R-AUTHORITY | Still blocked until final Phase 1 rows are selected and cited. |
| C-P2-DETECTION | C-S3R-AUTHORITY; C-S3R-DIRTY-DOC-GATE | Use committed v5 rows, not dirty doc prose, for manuscript values. |
| C-P3-COMPLIANCE | C-S3R-AUTHORITY; C-S3R-RUNTIME-GATE | Use committed n10 rows; exact workflow_dispatch inputs remain NOT FOUND. |
| C-P3-UNIMPLEMENTED-SUPERSEDED | C-S3R-P3-IMPLEMENTED | Retain only in AUDIT HISTORY. |

### Refreshed Unsafe Claim Blocks

| Unsafe claim | Label | Reason after Stage 3R | Required next evidence |
|---|---|---|---|
| "Phase 3 is unimplemented." | [SUPERSEDED] | Current committed implementation and n10 result rows supersede the earlier Stage 1 negative search. | Cite C-S3R-P3-IMPLEMENTED and retain old NOT FOUND only as audit history. |
| "Dirty change documents prove the manuscript numbers." | [UNRESOLVED] | Stage 0R2 file hashes classify dirty docs as documentation; empirical prose needs primary CSV/JSON/Actions/result-branch extraction. | Row-level committed result or verified artifact locators for each value. |
| "Root-level Phase 3 runtime files are authoritative result sources." | [UNRESOLVED] | Exact command, run, and artifact identity are NOT FOUND for those ignored local files. | Verified artifact ZIP/tree identity or committed `origin/results` row source. |
| "Stage 3R completed evaluation extraction." | [UNRESOLVED] | Stage 3R is model/map reconciliation only. | A later extraction stage with primary rows, analysis script refs, and exact commands. |

## Stage 3R2 - Advisor-Source And Current-Evidence Dependency Delta - 2026-06-17T15:32:49.8337247Z

### Stage 3R2 Source Tokens

| Token | Locator |
|---|---|
| ADVISOR-ALL | `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L1-L26` |
| ADVISOR-P1 | `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L7-L12` |
| ADVISOR-P2 | `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L14-L19` |
| ADVISOR-P3 | `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L21-L24` |
| PIVOT-SUPERSEDED-FOR-ADVISOR | `local-sha256:c2501030b1eff061cdd6770b5444578d301fac98af911bee215eb2b94456605d:paper_notes/EVIDENCE_GAPS.md:L5-L27`; `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L1-L26` |
| DIRTY-P1P2-DOC | `local-sha256:6885096decf6080cafec4f2c17f01197d18e7e400bc0fa5ccb9c6b0e65136943:docs/PHASE1_TO_PHASE2_CHANGES.md:L1-L1579` |
| DIRTY-P2P3-DOC | `local-sha256:0d30b28c54c818173f40e817480682d62c67b267bfbf018d6dd9233ee311a4e4:docs/PHASE2_TO_PHASE3_CHANGES.md:L1-L709` |
| STAGE6-P1-PRODUCT | `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L1-L133`; `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`; `local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520`; command `node paper_notes/phase1_extract_tables.mjs paper_notes/PHASE1_TABLES.csv` |
| STAGE8-P2-PRODUCT | `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L1-L133`; `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`; `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L1-L488`; command `node paper_notes\phase2_extract_results.mjs --root paper_notes\stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f --out paper_notes\PHASE2_TABLES.csv` |
| P3-N10-ROWS | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9` |
| STAGE3R-OLDER-GATE | `local-sha256:6ae2aea452eb654f290f3f2222339ecdc189bb70b5c1d96ae35491b0b57d8462:paper_notes/RESEARCH_MODEL.md:L124-L132`; `local-sha256:039e1435d053284622b94c57cb5f5d64aa71479e4505848141acf6d7d5846022:paper_notes/CLAIM_DEPENDENCY_MAP.md:L121-L129`; `paper_notes/CLAIM_LEDGER.csv:row 90; claim_id CLM-S3R-006` |

### Stage 3R2 Claim Nodes

| Node | Label | Product scope | Claim | Depends on | Current dependency effect | Research status | Source locators |
|---|---|---|---|---|---|---|---|
| C-S3R2-ADVISOR-SOURCE | [DIRECT] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | The external advisor note is now the direct local source for Phase 1/2/3 requirement wording; `THESIS_PIVOT_MASTER.md` remains a local surrogate/history source for advisor content. | none | Replaces pivot-only requirement routing with a hash-addressed external advisor-note locator. | NOT_APPLICABLE | ADVISOR-ALL; PIVOT-SUPERSEDED-FOR-ADVISOR |
| C-S3R2-P1-RESULT-AVAILABLE | [SUPERSEDED] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | The older Stage 3R statement that final Phase 1 numeric extraction was deferred is superseded for current routing by Stage 6 Phase 1 result products. | C-S3R-DIRTY-DOC-GATE; C-P1-EFFECT | Manuscript Phase 1 values must route to STAGE6-P1-PRODUCT; Stage 6 limitations still apply. | POST_HOC_EXPLORATORY | STAGE3R-OLDER-GATE; STAGE6-P1-PRODUCT |
| C-S3R2-P2-RESULT-AVAILABLE | [SUPERSEDED] | AUDIT_HISTORY;MANUSCRIPT_EVIDENCE | The older Stage 3R statement that Phase 2 table extraction was pending is superseded for current routing by Stage 8 Phase 2 result products. | C-P2-DETECTION; C-S3R-DIRTY-DOC-GATE | Manuscript Phase 2 values must route to STAGE8-P2-PRODUCT; Stage 8 limitations still apply. | ENGINEERING_VALIDATION;POST_HOC_EXPLORATORY | STAGE3R-OLDER-GATE; STAGE8-P2-PRODUCT |
| C-S3R2-P3-IMPLEMENTED-BOUNDARY | [DIRECT] | MANUSCRIPT_EVIDENCE | Current claim structure treats Phase 3 as implemented and evaluated with n10 committed rows; it remains confirmatory only relative to a local plan, not to a formal preregistration. | C-S3R-P3-IMPLEMENTED; C-P3-N10-STATUS | Blocks current manuscript notes from describing Phase 3 as only future work; requires dispatch-input and artifact limitations. | CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN | ADVISOR-P3; DIRTY-P2P3-DOC; P3-N10-ROWS |
| C-S3R2-DOC-GATE | [UNRESOLVED] | AUDIT_HISTORY | Dirty change documents can support implementation intent but cannot serve as primary evidence for numeric manuscript claims. | C-S3R-DIRTY-DOC-GATE | Forces Stage 6, Stage 8, or committed Phase 3 result-row sources for every result value. | UNRESOLVED | DIRTY-P1P2-DOC; DIRTY-P2P3-DOC |
| C-S3R2-THREE-RQ-STRUCTURE | [INTERPRETATION] | MANUSCRIPT_EVIDENCE | Current manuscript evidence should keep the three-part structure: clean KG acceleration, fault recognition/re-learning, and response-delay dynamics learning. | C-S3R2-ADVISOR-SOURCE; C-S3R2-P1-RESULT-AVAILABLE; C-S3R2-P2-RESULT-AVAILABLE; C-S3R2-P3-IMPLEMENTED-BOUNDARY | Separates advisor requirements, implementation intent, actual implementation, observed results, exploratory claims, local-confirmatory claims, and unresolved gaps. | NOT_APPLICABLE | ADVISOR-P1; ADVISOR-P2; ADVISOR-P3; STAGE6-P1-PRODUCT; STAGE8-P2-PRODUCT; P3-N10-ROWS |
| C-S3R2-NO-NEW-EXPERIMENT | [DIRECT] | AUDIT_HISTORY | Stage 3R2 is claim-structure reconciliation and ledger update only; no workflow dispatch, experimental run, result-value analysis, effect-size analysis, or statistical-test analysis is performed in this pass. | none | Prevents Stage 3R2 products from being treated as new experiment outputs. | NOT_APPLICABLE | `local-sha256:440aa36d3121a1fda187368957c4125f2e2ed6d8802c6d8509cbc5982f586fa4:paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md:L5-L11` |

### Stage 3R2 Dependency Adjacency

| Node | Requires | Blocking / routing note |
|---|---|---|
| C-ROOT | C-S3R2-THREE-RQ-STRUCTURE; C-S3R2-ADVISOR-SOURCE | Advisor requirements and local pivot history remain distinct. |
| C-P1-EFFECT | C-S3R2-P1-RESULT-AVAILABLE; C-S3R2-DOC-GATE | Use Stage 6 table/script/command for values; keep post-hoc exploratory status. |
| C-P2-DETECTION | C-S3R2-P2-RESULT-AVAILABLE; C-S3R2-DOC-GATE | Use Stage 8 table/script/command for values; preserve artifact/input/bootstrap limits. |
| C-P2-RECOVERY | C-S3R2-P2-RESULT-AVAILABLE; C-S3R2-DOC-GATE | Restrict recovery-speed claims to row-supported, well-posed cells in Stage 8 products. |
| C-P3-COMPLIANCE | C-S3R2-P3-IMPLEMENTED-BOUNDARY; C-S3R-RUNTIME-GATE | Use committed n10 rows; exact workflow_dispatch inputs remain NOT FOUND. |
| C-P3-UNIMPLEMENTED-SUPERSEDED | C-S3R2-P3-IMPLEMENTED-BOUNDARY | Keep only in AUDIT HISTORY. |
| C-S3R2-NO-NEW-EXPERIMENT | C-S3R2-ADVISOR-SOURCE | This pass updates dependency structure and ledgers, not results. |

### Stage 3R2 Unsafe Claim Blocks

| Unsafe claim | Label | Reason after Stage 3R2 | Required evidence |
|---|---|---|---|
| "The advisor notes are original advisor-authored meeting notes." | [UNRESOLVED] | The external note is hashed and direct for local extraction, but the original advisor-authored artifact and exact pivot timestamp remain NOT FOUND. | Original artifact or immutable meeting-source record resolving GAP-001. |
| "Phase 1 numeric extraction is still pending." | [SUPERSEDED] | Stage 6 Phase 1 result products now exist. | Cite STAGE6-P1-PRODUCT and preserve Stage 6 limitations. |
| "Phase 2 manuscript table extraction is still pending." | [SUPERSEDED] | Stage 8 Phase 2 result products now exist. | Cite STAGE8-P2-PRODUCT and preserve Stage 8 limitations. |
| "Phase 3 is unimplemented." | [SUPERSEDED] | Current routing and n10 committed rows treat Phase 3 as implemented. | Cite C-S3R2-P3-IMPLEMENTED-BOUNDARY and P3-N10-ROWS. |
| "Dirty documentation is primary evidence for result values." | [UNRESOLVED] | Dirty docs are mutable documentation/intent sources. | Use Stage 6/Stage 8/committed n10 row locators or verified artifacts. |
| "Stage 3R2 validates new empirical findings." | [UNRESOLVED] | Stage 3R2 performs no new experiment, effect-size analysis, or statistical-test analysis. | A later extraction or experiment stage with sources, script SHA, and exact command. |
