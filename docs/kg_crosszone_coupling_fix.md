# KG Cross‑Zone Coupling Stereotypes — Implementation Notes (lab3)

**Status:** implemented, compiles, audited. Default behaviour of the headline
factorial arm is **unchanged** (zero blast radius) until the new lever is
explicitly enabled.

**Scope:** lab3 (`building_3_complex.ttl`, port 1894) cross‑zone light spill.
This is the *Connection Stereotype* design (**Option B**) built on the
`Stream` / `StreamKind` primitives (**Option A**), as approved.

---

## 1. TL;DR

The lab3 KG declares four *cross‑zone* spill arcs (`brick:feeds`) — a lamp or
blind in one zone bleeds light into the **other** zone:

```
CeilingLight_Z1 → LightSensor_Z2   (+50 lux)
CeilingLight_Z2 → LightSensor_Z1   (+50 lux)
Blind_Z1        → LightSensor_Z2   (0.25·Sun)
Blind_Z2        → LightSensor_Z1   (0.25·Sun)
```

The reasoner used to convert every such arc into a **direction‑only ±1 rank
prediction** for the neighbour zone — i.e. it claimed "activating this actuator
raises the neighbour's discretised illuminance rank". But the spill is
**sub‑rank**: against the lab3 discretisation bounds `[50, 100, 300]`, a +50 lux
lamp bleed (or `0.25·Sun` blind bleed) almost never moves the neighbour's rank.

A standalone structural audit over the **entire** lab3 transition space
(32 actuator configs × 4 sun levels, off→on toggles) quantifies this:

| Prediction | WRONG |
|---|---|
| same‑zone (primary) | **52.3 %** (134/256) |
| **cross‑zone (spill)** | **80.5 %** (206/256) |
| └ lamp spill (+50 lux) | 81.2 % (104/128) |
| └ blind spill (0.25·Sun) | 79.7 % (102/128) |

The fix gives the KG a way to say *"I know this arc EXISTS (structure), but it is
a **weak** coupling whose magnitude I will **not** predict at rank granularity —
the RL agent must learn the value."* That is exactly the thesis position:
**the KG declares the spillage structure; RL learns the magnitudes.**

It is delivered in two independent, separately‑gated parts:

* **Part A** — a weak (`SECONDARY`) cross‑zone coupling makes **no** rank claim.
  This removes the 80.5 %‑wrong signal that was globally deflating the
  adaptive‑trust calibration for the whole action.
* **Part B** — an **optional, default‑OFF** optimistic Q‑init "exploration
  head‑start" that nudges the agent to *try* the cross‑zone lever (so it can
  then learn its true value). Enabled only via the new `phase1_kg_xzone`
  profile / `-Dstereo.crossZoneBonus`.

---

## 2. Why Option B (Connection Stereotype) on Option A primitives

| Option | Idea | Verdict |
|---|---|---|
| **A — Stream / StreamKind primitive** | Tag each arc's transferred "stuff" with a stream kind (e.g. a weak coupling stream). | Necessary vocabulary, but a `StreamKind` alone does not tell the reasoner *how to treat* the arc. |
| **B — Connection Stereotype (chosen)** | Reify each `brick:feeds` arc as an `elem:InternalConnection` carrying a **coupling stereotype** (`PrimaryOpticalCoupling` / `WeakOpticalCoupling`), exactly mirroring how a *component* carries a behavioural stereotype. | Reuses the existing stereotype → mechanism → stream machinery; lets the reasoner read a per‑arc **magnitude class**; leaves the numeric gain to RL. |

Option B is implemented **on top of** Option A: the `WeakOpticalCoupling`
stereotype points at the Option‑A `ws:SecondaryCouplingStream` `StreamKind`, and
the `PrimaryOpticalCoupling` stereotype reuses the existing
`ws:IndoorLightingStream`. So the stream primitive is the substrate; the
connection stereotype is the classifier built on it.

**Magnitude is deliberately left unspecified.** The new mechanism
`ws:pm_secondary_illumination_transfer` declares only *that* it increases
luminance (`elem:increases elem:luminiscence`), with **no** gain — this is the
Phase‑3 write‑back target where the learned value would eventually be recorded.

---

## 3. The ontology model (`src/resources/building_3_complex.ttl`)

All additions are **additive**; no existing triple was changed or removed. The
original four `brick:feeds` arcs are kept intact (the reasoner still discovers
them); the new triples *annotate* them with a magnitude class.

### 3.1 New object properties (near the top, after `ws:stateSlotRole`)

```ttl
ws:connSource a owl:ObjectProperty ; rdfs:label "connection source component" .
ws:connTarget a owl:ObjectProperty ; rdfs:label "connection target component" .
```

