# Stage 4 Worktree Status Snapshot

- Observed at UTC: `2026-06-16T14:34:35Z`
- Current branch: `phase3-process-dynamics`
- HEAD: `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`
- Upstream: `origin/phase3-process-dynamics`
- Upstream divergence: `+1/-0`
- Normal tracked status entries: `2`
- Normal untracked top-level entries: `40`
- Status limitation: `git status --porcelain=v2 --branch --untracked-files=normal` reported `warning: could not open directory '.pytest_cache/': Permission denied` in the terminal output; `.pytest_cache/` remains excluded from evidence.

## Tracked Dirty Files

- [DIRECT] `docs/PHASE1_TO_PHASE2_CHANGES.md` is tracked and modified in the worktree.
  - Local locator: `local-sha256:6885096decf6080cafec4f2c17f01197d18e7e400bc0fa5ccb9c6b0e65136943:docs/PHASE1_TO_PHASE2_CHANGES.md:L1-L1579`
  - Diff stat observed: `252` insertions.
  - Dirty-added region begins at line `1331` with `## 19 Run #27547019772 ("v5") -- final certified results & Phase-2 sign-off`.
  - Stage 4 did not analyze or verify the numeric result claims in this dirty region.
- [DIRECT] `docs/PHASE2_TO_PHASE3_CHANGES.md` is tracked and modified in the worktree.
  - Local locator: `local-sha256:0d30b28c54c818173f40e817480682d62c67b267bfbf018d6dd9233ee311a4e4:docs/PHASE2_TO_PHASE3_CHANGES.md:L1-L709`
  - Diff stat observed: `49` insertions and `3` deletions.
  - Dirty-added confirmatory-result region begins at line `668` with `### 19.4 Confirmatory run results (run 27621106006, n = 10 replicas, 8 probes)`.
  - Stage 4 did not analyze or verify the numeric result claims in this dirty region.

## Normal Untracked Top-Level Paths

- `.github/prompts/`
- `.node-red-lab1/`
- `.node-red-lab2/`
- `.node-red-lab2_f1dead/`
- `.node-red-lab2_slow/`
- `.node-red-lab3/`
- `.node-red-lab3_slow/`
- `THESIS_PIVOT_MASTER.md`
- `analysis/custom9_rediagnose.py`
- `analysis/demo_decision_explainer.py`
- `analysis/out_full/`
- `analysis/out_kg_only/`
- `benchmark/results_full_seed1/`
- `dashboard/public/demo-traces/custom9-ql-true-demo.jsonl`
- `docs/DEMO_GUIDE.md`
- `docs/custom9_rediagnosis.md`
- `docs/demo_walkthrough_custom9.md`
- `docs/paper_results_section.md`
- `docs/phase1_results_n10.md`
- `docs/phase1_xzone_ablation_analysis.md`
- `docs/phase1_xzone_asis_analysis.md`
- `docs/phase1_xzone_bumped_analysis.md`
- `docs/phase1_xzone_replication_s11_20_analysis.md`
- `docs/simple_labs_design.md`
- `docs/thesis_meeting_2026-06-08 - Copy.md`
- `docs/thesis_meeting_2026-06-08.md`
- `paper_notes/`
- `phase1_xzone_ablation/`
- `phase1_xzone_asis/`
- `phase1_xzone_bumped/`
- `phase1_xzone_bumped_s11_20/`
- `phase2_results/`
- `phase2_results_v2/`
- `phase2_results_v3/`
- `phase2_results_v4/`
- `phase2_results_v5/`
- `phase3_download/`
- `phase3_download_n10/`
- `tmp_sweep18_results/`
- `tmp_sweep_n10_results/`

## Git Provenance Refs Inspected

- [DIRECT] `git log --all --decorate -n 80 --pretty=format:"%H%x09%D%x09%s"` included:
  - `0372ecd5864fa6555ebfce7d05e05d9aaab96994` as `origin/results`, message `Phase 3 dynamics results: run 27621106006 (20260616-133306)`.
  - `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` as `HEAD -> phase3-process-dynamics`, message `ci(phase3): default replicas 1..10 to clear Wilcoxon floor; document confirmatory sweep`.
  - `3bb5289c36cb3093228ec0609fe57ec676b1ee53` as `origin/main, origin/HEAD`, message `Merge pull request #2 from esra-dev/phase3-process-dynamics`.
  - `22a448be5d9829751badd341904e36ed582f091f`, message `Phase 2 recovery results: run 27547019772 (20260615-183138)`.
- [DIRECT] `git show --stat --oneline --decorate --no-renames eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` reported `2 files changed, 668 insertions(+), 2 deletions(-)`.
- [DIRECT] `git show --stat --oneline --decorate --no-renames 3bb5289c36cb3093228ec0609fe57ec676b1ee53` reported `45 files changed, 11223 insertions(+), 30 deletions(-)`.
- [DIRECT] `git show --stat --oneline --decorate --no-renames 0372ecd5864fa6555ebfce7d05e05d9aaab96994` reported `123 files changed, 2639 insertions(+)`.

## Stage 4 Boundary

- [DIRECT] No branch switch, reset, clean, delete, or artifact overwrite was performed.
- [DIRECT] Stage 4 performed inventory and provenance updates only.
- [UNRESOLVED] Root-level Phase 3 runtime files were hashable but not tied to an exact command, run, or artifact digest in this pass.
- [UNRESOLVED] Local extracted/downloaded Phase 2 v5 and Phase 3 directories are not byte-verified against artifact ZIP digests in this pass.
