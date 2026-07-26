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

## Post-run gates (registration §6)

Archive under `phase1b_corrected/run_<id>/`; validate with
`analysis/validate_phase1b_archive.py --stage confirmatory`; build the
registered tables with `analysis/phase1b_report.py` (family m=5: M1–M4, M6;
M5 exploratory); byte-reproduce via `analysis/reproduce_phase1b.py`; verify
results-branch copies on the remote; add the additive `check_provenance.py`
phase1b block.
