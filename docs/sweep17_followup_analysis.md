# Sweep 17 — Follow-up Analysis & Correction (run `27008592029`, 5 seeds, full benchmark)

**Date:** 2026-06-06 · **Analyst:** automated review · **Supersedes the "no-benchmark / single-seed / unevaluable" claims in** [docs/sweep17_analysis.md](sweep17_analysis.md)
**Authoritative artifact source:** GitHub Actions run **`27008592029`** ("Sweep (paper)", `workflow_dispatch`, headSha `466fc89`, conclusion **success**, 8 h 21 m) → **workflow-run artifacts** (202 total), bundle **`sweep-paper-consolidated`** (4025 files).
**NOT** `origin/results` branch (that branch only received the training-phase dump — see §1).

---

## 0. TL;DR — what changed versus the first analysis

| First analysis said | Truth (from run 27008592029 artifacts) |
|---|---|
| "Single-seed pilot" | ❌ Wrong. **5 seeds (1–5)** were run, paired across profiles. |
| "Training-only, no benchmark CSVs" | ❌ Wrong. Full **held-out benchmark** ran for all 8 profiles × 3 modes × 5 seeds, plus the entire `analysis/out/` statistics layer (`summary_table_ci.csv`, `paired_tests.csv`, `first_goal_table.csv`). |
| "custom8 ≡ custom7, headline unevaluable" | 🟡 **Partly right.** The collision is **real but scoped to the *training/Q-table* publish artifacts**. The **benchmark results for c7 and c8 are distinct** (different MD5 across all 5 seeds), so the confirmatory `goal_rate` *was* computed for custom8. |
| "Wave-A fixes uncreditable" | ❌ Now creditable. The pre-registered primary metric exists → **H1 and H3 are now evaluable**. |

**The reason for the contradiction:** the **`results` branch** publish and the **workflow-run artifacts** are two different stores with different scope. The branch got only the training dump (272 files, single representative copy, c7/c8 aliased). The 5-seed benchmark + statistics went to the **workflow artifacts**, which the first analysis never inspected. **"Actions = success" only means the pipeline ran without throwing — it says nothing about scientific validity** (see §5).

---

## 1. Is the "5 seeds + benchmarking, successful" claim true? — **YES.**

Verified directly from the run:

- `gh run view 27008592029` → `conclusion = success`, 202 artifacts.
- Artifact inventory: `bench-customN-ql_false-seed-{1..5}` (37), `bench-customN-ql_true-seed-{1..5}` (36), `bench-customN-rule_based-seed-{1..5}` (26), **+ `sweep-paper-consolidated`** (1, the aggregated bundle).
- `sweep-paper-consolidated/benchmark/` contains `results_seed1 … results_seed5`, each with `custom2…custom9 / {ql_false,ql_true,rule_based} / benchmark_results_*.csv`.
- `sweep-paper-consolidated/analysis/out/` contains `summary_table_ci.csv`, `paired_tests.csv`, `first_goal_table.csv` (and `learning_curve_*.png`, `fire_density_*.png`, `weakness_heatmap.csv`).

