# MT-Esra: Stereotype-Guided Q-Learning for Smart Building Illuminance Control

A JaCaMo-based Multi-Agent System (MAS) that investigates whether **stereotype-guided Q-learning initialization** — using ontology-encoded domain knowledge — converges faster and performs better than standard Q-learning for smart building lighting control.

## Overview

This project implements three agent modes operating against a Node-RED simulated lab environment:

1. **Rule-based** — Ontology-driven dynamic control (BRICK + Elementary Ontology via SPARQL). All zone and actuator discovery is fully dynamic; no component names are hardcoded.
2. **Q-learning without stereotypes (`ql_false`)** — Standard tabular Q-learning with zero-initialized Q-tables.
3. **Q-learning with stereotypes (`ql_true`)** — Stereotype-guided Q-table initialization: impossible actions are pre-penalized using SPARQL reasoning over the lab ontology, and action masking prevents wasted exploration.

The research compares these three modes across **six weakness labs** (custom2–custom7), each injecting one systematic ontology gap into the simulator, to measure how well each agent mode detects and adapts to failures that the ontology does not predict.

## Architecture

### Agents (Jason / AgentSpeak)

| File | Role |
|------|------|
| `illuminance_controller_agent.asl` | Rule-based agent — fully dynamic zone/actuator discovery via OntologyArtifact |
| `illuminance_controller_agent_ql.asl` | Q-learning agent — switch `use_stereotypes(true/false)` to toggle stereotype-guided init |
| `illuminance_controller_agent_bench.asl` | Benchmark agent — runs fixed scenarios in one of three modes, records metrics |
| `lab_profiles.asl` | Lab Profile Registry — single source of truth for all lab configurations |

### Environment Artifacts (Java / CArtAgO)

| Class | Role |
|-------|------|
| `LabEnvironment` | Loads WoT Thing Description (TTL), dispatches HTTP actions, reads state from REST API. Supports `classpath:` URIs for bundled TD files. |
| `OntologyArtifact` | SPARQL reasoning over BRICK + Elementary Ontology KG. Provides dynamic zone discovery, quantity discovery, and best-action queries. Implements Cecconi et al. (2023) Component Stereotypes. |
| `QLearner` | Decomposed tabular Q-learning for multi-zone control. State space and action space are fully data-driven from the ontology via `StereotypeReasoner`. |
| `StereotypeReasoner` | Plain Java (used by `QLearner`). Queries lab-ontology.ttl via Apache Jena SPARQL to compute Q-table initialization penalties and runtime action masks. |
| `StereotypeLearner` | Observes (state, action, next-state) triples during training. Uses Welford's online algorithm to surface ontology gaps as learned Turtle effect files. |
| `BenchmarkLogger` | Records per-scenario execution-phase metrics and weakness-classification counts. Writes `benchmark_results_<mode>.csv`. |

## Lab Profiles

All environment-specific parameters live in `src/agt/lab_profiles.asl`. Switching labs requires a single line change:

```prolog
active_profile("custom2").  % change this to switch labs
```

| Profile | Simulator port | Weakness | Description |
|---------|---------------|----------|-------------|
| `custom` | 1881 | none | 2-zone baseline lab (spotlight + radiators) |
| `custom_full_train` | 1881 | none (ablation) | Same 2-zone lab trained over the fixed train-scenario cycle; Q-tables get a `_full` suffix so they do not overwrite random-start Q-tables (`ql_full_train` ablation) |
| `custom2` | 1882 | W1 | Missing-stereotype: CorridorLight bleeds +30 lux to all zones (undeclared in ontology) |
| `custom3` | 1883 | W2 | Context-dependent inversion: Blind_Z2 effect inverts sign at Sunshine >= 500 lux |
| `custom4` | 1884 | W3 | Dynamics: per-lamp ramp + residual illuminance + hysteresis |
| `custom5` | 1885 | W4 | Shared resource: 7-unit power cap silently drops lowest-priority lamp |
| `custom6` | 1886 | W5 | Dynamic topology: Partition23 connection toggles every 5 ticks |
| `custom7` | 1887 | W6 | Multi-objective heat: every ON lamp raises zone temperature +0.1 C/tick |

## State Space

The state vector is data-driven from `wot-mappings.ttl`. For the custom 2-zone lab:

```
[Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Spotlight, Sunshine]
```

