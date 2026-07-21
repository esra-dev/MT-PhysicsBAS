# Phase 1 — Complete Critical Audit (2026-07-19)

> **CORRECTION NOTICE (2026-07-21).** Parts A-D and the original result conclusions in
> this document are not current. A subsequently identified scenario-scheduler defect,
> invalid legacy first-goal aggregation, and wall-clock energy metric materially affect
> the Phase 1 evidence. The +53.30-episode `mean_first_goal` interpretation is withdrawn.
> All existing Phase 1 results are historical/protocol-affected pending protocol-v2
> reruns. See `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`.

**Auditor:** independent read-through of the repository at branch
`kg-crosszone-coupling-mid`, working tree of 2026-07-19 (last commit `4512ad0`).
**Scope:** Phase 1 only (the "knowledge-graph acceleration on clean labs" experiment).
**Ground truth for results:** the pooled-20 Plan B primary analysis
(`phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv`), per the
registered supersession rule of Addendum 2026-07-18c/19c. Older numbers (the n = 10
seed results, the pre-inversion runs) are reported here only as history and are marked
superseded.

**Evidence tags used throughout:**

- **[VERIFIED]** — I checked this myself in the code, data files, or git history during
  this audit.
- **[STATED]** — asserted in the project's write-ups; I could not (or did not) verify it
  independently from this machine.
- **[INFERRED]** — my own reading or judgment; could be wrong.

**Plain-language glossary (terms used throughout, defined once):**

- **MAS / JaCaMo** — a *multi-agent system* framework combining Jason (a language for
  writing software "agents" with beliefs, goals, and plans) and CArtAgO ("artifacts" —
  Java objects the agents call like tools).
- **Knowledge graph (KG) / ontology** — a machine-readable description of the lab
  written as subject–predicate–object triples in Turtle (`.ttl`) files; here it
  describes devices (lamps, blinds), their physics ("stereotypes"), and room topology.
- **SPARQL** — the query language used to read the knowledge graph.
- **Q-learning** — a reinforcement-learning algorithm that learns a table
  (the "Q-table") scoring every (situation, action) pair; the agent gradually improves
  the table by trial and error.
- **Arm** — one experimental configuration (e.g., "KG prior on, everything else off").
- **Seed** — the number that initialises the random-number generator; running the same
  experiment with 10 different seeds gives 10 independent replicates.
- **CI** — continuous integration; here, GitHub Actions, which runs the whole
  experiment in the cloud and stores the outputs ("artifacts").
- **Bootstrap** — a statistical method that estimates uncertainty by resampling the
  observed data many times (here 10 000 times).
- **BH / FDR / q-value** — Benjamini–Hochberg correction for running many statistical
  tests at once; a q-value is a p-value adjusted for the number of tests (m) in the
  declared "family".
- **Cliff's δ (delta)** — an effect-size measure in [−1, 1]; δ = 1.0 means every value
  in one group exceeds every value in the other.
- **lux** — the physical unit of illuminance (light level on a surface).
- **Rank** — the discretised light level used by the agent: rank 0–3, with boundaries
  at 50 / 100 / 300 lux indoors (rank 3 = at or above 300 lux) [VERIFIED —
  `src/resources/building_2_intermediate.ttl:136-138`; `src/agt/lab_profiles.asl:266`].

---

# PART A — WHAT EXISTS

## A1. What was built in Phase 1, and what changed relative to the pre-Phase-1 baseline

**The pre-Phase-1 ("OLD era") baseline.** Before Phase 1, the project ran a different
experiment: Q-learning on labs called `custom2`–`custom9`, where the *ontology itself*
contained deliberately wrong or missing knowledge ("weakness labs" W1–W6), with
potential-based reward shaping (PBRS) and an "adaptive trust" mechanism switched on.
That line ended in a null result (Sweep-18 on `custom9`), recorded as a registered
deviation in `docs/pre_registration.md` §6.7, and the project pivoted at the thesis
meeting of 2026-06-08 [VERIFIED — `docs/pre_registration.md:511-529`]. The OLD-era
result CSVs still sitting at the repository root are orphaned and are not thesis
results [STATED — `docs/_audit/THESIS_STATE_REPORT.md:9-13`; consistent with what I
saw].

**What Phase 1 added (the "NEW era" clean ladder).** Phase 1 asks one question: *does
priming an otherwise identical Q-learning agent with physics knowledge from a
knowledge graph make it learn faster in a clean, fault-free world?* To answer it, the
following were built [VERIFIED in the tree]:

1. **Three purpose-built simulated labs** (`lab1`, `lab2`, `lab3`) as Node-RED flows
   (`simulator/simulator_flow_lab{1,2,3}.json`), forming a difficulty ladder
   (1 zone/1 lamp → 2 independent zones with blinds → 2 coupled zones with a shared
   spotlight). Physics is deterministic; details in A2.
2. **Three self-contained knowledge graphs**, one per lab
   (`src/resources/building_1_trivial.ttl`, `building_2_intermediate.ttl`,
   `building_3_complex.ttl`), each carrying the device stereotypes, room topology,
   the agent's state-vector layout, and the WoT (Web of Things) action bindings.
   Each lab loads *only* its own file, so nothing can leak in from the global
   `lab-ontology.ttl` [VERIFIED — `src/agt/lab_profiles.asl:242-303`].
3. **A training agent** (`src/agt/illuminance_controller_agent_ql.asl`) that runs
   episodes against the simulator, and **a benchmark agent**
   (`src/agt/illuminance_controller_agent_bench.asl`) that evaluates three policies
   (rule-based oracle, tabula-rasa Q-learner, KG-primed Q-learner) on held-out start
   states.
4. **The learning artifacts in Java**: `QLearner.java` (tabular Q-learning with
   per-zone value decomposition), `StereotypeReasoner.java` (parses the KG with Jena
   SPARQL, derives Q-table initialisation values and soft action "priors"),
   `StereotypeLearner.java` (passively logs observed effects back out as Turtle),
   `BenchmarkLogger.java` (benchmark metrics), `LabEnvironment.java` (HTTP/WoT bridge
   to Node-RED).
5. **Factorial run modes** in `config/run_config.json` isolating the KG prior from
   the other accelerators (arms A–D plus variants; details in A6)
   [VERIFIED — `config/run_config.json:49-200`].
6. **A CI pipeline** (`.github/workflows/phase1.yml`) that trains and benchmarks every
   (lab × arm × seed) cell as a separate cloud job and aggregates the statistics
   (`analysis/sweep_report.py`), publishing results to a `results` branch with a tag.
7. **Mid-phase infrastructure change — the "action-space inversion" (2026-07-10):**
   originally the agent's action list was *discovered from the stereotype layer* of
   the KG; after the inversion it is enumerated from the WoT Thing-Description
   contract, and the stereotype layer only *annotates* those actions with physics
   knowledge. This makes the two arms' action spaces identical by construction
   [VERIFIED — `src/env/tools/StereotypeReasoner.java:161-192` and
   `docs/ACTION_SPACE_INVERSION.md`]. All headline Phase-1 numbers now come from
   post-inversion runs.

**What Phase 1 is *not*:** it contains no faults (Phase 2), no actuator delays
(Phase 3), no energy/dependency ladder (Phase 4), and — since 2026-07-12 — no LLM
baseline anywhere in the project [STATED — state report Addendum 2026-07-12d].

## A2. The labs and their exact physics

All three labs follow the same pattern: a Node-RED flow holds boolean actuator states
and a per-episode `Sunshine` value; a function node named **"Update environment"**
recomputes zone illuminance deterministically from those states on every simulator
tick. There is **no randomness inside the physics** — the only random draw is at
episode reset [VERIFIED — I extracted the function nodes from all three flow JSONs;
the reset node is quoted below].

**lab1 (1 zone, 1 lamp, port 1892)** [VERIFIED — `simulator/simulator_flow_lab1.json`,
"Update environment" node]:

```js
var z1 = 25 + (z1light ? 400 : 0);
```

In words: the room has a constant ambient level of 25 lux; the single ceiling lamp
adds 400 lux when on. Sunshine exists as a variable but deliberately does **not**
enter lab1's physics (a former `0.10·sun` ambient term was deleted on 2026-07-08 so
that the lab is exactly what its KG says it is) [VERIFIED — comment in the same node;
[STATED] for the deletion date].

**lab2 (2 independent zones, adds blinds, port 1893)** [VERIFIED —
`simulator/simulator_flow_lab2.json`]:

```js
var z1 = 25 + (z1l ? 400 : 0) + (z1b ? 0.50 * sun : 0);
var z2 = 25 + (z2l ? 400 : 0) + (z2b ? 0.50 * sun : 0);
```

Each zone: 25 lux ambient, +400 lux from its own lamp, and — when its blind is open —
half of the outdoor illuminance. The blind term is the pedagogical heart of Phase 1:
it is *conditional* on sunshine ("Mediates" mechanism), and the KG deliberately does
not say how much sun is needed — the agent must learn that.

**lab3 (cross-zone coupling + shared spotlight, port 1894)** [VERIFIED —
`simulator/simulator_flow_lab3.json`]:

```js
var corridor = sp ? 150 : 0;
var z1 = 25 + (z1l ? 400 : 0) + (z2l ? 100 : 0)
       + (z1b ? 0.50 * sun : 0) + (z2b ? 0.30 * sun : 0) + corridor;
var z2 = 25 + (z2l ? 400 : 0) + (z1l ? 100 : 0)
       + (z2b ? 0.50 * sun : 0) + (z1b ? 0.30 * sun : 0) + corridor;
```

Line by line: each zone gets its neighbour's lamp bleed-through (+100 lux), its
neighbour's open blind bleed-through (+0.30·sun), and a shared corridor spotlight
that adds 150 lux to *both* zones. These are the *current* magnitudes
(commit `ad3cb3b`, 2026-07-08). The spill magnitudes were changed twice during
Phase 1: original 50 lux / 0.25·sun → bumped 150 / 0.40 → current 100 / 0.30
("rank-moving but non-trivialising": 0.30·900 = 270 < 300, so no cross-zone lever can
reach rank 3 alone) [VERIFIED — current values in the flow; [STATED/VERIFIED] the
history via `analysis/check_provenance.py:8-13` and state report §4.1].

**Energy accounting:** lamps cost 1 unit per tick while on, the lab3 spotlight costs
2, blinds are free; the simulator accumulates `TotalEnergyCost` [VERIFIED — same
function nodes]. Energy is **not** part of the learning reward in Phase 1; it is only
a benchmark report column.

**Episode reset (the only randomness in the environment)** [VERIFIED —
"Reset episode" node, `simulator_flow_lab2.json`]:

```js
var levels   = [25, 75, 150, 500];
var sunRanks = [0, 100, 400, 900];
flow.set('Z1Level',  levels[Math.floor(Math.random() * levels.length)]);
...
flow.set('Sunshine', sunRanks[Math.floor(Math.random() * sunRanks.length)]);
flow.set('SunshinePinned', true);  // sun is FIXED per episode
```

