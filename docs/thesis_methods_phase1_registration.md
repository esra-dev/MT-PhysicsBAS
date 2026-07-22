# Phase 1 methods — corrected protocol v2 and registration disclosure

**Current thesis-ready methods draft, corrected campaign completed 2026-07-21 and
archived/analyzed 2026-07-22.**

## Research question

Phase 1 tests whether a tabular Q-learning controller that receives structured prior
knowledge learns differently from an otherwise paired controller that receives no such
prior. The test is restricted to three deterministic, clean simulated illuminance-control
laboratories. It is not a claim about real buildings.

## Laboratories

Lab1 contains one zone and one Boolean task light. Lab2 contains two independent zones,
each with a Boolean 400-lux task light and a Boolean blind that admits `0.50*Sunshine`.
Lab3 adds symmetric 100-lux task-light spill, `0.30*Sunshine` blind spill, and one shared
150-lux spotlight. Every zone has 25 lux of fixed ambient light. The exact equations are
implemented in `simulator/simulator_flow_lab{1,2,3}.json:130` and audited line by line in
`docs/audit/phase1_audit_2026-07-19.md`, A2.

Clean-lab physics is deterministic. Sunshine is fixed within a scenario; sensor noise,
occupancy, continuous dimming, actuator lag, and weather trajectories are absent. The
controller observes discretized illuminance ranks with bounds 50/100/300 and sunshine
ranks with bounds 50/200/600. The goal is rank 3 in every zone
(`src/agt/lab_profiles.asl:260-321`).

## Controller and knowledge treatment

The action list is enumerated from the Web of Things contract for both arms. A SPARQL
enrichment query annotates those common actions with affected zones, causal or mediated
mechanism, outdoor-light dependence, minimum independent-variable rank, topology, and
optional energy metadata (`src/env/tools/StereotypeReasoner.java:111-192`). Thus the KG arm
does not receive extra actions.

The Q-learner keeps one Q-table per zone and chooses the action with the greatest sum of
zone values. Its Bellman parameters are `alpha=0.1` and `gamma=0.9`; epsilon begins at 0.3
and is bounded below by 0.01 (`src/env/tools/QLearner.java:53-60,566-611`). Epsilon decay is
0.992/0.996/0.997 in lab1/lab2/lab3 respectively
(`src/agt/lab_profiles.asl:260-321`). This cross-lab asymmetry does not differ between arms
inside a lab but prevents a one-factor causal interpretation of differences between labs.

Per-zone reward is clipped to `[-50,+50]` and rewards rank progress, first target arrival,
and target holding; it penalizes time, regression, losing the target, ineffective action,
and do-nothing away from target. Energy and switching are not in the reward
(`src/env/tools/QLearner.java:2555-2612`).

In arm C, KG-derived initialization and a decaying soft greedy prior are active; PBRS and
adaptive trust are off. The no-KG pair starts with zero Q-values and no prior. In the
redundancy-only control, the treatment label receives only a state/action-derived penalty
for requesting an actuator value it already has. In baseline, the prior and PBRS are off
for both labels. In PBRS-only, both labels receive potential-based reward shaping but no
KG prior. Exact configurations are `phase1_v2_kg_only`,
`phase1_v2_redundancy_only`, `phase1_v2_baseline`, and `phase1_v2_pbrs_only` in
`config/run_config.json:116-174`.

## Training protocol v2

Each mode is run on lab1, lab2, and lab3 with seeds 1-20. Both labels use the same
seed-derived random stream at initialization. Treatment-dependent actions may make later
trajectories diverge. Every lab/label/seed cell completes exactly 3,000 episodes; early
stopping is disabled.

The scheduler cycles through the actual ordered objects in the training-scenario file. It
selects by zero-based file position and returns the object's real ID. A duplicate, missing,
or unknown ID is fatal; random simulator reset is never a fallback
(`src/env/tools/ScenarioCatalog.java:34-90`;
`src/env/tools/LabEnvironment.java:700-719`). After assigning a scenario, the agent waits
250 ms before observing and recording its settled start state
(`src/agt/illuminance_controller_agent_ql.asl:207-232`).

Every training row stores its real scenario ID. `TRAINING_OK.json` stores protocol version,
ordered IDs and SHA-256 hash, fixed horizon, paired-RNG version, benchmark schema, run seed,
and fallback count. The archive validator requires protocol `phase1-v2`, horizon 3,000,
paired RNG `common-seed-v1`, schema `phase1-benchmark-v2`, and fallback count zero
(`analysis/validate_phase1_v2_archive.py`).

## First-success outcome

`mean_first_goal_presentations` is scenario based. For each declared scenario, the file
records total presentations, first successful presentation, censor flag, and analysis
presentation. A successful scenario uses its first successful presentation number; a
never-solved scenario uses total presentations plus one. Terminal-at-start and never-solved
scenarios are retained. The seed metric is the arithmetic mean over every declared
scenario. Corrected analysis rejects legacy state-index files and rejects paired arms with
different scenario rows (`src/env/tools/QLearner.java:1910-2200`;
`analysis/sweep_report.py:1060-1120`).

