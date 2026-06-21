# Phase 4 — Hidden Dependencies, Energy-Aware Goals, and the KG-vs-LLM Comparison

**Project:** MT-Esra (Knowledge-Guided RL for Building Automation)
**Stack:** JaCaMo (Jason AgentSpeak BDI + CArtAgO) · Q-Learning · Knowledge Graph / Stereotypes · Node-RED labs
**Branch:** `phase4-dependencies-energy`
**Builds on:** Phase 1 "clean lab ladder" (`lab1`/`lab2`/`lab3`), which already compares a KG-primed Q-learner (`ql_true`) against a tabula-rasa Q-learner (`ql_false`).

---

## 1. What changed conceptually

Phase 1 proved that KG-priming **accelerates learning in clean labs**. Phase 2 added **fault detection**, Phase 3 added **temporal-dynamics learning**. Phase 4 adds the two capabilities the advisor asked for and frames the overarching comparison against an LLM:

1. **Hidden dependencies (lab4 — smart plug).** The Zone-1 ceiling lamp is wired behind a *smart plug*. The lamp emits light **only when both its own switch AND the plug are ON**. The dependency is *known in the knowledge graph* (`ws:powerGates` / `ws:poweredBy`). The KG-primed learner enables the plug first; the tabula-rasa learner must discover the dependency by trial and error (and is punished by the no-effect penalty for switching the lamp while the plug is off).

2. **Energy-aware goals (lab5 — efficient vs inefficient lamps).** Each zone has **two directly-actionable lamps with identical brightness (+400 lux) but different energy cost** (efficient = 1 unit/tick, inefficient = 4 units/tick), encoded as `ws:energyCost` in the KG. The goal is energy-aware: *"both zones bright AND steady-state power ≤ budget."* Energy is **not** part of the Q-reward; only the KG-primed agent — through a new **non-fading energy prior** — prefers the efficient lamp (or the zero-energy blinds when daylight suffices). The tabula-rasa agent is energy-blind.

3. **The overarching KG-vs-LLM framing.** An **offline, reproducible LLM baseline** ([analysis/phase4_llm_baseline.py](../analysis/phase4_llm_baseline.py)) plays the same scenarios with a *general-knowledge* controller that sees commonsense device facts (a lamp brightens a room, a blind admits free daylight) but **not** the KG's hidden facts (no wiring diagram, no per-device energy datasheet). This operationalises the thesis claim: *the KG informs the agent better than an LLM is informed by its general knowledge.*

> **The most important comparison remains within-lab `ql_true` vs `ql_false`** (KG-primed vs tabula-rasa Q-learning), measured to statistical significance across seeds. The LLM baseline is the *framing* layer on top.

### Separation of concerns

Unlike Phases 2–3, Phase 4 **does** touch the two core Java files — but **only additively, gated, and backward-compatibly** (explicitly approved):

- Every new behaviour is **off by default**. The energy prior weight defaults to `0.0`; the power-gate query returns nothing unless a KG declares `ws:powerGates`. Labs 1–4 are bit-for-bit unaffected even when the energy knob is set, because only lab5's KG declares `ws:energyCost`.
- No Phase 1/2/3 lab profile, ontology, simulator flow, scenario set, Gradle task, runner default, analysis script, or workflow is modified. Phase 1–3 results remain reproducible.

---

## 2. The two new labs

Both labs fork the Phase 1 `lab3` template (two zones, target rank 3 = "bright", deterministic Node-RED physics, **no** `Math.random` in the per-tick update, sun ∈ {0, 100, 400, 900}). Shared physics constants: `AMBIENT=25`, `LAMP_PRIMARY=+400` (own zone), `LAMP_CROSS=+150` (adjacent zone), `BLIND_PRIMARY=0.50·sun`, `BLIND_CROSS=0.40·sun`, `SPOTLIGHT=+150` (both zones). Discretisation bounds `[50,100,300]` → rank 0/1/2/3; target rank 3 means zone level ≥ 300.

