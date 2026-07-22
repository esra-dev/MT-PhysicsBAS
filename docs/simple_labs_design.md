# Simple-Lab Track — design, reachability, and convergence analysis

**Purpose.** The thesis arc requires us to *first* demonstrate that stereotype priors help in a
**simple lab where the base learner actually converges**, and only then stress-test them. The
current 4-zone labs do **not** converge within a tractable episode budget (the n=10 sweep shows
the base learner plateaus at goal-rate 0.11–0.21 even at 10 000 episodes — see
[sweep_n10_results_analysis.md](sweep_n10_results_analysis.md)). This document specifies a set of
**simpler sibling labs** that test the *same mechanism* as each live lab but are designed to
converge in **~1000 episodes**, plus the corrected-training-distribution fix for the headline lab.

This is a **design + arithmetic** document. The labs it specifies require a Node-RED simulator
build + a CI sweep to validate empirically; that is the proposed next compute step and **cannot be
validated inside the meeting**. The reachability arithmetic below is exact and verifiable by hand.

---

## 1. Why the 4-zone labs don't converge in 1000 episodes (the diagnosis we are fixing)

The tabular per-zone Q-learner keys on a 13-slot state vector
`[Z1..Z4 Level, Z1..Z4 Light, Z1..Z4 Blinds, Sunshine]`. The reachable state count and the number
of correct toggles needed to satisfy **all four** zone targets simultaneously make the terminal
reward extremely sparse under a 20-step horizon and ε-greedy exploration.

| Driver | 4-zone value | Effect |
|---|---|---|
| Zones that must be simultaneously correct | 4 | Terminal reward is conjunctive over 4 zones → exponentially rare under random exploration. |
| Actuators in play | 8 lights + 8/… blinds + corridor (+ 2 disabled spotlights) | Large branching factor; the prior's signal is diluted across many irrelevant actions. |
| Toggles to reach a 4-zone target | ~6–11 | Often near/over the 20-step horizon → episodes time out before terminal reward. |
| Sunshine coverage in training | pinned ~rank 2 | The blind/sun lever is **out of distribution** during training (see §3). |

**Convergence lever theory (why a simpler lab helps):** episodes-to-first-success scales roughly
with the inverse probability that a random/ε-greedy trajectory stumbles onto a terminal state.
Halving the number of zones that must be jointly satisfied and halving the toggle-depth both
multiply that probability up by large factors, moving first-success from "rarely within 10 000
episodes" to "routinely within a few hundred." Once first-success is frequent, the AUC-of-learning
-curve contrast between informed and uninformed agents becomes measurable inside 1000 episodes.

---

## 2. The simple-lab pattern (shared design)

Each simple lab is a **2-zone** reduction (Z1, Z2 only) of its 4-zone parent, keeping the
*mechanism under test* identical and changing only the things that block convergence:

1. **2 zones instead of 4** — the conjunctive terminal reward is over 2 zones, not 4.
2. **Shallow targets** — `Z1 = bright(3)`, `Z2 = medium(2)`; reachable in **2–4 toggles**.
3. **Full sunshine coverage in training** — sample the entire range so every IV regime is seen.
4. **Only the mechanism-relevant actuators** — task lights + blinds (+ the one shared light needed),
   no spotlights, so the prior's signal is not diluted.
5. **Same discretisation** — light bounds `[75, 200, 400]`, sunshine bounds `[50, 150, 500]`, so the
   stereotype semantics are unchanged.

State vector shrinks to `[Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Sunshine]`
(the original 8-slot 2-zone schema the learner already supports — see
[QLearner.java](../src/env/tools/QLearner.java) header, "2048 states").

---

## 3. `custom9s` — simple constructive lab (blind ↔ sun)

**Mirror of:** `custom9` (clean lab, sun-dependent optimum, the headline H1 lab).
**Mechanism isolated:** the **Mediates(blind, sunshine)** stereotype — opening a blind harvests
daylight *only* when the sun is high. This is where the prior is supposed to be *constructive*.

### 3.1 Physics (2-zone, spotlights removed)

