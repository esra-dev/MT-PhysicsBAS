# Stage 11 Appendix Notes

Scope: appendix-oriented evidence notes, reproduction records, full-table routes,
audit-history routing, and unresolved evidence records. This file is not polished
thesis prose.

## Control Record

| item | label | evidence record |
|---|---|---|
| Protocol | [DIRECT] | Appendix must preserve provenance, commands, run/artifact records, full table routes, and gap indexes without replacing primary sources. Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236`. |
| Template appendix target | [DIRECT] | Template includes `content/appendix` after bibliography and before `declaration-originality.pdf`. Locator: `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L156-L168`; appendix placeholder `local-sha256:6203cfe7864a04577cf766f12fa28991ac2336f82a0958f2f38f952c3b19579d:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/appendix.tex:L1-L1`. |
| Appendix routing | [DIRECT] | Appendix evidence categories: reproduction commands, workflows, run/artifact provenance, config/profile matrices, schemas, full tables/figures, deviations, and audit indexes. Locator: `local-sha256:0fc9679a9ab9f5b53a2ce5ae9fcb4ee654c29a1111e4135defdd6cd3df03da1c:paper_notes/TEMPLATE_MAP.md:L45-L52`; `local-sha256:0fc9679a9ab9f5b53a2ce5ae9fcb4ee654c29a1111e4135defdd6cd3df03da1c:paper_notes/TEMPLATE_MAP.md:L138-L148`. |

## Appendix A - Source And Run Provenance

| record | label | appendix notes | source locator |
|---|---|---|---|
| Repository state for Stage 11 | [DIRECT] | Current branch during Stage 11 work: `phase3-process-dynamics`; current HEAD observed by `git rev-parse`: `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`; `origin/results`: `0372ecd5864fa6555ebfce7d05e05d9aaab96994`. | `local-sha256:bc550ccaf4706201eba851203a59b176af5b1f70f63fae5cee379ce32923eeb4:paper_notes/STAGE11_GIT_AUDIT_20260618T112457Z.txt:L1-L66`; prior locator `local-sha256:698680a425a28a7c5f7e854f69b33772bf34c17fdf79da2db980f2f3b4f56ef4:paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt:L1-L4`. |
| Phase 1 result route | [DERIVED] | Stage 6 `PHASE1_TABLES.csv` is authoritative numeric table; R2 file is a selected-row routing/index table. Stage 9 confirmed `480` data rows and `0` deterministic mismatch/not-found rows, while bootstrap/statistical fields remain not independently resampled. | `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`; `local-sha256:a6004ae672bfbb32c746d907e4c1855ec54c540d98063c06d6339258411a06b0:paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv:L1-L15`; Stage 9 rows `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-16`. |
| Phase 2 result route | [DERIVED] | Final Phase 2 authority uses run `27547019772`, selected v5 source head `985c7a18558b6d5cb96c018a395b0aae6389f410`, result commit `22a448be5d9829751badd341904e36ed582f091f`, and Stage 8/R2 tables. | Run/action route `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L36-L47`; committed CSVs `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19`; `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| Phase 3 result route | [DIRECT] | Final candidate Phase 3 authority uses run `27621106006`, head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, artifact `phase3-consolidated`, artifact id `7668397627`, digest `sha256:a882677d1689d2f25470591771fd1ef80035de560e837e9ab01857381e9f9416`, and result commit `0372ecd5864fa6555ebfce7d05e05d9aaab96994`. | `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:rows 9-11,34; named columns evidence_id,claim_or_object,metric,value,input_sources`. |
| Related-work route | [DIRECT] | Bibliographic ledger has `BIB-S10B-001` through `BIB-S10B-016` plus rejected DOI row `BIB-S10B-REJ-001`; DOI-only rows require full-text review before technical claims beyond metadata. | `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:L1-L18`; gap `local-sha256:21bda331030f22c593454e85fa1daf2a4c066eef0a656d3e8872e9be3381f86d:paper_notes/RELATED_WORK_NOTES.md:L170-L177`. |

## Appendix B - Reproduction Commands

Use as command notes, not as a claim that the command was rerun in Stage 11 unless stated.