### 2.1 lab4 — smart-plug dependency (port 1897, suffix `_lab4`)

| Artifact | File |
|---|---|
| Knowledge graph | [src/resources/building_4_smartplug.ttl](../src/resources/building_4_smartplug.ttl) |
| WoT Thing Description | [src/resources/interactions-lab4.ttl](../src/resources/interactions-lab4.ttl) |
| Node-RED simulator | [simulator/simulator_flow_lab4.json](../simulator/simulator_flow_lab4.json) |
| Benchmark scenarios | [benchmark/scenarios_lab4.json](../benchmark/scenarios_lab4.json) |
| Training scenarios | [benchmark/train_scenarios_lab4.json](../benchmark/train_scenarios_lab4.json) |

**State vector (9 slots):** `[Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Spotlight, PlugZ1, Sunshine]`. The new slot is `PlugZ1` (index 7). 4096 reachable states.

**Hidden dependency (AND-gate):** the Zone-1 lamp's contribution is

```
z1lamp_on = Z1Light AND PlugZ1
z1_level   = 25 + (z1lamp_on ? 400 : 0) + (Z2Light ? 150 : 0)
                + (Z1Blinds ? 0.50·sun : 0) + (Z2Blinds ? 0.40·sun : 0) + (Spotlight ? 150 : 0)
```

Zone-2's lamp is directly actionable (no plug). Energy per tick = `(z1lamp_on?1) + (Z2Light?1) + (Spotlight?2)`; the plug draws nothing on its own.

**How the KG encodes it:** `building_4_smartplug.ttl` declares a `ws:SmartPlugStereotype` (so the plug is *discovered* as an actuator), and the dependency triple

```turtle
lab:SmartPlug_Z1   ws:powerGates  lab:CeilingLight_Z1 .
lab:CeilingLight_Z1 ws:poweredBy  lab:SmartPlug_Z1 .
```

### 2.2 lab5 — energy-aware (port 1898, suffix `_lab5`)

| Artifact | File |
|---|---|
| Knowledge graph | [src/resources/building_5_energy.ttl](../src/resources/building_5_energy.ttl) |
| WoT Thing Description | [src/resources/interactions-lab5.ttl](../src/resources/interactions-lab5.ttl) |
| Node-RED simulator | [simulator/simulator_flow_lab5.json](../simulator/simulator_flow_lab5.json) |
| Benchmark scenarios | [benchmark/scenarios_lab5.json](../benchmark/scenarios_lab5.json) |
| Training scenarios | [benchmark/train_scenarios_lab5.json](../benchmark/train_scenarios_lab5.json) |

**State vector (10 slots):** `[Z1Level, Z2Level, Z1Eff, Z1Ineff, Z2Eff, Z2Ineff, Z1Blinds, Z2Blinds, Spotlight, Sunshine]`. Two lamps per zone. 8192 reachable states.

**Identical brightness, different cost:** within a zone, `anyLamp = Eff OR Ineff` contributes `+400` once (turning *both* on wastes energy for no extra light). Cross-zone `+150` from `anyLamp`. Energy per tick:

```
power = (Z1Eff?1) + (Z1Ineff?4) + (Z2Eff?1) + (Z2Ineff?4) + (Spotlight?2)
```

**How the KG encodes it:** each lamp instance carries a `ws:energyCost` datatype property (efficient = 1, inefficient = 4, spotlight = 2, blinds = 0):

```turtle
lab:EffLight_Z1   ws:energyCost 1 .
lab:IneffLight_Z1 ws:energyCost 4 .
```

**Energy budget:** [benchmark/scenarios_lab5.json](../benchmark/scenarios_lab5.json) adds an `energyBudget` field (default **2**) per scenario. A budget of 2 is satisfied by two efficient lamps (1 + 1) or by free daylight (blinds = 0); it is *violated* by any inefficient lamp (4), a redundant double-lamp, or the spotlight (+2 on top).

---

## 3. New KG vocabulary

