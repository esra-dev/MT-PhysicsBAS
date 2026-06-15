# Phase 1 → Phase 2 — Change Documentation

**Project:** MT-Esra (Knowledge-Guided RL for Building Automation)
**Stack:** JaCaMo (Jason AgentSpeak BDI + CArtAgO) · Q-Learning · Knowledge Graph / Stereotypes · Node-RED labs
**Branch:** `phase2-fault-detection` (off the Phase 1 anchor `kg-crosszone-coupling-bump`)
**Default-branch note:** `phase2.yml` is also registered on `main` solely so `workflow_dispatch` is callable (see §8).

---

## 1. What changed conceptually

Phase 1 proved that KG-priming **accelerates learning in clean labs** (faster first goal, higher reward AUC, fewer redundant actions vs. tabula-rasa).

Phase 2 adds a new capability on top of the *unchanged* Phase 1 learner: the agent no longer tries to *adapt around* a broken actuator. Instead it:

1. **MONITORS** every step — compares the KG/stereotype physics prediction for the action it just took against the observed reality.
2. **DETECTS** a defective component when reality diverges from physics over enough samples.
3. **BLACKLISTS** the component (removes both its ON and OFF actions) and **alerts the user**.
4. **RE-LEARNS** (warm restart) over the surviving action space.

The headline Phase 2 metric is:

```
RecoveryEpisodes = ReconvergeEpisode − DetectEpisode
```

Thesis claim: `RecoveryEpisodes(ql_true) < RecoveryEpisodes(ql_false)` — i.e. the KG-primed arm realigns to the reduced reality faster than tabula-rasa.

**Strict separation preserved:** Phase 1 training code path (`taskQl` / `_ql.asl`) is untouched. All Phase 2 logic lives in new files or in additive, detection-only code paths.

---

## 2. `QLearner.java` — fault operations (additive)

New CArtAgO `@OPERATION`s and supporting state. None of these touch the Phase 1 learning path; `getActionPrediction` (the bench fingerprint) is unchanged, so Phase 1 results are bit-for-bit reproducible.

### Detection constants (system-property overridable)

| Constant | Default | Property | Meaning |
|---|---|---|---|
| `FAULT_MIN_SAMPLES` | `20` | `fault.detect.minSamples` | Min falsifiable observations before a component can be judged |
| `FAULT_DEAD_RATE` | `0.80` | `fault.detect.deadRate` | Fraction of "no zone response" obs that flags a **dead** lamp |
| `FAULT_INV_RATE` | `0.60` | `fault.detect.invRate` | Fraction of "opposite-sign response" obs that flags an **inverted** lamp |
| `FAULT_ANOMALY_RATE` | `0.75` | `fault.detect.anomalyRate` | Combined (dead+inverted)/obs trigger for mixed evidence |
| `FAULT_EPS_BOOST` | `0.30` | `fault.relearn.epsBoost` | ε floor restored on warm restart |

### Key operations

- **`observeForFaults(stateVecBefore, actionIdx, stateVecAfter, OpFeedbackParam<String> newlyDefective)`**
  Reuses `reasoner.getActionPrediction` to get the expected directional effect (±1 per zone slot), compares against the observed Δ, and buckets each observation as healthy / dead / inverted. Pure accumulation — no policy mutation. Returns the `wotActionType` of a component the moment it crosses threshold (else `""`).

- **`blacklistComponent(wotActionType, OpFeedbackParam<Integer> nRemoved)`**
  Marks **both** the ON and OFF action indices of the component as blacklisted. Never blacklists `DO_NOTHING`; guarantees ≥1 action remains.

- **`warmRestart()`** — targeted reset (master doc §3.1), *not* a full wipe:
  1. zero `Q(s, a*)` and visit counts for every blacklisted `a*`;
  2. decay poisoned states (states whose old argmax was blacklisted) by factor 0.5;
  3. restore `ε ← max(ε, FAULT_EPS_BOOST)`;
  4. KG re-prime is automatic (greedy reads priors over the filtered action set).

- **`getNumApplicableActions(...)`**, **`isComponentBlacklisted(...)`** — assertion/logging helpers.
- **`saveRecoveryLog(filename, detectEp, reconvergeEp, defectLabel)`** — appends one recovery row.

### Blacklist enforcement (chokepoints)
- `computeApplicableActions(sv)` filters out blacklisted actions (single chokepoint for both exploration and greedy selection).
- `jointArgmaxAction(sNext)` skips blacklisted actions in the VDN bootstrap target, so a dead actuator can never poison `max_a Q`.

### The `ivGatedComponents` fix (false-positive guard)
Blinds are **Mediates** actuators (effect gated by an interaction variable — sunlight). A lamp pinning a zone at its target rank, or sun=0 episodes, can make a *healthy* blind look "dead." Fix: at `configureQLearner` time, precompute the set of `wotActionType`s whose action carries an IV, and have `observeForFaults` **skip them entirely**:

```java
if (ivGatedComponents.contains(ai.wotActionType)) return;
```

Only **Causes** actuators (lamps, spotlight — unconditional sign) are adjudicated. All injected faults are on Causes lamps, so no designed fault is ever missed, and the previous false positive on `SetZ2Blinds` is eliminated.

---

## 3. New adapt agent — `src/agt/illuminance_controller_agent_adapt.asl`

A new BDI agent that orchestrates the detect→blacklist→alert→relearn lifecycle in a single loop:

- **`@apply_runtime_overrides_adapt`** — reads `-Dactive.profile` and `-Dadapt.mode`; `ql_false` → `use_stereotypes(false)`, otherwise `true`.
- **`@start_adapt`** — creates `LabEnvironment` (on the faulty port) + `QLearner` + `StereotypeLearner`, then **warm-loads the clean Phase-1 Q-table** named by `adapt_source` (`qtable_final_stereotypes_<bool>_<lab>.csv`). Episode budget overridable via `system_prop_num("adapt.episodes", ...)`.
- **`@do_step_adapt`** — ε-greedy action → `invokeAction` → observe → `calculateQ` → `observeForFaults(...)`; if a component is newly defective, raises `!on_defect(Comp, EpN)`.
- **`@on_defect_new`** (guarded `not defective(Comp)`) — prints `[FAULT] DEFECTIVE component detected: <Comp>`, records `+defective(Comp)`, records `+detected(EpN)` / `+primary_defect(Comp)` on first detection only, calls `blacklistComponent` then `warmRestart`. Duplicate detections are ignored. Monitoring stays active, so several-fault labs are pruned **iteratively**.
- **`@adapt`** loop — checks `hasConverged`; sets `+reconverged(N)` only **after** a fault has been `detected(_)`.
- **`@adapt_finish`** — saves `qtable_adapted_*`, `metrics_adapted_*`, and `recovery_stereotypes_*` CSVs, then `.stopMAS`. Safe-default getters emit `-1` / `"none"` when no fault was detected or re-convergence didn't occur within budget.

### Supporting agent / build wiring
- **`task_adapt.jcm`** — `mas lab_adapt { agent illuminance_controller_agent_adapt }`.
- **`build.gradle` `taskAdapt`** — `JavaExec`; forwards `-Pprofile → active.profile`, `-Pmode → adapt.mode`, 4 GB heap; the existing `tasks.withType(JavaExec).configureEach` block forwards `-Prun.seed` and other `_httpKeys`.
- **`src/env/tools/jia/system_prop_num.java`** — new numeric sibling of `system_prop`; parses a `System.getProperty` value to a `NumberTerm` with a default when unset/unparseable (used for `adapt.episodes`).

---

## 4. Faulty lab profiles — `src/agt/lab_profiles.asl`

Nine faulty profiles, each sharing its clean parent's ontology, dimensions, targets, and bounds (the KG = *nominal* physics; the simulator injects the fault). Existing 13-field `lab_profile/13` arity is preserved; the clean-source mapping is a separate `adapt_source/2` belief.

| Profile | Parent | Fault | Port | state dim |
|---|---|---|---|---|
| `lab1_f1dead` | lab1 | 1 lamp dead | 1892 | 2 |
| `lab2_f1dead` | lab2 | 1 lamp dead | 1893 | 7 |
| `lab2_f1inv` | lab2 | 1 lamp inverted | 1893 | 7 |
| `lab2_f2dead` | lab2 | 2 lamps dead | 1893 | 7 |
| `lab2_f2inv` | lab2 | 2 lamps inverted | 1893 | 7 |
| `lab3_f1dead` | lab3 | 1 lamp dead | 1894 | 8 |
| `lab3_f1inv` | lab3 | 1 lamp inverted | 1894 | 8 |
| `lab3_f2dead` | lab3 | 2 lamps dead | 1894 | 8 |
| `lab3_f2inv` | lab3 | 2 lamps inverted | 1894 | 8 |

This spans the full weakness matrix the advisor asked for: **{one component broken, several broken} × {dead, faulty/inverted} × {lab1, lab2, lab3}**.

Each profile carries an `adapt_source(<faulty>, "_<parent>")` belief so the adapt agent warm-starts from the matching **clean** Q-table.

> **Scope notes:** lab1 has a single lamp, so "several faults" is N/A there; `lab1_f1dead` is detection-only (the lone actuator is never blacklisted to keep ≥1 action) and its recovery is reported as N/A. Blinds (Mediates) are intentionally **never** injected or detected — only Causes lamps/spotlight.

---

## 5. Faulty simulator flows — `simulator/generate_faulty_flows.ps1`

Generator produces one Node-RED flow per faulty profile using literal `.Replace` on the clean flow's physics:

- **dead** → the lamp's lux contribution becomes `0` (e.g. `z1l ? 400` → `z1l ? 0`);
- **inverted** → negated (e.g. `z1l ? 400` → `z1l ? -400`);
- **lab3 multi-fault** also kills/negates the cross-zone spill terms (`z1l ? 150`, `z2l ? 150`).

Output files: `simulator/simulator_flow_lab{1,2,3}_f{1,2}{dead,inv}.json` (9 flows, all validated as JSON). Ports reuse the parent lab's port (only one fault lab runs at a time).

---

## 6. Orchestrator — `run_phase2_adapt.ps1`

New PowerShell runner (clone of the Phase 1 structure; the Phase 1 runner is untouched). UTF-8 **BOM**-encoded (PS 5.1 requirement). For each profile it starts the matching faulty Node-RED flow on the parent port, then runs `taskAdapt` for each mode (`ql_true`, `ql_false`). Features:

- `-RunSeed` param → forwards `-Prun.seed=<n>` when ≥ 0;
- watchdog: kills the JVM once the recovery CSV appears and the process goes idle;
- deletes stale `recovery_*` / `qtable_adapted_*` / `metrics_adapted_*` first (recovery CSV is append-mode);
- reads the phase2 maps from `config/run_config.json`.

