# Audit 02 — The Q-Learning Layer (`QLearner.java`)

**Scope:** `src/env/tools/QLearner.java` (2642 lines) — state/action representation, TD update,
reward decomposition, PBRS, exploration schedule, stereotype-prior machinery, seeding,
convergence/recovery detection, Phase-2 fault detection + blacklist + warm restart, and the
Phase-3 response-delay learner (`src/env/tools/DynamicsLearner.java`). Every number is cited as
`path#Lstart-Lend`. Effective runtime values come from `config/run_config.json` and
`src/agt/lab_profiles.asl`; where a code default differs from the config-forwarded value, both
are listed.

**Git state at time of audit:** branch `phase2-instant-blacklist`, last commit `ba0303e`
dated 2026-07-07. This file documents the **NEW (phase-based) era**. The QLearner artifact is
shared by both eras (the OLD custom8/custom9 sweeps ran the same class at older commits); all
line cites below are to the current working tree. OLD-era-only remnants are flagged inline.

**Config → code plumbing:** `run_config.json`'s `learning` block (`config/run_config.json#L267-L281`)
is forwarded by `run_full_project.ps1#L183-L205` as Gradle `-P` properties
(e.g. `-Preward.clip=…`, `-Pstereo.priorScale=…`), which `build.gradle#L232-L271` re-emits as
JVM `-D` system properties read by `parseDoubleProp`/`parseIntProp`/`parseLongProp`
(`QLearner.java#L134-L151`). Per-profile `learning_overrides` blocks (factorial arms A–D,
`run_config.json#L60-L176`) override individual keys per RunMode.

---

## 1. State representation

### 1.1 Data-driven layout (NEW era)

The state vector layout is **not hardcoded**: `configureQLearner` pulls it from the
`StereotypeReasoner` slot registry parsed out of the lab's ontology
(`QLearner.java#L400-L410`):

- `domainSizes[i]` — cardinality of slot *i*; `strides[i] = ∏_{j>i} domainSizes[j]`;
  `nStates = ∏_i domainSizes[i]` (`#L404-L410`).
- `zoneLevelIndices[z]` — which slot holds zone *z*'s illuminance rank (`#L401`).
- `sunshineIndex` — slot of the sunshine rank, `-1` if absent (`#L402`).

Flat index: $\; \mathrm{idx}(s) = \sum_i \mathrm{clamp}(s_i,\,0,\,d_i-1)\cdot \mathrm{stride}_i$
(`stateVecToIndex`, `#L2450-L2457`; decode `#L2460-L2467`).

The legacy 8-slot example in the class comment —
`[Z1Level(0-3), Z2Level(0-3), Z1Light, Z2Light, Z1Blinds, Z2Blinds, Spotlight, sunshine(0-3)]`,
2048 states — describes the lab3-shaped layout only (`#L22-L28`). Actual per-lab dimensions
(`run_config.json#L241-L260`): lab1=2, lab2=7, lab3=8, lab4=9, lab5=10, labmon=3, labmon2=9,
`*_slow` same as parents.

**What is in the state:** per-zone discretised illuminance rank (0–3), one boolean bit per
actuator (populated from WoT status URIs via `reasoner.getWotStateToSvIndexMap()`,
`#L524-L535`), and the sunshine rank.
**What is NOT in the state:** raw lux values, outdoor illuminance magnitude (only its rank),
energy cost/consumption, time/tick counter, response delays, goal ranks (targets enter only
through the reward), and fault status (blacklisting acts on the action space, not the state).

### 1.2 Per-zone (decomposed / VDN) Q-tables

One Q-table per zone: `qTables[numZones][nStates][nActions]` (`#L186`, allocated `#L413`).
Action selection and bootstrapping use the **combined** value
$Q(s,a) = \sum_z Q_z(s,a)$ (`combinedQ`, `#L2470-L2474`) — a VDN-style value decomposition
(joint argmax `#L2484-L2494`).