| Predicate | Type | Lab | Meaning |
|---|---|---|---|
| `ws:powerGates` | object property | lab4 | `plug ws:powerGates lamp` — the lamp emits light only when the plug's state slot is ON |
| `ws:poweredBy` | object property | lab4 | inverse of `ws:powerGates` (documentary) |
| `ws:plugPowerSwitch` | process var | lab4 | the plug's manipulated variable (so the `SmartPlugStereotype` is discoverable) |
| `ws:energyCost` | datatype property (`owl:DatatypeProperty`) | lab5 | per-actuator energy draw used by the energy prior |

Both KGs are **self-contained** — they parse standalone (no shared lab-ontology / WoT-mappings import), as asserted by the regression test in §6.

---

## 4. Core Java changes (additive, gated, backward-compatible)

### 4.1 `StereotypeReasoner.java` — discover the plug gate and the energy cost

[src/env/tools/StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java):

- **`ActionInfo.energyCost`** — new `double` field, default `0.0`.
- **Actuator-discovery query** gains an `OPTIONAL { ?comp ws:energyCost ?energyCost }`; the value is parsed onto `ActionInfo.energyCost` (max across rows). Absent ⇒ stays `0.0`.
- **`POWER_GATE_QUERY` + `discoverPowerGates()`** — for every `gate ws:powerGates lamp`, the gated lamp's **ON** action is marked **IV-gated on the plug's state slot**: `hasIV = true`, `ivStateVecIndex = plugSlot (7)`, `ivMinRank = 1`. This **reuses the existing instrumental-variable (IV) machinery** verbatim — no rule was changed. The lamp-on action is now penalised when the plug is off and rewarded when it is on; the plug-on action (which has no IV) keeps its unconditional enabler bonus, so the agent learns *enable the plug first*.
- The constructor calls `discoverPowerGates()` after `discoverActuators()`. With no `ws:powerGates` triples the query is empty and nothing changes (labs 1–3).

### 4.2 `QLearner.java` — the non-fading energy prior

[src/env/tools/QLearner.java](../src/env/tools/QLearner.java):

```java
// Static knob, default 0.0 (OFF). build.gradle forwards -Pstereo.energyPriorWeight.
ENERGY_PRIOR_WEIGHT = parseDoubleProp("stereo.energyPriorWeight", 0.0);

// Inside greedyAction(), a persistent NON-FADING term (unlike the decaying KG prior):
if (useStereotypes && ENERGY_PRIOR_WEIGHT > 0
        && actionInfos != null && a < actionInfos.length && actionInfos[a] != null
        && actionInfos[a].wotValue                 // an ON action
        && actionInfos[a].energyCost > 0) {
    q -= ENERGY_PRIOR_WEIGHT * actionInfos[a].energyCost;
}
```

This is the **only** way the KG-primed agent prefers the efficient lamp, because energy is deliberately **not** in the Q-reward (`computeZoneReward` is unchanged). The term is **triple-gated**: `useStereotypes` (so `ql_false` never sees it), `ENERGY_PRIOR_WEIGHT > 0`, and `energyCost > 0`. At weight 2.0 the inefficient lamp (cost 4) is penalised −8 and the efficient lamp (cost 1) only −2, so the agent prefers efficiency without ever being told "energy is in the reward." Because labs 1–4 have no `ws:energyCost`, the term is inert there even when the knob is set.

### 4.3 Wiring

- [build.gradle](../build.gradle) forwards `stereo.energyPriorWeight` to the JVM.
- [config/run_config.json](../config/run_config.json): the global default `learning.stereo_energy_prior_weight = 0.0`, and a new **`phase4` run-mode profile** sets `learning_overrides.stereo_energy_prior_weight = 2.0` (3000 episodes, KG prior + PBRS + adaptive-trust on, same timing as `phase1`). [run_full_project.ps1](../run_full_project.ps1) passes the knob through to **both** training and benchmarking.
- [src/agt/lab_profiles.asl](../src/agt/lab_profiles.asl): `lab4`/`lab5` profile entries (ports 1897/1898, targets rank 3, `training_params(3000, 0.9970)`).
- `lab4`/`lab5` are **not** in the default `$TrainProfiles` set, so a plain `phase1` run is unchanged; they are selected per-cell with `-OnlyProfiles`.