Sunshine is drawn once from {0, 100, 400, 900} and pinned for the episode. However —
and this matters — **in the CI training runs this random reset path is not used**:
the training agent cycles deterministically through a fixed scenario file (episode N
uses scenario (N mod count)+1) because lab1–3 profiles declare `train_scenarios`
files (6 / 11 / 10 scenarios) [VERIFIED —
`src/agt/illuminance_controller_agent_ql.asl:207-218`;
`benchmark/train_scenarios_lab{1,2,3}.json`]. So both arms see identical start-state
sequences; the only stochasticity separating replicate seeds is the agent's own
ε-greedy exploration RNG.

**Discretisation:** raw lux is mapped to ranks by bounds [50, 100, 300] indoors and
[50, 200, 600] for sunshine (so sun 0/100/400/900 → ranks 0/1/2/3) [VERIFIED —
`lab_profiles.asl:266-267`; TTL rank bounds]. Targets: every zone's goal is rank 3
(≥ 300 lux) in all three labs [VERIFIED — `lab_profiles.asl:268,283,299`].

**Realism notes for later (B1):** illumination is purely additive-linear; actuators
are binary and act instantly; there is no sensor noise, no lamp aging, no daylight
dynamics within an episode; energy is linear in on-time. The environment is fully
observable given the state vector (the level ranks are a deterministic function of
the actuator bits + sunshine) [INFERRED from the physics above].

## A3. The knowledge graphs, layer by layer, and a worked example

Each `building_N_*.ttl` is self-contained and has (using lab2 as the example; file
`src/resources/building_2_intermediate.ttl`, all [VERIFIED]):

- **Layer 1 — Physical mechanisms** (lines 64–100): e.g.
  `ws:pm_incandescent_light_emission` (a "Causes" mechanism: manipulated variable =
  electrical power, dependent variable = luminiscence, sign asserted via
  `elem:increases`), and `ws:pm_daylight_ingress` (a "Mediates" mechanism: the blind
  aperture is the manipulated variable *gating* an independent variable —
  outdoor illuminance — into the room; `elem:increases` deliberately absent because
  the sign depends on the sun; only `ws:ivMinRank 1` is asserted, i.e. "needs at
  least sun rank 1", with the true numeric threshold left for the learner).
- **Layer 2 — Stereotypes** (lines 167–255): `ws:LampIncandescentStereotype`,
  `ws:BlindStereotype`, plus sensor/weather/sun stereotypes, each pointing at its
  mechanism via `elem:hasPhysicalMechanism` and carrying connection points.
- **Layer 3 — Component instances + topology** (lines 258–380): Brick-typed devices
  (`lab:CeilingLight_Z1 a brick:Luminaire`, `lab:Blind_Z2 a brick:Blind` …) located
  in zones (`brick:isLocatedIn`), linked to stereotypes via
  `elem:hasBehavioralStereotype`, and wired with `brick:feeds` arcs
  (in lab2: each actuator feeds only its own zone's sensor — no cross-zone arcs;
  in lab3 the cross-zone `brick:feeds` arcs exist and are additionally reified as
  connections tagged `ws:WeakOpticalCoupling`, with **no magnitude** — structure
  only [VERIFIED — `building_3_complex.ttl`; `StereotypeReasoner.java:198-219`]).
- **Component actions + WoT bindings + state-slot registry** (lines 383–441):
  each actuator declares an ON and OFF `elem:ComponentAction`, its WoT action type
  (e.g. `http://example.org/was#SetZ2Blinds`), and its position and domain size in
  the agent's state vector (`ws:stateVecIndex` etc.). The state layout itself is
  KG-driven: lab2 = [Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds,
  Sunshine] = 4·4·2·2·2·2·4 = 1024 states; lab3 adds the spotlight bit → 2048; lab1
  has 8 states.

**How the code consumes it** [VERIFIED — `StereotypeReasoner.java`]:

1. `WOT_CONTRACT_ACTUATOR_QUERY` (lines 184–192) enumerates the action space from
   the WoT bindings alone — this defines what *both* arms can do (post-inversion
   contract).
2. `ACTUATOR_DISCOVERY_QUERY` (lines 134–159) then *annotates* each action with
   physics: which zone(s) it affects, whether it is IV-gated (Mediates) and the
   declared `ws:ivMinRank`, and (Phase 4 only) its energy cost.
3. `CROSS_ZONE_FEEDS_QUERY` (lines 198–219) finds cross-zone spill arcs and their
   coupling class.

**Worked example (lab2, KG arm, action `SetZ2Blinds=ON`).** At Q-table construction,
`getInitPenaltyForZone` (lines 1183–1282) is evaluated for every (state, action,
zone) cell. Take the state "Z2 dark (rank 0), Z2 blind closed, sun rank 0":
rule 1 (redundancy) does not fire (the blind is not already open); rule 2 (IV gate)
fires because sun rank 0 < ivMinRank 1 → penalty −100, scaled by
`INIT_PENALTY_SCALE = 0.5` → the cell starts at **−50**. Same state but sun rank 3:
no penalty; rule 5 (constructive bonus) fires because the action is an activation
affecting Z2, Z2 is 3 ranks below goal, and the IV is satisfied → the cell starts at
`15 · 3 · 0.5 = +22.5`. The tabula-rasa arm starts every cell at 0.0
[VERIFIED — `QLearner.java:435-486`]. At *runtime*, the greedy choice additionally
adds a fading soft prior: −1 if the action is redundant now, −5 if its IV is
currently unsatisfied by the *learned* statistics (`isIVSatisfied`, lines
1023–1038: the gate opens per sun-rank once ≥ 10 trials show ≥ 5 % success)
[VERIFIED]. So the KG's concrete effect is: the KG arm starts believing "open the
blind when it's sunny and the room is dark, don't bother when it's dark outside,
don't press buttons that are already pressed" — and all of that is data-overridable.

**What the KG does *not* contain:** any magnitudes (the 400/0.50/100/0.30/150
numbers), the sunshine threshold as a number, or anything about timing/noise.
[VERIFIED — grep over the TTLs; magnitudes appear only in comments/labels, which no
query reads — `StereotypeReasoner.java` CROSS_ZONE_FEEDS_QUERY selects no labels.]

**The `OntologyArtifact.java` SPARQL path** (`queryBestIncreaseAction` etc.) is used
only by the *rule-based* benchmark oracle, not by either learner arm [VERIFIED —
`illuminance_controller_agent_bench.asl:139-143`].

## A4. The learning mechanism

**Algorithm** [VERIFIED — `QLearner.java`]: tabular Q-learning with per-zone value
decomposition (VDN-style): one Q-table per zone, `qTables[zone][state][action]`;
action selection and the bootstrap target use the **sum** across zones
(`combinedQ`, line 2574; `jointArgmaxAction`, line 2588). Update (lines 553–657):

> Q_z(s,a) ← Q_z(s,a) + α·[ (r̃_z + F_z)/Z + γ·Q_z(s′, a*) − Q_z(s,a) ]

where a* is the single joint-greedy action at s′ shared by all zones, r̃_z the
per-zone clipped reward, F_z the PBRS term (**zero in the headline arm** —
`reward_shaping="none"` in `phase1_kg_only` [VERIFIED — `run_config.json:95`]), and
Z the number of zones.

**Reward per zone per step** (lines 2489–2547) [VERIFIED]:
−1 per step; +40 per rank of progress toward the target (−40 per rank of
regression); +200 once on entering the goal rank; +5 per step while holding it;
−200 on losing it; −10 if an action that claims to affect this zone had no effect
while off-goal; −5 for doing nothing while off-goal. Clipped to ±200
(`reward.clip=200` in all CI runs; code default 50 is overridden) [VERIFIED —
`QLearner.java:60`, `run_config.json:331`].

**Exploration:** ε-greedy, ε₀ = 0.3 decaying per episode by a per-profile factor λ
(lab1 0.9920, lab2 0.9960, lab3 0.9970) to a floor of 0.01 [VERIFIED —
`QLearner.java:55-57`; `lab_profiles.asl:272,287,303`].

**The KG prior at runtime** (greedy selection only, lines 2644–2722) [VERIFIED]:
score = ΣQ_z(s,a) + w·π_a(s)·cellFade, with π ∈ {0, −1, −5} as above;
w decays linearly over `stereo_prior_decay_episodes` E = 10 000 (so after the
3 000-episode budget it is still 0.70 of full strength) and fades per cell as
min(1, 25/visits). Adaptive trust exists but is OFF in arm C. At benchmark time,
`loadQTable` pins the episode counter so the episode-level weight is at its floor
(0.0) [VERIFIED — comments at lines 2654–2660; `run_config.json:333-334`].

**Hyperparameters:** α = 0.1, γ = 0.9 (compile-time constants, no config override)
[VERIFIED — `QLearner.java:53-54`]. Seeding: base seed 42 XOR an arm-specific
constant (different for stereo=true/false, deliberately, so the two arms explore
different trajectories) XOR a SplitMix64-mixed per-run seed 1–20 [VERIFIED — lines
373–375, 152–159].

**One training episode, step by step** [VERIFIED —
`illuminance_controller_agent_ql.asl:202-353`]: (1) the agent sets the simulator to
the next scheduled training scenario (deterministic cycle) and calls
`beginEpisodeFromState`; (2) up to `max_steps_per_episode = 20` times: read the lab
over HTTP, encode to the slot-registry state vector, stop if both zones are at
target; otherwise pick an action ε-greedily, POST it to the simulator, wait
`action_delay_ms = 65 ms`, re-read, run the Bellman update, feed the transition to
the IV-statistics tracker and the passive StereotypeLearner; (3) at episode end,
record goal/steps/reward metrics and decay ε. Early stopping: training halts when
the max Bellman delta stays below 10⁻³ for 100 consecutive episodes [VERIFIED —
convergence check in the agent loop / `QLearner` constants; observed in data — lab1
cells stop at ≈ 383–401 episodes].

**Effective training budget — a documentation discrepancy worth knowing:** the CI
orchestrator patches *every* profile's episode budget to the run-config value 3000
(`run_full_project.ps1:545`), so lab1, lab2, and lab3 all train up to 3000 episodes
in every CI run (lab1 early-stops around 400). The state report's §4.1/§3.5.1 claim
of per-profile budgets 1000/2000/3000 (and the λ-percentage justifications built on
them) does **not** match the runs of record [VERIFIED — archived
`phase1_postinv/run_29639767776/metrics_stereotypes_*_lab2.csv` contains 3000
episodes; lab1 383/401; see B3/B7].

## A5. Benchmarking and how a run is structured end to end

**Benchmark ≠ training.** After training, a separate agent evaluates three policies
on a *held-out* scenario set (16 scenarios for lab2/lab3, 8 for lab1, each defined
as explicit start states covering all four sun ranks), repeating the whole set
`bench_runs = 5` times with a 20-step cap per episode, greedy policy only (prior at
floor). The three modes are: `rule_based` (hand-coded oracle using
`OntologyArtifact`), `ql_false` (tabula-rasa table), `ql_true` (KG-primed table)
[VERIFIED — `benchmark/scenarios_lab2.json`; `run_config.json:91-93`;
`illuminance_controller_agent_bench.asl`]. That yields 80 benchmark episodes per
(lab, mode, seed).

**A single CI run end to end** [VERIFIED — `.github/workflows/phase1.yml`]:
`workflow_dispatch` with inputs (profiles, seeds, run_mode; defaults
lab1,lab2,lab3 / seeds 1–10 / `phase1_kg_only` since 2026-07-18) → a `setup` job
materialises the matrix → **train jobs** (one per lab × stereo × seed; 60 jobs for
the full matrix), each booting Node-RED with the lab's flow, running Gradle
`taskQl`, writing `TRAINING_OK.json` with the effective `run_mode` (the guard
against the arm-confound footgun), and uploading per-cell artifacts → **bench
jobs** (lab × mode × seed; 90 jobs) download the matching Q-tables and run the
benchmark → an **aggregate job** reconstructs `benchmark/results_seed<N>/…`,
runs `analysis/sweep_report.py --seeds-mode --ci-bootstrap-iters 10000`, publishes
everything to the `results` branch and pushes a tag
`results-<timestamp>-<run_mode>-<head>`. 152 jobs total for the full matrix
("152/152 green"). Runs of record are then archived *in the main branch* under
`phase1_postinv/run_<id>/` with a MANIFEST (artifact id + SHA-256).

**Statistics** [VERIFIED — `analysis/sweep_report.py:440-540`]: for each (lab,
metric) the per-seed scalar difference (ql_true − ql_false, paired by seed) is
tested with a deterministic paired bootstrap (10 000 resamples, RNG seed 0xC1,
two-sided doubled-tail p), a Wilcoxon signed-rank sensitivity test, Cliff's δ, and
BH correction within per-file families (learning-speed m = 12; benchmark
confirmatory m = 42).

## A6. The experimental arms

All Phase-1 arms share identical timing, budgets, ε schedule, reward, and simulator;
they differ only in the learning_overrides block [VERIFIED —
`config/run_config.json:49-200`]:

| Arm | run_mode | KG prior | PBRS | adaptive trust | other | purpose |
|---|---|---|---|---|---|---|
| A | `phase1_baseline` | OFF (scale 0, bonus 0) | OFF | OFF | — | negative control: ql_true must ≈ ql_false (harness carries no bias) |
| B | `phase1_pbrs_only` | OFF | ON | OFF | — | generic-shaping control ("your speedup is just shaping") |
| **C** | **`phase1_kg_only`** | **ON (scale 1, init bonus 15)** | **OFF** | **OFF** | cross_zone_bonus 0 | **headline: KG prior alone** |
| D | `phase1_full` (= old default `phase1`) | ON | ON | ON | — | full-stack sensitivity |
| KG-X | `phase1_kg_xzone` | ON | OFF | OFF | cross_zone_bonus 3.0 | lab3 spillage-structure lever (the §7-registered config) |
| ib5 | `phase1_kg_only_ib5` | ON, init bonus 5 | OFF | OFF | — | init-bonus sensitivity |
| E-sweep | `phase1_kg_only_e750` / `_e3000` | ON | OFF | OFF | prior-decay E = 750 / 3000 | prior-decay-horizon sensitivity |

Verified outcomes of the control arms: arm A and arm B show **no significant
learning-speed cells at all** [VERIFIED — recomputed from
`phase1_headline_download/baseline/analysis/out/learning_speed_tests.csv` and
`…/pbrs_only/…`: zero rows with q ≤ 0.05]. The ib5 variant keeps the lab2 anchor
(+0.0161, q = 0) but makes lab3's `auc_goal` significantly *negative* (−0.0150,
q = 0.0048) — the non-monotone init-bonus sensitivity cited in §5.4.1 is real
[VERIFIED — `phase1_headline_download/ib5/analysis/out/learning_speed_tests.csv`].

