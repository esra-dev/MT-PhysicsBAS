# Phase 2.6 — KG-Silent Monitor Variants (misdocumented / undocumented KG)

## Motivation

Phase 2.5 introduced the monitor labs (`labmon`, `labmon2`) where the monitor's
light side-effect is **fully modeled** in the KG (`ws:MonitorStereotype` with an
`elem:luminiscence` dependent variable), so the KG-primed agent is told up front
that the monitor can brighten the room.

Phase 2.6 asks the complementary question: **what happens when the monitor can
physically brighten the room, but the stereotype layer never says so?** The
monitor still exists in the lab (identical physics simulation) and still exists
in the KG (located, WoT-actuatable equipment) — only the *behavioral knowledge*
is removed, in two graded ways:

| Variant | KG state | Building ontology |
|---|---|---|
| **A — info-only** (`*_infoonly`) | MISDOCUMENTED: the monitor HAS a stereotype, but its mechanism's only dependent variable is `ws:displayed_information`. The light side-effect (`elem:luminiscence` DV, `elem:increases`, photon outlet connection point) is missing. | `building_6_monitor_infoonly.ttl`, `building_7_dualmonitor_infoonly.ttl` |
| **B — no stereotype** (`*_nostereo`) | UNDOCUMENTED: the monitor has NO `elem:hasBehavioralStereotype` triple at all. Instance + WoT mapping only. | `building_6_monitor_nostereo.ttl`, `building_7_dualmonitor_nostereo.ttl` |

The Phase 2.5 parents are untouched, so the experiment supports a **3-way
contrast**: full KG (`labmon`/`labmon2`) vs misdocumented KG (`*_infoonly`) vs
undocumented KG (`*_nostereo`), over identical physics.

Research question: when the task lamp(s) fail and the goal becomes unreachable,
do the agents still *adapt* and adopt the unmodeled monitor as the best-effort
fallback light source — and does the KG-primed agent (whose priors cover every
component EXCEPT the monitor) do so better/faster/more reliably than the
tabula-rasa agent, or does the knowledge gap erase (or invert) its advantage?

## Mechanics — KG-SILENT actions under the action-space inversion

> **Updated 2026-07-10:** the original Phase 2.6 implementation added KG-silent
> actions via a *fallback* query appended after the stereotype-based discovery.
> This has been superseded by the **action-space inversion** (see
> [ACTION_SPACE_INVERSION.md](ACTION_SPACE_INVERSION.md)): the action space is
> now PRIMARILY enumerated from the WoT TD contract
> (`WOT_CONTRACT_ACTUATOR_QUERY`), and the stereotype query is a pure
> *enrichment* pass. The observable semantics below are unchanged
> (equivalence-audited); only the architecture is cleaner.

The action registry for **both** learner arms is built by
`StereotypeReasoner.discoverActuators`: pass 1 enumerates every component
carrying the WoT contract (`ws:hasWoTActionSemanticType` +
`elem:hasComponentAction`) into the registry; pass 2 (stereotype enrichment)
annotates actions with physics knowledge. A monitor whose stereotype makes no
Illuminance claim (or that has no stereotype at all) is simply never enriched
and stays a **KG-SILENT** action (`ActionInfo.kgSilent = true`) with:

- `affectedZones = {}` — the KG makes **no zone-level illuminance claim**, so:
  - no constructive Q-init bonus (Rule 5 requires `affectedZones.contains(zone)`),
  - no shared-actuator / cross-zone penalties (Rules 3/4),
  - `getActionPrediction` claims only the actuator bit — nothing to falsify;
- `hasIV = false`, `energyCost = 0`;
- `observeForFaults` **abstains entirely** on KG-silent actions (there is no
  Expected-vs-Actual prediction to falsify; this also protects the essential
  fallback lever from a spurious bit-level dead flag);