### 3.2 New `StreamKind` (Option‑A primitive, §3)

```ttl
ws:SecondaryCouplingStream a owl:NamedIndividual, elem:StreamKind ;
    rdfs:label "Secondary (cross-zone) optical coupling stream" .
```

### 3.3 Coupling mechanisms + stereotypes (new §4b)

```ttl
ws:pm_primary_illumination_transfer   a … elem:PhysicalMechanism ;
    elem:hasDependentVariable elem:luminiscence ; elem:increases elem:luminiscence .
ws:pm_secondary_illumination_transfer a … elem:PhysicalMechanism ;
    elem:hasDependentVariable elem:luminiscence ; elem:increases elem:luminiscence .
    # gain intentionally ABSENT — learned by the Q-agent (Phase 3)

ws:PrimaryOpticalCoupling a … elem:Stereotype ;
    elem:hasPhysicalMechanism ws:pm_primary_illumination_transfer ;
    elem:hasStreamKind        ws:IndoorLightingStream .
ws:WeakOpticalCoupling    a … elem:Stereotype ;
    elem:hasPhysicalMechanism ws:pm_secondary_illumination_transfer ;
    elem:hasStreamKind        ws:SecondaryCouplingStream .
```

### 3.4 Reified connections (new §7b) — one per arc

The four **cross‑zone** arcs are tagged `WeakOpticalCoupling`; the four
**same‑zone** arcs are tagged `PrimaryOpticalCoupling` (documentary contrast
only — same‑zone arcs are excluded from the cross‑zone query by the zone
filter, so `PrimaryOpticalCoupling` == legacy behaviour).

```ttl
ws:conn_CLz1_to_LSz2 a … elem:InternalConnection ;
    ws:connSource lab:CeilingLight_Z1 ; ws:connTarget lab:LightSensor_Z2 ;
    elem:hasStructuralStereotype ws:WeakOpticalCoupling .
# … 3 more cross-zone (WEAK) + 4 same-zone (PRIMARY)
```

> **Why `elem:hasStructuralStereotype` (not `hasBehavioralStereotype`)?** The
> actuator‑discovery and cross‑zone queries match components via
> `elem:hasBehavioralStereotype` and mechanisms via
> `elem:hasManipulatedVariable`. The connection stereotypes use a **different**
> predicate (`hasStructuralStereotype`) and their mechanisms have **no**
> `hasManipulatedVariable`, so they are invisible to those queries and cannot be
> mis‑picked as actuators. Verified.

> **Prefix safety.** The reasoner's SPARQL `PREFIX` block and the TTL
> `@prefix` declarations are byte‑identical
> (`ws: → http://example.org/was/lab/stereotypes#`,
> `elem: → http://w3id.org/elementary#`,
> `lab: → http://example.org/was/lab#`), so the new `OPTIONAL` join binds.
> Verified.

---

## 4. The reasoner changes (`src/env/tools/StereotypeReasoner.java`)

> This is a protected file; the edit was explicitly approved.

### 4.1 Capture the coupling class

* `CrossZoneEffect` gains a nested `enum CouplingClass { PRIMARY, SECONDARY }`
  and a field `couplingClass` that **defaults to `PRIMARY`** (= legacy).
* `CROSS_ZONE_FEEDS_QUERY` projects a new `?couplingStereo` and adds an
  `OPTIONAL { ?conn ws:connSource ?sourceComp ; ws:connTarget ?targetSensor ;
  elem:hasStructuralStereotype ?couplingStereo }` block.
* `discoverCrossZoneFeeds` reads `?couplingStereo`; a URI ending in
  `WeakOpticalCoupling` ⇒ `SECONDARY`, otherwise `PRIMARY`. The class is logged.

Because the default is `PRIMARY`, **every other lab (custom2…custom9, lab1,
lab2) is byte‑identical** — they declare no reified connections, so every arc
stays `PRIMARY`.

### 4.2 Part A — stop the false rank claim (`getActionPrediction`, step 3)

```java
for (CrossZoneEffect cz : crossZoneEffects) {
    if (cz.actionIndex != actionIdx) continue;
    if (cz.couplingClass == CrossZoneEffect.CouplingClass.SECONDARY) continue; // ← Part A
    … pred[slot] += dir;   // only PRIMARY couplings co-sign the direction
}
```

A `SECONDARY` coupling now emits **0** for the neighbour slot. The adaptive‑trust
calibration in `QLearner.calculateQ` skips zero predictions (`predSign == 0 →
continue`), so the unreliable cross‑zone signal can no longer deflate the
action's calibration multiplier.

