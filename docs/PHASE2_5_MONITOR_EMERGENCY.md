# Phase 2.5 — The Monitor Emergency-Fallback Lab

> **What this adds.** A new component **stereotype** (a computer *monitor*) and a
> new single-zone lab (`labmon`) that tests whether a physics/KG-primed agent,
> when its primary task lamp dies, recognises an **unconventional fallback light
> source** (the monitor) faster than a tabula-rasa agent. This extends the
> Phase 2 fault-recovery story (`docs/PHASE1_TO_PHASE2_CHANGES.md` §§18–21) with
> a qualitatively new *kind* of recovery lever: a device whose light output is a
> **side-effect**, not its primary purpose.

## 1. Motivation and research question

The advisor's Phase-2 framing is: *the agent should recognise that an action in
its policy produced unexpected behaviour, discard that artefact (blacklist the
component), and re-learn — faster with physics knowledge.* Phase 2 so far
recovered by falling back on **other lights** (a cross-zone lamp, a shared
spotlight, a blind). Those are all *intended* lighting devices.

A **monitor** is different. Its **primary** output is displayed information; it
also emits a **weak** amount of light as a **side-effect** of its backlight.
Nobody lights a room with a monitor on purpose. The research question is:

> **In an emergency where the normal lighting options fail, can the system fall
> back on the monitor as an unconventional light source — and does the
> KG-primed agent discover this fallback faster than the tabula-rasa agent?**

This is a clean test of whether *physics knowledge generalises to using a device
outside its primary role*. The KG advertises the monitor as a (weak) Causes
light; the tabula-rasa agent has no such hint and must discover the monitor's
usefulness by trial and error.

## 2. The new stereotype — `ws:MonitorStereotype`

Declared in the new self-contained ontology
[src/resources/building_6_monitor.ttl](../src/resources/building_6_monitor.ttl).
The monitor's mechanism has **multiple dependent variables** — its primary
output (displayed information) and a **side-effect** (light):

```turtle
ws:pm_monitor_operation a elem:PhysicalMechanism ;
    elem:hasManipulatedVariable ws:monitor_power_input ;      # electricity IV (like a lamp)
    elem:hasDependentVariable   ws:displayed_information ;    # PRIMARY output (NOT Illuminance)
    elem:hasDependentVariable   elem:luminiscence ;           # SIDE-EFFECT (Illuminance)
    elem:increases              elem:luminiscence .           # Causes: unconditional +light
```

The `StereotypeReasoner` actuator-discovery query keeps only the dependent
variable whose quantity is `qudtqk:Illuminance`, so the monitor contributes
**exactly one ON/OFF lighting action** even though it "does several things" — the
`ws:displayed_information` DV is filtered out. This is how "a monitor is not a
lamp, but it *can* brighten the room" is expressed in the KG: a Causes light with
a primary purpose elsewhere.

## 3. The lab — `labmon` (single zone, two Causes actuators, port 1899)

| Actuator | Stereotype | Lux | Reward-energy cost | Role |
|---|---|---:|---:|---|
| `Z1Light` (primary lamp) | `LampIncandescentStereotype` | +400 | **0 (free)** | the normal task light |
| `Z1Monitor` (monitor) | **`MonitorStereotype` (new)** | +290 | **4/tick (costly)** | light is a *side-effect*; wasteful to use |

Deterministic physics (no sunshine term, no blinds, no cross-zone):

$$Z1 = 25 + (\text{Z1Light}\,?\,400) + (\text{Z1Monitor}\,?\,290)$$

State vector `[Z1Level, Z1Light, Z1Monitor]` = `4·2·2` = **16 states**.
Goal = rank 3 (>300 lux), `light_bounds [50,100,300]`.

### Why it is a *well-posed* emergency

The faulty variant `labmon_f1dead` kills the primary lamp
(`z1l ? 400` → `z1l ? 0`). The rank-3 reachability table (deterministic, so it
holds for every episode):

| Actuator set | Lux | Rank | Note |
|---|---:|:--:|---|
| primary lamp on | 425 | **3** | clean optimum — one action, FREE |
| **monitor on** | **315** | **3** | the ONLY surviving rank-3 path — one action, COSTLY |

Both levers reach rank 3 in a **single action**, so they are explored
symmetrically (no multi-step path to get stuck in). The difference is **cost**:
the lamp is free, the monitor is costly (`ws:rewardEnergyCost 4`). Two properties
make this a **Tier-1 confirmatory** recovery cell (in the sense of
`docs/PHASE1_TO_PHASE2_CHANGES.md` §21.7.0):

1. **The monitor is *necessary*.** After the lamp is blacklisted, the monitor is
   the only remaining rank-3 lever. The agent *must* use it.
2. **The survivor path is *deterministic* (sun-independent).** `monitor` = 315 >
   300 for every episode, so a recovery-**speed** contrast is well-posed — the
   cell is added to `_WELL_POSED_RECOVERY` in
   [analysis/phase2_recovery.py](../analysis/phase2_recovery.py).

