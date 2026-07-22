# Phase 1 — Complete Critical Audit, corrected through 2026-07-22

[VERIFIED] **Validity-changing finding.** The protocol-v1 `mean_first_goal` result of
`+53.30` episodes, every legacy energy result, and all pooled-20 headline/control
conclusions are historical protocol-affected findings, not thesis-final evidence. The
training scheduler silently substituted unseeded random resets for missing scenario IDs;
the first-goal aggregation compared different, selected state sets; and energy depended on
wall-clock duration. Evidence: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`, items
1-5; protocol-v1 archives from runs `29639767776` and `29692725784` under
`phase1_postinv/historical_raw/`.

[VERIFIED] Protocol v2 fixes those defects and was registered before corrected campaign
dispatch. All four runs completed successfully on `d344238`: arm C `29848584965`,
redundancy-only `29848587274`, baseline `29848589682`, and PBRS-only `29848592010`.
Every archive/protocol gate passes. Evidence: the two correction registrations and
`phase1_v2_corrected/analysis/phase1_v2_protocol_gate_summary.json`.

[VERIFIED] The corrected headline is narrower. Arm C has a small favorable lab2
`auc_goal` difference of `+0.003700`; redundancy-only reproduces 69.8% of that mean, while
arm C retains a smaller `+0.001117` advantage beyond redundancy. Lab3 first-goal
presentations (`+0.110`) and cycling (`+0.07375`) are null. Evidence:
`phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv` and
`phase1_v2_decomposition.json`.

[VERIFIED] Two post-download execution problems were corrected transparently: seed paths
needed numeric sorting, and cross-platform last-bit float text needed a canonical
12-significant-digit comparison. Neither correction changed data selection or a registered
formula. Evidence: `docs/phase1_correction_analysis_deviation_2026-07-22.md` and passing
`analysis/reproduce_phase1_v2.py`.

## Reading rules and definitions

[VERIFIED] A knowledge graph (KG) is a set of machine-readable statements connecting
things and concepts. SPARQL is the query language used to retrieve those statements.
Q-learning is a reinforcement-learning algorithm that estimates the long-run value of
taking each action in each observed state. JaCaMo is the multi-agent platform; Jason is its
agent language; CArtAgO exposes Java objects as agent artifacts; Node-RED runs the simulated
laboratories. Evidence: `build.gradle:44-66`, `src/agt/illuminance_controller_agent_ql.asl`,
and `src/env/tools/QLearner.java:46-67`.

[VERIFIED] `[VERIFIED]` means I checked code, committed data, or immutable run metadata.
`[STATED]` means a project document asserts the point but independent checking was not
possible. `[INFERRED]` is a reasoned interpretation that could be wrong. Source: this
audit, “Reading rules and definitions.”

# PART A — WHAT EXISTS

## A1. What Phase 1 built

[VERIFIED] The earlier project used `custom2`-through-`custom9` weakness laboratories,
potential-based reward shaping (PBRS), and adaptive trust. After a null Sweep-18 result,
the project pivoted to a clean three-lab ladder. Evidence: `docs/pre_registration.md`,
sections 6.7 and 7; git history retained before `f9f41df`.

[VERIFIED] The clean Phase 1 system contains three Node-RED simulators, three self-contained
Turtle knowledge graphs, a training agent, a benchmark agent, a Java Q-learner, a SPARQL
reasoner, a simulator bridge, a benchmark logger, run configurations, analysis programs,
and GitHub Actions workflows. Evidence: `simulator/simulator_flow_lab{1,2,3}.json`;
`src/resources/building_{1_trivial,2_intermediate,3_complex}.ttl`;
`src/agt/illuminance_controller_agent_{ql,bench}.asl`; `src/env/tools/{QLearner,
StereotypeReasoner,LabEnvironment,BenchmarkLogger}.java`; `config/run_config.json`;
`analysis/sweep_report.py`; `.github/workflows/phase1.yml`.

[VERIFIED] Each clean lab loads only its own self-contained ontology file. This prevents
devices or rules in the older global ontology from entering the action registry. Evidence:
`src/agt/lab_profiles.asl:245-248,260-321`.

[VERIFIED] The 2026-07-10 action-space inversion made the Web of Things (WoT) contract the
only source of actions. SPARQL knowledge now annotates the common action list rather than
creating extra actions for the treatment arm. Evidence:
`src/env/tools/StereotypeReasoner.java:161-192` and `docs/ACTION_SPACE_INVERSION.md`.

[VERIFIED] Phase 1 contains clean, fault-free illuminance control. Fault recovery is Phase
2, response delay is Phase 3, and the energy/dependency ladder is Phase 4. Evidence:
`src/agt/lab_profiles.asl:245-330` and `docs/_audit/THESIS_STATE_REPORT.md`, sections 4-8.

## A2. Laboratories and exact physics

### A2.1 Shared update rules

[VERIFIED] All three clean simulators update every 50 ms. Illuminance is a deterministic,
instantaneous, additive function of Boolean actuator state and a fixed `Sunshine` value.
There is no clean-lab sensor noise, thermal lag, actuator ramp, lamp ageing, occupancy, or
time-dependent daylight trajectory. Evidence: `config/run_config.json:116-174` (`tick`);
the `update_env` functions at `simulator/simulator_flow_lab{1,2,3}.json:130`.

[VERIFIED] The simulator still contains a random-reset endpoint, but protocol v2 never uses
it as a missing-scenario fallback. Every training episode selects an actual scenario by
zero-based file position, waits 250 ms, and then observes the settled state. Evidence:
`src/env/tools/LabEnvironment.java:700-719`; `src/agt/illuminance_controller_agent_ql.asl:207-232`;
`src/env/tools/ScenarioCatalog.java:34-90`.

[VERIFIED] Scenario sunshine is fixed for the episode. The clean flows also implement a
random reset that samples `{0,100,400,900}`, but that endpoint is legacy/diagnostic under
the v2 schedule. Evidence: each flow's reset function at
`simulator/simulator_flow_lab{1,2,3}.json:155`; v2 training plan at
`src/agt/illuminance_controller_agent_ql.asl:207-232`.

### A2.2 Lab1: one independent lamp

[VERIFIED] Lab1 has one zone, one task light, one illuminance sensor, and no blind,
spotlight, or cross-zone connection. Its state has four illuminance ranks times two lamp
states, or eight discrete states. Evidence: `src/agt/lab_profiles.asl:251-272` and
`src/resources/building_1_trivial.ttl`.

```javascript
var z1light = flow.get('Z1Light') || false;
var z1 = 25
       + (z1light ? 400 : 0);
flow.set('Z1Level', z1);
var energy = (flow.get('TotalEnergyCost') || 0)
           + (z1light ? 1 : 0);
