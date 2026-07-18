# Phase 4 — post-inversion confirmatory run of record

**Run ID:** `29193486193`
**Workflow:** `.github/workflows/phase4.yml` ("Phase 4 (Dependencies + Energy)")
**Branch / head SHA:** `kg-crosszone-coupling-mid` / `d336fdf85d73d6c5dc73ad5a4edae0a784171b4a`
**Dispatched / completed:** 2026-07-12 12:55:38Z → 14:39:57Z (1h44m19s)
**Conclusion:** success — **402 / 402 jobs green** (0 failures)
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29193486193

## Registered dispatch inputs (PHASE4_DEPENDENCY_LADDER.md §5, §7)

| Input | Value |
|---|---|
| `profiles` | `lab4,lab4dual,lab4chain,lab5` (the full dependency ladder + energy cell) |
| `seeds` | `1..20` (fixed in advance) |
| `run_mode` | `phase4` (3000 training episodes/seed, KG-arm energy-prior 2.0) |
| `publish_results` | `true` |

Matrix: 4 profiles × 2 arms (stereo true/false) × 20 seeds = 160 train cells;
4 profiles × 3 modes (rule_based, ql_false, ql_true) × 20 seeds = 240 bench cells;
+ setup + aggregate = 402 jobs.

## Provenance of the archived files

- Source artifact: **`phase4-consolidated`** (artifact id `8261160582`,
  49,443,389 bytes, `sha256:7ebc2cd39d3d840fb2f1b3ec4e00e8c59b8dcdfd563499b289ce563005ca475e`).
- Also published to the **`results` branch** as commit `487d2512e`
  (`results-20260712-143949-phase4-d336fdf`, append mode) via
  `scripts/version_artifacts.ps1`.

This directory keeps the **citable statistical outputs** of the run (the full
consolidated tree is ~713 MB uncompressed — 5,120 per-seed benchmark/Q-table CSVs
— and is preserved in the GitHub artifact + the `results` branch, not committed here):

```
analysis/out/         registered result CSVs + learning-curve PNGs + the ladder figure
learned_ttls/         learned_stereotypes_{true,false}_{lab4,lab4dual,lab4chain,lab5}.ttl
iv_stats/             iv_stats_{true,false}_{...}.json  (per-arm learned IV/power-gate stats)
```

**Headline files (all `ql_true − ql_false`, seed-paired, BH-FDR within family):**

| File | Content |
|---|---|
| `analysis/out/paired_tests.csv` | benchmark efficiency deltas — **the dependency-ladder headline** (`avg_redundant`, `avg_steps`, `avg_wasted`, `avg_dev`, `avg_cycling`, `avg_energy`, `goal_rate`) |
| `analysis/out/phase4_energy_paired.csv` | lab5 energy — `energy_compliance`, `mean_steady_power`, `over_budget_rate` |
| `analysis/out/phase4_energy_ci.csv` | per-(profile, mode) energy means ± 95% CI |
| `analysis/out/learning_speed_tests.csv` | `auc_goal` (primary), `auc_reward`, `mean_first_goal` |
| `analysis/out/summary_table_ci.csv` | per-(profile, arm) benchmark means ± 95% CI |
| `analysis/out/p4_ladder_efficiency_deltas.png` | the ladder figure (also in `docs/_audit/figures/`) |

## Supersedure

This run **supersedes `PHASE4.md` §10a** (pre-inversion run `27905392725`) for lab4
and lab5, and is the first (confirmatory) record for lab4dual and lab4chain. No
number from run `27905392725` is mixed into the post-inversion tables. Reproduce
the ladder figure with:

```
python analysis/phase4_ladder_figure.py \
    --paired phase4_postinv/run_29193486193/analysis/out/paired_tests.csv \
    --out docs/_audit/figures
```
