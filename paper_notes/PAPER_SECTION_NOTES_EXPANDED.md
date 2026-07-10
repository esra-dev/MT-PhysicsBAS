# Stage 11 Expanded Section Notes

Scope: expanded, prose-form drafting notes for each thesis-template destination
(`content/abstract`, `content/01_chapter1` … `content/05_chapter5`, and
`content/appendix`). This file converts the table-form Stage 11 notes in
`PAPER_SECTION_NOTES.md` and `APPENDIX_NOTES.md` into running paragraphs so the
manuscript-writing pass has narrative scaffolding rather than cells.

This is still drafting scaffolding, not final thesis prose. Every numeric value
remains tied to the immutable locators recorded in the table-form notes; this
file paraphrases and connects them but does not replace them. The full
per-value locator chains stay in `PAPER_SECTION_NOTES.md`,
`PHASE1_TABLES_R2_20260618T075201Z.csv`, the committed Phase 2/Phase 3
`origin/results` CSVs, and `STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`.

## Reading And Labeling Conventions

- Evidence labels `[DIRECT]`, `[DERIVED]`, `[INTERPRETATION]`, `[UNRESOLVED]`,
  and `[SUPERSEDED]` carry the same meaning as in `00_PROTOCOL.md` §3.
- Research-status tags (`POST_HOC_EXPLORATORY`, `ENGINEERING_VALIDATION`,
  etc.) follow `00_PROTOCOL.md` §4. No phase may be written up as
  `PRE_REGISTERED_CONFIRMATORY`: formal post-pivot preregistration is
  `NOT FOUND` (GAP-021 / S9T-019 / P3T-035).
- Numbers stated below are either deterministic (recomputable from raw run
  data) or direct analysis outputs (bootstrap CIs / bootstrap p-values that were
  *not* independently resampled in this environment). The prose flags which is
  which wherever a confidence interval or bootstrap p-value appears, because the
  Stage 9 audit kept those two categories explicitly separate.

---

## `content/abstract.tex` — Abstract

Write the abstract last, after the chapters are settled. The structural plan is a
four-move abstract: problem, method, principal findings, strongest limitation.

**Problem move [DIRECT].** The thesis studies whether semantic / knowledge-graph
(KG) and physics knowledge measurably helps a reinforcement-learning agent
control small simulated building labs, across three increasingly demanding
situations: (i) learning a clean lab whose physics already matches the KG, (ii)
reacting when a component the agent was trained on becomes defective, and (iii)
learning the temporal response behaviour of actuators and feeding that knowledge
back into the KG. These three situations come directly from the advisor's
requirement note (Phase 1 / Phase 2 / Phase 3 framing).

**Method move [DIRECT].** Three mechanisms are evaluated on a JaCaMo (Jason BDI +
CArtAgO) multi-agent stack with a tabular Q-learner, a KG/stereotype reasoner,
and Node-RED illuminance-lab simulators: (1) clean-lab KG/physics priming of the
Q-learner; (2) an expected-versus-actual fault detector that blacklists a
defective component and warm-restarts learning; and (3) a probing routine that
estimates per-actuator response delays, writes them back to the KG as
`ws:responseDelay`, and lets a deadline-aware BDI planner use them.

**Principal findings move.**
- Phase 1 [DERIVED, `POST_HOC_EXPLORATORY`]: in the clean lab2 profile, the
  KG/physics-primed arm (`ql_true`) beats the no-knowledge arm (`ql_false`) on
  goal-reaching AUC, average steps, redundant actions, and goal rate; the
  improvement also replicates on fresh seeds. Lab3 is more nuanced — its reward
  signal improves clearly while its *binary* goal metric does not.
- Phase 2 [INTERPRETATION, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`]: the
  detector achieves complete detection recall and correct component attribution
  across every injected-fault cell tested; the *recovery-speed* advantage of the
  KG arm is narrow — faster for `lab3_f1dead` but not for `lab3_f1inv`.
- Phase 3 [INTERPRETATION, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`]: the
  agent learns the blind's delay to within ~2 % of ground truth and the informed
  planner meets every tight deadline where the delay-blind planner meets none, at
  the cost of higher energy use.

**Limitation move [UNRESOLVED].** State plainly that this is controlled
simulator/lab evidence, not real-building deployment; that no phase was formally
preregistered; that some statistical fields (Phase 1/2 bootstrap CIs and
bootstrap p-values) are reported as original analysis outputs and were not
independently re-resampled; and that exact workflow-dispatch payloads and
artifact-ZIP byte identity remain unverified.

---

## `content/01_chapter1.tex` — Introduction

### 1.1 Problem context [DIRECT]

Open from the advisor's anchoring question: in a *clean* environment, does a
Q-learning agent that is given prior physics/KG knowledge do better than one that
starts tabula rasa? The expected gains were specifically *time-to-goal* and
*avoidance of redundant actions*, with final task success expected to be roughly
comparable between the two. This expectation, not a result, motivates the work
and frames the first research question. Establish here that the agent operates on
small illuminance-control "labs" — rooms with lamps, a spotlight, and motorized
blinds — and that a knowledge graph encodes the nominal physics of those rooms.