flow.set('TotalEnergyCost', energy);
flow.set('EnergyCost', z1light ? 1 : 0);
var hr = (flow.get('Hour') || 0) + 0.1;
if (hr >= 24) hr = 0;
flow.set('Hour', hr);
return null;
```

| Code line | Plain-language meaning |
|---|---|
| [VERIFIED] `var z1light ...` | Read the lamp switch; treat a missing value as off. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `var z1 = 25` | Start every calculation at 25 lux of fixed ambient light. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `+ (z1light ? 400 : 0)` | Add 400 lux when the lamp is on, otherwise add zero. The only possible settled levels are therefore 25 and 425 lux. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `flow.set('Z1Level', z1)` | Replace the sensor level with that exact value on every tick. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `var energy ...` | Add one legacy energy unit per tick while the lamp is on. This wall-clock accumulator is not used as corrected energy evidence. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `EnergyCost` assignment | Publish the instantaneous cost: one if on, zero if off. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `Hour` lines | Advance an informational counter by 0.1 and wrap at 24; it does not affect illuminance. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |
| [VERIFIED] `return null` | Stop the Node-RED message after updating shared flow state. Source: A2.2 code block, `simulator/simulator_flow_lab1.json:130`. |

[VERIFIED] The quoted block is the complete physical update logic, copied from
`simulator/simulator_flow_lab1.json:130`.

### A2.3 Lab2: two independent lamp/blind zones

[VERIFIED] Lab2 has two independent zones. Each has a 400-lux task light and a blind that
admits half the outdoor-illuminance value. No actuator affects the other zone. Its state is
`4*4*2*2*2*2*4 = 1024` discrete combinations. Evidence:
`src/agt/lab_profiles.asl:274-287`; `src/resources/building_2_intermediate.ttl:410-441`.

```javascript
var sun = flow.get('Sunshine') || 0;
var z1l = flow.get('Z1Light') || false;
var z2l = flow.get('Z2Light') || false;
var z1b = flow.get('Z1Blinds') || false;
var z2b = flow.get('Z2Blinds') || false;
var z1 = 25 + (z1l ? 400 : 0) + (z1b ? 0.50 * sun : 0);
var z2 = 25 + (z2l ? 400 : 0) + (z2b ? 0.50 * sun : 0);
flow.set('Z1Level', z1);
flow.set('Z2Level', z2);
var perTick = (z1l ? 1 : 0) + (z2l ? 1 : 0);
flow.set('TotalEnergyCost', (flow.get('TotalEnergyCost') || 0) + perTick);
flow.set('EnergyCost', perTick);
var hr = (flow.get('Hour') || 0) + 0.1;
if (hr >= 24) hr = 0;
flow.set('Hour', hr);
return null;
```

| Code line | Plain-language meaning |
|---|---|
| [VERIFIED] `sun` | Read the fixed outdoor-light value; missing means zero. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `z1l`, `z2l` | Read each lamp's Boolean state. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `z1b`, `z2b` | Read each blind's Boolean state. Here `true` means open/admitting daylight. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `z1 = ...` | Zone 1 is 25 lux plus 400 if its lamp is on plus 50% of sun if its blind is open. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `z2 = ...` | Apply the identical formula independently to zone 2. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] two `flow.set` calls | Publish those exact sensor levels. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `perTick` | Count one legacy energy unit for each lit task lamp; blinds cost zero. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] two energy calls | Accumulate legacy wall-clock energy and publish instantaneous cost. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |
| [VERIFIED] `Hour` and return | Advance an unused clock and end the update. Source: A2.3 code block, `simulator/simulator_flow_lab2.json:130`. |

[VERIFIED] The quoted block is the complete physical update logic from
`simulator/simulator_flow_lab2.json:130`.

### A2.4 Lab3: coupling and a shared spotlight

[VERIFIED] Lab3 retains two lamps and two blinds, adds a shared 150-lux spotlight, gives
each task lamp a 100-lux effect in the other zone, and gives each blind a `0.30*sun` effect
in the other zone in addition to its own `0.50*sun` effect. Its state has 2,048 discrete
combinations. Evidence: `src/agt/lab_profiles.asl:307-321` and
`simulator/simulator_flow_lab3.json:7,130`.

```javascript
var sun = flow.get('Sunshine') || 0;
var z1l = flow.get('Z1Light') || false;
var z2l = flow.get('Z2Light') || false;
var z1b = flow.get('Z1Blinds') || false;
var z2b = flow.get('Z2Blinds') || false;
var sp = flow.get('Spotlight') || false;
var corridor = sp ? 150 : 0;
var z1 = 25
       + (z1l ? 400 : 0)
       + (z2l ? 100 : 0)
       + (z1b ? 0.50 * sun : 0)
       + (z2b ? 0.30 * sun : 0)
       + corridor;
var z2 = 25
       + (z2l ? 400 : 0)
       + (z1l ? 100 : 0)
       + (z2b ? 0.50 * sun : 0)
       + (z1b ? 0.30 * sun : 0)
       + corridor;
