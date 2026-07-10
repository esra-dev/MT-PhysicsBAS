# Stage 2 Handoff

## Completed

- [DIRECT] Created `paper_notes/CHRONOLOGY.md` with separate `AUDIT HISTORY`
  and `MANUSCRIPT EVIDENCE` routing, ref topology, dated iterations,
  supersession records, result tags, experiment-design records, authority
  candidates, and figure specifications.
- [DERIVED] Captured `117` Actions runs visible at
  `2026-06-15T15:34:50.3118706Z`. Evidence:
  `SRC-S2-002` through `SRC-S2-006`; claim `CLM-S2-004`.
- [DIRECT] Refreshed six selected Actions runs at
  `2026-06-15T15:50:57.8683740Z`. Run `27547019772` remained `in_progress` on
  head `985c7a18558b6d5cb96c018a395b0aae6389f410`. Evidence: `SRC-S2-008`,
  `CLM-S2-008`, and the additive Stage 2 row in `RUN_LEDGER.csv`.
- [DIRECT] Reconstructed Phase 1 progression: clean-lab full stack, factorial
  isolation, init-bonus sensitivity, KG-off falsification, cross-zone as-is,
  bumped treatment, independent seed replication, and untargeted ablation.
  Evidence: `CLM-S2-006` and `CHRONOLOGY.md` records `EXP-P1-01` to
  `EXP-P1-04`.
- [DIRECT] Reconstructed Phase 2 v1-v5 instrument/detector corrections.
  Evidence: `CLM-S2-007` and `CHRONOLOGY.md` records `EXP-P2-01` to
  `EXP-P2-05`.
- [DERIVED] Searched named refs for a formal post-pivot preregistration. It was
  `NOT FOUND` under the recorded search scope. Evidence: `SRC-S2-011`,
  `SRC-S2-012`, and `CLM-S2-005`.
- [SUPERSEDED] Preserved the invalid first Actions normalization, intermediate
  scalar-truncated Git audit, and invalid `System.Object[]` run-ledger row.
  Corrected successors were added without deleting audit artifacts. Evidence:
  `SRC-S2-013`, `SRC-S2-014`, and `CLM-S2-010`.
- [DIRECT] Updated `SOURCE_LEDGER.csv`, `CLAIM_LEDGER.csv`, `RUN_LEDGER.csv`,
  and `EVIDENCE_GAPS.md`.

## Unresolved

- [UNRESOLVED] Original advisor-authored pivot notes and the exact meeting time
  remain `NOT FOUND`; use only the hashed requirement surrogate and the bounded
  implementation interval. Evidence: `GAP-001`, `CLM-S2-003`.
- [UNRESOLVED] Phase 2 v5 run `27547019772` has no completed conclusion or final
  ingested result root. Do not promote v4 to final authority without a new status
  check. Evidence: `GAP-012`, `CLM-S2-008`.
- [UNRESOLVED] All six selected jobs endpoints returned HTTP 504/invalid JSON;
  job-step details are `NOT FOUND`. Evidence: `SRC-S2-009`, `CLM-S2-009`.
- [UNRESOLVED] Formal post-pivot preregistration remains `NOT FOUND`. Phase 1/2
  are post-hoc exploratory or engineering-validation lines; replication and
  ablation are prospective checks within a post-hoc line. Evidence: `GAP-021`,
  `CLM-S2-005`.
- [UNRESOLVED] Complete artifact ZIP-to-local-root identity remains open.
  Evidence: `GAP-002`, `GAP-009`, `GAP-013`.
- [UNRESOLVED] Numeric findings have not been re-extracted in Stage 2. Local
  analysis notes are source statements, not substitutes for raw row-level
  verification.
- [UNRESOLVED] Thesis Phase 3 implementation/results remain `NOT FOUND`.
  Evidence: `GAP-017`, `CLM-S1-006`.

## Required Read Order For The Next Stage

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/STAGE2_HANDOFF.md`
3. `paper_notes/CHRONOLOGY.md`
4. `paper_notes/SOURCE_LEDGER.csv`
5. `paper_notes/CLAIM_LEDGER.csv`
6. `paper_notes/RUN_LEDGER.csv`
7. `paper_notes/EVIDENCE_GAPS.md`
8. `paper_notes/ACTIONS_RUNS_20260615T153450Z.csv`
9. `paper_notes/ACTIONS_SELECTED_RUNS_20260615T155057Z.csv`
10. `paper_notes/ACTIONS_CAPTURE_ERRORS_20260615T155057Z.csv`
11. `paper_notes/ACTIONS_ARTIFACTS_20260615T155057Z.csv`
12. `paper_notes/GIT_AUDIT_20260615T153450Z.txt`
13. `paper_notes/POST_PIVOT_PREREG_SEARCH_20260615.txt`
14. `THESIS_PIVOT_MASTER.md`
15. `docs/pre_registration.md`
16. `docs/phase1_results_n10.md`
17. `docs/phase1_xzone_asis_analysis.md`
18. `docs/phase1_xzone_bumped_analysis.md`
19. `docs/phase1_xzone_replication_s11_20_analysis.md`
20. `docs/phase1_xzone_ablation_analysis.md`
21. `docs/PHASE1_TO_PHASE2_CHANGES.md`

## Required Immutable Ref Reads

- `feature/qlearning-stereotype-comparison@9cfe38c292983347e08f6b6773243ee40fe5a001:docs/thesis_meeting_2026-05-22.tex`
- `main@beaf8eac3137d1bbf255f9e3b68ce94413eea805:docs/pre_registration.md`
- `main@7ac37a10fe3b3c23bc2b54159c40142fd367e821:config/run_config.json`
- `main@7ac37a10fe3b3c23bc2b54159c40142fd367e821:.github/workflows/phase1.yml`
- `kg-crosszone-coupling@7629d0f1f5a77e22329ccec159115e4c7ab52cec:docs/kg_crosszone_coupling_fix.md`
- `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:simulator/simulator_flow_lab3.json`
- `kg-crosszone-ablation@e8d63e09be504f1dc206737ca8feb05299fe1031:config/run_config.json`
- `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/PHASE1_TO_PHASE2_CHANGES.md`
- `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/phase2.yml`
- `origin/results@791626314fb47d5324ba3336daed5906ef2e53b1:results-20260611-123741-phase1_baseline-7ac37a1/RUN_MANIFEST.json`
- `origin/results@e9b9e3529cd71fce3ad9dfe5fa29c64793898b2e:phase2/27529585379-20260615-112824`

## Next-Stage Boundary

- Begin row-level result extraction only from candidate authoritative runs listed
  in `CHRONOLOGY.md`.
- Keep failed/superseded runs in `AUDIT HISTORY`; do not move their effect values
  into `MANUSCRIPT EVIDENCE`.
- Re-query run `27547019772` before selecting final Phase 2 authority because its
  Stage 2 status was mutable and incomplete.
