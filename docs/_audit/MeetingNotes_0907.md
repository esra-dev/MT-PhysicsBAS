# Thesis Meeting - 1307

> **Historical record (meeting of 2026-07-13) — the Phase-1 readings below are
> superseded.** The arm-C dispatch flagged as outstanding in §5.1 ran on 2026-07-18
> (run 29639767776, archived at `phase1_postinv/run_29639767776/`) and re-adjudicated
> the §5 arm-D readings: the lab3 first-goal regression is significant again under
> arm C (+67.56, q = 0.0104), the lab3 efficiency tax narrows to `avg_cycling`
> (+0.744, q = 0.0154; `avg_redundant` ns), and the lab1 +0.0225 blemish vanishes
> (q = 0.369). Every §5 number below is an arm-D number and must be cited as such.
> Current adjudication: `THESIS_STATE_REPORT.md` §5.2, §10.3, Addendum 2026-07-18b.

| Phase | Status | Headline result |
|---|---|---|
| 1 - clean labs | Arm-D run of record (29105464710); arm-C dispatch still outstanding | lab2 `auc_goal` Δ=+0.01924, q=0, δ=1.0; lab1 a floor control (only a trivial +0.0225 redundant-action penalty) |
| 1 - lab3 cross-zone | Complete | `auc_reward` win (Δ=+12.47, q≈0, δ=0.98); `auc_goal` null; `mean_first_goal` ns. Weakness is a final-policy efficiency tax: cycling +1.21, redundant +1.58 (both q≈0) |
| 2 - fault detect → re-learn | Complete (§9.10) | 3/8 Tier-1 recovery cells significant (`lab2_f1bdead`, `lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun`); detection family null |
| 3 - dynamics learning | Complete | Blind delay learned to ≤1.46% error, written back to the KG; KG arm meets 6/6 deadlines vs 3/6 (29166356524) |
| 4 - energy & dependency ladder | Complete — extension beyond the three phases | `avg_redundant` advantage grows with dependency depth (−0.33 / −0.93 / −1.46, all q≈0); lab5 energy compliance +0.096 (q≈0) at goal parity (29193486193, n=20) |

---

## 1. System architecture

A JaCaMo application (Jason BDI agents + CArtAgO artifacts) driving Node-RED lab simulators over HTTP/WoT. One agent per phase: `_ql` (training), `_bench` (benchmark), `_adapt` (fault adaptation), `_dynamics` (delay probing). The key Java artifacts are `QLearner` (tabular Q-learning + fault machinery), `StereotypeReasoner` (KG parsing, priors, IV gate), `StereotypeLearner` (Welford effect discovery), and `DynamicsLearner` (delay estimation + KG write-back). All agents share `lab_profiles.asl`; experiments run on GitHub Actions.

Both arms enumerate their action space from the WoT Thing-Description contract alone. The stereotype layer only enriches it (initial-Q shaping, runtime priors, IV gating) and never decides what actions exist, so the two arms are capability-identical — the only difference is knowledge.

Each training step: sense the lab (lux → ranks 0–3), pick an action ε-greedily from the KG-primed score, send it as a WoT action, sense again, apply the Bellman update, let the stereotype learner observe the transition, recurse.

---

## 2. Knowledge graph & ontologies

### 2.1 Mechanism patterns

Two patterns in the building TTLs:

- **Causes** (lamp, spotlight, monitor): the manipulated variable drives the dependent variable directly, sign asserted via `elem:increases`.
- **Mediates** (blind): `ws:blindApertureRatio` gates a transfer from `ws:outdoorIlluminance` to indoor illuminance. The sign is state-dependent, so `elem:increases` is omitted and only a structural bound (`ws:ivMinRank 1`) is asserted — the quantitative sunshine threshold is exactly what the agent must learn.

lab3 cross-zone spill is encoded as `brick:feeds` arcs (primary vs. weak coupling) with the secondary magnitude intentionally absent: structure only, magnitudes learned. For Phase 3 the KGs assert a qualitative `ws:hasResponseDynamic` class (instantaneous vs. delayed) but leave `ws:responseDelay` valueless; measured delays are written back as `learned:ResponseDynamic` records.

### 2.2 How the KG influences learning (three channels)

