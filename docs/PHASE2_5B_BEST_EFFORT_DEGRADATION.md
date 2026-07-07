# Phase 2.5b — Proof-Gated Best-Effort Degradation (replacing the cost hack)

> **What this changes.** This supersedes the *cost-based* monitor design of
> [docs/PHASE2_5_MONITOR_EMERGENCY.md](PHASE2_5_MONITOR_EMERGENCY.md). The
> monitor is no longer an equally-capable-but-*costly* rank-3 lever. It is now a
> genuinely **weak** light that can only reach **rank 2** — one rank short of the
> goal. When the primary lamp dies the goal becomes **unreachable**, and the
> agent's job changes from "recover to the goal" to "**prove** the goal is
> unreachable, get **as close as possible**, and **tell the user**." No reward
> cost, no Q-init bias, no artificial "unwillingness" — the fallback behaviour is
> gated on a *deterministic proof* and fires **only in the faulty lab, only when
> the goal cannot be reached**.

---

## 1. Why we abandoned the cost design

The previous design (Phase 2.5) made the monitor reach the **same** rank as the
lamp (rank 3, 315 lux) but attached a per-tick **reward cost**
(`ws:rewardEnergyCost 4`) plus a symmetric pessimistic **Q-init bias** so the
free lamp would stay the clean optimum and its death would be exercised and
detected. It worked and was CI-green, but the justification was unconvincing:

- **"The monitor is costly" is a fiction.** A screen backlight does not draw
  meaningfully more power than a ceiling lamp; the number `4/tick` was chosen to
  win the entrenchment lottery, not measured from anything. The advisor's framing
  is that the monitor is *weak / not a real light*, **not** that it is expensive.
- **It smuggled the answer into the reward.** Making the lamp win required a
  hand-tuned cost *and* a hand-tuned init bias. That is a lot of machinery whose
  only purpose is to force a symmetry break that the physics should provide.