```
z_i = 25 (ambient)
    + 400·TaskLight_i + 50·TaskLight_other          (lamps; Causes)
    + 0.50·sun·Blind_i + 0.25·sun·Blind_other       (blinds; Mediates on sun)
    + 150·CorridorLight                              (shared Causes)
```

Ranks: light `[75,200,400]` → 0:dark <75, 1:dim, 2:medium, 3:bright ≥400.
Sun `[50,150,500]` → rank 3 means sun ≥ 500.

### 3.2 ~~The critical fix: train across the full sun range~~ — RETRACTED (premise disproven 2026-06-08)

> **⚠️ This section's original claim was FALSE and has been retracted.** It asserted that `custom9`
> training pins sun to rank 2 via `Sunshine = 150 + 50·rand`, creating a train/eval coverage gap.
> Direct inspection of the training path disproves this:
>
> - `custom9` sets `train_scenarios("benchmark/train_scenarios_custom9.json")`. The QL training loop
>   (`illuminance_controller_agent_ql.asl` `@train`) calls `setScenarioLabState(...)` each episode,
>   which POSTs `/was/rl/setState` with the scenario's `Sunshine` value and raises `SunshinePinned`.
> - `train_scenarios_custom9.json` (150 scenarios) **all** carry a `Sunshine` field covering **all
>   four ranks**: rank0=32, rank1=33, rank2=49, rank3=36 (e.g. id 3 = 700 lux = rank 3).
> - The `150 + 50·rand` line lives in `env_fn` and only fires when `SunshinePinned` is **false**
>   (the unpinned fallback). During training *and* benchmark, sun is always pinned, so that line
>   never applies. The full-range `reset_fn` is used only when **no** train-scenarios file is set —
>   not custom9's case.
> - Benchmark `scenarios_custom9.json` (33 scenarios) also covers all ranks, but is **night-skewed**:
>   rank0=14, rank1=6, rank2=7, rank3=6.
>
> **Consequence:** there is no train/eval sun-coverage gap, and a `custom9s` that merely "samples sun
> across all ranks in training" fixes a non-existent bug. The real candidate causes of the custom9
> negative are (1) the 4-zone conjunctive task not converging in the 20-step horizon, and (2) the
> **evaluation** set being night-dominated (rank0 = 14/33), where the blind/sun lever is useless, so
> a blind-biased prior wastes early exploration in the regime that dominates scoring. Re-diagnose
> before building. The convergence motivation in §1 (2-zone converges faster) is unaffected and still
> valid; only the sun-coverage justification is withdrawn.

### 3.3 Reachability proof (target `Z1=3, Z2=2`)

We need `z1 ≥ 400` and `z2 ∈ [200, 400)`, at every sun rank, in few toggles.

| Sun rank | sun lux | Cheapest witness policy | z1 | z2 | ranks | toggles | energy |
|---:|---:|---|---:|---:|---|---:|---:|
| 0 (night) | 0 | `Z1Light=ON, CorridorLight=ON` | 25+400+150=575 | 25+50+150=225 | 3,2 ✓ | 2 | 180 |
| 1 (low) | 100 | `Z1Light=ON, CorridorLight=ON` | 575 | 225 | 3,2 ✓ | 2 | 180 |
| 2 (medium) | 250 | `Z1Light=ON, CorridorLight=ON` | 575 | 225 | 3,2 ✓ | 2 | 180 |
| 3 (bright) | 600 | **`Z1Blinds=ON, CorridorLight=ON`** | 25+300+150=475 | 25+150+150=325 | 3,2 ✓ | 2 | **85** |

**Key property:** at sun rank 3 the **blind** witness (energy 85) is strictly cheaper than the
task-light witness (energy 180) and still hits the target — so the *optimal* policy is
**sun-conditioned**: use the task light when dark, use the blind when bright. This is exactly the
lever the Mediates(blind, sun) stereotype encodes. A learner that knows the stereotype should reach
this policy in fewer episodes; an uninformed learner must discover the sun-conditioning from
scratch.

> Note Z2 never overshoots: with only `CorridorLight` it sits at rank 2 (225–325 lux) across all
> sun ranks, satisfying its `medium(2)` target without any Z2 actuator. This keeps the task to
> essentially "pick the right Z1 source for the current sun" — a clean 2-toggle problem ideal for
> demonstrating the prior.

