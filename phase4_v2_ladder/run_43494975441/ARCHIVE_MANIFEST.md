# Phase-4 knowledge-ladder archive — run 43494975441 (A1, redundancy rule only; seeds 11–20)

- **Status:** control arm of the registered Phase-4 knowledge ladder; data of record for
  the families in `../analysis/registered/phase4_v2_knowledge_ladder_family.csv`.
- **Registration:** `docs/_audit/THESIS_STATE_REPORT.md`, Addendum 2026-11-13b, committed in
  `ee656178` before the dispatch. The dispatch head is that same commit, so the
  registration, the run profile, and the frozen analysis script are contained in the
  dispatched tree.
- **Workflow:** `.github/workflows/phase4.yml`, `workflow_dispatch`, GitHub Actions run
  `43494975441`; created `2026-11-13T19:44:09Z`, completed `2026-11-13T22:16:51Z`; 152 of 152 jobs concluded
  `success` (60 training, 90 benchmark, compile, aggregate). No job was re-run.
- **Source commit and ref:** `ee656178dc3528d56b69a7123c1a37ed43919936`,
  `refs/heads/phase4-knowledge-ladder-2026-11`.
- **Inputs:** `profiles=lab4,lab4dual,lab4chain`, `seeds=11..20`, `run_mode=phase4_v2_redundancy_only`,
  `publish_results=true` (`analysis/out/workflow_inputs.json`; its `workflow` field is
  written as `phase1.yml` by the shared aggregate step in every Phase-4 run, including the
  archived full-KG campaign).
- **Source artifact:** `phase4-consolidated`, id `14082430413`, 15,484,622 bytes,
  `sha256:d162ccb1e2446cec1eb7e841348047008ddd853d51039d03b7c2dd24aa216f10`; retained by GitHub until 2027-02-11. The ZIP downloaded on 2026-11-13
  reproduces this digest, and every extracted file equals its ZIP member.
- **Results tag (verified on the remote on 2026-11-13):** `results-20261113-221644-phase4_v2_redundancy_only-ee656178`. The tag marks the source
  commit; the matching commit on the `results` branch is `b28cca9f` and holds
  no data files (this half has no seed 1, and only seed-1 files are published there).
- **Contents:** `benchmark/results_seed<N>/<lab>/` for seeds 11..20 with, per cell, the
  protocol `phase1-v2` TRAINING_OK gate manifest (fixed 3000-episode horizon, zero scenario
  fallbacks, paired-arm schedule identity), per-episode training metrics, first-goal files,
  initial and final Q-tables, and v2-schema benchmark CSVs and step logs for the three bench
  modes; `analysis/out/` aggregate tables and `workflow_inputs.json`.
- **Inventory:** `SHA256SUMS.csv` lists all 2,537 extracted files (248,256,321 bytes).
- **Committed subset:** the gate manifests, the benchmark traces, `analysis/out/`, this
  manifest, the inventory, and `verification/`. The remaining files match ignore patterns
  for generated artifacts, as in the archived full-KG campaign. Rebuilding the registered
  tables therefore needs the extracted artifact; the inventory verifies a restored copy.
- **Gates:** `analysis/validate_phase4_v2_archive.py` passes for seeds 11..20 and the
  3 labs of this dispatch (called through `analysis/reproduce_phase4_v2_ladder.py`,
  which reads the lab list from the workflow inputs).

## `verification/` — treatment delivery and comparability

| File | Content |
|---|---|
| `workflow_jobs.csv` | Identifier, name, conclusion, and timestamps of all 152 jobs. |
| `training_log_knowledge_layer_evidence.csv` | Per training job: number of log lines that report `knowledgeLayer=REDUNDANCY`, number that report any other layer, and the reported learner mode. |
| `gate_invariance_proof.json` | Output of `analysis/phase4_v2_ladder_layer_proof.py` for this run. |
| `cross_run_identity_vs_phase4_v2_corrected.json` | Output of `analysis/phase4_v2_ladder_cross_run_identity.py` against the archived full-KG campaign. |
| `initial_table_difference_vs_full_kg.json` | Second output of the proof script: cell-by-cell comparison of the knowledge-arm initial Q-tables with the archived full-KG ones. |

Findings recorded in those files, in the order of the registered proof of delivery:

1. **Run mode.** All 60 `TRAINING_OK.json` files record `run_mode = phase4_v2_redundancy_only`, status
   `ok`, 3000 fixed episodes, and zero scenario fallbacks.
2. **Log evidence.** Every one of the 60 training jobs, in both stereo arms, prints
   `knowledgeLayer=REDUNDANCY` in each of its 60 progress lines and no other layer.
3. **Gate invariance.** In the knowledge-arm initial Q-tables of lab4, lab4dual, and
   lab4chain, the ON column of every power-gated action has the same value in every pair of
   states that differ only in the state of its upstream switch (0 differing pairs of 2,048
   on lab4 and of 4,096 per gated action on lab4dual and lab4chain). The tables are
   identical across the ten seeds of this run; the check starts from seed 11. In the
   archived full-KG tables half of those pairs differ
   (`../verification/gate_invariance_reference_full_kg.json`).
4. **Comparability.** In every lab and seed of this run the tabula-rasa training cell
   (episode metrics, initial and final Q-table, first-goal rows, coverage) is byte-identical
   to the archived full-KG campaign's cell. The `ql_false` and `rule_based` benchmark results
   differ from the archived ones only in the wall-clock energy diagnostic column, which no
   analysis reads.
5. **Table comparison (additional check, added after the registered proof).** Against the
   archived full-KG tables this arm differs in every ON column (6 of 13 columns on lab4, 7 of
   15 on lab4dual and on lab4chain), as expected for a layer without Rules 3 to 5 and without
   gates. Every OFF column and the no-op column are identical.
