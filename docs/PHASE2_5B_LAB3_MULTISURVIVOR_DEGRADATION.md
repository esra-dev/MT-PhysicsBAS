# Phase 2.5B — `lab3_f2dead_lowsun`: a multi-survivor degraded cell for the KG recovery-speed contrast

**Status:** implemented, ASL/Java validated locally, dispatched to CI (10 seeds × 2 arms).
**Branch:** `phase2-instant-blacklist`.
**Author:** design + implementation notes for the thesis appendix.

---

## 1. Why this lab exists (the gap it fills)

The Phase 2.5B best-effort degradation mechanism (reachability probe → lower the
effective goal → notify the user) was first proven on **`labmon_f1dead`** — the
monitor emergency-fallback lab. That run (CI `28863439179`, N = 10 × 2 arms)
confirmed the *mechanism* is perfect and identical across arms:

| metric | ql_true (KG) | ql_false (vanilla) |
|---|---|---|
| detection_rate | 1.0 | 1.0 |
| DetectEpisode | 0 | 0 |
| degraded_rate | 1.0 | 1.0 |
| BestEffortRank / NominalGoal | 2 / 3 | 2 / 3 |
| RecoveredGoalRate | 1.0 | 1.0 |

But the headline **recovery-speed** contrast came back **null**:
KG mean 84.5 episodes [58.8, 111.1] vs vanilla 62.3 [51.0, 84.3]; diff +22.2
(KG nominally *slower*), CI [−18.1, +57.0] crosses 0; bootstrap p = 0.248,
Wilcoxon p = 0.430, Cliff's δ = 0.05 (negligible).

**Root cause of the null:** `labmon` is a *single-survivor* degradation. After
the primary lamp is blacklisted, only **one** actuator path (`{Z1Monitor,
Z1Backup}`) can reach the best-effort rank. There is no *triage* to perform —
both arms have exactly one way to degrade gracefully, so a structural prior over
survivors cannot help. The KG's advantage is in **choosing among survivors**,
and `labmon` offers no choice.

To give the KG recovery-speed hypothesis a lab where it *can* show up, we need a
degradation that is simultaneously:

1. **Robustly unreachable** — the nominal goal is impossible on *every* episode
   (so the effective goal is well-defined and stable, not sun-conditional), and
2. **Multi-survivor** — several actuators remain after the fault, so there is a
   genuine triage the KG's structural priors can accelerate.

`lab3_f2dead_lowsun` is that lab.

---

## 2. The physics constraint that shaped the design

`lab3` (Complex, port 1894) is a two-zone, five-actuator, cross-coupled lab. The
**actual simulator flow** physics (which differs from the ontology comment — the
cross-lamp spill is **+150**, not +50, and the cross-blind coefficient is
**0.40·sun**, not 0.25) is:

```
z1 = 25 + (Z1Light?400) + (Z2Light?150) + (Z1Blinds?0.50·sun) + (Z2Blinds?0.40·sun) + (Spotlight?150)
z2 = 25 + (Z2Light?400) + (Z1Light?150) + (Z2Blinds?0.50·sun) + (Z1Blinds?0.40·sun) + (Spotlight?150)
```

Rank bounds on sensed illuminance are `[50, 100, 300]`, so **rank 3 = strictly
> 300 lux**. The nominal goal is **both zones at rank 3**. Sun is sampled once
per episode from `{0, 100, 400, 900}` and **pinned** for the episode.

Two facts make a *robust* degradation non-trivial:

- **The blinds reach rank 3 alone at high sun.** `0.50 · 900 = 450 > 300`. So any
  fault that leaves the blinds intact is *reachable* at high sun — the plain
  `lab3_f2dead` (both lamps dead, sun free) is degraded only on low-sun episodes,
  a muddied sun-conditional cell.
- **The cross-lamp (150) and Spotlight (150) together reach rank 3.**
  `25 + 150 + 150 = 325 > 300`. So killing a single lamp is never enough; the
  redundant levers close the gap.

**Conclusion:** to make rank 3 unreachable on *every* episode while keeping
multiple survivors, we must (a) kill **both** task lamps *and* (b) **pin the sun
low** so the blinds cannot reach rank 3 on their own. This is exactly the
"sun-mediated degraded cell" flagged earlier as a use for the general probe.

---

## 3. The chosen design (Design A)

**Fault:** both task lamps dead (`Z1Light`, `Z2Light`) **and** the episode sun
pinned to **rank 1 (100 lux)** instead of being sampled.

**Resulting physics** (both lamps zeroed, sun = 100):

```
z_i = 25 + (own_blind?50) + (cross_blind?40) + (Spotlight?150)
    ≤ 25 + 50 + 40 + 150 = 265 lux = rank 2   (for both zones)
```

