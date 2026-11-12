# Phase-2 low-sun re-execution archive — run 43099277363 (dispatch L1, seeds 1-20)

- **Workflow:** `.github/workflows/phase2.yml`, GitHub Actions run `43099277363`
  (completed success 2026-11-12 07:36Z, 162/162 jobs green), head `77e7791f`,
  branch `round3-rerun-2026-11`.
- **Registration:** `docs/phase2_lowsun_rerun_registration_2026-11-11.md`
  (commit `0f93d4eb`, contained in the dispatch head; implementation freeze
  `86ab4cdd`). Dispatch record:
  `docs/phase2_lowsun_rerun_dispatch_record_2026-11-11.md`.
- **Inputs:** `adapt_profiles=lab3_f2dead_lowsun,labmon2_f2dead_lowsun`,
  `seeds=1-20`, `run_mode=phase1_v2_kg_only`, `adapt_episodes=0`,
  `publish_results=true` (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase2-consolidated`, id `13923954013`,
  `sha256:c62c38d246cc13efac2955ab0ee8f2a3b8606bb96535e023d34a45d43b8b3bf7`
  (25,141,450 bytes).
- **Publish:** results branch snapshot `phase2/43099277363-20261112-073608`
  (commit `a5bfbf03` on `results`), verified on the remote; the Phase-2
  workflow creates no results tag (disclosed long-standing mechanism).
- **Treatment delivery:** both cells started every adaptation episode from the
  pinned schedules `benchmark/train_scenarios_lab3_lowsun.json`
  (`119dc755…`) / `benchmark/train_scenarios_labmon2_lowsun.json`
  (`8e9f5467…`); every ADAPT_OK manifest records `lowsun_pin_delivered=true`,
  `scenario_sunshine_values=[100]` and the committed file hash. All 45 records
  in which a fault was detected entered DEGRADED mode with best-effort rank 2
  (shortfall 1); the 35 never-detected records keep the nominal rank by
  construction (see registration amendment A1).
- **Contents:** `recovery_root/seed*/` (ADAPT_OK gate manifests — protocol
  `phase2-v2`, detector `fault-detector-v2`, settled starts, zero fallbacks,
  paired-arm schedule identity, parent-qtable hashes, treatment-delivery keys —
  plus recovery CSVs with the full `BlacklistEvents` record and per-episode
  adapt metrics; the recovery and metrics CSVs are committed for this campaign
  despite the generic ignore patterns because the archive is small, 5.2 MB),
  `_artifacts/clean/` (parent protocol `phase1-v2` TRAINING_OK provenance +
  Q-tables; Q-tables local-only, hash-inventoried), `analysis/out/` aggregates +
  `workflow_inputs.json`.
- **Gates:** `python analysis/validate_phase2_v2_archive.py <this dir>
  --profiles lab3_f2dead_lowsun,labmon2_f2dead_lowsun --seeds 1-20
  --require-treatment-delivery` passes.
- **Inventory:** `SHA256SUMS.csv` (1,363 files).
