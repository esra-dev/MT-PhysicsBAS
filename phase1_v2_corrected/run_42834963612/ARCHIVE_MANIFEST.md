# Corrected Phase 1 archive — run 42834963612

- Status: protocol-v2 knowledge-ladder control arm (A2, Brick structure only); data of record for the registered ladder family.
- Mode: `phase1_v2_brick_only`.
- Registration: `docs/_audit/THESIS_STATE_REPORT.md`, Addendum 2026-11-10, committed in `140906f2` at `2026-11-10T14:29:23Z`. The dispatch head is that same commit, so the registration is contained in the dispatched tree.
- Workflow: `.github/workflows/phase1.yml`, `workflow_dispatch`.
- Created: `2026-11-10T14:31:36Z`; completed successfully: `2026-11-10T19:02:47Z`; 302 of 302 jobs concluded `success` (120 training, 180 benchmark, compile, aggregate).
- Source ref: `refs/heads/phase234-correction-2026-07-22`.
- Source commit: `140906f2b325aefdb32b6c00ffaae063507f215e`.
- GitHub run: <https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/42834963612>.
- Consolidated artifact ID: `13793597268`; reported compressed size: `13,074,614` bytes.
- GitHub artifact digest: `sha256:cacc49e0449b148d0883f0506077ab601c258a20ef3a636ccb386a322262758d`; the downloaded ZIP reproduces this digest.
- Result tag: `results-20261110-190237-phase1_v2_brick_only-140906f2` (present on the remote on 2026-11-13).
- Downloaded permanently on `2026-11-13`; extracted contents: 4,979 files and 107,924,367 bytes before this manifest and the `verification/` directory.
- Artifact integrity: `analysis/out/SHA256SUMS.csv` verifies every file uploaded in the consolidated artifact (4,978 rows, zero errors).
- Protocol gate: `analysis/validate_phase1_v2_archive.py` passed for 20 seeds × 3 labs (120 training cells, 180 benchmark cells, fixed 3,000 episodes, zero scenario fallbacks, zero schedule-pair mismatches).

This directory is the extracted GitHub artifact plus this manifest and `verification/`. The
campaign-level `../SHA256SUMS.csv` inventories all of it.

## `verification/` — treatment delivery and comparability

| File | Content |
|---|---|
| `brick_only/qtable_initial_stereotypes_true_lab{2,3}_zone{1,2}.csv` | Seed-1 per-zone initial Q-tables of this run, taken byte-for-byte from the results-branch commit `1b9892fa` (tag above). |
| `arm_c/qtable_initial_stereotypes_true_lab{2,3}_zone{1,2}.csv` | The same tables of the full-KG run 29848584965, from results-branch commit `f5c372a8` (tag `results-20260721-204832-phase1_v2_kg_only-d344238`). |
| `elementary_layer_off_proof.json` | Output of `analysis/phase1_v2_brick_layer_proof.py`: cell-by-cell comparison of the initial Q-tables of the two arms (per-zone seed 1, and the combined tables of all 20 seeds). |
| `training_log_knowledge_layer_evidence.csv` | Per training job: number of log lines reporting `knowledgeLayer=BRICK`, number reporting any other layer, and the reported learner mode. |
| `workflow_jobs.csv` | Identifier, name, conclusion, and timestamps of all 302 jobs. |
| `cross_run_identity_vs_run_29848584965.json` | Output of `analysis/phase1_v2_cross_run_identity.py`: which files are byte-identical between this run and the full-KG run. |

Findings recorded in those files:

1. **Elementary layer off.** The initial Q-tables of the two arms differ only on the two
   blind-activation columns and only at sun rank 0. In those cells the full-KG arm holds the
   IV-gate well; the Brick arm holds 0 or the Rule-5 bonus (+7.5, +15, +22.5 per zone), plus the
   unchanged cross-zone overshoot term on lab3. In the Brick arm the blind-activation columns
   do not depend on the sun rank at all. The initial tables are identical across all 20 seeds
   within each arm.
2. **Delivery signature restated.** The registration worded the signature as "no −50 cell on
   any blind-ON column at sun rank 0". Read literally, no knowledge arm can satisfy it: Rule 1
   (redundancy, derived from the action registry, active in every knowledge arm) also writes
   −50 per zone when the blind is already open. The proof therefore reports the literal count
   and the criterion restricted to states in which the blind is closed, where −50 can only
   come from the IV gate; the restricted criterion holds in every table. This restatement was
   made after data contact and is a labelled deviation.
3. **Log evidence.** The registration expected the line `knowledge layer = BRICK`. That line
   is written by the reasoner's Java logger, which the job log does not capture. The training
   progress line of the learner reports `knowledgeLayer=BRICK` in all 120 training jobs and no
   other layer in any job.
4. **Comparability with run 29848584965.** In all three labs and all 20 seeds, the
   tabula-rasa training cells (episode metrics, initial and final Q-tables, first-goal rows)
   are byte-identical between the two runs. The `ql_false` and `rule_based` benchmark results
   differ only in the excluded wall-clock energy diagnostic column. On lab1, which has no
   blinds, the knowledge-arm training cells are byte-identical as well.