So **both zones robustly degrade to rank 2** on every episode. After the two
lamps are blacklisted, the survivors are **`Z1Blinds`, `Z2Blinds`, `Spotlight`**
→ 2³ = **8** reachability-probe combinations, and **both** zones must be probed.

### Why this gives the KG an advantage — the "redundant → essential" inversion

In the **clean** `lab3`, the Spotlight is deliberately **redundant** (150 < 300,
never sufficient alone), so the trained agent learns to **avoid** it (it costs
energy and the cycling penalty discourages pointless toggling). Both arms
warm-start Phase 2 from that same "avoid-spotlight" clean Q-table.

The fault **inverts the Spotlight's value**: with both lamps gone and low sun,
the Spotlight (+150) is now the **single largest best-effort lever** — the
essential path to rank 2. The recovery task is therefore *re-valuing a
previously-suppressed actuator*.

- The **KG arm (`ql_true`)** carries a structural prior: the Spotlight
  *Causes* light. That prior re-biases its post-fault exploration toward turning
  the Spotlight on, so it re-discovers the best-effort policy faster.
- The **vanilla arm (`ql_false`)** must *unlearn* the "avoid-spotlight"
  Q-values by trial and error before it stabilises on the spotlight-based
  policy.

This is a recovery-**speed** contrast *inside* a degradation — precisely what
`labmon` could not offer.

### Design B (rejected)

A single-zone variant (`Z1Light` + `Spotlight` dead + sun pinned) would reuse
the validated zone-0 probe unchanged, but `Z1` reaches rank 2 *trivially* via the
+150 cross-lamp (turning on `Z2Light` for `Z2`'s own recovery incidentally lifts
`Z1` to rank 2), so the `Z1`-specific triage signal is weak. Design A's symmetric
two-zone degradation with the redundant-Spotlight inversion is the stronger,
cleaner test, and — as shown in §5 — the two-zone probe it needs is a small,
low-risk change.

---

## 4. Implementation

All changes are additive; no existing profile or tested path is modified.

### 4.1 Faulty simulator flow — `simulator/generate_faulty_flows.ps1`

New recipe (string-replacement on the clean `simulator_flow_lab3.json`):

```powershell
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f2dead_lowsun.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F2DEAD_LOWSUN (port 1894)' `
    @(@('z1l ? 400', 'z1l ? 0'), @('z1l ? 150', 'z1l ? 0'), `
      @('z2l ? 400', 'z2l ? 0'), @('z2l ? 150', 'z2l ? 0'), `
      @('sunRanks[Math.floor(Math.random() * sunRanks.length)]', '100'))
```

The first four replacements zero both task lamps (own +400 and cross +150 in each
zone); the fifth replaces the episode-start sun sampling with the constant `100`.
`SunshinePinned` is already raised by the clean reset node, so the env tick treats
sun = 100 as constant. Generated + JSON-validated: physics function now reads
`(z1l ? 0 …)`/`(z2l ? 0 …)` in both zones, and the reset node sets
`Sunshine, 100`.

### 4.2 Two-zone reachability probe — `src/env/tools/QLearner.java` + adapt agent

The probe is **per-zone parameterized already** (`recordProbeRank(stateVec, zone)`
uses `goal[zone]` and `zoneLevelIndices[zone]`; `finishReachabilityProbe(zone, …)`
sets `effectiveGoal[zone]`; `beginReachabilityProbe` resets its scratch on each
call). Previously the adapt agent only probed zone 0 (`assess_reachability(0)`),
which is correct for single-zone labs but **wrong** for a two-zone degradation.

**QLearner.java** — added one operation:

```java
@OPERATION
public void getNumZones(OpFeedbackParam<Integer> out) { out.set(goal.length); }
```

**`illuminance_controller_agent_adapt.asl`** — the post-blacklist recovery now
probes **every** zone:

```jason
getNumZones(NumZones)[artifact_id(QlId)];
!assess_zones(0, NumZones).

@assess_zones_done  +!assess_zones(Z, N) : Z >= N <- true.
@assess_zones_step  +!assess_zones(Z, N) : Z <  N <-
    !assess_reachability(Z);
    !assess_zones(Z + 1, N).
