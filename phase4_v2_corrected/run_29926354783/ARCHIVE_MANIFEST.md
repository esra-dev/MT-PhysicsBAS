# Phase-4 protocol-v2 archive — run 29926354783 (dispatch P4-2, seeds 11–20)

- **Workflow:** `.github/workflows/phase4.yml`, GitHub Actions run `29926354783`
  (completed success, 2026-07-22), head `90e53f8b087fc390a7ad51a0187b81c89c21c64e`,
  branch `phase234-correction-2026-07-22`.
- **Registration:** `docs/phase4_correction_registration_2026-07-22.md`
  (commit `03bcc516`, contained in the dispatch head). Dispatch record:
  `docs/phase34_v2_dispatch_record_2026-07-22.md`.
- **Inputs:** `profiles=lab4,lab4dual,lab4chain,lab5`, `seeds=11..20`,
  `run_mode=phase4_v2`, `publish_results=true`
  (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase4-consolidated`, id `8538860328`,
  `sha256:16f9a6131351970db33be73864fc5a14a52713720fbd65566e58792f50a61c67`.
- **Results tag (verified on remote):**
  `results-20260722-173227-phase4_v2-90e53f8b`.
- **Contents:** `benchmark/results_seed{11..20}/<lab>/` — same per-cell
  structure as run 29926341581 (protocol `phase1-v2` TRAINING_OK manifests,
  training metrics, first-goal files, Q-tables, v2 benchmark CSVs + step
  logs); `analysis/out/` aggregate tables + `workflow_inputs.json`.
- **Gates:** `python analysis/validate_phase4_v2_archive.py <this dir>
  --seeds 11-20` passes.
- **Inventory:** `SHA256SUMS.csv` (3,378 files).
