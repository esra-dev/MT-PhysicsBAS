# Phase 1 — **registered Plan B seed extension** (seeds 11–20, `phase1_kg_only`)

**Run ID:** `29692725784`
**Workflow:** `.github/workflows/phase1.yml` ("Phase 1 (KG acceleration, clean labs)")
**Branch:** `kg-crosszone-coupling-mid`
**Head SHA:** `02ed6c1f1677a26b92fe5425b9e446dccbdbba5b` (`02ed6c1`) — this is the
Addendum 2026-07-18c **registration commit itself**, so the dispatch head contains
the registration by construction (pre-registered-at-dispatch).
**Dispatched / completed:** 2026-07-19 15:23:02Z → 15:54:03Z
**Conclusion:** success — 102 / 102 jobs green
**Dispatch inputs:** `run_mode=phase1_kg_only`, `profiles=lab2,lab3`,
`seeds=11,12,…,20`, `publish_results=true` — exactly the registered Plan B
dispatch (Addendum 2026-07-18c §2). lab1 excluded per registration (clean floor
control, fully null under arm C). `run_mode: "phase1_kg_only"` verified in all
40 `TRAINING_OK.json` cells (10 seeds × 2 labs × 2 arms).
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29692725784

## Standing of this run

This is the **single registered seed extension** of the arm-C headline family
(Addendum 2026-07-18c §2, "Plan B"), extending run-of-record `29639767776`
(seeds 1–10, head `e631877`). Per the registration:

- **Registered primary — NOT computed at archive time:** the pooled-20 paired
  bootstrap (seeds 1–10 from `29639767776` merged with seeds 11–20 from this
  run) over the m = 3 confirmatory family, to be recomputed locally with the
  §5.2 instrument and archived as `phase1_postinv/pooled20_reanalysis/` and
  recorded in a reporting addendum. Until then, **no number in this directory
  supersedes any §5.2 citation.**
- **Registered secondary (seeds-11–20-only sign / replication check): all
  three registered cells agree in sign with the seeds-1–10 record** (values
  below from this run's own `analysis/out/`, families m = 8 / m = 28 over
  lab2+lab3 only — descriptive, NOT comparable to §5.2's m = 12/42 families
  nor to the registered pooled m = 3 q-values):

| Registered cell | seeds 1–10 record | seeds 11–20 (this run) | sign |
|---|---|---|---|
| lab2 `auc_goal` (anchor) | +0.01679, q = 0, δ = 1.0 | **+0.02076** [0.01447, 0.02726], q = 0, δ = 1.0 | agrees |
| lab3 `mean_first_goal` (timing tax) | +67.56, q = 0.0104, δ = 0.68 | **+39.04** [9.56, 72.99], q = 0.016, δ = 0.56 | agrees |
| lab3 `avg_cycling` (policy-quality tax) | +0.744, q = 0.0154, δ = 0.79 | **+0.731** [0.344, 1.100], q = 0, δ = 0.76 | agrees |

- All other cells/metrics in this run are **descriptive only** (registration:
  "No other cell, lab, or metric from the new run acquires confirmatory
  status").
- **Single-shot rule:** this was the one registered extension; no further seed
  extension may be dispatched without a fresh registration that first
  discloses this outcome.

## Code identity vs the seeds-1–10 run of record (like-for-like audit)

`git diff e631877..02ed6c1` touches **no run-affecting code** for
`phase1_kg_only` on lab2/lab3:

- `config/run_config.json`: `phase1_kg_only` block **byte-identical**; changes
  are the explicit (value-identical) arm-D overrides on `phase1` and the two
  new E-sweep profiles (`_e750`, `_e3000`).
- Simulator flows: untouched. `run_full_project.ps1`: ValidateSet additions
  only. `phase1.yml`: input description string only.
- `src/resources/building_3_complex.ttl` (lab3 KG): **comment and
  `rdfs:label` text corrections only** — stale "+50 lux / 0.25·Sun" spill
  annotations updated to the actual "+100 lux / 0.30·Sun" physics (which run
  `29639767776` already ran under). Behaviorally inert: the labels sit on the
  reified `ws:conn_*` arcs, and `CROSS_ZONE_FEEDS_QUERY`
  (`StereotypeReasoner.java`) selects only `connSource`/`connTarget`/
  `hasStructuralStereotype` — no query consumes those label strings.
  Disclosed here for the reporting addendum.

## Provenance of the archived files

- Source artifact: **`phase1-consolidated`** (artifact id `8444359131`,
  5,678,938 bytes,
  `sha256:3bf6c4a8c993b22dd5b68bde66374cdda796d90e21d7e927d576807266acf0f5`,
  verified locally against the GitHub-reported digest; GitHub expiry
  2026-10-17). Downloaded and extracted 2026-07-19.
- Published to the **`results` branch** as commit `75b3820` (append mode).
- Results tag **`results-20260719-155358-phase1_kg_only-02ed6c1`** was pushed
  by CI and **verified present on the remote** (`git ls-remote`, points at
  `02ed6c1`). No local repair needed — the 2026-07-18 tag-rejection footgun
  did not recur because the dispatch head was still the branch tip at publish
  time (nothing was pushed to the branch while the run was in flight,
  deliberately).
- **No artifact-root convenience copies** (`qtable_final_*`,
  `metrics_stereotypes_*`, etc.) exist in this artifact: the aggregate job
  stages those from seed 1, which this run does not contain (seeds 11–20).
  Not a defect; the per-seed sources live in the tree below / in the CI
  artifact.

Curation is identical to `phase1_postinv/run_29639767776/`:

```
analysis/out/                       result CSVs/TeX + learning-curve PNGs (lab2, lab3)
benchmark/results_seed<n>/<lab>/<mode>/
    benchmark_results_<mode>.csv    per-run benchmark outcome rows (feed paired_tests)
    first_goal_stereotypes_*.csv    first-goal episode per training cell
    coverage_stereotypes_*.csv      state-coverage per training cell
    iv_stats_stereotypes_*.json     learned IV-gate statistics per arm
    learned_stereotypes_*.ttl       learned stereotype overlays per arm
benchmark/results_seed<n>/<lab>/training_stereo_<arm>/
    TRAINING_OK.json                per-cell run_mode + artifact receipt
    (+ coverage / first_goal / iv_stats / learned per arm)
```

**Pruned before commit** (reproduction internals, preserved in the CI artifact
and on the `results` branch): per-seed `qtable_*`, `trace_bench_*.jsonl`,
`bench_step_log_*.csv`, `metrics_stereotypes_*.csv`.