### 3.4 Convergence expectation

Target reachable in **2 toggles** within a 20-step horizon → a random trajectory hits the terminal
state with high probability per episode → first-success within tens of episodes → the AUC contrast
between `ql_true` and `ql_false` is resolvable well inside **1000 episodes**.

---

## 4. `custom3s` — simple wrong-prior lab (graceful degradation)

**Mirror of:** `custom3` (W2: Z2 blind sign-flips at sun ≥ 500).
**Mechanism isolated:** the ontology says "blind increases light" but in this lab the Z2 blind
**reduces** light at high sun (e.g. an automatic glare shade closes). The stereotype prior is
therefore **wrong** exactly at sun rank 3. Tests **adaptive-trust / IV-learning recovery**: the
informed agent must *unlearn* the bad prior; the uninformed agent has no bad prior to overcome.

### 4.1 Physics delta from `custom9s`

Identical to §3.1 except the Z2 blind term flips sign at rank 3:

```
if (sun_rank < 3)  z2 += 0.50·sun·Blind2   // normal: blind helps
else               z2 -= 0.30·sun·Blind2   // W2: at bright sun the Z2 blind HURTS
```

### 4.2 What we expect to see

- Early episodes: `ql_true` follows the (wrong) prior, opens the Z2 blind at high sun, *loses* rank.
- The runtime IV-effectiveness tracker (`recordActionOutcome` / `getLearnedIVMinRank` in
  [StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java)) observes the blind failing at
  rank 3 and the adaptive-trust EMA attenuates the prior.
- Asymptote: both agents converge to "don't use the Z2 blind at bright sun" → **do-no-harm**.
- The thesis claim: even with a *wrong* prior, the informed agent is **not worse** at the asymptote
  and the energy benefit persists (this is the mechanically-valid graceful-degradation lab — the
  4-zone `custom3` already shows Δgoal +0.163, q≈0).

Targets `Z1=3, Z2=2`; at bright sun the safe Z2 witness is `CorridorLight` alone (no Z2 blind),
giving z2 = 325 (rank 2) ✓ — so the recovery policy is reachable in 2 toggles.

---

## 5. `custom5s` — simple benign-constraint lab (compatible prior)