The refined research question (user's words):

> *"Only in the faulty labs and only when the desired rank cannot be reached, the
> system adapts and tries to find the option that gets closest to the goal."*

That is a **graceful-degradation** requirement, not a cost requirement. The clean
design expresses it directly.

---

## 2. The new design in one paragraph

Make the monitor **physically weak**: `+260` lux → `285` = **rank 2** in the
clean lab (the goal is rank 3, `>300`). Now the lamp (`+400` → `425` = rank 3) is
the **only single-action rank-3 lever**, so *both* arms must learn to use it with
**no** cost signal and **no** init bias — and therefore its death is exercised and
detected for free. In the faulty lab the lamp is dead, so **rank 3 is genuinely
unreachable**. After blacklisting the lamp, the adapt agent runs a **deterministic
reachability probe** over the surviving actuators; if it *proves* the nominal goal
cannot be reached, it lowers the **effective** goal to the closest achievable rank
(rank 2, via the monitor), **notifies the user**, and re-learns toward that
best-effort target. In clean labs and in any faulty lab where the goal is still
reachable, the probe is a **no-op** and behaviour is byte-for-byte unchanged.

---

## 3. The two decisions you made

1. **Probe form → the general enumerate-and-argmin probe.** Rather than a
   monitor-specific shortcut, the probe enumerates every combination of the
   surviving (non-blacklisted) boolean actuators, drives the simulator into each,
   reads the achieved rank, and keeps the combination whose rank is **closest to
   the nominal goal** (argmin `|rank − goal|`, ties broken toward the higher
   rank). This is general enough to handle future sun-mediated or multi-actuator
   degraded cells, not just the single-monitor case.
2. **`labmon` → reworked in place.** We did not fork a new lab. The existing
   `building_6_monitor.ttl` / `simulator_flow_labmon.json` / `labmon_f1dead`
   recipe were edited so the monitor is weak and the cost machinery is gone.

---

## 4. The key insight: "get as close as possible" is already in the reward

The zone reward (`QLearner.computeZoneReward`) already contains a term that
rewards *closing the rank gap*:

```
reward += gapChange * 40      // gapChange = (prev rank-distance) − (new rank-distance)
```

So moving from rank 0 → rank 2 is **already** rewarded even if rank 3 is never
reached. What blocked "settle for the best reachable rank" was **not** the
progress term — it was three terms keyed to the **exact nominal target**:

| Term | Keyed to | Effect when the goal is unreachable |
|---|---|---|
| terminal `+200` (once) | exact target rank | never fires → no strong attractor at the best-effort rank |
| hold `+5`/step | exact target rank | never fires → no reason to *stay* at rank 2 |
| no-effect `−10`, stagnation `−5` | sitting below target | **punishes** sitting at the best reachable rank |

The fix is therefore **not** a reward rewrite (that would change every lab). It is
a single indirection: introduce an **`effectiveGoal`** that defaults to a clone of
the nominal `goal`, and have `isTerminal`, the terminal/hold bonus, and the PBRS
shaping read `effectiveGoal` instead of `goal`. Lower `effectiveGoal` **only** when
the probe proves the nominal goal unreachable. Because `effectiveGoal == goal`
everywhere else, all currently-validated reachable-recovery cells are unchanged.

---

## 5. Mechanism (code walk-through)

### 5.1 `effectiveGoal` indirection — `QLearner.java`

- New field `int[] effectiveGoal`, set to `goal.clone()` in `configureQLearner`.
- `isTerminal`, `computeZoneReward` (terminal/hold/penalty branches) and the PBRS
  potential now read `effectiveGoal[z]` instead of `goal[z]`.
- The **progress** term (`gapChange*40`) is unchanged — it always pulls toward
  higher ranks, which is exactly the "get closer" behaviour we want.

### 5.2 The reachability probe — `QLearner.java` @OPERATIONs

| Operation | What it does |
|---|---|
| `beginReachabilityProbe(numCombos)` | Groups surviving non-blacklisted actuators by WoT action type into `{onIdx, offIdx}` pairs; returns `2^k` combinations (capped at `2^16`). |
| `getProbeCombo(comboIdx, actionList)` | Returns the action indices that realise combination `comboIdx` (bit set → ON index, else OFF index). |
| `recordProbeRank(stateVec, zone)` | After the agent drives the lab into a combo and reads the state, records the achieved rank; keeps argmin `|rank − goal|` (ties → higher rank). |
| `finishReachabilityProbe(zone, bestRank, degraded)` | If `bestRank < goal[zone]`, sets `effectiveGoal[zone] = bestRank` and returns `degraded = true`; otherwise no-op. |
| `getNominalGoal` / `setEffectiveGoal` / `getGoalStatus` | Accessors used by the agent to read/annotate the degraded status. |

The probe is **deterministic**: it does not sample or learn, it just measures the
physics of the surviving actuators once. In `labmon_f1dead` there is one survivor
(the monitor), so `2^1 = 2` combinations (monitor OFF → rank 0, monitor ON → rank
2); the argmin is rank 2, which is `< 3`, so the zone is degraded to rank 2.

### 5.3 Agent orchestration — `illuminance_controller_agent_adapt.asl`

After the fault is detected, the lamp blacklisted, and the Q-table warm-restarted,
`@on_defect_new` calls `!assess_reachability(0)`:

```
+!assess_reachability(Zone) <-
    beginReachabilityProbe(NumCombos)[QlId];
    !probe_combo_loop(Zone, 0, NumCombos);         // recursive: apply combo → read → recordProbeRank
    finishReachabilityProbe(Zone, BestRank, Degraded)[QlId];
    if (Degraded) {
        getNominalGoal(Zone, Nominal)[QlId];
        +degraded_mode(Zone, BestRank, Nominal);
        .print("[DEGRADED] Goal rank ", Nominal, " UNREACHABLE — best effort rank ",
               BestRank, ". USER NOTIFIED.");
    } else { .print("[Adapt] Nominal goal still reachable — normal recovery.") }.
```

The recursive `@probe_combo_loop` / `@apply_combo` plans follow the codebase's
existing recursive-plan idiom (no `for` loops): for each combo they map each
action index to its WoT type+value (`actionToWoT`), call `invokeAction` on the
lab, wait a settle delay, read the lab status, encode the state, and call
`recordProbeRank`.

### 5.4 Recovery log — `saveRecoveryLog`

The recovery CSV header gains four columns:

```
...,RecoveredGoalRate,NominalGoal,BestEffortRank,RankShortfall,DegradedMode
```

`RankShortfall = NominalGoal − BestEffortRank`; `DegradedMode = 1` when degraded.
`analysis/phase2_recovery.py` reads these tolerantly (older CSVs without the
columns still parse) and surfaces `degraded_rate`, `best_effort_rank`, and
`nominal_goal` in `phase2_recovery_ci.csv`. In a degraded cell `RecoveredGoalRate`
is **best-effort attainment** (fraction of greedy rollouts reaching the effective
rank), because `isTerminal` now targets `effectiveGoal`.

---

## 6. Why the cost hack is now unnecessary

The Phase 2.5 doc §3 identified a "shared-physics wall": with energy-free reward,
any non-lamp path that rescued the faulty lab **also** reached rank 3 in the clean
lab, so the agent had no reason to use the lamp and never exercised (hence never
detected) its death. That wall **dissolves** the moment the monitor is weak:

- Clean lab: monitor → rank 2 (insufficient). The **lamp is the only rank-3
  lever**, so both arms *must* put it on the greedy path → its death is exercised
  and detected — with **zero** cost and **zero** init bias.
- Faulty lab: rank 3 is unreachable, so we no longer *require* a rank-3 survivor
  path. Best-effort rank 2 via the monitor is the honest, provable outcome.

Removing the cost also removed: `ws:rewardEnergyCost` (ontology property + the
`Monitor_Z1` triple), the `REWARD_ENERGY_INIT_WEIGHT` constant and its symmetric
Q-init block, the reward-side `energyPenalty` term in `computeZoneReward`, and the
now-dead `rewardEnergyCost` parse in `StereotypeReasoner` (SELECT var, OPTIONAL
clause, field, assignment). Lab5's genuine `ws:energyCost` **prior** is untouched
(confirmed by `Phase4KgDiscoveryTest`).

---

## 7. The KG angle (and an honest caveat)

**How the KG is expected to help.** Detection is not KG-gated (both arms freeze
the same clean policy, exercise the lamp, see no rank response, and blacklist it).
The differentiator is **recovery speed**: the KG arm's `MonitorStereotype` seeds a
positive prior on the monitor's ON action, so once the lamp is blacklisted the KG
agent immediately treats the monitor as a candidate light and re-optimises toward
the best-effort rank faster than the tabula-rasa agent, which must rediscover the
monitor from scratch.

**Honest caveat.** The KG in this project is **qualitative** — it declares the
monitor *Causes* light (a positive sign) but the *magnitude* is learned, not
stated (see the learned-dynamics TTLs, e.g. "the MAGNITUDE is learned"). So the KG
does **not** let either agent *predict a priori* that rank 3 is unreachable. That
is why the degradation is gated on a **runtime probe that measures** the surviving
physics, not on a KG inference. The KG accelerates *re-learning*; the probe
supplies the *proof of unreachability*. We state this explicitly rather than
overclaiming that the KG "knows" the goal is unreachable.

**Does the probe bias the contrast?** No. The probe is run **identically** in both
arms after detection, is deterministic, and sets the same `effectiveGoal` in both
arms. It is a property of the **environment** (which ranks the surviving actuators
can reach), not a treatment — so conditioning on it does not favour ql_true over
ql_false, exactly like the `_WELL_POSED_RECOVERY` stratifier.

---

## 8. Files changed

**Edited**
- [src/env/tools/QLearner.java](../src/env/tools/QLearner.java) — `effectiveGoal`
  indirection; reachability-probe + degrade `@OPERATION`s; `saveRecoveryLog`
  extended with `NominalGoal, BestEffortRank, RankShortfall, DegradedMode`;
  removed the `REWARD_ENERGY_INIT_WEIGHT` constant, its Q-init block, and the
  reward-side `energyPenalty`.
- [src/agt/illuminance_controller_agent_adapt.asl](../src/agt/illuminance_controller_agent_adapt.asl)
  — probe orchestration in `@on_defect_new`; recursive `@probe_combo_loop` /
  `@apply_combo` plans; `degraded_mode` belief + user notification; `getGoalStatus`
  wired into `@adapt_finish`'s `saveRecoveryLog` call.
- [src/env/tools/StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java)
  — removed the now-dead `ws:rewardEnergyCost` parse (SELECT var, OPTIONAL clause,
  `ActionInfo` field, assignment).
- [src/resources/building_6_monitor.ttl](../src/resources/building_6_monitor.ttl)
  — removed `ws:rewardEnergyCost` (property decl + `Monitor_Z1` triple); rewrote
  the header comments to describe the monitor as a weak rank-2 emergency light and
  the proof-gated degradation.
- [simulator/simulator_flow_labmon.json](../simulator/simulator_flow_labmon.json)
  — monitor dimmed `+290 → +260` (rank 3 → rank 2); physics/info/reset comments
  updated.
- [simulator/generate_faulty_flows.ps1](../simulator/generate_faulty_flows.ps1) —
  `labmon_f1dead` comment corrected (no backup; goal unreachable, best effort rank
  2). Faulty flow regenerated.
- [src/test/java/tools/MonitorKgDiscoveryTest.java](../src/test/java/tools/MonitorKgDiscoveryTest.java)
  — dropped the cost assertions; asserts both actuators carry no energy prior.
- [analysis/phase2_recovery.py](../analysis/phase2_recovery.py) — `labmon_f1dead`
  comment updated (best-effort rank 2); tolerant reads of the new degradation
  columns; `degraded_rate` / `best_effort_rank` / `nominal_goal` in the CI table.

**Unchanged (self-gating guarantees):** every other lab's reward, Q-init, state
space, and warm-startable Q-tables are byte-for-byte identical, because
`effectiveGoal` only diverges from `goal` after a proof of unreachability, which
only happens in `labmon_f1dead`.

---

## 9. Validation

### 9.1 Unit tests (green)
- `MonitorKgDiscoveryTest` — two Causes actuators discovered, monitor `hasIV ==
  false`, no energy prior, 3-slot / 16-state vector, distinct bits.
- `Phase4KgDiscoveryTest` — lab5's `ws:energyCost` prior still parses (confirms
  the `rewardEnergyCost` removal did not disturb the surviving prior).