| command target | label | exact command / command family | source locator |
|---|---|---|---|
| Phase 1 extraction | [DERIVED] | `node paper_notes/phase1_extract_tables.mjs paper_notes/PHASE1_TABLES.csv` | Script `local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520`; route `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L11-L17`. |
| Phase 2 extraction | [DERIVED] | `node paper_notes\phase2_extract_results.mjs --root paper_notes\stage8_phase2_origin_results_22a448be5d9829751badd341904e36ed582f091f --out paper_notes\PHASE2_TABLES_R2_20260618T090000Z.csv` | Script `local-sha256:ad7844e6d06e02b34a92af278774bd853a3ba48ea8ef5763ec35556bfc27ed42:paper_notes/phase2_extract_results.mjs:L1-L488`; route `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L21-L27`. |
| Stage 9 audit | [DERIVED] | `node paper_notes/stage9_statistical_integrity_audit.mjs paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv` | Script `local-sha256:4a676e702609ccb35915a8698c1ecca458d7d1afb7ae3d3723d6c219c0d848e8:paper_notes/stage9_statistical_integrity_audit.mjs:L1-L300`; output `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:L1-L22`. |
| Phase 3 n10 recompute | [DERIVED] | `python analysis/phase3_dynamics.py --root phase3_download_n10/phase3-consolidated/dynamics_root --out paper_notes/stage10a_phase3_recompute_n10` | Script `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L1-L575`; evidence `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:rows 14-15`. |
| Phase 3 n5 audit recompute | [SUPERSEDED] | `python analysis/phase3_dynamics.py --root phase3_download/phase3-consolidated/dynamics_root --out paper_notes/stage10a_phase3_recompute_n5` | `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 33`. |
| Local tree hashing | [DERIVED] | `node paper_notes/TREE_SHA256_V1.mjs <path>`; use for local directory provenance only. | Protocol definition `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L82-L103`; Phase 3 example `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 12`. |

## Appendix C - Experiment Matrices

| phase | label | matrix notes | source locator |
|---|---|---|---|
| Phase 1 | [DIRECT] | Profiles `lab1`, `lab2`, `lab3`; stereotype training arms `true`, `false`; benchmark modes `rule_based`, `ql_false`, `ql_true`; workflow default seed input `1,2,3,4,5,6,7,8,9,10`; exact dispatch inputs remain `NOT FOUND`. | `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:config/run_config.json:L163-L165`; `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:.github/workflows/phase1.yml:L28-L35`; unresolved `local-sha256:b68dfdf6341ccb3fbf72e2706a7cf8dd04560e9518d1f1509d4caeca4b2f3523:paper_notes/PHASE1_METHODS.md:L301-L307`. |
| Phase 1 run modes | [DIRECT] | Include `phase1_baseline`, `phase1_kg_only`, `phase1_kg_only_ib5`, `phase1_pbrs_only`, `phase1_full`, `phase1_kg_xzone`, and `phase1_kg_xzone_rand`; use table to separate component isolation from main lab2 result. | `local-sha256:b68dfdf6341ccb3fbf72e2706a7cf8dd04560e9518d1f1509d4caeca4b2f3523:paper_notes/PHASE1_METHODS.md:L71-L96`; ablation `kg-crosszone-ablation@e8d63e09be504f1dc206737ca8feb05299fe1031:config/run_config.json:L162-L178`. |
| Phase 2 | [DIRECT] | Adapt profiles: `lab1_f1dead`, `lab2_f1dead`, `lab2_f1inv`, `lab2_f2dead`, `lab2_f2inv`, `lab3_f1dead`, `lab3_f1inv`, `lab3_f2dead`, `lab3_f2inv`; modes `ql_true`, `ql_false`; parent profiles, ports, flows, Q-table suffixes, clean-source suffixes, and state-vector dimensions in config. | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L242-L313`. |
| Phase 3 | [DIRECT] | Profiles `lab2_slow`, `lab3_slow`; modes `ql_true`, `ql_false`; `seconds_per_tick=5.0`; `blind_delay_ticks=12`; `probes_per_actuator=8`; `settle_ms=400`; `poll_ms=50`; `max_wait_ticks=60`; target rank `3`; probe sun rank `900`; `6` time-bounded goals. | `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L322-L365`; methods row `local-sha256:6f52ebe57ffbbc85fccd28e495538129b086d94c3483f594bb2daf6e5d9ac0ee:paper_notes/PHASE3_METHODS.md:L51-L75`. |

## Appendix D - Statistical Integrity

| statistical item | label | notes | source locator |
|---|---|---|---|
| Phase 1 table audit | [DERIVED] | `480` data rows; `348` mean rows match raw data; `132` mean-difference rows match raw data; `0` mismatch/not-found rows; `348` CI rows and `132` p/q/CI rows are not independently resampled. | `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 11-16`. |
| Phase 2 table audit | [DERIVED] | `521` data rows; `306` deterministic-from-raw; `99` deterministic-or-exact-test; `116` direct analysis-output resampling rows; `0` failed-check rows. | `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 2-8`. |
| Phase 2 family sizes | [DIRECT] | `RecoveryEpisodes` paired-family size is `2`; `DetectEpisode` paired-family size is `9`. | `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 9-10`; direct paired CSV `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| Phase 3 recompute | [DERIVED] | n10 recomputation produced `4` delay rows, `4` compliance CI rows, and `8` paired rows; delay and paired CSVs are byte-identical to downloaded consolidated CSVs; compliance CI is numeric-match-not-byte-identical due to floating string representation. | `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:rows 14-15`. |
| BH nuance | [INTERPRETATION] | Phase 2 BH arithmetic was checked from aggregate bootstrap p-values, but bootstrap p-values remain direct analysis outputs; do not describe BH q-values as independently resampled evidence. | `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L46-L60`. |