For the 4-zone weakness labs (custom2–custom7), the state vector is extended with additional zone levels, lights, blinds, a spotlight cooldown flag, and a corridor light flag.

### Illuminance Discretization

Continuous lux values are mapped to ranks using configurable bounds (default: `[75, 200, 400]` lux):

| Rank | Lux range | Description |
|------|-----------|-------------|
| 0 | < 75 lux | Very dark |
| 1 | 75–200 lux | Dim |
| 2 | 200–400 lux | Medium |
| 3 | >= 400 lux | Bright |

## Q-Learning Configuration

Hyperparameters are set as beliefs in `illuminance_controller_agent_ql.asl`:

| Belief | Default | Description |
|--------|---------|-------------|
| `num_episodes(N)` | 2500 | Training episodes |
| `max_steps_per_episode(N)` | 20 | Steps budget per episode |
| `action_delay_ms(N)` | 65 ms | Delay between actions (must exceed simulator tick + jitter) |
| alpha (learning rate) | 0.1 | Q-table update step size |
| gamma (discount factor) | 0.9 | Future reward weight |
| epsilon (exploration) | 0.3 -> 0.01 | Epsilon-greedy decay (x0.995 per episode) |

## Benchmark Metrics

The benchmark agent (`BenchmarkLogger`) records per-scenario:

| Metric | Description |
|--------|-------------|
| `GoalReached` | Whether all zone targets were satisfied before the step budget ran out |
| `Steps` | Total actions dispatched |
| `CumIlluminanceDeviation` | Sum over steps of sum over zones of abs(level - target) |
| `WastedSteps` | Actions that left the full state vector unchanged |
| `ActuatorCyclingCount` | ON->OFF or OFF->ON reversals (proxy for wear) |
| `CrossZoneInterferences` | Steps where an action moved a non-target zone away from its target |
| `TotalEnergyCost` | Cumulative energy cost reported by the simulator |
| `SilentlyDropped` | Steps where a dispatched actuator command was silently budget-dropped without taking effect (W4) |
| `DelayedEffectSteps` | Steps where an action had no immediate illuminance change despite the actuator bit flipping (W3) |
| `UnmodelledZoneEffect` | Steps where a zone changed unexpectedly vs ontology prediction — accumulates both W1 (hidden bleed) and W6 (w6_unmodelled fingerprint) counts |
| `ConditionInversions` | Steps where the observed zone Δ was opposite in sign to the ontology prediction (W2) |
| `TopologyMismatches` | Steps where a zone outside the action's declared stereotype footprint changed unexpectedly (W5) |
| `ComfortDeviation` | Accumulated absolute temperature excess above the 22 °C comfort target across all zones and steps (W6) |

### Weakness Classification (W1–W6)

The benchmark agent classifies each step against ontology predictions:

| Tag | Weakness | Counter |
|-----|----------|---------|
| W1 | Unmodelled cross-zone effect | `unmodelledZoneEffect` |
| W2 | Condition inversion | `conditionInversions` |
| W3 | Delayed effect (no immediate state change) | `delayedEffectSteps` |
| W4 | Silently dropped action (power budget) | `silentlyDropped` |
| W5 | Topology mismatch vs ontology feeds-arc | `topologyMismatches` |
| W6 | Thermal comfort: fingerprint fires to `unmodelledZoneEffect`; continuous deviation tracked separately in `comfortDeviation` | see notes above |

> **Note on W6:** W6 is detected via two paths. The `w6_unmodelled` fingerprint from `classifyWeaknesses()` is merged into the `UnmodelledZoneEffect` column (alongside W1). The continuous thermal overload is accumulated independently in `ComfortDeviation` (°C excess per step, via `recordComfortDeviation`).

### Additional Benchmark Output Files

In addition to `benchmark_results_<mode>.csv`, the benchmark agent writes a per-step debug log:

| File | Description |
|------|-------------|
| `benchmark_results_<mode>.csv` | Per-scenario summary metrics (see table above) |
| `bench_step_log_<mode>.csv` | Per-step debug log: one row per (scenario, run, step) with zone levels, action dispatched, wasted flag, and weakness tags |

## Training Output Files

The Q-learning agent (`taskQl` / `runFullSweep` training phase) writes the following artefacts to the project root:

