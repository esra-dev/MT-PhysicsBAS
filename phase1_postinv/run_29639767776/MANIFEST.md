# Phase 1 — post-inversion **arm-C headline** run of record (`phase1_kg_only`)

**Run ID:** `29639767776`
**Workflow:** `.github/workflows/phase1.yml` ("Phase 1 (KG acceleration, clean labs)")
**Branch:** `kg-crosszone-coupling-mid`
**Head SHA:** `e63187754ae1530f936cc98fff2d56a402ab3599` (`e631877`)
**Dispatched / completed:** 2026-07-18 09:48:01Z → 10:24:29Z
**Conclusion:** success — 152 / 152 jobs green
**Dispatch:** pure workflow defaults after the `c1d8f40` footgun fix
(`run_mode=phase1_kg_only`, `profiles=lab1,lab2,lab3`, `seeds=1..10`,
`publish_results=true`). `run_mode: "phase1_kg_only"` verified in all 60
`TRAINING_OK.json` cells (10 seeds × 3 labs × 2 arms).
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29639767776

## Standing of this run (why it is the headline)

This is the **like-for-like post-inversion re-measurement of the §5.2 arm-C
headline** (factorial arm C: KG prior ON, PBRS OFF, adaptive trust OFF) that
Addendum 2026-07-13 declared outstanding. It **supersedes the pre-inversion
arm-C run `27336756264` as the §5.2 table of record** and discharges the arm-D
confound carried by `phase1_postinv/run_29105464710/` (which stays archived as
the arm-D sensitivity record — never mix the two runs' numbers).

Headline outcomes (all `ql_true − ql_false`, seed-paired, n = 10, BH within
family; interpretation in `THESIS_STATE_REPORT.md` §5.2 + Addendum 2026-07-18b):

- **lab2 `auc_goal` (primary) replicates like-for-like:** Δ = +0.01679
  [0.00959, 0.02606], q = 0, δ = 1.0.
- **lab3 `auc_reward` win replicates:** Δ = +16.62 [13.06, 19.96], q = 0, δ = 1.0.
- **lab3 `mean_first_goal` regression is significant again under arm C:**
  Δ = +67.56 [26.03, 108.95], q = 0.0104, δ = 0.68 (the arm-D "not significant"
  reading was an arm artifact).
- **lab3 benchmark tax under arm C:** `avg_cycling` +0.744 (q = 0.0154, δ = 0.79)
  persists; `avg_redundant` +0.994 (q = 0.211) is **not** supported (arm-D
  stacking).
- **lab1 is a clean floor control again:** `avg_wasted`/`avg_redundant` +0.0175
  (q = 0.369, ns) — the arm-D +0.0225 blemish does not appear under arm C.
- lab2 `mean_first_goal` is +21.29 (q = 0.104, ns) — the pre-inversion
  marginal "KG faster to first goal on lab2" does not survive the inversion
  (disclosed in §5.2).

⚠️ lab3 physics in this run is the current **100 lux / 0.30·Sun** intermediate
bleed (`ad3cb3b`), not the 50/0.25 of pre-inversion run 27336756264; the
matched pre-inversion lab3 comparator is run `28941204656` (§5.3).

## Provenance of the archived files

- Source artifact: **`phase1-consolidated`** (artifact id `8428536694`,
  6,408,834 bytes,
  `sha256:4029c69365f28741554cde915ae1eea5c51f9322199cc37b4ffaaacd6961d29f`,
  GitHub expiry 2026-10-16). Downloaded and extracted 2026-07-18.
- Also published to the **`results` branch** as commit `077541b` (append mode).
  ⚠️ The CI tag push was **remote-rejected** (`refusing to allow a GitHub App
  to create or update workflow .github/workflows/phase1.yml without 'workflows'
  permission` — the head `e631877` was no longer a branch tip at push time, so
  GitHub applied its workflow-file check to the new tag ref; the same step
  succeeded for the two E-sweep runs whose head was the branch tip). The
  intended tag **`results-20260718-102423-phase1_kg_only-e631877`** was created
  from the local account on 2026-07-18 so the tag convention stays unbroken.
  The "Aggregate & publish" job reports success despite the rejected tag push —
  verify tags, not step conclusions.

This directory keeps the **citable statistical outputs plus the per-seed
primary-outcome files** (same curation rule as `phase4_postinv/` and
`phase1_postinv/run_29105464710/`):

```
analysis/out/                       registered result CSVs/TeX + learning-curve PNGs
benchmark/results_seed<n>/<lab>/<mode>/
    benchmark_results_<mode>.csv    per-run benchmark outcome rows (feed paired_tests)
    first_goal_stereotypes_*.csv    first-goal episode per training cell
    coverage_stereotypes_*.csv      state-coverage per training cell
    iv_stats_stereotypes_*.json     learned IV-gate statistics per arm
    learned_stereotypes_*.ttl       learned stereotype overlays per arm
benchmark/results_seed<n>/<lab>/training_stereo_<arm>/
    TRAINING_OK.json                per-cell run_mode + artifact receipt
```

**Pruned before commit** (reproduction internals, preserved in the CI artifact
and on the `results` branch, not needed to verify any cited number): per-seed
`qtable_*`, `trace_bench_*.jsonl`, `bench_step_log_*.csv`,
`metrics_stereotypes_*.csv`. The artifact-root convenience copies
(last-aggregated `qtable_final_*`, `metrics_stereotypes_*`) are kept, matching
the `run_29105464710` archive.

**Headline files:**

| File | Content |
|---|---|
| `analysis/out/learning_speed_tests.csv` | `auc_goal` (primary), `auc_reward`, `mean_first_goal` (m = 12) |
| `analysis/out/paired_tests.csv` | benchmark efficiency deltas (m = 42) |
| `analysis/out/summary_table_ci.csv` | per-(profile, arm) benchmark means ± 95% CI |
| `analysis/out/first_goal_wilcoxon.csv` | first-goal Wilcoxon detail |
| `analysis/out/learning_curve_lab<n>.png` | multi-seed learning-curve bands (copied to `docs/_audit/figures/p1_kgonly_postinv_lab<n>_curves.png`) |
