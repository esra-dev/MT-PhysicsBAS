# Phase-2 protocol-v2 archive — run 30001857104 (dispatch A1 round 3, seeds 1-10)

- **Workflow:** `.github/workflows/phase2.yml`, GitHub Actions run `30001857104`
  (completed success, 2026-07-23/24), head `19f4f3ff`, branch
  `phase234-correction-2026-07-22`.
- **Registration:** `docs/phase2_correction_registration_2026-07-22.md`
  (commit `7a6b5a71`, contained in the dispatch head). Dispatch record incl.
  the two documented pre-data failure rounds:
  `docs/phase2_v2_dispatch_record_2026-07-22.md`.
- **Inputs:** `adapt_profiles=A group` (Group A (12 profiles): lab1_f1dead, lab2_f1dead, lab2_f1inv, lab2_f2dead, lab2_f2inv, lab2_f1bdead, lab2_f1binv, labmon_f1dead, labmon_infoonly_f1dead, labmon_nostereo_f1dead, labmon2_f2dead_lowsun, labmon2_infoonly_f2dead_lowsun),
  `seeds=1-10`, `run_mode=phase1_v2_kg_only`, `adapt_episodes=0`,
  `publish_results=true` (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase2-consolidated`, id `8572943960`, `sha256:0391dcdc7f35a1e2f7589797a789ec0011bedd5e970327ddcbff7122658b4639`.
- **Publish:** results branch only — the Phase-2 workflow creates no results
  tag (long-standing publish mechanism, disclosed); the immutable provenance
  anchors are the run ID and artifact digest above.
- **Contents:** `recovery_root/seed*/` (per-cell ADAPT_OK gate manifests —
  protocol `phase2-v2`, detector `fault-detector-v2`, settled starts, zero
  fallbacks, paired-arm schedule identity, parent-qtable hashes — plus
  recovery CSVs with the full BlacklistEvents record and per-episode adapt
  metrics), `_artifacts/clean/` (parent protocol `phase1-v2` TRAINING_OK
  provenance + Q-tables), `analysis/out/` aggregates + `workflow_inputs.json`.
- **Gates:** `python analysis/validate_phase2_v2_archive.py <this dir>
  --profiles <group> --seeds 1-10` passes.
- **Inventory:** `SHA256SUMS.csv` (2603 files).