### 4.3 Part B — gated cross‑zone exploration prior (`getInitPenaltyForZone`, new Rule 6)

```java
private static final double CROSS_ZONE_BONUS_MAG =
    Double.parseDouble(System.getProperty("stereo.crossZoneBonus", "0.0")); // default OFF

// Rule 6 (after the existing Rule 5 positive-init):
if (CROSS_ZONE_BONUS_MAG > 0.0 && penalty == 0.0 && ai.wotValue) {
    for (CrossZoneEffect cz : crossZoneEffects) {
        if (cz.actionIndex == actionIdx && cz.targetZoneIdx == zoneIdx
                && cz.couplingClass == SECONDARY) {
            int gap = goal[zoneIdx] - stateVec[zoneLevelIndices[zoneIdx]];
            if (gap > 0) return CROSS_ZONE_BONUS_MAG * gap * INIT_PENALTY_SCALE;
        }
    }
}
```

With `crossZoneBonus = 0.0` (the default) Rule 6 never fires. When enabled it
gives a small optimistic head‑start (per rank of remaining gap) to a `SECONDARY`
cross‑zone activation whose spill target is still below goal — nudging the agent
to *try* the lever, after which the true (sub‑rank) value is learned by the
Bellman updates. It is bounded far below the primary Rule‑5 bonus
(`INIT_BONUS_MAG = 15`).

### 4.4 Which arm does each part actually affect? (important)

The two parts touch **different** consumers, which are active in **different**
factorial arms:

| Channel | Consumer | Gated by | Active in |
|---|---|---|---|
| **Part A** (`getActionPrediction`) | adaptive‑trust calibration (`QLearner.calculateQ`) | `adaptive_trust = true` | `phase1_full`, default `phase1` |
| **Part B** (`getInitPenaltyForZone` Rule 6) | optimistic Q‑init (`initWithStereotypes`) | `crossZoneBonus > 0` | `phase1_kg_xzone` (and any profile that sets the flag) |

Consequences:

* In the **headline** `phase1_kg_only` arm (`adaptive_trust = false`,
  `crossZoneBonus = 0`): Part A's *training* path is inactive **and** Part B is
  off ⇒ **the learned policy is unchanged**. (Part A still changes the
  diagnostic `getPredictedDelta` / `classifyWeaknesses` outputs, which is
  strictly more correct, but does not alter the headline result.)
* Part A's benefit shows up in **adaptive‑trust** arms (`phase1_full`), where the
  cross‑zone over‑claim was the channel that produced the n=10 +38.09‑step
  first‑goal regression on lab3.
* Part B is the lever to test "does structure‑aware exploration help the
  KG‑only arm on lab3?" via `phase1_kg_xzone`.

### 4.5 Deliberate asymmetry with the existing Rule 3 (documented, not a bug)

The existing **Rule 3** (cross‑zone *overshoot* penalty, `−50`) still fires for
`SECONDARY` arcs when the neighbour is already at/above goal. This is kept on
purpose:

* Rule 3 is a **local, recoverable, state‑specific** Q‑init nudge (×
  `INIT_PENALTY_SCALE = 0.5`) — "don't add light to an already‑satisfied
  neighbour." Conservative and cheap to unlearn.
* Part A fixed a **global** harm — a wrong prediction that deflated the action's
  calibration across *all* states.