- bit-level redundancy handling (Rule 1 / soft prior) still applies — that is
  TD-contract knowledge (toggling an already-ON switch is a no-op), not
  stereotype physics.

On every fully-stereotyped lab (lab1..lab5, labmon, labmon2) every enumerated
action is enriched, so no KG-silent actions appear — verified by smoke test and
by the `verifyActionRegistry` golden check: parent labmon/labmon2 registries
are bit-for-bit unchanged. (The legacy `custom`/`custom2..9` labs DO carry
KG-silent radiator/corridor actions — their WoT mappings expose actuators the
lighting stereotypes never covered; see ACTION_SPACE_INVERSION.md §5.)

Verified behaviour on the variants (smoke test, all-dark state, goal rank 3):

| Action | Parent labmon | infoonly / nostereo |
|---|---|---|
| `SetZ1Light=ON` | prior **+22.5**, predicts zone rise | prior **+22.5**, predicts zone rise |
| `SetZ1Monitor=ON` | prior **+22.5**, predicts zone rise | prior **0.0**, KG-SILENT, no zone claim |

So in the variants the KG-primed arm keeps its priors on all *documented*
components and is genuinely neutral on the monitor; the tabula-rasa arm is
zero-initialised everywhere, as always. Both arms can toggle the monitor and
must learn its +lux effect from reward alone.

Variants A and B are **behaviourally identical** for the reasoner (both are
KG-silent about the monitor's light effect). The contrast between them is
representational — what the KG documents (a partial stereotype vs nothing) —
which matters for KG-side diagnosis, reporting and the thesis discussion, not
for the Q-learning dynamics.

## Why the degraded-goal machinery still works

The Phase 2.5b reachability probe is **physical**: after blacklisting, the
adapt agent enumerates ON/OFF combinations of the *surviving* actuators, drives
the real lab into each combination and records the observed rank
(`beginReachabilityProbe` / `getProbeCombo` / `recordProbeRank`). It never
consults stereotype claims, so an unmodeled monitor is probed like any other
survivor and its real +lux contribution is observed. The effective goal is
therefore still correctly lowered to rank 2 and the user notified — the KG gap
affects only *how fast the policy re-converges*, which is exactly the
experimental signal.

Fault detection of the lamps is unaffected: the lamps keep full stereotypes,
predictions and instant dead/inverted adjudication in all variants.

## New profiles (lab_profiles.asl)

Clean (train both arms from scratch; same flows/ports as the Phase 2.5 parents):

| Profile | Ontology | Flow / port | Q-suffix |
|---|---|---|---|
| `labmon_infoonly` | building_6_monitor_infoonly.ttl | simulator_flow_labmon.json / 1899 | `_labmon_infoonly` |
| `labmon_nostereo` | building_6_monitor_nostereo.ttl | simulator_flow_labmon.json / 1899 | `_labmon_nostereo` |
| `labmon2_infoonly` | building_7_dualmonitor_infoonly.ttl | simulator_flow_labmon2.json / 1900 | `_labmon2_infoonly` |
| `labmon2_nostereo` | building_7_dualmonitor_nostereo.ttl | simulator_flow_labmon2.json / 1900 | `_labmon2_nostereo` |

Faulty (adapt; same fault flows as the Phase 2.5 cells; warm-load from the
MATCHING clean variant via `adapt_source/2`):

| Profile | Fault | Flow | Warm-load source |
|---|---|---|---|
| `labmon_infoonly_f1dead` | primary lamp dead | simulator_flow_labmon_f1dead.json | `_labmon_infoonly` |
| `labmon_nostereo_f1dead` | primary lamp dead | simulator_flow_labmon_f1dead.json | `_labmon_nostereo` |
| `labmon2_infoonly_f2dead_lowsun` | both lamps dead + sun pinned rank 1 | simulator_flow_labmon2_f2dead_lowsun.json | `_labmon2_infoonly` |
| `labmon2_nostereo_f2dead_lowsun` | both lamps dead + sun pinned rank 1 | simulator_flow_labmon2_f2dead_lowsun.json | `_labmon2_nostereo` |

State spaces are identical to the parents (16 / 4096 states), so clean→faulty
warm-loading within each variant family is shape-compatible. Since the
action-space inversion (2026-07-10) the variant registries also share the
PARENT'S action ordering (the WoT-contract enumeration is alphabetical, so the
monitors sit at the same indices as in labmon2) — and ordering is no longer
load-bearing anyway, because all persisted per-action artifacts are
label-remapped on load. Compare actions by label regardless.

