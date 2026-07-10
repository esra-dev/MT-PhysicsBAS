# Stage 0 Worktree Status Refresh

## Snapshot

- Observed at UTC: `2026-06-17T06:51:11.3582240Z`
- Local timezone shown by shell: `Europe/Zurich`, command output `2026-06-17T08:48:16.5502933+02:00`
- Current branch: `phase3-process-dynamics`
- Current HEAD: `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`
- Upstream: `origin/phase3-process-dynamics`
- Upstream divergence: `+1/-0`
- Staged tracked changes: `0`
- Unstaged tracked changes: `2`
- Unstaged tracked files:
  - `docs/PHASE1_TO_PHASE2_CHANGES.md`
  - `docs/PHASE2_TO_PHASE3_CHANGES.md`
- Normal untracked files from `git ls-files --others --exclude-standard -z`: `2343`
- Normal untracked top-level paths: `26`
- Ignored files from `git ls-files --others -i --exclude-standard -z`: `19243`
- Ignored top-level paths: `226`
- Git emitted warning during untracked/ignored enumeration:
  `warning: could not open directory '.pytest_cache/': Permission denied`

## Normal Untracked Top-Level Paths

`.github`; `.node-red-lab1`; `.node-red-lab2`; `.node-red-lab2_f1dead`;
`.node-red-lab2_slow`; `.node-red-lab3`; `.node-red-lab3_slow`; `analysis`;
`benchmark`; `dashboard`; `docs`; `paper_notes`; `phase1_xzone_ablation`;
`phase1_xzone_asis`; `phase1_xzone_bumped`; `phase1_xzone_bumped_s11_20`;
`phase2_results`; `phase2_results_v2`; `phase2_results_v3`;
`phase2_results_v4`; `phase2_results_v5`; `phase3_download`;
`phase3_download_n10`; `THESIS_PIVOT_MASTER.md`; `tmp_sweep_n10_results`;
`tmp_sweep18_results`.

## Scope Boundary

- This refresh is provenance-only.
- No branch switch, reset, clean, delete, artifact overwrite, workflow dispatch,
  or experimental analysis was performed.
- Result-root hashes are recorded in
  `paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv`.
- Dirty documentation and root-level Phase 3 runtime-file hashes are recorded in
  `paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv`.
- Empirical claims inside dirty documentation remain documentation-only until a
  later stage checks each numeric value against primary CSV, JSON, Actions, or
  committed result sources.

## Commands

- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git rev-parse --abbrev-ref --symbolic-full-name '@{u}'`
- `git rev-list --left-right --count HEAD...'@{u}'`
- `git status --short --branch --untracked-files=no`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git ls-files --others --exclude-standard -z`
- `git ls-files --others -i --exclude-standard -z`
- `node paper_notes/TREE_SHA256_V1.mjs <root>`