---

## 5. Analysis scripts

### 5.1 `analysis/phase4_energy.py` — the one new metric

[analysis/phase4_energy.py](../analysis/phase4_energy.py) computes **lab5 energy-budget compliance**, the only metric not already produced by `sweep_report.py`. For each replica (seed) it reads the **final** `ActuatorState` from `bench_step_log_<mode>.csv`, computes the deterministic steady-state power from the KG power formula, and scores:

- `goal_rate` — fraction of scenarios reaching the goal.
- `energy_compliance` — fraction with **GoalReached AND power ≤ budget** (higher better).
- `mean_steady_power` — average final power (lower better).
- `over_budget_rate` — fraction over budget (lower better).

It then runs the same statistics as Phase 1/3 — paired bootstrap CIs, Wilcoxon signed-rank, Cliff's delta, BH-FDR — across seeds for `ql_true − ql_false`, writing `phase4_energy_ci.csv` and `phase4_energy_paired.csv`. lab4 (no budget) collapses `energy_compliance` to `goal_rate`.

### 5.2 `analysis/phase4_llm_baseline.py` — the offline LLM baseline

[analysis/phase4_llm_baseline.py](../analysis/phase4_llm_baseline.py) replays the *same* `scenarios_lab4.json` / `scenarios_lab5.json` with a **general-knowledge controller** (an offline LLM proxy) that:

- sees commonsense device facts and live brightness feedback, but **not** the KG's hidden wiring/energy facts;
- discovers the lab4 plug only by feedback (a "switch did nothing" observation);
- treats the lab5 efficient and inefficient lamps as **indistinguishable** (an unbiased coin), because brightness alone cannot tell them apart.

It emits `phase4_llm_summary.csv` (mirroring the energy columns) and `phase4_llm_prompts_<profile>.jsonl` (the exact natural-language prompts, for auditing or replay against a real model via `--backend cached --responses <jsonl>`). It is fully offline and deterministic — **never wired to a live API in CI** — so the baseline is reproducible.

---

## 6. Regression test

[src/test/java/tools/Phase4KgDiscoveryTest.java](../src/test/java/tools/Phase4KgDiscoveryTest.java) (JUnit 5, runs in the normal `gradlew test`):

- **`lab4SmartPlugGatesTheZ1Lamp`** — loads `building_4_smartplug.ttl` and asserts the Z1 lamp's ON action is IV-gated on slot 7 with `ivMinRank == 1`, the plug's ON action is *not* IV-gated (it is the enabler), and lab4 `energyCost == 0`.
- **`lab5ParsesPerActuatorEnergyCost`** — loads `building_5_energy.ttl` and asserts `SetZ1Eff` cost 1, `SetZ1Ineff` cost 4, `SetSpotlight` cost 2, inefficient > efficient.

Both tests pass; the full pre-existing suite stays green (no regressions).

---

## 7. The Phase 4 workflow

[.github/workflows/phase4.yml](../.github/workflows/phase4.yml) forks `phase1.yml` exactly (same `setup → train → bench → aggregate` DAG, same JitPack-retry / Node-RED 4 / free-disk-space hardening) with Phase-4 defaults and an extended aggregate job.

**Four jobs:**