**Dropped/superseded along the way:** the OLD-era custom labs and W1–W6 weakness
suite (pivot, 2026-06-08); the original lab3 spill magnitudes (twice retuned); the
pre-inversion instrument (all June runs); arm D as the default dispatch mode (the
2026-07-10 defaults dispatch produced the arm-confounded run 29105464710; default
changed to `phase1_kg_only` in commit `c1d8f40`) [VERIFIED — MANIFEST of
`phase1_postinv/run_29105464710/`; `phase1.yml:14-17`]. An LLM baseline never
existed in Phase 1 (it was a Phase-4 item, deleted 2026-07-12) [STATED].

## A7. The metrics, precisely

**Learning-speed metrics** (computed from each training cell's per-episode
`metrics_stereotypes_*.csv`) [VERIFIED — `analysis/sweep_report.py:797-914`]:

- **`auc_goal`** (primary): the normalised trapezoidal area under the per-episode
  goal curve = for a 0/1 series, essentially **the fraction of training episodes
  that ended at goal**. Unitless, 0–1. Higher = solved earlier and more often.
  Pooled-20 lab2 value +0.01877 means: over 3000 training episodes the KG arm ended
  ≈ 1.9 percentage points more episodes at goal — roughly 56 extra successful
  episodes, concentrated early in training (that is where the arms differ).
- **`auc_reward`** (secondary): same construction on the per-episode summed reward
  (RewardZ1+RewardZ2). Units: reward points (the ±200-scale internal currency).
  Higher = better trajectory economy during learning.
- **`mean_first_goal`** (secondary): mean over start-scenarios of the first episode
  index at which that scenario first reached goal (from
  `first_goal_stereotypes_*.csv`). Units: episodes. Lower = faster. The pooled-20
  lab3 value **+53.30 means the KG arm needed on average 53 more episodes to reach
  its first goal — a regression, against the KG arm.**
- **`episodes_to_threshold`** (secondary, censored): first episode where the rolling
  goal rate reaches a threshold; right-censored; degenerate (all-zero Δ) in these
  runs and never a claim.

**Benchmark metrics** (per benchmark episode, averaged; from
`benchmark_results_<mode>.csv`) [VERIFIED — `sweep_report.py:67-99`;
`BenchmarkLogger.java:100-205`]:

- **`goal_rate`** — fraction of the 80 benchmark episodes ending with both zones at
  target.
- **`avg_steps`** — mean actions per episode (cap 20).
- **`avg_dev`** — mean cumulative Σ|rank − target| per episode (rank·steps units).
- **`avg_energy`** — mean simulator `TotalEnergyCost` per episode (energy units).
- **`avg_wasted`** — mean count of steps whose action changed nothing.
- **`avg_cycling`** — mean count of actuator state reversals between consecutive
  steps (an ON→OFF or OFF→ON flip of any actuator relative to the previous step).
  +0.7375 means ≈ 0.74 extra flips per 20-step episode in the KG arm.
- **`avg_redundant`** — **defined as `avg_wasted + avg_cycling`** — a derived sum,
  not an independent measurement [VERIFIED — `sweep_report.py:97`].

## A8. Major decisions taken in Phase 1

1. **The pivot itself** (2026-06-08): abandon weakness-injection, build the clean
   ladder [STATED — pre_registration §7.1].
2. **Post-hoc §7 registration** (2026-06-19, commit `ef7aaf2`): hypotheses
   H-CL1–H-CL4 written *after* all June data and after the analysis documents (the
   registration text cites them) [VERIFIED — timeline; see B6].
3. **lab3 spill retunes**: 50/0.25 (sub-rank, "nothing to learn") → 150/0.40
   (trivialising ceiling) → 100/0.30 ("rank-moving but non-trivialising",
   `ad3cb3b`, 2026-07-08). Consequence: three physics regimes that must never be
   mixed; the current physics is the only citable one [VERIFIED —
   flow + check_provenance registry].
4. **Action-space inversion** (2026-07-10, commit `8c386f8`): action space now
   defined by the WoT contract for both arms; stereotypes only annotate.
   Measured consequence: Phase-2's outcome changed 8/8 → 3/8; in Phase 1 the lab2
   anchor survived, lab2 `mean_first_goal` sign-flipped (pre-inversion marginal
   "KG faster" −32.03 became +21.29 ns — the claim is dead), and the lab3 taxes
   persisted [VERIFIED — §5.2 table vs archived CSVs].
5. **Arm-C re-run as headline** (registered 2026-07-13 as a duty, discharged
   2026-07-18 as run 29639767776) after the defaults-dispatch arm-D confound
   [VERIFIED — MANIFESTs, addenda].
6. **E-decay sweep** (2026-07-18): E ∈ {750, 3000, 10000}; headline E-robust; the
   lab3 tax trades timing ↔ policy-quality with E but never vanishes [VERIFIED —
   archived E-sweep CSVs match the addendum table].
7. **Toggling micro-mechanism test** (registered 18c, executed 19a): INDETERMINATE
   (13 < 20 pairs); descriptives *contradict* the "rarely-visited cells" story
   (median 159 visits) — §5.4.1 stays interpretation [VERIFIED — addendum 19a and
   `phase1_postinv/run_29639767776_toggling_audit/` exists; numbers [STATED]].
8. **Plan B seed extension + pooling** (registered 18c, executed 19c, run
   29692725784): seeds 11–20, arm C, lab2+lab3 only; pooled-20 is the registered
   primary with an m = 3 BH family; single-shot rule now in force [VERIFIED —
   dispatch inputs in MANIFEST; pooled CSV].
9. **REFRAME presentation decision**: lab3 is presented as a characterized
   weakness (lead with `auc_reward`, disclose the taxes), bridging to Phase 2
   [STATED — 14_presentation_rules via state report §5.4].

## A9. How runs were executed, registered, tagged, archived

Covered in A5 for mechanics. Provenance machinery [VERIFIED]:

- **Registration-at-dispatch:** run 29639767776's server-recorded head `e631877`
  contains both `pre_registration.md` §7 and the state-report addendum registering
  the arm-C re-run; run 29692725784's head `02ed6c1` *is* the Plan-B registration
  commit. I verified both containments locally (`git show e631877:docs/…`).
- **Tags:** `results-20260718-102423-phase1_kg_only-e631877` and
  `results-20260719-155358-phase1_kg_only-02ed6c1` both exist on origin and point
  at the claimed heads [VERIFIED — `git ls-remote --tags origin`]. The 2026-07-18
  tag was initially remote-rejected while the publish step reported green (the
  "footgun"); it was pushed manually the same day [STATED — Addendum 2026-07-18b].
- **Archives:** `phase1_postinv/run_29639767776/` (per-seed benchmark files +
  `analysis/out` + root convenience copies + MANIFEST with artifact id 8428536694,
  sha256 `4029c693…`), same for 29692725784 (artifact 8444359131, sha256
  `3bf6c4a8…`), the two E-sweep runs, the arm-D run, and
  `pooled20_reanalysis/` [VERIFIED — directories and MANIFESTs present; sha256
  values [STATED] as I did not re-download the CI artifacts].
- **Golden check:** `analysis/check_provenance.py` (wired into `ci.yml:103`)
  enforces stale-physics, pre-inversion-run-ID, and cross-zone-bonus-disclosure
  rules. **It currently FAILS on this tree** — see B7/Part D.

## A10. Results of record

**Registered primary (pooled seeds 1–20, arm C, BH within m = 3)** [VERIFIED —
`phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv`]:

| Cell | Δ (ql_true − ql_false) | 95 % CI | p_boot | q (m=3) | Wilcoxon p | Cliff's δ |
|---|---|---|---|---|---|---|
| lab2 `auc_goal` | **+0.018773** | [0.013663, 0.024183] | 0 (< 10⁻⁴) | 0 | 8.84×10⁻⁵ | 1.00 |
| lab3 `mean_first_goal` | **+53.302** (KG slower) | [26.545, 81.165] | 0 (< 10⁻⁴) | 0 | 0.00143 | 0.585 |
| lab3 `avg_cycling` | **+0.7375** (KG worse) | [0.40625, 1.0375] | 0.0002 | 0.0002 | 0.00119 | 0.77 |