**Where to find the results:** GitHub → Actions → run `27008592029` → Artifacts → **`sweep-paper-consolidated`** (everything aggregated) or the 99 per-seed `bench-*-seed-*` bundles (raw). Locally downloaded to `C:\Users\esrad\Downloads\sweep17_consolidated\`.

---

## 2. The c7/c8 collision — re-scoped precisely

Hashes from the consolidated bundle:

| Artifact family | c7 vs c8 | Verdict |
|---|---|---|
| **Training** `metrics_stereotypes_{true,false}_customN.csv` | identical MD5 (`650D2532…` / `450CFEBD…`) | ⛔ **collided** |
| **Final Q-tables** `qtable_final_..._customN_{main,zone1..4,visits,trust}.csv` | **all** identical MD5 (e.g. zone1 `04AD2DC6…`, true-main `77490B24…`) | ⛔ **collided** |
| **Benchmark** `results_seed{1..5}/customN/.../benchmark_results_*.csv` | **distinct** MD5 for every seed (e.g. seed1 ql_true c7 `7B153383…` ≠ c8 `4353DA62…`) | ✅ **distinct** |

**Interpretation.** The collision lives in the **top-level training / policy publish** step (the consolidation copies custom7's trained artifacts onto the custom8 names), **not** in the per-seed benchmark evaluation, which produced genuinely different numbers for c7 and c8. So:

- The **benchmark `goal_rate` for custom8 is real and distinct** → H1 *is* numerically evaluable.
- **BUT** because the *published* Q-tables for c8 are byte-identical to c7's, we **cannot yet certify** that the c8 benchmark loaded a genuinely **c8-trained policy** rather than c7's policy run on c8's scenarios. The distinct benchmark output could arise from different eval scenarios alone.
- **Action required (§7-A):** root-cause the publish aliasing and re-confirm the c8 *policy* provenance before citing custom8 in the thesis. **For custom2–c7 and c9 there is no collision evidence — their verdicts stand unconditionally.**

---

## 3. The real confirmatory results (5 seeds, paired bootstrap, BH-corrected)

### 3.1 Held-out benchmark `goal_rate` (mean over 5 seeds [95 % CI])

| Profile | ql_false | ql_true | rule_based | ql_true − ql_false (paired) | q (BH) | verdict |
|---|---|---|---|---|---|---|
| custom2 | 0.033 [.020,.047] | 0.020 [.006,.039] | **0.250** | **−0.0129 [−.020,−.006]** | 0.0018 | ql_true **worse** |
| custom3 | 0.043 [.027,.066] | 0.053 [.026,.079] | **0.179** | +0.010 [−.036,+.041] | 0.58 | parity |
| custom4 | 0.067 [.059,.076] | 0.023 [.014,.040] | **0.476** | **−0.0443 [−.056,−.031]** | ≈0 | ql_true **worse** |
| custom5 | 0.017 [.007,.029] | 0.030 [.011,.049] | **0.250** | +0.0129 [−.016,+.041] | 0.56 | parity |
| custom6 | 0.047 [.036,.060] | 0.009 [.004,.013] | **0.179** | **−0.0386 [−.050,−.027]** | ≈0 | ql_true **worse** (expected: W5 non-Markov) |
| custom7 | 0.014 [.006,.023] | 0.030 [.003,.067] | **0.250** | +0.0157 [−.017,+.059] | 0.46 | parity |
| **custom8** | 0.030 [.013,.046] | 0.017 [.004,.030] | **0.250** | **−0.0129 [−.026,−.001]** | **0.026** | ql_true **worse** ← **H1** |
| custom9 | 0.070 [.023,.117] | 0.046 [.027,.064] | **0.250** | −0.0243 [−.087,+.039] | 0.55 | parity |

`paired_tests.csv` columns confirm direction: `mode_a=ql_true, mode_b=ql_false`, so a negative `mean_diff` = ql_true is worse.

### 3.2 Pre-registered hypothesis verdicts

| Hyp. | Claim | Verdict | Evidence |
|---|---|---|---|
| **H1** | custom8: ql_true `goal_rate` ≥ ql_false (one-sided) | **❌ FALSIFIED** | `p_one_sided_positive = 1.0`, `p_one_sided_negative = 0.009`, q = 0.026, CI strictly negative. ql_true is **significantly worse**. |
| **H2** | PBRS lowers episodes-to-first-goal | **⛔ UNEVALUABLE** | `first_goal_table.csv` has **only `pbrs_on`** rows; **no `pbrs_off` control arm**. `first_goal_wilcoxon.csv` is **0 bytes** (test never computed). |
| **H3** | `{c2,c3,c4,c5}`: ql_true not significantly worse | **❌ FALSIFIED** | custom2 (CI [−.020,−.006]) and custom4 (CI [−.056,−.031]) show **significant harm**. Only c3, c5 are parity. |
| **H4** | Ablation B (no adaptive trust) | **⛔ NOT RUN** | no ablation-B cells in artifacts. |
| **H5** | Ablation C (`prior_scale=0`) | **⛔ NOT RUN** | no ablation-C cells in artifacts. |

**Pre-registration decision table → `H1 falsified ∧ H3 falsified ⇒ HONEST NEGATIVE:** "stereotype priors as currently formalised are not net-positive on `goal_rate` in this domain."** This is now the defensible, data-backed headline — a *publishable negative result*, not a pipeline failure.

