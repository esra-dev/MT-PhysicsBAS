# Phase 2.5 — `labmon2`: a dual-zone monitor-fallback lab (spotlight removed) for the KG recovery-speed contrast

**Status:** implemented, ASL/Java validated locally (detection + degradation + recovery confirmed), dispatched to CI (10 seeds × 2 arms).
**Branch:** `phase2-instant-blacklist`.
**Author:** design + implementation notes for the thesis appendix.

---

## 1. Why this lab exists (the gap it fills)

The best-effort degradation mechanism (reachability probe → lower the effective
goal → notify the user) was first proven on **`labmon_f1dead`** — the single-zone
monitor emergency-fallback lab. That run confirmed the *mechanism* is perfect and
identical across arms (detection_rate 1.0, DetectEpisode 0, degraded_rate 1.0,
BestEffortRank 2 / NominalGoal 3, RecoveredGoalRate 1.0), but the headline
**recovery-speed** contrast came back **null**: `labmon` is a *single-survivor*
degradation. After the primary lamp is blacklisted only **one** actuator path
reaches the best-effort rank, so there is no *triage* — a structural prior over
survivors cannot help. The KG's advantage is in **choosing among survivors**, and
`labmon` offers no choice.

`lab3_f2dead_lowsun` (Phase 2.5B) addressed this by reusing the complex
cross-coupled `lab3` and inverting the value of the (previously redundant)
**spotlight**. `labmon2` is the **complementary, self-contained** design: it
**removes the spotlight entirely** and instead gives **each of two independent
zones** its own lamp + monitor + blind. The multi-survivor triage now comes from
having **two separate zones each with a monitor + blind fallback**, with **no
cross-zone coupling** to muddy the physics.

The two labs are deliberately different mechanisms for the same hypothesis:

| | `lab3_f2dead_lowsun` | `labmon2_f2dead_lowsun` |
|---|---|---|
| survivor structure | shared spotlight + 2 blinds (cross-coupled) | per-zone monitor + blind, ×2 zones (independent) |
| triage | re-value one suppressed shared lever | re-value the monitor fallback in **each** zone |
| coupling | cross-lamp +150, cross-blind 0.40·sun | **none** (two clean independent zones) |
| survivors after fault | 3 (`Z1Blinds`,`Z2Blinds`,`Spotlight`) → 8 combos | 4 (`Z1Monitor`,`Z2Monitor`,`Z1Blinds`,`Z2Blinds`) → 16 combos |

---

## 2. The physics

Two **independent** zones, each with a primary task **lamp**, a computer
**monitor** (whose light is a screen-backlight **side-effect**, modelled with
`ws:MonitorStereotype` / *Causes*) and a sun-mediated window **blind**. No
spotlight, no cross-zone spill:

```
z1 = 25 + (Z1Light?400) + (Z1Monitor?200) + (Z1Blinds?0.50·sun)
z2 = 25 + (Z2Light?400) + (Z2Monitor?200) + (Z2Blinds?0.50·sun)
```

Rank bounds on sensed illuminance are `[50, 100, 300]`, so **rank 3 = ≥ 300 lux**.
The nominal goal is **both zones at rank 3**. Sun is sampled once per episode from
`{0, 100, 400, 900}` and **pinned** for the episode.

Locally probed clean physics (via `/action` + one env tick), confirming the
detection-critical property:

| condition (per zone) | level | rank |
|---|---|---|
| sun 100, all off | 25 | 0/1 |
| sun 100, lamp only | **425** | **3** |
| sun 100, monitor only | 225 | 2 |
| sun 100, monitor + blind | 275 | 2 |
| sun 400, monitor + blind | 425 | 3 |
| sun 900, blind only | 475 | 3 |

**Key fact → why detection works with no reward-cost / Q-init bias.** At **low
sun** the **lamp is the only rank-3 lever** (monitor + blind max out at 275 < 300).
So both arms learn to use the lamp on low-sun episodes, and — because the Phase-2
adapt run **pins sun = 100** — the warm greedy policy tries the lamp first, and its
death is detected immediately. At sun ≥ 400 the blind path reaches rank 3 on its
own, which is exactly why the fault variant pins the sun low.

---

## 3. The fault (`labmon2_f2dead_lowsun`)

**Fault:** both task lamps dead (`Z1Light`, `Z2Light`) **and** the episode sun
pinned to **rank 1 (100 lux)**.

**Resulting physics** (both lamps zeroed, sun = 100):

```
z_i = 25 + (Zi_Monitor?200) + (Zi_Blinds?50)  ≤  25 + 200 + 50 = 275 lux = rank 2
```