Note on "q = 0": the bootstrap used 10 000 resamples, so a reported p of exactly 0
means "no resample crossed zero" and should be read (and printed in the thesis) as
**p < 10⁻⁴**, not as zero — see B5.

**Registered secondary (seeds 11–20 alone — the independent replication)**
[VERIFIED — `phase1_postinv/run_29692725784/analysis/out/`]: lab2 `auc_goal`
+0.02076 [0.01447, 0.02726], δ = 1.0; lab3 `mean_first_goal` +39.04 [9.56, 72.99],
δ = 0.56; lab3 `avg_cycling` +0.731 [0.344, 1.100], δ = 0.76. All three
sign-consistent with seeds 1–10 *and* individually significant in their own run's
families — the replication is substantive, not merely directional.

**Superseded n = 10 record (run 29639767776; kept for history)** [VERIFIED —
archived CSVs]: lab2 `auc_goal` +0.01679 [0.00959, 0.02606] q = 0 (m = 12);
lab3 `mean_first_goal` +67.56 [26.03, 108.95] q = 0.0104; lab3 `avg_cycling`
+0.744 [0.213, 1.200] q = 0.0154 (m = 42); lab3 `auc_reward` +16.62 [13.06,
19.96] q = 0 — the auc_reward win is *outside* the registered m = 3 family and its
citable status is the n = 10 record plus the seeds-11–20 descriptive +15.85
[VERIFIED].

**Pooled-20 full tables (descriptive only, per the registration)** [VERIFIED —
`pooled20_reanalysis/analysis_out/paired_tests.csv`] — these matter for honesty
(see B8): lab2 `goal_rate` +0.028 [0.009, 0.050] p = 0.0012 (a KG *win* that was
only marginal at n = 10); lab2 efficiency wins all hold (steps/dev/energy/wasted/
cycling/redundant all favourable, p ≤ 0.0022); **lab3 `avg_redundant` +1.107
[0.352, 1.796] p = 0.005, `avg_energy` +2.604 [1.052, 3.944] p = 0.0022,
`avg_dev` +0.5375 [0.053, 0.991] p = 0.031 — all *against* the KG arm and all
"significant" at face value in the descriptive pooled tree.**

**Controls:** arm A and arm B null everywhere (learning-speed families) [VERIFIED];
lab1 null in every contrast under arm C [VERIFIED — archived learning-speed and
paired-tests tables].

---

# PART B — IS THE LOGIC SOUND?

## B1. Physics plausibility — verdict: **internally consistent toy; external validity is thin, and the near-zero noise inflates effect-size rhetoric, but the *direction* of the headline is probably not an artifact**

The physics is a linear, additive, noise-free, instantaneous, binary-actuator model
with a four-value sun. As a model of a real lab it omits: continuous dimming,
actuator latency (deliberately deferred to Phase 3), sensor noise, daylight
variation within an episode, occupancy, reflections/non-linearity, and any coupling
between energy and heat/light [INFERRED — from the flow functions in A2].

Consequences to be honest about:

1. **Cliff's δ = 1.0 and q = 0 are cheap in this world.** With deterministic
   physics and a fixed scenario cycle, the only variance across seeds is
   exploration randomness, so tiny mean differences (e.g. +1.9 percentage points
   of auc_goal) become "every seed beats every seed". The effect is real but the
   *strength labels* (maximal δ) say more about the simulator's noiselessness than
   about the intervention. The thesis should report the absolute magnitudes next
   to δ [INFERRED, but arithmetically evident].
2. **Could the unrealism be doing the work?** The KG advantage on lab2 flows
   through (a) redundancy penalties (don't toggle what's already set), (b) the IV
   gate (don't open blinds in the dark), and (c) optimistic init toward helpful
   actions. All three would survive in a noisier or continuous world in some form,
   but their *measured payoff* here is amplified by the tiny action space (9
   actions in lab2) and the 20-step horizon: a tabula-rasa learner wastes a
   meaningful fraction of its early budget on exactly the actions the prior
   suppresses. In a large realistic action space the prior's relative value could
   go either way (more valuable: more junk to avoid; less valuable: the penalties
   cover a smaller fraction of the space). This is an honest open question, not a
   refutation [INFERRED].
3. **The lab3 negative results are the strongest evidence the harness is not
   rigged**: the same prior machinery *hurts* where the promoted structure is
   redundant. A simulator engineered to flatter the KG would not produce a
   +53-episode first-goal regression [INFERRED — but the data is VERIFIED].
4. One inconsistency of record: `lab3_slow` (Phase 3) still runs the *bumped*
   150/0.40 spill physics while lab3 runs 100/0.30 [STATED — state report §4.3;
   acknowledged there]. Within Phase 1 this does not bite; across chapters it can
   confuse readers and should be flagged wherever both labs appear.

## B2. KG correctness and meaningfulness — verdict: **ontology internally consistent and honestly scoped; but the measured "KG advantage" is substantially "cheap procedural knowledge", and the one control that would prove otherwise is missing**

**Internal consistency** [VERIFIED — reading the TTLs against the queries]: the
three-layer design is coherent; the property names the code queries
(`elem:hasBehavioralStereotype`, `elem:hasPhysicalMechanism`,
`ws:hasWoTActionSemanticType`, `ws:ivMinRank`…) all resolve; magnitudes are
genuinely absent from the queried triples (only comments/labels mention them, and
after the 2026-07-18 label sync those match the physics). The slot registry is the
single source of the state layout, and `expected_state_vec_dim` in run_config
guards it. One nit: the memory/older docs describe `elem:hasStereotype` while the
NEW-era TTLs use `elem:hasBehavioralStereotype` — only the latter is live
[VERIFIED].

**Post-inversion wiring is fair**: both arms get the identical WoT-contract action
space [VERIFIED — `WOT_CONTRACT_ACTUATOR_QUERY` is stereotype-free; the ordering is
canonical and label-remapping makes saved artifacts order-independent]. The old
"KG defines what you can do" confound is genuinely gone, and the Phase-2 8/8→3/8
change shows the inversion had teeth.

**The critical question — what knowledge is actually paying?** Decompose the arm-C
prior: (i) redundancy penalty/prior — *derivable without any ontology* from the WoT
state binding alone ("action sets bit b to v; bit b already equals v"); (ii)
IV gate — genuine physics knowledge (blind–sun dependency, with the threshold
honestly learned); (iii) constructive init bonus toward activations that help a
below-target zone — this needs the zone/DV mapping, i.e. mid-value knowledge;
(iv) cross-zone structure — OFF in the headline arm. Item (i) is the one a skeptic
will point at: a hard-coded, ontology-free "don't repeat a set bit" heuristic
might reproduce a large share of the lab2 win. **Arm B (PBRS) does not control for
this** — PBRS is potential-based shaping over rank distance, not no-op
suppression. There is no arm that runs the redundancy heuristic *without* the KG.
Until that ablation exists, the claim must be phrased as "KG-derived priors
(including trivially derivable redundancy knowledge) accelerate learning", not
"physics knowledge accelerates learning" [INFERRED — gap; concrete fix in Part D
item 4].

**Could the agent get the IV knowledge more cheaply?** Yes — it does: the learned
IV statistics converge in a few hundred episodes and the gate is data-driven either
way. The KG's contribution is only the *initial* bias (avoid dark-sky blind
flapping during the first ~100–300 episodes). That is exactly what a
learning-speed (not asymptotic) claim should look like, and the write-ups do
confine the claim to speed [VERIFIED — §5.1]. Fair.

**Ordering/side-channel effects:** post-inversion ordering is canonical and
shared; tie-breaks in greedy selection are randomised; I found no channel through
which the KG arm gets extra environment information [VERIFIED — code read;
INFERRED for absence, one cannot prove a negative].

## B3. Agent/learning logic — verdict: **sound for this task; three disclosed asymmetries and one documentation error**

- **State sufficiency:** the state vector (zone ranks + actuator bits + sun rank)
  makes the environment fully observable and Markovian — the rank slots are
  redundant encodings of bits+sun, which costs state-space size but not
  correctness [VERIFIED physics ⇒ INFERRED observability]. Both arms share the
  layout, so no differential partial observability exists.
- **Reward–metric alignment:** the reward optimises reaching/holding the rank
  target quickly; `auc_goal`/`mean_first_goal` measure exactly that during
  training. `avg_cycling`/`avg_energy` are *not* in the reward — which is why the
  lab3 cycling tax can persist into a "converged" policy without the reward ever
  punishing it (the toggles move between goal-satisfying states; verified in the
  toggling audit descriptives: the entrenched Z2-blind 2-cycle crosses no rank
  boundary [STATED — Addendum 2026-07-19a]). This is a real design lesson, and
  the write-ups own it.
- **Arm symmetry of hyperparameters:** α, γ, ε schedule, budgets, clip, and
  timing are shared; the only intended differences are Q-init and the greedy
  prior [VERIFIED — run_config + code]. Two deliberate, disclosed asymmetries:
  (1) the RNG base seed differs by arm (so "seed-paired" arms do *not* share
  exploration noise — see B5); (2) `hasConverged` early stopping can truncate
  arms at different episode counts — in the runs of record it fired only on lab1
  (383 vs 401 episodes), where everything is null anyway, but it is a latent
  hazard for auc comparisons if it ever fires asymmetrically on a discriminating
  lab [VERIFIED — archived metrics row counts].
- **Documentation error (fix in text):** per-profile budgets are documented as
  1000/2000/3000 but every CI run trains 3000 episodes on all labs
  (`run_full_project.ps1:545` patches `training_params`); the λ-fraction
  justifications in state report §3.5.1 are computed against the wrong budgets
  [VERIFIED]. No result is invalidated (both arms share whatever the budget is),
  but an examiner reading code against text will catch it.
- The prior-decay horizon E = 10 000 with a 3000-episode budget leaves the
  episode-level prior at 0.70 at end of training; disclosed at length and
  sensitivity-swept — adequate [VERIFIED — E-sweep archives match the addendum].

## B4. Experimental design fairness — verdict: **post-inversion arm C vs its tabula-rasa twin is a clean comparison; residual differences are enumerable and defensible**

Complete list of things that differ between ql_true and ql_false inside run mode
`phase1_kg_only` [VERIFIED — code/config read]:

1. Q-table initialisation (stereotype penalties/bonuses vs zeros) — the treatment.
2. Greedy-selection soft prior (fading) — the treatment.
3. IV-statistics collection feeding the prior (`recordActionOutcome` runs in both
   arms — but only the KG arm consults it) — treatment side-effect.
4. RNG base-seed constant (0x5A5A… vs 0xA5A5…) — deliberate decorrelation;
   without it both arms would replay identical trajectories under a shared seed.
   Effect: pairing is nominal (see B5), not a confound of direction.
5. Nothing else: same action space (post-inversion), same scenario schedule, same
   ε, same budgets, same benchmark procedure (prior at floor at bench).

The remaining cross-arm hazards are historical and were caught: the pre-inversion
action-space asymmetry (fixed by the inversion) and the arm-D defaults dispatch
(caught via `TRAINING_OK.json` run_mode verification and re-run). The negative
control (arm A ⇒ ql_true ≡ ql_false statistically) passing is strong evidence the
harness itself is symmetric [VERIFIED — arm A nulls].

