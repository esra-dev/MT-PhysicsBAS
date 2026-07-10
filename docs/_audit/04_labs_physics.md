# Audit 04 — Lab Physics (Node-RED flows) × Lab Profiles (`lab_profiles.asl`)

**Era: NEW (phase-based approach, THESIS_PIVOT_MASTER.md).** Every lab in this document belongs
to the new phase-based ladder (lab1/lab2/lab3, faulty variants, labmon/labmon2, *_slow, lab4/lab5).
The OLD era's flows (`simulator/simulator_flow.json`, `simulator_flow_custom.json` …
`simulator_flow_custom9s.json`) and profiles (`custom`, `custom_full_train`, `custom2`–`custom9s`,
registered at src/agt/lab_profiles.asl#L39-L253) are **out of scope here** and are only mentioned
where a new-era file explicitly references them (e.g. the lab3 physics comment names the
custom9s PRNG leak, simulator/simulator_flow_lab3.json#L130).

Audited on branch `phase2-instant-blacklist` (repo state of 2026-07-07).
**Delta-refreshed 2026-07-08** (post-Batch state, branch `kg-crosszone-coupling-mid`): lab1
ambient term deleted (working tree), lab3 cross-zone magnitudes changed (commit `ad3cb3b`),
labmon stale comments partially cleaned (working tree). See §1.1, §1.3, §6.

---

## 0. How the physics was extracted (method + common structure)

Every new-era flow file `simulator/simulator_flow_<lab>.json` has the same node layout
(verified for all 27 lab* / labmon* files):

| Node (name) | JSON location (same in every file) | Role |
|---|---|---|
| `Initialization` | `"func"` at `#L30` | boot defaults |
| `Status` | `"func"` at `#L55` | GET state endpoint |
| `Update action` | `"func"` at `#L91` | mutates actuator **flags only** — "NO physics here" |
| `Update environment` | node id `#L126`, name `#L129`, **`"func"` at `#L130`** | **the lux physics** (deterministic, pure function of flow state) |
| `Reset episode` | name `#L154`, **`"func"` at `#L155`** | episode-start PRNG sampling |
| `Set state (benchmark)` | `"func"` at `#L191` | pins exact state for benchmark scenarios |
| `Health` | `"func"` at `#L227` | liveness probe |

All lux formulas below are quoted literally from the `Update environment` `"func"` string at
`#L130` of the named file. Common properties (verified per file, cited at the canonical clean
flows):

- **Deterministic physics**: "NO Math.random calls" in the env tick; PRNG only in `Reset episode`
  (simulator/simulator_flow_lab3.json#L130, lab1 #L130, lab2 #L130).
- **Pinned sunshine**: sun is sampled once per episode from `[0, 100, 400, 900]` and pinned
  (`SunshinePinned=true`) for the rest of the episode (reset func, e.g.
  simulator/simulator_flow_lab2.json#L155; also stated at src/agt/lab_profiles.asl#L256-L257).
- **Episode-start level priors**: `levels = [25, 75, 150, 500]`; actuator flags sampled
  `Math.random() < 0.5` (Spotlight `< 0.3`) — reset func `#L155` of each flow. Exception:
  **labmon** starts all actuators OFF each episode (simulator/simulator_flow_labmon.json#L155).
- **Env tick rate**: the env tick inject node repeats every `0.05` s real time
  (`"repeat": "0.05"`, e.g. simulator/simulator_flow_lab3.json#L117). The *simulated* clock
  mapping `seconds_per_tick(5.0)` lives agent-side
  (src/agt/illuminance_controller_agent_dynamics.asl#L56).
- **Energy accounting** is computed in the env tick per lab (values listed per lab below); it is
  informational except in lab5's compliance scoring (see §4).

**Profile schema** (13 fields): `lab_profile(Name, td, ont, scenarios, train_scenarios, sim_port,
light_bounds, sunshine_bounds, zone_targets, sunshine_prob, weakness_flags, qtable_suffix,
training_params(NumEpisodes, EpsilonDecay))` — src/agt/lab_profiles.asl#L10-L23.

**Shared profile values for ALL new-era labs** (every profile row cited below):
`light_bounds([50, 100, 300])`, `sunshine_bounds([50, 200, 600])` (`[r1Upper, r2Upper, r3Upper]`,
schema comment src/agt/lab_profiles.asl#L17-L18), `sunshine_prob(0.75)`, targets always rank 3.
So rank 3 ⇔ lux ≥ 300 (consistent with the in-repo derivations "265 lux = rank 2"
src/agt/lab_profiles.asl#L766-L767 and "0.50*900 = 450 > 300" simulator/generate_faulty_flows.ps1#L118).

---

## 1. Phase 1 — clean ladder (lab1, lab2, lab3)

Per ThesisGoalDescription: clean labs fully aligned with the KG; KG-primed QL vs tabula-rasa QL.

### 1.1 lab1 — Trivial, 1 zone, 1 actuator (port 1892)

Physics (simulator/simulator_flow_lab1.json#L130):

```js
var z1 = 25
       + (z1light ? 400 : 0);
```

- The former **non-actuable ambient daylight term `0.10 * sun` was deleted on 2026-07-08**
  (13_logic_report.md §3 item 7, option "delete it from the flow"): the func now states
  "physics is a pure function of (Z1Light)" and "Sunshine is sampled at /was/rl/reset … but
  does NOT enter physics (no un-modelled ambient term)". `building_1_trivial.ttl#L25` was
  updated to match (`Z1Level = 25 + (Z1Light ? 400 : 0)`). Energy: lamp = 1 unit/tick
  (same func, `z1light ? 1 : 0`).

Profile (src/agt/lab_profiles.asl#L260-L272): ont `building_1_trivial.ttl`, port **1892**,
zone_targets `[target(1, 3)]`, qtable_suffix `"_lab1"`, training_params **(1000, 0.9920)**,
weakness_flags `[]`, scenarios `benchmark/scenarios_lab1.json` / `train_scenarios_lab1.json`.

### 1.2 lab2 — Intermediate, 2 independent zones, adds Mediates blinds (port 1893)

Physics (simulator/simulator_flow_lab2.json#L130):

```js
var z1 = 25
       + (z1l ? 400        : 0)
       + (z1b ? 0.50 * sun : 0);

var z2 = 25
       + (z2l ? 400        : 0)
       + (z2b ? 0.50 * sun : 0);
```

- "Two INDEPENDENT zones (no cross-zone bleed)" (same func). Energy: lamps 1/tick each,
  blinds passive (0).
- The blind is the **IV-gated (Mediates) mechanism**: its effect is `0.50 * sun`, i.e. zero when
  sun = 0 — the unquantified threshold the agent must learn (ThesisGoalDescription Phase 1).

Profile (src/agt/lab_profiles.asl#L275-L287): ont `building_2_intermediate.ttl`, port **1893**,
targets `[target(1,3), target(2,3)]`, suffix `"_lab2"`, training_params **(2000, 0.9960)**.

### 1.3 lab3 — Complex, cross-zone spillage + shared spotlight (port 1894)

Physics (simulator/simulator_flow_lab3.json#L130):

```js
var corridor = sp ? 150 : 0;

var z1 = 25
       + (z1l ? 400        : 0)
       + (z2l ? 100        : 0)
       + (z1b ? 0.50 * sun : 0)
       + (z2b ? 0.30 * sun : 0)
       + corridor;

var z2 = 25
       + (z2l ? 400        : 0)
       + (z1l ? 100        : 0)
       + (z2b ? 0.50 * sun : 0)
       + (z1b ? 0.30 * sun : 0)
       + corridor;
```

- Cross-zone spill: each lamp adds **+100** to the *other* zone; each blind adds **0.30·sun** to
  the other zone; the shared Spotlight adds **+150 to both** zones. Energy: lamps 1/tick,
  spotlight 2/tick, blinds 0.
- **Magnitudes changed 2026-07-08** (commit `ad3cb3b`, "intermediate cross-zone bleed"):
  lamp bleed 150 → **100**, blind bleed 0.40 → **0.30**·sun — rank-moving but non-trivialising
  (0.30·900 = 270 < 300, so cross-zone bleed alone no longer reaches rank 3; derivation
  docs/_audit/14_presentation_rules.md#L76-L77). All four `phase1_xzone_*` runs listed in
  05_results_index.md §1.3 predate this change (they ran against the 150 / 0.40·sun physics);
  the intermediate-magnitude run 28941204656 (`phase1_xzone_mid/`) is the first against the
  new values.
- The func comment states this flow is "the explicit fix for simulator_flow_custom9s.json's PRNG
  leak where Sunshine was perturbed by `150 + 50 * Math.random()` every tick"
  (simulator/simulator_flow_lab3.json#L130) — i.e. the OLD-era custom9s physics was stochastic
  per tick; the NEW lab3 is deterministic.

Profile (src/agt/lab_profiles.asl#L291-L303): ont `building_3_complex.ttl`, port **1894**,
targets `[target(1,3), target(2,3)]`, suffix `"_lab3"`, training_params **(3000, 0.9970)**.

---

## 2. Phase 2 — faulty ladder (detect → blacklist → re-learn)

Every faulty flow is generated from its clean parent by literal string replacement in
`simulator/generate_faulty_flows.ps1` (`New-FaultyFlow`, #L4-L14 — throws if a pattern is not
found). Faulty profiles reuse the clean parent's **TD, ontology, port, scenarios and bounds**
("only ONE lab variant runs at a time during adaptation", src/agt/lab_profiles.asl#L453-L464), and
`adapt_source/2` maps each faulty profile to the clean parent's Q-table suffix for warm-loading
(src/agt/lab_profiles.asl#L812-L838). In every faulty flow the changed physics is again at
`simulator_flow_<variant>.json#L130` (env func); I verified each diff against the parent flow.

Note on budgets: the lab3-based faulty profiles train **4000** episodes vs the clean lab3's 3000
(e.g. src/agt/lab_profiles.asl#L532 vs #L303); lab2-based use 2000, lab1-based 1000, labmon-based
1500 — same as their parents.

### 2.1 Single-lamp faults

| Profile | Killed/negated term (literal, at `#L130` of the variant JSON) | Generator | Profile row | flags | adapt_source |
|---|---|---|---|---|---|
| `lab1_f1dead` | `z1light ? 400` → `z1light ? 0` | generate_faulty_flows.ps1#L17-L19 | lab_profiles.asl#L473-L485 | `[w4]` | `"_lab1"` (#L817) |
| `lab2_f1dead` | `z1l ? 400` → `z1l ? 0` | #L22-L24 | #L489-L501 | `[w4]` | `"_lab2"` (#L818) |
| `lab2_f1inv` | `z1l ? 400` → `z1l ? -400` | #L27-L29 | #L504-L516 | `[w2]` | `"_lab2"` (#L819) |
| `lab3_f1dead` | `z1l ? 400` → `z1l ? 0` **and** cross-zone `z1l ? 150` → `z1l ? 0` | #L32-L34 | #L520-L532 | `[w4]` | `"_lab3"` (#L820) |
| `lab3_f1inv` | `z1l ? 400` → `z1l ? -400` **and** `z1l ? 150` → `z1l ? -150` | #L37-L39 | #L537-L549 | `[w2]` | `"_lab3"` (#L821) |
| `lab3_f1dead_z2` | `z2l ? 400` → `z2l ? 0` **and** `z2l ? 150` → `z2l ? 0` (symmetric Z2 cell) | #L74-L76 | #L643-L655 | `[w4]` | `"_lab3"` (#L827) |
| `lab3_f1inv_z2` | `z2l ? 400` → `z2l ? -400` **and** `z2l ? 150` → `z2l ? -150` | #L79-L81 | #L658-L670 | `[w2]` | `"_lab3"` (#L828) |

`lab1_f1dead` is the degenerate detect-only cell: lab1's single actuator dies, so after
blacklisting there is "NO surviving lever — the agent DETECTS + ALERTS but cannot recover"
(src/agt/lab_profiles.asl#L470-L472).

### 2.2 Multi-lamp faults ("several components do not work")

| Profile | Killed/negated terms | Generator | Profile row | flags | adapt_source |
|---|---|---|---|---|---|
| `lab2_f2dead` | `z1l ? 400`→`0` and `z2l ? 400`→`0` | #L45-L47 | #L561-L573 | `[w4]` | `"_lab2"` (#L822) |
| `lab2_f2inv` | `z1l ? 400`→`-400` and `z2l ? 400`→`-400` | #L50-L52 | #L577-L589 | `[w2]` | `"_lab2"` (#L823) |
| `lab3_f2dead` | all four lamp terms zeroed: `z1l ? 400`→`0`, `z1l ? 150`→`0`, `z2l ? 400`→`0`, `z2l ? 150`→`0` | #L56-L59 | #L595-L607 | `[w4]` | `"_lab3"` (#L824) |
| `lab3_f2inv` | all four lamp terms negated: `400`→`-400`, `150`→`-150` for both lamps | #L62-L65 | #L612-L624 | `[w2]` | `"_lab3"` (#L825) |

Only Causes lamps are injected in the multi-fault cells; blinds stay healthy
(generate_faulty_flows.ps1#L41-L42).

### 2.3 Blind (Mediates) faults — advisor's "blinds defected/inverted" request

| Profile | Killed/negated terms | Generator | Profile row | flags | adapt_source |
|---|---|---|---|---|---|
| `lab3_f1bdead` | `z1b ? 0.50 * sun`→`z1b ? 0` **and** cross-zone `z1b ? 0.40 * sun`→`z1b ? 0` | #L84-L86 | #L676-L688 | `[w4]` | `"_lab3"` (#L829) |
| `lab3_f1binv` | `z1b ? 0.50 * sun`→`z1b ? -0.50 * sun` **and** `z1b ? 0.40 * sun`→`z1b ? -0.40 * sun` | #L89-L91 | #L694-L706 | `[w2]` | `"_lab3"` (#L830) |
| `lab2_f1bdead` | `z1b ? 0.50 * sun`→`z1b ? 0` (lab2 has no cross-zone term) | #L94-L96 | #L711-L723 | `[w4]` | `"_lab2"` (#L831) |
| `lab2_f1binv` | `z1b ? 0.50 * sun`→`z1b ? -0.50 * sun` | #L99-L101 | #L727-L739 | `[w2]` | `"_lab2"` (#L832) |

Blind faults are "only soundly falsifiable on the OPEN action under sun rank ≥2"
(src/agt/lab_profiles.asl#L634-L640; generate_faulty_flows.ps1#L69-L71).

### 2.4 Monitor-as-fallback labs (Phase 2.5): labmon, labmon2

#### labmon — single-zone monitor emergency lab (port 1899)

Clean physics (simulator/simulator_flow_labmon.json#L130):

```js
var z1 = 25
       + (z1l   ? 400 : 0)    // primary lamp (Causes, free)
       + (z1mon ? 260 : 0);   // monitor light SIDE-EFFECT (Causes, WEAK: rank 2 only)
```

No sunshine term, no blinds ("Sunshine is sampled at reset but intentionally UNUSED", same func).
Energy: lamp 1/tick, monitor **3**/tick — "informational only; does NOT affect the reward" (same
func). Reset starts both actuators **OFF** every episode (simulator/simulator_flow_labmon.json#L155).

Profile (src/agt/lab_profiles.asl#L370-L382): ont `building_6_monitor.ttl`, port **1899**,
targets `[target(1, 3)]`, suffix `"_labmon"`, training_params **(1500, 0.9950)**.

**Fault `labmon_f1dead`**: `z1l   ? 400 : 0` → `z1l   ? 0 : 0`
(generate_faulty_flows.ps1#L109-L111; verified in simulator/simulator_flow_labmon_f1dead.json#L130).
With the lamp dead, max reachable = 25 + 260 = **285 lux = rank 2**: the rank-3 goal is
**unreachable**, the monitor is the best-effort fallback and the agent must proof-gate the
degraded goal + notify the user (generate_faulty_flows.ps1#L104-L108). Profile
src/agt/lab_profiles.asl#L748-L760, flags `[w4]`, adapt_source `"_labmon"` (#L834).

> ⚠️ **Stale-comment discrepancy (flagged, not fixed):** the labmon profile header comment
> claims a third actuator "dim backup lamp", a "{monitor, backup} (375 lux)" recovery path and
> "32 states" (src/agt/lab_profiles.asl#L360-L369), and interactions-labmon.ttl#L14 mentions a
> `SetZ1Backup` action. **The actual flow has only Z1Light and Z1Monitor** (init/status/action
> funcs, simulator/simulator_flow_labmon.json#L30, #L55, #L91; grep for `Backup` in simulator/
> returns nothing), and the fallback ceiling is 285 lux (rank 2), matching
> generate_faulty_flows.ps1#L104-L108 — not 375. The comments describe an earlier design.

#### labmon2 — dual-zone monitor-fallback lab, no spotlight (port 1900)

Clean physics (simulator/simulator_flow_labmon2.json#L130):

```js
var z1 = 25
       + (z1l ? 400 : 0)
       + (z1m ? 200 : 0)
       + (z1b ? 0.50 * sun : 0);

var z2 = 25
       + (z2l ? 400 : 0)
       + (z2m ? 200 : 0)
       + (z2b ? 0.50 * sun : 0);
```

Two independent zones, no cross-zone coupling, no spotlight (same func). Energy: lamps 1/tick,
monitors 1/tick, blinds 0.

Profile (src/agt/lab_profiles.asl#L396-L408): ont `building_7_dualmonitor.ttl`, port **1900**,
targets `[target(1,3), target(2,3)]`, suffix `"_labmon2"`, training_params **(4000, 0.9975)**.

**Fault `labmon2_f2dead_lowsun`** (generate_faulty_flows.ps1#L155-L159; verified diff):
1. `z1l ? 400` → `z1l ? 0` and `z2l ? 400` → `z2l ? 0`
   (simulator/simulator_flow_labmon2_f2dead_lowsun.json#L130);
2. Reset sun pin: `sunRanks[Math.floor(Math.random() * sunRanks.length)]` → `100`
   (same file #L155). The `Set state (benchmark)` endpoint is unchanged (benchmark scenarios
   still set sun explicitly).

Per-zone ceiling = 25 + monitor(200) + blind(0.50·100 = 50) = **275 lux = rank 2** in both zones
every episode; survivors = Z1Monitor, Z2Monitor, Z1Blinds, Z2Blinds → 2⁴ = 16 probe combos
(generate_faulty_flows.ps1#L144-L154). Profile src/agt/lab_profiles.asl#L798-L810, flags `[w4]`,
training_params (4000, 0.9970), adapt_source `"_labmon2"` (#L838).

### 2.5 lab3 multi-survivor degradation (Phase 2.5B): `lab3_f2dead_lowsun`

Generator (generate_faulty_flows.ps1#L134-L138; verified diff):
1. All four lamp terms zeroed (as in lab3_f2dead): `z1l ? 400`→`0`, `z1l ? 150`→`0`,
   `z2l ? 400`→`0`, `z2l ? 150`→`0` (simulator/simulator_flow_lab3_f2dead_lowsun.json#L130);
2. Reset sun pin: `sunRanks[...]` → `100` (same file #L155).

Rationale as documented: plain lab3_f2dead is only sun-conditionally degraded (0.50·900 = 450 >
300 at high sun); pinning sun = 100 makes the per-zone ceiling
25 + spotlight(150) + 0.50·100 + 0.40·100 = **265 lux = rank 2** every episode; survivors =
Z1Blinds, Z2Blinds, Spotlight → 2³ = 8 probe combos; the spotlight flips from redundant to
essential (generate_faulty_flows.ps1#L113-L133). Profile src/agt/lab_profiles.asl#L774-L786,
flags `[w4]`, training_params (4000, 0.9970), adapt_source `"_lab3"` (#L836).

---

## 3. Phase 3 — dynamics ladder (lab2_slow, lab3_slow)

Both slow flows keep the parent's lux formula but route the blind terms through a **delayed
effective state**: the commanded flag `Z*Blinds` only becomes the effective aperture
`Z*BlindsEff` after `DELAY = 12` env ticks — "BLIND_DELAY_TICKS (≈ 60 s at seconds_per_tick = 5)"
(simulator/simulator_flow_lab2_slow.json#L130; agent-side `seconds_per_tick(5.0)` at
src/agt/illuminance_controller_agent_dynamics.asl#L56). Lamps (and lab3's spotlight) stay
instantaneous. A monotonic `Tick` counter is exposed for the DynamicsLearner (same func). The
countdown logic is the `stepBlind(cmdKey, effKey, remKey)` helper (same func):

```js
var DELAY = 12;
function stepBlind(cmdKey, effKey, remKey) {
    var cmd = flow.get(cmdKey) || false;
    var eff = flow.get(effKey) || false;
    var rem = flow.get(remKey);
    if (cmd !== eff) {
        if (rem === undefined || rem === null) rem = DELAY;
        rem = rem - 1;
        if (rem <= 0) { eff = cmd; rem = null; }
    } else { rem = null; }
    ...
}
```

### 3.1 lab2_slow (port 1895)

Physics (simulator/simulator_flow_lab2_slow.json#L130):

```js
var z1 = 25 + (z1l ? 400 : 0) + (z1bEff ? 0.50 * sun : 0);
var z2 = 25 + (z2l ? 400 : 0) + (z2bEff ? 0.50 * sun : 0);
```

**Delayed term:** the blind's `0.50 * sun` in each zone is gated by `z*bEff` instead of the
commanded flag — a 12-tick lag on both blinds. Blinds start settled (eff == cmd) at reset
(same file #L155). Profile (src/agt/lab_profiles.asl#L423-L435): ont `building_2_slow.ttl`,
port **1895**, suffix `"_lab2_slow"`, training_params **(2000, 0.9960)**; scenarios **reused from
clean lab2** (`benchmark/scenarios_lab2.json`, `train_scenarios_lab2.json` — state schema
identical, comment #L418-L420).

### 3.2 lab3_slow (port 1896)

Physics (simulator/simulator_flow_lab3_slow.json#L130):

```js
var corridor = sp ? 150 : 0;
var z1 = 25 + (z1l ? 400 : 0) + (z2l ? 150 : 0)
       + (z1bEff ? 0.50 * sun : 0) + (z2bEff ? 0.40 * sun : 0) + corridor;
var z2 = 25 + (z2l ? 400 : 0) + (z1l ? 150 : 0)
       + (z2bEff ? 0.50 * sun : 0) + (z1bEff ? 0.40 * sun : 0) + corridor;
```

**Delayed terms:** BOTH blinds' own-zone (`0.50·sun`) **and** cross-zone (`0.40·sun`) terms are
driven by the lagged effective apertures; lamps + spotlight instantaneous (same func). Profile
(src/agt/lab_profiles.asl#L438-L450): ont `building_3_slow.ttl`, port **1896**, suffix
`"_lab3_slow"`, training_params **(3000, 0.9970)**; scenarios reused from clean lab3.

---

## 4. Phase 4 — lab4, lab5 ⚠️ EXTENSION, NOT REQUIRED BY THE ADVISOR'S PHASE 1–3 GOALS

**Flag:** ThesisGoalDescription_important.txt defines exactly three advisor phases (clean
comparison / fault re-alignment / learned dynamics). lab4 and lab5 are a self-added "Phase 4
KNOWLEDGE LADDER (Hidden Dependencies & Energy)" (src/agt/lab_profiles.asl#L305-L328) — clean
labs testing KG-prior exploitation, **not** part of the advisor's Phase 1–3 description.

### 4.1 lab4 — Smart-Plug hidden dependency (port 1897)

Physics (simulator/simulator_flow_lab4.json#L130): identical to lab3 except the Z1 lamp is
AND-gated by a smart plug:

```js
var z1lamp_on = z1l && plug;   // AND-gate: lamp lit only if switch AND plug are ON

var z1 = 25 + (z1lamp_on ? 400 : 0) + (z2l ? 150 : 0)
       + (z1b ? 0.50 * sun : 0) + (z2b ? 0.40 * sun : 0) + corridor;
var z2 = 25 + (z2l ? 400 : 0) + (z1lamp_on ? 150 : 0)
       + (z2b ? 0.50 * sun : 0) + (z1b ? 0.40 * sun : 0) + corridor;
```

The AND-gate is "documented in the KG via ws:powerGates / ws:poweredBy
(building_4_smartplug.ttl §5b)" (same func). Energy: Z1 lamp 1/tick only when actually lit,
plug 0 standby, Z2 lamp 1, spotlight 2. Profile (src/agt/lab_profiles.asl#L331-L343): ont
`building_4_smartplug.ttl`, port **1897**, suffix `"_lab4"`, training_params **(3000, 0.9970)**;
4096 states (comment #L319).

### 4.2 lab5 — Energy differentiation (port 1898)

Physics (simulator/simulator_flow_lab5.json#L130): lab3 topology with two lamps per zone that OR
into a single +400 term:

```js
var z1AnyLamp = z1eff || z1ineff;   // +400 once, never +800
var z2AnyLamp = z2eff || z2ineff;

var z1 = 25 + (z1AnyLamp ? 400 : 0) + (z2AnyLamp ? 150 : 0)
       + (z1b ? 0.50 * sun : 0) + (z2b ? 0.40 * sun : 0) + corridor;
var z2 = 25 + (z2AnyLamp ? 400 : 0) + (z1AnyLamp ? 150 : 0)
       + (z2b ? 0.50 * sun : 0) + (z1b ? 0.40 * sun : 0) + corridor;
```

Energy per tick matches KG `ws:energyCost`: efficient lamp **1**, inefficient lamp **4**,
spotlight **2**, blinds **0**; both lamps on = 5 units for the same +400 lux (same func).
"Energy is NOT in the Q-reward" — it enters only via a KG energy prior and benchmark-time
compliance scoring (src/agt/lab_profiles.asl#L321-L328). Profile (src/agt/lab_profiles.asl#L346-L358):
ont `building_5_energy.ttl`, port **1898**, suffix `"_lab5"`, training_params **(3000, 0.9970)**;
8192 states (comment #L328).

---

## 5. Quick-reference: profile matrix (all new-era labs)

All rows share `light_bounds([50,100,300])`, `sunshine_bounds([50,200,600])`, `sunshine_prob(0.75)`.

| Profile | Port | Zones/targets | Episodes | ε-decay | flags | qtable_suffix | adapt_source | Source (lab_profiles.asl) |
|---|---|---|---|---|---|---|---|---|
| lab1 | 1892 | Z1→3 | 1000 | 0.9920 | [] | `_lab1` | — | #L260-L272 |
| lab2 | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [] | `_lab2` | — | #L275-L287 |
| lab3 | 1894 | Z1→3, Z2→3 | 3000 | 0.9970 | [] | `_lab3` | — | #L291-L303 |
| lab4 ⚠️ext | 1897 | Z1→3, Z2→3 | 3000 | 0.9970 | [] | `_lab4` | — | #L331-L343 |
| lab5 ⚠️ext | 1898 | Z1→3, Z2→3 | 3000 | 0.9970 | [] | `_lab5` | — | #L346-L358 |
| labmon | 1899 | Z1→3 | 1500 | 0.9950 | [] | `_labmon` | — | #L370-L382 |
| labmon2 | 1900 | Z1→3, Z2→3 | 4000 | 0.9975 | [] | `_labmon2` | — | #L396-L408 |
| lab2_slow | 1895 | Z1→3, Z2→3 | 2000 | 0.9960 | [] | `_lab2_slow` | — | #L423-L435 |
| lab3_slow | 1896 | Z1→3, Z2→3 | 3000 | 0.9970 | [] | `_lab3_slow` | — | #L438-L450 |
| lab1_f1dead | 1892 | Z1→3 | 1000 | 0.9920 | [w4] | `_lab1_f1dead` | `_lab1` | #L473-L485 |
| lab2_f1dead | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w4] | `_lab2_f1dead` | `_lab2` | #L489-L501 |
| lab2_f1inv | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w2] | `_lab2_f1inv` | `_lab2` | #L504-L516 |
| lab3_f1dead | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_lab3_f1dead` | `_lab3` | #L520-L532 |
| lab3_f1inv | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w2] | `_lab3_f1inv` | `_lab3` | #L537-L549 |
| lab2_f2dead | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w4] | `_lab2_f2dead` | `_lab2` | #L561-L573 |
| lab2_f2inv | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w2] | `_lab2_f2inv` | `_lab2` | #L577-L589 |
| lab3_f2dead | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_lab3_f2dead` | `_lab3` | #L595-L607 |
| lab3_f2inv | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w2] | `_lab3_f2inv` | `_lab3` | #L612-L624 |
| lab3_f1dead_z2 | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_lab3_f1dead_z2` | `_lab3` | #L643-L655 |
| lab3_f1inv_z2 | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w2] | `_lab3_f1inv_z2` | `_lab3` | #L658-L670 |
| lab3_f1bdead | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_lab3_f1bdead` | `_lab3` | #L676-L688 |
| lab3_f1binv | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w2] | `_lab3_f1binv` | `_lab3` | #L694-L706 |
| lab2_f1bdead | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w4] | `_lab2_f1bdead` | `_lab2` | #L711-L723 |
| lab2_f1binv | 1893 | Z1→3, Z2→3 | 2000 | 0.9960 | [w2] | `_lab2_f1binv` | `_lab2` | #L727-L739 |
| labmon_f1dead | 1899 | Z1→3 | 1500 | 0.9950 | [w4] | `_labmon_f1dead` | `_labmon` | #L748-L760 |
| lab3_f2dead_lowsun | 1894 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_lab3_f2dead_lowsun` | `_lab3` | #L774-L786 |
| labmon2_f2dead_lowsun | 1900 | Z1→3, Z2→3 | 4000 | 0.9970 | [w4] | `_labmon2_f2dead_lowsun` | `_labmon2` | #L798-L810 |

Faulty flags convention: dead components carry `[w4]`, inverted carry `[w2]`; the flags are
"informational here (the adapt agent uses its own observeForFaults detector)"
(src/agt/lab_profiles.asl#L467-L468).

---

## 6. Discrepancies / audit flags

1. **labmon "backup lamp" comments — PARTIALLY RESOLVED 2026-07-08.** The labmon profile
   comment (src/agt/lab_profiles.asl#L361-L368) was rewritten to the two-actuator reality
   ("TWO Causes actuators", "monitor alone reaches rank 2 only (285 lux)", "State = [Z1Level,
   Z1Light, Z1Monitor] = 16 states") and the `SetZ1Backup` mention was removed from
   interactions-labmon.ttl. **Still stale:** the labmon_f1dead comment
   (src/agt/lab_profiles.asl#L743-L745) retains "{Z1Monitor, Z1Backup} = 375 lux" and
   "monitor + backup ON actions" — it does not match the shipped flow (Z1Light +400,
   Z1Monitor +260 only, simulator/simulator_flow_labmon.json#L130).
2. **lab1 free ambient-sun term — RESOLVED 2026-07-08.** The un-gated `0.10 * sun` term was
   deleted from simulator/simulator_flow_lab1.json#L130 and from the physics comment in
   src/resources/building_1_trivial.ttl#L25 (13_logic_report.md §3 item 7). lab1 illuminance
   is now sun-independent; the "clean lab fully aligns with KG" premise (REQ-11) holds.
3. **Faulty lab3 profiles train 4000 episodes vs clean lab3's 3000** (src/agt/lab_profiles.asl#L532
   etc. vs #L303) — budget is not identical across clean vs faulty lab3 cells.
4. **labmon2 clean uses ε-decay 0.9975 but labmon2_f2dead_lowsun uses 0.9970**
   (src/agt/lab_profiles.asl#L408 vs #L810).
5. **Sun pinning in `*_lowsun` variants affects only training resets** (`Reset episode` #L155);
   the `Set state (benchmark)` endpoint still accepts any `Sunshine` value, and the benchmark
   scenario files are reused from the clean parents (src/agt/lab_profiles.asl#L777-L778,
   #L801-L802).
6. **`simulator/generate_flows.ps1` exists** alongside `generate_faulty_flows.ps1`; this audit
   verified the shipped JSONs directly (env func #L130 diffs), so the clean-flow generator was
   not needed as evidence.