### 1.2 Research trajectory [DIRECT]

Explain that the project deliberately unfolds in three phases of rising
difficulty, each building on the previous learner without rewriting it:

1. **Phase 1 — clean labs.** Labs whose true physics is aligned with the KG; the
   question is purely whether KG priors accelerate clean learning.
2. **Phase 2 — weakness labs.** The agent is first trained clean, then dropped
   into a lab where a component it relied on is now broken (dead or inverted). The
   question is whether the agent can notice, discard the broken component, and
   relearn — and whether KG knowledge helps it realign faster.
3. **Phase 3 — process dynamics.** The agent learns the *temporal* behaviour
   (response delay) of each actuator, writes it back into the KG, and uses it to
   satisfy deadline-constrained goals.

Emphasize the strict-separation design: each phase is additive, so Phase 1 and
Phase 2 numerical results stay reproducible even after later phases are built.

### 1.3 Research questions

State three research questions, each carrying its honest status tag. Note up
front that none is preregistered confirmatory (formal preregistration is
`NOT FOUND`), so all three are framed as exploratory / engineering-validation
questions answered against a local pre-run expectation.

- **RQ1 [INTERPRETATION, `POST_HOC_EXPLORATORY`].** Does KG/physics priming
  improve clean-lab Q-learning *speed* and *action efficiency* while preserving
  task success?
- **RQ2 [INTERPRETATION, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`].** Can a
  clean-trained agent recognise unexpected component behaviour, discard the
  defective component, and relearn — and does the KG/physics prior speed
  realignment?
- **RQ3 [INTERPRETATION, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`].** Can
  the agent estimate actuator response delays, materialise them as KG facts, and
  use them to meet time-bounded goals better than a delay-blind planner?

For each RQ, the candidate-RQ table in `RESEARCH_MODEL.md` also records the
expected mechanism and the falsification condition; carry those into the chapter
so each RQ is stated together with what would have counted as a negative result.

### 1.4 Contributions [DIRECT]

Frame four contributions:

1. A **semantic/KG prior for tabular Q-learning** in clean building labs,
   including a cross-zone structural prior that is kept conceptually distinct from
   generic KG priming.
2. A **fault-recognition loop** that compares KG-predicted effects against
   observed effects, blacklists the offending component, and warm-restarts
   learning over the surviving action set.
3. A **response-delay learning mechanism** that probes actuators, writes
   `ws:responseDelay` back to the KG, and drives a deadline-aware BDI planner.
4. A **reproducible evidence layer** — labelled ledgers, immutable locators, and
   a statistical-integrity audit — that makes the provenance and the limits of
   every reported number explicit.

### 1.5 Scope statement [UNRESOLVED]

Bound the claims carefully. The evidence is from controlled Node-RED simulators
and small labs, not deployed buildings. Do not claim formal preregistration, do
not claim byte-verified artifact-ZIP identity, and do not present Phase 1/2
bootstrap intervals as independently reproduced. These scope caveats are not
incidental — they are the same items that reappear as the chapter-5 limitations.

---

## `content/02_chapter2.tex` — Background and Related Work

Keep foundations (what the reader must know) separate from related work (how the
project compares to alternative research). All external sources below are in
`BIBLIOGRAPHIC_LEDGER.csv` (`BIB-S10B-001`…`016`); DOI-only rows are
metadata-verified but not full-text reviewed (see the full-text gap, GAP-046).

### 2.1 Foundations

**MAS and BDI [DIRECT].** Introduce the BDI agent model and the AgentSpeak(L)
programming language (Rao 1996, `BIB-S10B-001`) and the JaCaMo multi-agent
programming platform (Boissier et al. 2013, `BIB-S10B-002`). These are the
implementation foundations: the project's agents are Jason/AgentSpeak plans and
its environment tools are CArtAgO artifacts (e.g. the dynamics agent and
`DynamicsLearner`). Treat these as foundations only — JaCaMo literature does not
supply evidence for the project's KG-prior or delay-learning claims.

**Q-learning [DIRECT].** Present tabular Q-learning via Watkins and Dayan (1992,
`BIB-S10B-003`) as the RL algorithm the project builds on. Explicitly warn that
the Watkins–Dayan convergence theorem must *not* be used as evidence that the
project's runs converged; convergence in these labs is an empirical matter
checked per run.

**Semantic Web / KG metadata [DIRECT].** Introduce SOSA/SSN
(`BIB-S10B-008`, `BIB-S10B-009`) and Brick (`BIB-S10B-010`) as the standard
vocabularies for describing sensors, actuators, and building metadata. Make the
boundary clear: the project uses a *custom* `ws:` stereotype vocabulary (e.g.
`building_2_slow.ttl`, `building_3_slow.ttl`), so do **not** claim SSN/SOSA or
Brick compliance or extension. Note the source-hygiene correction here only if
useful: a wrong Brick DOI candidate was rejected and the correct DOI recorded
(`BIB-S10B-REJ-001` → `BIB-S10B-010`).