| File pattern | Description |
|---|---|
| `qtable_initial_stereotypes_<bool>[<suffix>].csv` | Q-table snapshot immediately after initialization (before any training) — combined Q1+Q2 |
| `qtable_initial_stereotypes_<bool>[<suffix>]_zone<N>.csv` | Per-zone initial Q-table |
| `qtable_final_stereotypes_<bool>[<suffix>].csv` | Final trained Q-table after all episodes — combined Q1+Q2 |
| `qtable_final_stereotypes_<bool>[<suffix>]_zone<N>.csv` | Per-zone final Q-table |
| `metrics_stereotypes_<bool>[<suffix>].csv` | Per-episode training metrics: `Episode, Steps, RewardZ1, RewardZ2, GoalReached, Epsilon, WastedByPenalty, WastedByNoEffect` plus summary lines |
| `iv_stats_stereotypes_<bool>[<suffix>].json` | Per-(action, state-slot) IV effectiveness statistics accumulated during training |
| `coverage_stereotypes_<bool>[<suffix>].csv` | Per-(state, action) visit counts over the full training run |
| `first_goal_stereotypes_<bool>[<suffix>].csv` | First episode in which the goal was reached for each starting state |
| `learned_stereotypes_<bool>[<suffix>].ttl` | Turtle file of discovered effects emitted by `StereotypeLearner` (Welford Δ-mean above Z-score threshold) |

`<bool>` is `true` or `false` (stereotype mode). `<suffix>` is the `qtable_suffix` from the active lab profile (e.g., `_custom2` for profile `custom2`; empty string for profile `custom`).

## Project Structure

```
MT-Esra/
|-- build.gradle                             # Gradle build + tasks (task, taskQl, taskBench, runFullSweep)
|-- task.jcm                                 # JaCaMo project file -- rule-based agent
|-- task_ql.jcm                              # JaCaMo project file -- Q-learning agent
|-- task_bench.jcm                           # JaCaMo project file -- benchmark agent
|-- gradlew / gradlew.bat                    # Gradle wrapper
|-- run_full_project.ps1                     # End-to-end automation (training -> benchmark -> analysis)
|-- analysis/
|   `-- sweep_report.py                      # Aggregates sweep results into charts and tables
|-- benchmark/
|   |-- scenarios.json                       # 20 held-out scenarios for 2-zone lab
|   |-- scenarios_custom2..7.json            # Scenarios for each weakness lab
|   |-- train_scenarios.json                 # Training scenario cycle (2-zone)
|   |-- train_scenarios_custom2.json         # Training scenario cycle (4-zone)
|   `-- results/                             # Output directory for runFullSweep artefacts
|-- simulator/
|   |-- simulator_flow.json                  # Original 2-zone simulator (port 1880)
|   |-- simulator_flow_custom.json           # Custom 2-zone lab (port 1881)
|   |-- simulator_flow_custom2..7.json       # 4-zone weakness labs (ports 1882-1887)
|   `-- generate_flows.ps1                   # Script to regenerate weakness-lab flows
`-- src/
    |-- agt/
    |   |-- illuminance_controller_agent.asl          # Rule-based agent
    |   |-- illuminance_controller_agent_ql.asl       # Q-learning agent
    |   |-- illuminance_controller_agent_bench.asl    # Benchmark agent
    |   `-- lab_profiles.asl                          # Lab Profile Registry
    |-- env/tools/
    |   |-- LabEnvironment.java              # WoT interaction artifact
    |   |-- OntologyArtifact.java            # SPARQL reasoning artifact
    |   |-- QLearner.java                    # Decomposed Q-learning artifact
    |   |-- StereotypeReasoner.java          # Ontology-based Q-table init (plain Java)
    |   |-- StereotypeLearner.java           # Online effect learning artifact
    |   `-- BenchmarkLogger.java             # Benchmark metrics artifact
    `-- resources/
        |-- lab-ontology.ttl                 # BRICK + Elementary Ontology definitions
        |-- lab-ontology-custom2.ttl         # Extended ontology for 4-zone labs
        |-- wot-mappings.ttl                 # WoT state slot registry (2-zone)
        |-- wot-mappings-custom2.ttl         # WoT state slot registry (4-zone)
        `-- interactions-lab-custom*.ttl     # W3C WoT Thing Descriptions per lab
```

## Running the Project

### Prerequisites

