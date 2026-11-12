# Phase-1b extended-arm re-execution dispatch record (2026-11-11)

Registration: `docs/phase1b_extended_rerun_registration_2026-11-11.md`
(BINDING, commit `0f93d4eb`; implementation freeze `86ab4cdd`). Dispatch head
`77e7791f` on branch `round3-rerun-2026-11` — a descendant of the registration
commit whose additional changes are archive tooling, CI configuration, and
mechanical claim-ledger rebuilds only (registration §5 allows
documentation/archive-tooling descendants). CI run `43099282399` was green on
the dispatch head.

## Dispatches (workflow `.github/workflows/phase1.yml`, ref `round3-rerun-2026-11`)

Inputs common to both: `run_mode=phase1b_v2_extended`,
`phase1b_stage=confirmatory`,
`profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
`publish_results=true`.

| Half | seeds | GitHub Actions run | dispatched |
|---|---|---|---|
| E1 | 1–10 | `43099281565` | 2026-11-11 20:59:57Z |
| E2 | 11–20 | `43099286057` | 2026-11-11 20:59:59Z |

## Amendment 2026-11-12 — one pre-data infrastructure failure per half; failed jobs re-run

Attempt 1 of both halves ended with exactly one failed job each, both in the
Gradle dependency warm-up step that precedes any training or benchmarking
(three attempts to resolve `org.apache.httpcomponents.client5:httpclient5:5.5.1`
from Maven Central failed; `validateTurtle` never ran). No data was produced by
either failed cell, so no data-bearing cell is replaced:

| Half | failed job (attempt 1) | consequence |
|---|---|---|
| E1 | `bench labrel16 mode=rule_based seed=4` | 350 other jobs green (all 140 training cells, 209 benchmark cells); aggregate skipped |
| E2 | `train labrel0 stereo=true seed=12` | 140 other jobs green (139 training cells); the dependent benchmark matrix and aggregate skipped |

Remedy: `gh run rerun --failed` on both runs (2026-11-12, ≈09:40 UTC), which
re-executes only the failed job and the jobs that were skipped because of it
(attempt 2 under the SAME run IDs; attempt-1 cells and their artifacts are
untouched). The benchmark cell of E1 is not an input of M2/M4/M5 (training
`auc_goal` and the labband `ql_true` benchmark deviation); the E2 training cell
is an M2 input and had produced no data. Outcome of attempt 2 is appended
below when both aggregates complete.