One design choice worth defending in the thesis: the *within-mode* contrast (arm C
ql_true vs arm C ql_false) means the tabula-rasa baseline is always trained in the
same CI run under identical conditions — good. But note the ql_false cells of arm
C are configuration-identical to the ql_false cells of arm A/B (modulo PBRS in B);
the design re-trains them per run rather than reusing them, which spends compute
but avoids cross-run pairing — defensible [INFERRED].

## B5. Statistics — verdict: **fundamentally sound machinery, honestly executed; four things must be fixed in presentation, one in substance**

1. **The pooled-20 "registered primary" is not an independent confirmation, and
   the write-ups already know it.** The three-cell family was chosen *because*
   those cells were significant at n = 10; pooling seeds 1–10 back in means the
   pooled q-values partially re-use the data that selected the hypotheses. The
   registration itself says the subset (11–20) is the independent check
   [VERIFIED — Addendum 2026-07-18c reporting rules]. The saving grace is that
   the seeds-11–20 subset is *itself* significant in all three cells (lab2 q = 0
   m = 8; lab3 first-goal q = 0.016 m = 8; cycling q ≈ 0 m = 28) [VERIFIED].
   **Recommended thesis framing:** lead with the subset as the confirmatory
   replication; cite pooled-20 as the best *estimate* (pooling is fine for
   estimation); do not present pooled q-values as if the family were chosen
   blind. Under that framing the three results stand.
2. **"q = 0" must not be printed.** The bootstrap has a resolution floor of
   1/10 000; report "p < 10⁻⁴" (or "< 2×10⁻⁴" two-sided doubled-tail). The
   Wilcoxon values (8.8×10⁻⁵, 1.4×10⁻³, 1.2×10⁻³ for the three registered cells)
   are the honest finite p-values and should accompany them [VERIFIED — CSVs].
3. **Pairing is nominal.** Because the arms use different RNG base constants,
   seed i's ql_true and ql_false runs share only the deterministic scenario
   schedule, not exploration noise. The paired bootstrap is still valid (each
   difference is a well-defined independent draw), but the design gains no
   variance reduction from pairing, and the thesis should not imply matched-noise
   pairing [VERIFIED — `QLearner.java:373-375`; INFERRED for the implication].
4. **Independence assumptions are respected where it matters.** All tests operate
   on one scalar per seed (n = 10 or 20); episodes within a seed are never
   treated as independent units [VERIFIED — `_collect_per_seed_values` /
   learning-speed collectors]. Correct. Caveats: n = 10 bootstrap CIs are
   coarse; Wilcoxon near ceiling loses power to ties (disclosed, §5.5); and the
   *metrics within* a family are heavily correlated — in particular
   `avg_redundant = avg_wasted + avg_cycling` is a deterministic sum of two other
   family members, so the m = 42 family double-counts evidence. BH tolerates
   positive dependence (still valid, conservative m), so this is a reporting
   nit, not an error [VERIFIED — metric definition; INFERRED for BH validity].
5. **Family bookkeeping is honest but confusing.** Three different BH families
   (m = 12/42 for the run-level tables, m = 8/28 for two-lab runs, m = 3 for the
   registered family) produce q-values that cannot be compared across tables —
   the write-ups repeatedly warn about this, correctly. The §7 registration
   itself is internally inconsistent: H-CL1's test paragraph says "BH family
   m = 42" while §7.4 assigns `auc_goal` to the learning-speed family (m = 12)
   [VERIFIED — `pre_registration.md:555-556` vs `:581-587`]. Harmless in effect
   (the result is q ≈ 0 under any of these), but it must be acknowledged, not
   silently normalised.
6. **Registered-vs-executed config mismatch:** §7.2 registers
   `num_episodes = 10000` and cross_zone_bonus 3.0 (the `phase1_kg_xzone`
   profile); every executed Phase-1 cell trained 3000 episodes, and the headline
   arm runs bonus 0 [VERIFIED — §7.2 text vs archived metrics and run_config].
   The headline's registration cover comes from the *state-report addenda*
   (2026-07-13 duty; 2026-07-18c families), not from §7. The thesis must cite
   the addenda — §7 alone does not register the headline configuration.

## B6. Registration integrity — verdict: **the June record is post-analysis, not just post-data, and one commit-message blemish makes it look worse; the July record is genuinely registration-before-dispatch; the current disclosure paragraph is accurate and should be used verbatim**

Facts [VERIFIED — git history, run metadata captures in `paper_notes/ACTIONS_RUNS_*`,
and containment checks]:

- First Phase-1 dispatch: run 27305796237, 2026-06-10 20:56 UTC. §7 registration
  pushed 2026-06-19 (commit `ef7aaf2`) — 8.6 days later, 6.0 days after the last
  June run it governs, and its own text cites the completed xzone analysis
  documents and the ablation run ID. So the June hypotheses were written with
  analyses in hand; "hypotheses were formed before analysis" is author assertion
  only, exactly as Addendum 2026-07-19b concedes.
- Aggravating detail the addendum does *not* mention: `ef7aaf2`'s commit message
  reads "docs(phase3): add §8 pre-registration addendum …" — the Phase-1 §7
  registration was added under a message describing Phase 3 [VERIFIED —
  `git show ef7aaf2 --stat`]. Nothing nefarious follows from it, but an examiner
  doing forensics will find it, so the thesis disclosure should name it first.
- The June seeds-11–20 xzone "replication" (run 27462446044) was dispatched 16
  minutes after the seeds-1–10 results completed, sighted and unregistered
  [STATED — Addendum 2026-07-19b, anchored to run timestamps I partially
  verified].
- The July record is different in kind: run 29639767776's head contains the
  frozen §7 *and* the addendum registering the re-run; run 29692725784's head IS
  the Plan-B registration commit; both results tags exist on origin [VERIFIED].

**What retains confirmatory status:** (a) the three registered cells, on the
strength of the 2026-07-18c registration + the significant seeds-11–20
replication; (b) arm-A/B control nulls (no one registers negative controls, and
they are risk-free). **What must be labelled exploratory /
confirmatory-with-post-hoc-registration:** every June-2026 number (including the
pre-inversion headline +0.01707 and the entire xzone family), the lab3
`auc_reward` win (never in a registered family — it is H-CL4 in the post-hoc §7
only), the E-sweep, the residual-prior quantification, and the post-hoc
"entrenched 2-cycle" mechanism reading. The canonical disclosure paragraph in
Addendum 2026-07-19b §3 is accurate against everything I checked and should go
into the Methods chapter verbatim, with the commit-message detail added
[VERIFIED/INFERRED].

## B7. Claims-vs-evidence trace

Every quantitative Phase-1 claim in the live sections of
`docs/_audit/THESIS_STATE_REPORT.md` (exec summary row 1–2, §5.2–§5.5, §10.3,
Addenda 2026-07-18b/19a/19c), traced to artifacts. "✓" = value matches the named
file exactly (my recomputation/read); source paths relative to repo root.

| # | Claim (document, location) | Artifact | Match? |
|---|---|---|---|
| 1 | pooled-20 lab2 auc_goal +0.01877 [0.01366, 0.02418] q=0 δ=1.0 (exec summary, §5.2 note, §10.3, 19c) | `phase1_postinv/pooled20_reanalysis/pooled20_registered_family.csv` | ✓ [VERIFIED] |
| 2 | pooled-20 lab3 mean_first_goal +53.30 [26.55, 81.17] q=0 δ=0.585 | same file | ✓ [VERIFIED] |
| 3 | pooled-20 lab3 avg_cycling +0.7375 [0.406, 1.038] q=0.0002 δ=0.77 | same file | ✓ [VERIFIED] (CI hi prints 1.0375 in file vs "1.038" rounded) |
| 4 | n=10 lab2 auc_goal +0.01679 [0.00959, 0.02606] q=0 (§5.2) | `phase1_postinv/run_29639767776/analysis/out/learning_speed_tests.csv` | ✓ [VERIFIED] |
| 5 | n=10 lab3 auc_reward +16.62 [13.06, 19.96] q=0 δ=1.0 (§5.2) | same file | ✓ [VERIFIED] |
| 6 | n=10 lab3 mean_first_goal +67.56 [26.03, 108.95] q=0.0104 (§5.2) | same file | ✓ [VERIFIED] |
| 7 | n=10 lab2 mean_first_goal +21.29, q=0.1038 ns; sign-flip disclosure (§5.2) | same file | ✓ [VERIFIED] |
| 8 | §5.2 benchmark: lab2 steps −0.594 q=0.0154 / wasted −0.595 q=0.0106 / redundant −0.714 q=0.0121 / dev −1.494 q=0.0072 / energy −1.365 q=0 / goal_rate +0.025 q=0.1027 / lab3 cycling +0.744 q=0.0154 δ=0.79 / lab3 redundant +0.994 q=0.211 / lab1 wasted +0.0175 q=0.369 | `…run_29639767776/analysis/out/paired_tests.csv` | ✓ all [VERIFIED] |
| 9 | seeds-11–20 subset: lab2 +0.02076 [0.01447,0.02726] δ=1.0; lab3 mfg +39.04 [9.56,72.99] δ=0.56; cycling +0.731 [0.344,1.100] δ=0.76 (19c §4) | `phase1_postinv/run_29692725784/analysis/out/…` | ✓ [VERIFIED] |
| 10 | pre-inversion arm-C comparator lab3 mfg +23.95, run 28941204656 (§5.3) | `phase1_xzone_mid/analysis/out/learning_speed_tests.csv` | ✓ (+23.954, q=0.0108) [VERIFIED] |
| 11 | xzone-mid lab2 auc_goal +0.02124; lab3 auc_reward +12.66 (§5.3) | same file | ✓ [VERIFIED] |
| 12 | E-sweep table (18b §4): E750 lab2 +0.02711 / E3000 +0.01484 / E10000-subset +0.02224; lab3 mfg +80.18 at E10000-subset; lab2 mfg −15.51 q=0.0064 at E3000, +29.50 q=0.0164 at E10000-subset; etc. | `phase1_postinv/run_29641043465,29641899071,run_29639767776_seeds1-5_reanalysis/analysis/out/…` | ✓ spot-checked 8 cells, all match [VERIFIED] |
| 13 | arm A & B nulls (§5.4 item 4) | `phase1_headline_download/{baseline,pbrs_only}/analysis/out/learning_speed_tests.csv` | ✓ zero significant cells [VERIFIED] |
| 14 | ib5: "lowering the bonus 15→5 made lab3 worse" (§5.4.1) | `phase1_headline_download/ib5/…` lab3 auc_goal −0.0150 q=0.0048 | ✓ [VERIFIED] |
| 15 | toggling audit: 13 pairs, G1 800/800, Δcycling +0.7438 cross-check, P1 median 159 visits, P2 13/13 p=1e-5, P3 1/13 (19a) | `phase1_postinv/run_29639767776_toggling_audit/` (dir exists; internals not recomputed) | [STATED — plausible, not recomputed] |
| 16 | residual-prior table (18b §4): median w 0.70, ~97 % cells > 0.5, etc. | `analysis/out/residual_prior_weight.csv` | ✓ spot-checked lab2 rows (96.64 % ≈ "96.6") [VERIFIED]; script reads the *archive* copies, so the stale repo-root sidecars did not contaminate it [VERIFIED] |
| 17 | timeline T1–T9 (19b): run 27305796237 created 2026-06-10T20:56:14Z etc. | `paper_notes/ACTIONS_RUNS_20260617T074205Z.csv` + `git ls-remote` tags | ✓ T1/T2/T4–T7 corroborated; T8 push-runs and T9 [STATED — run IDs not in the June capture, tags verified] |
| 18 | "registration ⊂ dispatched tree" for e631877 / 02ed6c1 | `git show e631877:docs/pre_registration.md` (contains H-CL1), `…:THESIS_STATE_REPORT.md` (contains 2026-07-13 duty); `02ed6c1` contains 18c | ✓ [VERIFIED] |
| 19 | results tags exist on origin pointing at run heads | `git ls-remote --tags origin` | ✓ both [VERIFIED] |
| 20 | run_mode verified in 60/40 TRAINING_OK.json (§5.2, 19c) | spot-checked `…/results_seed1/lab2/training_stereo_true/TRAINING_OK.json` = `phase1_kg_only` | ✓ sample [VERIFIED]; full 60/40 sweep [STATED] |
| 21 | "efficiency tax under arm C = avg_cycling only, avg_redundant ns (arm-D stacking)" (exec summary, §5.4 item 3, §10.3, 18b §3) | pooled-20 descriptive `paired_tests.csv`: lab3 avg_redundant **+1.107, p=0.005**; avg_energy +2.60 p=0.0022; avg_dev +0.54 p=0.031; seeds-11–20 alone: redundant +1.22 q=0.0032 | ✗ **STALE at n=20 — see B8. The registered-family statement is untouched, but "only"/"ns" is contradicted by the current best data.** [VERIFIED] |
| 22 | per-profile training budgets 1000/2000/3000 (§3.5.1, §4.1) | archived metrics: all labs 3000 (lab1 early-stop ~383/401) | ✗ wrong for the runs of record [VERIFIED] |
| 23 | §7.2 registered config (`phase1_kg_xzone`, 10000 episodes, bonus 3.0) describes the headline | run_config + archives: headline is `phase1_kg_only`, 3000 episodes, bonus 0 | ✗ mismatch — headline registration lives in the addenda, not §7 [VERIFIED] |
| 24 | dashboard serves the citable numbers | `dashboard/public/data/phase1.json`: n=10 values with run-29639767776 provenance, no pooled-20 supersession note | ✗ violates the 19c supersession rule ("wherever they are quoted") [VERIFIED] |
| 25 | CI golden check green | `python analysis/check_provenance.py` → **FAILS, 2 violations** (`THESIS_STATE_REPORT.md:843` and `:2548`, run 27464846574 cited without pre-inversion marker) | ✗ broken on current tree [VERIFIED] |
| 26 | sha256 of CI artifacts (`4029c693…`, `3bf6c4a8…`) | MANIFESTs | [STATED — not re-downloaded] |

