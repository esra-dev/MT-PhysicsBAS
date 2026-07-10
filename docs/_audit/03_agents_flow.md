# Audit Step 3 — Agents & Runtime Information Flow

**Era:** NEW (Phase-based, lab1/lab2/lab3 ladder + faulty labs + labmon + lab4/lab5 + slow labs)  
**Date:** 2026-07-07  
**Scope:** Every `.asl` agent in `src/agt/`; every CArtAgO artifact under `src/env/tools/`
(including `jia/` internal-action operators); the complete per-step data path from
`readLabStatus` through `invokeAction` to `calculateQ`; and the profile-selection
mechanism in `lab_profiles.asl`.

> **Traceability rule (ground rule 1):** every number, parameter, and claim below is
> cited as `path#Lstart–Lend`.  "NOT FOUND" marks anything that could not be located.

---

## 1. Agents — roles, plans, era labels

All five agents reside in `src/agt/`.  Each file includes the shared profile registry
via `{ include("lab_profiles.asl") }` so a single `active_profile/1` belief change
controls every agent uniformly.

### 1.1  `illuminance_controller_agent.asl` — demo-only, OLD era

**Role:** Interactive pedagogical demo for the original single-zone custom lab (port 1881).
An explicit banner at  
[src/agt/illuminance_controller_agent.asl#L5–L10](../../../src/agt/illuminance_controller_agent.asl#L5)  
reads:
> "⚠️ INTERACTIVE DEMO ONLY — NOT USED BY THE BENCHMARK OR PAPER EXPERIMENTS."

The rule-based benchmark mode is in `illuminance_controller_agent_bench.asl`;
Q-learning training is in `illuminance_controller_agent_ql.asl`.

**Plans:**

| Plan label | Context | Purpose |
|---|---|---|
| `@start` | `lab_environment_custom(CustomURL)` | Creates `LabEnvironment` + `OntologyArtifact`, configures discretisation, calls `discoverZones`, enters control loop |
| `@setup_zone_goals` | per-zone | Queries `discoverZoneQuantity` from the ontology; adds `zone_goal/5` belief |
| `@control_loop` | NOT FOUND in file | Described by comments but implementation details are embedded further down |

This agent uses **live calibration** for rank bounds (calling `calibrate`) and
**static beliefs** `zone_target(1, 3)` / `zone_target(2, 2)` at
[src/agt/illuminance_controller_agent.asl#L34–L35](../../../src/agt/illuminance_controller_agent.asl#L34).

---

### 1.2  `illuminance_controller_agent_ql.asl` — Phase 1 (NEW era)

**Role:** Trains a Q-table over `num_episodes` episodes, then executes one greedy policy
demonstration.  Runs as Gradle task `taskQl`.

**Key beliefs (defaults):**

| Belief | Value | Source line |
|---|---|---|
| `use_stereotypes` | `true` (toggle for ql_false) | [L36](../../../src/agt/illuminance_controller_agent_ql.asl#L36) |
| `num_episodes` | `3000` (overridden by profile) | [L49](../../../src/agt/illuminance_controller_agent_ql.asl#L49) |
| `max_steps_per_episode` | `20` | [L50](../../../src/agt/illuminance_controller_agent_ql.asl#L50) |
| `action_delay_ms` | `65` ms ⚠️ | [L56](../../../src/agt/illuminance_controller_agent_ql.asl#L56) |
| `exec_delay_ms` | `100` ms | [L61](../../../src/agt/illuminance_controller_agent_ql.asl#L61) |
| `exec_max_steps` | `20` | [L63](../../../src/agt/illuminance_controller_agent_ql.asl#L63) |

> ⚠️ `action_delay_ms(65)` at [L56](../../../src/agt/illuminance_controller_agent_ql.asl#L56) is annotated "must exceed 200 ms simulator tick" — the
> value is **inconsistent with its own comment**.  Audit Step 4 recorded a fix to 250 ms
> (see `docs/pre_registration.md §S4-5`).  This line has not been updated in the source.

**Initial goal:** `!apply_profile_then_start`
[src/agt/illuminance_controller_agent_ql.asl#L66](../../../src/agt/illuminance_controller_agent_ql.asl#L66).

**Plan sequence — startup:**

1. `@apply_runtime_overrides_ql` — reads `-Dactive.profile` via `tools.jia.system_prop`;
   retains pre-patched `active_profile/1` if the JIA is unavailable
   [L82–L96](../../../src/agt/illuminance_controller_agent_ql.asl#L82).
2. `@apply_profile_then_start` — calls `!profile_td`, `!profile_light_bounds`,
   `!profile_sunshine_bounds`, `!profile_zone_targets`, `!derive_zone_goal`,
   `!maybe_set_train_scenarios_file`, `!start`
   [L69–L80](../../../src/agt/illuminance_controller_agent_ql.asl#L69).
3. `@start` — creates `LabEnvironment` artifact, probes simulator reachability,
   calls `configureDiscretization`, creates `QLearner` artifact, calls
   `configureQLearner(Goal, UseStereotypes, OntPaths, SunProb)`, applies
   per-profile training parameters (`setEpsilonDecay`, `setTrainingBudgetEpisodes`),
   creates `StereotypeLearner` artifact, seeds it with action metadata,
   saves initial Q-table, calls `!train(0)`
   [L132–L194](../../../src/agt/illuminance_controller_agent_ql.asl#L132).

**Plan sequence — training loop:**

| Plan | Trigger | Action |
|---|---|---|
| `@train` | `N < MaxEpisodes` | Set start state (scenario or random), `.wait(250)`, `!run_episode(N,0)`, `readLabStatus`, `encodeState`, `isTerminal`, `endEpisode`, `decayEpsilon`, log, `hasConverged` check [L198–L248](../../../src/agt/illuminance_controller_agent_ql.asl#L198) |
| `@train_done` | `N >= MaxEpisodes` | Saves Q-table, metrics CSV, IV-stats JSON, coverage CSV, first-goal CSV, learned stereotypes TTL, then calls `!execute_policy(0)` [L252–L295](../../../src/agt/illuminance_controller_agent_ql.asl#L252) |
| `@run_episode` | recursive | `readLabStatus → encodeState → isTerminal → !do_step` [L305–L316](../../../src/agt/illuminance_controller_agent_ql.asl#L305) |
| `@do_step` | one action per step | **The core step** — see §3 for the full trace [L322–L357](../../../src/agt/illuminance_controller_agent_ql.asl#L322) |
| `@execute_policy` | post-training greedy demo | `readLabStatus → encodeState → isTerminal → getActionFromState(explore=false) → invokeAction → .wait(exec_delay_ms) → recurse` [L365–L396](../../../src/agt/illuminance_controller_agent_ql.asl#L365) |

**Artifacts created (names):** `"lab"` (LabEnvironment), `"qlearner"` (QLearner),
`"learner"` (StereotypeLearner).

---

### 1.3  `illuminance_controller_agent_bench.asl` — Phase 1 benchmark (NEW era)

**Role:** Executes three benchmark modes (`rule_based`, `ql_false`, `ql_true`) over a
fixed scenario list and produces `benchmark_results_<mode>.csv` + `bench_step_log_<mode>.csv`.
Runs as Gradle task `taskBench`.

**Key beliefs:**

| Belief | Value | Source line |
|---|---|---|
| `bench_mode` | `"ql_true"` (one uncommented) | [L27](../../../src/agt/illuminance_controller_agent_bench.asl#L27) |
| `bench_runs` | `5` | [L27](../../../src/agt/illuminance_controller_agent_bench.asl#L27) |
| `exec_max_steps` | `20` | [L28](../../../src/agt/illuminance_controller_agent_bench.asl#L28) |
| `exec_delay_ms` | `100` ms | [L31](../../../src/agt/illuminance_controller_agent_bench.asl#L31) |
| `bench_anti_stuck` | `false` | [L38](../../../src/agt/illuminance_controller_agent_bench.asl#L38) |

**Mode-specific initialisation:**

| Mode | Plan | Artifacts created |
|---|---|---|
| `rule_based` | `@init_mode_rule_based` — creates `OntologyArtifact`, optionally imports `learned_stereotypes_true<QtSuffix>.ttl`, discovers zones [L140–L150](../../../src/agt/illuminance_controller_agent_bench.asl#L140) | `"lab"`, `"ontology"`, `"benchlogger"` |
| `ql_true` / `ql_false` | `@init_mode_ql` — creates `QLearner`, calls `setSeed(42)`, `loadQTable`, `loadIVStats`, opens rich JSONL trace [L165–L200](../../../src/agt/illuminance_controller_agent_bench.asl#L165) | `"lab"`, `"qlearner"`, `"benchlogger"` |

**Outer loop:** `!run_all_runs(1, TotalRuns)` → `!run_scenario_list` → `!run_scenario_step`.

**Step dispatch** (`@run_scenario_step_continue`):
[L317–L372](../../../src/agt/illuminance_controller_agent_bench.asl#L317)
```
readLabStatus → !check_terminal → if AtGoal → endScenario(true, …)
                                  else → !dispatch(Mode, …)
                                       → readLabStatus (post-action)
                                       → readZoneTemperatures
                                       → !is_wasted / !is_cross_zone
                                       → recordStep / recordStepDetailRichV2
                                       → !fingerprint_weakness  (QL modes)
                                       → .wait(Delay)
                                       → recurse
```

**Dispatch sub-plans:**
- `@dispatch_rule_based` — calls `!rb_process_first_off_target` which uses
  `OntologyArtifact` SPARQL to identify off-target zones and tries
  `!rb_increase` / `!rb_decrease`
  [L421–L433](../../../src/agt/illuminance_controller_agent_bench.asl#L421).
- `@dispatch_ql` (via `!dispatch("ql_true"|"ql_false", …)`) — NOT a separate plan;
  QL modes call `getActionFromState(StateVec, false, Action)` directly inside
  `@run_scenario_step_continue` or via the shared `@dispatch` router (exact lines
  within `@run_scenario_step_continue` referenced above).

---

### 1.4  `illuminance_controller_agent_adapt.asl` — Phase 2 (NEW era)

**Role:** Loads a Phase-1 clean-trained Q-table into a faulty simulator, detects faults
via `observeForFaults`, blacklists defective components, warm-restarts re-learning
over the surviving action set.  Runs as Gradle task `taskAdapt`.

**Key beliefs:**

| Belief | Value | Source line |
|---|---|---|
| `use_stereotypes` | `true` | [L35](../../../src/agt/illuminance_controller_agent_adapt.asl#L35) |
| `num_episodes` | `2000` (overridden per-profile) | [L45](../../../src/agt/illuminance_controller_agent_adapt.asl#L45) |
| `max_steps_per_episode` | `20` | [L46](../../../src/agt/illuminance_controller_agent_adapt.asl#L46) |
| `greedy_eval_episodes` | `20` | [L51](../../../src/agt/illuminance_controller_agent_adapt.asl#L51) |

**Startup:** `@apply_profile_then_start_adapt` → `@start_adapt`:
creates `LabEnvironment` and `QLearner` with the **faulty** simulator's TD,
but the **nominal** ontology (same as clean parent), then warm-loads
`qtable_final_stereotypes_<bool><CleanSuffix>.csv` via `loadQTable`
[L175–L185](../../../src/agt/illuminance_controller_agent_adapt.asl#L175).
The `CleanSuffix` is resolved from `adapt_source/2` at
[src/agt/lab_profiles.asl#L817–L838](../../../src/agt/lab_profiles.asl#L817).

**Adaptation loop:** `@adapt(N)` mirrors `@train(N)` but adds after `!run_episode_adapt`:
```
if (detected(_)) →
    updateRecoveryDetector →
    hasRecovered(Recovered) →
    if (Recovered & not reconverged(_)) → +reconverged(N) → jump to @adapt_done
```
[L221–L247](../../../src/agt/illuminance_controller_agent_adapt.asl#L221).

**Step plan `@do_step_adapt`** adds `observeForFaults(SVBefore, Action, SVAfter, NewlyDefective)`
after every Bellman update.  If `NewlyDefective` is non-empty it calls
`blacklistComponent(WotType, NRemoved)` → `warmRestart` → asserts `detected(EpN)`.

**Outputs:** `recovery_log_<bool>_<profile>.csv` (via `saveRecoveryLog`), plus the
same Q-table / metrics / coverage / learned-stereotypes files as the QL agent.

---

### 1.5  `illuminance_controller_agent_dynamics.asl` — Phase 3 (NEW era)

**Role:** Does **not** train a Q-table.  Runs two phases:
- **Phase A (probe):** controlled single-actuator trials to measure response delays;
  results written to KG (`learned_dynamics_<bool>_<profile>.ttl`) and CSV.
- **Phase B (exploit):** deadline-aware planning for `tb_goal/4` goals
  (`tb_goal("g1", 1, 3, 15.0)` … `tb_goal("g6", 2, 3, 300.0)`)
  [L83–L90](../../../src/agt/illuminance_controller_agent_dynamics.asl#L83).

**Key beliefs:**

| Belief | Default | Source line |
|---|---|---|
| `use_dynamics_kg` | `true` | [L43](../../../src/agt/illuminance_controller_agent_dynamics.asl#L43) |
| `seconds_per_tick` | `5.0` | [L59](../../../src/agt/illuminance_controller_agent_dynamics.asl#L59) |
| `probe_settle_ms` | `400` | [L60](../../../src/agt/illuminance_controller_agent_dynamics.asl#L60) |
| `probe_poll_ms` | `50` | [L61](../../../src/agt/illuminance_controller_agent_dynamics.asl#L61) |
| `probe_max_wait_ticks` | `60` | [L62](../../../src/agt/illuminance_controller_agent_dynamics.asl#L62) |
| `probe_hold_ticks` | `16` | [L63](../../../src/agt/illuminance_controller_agent_dynamics.asl#L63) |
| `probes_per_actuator` | `8` | [L64](../../../src/agt/illuminance_controller_agent_dynamics.asl#L64) |

**Planner rule** (Jason rule):
```prolog
believed_delay(A, true,  D) :- learned_delay_sec(A, D).
believed_delay(_, false, 0).
```
[L96–L99](../../../src/agt/illuminance_controller_agent_dynamics.asl#L96) —
KG-primed arm reads learned delay; tabula-rasa arm assumes zero, always choosing the
cheapest (and potentially slow blind) actuator, missing tight deadlines.

**Artifacts created:** `"lab"` (LabEnvironment), `"qlearner"` (QLearner — action-space
enumeration only), `"dynamics"` (DynamicsLearner).

**Probe baselines** declared as facts:
```prolog
probe_baseline("lab2_slow", ["Z1Light","Z2Light","Z1Blinds","Z2Blinds","Sunshine"],
                            [false,false,false,false,900]).
probe_baseline("lab3_slow", ["Z1Light","Z2Light","Z1Blinds","Z2Blinds","Spotlight","Sunshine"],
                            [false,false,false,false,false,900]).
```
[L69–L74](../../../src/agt/illuminance_controller_agent_dynamics.asl#L69).

---

## 2. CArtAgO Artifacts

### 2.1  `LabEnvironment.java` — environment interface

**Package / extends:** `tools` / `cartago.Artifact`
[src/env/tools/LabEnvironment.java#L1–L40](../../../src/env/tools/LabEnvironment.java#L1).

**Responsibilities:** Loads a W3C WoT Thing Description; provides CArtAgO `@OPERATION`
methods that translate ASL calls into HTTP requests to the Node-RED simulator.

**Fields of note:**

| Field | Type | Default | Purpose |
|---|---|---|---|
| `lightBounds` | `double[3]` | `{75.0, 200.0, 400.0}` | Indoor lux rank thresholds |
| `sunshineBounds` | `double[3]` | `{50.0, 200.0, 700.0}` | Sunshine rank thresholds |
| `simHttp` | `SimulatorHttpClient` | — | Fault-tolerant HTTP (retries, backoff) |
| `validator` | `WotInputValidator` | — | TD-driven input gating before every HTTP dispatch |
| `dryRun` | `volatile boolean` | `false` | Short-circuits all mutating calls; read-path stays live |
| `scenarioRng` | `Random` | seed `42L^mix64(runSeed)` | Seeded PRNG for `setRandomLabState` (S0-FIX-1) |

**Key operations:**

| `@OPERATION` | Inputs | Output | Notes |
|---|---|---|---|
| `init(tdUrl)` | `String` | — | Resolves `classpath:` URIs, strips UTF-8 BOM; builds `WotInputValidator` [L57–L104](../../../src/env/tools/LabEnvironment.java#L57) |
| `configureDiscretization(lBounds, sBounds)` | `Object[3]` × 2 | — | Sets `lightBounds` / `sunshineBounds` [L117–L124](../../../src/env/tools/LabEnvironment.java#L117) |
| `readLabStatus(zoneLevels, sunshineRank, boolStateKeys, boolStateValues)` | — | 4× `OpFeedbackParam` | HTTP GET `/status` → parse JSON → regex `#Z<n>Level$` → `discretize(v, lightBounds)` → sort by zone index; boolean state URI arrays [L349–L392](../../../src/env/tools/LabEnvironment.java#L349) |
| `readLabStatusTimed(zoneLevels, sunshineRank, tick)` | — | 3× `OpFeedbackParam` | Same as above + reads `was#Tick` for Phase-3 delay measurement; tick=-1 if absent [L399–L448](../../../src/env/tools/LabEnvironment.java#L399) |
| `readZoneTemperatures(zoneTemperatures)` | — | `OpFeedbackParam<Object[]>` | Regex `#Z<n>Temp$`; empty array if absent (legacy 2-zone flows) [L453–L477](../../../src/env/tools/LabEnvironment.java#L453) |
| `invokeAction(wotSemanticType, value)` | `String`, `boolean` | — | Validates via `WotInputValidator`; looks up TD affordance by semantic type → builds JSON payload → HTTP POST `/action` [L799–L856](../../../src/env/tools/LabEnvironment.java#L799) |
| `setLabStateFromMap(keys, values)` | `Object[]` × 2 | — | Validates then HTTP POST `/setState` with JSON body [L519–L558](../../../src/env/tools/LabEnvironment.java#L519) |
| `setRandomLabState()` | — | — | Reads `benchmark/train_scenarios.json`; picks `scenarioRng.nextInt(N)` (post-S0-FIX-1); calls `setLabStateFromMap` [L647–L680](../../../src/env/tools/LabEnvironment.java#L647) |
| `setScenarioLabState(file, id)` | `String`, `int` | — | Finds scenario by id in JSON file; calls `setLabStateFromMap` [L685–L715](../../../src/env/tools/LabEnvironment.java#L685) |
| `getScenarioIds(file, ids)` | `String` | `OpFeedbackParam` | Enumerates `"id"` fields from scenario JSON [L722–L739](../../../src/env/tools/LabEnvironment.java#L722) |
| `readEnergyCost(totalCost)` | — | `OpFeedbackParam<Double>` | Reads `was#TotalEnergyCost` from `/status` |
| `calibrate(numSamples, …)` | `int` | 2× `OpFeedbackParam` | N×reset + sample → percentile-based bounds (25th/50th/75th) [L252–L330](../../../src/env/tools/LabEnvironment.java#L252) |

**`deriveSimulatorUrl(path)`** — iterates `td.getActions()` to find the first
`invokeAction` Form, replaces `/action$` suffix with `path` (`/reset`, `/setState`,
etc.) [L770–L793](../../../src/env/tools/LabEnvironment.java#L770).  Does **not**
hard-code any action semantic type so labs with non-default types (e.g. lab5's
`SetZ1Eff`/`SetZ1Ineff`) still resolve correctly.

---

### 2.2  `QLearner.java` — decomposed tabular Q-learning

**Package / extends:** `tools` / `cartago.Artifact`
[src/env/tools/QLearner.java#L1–L45](../../../src/env/tools/QLearner.java#L1).

**Hyperparameters (compile-time defaults via `parseDoubleProp`):**

| Sysprop | Default | Purpose |
|---|---|---|
| `reward.clip` | `50.0` | Per-step reward clamp `[-clip, +clip]` |
| `stereo.priorScale` | `1.0` | Multiplier on stereotype soft-prior in `greedyAction` |
| `stereo.priorDecayEpisodes` | `-1` (auto: `0.25×numEpisodes`) | Linear decay of `priorScale` to `priorDecayFloor` |
| `stereo.priorDecayFloor` | `0.0` | Asymptotic floor of prior weight |
| `stereo.priorFadeVisits` | `25` | Per-cell visit threshold above which prior is faded out |
| `stereo.energyPriorWeight` | `0.0` | Non-fading energy prior (lab5 only) |
| `reward.shaping` | `"none"` | `"pbrs"` activates policy-invariant potential shaping |
| `stereo.adaptiveTrust` | `false` | Per-action calibration multiplier on prior |
| `stereo.adaptiveTrust.minSamples` | `50` | Min observations before calibration is applied |
| `stereo.adaptiveTrust.floor` | `0.1` | Calibration multiplier floor |
| `run.seed` | `0L` | XORed into base seed via `mix64`; `0` = deterministic |

[src/env/tools/QLearner.java#L55–L100](../../../src/env/tools/QLearner.java#L55).

**RNG seeding:**  
`baseSeed = 42L ^ (useStereotypes ? 0x5A5A5A5A… : 0xA5A5A5A5…)`  
`if (RUN_SEED != 0L) baseSeed ^= mix64(RUN_SEED)`  
`this.rng = new Random(baseSeed)`  
[src/env/tools/QLearner.java#L221–L224](../../../src/env/tools/QLearner.java#L221).  
`mix64` (SplitMix64 finalizer) at [L158–L163](../../../src/env/tools/QLearner.java#L158).

**Key operations:**

| `@OPERATION` | Role | Key lines |
|---|---|---|
| `configureQLearner(goal, useStereotypes, paths, sunProb)` | Allocates `qTables[numZones][nStates][nActions]`, builds `StereotypeReasoner`, derives `strides[]`, `zoneLevelIndices[]`, `sunshineIndex` from slot registry; if `useStereotypes && priorScale>0` calls `initWithStereotypes()` | [L360–L440](../../../src/env/tools/QLearner.java#L360) |
| `encodeState(zoneLevels, sunshineRank, boolStateKeys, boolStateValues, stateVec)` | Allocates `Object[stateVecLen]`; fills zone-level slots via `zoneLevelIndices[]`; fills sunshine slot; fills boolean component slots via `reasoner.getWotStateToSvIndexMap()` | [L468–L510](../../../src/env/tools/QLearner.java#L468) |
| `getActionFromState(stateVec, explore, action)` | ε-greedy: `rng.nextDouble() < epsilon` → random from `computeApplicableActions`; else → `greedyAction(sIdx, applicable)` | [L667–L682](../../../src/env/tools/QLearner.java#L667) |
| `actionToWoT(action, wotType, value)` | Maps action index → `(wotSemanticType, boolean)` via `actionInfos[action]`; `wotType="none"` for DO_NOTHING | [L1555–L1565](../../../src/env/tools/QLearner.java#L1555) |
| `calculateQ(stateVec, action, nextStateVec)` | VDN joint bootstrap (`aStarNext = jointArgmaxAction(sNext)`); per-zone Bellman update with optional PBRS shaping; updates `visitCounts[sIdx][action]`; updates `lastBellmanDelta` | [L520–L620](../../../src/env/tools/QLearner.java#L520) |
| `observeForFaults(svBefore, actionIdx, svAfter, newlyDefective)` | Phase-2 instant fault detection (DEAD / INVERTED); structural guards: skip multi-zone Causes, skip IV-gated MEDIATES below IV_DETECT_MIN_SUN_RANK, skip contaminated zones | [L1079–L1200](../../../src/env/tools/QLearner.java#L1079) |
| `blacklistComponent(wotActionType, nRemoved)` | Marks BOTH ON and OFF actions of the component; marks contaminated zones; refuses to remove the last actuator action | [L1307–L1360](../../../src/env/tools/QLearner.java#L1307) |
| `warmRestart()` | Wipes Q-columns of blacklisted actions; decays "poisoned" states (states involving those actions); boosts ε to `FAULT_EPS_BOOST`; resets `currentEpisodeNum`, `convergenceCount`, `recoveryPolicy` | [L1363–L1425](../../../src/env/tools/QLearner.java#L1363) |
| `isTerminal(stateVec, terminal)` | Checks `effectiveGoal` (not nominal `goal`) — best-effort target after fault detection | [L1568–L1580](../../../src/env/tools/QLearner.java#L1568) |

**`greedyAction(stateIdx, applicable)`** (private):  
[src/env/tools/QLearner.java#L2540–L2600](../../../src/env/tools/QLearner.java#L2540)  
For each applicable action computes:
```
effectivePrior = priorWeight × priors[a] × calMul × cellMul
q = combinedQ(sIdx, a) + effectivePrior − [energyPrior if lab5]
```
where:
- `priorWeight` decays linearly from `STEREO_PRIOR_SCALE` to
  `STEREO_PRIOR_SCALE × PRIOR_DECAY_FLOOR` over `priorDecayEpisodes`
- `calMul ∈ [ADAPTIVE_TRUST_FLOOR, 1.0]` (adaptive trust, gated by `minSamples`)
- `cellMul = min(1, PRIOR_FADE_VISITS / visitCounts[sIdx][a])` (per-cell fade)

---

### 2.3  `BenchmarkLogger.java` — execution-phase metric accumulator

**Package / extends:** `tools` / `cartago.Artifact`
[src/env/tools/BenchmarkLogger.java#L1–L40](../../../src/env/tools/BenchmarkLogger.java#L1).

**Per-scenario metrics tracked:**

| Field | Meaning |
|---|---|
| `cumIlluminanceDeviation` | `Σ_t Σ_z |level_z(t) − target_z|` |
| `wastedSteps` | Actions leaving all zone levels and actuator states unchanged |
| `actuatorCyclingCount` | ON→OFF or OFF→ON reversals (proxy for wear) |
| `crossZoneInterferences` | Steps where an action moved a non-target zone away from target |
| `silentlyDropped` | W4: action dispatched but power-budget-dropped |
| `delayedEffectSteps` | W3: action with no immediate effect (dynamics) |
| `unmodelledZoneEffect` | W1/W6: cross-zone change unexplained by ontology |
| `conditionInversions` | W2: action sign opposite of ontology prediction |
| `topologyMismatches` | W5: `brick:feeds`-arc disagreement |
| `comfortDeviation` | W6: `Σ |temp − target|` |

[src/env/tools/BenchmarkLogger.java#L46–L72](../../../src/env/tools/BenchmarkLogger.java#L46).

**Key operations:** `beginScenario`, `recordStep`, `recordStepDetailRichV2`,
`endScenario`, `saveBenchmarkResults(OutFile)`, `saveStepLog(StepLogFile)`,
`openTraceJsonl` / `closeTraceJsonl` (rich per-step JSONL trace in
`benchmark/results/<profile>/<mode>/trace_bench_<mode>.jsonl`).

---

### 2.4  `StereotypeLearner.java` — online effect discovery

**Package / extends:** `tools` / `cartago.Artifact`
[src/env/tools/StereotypeLearner.java#L1–L44](../../../src/env/tools/StereotypeLearner.java#L1).

**Purpose:** Accumulates Welford online mean/variance for every `(action, state-slot)`
pair during training.  At training end, emits a Turtle file (`learned_stereotypes_<bool><QtSuffix>.ttl`)
describing discovered effects whose signal-to-noise ratio exceeds a threshold.

**Statistical thresholds (defaults):**

| Sysprop | Default | Meaning |
|---|---|---|
| `stereotype.learner.minSamples` | `30` | Minimum `n` per `(action, slot)` |
| `stereotype.learner.zCutoff` | `3.0` | Required `|mean|/SEM` ratio |
| `stereotype.learner.minEffect` | `0.05` | Required `|mean|` magnitude (rank units) |

[src/env/tools/StereotypeLearner.java#L47–L53](../../../src/env/tools/StereotypeLearner.java#L47).

**`observe(stateBefore, actionIdx, stateAfter)`** (called from `@do_step`):  
For each state-slot `s`: `delta = stateAfter[s] - stateBefore[s]`, then
Welford update of `count[a][s]`, `mean[a][s]`, `m2[a][s]`
[src/env/tools/StereotypeLearner.java#L107–L121](../../../src/env/tools/StereotypeLearner.java#L107).

**`saveLearnedStereotypes(filename)`**: tests each `(a, s)` with
`n ≥ minSamples`, `|mean|/SEM ≥ zCutoff`, `|mean| ≥ minEffect`; emits one
`learned:DiscoveredEffect` blank node per passing pair in Turtle
[src/env/tools/StereotypeLearner.java#L125–L185](../../../src/env/tools/StereotypeLearner.java#L125).

---

### 2.5  `jia/` — Jason Internal Actions

All three classes in `src/env/tools/jia/` extend
[`SystemProp`](../../../src/env/tools/jia/SystemProp.java) (abstract base) or delegate to it.

| ASL call | Java class | Behaviour |
|---|---|---|
| `tools.jia.system_prop(+Name, +Default, -Value)` | `system_prop.java` → `SystemProp` | `System.getProperty(name, default)` → unifies result as `StringTerm` |
| `tools.jia.system_prop_num(+Name, +Default, -Value)` | `system_prop_num.java` | Same but unifies a numeric term (used for `-Dadapt.episodes`, `-Dfault.recover.evalEpisodes`, etc.) |

`SystemProp.java` full implementation:
[src/env/tools/jia/SystemProp.java#L1–L44](../../../src/env/tools/jia/SystemProp.java#L1).

These JIAs are the **only bridge** between JVM system properties
(`-D` flags forwarded by Gradle's `build.gradle` from `config/run_config.json`) and
Jason agent beliefs.  Without them every profile switch requires mutating `.asl` files.

---

### 2.6  `OntologyArtifact.java` — ontology SPARQL access (rule-based mode)

Used **only** by the benchmark agent when `bench_mode("rule_based")`.  Loads one or
more TTL files into Apache Jena and exposes SPARQL-driven operations:
`discoverZones`, `discoverZoneQuantity`, `importLearnedStereotypes(path, nMerged)`.

`importLearnedStereotypes` merges a `learned_stereotypes_true<QtSuffix>.ttl` file
(written by `StereotypeLearner`) into the live ontology so SPARQL-driven rules
can exploit newly discovered effects in the rule-based comparison benchmark.

---

### 2.7  `DynamicsLearner.java` — Phase 3 response delay

Used only by `illuminance_controller_agent_dynamics.asl`.  Maintains per-action
Welford delay accumulators, materialized delay beliefs (`learned_delay_sec/2`),
and exploitation results.  Operations: `initDynamics`, `recordDelay`, `saveLearnedDynamics`,
`saveDelayTable`, `saveExploitResults`.

---

## 3. Step-by-Step Data Flow (Phase 1 Training, one `@do_step`)

> Source: `@do_step` plan at
> [src/agt/illuminance_controller_agent_ql.asl#L322–L357](../../../src/agt/illuminance_controller_agent_ql.asl#L322).
> Numbers in parentheses are the sequential operation numbers within that plan.

```
(1) SENSE
    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)
    [LabEnvironment]
       → SimulatorHttpClient.GET  http://<nodeRedHost>:<port>/was/rl/status
       ← JSON: {"Z1Level": 75.0, "Z2Level": 25.0, "Sunshine": 150.0,
                "Z1Light": false, "Z2Blinds": false, ...}
       → regex #Z<n>Level$ → discretize(v, lightBounds)
           e.g. 75.0 → rank 1  (lightBounds=[50,100,300])
       → discretize(Sunshine, sunshineBounds)
           e.g. 150.0 → rank 1 (sunshineBounds=[50,200,600])
       → boolean keys/values (all non-numeric fields)

(2) ENCODE
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)
    [QLearner]
       → Object[stateVecLen] initialised to 0
       → zoneLevelIndices[z] ← ZoneLevels[z]
       → sv[sunshineIndex]   ← SunshineRank
       → for each (key, val) in boolState:
             wotMap.get(key) → sv-index → sv[idx] ← 0|1
       → stateVec = [Z1Level, Z2Level, Z1Blinds, Z2Blinds, Z1Light, Z2Light, Sunshine, ...]

(3) TERMINAL CHECK
    isTerminal(StateVec, Terminal)
    [QLearner]
       → for each z: stateVec[zoneLevelIndices[z]] == effectiveGoal[z]?
       → if all match: Terminal=true → !run_episode recursion ends

(4) ACTION SELECTION  (if not Terminal)
    getActionFromState(StateVec, true, Action)   ← explore=true during training
    [QLearner]
       → sIdx = Σ stateVec[i] × strides[i]
       → applicable[] = computeApplicableActions(stateVec)
             [blacklisted? soft-mask? IV-satisfaction? DO_NOTHING always included]
       → if rng.nextDouble() < epsilon:
             Action = applicable[rng.nextInt(|applicable|)]   ← EXPLORE
         else:
             Action = greedyAction(sIdx, applicable)           ← EXPLOIT
                → combinedQ(sIdx, a) = Σ_z qTables[z][sIdx][a]
                → effectivePrior = priorWeight × priors[a] × calMul × cellMul
                → argmax  (combinedQ + effectivePrior)
                → ties broken by random pick from rng

(5) TRANSLATE
    actionToWoT(Action, WotType, WotValue)
    [QLearner]
       → actionInfos[Action].wotActionType  (e.g. "http://example.org/was#SetZ1Light")
       → actionInfos[Action].wotValue       (e.g. true)
       → if wotActionType == null: WotType = "none"  → DO_NOTHING

(6) EXECUTE  (if WotType != "none")
    invokeAction(WotType, WotValue)
    [LabEnvironment]
       → WotInputValidator.validateAction(wotSemanticType, value)
           [TD-driven: checks the action type exists and the payload type]
       → td.getFirstActionBySemanticType(wotSemanticType)
       → request = TDHttpRequest(form, TD.invokeAction)
       → payload = {"Z1Light": true}   (property name from ObjectSchema)
       → SimulatorHttpClient.POST  http://<nodeRedHost>:<port>/was/rl/action
           ← HTTP 200 OK

(7) WAIT
    .wait(action_delay_ms)    ← 65 ms default (QL agent) / 100 ms (bench agent)
    Node-RED simulator runs its compute_levels tick (period ≈ 50–200 ms per lab config)
    New illuminance values propagate through the flow

(8) OBSERVE NEXT STATE
    readLabStatus(ZoneLevels2, SunshineRank2, SKs2, SVs2)
    [LabEnvironment]
       → same HTTP GET / parse / discretize as step (1)

(9) ENCODE NEXT STATE
    encodeState(ZoneLevels2, SunshineRank2, SKs2, SVs2, NextState)
    [QLearner]
       → same slot-filling as step (2)

(10) BELLMAN UPDATE
    calculateQ(StateVec, Action, NextState)
    [QLearner]
       → sIdx  = stateVecToIndex(StateVec)
       → sNext = stateVecToIndex(NextState)
       → aStarNext = jointArgmaxAction(sNext)   ← VDN joint bootstrap
       → for each zone z:
             rz = computeZoneReward(z, stateVec, action, nextStateVec)
             rClipped = clip(rz, -REWARD_CLIP, +REWARD_CLIP)
             rForQ = rClipped / numZones
             if REWARD_SHAPING_PBRS:
                 F = γ × Φ_z(s') - Φ_z(s)
                 rForQ += F / numZones
             newQ = oldQ + α × (rForQ + γ × qTables[z][sNext][aStarNext] - oldQ)
             qTables[z][sIdx][action] = newQ
       → visitCounts[sIdx][action]++
       → lastBellmanDelta = max |newQ - oldQ| across zones

(11) STEREOTYPE LEARNING
    observe(StateVec, Action, NextState)
    [StereotypeLearner]
       → for each slot s:
             delta = NextState[s] - StateVec[s]
             Welford update: count[action][s]++; mean, m2

(12) CHECK TERMINAL + RECURSE
    isTerminal(NextState, Terminal)
    if (Terminal) → notifyGoalReached(EpN)
    if (not Terminal & Step+1 < MaxSteps) → !run_episode(EpN, Step+1)
```

---

## 4. Mermaid Data-Flow Diagram

```mermaid
flowchart TD
    A["lab_profiles.asl\nactive_profile/1\nlab_profile/13"] -->|profile fields| B

    subgraph "Jason BDI Agent (illuminance_controller_agent_ql.asl)"
        B["@apply_profile_then_start\n!profile_td / !profile_ont\n!profile_zone_targets"]
        B --> C["@start\nmakeArtifact LabEnvironment\nmakeArtifact QLearner\nmakeArtifact StereotypeLearner\nconfigureQLearner(Goal,Stereo,Paths,SunProb)\n!train(0)"]
        C --> D["@train / @run_episode\nsetRandomLabState or setScenarioLabState\nbeginEpisode"]
        D --> E["@do_step\n(per step, recursive)"]
    end

    E -->|readLabStatus| F["LabEnvironment\n(CArtAgO Artifact)"]
    F -->|HTTP GET /status| G["Node-RED Simulator\nports 1892–1900\n(compute_levels tick)"]
    G -->|JSON: ZnLevel, Sunshine, ZnLight, …| F
    F -->|zoneLevels, sunshineRank, boolStateKeys, boolStateValues| E

    E -->|encodeState| H["QLearner\n(CArtAgO Artifact)"]
    H -->|stateVec int[]| E

    E -->|getActionFromState\n(ε-greedy)| H
    H -->|Action int| E

    E -->|actionToWoT| H
    H -->|WotType, WotValue| E

    E -->|invokeAction WotType=value| F
    F -->|HTTP POST /action\n{Z1Light:true}| G
    G -->|HTTP 200| F

    E -->|".wait(delay_ms)"| G

    E -->|readLabStatus 2nd time| F
    E -->|encodeState 2nd time → NextState| H
    E -->|calculateQ StateVec Action NextState| H
    H -->|Bellman update qTables[z][sIdx][a]| H

    E -->|observe StateVec Action NextState| I["StereotypeLearner\n(CArtAgO Artifact)\nWelford accumulators"]

    subgraph "End of Training"
        J["@train_done\nsaveQTable / saveMetrics / saveIVStats\nsaveCoverage / saveFirstGoal"]
        K["StereotypeLearner\nsaveLearnedStereotypes → .ttl"]
    end

    H --> J
    I --> K

    subgraph "Phase-2 Adapt Extension"
        L["@do_step_adapt\nobserveForFaults(svBefore,action,svAfter)"]
        L -->|newlyDefective non-empty| M["blacklistComponent\nwarmRestart\n+detected(EpN)"]
        M -->|ε boost, Q wipe, episode reset| H
    end

    subgraph "Phase-3 Dynamics Extension"
        N["probe_all\nreadLabStatusTimed + invokeAction\n→ DynamicsLearner.recordDelay"]
        O["exploit_all\nbelieved_delay → planner\n→ invokeAction + measure actual TTR"]
    end

    F -.->|readLabStatusTimed: tick counter| N
    N --> O
```

---

## 5. Lab Profile Selection — `lab_profiles.asl`

**File:** [src/agt/lab_profiles.asl](../../../src/agt/lab_profiles.asl)  
**Schema** declared via comment [L1–L26](../../../src/agt/lab_profiles.asl#L1):

```prolog
lab_profile(Name,
            td(TdUrl),                    % WoT Thing Description (classpath:… or http://)
            ont(OntologyPaths),           % Jason list of TTL classpath resources
            scenarios(BenchScenariosFile),
            train_scenarios(TrainFile),
            sim_port(Port),               % Node-RED port (informational)
            light_bounds(LightRankBounds),    % [r1Upper, r2Upper, r3Upper] in lux
            sunshine_bounds(SunshineRankBounds),
            zone_targets(ZoneTargetList), % list of target(ZIdx, Rank) pairs
            sunshine_prob(SunProb),       % P(sunshine >= rank 1)
            weakness_flags(Flags),
            qtable_suffix(Suffix),
            training_params(NumEpisodes, EpsilonDecay))
```

**Active profile selector (single line to change):**
```prolog
active_profile("lab1").   % src/agt/lab_profiles.asl#L31
```

**Registered profiles (NEW era, clean ladder):**

| Profile | Port | Ontology files | ZoneTargets | NumEps | εDecay | Notes |
|---|---|---|---|---|---|---|
| `lab1` | 1892 | `building_1_trivial.ttl` | `[target(1,3)]` | 1000 | 0.9920 | 1 zone, 1 Causes lamp |
| `lab2` | 1893 | `building_2_intermediate.ttl` | `[target(1,3),target(2,3)]` | 2000 | 0.9960 | +Mediates blind |
| `lab3` | 1894 | `building_3_complex.ttl` | `[target(1,3),target(2,3)]` | 3000 | 0.9970 | +cross-zone spill, spotlight |
| `lab4` | 1897 | `building_4_smartplug.ttl` | `[target(1,3),target(2,3)]` | 3000 | 0.9970 | SmartPlug AND-gate |
| `lab5` | 1898 | `building_5_energy.ttl` | `[target(1,3),target(2,3)]` | 3000 | 0.9970 | Energy differentiation |
| `labmon` | 1899 | `building_6_monitor.ttl` | `[target(1,3)]` | 1500 | 0.9950 | Monitor fallback |
| `labmon2` | 1900 | `building_7_dualmonitor.ttl` | `[target(1,3),target(2,3)]` | 4000 | 0.9975 | Dual-zone monitor |
| `lab2_slow` | 1895 | `building_2_slow.ttl` | `[target(1,3),target(2,3)]` | 2000 | 0.9960 | Lab2 + blind delay |
| `lab3_slow` | 1896 | `building_3_slow.ttl` | `[target(1,3),target(2,3)]` | 3000 | 0.9970 | Lab3 + blind delay |

[src/agt/lab_profiles.asl#L226–L310](../../../src/agt/lab_profiles.asl#L226) (lab1–lab3);
[L311–L360](../../../src/agt/lab_profiles.asl#L311) (lab4/lab5);
[L361–L418](../../../src/agt/lab_profiles.asl#L361) (labmon/labmon2);
[L419–L460](../../../src/agt/lab_profiles.asl#L419) (slow labs).

**How the profile is consumed:**  
Each agent runs `@apply_profile_then_start` (or the `_adapt`/`_dynamics` variant) which calls the
`!profile_*` accessor plans [L858–L920](../../../src/agt/lab_profiles.asl#L858):

```prolog
@profile_td
+!profile_td(TdUrl)
    : active_profile(P) & lab_profile(P, td(TdUrl), _, _, _, _, _, _, _, _, _, _, _) <- true.
```

Fields consumed:

| Profile field | Accessor plan | Consumed by |
|---|---|---|
| `td(TdUrl)` | `!profile_td` | `makeArtifact("lab", "tools.LabEnvironment", [TdUrl])` |
| `ont(OntPaths)` | `!profile_ont` | `configureQLearner(…, OntPaths, …)` / `makeArtifact("ontology", OntPaths)` |
| `scenarios(File)` | `!profile_scenarios` | `getScenarioIds(File, Ids)` in bench agent |
| `train_scenarios(File)` | activates `train_scenarios_file/1` | `setScenarioLabState(File, Id mod TCount)` in training loop |
| `sim_port(Port)` | `!profile_sim_port` | Informational; actual URL derived from TD |
| `light_bounds(B)` | `!profile_light_bounds` | `configureDiscretization(LightBounds, SunshineBounds)` |
| `sunshine_bounds(B)` | `!profile_sunshine_bounds` | same |
| `zone_targets(L)` | `!profile_zone_targets` | `!derive_zone_goal` → `zone_goal/1` belief → `configureQLearner(Goal, …)` |
| `sunshine_prob(P)` | `!profile_sunshine_prob` | `configureQLearner(…, SunProb)` → `StereotypeReasoner` |
| `weakness_flags(F)` | `!profile_weakness_flags` | Bench agent `!fingerprint_weakness` guard |
| `qtable_suffix(S)` | `!profile_qtable_suffix` | Q-table/metrics filenames (e.g. `qtable_final_stereotypes_true_lab3.csv`) |
| `training_params(N, D)` | `!profile_training_params` | `-+num_episodes(N)` and `setEpsilonDecay(D)` on QLearner |

**Runtime override path:**  
`-Dactive.profile=lab2` (Gradle task property) → forwarded to JVM via `build.gradle`
`_httpKeys.each { systemProperty }` → `System.getProperty("active.profile")` →
`tools.jia.system_prop("active.profile", "", OverrideProfile)` in `@apply_runtime_overrides_ql`
[src/agt/illuminance_controller_agent_ql.asl#L82–L95](../../../src/agt/illuminance_controller_agent_ql.asl#L82) →
replaces the `active_profile/1` belief, so the same `.asl` binary serves all labs.

**`adapt_source/2` mapping** (Phase 2 only):  
Maps each faulty profile to its clean parent's `qtable_suffix`:
```prolog
adapt_source("lab2_f1dead", "_lab2").   % L818
adapt_source("lab3_f1inv",  "_lab3").   % L821
adapt_source("lab3_f1bdead","_lab3").   % L829
adapt_source("labmon_f1dead","_labmon").% L834
```
[src/agt/lab_profiles.asl#L817–L838](../../../src/agt/lab_profiles.asl#L817).  
Used by `@profile_adapt_source_ok` in adapt agent to construct the warm-load filename
`qtable_final_stereotypes_<bool><CleanSuffix>.csv`.

---

## 6. Node-RED Simulator Interface

The Node-RED flows (one per port, one per lab profile) expose three HTTP endpoints
derived from any TD `invokeAction` Form target by swapping the `/action` path suffix
(see `deriveSimulatorUrl` at
[src/env/tools/LabEnvironment.java#L770–L793](../../../src/env/tools/LabEnvironment.java#L770)):

| Endpoint | Method | Purpose | Called by |
|---|---|---|---|
| `/was/rl/status` | GET | Return current lab state as flat JSON (`ZnLevel`, `Sunshine`, `ZnLight`, `ZnBlinds`, …) | `readLabStatus`, `readLabStatusTimed`, `readEnergyCost` |
| `/was/rl/action` | POST | Toggle a single Boolean actuator (`{"Z1Light": true}`) | `invokeAction` via `performBooleanAction` |
| `/was/rl/setState` | POST | Pin all state fields to a scenario dict | `setLabStateFromMap` (called by `setRandomLabState`, `setScenarioLabState`) |
| `/was/rl/reset` | POST `{}` | Reset to default (random) state | `doReset` (called by `resetLab`, `calibrate`) |

The simulator tick period varies by lab (50 ms for fast custom labs, 200 ms for the clean
Phase-1 ladder).  The `action_delay_ms` belief in the agent (65 ms / 100 ms) must exceed
the tick period to ensure `readLabStatus` returns the **post-action** state; as noted in
audit Step 4 the 65 ms value for the QL agent is a known inconsistency.

---

## 7. Cross-Cutting Observations

1. **`lab_profiles.asl` is the single configuration authority (NEW era).**
   No agent hard-codes zone counts, port numbers, target ranks, or ontology paths.
   Adding a new lab requires one new `lab_profile/13` fact + the matching TTL + Node-RED
   flow; no agent code changes.

2. **The `@apply_profile_then_start` bridge pattern** (identical across `_ql`, `_bench`,
   `_adapt`, `_dynamics`) copies profile fields into legacy belief names (`lab_td`,
   `light_rank_bounds`, `zone_goal`, etc.) before the body of `!start` / `!start_adapt`
   / `!start_dynamics` runs.  This isolates the profile layer from the control layer.

3. **`tools.jia.system_prop`** is the **only channel** through which Gradle `-P` flags
   reach Jason beliefs at runtime.  If the JIA class is absent (ClassLoader race),
   each agent has a `@apply_runtime_overrides_*_fail` handler that logs a warning and
   falls back to the pre-patched `lab_profiles.asl` value.

4. **Decomposed Q-tables** (`qTables[numZones][nStates][nActions]`) and the
   **VDN joint bootstrap** (`aStarNext = jointArgmaxAction(sNext)`) mean the action is
   always selected globally (maximising total zone reward) while individual zones still
   have their own credit signal.  This is critical for multi-zone labs where a single
   action can improve Z1 while harming Z2.

5. **`StereotypeLearner.observe`** is a passive side-channel — it accumulates statistics
   every step but has **no effect on Q-updates or action selection**.  Its output
   (`learned_stereotypes_*.ttl`) is only consumed by the rule-based benchmark agent
   (via `importLearnedStereotypes`) to optionally enrich SPARQL-driven actuation.

6. **Phase-2 instant isolation** (`observeForFaults` → `blacklistComponent` → `warmRestart`)
   is structurally guarded (skip multi-zone Causes, skip IV-gated below sun threshold,
   skip contaminated zones) so false positives are prevented without statistical accumulation
   thresholds.  The headline metric is `RecoveryEpisodes = ReconvergeEpisode − DetectEpisode`
   written to `recovery_log_<bool>_<profile>.csv`.

7. **Phase-3 dynamics** does not touch Q-tables.  The QLearner artifact is instantiated
   only to enumerate the action space (`getNumActions`, `getActionMetadataForLearner`);
   all probing and exploitation is driven by `DynamicsLearner` and the `believed_delay` rule.

---

## 8. File Reference Index

| File | Audit item |
|---|---|
| [src/agt/lab_profiles.asl](../../../src/agt/lab_profiles.asl) | §5 — profile schema, all registered profiles, adapt_source/2, accessor plans |
| [src/agt/illuminance_controller_agent.asl](../../../src/agt/illuminance_controller_agent.asl) | §1.1 — demo agent |
| [src/agt/illuminance_controller_agent_ql.asl](../../../src/agt/illuminance_controller_agent_ql.asl) | §1.2, §3 — training agent + step trace |
| [src/agt/illuminance_controller_agent_bench.asl](../../../src/agt/illuminance_controller_agent_bench.asl) | §1.3 — benchmark agent |
| [src/agt/illuminance_controller_agent_adapt.asl](../../../src/agt/illuminance_controller_agent_adapt.asl) | §1.4 — Phase-2 adaptation |
| [src/agt/illuminance_controller_agent_dynamics.asl](../../../src/agt/illuminance_controller_agent_dynamics.asl) | §1.5 — Phase-3 dynamics |
| [src/env/tools/LabEnvironment.java](../../../src/env/tools/LabEnvironment.java) | §2.1, §3.1/3.6/3.8, §6 — WoT HTTP interface |
| [src/env/tools/QLearner.java](../../../src/env/tools/QLearner.java) | §2.2, §3.2–3.11 — Q-learning artifact |
| [src/env/tools/BenchmarkLogger.java](../../../src/env/tools/BenchmarkLogger.java) | §2.3 — metric accumulator |
| [src/env/tools/StereotypeLearner.java](../../../src/env/tools/StereotypeLearner.java) | §2.4, §3.11 — effect discovery |
| [src/env/tools/OntologyArtifact.java](../../../src/env/tools/OntologyArtifact.java) | §2.6 — rule-based SPARQL |
| [src/env/tools/DynamicsLearner.java](../../../src/env/tools/DynamicsLearner.java) | §2.7, §1.5 — delay learner |
| [src/env/tools/jia/SystemProp.java](../../../src/env/tools/jia/SystemProp.java) | §2.5 — system property JIA |
| [src/env/tools/jia/system_prop.java](../../../src/env/tools/jia/system_prop.java) | §2.5 — lowercase adapter |
| [src/env/tools/jia/system_prop_num.java](../../../src/env/tools/jia/system_prop_num.java) | §2.5 — numeric variant |
| [src/env/tools/SimulatorHttpClient.java](../../../src/env/tools/SimulatorHttpClient.java) | §2.1 (referenced) — fault-tolerant HTTP |
| [src/env/tools/WotInputValidator.java](../../../src/env/tools/WotInputValidator.java) | §2.1 (referenced) — TD-driven input gating |