## How to run

```powershell
# 1. Train the clean variants (both arms), e.g. single-zone info-only:
.\run_full_project.ps1 -OnlyProfiles labmon_infoonly
.\run_full_project.ps1 -OnlyProfiles labmon_nostereo

# 2. Adapt in the faulty cells (starts the faulty flow itself):
.\run_phase2_adapt.ps1 -AdaptProfiles labmon_infoonly_f1dead
.\run_phase2_adapt.ps1 -AdaptProfiles labmon_nostereo_f1dead

# Dual-zone family:
.\run_full_project.ps1 -OnlyProfiles labmon2_infoonly
.\run_phase2_adapt.ps1 -AdaptProfiles labmon2_infoonly_f2dead_lowsun

# Pipeline smoke check first (recommended):
.\run_phase2_adapt.ps1 -Smoke -AdaptProfiles labmon_infoonly_f1dead -Modes ql_true
```

The KG-silent discovery announces itself in the training/adapt logs:

```
WARNING: KG-SILENT actuator action: SetZ1Monitor=ON — WoT-mapped but the
stereotype layer makes no illuminance claim for it (missing/partial stereotype).
No priors, no fault adjudication; learnable by reward only.
```

## What to look for (hypotheses)

1. **Clean training**: both arms should still converge to the lamp policy (the
   monitor is never needed). ql_true's convergence advantage should be slightly
   smaller than on the full-KG parent (one prior fewer), but present.
2. **Faulty adaptation**: detection of the dead lamp(s) is unchanged
   (stereotyped Causes lamps). Recovery now requires *discovering* the
   monitor's value with no prior. Compare `RecoveryEpisodes` across the 3-way
   KG contrast per family:
   - full KG (labmon_f1dead / labmon2_f2dead_lowsun): KG points at the monitor;
   - info-only / nostereo: KG is silent — does ql_true still beat ql_false
     (residual structural priors + faster elimination of dead-end actions), or
     does the advantage vanish/invert (misleading redundancy-free neutrality)?
3. **Best-effort degradation**: in all cells the physical probe should prove
   rank 3 unreachable, lower the effective goal to rank 2 and alert the user —
   independent of the KG variant.

## Files touched

- `src/env/tools/StereotypeReasoner.java` — KG-silent discovery (originally a
  fallback query; since the action-space inversion the primary
  `WOT_CONTRACT_ACTUATOR_QUERY` enumeration + stereotype enrichment, see
  ACTION_SPACE_INVERSION.md), `ActionInfo.kgSilent`.
- `src/env/tools/QLearner.java` — `observeForFaults` abstains on KG-silent
  actions.
- `src/resources/building_6_monitor_{infoonly,nostereo}.ttl`,
  `src/resources/building_7_dualmonitor_{infoonly,nostereo}.ttl` — variant KGs.
- `src/agt/lab_profiles.asl` — 8 profiles + 4 `adapt_source/2` entries.
- `config/run_config.json` — port/flow/suffix/state-dim maps (top level +
  phase2 block), `adapt_profiles`.
- `run_full_project.ps1` — `$KnownProfiles`, `$ProfileQtableSuffix`,
  `$Simulators`.

No simulator flow, TD, or scenario JSON was added — the variants reuse the
Phase 2.5 parents' physics artifacts verbatim, which is the point: reality is
constant, only the documentation changes.
