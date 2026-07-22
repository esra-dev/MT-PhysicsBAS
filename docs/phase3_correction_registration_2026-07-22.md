# Phase 3 correction registration (2026-07-22)

**Status: binding pre-data registration for the Phase-3 protocol-v2 corrective
campaign.** Committed on branch `phase234-correction-2026-07-22` after the
corrected instrument was frozen and before any corrected Phase-3 experiment
was dispatched.

## 1. Defects and disclosure

Withdrawn evidence and the corrected instrument are defined in
`docs/PHASE3_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md`. Previously seen results
(all sighted, all withdrawn): run 27621106006 and run 29166356524, each n=10 —
learned blind delay 12.11–12.18 ticks (rel. error 0.94–1.46%) in all four
(profile × arm) cells, lamps/spotlight classified instantaneous everywhere;
KG arm 6/6 deadlines met vs 3/6 for the zero-delay baseline in both profiles;
wall-clock energy figures (withdrawn) of roughly 3.1–3.5 units for the KG arm
on tight goals vs 0 for the baseline.

## 2. Frozen instrument

The corrected instrument (energy meter `tick-v1`) is frozen at this branch
head: `LabEnvironment.readEnergyCostTimed` (energy + tick in one status
fetch); per-tick holding power (Δenergy/Δticks) as the planner's cost input;
per-attempt `tick_energy`/`tick_span` columns; the withdrawn cumulative read
kept only as `energy_cost_wallclock_legacy`; `DYNAMICS_OK.json` gate manifest
per cell; aggregate `analysis/phase3_dynamics.py` summarising
`total_tick_energy` with the legacy sum as a labelled diagnostic. Tests:
`analysis/tests/test_phase3_tick_energy.py`. Everything else — probing,
Welford estimation, KG write-back, goal set, deadlines, replica count — is
unchanged from the withdrawn record's instrument.

## 3. Registered outcomes

- **Confirmatory reproduction (headline):** delay-learning accuracy — the
  slowest actuator's learned mean ticks per (profile × arm) versus the
  ground-truth 12 ticks — and deadline compliance (overall/tight/loose met
  rates per arm). The registered expectation is that the withdrawn headline
  reproduces (≈1% delay error; KG arm meets tight deadlines, zero-delay
  baseline does not). Any deviation is reported and the corrected run
  governs. As in the withdrawn record, the compliance contrast is
  deterministic given learned delays and is reported as a worked
  demonstration with descriptive intervals, not hypothesis tests.
- **Descriptive only (no hypothesis tests, binding):** `total_tick_energy`
  per (profile × arm) with bootstrap intervals; the per-actuator holding
  power table; `total_energy_wallclock_legacy` as a labelled diagnostic. No
  p- or q-value may be attached to any Phase-3 energy quantity.

## 4. Campaign

One dispatch of `.github/workflows/phase3.yml` at or after this registration
head: profiles `lab2_slow,lab3_slow`, modes `ql_true,ql_false`, replicas
1–10 (unchanged from the record; the headline instrument is unchanged and
gains no power from more replicas), `publish_results=true`. 40 dynamics cells
plus aggregate. Until the aggregate completes, only operational status is
inspected. A failed cell is preserved and documented; re-dispatch uses
byte-identical inputs with both run IDs recorded.

## 5. Archive and completion gates

The run is archived permanently under `phase3_v2_corrected/run_<run_id>/`
(consolidated artifact: `dynamics_root/`, `analysis/out/` including
`workflow_inputs.json`) with `ARCHIVE_MANIFEST.md` and a SHA-256 inventory.
Completion requires: aggregate green; every cell carries a passing
DYNAMICS_OK (protocol `phase3-v2`, meter `tick-v1`, correct ground-truth
constants); every time-bounded row is stamped `tick-v1`;
`python analysis/reproduce_phase3_v2.py phase3_v2_corrected` validates the
archive and rebuilds `phase3_delay_accuracy.csv`,
`phase3_compliance_ci.csv`, and `phase3_compliance_paired.csv`
byte-equivalently in canonical numeric form; results tags verified on the
remote. Corrected results replace the historical narrative regardless of
direction.