## Appendix E - Full Table Routes

| table family | label | append notes | source locator |
|---|---|---|---|
| Phase 1 compact evidence table | [DERIVED] | Include all rows from `PHASE1_TABLES_R2_20260618T075201Z.csv` or link as supplementary CSV; row IDs `R2P1T-001` through `R2P1T-014`. | `local-sha256:a6004ae672bfbb32c746d907e4c1855ec54c540d98063c06d6339258411a06b0:paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv:L1-L15`. |
| Phase 2 final CI table | [DIRECT] | Include committed aggregate CI table or reproduce selected columns; source has `18` data rows for `9` profiles by `2` modes. | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19`. |
| Phase 2 final paired table | [DIRECT] | Include committed aggregate paired table; rows `2-3` are `RecoveryEpisodes`, rows `4-12` are `DetectEpisode`. | `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`. |
| Phase 2 detailed verification table | [DERIVED] | Keep `PHASE2_TABLES_R2_20260618T090000Z.csv` as supplementary evidence because it contains raw-derived input chains and verification statuses. | `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv:L1-L522`. |
| Phase 3 result tables | [DIRECT] | Include delay accuracy, compliance CI, paired compliance, and selected mechanism/provenance rows from `PHASE3_TABLES.csv`. | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`; `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:L1-L36`. |
| Bibliographic ledger | [DIRECT] | Include or reference source IDs, topic buckets, DOI/arXiv fields, full-text status, and rejected Brick DOI correction. | `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:L1-L18`. |

## Appendix F - Figure Specifications

| figure family | label | appendix notes | source locator |
|---|---|---|---|
| Architecture diagrams | [DIRECT] | Include component and dataflow diagrams as evidence diagrams, not polished final figures unless rendered and checked later. | `local-sha256:686cb1cf647d8fa1dd53f82aaf4fe26ef157f262839d386916587fd9ad97934e:paper_notes/ARCHITECTURE_COMPONENT_DIAGRAM_R2_20260617T185133Z.mmd:L1-L100`; `local-sha256:b34d62b3e15e44bf6acdf163203a3c2717465c2fb00e5780abd3fcb2b57ae2a9:paper_notes/ARCHITECTURE_DATAFLOW_DIAGRAM_R2_20260617T185133Z.mmd:L1-L67`. |
| Phase 1 figures | [DIRECT] | Lab2 forest plot, lab3 active/superseded boundary panel, ablation panel, provenance map, limitations panel. | `local-sha256:d7ffc30e83ef10fca0e79f32ae66ce65eeb6e2a4a68c974cabde52ea4e576094:paper_notes/PHASE1_FIGURES_R2_20260618T075201Z.md:L9-L27`. |
| Phase 2 figures | [DIRECT] | Detection/attribution heatmap, well-posed recovery forest plot, detection latency panel, Phase 2 supersession strip, provenance/limitation panel. | `local-sha256:5775e278fb7b2d280158d2b728d4364e93c6b41d91fce077460a2418680ea87b:paper_notes/PHASE2_FIGURES.md:L1-L39`. |
| Phase 3 figures | [DIRECT] | Pipeline diagram, deadline-planner schematic, delay accuracy, compliance bars, paired effect panel, energy trade-off panel, n5/n10 supersession strip, provenance status panel. | `local-sha256:d8e7b1953499f3e0a951d1c85c5b3dcb0128285c7f0bb38783680ed76dc778dd:paper_notes/PHASE3_FIGURES.md:L5-L25`. |
| Related-work map | [INTERPRETATION] | Layered related-work map and categorical heatmap are suitable appendix figures if main text needs shorter related-work prose. | `local-sha256:21bda331030f22c593454e85fa1daf2a4c066eef0a656d3e8872e9be3381f86d:paper_notes/RELATED_WORK_NOTES.md:L161-L168`. |

