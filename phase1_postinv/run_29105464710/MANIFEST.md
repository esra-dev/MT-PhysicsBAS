# Phase 1 — post-inversion run of record ⚠️ arm D (NOT the arm-C headline configuration)

**Run ID:** `29105464710`
**Workflow:** `.github/workflows/phase1.yml` ("Phase 1 (KG acceleration, clean labs)")
**Branch:** `kg-crosszone-coupling-mid`
**Head SHA:** workflow-recorded `df53b714e7f546616876b845b71ba889d06ce02a` (pre-rebase
history); **tree-identical** to `8c386f8c3d78d21c014fa3b97778035ad7933dc4` in the
current history — the commit cited by `THESIS_STATE_REPORT.md`.
**Dispatched / completed:** 2026-07-10 15:55:11Z → 16:32:39Z
**Conclusion:** success — 152 / 152 jobs green
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29105464710

## ⚠️ Arm caveat (read before citing)

This run was dispatched with the workflow defaults of the day
(`profiles=lab1,lab2,lab3`, `seeds=1..10`, `run_mode=phase1`). The `phase1`
run_config profile carries **no `learning_overrides`** and therefore inherits the
global learning block (`reward_shaping=pbrs`, `adaptive_trust=true`) — i.e. this is
**factorial arm D (KG prior + PBRS + adaptive trust)**, whereas the pre-inversion
Phase-1 headline (run `27336756264`) is **arm C** (`phase1_kg_only`: KG prior only).
It is therefore **not a like-for-like replacement** for the §5.2 headline table; a
post-inversion **arm-C re-run is still outstanding**
(`gh workflow run phase1.yml -f run_mode=phase1_kg_only` — see
`THESIS_STATE_REPORT.md`, Addendum 2026-07-13). The workflow's default `run_mode`
has since been changed to `phase1_kg_only` to close this footgun.

## Provenance of the archived files

- Source artifact: **`phase1-consolidated`** (artifact id `8233495956`,
  6,457,921 bytes,
  `sha256:6cf00d318aa1544b11f344d4f77d32fb99819f6afd337e0bd0e4f18457fa1c70`,
  GitHub expiry 2026-10-08). Downloaded and extracted 2026-07-18.
- Also published to the **`results` branch**
  (tag `results-20260710-163230-phase1-df53b71`, append mode).

This directory keeps the **citable statistical outputs plus the per-seed
primary-outcome files** (same curation rule as `phase4_postinv/`):

```
analysis/out/                       registered result CSVs/TeX + learning-curve PNGs
benchmark/results_seed<n>/<lab>/<mode>/
    benchmark_results_<mode>.csv    per-run benchmark outcome rows (feed paired_tests)
    first_goal_stereotypes_*.csv    first-goal episode per training cell
    coverage_stereotypes_*.csv      state-coverage per training cell
    iv_stats_stereotypes_*.json     learned IV-gate statistics per arm
    learned_stereotypes_*.ttl       learned stereotype overlays per arm
```

**Pruned before commit** (reproduction internals, preserved in the CI artifact and
on the `results` branch, not needed to verify any cited number):
`qtable_*` (final Q-tables + trust/visits), `trace_bench_*.jsonl` (step traces),
`bench_step_log_*.csv`, `metrics_stereotypes_*.csv` (per-episode training metrics
behind the learning-curve PNGs).

**Headline files (all `ql_true − ql_false`, seed-paired, BH-FDR within family):**

| File | Content |
|---|---|
| `analysis/out/learning_speed_tests.csv` | `auc_goal` (primary), `auc_reward`, `mean_first_goal` — lab2 anchor `auc_goal` Δ=+0.01924, q=0, δ=1.0 |
| `analysis/out/paired_tests.csv` | benchmark efficiency deltas (goal_rate, steps, wasted, redundant, cycling, energy, dev) |
| `analysis/out/summary_table_ci.csv` | per-(profile, arm) benchmark means ± 95% CI |
| `analysis/out/first_goal_wilcoxon.csv` | first-goal Wilcoxon detail |

## Standing of this run

Interpreted in `THESIS_STATE_REPORT.md` Addendum 2026-07-13: the **lab2 anchor
replicates** post-inversion, lab3 `auc_reward` replicates, the lab3 first-goal
regression does **not** (q = 0.632, ns), and the lab3 efficiency penalty migrates to
`avg_cycling`/`avg_redundant` — all under the arm-D caveat above. Do **not** swap
these numbers into the §5.2 (arm-C) table.