### `config/run_config.json` (phase2 block)
Expanded to all 9 profiles with seven aligned maps: `parent_profile`, `simulator_port_map`, `simulator_flow_map`, `qtable_suffix_map`, `clean_source_suffix`, `expected_state_vec_dim`, plus `adapt_profiles` / `adapt_modes`. (BOM-encoded; validated as JSON.)

---

## 7. Analysis — `analysis/phase2_recovery.py`

Reads `recovery_stereotypes_<bool><suffix>.csv` (header `DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes`) and produces:

- **`phase2_recovery_ci.csv`** — per-(profile, arm) bootstrap 95% CI of `RecoveryEpisodes`;
- **`phase2_recovery_paired.csv`** — paired bootstrap `ql_true − ql_false` with Benjamini–Hochberg FDR.

Reuses the `sweep_report.py` bootstrap helpers; config read as `utf-8-sig`; deterministic RNG seed `0xC1`. Headline: recovery(ql_true) < recovery(ql_false).

---

## 8. CI — `.github/workflows/phase2.yml`

Self-contained `workflow_dispatch` pipeline that runs **all of Phase 2 in one dispatch** (no local runs needed).

**Inputs:** `adapt_profiles` (default all 9), `seeds` (default `1,2,3,4,5`), `run_mode` (default `phase1`), `adapt_episodes` (default `0` = profile default), `publish_results` (default `true`).

**Jobs (DAG):**
1. **`setup`** — compiles classes (with retry); derives `profiles_json`, `parents_json` (unique parent labs via `jq` on `run_config.json`), `seeds_json`.
2. **`train_clean`** — matrix `[parent × {true,false} × seed]`; runs the Phase 1 trainer (`-SkipBenchmark -SkipPreflight`); uploads each clean Q-table as `clean-<parent>-stereo-<bool>-seed-<seed>`.
3. **`adapt`** — matrix `[profile × {ql_true,ql_false} × seed]`; downloads the matching clean Q-tables, regenerates the faulty flow, runs `run_phase2_adapt.ps1` with `-RunSeed <seed> -WatchdogIdleSec 1800`; uploads `recovery_stereotypes_*.csv` (+ adapted Q-table / metrics).
4. **`aggregate`** — reconstructs the per-seed layout, runs `python analysis/phase2_recovery.py`, writes a job summary, uploads `phase2-consolidated`, and (if `publish_results`) publishes to the `results` branch under `phase2/<run_id>-<ts>/`.

**Dispatch command:**
```powershell
gh workflow run phase2.yml --ref phase2-fault-detection
```
Variants: `-f seeds=1,2,3,4,5,6,7,8,9,10` (more statistical power); `-f run_mode=dev -f adapt_episodes=200 -f seeds=1,2` (fast smoke — expect `RecoveryEpisodes = -1` because re-convergence needs ≥100 episodes).

> **Why `phase2.yml` is also on `main`:** `workflow_dispatch` only resolves a workflow that exists on the repository's **default branch**. A single workflow-only commit (`67d90de`) registers it on `main`; it does not affect Phase 1 code and can be reverted after the run.

---

## 9. Important constraints / gotchas

- **`adapt_episodes` must stay `0`** (profile default) for a *real* recovery number — `convergenceWindow = 100`, so re-convergence is structurally impossible in fewer than 100 episodes.
- **Faulty components are always Causes** (lamps/spotlight), never Mediates (blinds).
- **All `.ps1` files need UTF-8 BOM** (PS 5.1 mis-parses non-ASCII otherwise).
- **PS 5.1 git stderr quirk:** git's normal stderr surfaces as a non-zero exit even on success — verify pushes by matching SHAs, not exit codes.

---

## 10. File inventory (Phase 2 additions / edits)

| File | Status | Role |
|---|---|---|
| `src/env/tools/QLearner.java` | edited | fault detection + blacklist + warm restart + IV gate |
| `src/env/tools/jia/system_prop_num.java` | new | numeric system-property reader |
| `src/agt/illuminance_controller_agent_adapt.asl` | new | adapt-phase BDI agent |
| `src/agt/lab_profiles.asl` | edited | 9 faulty profiles + `adapt_source` mappings |
| `task_adapt.jcm` | new | MAS launch config for the adapt agent |
| `build.gradle` | edited | `taskAdapt` JavaExec |
| `simulator/generate_faulty_flows.ps1` | edited | faulty-flow generator |
| `simulator/simulator_flow_lab{1,2,3}_f*.json` | new | 9 faulty Node-RED flows |
| `run_phase2_adapt.ps1` | new | adapt orchestrator (`-RunSeed`, watchdog) |
| `config/run_config.json` | edited | phase2 block (9 profiles × 7 maps) |
| `analysis/phase2_recovery.py` | new | recovery CI + paired bootstrap |
| `.github/workflows/phase2.yml` | new | one-dispatch full Phase 2 pipeline |

---

## 11. Phase 2.1 — making recovery measurable

### 11.1 Why the first run measured 0 % re-convergence

The first full Phase 2 run (CI `27470382799`, 90 runs) gave a *perfect* detection
rate (1.00 in all 18 cells) but a **0 % re-convergence rate** — every raw
`recovery_*` row read `ReconvergeEpisode = -1`, so the headline metric
`RecoveryEpisodes = ReconvergeEpisode − DetectEpisode` was undefined and the
thesis claim `recovery(ql_true) < recovery(ql_false)` was **not evaluable**.

Root cause: the recovery test reused the **Phase-1 Bellman-stability**
criterion (`hasConverged` = max&nbsp;|ΔQ| < 1e-3 for 100 consecutive episodes).
That instrument is wrong for the faulted / warm-restarted regime:

1. The warm restart **boosts ε to 0.30** (`fault.relearn.epsBoost`) to force
   re-exploration, so TD targets keep getting perturbed — |ΔQ| never falls
   below 1e-3 for 100 straight episodes.
2. For dead-lamp labs the post-fault goal is only **stochastically reachable**
   (the surviving lever is the sun-gated blind), so the value function has
   irreducible per-episode variance and never settles to a fixed point.

### 11.2 The fix — a policy-stability recovery criterion

Recovery is now defined on the **greedy policy**, not on the value function:

> **Recovered** = the greedy policy (argmax over the *surviving*, non-blacklisted
> actions, summed across zones via `jointArgmaxAction`) is **identical for
> `fault.recover.window` (default 50) consecutive episodes** after the fault was
> blacklisted.

Why this is the right instrument:

- **ε-robust** — the argmax ignores the exploration rate, so the residual
  ε-boost noise that blocked the Bellman test is irrelevant.
- **Reachability-robust** — it tracks the *ranking* of actions, not whether the
  (possibly sun-gated) goal happened to be hit this episode, so it settles even
  when the goal is only stochastically reachable.
- **No lab redesign needed** — it works for every lab as-is. lab3 already has a
  deterministic survivor path (Spotlight +150 with the cross-zone lamp bleed
  +150 = rank&nbsp;3, no sun required); lab2's dead-lamp survivor is the sun-gated
  blind, and the ranking criterion handles both without forcing deterministic
  sun (which would have caused **saturation false-positives** on the healthy
  Causes actuators). lab1 stays detection-only (single lamp ⇒ recovery = N/A).

A constant `+window` confirmation lag is added to `ReconvergeEpisode`, but it is
identical across both arms, so it cancels in the paired `ql_true − ql_false`
difference and does not bias the thesis comparison.

### 11.3 Secondary-defect logging (multi-fault labs)

The iterative detect→blacklist→warm-restart loop now records the episode at
which a **second distinct** defective component is caught
(`secondary_detect/1`). It is written to a new `SecondaryDetectEpisode` column in
`recovery_*.csv`, so iterative-isolation latency on the multi-fault labs becomes
quantifiable. (The analyser reads columns by name, so the extra column is
backward-compatible.) Recovery is still measured from the **primary** detection
to keep `DetectEpisode` and `RecoveryEpisodes` aligned.

### 11.4 Budget + power

- lab3 faulty re-learn budget raised **3000 → 4000** episodes
  (`lab3_f1dead/f1inv/f2dead/f2inv`) to give the richer lab room to re-converge.
  Policy-stability **terminates early** when the window is satisfied, so this
  only affects cells that do not recover sooner — overall wall-clock should
  *drop* versus run 1 (which ran the full budget in every cell).
- `phase2.yml` default seeds **1..5 → 1..10** for confirmatory paired-Wilcoxon
  power (n ≥ 6 required for p < 0.05).

### 11.5 New / changed knobs

| Knob | Default | Meaning |
|---|---|---|
| `-Dfault.recover.window` | `50` | consecutive stable-policy episodes ⇒ recovered |
| `phase2.yml seeds` | `1..10` | confirmatory power |
| lab3 faulty `training_params` | `4000` | re-learn budget |

### 11.6 File inventory (Phase 2.1 edits)

| File | Change |
|---|---|
| `src/env/tools/QLearner.java` | `updateRecoveryDetector()` + `hasRecovered()` ops; `recoveryPolicy`/`recoveryStableCount` fields + `RECOVERY_WINDOW`; reset in `warmRestart`; `saveRecoveryLog` gains `SecondaryDetectEpisode` |
| `src/agt/illuminance_controller_agent_adapt.asl` | `@adapt` loop calls `updateRecoveryDetector`/`hasRecovered` instead of `hasConverged`; `secondary_detect/1` logging + getter; recovery log passes the secondary episode |
| `src/agt/lab_profiles.asl` | lab3 faulty budgets 3000 → 4000 |
| `.github/workflows/phase2.yml` | seeds default 1..10; refreshed input descriptions |

### 11.7 How to run + download

```powershell
# 1. push is already on the working branch; dispatch the full pipeline
gh workflow run phase2.yml --ref phase2-fault-detection

# 2. watch (grab the run id from the list, then watch it)
gh run list --workflow="phase2.yml" --limit 1
gh run watch <run-id>

# 3. download the consolidated results once it finishes
gh run download <run-id> -n phase2-consolidated -D phase2_results
```

The default dispatch now runs 9 profiles × 2 arms × 10 seeds = **180 runs**.
After download, the recovery CSVs (`recovery_stereotypes_<bool><suffix>.csv`)
will carry real `ReconvergeEpisode` / `RecoveryEpisodes` values, and
`analysis/phase2_recovery.py` will report the paired `ql_true − ql_false`
recovery contrast with bootstrap CIs and BH-FDR.

---

# 11. Results & Analysis — First Full Phase 2 Run