If you later prefer full symmetry ("a weak coupling makes no claim in *either*
direction"), gate Rule 3 by `couplingClass != SECONDARY` too — but note that
**does** change the headline `phase1_kg_only` arm, so re‑validate it. It was
intentionally left out of this change to preserve zero headline blast radius.

---

## 5. Config & wiring

| File | Change |
|---|---|
| `build.gradle` | added `'stereo.crossZoneBonus'` to `_httpKeys` (forwarded as a `-D` system property to the child JVM). |
| `run_full_project.ps1` | learning block now forwards `-Pstereo.crossZoneBonus=<cross_zone_bonus>`; **and** `phase1_kg_xzone` added to the `-RunMode` `[ValidateSet]`. |
| `run_full_project_parallel.ps1` | `phase1_kg_xzone` added to the `-RunMode` `[ValidateSet]`. |
| `config/run_config.json` | global `learning.cross_zone_bonus = 0.0` (default OFF); new profile **`phase1_kg_xzone`** = clone of `phase1_kg_only` + `learning_overrides.cross_zone_bonus = 3.0`. |

Verified resolution through `scripts/Read-RunConfig.ps1` (generic
`learning_overrides`‑over‑`learning` merge):

```
phase1_kg_xzone → cross_zone_bonus=3.0  reward_shaping=none  adaptive_trust=False  stereo_init_bonus=15.0
phase1_kg_only  → cross_zone_bonus=0.0  reward_shaping=none  adaptive_trust=False
```

## 6. Audit tool (`analysis/crosszone_prediction_audit.py`)

Added a `--secondary-zero` flag that models the Part‑A fix: `WeakOpticalCoupling`
arcs make no rank claim, so they are removed from the wrong‑claim tally.

```
python analysis/crosszone_prediction_audit.py --structural-only                 # legacy: cross-zone WRONG 80.5%
python analysis/crosszone_prediction_audit.py --structural-only --secondary-zero # fixed: 0 cross-zone claims
```

---

## 7. Complete file‑change list

| File | Protected? | Nature |
|---|---|---|
| `src/resources/building_3_complex.ttl` | no | additive ontology (props, StreamKind, mechanisms, stereotypes, reified connections) |
| `src/env/tools/StereotypeReasoner.java` | **yes (approved)** | coupling class capture + Part A + Part B (gated) |
| `build.gradle` | no | `_httpKeys` += `stereo.crossZoneBonus` |
| `run_full_project.ps1` | no | forward flag + ValidateSet |
| `run_full_project_parallel.ps1` | no | ValidateSet |
| `config/run_config.json` | no | global default + `phase1_kg_xzone` profile |
| `analysis/crosszone_prediction_audit.py` | no | `--secondary-zero` flag |

`QLearner.java` was **not** modified — its consumers already handle a zero
prediction (`predSign == 0 → continue`).

---

## 8. What to run, in order

All commands are run from the workspace root in **Windows PowerShell**
(`c:\Users\esrad\Downloads\MT-Esra-V1 - Copy`). Do not use `&&`.

### Step 1 — Compile (verifies the reasoner change)

```powershell
.\gradlew compileJava --console=plain
```

Expect `BUILD SUCCESSFUL`. (Done once already.)

### Step 2 — Validate the structural claim (no training, seconds)

```powershell
python analysis/crosszone_prediction_audit.py --structural-only
python analysis/crosszone_prediction_audit.py --structural-only --secondary-zero
```

Expect cross‑zone WRONG **80.5 %** (legacy) and **0 claims** (fixed).

### Step 3 — Headline regression guard (must be UNCHANGED)

Run the headline KG‑only arm and confirm it is unaffected (Part A inert here,
Part B off):

```powershell
.\run_full_project.ps1 -RunMode phase1_kg_only
# or, faster, in parallel:
.\run_full_project_parallel.ps1 -RunMode phase1_kg_only -MaxParallel 2
```

Compare lab1/lab2/lab3 metrics against your existing `phase1_kg_only` baseline —
they should match within seed noise (ideally identical for a fixed seed).

### Step 4 — Part B lever (the new experiment) on lab3

```powershell
.\run_full_project.ps1 -RunMode phase1_kg_xzone
# or parallel:
.\run_full_project_parallel.ps1 -RunMode phase1_kg_xzone -MaxParallel 2
```

This is `phase1_kg_only` **plus** `cross_zone_bonus = 3.0`. Compare its lab3
`ql_true` − `ql_false` first‑goal / coverage delta against `phase1_kg_only`.

### Step 5 — Part A benefit (full‑stack arm) on lab3

```powershell
.\run_full_project.ps1 -RunMode phase1_full
```

`adaptive_trust = true` here, so Part A is active. Confirm the previously‑measured
lab3 first‑goal regression (≈ +38 steps, arm D vs B at n=10) recovers.

### Step 6 — Statistics (the system is non‑monotonic — do not eyeball)

Re‑run each arm across multiple seeds and compare with a paired CI, e.g.:

```powershell
foreach ($s in 1..10) { .\run_full_project.ps1 -RunMode phase1_kg_xzone -RunSeed $s }
```

Then run your existing analysis/aggregation over the produced
`benchmark_results_*` / `first_goal_*` / `coverage_*` CSVs. A single run can move
either way by chance; only the multi‑seed paired delta is interpretable.

### Step 7 — Overnight A/B on GitHub Actions (n=10, the before/after)

Two refs are on `origin`:

* `main` (`7ac37a1`) — **BEFORE** (current setup, no cross‑zone change; the basis
  of the prior n=10 Phase‑1 runs).
* `kg-crosszone-coupling` — **AFTER** (this change; `phase1_kg_xzone` profile adds
  the Part‑B cross‑zone exploration prior).

Fire both dispatches once (PowerShell, repo root). The existing `phase1.yml`
fans the full n=10 factorial across GitHub‑hosted runners; both dispatches share
concurrency group `phase1`, so the **second queues and runs automatically after
the first finishes** — exactly "first the current setup, then the change":

```powershell
# 1) BEFORE — current setup (main, KG‑only headline arm)
gh workflow run phase1.yml --ref main `
  -f run_mode=phase1_kg_only -f seeds=1,2,3,4,5,6,7,8,9,10 -f publish_results=false

# 2) AFTER — the change (feature branch, cross‑zone prior ON)
gh workflow run phase1.yml --ref kg-crosszone-coupling `
  -f run_mode=phase1_kg_xzone -f seeds=1,2,3,4,5,6,7,8,9,10 -f publish_results=false
```

`publish_results=false` keeps both runs from colliding on the `results` branch;
each run still uploads a self‑contained **`phase1-consolidated`** artifact
(retained 90 days). **Do not queue a third `phase1` run while these two are
pending** — GitHub keeps only one running + one pending per concurrency group and
would cancel the older pending one.

Monitor:

```powershell
gh run list --workflow=phase1.yml -L 5
```

Download + compare when both are done (`<BEFORE_ID>` / `<AFTER_ID>` from the list):

```powershell
gh run download <BEFORE_ID> -n phase1-consolidated -D ab/before
gh run download <AFTER_ID>  -n phase1-consolidated -D ab/after
```

Compare these files between `ab/before` and `ab/after` (focus on the **lab3
`ql_true`** rows; lab1/lab2 are a negative control and should be identical — the
prior never fires without a SECONDARY cross‑zone connection, which only lab3 has):

| File (`analysis/out/`) | What to read |
|---|---|
| `learning_speed_tests.csv` | `auc_goal` (↑ better), `mean_first_goal` / `episodes_to_threshold` (↓ better) |
| `summary_table_ci.csv` | per‑arm mean + 95 % bootstrap CI |
| `paired_tests.csv` | redundant‑action count + same‑goal‑rate (parity check) |

**Part‑A (full‑stack) follow‑up, optional.** After the two above finish, the
regression‑recovery story (Part A is active only when `adaptive_trust=true`) can
be run the same way — again ≤2 queued at a time:

```powershell
gh workflow run phase1.yml --ref main                  -f run_mode=phase1_full -f seeds=1,2,3,4,5,6,7,8,9,10 -f publish_results=false
gh workflow run phase1.yml --ref kg-crosszone-coupling -f run_mode=phase1_full -f seeds=1,2,3,4,5,6,7,8,9,10 -f publish_results=false
```

---

## 9. Honest caveats & limitations

1. **Non‑monotonic system.** Outcomes are not monotone in the hyper‑parameters;
   a single seed proves nothing. Validate every claim with the multi‑seed paired
   CI (Step 6).
2. **The lab3 spill is genuinely sub‑rank.** +50 lux (lamp) and `0.25·Sun`
   (blind) rarely cross the `[50, 100, 300]` rank boundaries. So:
   * Part A is unambiguously correct (it stops claiming a rank change that does
     not happen).
   * Part B will make the agent *try* the cross‑zone lever, but RL will correctly
     learn that its value is **small**. If the goal is always reachable with a
     zone's **own** actuators (true in current lab3 — the same‑zone lamp alone
     gives +400 lux), cross‑zone activation is never strictly *required*, so the
     measured lab3 gain from Part B may be modest. The clearest "KG avoids
     redundant actions" effect on lab3 comes from the **existing** overshoot
     avoidance (Rule 3) plus Part A removing the calibration harm.
3. **Optional simulator magnitude bump (NOT done — needs separate sign‑off).**
   To make cross‑zone coupling a *strong, clearly learnable* lever for a dramatic
   lab3 demonstration, the spill magnitude in the Node‑RED physics
   (`simulator_flow_lab3.json` / `building_3_complex.ttl` header) would need to
   be raised to ≈ rank‑moving size (e.g. +150 lux). That changes the
   environment's ground truth and the meaning of the lab, so it is **out of
   scope** for this change and requires your explicit approval before I touch the
   simulator.

---

## 10. Rollback

* **Disable Part B only:** leave everything in place and just don't use the
  `phase1_kg_xzone` profile (default `cross_zone_bonus = 0.0`).
* **Disable Part A behaviour:** in `building_3_complex.ttl`, retag the four
  cross‑zone connections from `ws:WeakOpticalCoupling` to
  `ws:PrimaryOpticalCoupling` (they revert to legacy co‑signing) — no code change
  needed, because the default class is `PRIMARY`.
* **Full revert:** `git checkout -- <files in §7>` (these are tracked source
  files; revert is clean since all edits were additive).