## B8. Interpretation — do the write-ups overclaim?

Mostly the write-ups *under*-claim by design ("one notch below the evidence"), and
the negative results are given unusual prominence. Three genuine problems:

1. **The "cycling-only tax" narrative is now wrong.** Exec summary, §5.4 item 3,
   §10.3 and Addendum 2026-07-18b all say the arm-C lab3 efficiency tax is
   `avg_cycling` **only**, with `avg_redundant` dismissed as ns / "arm-D
   stacking". That adjudication was correct *at n = 10*; at n = 20 the descriptive
   pooled tree shows `avg_redundant` +1.107 (p = 0.005), `avg_energy` +2.60
   (p = 0.0022) and `avg_dev` +0.54 (p = 0.031) against the KG arm, and the
   independent seeds-11–20 run alone shows redundant +1.22 (q = 0.0032)
   [VERIFIED]. The registered m = 3 conclusion is untouched, but the *narrative*
   ("the redundant tax was an arm-D artifact") is contradicted by the current
   best data and must be rewritten: the honest statement is "under arm C the lab3
   tax at n = 20 spans timing, cycling, redundant actions, deviation, and energy
   (the latter three descriptive, sign-consistent, nominally significant)".
   The alternative explanation the current text offers (arm-D stacking) can no
   longer carry the redundant tax.
2. **The lab2 goal_rate story flips favourably and is not yet told.** §5.2 records
   the n = 10 "honest downgrade" (goal_rate q = 0.1027 marginal). Pooled-20
   descriptive: +0.028, p = 0.0012 [VERIFIED]. If the unfavourable n=20
   descriptives in item 1 are reported (they must be), this favourable one should
   be too — symmetrically, as descriptive.
3. **"Confirmed 3/3" framing.** Two of the three "confirmed" registered cells are
   *anti-KG* findings (first-goal and cycling taxes). The write-ups are honest
   about their direction, but a hurried reader of "all three registered cells
   CONFIRMED" could take it as a KG triple-win. Thesis text should always name
   the direction next to the word "confirmed".

For each headline conclusion, strongest alternative explanation and status:

- **lab2 anchor (+0.0188 auc_goal):** alternative = "any generic accelerator would
  do this". Rejected for PBRS (arm B null) and for zero-prior (arm A null)
  [VERIFIED]; *not yet rejected* for an ontology-free redundancy heuristic (B2) —
  open ablation.
- **lab3 timing/cycling tax:** alternative = "artifact of the specific prior
  magnitudes / decay horizon". E-sweep shows the tax moves between metrics but
  never vanishes [VERIFIED]; the ib5 sweep shows non-monotonicity [VERIFIED].
  The *mechanism* (init-residue toggling) remains unproven (registered test
  INDETERMINATE; observed pairs contradict the rare-state clause) [STATED].
- **lab3 auc_reward win (+16.6):** alternative = "the reward metric mechanically
  favours the suppressive prior (fewer −10/−1 penalties) without any behavioural
  payoff a user would care about". Partially true by construction — auc_reward
  is internal currency; the write-ups should not present it as a user-visible
  benefit, only as trajectory economy [INFERRED].

## B9. What a skeptical examiner will ask that Phase 1 does not currently measure

1. **The ontology-free redundancy-heuristic control** (B2) — the single most
   damaging missing ablation for the "knowledge" claim.
2. **Robustness to noise:** one run with sensor noise or per-tick sun jitter would
   show whether the δ = 1.0 effects survive any stochasticity in the plant.
3. **Sample-efficiency curves, not just AUC:** where in training does the lab2
   advantage accrue? (The learning-curve PNGs exist; a quantified
   "advantage-by-episode-window" analysis does not.)
4. **Wrong-prior sensitivity in the NEW era:** Phase 1 deliberately dropped the
   W1–W6 wrong-ontology labs; arm C has never been run against a *mis*informed KG
   in the clean ladder. Phase 2 covers faults, not wrong priors. A single
   wrong-sign stereotype cell would bound the downside risk of the approach.
5. **Scalability:** 2048 states is tiny. Even one 3-zone lab would test whether
   the prior's value grows or shrinks with state-space size.
6. **Benchmark power:** 16 scenarios × 5 repeats with a deterministic greedy
   policy means the 5 repeats add nothing for ql modes (same trajectory each
   repeat, modulo tie-break RNG) [INFERRED — greedy determinism; tie-break
   randomness is the only variance source]. The benchmark's effective n is closer
   to 16 than 80 per cell — worth stating.
7. **Multiple-physics-regime honesty:** an examiner will ask why lab3's physics
   was retuned twice and whether the final choice was outcome-driven; the
   "rank-moving but non-trivialising" rationale is documented, but the middle
   setting was chosen *after* seeing both extremes [VERIFIED — history], so it
   should be presented as a designed instrument choice with that history, never
   as incidental.

---

# PART C — OPEN QUESTIONS, CAVEATS, RESOLVABILITY

## C1. Consolidated list (severity for the thesis / resolvable? / how)

1. **Narrative contradiction on the lab3 redundant/energy/dev taxes at n = 20**
   — *must-address* (it currently makes live sections false against the best
   data). Resolvable: text rewrite of exec summary, §5.4 item 3, §10.3, 18b §3
   echo; optionally a small registered addendum acknowledging the n=20
   descriptives. No new runs needed.
2. **check_provenance.py failing on the current tree** — *must-address*
   (CI red; the golden check is the thesis's own integrity instrument).
   Resolvable in minutes: add pre-inversion markers at the two flagged lines.
3. **Missing ontology-free redundancy-heuristic ablation** — *must-address for
   the central claim's wording; nice-to-have as a run*. Resolvable: implement a
   `phase1_redundancy_only` mode (prior from WoT state bindings alone, no
   stereotype layer), register it, run lab2+lab3 × seeds 1–10.
4. **Registration §7 vs executed config mismatch (episodes 10000 vs 3000; kg_xzone
   vs kg_only) + H-CL1 family inconsistency + `ef7aaf2` commit-message blemish** —
   *must-address in text* (examiner forensics). Resolvable: one paragraph in the
   Methods disclosure; do not amend §7 retroactively.
5. **Stale repo-root convenience artifacts** (55-episode metrics, mismatched
   visit sidecars, plus the whole OLD-era CSV litter) — *must-address* (hygiene;
   risk of accidental citation; the state report's own "root convenience copies"
   phrasing invites misreading). Resolvable: delete or move to an `attic/`
   directory in a housekeeping commit (outside this read-only session).
6. **Documented budgets (1000/2000/3000) vs effective 3000-everywhere** —
   *must-address in text*; trivial fix.
7. **"q = 0" printing** — *must-address*; report p-floors and Wilcoxon values.
8. **Dashboard still serving n = 10 numbers without the pooled-20 supersession**
   — *must-address* (violates the registered reporting rule). Resolvable:
   regenerate `phase1.json` from the pooled tree or add a supersession banner.
9. **lab3 auc_reward's confirmatory status** — *must-address in labeling*: it is
   the lab3 lead metric in the REFRAME but sits outside the registered family;
   label it replicated-descriptive (n=10 q=0; s11–20 +15.85 q=0) or register it
   in a (disclosed) follow-up family.
10. **Cycling-mechanism story unproven** — *nice-to-have*: the registered test
    was INDETERMINATE; a fresh registered test of the "prior-entrenched learned
    2-cycle" reading (e.g., predict the specific 1442⇄1450 cycle from init +
    training reward alone, or show that fix (a)/(c) removes it) would upgrade
    §5.4.1; otherwise keep as interpretation.
11. **Determinism/noise fragility (B1) and benchmark effective-n (B9.6)** —
    *nice-to-have*: one noise-robustness run; one sentence on benchmark
    determinism.
12. **Wilcoxon tie floor near ceiling; nominal pairing; correlated family
    members (avg_redundant = wasted + cycling)** — *nice-to-have*: one Methods
    paragraph each; no reruns.
13. **lab3_slow physics divergence (150/0.40)** — *nice-to-have*: cross-chapter
    flag.

## C2. What Phase 1 definitively answers, and what it does not

**Answered (with the strongest support):**

- *Does the KG prior accelerate learning in a clean two-zone lab (lab2)?* Yes —
  +1.9 pp auc_goal, δ = 1.0, replicated across two instruments, three arms
  configurations, and a registered fresh-seed extension; controls null
  [VERIFIED]. This is the thesis anchor and it is solid *as an
  effect-of-the-implemented-prior*; its attribution purely to "physics
  knowledge" awaits caveat 3.