```

This is generic: `labmon` (1 zone) still probes only zone 0; `lab3` (2 zones)
probes zones 0 and 1, each independently lowering its own effective goal.

### 4.3 Profile + wiring

- **`src/agt/lab_profiles.asl`** — new `lab_profile("lab3_f2dead_lowsun", …)`
  (reuses lab3 TD/ont/port 1894, `zone_targets [target(1,3), target(2,3)]`,
  `qtable_suffix "_lab3_f2dead_lowsun"`) and `adapt_source("lab3_f2dead_lowsun",
  "_lab3")` so the adapt agent warm-loads the clean lab3 Q-table.
- **`config/run_config.json`** (phase2 block) — added the profile to
  `adapt_profiles` and to all seven maps (`parent_profile` → lab3,
  `simulator_port_map` → 1894, `simulator_flow_map` → the new flow,
  `qtable_suffix_map`, `clean_source_suffix` → `_lab3`,
  `expected_state_vec_dim` → 8).
- **`analysis/phase2_recovery.py`** — added `lab3_f2dead_lowsun` to
  `_WELL_POSED_RECOVERY` (like `labmon_f1dead`, the recovery-speed contrast is
  well-posed against the proven best-effort effective goal).

---

## 5. Correctness argument (why the two-zone probe is *required*, not optional)

The greedy recovery certification and the re-learning reward both measure
attainment of the **effective** goal per zone. From `QLearner.isTerminal`:

```java
for (int z = 0; z < effectiveGoal.length; z++)
    if (toInt(stateVec[zoneLevelIndices[z]]) != effectiveGoal[z]) { t = false; break; }
```

and the reward uses `int target = effectiveGoal[z]` for each zone.

Both zones degrade to rank 2, so **both** `effectiveGoal[0]` and
`effectiveGoal[1]` must be lowered from 3 to 2. Had we kept the old single-zone
probe (`assess_reachability(0)` only), `effectiveGoal[1]` would remain at the
**unreachable** nominal rank 3 — the terminal check would then never fire (zone 1
can never hit rank 3), so `RecoveredGoalRate` would be ~0 for **both** arms and
the cell would be a broken, uninformative failure. Probing both zones is what
makes the cell well-posed. This was verified by reading `isTerminal`, the reward
loop, and `getGoalStatus` in `QLearner.java`.

The recovery row logs `getGoalStatus(0, …)` (zone 0), which is representative
because the degradation is **symmetric** (both zones → rank 2): the row will show
`NominalGoal = 3`, `BestEffortRank = 2`, `DegradedMode = 1`.

---

## 6. Local validation performed

- **`gradlew compileJava`** — clean (the new `getNumZones` operation compiles).
- **Faulty flow** — generated and JSON-validated; grep confirms both lamps zeroed
  in both `z1`/`z2` equations and the reset node pins `Sunshine, 100`.
- **`run_config.json`** — re-parsed as valid JSON after the seven map edits.
- **ASL parse smoke** — launched `taskAdapt -Pprofile=lab3_f2dead_lowsun` (no sim
  running): the agent parsed **all** `.asl` (no syntax/binding errors in the new
  `assess_zones`/`getNumZones` plans), resolved `active.profile=lab3_f2dead_lowsun`,
  mapped to port **1894**, and stopped only at the expected point (connection
  refused, because no simulator was running). `lab_profiles.asl` diff is +28 lines
  with **no** transient training/active-profile churn.

A full local integration smoke (drive the live faulty sim through the 8-combo
two-zone probe) was **not** run because no clean lab3 Q-tables exist locally and
generating them requires the full two-arm clean-training orchestration that the
CI pipeline performs per seed. The probe *execution* path is instead verified
statically against `isTerminal`/reward/`getGoalStatus` (§5) and will be exercised
end-to-end by the dispatched CI run (which trains clean lab3 per seed before
adapting).

---

## 7. CI run + hypothesis

Dispatched `phase2.yml` on `phase2-instant-blacklist`:

```
adapt_profiles = lab3_f2dead_lowsun
seeds          = 1,2,3,4,5,6,7,8,9,10
run_mode       = phase1
adapt_episodes = 0        # each profile's training_params default
publish_results = true
```

The workflow derives `parent = lab3` from `run_config.json`, trains the clean
lab3 Q-table (both stereo arms) per seed, then runs the adapt agent for both
arms.

**Expected mechanism outcome (both arms identical):** `DegradedMode = 1` for both
zones, `BestEffortRank = 2`, `NominalGoal = 3`, `RecoveredGoalRate ≈ 1.0` (the
best-effort rank-2 policy is easily reachable via the Spotlight).

**Headline hypothesis (recovery speed):** the KG arm (`ql_true`) re-converges on
the Spotlight-based best-effort policy in **fewer** episodes than the vanilla arm
(`ql_false`), because the KG's *Spotlight-Causes-light* prior lets it re-value the
previously-suppressed Spotlight without the vanilla arm's unlearning cost. Unlike
`labmon`, this cell has a real multi-survivor triage where that prior can bite —
so a non-null, KG-faster recovery-speed contrast is *possible* here (whereas in
`labmon` it was structurally impossible).

**Interpretation guardrails:** if the contrast is again null, the honest reading
is that even the redundant-Spotlight inversion is too easy for the warm-started
vanilla arm to unlearn (rank 2 is trivially reachable), and the KG recovery-speed
advantage may require a *harder* triage (more survivors, or a survivor whose
value is not obvious from a single Causes edge). This lab is the cleanest
available test of the hypothesis; a null here would meaningfully bound the claim.