### 2.2 Related work

Organize related work into five comparison buckets, each ending with the explicit
*difference from this project*. The taxonomy below maps onto Table RW-1.

**Building-control RL [DIRECT].** Compare with deep RL for HVAC control (Wei et
al. 2017, `BIB-S10B-004`), model-free control of thermostatically controlled
loads (Claessens et al. 2018, `BIB-S10B-005`), sparse-observation direct load
control (Ruelens et al. 2019, `BIB-S10B-006`), and MARL for HVAC (Bayer &
Pruckner 2022, `BIB-S10B-007`). These motivate RL for building control but differ
from the project in domain (HVAC/thermal vs. illuminance), in the use of semantic
priors, and in the BDI/KG layering. State the domain/actuator mismatch
explicitly and do not conflate the project's MAS architecture with multi-agent RL
training.

**KG priors and shaping [DIRECT/INTERPRETATION].** Use KG-enhanced RL in
recommender systems (Zhou et al. 2020, `BIB-S10B-011`) and the equivalence of
potential-based shaping and Q-value initialization (Wiewiora 2003,
`BIB-S10B-012`) as *analogical* and *theoretical* support that structured prior
knowledge can improve sample efficiency and action selection. Stress that KGQR is
not building automation and Wiewiora is theory, not semantic KG; the project's
causal evidence for KG priors must come from the Phase 1 result rows, not from
these sources.

**Physics-informed / model-assisted learning [DIRECT].** Compare with PhysQ
(Gokhale et al. 2022, `BIB-S10B-013`) and model-assisted sensor-fault-tolerant
HVAC control (Xu et al. 2021, `BIB-S10B-014`). These share the motivation that
prior physical knowledge improves building-control learning; the difference is
that the project uses *explicit symbolic RDF/KG priors* and tabular/BDI
mechanisms plus explicit response-delay writeback, not physics-informed neural
representations.

**Fault and anomaly detection [DIRECT].** Compare Phase 2 with transfer learning
for HVAC fault detection (Dowling & Zhang 2020, `BIB-S10B-015`) and KG-based
industrial root-cause diagnosis (Chen et al., `BIB-S10B-016`), plus the
model-assisted fault-tolerant work (`BIB-S10B-014`). The project differs by using
an *expected-versus-actual* KG check followed by blacklisting and relearning,
rather than training a transfer classifier or doing industrial RCA.

**Learned temporal / process dynamics [INTERPRETATION].** Position Phase 3
against the model-free / sparse-observation control works (`BIB-S10B-005`,
`BIB-S10B-006`) and PhysQ (`BIB-S10B-013`): building-control RL usually optimises
a policy directly, whereas this project evaluates whether explicit per-actuator
response-delay knowledge can be *learned, written back to the KG, and consumed by
a deadline-aware BDI planner*. Phrase the novelty as bounded to the tested
slow-lab actuator-delay setting, and do not claim the project learns full
building thermal dynamics.

### 2.3 Related-work artifacts

Plan Table RW-1 (taxonomy: rows = the six buckets above; columns = representative
source IDs, method family, mapped project phase, difference from project) and
Figure RW-1 (a layered map: MAS/BDI execution at the base, KG/stereotype priors
above it, the Q-learning/building-control RL layer, a fault/anomaly branch, and a
learned-response-delay branch, with the project placed at the intersection of KG
priors, the BDI planner, and learned temporal KG writeback). Carry the full-text
gap note [UNRESOLVED]: DOI-only rows need full-text review before any technical
claim beyond title/venue/year.

---

## `content/03_chapter3.tex` — Contributions / Approach

Keep this chapter conceptual. Push file-by-file code mapping to the appendix;
only enough implementation detail to define each mechanism belongs here.

### 3.1 Approach overview [INTERPRETATION]

Describe the work as one coherent research artifact with three layers of semantic
guidance: semantic priors that *accelerate* clean learning (Phase 1), semantic
expected-versus-actual checks that confer *robustness* under faults (Phase 2),
and learned process dynamics that are *written back* to the KG and reused for
time-bounded control (Phase 3). The unifying idea is that a knowledge graph is
not only a static prior but also a destination for newly learned facts.

### 3.2 Phase 1 — clean-lab ladder and semantic priors [DIRECT]