- *Is the harness itself biased toward the KG arm?* No — arm A/B nulls, lab1
  clean floor [VERIFIED].
- *Does structural knowledge of a redundant mechanism help on lab3?* No — it
  charges a measurable tax (timing +53 episodes; cycling +0.74/episode;
  descriptively also redundant/energy/dev), robust to instrument, arm, seeds,
  and decay horizon [VERIFIED].

**Not answered by Phase 1:**

- Whether the lab2-style advantage survives noise, scale, continuous actuation,
  or a wrong prior.
- *Why* the lab3 cycling tax exists mechanically (test INDETERMINATE).
- Whether cross-zone *structural* knowledge can be made to pay in a clean lab at
  non-trivialising magnitudes (the xzone family says "not by an init bonus";
  that is a characterization, not an impossibility proof).
- Anything about asymptotic (final-policy) superiority — the design measures
  speed, and final goal-rates are near-ceiling everywhere.

---

# PART D — PRIORITIZED TO-DO LIST

Ordered by (1) claim-validity, (2) examiner-proofing, (3) polish. "CI runs" assume
the public repo's free Actions minutes; each full phase1 matrix ≈ 152 jobs ≈ 45 min
wall-clock; the 6-hour job cap is nowhere near binding for these cells.

1. **Rewrite the lab3-tax narrative for n = 20** (validity). Update exec-summary
   row 2, §5.4 item 3, §10.3 live items, and add a dated note to Addendum
   2026-07-18b §3 stating that its avg_redundant adjudication was an n = 10
   statement now superseded descriptively. State plainly: registered family
   untouched; redundant/energy/dev taxes are nominally significant descriptives
   at n = 20. Effort: 1–2 h of careful text. Done when: no live section claims
   "cycling only" / "avg_redundant ns" without the n = 20 caveat, and the
   symmetric lab2 goal_rate improvement is recorded as descriptive.
2. **Fix the provenance golden check** (validity-adjacent; CI is red). Add
   pre-inversion/superseded markers to `THESIS_STATE_REPORT.md:843` and `:2548`
   (or teach the checker that those blocks are historical timelines). Effort:
   15 min. Done when: `python analysis/check_provenance.py` exits 0 and CI is
   green.
3. **Adopt the B5 statistical-presentation fixes** (validity of wording). Replace
   every "q = 0"/"p = 0" with "< 10⁻⁴" plus Wilcoxon; restate pooled-20 as
   best-estimate with the seeds-11–20 subset as the confirmatory replication;
   note nominal pairing; note the avg_redundant = wasted + cycling dependency.
   Effort: 2–3 h. Done when: the state report and any thesis tables carry the
   corrected notation.
4. **Run the ontology-free redundancy-heuristic control** (examiner question #1).
   Add `phase1_redundancy_only` (redundancy prior derived from WoT state
   bindings; stereotype layer disabled; no IV gate, no constructive bonus).
   Register it in a dated addendum *before* dispatch (disclose it follows the
   pooled-20 outcome), then one phase1.yml run: profiles lab2,lab3, seeds 1–10
   (~104 jobs, well within limits). Effort: ~1 day code + 1 CI run. Done when:
   the lab2 delta of the heuristic arm is on record and the thesis wording of the
   anchor claim matches the outcome (either "beyond trivially derivable
   redundancy knowledge" or an honest decomposition).
5. **Write the Methods registration-disclosure paragraph into the thesis**
   (examiner). Use Addendum 2026-07-19b §3 verbatim; add the `ef7aaf2`
   commit-message detail, the §7-vs-executed config mismatch (10000 vs 3000
   episodes; kg_xzone vs kg_only), and the H-CL1 family-assignment
   inconsistency. Effort: 1 h. Done when: the paragraph exists in the chapter
   draft and every June number in the thesis carries the
   confirmatory-with-post-hoc-registration label.
6. **Correct the budget documentation** (examiner). Fix §4.1/§3.5.1: all CI cells
   train up to 3000 episodes; lab1 early-stops (~383–401); recompute the
   λ-fraction sentences. Effort: 30 min. Done when: text matches
   `run_full_project.ps1:545` behaviour and archived episode counts.
7. **Repoint or banner the dashboard** (registered-rule compliance). Regenerate
   `dashboard/public/data/phase1.json` from the pooled-20 tree for the three
   registered cells (or add a `_provenance.superseded_by` note). Effort: 1 h.
   Done when: dashboard provenance names the pooled-20 record.
8. **Repo hygiene commit** (examiner-proofing). Move/delete stale repo-root
   result files (the 55-episode metrics, mismatched sidecars, OLD-era CSV/TTL
   litter, `tmp_*` trees) or fence them in an `attic/` with a README; the state
   report's "root convenience copies" phrase should be disambiguated to
   "archive-root". Effort: 2–3 h. Done when: no file at repo root can be
   mistaken for a run-of-record output (verify by re-running check_provenance
   plus a fresh `git status` review).
9. **Label lab3 `auc_reward` correctly everywhere** (examiner). Either add it to
   a small registered follow-up family (disclosing prior sight) or consistently
   caption it "replicated, outside the registered family" and avoid presenting
   internal reward units as user-visible benefit. Effort: text-only, 1 h.
10. **Noise-robustness pilot** (recommended control). One dispatch of
    lab2 × seeds 1–5 with ±10 % multiplicative sensor noise or per-tick sun
    jitter behind a flag (new flow variant; keep the clean flow untouched).
    Exploratory label; purpose is to show the anchor's direction survives noise
    and δ deflates from 1.0. Effort: ~1 day flow+profile work, 1 small CI run
    (~52 jobs). Done when: an exploratory table exists with the noisy-lab2
    delta.
11. **Optional: fresh registered mechanism test for the cycling tax** (polish;
    only if §5.4.1 is to be upgraded). Pre-commit a prediction that
    reproducing training with fix (c) (prior in exploration only) removes the
    1442⇄1450 2-cycle while preserving the lab2 anchor; run lab3 × seeds 1–10.
    Otherwise keep §5.4.1 as interpretation. Effort: 1–2 days.
12. **Polish**: cross-chapter flag for lab3_slow's 150/0.40 physics; a sentence
    on benchmark determinism/effective n; absolute-magnitude framing next to
    every δ = 1.0; keep the single-shot seed-extension rule visible in the
    thesis Methods.

---

*End of audit. Compiled 2026-07-19 against commit `4512ad0`; every [VERIFIED] item
was checked directly in this working tree during the audit session.*

---

# PART E — REMEDIATION LOG (executed 2026-07-19, same day as the audit)

Every Part D item was executed in this session, in validity-first order. This log
records what changed, where, and how each "done" criterion was verified. Items
E.4 and E.10 involve CI runs; their result subsections are appended below as the
runs complete.

## E.1 (D1) lab3-tax narrative rewritten for n = 20 — DONE

**New Addendum 2026-07-19d** in THESIS_STATE_REPORT.md is the authoritative
statement: at pooled n = 20 (sweep_report per-file BH, benchmark family m = 28)
lab3 `avg_redundant` +1.107 [0.352, 1.796] q = 0.0064, `avg_energy` +2.604
q = 0.0029, `avg_dev` +0.5375 q = 0.0375 are significant descriptives against the
KG arm (seeds-11–20 subset independently significant on all three: q = 0.0032 /
0.0016 / 0.0075); `avg_wasted` +0.369 ns. Symmetric favourable correction
recorded: lab2 `goal_rate` +0.028 q = 0.0018 (was q = 0.1027 at n = 10). All
values verified against
`phase1_postinv/pooled20_reanalysis/analysis_out/paired_tests.csv`
(`bh_family_m = 28` read from the file) and
`phase1_postinv/run_29692725784/analysis/out/paired_tests.csv`.

Live sections swept: exec-summary row 2 (tax now "timing + cycling + broader
descriptive efficiency tax"), §5.2 benchmark paragraph (n = 10 statements flagged
with the pooled-20 warning), §5.2 pooled-20 note, §5.4 banner (third amendment
paragraph), §5.4 item 3, §5.4.1 signature parenthetical, §10.3 (redundant tax
moved from "arm-D-only" to live-with-descriptive-label; lab1 bullet marked "not
in pooled tree"), §10.3 bottom line. Dated notes added inside Addendum
2026-07-18b §3 and the 2026-07-18 banner inside Addendum 2026-07-13. The
registered m = 3 family is untouched. "Cycling-only"/"redundant ns (arm-D
stacking)" no longer appears in any live section without the supersession.

## E.2 (D2) provenance golden check — DONE, exits 0

Both violations fixed by stating the true fact in the text (not by weakening the
checker): §5.5 now reads "the **pre-inversion** ablation 27464846574"; Addendum
2026-07-19b §2 item 1 now reads "the **pre-inversion** ablation run ID
27464846574". `python analysis/check_provenance.py` → exit 0 ("provenance check
OK"), re-verified after every subsequent edit in this session.

## E.3 (D3) statistical presentation — DONE

A 6-rule **"Statistical notation and interpretation rules"** block now leads
§5.2: (1) bootstrap floor — every stored `0` reported as < 10⁻⁴, with the finite
Wilcoxon p's for the three registered cells (8.84×10⁻⁵ / 1.43×10⁻³ / 1.19×10⁻³,
verified in `pooled20_registered_family.csv`); (2) nominal pairing (decorrelated
RNG base constants — "matched conditions, not matched noise"); (3)
`avg_redundant` = `avg_wasted` + `avg_cycling` derived-metric dependency; (4)
pooled-20 = best estimate, seeds-11–20 subset = the confirmatory replication;
(5) benchmark determinism / effective n = seeds (added under D12); (6) δ = 1.0 =
unanimity, not magnitude (added under D12). Every live Phase-1 "q=0"/"p=0"
instance replaced with < 10⁻⁴ (exec rows, §5.2 tables + superseded-table quote,
§5.3 table + caption, §5.4 banner + item 1, §10.3, pooled note); an additive
notation note placed under the Addendum 2026-07-19c table (dated records keep
their literal values). Phase-2/3/4 sections retain their old notation — out of
this audit's scope; flagged here as recommended follow-up.

## E.4 (D4) ontology-free redundancy-heuristic control arm — BUILT, REGISTERED; run pending

Code verification first: `isRedundant` and init Rule 1 consume only
`stateVecBitIndex`/`expectedBitValue`, assigned in `discoverActuators` **pass 1**
(WoT-contract enumeration) before any stereotype enrichment — the redundancy
signal is ontology-free by construction. The hard-mask path is dead in the
headline (maskStrict = false), so `getActionPriors` + `getInitPenaltyForZone`
are the only prior channels.

Changes: `StereotypeReasoner.REDUNDANCY_ONLY` (sysprop `stereo.redundancyOnly`,
default false) gates the IV-unsat soft prior and init Rules 2–6, leaving only
the registry-derived redundancy signal; `build.gradle` `_httpKeys` +
`run_full_project.ps1` forward the property; `config/run_config.json` gains
profile `phase1_redundancy_only` (clone of `phase1_kg_only` +
`stereo_redundancy_only: true`); schema updated; `phase1.yml` description
updated. `gradlew compileJava` clean. Flag defaults to false → every existing
profile's data-generating process is byte-identical.

**Registration: Addendum 2026-07-19e** (pre-dispatch, in the dispatched head),
with the required disclosure that it follows the pooled-20 outcome. Registered
primary: lab2 `auc_goal` Δ_red (m = 1); seed-matched comparator Δ_KG(n=10)
= +0.01679; pre-committed ⅓/⅔ interpretation rule (Outcomes A/B/C fixing the
thesis wording of the anchor claim). Dispatch: run_mode=phase1_redundancy_only,
profiles=lab2,lab3, seeds=1–10. *Result subsection appended below when the run
completes.*

## E.5 (D5) Methods registration-disclosure — DONE

New chapter-ready doc **`docs/thesis_methods_phase1_registration.md`**: the
Addendum 2026-07-19b §3 paragraph verbatim, plus the three audit disclosures —
(1) `ef7aaf2`'s commit message reads "docs(phase3): …" while adding the Phase-1
§7 registration (verified via `git log`/`git show --stat`: 171 lines into
pre_registration.md); (2) §7.2 registers `phase1_kg_xzone`
(cross_zone_bonus 3.0, num_episodes 10000) vs the executed headline
`phase1_kg_only` (bonus 0.0, effective 3000 episodes) — two-layer registration
structure stated; (3) H-CL1 *and H-CL4* prescribe "BH family m = 42" for
metrics that §7.4 assigns to the m = 12 learning-speed family — drafting error,
executed families to be stated next to every q. Plus the mandatory labeling
rules (June runs = confirmatory-with-post-hoc-registration + pre-inversion;
s11–20 June rerun = sighted, unregistered; July runs = registered-at-dispatch;
single-shot rule). The doc is added to `check_provenance.py` CURRENT_DOCS, so
its pre-inversion run citations are now guard-checked (checker green).

## E.6 (D6) budget documentation — DONE

§3.5.1 λ entry now carries the correction: λ was calibrated against *declared*
budgets (1000/2000/3000), but `run_full_project.ps1` patches every profile to
run-config `num_episodes` = 3000, so effective ε-floor fractions are
14%/28%/38%; lab1 early-stops at ≈ 383–401 episodes via the Bellman test
(verified in the archived run-of-record metrics: last episode 382 KG / 400
vanilla, lab2/lab3 train the full 3000). §3.5.1 E entry (b) recomputed
(w_ep = 0.70 lab2/lab3, ≈ 0.96 lab1). §4.1 gains a budget-correction banner and
per-lab declared-vs-effective figures; §5.1 protocol line updated.

## E.7 (D7) dashboard repointed/bannered to pooled-20 — DONE

`prepare_data.py`: phase1.json now embeds `registered_pooled20` (the 3-row
registered family CSV) and `_provenance` gains `registered_primary` (naming both
runs, head 02ed6c1, m = 3 family, Addendum 2026-07-19c), `pooled20_source`, and
`n10_role`. `Phase1.jsx`: the lab2 auc_goal and lab3 first-goal tiles now show
the pooled-20 registered values (with the n = 10 record in the sub-line); source
note rewritten to name the pooled-20 registered primary and the 19d descriptive
broadening. `check_provenance.py` now **enforces** the pooled block (golden
prefix 0.0187729 on the pooled lab2 auc_goal, exactly 3 registered rows,
provenance must name pooled-20). phase1.json regenerated; `npm run build` clean;
checker green.

## E.8 (D8) repo hygiene — DONE

Verified first: only 19 tracked files at repo root (all legitimate build/runner
files); every stale CSV/TTL/log at root was untracked/gitignored (local-only).
389 untracked local outputs swept into **`attic/local_outputs/`** (gitignored;
`attic/README.md` documents the fence and why moved-not-deleted). The two
*tracked* OLD-era trees (`tmp_sweep18_results/`, `tmp_sweep_n10_results/`) are
cited by 10+ tracked docs/scripts (Sweep-18 is the registered §6.7 null), so
they were fenced in place with `PROVENANCE_README.md` banners instead of moved.
The state report's ambiguous "root convenience copies"/"root visit sidecars"
phrases disambiguated to "archive-root … inside phase1_postinv/run_29639767776/"
(2 sites). Verified after: repo root holds only tracked project files;
`check_provenance.py` green; `analysis/residual_prior_weight.py` still runs
(reads archive copies, unaffected).

## E.9 (D9) lab3 `auc_reward` labeling — DONE (caption option)

Chose the caption option (no new registered family). Canonical rule added to §0:
`auc_reward` is always captioned **"replicated, outside the registered m = 3
family"** and described as the agent's internal training signal
(steps/energy/deviation-weighted composite), never user-visible benefit. Applied
at: exec row 2, §5.2 caption, §5.4 item 3 (incl. the REFRAME decision), §5.4.1,
§10.2 item 3.

## E.10 (D10) noise-robustness pilot — build/dispatch status recorded below

Flow variant + profile work and the dispatch record are appended below as
executed (kept exploratory; clean flow untouched).

## E.11 (D11) optional cycling mechanism test — SKIPPED, deliberately

Decision: keep §5.4.1 as interpretation. Rationale: the registered Test A
already returned INDETERMINATE (Addendum 2026-07-19a) — the observed toggling
concentrates in one heavily-trained 2-cycle, so the fix-(c) prediction as
written targets a phenomenon the instrumentation could not certify at
registered thresholds; a second underpowered mechanism run would add CI cost
without upgrade potential. §5.4.1's caveats already keep the claim one notch
below the evidence. Revisit only if the thesis needs §5.4.1 upgraded from
interpretation to finding.

## E.12 (D12) polish — DONE

(a) lab3_slow 150/0.40 cross-chapter flag added to §5.5 caveats; (b) benchmark
determinism / effective-n rule 5 and (c) δ-unanimity rule 6 added to the §5.2
notation block, with the absolute-magnitude framing applied at §5.4 item 1
(+0.0188 ≈ 1.9 points of normalized goal-rate AUC); (d) the single-shot
seed-extension rule is stated in the Methods doc (E.5) §3.

## E.13 Verification snapshot after the text/code phase

- `python analysis/check_provenance.py` → **OK (10 docs + dashboard data)**
- `gradlew compileJava` → clean
- dashboard `npm run build` → clean
- `analysis/residual_prior_weight.py` → runs
- run_config.json + schema: `phase1_redundancy_only` validates structurally
- `git status` reviewable: only intended modifications + new docs/attic READMEs

## E.14 CI status notes (2026-07-19, discovered during remediation)

- **sweep-dev.yml was an invalid workflow file** (two step headers had lost
  their newlines, creating duplicate `shell`/`run` keys in one step mapping) —
  GitHub stamped a failed zero-job workflow run on **every push** since at
  least 2026-07-18. Fixed and verified: the next push produced no phantom
  failure. (This failure was attributed to the file path
  `.github/workflows/sweep-dev.yml` in the Actions list and was easy to
  mistake for a real CI failure.)
- **ci.yml's "Smoke training (custom2 / stereo=false / dev)" job is red and
  was already red on main on 2026-06-21** (runs 27906825298, 27900066648 —
  same single job failing, all other jobs green). It is an OLD-era custom-lab
  smoke cell, pre-existing and unrelated to the Phase-1 remediation; the jobs
  that gate this audit's changes (Build & unit tests; Validate Turtle /
  scenarios / dashboard build, which runs `check_provenance.py`) are **green**
  on the remediation head (`75cd390`, ci run 29703116714). Fixing the custom2
  smoke cell is recorded as a follow-up outside Phase-1 scope.