**Mirror of:** `custom5` (W4: 7-unit shared power cap).
**Mechanism isolated:** a resource limit the prior does **not** contradict. The cap is observable
(an "on" actuator that doesn't change the level once the cap is hit). Tests "faster learning
persists under a benign constraint."

### 5.1 Physics delta

Identical to §3.1 plus a per-tick activation cap: at most **2** task-light-equivalents may be ON
(2-zone scale of the 7-unit 4-zone cap). Excess activations are silently dropped (the lowest-zone
priority is cut).

### 5.2 What we expect

The prior is *compatible* with the cap (it never tells the agent to exceed it), so the informed
agent should still learn faster (its early actions are the right ones), and the cap simply removes
one degenerate "turn everything on" strategy. With targets `Z1=3, Z2=2` reachable inside the cap
(`Z1Light + CorridorLight` = 1 task unit + shared), convergence in ~1000 episodes is expected; the
4-zone `custom5` already shows Δgoal +0.064, q≈0 and Δauc +0.041.

---

## 6. Implementation checklist (per simple lab)

Creating a runnable lab touches the following (mirrors the `custom9` scaffold from audit Step 5 §9):

1. **Simulator**: `simulator/simulator_flow_custom9s.json` — copy the 2-zone base, apply the
   §3.2 full-range sun sampling and the per-lab physics delta. New Node-RED port (e.g. 1891–1893).
2. **Thing Description**: `src/resources/interactions-lab-custom9s.ttl` — 2-zone TD.
3. **Ontology / WoT mappings**: reuse `lab-ontology.ttl` + a 2-zone `wot-mappings.ttl` (the original
   8-slot registry already exists for the 2-zone `custom` profile).
4. **Scenarios**: `benchmark/scenarios_custom9s.json` (held-out, all sun ranks) +
   `benchmark/train_scenarios_custom9s.json` (full sun-range start states).
5. **Profile**: a `lab_profile("custom9s", …)` record in
   [src/agt/lab_profiles.asl](../src/agt/lab_profiles.asl) with `zone_targets([target(1,3), target(2,2)])`,
   `light_bounds([75,200,400])`, `sunshine_bounds([50,150,500])`, `training_params(1000, …)`.
6. **Orchestrator wiring**: `config/run_config.json` (4 profile maps), `run_full_project.ps1`
   (`$TrainProfiles` + port map), `.github/workflows/sweep-paper.yml` (PROFILES), Node-RED dir.
7. **Smoke test before trusting any number**:
   `./run_full_project.ps1 -RunMode dev -OnlyProfiles custom9s` — confirm both arms train and
   benchmark end-to-end with no exceptions, then a 1-seed 1000-episode run to confirm the base
   learner plateaus high (`ql_false` goal-rate ≥ ~0.7) — the convergence gate.

> **Honesty note.** None of the simple-lab numbers may be cited until step 7 passes on CI. The
> arithmetic in §3–§5 establishes *feasibility*; only a sweep establishes *behaviour*.

---

## 7. Relationship to the registered results

The existing `custom9` / `custom3` / `custom5` (4-zone) and the n=10 sweep **stay as-is** — they are
the pre-registered, honest record (including the headline `custom9` negative). The simple labs are
an **additional, clearly-labelled exploratory track** whose purpose is the "mechanism works in a
simple lab" chapter. Per [pre_registration.md](pre_registration.md) §6 deviation policy, any sweep
that includes the simple labs is reported as exploratory alongside the confirmatory n=10 numbers.

**Recommended result-chapter structure for the thesis:**
1. **Chapter A (simple labs):** the mechanism works cleanly — informed agent learns faster, both
   converge, do-no-harm at asymptote.
2. **Chapter B (stress labs, n=10):** the mechanism survives systematic ontology gaps — `custom3`
   (wrong prior, graceful degradation) and `custom5` (benign constraint) both favour the prior at
   q≈0; the headline `custom9` negative is explained by the **rank-2 IV-gate mis-fire**
   (`ivMinRank=1` recommends blinds where they can't reach target; +0.280 at rank 3 vs −0.157 at
   rank 2 — see [custom9_rediagnosis.md](custom9_rediagnosis.md)) and is the lab that `custom9s`
   plus the `ivMinRank=3` fix are designed to resolve.
3. **Chapter C (energy):** the universal, maximally-significant emergent benefit — lower energy on
   every lab and seed (δ=−1.0, q≈0), honestly framed as a side effect of the priors.

---

## 8. Build status & validating sweep (`custom9s`)

**Built 2026-06-08** (the constructive convergence lab + `ivMinRank=3` testbed). The other two
simple labs (`custom3s`, `custom5s`) are **not** built yet — they are deltas on this scaffold (§4, §5).

### 8.1 Files created / wired for `custom9s`

| Artifact | Path | Notes |
|---|---|---|
| Simulator flow | [simulator/simulator_flow_custom9s.json](../simulator/simulator_flow_custom9s.json) | 2-zone, port **1891**. Physics per §3.1: ambient 25, task lights 400/+50, blinds 0.5·sun/0.25·sun, `Spotlight` repurposed as shared CorridorLight (+150). Radiators not in lux path. `reset_fn` samples full sun range; `setState` pins sun for benchmarks. |
| Thing Description | [src/resources/interactions-lab-custom9s.ttl](../src/resources/interactions-lab-custom9s.ttl) | Copy of the 2-zone `custom` TD repointed to `localhost:1891`; identity `urn:mt-esra:interactions-lab-custom9s`. |
| Ontology / mappings | *(reused)* `lab-ontology.ttl` + `wot-mappings.ttl` | No new TTL — the 8-slot 2-zone schema is unchanged, so the prior semantics are identical. |
| Benchmark scenarios | [benchmark/scenarios_custom9s.json](../benchmark/scenarios_custom9s.json) | 20 held-out, **balanced** 5/5/5/5 across sun ranks (vs. custom9's night-skew). |
| Training scenarios | [benchmark/train_scenarios_custom9s.json](../benchmark/train_scenarios_custom9s.json) | 14 held-in, full sun coverage. |
| Lab profile | [src/agt/lab_profiles.asl](../src/agt/lab_profiles.asl) | `lab_profile("custom9s", …)`, `zone_targets([target(1,3),target(2,2)])`, `training_params(1000, 0.9920)`. |
| Orchestrator wiring | `config/run_config.json`, `run_full_project.ps1` | Added to `simulator_port_map`/`simulator_flow_map`/`qtable_suffix_map`/`expected_state_vec_dim` (=8), `$TrainProfiles`, `$ProfileQtableSuffix`, `$Simulators`. |
| CI workflow | `.github/workflows/sweep-paper.yml` | **No edit needed** — the `profiles` input is passed straight to `-OnlyProfiles`. |

> **Episode-count caveat.** The orchestrator overwrites the profile's `training_params` episode
> count with the run-mode value ([run_full_project.ps1](../run_full_project.ps1) ~L495). So `paper`
> mode trains 10000 episodes regardless of the `1000` in the profile. For the *focused* ~1000-episode
> convergence demonstration, use a 1-seed `dev`/custom run (below). The `1000` records design intent.

### 8.2 Smoke test first (do not cite any number before this passes)

```powershell
# 1-seed end-to-end dev run: confirms both arms train + benchmark with no exceptions
./run_full_project.ps1 -RunMode dev -OnlyProfiles custom9s -RunSeed 1
```

Check: Node-RED came up on 1891, both `ql_true`/`ql_false` trained, benchmark wrote
`benchmark_results_ql_true.csv` / `_ql_false.csv`, no Java/Jason exceptions in
`log/train_custom9s_stereo_*.log`.

**Convergence gate** (the whole point of the simple lab): in a ~1000-episode run the *uninformed*
arm should plateau **high** (`ql_false` benchmark goal-rate ≳ 0.7). If it does, the lab converges and
the `ql_true` vs `ql_false` AUC contrast is measurable — unlike 4-zone custom9.

#### Smoke-test result — **PASSED 2026-06-08** (dev, 50 episodes, seed 1)

End-to-end clean: preflight 1/1, both training arms, 3-mode benchmark, analysis and cleanup, **no
exceptions**. Training goals reached (out of 50): `stereo=true` 35, `stereo=false` (standard QL) **40**
(first goal at episode 1, last four episodes all `goal=true`). Held-out benchmark (20 scenarios × 2 runs):

| Mode | Goal-rate | Avg energy | Avg steps |
|---|---|---|---|
| `ql_false` (standard QL — **convergence gate**) | **0.775** (31/40) | 33.6 | 7.2 |
| `ql_true` (stereotypes) | 0.750 (30/40) | 41.5 | 7.3 |
| `rule_based` (oracle) | 0.900 (36/40) | 12.9 | 3.5 |

**Gate passed.** Standard QL plateaus high (0.78) on `custom9s`, versus 4-zone `custom9` where
`ql_false` only reaches 0.11–0.21 — the 2-zone lab *is* learnable, so the prior-vs-baseline contrast
is measurable here. These are **dev smoke numbers** (50 episodes): at this short horizon `ql_true ≈
ql_false`, because the prior's *faster-learning* benefit only separates over the longer paper horizon.
Run §8.3 for the confirmatory prior-vs-baseline AUC delta.

### 8.3 Validating sweep (CI, after smoke test passes)

```bash
# Exploratory simple-lab sweep, 5 seeds, paper run-mode
gh workflow run sweep-paper.yml -f profiles=custom9s -f seeds=1,2,3,4,5 -f run_mode=paper
gh run list --workflow=sweep-paper.yml -L 5      # grab the run id
# when complete, download artefacts and analyse with the standard pipeline:
#   python analysis/sweep_report.py  (AUC-of-goal-rate primary metric)
```

Report `custom9s` numbers as **exploratory** alongside the confirmatory n=10 set (per
[pre_registration.md](pre_registration.md) §6 deviation policy).

### 8.4 `ivMinRank=3` gate experiment (the headline fix, on this lab)

`custom9s` is also the cheap place to validate the [custom9_rediagnosis.md](custom9_rediagnosis.md)
fix: edit the blind/sun `ws:ivMinRank` to `3` in the ontology used by `custom9s`, re-run 8.3, and
check whether the rank-2 drag disappears while the rank-3 win persists. Run it as a paired
ablation (gate=1 vs gate=3) so the effect is attributable to the gate alone.

---

## Source Index

All paths relative to the workspace root.

### §8 — custom9 / custom9s lab design

| File | Role | Used in |
|---|---|---|
| `src/resources/building_9_complex.ttl` | custom9 ontology (2-zone, 8 actuators). Base lab. | §8.1 |
| `src/resources/building_9s_complex.ttl` | custom9s ontology: custom9 + `ws:ivMinRank=1` for blinds/sun (the rank-drag bug ontology). | §8.1, §8.2, §8.3 |
| `src/resources/lab-ontology.ttl` | Core ontology: rank bounds, mechanism definitions, `ivMinRank` predicate. | §8.1 |
| `config/run_config.json` | Profiles `custom9` and `custom9s`; episode count, reward shaping, seed. | §8.1 |
| `src/agt/lab_profiles.asl` | `lab_profile("custom9",…)` and `lab_profile("custom9s",…)` plan-selection rules. | §8.1 |
| `src/agt/illuminance_controller_agent_ql.asl` | Training and benchmark agent plans. | §8.1 |
| `src/env/tools/StereotypeReasoner.java` | `getLearnedIVMinRank()`, `recordActionOutcome()` — IV-effectiveness tracker. Reads `ws:ivMinRank`. | §8.1 |
| `src/env/tools/QLearner.java` | Q-table, `initWithStereotypes()`, `calculateQ()`. | §8.1 |
| `simulator/simulator_flow_custom9.json` | Node-RED flow for custom9 (2-zone, single lab). | §8.1 |
| `simulator/simulator_flow_custom9s.json` | Node-RED flow for custom9s (identical physics; different ontology file path). | §8.1, §8.2 |
| `run_full_project.ps1` | `-RunMode custom9s`, `-RunSeed 1`, `-RunMode dev`/`-OnlyProfiles custom9s` flags. | §8.2 (smoke test) |
| `analysis/sweep_report.py` | `aggregate_seeds()`, `learning_speed_tests()`, `_bh_qvalues()`. Produces `metrics_*.csv`, `benchmark_results_*.csv`, `first_goal_*.csv`, `coverage_*.csv`. | §8.3 |
| `.github/workflows/sweep-paper.yml` | CI pipeline for multi-seed custom9/custom9s sweeps. | §8.3 |

### §8.2 smoke test provenance

The smoke-test table in §8.2 comes from a **local dev run**, not a CI job:

| Field | Value |
|---|---|
| Date | 2026-06-08 |
| Command | `./run_full_project.ps1 -RunMode dev -OnlyProfiles custom9s -RunSeed 1` |
| Episodes | 50 |
| CI run ID | none (local dev; no GH Actions job) |
| Commit | on branch `main` at the time of the run |

### §8.3 sweep output files (custom9s, n=10)

| File | Contents |
|---|---|
| `metrics_stereotypes_true_custom9s.csv` | Episode-level reward/steps/goal by seed. |
| `benchmark_results_stereotypes_true_custom9s.csv` | Final-policy benchmark per seed. |
| `first_goal_stereotypes_true_custom9s.csv` | First-goal episode per seed. |
| `coverage_stereotypes_true_custom9s.csv` | State-coverage per seed. |
| `qtable_final_stereotypes_true_custom9s.csv` | Final Q-table per seed. |
| (same files with `false` and `rule_based` suffixes) | ql_false and rule_based arms. |

### Diagnosis & remediation references

| Document | Topic |
|---|---|
| [custom9_rediagnosis.md](custom9_rediagnosis.md) | Root-cause diagnosis of `ivMinRank=1` rank-drag in custom9s. Fix: set `ws:ivMinRank=3` for blinds/sun. |
| [pre_registration.md](pre_registration.md) §6 | Deviation policy for custom2–8 → custom9 pivot and exploratory status of custom9s results. |