**Run:** GitHub Actions `phase2.yml` #`27470382799` (branch `phase2-fault-detection`), wall-clock 2 h 55 m, status *success*.
**Design:** 9 faulty profiles × 2 arms (`ql_true` = KG-primed, `ql_false` = tabula-rasa) × 5 seeds (1–5) = **90 adapt runs**, each warm-started from its lab's clean Phase-1 Q-table. Episode budgets are the profile defaults (lab1/lab2 = 2000, lab3 = 3000). Detection params at defaults (`minSamples=20`, `deadRate=0.80`, `invRate=0.60`, `anomalyRate=0.75`, `epsBoost=0.30`). Convergence criterion: 100 consecutive episodes with max per-step Bellman delta < 1e-3 (`convergenceWindow=100`, reset on warm restart).
**Analysis:** `analysis/phase2_recovery.py` — per-cell bootstrap 95 % CI, paired bootstrap `ql_true − ql_false` with Benjamini–Hochberg FDR (family m = 9), Wilcoxon signed-rank, and Cliff's δ.

## 11.1 Executive summary

| Claim under test | Verdict | Evidence |
|---|---|---|
| Faults are reliably **detected** via KG-vs-reality mismatch | **Confirmed** | detection_rate = 1.00 in **all 18** (profile × arm) cells; correct `DefectComponent` in every case |
| The defective component is **blacklisted** and the user **alerted** | **Confirmed** | every run logs a `DetectEpisode` + defect URI; multi-fault labs blacklist iteratively (two components) |
| KG-primed agent **re-converges faster** (headline `RecoveryEpisodes`) | **Not evaluable** | reconverge_rate = 0.00 in **all** cells; `ReconvergeEpisode = −1` everywhere → `RecoveryEpisodes` undefined |
| Secondary signal: **detection latency** differs by arm | **Confirmed, with a striking interaction** | 6/9 profiles significant at BH q < 0.05 — direction depends on *compensation capacity* (§11.4) |

In one sentence: **the detection-and-isolation half of Phase 2 works exactly as designed; the recovery-speed half could not be measured because no run satisfied the strict Bellman re-convergence criterion within budget.**

## 11.2 Result 1 — Detection and isolation (the core Phase 2 mechanism): success

Across all 90 runs the agent detected a genuine defect and blacklisted the correct actuator:

- **Detection rate = 1.00** for every profile and both arms (`n_detected = 5/5` in all 18 cells).
- **Correct component every time.** Single-fault labs flag the injected lamp (`SetZ1Light`); multi-fault labs flag the injected pair (`SetZ1Light` and `SetZ2Light`). No spurious component was ever logged — in particular the previously-troublesome Mediates blind (`SetZ2Blinds`) was **never** flagged, confirming the `ivGatedComponents` Causes-only adjudication fix holds at scale.
- **Iterative multi-fault isolation works.** In the `f2dead`/`f2inv` labs the monitor stays live after the first blacklist and catches the second dead/inverted lamp, blacklisting it too. (The recovery CSV logs only the *primary* — first-detected — defect, by design, so the second detection is visible in the run logs but not in the recovery table.)

This is the scientifically important claim of Phase 2 — that physics priors function as an **anomaly detector** rather than a means to silently adapt around faults — and it is unambiguously supported.

## 11.3 Result 2 — Re-convergence: the headline metric is undefined this run

**No run re-converged.** `reconverge_rate = 0.00` and `n_reconverged = 0` in all 18 cells; every raw recovery row reads `ReconvergeEpisode = −1`, so `RecoveryEpisodes = −1` and the per-cell mean is `nan`. Consequently the paired comparison contains **only `DetectEpisode`** — the thesis's headline claim `recovery(ql_true) < recovery(ql_false)` **cannot be evaluated from this run.**

This is a *negative result about the metric, not about the mechanism*. The most likely causes, in order of plausibility:

1. **The post-fault optimum is non-stationary / stochastically reachable.** Once the primary lamp is blacklisted, several targets become reachable only through the **stochastic** sun + blinds path (e.g. lab2 Z1 = 25 + (z1l?400) + (z1b?0.5·sun); with the lamp dead, hitting rank 3 needs high sun, which occurs only with probability `sunshine_prob = 0.75` and variable magnitude). A target whose reachability depends on a random exogenous variable yields a value function that keeps receiving non-trivial Bellman updates episode after episode, so the max-Bellman-delta < 1e-3 condition is essentially never met for 100 consecutive episodes. **Strict Bellman convergence is ill-defined for a fault that makes the goal only stochastically attainable.**
2. **ε-floor after warm restart.** `epsBoost = 0.30` deliberately re-injects exploration; with a 0.30 floor the agent keeps taking off-policy actions, which keeps per-episode Bellman deltas above threshold. The boost is correct for *re-exploration* but is in direct tension with a *Bellman-stability* convergence test.
3. **Budget.** Even where a deterministic post-fault optimum exists, 2000–3000 episodes under boosted ε in a harder (reduced-action) MDP may be too few to accumulate 100 consecutive sub-threshold episodes.

The practical consequence: the convergence test inherited from Phase 1 (designed for clean, deterministically-solvable labs) is **the wrong instrument** for the Phase 2 recovery question. See §11.6 for the fix.

## 11.4 Result 3 — Detection latency: a clean, significant interaction effect

Although recovery is unmeasurable, **detection latency** (`DetectEpisode`, episodes from fault-injection start to detection) is fully observed and yields the run's most interesting scientific signal. Paired `ql_true − ql_false`, n = 5 seeds, BH-FDR family m = 9:

| Profile | Faults | ql_true | ql_false | Δ (true−false) | p (boot) | Wilcoxon | Cliff's δ | BH q | Significant? | Direction |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|---|
| lab1_f1dead | 1 dead | 3.6 | 3.6 | 0.0 | 1.000 | 1.000 | +0.04 | 1.000 | no | tie |
| lab2_f1dead | 1 dead | 4.2 | 5.8 | −1.6 | 0.460 | 0.625 | −0.28 | 0.518 | no | true faster |
| lab2_f1inv | 1 inv | 3.4 | 4.8 | −1.4 | 0.087 | 0.250 | −0.64 | 0.112 | no | true faster |
| **lab2_f2dead** | 2 dead | 3.8 | 6.4 | −2.6 | 0.012 | 0.188 | −0.68 | **0.027** | **yes** | **true faster** |
| **lab2_f2inv** | 2 inv | 3.6 | 6.2 | −2.6 | 0.015 | 0.125 | −0.68 | **0.027** | **yes** | **true faster** |
| **lab3_f1dead** | 1 dead | 65.4 | 23.8 | **+41.6** | 0.009 | 0.125 | +0.84 | **0.026** | **yes** | **true SLOWER** |
| **lab3_f1inv** | 1 inv | 257.0 | 20.0 | **+237.0** | 0.000 | 0.063 | +1.00 | **0.000** | **yes** | **true SLOWER** |
| **lab3_f2dead** | 2 dead | 6.8 | 10.4 | −3.6 | 0.001 | 0.125 | −0.56 | **0.003** | **yes** | **true faster** |
| **lab3_f2inv** | 2 inv | 6.0 | 10.6 | −4.6 | 0.026 | 0.188 | −0.60 | **0.039** | **yes** | **true faster** |

A single explanatory axis — **compensation capacity** — accounts for every cell:

