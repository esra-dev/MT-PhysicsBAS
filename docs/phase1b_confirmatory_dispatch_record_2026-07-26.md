# Phase-1b CONFIRMATORY dispatch record (2026-07-26)

Registration: `docs/phase1b_registration_2026-07-26.md` (BINDING), added in
commit `e0316f01`. Dispatch head: `71217120` — a descendant of the
registration commit whose only change is a .gitignore guard for the local
pilot artifact trees (documentation/housekeeping only, per registration §2).
Implementation freeze lineage unchanged through `a8d3cb40`.

## Dispatches (workflow `.github/workflows/phase1.yml`, ref `phase1b-labs-2026-07`)

Inputs common to all four:
`profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
`seeds=1,2,...,20` (registered N=20; the workflow gate
`phase1b_stage=confirmatory` rejects pilot seeds 1001–1010 and out-of-range
seeds), `publish_results=true`.

| Arm (run_mode) | Actions run ID |
|---|---|
| `phase1b_v2_baseline` | 30198047162 |
| `phase1b_v2_redundancy_only` | 30198048033 |
| `phase1b_v2_kg_frozen` | 30198048806 |
| `phase1b_v2_extended` | 30198049550 |

Dispatched 2026-07-26 ≈10:19Z; all four accepted and in progress. Each
registered mode is dispatched exactly once; any pre-data dispatch failure
will be amended here in place with byte-identical inputs.

## Amendment A1 (2026-07-26) — round-1 PRE-DATA failure: CI matrix limit

All four round-1 runs (30198047162 / 30198048033 / 30198048806 /
30198049550) failed BEFORE ANY TRAIN JOB EXISTED: the registered train
matrix is 7 profiles × 2 arms × 20 seeds = 280 cells, which exceeds the CI
platform's hard 256-jobs-per-matrix limit, so the train job failed to
materialise (setup succeeded, the train job is absent from every run's job
list, and the dependent benchmark/aggregate jobs were skipped). No
data-bearing cell exists or was replaced.

Remedy (mirrors the established Phase-4 two-seed-halves convention): each
registered mode is re-dispatched as TWO seed-half runs — seeds 1–10 and
seeds 11–20 — with all other inputs identical. The registered campaign is
unchanged: same modes, same profiles, same seed block 1..20, same head
requirements; only the packaging into workflow runs changes.
`analysis/reproduce_phase1b.py` was amended (archive-tooling only, permitted
by registration §2) to accept one or two archives per mode with disjoint
halves whose union must equal the common seed block; more than two archives
per mode, overlapping halves, or colliding staged trees remain fatal
(analysis pytest 93/93).

### Round-2 dispatches (seed halves)

| Arm (run_mode) | Seeds | Actions run ID |
|---|---|---|
| `phase1b_v2_baseline` | 1–10 | (recorded below) |
| `phase1b_v2_baseline` | 11–20 | (recorded below) |
| `phase1b_v2_redundancy_only` | 1–10 | (recorded below) |
| `phase1b_v2_redundancy_only` | 11–20 | (recorded below) |
| `phase1b_v2_kg_frozen` | 1–10 | (recorded below) |
| `phase1b_v2_kg_frozen` | 11–20 | (recorded below) |
| `phase1b_v2_extended` | 1–10 | (recorded below) |
| `phase1b_v2_extended` | 11–20 | (recorded below) |

## Post-run gates (registration §6)

Archive under `phase1b_corrected/run_<id>/`; validate with
`analysis/validate_phase1b_archive.py --stage confirmatory`; build the
registered tables with `analysis/phase1b_report.py` (family m=5: M1–M4, M6;
M5 exploratory); byte-reproduce via `analysis/reproduce_phase1b.py`; verify
results-branch copies on the remote; add the additive `check_provenance.py`
phase1b block.
