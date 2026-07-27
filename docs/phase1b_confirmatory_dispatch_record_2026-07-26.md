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

Dispatch head: `c8e14a4b` (registration `e0316f01` + gitignore guard +
this amendment — documentation/archive-tooling only relative to the
registration commit). Dispatched 2026-07-26 ≈10:58–10:59Z in creation order
(mode/seed identity is additionally embedded in each archive's
`workflow_inputs.json`, which is authoritative at validation time):

| Arm (run_mode) | Seeds | Actions run ID |
|---|---|---|
| `phase1b_v2_baseline` | 1–10 | 30199243656 |
| `phase1b_v2_baseline` | 11–20 | 30199247467 |
| `phase1b_v2_redundancy_only` | 1–10 | 30199251189 |
| `phase1b_v2_redundancy_only` | 11–20 | 30199254246 |
| `phase1b_v2_kg_frozen` | 1–10 | 30199257204 |
| `phase1b_v2_kg_frozen` | 11–20 | 30199260042 |
| `phase1b_v2_extended` | 1–10 | 30199263213 |
| `phase1b_v2_extended` | 11–20 | 30199266427 |

Note: same-mode halves share the workflow concurrency group
(`phase1-<run_mode>`, cancel-in-progress false), so each mode's second half
queues until its first half finishes.

## Amendment A2 (2026-07-26) — two post-data job failures, failed-jobs re-run

Round-2 halves 30199243656 (baseline 1–10) and 30199251189 (redundancy 1–10)
completed green. Two halves ended with failed JOBS (training cells all
green in both; no training data affected):

- 30199257204 (kg_frozen 1–10): only the final "Publish to 'results'
  branch" step failed — a non-fast-forward push race against the
  near-simultaneous baseline publish (the known shared-results-branch
  footgun; the consolidated artifact was already uploaded).
- 30199263213 (extended 1–10): one benchmark cell failed —
  `bench labrel4 mode=rule_based seed=2`. rule_based is a contextual
  benchmark mode outside every registered member and ran green across the
  entire pilot; treated as a flaky cell.

Remedy: `gh run rerun --failed` on both runs (same commit, failed jobs
only — the succeeded training/benchmark cells and their artifacts are
reused verbatim). Outcomes recorded below when terminal. Results-branch
copies will be verified on the remote for all eight halves at archive time;
any still-missing snapshot after the re-runs will be appended to the
results branch from the consolidated artifact and noted here.

**A2 outcomes (2026-07-27):**
- 30199257204 (kg_frozen 1–10): rerun attempt 2 failed on a PLATFORM
  cross-attempt artifact-download error ("GetSignedArtifactURL … 404");
  its attempt-1 consolidated artifact is intact and is the archive of
  record (`phase1b_corrected/run_30199257204`, validation green). Its
  missing results-branch snapshot was appended manually as commit
  `ede943b2` on `results` (marker carries an explanatory `note` field and
  is authored by the local user, not the CI bot).
- 30199263213 (extended 1–10): the original cell failure was an
  `npm ECONNRESET` installing Node-RED (environment setup; the benchmark
  never ran); rerun attempt 2 hit the same platform artifact-download
  error; rerun attempt 3 completed green end-to-end and self-published
  (`c062d174` on `results`). Archive of record
  `phase1b_corrected/run_30199263213`, validation green.
- All eight halves therefore have remote-verified `results` snapshots and
  validated archives; no data-bearing cell was ever replaced.

## Post-run gates (registration §6)

Archive under `phase1b_corrected/run_<id>/`; validate with
`analysis/validate_phase1b_archive.py --stage confirmatory`; build the
registered tables with `analysis/phase1b_report.py` (family m=5: M1–M4, M6;
M5 exploratory); byte-reproduce via `analysis/reproduce_phase1b.py`; verify
results-branch copies on the remote; add the additive `check_provenance.py`
phase1b block.