## Appendix G - Audit History Index

| audit branch | label | include in appendix? | source locator |
|---|---|---|---|
| Phase 1 as-is -> bumped -> ablation | [SUPERSEDED] | Include compact supersession table only if needed to explain why lab3 as-is rows are not final authority. | `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L20-L35`. |
| Phase 2 v1-v5 | [SUPERSEDED] | Include compact supersession table for base Phase 2, Phase 2.1, Phase 2.2, attribution fix, ambiguous-abstain v5, and later CI hardening. | `local-sha256:29a0283decbc6967d15d72a2080722c314c035c343b8ff3ac4a44dcead113f9b:paper_notes/PHASE2_METHODS.md:L120-L156`; `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L36-L47`. |
| Phase 3 n5 -> n10 | [SUPERSEDED] | Include only as audit note: n5 had Wilcoxon floor issue; n10 is final candidate authority. | `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 33`. |
| Bibliographic correction | [SUPERSEDED] | Include only if documenting source hygiene: wrong Brick DOI candidate rejected; corrected DOI recorded. | `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:row 18`; successor `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:row 11`. |

## Appendix H - Evidence Gap Index

| gap | label | appendix note | source locator |
|---|---|---|---|
| GAP-001 advisor source provenance | [UNRESOLVED] | Advisor note is local external source and requirement evidence; do not treat it as empirical result evidence. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L5-L18`. |
| GAP-021 formal post-pivot preregistration | [UNRESOLVED] | Formal post-pivot preregistration remains `NOT FOUND`; Phase 3 n10 can be described only as confirmatory relative to local expectation/top-up documentation, not preregistered confirmatory. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L294-L322`. |
| GAP-035 Phase 1 result limits | [UNRESOLVED] | Phase 1 artifact ZIP byte identity, exact dispatch inputs, independent resampling, and lab3 stale magnitude remain unresolved. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L563-L581`. |
| GAP-037 Phase 2 result limits | [UNRESOLVED] | Phase 2 artifact ZIP identity, exact dispatch inputs, NumPy bootstrap reproduction, and formal Phase 2 preregistration remain unresolved. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L637-L660`. |
| GAP-044 Stage 9 statistical boundary | [UNRESOLVED] | Deterministic/exact checks are separated from unresolved bootstrap-resampling reproduction. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L853-L879`. |
| GAP-045 Phase 3 authority limits | [UNRESOLVED] | Phase 3 n10 is authority candidate; exact dispatch payload and ZIP-byte identity remain unresolved; formal prereg remains `NOT FOUND`. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L881-L921`. |
| GAP-046 related-work limits | [UNRESOLVED] | DOI-only Crossref rows need full-text review before technical claims beyond metadata. | `local-sha256:0fd561d0541c8e9c5456d1f439748c2a63fb4acae878eba95654eb14c50fee60:paper_notes/EVIDENCE_GAPS.md:L923-L954`. |

## Handoff

Completed:

- [DIRECT] Created appendix routing notes for source/run provenance, reproduction commands, experiment matrices, statistical integrity, table routes, figure specs, audit history, and evidence gaps.
- [DIRECT] Kept Phase 3 n10 as evaluated contribution and n5 as superseded audit history.
- [UNRESOLVED] Kept all active provenance/statistical gaps visible.

Unresolved:

- [UNRESOLVED] No final LaTeX appendix text was written.
- [UNRESOLVED] No artifact ZIPs were redownloaded or byte-verified in Stage 11.
- [UNRESOLVED] No bootstrap resampling was rerun in Stage 11.
- [UNRESOLVED] No figures were rendered in Stage 11.

Next stage must read:

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/PAPER_SECTION_NOTES.md`
3. `paper_notes/APPENDIX_NOTES.md`
4. `paper_notes/SOURCE_LEDGER.csv`
5. `paper_notes/CLAIM_LEDGER.csv`
6. `paper_notes/RUN_LEDGER.csv`
7. `paper_notes/EVIDENCE_GAPS.md`
8. `paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv`
9. `paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv`
10. `paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`
11. `paper_notes/PHASE3_TABLES.csv`
12. `paper_notes/BIBLIOGRAPHIC_LEDGER.csv`