So **both zones robustly degrade to rank 2** on every episode. After the two lamps
are blacklisted the survivors are **`Z1Monitor`, `Z2Monitor`, `Z1Blinds`,
`Z2Blinds`** → 2⁴ = **16** reachability-probe combinations, and **both** zones must
be probed.

### Why this gives the KG an advantage — the "redundant → essential" inversion

In the **clean** lab the monitor is a *side-effect* light source (rank 2 alone),
strictly weaker than the lamp for reaching rank 3, so the trained agent learns to
reach the goal with the **lamp** and treats the monitor as incidental. Both arms
warm-start Phase 2 from that same clean Q-table.

The fault **inverts the monitor's value**: with both lamps gone and low sun, the
**monitor (+200)** is now the **single largest best-effort lever** — the essential
path to rank 2 in each zone. Recovery is therefore *re-valuing a previously-
incidental actuator, independently in two zones*.

- The **KG arm (`ql_true`)** carries the structural prior that the monitor
  *Causes* light, re-biasing its post-fault exploration toward the monitor and
  re-discovering the best-effort policy faster.
- The **vanilla arm (`ql_false`)** must re-learn the monitor's value by trial and
  error in both zones before it stabilises.

---

## 4. Local validation (before CI dispatch)

Run locally on port 1900 (clean sim → clean `ql_true` training → faulty sim →
adapt smoke), all gates passed:

- **Ontology / state-space:** `StereotypeReasoner` loaded `building_7_dualmonitor.ttl`;
  slot registry `len=9 domain=[4,4,2,2,2,2,2,2,4]`; `Goal=[3,3]`; `States=4096
  Actions=13`; all **6 actuators** discovered (`Z1/Z2 × {Light,Monitor,Blinds}`);
  `StereotypeLearner ready` (KG priors active). `BUILD SUCCESSFUL`.
- **Clean `ql_true` training:** 4000 episodes, `qtable_final_stereotypes_true_labmon2*.csv`
  written (zone1/zone2 splits for warm-load). `BUILD SUCCESSFUL`.
- **Fault injection:** faulty sim reset pins `sun = 100`; both lamps ON → level
  stays 25 (dead); all actuators ON → 275 (rank-2 best effort).
- **Adapt smoke (`ql_true`, 400 ep):** warm-loaded the clean table; **Z1 lamp
  detected at episode 1**, blacklisted (13→11 actions); **both zones' reachability
  probe → rank 3 UNREACHABLE, best-effort rank 2, DEGRADED**; **Z2 lamp detected as
  secondary at episode ~8**, blacklisted (11→9); **RE-CONVERGED at episode ~132**.

Recovery CSV (`recovery_stereotypes_true_labmon2_f2dead_lowsun.csv`):

| DefectComponent | DetectEpisode | ReconvergeEpisode | SecondaryDetect | RecoveredGoalRate | NominalGoal | BestEffortRank | RankShortfall | DegradedMode |
|---|---|---|---|---|---|---|---|---|
| SetZ1Light | 0 | 132 | 8 | **1.0000** | 3 | 2 | 1 | 1 |

The mechanism (warm-load → detect → blacklist → per-zone degrade → recover) is
arm-agnostic, so the same detection fires for `ql_false`; CI runs both arms fresh
across 10 seeds to measure the recovery-speed contrast.

---

## 5. Files

- `src/resources/building_7_dualmonitor.ttl` — self-contained 2-zone ontology
  (2× lamp/monitor/blind, no coupling, no spotlight; state slot registry dim 9;
  WoT actuator mappings for the 6 actuators).
- `src/resources/interactions-labmon2.ttl` — Thing Description, base
  `http://localhost:1900/was/rl/`, 12 status props + 6 action affordances.
- `simulator/simulator_flow_labmon2.json` — clean sim (port 1900), deterministic
  per-tick physics, sun sampled `{0,100,400,900}` and pinned per episode.
- `simulator/simulator_flow_labmon2_f2dead_lowsun.json` — faulty variant (both
  lamps → 0, sun pinned 100); generated by `simulator/generate_faulty_flows.ps1`.
- `benchmark/scenarios_labmon2.json` (16 held-out) + `benchmark/train_scenarios_labmon2.json` (10).
- `src/agt/lab_profiles.asl` — `labmon2` (clean) + `labmon2_f2dead_lowsun` (faulty)
  profiles + `adapt_source("labmon2_f2dead_lowsun", "_labmon2")`.
- `config/run_config.json` — port/flow/suffix/dim maps (clean + phase2 block).
- `analysis/phase2_recovery.py` — `labmon2_f2dead_lowsun` added to the
  well-posed-recovery set.

Ports: `labmon2 = 1900` (clean and faulty reuse the same port; only one runs at a time).