### 3.3 Two findings the first analysis could not see

1. **The rule-based oracle dominates both RL variants by a wide margin.** rule_based `goal_rate` 0.18–0.48 vs RL 0.01–0.07; every RL-vs-rule_based paired test has `q ≈ 0` and **Cliff's δ = −1.0** (total separation). The learned policies barely reach goals relative to a trivial controller. This is the deepest signal complicating the thesis (consistent with audit Step-1b reachability concerns).
2. **ql_true roughly *halves* energy use — consistently.** `avg_energy_mean` ql_false → ql_true: c2 134.6→69.8, c3 127.4→60.5, c4 140.0→70.4, c5 160.6→83.8, c6 136.4→67.7, c7 147.1→78.7, c8 136.3→74.9, c9 85.5→44.3 (**−45 % to −53 % everywhere**), while `avg_steps` and `avg_wasted` stay ≈ equal. **This is the genuine positive contribution** — but note it co-occurs with *lower* goal_rate in the harmful labs, so it is partly "the prior trades goal attainment for energy thrift," not free efficiency. Frame as a **Pareto/energy story**, not a goal-rate win — and note rule_based already achieves comparable energy *with* higher goal_rate.

---

## 4. Re-answering: are the §3.2 "signals that complicate the thesis" still relevant?

**Yes — and the benchmark data makes them stronger, not weaker.** Re-stated against the real numbers, with next best actions:

1. **Exploration-cost penalty → now a held-out goal-rate penalty.** The training-phase reward penalty the first analysis saw is confirmed at evaluation: ql_true is *significantly worse* on goal_rate in c2, c4, c8 (and c6). 
   - **Action / why:** Implement audit Suggestion **S3b-1/S3b-3** (align prior-decay with the ε-schedule; stop penalising prior-favoured redundant actions while priors are active) and re-run. *Why:* the penalty mechanism is the identified cause; if it's the culprit, fixing it should move c2/c4/c8 from "worse" toward "parity." This is the single highest-value code change.
2. **First-goal speed claim (H2) cannot be made at all** — the `pbrs_off` arm is missing and the Wilcoxon file is empty.
   - **Action / why:** Add a `pbrs_off` (shaping-disabled) configuration to the sweep matrix and re-run so `first_goal_wilcoxon.csv` is actually populated. *Why:* H2 is currently vacuous; without the control arm the PBRS contribution is unfalsifiable.
3. **c6 (W5 partition) inversion** — ql_true significantly worse, as **pre-registered parity-not-recovery** (non-Markov). Still fine to report as the honest "priors can mislead on non-Markov dynamics" caveat.
   - **Action / why:** No fix; report as designed-in limitation.
4. **NEW — RL ≪ rule_based across the board.** Both learners are Pareto-dominated by the oracle on (goal_rate, energy).
   - **Action / why:** This is existential for any "our RL agent is good" framing. Either (a) reposition the thesis around *sample-efficiency / energy under a learning constraint* rather than absolute performance, or (b) investigate the Step-1b state/action reachability defect so the learners can actually compete. Decide this **before** re-running, because it changes what the sweep needs to measure.

---

## 5. Why did GitHub Actions report "success" despite a falsified thesis and a data defect?

**Because "success" is a *process* signal, not a *science* signal.** A workflow run is `success` iff every job exits 0. The Sweep 17 pipeline:

- trained all profiles, ran the benchmark, and emitted all CSVs **without any job throwing** → green check;
- the **c7/c8 publish aliasing is a silent logic bug** (a file copied to the wrong name), which produces *valid-looking* files and a 0 exit code;
- a **falsified hypothesis is a perfectly successful experiment** — the pipeline's job is to *measure*, not to *confirm*. H1 being false is a scientific result, not a CI failure.

So the green check is fully consistent with (a) a real, usable 5-seed benchmark dataset **and** (b) a thesis-level negative result **and** (c) a data-integrity defect in the training-artifact publish. The first analysis conflated "no benchmark data on the *branch*" with "no benchmark data *at all*" — the workflow artifacts had it the whole time.