## E.4 RESULTS (appended after run completion, same day)

**Run 29703323649 (dispatch 2) — success, 102/102 jobs.** Head `e664f3f`
(registration ⊂ dispatched tree); results tag
`results-20260719-212249-phase1_redundancy_only-e664f3f` verified on origin;
artifact 8447388203 (sha256 `47c6c1c4…8399`) archived at
`phase1_postinv/run_29703323649/` with MANIFEST; `run_mode` verified in all 40
`TRAINING_OK.json`. Operational proof the knowledge layer was off: the archived
seed-1 KG-arm initial Q-tables contain exactly {0 ×5120, −50 ×4096} per zone
(registry redundancy only) versus {−50, 0, +7.5, +15, +22.5} in a normal
stereo-mode table.

**Registered primary → OUTCOME A.** lab2 `auc_goal` Δ_red = **+0.016656**
[+0.009803, +0.023258], p_boot < 10⁻⁴ (p_wil = 3.9×10⁻³), δ = 0.94 — **99.2% of
the seed-matched arm-C point estimate** (+0.01679), far above the ⅔ threshold.
The pre-committed wording rule is now binding: the thesis presents the lab2
anchor as a decomposition and does not claim the KG prior adds beyond trivially
derivable redundancy knowledge on lab2.

**Descriptive secondaries (blunt reading).** The ontology-free control also
shows a significant lab3 `auc_goal` improvement the full KG arm lacks
(+0.01434, δ = 0.95 vs +0.00035 ns), pays none of the lab3 taxes (first-goal
+1.4 ns; cycling +0.06 ns; redundant −0.475 ns favourable), does not reproduce
the lab3 `auc_reward` win (+0.57 ns vs +16.62), and improves benchmark
goal_rate in both labs (lab2 +0.0375 q = 0.0056; lab3 +0.031 q = 0.029). On
this record the knowledge layer's unique contribution is the lab3 `auc_reward`
win (internal units), purchased at the cost of the lab3 timing + efficiency
taxes. The audit's examiner-question #1 is therefore answered in the
unfavourable direction, and the state report's exec summary, §5.4 item 1, and
§10.3 were rewritten accordingly (Addendum 2026-07-19g).

**Deviation on record:** dispatch 1 (run 29703115983) failed pre-data at
PowerShell `-RunMode` ValidateSet (fixed in `e664f3f`); no data was produced or
seen before dispatch 2.

## E.10 RESULTS (appended after run completion)

**Run 29705215235 — success 27/27** (dispatch 2; dispatch 1 = 29705065298
failed pre-data at the `-OnlyProfiles` KnownProfiles allow-list — second
harness allow-list gap of the day, both now fixed). Head `08bcd6c` contains
Addendum 2026-07-19f; tag `results-20260719-222137-phase1_kg_only-08bcd6c`
verified on origin; archive `phase1_postinv/run_29705215235/` (artifact
8447910059, sha256 `a754bb68…e590`), 10/10 `TRAINING_OK` guards pass.

**Exploratory result:** lab2noise `auc_goal` Δ = +0.01954 [+0.01274, +0.02878],
δ = 1.0, sign-consistent with the clean anchor. **Honest design finding: the
±10% multiplicative noise is structurally sub-threshold** — no achievable lab2
lux value's ±10% band contains a rank bound (nearest crossings need ≈ ±30%),
so the noise never reaches the agent's rank observation space and the run is
effectively a clean-lab2 replicate at n = 5 (which is exactly why δ = 1.0).
The pilot therefore does NOT license "the anchor survives sensor noise"; it
instead documents that the discretization absorbs sub-30% multiplicative
noise by construction. The to-do's actual goal (δ deflation under
observation-reaching noise) remains open; the identified follow-up is ≥ ~30%
noise, additive noise scaled to bound gaps, or per-episode sun jitter across
sunshine-rank bounds. Recorded in the 19f Result note and the archive
MANIFEST.
