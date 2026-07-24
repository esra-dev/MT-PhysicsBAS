# Phase-4 protocol-v2 archive — run 29926341581 (dispatch P4-1, seeds 1–10)

- **Workflow:** `.github/workflows/phase4.yml`, GitHub Actions run `29926341581`
  (completed success, 2026-07-22), head `90e53f8b087fc390a7ad51a0187b81c89c21c64e`,
  branch `phase234-correction-2026-07-22`.
- **Registration:** `docs/phase4_correction_registration_2026-07-22.md`
  (commit `03bcc516`, contained in the dispatch head). Dispatch record:
  `docs/phase34_v2_dispatch_record_2026-07-22.md`.
- **Inputs:** `profiles=lab4,lab4dual,lab4chain,lab5`, `seeds=1..10`,
  `run_mode=phase4_v2`, `publish_results=true`
  (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase4-consolidated`, id `8538449323`,
  `sha256:c2622624386c002665ca14d9a35d312c14c8f6a548e8dea8f114f129a9a01887`.
- **Results tag (verified on remote):**
  `results-20260722-171743-phase4_v2-90e53f8b`.
- **Contents:** `benchmark/results_seed{1..10}/<lab>/` — per-cell protocol
  `phase1-v2` TRAINING_OK gate manifests (fixed 3000-episode horizon, zero
  scenario fallbacks, paired-arm schedule identity, the frozen
  `policy_energy_weights` string), per-episode training metrics and
  first-goal-presentation files, initial/final Q-tables, and v2-schema
  benchmark CSVs + step logs for all three bench modes; `analysis/out/`
  aggregate tables + `workflow_inputs.json`.
- **Gates:** `python analysis/validate_phase4_v2_archive.py <this dir>
  --seeds 1-10` passes.
- **Inventory:** `SHA256SUMS.csv` (3,442 files).