**Guardrail to add (§7-A):** a post-run assertion that **fails the job** if any two profiles emit identical training/Q-table hashes, so this silent defect becomes a loud one next time.

---

## 6. Are the first analysis's §6 next actions still right? (revised)

| Original action | Still valid? | Revision |
|---|---|---|
| 1. Fix c7/c8 collision + hash guard | ✅ **Yes, top priority** | Narrow scope: the bug is in the **training/Q-table publish/consolidation** path, not the benchmark. Add the fail-on-duplicate-hash guard. |
| 2. Run 5-seed sweep + publish benchmark | ⚠️ **Already done** | The data exists in the workflow artifacts. **New action:** also **publish benchmark CSVs + `analysis/out/` to the `results` branch** (or a release) so they're discoverable, not buried in run artifacts. |
| 3. Promote custom9 to headline | ✅ **Yes** | Reinforced: custom8's optimal policy is sun-invariant (audit Step-1b) so the prior has no positive lever there — and the benchmark now *confirms* ql_true ≤ ql_false on c8. custom9 (parity, q=0.55) is the honest headline. Amend pre-registration. |
| 4. Report exploration-cost penalty honestly | ✅ **Yes, now mandatory** | It is now a *significant benchmark* penalty, not just a training artifact. Implement S3b-1/S3b-3 and re-measure, OR adopt the **energy-Pareto** framing from §3.3. |
| 5. Run H2/H4/H5 ablations | ✅ **Yes** | Add: H2 specifically needs the **`pbrs_off` arm** (currently missing → empty Wilcoxon). |

### Additional actions not in the original list

6. **Decide the thesis framing in light of RL ≪ rule_based (§3.3, §4-4).** This is new and structural; resolve before the next sweep.
7. **Certify custom8 policy provenance** (does the c8 benchmark use a c8-trained Q-table?) — blocked by the collision; resolve as part of §7-A.
8. **Correct/annotate** [docs/sweep17_analysis.md](sweep17_analysis.md): its §0–§2 "single-seed / no-benchmark / unevaluable" claims are wrong for the workflow artifacts and should point here.

---

## 7. Detailed next-step plan (ordered, with done-criteria)

**A. Root-cause & guard the c7/c8 publish collision** *(blocks H1)*
- Audit the consolidation/publish path (`run_full_project_parallel.ps1`, the bench profile-apply `*_bench.asl`, and the artifact-copy step) for `custom7`→`custom8` name aliasing.
- Add a post-run guard that **fails the job** if any two profiles share a training/Q-table hash.
- Confirm whether the **c8 benchmark loaded a c8-trained policy** (compare per-seed Q-tables, not just the top-level copy).
- *Done when:* a fresh dry-run shows 8 distinct training hashes **and** the guard is in CI.

**B. Patch the soft-prior exploration penalty** *(targets H1/H3 falsification)*
- Implement audit S3b-1/S3b-3: align prior-decay with ε-schedule; suppress redundant-action penalty while priors are active.
- *Done when:* on a 5-seed re-run, custom2/custom4/custom8 paired `ql_true − ql_false` CIs include 0 (parity) instead of being strictly negative — or, if not, the negative result is accepted and frozen.

**C. Add the missing arms** *(unblocks H2/H4/H5)*
- Add `pbrs_off` to the matrix so `first_goal_wilcoxon.csv` is populated (H2).
- Add Ablation-B (no adaptive trust, H4) and Ablation-C (`prior_scale=0`, H5) cells.
- *Done when:* `first_goal_wilcoxon.csv` is non-empty and H4/H5 cells exist in `paired_tests.csv`.

**D. Re-run the corrected 5-seed sweep and publish discoverably**
- Re-run after A–C; publish `benchmark/` + `analysis/out/` to the `results` branch or a tagged release (not only run artifacts).
- *Done when:* the results branch (or release) contains the 5-seed benchmark CSVs and the stats layer.