Describe the lab ladder (`lab1`, `lab2`, `lab3`) of increasing state-space size,
the two learning arms (`ql_false` no-prior vs. `ql_true` KG-primed), and the
benchmark modes (`rule_based`, `ql_false`, `ql_true`). Then describe the prior
mechanism: the KG/stereotype reasoner supplies action guidance that belongs to
the initialization / reward-shaping family (consistent with the Wiewiora framing
in chapter 2). Keep the **cross-zone structural prior** — which encodes that
actuators in one zone spill light into adjacent zones — conceptually separate
from generic KG priming, because the Phase 1 ablation specifically tests the
*targeted* cross-zone structure against an equal-budget *untargeted* optimism
baseline (`phase1_kg_xzone_rand`, `cross_zone_bonus=3.0`).

### 3.3 Phase 2 — fault detection, blacklist, relearn [DIRECT]

Present the detect→attribute→blacklist→warm-restart→re-certify loop. The agent
warm-starts from the clean Phase-1 Q-table, then on every step compares the
KG-predicted directional effect of the action it just took against the observed
effect. Accumulated divergence over enough samples flags a component as dead or
inverted; the component's ON and OFF actions are blacklisted (never
`DO_NOTHING`, and always leaving ≥1 action), and a *targeted* warm restart zeroes
only the blacklisted actions' Q-values and visit counts before relearning over
the reduced action set. Describe the false-positive guard: blinds are
interaction-variable-gated (Mediates) actuators whose effect depends on sunlight,
so they are excluded from adjudication; only unconditional-sign Causes actuators
(lamps, spotlight) are judged. Note that all injected faults are on Causes lamps,
so the guard removes a known false positive without ever masking a designed
fault. Define the headline metric here:
`RecoveryEpisodes = ReconvergeEpisode − DetectEpisode`, and the well-posed-cell
restriction that limits recovery-speed inference to cells where a post-fault
survivor policy actually exists.

### 3.4 Phase 3 — response-delay learning and KG writeback [DIRECT]

Present Phase 3 as an evaluated contribution that does *not* train a Q-table
(`task_dynamics.jcm`): the agent (a) probes each URI-bearing actuator from a
known baseline and measures, in simulator ticks, the delay until the controlled
zone rank first rises; (b) maintains a numerically stable Welford running
mean/variance per action and classifies each actuator as instantaneous or
delayed against a threshold; (c) writes the learned values back to the KG as a
Turtle file with `ws:responseDelay`, `ws:responseDelayTicks`, sample counts,
std, and response class; and (d) in an exploit phase, scores every action that
can reach the target zone rank by `(infeasible-flag, energy_cost, believed_delay)`
and picks the lexicographic minimum. The KG-primed arm reads the learned delay;
the tabula-rasa arm believes every actuator is instantaneous. Make the boundary
explicit [UNRESOLVED]: richer temporal goal semantics, additional dynamics
classes, real-building deployment, and broader scheduling integration are future
work, not claims of this chapter.

### 3.5 Approach figures

Plan three schematic figures: (A) system architecture — BDI agents → CArtAgO
artifacts → KG/RDF resources → Node-RED simulator → CSV/log analysis → evidence
ledgers; (B) the Phase 2 mechanism flow — clean Q-table warm-load → unexpected
transition → KG expected-effect check → component blacklist → warm restart →
recovery certification; (C) the Phase 3 pipeline — slow lab → actuator probes →
Welford delay table → `ws:responseDelay` TTL → deadline planner → time-bounded
result CSV.

### 3.6 Implementation / reproducibility (short here, expanded in appendix)

Summarize the stack — JaCaMo, tabular Q-learner, stereotype reasoner,
`DynamicsLearner` artifact, Node-RED labs, Python/Node analysis scripts, GitHub
Actions workflows — and forward the reader to the appendix for the config
matrices, exact commands, and run/artifact provenance.

---

## `content/04_chapter4.tex` — Evaluation

Structure: experiment design matrix first, then per-phase results, then the
statistical-integrity discussion. Every reported value is tied to a committed CSV
row or a complete derived chain; CIs and bootstrap p-values for Phase 1/2 are
flagged as direct analysis outputs that were not independently resampled.

### 4.1 Experiment design matrix

Present five experiments (Table T-EVAL-1). For each, give research status,
baseline, treatment, controls, metrics, and the key caveat.

- **EXP-P1-BUMP [DIRECT, `POST_HOC_EXPLORATORY`].** Does bumped clean-lab
  KG/physics priming beat no-knowledge learning? Baseline `ql_false`, treatment
  `ql_true`, profiles `lab1/lab2/lab3`, selected run `27461188614`. Deterministic
  means/differences recomputed; CI/p/q/Cliff read from analysis CSVs, not
  re-resampled. lab2 is the primary anchor; lab3 reward improves more clearly
  than lab3 binary goal.
- **EXP-P1-REPL [DIRECT, `POST_HOC_EXPLORATORY`].** Do fresh seeds repeat the
  Phase 1 directions? Fresh-seed root `P1-BUMP-S11-20`, run `27462446044`. This
  is replication evidence, not a new preregistered confirmatory test.
- **EXP-P1-ABL [DIRECT, `POST_HOC_EXPLORATORY`].** Does the targeted cross-zone
  structure beat equal-budget untargeted optimism (`phase1_kg_xzone_rand`)?
  Mechanism evidence only; language stays exploratory.
