# Phase 4 correction registration (2026-07-22)

**Status: binding pre-data registration for the Phase-4 protocol-v2 corrective
campaign.** Committed on branch `phase234-correction-2026-07-22` after the
corrected implementation was frozen and before any corrected Phase-4
experiment was dispatched.

## 1. Defects and previously seen results (full disclosure)

Defects: `docs/PHASE4_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md`. All previously
seen results are sighted and withdrawn: the post-inversion ladder record (run
`29193486193`, n=20 — `avg_redundant` −0.33 / −0.93 / −1.46 for lab4 /
lab4dual / lab4chain, all reported q≈0; lab5 `energy_compliance` +0.096,
`mean_steady_power` −0.431, `over_budget_rate` −0.090, goal-rate parity on
lab4/lab5 with a KG-favourable lift on lab4dual/lab4chain), and the
pre-inversion record (run `27905392725`). Nothing sighted may influence the
corrected sample, which is fixed at seeds 1–20 with no optional extension.

## 2. Frozen implementation

Frozen at this branch head: run-mode `phase4_v2` (`config/run_config.json`) —
protocol `phase1-v2`, benchmark schema `phase1-benchmark-v2`, fixed
3,000-episode horizon, strict by-position scenario scheduling (shared
corrected ql agent), paired RNG, arm-C convention (PBRS off, adaptive trust
off — an instrument change from the withdrawn PBRS+trust-stacked `phase4`
mode, registered here) plus the non-fading lab5 energy prior
(`stereo_energy_prior_weight=2.0`); ordered policy-energy token weights
`ineff:4,eff:1,spotlight:2,plug:0,masterswitch:0,light:1,blind:0`
(`Phase1PolicyEnergy`, forwarded as `phase1.policyEnergyWeights`; the
no-override default is byte-identical to the frozen Phase-1 rule —
regression-tested in `src/test/java/tools/Phase4PolicyEnergyTest.java`).
Scenario/physics validation covers lab4/lab4dual/lab4chain/lab5
(`analysis/validate_phase1_scenarios.py`; all committed Phase-4 scenario
files already match current physics with zero mismatches).

## 3. Frozen estimands, family, and statistics

- **avg_redundant** per (lab, arm, seed) = mean over the seed's benchmark rows
  of `WastedSteps + ActuatorCyclingCount` (v2 schema, 16 scenarios × 5 runs).
- **energy_compliance** per (lab5, arm, seed) = fraction of benchmark rows
  reaching the goal within the per-scenario energy budget, with steady power
  computed deterministically from the final actuator state ×
  `phase4.power_formula` (`analysis/phase4_energy.py::replica_scalars`).
- **Frozen family (m=4):** lab4 `avg_redundant`, lab4dual `avg_redundant`,
  lab4chain `avg_redundant` (negative difference = KG better), lab5
  `energy_compliance` (positive = KG better). Statistics: exact two-sided
  paired sign-flip (n=20), exact sign test, paired rank-biserial,
  10,000-draw bootstrap CI, BH within the family
  (`analysis/phase4_v2_registered_family.py`, using
  `analysis/exact_paired_stats.py`). No p/q may be reported as zero.
  Decision rule per member: supported iff q ≤ 0.05 in the favourable
  direction; adverse iff q ≤ 0.05 in the unfavourable direction; else null.
- **Ladder-growth secondary (outside the BH family, single ordered
  hypothesis):** per-seed d(lab4chain) − d(lab4) under a two-sided exact
  sign-flip test; d(lab4dual) − d(lab4) and d(lab4chain) − d(lab4dual)
  descriptive. The withdrawn record's monotone-growth reading is the sighted
  expectation; the corrected result governs.
- **Registered descriptives (never confirmatory):** goal_rate, avg_steps,
  avg_dev, avg_wasted, avg_cycling, `avg_policy_energy` (with the frozen
  weights), `mean_first_goal_presentations`, auc metrics,
  `mean_steady_power`, `over_budget_rate`, and all legacy wall-clock columns
  (diagnostic only).

## 4. Campaign

Two registered dispatches of `.github/workflows/phase4.yml` at or after this
registration head, identical inputs except seeds:
`profiles=lab4,lab4dual,lab4chain,lab5`, `run_mode=phase4_v2`,
`publish_results=true`; dispatch P4-1 seeds 1–10, dispatch P4-2 seeds 11–20.
Each: 80 training cells + 120 benchmark cells + aggregate. Until both
aggregates complete, only operational status is inspected. A failed cell or
dispatch is preserved and documented; a re-dispatch uses byte-identical
inputs with both run IDs recorded.

## 5. Archives and completion gates

Both runs are archived permanently under `phase4_v2_corrected/run_<run_id>/`
(consolidated artifact: `benchmark/results_seed<N>/`, `analysis/out/`
including `workflow_inputs.json`) with `ARCHIVE_MANIFEST.md` and SHA-256
inventories. Completion requires: both aggregates green; every training cell
carries a passing protocol `phase1-v2` TRAINING_OK (fixed horizon 3000, zero
fallbacks, paired-arm schedule identity, the frozen `policy_energy_weights`
string) validated by `analysis/validate_phase4_v2_archive.py`; every
benchmark row carries `phase1-benchmark-v2`;
`python analysis/reproduce_phase4_v2.py phase4_v2_corrected` rebuilds
`phase4_v2_registered_family.csv` and `phase4_v2_ladder_trend.csv`
byte-equivalently in canonical numeric form from the committed archives
alone; results tags verified on the remote. Corrected results replace the
historical narrative regardless of direction.