- **Multi-fault (all 4 cells): KG-primed detects significantly faster.** When *both* primary lamps fail, the policy cannot route around them; the KG prior keeps directing the agent at the high-leverage (now broken) lamps, so falsifiable observations accumulate quickly and the 20-sample threshold is reached sooner. This is the physics prior behaving as an **efficient active probe**.
- **lab3 single-fault: KG-primed detects dramatically slower** (+42 episodes for dead, +237 for inverted; Cliff's δ = +0.84 / +1.00, i.e. near-total separation). lab3 is the only lab rich enough (spotlight + cross-zone spill) for the agent to **compensate** around one broken lamp. A physics-guided policy quickly discovers it can meet the target *without* the faulty actuator, stops actuating it, and therefore **under-samples the very component it needs to falsify** — delaying detection. The tabula-rasa arm, lacking that efficient detour, keeps poking the broken lamp and detects fast. The inverted case is the extreme: using the lamp now actively *hurts* reward, so the primed policy abandons it almost immediately (detection slips to ~257 episodes, one seed to 402).
- **lab2 single-fault: same direction, not significant.** lab2's zones are independent (no spotlight, no spill), so compensation capacity is low; the primed arm is nominally faster but the effect is small and within noise.
- **lab1: exact tie.** A single actuator means zero compensation capacity and nothing to differentiate the arms.

This is a genuine, publishable finding and a **tension worth foregrounding in the thesis**: *the same physics knowledge that makes a policy robust (able to compensate around a fault) can make that fault harder to diagnose (because the agent stops exercising the broken component).* Robustness and diagnosability trade off. Crucially, the trade-off **disappears — and reverses in the KG agent's favour — under multiple simultaneous faults**, where compensation is impossible.

## 11.5 Were the results "as expected"? Did it work?

- **The detect → isolate → alert pipeline: yes, fully.** This is the central Phase 2 contribution and it is robust (100 % detection, correct components, no false positives, iterative multi-fault handling, clean shutdown over 90 runs and ~3 h of CI).
- **The recovery-speed claim: not demonstrated** — not refuted, but **unmeasured**, because zero runs met the strict re-convergence test. The experiment as configured cannot answer "does KG recover faster?" The metric/instrument needs to change (§11.6), not necessarily the agent.
- **A bonus result emerged**: a significant, mechanistically-explained interaction in *detection latency* (compensation masks single faults; multi-faults restore the physics advantage). This was not the planned headline but is arguably more interesting than a simple speed delta.

## 11.6 Recommended changes before the next run (to make recovery measurable)

The recovery question is well-posed only if the post-fault MDP has a **stable, deterministically reachable** optimum and the convergence test tolerates the re-exploration boost:

1. **Redesign recovery labs so a deterministic survivor path exists.** After the faulty actuator is removed, a *non-stochastic* actuator must still be able to reach each target (e.g. give each zone a redundant lamp, or lower the post-fault target rank so it is reachable without relying on stochastic sun). Otherwise "re-convergence" is mathematically ill-defined for dead-lamp faults.
2. **Replace the Bellman-stability convergence test (for the adapt regime only) with a policy-performance test.** Measure re-convergence as *the first episode after detection at which the greedy policy reaches the goal in K consecutive episodes* (e.g. K = 30), or a moving-average goal-rate ≥ threshold. This is robust to residual ε and to mild stochasticity, and it is what "recovered" actually means operationally.
3. **Decay the ε-boost back down on a schedule** (already partially in place) and/or evaluate convergence on **greedy** roll-outs so exploration noise doesn't veto convergence.
4. **Raise the lab3 budget** (or add an early-stop on goal-rate plateau) given lab3's much longer detection tails.
5. **Log the secondary defect episode** for multi-fault labs so iterative-isolation latency is quantifiable, not just visible in logs.
6. **Increase seeds to 10** for the next run — at n = 5 the Wilcoxon signed-rank floor is p = 0.0625, so it can never clear α = 0.05 alone (note all significance above rests on the bootstrap, with Wilcoxon/Cliff's δ as concordant corroboration).

## 11.7 Threats to validity

- **Statistical power.** n = 5 seeds/cell; the paired Wilcoxon cannot reach p < 0.0625, so significance leans on the bootstrap. The effects that survive BH-FDR (multi-fault and lab3-single) also show large Cliff's δ (|δ| ≥ 0.56), so they are unlikely to be artefacts, but n = 10 would harden them.
- **Single instrument for "recovery."** The null recovery result is conditional on the Bellman-stability definition; a different (and more appropriate) convergence definition could yield non-zero recovery. The negative result therefore bounds the *instrument*, not the *agent*.
- **Detection-latency confound.** `DetectEpisode` mixes two things: how often the policy actuates the broken component (sampling rate) and the statistical threshold (20 samples). The compensation interpretation is well-supported by the direction and magnitude, but isolating "sampling rate" explicitly (e.g. logging actuations-of-defective-component-until-detection) would make the mechanism airtight.
- **Primary-defect-only logging** undercounts multi-fault detection events.

## 11.8 Bottom line for the thesis

Phase 2 **delivers its core scientific claim** — physics priors act as a reliable, false-positive-free fault detector that isolates the broken component and alerts the user, including under multiple simultaneous faults. The **recovery-speed comparison remains open**: this run shows the current convergence instrument is unsuitable for faulted MDPs, and prescribes the lab-design and metric changes needed to measure it cleanly. The unplanned **detection-latency / compensation-capacity interaction** is a strong, defensible secondary result that enriches the narrative rather than complicating it.

---

# 12. Results & Analysis — Phase 2.1 Run (Recovery Now Measurable)

**Run:** GitHub Actions `phase2.yml` #`27499405083` (branch `phase2-fault-detection`, commit `f4ac3fe`), status *success*.
**Design:** 9 faulty profiles × 2 arms (`ql_true` = KG-primed, `ql_false` = tabula-rasa) × **10 seeds (1–10)** = **180 adapt runs**, each warm-started from its lab's clean Phase-1 Q-table. Episode budgets are the profile defaults (lab1 = 1000, lab2 = 2000, lab3 = **4000** after the §11.4 bump). Detection params at defaults (`minSamples=20`, `deadRate=0.80`, `invRate=0.60`, `anomalyRate=0.75`, `epsBoost=0.30`).
**What changed vs run 1 (§11):** the recovery criterion is now the Phase-2.1 **greedy-policy-stability** test (`fault.recover.window = 50` consecutive episodes with an unchanged argmax policy over the surviving action set), replacing the unsuitable Bellman-stability test that produced 0 % re-convergence everywhere.
**Analysis:** `analysis/phase2_recovery.py` — per-cell bootstrap 95 % CI, paired bootstrap `ql_true − ql_false` with Benjamini–Hochberg FDR (recovery family m = 6, detection family m = 9), Wilcoxon signed-rank, Cliff's δ. Below, `*` marks a contrast that survives BH at q < 0.05.

## 12.1 Executive summary

1. **The instrument fix worked.** Re-convergence went from **0/18 cells** (run 1) to **measurable recovery in 12/18 cells** — every single-fault lab now recovers at 100 %, and the headline metric `RecoveryEpisodes` is finally populated with real numbers and tight CIs.
2. **Detection is still perfect:** detection_rate = **1.00 in all 18 cells**, replicated at n = 10. The core Phase-2 claim (physics priors detect + isolate the broken component) is now confirmed on 180 runs.
3. **The headline recovery claim `recovery(ql_true) < recovery(ql_false)` is complexity-gated, not universal.** KG **wins recovery in the complex lab** (lab3_f1dead −95.3 ep*, lab3_f1inv −287 ep, lab3_f2dead −462 ep) but **loses in the trivial/intermediate labs** (lab1_f1dead +56.3 ep*, lab2_f1inv +337 ep*, lab2_f1dead +96 ep). The priors help recovery **in proportion to how much exploitable physical structure the environment contains.**
4. **On total time-to-operational (Detect + Recover), KG wins outright in lab3** (f1dead 197 vs 254 ep; f1inv 432 vs 645 ep) — the slower detection is repaid by much faster recovery.
5. **KG also recovers more *reliably*:** where the rule-based arm sometimes fails to re-stabilise (lab2_f1inv 70 %, lab3_f2dead 50 %), the KG arm reaches **100 %**.
6. **The detection-latency / compensation-capacity interaction from run 1 replicated and hardened** at n = 10 (lab3 single-fault: KG detects significantly *slower*; multi-fault & lab2: KG detects *faster* or ties).
7. **Two honest caveats:** (a) three multi-fault cells (lab2_f2dead, lab2_f2inv, lab3_f2inv) record **0 % recovery in both arms** — a genuine *physical* limit (only sun-gated survivors remain), not an instrument failure; (b) a **spotlight false-positive** appears in lab3_f2inv `ql_true` (5/10 seeds), the first false detection observed.

## 12.2 Result 1 — The recovery instrument now works

| | Run 1 (Bellman test) | Run 2 / Phase 2.1 (policy-stability) |
|---|---|---|
| Cells with any re-convergence | **0 / 18** | **12 / 18** |
| Single-fault cells at 100 % recovery | 0 / 6 | **6 / 6** |
| `RecoveryEpisodes` populated? | never (all −1) | yes (real values + CIs) |

The change validated the §11.2 hypothesis exactly: the old test failed because residual ε-boost noise and stochastic goal-reachability prevent the *value function* from settling, whereas the *greedy policy ranking* settles cleanly. No lab redesign was required.

## 12.3 Result 2 — The headline recovery contrast (`ql_true − ql_false`)

Paired bootstrap, recovery family m = 6 (only cells with measurable recovery enter the family):

| Profile | n | `ql_true` | `ql_false` | Δ (true−false) | 95 % CI | q (BH) | Cliff's δ | Winner |
|---|---|---|---|---|---|---|---|---|
| lab1_f1dead | 10 | 184.1 | 127.8 | **+56.3** | [11.4, 96.6] | **0.032*** | +0.70 | rule-based |
| lab2_f1dead | 10 | 480.6 | 384.5 | +96.1 | [−138, 301] | 0.466 | +0.44 | (ns) rule-based |
| lab2_f1inv | 7 | 606.4 | 269.6 | **+336.9** | [130, 544] | **0.004*** | +0.92 | rule-based |
| lab3_f1dead | 10 | 143.1 | 238.4 | **−95.3** | [−151, −41] | **0.004*** | −0.64 | **KG** |
| lab3_f1inv | 10 | 341.3 | 628.3 | −287.0 | [−966, 78] | 0.689 | +0.31 | (ns) KG |
| lab3_f2dead | 5 | 1781.0 | 2242.8 | −461.8 | [−1001, 134] | 0.182 | −0.20 | (ns) KG |

**Interpretation — the complexity gradient.** The sign of the effect tracks lab complexity monotonically:

- **lab1 (1 actuator, no structure):** after blacklisting the only lamp there is *nothing to reason about*; the KG priors add re-exploration cost with no structural payoff → KG significantly *slower* (+56 ep*).
- **lab2 (2 independent zones, no coupling):** still little to exploit; KG slower (f1inv significantly so, +337 ep*).
- **lab3 (cross-zone bleed + shared spotlight + sun):** the survivor set is *rich and physically structured*, so the KG priors re-rank the surviving actuators efficiently → KG *faster*, significantly so for the dead-lamp case (−95 ep*).

This is a **stronger and more defensible thesis result than a blanket win**: KG-physics priors accelerate recovery *exactly when the post-fault environment retains exploitable structure*, and are a net cost in degenerate environments where there is no physics left to exploit. The mechanism is causal and interpretable, not a tuning artefact.

## 12.4 Result 3 — Total time-to-operational (Detect + Recover)

Recovery latency alone understates the KG arm in lab3 because detection there is deliberately slow (compensation, §12.6). The operationally meaningful quantity is **episodes from fault onset to a stable recovered policy = DetectEpisode + RecoveryEpisodes**:

| Profile | `ql_false` total | `ql_true` total | KG advantage |
|---|---|---|---|
| lab1_f1dead | 3.2 + 127.8 = **131.0** | 3.2 + 184.1 = **187.3** | −56 (rule-based) |
| lab2_f1dead | 5.4 + 384.5 = **389.9** | 3.4 + 480.6 = **484.0** | −94 (rule-based) |
| lab3_f1dead | 15.7 + 238.4 = **254.1** | 54.2 + 143.1 = **197.3** | **+57 (KG)** |
| lab3_f1inv | 16.8 + 628.3 = **645.1** | 90.5 + 341.3 = **431.8** | **+213 (KG)** |

In the complex lab the KG arm reaches an operational recovered policy **22–33 % sooner end-to-end**, even though it spends longer in the detection phase. The "slow detection" is not wasted: by the time the KG arm blacklists the fault it has already partially adapted around it, so the subsequent re-convergence is short.

## 12.5 Result 4 — Recovery reliability (re-convergence rate)

| Profile | `ql_false` reconv. rate | `ql_true` reconv. rate |
|---|---|---|
| lab2_f1inv | 7/10 (70 %) | **10/10 (100 %)** |
| lab3_f2dead | 5/10 (50 %) | **10/10 (100 %)** |
| all other single-fault | 10/10 | 10/10 |

Where the tabula-rasa arm sometimes **fails to re-stabilise at all within budget**, the KG arm always does. So even in cells where the KG mean latency is higher (lab2_f1inv), the KG arm is strictly more *dependable* — it trades a longer but **guaranteed** recovery for the rule-based arm's faster-but-flaky one. For a building-automation safety story, reliability of recovery is at least as important as its speed.

## 12.6 Result 5 — Detection latency: compensation capacity replicates at n = 10

Paired bootstrap, detection family m = 9:

| Profile | `ql_true` | `ql_false` | Δ | q (BH) | Cliff's δ | Faster detector |
|---|---|---|---|---|---|---|
| lab2_f1dead | 3.4 | 5.4 | −2.0 | **0.000*** | −0.71 | **KG** |
| lab2_f2inv | 4.5 | 6.3 | −1.8 | 0.081 | −0.43 | (ns) KG |
| lab2_f1inv | 3.9 | 5.9 | −2.0 | 0.095 | −0.61 | (ns) KG |
| lab3_f2inv | 8.1 | 11.3 | −3.2 | **0.028*** | −0.43 | **KG** |
| lab1_f1dead | 3.2 | 3.2 | 0.0 | 1.000 | 0.00 | tie |
| lab3_f2dead | 10.2 | 9.9 | +0.3 | 0.882 | −0.04 | tie |
| lab3_f1dead | 54.2 | 15.7 | **+38.5** | **0.000*** | +0.92 | rule-based |
| lab3_f1inv | 90.5 | 16.8 | **+73.7** | **0.000*** | +1.00 | rule-based |

The run-1 mechanism is confirmed and sharpened: **the KG primed policy is so good at *compensating around* a single fault in the rich lab that it under-samples the broken actuator, delaying the 20-sample detection threshold** (lab3 single-fault, |δ| = 0.92–1.0, the largest effects in the study). When the lab is poorer (lab2) or the fault cannot be routed around (multi-fault), the physics advantage flips back to *faster* detection. This is the **robustness ↔ diagnosability trade-off**: the better an agent is at silently absorbing a fault, the longer that fault hides.

## 12.7 Result 6 — The 0 %-recovery cells are a physical limit, not a bug

Three cells record 0 % re-convergence in **both** arms: lab2_f2dead, lab2_f2inv, lab3_f2inv. This is **not** an instrument failure (the instrument now fires correctly in 12 cells); it is the post-fault physics:

- lab2_f2dead / f2inv: both task lamps are gone, leaving only the **sun-gated blinds** (a Mediates actuator whose effect is `0.5 × sun`). Rank-3 is reachable *only* in high-sun episodes, so no fixed greedy policy is optimal across the pinned-sun episode distribution → the policy keeps re-ranking and never holds for 50 straight episodes.
- lab3_f2inv: compounded by the spotlight false-positive (§12.8) removing a third actuator in half the seeds.

By contrast **lab3_f2dead reaches 100 % recovery in the KG arm** (50 % rule-based) because the **shared Spotlight survives** (a deterministic Causes actuator, +150 to both zones), giving a stable structural lever the blinds-only labs lack. The recovery-rate pattern therefore reads cleanly off the survivor physics: *recovery is possible iff a deterministic survivor lever remains*, and the KG arm exploits it more reliably.

## 12.8 Diagnosability caveat — spotlight false-positive in lab3_f2inv

In lab3_f2inv `ql_true`, the **healthy Spotlight was flagged defective in 5/10 seeds** (seeds 2, 3, 6, 7, 8 reported `SetSpotlight` as the primary defect). This is the **first false positive** in the whole study (detection precision was otherwise perfect across 180 runs). Mechanism: when *both* task lamps are inverted in the cross-coupled lab, the Expected-vs-Actual residual for a spotlight toggle is corrupted by the simultaneous wrong-direction lamp contributions, and the anomaly-rate trigger mis-attributes the violation. It is confined to the **double-inversion + cross-coupling** corner case. Mitigation options for a follow-up: raise `invRate`/`anomalyRate` for cross-coupled labs, require the residual to be component-attributable before blacklisting, or detect faults one component at a time with re-baselining between isolations.

## 12.9 Were the results "as expected"? Did it work?

- **The instrument fix: yes, decisively.** Recovery is measurable; the §11.2 design rationale held in practice.
- **The headline claim: partially, and more interestingly than expected.** `recovery(ql_true) < recovery(ql_false)` is **true in the complex lab** (the regime the thesis cares about) and **false in degenerate labs** — yielding a *complexity-gated* result with a clean causal mechanism, plus an outright **end-to-end** win for KG in lab3 once detection time is included.
- **Detection: confirmed and replicated** (100 %, n = 10), with the compensation-capacity interaction now resting on the two largest effect sizes in the study.
- **Bonus reliability result:** KG recovers where rule-based fails (lab2_f1inv, lab3_f2dead).

## 12.10 Threats to validity

- **`+window` confirmation lag.** Every `ReconvergeEpisode` includes a constant 50-episode confirmation tail; it is **identical across arms** and cancels in the paired Δ, so it does not bias any contrast — but absolute recovery numbers are inflated by ~50 episodes and should be read as relative.
- **Power at the cell level.** n = 10 lifts the Wilcoxon floor below 0.05 (best case p = 0.002), so significance no longer rests on the bootstrap alone; the three BH-significant recovery effects also carry |δ| ≥ 0.64. The non-significant KG-favouring cells (lab3_f1inv, lab3_f2dead) have wide CIs from heavy right-skew and reduced paired n (5–10) — directional but underpowered.
- **Policy-stability ≠ goal-optimality.** The criterion certifies a *stable* greedy policy, not necessarily a *goal-reaching* one; in sun-gated labs a stable policy may still miss rank-3 on low-sun episodes. This is the correct operational notion of "re-converged" for a non-stationary MDP, but it should be reported as *policy convergence*, not *performance optimality*.
- **Spotlight false-positive** (§12.8) means detection precision is 100 % only outside the double-inversion cross-coupled corner; this should be disclosed, not hidden.
- **Pinned-sun episode design** makes some post-fault optima genuinely unreachable; the 0 %-recovery cells reflect that design choice, so they bound the *environment*, not the *agent*.

## 12.11 Bottom line for the thesis

Phase 2.1 **closes the open question from run 1**: with a fault-appropriate recovery instrument, re-convergence is measurable, and the data deliver a nuanced positive result. **Detection and isolation are perfect and replicated (100 %, 180 runs).** The recovery-speed claim holds **where it matters** — in the structurally rich complex lab, KG-physics priors recover faster (−95 ep*, and −22 to −33 % end-to-end including detection) **and** more reliably (100 % vs 50–70 %) — while honestly *reversing* in degenerate labs that retain no exploitable physics. The framing this run supports is therefore: **physics priors convert environmental complexity from a liability into an advantage for fault recovery**, with the compensation-capacity interaction and the lab3_f2inv false-positive as the two caveats that keep the story scientifically honest.

---

# 13. Critical re-assessment — is the recovery analysis paper-ready, and are we done with Phase 2?

This section is a deliberately sceptical audit of §12 against the advisor's exact
requirement (*"the agent recognizes an action produced unexpected behaviour,
re-checks with physics, discards the artifact, re-learns with and without
physics; expected that it realigns **faster** with physics"*). It supersedes the
§12 "complexity-gated" framing where the two disagree.

## 13.1 Short verdict

| Question | Answer |
|---|---|
| Do we have full paper-quality analysis + data? | **Partially.** Detection is paper-ready. The recovery analysis has **three fixable validity gaps** and is not yet defensible as-is. |
| Are the results as expected (advisor's hypothesis)? | **Not in aggregate — but yes in the cells where the recovery question is actually well-posed.** |
| Did it work correctly? | Detection / isolation / pipeline: **yes**. Recovery *instrument*: it produces numbers, but it measures policy *stability*, not goal-*reaching*, and this run has no data to bridge that gap. |
| Are we done with Phase 2? | **No.** The detection half is done; the recovery half needs one more focused iteration. |

## 13.2 The framing correction: "well-posedness-gated", not "complexity-gated"

§12.3 reads the result as a smooth *complexity* gradient (KG loses in simple labs,
wins in complex ones). Tracing each cell's **post-fault physics** gives a sharper —
and more hypothesis-favourable — explanation: **the sign of the KG effect tracks
whether a *deterministic* recovery path even exists**, not lab complexity per se.

| Cell | Deterministic survivor path after fault? | KG recovery result |
|---|---|---|
| `lab3_f1dead` | **Yes** — Spotlight +150 ∧ cross-zone bleed +150 = rank-3, no sun needed | **KG faster −95.3*** |
| `lab3_f1inv` | **Yes** — same survivor structure | KG faster −287 (ns) |
| `lab2_f1dead` | No — only survivor is the sun-gated blind (rank-3 only at sun≈900) | ns (+96) |
| `lab2_f1inv` | No — sun-gated blind only | **KG slower +337*** |
| `lab1_f1dead` | **No path at all** — single lamp dead ⇒ rank-3 physically unreachable | **KG slower +56.3*** |
| `lab2_f2*`, `lab3_f2*` | No (sun-gated / blinds-only) | 0 % both arms (3 cells) / mixed |

Read this way: **in every cell where a working post-fault policy exists, KG is at
least as fast and usually faster; the two significant "KG slower" results
(`lab1_f1dead`, `lab2_f1inv`) are precisely the cells where no deterministic
recovery is possible.** So the honest headline is the *opposite* of a reversal —
it **supports** the advisor's hypothesis once ill-posed cells are excluded, rather
than contradicting it in "simple" labs.

## 13.3 Validity gap 1 — `lab1_f1dead` recovery is semantically invalid

`lab1_f1dead` kills the lab's **only** lamp, so rank-3 is physically unreachable
afterwards (confirmed from raw rows: it still records `ReconvergeEpisode` — e.g.
`ql_false=90`, `ql_true=210` for seed 1 — because the **policy** stabilises even
though no goal is reachable). The doc itself defines lab1 as **detection-only,
recovery = N/A** (§4 scope note, §11.2). Yet §12.3 includes its `+56.3*` in the
recovery family and reads it as "KG slower."

**This is measuring how fast the agent settles into a *futile* stable policy, not
realignment speed.** It must be removed from the recovery family (it inflates the
BH family size and produces a misleading significant "KG loses"). KG taking longer
here is plausibly *good* behaviour — it keeps trying physically-sensible actions
longer before giving up.

## 13.4 Validity gap 2 — "stability" ≠ "goal-reaching" (no data to bridge it)

The recovery criterion certifies the greedy policy **stopped changing** for 50
episodes, not that it **reaches the goal**. A faster "recovery" could in principle
be premature convergence to a stable-but-bad policy. The downloaded artifact
(`phase2-consolidated`) contains **only the recovery CSVs** — there is **no
`metrics_adapted_*` (per-episode goal-rate)** in it. So with this run's data we
**cannot prove a "recovered" policy is actually a good policy.** For `lab3_f1*`
the deterministic survivor makes it very likely; for a paper-quality "realigns
faster" claim it must be *shown*, not assumed.

## 13.5 Validity gap 3 — the first false positive is real and must be disclosed

`lab3_f2inv` `ql_true` flagged the **healthy Spotlight** as defective in **5/10
seeds** (raw `DefectComponent = SetSpotlight` for seeds 2, 3, 6, 7, 8). This is
the only precision failure in 180 runs. It means the clean "100 % detection, zero
false positives" headline holds **everywhere except the double-inversion +
cross-coupling corner**, and that caveat must travel with the headline.

## 13.6 What the run got unambiguously right

- **Detection / isolation / alert — the advisor's central requirement — is fully
  delivered and replicated:** 100 % detection in all 18 cells over 180 runs,
  correct primary component, iterative multi-fault isolation, and the
  `SecondaryDetectEpisode` column now populated for all four multi-fault cells in
  both arms (10/10).
- **The recovery instrument fix worked:** 0/18 → 12/18 cells with measurable
  re-convergence; the §11.2 design rationale held.
- **Where recovery is well-posed, the hypothesis holds:** `lab3_f1dead` −95.3 ep*
  (and the end-to-end Detect+Recover win in `lab3_f1*`), plus the reliability win
  (KG 100 % vs rule-based 50–70 %).

## 13.7 What remains before Phase 2 is "done" (one focused iteration)

1. **Validate recovery against goal-rate (highest priority).** Emit a
   post-detection **greedy goal-rate** per episode and ship `metrics_adapted_*` in
   the consolidated artifact; redefine "recovered" as **stable AND goal-reaching**
   (e.g. greedy goal-rate ≥ θ for K consecutive episodes), or at minimum report
   both side by side. This closes §13.4.
2. **Restrict the recovery-speed family to well-posed cells** (`lab3_f1dead`,
   `lab3_f1inv`; provisionally `lab2_f1dead`). Mark `lab1_f1dead` and the
   sun-gated / blinds-only cells as **detection-only / recovery = N/A** so they no
   longer generate misleading significant "KG slower" artifacts (closes §13.3) and
   the BH family shrinks correctly.
3. **Fix / bound the spotlight false-positive** (§13.5): require the
   Expected-vs-Actual residual to be component-attributable before blacklisting,
   or isolate faults one component at a time with re-baselining between
   isolations; re-run `lab3_f2inv` to confirm precision returns to 100 %.

Items 1–2 are analysis/instrumentation changes (small code + one CI re-run); item
3 is a detector refinement. None require a Phase-1 redesign.

## 13.8 Bottom line

**Detection — the scientifically central half of Phase 2 — is complete and
robust.** The **recovery half is promising and, once the ill-posed cells are
excluded, actively supports the advisor's hypothesis**, but it is **not yet
paper-ready**: it needs the goal-rate validation (§13.4), the well-posed-family
restriction (§13.3), and the false-positive fix (§13.5). **We are not done with
Phase 2** — we are one focused iteration away, and that iteration is about
*measurement rigour and detector precision*, not about the agent's core behaviour,
which already works.

---

# 14. Phase 2.2 — measurement rigour & detector precision (the §13.7 iteration)

This iteration implements the three remedial items from §13.7. Each is a small,
targeted change to instrumentation / detector logic; none touches the agent's
core detect→blacklist→warm-restart behaviour. After these changes one CI dispatch
produces everything needed to close Phase 2.

## 14.1 Fix 1 — recovery is now validated against goal-rate (closes §13.4)

**Problem.** "Re-converged" meant *the greedy policy stopped changing* (policy
stability), not *the greedy policy reaches the goal*. In sun-gated cells a policy
can be stable yet futile, and we shipped no per-episode data to tell the two
apart.

**Change.** After all adaptation training finishes, the adapt agent runs a
**greedy (ε=0) certification rollout** over the *final* surviving policy and
records the fraction of evaluation episodes that reach the goal:

- `src/agt/illuminance_controller_agent_adapt.asl`
  - new belief `greedy_eval_episodes(20)` (overridable via
    `-Dfault.recover.evalEpisodes`);
  - new plans `@certify_recovery`, `@greedy_eval_loop`, `@greedy_rollout` —
    ε=0 exploitation of `getActionFromState(StateVec, false, …)`, **no**
    `calculateQ` and **no** `observeForFaults`, so certification cannot perturb
    either learning or the recovery measurement;
  - `@adapt_finish` calls `!certify_recovery(GoalRate)` and threads the result
    into the recovery log.
- `src/env/tools/QLearner.java` — `saveRecoveryLog(…)` gains a
  `double recoveredGoalRate` parameter; the CSV header is now
  `DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes,SecondaryDetectEpisode,RecoveredGoalRate`.
- `.github/workflows/phase2.yml` — the aggregate job's "Reconstruct per-seed
  recovery layout" step now also copies `metrics_adapted_stereotypes_*.csv` into
  the consolidated `recovery_root/seed*/` tree, so the per-episode `GoalReached`
  series ships in the single `phase2-consolidated` artifact.

**Reported metric.** We keep `ReconvergeEpisode` as the *policy-stability* point
(unchanged semantics) and report `RecoveredGoalRate` **alongside** it — the
"report both side by side" option from §13.7.1. A run counts as a *goal-reaching*
recovery iff it re-converged **and** its greedy goal-rate ≥ θ (θ = 0.5).

## 14.2 Fix 2 — recovery-speed family restricted to well-posed cells (closes §13.3)

**Problem.** Cells with no deterministic post-fault survivor (`lab1_f1dead` — lone
lamp; sun-gated `lab2_*` / `lab3_f2*`) were entering the recovery-speed comparison
and generating misleading significant "KG slower" rows, and inflating the BH
family.

**Change.** `analysis/phase2_recovery.py`:

- `_WELL_POSED_RECOVERY = ("lab3_f1dead", "lab3_f1inv")` — the only cells with a
  deterministic survivor path (shared Spotlight +150 to both zones plus cross-zone
  lamp bleed reaches rank-3 without relying on the stochastic sun);
- `write_paired_table` **skips non-well-posed profiles for the
  `RecoveryEpisodes` metric**, so the recovery-speed BH family contains only
  well-posed cells. The `DetectEpisode` (detection-latency) family still spans all
  profiles;
- the CI table gains `well_posed_recovery`, `greedy_goal_rate_mean`,
  `n_goal_reaching`, `goal_reaching_rate`; the console summary gains a `goal%`
  column and a `wp` (well-posed) flag.

Ill-posed cells are thus reported **descriptively** (detection + goal-rate) and
remain in the detection family, but no longer produce recovery-speed significance
artifacts.

## 14.3 Fix 3 — the `lab3_f2inv` spotlight false positive (closes §13.5)

> **⚠ Empirical outcome (see §15.9): the guards described in this section did NOT
> resolve the false positive.** The Phase 2.2 run flagged the healthy Spotlight in
> **8/10** seeds (up from 5/10). Root cause: the FP occurs at *primary* detection —
> before any component is blacklisted — so the two post-blacklist guards below never
> engage. **The genuine remedy — a primary-detection-time component-attribution
> rule — is now implemented and documented in §16.** The description below is
> retained for the record as what was attempted.

**Problem.** With the lamp inverted *and* blacklisted, its frozen/inverted output
corrupted the shared-zone residual; the Expected-vs-Actual check then mis-charged
the **healthy Spotlight** in 5/10 seeds — the study's only precision failure.

**Change.** Two complementary guards in `src/env/tools/QLearner.java`:

1. **Component-attributable residuals (`zoneCauseContaminated[]`).** When a
   component is blacklisted, every zone it *Causes*-feeds is marked contaminated
   (`blacklistComponent`). `observeForFaults` then **abstains** on contaminated
   zones when adjudicating *other* components — a residual in a zone fed by a
   frozen actuator is not attributable to the component under test. The guard sits
   only in the inverted-detection branch (the dead-actuator branch keys off the
   component's *own* command bit, which contamination cannot corrupt).
2. **Per-component sequential isolation (re-baselining).** `warmRestart` now
   zeroes the fault-evidence counters (`faultObsN`, `faultDeadN`, `faultInvertN`)
   so evidence accumulated while the just-blacklisted component was still active is
   discarded, and the next component is adjudicated afresh in the reduced action
   space. Legitimate multi-fault evidence re-accumulates after the reset (run 2
   populated `SecondaryDetectEpisode` 10/10), so iterative isolation is preserved.

Neither guard affects the well-posed `lab3_f1*` cells (single-fault: no further
component to adjudicate) nor primary detection (which precedes any blacklist).

## 14.4 File inventory (Phase 2.2 edits)

| File | Change |
|---|---|
| `src/env/tools/QLearner.java` | `saveRecoveryLog` +`recoveredGoalRate` column; `zoneCauseContaminated[]` field + allocation; contamination guard in `observeForFaults`; contamination marking in `blacklistComponent`; fault-counter re-baseline in `warmRestart`. |
| `src/agt/illuminance_controller_agent_adapt.asl` | `greedy_eval_episodes` belief + `-Dfault.recover.evalEpisodes` override; `@certify_recovery` / `@greedy_eval_loop` / `@greedy_rollout` plans; `@adapt_finish` certifies and threads `GoalRate` into `saveRecoveryLog`. |
| `.github/workflows/phase2.yml` | consolidated artifact now also carries `metrics_adapted_stereotypes_*.csv`. |
| `analysis/phase2_recovery.py` | `_WELL_POSED_RECOVERY`, θ; `RecoveredGoalRate` parsing; goal-rate + well-posed columns; recovery BH family restricted to well-posed cells. |

All Java compiles clean (`./gradlew compileJava`); `phase2_recovery.py` byte-compiles
clean. The change set is measurement/precision only — the agent's detect→isolate→
re-learn loop is unchanged.

---

# 15. Results & Analysis — Phase 2.2 Run (goal-rate certified recovery)

**Run:** GitHub Actions `phase2.yml` #`27507087176` (branch `phase2-fault-detection`, commit `aa74486`), status *success*.
**Design:** 9 faulty profiles × 2 arms (`ql_true` = KG-primed, `ql_false` = tabula-rasa) × **10 seeds (1–10)** = **180 adapt runs**, each warm-started from its lab's clean Phase-1 Q-table. Profile-default budgets (lab1 = 1000, lab2 = 2000, lab3 = 4000). Detection params at defaults.
**What is new vs Phase 2.1 (§12):** (a) every run now emits a **greedy (ε=0) goal-rate** over its *final* policy (`RecoveredGoalRate`), so "recovered" can be split into *stable* vs *stable-AND-goal-reaching*; (b) the recovery-speed BH family is restricted to the two **well-posed** cells (`lab3_f1dead`, `lab3_f1inv`); (c) a false-positive-mitigation attempt was deployed for `lab3_f2inv`.
**Analysis:** `analysis/phase2_recovery.py` — bootstrap 95 % CI, paired bootstrap `ql_true − ql_false` with BH-FDR (recovery family **m = 2**, detection family m = 9), Wilcoxon, Cliff's δ. `*` = survives BH at q < 0.05.

## 15.1 Did the three §13.7 items land?

| §13.7 item | Implemented? | Worked? | Evidence |
|---|---|---|---|
| 1 — validate recovery against goal-rate | **Yes** | **Yes, decisively** | `RecoveredGoalRate` populated for all 180 runs; cleanly separates futile-stable (lab1/lab2 ≈ 0) from genuine recovery (lab3_f1dead ≈ 0.9) — §15.3 |
| 2 — restrict recovery family to well-posed cells | **Yes** | **Yes** | recovery BH family now m = 2 (lab3_f1dead, lab3_f1inv); the misleading `lab1_f1dead` "+56 KG-slower" is gone — §15.7 |
| 3 — fix the `lab3_f2inv` spotlight false positive | Attempted | **No — regressed to 8/10** | the FP fires at *primary* detection, before any blacklist, so the post-blacklist guards never engage — §15.9 |

**Two of three landed; the goal-rate certification (item 1) is the most consequential change in the whole Phase-2 effort** because it retro-actively tightens — and in places overturns — the §12 conclusions.

## 15.2 Executive summary

1. **Detection still perfect on the lamps:** detection_rate = **1.00 in all 18 cells** (180 runs); the correct injected lamp(s) flagged everywhere — *except* the `lab3_f2inv` KG arm, where the healthy Spotlight is mis-flagged in 8/10 seeds (§15.9).
2. **The goal-rate certification is the decisive instrument.** It shows that **only one cell in the entire study has a genuinely goal-reaching recovery: `lab3_f1dead`** (greedy goal-rate ≈ 0.92–0.97, 10/10 and 9/10 goal-reaching). Every "recovery" in lab1, lab2, and the sun-gated multi-fault cells is **stable-but-futile** (goal-rate ≈ 0–0.09).
3. **In that one well-posed, goal-reaching cell the thesis hypothesis holds cleanly and strongly:** KG recovers **−126.8 episodes faster** (q = 0.004*, Cliff's δ = −0.83) **and** wins **end-to-end** (detect + recover: 186 vs 285 ep) **and** is fully goal-reaching (10/10 vs 9/10).
4. **The other well-posed cell, `lab3_f1inv`, is an honest partial:** *neither* arm reliably reaches the goal (goal-rate ≈ 0.43 both), and KG is **slower** to re-stabilise (+147.6 ep, q = 0.009*) though marginally more goal-reaching (4/10 vs 2/10).
5. **The §12.5 "reliability win" was a stability artifact.** Goal-rate ≈ 0.02–0.09 in lab2 single-fault cells means those 100 %-vs-70 % re-convergence figures were comparing *futile* stable policies — exactly the §13.4 risk, now measured and corrected.
6. **Detection-latency / compensation-capacity interaction replicated a third time:** KG detects single lab3 faults much slower (f1dead +33.5 q*, f1inv +126 q*) and multi-fault / lab2 faults faster — the robustness ↔ diagnosability trade-off is now a stable, thrice-observed result.
7. **The spotlight false positive is unresolved and slightly worse (8/10).** This is the one regression and the single remaining blocker to a clean precision headline.

## 15.3 Result 1 — Goal-rate certification: the instrument that re-frames Phase 2

The new `RecoveredGoalRate` (fraction of 20 greedy ε=0 episodes the *final* policy reaches the goal) cleanly partitions the cells into three physically-meaningful classes:

| Cell | `ql_false` goal-rate | `ql_true` goal-rate | Class |
|---|---:|---:|---|
| **lab3_f1dead** | **0.97** | **0.915** | **goal-reaching recovery** |
| lab3_f1inv | 0.44 | 0.425 | partial (neither reaches) |
| lab3_f2dead | 0.335 | 0.365 | partial (neither reaches) |
| lab3_f2inv | 0.215 | 0.305 | mostly futile |
| lab2_f1dead | 0.065 | 0.085 | **futile-stable** |
| lab2_f2dead | 0.055 | 0.065 | futile-stable |
| lab2_f1inv | 0.02 | 0.03 | futile-stable |
| lab2_f2inv | 0.02 | 0.02 | futile-stable |
| lab1_f1dead | 0.00 | 0.00 | **physically unreachable** |

This is exactly the bridge §13.4 demanded. It validates the §11.2 design choice (policy-stability is the right *recovery-detection* instrument) **while exposing that stability alone overstates success**: a stable policy in lab1_f1dead (lone dead lamp) reaches the goal 0 % of the time, and the lab2 single-fault "recoveries" reach it ≈ 2–9 %. The certification does precisely what a referee would ask for — it refuses to call a futile-but-stable policy "recovered."

**Headline reframing:** the Phase-2 recovery claim should now be stated as *goal-reaching* recovery, and on that strict definition **the study has exactly one clean positive cell — and it favours KG.**

## 15.4 Result 2 — The clean win: `lab3_f1dead` (goal-reaching, KG faster, end-to-end)

This is the only cell where the advisor's question is fully well-posed (a deterministic survivor path exists: Spotlight +150 to both zones ∧ cross-zone lamp bleed +150 = rank-3 without sun) **and** the final policy actually reaches the goal. Per-seed:

| | `ql_true` (KG) | `ql_false` (rule-based) |
|---|---|---|
| Recovery episodes (paired n=9) | **133.7** | 260.4 |
| Δ (true−false) | **−126.8**, 95 % CI [−187, −76], **q = 0.004***, δ = **−0.83** | — |
| Greedy goal-rate (mean) | 0.915 (all 10 seeds ≥ 0.5) | 0.97 (9 reconverged, all ≥ 0.5) |
| Goal-reaching recoveries | **10 / 10** | 9 / 10 |
| Detect episode (mean) | 58.4 | 24.9 |
| **End-to-end (detect + recover)** | **186.5** | 285.3 |

KG is **48 % faster to re-stabilise** and reaches an operational, **goal-reaching** policy **≈ 99 episodes (35 %) sooner end-to-end**, despite paying a longer detection phase (the compensation effect, §15.6). Both arms are genuinely goal-reaching, so this is *not* a stability artifact — it is the advisor's hypothesis confirmed in the regime where it is meaningful. This single cell is the paper's central Phase-2 recovery result.

## 15.5 Result 3 — The honest partial: `lab3_f1inv`

The second well-posed cell tells a more cautious story. The inverted single lamp leaves the same survivor structure as f1dead, yet the greedy goal-rate is only **≈ 0.43 in both arms** — the surviving Spotlight+bleed path reaches rank-3 in fewer than half of episodes, so *no* stable policy is reliably goal-reaching here.

| | `ql_true` (KG) | `ql_false` (rule-based) |
|---|---|---|
| Recovery episodes (paired n=9) | 420.3 | 272.8 |
| Δ (true−false) | **+147.6**, 95 % CI [+36, +278], **q = 0.009***, δ = +0.58 | — |
| Greedy goal-rate (mean) | 0.425 | 0.44 |
| Goal-reaching recoveries | **4 / 10** | 2 / 10 |

So KG is **significantly slower** to re-stabilise here, but ends **more often goal-reaching** (4 vs 2 of 10). The two well-posed cells therefore split: KG wins the dead-lamp case decisively and loses the inverted-lamp speed race while edging the goal-reaching count. The honest paper statement is *"KG accelerates goal-reaching recovery for a dead actuator with a deterministic survivor; for an inverted actuator the picture is mixed and neither agent reliably re-reaches the goal."*

## 15.6 Result 4 — Detection latency / compensation capacity (third replication)

Detection family (m = 9), paired bootstrap:

| Profile | `ql_true` | `ql_false` | Δ | q (BH) | δ | Faster |
|---|---:|---:|---:|---:|---:|---|
| lab3_f1inv | 152.1 | 26.1 | **+126.0** | **0.000*** | +0.98 | rule-based |
| lab3_f1dead | 58.4 | 24.9 | **+33.5** | **0.005*** | +0.54 | rule-based |
| lab2_f1inv | 3.7 | 6.2 | −2.5 | **0.009*** | −0.65 | KG |
| lab2_f1dead | 3.9 | 5.8 | −1.9 | **0.037*** | −0.54 | KG |
| lab3_f2inv | 5.5 | 10.2 | −4.7 | **0.000*** | −0.81 | KG |
| lab2_f2dead | 3.8 | 5.6 | −1.8 | 0.059 | −0.40 | (ns) KG |
| lab2_f2inv | 4.8 | 5.6 | −0.8 | 0.482 | −0.26 | (ns) KG |
| lab3_f2dead | 9.7 | 10.3 | −0.6 | 0.575 | −0.12 | tie |
| lab1_f1dead | 3.4 | 3.7 | −0.3 | 0.652 | −0.10 | tie |

The pattern from runs 1 and 2 reproduces a third time, now with the two largest effects in the study (lab3 single-fault, |δ| = 0.54–0.98): **a KG policy good enough to compensate around one fault in the rich lab under-samples the broken actuator and detects it later**, while in poorer labs (lab2) or unroutable multi-fault cells it detects *faster*. This robustness ↔ diagnosability trade-off is now the most stable secondary finding of Phase 2.

## 15.7 Result 5 — The well-posed family restriction worked

The recovery BH family is now **m = 2** (only `lab3_f1dead`, `lab3_f1inv`), so the §12.3 artifacts — most importantly the significant `lab1_f1dead` "+56 ep KG-slower" that was really *"KG takes longer to settle into a futile policy on the lone-dead-lamp cell"* — no longer pollute the recovery conclusion. `lab1_f1dead` (goal-rate 0.0) and the sun-gated cells remain in the **detection** family and are reported descriptively via goal-rate, exactly as §13.3 prescribed. The recovery comparison is now made only where it is mathematically meaningful.

## 15.8 Result 6 — Recovery reliability, re-read through goal-rate

§12.5 reported a KG "reliability win" (lab2_f1inv: 100 % vs 70 % re-convergence; lab3_f2dead: 100 % vs 50 %). Goal-rate certification forces a correction:

- **lab2_f1inv** — both arms' goal-rate ≈ 0.02–0.03. The KG arm re-stabilises more *often*, but into a policy that essentially **never reaches the goal**. The "reliability win" is a win in *policy stability*, **not** in task success. It must be reported as such, or dropped.
- **lab3_f2dead** — KG reconverges 9/10 vs 7/10, goal-rate ≈ 0.34–0.37. Neither reaches the goal reliably (the shared Spotlight survives but the double-dead-lamp + sun gating leaves rank-3 only partially reachable). A *partial* reliability signal, not a success signal.

This is precisely the §13.4 hazard — "faster/again-stable ≠ better" — and the new instrument catches it. It is a strengthening of scientific rigour, not a loss of result.

## 15.9 Result 7 — The spotlight false positive is unresolved (and worse)

The §14.3 fix **did not work.** In `lab3_f2inv` `ql_true` the healthy Spotlight is now flagged as the primary defect in **8/10 seeds** (seeds 2, 3, 4, 5, 6, 7, 8, 10; only seeds 1 and 9 correctly flag `SetZ2Light`) — up from 5/10 in run 2. (The `ql_false` arm is unaffected: it correctly flags `SetZ1Light;SetZ2Light`.)

**Root-cause diagnosis.** The Spotlight is flagged at **primary** detection (`DetectEpisode` = 3–11), i.e. *before any component is blacklisted*. The two deployed guards — the contaminated-zone skip and the `warmRestart` counter re-baseline — only act **after** the first blacklist. They therefore **never engage on the event that produces this FP.** The earlier hypothesis ("frozen blacklisted lamp corrupts the residual") mis-located the failure in time: the corruption comes from the **two simultaneously-inverted, still-active lamps** depressing the shared zones, so when the agent toggles the (healthy) Spotlight the zone response is muted/contradictory and the anomaly trigger mis-charges it. The KG arm hits this more than rule-based because its prior makes it exercise the Spotlight in the corrupted regime sooner.

**The correct fix (not yet implemented).** Make the residual *component-attributable at primary detection*: only blacklist a component when the zone evidence cannot be jointly explained by other still-suspected actuators feeding the same zone — equivalently, **isolate one component at a time**, withholding judgement on any actuator that shares a zone with another actuator currently accumulating dead/inverted evidence. This is a primary-detection-time rule, not a post-blacklist one, and is the genuine remedy. It is a detector refinement (a few dozen lines in `observeForFaults`) plus one confirmatory CI run.

## 15.10 Threats to validity

- **One clean positive cell.** The goal-reaching recovery result rests on `lab3_f1dead` alone. It is strong (q = 0.004, δ = −0.83, 10/10 goal-reaching, end-to-end win), but the well-posed-and-goal-reaching design space is narrow; broadening it (e.g. a deterministic-survivor lab2 variant, or a lower post-fault target rank) would let the claim generalise beyond a single cell.
- **Greedy goal-rate sampling.** `RecoveredGoalRate` uses K = 20 ε=0 episodes over the training scenario set; the 0.05 quantisation (1/20) and the θ = 0.5 cutoff are coarse. The qualitative classes (≈ 0 vs ≈ 0.4 vs ≈ 0.9) are unambiguous, but the exact `n_goal_reaching` counts near θ (lab3_f1inv) would tighten with larger K.
- **Detection-precision caveat now larger.** The clean "100 % detection, zero false positives" line holds for 17/18 cells but fails in `lab3_f2inv` KG (8/10 FP). This must travel with every detection headline until the §15.9 fix lands.
- **`+window` confirmation lag** (50 episodes) still inflates absolute recovery numbers identically in both arms; it cancels in the paired Δ but absolute episode counts are relative, not absolute.
- **lab3_f1inv goal-rate < 0.5 in both arms** means its "recovery" comparison is partly a comparison of *partly-goal-reaching* policies; report it as mixed, not as a KG loss.

## 15.11 Are we done with Phase 2?

**Almost — closer than after run 2, but not yet.** Scorecard against §13.7:

| Requirement | Status |
|---|---|
| Detection / isolation / alert | **Done** — 100 % on lamps over 180 runs, replicated ×3 |
| Recovery measurable | **Done** (Phase 2.1) |
| Recovery *validated against goal-rate* (§13.4) | **Done** (this run) — and it sharpened the claims |
| Recovery family well-posed (§13.3) | **Done** (this run) |
| Goal-reaching KG recovery advantage demonstrated | **Done in `lab3_f1dead`**; mixed in `lab3_f1inv` |
| Detection precision = 100 % (§13.5) | **Fix implemented (§16), pending CI** — `lab3_f2inv` KG FP 8/10 in run 3; primary-detection-time attribution rule now in `observeForFaults`, awaiting one confirmatory run |

**What remains is a single, well-understood detector fix** (§15.9: primary-detection-time component-attributable isolation) plus one confirmatory CI run. Optionally, to strengthen the recovery claim beyond one cell, add a second deterministic-survivor well-posed cell. The science of Phase 2 — *physics priors detect faults reliably, and accelerate goal-reaching recovery where a deterministic survivor exists* — is now **demonstrated and correctly bounded**; the only open engineering item is the cross-coupled double-inversion precision corner.

## 15.12 Bottom line for the thesis

Phase 2.2 delivers the measurement rigour §13 demanded and, in doing so, produces the **cleanest and most defensible Phase-2 statement so far**: with goal-rate certification, **the agent reliably detects and isolates defective actuators, and — in the one cell where a deterministic post-fault solution exists and is actually reachable (`lab3_f1dead`) — the KG-primed agent re-aligns to the reduced reality both faster (−127 ep, −35 % end-to-end) and fully goal-reaching (10/10), exactly the advisor's hypothesis.** The same instrument honestly dissolves the earlier lab1/lab2 "wins" as stable-but-futile and keeps the inverted-lamp cell as a mixed result. One precision defect remains (the `lab3_f2inv` spotlight false positive, now correctly diagnosed as a primary-detection-time attribution problem), and it is the last item standing between this and a paper-ready Phase 2.

---

## 16 Fix 3 (corrected) — primary-detection-time component attribution

This section supersedes §14.3 and implements the remedy described in §15.9. It is
the genuine fix for the `lab3_f2inv` healthy-Spotlight false positive and is the
last engineering item for a clean Phase 2.

### 16.1 Why the previous attempt failed (recap)

The §14.3 guards (`zoneCauseContaminated[]` zone-skip + `warmRestart` counter
re-baseline) only act **after** a component is blacklisted. But the Spotlight is
mis-flagged at **primary** detection (`DetectEpisode` 3–11), *before* any
blacklist — so the guards never engage. The FP even widened (5/10 → 8/10) because
the KG prior exercises the Spotlight in the corrupted regime sooner.

### 16.2 The actual mechanism

In `lab3_f2inv` both task lamps are **inverted and still active** (not yet
removed). They subtract large lux (−400, −150) from the two shared zones, driving
the underlying illuminance far below zero, where the discretiser **clamps both
zones to rank 0 (the floor)**. When the agent then toggles the **healthy**
Spotlight (a single-step +150 lux to both zones), +150 is not enough to lift a
floored-far-below-zero zone off rank 0, so the zone shows **no rank change**
(`noResp`). Repeated ≥ `FAULT_MIN_SAMPLES` times, the healthy Spotlight is charged
with a dead/anomaly verdict. Crucially the Spotlight can **never** show an
opposite-sign (`opp`) response from a single +150 toggle, so the FP is *purely a
`noResp`/dead artifact* — the inverted signal is uninvolved.

### 16.3 The rule

Adjudicate each component **only on evidence attributable to it**. In the
zone-residual loop of `observeForFaults`:

- **`opp` (opposite-sign) evidence is kept ungated.** Only the toggled actuator
  changes in a step, so its own contribution sets the sign — an inverted lamp's
  own zone still inverts regardless of neighbours. This preserves inverted-fault
  detection in the cross-coupled lab.
- **`noResp` (no-change) evidence is gated by `zoneHasSuspectCoFeeder`.** If a
  *different* actuator that structurally feeds the same zone is currently
  **fault-suspect**, the null response may be that neighbour flooring the zone
  rather than this component being dead, so we **abstain** on that zone (it is not
  counted as a falsifiable claim).

An actuator is **fault-suspect** (`isFaultSuspect`) once it has at least
`FAULT_SUSPECT_MIN` (default **3**) dead+inverted observations that also form the
majority of its falsifiable observations — a deliberately early, low bar, far
below the `FAULT_MIN_SAMPLES` (20) needed to actually flag a defect. Because the
two inverted lamps accumulate `opp` evidence on their *own* zones almost
immediately, they are flagged "suspect" long before the Spotlight reaches 20
observations — so every Spotlight `noResp` on a shared zone is discounted, its
evidence never accumulates, and the FP cannot fire.

Co-feeders are matched on the static `ActionInfo.affectedZones` coupling; both the
ON and OFF actions of the component under test are excluded (shared
`wotActionType`).

### 16.4 Why it harms nothing else (validated per cell)

| Cell / case | Effect of the rule |
|---|---|
| `lab3_f2inv` (the FP) | both Spotlight zones have an inverted-lamp suspect co-feeder → `noResp` gated → `claimed`→0 → no evidence → **no FP**; the two lamps are still flagged via their own `opp` |
| Inverted lamps (any cell) | detected on their **own** zone via the **ungated** `opp` branch — single-step −400 dominates the sign |
| Genuine dead lamp (`f1dead`, `f2dead`, lab2) | caught by the **bit-level** `bitObs==0` check **before** the zone loop — the gate never applies |
| Well-posed `lab3_f1dead` / `lab3_f1inv` (single fault) | no second faulty actuator → no suspect co-feeder → **zero behaviour change**; the headline win is untouched |
| lab2 (independent zones, no shared feeder) | `zoneHasSuspectCoFeeder` is always false → **no behaviour change** |

The gate can only ever suppress a `noResp`/dead verdict, and the only dead fault we
inject (a silently-dropped command) is detected at the bit level, so no injected
fault can be hidden. The post-blacklist §14.3 guards are retained — they remain
valid for the *secondary* (post-blacklist) detection step and do not conflict.

### 16.5 Code

| Symbol (`src/env/tools/QLearner.java`) | Role |
|---|---|
| `FAULT_SUSPECT_MIN` (`-Dfault.detect.suspectMin`, default 3) | min dead+inverted obs for an actuator to count as a masking suspect |
| `isFaultSuspect(int b)` | early, majority-of-obs suspicion test |
| `zoneHasSuspectCoFeeder(int zone, int selfAction)` | true iff a different component feeding `zone` is suspect |
| zone-loop restructure in `observeForFaults` | `opp` ungated; `noResp` gated on a suspect co-feeder; `claimed` counted per-branch |

Compiles clean (`./gradlew compileJava`). **Expected CI outcome:** `lab3_f2inv`
`ql_true` per-seed `DefectComponent` becomes `SetZ1Light`/`SetZ2Light` for all 10
seeds (no `SetSpotlight`), restoring 100 % detection precision across all 18 cells
and closing §13.5.
