# Stage 4 Inventory Handoff

## Completed Work

- [DIRECT] Read `paper_notes/00_PROTOCOL.md`, `paper_notes/STAGE_HANDOFF.md`, `paper_notes/STAGE2_PHASE3_HANDOFF.md`, `paper_notes/STAGE3_HANDOFF.md`, and current `docs/PHASE2_TO_PHASE3_CHANGES.md`.
- [DIRECT] Inspected repository history and refs using `git status`, `git log`, `git show`, and `git diff`; no branch switch, reset, clean, deletion, or artifact overwrite was performed.
- [DERIVED] Created current local tree-hash manifest `paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv`.
- [DERIVED] Created current local file-hash manifest `paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv`.
- [DIRECT] Created current worktree-status snapshot `paper_notes/STAGE4_WORKTREE_STATUS_20260616T143435Z.md`.
- [DIRECT] Added Stage 4 source, claim, run, and evidence-gap ledger entries for inventory/provenance only.

## Inventory Findings

- [DIRECT] Current branch is `phase3-process-dynamics` at `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`, ahead of `origin/phase3-process-dynamics` by `+1/-0`.
- [DIRECT] Dirty tracked files are `docs/PHASE1_TO_PHASE2_CHANGES.md` and `docs/PHASE2_TO_PHASE3_CHANGES.md`.
- [DIRECT] Normal untracked top-level path count is `40`; the count excludes ignored root-level Phase 3 runtime files.
- [DERIVED] New or newly relevant local result/download roots hashed in this pass:
  - `phase2_results_v5`: `TREE-SHA256-V1=3798621f34ecd354993e13a7c5a096dab6fe54c4873225798efcd16750ee97e1`
  - `phase3_download`: `TREE-SHA256-V1=4ba5cc8f694d07c3e53d1be5d4fd4fae42a8b5ee3e4fb36d520fa48fb759aebe`
  - `phase3_download_n10`: `TREE-SHA256-V1=5fe3c3e8c57c1ea1da0338fe888161006b99e26a7f50d6cbabc7850ab3848d2c`
  - `.node-red-lab2_slow`: `TREE-SHA256-V1=c9edabed97512e512aa8b8e8db5e18b852ad9e5451217014345c8f2ebb881e38`
  - `.node-red-lab3_slow`: `TREE-SHA256-V1=fbc19a2f6133a9cb229ca0d61e5591cd265aef5808c672cb9475d59238934d7d`

## Unresolved Issues

- [UNRESOLVED] `phase2_results_v5`, `phase3_download`, and `phase3_download_n10` are classified as declared Actions-derived local roots, but artifact ZIP byte identity was not verified in Stage 4.
- [UNRESOLVED] Root-level ignored Phase 3 runtime files were hashed individually, but exact command/run identity is NOT FOUND; prefer run-scoped `origin/results` or Actions artifacts for manuscript evidence.
- [UNRESOLVED] Dirty documentation files contain empirical result prose and numeric values; Stage 4 did not analyze those result claims.
- [UNRESOLVED] `.pytest_cache/` remains unreadable due access denial and excluded from evidence.

## Next Stage Must Read

- `paper_notes/00_PROTOCOL.md`
- `paper_notes/STAGE4_WORKTREE_STATUS_20260616T143435Z.md`
- `paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv`
- `paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv`
- `paper_notes/SOURCE_LEDGER.csv`
- `paper_notes/CLAIM_LEDGER.csv`
- `paper_notes/RUN_LEDGER.csv`
- `paper_notes/EVIDENCE_GAPS.md`
- `paper_notes/STAGE3_HANDOFF.md`
- `paper_notes/STAGE2_PHASE3_HANDOFF.md`
- `docs/PHASE2_TO_PHASE3_CHANGES.md`
- `docs/PHASE1_TO_PHASE2_CHANGES.md`

## Boundary For Next Stage

- Do not treat dirty docs as primary empirical evidence.
- Do not cite local result roots as byte-identical Actions artifacts unless ZIP/download digest verification is added.
- Do not analyze Phase 3 or Phase 2 result values from Stage 4 manifests; use primary CSV rows from committed `origin/results` snapshots or verified Actions artifacts.
