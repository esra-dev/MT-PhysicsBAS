# Phase 3 protocol-affected evidence notice (2026-07-22)

**Status: binding withdrawal notice, committed before the Phase 3 protocol-v2 rerun.**

Phase 3's exposure to the protocol-v1 defect classes is narrower than Phase 1's,
Phase 2's, or Phase 4's, and this notice states both sides precisely.

**Structurally immune (evidence-based, not asserted):** the two headline
metrics — delay-learning accuracy (learned blind delay in simulator ticks
versus the ground-truth `blind_delay_ticks = 12`) and deadline compliance
(met/total over the six time-bounded goals) — are measured on the simulator's
monotone `Tick` counter by an agent that performs no Q-table training and no
scenario-catalogue scheduling (`illuminance_controller_agent_dynamics.asl`;
`readLabStatusTimed`). Defect classes (a) scenario scheduling and (b)
first-goal aggregation have no surface in Phase 3.

**Withdrawn:** every Phase-3 energy figure. The recorded `energy_cost` was a
cumulative wall-clock accumulator read (`readEnergyCost` →
`TotalEnergyCost`), the same defect class (c) that invalidated Phase-1 legacy
energy: its value depends on elapsed real time and accumulation history, not
on the attempt being measured. This affects both the per-actuator "holding
energy" used by the deadline planner's cost ranking and the per-goal
`energy_cost` column of the record. Consequently the planner's tie-breaking
among feasible actuators — and therefore, in principle, the compliance record
itself — sat on a timing-noisy input, which is why runs 27621106006 (n=10,
canonical) and 29166356524 (n=10, post-inversion) are reclassified historical
**in full** rather than metric-by-metric: the corrected campaign yields
exactly one citable run of record for all Phase-3 metrics.

**Corrected instrument (protocol phase3-v2, energy meter `tick-v1`):**
energy is measured as accumulator DELTAS between two single-fetch reads that
also return the tick counter (`readEnergyCostTimed`), giving (i) a
deterministic per-tick holding power (Δenergy/Δticks over the held window)
for the planner's cost ranking and (ii) a deterministic per-attempt
`tick_energy` with its `tick_span`. The withdrawn cumulative read survives
only as the labelled `energy_cost_wallclock_legacy` diagnostic column. Every
cell writes a `DYNAMICS_OK.json` gate manifest.

The corrected campaign is defined by the pre-data registration committed on
this branch after the instrument code and tests are frozen and before
dispatch. Corrected results replace the historical narrative regardless of
direction. Historical files, commits, tags, and run archives remain available
for provenance and are not being rewritten.

**Reading rule:** until a document is rewritten with phase3-v2 results, every
Phase 3 number in it must be read as superseded/protocol-affected unless it is
explicitly a code or configuration constant rather than an empirical result.