- Full `./gradlew test` suite green.

### 9.2 Local smoke (mechanism check)
Early clean-training signal confirmed the physics is well-posed: the KG arm
reaches the goal (rank 3, via the lamp — the only rank-3 lever) within the first
tens of episodes. Full both-arms smoke + `labmon_f1dead` adapt verifies
`DetectEpisode ≥ 0`, `DegradedMode = 1`, `BestEffortRank = 2`, `RankShortfall =
1`. *(Smoke is validation only; the experiment runs on GitHub Actions.)*

### 9.3 Confirmatory run (GitHub Actions)
`phase2.yml`, N = 10 seeds, both arms. **Results to be filled in after the run
completes.**

| Metric | ql_true (KG) | ql_false (vanilla) | Notes |
|---|---|---|---|
| DetectEpisode (mean) | _TBD_ | _TBD_ | expect ≈ 0 both arms (detection not KG-gated) |
| RecoveryEpisodes (mean) | _TBD_ | _TBD_ | headline: KG faster to best-effort |
| DegradedMode rate | _TBD_ | _TBD_ | expect 1.0 both arms (rank 3 provably unreachable) |
| BestEffortRank | _TBD_ | _TBD_ | expect 2 |
| RecoveredGoalRate (best-effort) | _TBD_ | _TBD_ | expect ≈ 1.0 |

---

## 10. Design alternatives considered (and why rejected)

| Option | Idea | Why rejected |
|---|---|---|
| **A. Plateau heuristic** | Lower the goal when reward plateaus below target for N episodes | Could degrade a *reachable* goal that is merely on a temporary learning plateau — not proof-gated. |
| **B. Monotone reward rewrite** | Replace terminal/hold with a smooth "closer is always better" reward | Changes the reward for **every** lab; risks regressing all validated cells. |
| **C. Proof-gated probe (chosen)** | Deterministically measure the surviving actuators; degrade only on proof | Untouched in clean labs and reachable faulty cells; degrades **only** on a deterministic proof of unreachability. |
