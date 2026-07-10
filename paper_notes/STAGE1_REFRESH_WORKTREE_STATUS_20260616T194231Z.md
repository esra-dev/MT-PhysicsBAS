# Stage 1 Refresh Worktree Snapshot

- [DIRECT] Observed at UTC: `2026-06-16T19:42:31.0335226Z`.
- [DIRECT] Current working directory: `C:\Users\esrad\Downloads\MT-Esra-V1 - Copy`.
- [DIRECT] Current branch: `phase3-process-dynamics`.
- [DIRECT] Current HEAD: `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`.
- [DIRECT] Branch relation reported before note edits:
  `phase3-process-dynamics...origin/phase3-process-dynamics [ahead 1]`.
- [DIRECT] Dirty tracked files reported before note edits:
  `docs/PHASE1_TO_PHASE2_CHANGES.md` and
  `docs/PHASE2_TO_PHASE3_CHANGES.md`.
- [DIRECT] The normal `git status --short --branch` command reported a
  `.pytest_cache/` permission warning before note edits; this cache remains
  excluded from evidence inventory.
- [DIRECT] No branch switch, reset, clean, deletion, artifact overwrite, or
  experimental run was performed during this Stage 1 refresh.

## Commands Used

- `git status --short --branch`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git ls-tree -r --name-only HEAD`
- `git log --oneline --decorate --max-count 20 --all`
- `git branch --all --verbose --no-abbrev`
- `git diff --name-status HEAD -- docs\PHASE1_TO_PHASE2_CHANGES.md docs\PHASE2_TO_PHASE3_CHANGES.md`
- `node paper_notes\TREE_SHA256_V1.mjs 'C:\Users\esrad\Downloads\Template-ThesisReport\Template-ThesisReport'`
- `rg -n ...` over current committed source files to obtain line locators
