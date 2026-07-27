# Phase-1b confirmatory campaign — permanent archive manifest

Registration: `docs/phase1b_registration_2026-07-26.md` (BINDING, commit
`e0316f01`); power protocol `docs/PHASE1B_POWER_PROTOCOL.md`; pilot
dispatch record `docs/phase1b_pilot_dispatch_record_2026-07-25.md`;
confirmatory dispatch record (incl. amendments A1/A2)
`docs/phase1b_confirmatory_dispatch_record_2026-07-26.md`. Implementation
freeze `a8d3cb40`; dispatch head `c8e14a4b`; certificate index
`8444d7d798d675c662ff044be171f5b1c473f9e8c12cb5d198391529e81195db` (34/34
PASS).

## Runs of record (eight seed-half runs, amendment A1)

| run dir | mode | seeds |
|---|---|---|
| run_30199243656 | phase1b_v2_baseline | 1–10 |
| run_30199247467 | phase1b_v2_baseline | 11–20 |
| run_30199251189 | phase1b_v2_redundancy_only | 1–10 |
| run_30199254246 | phase1b_v2_redundancy_only | 11–20 |
| run_30199257204 | phase1b_v2_kg_frozen | 1–10 |
| run_30199260042 | phase1b_v2_kg_frozen | 11–20 |
| run_30199263213 | phase1b_v2_extended | 1–10 |
| run_30199266427 | phase1b_v2_extended | 11–20 |

Each run dir carries `analysis/out/workflow_inputs.json`, a curation-time
root `SHA256SUMS.csv` over `analysis/** benchmark/**`, and the raw
per-seed/per-profile training + benchmark artifacts. Gates:
`analysis/validate_phase1b_archive.py --stage confirmatory` (all eight
pass), `analysis/reproduce_phase1b.py phase1b_corrected` (registered tables
byte-equivalent), `analysis/check_provenance.py` phase1b block, and all
eight `results`-branch snapshots verified on the remote (kg_frozen 1–10's
snapshot manually appended per amendment A2, commit `ede943b2` on
`results`).

## Registered tables

`analysis/registered/phase1b_registered_family.csv` (six enumerated members;
confirmatory BH family m=5 — M5 prospectively exploratory) and
`analysis/registered/phase1b_supporting.csv`. Built by
`build_registered.py`; reproduced byte-equivalently by
`analysis/reproduce_phase1b.py`.