1. **setup** — compile once, cache `build/classes`, materialise the profile and seed matrices.
2. **train** — matrix `profile × stereo(true,false) × seed`; each cell runs `run_full_project.ps1 -RunMode phase4 -OnlyProfiles <p> -OnlyStereo <s> -RunSeed <n> -SkipBenchmark`. Uploads the trained Q-tables.
3. **bench** — matrix `profile × mode(rule_based,ql_false,ql_true) × seed`; benchmarks against the trained Q-tables, uploads `bench_step_log_*` / `benchmark_results_*`.
4. **aggregate** — reconstructs the `results_seed<N>/<profile>/<mode>/` layout and runs **three** analyses:
   - `sweep_report.py --seeds-mode` → learning-speed headline (AUC, first-goal, redundant actions, goal rate, energy);
   - `phase4_energy.py` → lab5 energy-budget compliance;
   - `phase4_llm_baseline.py` → the offline LLM baseline.
   It writes a job summary, uploads `phase4-consolidated`, and (optionally) publishes to the `results` branch.

Every `(profile × stereo × seed)` and `(profile × mode × seed)` cell runs **concurrently**, so wall-clock is set by the slowest single cell, not the cell count.

---

## 8. How to run it via GitHub Actions

1. Push the `phase4-dependencies-energy` branch (and, if you want it dispatchable from the default branch, merge it so `phase4.yml` is on `main` — GitHub only lists `workflow_dispatch` workflows that exist on the default branch).
2. In the repo, open **Actions → "Phase 4 (Dependencies + Energy, KG vs LLM framing)" → Run workflow**.
3. Inputs (all have sensible defaults):

   | Input | Default | Notes |
   |---|---|---|
   | `profiles` | `lab4,lab5` | which Phase-4 labs to run |
   | `seeds` | `1,2,3,4,5,6,7,8,9,10` | 10 seeds for confirmatory power (Wilcoxon reaches p<0.05 only at n ≥ 6). Use `1,2,3,4,5` for a faster replication. |
   | `run_mode` | `phase4` | 3000 episodes, KG arm energy-prior 2.0. `dev` (50 ep) for a quick plumbing check. |
   | `run_llm_baseline` | `true` | also compute the offline LLM baseline |
   | `publish_results` | `true` | push the consolidated outputs to the `results` branch |

4. Click **Run workflow**.

**Quick first run:** set `seeds = 1,2,3` to confirm the whole pipeline end-to-end in a fraction of the time, then run the full `1..10` for the statistics.

---

## 9. How long it takes

GitHub-hosted runners execute the matrix in parallel, so the wall-clock is dominated by **one** training cell plus queueing, not the total number of cells.

| Stage | Cells (10 seeds, 2 labs) | Per-cell | Notes |
|---|---|---|---|
| setup | 1 | ~3–6 min | compile + cache |
| train | 2 labs × 2 stereo × 10 seeds = **40** | ~40–60 min | `phase4` = 3000 episodes; 180-min timeout/cell |
| bench | 2 labs × 3 modes × 10 seeds = **60** | ~5–15 min | 90-min timeout/cell |
| aggregate | 1 | ~5–10 min | three analyses + publish |

**Expected wall-clock:** roughly **1.5–2.5 hours** end-to-end at 10 seeds, subject to runner availability (GitHub free tier limits concurrency, which can serialise some cells). A `seeds = 1,2,3` smoke typically finishes in **under an hour**. A `run_mode = dev` dispatch finishes in **~20–30 minutes**.

---

## 10. What results to expect

**Headline (within-lab `ql_true` vs `ql_false`, paired across seeds):**

- **lab4 (dependency):** the KG-primed agent reaches the first goal **sooner** and with **fewer redundant actions** — it enables the plug before switching the lamp, while the tabula-rasa agent wastes actions toggling a dead lamp. Final goal-rate converges to parity (both eventually solve it); the *speed* and *redundancy* gaps are the finding.
- **lab5 (energy):** the KG-primed agent achieves **higher energy-budget compliance** and **lower steady-state power** at equal goal-rate — it picks the efficient lamp / free daylight, while the tabula-rasa agent is energy-blind and frequently lands on the inefficient lamp.

**KG-vs-LLM framing (offline baseline, current numbers from [analysis/phase4_llm_baseline.py](../analysis/phase4_llm_baseline.py)):**

