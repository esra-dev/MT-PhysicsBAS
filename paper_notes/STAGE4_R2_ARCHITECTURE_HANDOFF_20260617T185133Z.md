# Stage 4R2 Architecture Handoff - 20260617T185133Z

## Scope

- [DIRECT] Stage 4R2 read the Stage3R2 handoff bundle and refreshed architecture notes against current Stage 6 Phase 1, Stage 8 Phase 2, and Phase 3 n10 routing. Source: `local-sha256:440aa36d3121a1fda187368957c4125f2e2ed6d8802c6d8509cbc5982f586fa4:paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md:L31-L51`.
- [DIRECT] No workflow was dispatched, no experiment was executed, no result value was recomputed, and no statistical test was run in Stage 4R2. Stage 4R2 is architecture/source-trace evidence only.
- [DIRECT] Worktree safety boundary: no branch switch, reset, clean, delete, or artifact overwrite was performed. New artifacts were added beside existing Stage 4 files.

## Completed Work

- [DERIVED] Appended Stage 4R2 architecture refresh to `ARCHITECTURE_NOTES.md`. Locator: `local-sha256:a9c7575fa7eab03b3148db31cb9f1f63ac66007babc995adfca27d8f64c61472:paper_notes/ARCHITECTURE_NOTES.md:L153-L284`.
- [DERIVED] Added R2 component diagram. Locator: `local-sha256:686cb1cf647d8fa1dd53f82aaf4fe26ef157f262839d386916587fd9ad97934e:paper_notes/ARCHITECTURE_COMPONENT_DIAGRAM_R2_20260617T185133Z.mmd:L1-L100`.
- [DERIVED] Added R2 data-flow diagram. Locator: `local-sha256:b34d62b3e15e44bf6acdf163203a3c2717465c2fb00e5780abd3fcb2b57ae2a9:paper_notes/ARCHITECTURE_DATAFLOW_DIAGRAM_R2_20260617T185133Z.mmd:L1-L67`.
- [DIRECT] Traced required layers: Jason agents, Java/CArtAgO artifacts, `QLearner`, `StereotypeReasoner`, `DynamicsLearner`, ontologies/TTL, Thing Descriptions, Node-RED slow physics, lab profiles, configuration, PowerShell orchestration, workflows, analysis scripts, and output contracts. Primary locators are in `ARCHITECTURE_NOTES.md` Stage 4R2 tables.
- [SUPERSEDED] Marked older Stage 4 "Phase 1/Phase 2 extraction pending" routing as audit history only. Current manuscript routing uses Stage 6 Phase 1 and Stage 8 Phase 2 products. Sources: `local-sha256:73ade353d433f46a5e8beaec51eb6e542abca16b5ece8f7aa7f9e0dd85d33263:paper_notes/RESEARCH_MODEL.md:L147-L148`; `local-sha256:cbc6fa703b65be98da371c8783f6fc92c7c6218464d85b584ee03bf5916e3c03:paper_notes/CLAIM_DEPENDENCY_MAP.md:L154-L155`.

## Unresolved Issues

- [UNRESOLVED] Original advisor-authored artifact and exact pivot timestamp remain NOT FOUND. Source: `local-sha256:27d9cf1bd352d08ca67b6678e47e2ac73ba70baf819848ef9c4a1c6a52905f64:paper_notes/EVIDENCE_GAPS.md:L669-L698`.
- [UNRESOLVED] Artifact ZIP byte identity remains NOT VERIFIED unless separately resolved for each run. Source: `local-sha256:27d9cf1bd352d08ca67b6678e47e2ac73ba70baf819848ef9c4a1c6a52905f64:paper_notes/EVIDENCE_GAPS.md:L669-L698`.
- [UNRESOLVED] Formal post-pivot preregistration remains NOT FOUND; Phase 3 is confirmatory only relative to local pre-run plan. Source: `local-sha256:73ade353d433f46a5e8beaec51eb6e542abca16b5ece8f7aa7f9e0dd85d33263:paper_notes/RESEARCH_MODEL.md:L157-L165`.
- [UNRESOLVED] Stage 6 Phase 1 and Stage 8 Phase 2 independent resampling limits remain active. Sources: `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L102-L119`; `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L102-L119`.
- [UNRESOLVED] Exact Phase 3 run `27621106006` workflow_dispatch inputs remain NOT FOUND, and root-level Phase 3 runtime TTL/CSV identity remains audit-only unless exact command/run/artifact identity is recovered. Source: `local-sha256:440aa36d3121a1fda187368957c4125f2e2ed6d8802c6d8509cbc5982f586fa4:paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md:L20-L29`.
- [UNRESOLVED] Dirty `docs/*` files remain intent/history context only, not primary numeric evidence. Source: `local-sha256:440aa36d3121a1fda187368957c4125f2e2ed6d8802c6d8509cbc5982f586fa4:paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md:L20-L29`.

## Next Stage Must Read

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/RESEARCH_MODEL.md`
3. `paper_notes/CLAIM_DEPENDENCY_MAP.md`
4. `paper_notes/SOURCE_LEDGER.csv`
5. `paper_notes/CLAIM_LEDGER.csv`
6. `paper_notes/RUN_LEDGER.csv`
7. `paper_notes/EVIDENCE_GAPS.md`
8. `paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md`
9. `paper_notes/PHASE1_RESULTS.md`
10. `paper_notes/PHASE1_TABLES.csv`
11. `paper_notes/PHASE1_FIGURES.md`
12. `paper_notes/phase1_extract_tables.mjs`
13. `paper_notes/PHASE2_RESULTS.md`
14. `paper_notes/PHASE2_TABLES.csv`
15. `paper_notes/phase2_extract_results.mjs`
16. `paper_notes/PHASE2_ACTIONS_STAGE8.csv`
17. `paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv`
18. `docs/PHASE1_TO_PHASE2_CHANGES.md`
19. `docs/PHASE2_TO_PHASE3_CHANGES.md`
20. `C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt`
21. `paper_notes/ARCHITECTURE_NOTES.md`
22. `paper_notes/ARCHITECTURE_COMPONENT_DIAGRAM.mmd`
23. `paper_notes/ARCHITECTURE_DATAFLOW_DIAGRAM.mmd`
24. `paper_notes/ARCHITECTURE_COMPONENT_DIAGRAM_R2_20260617T185133Z.mmd`
25. `paper_notes/ARCHITECTURE_DATAFLOW_DIAGRAM_R2_20260617T185133Z.mmd`
26. `paper_notes/STAGE4_R2_ARCHITECTURE_HANDOFF_20260617T185133Z.md`