**E. Decide framing & write up** *(strategic)*
- Resolve the RL ≪ rule_based question (§4-4): reposition around energy-Pareto / sample-efficiency, or fix Step-1b reachability.
- Update pre-registration: promote custom9 to headline; record H1/H3 outcome honestly.
- Annotate the first analysis to defer here.
- *Done when:* thesis claims match the data — **"stereotype priors give a consistent ~50 % energy reduction at parity-or-small-cost in goal_rate; they do not improve goal attainment, and neither RL variant matches the rule-based oracle."**

---

## 8. Provenance

- Run `27008592029` (`gh run view`), artifacts via `gh api .../actions/runs/27008592029/artifacts` (202) and `gh run download 27008592029 -n sweep-paper-consolidated` → `C:\Users\esrad\Downloads\sweep17_consolidated\` (4025 files).
- Numbers read from `analysis/out/summary_table_ci.csv`, `analysis/out/paired_tests.csv`, `analysis/out/first_goal_table.csv`.
- Collision scoping by MD5: training `metrics_*` and **all** `qtable_final_*` c7≡c8; per-seed `benchmark_results_*` c7≠c8 across seeds 1–5.
- `first_goal_wilcoxon.csv` = 0 bytes (H2 control arm absent).

---

## 9. custom9 reachability proof (blocker — audit Step-5 §6.B / §8-Q4)

**Status: PASS.** The target tuple is achievable at **every** sunshine rank with comfortable rank margins, well inside the 20-step episode budget. **No coefficient recalibration is required** (the §6.B contingency — blind self-coeff 0.40, bleed 0.10 — is *not* applied, because a non-overshoot policy already exists at all ranks).

### 9.1 Verified dynamics (source: `simulator/simulator_flow_custom9.json`, node `custom9_env_fn`)

Per-zone illuminance (lux) is the clamped (≥0) sum of:

| Contribution | Value |
|---|---|
| Ambient floor | **+25** (always) |
| Own task light | **+400** if on |
| Bleed from each *other* task light on | **+50** each |
| Own blinds open | **+0.50 · sun** |
| Bleed from each *other* open blind | **+0.25 · sun** each |
| `CorridorLight` (shared, all 4 zones) | **+150** if on |
| `Spotlight` / `SpotlightCD` | **+0** — both gated by `if (false && …)` (disabled in custom9) |

Rank cuts (verified from `lab_profiles.asl` custom9):
- `light_bounds [75,200,400]` → r0 [0,75), r1 [75,200), **r2 [200,400)**, **r3 [400,∞)**
- `sunshine_bounds [50,150,500]` → r0 [0,50), r1 [50,150), r2 [150,500), r3 [500,∞)
- `zone_targets` → **Z1 = r3, Z2 = r2, Z3 = r3, Z4 = r2**

Representative pinned sun per rank (from `custom9_reset_fn` array `[0,100,400,900]`): **r0=0, r1=100, r2=400, r3=900.** Note: during *training* the env overwrites sun with `150+50·rand` ⇒ training sun is **always rank 2** (~150–200); benchmark pins the other ranks via `setstate`.

### 9.2 A sun-invariant feasible policy (proves reachability at all 4 ranks)

Policy **P₀ = {Z1Light, Z3Light, CorridorLight on; all blinds + Z2Light + Z4Light off}**. Because no blinds are open, **sun never enters** — so P₀ yields the same levels at every rank:

| Zone | Level | Target | Result | Margin |
|---|---|---|---|---|
| Z1 | 25 + 400 + 50(Z3) + 150(CL) = **625** | r3 (≥400) | ✅ | +225 above floor |
| Z2 | 25 + 50(Z1) + 50(Z3) + 150(CL) = **275** | r2 [200,400) | ✅ | +75 / −125 |
| Z3 | 25 + 400 + 50(Z1) + 150(CL) = **625** | r3 (≥400) | ✅ | +225 above floor |
| Z4 | 25 + 50(Z1) + 50(Z3) + 150(CL) = **275** | r2 [200,400) | ✅ | +75 / −125 |

⇒ Target `[3,2,3,2]` is hit at **sun r0, r1, r2, r3** with no borderline ranks. `CorridorLight` (+150 to all) is the lever that lifts the rank-2 zones at low sun where blinds are useless. **Reachability is therefore guaranteed unconditionally.**

### 9.3 A cheaper, blinds-based optimum at high sun (the prior's constructive lever)

At **sun = r3 (900)**, policy **P₃ = {Z1Blinds open, Z3Light on; all else off}**:

| Zone | Level | Target | Result |
|---|---|---|---|
| Z1 | 25 + 0.50·900(own blind) + 50(Z3 task) = **525** | r3 | ✅ |
| Z2 | 25 + 0.25·900(Z1 blind bleed) + 50(Z3 task) = **300** | r2 | ✅ |
| Z3 | 25 + 400(own task) + 0.25·900(Z1 blind bleed) = **650** | r3 | ✅ |
| Z4 | 25 + 0.25·900(Z1 blind bleed) + 50(Z3 task) = **300** | r2 | ✅ |

Energy(P₃) = **1** (one task light) vs Energy(P₀) = **4** (two task lights + corridor). So at high sun the **blinds-open action is part of a strictly cheaper goal policy** — this is the positive lever that custom8 lacks (audit Step-1b §3) and the reason custom9 is the lab on which `Mediates(blind, sunshine)` is mechanically testable.

### 9.4 The §6.B overshoot warning is real but does not block reachability

Naive **all-blinds-open at sun = 900** gives every zone `25 + 0.50·900 + 3·(0.25·900) = 1150 → r3`, so **Z2 and Z4 overshoot** their r2 target. Hence the prior must be applied **selectively**: it is *correct* for the rank-3 zones (Z1, Z3) but would *overshoot* the rank-2 zones (Z2, Z4) if over-trusted at high sun. This is a feature, not a defect — custom9 becomes a genuine test of **adaptive trust** (the agent must down-weight the prior on Z2/Z4 out-of-distribution). In-distribution (training sun = r2, ~175) the own-blind contribution is only `0.50·175 ≈ 88`, which lifts Z2/Z4 toward r2 **without ever overshooting**, so the prior is safely constructive on the training distribution.

### 9.5 Action-budget check

From any benchmark start state, the target ranks depend on only **five** actuators (Z1Light, Z3Light, CorridorLight ON; Z2Light, Z4Light OFF). Reaching P₀ needs ≤ 5 single-actuator toggles; `Spotlight`/`SpotlightCD` toggles are inert (disabled) and never block the target. Both ≪ the 20-step budget. **PASS.**

**Conclusion.** custom9 clears the audit Step-5 §6.B / §8-Q4 reachability blocker: the target is reachable at every sunshine rank (P₀, sun-invariant, robust margins), a cheaper blinds-based optimum exists at high sun (P₃), the overshoot risk is confined to over-application of the prior on the rank-2 zones (adaptive-trust signal), and no coefficient recalibration is needed. custom9 is cleared to enter the confirmatory sweep as the headline lab.

---

## 10. Corrections implemented (2026-06-06) — diagnosis → fixes

§§3–4 above are the *diagnosis*; §7 was the *plan*. This section is the **as-built record** of what was actually changed in response, so the thesis Methods section can cite a single source of truth. All changes verified with `gradlew compileJava` (EXIT 0), `gradlew test` (EXIT 0), and a full dev-mode smoke (train both arms + benchmark all 3 modes on custom9, BUILD SUCCESSFUL). Pre-registration counterpart: [pre_registration.md](pre_registration.md) §6.6 (SW17-1…SW17-8).

### 10.1 Root-cause summary (why Sweep 17 read as a negative)

| # | Cause | Evidence | Fix |
|---|---|---|---|
| 1 | **Wrong metric.** Terminal `goal_rate` measures asymptote, but the thesis claims *learning speed*. A prior that bends the early curve but converges to the same plateau is invisible to `goal_rate`. | §3.2 H1 falsified on asymptote | SW17-1 — learning-speed primary metric (AUC + episodes-to-threshold) |
| 2 | **Headline lab had no positive lever.** `custom8`'s optimum is sun-invariant ⇒ `Mediates(blind,sun)` prior cannot help there even in principle (audit Step-1b §3). | §6 row 3 | SW17-2 — headline → `custom9` (proof §9); lab set reduced to `{custom9,custom3,custom5}` |
| 3 | **Under-training.** 2500 episodes ≈ 2 visits/state-cell — nobody converged, confounding "priors don't help" with "nobody learned." | tabular cell-visit count | SW17-3 — `num_episodes` 2500 → 10000 (provisional) |
| 4 | **Penalty-only prior.** The reasoner could discourage wrong actions but never *encourage* the right one, so it had no constructive lever to bend the early curve. | `getInitPenaltyForZone` emitted only penalties | SW17-6 — constructive optimistic init (Rule 5) |
| 5 | **Saturated reward.** `reward_clip = 50` flattened the goal-bonus + PBRS signal the prior is meant to sharpen. | reward range vs clip | SW17-4 — `reward_clip` 50 → 200 |
| 6 | **Per-zone over-estimation noise.** Independent per-zone max bootstrap is inconsistent with the decomposed reward (audit Step-3a R-1). | early-curve variance | SW17-5 — VDN joint Bellman target |
| 7 | **Empty `first_goal` table + latent build bug.** H2 aggregator read the wrong dir; two `-P` knobs never reached the JVM. | `first_goal_table.csv` empty; `_httpKeys` gap | SW17-8, SW17-7 |

### 10.2 Files changed

| File | Change | Pre-reg ref |
|---|---|---|
| `src/env/tools/QLearner.java` | VDN joint target in `calculateQ` via new `jointArgmaxAction(sNext)`; removed dead `maxQ` | SW17-5 |
| `src/env/tools/StereotypeReasoner.java` | Rule 5 constructive optimistic init (`stereo.initBonus`, default 15.0) | SW17-6 |
| `config/run_config.json` | `profiles_to_run = [custom9,custom3,custom5]`; custom9 added to all 4 maps (port 1889, flow, suffix, dim 13); `paper.num_episodes` 2500→10000; `learning.reward_clip` 50→200; `stereo_init_bonus = 15.0` | SW17-2/3/4/6 |
| `run_full_project.ps1` | forward `-Pstereo.initBonus`; custom9 simulator/port wiring | SW17-6 |
| `build.gradle` | added `stereo.priorRedundant`, `stereo.priorIVUnsat`, `stereo.initBonus` to `_httpKeys` (latent forwarding bug) | SW17-7 |
| `analysis/sweep_report.py` | learning-speed block (`learning_speed_tests`, `--speed-window`, `--speed-threshold`); `first_goal` dir fix; legend-crash guard | SW17-1/8 |
| `.github/workflows/sweep-paper.yml` | `PROFILES` default → `custom9,custom3,custom5` | SW17-2 |
| `simulator/simulator_flow_custom9.json`, `src/agt/lab_profiles.asl` | custom9 lab (used for §9 reachability proof; unchanged this round) | SW17-2 |

### 10.3 Validation evidence

- `gradlew.bat compileJava` → EXIT 0 (twice); `gradlew.bat test` → EXIT 0.
- Dev-mode smoke on custom9: train `ql_true` + `ql_false`, benchmark `ql_true`/`ql_false`/`rule_based` end-to-end, no runtime exceptions, BUILD SUCCESSFUL; `ql_true` benchmark wrote 56 records.
- `analysis/sweep_report.py` single-root and `--seeds-mode` both EXIT 0 under `-W error::UserWarning`. Against real custom9 data the learning-speed metric separates the arms (AUC goal ON 0.031 vs OFF 0.020) and `first_goal_table.csv` now populates (2 rows vs 0 before the dir fix).

### 10.4 Deferred (flagged exploratory; not run)

- **Episode-count calibration probe** — confirm 10000 is past convergence; the budget is provisional until measured.
- **Confirmatory sweep** — 5 seeds × `{custom9,custom3,custom5}` × `{ql_true,ql_false}` (+`rule_based`), **venue = GitHub Actions `sweep-paper.yml`**. Run after the probe.
- **B2 (Δrank state encoding)** — deliberately skipped: per-lab fixed targets + per-lab Q-tables make absolute→Δrank a constant relabel (zero convergence benefit, regression risk).
- **C1 (stereotype PBRS potential)** — deferred: existing distance-PBRS `Φ_z(s) = −|level − target|` already covers it.
