# Thesis Meeting Brief — 8 June 2026

**Project:** MT-Esra — Stereotype-guided Q-learning for multi-zone smart-building illuminance control
**Framework:** JaCaMo (Jason BDI agents + CArtAgO artifacts) + Node-RED physics simulator
**Authoritative data this brief is built on:** GitHub Actions sweep `27094219403` (n=10 seeds, commit `9b2bc9b`), report in [docs/sweep_n10_results_analysis.md](sweep_n10_results_analysis.md).

---

## 0. TL;DR for the meeting 

1. **The hypothesis is partially confirmed and the picture is now statistically solid (n=10).**
   - On **two of three labs** (`custom3`, `custom5`) stereotype priors make the learner **reach a higher goal-rate AND learn faster**, at the strongest significance the test can give (q ≈ 0.000).
   - On the **headline "constructive" lab `custom9`** the prior **does not help goal-rate and significantly *slows* learning** (AUC Δ = −0.062, q ≈ 0). This is the result we have to explain.
   - **Energy is the universal win:** the prior cuts average energy on **every lab, every seed** (Cliff's δ = −1.0, q ≈ 0). This is the strongest and cleanest result in the thesis — and it is exactly the "energy as a side effect" point.

2. **Why `custom9` did not work is now understood and it is a *fixable, conceptual* problem, not a flaw in the idea** (details in §4):
   - **Training/benchmark distribution — NOTE (corrected 2026-06-08):** an earlier draft blamed a
     training sun-coverage gap; that was **disproven** (training covers all sun ranks). Re-analysing
     the existing n=10 data by sun rank pins the real cause: the prior is **strongly favourable at
     bright sun (Δ=+0.280)** but **mis-fires at medium sun (Δ=−0.157)** because the blind/sun IV gate
     (`ivMinRank=1`) is too permissive — it recommends blinds at rank 2 where they can't reach the
     target. The two nearly cancel → overall Δ=−0.002. Fixable with a one-line `ivMinRank=3` change.
     See §4.1 and [docs/custom9_rediagnosis.md](custom9_rediagnosis.md).
   - **The base RL learner does not converge** even at 10 000 episodes (goal-rate plateaus at 0.11–0.21). The 20-step horizon + the 4-zone state space make the task too hard to solve cleanly, so there is no "simple lab where stereotypes obviously work" yet.

3. **What I am proposing / have started (details in §6–§7):**
   - A **simple-lab track**: smaller, faster-converging versions of each lab so we can *first* demonstrate the mechanism cleanly (the thesis's "show it works in a simple lab" step) before stress-testing.
   - A **corrected-training-distribution `custom9`** so the blind/sun stereotype is in-distribution during training (the single highest-value fix).
   - A **horizon ablation** (`paper_h40` / `paper_h60`) to separate "task unsolvable in 20 steps" from "prior misleads" on `custom9`.

4. **Two demos are ready to show** (§5): a step-by-step *agent decision explainer* (terminal, exact ground-truth data) and the *Agent Trace Cockpit* dashboard (visual replay of a real benchmark run).

---

## 1. The storyline 

> **Claim under test:** stereotype knowledge (Brick + Elementary ontology, compiled into soft Q-table priors) gives a Q-learning agent *more useful prior information* than a zero-initialised learner, so it **learns faster and ends up more efficient**.

The thesis arc:

1. **Show stereotypes work in a simple lab.** → *Not yet cleanly demonstrated* — the base learner doesn't converge on the current 4-zone labs. **This is the gap we are closing now** (§6 simple-lab track).
2. **Stress-test the stereotypes, reveal weaknesses.** → *Done.* Six weakness labs (W1–W6) inject one systematic ontology gap each.
3. **Define weakness labs to isolate effects.** → *Done* (custom2–custom7), then **reduced to the three mechanically-valid ones** (`custom3`, `custom5`, `custom9`) after the audit found the others were null-by-design (W6 temperature has no goal channel, W5 is non-Markov, etc.).
4. **Show Q-learning + stereotypes overcomes weaknesses & learns faster than uninformed Q-learning.** → *Confirmed on `custom3`/`custom5`; open on `custom9`.*

**Where we are on the arc:** we jumped to step 4 (the stress tests) and got a genuinely strong result there, but we **skipped step 1** (the clean demonstration). The headline lab meant to be the clean demonstration (`custom9`) is itself too hard for the base learner and has a training-distribution bug. The plan below puts step 1 back in.

---

## 2. What the metrics show (n = 10, authoritative)

All numbers are paired `ql_true − ql_false` across 10 seeds, Benjamini–Hochberg corrected. `ql_true` = Q-learning **with** stereotype priors; `ql_false` = Q-learning **without** (the "naive" learner); `rule_based` = hand-written ontology-driven controller (the "naive expert" baseline).

### 2.1 Final goal-rate (H1 — does the prior help the end policy?)

| Lab | What it tests | `ql_false` | `ql_true` | Δ (true−false) | BH q | Verdict |
|---|---|---|---|---|---|---|
| **custom3** | Wrong-prior weakness (blind sign-flips at high sun) | 0.048 | 0.211 | **+0.163** | 0.000 | ✅ prior helps |
| **custom5** | Benign constraint (7-unit power cap) | 0.026 | 0.090 | **+0.064** | 0.000 | ✅ prior helps |
| **custom9** | Clean lab, sun-dependent optimum (headline) | 0.107 | 0.105 | −0.002 | 0.872 | ⚪ null |

### 2.2 Learning speed — AUC of the goal-rate curve (PRIMARY metric)

Higher AUC = faster learning. This is the pre-registered primary outcome.

| Lab | `auc_goal` false | `auc_goal` true | Δ | 95% CI | BH q | Verdict |
|---|---|---|---|---|---|---|
| **custom3** | 0.0895 | 0.1620 | **+0.073** | [0.024, 0.126] | 0.0016 | ✅ faster |
| **custom5** | 0.0467 | 0.0873 | **+0.041** | [0.019, 0.059] | 0.0016 | ✅ faster |
| **custom9** | 0.1697 | 0.1080 | **−0.062** | [−0.082, −0.036] | 0.000 | ❌ **slower** |

> The **headline negative**: on `custom9` the **uninformed** learner learns *faster* (AUC 0.170 vs 0.108). The prior actively suppresses the learning curve. At n=5 this was a weak trend (δ=−0.6); at n=10 it is significant with a large effect (δ=−0.84). We cannot wave this away — but §4 explains *why*, and it is fixable.

### 2.3 Energy efficiency (the "side effect")

| Lab | Δ avg_energy (true−false) | Cliff's δ | BH q |
|---|---|---|---|
| custom3 | **−81.8** | −1.0 | 0.000 |
| custom5 | **−71.4** | −1.0 | 0.000 |
| custom9 | **−47.1** | −1.0 | 0.000 |

**This is the most robust finding in the whole project.** The prior reduces average energy on every lab and every seed at the maximum significance n=10 allows. Even on `custom9`, where the prior hurts *speed*, it still saves energy: the agent reaches comparable goal-rates through lower-energy trajectories (fewer redundant actuator activations).

> **Honest framing (locked in pre-registration):** energy is an **emergent side effect of the priors**, *not* a learned trade-off — the reward function contains **no energy term**. The priors discourage redundant activations, which happens to save energy. We deliberately did **not** add energy to the reward this cycle (it would change the optimum and invalidate the pre-registered comparison).

### 2.4 RL vs the hand-written expert (testing the naive versions)

| Lab | Δ goal-rate (ql_true − rule_based) | Verdict |
|---|---|---|
| custom3 | +0.032 (ns) | draw |
| custom5 | −0.160 (δ=−1.0) | rule_based dominates |
| custom9 | −0.145 (δ=−1.0) | rule_based dominates |

The hand-written controller still beats the learner on the two harder labs. **Honest framing:** stereotype priors deliver *sample-efficiency* and *energy* benefits **to the learner**; they do **not** make tabular RL beat hand-written expert control on these tasks. That is a defensible and interesting contribution on its own (priors as a warm-start, not as a replacement for expert knowledge).

---

## 3. The stereotype models — and the blinds / outdoor-light model specifically

The ontology ([src/resources/lab-ontology.ttl](../src/resources/lab-ontology.ttl)) encodes each actuator as an **Elementary `PhysicalMechanism`** following Ramanathan & Mayer (BuildSys 2023). Two mechanism *patterns* matter:

| Pattern | Meaning | Example | How the sign is decided |
|---|---|---|---|
| **Causes** (`elem:increases`) | Manipulated variable directly, unconditionally changes the dependent variable. | A **lamp**: electrical power → luminance, always positive. | Sign is **fixed positive**, declared in the ontology. |
| **Mediates** (no `elem:increases`) | The manipulated variable *gates* an independent variable's effect on the dependent variable. The sign is **state-dependent**. | A **blind**: outdoor illuminance (IV) → indoor luminance (DV), *gated by* blind aperture (MV). | Sign is **derived at run time** from the current IV rank vs `ws:ivMinRank`. |

### 3.1 The blinds model

```
pm_daylight_ingress  (Mediates mechanism)
    IV  = ws:outdoorIlluminance   (the sun — independent variable)
    MV  = ws:blindApertureRatio   (the blind — what the agent actuates)
    DV  = elem:luminiscence       (indoor light — what we want at target)
    ws:ivMinRank = 1              (minimum sun rank for the blind to do anything)
    NO elem:increases             (deliberately omitted — sign is conditional)
```

**Plain-language semantics:** "Opening the blind raises indoor light **only when there is outdoor light to let in**. In the dark (sun rank 0) opening the blind does nothing; on a bright day (sun rank ≥ ivMinRank) it helps."

This is the crucial modelling choice: a naive ontology would say "blind increases light" unconditionally (a `Causes` shortcut). That would be **wrong at night**. By modelling the blind as a **Mediates** mechanism, the stereotype says "blind helps *conditional on the sun*," and the consumer (`StereotypeReasoner`) decides the per-state sign from the observed sunshine rank.

### 3.2 How the blind stereotype enters the Q-learner

Three channels, all in [src/env/tools/StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java) + [src/env/tools/QLearner.java](../src/env/tools/QLearner.java):

1. **Constructive optimistic Q-init** (`getInitPenaltyForZone`, "Rule 5"): if a stereotype-favoured action would move a below-target zone toward its goal *and its IV is satisfied*, the Q-value is seeded **positive** (`+INIT_BONUS·gap`). For the blind, this only fires when the sun rank is high enough — so at night the blind gets **no** optimistic boost.
2. **Soft runtime prior** at action-selection time: penalises activating an action whose IV is starved (blind ON at sun rank 0 → discouraged).
3. **Runtime IV-effectiveness learning** (`isIVSatisfied` / `recordActionOutcome` / `getLearnedIVMinRank`): the agent *measures* whether opening the blind actually raised the light at each sun rank, and learns the true `ivMinRank` from experience. The ontology triple is treated as a **falsifiable hypothesis**, not a hard rule — the agent can override it if the data disagrees. This is what gives "graceful degradation" when the ontology is wrong (the whole point of `custom3`).
4. **Adaptive trust** (EMA in [0.1, 1.0]): scales the prior down where its predictions have been unreliable. It can *soften* a wrong prior but **cannot sign-reverse** it — a known limitation worth mentioning.

### 3.3 The other stereotypes 

- **Task lights (Z1–Z4):** Causes mechanism, `elem:increases` luminance, energy cost 1/tick. Always-available, sun-independent.
- **Corridor light:** Causes, broadcasts +150 lux to all four zones (a cheap shared resource).
- **Spotlight / SpotlightCD:** Causes, +250 lux to a zone pair — **disabled in `custom9`** on purpose, to *force* the blind/sun stereotype onto the optimal path.
- **Radiators / temperature:** present in the ontology but **not in the reward** — relevant only to the (now-demoted) `custom7` heat weakness.

---

## 4. Why `custom9` did not work — conceptual diagnosis

This is the heart of the "why didn't it work / is it fixable" discussion. The decisive cause is a
**mis-calibrated IV gate** (§4.1), confirmed from the existing data; non-convergence (§4.2) compounds it.

### 4.1 (DECISIVE, evidence-based) The prior mis-fires at medium sun — a too-permissive IV gate

Re-analysing the **existing n=10 benchmark data** by sun rank (no new compute;
[analysis/custom9_rediagnose.py](../analysis/custom9_rediagnose.py) →
[docs/custom9_rediagnosis.md](custom9_rediagnosis.md)) gives a sharp, honest picture. Per-rank
goal-rate Δ (informed − naive), pooled over 10 seeds × 5 runs:

| Sun rank | ql_true | ql_false | Δ | Reading |
|---|---:|---:|---:|---|
| 3 (bright) | 0.363 | 0.083 | **+0.280** | **Hypothesis CONFIRMED where the mechanism is active.** At sun ≥ 500 the blind (`0.5·sun ≥ 250` + corridor 150) reaches a bright target cheaply; the informed agent exploits it, the naive one doesn't. |
| 2 (medium) | 0.014 | 0.171 | **−0.157** | **The prior MIS-FIRES.** At sun ∈ [150,500) the blind yields only ~88–125 lux — short of a bright(3) target even with the corridor (≈275 < 400). A task light is required, but the prior still pushes blinds → wasted exploration. |
| 1 (low) | 0.060 | 0.080 | −0.020 | mild waste |
| 0 (night) | 0.033 | 0.091 | −0.058 | mild waste (lever absent) |

**Root cause (verified in code):** the Mediates(blind, sunshine) mechanism has `ivMinRank = 1`
([StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java) line 57; `ws:ivMinRank` in the
ontology). So the prior calls the blind "helpful" at sun rank ≥ 1, but in `custom9` the blind only
*reaches a bright target* at rank 3. **The gate is too permissive by two ranks**, mis-firing across
ranks 1–2. The strong rank-3 win (+0.280, 21% of scenarios) is nearly cancelled by the rank-2 loss
(−0.157, 25%), so the overall Δ collapses to −0.002. (Re-weighting sun ranks uniformly only moves Δ
to +0.011, confirming the rank-2 mis-fire — *not* the night mix — is the dominant drag.)

**This is fixable in-distribution (no training-distribution change):**
1. **Tighten the gate** — set `ws:ivMinRank = 3` for the blind/sun mechanism in the custom9
   ontology. Predicted to remove the rank-2 drag while keeping the rank-3 win → Δ turns clearly
   favourable. One-line ontology change, one sweep to confirm.
2. **Adaptive trust** — the runtime IV-effectiveness tracker (`getLearnedIVMinRank`) is *meant* to
   learn that the blind fails below rank 3 and attenuate the prior. If it doesn't within budget,
   that is itself a reportable finding about the tracker's learning rate.

> The earlier draft blamed a **training** sun-coverage gap. That was **disproven** (training covers
> all sun ranks: rank0=32/rank1=33/rank2=49/rank3=36). The *physical* intuition ("blind underperforms
> at rank 2") was right; the locus is the **evaluation** rank-2 scenarios plus the too-permissive IV
> gate — both verified above from data and code.

### 4.2 The base learner does not converge (structural)

Even the uninformed learner plateaus at goal-rate 0.11–0.21 after 10 000 episodes. Likely causes:
- **20-step horizon** vs a task that needs up to ~8–11 correct toggles across 4 zones with cross-zone bleed.
- **Large state space** (4 zone-levels × 4 lights × 4 blinds × sunshine) with sparse terminal reward → too few visits per state.
- The **expert `rule_based` controller dominates**, confirming the task *is* solvable — the *learner* is the bottleneck, not the environment.

→ The **horizon ablation** (`paper_h40` = 40 steps, `paper_h60` = 60 steps) is registered to separate "unsolvable in 20 steps" from "prior misleads." This is the experiment currently being launched.

### 4.3 The headline lab was the *wrong* place to demonstrate the mechanism first

`custom9` is simultaneously (a) the cleanest lab conceptually and (b) one of the hardest to *solve*. We tried to prove "the prior helps" on a lab where **nobody** (informed or not) learns well. The fix is the **simple-lab track** (§6): demonstrate the mechanism where convergence is achievable, *then* show it survives the stress tests.

---




## 5. The simple-lab track (closing the "show it works in a simple lab" gap)

**Goal:** for each of the three live labs, a *simpler* sibling that tests the **same mechanism** but is
small enough to **converge inside ~1000 episodes**, so we can demonstrate the stereotype benefit
cleanly before stress-testing.

**Why this should converge much faster (the levers):**

| Lever | Current (4-zone) | Simple sibling | Effect on convergence |
|---|---|---|---|
| Zones | 4 | **2** | State space shrinks by orders of magnitude (each zone multiplies the index). |
| Horizon vs task depth | 20 steps, ~8–11 toggles | 20 steps, ~3–4 toggles | Terminal reward is reachable by random exploration far more often. |
| Sunshine coverage | ~~training pinned to rank 2~~ **already full-range (no gap — see §4.1)** | full-range in training | No change: this lever was based on a disproven premise. |
| Distinct optimal actions | many (spotlights, corridor, 8 lights/blinds) | the **one** mechanism under test | The prior's signal isn't diluted. |

| Simple lab | Mirrors | Mechanism isolated | Stereotype lever |
|---|---|---|---|
| `custom9s` | custom9 | clean, sun-dependent optimum | blind↔sun Mediates (constructive) |
| `custom3s` | custom3 | wrong-prior (blind sign-flip at high sun) | adaptive-trust recovery |
| `custom5s` | custom5 | benign constraint (power cap) | compatible prior under a limit |

**Status:** the simple-lab track is fully **designed with exact reachability arithmetic and the
corrected sun-sampling code** in [docs/simple_labs_design.md](simple_labs_design.md). The registered
4-zone `custom9` is deliberately **left unchanged** so the pre-registered n=10 record (including the
honest headline negative) stays intact; the fix lives in the new `custom9s` sibling. Building the
2-zone Node-RED simulators + running a validating sweep is the proposed next compute step (cannot be
validated in today's meeting — sweeps run for hours on CI).

---

## 7. What was implemented for this meeting

Full how-to in [docs/DEMO_GUIDE.md](DEMO_GUIDE.md); simple-lab arithmetic in
[docs/simple_labs_design.md](simple_labs_design.md). Headline items:

- **Decision-explainer demo** ([analysis/demo_decision_explainer.py](../analysis/demo_decision_explainer.py))
  + pre-rendered transcript ([docs/demo_walkthrough_custom9.md](demo_walkthrough_custom9.md)).
- **Dashboard custom9 demo trace** wired in (real `ql_true` benchmark run, data-derived schema) —
  new `load demo (custom9)` button in [dashboard/src/App.jsx](../dashboard/src/App.jsx).
- **Simple-lab design doc** with exact reachability arithmetic for the 2-zone reductions. (Its
  §3.2 "full-range sun fix" has been **retracted** — verification showed `custom9` training already
  covers all sun ranks; the 2-zone labs remain justified by the **convergence** argument alone.)

---

## 8. Achievement log 

Grouped from the git history (`2026-05-22 … 2026-06-08`).

### Experiment infrastructure & CI (made the science reproducible)
- Migrated the whole sweep to **GitHub Actions** as the locked experiment venue (parallel train + benchmark DAG), fixed Java 11→21, Gradle wrapper, JitPack timeouts, runner disk exhaustion, artifact publishing, watchdog kill on JVM teardown hang.
- Added `run_mode` workflow input + **horizon-ablation profiles** (`paper_h40`, `paper_h60`).

### Core learner & reasoner fixes (the audit fix-slate)
- **VDN joint Bellman target** (coordinated multi-actuator goals now learnable).
- **Reward rescale** (`reward_clip` 50→200) so 2–3 rank jumps aren't flattened.
- **Constructive optimistic Q-init** ("Rule 5") — priors became a *guide*, not just a penalty.
- **Bench-time prior decay + persisted trust/visit sidecars** so the prior isn't applied at full strength during evaluation.
- **Runtime IV-effectiveness learning** (blind/sun gating learned end-to-end).
- Episode budget 2500 → **10 000**.

### Labs & scenarios
- Built/repaired the weakness labs (W1–W6), scaffolded the **clean constructive lab `custom9`**, ran a static **reachability proof**, stripped dead scenario fields, fixed W1 gate and W5 phase-leakage.
- **Reduced the confirmatory family** to the mechanically-valid labs after auditing out the null-by-design ones.

### Analysis & statistics (research-grade)
- **Learning speed (AUC) made the primary metric**, paired bootstrap + Wilcoxon + Cliff's δ + BH correction, confirmatory/exploratory family split, first-goal aggregation fixed.
- Surfaced and documented the **`episodes_to_threshold` censoring** honestly instead of retuning the threshold (no HARKing).

### Results produced
- **Sweep-17** (honest negative), **Sweep-18** (clean 10k), **n=10 confirmatory** (`27094219403`) — the authoritative dataset behind this brief.
- Full written analyses in `docs/sweep17_followup_analysis.md`, `docs/sweep18_results_analysis.md`, `docs/sweep_n10_results_analysis.md`, and `docs/pre_registration.md`.

### Tooling
- **Agent Trace Cockpit dashboard** (React/Vite) for visual benchmark replay.

---

## 9. What we are working on right now

1. **Horizon ablation on `custom9`** (`paper_h40` / `paper_h60`) — to decide whether the custom9 problem is "20-step horizon too short" or "prior misleads." *(Launch was attempted from the terminal; verify it actually queued — see §12.)*
2. **Re-diagnosing the custom9 negative** — the prior "training sun-coverage gap" hypothesis was disproven (§4.1); the open candidates are non-convergence and the night-dominated benchmark mix.
3. **Standing up the simple-lab track** (justified by convergence, not the retracted sun fix) so we finally have the "clean simple-lab" demonstration the thesis arc needs.

---

## 10. What is left to do (prioritised)

| # | Task | Why | Cost |
|---|---|---|---|
| 1 | **Tighten the blind/sun IV gate** (`ws:ivMinRank = 3`) in the custom9 ontology and re-sweep | §4.1 shows the prior mis-fires at rank 2; predicted to flip custom9 Δ favourable | 1-line edit + 1 CI sweep |
| 2 | Build + validate the **2-zone simple labs** (convergence rationale) | The clean "stereotypes work in a simple lab" result; should converge in ~1000 eps | sim build + 1 sweep |
| 3 | Resolve the **horizon ablation** | Removes the convergence confound on custom9 | running now |
| 4 | If custom9 still fails after 1–2: **pivot framing** to "priors = sample-efficiency + energy on stress labs; do-no-harm at asymptote" (pre-registered fallback) | Keeps the thesis defensible regardless | writing only |
| 5 | Write up: methods, the three results chapters (simple → stress → energy), limitations | Thesis | writing |

---