## Benchmark protocol v2

Benchmarking loads trained Q-tables and does not update them. Every declared scenario is
run five times for each of rule-based, QL-no-KG, and QL-KG, with a 20-step cap. An action is
dispatched, the simulator is allowed to update, and only then is the effect observed and
logged (`src/agt/illuminance_controller_agent_bench.asl:300-405`).

Cycling starts from the scenario's settled actuator state, so the first change counts.
`PolicyEnergyCost` sums instantaneous active-actuator cost once per decision: one unit per
task light, two per spotlight, and zero per blind. The simulator's wall-clock
`TotalEnergyCost` is retained only as `LegacyWallClockTotalEnergyCost` and is not an outcome
(`src/env/tools/BenchmarkLogger.java:132-208`; `src/env/tools/Phase1PolicyEnergy.java`).

## Registered outcomes and statistics

The corrected primary family has exactly five two-sided paired seed-level tests:

1. arm-C lab2 `auc_goal`;
2. redundancy-only lab2 `auc_goal`;
3. arm-C minus redundancy-only lab2 treatment-effect difference;
4. arm-C lab3 `mean_first_goal_presentations`;
5. arm-C lab3 `avg_cycling`.

`auc_goal` is the fraction of all 3,000 training episodes that reached goal. Corrected
first-goal is defined above. `avg_cycling` is the mean reversal count across benchmark
rows. Lab1, baseline, PBRS-only, deterministic policy energy, deviation, goal rate, and all
other metrics are registered controls/descriptives, not additional discoveries.

For `n<=20`, the null test enumerates every sign assignment of the nonzero paired
differences and reports an exact two-sided sign-flip p-value. If more than 20 nonzero pairs
were ever analyzed, one million random sign flips with a plus-one correction would be used.
The analysis also reports an exact sign test, mean and median paired differences, paired
rank-biserial effect size, and a 10,000-draw paired-bootstrap 95% confidence interval.
Bootstrap is estimation only. Cliff's delta is labelled unpaired descriptive context.
Benjamini-Hochberg adjustment is applied once across the five sign-flip p-values. No p- or
q-value is printed as zero (`analysis/sweep_report.py:413-610`;
`analysis/phase1_v2_registered_family.py`).

The descriptive redundancy reproduction fraction is the redundancy mean effect divided by
the arm-C mean effect. Less than one third is “little,” one third through two thirds is
“partial,” and more than two thirds is “most.” Zero denominators are undefined and
opposite signs are reported as a conflict, not as reproduction.

## Execution and archiving

One GitHub Actions workflow run contains 120 training jobs and 180 benchmark jobs plus
setup and aggregation. Four mode-specific workflow runs completed successfully from commit
`d344238`, with each matrix limited to ten parallel jobs. Every raw input, result,
provenance file, artifact hash, and complete SHA-256 inventory is permanently committed
under `phase1_v2_corrected/`. `analysis/reproduce_phase1_v2.py` rebuilds all corrected
numeric CSV output from those committed archives, canonicalizes numeric cells to 12
significant digits to remove platform-only floating-representation noise, and requires
byte equality of the canonical outputs.

## Registration chronology and required disclosure

The June 2026 Phase 1 registration was pushed approximately 8.6 days after the first
relevant dispatch and cited completed analyses. June results therefore never had genuine
prospective registration. July protocol-v1 runs were registered before dispatch, but a
prospective timestamp could not rescue the later-discovered scheduler, first-goal, and
wall-clock-energy defects.

All protocol-v1 empirical results, including pooled-20, redundancy, baseline, PBRS, and
noise-pilot outcomes, are historical protocol-affected findings. The binding withdrawal is
`docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`.

Protocol v2 disclosed all previously seen results and froze the design before data in
`docs/phase1_correction_registration_2026-07-21.md` (commit `87ae528`). The queue addendum
`docs/phase1_correction_registration_2026-07-21a.md` was committed as `d344238` before any
corrected campaign dispatch. The four workflow run IDs are `29848584965`, `29848587274`,
`29848589682`, and `29848592010`, all on `d344238`. Corrected outcomes replace the old
narrative regardless of direction.

After artifact download, the registered-family reader initially stopped before producing
a statistic because seed-directory names were lexicographically rather than numerically
ordered. A tested integer-sort correction left the seed set and every registered formula
unchanged. Full reproduction then exposed only Linux/Windows last-bit float serialization
differences, leading to the canonical 12-significant-digit comparison described above.
Both post-data execution corrections are disclosed in
`docs/phase1_correction_analysis_deviation_2026-07-22.md`; original artifacts and their
GitHub SHA-256 inventories were not modified.

The corrected numerical results and interpretation are reported separately in
`docs/phase1_results_v2.md` so that this document remains a methods and registration record.
