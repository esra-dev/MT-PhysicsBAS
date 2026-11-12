# Phase-1b extended-arm re-execution archive — run 43099281565 (dispatch E1, seeds 1-10)

- **Workflow:** `.github/workflows/phase1.yml`, GitHub Actions run `43099281565`
  (conclusion success at attempt 2, 2026-11-12; attempt 1 lost one job to a
  pre-data Maven Central resolution failure — see the dispatch record), head
  `77e7791f`, branch `round3-rerun-2026-11`.
- **Registration:** `docs/phase1b_extended_rerun_registration_2026-11-11.md`
  (commit `0f93d4eb`, contained in the dispatch head; implementation freeze
  `86ab4cdd`). Dispatch record: `docs/phase1b_extended_rerun_dispatch_record_2026-11-11.md`.
- **Inputs:** `run_mode=phase1b_v2_extended`, `phase1b_stage=confirmatory`,
  `profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
  `seeds=1-10`, `publish_results=true` (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase1-consolidated`, id `13927831370`, `sha256:a67a5b993126c542b1c0a9eb9d4683114e16b86a8139bbd0c0eafa70d43c5faa`.
- **Publish:** results-branch commit `78f2cf06`, tag `results-20261112-083254-phase1b_v2_extended-77e7791f` (verified on the remote).
- **Treatment delivery:** every TRAINING_OK.json carries
  `stereo_effective_props` = {`stereo.irrelevantDvPrior` 2.0,
  `stereo.bandMirrorInit` 5.0, `stereo.bandMirrorPrior` 2.0} equal to
  `stereo_requested_props`; the stereo-true initial Q-tables of labrel16 and
  labband differ from the frozen archive (30199257204/30199260042) for every
  seed of this half.
- **Contents:** `analysis/out/` (sweep aggregates, learning curves,
  `workflow_inputs.json`, workflow-side inventory), `benchmark/results_seed<N>/<profile>/`
  (training_stereo_{true,false}/ with TRAINING_OK.json, metrics, first-goal,
  coverage, iv_stats, learned stereotypes and initial/final Q-tables;
  rule_based/ql_false/ql_true benchmark cells). Committed: manifests, analysis
  outputs, benchmark traces, SHA256SUMS.csv and the stereo-true initial
  Q-tables (delivery evidence); other raw CSV/Q-table files are local-only and
  hash-inventoried.
- **Gates:** `python analysis/validate_phase1b_archive.py <this dir> --stage confirmatory
  --require-effective-props --divergence-against <frozen halves>` passes.
- **Inventory:** `SHA256SUMS.csv` (5,480 files).