## 2. Action space

Dynamically discovered from the ontology by `StereotypeReasoner`: for each actuator an ON
action and an OFF action, plus `DO_NOTHING` (identified by `wotActionType == null`) as the
last action (`#L30-L32` comment; `nActions = reasoner.getNumActions()` `#L395`). There is no
hardcoded action count. Blacklisted actions (Phase 2) are excluded from the applicable set
(`computeApplicableActions`, `#L2517-L2537`). The `maskStrict` hard-masking mode exists for
ablation but has **zero production call sites** (documented dead code, `#L2141-L2147`);
default is soft priors (`maskStrict = false`, `#L202`).

## 3. TD update (Bellman)

`calculateQ(s, a, s')` (`#L553-L657`) performs one decomposed update per zone. With
$Z = $ number of zones, per-zone clipped reward $\tilde r_z$, PBRS term $F_z$ (§5), and the
**joint** bootstrap action $a^{*} = \arg\max_{a'} \sum_z Q_z(s', a')$ over non-blacklisted
actions (`#L571`, `jointArgmaxAction` `#L2484-L2494`):

$$
Q_z(s,a) \;\leftarrow\; Q_z(s,a) \;+\; \alpha \Big[ \tfrac{1}{Z}\big(\tilde r_z + F_z\big) \;+\; \gamma\, Q_z(s', a^{*}) \;-\; Q_z(s,a) \Big]
$$

- Implementation: `newQz = oldQz + alpha * (rForQ + gamma * maxNextQz - oldQz)` (`#L598`),
  with `rForQ = clip(r_z)·(1/Z) + F_z·(1/Z)` (`#L574-L592`, `zoneNorm = 1/max(1,Z)` `#L565`).
- The shared joint $a^{*}$ (not the per-zone independent max) is deliberate — audit Step-3a R-1
  fix against over-estimation (`#L566-L571`).
- `lastBellmanDelta` = max per-zone $|\Delta Q|$ of the step (`#L600-L604`), feeding the
  convergence detector (§8).

### Hyperparameters

| Symbol | Value | Source |
|---|---|---|
| $\alpha$ (learning rate) | **0.1** | `QLearner.java#L53` (no config override path) |
| $\gamma$ (discount) | **0.9** | `QLearner.java#L54` (no config override path) |
| Reward clip | code default **50.0** (`-Dreward.clip`); **effective 200.0** in all CI runs | `QLearner.java#L60`; `run_config.json#L268` → `run_full_project.ps1#L186` |

## 4. Reward decomposition (`computeZoneReward`, `#L2385-L2443`)

Per zone $z$, with `prevLevel`/`nextLevel` the zone rank before/after and
$t_z$ = `effectiveGoal[z]` (== nominal goal except in Phase-2.5b degraded mode, `#L2390-L2392`),
$d = |{\rm level} - t_z|$, $\Delta d = d_{\rm prev} - d_{\rm next}$:

$$
r_z \;=\; -1 \;+\; 40\,\Delta d \;+\; 200\cdot\mathbb{1}[\text{entered goal}] \;+\; 5\cdot\mathbb{1}[\text{held goal}] \;-\; 200\cdot\mathbb{1}[\text{lost goal}] \;-\; 10\cdot\mathbb{1}[\text{no-effect}] \;-\; 5\cdot\mathbb{1}[\text{idle stagnation}]
$$

| Term | Value | Condition | Cite |
|---|---|---|---|
| Step cost | $-1.0$ | always | `#L2398-L2399` |
| Gap term | $+40\cdot\Delta d$ (negative on regression) | rank distance to target changed | `#L2403-L2409` |
| Terminal bonus | $+200$ **once**, on the transition *into* the target rank | `prevLevel != target && nextLevel == target` | `#L2412-L2414` |
| Holding reward | $+5$ per step | stayed at target | `#L2415-L2418` |
| Lost-goal penalty | $-200$ | was at target, moved off | `#L2421-L2424` |
| No-effect penalty | $-10$ | action's `affectedZones` contains $z$, level unchanged, not at goal | `#L2429-L2435` |
| Stagnation penalty | $-5$ | `DO_NOTHING` while zone not at goal | `#L2438-L2440` |

Then per-step clip $\tilde r_z = \max(-C, \min(C, r_z))$ with $C=$ `REWARD_CLIP`
(`#L574`), and zone-normalisation $\tilde r_z / Z$ before entering the update (`#L575`).
Metrics CSVs record the clipped but **un-normalised, un-shaped** $\tilde r_z$ (`#L594`,
`#L607-L608`).

**Energy is NOT in the reward.** There is no energy term anywhere in `computeZoneReward`.
Energy enters only as a *non-fading greedy-selection prior* (Phase 4 / lab5):
$q \mathrel{-}= w_E \cdot \mathrm{energyCost}(a)$ for activation actions of costed actuators
(`#L2601-L2607`), with $w_E =$ `stereo.energyPriorWeight`, code default **0.0** = OFF
(`#L80`), set to **2.0** only by the `phase4` profile (`run_config.json#L174`, `#L458`).
Design rationale documented at `#L69-L80`.

## 5. Potential-Based Reward Shaping (PBRS)

Gated by `-Dreward.shaping=pbrs` (`#L112-L113`). Per zone (Ng, Harada & Russell 1999,
`#L102-L111`):

$$
\Phi_z(s) = -\big|\,\mathrm{level}_z(s) - t_z\,\big|, \qquad
F_z = \gamma\,\Phi_z(s') - \Phi_z(s)
$$

added as `rForQ += F * zoneNorm` (`#L581-L593`). Effective setting: the global `learning`
block enables it (`"reward_shaping": "pbrs"`, `run_config.json#L277`), but the **headline
factorial arm C (`phase1_kg_only`) turns it OFF** (`"reward_shaping": "none"`,
`run_config.json#L90`), as do arms A (`#L74`) and the KG-X arm (`#L157`); arm B is PBRS-only
(`#L125`), arm D / `phase1_full` is PBRS+trust (`#L141-L142`).

## 6. Action selection

### 6.1 ε-greedy

`getActionFromState` (`#L666-L681`): with probability $\varepsilon$ pick uniformly from the
applicable (non-blacklisted) set, else `greedyAction`. An anti-stuck variant excludes recently
repeated actions + DO_NOTHING when the bench agent detects 3 identical consecutive states
(`#L695-L742`).

### 6.2 ε schedule

$$
\varepsilon_0 = 0.3,\qquad \varepsilon \leftarrow \max(\varepsilon_{\min},\ \varepsilon\cdot\lambda) \text{ once per episode},\qquad \varepsilon_{\min}=0.01
$$

- Start **0.3** (`#L55`), min **0.01** (`#L57`), code-default decay **0.995** (`#L56`).
- Per-profile decay $\lambda$ is injected via `setEpsilonDecay` (`#L1735-L1739`) from
  `lab_profiles.asl` `training_params(NumEpisodes, EpsilonDecay)`:
  lab1 = (1000, **0.9920**) `lab_profiles.asl#L272`; lab2 = (2000, **0.9960**) `#L287`;
  lab3 = (3000, **0.9970**) `#L303`; lab4/lab5 = (3000, 0.9970) `#L343`,`#L358`;
  labmon = (1500, 0.9950) `#L382`; labmon2 = (4000, 0.9975) `#L408`.
- Applied by the training agent at `illuminance_controller_agent_ql.asl#L179-L185`, by the
  adapt agent at `illuminance_controller_agent_adapt.asl#L185-L191`.
- Phase-2 warm restart re-boosts $\varepsilon \leftarrow \max(\varepsilon, 0.30)$
  (`fault.relearn.epsBoost` default **0.30**, `#L311`; applied `#L1388`).

### 6.3 Stereotype soft prior + decay + fade + trust

In stereotype mode (soft priors), the greedy score is
(`greedyAction`, `#L2540-L2618`):

$$
\mathrm{score}(s,a) \;=\; \sum_z Q_z(s,a)\;+\;\underbrace{w_{\rm prior}(e)\cdot \pi_a(s)\cdot \mathrm{calMul}_{a,b}\cdot \mathrm{cellMul}_{s,a}}_{\text{fading KG prior}}\;-\;\underbrace{w_E\cdot \mathrm{energyCost}(a)}_{\text{non-fading, lab5 only}}
$$

where $\pi_a(s)$ is the ontology prior from `reasoner.getActionPriors(sv)` (`#L2549`;
magnitudes `stereo_prior_redundant=1.0`, `stereo_prior_iv_unsat=5.0`, `stereo_init_bonus=15.0`
from `run_config.json#L272-L274` — reasoner internals covered in `01_kg.md`), and:

- **Episode decay** (`#L2557-L2560`): with $e$ = `currentEpisodeNum`, $E$ = `priorDecayEpisodes`,
  $f$ = `PRIOR_DECAY_FLOOR`:
  $$
  w_{\rm prior}(e) \;=\; S \cdot \Big[\,1 - \min\!\big(1, \tfrac{e}{E}\big)\,(1-f)\Big]
  $$
  $S$ = `stereo.priorScale`, code default **1.0** (lowered from 5.0 in audit Step 3b §S3b-4,
  `#L61-L67`); run_config **1.0** (`run_config.json#L269`); H5/arm-A ablation **0.0**
  (`#L72`, which also zeroes the Q-init, `QLearner.java#L439-L446`).
  Floor $f$ code default **0.0** (lowered from 0.1, `#L90-L94`); run_config **0.0** (`#L271`).
  $E$: sysprop default −1 → "auto" 0.25 × num_episodes via `setTrainingBudgetEpisodes`
  (`#L86-L89`, `#L2170-L2182`, fallback constant 2500 `#L89`) — **but** the run_config
  learning block forwards `stereo_prior_decay_episodes = 10000` (`run_config.json#L270` →
  `run_full_project.ps1#L188`), and a positive sysprop **disables the auto-coupling**
  (`#L2172-L2177`). So in config-driven CI runs $E = 10000$, i.e. with 1000–3000-episode
  phase-1 budgets the prior only decays part-way (e.g. lab3: $e/E = 3000/10000$ → prior
  still at 70 % of $S$ at end of training).
- **Per-cell visit fade** (`#L2585-L2591`): $\mathrm{cellMul} = \min(1, V_f / \mathrm{visits}(s,a))$
  with $V_f$ = `stereo.priorFadeVisits` = **25** (`#L100`; no config override key in the
  `learning` block).
- **Adaptive trust** (`#L2571-L2578`): per (action, sun-bucket) *running mean* — not an EMA —
  of the per-step fraction of zone slots where the KG-predicted sign matched the observed sign
  (accumulation `#L628-L645`): $\mathrm{cal} = \frac{\sum \text{matched/considered}}{N}$,
  applied only when $N \ge$ `stereo.adaptiveTrust.minSamples` = **50** (`#L126`;
  `run_config.json#L279`), clamped below at `stereo.adaptiveTrust.floor` = **0.1**
  (`#L127`; `run_config.json#L280`), upper bound 1.0 by construction. Code default
  **disabled** (`#L125`); run_config `learning` block enables it (`#L278`) but arms A/B/C and
  KG-X disable it (`run_config.json#L75`,`#L92`,`#L127`,`#L158`); arm D enables it (`#L142`).
- **Tie-break:** among actions within $10^{-9}$ of the best score, uniform random pick
  (`#L2608-L2617`).

Q-init in stereotype mode: every cell pre-filled with
`reasoner.getInitPenaltyForZone(fullSv, a, z, goal)` (`#L477-L486`); zero-init when
stereotypes off or priorScale = 0 (`#L439-L449`).

### 6.4 Bench-time restoration

The bench agent never calls `beginEpisode`, so `loadQTable` explicitly sets
`currentEpisodeNum = priorDecayEpisodes` (prior at floor regime, audit S3b-1 fix,
`#L2235-L2241`) and restores the visit-count and adaptive-trust sidecars
(`*_visits.csv`, `*_trust.csv`, `#L2243-L2249`; written at `#L1924-L1927`). Per-zone Q-table
files are preferred over the lossy combined/divide-by-Z fallback (`#L2213-L2233`).

## 7. Seeding & reproducibility

- Base seed: `42 ^ (useStereotypes ? 0x5A5A5A5A5A5A5A5AL : 0xA5A5A5A5A5A5A5A5L)`
  (`#L373`) — stereo-on/off runs explore different trajectories by design (`#L368-L372`).
- `RUN_SEED` = `-Drun.seed`, default **0** = off (`#L129-L132`); when set,
  `baseSeed ^= mix64(RUN_SEED)` (`#L374`).
- `mix64` is the **SplitMix64 finalizer** (constants `0xBF58476D1CE4E5B9`,
  `0x94D049BB133111EB`, shifts 30/27/31; `#L152-L159`) so small seeds 1..N yield
  well-separated PRNG streams.
- `setSeed(long)` op allows explicit reseeding for benchmark runs (`#L838-L842`).

## 8. Convergence criteria

**Phase-1 (training) — Bellman stability:** an episode counts as "stable" when its max
per-step Bellman delta `episodeMaxBellmanDelta` < `CONVERGENCE_THRESHOLD` = **1e-3**
(`#L252`, tested `#L1823`); `hasConverged` = **100** consecutive stable episodes
(`convergenceWindow`, `#L251`, `#L1832-L1834`).

**Phase-2.1 (recovery) — greedy-policy stability:** the Bellman test cannot settle post-fault
(residual ε-boost noise, stochastically reachable sun-gated goals — rationale `#L320-L327`).
Instead `updateRecoveryDetector` snapshots the full greedy policy
$\pi(s) = \arg\max_a \sum_z Q_z(s,a)$ over all states each adapt episode (`#L1845-L1855`);
`hasRecovered` = policy unchanged for `fault.recover.window` = **50** consecutive episodes
(`RECOVERY_WINDOW`, `#L330`, `#L1864-L1867`). Headline Phase-2 metric:
`RecoveryEpisodes = ReconvergeEpisode − DetectEpisode` (`saveRecoveryLog`, `#L1437-L1474`).

## 9. Phase 2 — fault detection, blacklist, warm restart

**Era note:** this branch (`phase2-instant-blacklist`) implements **Phase 2.3 "INSTANT
isolation"**. The evidence-accumulation thresholds the task list names
(`fault.detect.minSamples` / `deadRate` / `invRate` / `anomalyRate`) **have been removed** —
the code comment records their deletion explicitly (`#L306-L310`); a component is blacklisted
on its **first** unambiguous, falsifiable, component-attributable anomaly (`#L257-L281`,
`#L1238-L1252`). Remaining numeric knobs:

| Knob | Default | Cite |
|---|---|---|
| `fault.relearn.epsBoost` (ε after warm restart) | **0.30** | `#L311` |
| `fault.detect.suspectMin` (dead+inverted obs to mark a co-feeder "suspect") | **2** (plus a 1-inverted-observation fast path) | `#L318`, `#L1270-L1274` |
| `fault.detect.ivMinSunRank` (min sun rank to adjudicate a blind's OPEN) | **2** | `#L344-L345` |
| `fault.recover.window` | **50** | `#L330` |

**Detection (`observeForFaults`, `#L1078-L1253`).** For the dispatched action's KG prediction
vs the observed transition: **DEAD** = actuator bit dropped (`#L1143-L1145`) or bit flipped but
every falsifiable claimed zone showed zero rank response (`#L1210-L1211`); **INVERTED** =
any claimed zone moved opposite to the KG sign (never gated, `#L1164-L1170`, `#L1197-L1200`).
False positives are prevented **structurally, not statistically**: (i) only falsifiable claims
scored — non-zero bit claim (`#L1137-L1138`) and non-saturated zone (`#L1160-L1162`);
(ii) multi-zone Causes feeders (Spotlight) never adjudicated (`#L1101-L1116`);
(iii) IV-gated blinds adjudicated only on OPEN with sun rank ≥ 2 (`#L1129-L1133`);
(iv) zones fed by an already-blacklisted Causes actuator skipped ("contaminated",
`#L1153-L1157`, set in `#L1336-L1344`); (v) abstain when a fault-suspect co-feeder could mask
the zone's null response (`#L1171-L1209`, `zoneHasSuspectCoFeeder` `#L1284-L1297`).
Counters `faultObsN/faultDeadN/faultInvertN` are kept only to power the suspect guard
(`#L1220-L1225`). An active diagnostic probe opens untested blinds under adequate sun
(`getDiagnosticProbeAction`, `#L1011-L1047`; healthy blinds verified once via `probeVerified`,
`#L1233-L1236`).

**Blacklist (`blacklistComponent`, `#L1306-L1346`).** Removes BOTH polarities of the
component's actions; DO_NOTHING never removed; last surviving actuator action protected
(`#L1317-L1327`); marks fed zones contaminated (`#L1336-L1344`).

**Warm restart (`warmRestart`, `#L1362-L1411`).** (1) zero blacklisted action columns +
visit counts (`#L1372-L1380`); (2) halve (×0.5) all surviving Q in "poisoned" states whose
pre-wipe unfiltered argmax was a blacklisted action (`#L1365-L1371`, `#L1382-L1386`);
(3) $\varepsilon \leftarrow \max(\varepsilon, 0.30)$ (`#L1388`); (4) prior-decay clock reset
`currentEpisodeNum = 0` so KG priors regain weight during re-learning (`#L1389`);
(5) convergence + recovery detectors reset (`#L1390-L1394`); (6) fault-evidence counters
re-baselined for sequential multi-fault isolation (`#L1395-L1406`).

**Phase 2.5b — best-effort degradation.** After blacklisting, a deterministic reachability
probe enumerates all $2^k$ surviving-actuator combinations ($k \le 16$ cap, `#L1649-L1672`,
combos `#L1680-L1689`); if the nominal goal rank is unreachable, `effectiveGoal[z]` is lowered
to the closest achievable rank (argmin $|{\rm rank} - {\rm goal}|$, ties toward higher rank,
`#L1696-L1706`, `#L1714-L1729`). `isTerminal` and the reward target both read `effectiveGoal`
(`#L1568-L1578`, `#L2390-L2392`); in clean labs `effectiveGoal == goal` (`#L362-L366`).

## 10. Phase 3 — response-delay learning (`DynamicsLearner.java`)

**Estimator.** The dynamics agent runs controlled probe trials (pin baseline via `/setState`,
read the simulator `Tick` clock, toggle ONE actuator, poll until the target zone rank is
reached; `DynamicsLearner.java#L19-L24`, orchestration described in `run_config.json#L409`).
Each measured delay (in env ticks) is folded into a per-action **Welford** running
mean/variance (`recordDelaySample`, `DynamicsLearner.java#L121-L130`):

$$
\mu_n = \mu_{n-1} + \frac{x_n - \mu_{n-1}}{n}, \qquad
M_{2,n} = M_{2,n-1} + (x_n - \mu_{n-1})(x_n - \mu_n), \qquad
\sigma^2 = \frac{M_{2,n}}{n-1}
$$

(variance at write-out, `#L199-L200`). Seconds conversion:
$\mu_{\rm sec} = \mu_{\rm ticks} \cdot \mathrm{secondsPerTick}$ (`#L155`, `#L201`), with
`seconds_per_tick` = **5.0** (`run_config.json#L412`). Ground truth:
`blind_delay_ticks` = **12** → 60 s (`run_config.json#L413`, `#L443`).

**Thresholds:**

| Knob | Default | Cite |
|---|---|---|
| `dynamics.learner.minSamples` (min samples before a delay is written to the KG) | **3** | `DynamicsLearner.java#L57` |
| `dynamics.instant.threshold.sec` (`INSTANT_THRESHOLD_SEC`; below → `ws:InstantaneousResponse`, else `ws:DelayedResponse`) | **30.0 s** (= 6 ticks; midpoint between the lamp's ~5–10 s HTTP-polling measurement floor and the blind's 60 s) | `DynamicsLearner.java#L58-L60`, rationale `#L44-L51` |

Probe budget (`run_config.json#L435-L442`): `probes_per_actuator` = **8**, `settle_ms` = 400,
`poll_ms` = 50, `max_wait_ticks` = 60, `target_rank` = 3, `probe_sun_rank` = 900;
smoke runs use 3 probes (`#L414`).

**KG writeback (`saveLearnedDynamics`, `DynamicsLearner.java#L176-L230`).** For each action
with $n \ge 3$ samples, one `learned:ResponseDynamic` blank node is written to a Turtle file
(`learned_dynamics_stereotypes_<bool><suffix>.ttl`, `run_config.json#L409`) carrying:
`learned:action` (WoT URI), `learned:actionValue`, `learned:actionLabel`,
**`ws:responseDelay`** (seconds, `xsd:decimal`, 4 dp — the unit temporal goals use,
`#L214-L215`), `ws:responseDelayTicks` (rounded, `#L216`), `ws:responseDelaySamples`
(`#L217`), `learned:responseDelayStdTicks` (`#L218-L219`), and `learned:responseClass`
(`#L203-L205`, `#L220`). This augments the *asserted* `ws:hasResponseDynamic` markers in the
`*_slow` domain ontologies with *measured* numeric delays (`#L171-L174`).

**Exploitation.** Time-bounded goals g1–g6 (deadlines 15/45/90/300 s,
`run_config.json#L444-L451`): the ql_true arm plans with the learned delay, ql_false assumes
zero delay (`#L443`); outcomes logged per goal via `recordExploitResult`/`saveExploitResults`
(`DynamicsLearner.java#L288-L320`).

## 11. Instrumentation summary (for cross-referencing result CSVs)

- Per-episode metrics row: `Episode, Steps, RewardZ1, RewardZ2, GoalReached, Epsilon,
  WastedByPenalty, WastedByNoEffect` (`#L1810-L1824`, header `#L1876`); summary footer with
  `FirstGoalEpisode`, `TotalGoalCount`, `GoalRate_last100` (`#L1883-L1892`).
- `WastedByPenalty` = any zone's regression / lost-goal / no-effect penalty fired
  (`#L2408`, `#L2423`, `#L2434`); `WastedByNoEffect` = state vector unchanged (`#L613-L615`).
- Coverage: per-(state, action) visit counts (`#L242`, `#L2057-L2094`); per-start-state
  first-goal episodes (`#L2104-L2119`); recovery CSV schema `#L1463`.

## NOT FOUND / explicitly absent

- No learning-rate (α) or discount (γ) config override key exists — α and γ are compile-time
  literals (`#L53-L54`); `run_config.json` has no `alpha`/`gamma` key.
- No `fault.detect.minSamples` / `deadRate` / `invRate` / `anomalyRate` properties exist in
  the current tree (removed by Phase 2.3, `#L306-L310`).
- No epsilon-start override — `epsilon = 0.3` is a field initialiser (`#L55`); only the decay
  rate is profile-configurable.
- Energy appears nowhere in `computeZoneReward` — confirmed absent from the reward (§4).