1. **Initial-Q penalties**, applied once at table build (scale 0.5): redundancy −100, IV gate −100, cross-zone overshoot −50, shared actuator at goal −75, plus a +15·gap bonus toward helpful ON actions.
2. **Runtime soft priors** that fade over episodes: −1.0 for redundant actions, −5.0 when the IV is (as far as learned) unsatisfied. Each is multiplied by an episode-decay weight, a per-cell visit fade, and — arm D only — an adaptive-trust factor tracking how often the KG's sign matched the observed one.
3. **A learned-statistics IV gate**: per (action, sunshine-rank) counts open the gate once effectiveness reaches ≥ 0.05 with ≥ 10 samples (under-sampled ranks treated optimistically). This is how the blind's unquantified sunshine threshold is learned, and it persists from training into the benchmark.

The state layout is also KG-driven, via `ws:stateVecIndex` / `ws:stateDomainSize` triples (lab3: 2 048 states; lab1: 8). Indoor illuminance discretises to ranks 0–3 at {50, 100, 300} lux, sunshine at {50, 200, 600} lux.

---

## 3. Q-learning

### 3.1 State & action space

- **State:** per-zone illuminance rank (0–3), one boolean per actuator, sunshine rank. Raw lux, energy, time, and fault status are deliberately excluded.
- **Q-tables:** one per zone (VDN-style); greedy selection uses the summed value $Q(s,a)=\sum_z Q_z(s,a)$.
- **Actions:** the ON/OFF pair per actuator from the WoT contract, plus DO_NOTHING; blacklisted actions excluded. The stereotype layer only annotates these — it can neither add nor remove any.

### 3.2 TD update