| Profile | goal_rate | energy_compliance | mean_steady_power | mean_redundant |
|---|---|---|---|---|
| lab4 | 1.00 | 1.00 | 1.56 | 0.375 |
| lab5 | 1.00 | **0.556** | 3.39 | 0.06 |

Reading: the general-knowledge LLM proxy *reaches* the goal but, on lab5, complies with the energy budget only **~56%** of the time — it cannot tell the efficient lamp from the inefficient one without the KG. The KG-primed `ql_true` agent is expected to reach **~100%** compliance, which is the quantified "the KG informs the agent better than the LLM's general knowledge" result. On lab4 the LLM eventually discovers the plug via feedback, so the differentiator there is the **redundant-action** count, not goal-rate.

> These LLM numbers are deterministic and reproducible; the `ql_true`/`ql_false` numbers come from the actual CI run and are confirmed with Wilcoxon p-values, bootstrap CIs, and BH-FDR q-values.

---

## 11. Where to find the results

After a dispatch completes:

- **Job summary** — the run's **Summary** page renders the key tables inline (`learning_speed_tests.csv`, `paired_tests.csv`, `phase4_energy_paired.csv`, `phase4_energy_ci.csv`, `phase4_llm_summary.csv`, `summary_table_ci.csv`).
- **`phase4-consolidated` artifact** (Actions → run → Artifacts) — the full `analysis/out/**`, per-seed benchmark trees, Q-tables, learned TTLs, and raw CSVs.
- **`results` branch** (if `publish_results = true`) — a versioned snapshot published by [scripts/version_artifacts.ps1](../scripts/version_artifacts.ps1).

Key files inside `analysis/out/`:

| File | Content |
|---|---|
| `learning_speed_tests.csv` | AUC / first-goal / episodes-to-threshold, `ql_true − ql_false` paired |
| `paired_tests.csv` | redundant-action and same-goal-rate paired tests |
| `phase4_energy_ci.csv` | per profile/mode compliance + power with 95% CI |
| `phase4_energy_paired.csv` | `ql_true − ql_false` energy-compliance, Wilcoxon p + Cliff's δ + BH q |
| `phase4_llm_summary.csv` | offline LLM baseline (goal-rate, compliance, power, redundant) |
| `phase4_llm_prompts_<profile>.jsonl` | the exact prompts the LLM proxy saw (auditable) |
| `summary_table_ci.csv` | multi-seed summary with 95% CIs |

---

## 12. Local smoke (optional)

A fast end-to-end plumbing check (no statistics) without GitHub Actions:

```powershell
# 50-episode dev run for one lab (needs Node-RED + Java 21 via gradlew):
./run_full_project.ps1 -RunMode dev -OnlyProfiles lab5 -RunSeed 1 -SkipPreflight

# then score the produced flat-layout CSVs:
python analysis/phase4_energy.py --root . --profile lab5 --out analysis/out

# and the offline LLM baseline (no simulator needed):
python analysis/phase4_llm_baseline.py --profile lab4 --profile lab5 --emit-prompts
```

The full statistical result requires the multi-seed GitHub Actions run in §8.

---

## 13. File manifest

**New files**

- `src/resources/building_4_smartplug.ttl`, `src/resources/interactions-lab4.ttl`, `simulator/simulator_flow_lab4.json`
- `src/resources/building_5_energy.ttl`, `src/resources/interactions-lab5.ttl`, `simulator/simulator_flow_lab5.json`
- `benchmark/scenarios_lab4.json`, `benchmark/train_scenarios_lab4.json`, `benchmark/scenarios_lab5.json`, `benchmark/train_scenarios_lab5.json`
- `analysis/phase4_energy.py`, `analysis/phase4_llm_baseline.py`
- `src/test/java/tools/Phase4KgDiscoveryTest.java`
- `.github/workflows/phase4.yml`
- `docs/PHASE4.md` (this file)

**Modified files (additive, backward-compatible)**

