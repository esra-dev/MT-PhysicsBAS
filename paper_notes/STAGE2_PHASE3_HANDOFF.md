# Stage 2 Continuation Handoff: Phase 3 Chronology

## Completed

- [DIRECT] Refreshed Git/Actions evidence after Phase 3 n10 completion:
  `ACTIONS_RUNS_20260616T133609Z.*`, `GIT_AUDIT_20260616T133609Z.txt`,
  `ACTIONS_SUMMARY_20260616T133609Z.csv`, and selected run/job/artifact captures
  at `2026-06-16T13:36:27.7201156Z`.
- [DIRECT] Updated `CHRONOLOGY.md` with finalized Phase 2 v5, Phase 3 n5
  supersession, Phase 3 n10 authority candidate, and an `EXP-P3-01` design
  record.
- [DIRECT] Updated ledgers:
  `SOURCE_LEDGER.csv` (`SRC-S2-017` through `SRC-S2-031`),
  `CLAIM_LEDGER.csv` (`CLM-S2-011` through `CLM-S2-018`), `RUN_LEDGER.csv`
  additive corrected rows for Phase 2/Phase 3, and `EVIDENCE_GAPS.md`
  (`GAP-012`, `GAP-013`, `GAP-017`, `GAP-021`).

## Unresolved

- [UNRESOLVED] Exact `workflow_dispatch` inputs for run `27621106006` are
  `NOT FOUND`. The run executed n10 according to result rows/job matrices, but
  the exposed run metadata reports head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`,
  whose workflow default is still `1,2,3,4,5`.
- [UNRESOLVED] Artifact ZIP byte identity and downloaded local tree hashes for
  Phase 2 v5 and Phase 3 n10 are `NOT FOUND`; committed `origin/results` CSVs
  are the current authoritative result sources.
- [UNRESOLVED] Formal post-pivot preregistration remains `NOT FOUND`. Phase 3
  n10 is confirmatory relative to local pre-run commit
  `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`, not formally registered.

## Next Stage Must Read

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/CHRONOLOGY.md`
3. `paper_notes/SOURCE_LEDGER.csv`
4. `paper_notes/CLAIM_LEDGER.csv`
5. `paper_notes/RUN_LEDGER.csv`
6. `paper_notes/EVIDENCE_GAPS.md`
7. `docs/PHASE1_TO_PHASE2_CHANGES.md`
8. `docs/PHASE2_TO_PHASE3_CHANGES.md`
9. `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/`
10. `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/`