$$
Q_z(s,a) \;\leftarrow\; Q_z(s,a) + \alpha \Big[ \tfrac{1}{Z}\bigl(\tilde r_z + F_z\bigr) + \gamma\, Q_z(s', a^{*}) - Q_z(s,a) \Big]
$$

with $a^* = \arg\max_{a'} \sum_z Q_z(s', a')$ — all zones bootstrap on the same joint action, a deliberate guard against over-estimation.

### 3.3 Reward

Per zone $z$, with $\Delta d = d_{\rm prev} - d_{\rm next}$ (change in distance to target):

$$
r_z = -1 + 40\,\Delta d + 200\cdot\mathbb{1}[\text{goal entered}] + 5\cdot\mathbb{1}[\text{goal held}] - 200\cdot\mathbb{1}[\text{goal lost}] - 10\cdot\mathbb{1}[\text{no-effect}] - 5\cdot\mathbb{1}[\text{idle stagnation}]
$$

clipped to [−200, 200] and normalised by zone count. Energy is *not* in the reward — it appears only as a non-fading greedy-selection penalty in lab5 (§8).

### 3.4 Action selection: ε-greedy with a fading KG prior

$$
\varepsilon_0 = 0.3,\qquad \varepsilon \leftarrow \max(0.01,\; \varepsilon\cdot\lambda)
$$

The greedy score in KG mode (arms C / D):

$$
\mathrm{score}(s,a) = \sum_z Q_z(s,a) + \underbrace{w_{\rm prior}(e)\cdot \pi_a(s)\cdot \mathrm{calMul}_{a}\cdot \mathrm{cellMul}_{s,a}}_{\text{fading KG prior}} - \underbrace{w_E\cdot \mathrm{energyCost}(a)}_{\text{lab5 only}}
$$

with $w_{\rm prior}(e) = S\cdot\bigl[1 - \min(1,\,e/E)(1-f)\bigr]$. The factorial arms separate the channels: arm C (`phase1_kg_only`) runs the prior alone (PBRS and trust off); arm D (`phase1_full`) layers PBRS and adaptive trust on top.

### 3.5 Key hyperparameters

| Parameter | Value |
|---|---|
| α / γ | 0.1 / 0.9 (compile-time constants) |
| ε₀ / ε_min | 0.3 / 0.01 |
| λ (ε-decay, per profile) | lab1 0.9920 · lab2 0.9960 · lab3–5 0.9970 · labmon 0.9950 · labmon2 0.9975 |
| Reward clip | 200 (all CI runs) |
| Prior scale S / decay horizon E / floor f | 1.0 / 10 000 ep / 0.0 |
| Prior fade visits V_f | 25 |
| Prior magnitudes (redundant / IV-unsat / init bonus) | 1.0 / 5.0 / 15.0 |
| IV gate (min samples / effectiveness threshold) | 10 / 0.05 |
| Convergence criterion | Bellman delta < 1e-3 for 100 consecutive episodes |
| Recovery criterion | Greedy policy unchanged for 50 consecutive episodes |

With E = 10 000 and 1 000–3 000-episode budgets, the prior only decays part-way during training (lab3: ~70% of its initial weight at the end).

---

## 4. Labs & physics

All profiles share `light_bounds([50,100,300])`, `sunshine_bounds([50,200,600])`, `sunshine_prob(0.75)`, and a rank-3 target (≥ 300 lux). Sunshine is sampled once per episode then pinned; within-episode physics is deterministic.

### 4.1 Phase 1 - the clean lab ladder

**lab1** - 1 zone, 1 lamp, 1 000 episodes:
```js
z1 = 25 + (z1light ? 400 : 0);
```

**lab2** - 2 independent zones, adds the Mediates blinds, 2 000 episodes:
```js
z1 = 25 + (z1l ? 400 : 0) + (z1b ? 0.50*sun : 0);
z2 = 25 + (z2l ? 400 : 0) + (z2b ? 0.50*sun : 0);
```
The blind term vanishes at sun = 0 — the IV threshold the agent must discover.

**lab3** - cross-zone spillage plus a shared spotlight, 3 000 episodes:
```js
var corridor = sp ? 150 : 0;
z1 = 25 + (z1l?400:0) + (z2l?100:0) + (z1b?0.50*sun:0) + (z2b?0.30*sun:0) + corridor;
z2 = 25 + (z2l?400:0) + (z1l?100:0) + (z2b?0.50*sun:0) + (z1b?0.30*sun:0) + corridor;
```
Spill is rank-moving but non-trivialising: 0.30·900 = 270 < 300, so no cross-zone lever reaches goal alone while the own lamp (+400) always does — a property the §5.3 analysis leans on.

### 4.2 Phase 2 - the faulty labs

Each faulty flow is a literal string replacement in the parent's physics, so the KG, Thing Description, and scenarios stay identical. Fault families:

| Family | Cells | Physics change |
|---|---|---|
| Lamp dead / inverted | lab1_f1dead; lab2, lab3 f1dead/f1inv; lab3 f1dead_z2/f1inv_z2 | `z1l?400` → `0` (dead) or `−400` (inverted) |
| Multi-lamp dead / inverted | lab2, lab3 f2dead/f2inv | Both lamp terms zeroed/negated; blinds intact |
| Blind dead / inverted | lab2, lab3 f1bdead/f1binv | `z1b?0.50*sun` → `0` / `−0.50*sun`; falsifiable only when OPEN under sun rank ≥ 2 |
| Multi-blind dead | lab3_f2bdead | Both blinds' own- and cross-zone terms zeroed; survivors keep rank 3 reachable |
| Monitor fallback | labmon_f1dead | Lamp dead → ceiling 285 lux (rank 2); monitor is the best-effort actuator |
| Degraded multi-survivor | lab3_f2dead_lowsun, labmon2_f2dead_lowsun | Lamps dead + sun pinned to 100 → rank 3 unreachable |

labmon physics: `z1 = 25 + (z1l?400:0) + (z1mon?260:0)` — the monitor alone reaches only rank 2. labmon2 puts a monitor and a blind in each of two independent zones. lab1_f1dead is deliberately degenerate: with its single actuator dead, the agent can detect and alert but has nothing to recover with.

### 4.3 Phase 3 - the slow labs

`lab2_slow` and `lab3_slow` keep the parent lux formula but route blind commands through a 12-tick delay (≈ 60 s at 5 s/tick); lamps stay instantaneous:
```js
z1 = 25 + (z1l?400:0) + (z1bEff?0.50*sun:0);   // z1bEff lags the commanded state by DELAY=12 ticks
z2 = 25 + (z2l?400:0) + (z2bEff?0.50*sun:0);
```

---

## 5. Phase 1 results - KG acceleration on clean labs

### 5.1 Arms and run of record

The factorial arms isolate the channels: A `phase1_baseline` (all off), B `phase1_pbrs_only`, C `phase1_kg_only` (KG prior alone), D `phase1_full` (prior + PBRS + adaptive trust). The run of record is **29105464710** (seeds 1–10), which resolves to **arm D** — so every §5 number is an arm-D number, labelled as such. The one outstanding Phase-1 item is an arm-C dispatch on the same instrument (`run_mode=phase1_kg_only`, lab1–lab3, seeds 1–10) to isolate the prior; arm D can't separate the prior's contribution from PBRS and trust, and I want that run before finalising the Phase-1 chapter.

### 5.2 Learning speed (run 29105464710, arm D)

Paired contrasts ql_true − ql_false, seed-paired, n = 10, BH-corrected:

| Profile | Metric | Tier | Δ | 95% CI | Cliff's δ | BH q |
|---|---|---|---|---|---|---|
| lab1 | auc_goal | primary | 0 | [0, 0] | 0 | 1 |
| lab1 | mean_first_goal | secondary | −1.80 | [−21.6, +17.4] | −0.11 | 1 |
| **lab2** | **auc_goal** | **primary** | **+0.01924** | **[0.0148, 0.0236]** | **1.0** | **0** |
| lab2 | auc_reward | secondary | +5.18 | [−0.66, +11.69] | 0.46 | 0.269 |
| lab2 | mean_first_goal | secondary | −28.18 | [−58.98, +2.56] | −0.36 | 0.269 |
| lab3 | auc_goal | primary | −0.00245 | [−0.0079, +0.0033] | −0.32 | 0.801 |
| **lab3** | **auc_reward** | secondary | **+12.47** | **[8.27, 16.59]** | **0.98** | **0** |
| lab3 | mean_first_goal | secondary | +25.29 | [−20.82, +66.13] | 0.42 | 0.632 (ns) |

Benchmark contrasts, same run: lab2 wins across the board — goal_rate +0.025 (q=0.023), avg_steps −0.56, avg_wasted −0.57, avg_redundant −0.66, avg_energy −1.29, avg_dev −1.18. lab3 turns against the KG arm on efficiency — avg_cycling +1.21 (δ=0.99, q≈0), avg_redundant +1.58 (δ=0.88, q≈0). lab1 shows one tiny contrast against the KG arm (+0.0225 on avg_wasted/avg_redundant).

### 5.3 What I take from Phase 1

1. **lab2 is the anchor.** The pre-declared primary metric (`auc_goal`) shows a maximal effect (δ = 1.0, q = 0) on the capability-identical instrument: both arms draw the same action space from the WoT contract, so the difference is knowledge and nothing else.
2. **lab1 is a floor control.** An 8-state, one-lamp lab converges near-instantly in both arms. The only non-null contrast is the +0.0225 redundant-action penalty — one wasted action per ~44 episodes, negligible in practice, but enough that I qualify "all lab1 contrasts are null."
3. **lab3 is a characterised weakness, not a win — and I can say why.** The KG arm is null on `auc_goal`, directionally slower to first goal (ns), better on `auc_reward`, and pays an efficiency tax in the final policy (cycling +1.21, redundant +1.58). The cross-zone structure the KG knows is real but never *required*: no cross-zone lever reaches rank 3 alone (0.30·900 = 270 < 300), while the own lamp (+400) always does. So both arms share the fastest route to goal, and the optimistic KG bonus acts as an exploration schedule — the KG arm works through the "looks helpful" cross-zone levers while the tabula-rasa agent stumbles onto "own lamp ON" and stops searching. In a 2 048-state space visited only sparsely over 3 000 episodes, those initial-Q orderings survive into the greedy policy as on/off toggling — which is what the cycling and redundant contrasts count. Meanwhile the prior's suppressive half (no-effect, redundancy) pays from episode one, which is why `auc_reward` wins. The two metrics genuinely measure different things.
4. **Why I won't "fix" lab3 by tuning.** Design-level fixes exist — fading the initial-Q penalties with visits, delivering the prior through PBRS (policy-invariant by theorem, so a final-policy cycling penalty becomes impossible), or restricting the prior to exploration — but each needs a fresh registered run. More to the point, the efficiency tax *is* the finding: a static prior over redundant structure is a cost the agent pays for knowledge it can't yet use, and Phase 2 shows that same knowledge paying off the moment the environment makes it essential (in lab3_f2dead_lowsun the spotlight flips from redundant to essential and the KG arm re-learns 2.1× faster). That is the transition I want to write between the two chapters.

---

## 6. Phase 2 - fault detection, blacklisting, re-learning

### 6.1 Design

The pre-trained agent warm-loads its clean-lab Q-table into a faulty simulator and, every step, rechecks the observed transition against the KG's physics claims. A component is blacklisted on its *first* falsifiable anomaly — DEAD if the claimed response drops to zero, INVERTED if it opposes the asserted sign. There is no evidence counter; false positives are prevented structurally instead: only falsifiable claims are scored, IV-gated blinds are judged only when OPEN under sun rank ≥ 2, contaminated zones are skipped, and a diagnostic probe actively opens untested blinds so blind faults become visible at all.

The probe exists because a blind is only soundly falsifiable when opened under sun rank ≥ 2 with headroom below saturation — below that, a null response is expected-healthy (at sun ≥ 400 a healthy open adds ≥ 200 lux, crossing a rank boundary; hence the ≥ 2 floor). But the warm-started policy never opens blinds: the lamp is deterministic and sufficient, and energy isn't in the reward, so daylight harvesting is off the greedy path. Without the probe a dead or inverted blind yields zero falsifiable observations, and the blind-fault cells would be unmeasurable. So whenever the state permits a sound test (blind closed, sun high enough, below saturation), the agent opens the blind once as a self-test: a healthy blind is verified once and never re-probed, a faulty one is blacklisted immediately. This puts blind detection at ep ≈ 6–7 in both arms. The probe is shared, identical instrumentation, so it can't tilt the comparison — and being KG-directed, it is itself an instance of "actively recheck against the physics knowledge."

On detection, both polarities of the component's actions are removed, the user is alerted, and a warm restart wipes the blacklisted Q-columns, halves Q in poisoned states, boosts ε back to 0.30, and lets the prior regain weight. Recovery is declared once the greedy policy holds stable for 50 consecutive episodes; the headline metric is **RecoveryEpisodes = ReconvergeEpisode − DetectEpisode**.

If the nominal rank becomes unreachable after blacklisting, a deterministic reachability probe enumerates the surviving actuator combinations, lowers the effective goal to the best achievable rank, and notifies the user — proof-gated, not a heuristic.

The phase runs under a frozen pre-registration (one pooled Tier-1 recovery family, m = 8; seed-keyed pairing; one run of record per cell). The registered record for the runs below is `pre_registration.md` §9.10.

### 6.2 Results (seed-paired, pooled BH, m = 8)

Runs of record (all on commit `6c727b6`, `phase2.yml`, self-contained train-clean→adapt pairing; raw data under `phase2_postinv/`):

| Run | CI run ID | Cells | Seeds |
|---|---|---|---|
| 1A | 29148475671 | lab1_f1dead, lab2 f1dead/f1inv/f2dead/f2inv, lab3 f1dead/f1inv/f2dead | 1–10 |
| 1B | 29151540231 | lab3 f2inv/f1dead_z2/f1inv_z2/f1bdead/f1binv, lab2 f1bdead/f1binv | 1–10 |
| 2 | 29155539633 | labmon_f1dead, lab3_f2dead_lowsun, labmon2_f2dead_lowsun | 1–10 |
| 3 | 29157197853 | Phase-2.6 KG-silent variants (descriptive, §6.4) | 1–10 |
| 1C | 29163456132 | lab3_f1dead one-shot replication (this cell's run of record) | 11–20 |

Tier-1 recovery family (RecoveryEpisodes, ql_true − ql_false):

| Cell | n | KG (ep) | Base (ep) | Δ | 95% CI | Cliff's δ | BH q | Verdict |
|---|---|---|---|---|---|---|---|---|
| lab2_f1bdead | 10 | 75.6 | 382.1 | −306.5 | [−439.5, −174.6] | −0.92 | 0 | significant |
| lab3_f2dead_lowsun | 10 | 63.5 | 134.9 | −71.4 | [−102.3, −41.3] | −0.84 | 0 | significant |
| labmon2_f2dead_lowsun | 10 | 187.1 | 334.7 | −147.6 | [−230.9, −61.4] | −0.76 | 0.0021 | significant |
| lab3_f1dead_z2 | 9 | 511.1 | 571.3 | −60.2 | [−120.1, −4.3] | −0.28 | 0.066 | marginal, ns |
| lab3_f1bdead | 10 | 198.1 | 288.1 | −90.0 | [−265.0, +86.5] | −0.33 | 0.365 | ns |
| lab3_f1binv | 10 | 398.5 | 405.0 | −6.5 | [−138.4, +116.0] | −0.02 | 0.929 | ns |
| labmon_f1dead | 10 | 84.5 | 62.3 | +22.2 | [−15.8, +57.2] | +0.05 | 0.328 | ns |
| lab3_f1dead (seeds 11–20) | 9 | 505.0 | 420.0 | +85.0 | [−31.6, +205.1] | +0.43 | 0.276 | ns |

H-P2 is supported in **3 of 8** cells (KG faster in all three; 1.8×–5.1× by the means), marginal in 1, ns in 4 (two with Δ > 0). Six of eight deltas are negative. `lab3_f1dead` is registered unsupported: its run of record is the seeds-11–20 replication, which shows Δ > 0, and no rerun is permitted.

The detection family is null (min q = 0.656). Lamp faults detect at episode 0 in both arms — four cells realise degenerate 0-vs-0 detection and stay in the family at p = 1 — and blind faults at ep ≈ 6–7, all null. Detection is identical instrumentation in both arms, and the family confirms it.

### 6.3 Monitor fallback & degraded-goal cells

- **labmon_f1dead:** lamp dead → ceiling 285 lux (rank 2), goal unreachable. Both arms detect at episode 0, find the monitor fallback, reach a 100% greedy goal-rate on the rank-2 goal, and fire the proof-gated degraded path in 10/10 seeds. Recovery is ns (84.5 vs 62.3, q = 0.328): with one obvious fallback lever, knowledge adds nothing.
- **lab3_f2dead_lowsun:** both lamps dead + pinned low sun → ceiling 265 lux; the once-redundant spotlight becomes essential, and both arms find it. KG 63.5 vs 134.9 (q ≈ 0); goal-rate 1.0 vs 0.96; degraded path 10/10.
- **labmon2_f2dead_lowsun:** an independent, spotlight-free, dual-zone version of the same effect: 187.1 vs 334.7 (q = 0.0021); goal-rate 0.99 vs 0.895; degraded path 10/10.

### 6.4 KG-silent variants (Phase 2.6, run 29157197853, descriptive)

The `infoonly` / `nostereo` profiles hide the monitor's light contribution from the KG in both arms. Even so, the KG arm recovers ~2× faster in the dual-zone cells (172.0 vs 370.2; 162.6 vs 364.0) and faster in the single-zone cells (51.3 vs 71.5, both variants); all detect at episode 0 and reach the degraded goal 10/10. These cells sit outside the registered family (no q-values), but they localise the advantage: it comes from knowledge over the *surviving* actuators, not from modelling the faulted or fallback component.

### 6.5 Multi-blind cell (Phase 2.7, run 29187088096, exploratory)

`lab3_f2bdead` — both lab3 blinds dead — is the first Mediates-class multi-fault cell (two probe→blacklist→warm-restart iterations, each blind falsifiable only on the OPEN probe under sun rank ≥ 2) and the first well-posed full-recovery multi-fault cell (survivors Z1Light, Z2Light, Spotlight keep both zones rank-3 reachable). Exploratory (§9.11), no q-value, one dispatch, closed.

- **Recovery:** 570.0 (KG) vs 447.7, Δ = +122.3, 95% CI [−11.5, +265.3], ns — the KG arm is directionally *slower*.
- **Detection:** both blinds caught in all 20 replicas (first blacklist ep 2–8, second ep 3–87); DetectEpisode 3.8 vs 5.8. The iterative Mediates loop works as designed.

The survivors are exactly the levers the warm-started policy already ranks correctly, so losing the blinds forces no re-ranking the KG could accelerate; both arms fall back to generic re-learning of the 2 048-state policy — the same regime as the adverse-trend lamp cells (`lab3_f1dead` +85.0, `labmon_f1dead` +22.2).

### 6.6 What I take from Phase 2

1. **Detection is structural and symmetric.** Lamp faults at episode 0 in both arms; blind faults at ep ≈ 6–7 via the KG-directed probe (without which a dead blind is invisible off-policy); the family is null. Detection isn't where the KG pays — recovery is.
2. **The recovery advantage is selective, and the boundary is clear.** Knowledge pays where the fault demotes levers the policy relied on and promotes survivors it had learned to ignore: `lab2_f1bdead` (must newly exploit daylight) and the low-sun triage cells. Where the surviving set is already dominant — one obvious lever (`labmon_f1dead`), or survivors the policy already ranks right (`lab3_f2bdead`) — the contrast is null. Multiple survivors alone aren't enough.
3. **The KG-silent variants confirm this:** the advantage survives removing the faulted/fallback component from the KG, so it rides on knowledge over the survivors.
4. **Caveats, as-is:** two family cells trend adverse (ns, Δ > 0), and the descriptive cell `lab2_f1binv` pairs only n = 4 seeds, so I lean on nothing from it.

---

## 7. Phase 3 - response-delay learning

### 7.1 Design

No Q-table training. The dynamics agent runs controlled probes — pin a baseline state, toggle one actuator, count ticks to the target rank — feeding each measurement into a per-actuator Welford estimate:

$$
\mu_n = \mu_{n-1} + \frac{x_n - \mu_{n-1}}{n}, \qquad \sigma^2_n = \frac{M_{2,n}}{n-1}
$$

with 8 probes per actuator, 5 s/tick, minSamples = 3, and a 30 s threshold splitting instantaneous from delayed. Learned delays are written back as `ws:responseDelay`. At exploitation, the KG arm plans with the measured delay and the baseline assumes zero, over six time-bounded goals (tight 15/45 s, loose 90/300 s).

### 7.2 Results (run 29166356524, n = 10 replicas)

Learned delay vs ground truth (12 ticks = 60 s); lamps and spotlight are correctly classified instantaneous in every cell:

| Profile | Arm | Slowest actuator | Learned ticks | Rel. error |
|---|---|---|---|---|
| lab2_slow | ql_false | SetZ1Blinds=ON | 12.175 | 1.46% |
| lab2_slow | ql_true | SetZ2Blinds=ON | 12.150 | 1.25% |
| lab3_slow | ql_false | SetZ1Blinds=ON | 12.1125 | 0.94% |
| lab3_slow | ql_true | SetZ1Blinds=ON | 12.1625 | 1.35% |

Compliance (counts, not inference — see below): the KG arm meets all six deadlines in both profiles; the zero-delay baseline meets only the three loose ones. The KG arm buys the tight deadlines with energy (3.1–3.5 units vs 0), switching to the instantaneous lamp when it knows the blind can't respond in time.

### 7.3 What I take from Phase 3

1. The cleanest phase: the blind's ~60 s delay is something the stereotype can't express quantitatively, the agent measures it to ≤ 1.46% error, and writes it back to the KG where the planner uses it.
2. One honest caveat: the compliance contrast is deterministic given the learned delays — ten replicas of a planner that knows the delays carry the information of one, so p-values would be vacuous. I report it as a worked demonstration (6/6 vs 3/6), not inference. The delay-accuracy numbers do sample real jitter and are statistically sound.

---

## 8. Phase 4 - energy & dependency ladder (extension)

Phase 4 sits outside the three phases and compares the same two arms on labs with actuation dependencies and energy costs: lab4 (lamp AND-gated by a smart plug, `ws:powerGates`), lab4dual (parallel plugs), lab4chain (breaker → plug → lamp), and lab5 (efficient vs inefficient lamps, `ws:energyCost`, energy scored at benchmark time only). The confirmatory run of record is **29193486193** (n = 20): the primary `avg_redundant` advantage grows monotonically with dependency depth — Δ = −0.33 (lab4) / −0.93 (lab4dual) / −1.46 (lab4chain), all q ≈ 0 — and lab5 energy compliance is +0.096 (q ≈ 0) at goal-rate parity, with steady-state power −0.431. Goal rates are at parity on lab4/lab5, with a KG-favourable lift on lab4dual/lab4chain (disclosed). Details in `docs/PHASE4.md` and `docs/PHASE4_DEPENDENCY_LADDER.md`.