- `src/env/tools/StereotypeReasoner.java` — `ActionInfo.energyCost`, `ws:energyCost` discovery, `POWER_GATE_QUERY` + `discoverPowerGates()`
- `src/env/tools/QLearner.java` — `ENERGY_PRIOR_WEIGHT` non-fading energy term in `greedyAction`
- `src/env/tools/LabEnvironment.java` — two backward-compatible robustness fixes required by lab5's renamed actuators (see §14)
- `build.gradle` — forward `stereo.energyPriorWeight`
- `config/run_config.json` — global default + `phase4` run-mode profile + metadata block + sim/port/suffix maps
- `src/agt/lab_profiles.asl` — `lab4`/`lab5` profile entries
- `run_full_project.ps1`, `run_full_project_parallel.ps1` — `lab4`/`lab5` simulators, energy-prior passthrough, `phase4` run mode

---

## 14. `LabEnvironment.java` robustness fixes (required by lab5's renamed actuators)

lab5 is the first lab to **rename its lamp actuators** away from the Phase-1 `SetZ1Light`/`SetZ2Light` convention (to `SetZ1Eff`/`SetZ1Ineff`/`SetZ2Eff`/`SetZ2Ineff`) and the first to add a per-scenario **`energyBudget`** field. Two places in `LabEnvironment.java` had baked-in assumptions that those changes broke. Both fixes are additive and **bit-for-bit backward-compatible with labs 1–4**.

### 14.1 Generic simulator-URL derivation (the critical one)

`deriveSimulatorUrl(path)` recovers the simulator base URL (for `/reset` and `/setState`) from the Thing Description by taking any action's invoke-form target (which points at `…/was/rl/action`) and swapping the suffix. The original code looked up a **hardcoded** semantic type:

```java
// BEFORE — breaks on any lab without a SetZ1Light action
this.td.getFirstActionBySemanticType("http://example.org/was#SetZ1Light");
```

labs 1–4 all expose a `SetZ1Light` action, so this worked. lab5 has **no** `SetZ1Light` (its lamps are `SetZ1Eff`/`SetZ1Ineff`/…), so the lookup returned empty → the `/setState` and `/reset` URLs could not be derived → **both calls were silently skipped (a logged warning, no failure)**. The consequence was severe and silent: during **training** the simulator was never reset between episodes, and during **benchmarking** the per-scenario start state was never applied — so every lab5 episode ran from stale simulator state. The fix derives the URL from *any* action, independent of naming:

```java
// AFTER — naming-agnostic; every action's form targets …/was/rl/action
private String deriveSimulatorUrl(String path) {
    for (ActionAffordance action : this.td.getActions()) {
        Optional<Form> f = action.getFirstFormForOperationType(TD.invokeAction);
        if (f.isPresent()) {
            return f.get().getTarget().replaceAll("/action$", path);
        }
    }
    return null;
}
```

Because every action in every lab's TD points at the same `…/was/rl/action` base, picking the first action yields an identical base URL to the old `SetZ1Light` lookup for labs 1–4 — so their training/benchmark behaviour is unchanged, while lab5 (and any future lab with custom actuator names) now resets and applies scenario state correctly. Verified end-to-end: a lab5 dev smoke shows zero "could not derive" warnings, `setState → 200` POSTs in both training and benchmark logs, populated `bench_step_log` rows carrying the energy actuators, and realistic per-scenario energy (vs. the pre-fix symptom of `Steps=0`, `GoalReached=1` for every scenario and a runaway `TotalEnergyCost`).

### 14.2 `energyBudget` is scenario metadata, not a state key

`extractScenarioKV()` translates a scenario JSON object into simulator state keys, validating each against the Thing Description. lab5 scenarios add an `energyBudget` field (consumed *only* by the bench-time compliance metric in `phase4_energy.py`, never sent to the simulator). It is now skipped alongside the other non-state keys (`id`, `description`, `comment`), so the WoT input validator no longer rejects a lab5 scenario. Labs 1–4 carry no `energyBudget`, so nothing changes for them.