- **EXP-P2-V5 [DIRECT, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`].** Can
  clean-trained agents detect faults, discard the defective component, and
  relearn faster with KG knowledge? Nine fault profiles, modes
  `ql_false`/`ql_true`, 10 seeds per CI cell, selected run `27547019772`,
  result commit `22a448be…`. Recovery-speed inference restricted to
  `lab3_f1dead` and `lab3_f1inv` (the only well-posed cells).
- **EXP-P3-DYN-N10 [DIRECT, `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`].**
  Can the agent learn delays, write them to the KG, and use them for deadlines?
  Profiles `lab2_slow`/`lab3_slow`, modes `ql_true`/`ql_false`, 10 replicas, 6
  goals per cell, `seconds_per_tick=5.0`, `blind_delay_ticks=12`, run
  `27621106006`, result commit `0372ecd5…`. The n5 run is superseded.

### 4.2 Phase 1 results

**Lab2 primary anchor [DERIVED].** This is the strongest clean-lab result.
`ql_true − ql_false` differences: goal-reaching AUC `+0.0197` (CI
`[0.0147, 0.0245]`, q `0.0`, Cliff's δ `1.0`); average steps `−0.9` (CI
`[−1.55, −0.325]`, q `0.0`, Cliff's δ `−0.71`); average redundant actions
`−0.9825` (CI `[−1.59, −0.399]`, q `0.0`, Cliff's δ `−0.72`); goal rate `+0.04375`
(CI `[0.0125, 0.08125]`, q `0.009`, Cliff's δ `0.5`). The directional means and
mean differences are deterministic from raw data; the CIs and q-values are
original analysis outputs. Read this as: KG priming makes lab2 learning faster,
more action-efficient, less wasteful, *and* modestly more successful.

**Lab2 fresh-seed replication [DERIVED].** On fresh seeds, goal AUC difference
`+0.0182` (CI `[0.0106, 0.0273]`, q `0.0`, Cliff's δ `1.0`) and reward AUC
difference `+7.67` (CI `[2.16, 12.91]`, q `0.033`, Cliff's δ `0.6`). The direction
holds, supporting robustness of the lab2 finding.

**Lab3 active boundary [DERIVED].** Be careful and honest here. The bumped lab3
*binary-goal* result is **not** a clean positive: goal AUC difference `−0.00375`
(CI `[−0.00802, 0.00067]`, q `0.296`) — i.e. not distinguishable from zero. But
the lab3 *reward* evidence is clearly positive: reward AUC difference `+14.26`
(CI `[11.23, 17.20]`, q `0.0`, Cliff's δ `1.0`), replicated on fresh seeds at
`+18.85` (CI `[16.21, 21.19]`, q `0.0`, Cliff's δ `1.0`). Report binary-goal and
reward metrics separately for lab3 and do not overstate.

**Superseded as-is lab3 [SUPERSEDED].** The earlier "as-is" lab3 rows
(goal AUC `−0.00885`, q `0.0072`; cycling `+0.3375`, q `0.0252`) are audit/control
evidence only, retained to explain why the bumped targeted run is the lab3
authority — not final lab3 performance numbers.

**Phase 1 statistical caveat [UNRESOLVED].** The Phase 1 table has 480 data rows;
Stage 9 confirmed all deterministic means (348 rows) and mean differences (132
rows) match the raw data with zero mismatches, but the 348 CI rows and 132
p/q/CI rows were not independently resampled. Present Phase 1 CIs/p-values as
reproduced-from-analysis, not re-derived.

### 4.3 Phase 2 results

**Detection and attribution [DERIVED].** In the final v5 run, all 18 CI rows have
`n_runs=10`, `detection_rate=1.0`, and `n_detected=10`; and all 18 cells have
`aggregate_defect_set_matches_expected=true` with `unexpected_component_row_count=0`.
So in the tested injected-fault matrix, detection recall is complete and there are
no spurious attributions. Bound the claim to the tested matrix — do not
generalise to untested fault types or real buildings.

**Well-posed recovery scope [DIRECT].** Only `lab3_f1dead` and `lab3_f1inv` are
marked `well_posed_recovery=True`; all other cells are descriptive/provisional for
recovery-*speed* inference because a clean post-fault survivor policy is not
well-defined there.

**Recovery speed — the honest split [DERIVED].**
- `lab3_f1dead`: KG is clearly faster. `n_paired=10`, `ql_true` mean `150.5` vs.
  `ql_false` mean `363.4`, difference `−212.9` (CI `[−271.9, −148.3]`, Wilcoxon p
  `0.0039`, Cliff's δ `−0.86`, BH q `0.0`, `ql_true_faster=True`).
- `lab3_f1inv`: KG is **not** faster. `n_paired=9`, `ql_true` mean `364.6` vs.
  `ql_false` mean `332.8`, difference `+31.8` (CI `[−137.2, 174.6]`, Wilcoxon p
  `0.496`, Cliff's δ `0.23`, BH q `0.650`, `ql_true_faster=False`).

So the supported Phase 2 headline is narrow: KG-primed recovery is faster than
naive for the dead-lamp case but not for the inverted-lamp case.

**Detection latency [DERIVED].** Detection timing is mixed across the nine
DetectEpisode paired rows (differences ranging `−2.2`…`+126.2`); only
`lab3_f1inv` shows a large, significant positive detection delay (Wilcoxon p
`0.00195`, Cliff's δ `1.0`, BH q `0.0`). Do **not** state that KG generally
detects faster.

**Phase 2 statistical caveat [UNRESOLVED].** Of 521 R2 table rows, 306 are
deterministic-from-raw, 99 deterministic-or-exact-test, 116 direct
analysis-output resampling rows, and 0 failed checks. Bootstrap CIs and bootstrap
p-values were not independently resampled (no Python was available in the audit
environment). The exact Wilcoxon p-values, Cliff's δ, and BH q arithmetic *were*
checked.

### 4.4 Phase 3 results

**Run authority [DIRECT].** Results come from GitHub Actions run `27621106006`
(workflow "Phase 3 (process dynamics, response-delay learning)", success, head
SHA `3bb5289c…`), published to `origin/results@0372ecd5…` under
`phase3/27621106006-20260616-133306/`. The local n10 raw tree has 40 delay files
(180 rows), 40 time-bounded files (240 rows), 40 learned TTL files, and 10
replica directories.

**Delay-learning accuracy [DIRECT].** Learned slowest (blind) delays stay near
the ground-truth 12 ticks: lab2 `ql_false` `12.1125`, lab2 `ql_true` `12.1875`,
lab3 `ql_false` `12.2125`, lab3 `ql_true` `12.2125`; maximum relative error
`1.77 %`. Across all 180 raw delay rows, the response class matched expectation in
180/180 (80 delayed-blind rows, 100 instantaneous non-blind rows).

**Deadline compliance [DIRECT].** `ql_false` compliance is overall `0.5`, tight
`0.0`, loose `1.0` for both slow profiles; `ql_true` is `1.0` on overall, tight,
and loose for both. The informed planner meets every tight deadline the
delay-blind planner misses.

**Paired statistics [DIRECT].** Overall compliance: both profiles `n=10`,
`ql_true` `1.0` vs. `ql_false` `0.5`, difference `0.5` (CI `[0.5, 0.5]`, Wilcoxon
p `0.00195`, Cliff's δ `1.0`, BH q `0.0`). Tight compliance: difference `1.0` (CI
`[1.0, 1.0]`, Wilcoxon p `0.00195`, Cliff's δ `1.0`, BH q `0.0`). Loose
compliance: difference `0.0` (both already meet loose deadlines).

**Energy trade-off [DIRECT].** `ql_true` spends more energy: lab2 total-energy
difference `+3.2` (CI `[3.0, 3.5]`), lab3 `+3.3` (CI `[3.0, 3.6]`), with
`lower_is_better=True` and `ql_true_better=False`. Explain the mechanism: the
informed planner reaches for the fast, powered lamp under tight deadlines instead
of the cheap, slow blind. Lower energy is therefore *not* the headline success
metric — meeting deadlines is — and the energy cost is the conditioned price of
that compliance.

**Mechanism example [DIRECT].** In lab2 rep1, `ql_true` met 6/6 goals while
`ql_false` met 3/6, missing tight goals `g1`, `g2`, `g5` after choosing blinds
with believed delay `0.00`. This single-replica trace makes the abstract numbers
concrete.

**Choice-stability nuance [DERIVED].** Do not claim actuator-label decisions are
bit-identical across replicas: lab3 `ql_true` loose-goal blind labels split 5/5
between `SetZ1Blinds=ON` and `SetZ2Blinds=ON` for goals `g3`, `g4`, `g6`, while
every *met* outcome stayed stable. The compliance result is robust even though
the specific blind chosen for loose goals is not unique.

**Superseded n5 [SUPERSEDED].** The earlier n5 run `27598417789` is audit history
only: at `n_paired=5` the Wilcoxon p floors at `0.0625`, which cannot reach
significance, so the n10 run is the authority candidate.

### 4.5 Statistical integrity and threats to validity [UNRESOLVED]

Devote an explicit subsection to honesty about the evidence. Present the Stage 9
matrix (Figure F-EVAL-4) separating deterministic/exact checks from unresolved
bootstrap-output categories. State the threats: (i) no formal preregistration, so
all results are exploratory/engineering-validation; (ii) Phase 1/2 bootstrap CIs
and p-values are original analysis outputs, not independently re-resampled; (iii)
exact workflow-dispatch payloads are `NOT FOUND` and artifact-ZIP byte identity is
not verified, so committed `origin/results` CSV rows are treated as the numeric
authority; (iv) all evidence is simulator/lab, not real-building. These are the
same items carried into chapter 5.

### 4.6 Evaluation tables and figures

Plan: T-EVAL-1 (experiment matrix), T-EVAL-2 (Phase 1 compact table: lab2 anchor,
lab2 replication, lab3 boundary, superseded as-is rows), T-EVAL-3 (Phase 2
detection/attribution matrix plus well-posed recovery table filtered to the lab3
f1 cells), T-EVAL-4 (Phase 3 delay accuracy, compliance CI, paired compliance,
energy). Figures: F-EVAL-1 (Phase 1 lab2 forest plot + lab3 boundary panel, marked
exploratory with the resampling caveat), F-EVAL-2 (Phase 2 recovery forest plot
for the two well-posed cells + detection/attribution matrix), F-EVAL-3 (Phase 3
grouped compliance bars + paired effect panels + energy panel), F-EVAL-4 (the
statistical-integrity matrix).

---

## `content/05_chapter5.tex` — Conclusions

### 5.1 RQ answers

**RQ1 [INTERPRETATION].** Answer: supported but exploratory. The strongest
clean-lab evidence is lab2, where KG/physics priming improves goal AUC, action
efficiency, redundant-action count, and goal rate, with fresh-seed replication.
Lab3 is split — reward evidence is positive and replicated, but the binary-goal
metric is not distinguishable from zero. Conclusion: KG priors accelerate and
streamline clean-lab learning where the lab is well-aligned with the KG, with the
honest caveat that the binary success benefit is lab-dependent.

**RQ2 [INTERPRETATION].** Answer: supported as engineering validation. The
detector and attribution work across the entire tested injected-fault matrix
(complete recall, no spurious attributions). The KG *recovery-speed* advantage,
however, is narrow and fault-type-dependent: clearly faster for the dead-lamp
case (`lab3_f1dead`), not faster for the inverted-lamp case (`lab3_f1inv`). State
the capability claim (detect → discard → relearn works) separately from the
weaker speed claim.

**RQ3 [INTERPRETATION].** Answer: supported as engineering validation. The agent
learns the blind's response delay accurately (≤1.77 % relative error), writes it
back to the KG, and the informed planner meets every tight deadline the
delay-blind planner misses — at a consistent, explainable energy cost. Bound this
to the two tested slow-lab profiles with a single delayed actuator class.

### 5.2 Limitations [UNRESOLVED]

List, without softening: (1) no formal post-pivot preregistration was found, so
no result is preregistered confirmatory; (2) Phase 1/2 bootstrap CIs and
bootstrap p-values were not independently resampled; (3) exact workflow-dispatch
input payloads are `NOT FOUND` for all phases; (4) local artifact directories are
not ZIP-byte-verified against GitHub artifact digests; (5) all evidence is from
controlled simulators, not deployed buildings; (6) the lab3 stale-magnitude
documentation issue remains; (7) DOI-only related-work rows are not full-text
reviewed; (8) Phase 3 covers a limited dynamics scope (one delayed actuator class
in two profiles).

### 5.3 Future work [INTERPRETATION]

Frame future work as the natural continuation: more actuator/dynamics classes and
richer temporal goal specifications; online/real-building deployment; artifact-ZIP
verification and recovery of exact dispatch payloads; preregistered confirmatory
reruns; independent bootstrap reruns to close the resampling gap; and a full-text
related-work audit of the DOI-only sources.

---

## `content/appendix.tex` — Appendix (expanded routing)

The appendix preserves provenance and reproduction detail without replacing the
primary sources. Organize it as eight sections (A–H), each summarized below; the
exact locator chains live in `APPENDIX_NOTES.md`.

**Appendix A — Source and run provenance.** Record the repository state during
Stage 11 (branch `phase3-process-dynamics`, HEAD `eda6ca1f…`, `origin/results`
`0372ecd5…`); the Phase 1 route (Stage 6 `PHASE1_TABLES.csv` is the authoritative
numeric table, 480 rows, zero deterministic mismatches); the Phase 2 route (run
`27547019772`, v5 head `985c7a18…`, result commit `22a448be…`); and the Phase 3
route (run `27621106006`, head `3bb5289c…`, artifact `phase3-consolidated` id
`7668397627`, digest `sha256:a882677d…`, result commit `0372ecd5…`).

**Appendix B — Reproduction commands.** List the exact extraction/recompute
commands as command notes (not claims they were rerun in Stage 11): the Phase 1
table extractor (`node paper_notes/phase1_extract_tables.mjs …`), the Phase 2
extractor, the Stage 9 audit script, the Phase 3 n10 recompute
(`python analysis/phase3_dynamics.py --root … --out …`), and the tree-hash
command. Mark the n5 recompute command as superseded.

**Appendix C — Experiment matrices.** Give the full profile/mode/timing matrices
per phase: Phase 1 (`lab1/2/3`, stereotype arms true/false, benchmark modes,
component-isolation run modes `phase1_baseline`…`phase1_kg_xzone_rand`); Phase 2
(nine fault profiles × two modes, with parent ports, flows, suffixes, and state
dims); Phase 3 (`lab2_slow`/`lab3_slow`, two modes, `seconds_per_tick=5.0`,
`blind_delay_ticks=12`, `probes_per_actuator=8`, settle/poll/max-wait constants,
target rank 3, probe sun 900, six goals). Note that exact dispatch inputs remain
`NOT FOUND`.

**Appendix D — Statistical integrity.** Reproduce the Stage 9 audit breakdown:
Phase 1 (480 rows, 348 mean + 132 diff rows verified, 348 CI + 132 p/q/CI rows not
resampled); Phase 2 (521 rows: 306 deterministic-from-raw, 99
deterministic-or-exact-test, 116 direct-analysis-output, 0 failures); Phase 2
family sizes (`RecoveryEpisodes` family size 2, `DetectEpisode` family size 9);
Phase 3 recompute (4 delay rows, 4 compliance CI rows, 8 paired rows; delay and
paired CSVs byte-identical to the downloaded consolidated CSVs; compliance CI a
numeric — not byte — match). Add the BH nuance: BH arithmetic was checked from
aggregate bootstrap p-values, but those bootstrap p-values are themselves direct
analysis outputs.

**Appendix E — Full table routes.** Point to the full Phase 1 compact evidence
table (`R2P1T-001`…`014`), the Phase 2 final CI table (18 rows), the Phase 2 final
paired table (rows 2–3 RecoveryEpisodes, 4–12 DetectEpisode), the Phase 2 detailed
verification table (522 rows with input chains), the Phase 3 result tables, and
the bibliographic ledger.

**Appendix F — Figure specifications.** Route the architecture component/dataflow
diagrams, the Phase 1/2/3 figure families, and the related-work map as
evidence-grade figures (not yet rendered).

**Appendix G — Audit history index.** Keep compact supersession tables: Phase 1
as-is → bumped → ablation; Phase 2 v1–v5 (v5 removes the earlier `SetSpotlight`
attribution rows); Phase 3 n5 → n10 (n5 had the Wilcoxon-floor issue); and the
rejected Brick DOI correction.

**Appendix H — Evidence-gap index.** Index the open gaps: GAP-001 (advisor source
provenance), GAP-021 (formal preregistration `NOT FOUND`), GAP-035 (Phase 1 result
limits), GAP-037 (Phase 2 result limits), GAP-044 (Stage 9 statistical boundary),
GAP-045 (Phase 3 authority limits), GAP-046 (related-work full-text), and GAP-047.

---

## Cross-Cutting Discipline Reminders

- Never upgrade exploratory/engineering-validation results to confirmatory.
- Always separate deterministic numbers from not-independently-resampled CIs and
  bootstrap p-values when writing the prose.
- Keep `[SUPERSEDED]` material (Phase 1 as-is lab3, Phase 2 v1–v4, Phase 3 n5) in
  audit history, surfacing it in the main text only when a limitation needs it.
- Use `NOT FOUND` / `NOT VERIFIED` explicitly rather than filling gaps by
  inference (dispatch payloads, artifact-ZIP identity, preregistration).
- Bound every empirical claim to the simulator/lab setting and the specific
  tested matrix.

## Handoff

Completed:

- [DIRECT] Converted the table-form Stage 11 section notes into expanded prose
  drafting notes for the abstract, all five chapters, and the appendix.
- [DIRECT] Preserved evidence labels, research-status tags, key numeric values,
  and the deterministic-vs-resampled distinction.
- [UNRESOLVED] Kept formal-preregistration, dispatch-payload, artifact-ZIP, and
  Phase 1/2 resampling gaps visible in every relevant section.

Unresolved (carried forward unchanged):

- [UNRESOLVED] No polished final thesis prose or LaTeX was written.
- [UNRESOLVED] No figures/tables were rendered.
- [UNRESOLVED] Full-text related-work review of DOI-only rows is still pending.
- [UNRESOLVED] Formal post-pivot preregistration, exact dispatch payloads, and
  artifact-ZIP byte identity remain `NOT FOUND` / `NOT VERIFIED`.

Source basis: `00_PROTOCOL.md`; `PAPER_SECTION_NOTES.md`; `APPENDIX_NOTES.md`;
`PHASE1_RESULTS_R2_20260618T075201Z.md` and `PHASE1_TABLES_R2_20260618T075201Z.csv`;
`PHASE2_RESULTS_R2_20260618T090000Z.md`; `PHASE3_METHODS.md`, `PHASE3_RESULTS.md`,
`PHASE3_TABLES.csv`; `STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md`;
`RELATED_WORK_NOTES.md`; `BIBLIOGRAPHIC_LEDGER.csv`; `RESEARCH_MODEL.md`;
`TEMPLATE_MAP.md`.