The monitor is dominated in the **clean** lab (it costs more than the free lamp
for the same rank-3 result), so it stays off the clean greedy path — exactly the
"not a primary lighting method / not something we *willingly* use" property from
the research question — yet it is the essential rescue lever in the emergency.

### Why a *cost signal* is required (and how it stays isolated)

There is a subtlety that the first design missed. With a purely **energy-free**
reward, the monitor path (315 lux, rank 3) is *also* a valid rank-3 path in the
**clean** lab — the physics is identical, only the lamp is killed by the fault.
So an energy-free agent has **no reason to prefer the lamp** and may satisfy the
goal with the monitor instead, never exercising the lamp — in which case the dead
lamp is **never detected**. Two early smokes confirmed this exactly: even a fully
converged energy-free clean policy reached the goal with the monitor and produced
`detect = -1` (the Q-table showed the lamp ON action under-explored, its Q stuck
far below the monitor's).

The fix follows the research question's own wording — the monitor is *"not the
desired effect that we usually or **willingly** use"*. Unwillingness is a **cost**.
We therefore attach a **reward-side** energy cost to the monitor (4/tick), leaving
the lamp free (0). This is a new ontology property `ws:rewardEnergyCost`,
subtracted from the Q-reward (once per step) while an actuator is ON. Three
cooperating pieces make the free lamp the robust clean optimum:

1. **Per-step reward cost** (`ws:rewardEnergyCost`, both arms): the monitor costs
   4/tick, so its recovered value is strictly below the free lamp's.
2. **Symmetric pessimistic Q-init** (`reward.energyInitWeight`, both arms): the
   reward clip (200) masks the cost at the *goal-reaching* step, so two
   one-action rank-3 levers would otherwise be an entrenchment lottery. The
   initial Q-table therefore seeds any cost-carrying actuator pessimistically
   (monitor start ≈ −25, lamp ≈ +22 for the KG arm), so the agent *begins with*
   the lamp and holds it. This is applied **identically to both arms**, so it
   does not bias the KG-vs-vanilla contrast — it only breaks the symmetry toward
   the (correct) free lever.
3. **All-off episode start** (flow reset): each episode starts with both
   actuators off, so the agent faces the lamp-vs-monitor choice every episode and
   the free lamp is exercised (and, in the faulty lab, its death detected)
   instead of being hidden behind a random already-on monitor.

Consequently:

- In the **clean** lab both arms strictly prefer the free lamp (a one-action,
  zero-cost rank-3 solution), so the lamp is on the greedy path and its death is
  **detected** on the first faulty step.
- In the **emergency** the lamp is gone, so the costly monitor path is the only
  way to the goal and the agent uses it despite the cost.

`ws:rewardEnergyCost` is **self-gating**: it is distinct from lab5's
`ws:energyCost` (a KG *prior*), only `building_6_monitor.ttl` declares it, and
`StereotypeReasoner` parses it as `0.0` everywhere else — so the Q-reward and the
Q-init of *every other lab (including lab5) are bit-for-bit unchanged*. Because
the cost and the init bias are applied to **both** arms, detection stays
arm-symmetric; the KG advantage remains purely a **recovery-speed** effect (the
`MonitorStereotype` prior lets the KG agent re-find the monitor faster once the
lamp is blacklisted).


`ws:rewardEnergyCost` is **self-gating**: it is distinct from lab5's
`ws:energyCost` (a KG *prior*), only `building_6_monitor.ttl` declares it, and
`StereotypeReasoner` parses it as `0.0` everywhere else — so the Q-reward of
*every other lab (including lab5) is bit-for-bit unchanged*. Because it is in the
**reward** (not the KG prior) it applies to **both** arms, keeping detection
arm-symmetric. The KG advantage remains purely a **recovery-speed** effect.

### How the KG is expected to help

Both arms **detect** the dead lamp identically (detection is not KG-gated — the
frozen clean policy exercises the lamp, sees no rank response, and blacklists it).
The differentiator is **recovery speed**: the KG arm's `MonitorStereotype` and
backup-lamp stereotype seed **positive priors** on the monitor and backup ON
actions, so after the lamp is blacklisted the KG agent immediately treats the
monitor as a candidate light and finds the `{monitor, backup}` combination
faster. The tabula-rasa agent must rediscover the monitor's usefulness from
scratch.

## 4. Files created / changed

**Created**
- [src/resources/building_6_monitor.ttl](../src/resources/building_6_monitor.ttl) — self-contained ontology: monitor stereotype + mechanism, primary lamp, backup lamp, 4-slot state registry.
- [src/resources/interactions-labmon.ttl](../src/resources/interactions-labmon.ttl) — WoT Thing Description (port 1899, three action affordances + Status).
- [simulator/simulator_flow_labmon.json](../simulator/simulator_flow_labmon.json) — clean Node-RED flow (deterministic three-actuator physics).
- [benchmark/scenarios_labmon.json](../benchmark/scenarios_labmon.json), [benchmark/train_scenarios_labmon.json](../benchmark/train_scenarios_labmon.json) — held-out / held-in scenarios.
- [src/test/java/tools/MonitorKgDiscoveryTest.java](../src/test/java/tools/MonitorKgDiscoveryTest.java) — JUnit regression gate (ontology + actuator discovery + state-vector shape).

**Edited**
- [src/env/tools/StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java) — parse the new `ws:rewardEnergyCost` property into `ActionInfo` (0.0 when absent).
- [src/env/tools/QLearner.java](../src/env/tools/QLearner.java) — (a) `computeZoneReward` subtracts the reward-side energy cost of ON actuators once per step; (b) a symmetric pessimistic Q-init bias (`reward.energyInitWeight`, default 12) on any actuator carrying `ws:rewardEnergyCost`. Both are self-gating (inert for every lab that declares no cost) and applied to both arms.
- [src/agt/lab_profiles.asl](../src/agt/lab_profiles.asl) — `labmon` clean profile + `labmon_f1dead` faulty profile + `adapt_source`.
- [config/run_config.json](../config/run_config.json) — clean-lab maps (`labmon` → port 1899, flow, suffix, dim 3) + phase2 maps (`labmon_f1dead` → parent `labmon`, faulty flow, dim 3).
- [simulator/generate_faulty_flows.ps1](../simulator/generate_faulty_flows.ps1) — `labmon_f1dead` dead-lamp recipe.
- [analysis/phase2_recovery.py](../analysis/phase2_recovery.py) — `labmon_f1dead` added to `_WELL_POSED_RECOVERY`.
- [run_full_project.ps1](../run_full_project.ps1) — `labmon` in known profiles, qtable-suffix map, and simulator map (port 1899).

The change is strictly **additive**: because the `lab1`–`lab5` state-slot
registries are per-lab and self-contained, adding the monitor slot inside
`building_6_monitor.ttl` changes the state space of **only** `labmon`; and the
new `ws:rewardEnergyCost` term is self-gating, so the reward of every existing
lab is unchanged. Every existing lab (and its warm-startable Q-tables) is
untouched.

## 5. Validation

### 5.1 Unit tests (green)

`MonitorKgDiscoveryTest` (run via `./gradlew.bat test`) asserts:
- all three Causes actuators (`SetZ1Light`, `SetZ1Monitor`, `SetZ1Backup`) are discovered as ON/OFF pairs;
- the monitor is a **Causes** actuator (`hasIV == false`) — its multiple DVs collapse to exactly one lighting action;
- the state vector is length 4 (32 states) and each actuator toggles a distinct bit.

The full existing suite still passes (no regressions) — the new self-contained
lab breaks no test that asserts on other labs' sizes.

### 5.2 Local end-to-end smoke

### 5.2 Local end-to-end smoke

A full clean-train → adapt cycle was run locally for both arms (seed 1, phase1
episode budget). Both arms behave exactly as designed:

| Arm | Clean greedy at all-off | Detect | Reconverge | Recovered goal-rate | Recovered via |
|---|---|:--:|:--:|:--:|---|
| **KG (`ql_true`)** | `SetZ1Light=ON` (Q 203 ≫ monitor 53) | ✅ ep 0 (first faulty step) | 53 ep | **1.0** | the monitor |
| **vanilla (`ql_false`)** | `SetZ1Light=ON` (Q 203 ≫ monitor 20) | ✅ ep 0 (first faulty step) | 59 ep | **1.0** | the monitor |

- **Both arms use the free lamp in the clean lab** (the cost + init bias work
  symmetrically), so both **detect** the dead lamp on the first faulty step —
  `observeForFaults: SetZ1Light flagged DEFECTIVE … [dead/no-response]`.
- **Both arms recover by falling back on the monitor** (`goalRate = 1.0`): after
  the lamp is blacklisted (action space 5 → 3), the only surviving rank-3 lever
  is the monitor, and both re-learn to use it.
- **Directionally, the KG arm re-aligns faster** (53 vs 59 episodes at this
  single seed) — the physics prior on the monitor's light-raising effect helps
  the KG agent re-find the fallback sooner. The confirmatory CI (below, n = 10)
  provides the statistical contrast.

This confirms the core research claim: *the system falls back on the monitor as
an unconventional light source in the emergency, and the KG-primed agent does so
at least as fast as tabula-rasa.*


## 6. Confirmatory CI run

<!-- CI_RESULTS -->

## 7. Analysis wiring

`labmon_f1dead` is a member of `_WELL_POSED_RECOVERY`, so the two-tier recovery
analysis (`analysis/phase2_recovery.py`) treats it as a **confirmatory** cell iff
both arms reach the goal after recovery (per-arm greedy goal-rate ≥ 0.5) — which
the deterministic `monitor+backup` path guarantees. Its paired `ql_true` vs
`ql_false` `RecoveryEpisodes` contrast enters the Tier-1 BH-FDR family alongside
the lamp/blind cells.