flow.set('Z1Level', z1);
flow.set('Z2Level', z2);
var perTick = (z1l ? 1 : 0) + (z2l ? 1 : 0) + (sp ? 2 : 0);
flow.set('TotalEnergyCost', (flow.get('TotalEnergyCost') || 0) + perTick);
flow.set('EnergyCost', perTick);
var hr = (flow.get('Hour') || 0) + 0.1;
if (hr >= 24) hr = 0;
flow.set('Hour', hr);
return null;
```

| Code line | Plain-language meaning |
|---|---|
| [VERIFIED] first six declarations | Read fixed sun and the five Boolean actuator states. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] `corridor` | The shared spotlight contributes 150 lux to both zones when on. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 1 base/own lamp | Begin at 25 lux and add 400 lux from the zone-1 lamp. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 1 foreign lamp | Add 100 lux if the zone-2 lamp is on. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 1 own blind | Add 50% of sun if the zone-1 blind is open. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 1 foreign blind | Add 30% of sun if the zone-2 blind is open. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 1 corridor | Add the shared 150-lux spotlight contribution. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] Zone 2 block | Repeat the same equation symmetrically with zone labels exchanged. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] two `flow.set` calls | Publish both exact levels. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] `perTick` | Charge one legacy unit per task lamp and two for the spotlight; blinds remain free. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |
| [VERIFIED] energy/clock/return lines | Update legacy diagnostics, advance an unused clock, and stop. Source: A2.4 code block, `simulator/simulator_flow_lab3.json:130`. |

[VERIFIED] The quoted block is the complete physical update logic from
`simulator/simulator_flow_lab3.json:130`. Corrected lab3 training scenarios include the
current-physics 525, 125, 675, and 745-lux states; the scenario validator recomputes every
declared level from these equations. Evidence: `benchmark/train_scenarios_lab3.json` and
`analysis/validate_phase1_scenarios.py`.

### A2.5 Observation and actuation timing

[VERIFIED] Illuminance and sunshine are converted to ranks using bounds `[50,100,300]`
and `[50,200,600]`. The target rank is 3 in every clean zone. Evidence:
`src/agt/lab_profiles.asl:260-321`.

[VERIFIED] Training assigns a scenario, waits 250 ms, reads it, chooses an action, dispatches
that action, and reads the next state after the configured action delay. Benchmark v2
dispatches, waits, and then observes. Evidence:
`src/agt/illuminance_controller_agent_ql.asl:207-259` and
`src/agt/illuminance_controller_agent_bench.asl:300-405`.

## A3. Knowledge graphs and an executed query

[VERIFIED] Each building Turtle file has three practical layers: vocabulary and mechanism
templates; device/zone instances and topology; and the WoT/state-vector registry used by
Java. Evidence: `src/resources/building_2_intermediate.ttl:1-118,274-403,405-441`.

[VERIFIED] A `Causes` lamp mechanism says a manipulated lamp state affects an illuminance
dependent variable. A `Mediates` blind mechanism also identifies outdoor illuminance as an
independent variable and sets `ivMinRank=1`. Evidence:
`src/resources/building_2_intermediate.ttl:70-99`.

[VERIFIED] The WoT-contract query enumerates the common action space. The stereotype query
then retrieves component, zone, dependent variable, optional independent variable and
threshold, action/state semantic types, action polarity, and optional energy cost. Evidence:
`src/env/tools/StereotypeReasoner.java:111-192`.

[VERIFIED] I executed the exact stereotype query on
`building_2_intermediate.ttl`. It returned eight rows: ON and OFF for each of the two lamps
and two blinds. Both blind-ON rows carried outdoor illuminance and minimum rank 1; lamp rows
had no independent variable. The full query and unedited row capture are in
`docs/audit/evidence/lab2_sparql_execution_2026-07-21.txt`.

[VERIFIED] Concrete worked decision: for state `[0,2,0,0,0,0,0]` and goal `[2,2]`, zone 1
is dark, zone 2 is already at target, all actuators are off, and sun rank is zero. The
queried IV threshold makes blind-open unsuitable at initialization, while the queried lamp
effect gives `SetZ1Light=true` a summed initial Q-value of `+15`. Every OFF action and both
blind actions have `-100`, while zone-2 lamp ON and do-nothing have zero. The unique greedy
selection is action 3, `SetZ1Light=true`. Evidence: the same capture; decision rules at
`src/env/tools/StereotypeReasoner.java:1203-1277`; summed-Q selection at
`src/env/tools/QLearner.java:2640-2663`.

[VERIFIED] The KG does not store the clean simulator's 400-, 100-, 150-, or fractional-lux
magnitudes as learning inputs. It supplies sign, affected zone, conditionality, topology,
and action semantics. The Q-learner must learn values from transitions. Evidence:
`StereotypeReasoner.ActionInfo` at `src/env/tools/StereotypeReasoner.java:46-72` and the
direction-only prediction contract at lines 956-1013.

## A4. Learning mechanism

[VERIFIED] The learner maintains one Q-table per zone and sums their values to choose one
shared action. Lab1 has 3 actions; lab2 has 9; lab3 has 11, each including do-nothing.
Evidence: `src/env/tools/QLearner.java:186,2640-2663`; action registries under
`config/golden_registry/registry_lab{1,2,3}.csv`.

[VERIFIED] The Bellman update for zone `z` is
`Qz(s,a) <- Qz(s,a) + alpha * (rz/Z + gamma*Qz(s',a*) - Qz(s,a))`, where `a*`
maximizes the sum of all zone tables, `Z` is the zone count, `alpha=0.1`, and
`gamma=0.9`. Evidence: `src/env/tools/QLearner.java:53-60,566-611`.

[VERIFIED] Per-zone reward starts at `-1`; moving one rank closer adds 40 and moving one
rank farther subtracts 40; first arrival at target adds 200; holding target adds 5; leaving
target subtracts 200; an expected but ineffective action subtracts 10; do-nothing away
from target subtracts 5. The result is clipped to `[-50,+50]` before zone normalization.
Energy and cycling are absent from this reward. Evidence:
`src/env/tools/QLearner.java:59-60,2555-2612`.

[VERIFIED] PBRS, when enabled only in the PBRS control, adds
`gamma*Phi(s')-Phi(s)` with `Phi=-|level-target|`. Evidence:
`src/env/tools/QLearner.java:102-110,588-605`; `config/run_config.json:161-174`.

[VERIFIED] Exploration is epsilon-greedy. It begins at 0.3, never drops below 0.01, and
uses profile-specific multiplicative decays: 0.992 for lab1, 0.996 for lab2, and 0.997 for
lab3. Evidence: `src/env/tools/QLearner.java:53-57,1764-1765` and
`src/agt/lab_profiles.asl:260-321`.

[VERIFIED] In the KG arm, Q-table initialization applies redundancy penalties, an IV
penalty when sun is below the blind threshold, and a constructive bonus of
`15*rank-gap*0.5`. The soft greedy prior discourages redundancy by 1 and an empirically
ineffective IV action by 5; its episode-level weight decays to zero over one quarter of the
training budget, and a visited-cell fade also applies. Evidence:
`src/env/tools/StereotypeReasoner.java:300-380,1203-1309`;
`src/env/tools/QLearner.java:81-100,2710-2765`.

[VERIFIED] A v2 training episode proceeds as follows: select the next real scenario ID;
set it; wait 250 ms; record its settled state and presentation number; if already terminal,
record immediate success; otherwise repeat choose action, dispatch, observe, reward/update
until success or 20 steps; write one episode metric row; update first-goal tracking; decay
epsilon; advance to the next scenario. Training always continues to episode 3,000.
Evidence: `src/agt/illuminance_controller_agent_ql.asl:193-281` and
`src/env/tools/QLearner.java:1910-2200`.

[VERIFIED] The ordered training IDs are lab1 `{1,2,3,4,6,7}`, lab2
`{1,2,4,5,6,7,9,10,12,13,16}`, and lab3 `{1,2,5,6,7,9,10,11,13,16}`. Lab1 scenarios
appear 500 times each, lab2 scenarios 272 or 273 times, and lab3 scenarios 300 times.
Evidence: `benchmark/train_scenarios_lab{1,2,3}.json`; fixed horizon in
`config/run_config.json:116-174`.

## A5. Benchmark and run structure

[VERIFIED] Benchmarking does not update Q-values. It loads the trained tables and evaluates
rule-based, QL-no-KG, and QL-KG policies on every declared scenario, five repeats per
scenario, with a 20-step cap. Evidence: `config/run_config.json:116-174` and
`.github/workflows/phase1.yml:228-383`.

[VERIFIED] Lab1 has eight benchmark scenarios; lab2 and lab3 have sixteen each. Therefore,
one seed/policy cell has 40 lab1 rows or 80 lab2/lab3 rows. Evidence:
`benchmark/scenarios_lab{1,2,3}.json` and `bench_runs=5` in `config/run_config.json`.

[VERIFIED] One workflow compiles once, trains `3 labs * 2 arms * 20 seeds = 120` jobs,
benchmarks `3 labs * 3 policies * 20 seeds = 180` jobs, validates the archive, aggregates
analysis, writes workflow provenance and SHA-256 inventory, uploads one consolidated
artifact, and optionally publishes a results tag/branch. Evidence:
`.github/workflows/phase1.yml:55-604`.

[VERIFIED] The four mode workflows use distinct concurrency groups and each matrix is
capped at 10 parallel jobs, keeping intended aggregate data-job concurrency at about 40.
Evidence: `.github/workflows/phase1.yml:43-48,114-127,228-239` and registration addendum
2026-07-21a.

## A6. Experimental arms

| Mode | Exact manipulation | Purpose |
|---|---|---|
| [VERIFIED] `phase1_v2_kg_only` | `stereo=true` gets KG initialization/prior; `stereo=false` is tabula rasa. PBRS and adaptive trust are off. | Corrected arm-C treatment. Source: `config/run_config.json:116-174`. |
| [VERIFIED] `phase1_v2_redundancy_only` | Treatment receives only the WoT/state-derived “do not repeat the current actuator setting” rule. | Test how much of arm C is cheap redundancy shaping. Source: `config/run_config.json:116-174`. |
| [VERIFIED] `phase1_v2_baseline` | KG scale and bonus are zero; PBRS/trust are off in both labels. | Detect hidden label/harness divergence. Source: `config/run_config.json:116-174`. |
| [VERIFIED] `phase1_v2_pbrs_only` | KG scale and bonus are zero; PBRS is on in both labels. | Detect label divergence under generic shaping. Source: `config/run_config.json:116-174`. |

[VERIFIED] The exact settings are in `config/run_config.json:116-174`. Every corrected mode
carries protocol `phase1-v2`, benchmark schema `phase1-benchmark-v2`, and 3,000 episodes.

[VERIFIED] Historical arms A-D, KG-X, init-bonus-5, and prior-decay variants remain useful
only as protocol-v1 development history. The weakness-lab era, pre-inversion action space,
arm-D accidental headline, and noise pilot are dropped as final evidence. Evidence:
`docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`; historical arm definitions in
`config/run_config.json`; `phase1_postinv/run_29705215235/MANIFEST.md`.

## A7. Metrics and exact formulas

| Metric | Protocol-v2 formula and unit | Interpretation |
|---|---|---|
| [VERIFIED] `auc_goal` | `(1/3000) * sum_e GoalReached_e`; unitless. | Higher means a larger fraction of training episodes ended successfully. Evidence: `analysis/sweep_report.py:1025-1037`. |
| [VERIFIED] `auc_reward` | Arithmetic mean of per-episode `RewardZ1+RewardZ2`; internal reward units. | Higher means greater training reward, not physical energy. Evidence: `analysis/sweep_report.py:990-1037`. |
| [VERIFIED] `episodes_to_threshold` | First episode whose trailing window reaches the configured success rate; otherwise censored at horizon. | Lower is faster, but this is descriptive. Evidence: `analysis/sweep_report.py:1040-1058`. |
| [VERIFIED] `mean_first_goal_presentations` | For each declared scenario, first successful presentation; if never solved, `P_s+1` and `censored=true`; average all declared scenarios. | Lower is faster; terminal starts and failures remain in the estimand. Evidence: `src/env/tools/QLearner.java:1910-2200`; `analysis/sweep_report.py:1060-1120`. |
| [VERIFIED] `goal_rate` | `sum GoalReached / benchmark_rows`. | Higher is better final success. Evidence: `analysis/sweep_report.py:68-88`. |
| [VERIFIED] `avg_steps` | Mean `Steps` over benchmark rows; actions, cap 20. | Lower is faster conditional on the fixed scenario mixture. Source: `analysis/sweep_report.py:68-88`. |
| [VERIFIED] `avg_dev` | Mean over rows of `sum_steps sum_z |rank_z-target_z|`; rank-steps. | Lower means less accumulated discrete comfort deviation. Evidence: `src/env/tools/BenchmarkLogger.java:166-170`. |
| [VERIFIED] `avg_wasted` | Mean number of steps marked no-change per row. | Lower means fewer ineffective decisions. Source: `src/env/tools/BenchmarkLogger.java:132-185`. |
| [VERIFIED] `avg_cycling` | Mean number of actuator Boolean reversals, beginning from the scenario's settled actuator state. | Lower means less switching. Evidence: `src/env/tools/BenchmarkLogger.java:132-185`. |
| [VERIFIED] `avg_redundant` | `avg_wasted + avg_cycling`; derived count. | Lower is better; it is not an independent sensor measurement. Evidence: `analysis/sweep_report.py:82-98`. |
| [VERIFIED] `avg_policy_energy` | Mean over rows of `sum_decision_steps [1*active task lamps + 2*active spotlights]`; policy-cost units. Blinds cost zero. | Lower means less deterministic actuator-on cost per decision trace. Evidence: `src/env/tools/Phase1PolicyEnergy.java:1-32`; `src/env/tools/BenchmarkLogger.java:195-208`. |
| [VERIFIED] `avg_legacy_wallclock_energy` | Mean simulator `TotalEnergyCost`, explicitly diagnostic. | Never used for corrected inference because it depends on elapsed ticks. Source: `src/env/tools/BenchmarkLogger.java:195-208`. |

[VERIFIED] Corrected primary family member 3 is the per-seed difference between the arm-C
lab2 `auc_goal` treatment effect and the redundancy-only lab2 treatment effect. This is a
difference of paired differences, in `auc_goal` units. Evidence:
`analysis/phase1_v2_registered_family.py:78-99`.

## A8. Major decisions

| Decision | Reason | Consequence |
|---|---|---|
| [VERIFIED] Build a clean three-lab ladder | Separate aligned-knowledge acceleration from fault handling. | Phase 1 became an internal-validity simulation experiment, not a robustness experiment. Source: `docs/pre_registration.md` §7. |
| [VERIFIED] Invert action discovery | Remove action-space access as a KG-arm advantage. | Both labels now have identical WoT actions. Evidence: `src/env/tools/StereotypeReasoner.java:161-192`. |
| [VERIFIED] Extend protocol-v1 to pooled 20 | Reduce uncertainty after the first ten seeds. | Historical only; it was sighted and later invalidated by protocol defects. Source: `docs/_audit/THESIS_STATE_REPORT.md` Addendum 2026-07-19c. |
| [VERIFIED] Withdraw protocol-v1 claims | Scheduler, first-goal, and energy definitions were invalid. | No old number is thesis-final evidence. Source: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`. |
| [VERIFIED] Schedule actual IDs and fail hard | Eliminate silent random fallbacks. | Fixed, reviewable repeated-scenario schedules and fallback count zero. Source: `src/env/tools/ScenarioCatalog.java:27-93`. |
| [VERIFIED] Wait before start-state recording | Prevent stale pre-settle grouping. | First-goal rows correspond to declared scenario IDs. Source: `src/agt/illuminance_controller_agent_ql.asl:203-223`. |
| [VERIFIED] Fix horizon at 3,000 | Remove early-stop and unequal exposure. | Every seed/arm cell has the same episode count. Source: `config/run_config.json:116-174`. |
| [VERIFIED] Pair RNG by seed | Make paired statistical contrasts genuine at random-stream origin. | Treatment decisions may still create legitimate trajectory divergence. Source: `src/env/tools/QLearner.java:633-676`. |
| [VERIFIED] Replace first-goal metric | Include terminal and never-solved scenarios on the same support. | Comparable censored scenario-level estimand. Source: `src/env/tools/QLearner.java:1910-2200`. |
| [VERIFIED] Replace wall-clock energy | Remove computation-time confounding. | Deterministic step-based policy cost. Source: `src/env/tools/Phase1PolicyEnergy.java:1-32`. |
| [VERIFIED] Use exact sign-flip tests | Stop treating bootstrap estimation as a null test. | No p/q value can be printed as zero. Source: `analysis/sweep_report.py:734-812`. |
| [VERIFIED] Register one `m=5` family | Prevent flexible family selection. | All other metrics are controls/descriptives. Source: `docs/phase1_correction_registration_2026-07-21.md` §6. |

## A9. Execution, provenance, and archives

[VERIFIED] The corrected code, family, seeds, failure rules, and inspection embargo were
committed before dispatch. CI runs `29843626596`, `29845949046`, and `29847158485` were
non-inferential engineering gates; the final gate was green on `d344238`. Evidence:
registration sections 9-10 and GitHub Actions metadata.

[VERIFIED] Each successful cell must carry `TRAINING_OK.json` with protocol version,
ordered IDs and hash, horizon, paired-RNG version, metric schema, run seed, and zero
fallback count. The aggregate rejects missing or inconsistent fields. Evidence:
`analysis/validate_phase1_v2_archive.py:31-126`.

[VERIFIED] The two expiring historical raw artifacts were downloaded intact before expiry
and inventoried at `phase1_postinv/historical_raw/run_29639767776/` and
`run_29692725784/`. Each directory has `ARCHIVE_MANIFEST.md` and `SHA256SUMS.csv`.
Source: each named `ARCHIVE_MANIFEST.md` and `SHA256SUMS.csv`.

[VERIFIED] The corrected archives and remote provenance are listed below. Source: the four
`phase1_v2_corrected/run_*/ARCHIVE_MANIFEST.md` files.

| Run/mode | Artifact ID and GitHub digest | Results tag | Permanent source |
|---|---|---|---|
| [VERIFIED] `29848584965`, arm C | `8509715491`; `sha256:4b18affab…9f35` | `results-20260721-204832-phase1_v2_kg_only-d344238` | `phase1_v2_corrected/run_29848584965/ARCHIVE_MANIFEST.md`; source: that manifest. |
| [VERIFIED] `29848587274`, redundancy | `8509654263`; `sha256:8c2b5326…3547` | `results-20260721-204618-phase1_v2_redundancy_only-d344238` | `phase1_v2_corrected/run_29848587274/ARCHIVE_MANIFEST.md`; source: that manifest. |
| [VERIFIED] `29848589682`, baseline | `8509746522`; `sha256:4c68c48f…f07d` | `results-20260721-204940-phase1_v2_baseline-d344238` | `phase1_v2_corrected/run_29848589682/ARCHIVE_MANIFEST.md`; source: that manifest. |
| [VERIFIED] `29848592010`, PBRS only | `8509939485`; `sha256:e3ba488c…30ec` | `results-20260721-205651-phase1_v2_pbrs_only-d344238` | `phase1_v2_corrected/run_29848592010/ARCHIVE_MANIFEST.md`; source: that manifest. |

[VERIFIED] The complete reproduction command is
`python analysis/reproduce_phase1_v2.py phase1_v2_corrected`; it validates all archives,
rebuilds all four per-mode tables and the registered family, and byte-compares canonical
numeric CSV output. Evidence: `phase1_v2_corrected/CAMPAIGN_MANIFEST.md` and
`analysis/reproduce_phase1_v2.py:1-158`.

## A10. Results

[VERIFIED] The protocol-v1 results `lab2 auc_goal +0.01877`, lab3 legacy first-goal
`+53.30`, lab3 cycling `+0.7375`, redundancy-only `+0.01666`, baseline/PBRS nulls, and all
legacy energy differences are superseded. They may be cited only to explain why correction
was necessary. Evidence: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md` and
registration section 2.

| Corrected registered member | Mean/median difference | 95% bootstrap CI | exact sign-flip p | BH q (`m=5`) | paired rank-biserial | Verdict |
|---|---|---|---|---|---|---|
| [VERIFIED] 1 Arm-C lab2 `auc_goal` | `+0.003700 / +0.003500` | `[+0.002700,+0.004917]` | `1.907×10⁻⁶` | `9.537×10⁻⁶` | `+1.000` | Supported; source: registered-family CSV row 1. |
| [VERIFIED] 2 Redundancy lab2 `auc_goal` | `+0.002583 / +0.002000` | `[+0.001500,+0.003833]` | `1.030×10⁻⁴` | `1.717×10⁻⁴` | `+0.914` | Supported; source: registered-family CSV row 2. |
| [VERIFIED] 3 Arm C minus redundancy lab2 | `+0.001117 / +0.001000` | `[+0.000767,+0.001467]` | `3.052×10⁻⁵` | `7.629×10⁻⁵` | `+1.000` | Supported; source: registered-family CSV row 3. |
| [VERIFIED] 4 Arm-C lab3 `mean_first_goal_presentations` | `+0.110 / 0.000` | `[−0.060,+0.305]` | `0.3044` | `0.3044` | `+0.257` | Null; source: registered-family CSV row 4. |
| [VERIFIED] 5 Arm-C lab3 `avg_cycling` | `+0.07375 / +0.08125` | `[−0.02313,+0.17375]` | `0.1720` | `0.2150` | `+0.379` | Null; source: registered-family CSV row 5. |

[VERIFIED] Redundancy reproduces 69.8% of arm C's lab2 mean, which is “most” under the
frozen rule; member 3 shows that the residual arm-C advantage is nevertheless positive.
Evidence: `phase1_v2_corrected/analysis/registered/phase1_v2_decomposition.json`.

[VERIFIED] Registered descriptives are mixed. Arm C improves lab2 benchmark goal rate,
steps, deviation, deterministic policy energy, wasted actions, cycling, and redundant
actions. On lab3, `auc_goal` is `−0.002300` and deterministic policy energy is `+1.0744`
with intervals excluding zero, while final goal rate and redundant actions are null.
Baseline and PBRS-only are exactly equal on all corrected label contrasts; only the
withdrawn wall-clock diagnostic varies. Evidence:
`phase1_v2_corrected/analysis/phase1_v2_controls_and_descriptives.csv`.

# PART B — IS THE LOGIC SOUND?

## B1. Physics plausibility

[INFERRED] **Verdict: internally auditable toy physics, not a realistic laboratory model.**
The equations are transparent and deterministic, which is useful for mechanism testing,
but they omit nearly every feature that makes real illuminance control difficult. Source:
the complete simulator code in A2.

[VERIFIED] Unrealistic features include instantaneous Boolean actuators, exact linear
addition, fixed ambient light, four outdoor levels, no geometry or inverse-square effects,
no surface reflectance, no saturation, no measurement error, no weather path, no occupancy,
no glare, and rank-only comfort. Evidence: the complete physics in A2.

[INFERRED] The realized small lab2 effect could shrink or reverse in a continuous noisy
model. The KG prior is exactly aligned with the simulator's symbolic sign/topology
structure, and repeated fixed scenarios make early ordering knowledge unusually reusable.
The experiment establishes an effect inside this simulator; it cannot establish
real-building benefit. Source: A2 and corrected A10.
Source: A2 equations and `benchmark/train_scenarios_lab*.json`.

[INFERRED] The new energy metric is deterministic but still not watt-hours. Its weights
`1/2/0` are arbitrary policy-cost units and ignore startup energy, dimming, blind motors,
and duration between decisions. It solves timing confounding, not external validity.
Source: `src/env/tools/Phase1PolicyEnergy.java:1-32` and A2.

## B2. KG correctness and meaningfulness

[INFERRED] **Verdict: internally consistent and capability-equalized, but some “knowledge”
is cheap procedural shaping.** The action-space inversion removes the worst confound: both
arms can do the same things. The executed query confirms that the intended Mediates
threshold reaches Java. Source: A3 and `docs/audit/evidence/lab2_sparql_execution_2026-07-21.txt`.

[VERIFIED] Redundancy suppression needs only the action's target Boolean and current state;
it does not require an ontology. That is why the redundancy-only arm is necessary.
Evidence: `src/env/tools/StereotypeReasoner.java:367-380,1207-1220`.

[INFERRED] Even if arm C exceeds redundancy-only, this design does not prove that RDF/SPARQL
is the cheapest representation. The same sign, zone, and IV-threshold facts could be coded
as a small table. The experiment tests prior information, not the economic necessity of a
knowledge-graph technology. Source: A3 and the missing-control inventory in B9.

[VERIFIED] Redundancy-only realizes 69.8% of arm C's lab2 mean, so the registered verdict is
that cheap “do not repeat an already-set action” information explains most of the benefit.
Arm C is also `+0.001117` above redundancy, supporting a smaller additional bundled-prior
effect conditional on this implementation. It does not isolate RDF/SPARQL as the cause.
Source: A10 and the registered decomposition JSON.

## B3. Agent and learning logic

[INFERRED] **Verdict: coherent for the discrete simulator, with disclosed objective and
observation limitations.** The state contains all simulator variables that affect clean
physics at the chosen rank resolution, so the clean task is approximately Markov. Source:
`src/env/tools/QLearner.java:613-676` and A2.

[INFERRED] Rank discretization is lossy. Two physical lux values in one rank are treated as
identical, and transition magnitudes are invisible. The fixed scenario lattice reduces the
harm, but this representation would be partially observable under continuous sun/noise.
Source: `src/env/tools/QLearner.java:613-676` and `benchmark/train_scenarios_lab*.json`.

[VERIFIED] Reward strongly favors rank progress and target arrival but contains no cycling
or energy term. Therefore adverse cycling/energy alongside favorable `auc_goal` is not a
bug in optimization; it is an objective mismatch. Evidence: `src/env/tools/QLearner.java:2555-2612`.

[VERIFIED] Hyperparameters are equal between labels within every mode/seed. They are not
equal across labs: epsilon decays differ. This does not confound a within-lab KG contrast,
but it prevents a clean causal claim that a lab2-versus-lab3 difference is solely topology
or state-space size. Evidence: `src/agt/lab_profiles.asl:260-321`.

[INFERRED] The 3,000-episode horizon produces very different mean visits per state across
8-, 1,024-, and 2,048-state labs. Cross-lab difficulty combines topology, action count,
state count, scenario distribution, and exploration schedule. Source:
`src/agt/lab_profiles.asl:260-321` and `benchmark/train_scenarios_lab*.json`.

## B4. Experimental fairness

[INFERRED] **Verdict: the corrected within-mode contrasts are substantially fair; cross-mode
attribution still relies on controls rather than literal one-factor identity. Source:
`config/run_config.json:116-174` and correction registration §6.

| Difference | Intended? | Confounding assessment |
|---|---|---|
| [VERIFIED] KG initialization and soft prior in arm C | Yes | This is the treatment, but it bundles several knowledge-use mechanisms. Source: `config/run_config.json:116-174`. |
| [VERIFIED] Redundancy initialization/prior in the redundancy arm | Yes | Separates cheap state/action shaping from other KG facts. Source: `config/run_config.json:116-174`. |
| [VERIFIED] `useStereotypes` label and extra reasoning work | Unavoidable | Baseline/PBRS null-label runs test hidden divergence; deterministic energy removes timing bias. Source: correction registration §6.4. |
| [VERIFIED] Treatment-dependent later RNG consumption | Consequence | Streams start equal; different decisions legitimately create different trajectories. Source: correction registration §4.3. |
| [VERIFIED] Different workflow/hardware for arm C and redundancy | No | Member 3 pairs by seed across workflows, but execution noise is not a shared block. Settling and deterministic scenarios reduce, not eliminate, this risk. Source: `.github/workflows/phase1.yml:43-48`. |
| [VERIFIED] Lab-specific epsilon decay/state/action counts | No for within-lab, yes for ladder interpretation | Do not causally attribute cross-lab effect differences to one feature. Source: `src/agt/lab_profiles.asl:260-321`. |
| [VERIFIED] Rule-based benchmark mode | Descriptive | It is not part of the registered KG-versus-no-KG inference. Source: correction registration §6.4. |

[VERIFIED] No remaining identified asymmetry recreates the protocol-v1 scheduler,
first-goal, or wall-clock-energy defects. All four archive gates verify the actual
execution. Source: A8 and
`phase1_v2_corrected/analysis/phase1_v2_protocol_gate_summary.json`.

## B5. Statistics

[INFERRED] **Verdict: the v2 primary analysis is defensible for the registered seed-level
estimands; it does not support episode-level population claims. Source: correction
registration §§5-6 and `analysis/phase1_v2_registered_family.py:45-137`.

[VERIFIED] Each seed is reduced to one outcome per arm and inference pairs the 20 seed
differences. Episodes are not treated as 60,000 independent replicates. Evidence:
`analysis/phase1_v2_registered_family.py:17-99`.

[VERIFIED] For at most 20 nonzero pairs, all sign assignments are enumerated in a two-sided
sign-flip test. The smallest possible nonzero two-sided p-value with 20 nonzero pairs is
`2/2^20 = 0.0000019073486328125`. Above 20 pairs, one million draws use a plus-one
correction. Evidence: `analysis/sweep_report.py:507-567`.

[VERIFIED] Bootstrap is used only for a confidence interval on the mean paired difference.
The exact sign test, paired rank-biserial, mean and median differences are also reported.
Cliff's delta is explicitly unpaired descriptive context. Evidence:
`analysis/phase1_v2_registered_family.py:49-72`.

[VERIFIED] Benjamini-Hochberg is applied once to exactly five two-sided sign-flip p-values.
This family was frozen after full disclosure of old results but before v2 data. Evidence:
registration sections 2, 6, and 7.

[VERIFIED] No corrected p- or q-value is zero. The smallest realized p-value is the exact
floor `1.9073486328125×10⁻⁶`; its BH q-value is `9.5367431640625×10⁻⁶`. Evidence:
registered-family CSV row 1.

[INFERRED] The sign-flip test assumes exchangeability/symmetry of seed differences under
the null. With 20 seeds, that assumption cannot be strongly diagnosed. The exact sign test
is a useful weaker-assumption companion, while effect sizes and intervals should carry
more interpretive weight than a q-value threshold. Source: correction registration §5.

[INFERRED] The protocol-v1 pooled-20 analysis was not defensible as a clean confirmatory
endpoint after the first ten seeds were seen, regardless of its later registration label.
Protocol v2 does not extend seeds: 1-20 is fixed and sighted status is explicit. Source:
`docs/thesis_methods_phase1_registration.md` §1 and correction registration §2.

## B6. Registration integrity

[INFERRED] **Verdict: June protocol-v1 registration was post-analysis; July v1 registration
was prospective but measured a broken protocol; v2 is genuinely pre-data and explicitly
sighted.** Source: `docs/thesis_methods_phase1_registration.md` §1.

[VERIFIED] The original Phase 1 design addendum was pushed about 8.6 days after the first
June dispatch and cited completed analyses. Those June claims are exploratory or
confirmatory-with-post-hoc-registration, not preregistered. Evidence:
`docs/thesis_methods_phase1_registration.md`, section 1.

[VERIFIED] The July arm-C runs contained registrations before their dispatches, but
registration timing cannot validate a defective scheduler or metric. Evidence: runs
`29639767776`, `29692725784`; protocol notice.

[VERIFIED] V2 disclosed every known old result, fixed the code and family, ran green CI,
then dispatched four successful runs on the registration-containing SHA. The queue
correction was also committed before data. Evidence: registrations and runs listed in the
opening and the four archive manifests.

[VERIFIED] The post-download seed-order correction was made after data existed but before
the registered-family command produced output. The cross-platform canonicalization was
made after the registered output, when full reproduction exposed last-bit float text
differences. Both changes are narrow and non-analytic, but neither is pre-data and both must
remain disclosed. Evidence:
`docs/phase1_correction_analysis_deviation_2026-07-22.md`.

[VERIFIED] Earlier automated changes that violated the old audit's read-only rule remain in
history. This corrective campaign was explicitly authorized; history was not force-pushed
or rewritten. Evidence: git log from `f9f41df` through `d344238`.

## B7. Claims-versus-evidence trace

[VERIFIED] The exhaustive machine-readable ledger is
`docs/audit/phase1_claim_ledger.csv`. Its source manifest covers the state report and all
embedded addenda, registrations, Phase 1 methods/results drafts, xzone reports, dashboard,
protocol notices, and this audit. Each quantitative source line records document/line,
metric, numeric token(s), run/file, status, match result, and classification. Evidence:
`docs/audit/phase1_claim_sources.json` and `analysis/phase1_claim_ledger_lint.py`.

[VERIFIED] The final ledger contains 4477 quantitative source lines: 202 current matched lines, 1120 withdrawn historical lines, 1883 non-result quantities, and 1272 other-phase lines; there are 0 uncovered lines and 0 missing corrected sources. Evidence: `analysis/build_phase1_claim_ledger.py` and `analysis/phase1_claim_ledger_lint.py`.

[VERIFIED] Every protocol-v1 empirical line is classified historical/protocol-affected;
corrected result lines must match a committed `phase1_v2_corrected/` file. CI fails for a
missing line, stale line digest, mismatched numeric tokens, duplicate row, or untagged audit
paragraph/table row. Evidence: `analysis/phase1_claim_ledger_lint.py`.

## B8. Interpretation and alternative explanations

| Headline | Strongest alternative explanation | Can it be ruled out? |
|---|---|---|
| [VERIFIED] Arm-C lab2 `auc_goal` effect | Cheap redundancy shaping, not mechanism knowledge. | Mostly: redundancy reproduces 69.8%, but the registered residual is still positive. Source: A10. |
| [INFERRED] Arm C exceeds redundancy | Bundled optimistic initialization or ordering, not KG representation itself. | No. It is part of the treatment implementation. Source: `config/run_config.json:116-174`. |
| [VERIFIED] Lab3 first-goal/cycling effect | The old effect was broken measurement rather than coupling. | The corrected estimates are null, so the old headline is ruled out for protocol v2. Source: A10. |
| [VERIFIED] Baseline/PBRS label parity | Hidden label divergence. | Corrected outcomes are exactly equal, strongly ruling out realized divergence in these traces; equivalence beyond them is untested. Source: controls CSV. |
| [VERIFIED] Lab3 deterministic energy cost | Arm C keeps more weighted actuators active. | Supported as a trace explanation; real-energy meaning is not. Source: run `29848584965` paired-tests CSV. |
| [INFERRED] General KG benefit | Exact symbolic alignment and repeated scenarios favor priors. | No; a noisier continuous simulator and real lab are untested. Source: A2-A3. |

[INFERRED] Thesis wording must say “in this registered simulator protocol” and identify
which prior rule produced the effect. “Knowledge graphs improve building control” is not
supported by Phase 1 alone. Source: limits established in B1-B3.

## B9. Missing measurements and tests

- [INFERRED] No continuous dimming, spectral quality, glare, occupancy, real weather, or calibrated sensor noise. Source: A2 simulator equations.
- [INFERRED] No real-building or higher-fidelity simulator validation. Source: repository inventory in `docs/_audit/00_inventory.md`.
- [INFERRED] No hand-coded table containing exactly the same physics facts as the KG, so representation cost is untested. Source: corrected arms in `config/run_config.json:116-174`.
- [INFERRED] No factorial ablation of each KG rule inside arm C under protocol v2 beyond redundancy-only. Source: correction registration §6.3.
- [INFERRED] No within-seed repeated execution to quantify residual scheduler/timing variance after 250-ms settling. Source: `.github/workflows/phase1.yml:86-239`.
- [INFERRED] No common epsilon schedule/state-visit budget across labs, so the difficulty ladder is descriptive. Source: `src/agt/lab_profiles.asl:260-321`.
- [INFERRED] No reward that jointly optimizes goal, cycling, comfort deviation, and energy. Source: `src/env/tools/QLearner.java:2555-2612`.
- [INFERRED] No equivalence margin for baseline/PBRS controls; a nonsignificant difference is not proof of equality. Source: correction registration §6.4.
- [INFERRED] No sensitivity analysis for the `1/2/0` policy-energy weights. Source: `src/env/tools/Phase1PolicyEnergy.java:1-32`.
- [INFERRED] No out-of-distribution scenario family; benchmark states are fixed and public. Source: `benchmark/benchmark_scenarios_lab*.json`.

# PART C — OPEN QUESTIONS, CAVEATS, AND RESOLVABILITY

## C1. Consolidated caveat register

| Severity | Caveat | Resolvable? | Concrete resolution/status |
|---|---|---|---|
| [VERIFIED] blocker, resolved | Random fallback from non-contiguous IDs. | Yes | Actual-ID schedule, fatal validation, manifest fallback count zero. Source: A8 and `src/env/tools/ScenarioCatalog.java:27-93`. |
| [VERIFIED] blocker, resolved | Pre-settle/selected-set legacy first-goal. | Yes | Scenario presentations, censoring, equal-row rejection. Source: A8 and `src/env/tools/QLearner.java:1910-2200`. |
| [VERIFIED] blocker, resolved | Wall-clock energy confound. | Yes | Step-based `PolicyEnergyCost`; legacy column diagnostic only. Source: A7 and `src/env/tools/BenchmarkLogger.java:195-208`. |
| [VERIFIED] must-address, resolved | Pseudo-p-values and zero p/q. | Yes | Exact sign-flip/sign tests and lint. Source: B5 and `analysis/sweep_report.py:734-812`. |
| [VERIFIED] must-address, resolved | Raw historical artifacts expiring. | Yes | Both pooled-20 inputs permanently archived and hashed. Source: A9 archive manifests. |
| [VERIFIED] must-address, resolved | Four v2 runs and permanent archives. | Yes | Four aggregates succeeded; archives and inventories pass. Source: A9 and protocol-gate summary JSON. |
| [VERIFIED] must-address, resolved | Exhaustive claim trace. | Yes | Generated ledger and CI linter cover all declared sources. Source: B7. |
| [VERIFIED] must-address, resolved with disclosure | Post-download analysis execution defects. | Yes | Numeric seed sorting and canonical float serialization are tested and disclosed. Source: `docs/phase1_correction_analysis_deviation_2026-07-22.md`. |
| [INFERRED] must-address, unresolved scientifically | External validity of toy physics. | Partly | State limitation prominently; add higher-fidelity/real-lab validation as future work. Source: B1. |
| [INFERRED] must-address, unresolved | KG versus equivalent hand-coded knowledge. | Yes | Future protocol-v2 representation control with identical facts. Source: B2/B9. |
| [INFERRED] must-address, unresolved | Cross-lab epsilon/state-space confounding. | Yes | Rerun a factorial common-schedule/visit-budget study if cross-lab causality is claimed. Source: B3/B4. |
| [INFERRED] nice-to-have | Energy-weight sensitivity. | Yes | Recompute traces under registered alternative weights; no simulator rerun needed if states are archived. Source: B1/B9. |
| [INFERRED] nice-to-have | Residual repeatability noise. | Yes | Repeat selected seeds without changing the primary family; label descriptive. Source: B4/B9. |

## C2. What Phase 1 answers

[VERIFIED] Phase 1 answers that this exact KG-prior implementation produces a small
favorable lab2 `auc_goal` difference, that redundancy-only reproduces most but not all of
its mean, and that corrected lab3 first-goal presentations and cycling are null in these
three deterministic clean simulators at 3,000 episodes. Source: A10.

[VERIFIED] Registered descriptives additionally show favorable lab2 final-policy outcomes,
a small adverse lab3 full-horizon `auc_goal` difference, and an adverse lab3 deterministic
policy-energy cost for arm C. Source: controls/descriptives CSV.

[INFERRED] Phase 1 does not answer whether KGs improve real buildings, whether RDF/SPARQL
is cheaper than a table, whether the effect survives realistic noise/dynamics, whether one
reward can optimize comfort and energy, or whether topology alone explains lab-to-lab
differences. Source: B1-B4 and B9.

# PART D — PRIORITIZED THESIS-READY ACTIONS

| Priority | Action | Why | Effort | Done condition/status |
|---|---|---|---|---|
| [VERIFIED] 1 | Withdraw protocol-v1 claims. | They are invalid final evidence. | Completed | Binding notice and banners committed before rerun. Source: `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`. |
| [VERIFIED] 2 | Fix schedule, settle timing, censoring, horizon, RNG pairing. | Removes direct data/estimand defects. | Completed | Code/tests/green CI on `d344238`. Source: A8 and GitHub Actions run `29847158485`. |
| [VERIFIED] 3 | Replace wall-clock energy. | Removes timing/KG-compute confounding. | Completed | Deterministic trace tests and schema v2. Source: `src/test/java/tools/Phase1ProtocolV2Test.java:87-170`. |
| [VERIFIED] 4 | Register corrected analysis before data. | Restores prospective integrity. | Completed | Commits `87ae528` and `d344238`. Source: correction registrations. |
| [VERIFIED] 5 | Run arm C, redundancy, baseline, PBRS, labs 1-3, seeds 1-20. | Supplies replacement evidence and controls. | Completed | Four successful 302-job workflows. Source: A9. |
| [VERIFIED] 6 | Archive every raw/result file and verify inventories. | Prevents artifact expiry and selective retention. | Completed | Four complete archives, manifests, artifact inventories, and campaign inventory. Source: `phase1_v2_corrected/CAMPAIGN_MANIFEST.md`. |
| [VERIFIED] 7 | Run exact `m=5` analysis and reproduce byte-for-byte. | Produces the registered result without manual manipulation. | Completed | Canonical numeric reproduction exits zero; deviations disclosed. Source: `analysis/reproduce_phase1_v2.py` and deviation document. |
| [VERIFIED] 8 | Rewrite state report, drafts, dashboard, and audit. | Removes live superseded narrative. | Completed | Current surfaces use protocol-v2; historical files carry withdrawal banners. Source: `docs/phase1_results_v2.md`. |
| [VERIFIED] 9 | Generate exhaustive ledger and enable CI lint. | Makes every quantitative claim traceable. | Completed | Builder/linter and CI gate cover the source manifest. Source: B7 and `.github/workflows/ci.yml`. |
| [INFERRED] 10 | Limit thesis claim and propose external validation. | Simulation cannot establish real-world benefit. | Completed writing; future empirical work remains | Thesis uses simulator-conditional wording and a concrete future validation design. Source: B1/B9. |

[INFERRED] Scientific completion does not require favorable results. Null or adverse v2
outcomes replace the legacy narrative and close Phase 1 just as validly as positive ones.
Source: correction registration §1.