- Java 11 or higher
- [Node-RED](https://nodered.org/) (for the simulator)
- Python 3 with `matplotlib` (optional, for analysis charts)

### Quick start — rule-based agent (no simulator needed for original lab)

```bash
# Windows
gradlew.bat task

# Linux / macOS
./gradlew task
```

### Q-learning agent (requires Node-RED simulator on port 1881)

1. Start the custom-lab simulator:
   ```
   node-red --port 1881 simulator/simulator_flow_custom.json
   ```
2. Edit `use_stereotypes(true/false)` in `src/agt/illuminance_controller_agent_ql.asl`.
3. Run:
   ```bash
   gradlew.bat taskQl
   ```

### Benchmark agent (requires Node-RED simulator)

1. Start the appropriate simulator (see [Lab Profiles](#lab-profiles) for ports).
2. Set `bench_mode` in `src/agt/illuminance_controller_agent_bench.asl` to `"rule_based"`, `"ql_false"`, or `"ql_true"`.
3. For Q-learning modes, ensure the corresponding Q-table CSV (`qtable_final_stereotypes_<bool><suffix>.csv`) exists.
4. Run:
   ```bash
   gradlew.bat taskBench
   # or override mode without editing the file:
   gradlew.bat taskBench -Pmode=ql_true
   ```

### Full sweep (all profiles x all modes)

```bash
gradlew.bat runFullSweep
# Subset:
gradlew.bat runFullSweep -Pprofiles=custom2,custom4 -Pmodes=ql_true
```

Results are archived under `benchmark/results/<profile>/<mode>/`.

### End-to-end automation

`run_full_project.ps1` orchestrates the entire pipeline: starts all six weakness-lab simulators, trains Q-tables for each profile x stereotype mode, runs the full benchmark sweep, and generates the analysis report.

```powershell
# Recommended for development / smoke testing (~6-8 h total):
.\run_full_project.ps1 -RunMode dev

# Paper-quality run (~50-60 h total):
.\run_full_project.ps1 -RunMode paper

# Skip training if Q-tables already exist:
.\run_full_project.ps1 -SkipTraining
```

### Analysis

```bash
python analysis/sweep_report.py
# or with custom paths:
python analysis/sweep_report.py --root benchmark/results --out analysis/out
```

Outputs under `analysis/out/`:
- `summary_table.csv` — one row per (profile, mode) cell
- `weakness_heatmap.csv` / `weakness_heatmap.png` — weakness fire counts per lab
- `learning_curve_<profile>.png` — per-profile reward curves across modes
- `fire_density_<profile>.png` — per-profile per-step weakness fire density

## Environment Selection

To switch the rule-based agent between environments, edit the `@start` plan in `src/agt/illuminance_controller_agent.asl`:

```prolog
// Custom lab (port 1881, spotlight + radiators) -- default:
LabURL = CustomURL;

// Original simulated lab (fetched from GitHub, port 1880):
// LabURL = SimulatedURL;

// Physical lab:
// LabURL = RealURL;
```

For the Q-learning and benchmark agents, change `active_profile/1` in `src/agt/lab_profiles.asl`.

## Zone Targets

Default targets for the 2-zone lab (edit `zone_target/2` beliefs in `illuminance_controller_agent.asl` or `active_profile` in `lab_profiles.asl`):

| Zone | Target rank | Target lux |
|------|-------------|------------|
| Zone 1 | 3 | >= 400 lux |
| Zone 2 | 2 | 200–400 lux |

For the 4-zone weakness labs, zone targets are `[3, 2, 3, 2]` (zones 1–4).

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `com.github.GiugAles:jacamo` | SS2025 | JaCaMo MAS framework |
| `com.github.GiugAles:jacamo-hypermedia` | SS2025-1 | Hypermedia-driven agent actions |
| `com.github.Interactions-HSG:wot-td-java` | master-SNAPSHOT | W3C WoT Thing Description parsing |
| `org.apache.jena:jena-arq` | 4.10.0 | Apache Jena SPARQL 1.1 engine |
| `org.apache.httpcomponents.client5:httpclient5` | 5.0 | HTTP client for simulator REST API |
| `com.google.guava:guava` | 23.5-jre | Utility library |

## References

- Cecconi et al., "Reasoning about Physical Processes in Buildings through Component Stereotypes", CPS-IoT Week 2023.
- [BRICK Schema](https://brickschema.org/)
- [W3C Web of Things (WoT) Thing Description](https://www.w3.org/TR/wot-thing-description/)
- [JaCaMo MAS Framework](https://jacamo-lang.github.io/)
- [Node-RED](https://nodered.org/)