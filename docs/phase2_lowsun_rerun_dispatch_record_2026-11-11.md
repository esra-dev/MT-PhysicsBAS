# Phase 2 low-sun re-execution dispatch record (2026-11-11)

Registration: `docs/phase2_lowsun_rerun_registration_2026-11-11.md` (BINDING,
commit `0f93d4eb`; implementation freeze `86ab4cdd`). Dispatch head
`77e7791f` on branch `round3-rerun-2026-11` — a descendant of the registration
commit whose additional changes are archive tooling (curation scripts), CI
configuration (full-history checkout, matplotlib for an existing test), and
mechanical claim-ledger rebuilds; no change to implementation, physics,
scenarios, metrics, or learner hyperparameters. CI run `43099282399` was green
on the dispatch head.

## Dispatch (workflow `.github/workflows/phase2.yml`, ref `round3-rerun-2026-11`)

| Dispatch | GitHub Actions run | adapt_profiles | seeds | other inputs |
|---|---|---|---|---|
| L1 | `43099277363` | lab3_f2dead_lowsun, labmon2_f2dead_lowsun | 1–20 | run_mode=phase1_v2_kg_only, adapt_episodes=0, publish_results=true |

Dispatched 2026-11-11 20:59:55Z; completed 2026-11-12 07:36Z with every job
green (162/162: setup, 80 clean-training cells, 80 adaptation cells,
aggregate). No cell failed, so no re-dispatch was needed and no data-bearing
cell was replaced. Results-branch snapshot `phase2/43099277363-20261112-073608`
(commit `a5bfbf03` on `results`) verified on the remote. The Phase-2 workflow
creates no results tag (long-standing publish mechanism, disclosed in the
2026-07 record); the immutable provenance anchors are the run ID and the
consolidated artifact (`phase2-consolidated`, id `13923954013`,
`sha256:c62c38d246cc13efac2955ab0ee8f2a3b8606bb96535e023d34a45d43b8b3bf7`).

## Curation

`scripts/curate_phase2_lowsun_v3.ps1 -RunIds 43099277363` downloaded the
artifact into `phase2_v3_lowsun/run_43099277363/`, wrote the 1,363-file
`SHA256SUMS.csv`, and passed
`analysis/validate_phase2_v2_archive.py --require-treatment-delivery`
(20 seeds × 2 profiles × 2 arms; every low-sun cell carries
`lowsun_pin_delivered = true`, `scenario_sunshine_values = [100]` and the
committed scenario-file hashes). The registered tables were then built with
`analysis/phase2_lowsun_v3_family.py` into
`phase2_v3_lowsun/analysis/registered/` and are reproduced by
`python analysis/reproduce_phase2_lowsun_v3.py phase2_v3_lowsun`.

## Delivery check and registered outcome pointer

Delivery evidence: preflight passed for both profiles; 80/80 ADAPT_OK manifests
carry `lowsun_pin_delivered=true`, `scenario_sunshine_values=[100]` and the
committed pinned-file hashes; all 45 detected records entered DEGRADED mode at
best-effort rank 2. The §5 voiding signature fired on the 35 never-detected
records for an instrument reason (the best-effort rank is only lowered after a
blacklist); see registration amendment A1 (post-data, disclosed). Registered
tables: `phase2_v3_lowsun/analysis/registered/`; campaign summary:
`phase2_v3_lowsun/CAMPAIGN_MANIFEST.md`.
