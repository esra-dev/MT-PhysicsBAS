# Sweep 17 — Results Analysis (`results-20260605-182321-paper-466fc89`)

> ⚠️ **CORRECTION (2026-06-06):** This file reads only the `origin/results` **branch**, which received the *training-phase dump alone*. The full sweep (run `27008592029`) actually produced **5 seeds + held-out benchmark + the complete statistics layer**, published as **workflow-run artifacts** (`sweep-paper-consolidated`). The §0–§2/§5 claims of "single-seed / training-only / no benchmark / H1 unevaluable" are therefore **wrong for the real run**. The c7≡c8 collision is **real but scoped to the training/Q-table publish** — the **benchmark** results for c7 and c8 are distinct, and **H1 is evaluable and FALSIFIED**. See the authoritative corrected analysis in [docs/sweep17_followup_analysis.md](sweep17_followup_analysis.md).

**Date of analysis:** 2026-06-06 · **Analyst:** automated review (read against [docs/pre_registration.md](pre_registration.md) and the Step 0–8 audit trail)
**Artifact source:** `origin/results` branch, top-level dir `results-20260605-182321-paper-466fc89/` · 272 artifacts · `RUN_MANIFEST.json`
**Run configuration (from manifest):** `runMode = paper`, `profiles = custom2…custom9` (8 labs), `bench_modes = {rule_based, ql_false, ql_true}`, `git_sha = 466fc89` (branch `main`)

---

## 0. Headline verdict

> **Sweep 17 does not yet confirm the thesis, and it cannot — not because the result is negative, but because the run is not evaluable against the pre-registration.** Three structural problems block any confirmatory claim: (1) a **profile-collision data defect** that makes the headline lab `custom8` an exact byte-for-byte duplicate of `custom7`; (2) the run is **single-seed**, so none of the pre-registered paired-bootstrap CIs / q-values can be computed; and (3) the published branch contains **training-phase artifacts only** — there are no held-out `benchmark_results_*.csv`, so the pre-registered *primary* dependent variable (benchmark `goal_rate`) was not even produced.

What we *can* extract — the per-profile **training** learning curves — is **directionally encouraging for the H3 "do no harm" safety claim** (ql_true reaches the goal at least as often as ql_false on the confirmatory labs, and the new scaffolded lab `custom9` shows near-perfect parity), but it also exposes a **consistent exploration-cost penalty** for ql_true (lower episode reward, more penalised actions, later first goal) that must be addressed before the "faster + safer" framing can be sustained.

**Success against the Step-8 prediction (custom8 ql_true − ql_false moves from −0.073 to +0.05…+0.15): _cannot be evaluated_ — the custom8 cell is corrupt.**

---

## 1. What was actually published (and what was not)

The `results` branch carries, per `(profile ∈ {custom2..custom9}) × (stereotype ∈ {true,false})`:

| Family | File pattern | Purpose |
|---|---|---|
| Training metrics | `metrics_stereotypes_<bool>_customN.csv` | per-episode `Steps, RewardZ1, RewardZ2, GoalReached, Epsilon, WastedByPenalty, WastedByNoEffect` (2504 episodes + a `# Summary` trailer) |
| Final Q-tables | `qtable_final_..._{zone1..4,visits,trust}.csv` | learned policy + visit/trust diagnostics |
| Initial Q-tables | `qtable_initial_...csv` | cold-start (prior-seeded) tables |
| IV effectiveness | `iv_stats_stereotypes_<bool>_customN.json` | learned blind/sun effectiveness counts |
| Learned stereotypes | `learned_stereotypes_<bool>_customN.ttl` | post-training ontology dump |

**Absent from the publish (material gaps):**

- ❌ `benchmark_results_{rule_based,ql_false,ql_true}.csv` — the held-out 28-scenario evaluation. **This is the pre-registered primary-metric source** (`docs/pre_registration.md` §1). Without it, the headline `goal_rate` ordering ql_true ≥ ql_false ≥ rule_based is unmeasurable from this sweep.
- ❌ `results_seed<N>/` siblings — **only one seed was run/published.** The pre-registration locks **5 seeds** for the main sweep (§1, §2). No `aggregate_seeds`, no `paired_tests.csv`, no bootstrap CI, no BH q-values are possible.
- ❌ `analysis/out/summary_table_ci.csv`, `paired_tests.csv`, `first_goal_table.csv` — none of the statistics-layer outputs were generated.

> **Consequence:** Sweep 17 is, at best, a **single-seed training pilot**, not the confirmatory paper sweep. Every number below is **exploratory** by the project's own pre-registration rules.

---

## 2. ⛔ Critical data-integrity defect — `custom8 ≡ custom7`

`custom8` is the **headline clean-lab** that hypothesis **H1** is built on. In Sweep 17 it carries **no independent data**: every `custom8` artifact is a byte-for-byte duplicate of the corresponding `custom7` artifact.

Verified by MD5 across the full artifact set (stereotypes = true shown; false is identically collided):

| Artifact | custom7 MD5 | custom8 MD5 | Identical? |
|---|---|---|---|
| `metrics_..._true_customN.csv` | `501DA939…CDDB8` | `501DA939…CDDB8` | ✅ yes |
| `qtable_final_..._true_customN_zone1.csv` | `E9B9127F…A1CA` | `E9B9127F…A1CA` | ✅ yes |
| `qtable_final_..._true_customN_visits.csv` | `85EE51F5…F57A` | `85EE51F5…F57A` | ✅ yes |
| `qtable_final_..._true_customN_trust.csv` | `3321B76E…FFD96` | `3321B76E…FFD96` | ✅ yes |
| `iv_stats_..._true_customN.json` | `A3736DB7…1235` | `A3736DB7…1235` | ✅ yes |

The collision is **isolated to c7/c8** — a hash of the zone-1 final Q-table across all eight profiles yields **7 distinct hashes for 8 profiles**, with only c7 and c8 sharing a value (c2,c3,c4,c5,c6,c9 are all distinct). The bench scenario files themselves differ (`scenarios_custom7.json` MD5 `0CDB2C57…`, `scenarios_custom8.json` MD5 `73491BC6…`), so the inputs were *meant* to be different — the collision happened at run/publish time, not in the lab specs.

**Most likely cause:** a profile-loop overwrite or artifact-copy aliasing in the paper-mode orchestration (`run_full_project_parallel.ps1`), where the `custom8` leg either re-used the `custom7` trained artifacts or wrote to the `custom7` suffix. This matches the long-standing Step-5 ambiguity that **the `custom8` simulator tab is still mislabelled "W7 IV-coupling demo"** while the profile docstring says "clean baseline" — the two profiles are dangerously easy to alias.

**Impact on the thesis:**
- **H1 (headline) is unevaluable in Sweep 17.** The custom8 cell is custom7's W6-heat-lab data, not the clean lab.
- Any "the inversion is fixed" claim **must not** cite Sweep 17's custom8 numbers; doing so would report the W6 lab under the clean-lab label.
- This defect **must be fixed and the sweep re-run** before H1 can be stated either way.

---

## 3. Exploratory training-phase findings (the part that *is* usable)

Computed from the 2504-episode training logs. `GR100` / `St100` / `R100` / `WP100` / `WN100` are means over the last 100 episodes; `TotGoals` and `FirstGoal` are from the `# Summary` trailer. **`c8` is shown struck-through because it is a duplicate of `c7`.**

| Lab (weakness) | mode | FirstGoal ↓ | TotGoals ↑ | GoalRate(last100) ↑ | Steps(last100) ↓ | Reward(last100) ↑ | WastedByPenalty ↓ | WastedByNoEffect ↓ |
|---|---|---|---|---|---|---|---|---|
| **c2** (W1 schedule) | ql_true  | 17 | **97** | **0.04** | 19.25 | 20.46 | 6.91 | 15.46 |
|                      | ql_false |  2 | 87 | 0.03 | 19.44 | **67.42** | **1.48** | 17.48 |
| **c3** (W2 sun-flip) | ql_true  | 35 | **179** | **0.08** | **18.57** | 30.93 | 6.91 | 15.35 |
|                      | ql_false |  2 | 116 | 0.05 | 19.20 | **69.62** | **1.62** | 16.57 |
| **c4** (W3 delayed)  | ql_true  |  6 | **86** | 0.02 | 19.54 | −3.11 | 7.96 | 15.14 |
|                      | ql_false | 16 | 69 | **0.04** | **19.22** | **59.10** | **2.58** | 15.97 |
| **c5** (W4 power-cap)| ql_true  | 31 | **99** | **0.03** | 19.47 | 21.87 | 6.43 | 16.41 |
|                      | ql_false |  2 | 74 | 0.01 | 19.83 | **77.08** | **2.02** | 17.34 |
| **c6** (W5 partition)| ql_true  | 17 | 220 | 0.08 | 18.62 | 20.50 | 5.95 | 14.87 |
|                      | ql_false |  2 | **291** | **0.10** | **18.41** | **74.25** | **2.54** | 15.34 |
| **c7** (W6 heat·null)| ql_true  | 35 | **116** | **0.04** | 19.27 | 36.32 | 6.63 | 16.54 |
|                      | ql_false |  2 | 79 | 0.03 | 19.57 | **76.61** | **1.42** | 16.86 |
| ~~c8 (clean = dup of c7)~~ | ~~ql_true~~  | ~~35~~ | ~~116~~ | ~~0.04~~ | ~~19.27~~ | ~~36.32~~ | ~~6.63~~ | ~~16.54~~ |
|                            | ~~ql_false~~ |  ~~2~~ | ~~79~~ | ~~0.03~~ | ~~19.57~~ | ~~76.61~~ | ~~1.42~~ | ~~16.86~~ |
| **c9** (scaffolded prior)| ql_true  | 10 | **183** | 0.05 | **19.12** | 1.98 | 8.03 | 15.94 |
|                          | ql_false | 16 | 182 | **0.06** | 19.19 | **74.59** | **1.32** | 17.32 |

### 3.1 Signals that *support* the thesis

1. **Goal *throughput* favours ql_true on every valid clean-ish / wrong-ontology lab.** Total goals reached over training: c2 +10, c3 **+63**, c4 +17, c5 +25, c7 +37. The stereotype prior makes the agent hit the goal **more often** once it starts converging — exactly the intended "useful inductive bias" effect.
2. **Asymptotic goal rate (last-100) is ≥ for ql_true on c2, c3, c5, c7** (and on the corrupt c8). On the confirmatory H3 set `{c2,c3,c4,c5}`, ql_true is **not strictly worse** on throughput, and is equal-or-better on 3 of 4 for asymptotic rate (c4 is the one soft exception: GR100 0.02 vs 0.04, but TotGoals 86 > 69). This is the **direction H3 predicts** ("priors do not hurt when wrong").
3. **`custom9` behaves exactly as designed.** The new scaffolded constructive-prior lab gives near-perfect parity (TotGoals 183 vs 182; GR100 0.05 vs 0.06) and ql_true reaches the first goal **earlier** (ep 10 vs 16). This is the clean "priors are safe and slightly help bootstrap" demonstration that custom8 was *supposed* to provide — `custom9` is now the better headline candidate.

### 3.2 Signals that *complicate* the thesis (must be addressed)

1. **ql_true pays a large training-reward penalty everywhere.** Last-100 reward is dramatically lower for ql_true (e.g. c5: 21.9 vs 77.1; c9: 2.0 vs 74.6; c4 even negative −3.1). The gap is **fully explained by penalised actions**: `WastedByPenalty` is ~3–5× higher for ql_true (6–8/episode vs 1.3–2.6). The prior is steering exploration into stereotype-favoured actions that the reward function then penalises as redundant/no-effect. This is the same **soft-prior handicap** flagged in audit Steps 2/3b — it is *attenuated* but **not eliminated**.
2. **ql_true reaches its first goal *later*, not earlier.** On 5 of 7 valid labs ql_false hits the goal by episode 2 while ql_true takes 17–35 episodes (exceptions: c4 ep6, c9 ep10). This directly **contradicts the H2 "PBRS/priors speed up learning"** intuition at the *first-goal* milestone — although H2 is properly tested against the **PBRS ablation**, which this sweep did not run.
3. **c6 (W5 partition) inverts:** ql_false beats ql_true on every metric (TotGoals 291 vs 220, GR100 0.10 vs 0.08). This is **expected and pre-registered as parity-not-recovery** (Amendment 2026-06-03: W5 is non-Markov; neither variant can model it), so it is not a thesis failure — but the prior actively *hurts* here, so it should be reported as the honest "priors can mislead on non-Markov dynamics" caveat.

---

## 4. Status of each pre-registered hypothesis after Sweep 17

| Hyp. | Population / claim | Sweep 17 status | Why |
|---|---|---|---|
| **H1** | custom8 (clean): ql_true `goal_rate` ≥ ql_false | **⛔ UNEVALUABLE** | custom8 data is a duplicate of custom7 **and** no benchmark CSV was published **and** single seed → no CI. |
| **H2** | PBRS lowers episodes-to-first-goal on every profile | **⛔ NOT RUN** | Requires the noPBRS ablation; not in this sweep. Training first-goal here actually trends *against* H2 for ql_true vs ql_false (different comparison, but worth noting). |
| **H3** | `{c2,c3,c4,c5}`: ql_true not significantly worse than ql_false | **🟡 DIRECTION SUPPORTED, NOT CONFIRMED** | Training throughput shows ql_true ≥ ql_false on all 4; but no benchmark data and no CIs → cannot certify "not significantly worse". |
| **H4** | Without adaptive trust, ql_true worse on ≥1 lab (Ablation B) | **⛔ NOT RUN** | No ablation-B cells published. |
| **H5** | `stereo_prior_scale=0` ⇒ ql_true ≡ ql_false (Ablation C) | **⛔ NOT RUN** | No ablation-C cells published. |

**New, off-registration but valuable:** `custom9` (scaffolded constructive-prior lab) was added since the pre-registration was locked (the pre-reg only lists custom2…custom8). It should be **formally added as the H1-style headline lab** in a pre-registration amendment, because it is the lab where the Mediates(blind, sunshine) prior actually has a positive lever (unlike custom8, whose optimal policy is sun-invariant per audit Step 1b).

---

## 5. Did "the changes" succeed and improve the thesis?

**The Wave-A fixes (S3b-1 redundant-action step cost, S3b-2 bench episode-counter, S5-3, S6 BH-family cleanup) cannot be credited or faulted from Sweep 17**, because the one cell they were predicted to move (custom8 ql_true − ql_false: −0.073 → +0.05…+0.15) is the corrupted cell, and because the sweep produced no benchmark `goal_rate` at all.

What the run *does* establish:

- ✅ **The pipeline now trains all 8 profiles incl. the new `custom9`** and emits the full artifact family — infrastructure-wise this is a step forward.
- ✅ **The exploratory training signal is consistent with the intended mechanism**: ql_true reaches the goal more often (higher throughput) on clean/wrong-ontology labs, and is safe-parity on the scaffolded lab — i.e. the *direction* of H3 and the spirit of H1 hold in the data that is valid.
- ⚠️ **But the prior still imposes a measurable exploration-cost penalty** (lower reward, ~3–5× more penalised actions, later first goal). The "faster + safer" sentence is **not yet supported**; the current evidence supports at most "**comparable-or-better goal throughput at a higher exploration cost, with no held-out confirmation**".
- ⛔ **Two blocking defects** (custom8≡custom7 collision; single-seed training-only publish) mean **this sweep is not citable as a confirmatory result.**

**Net:** *Partial infrastructure progress; thesis claims neither confirmed nor improved by Sweep 17.* The run must be repeated correctly before it can move the thesis.

---

## 6. Required next actions (ordered)

1. **Fix the custom7/custom8 collision.** Audit `run_full_project_parallel.ps1` (and the `*_bench.asl` profile-apply path) for a suffix/overwrite aliasing between `custom7` and `custom8`; rename the `custom8` simulator tab from "W7 IV-coupling demo" to "Custom8 — clean baseline (port 1888)" so the two can never be confused; add a post-run guard that **fails the sweep if any two profiles emit identical artifact hashes.**
2. **Run the real multi-seed sweep (5 seeds) and publish the benchmark CSVs.** The pre-registration's primary metric is the **held-out benchmark `goal_rate`**, which this run never produced. Ensure `results_seed<N>/` siblings are published so `analysis/sweep_report.py --seeds-mode` can emit `paired_tests.csv` with bootstrap CIs and BH q-values.
3. **Promote `custom9` to the H1 headline lab via a pre-registration amendment.** custom8's optimal policy is sun-invariant (audit Step 1b), so the blind/sun prior has no positive lever there; custom9 is the lab where the prior *can* help, and Sweep 17 already shows it behaving as designed.
4. **Report the exploration-cost penalty honestly.** Either (a) fold the residual soft-prior handicap fix (audit Suggestion S3b-1/S3b-3: align prior-decay schedule with ε-schedule; reduce redundant-action penalty under active priors) and re-measure, or (b) frame the contribution as "higher goal throughput at a controlled exploration cost" rather than "faster + safer".
5. **Run the H2/H4/H5 ablations.** None were present in Sweep 17; all three confirmatory/integrity hypotheses remain untested.

---

## 7. Provenance / reproducibility notes

- Data pulled from `origin/results` (`git fetch origin results:refs/remotes/origin/results`), tree `results-20260605-182321-paper-466fc89/`, then materialised via `git archive --format=zip origin/results`.
- The GitHub release tarball/zip (`MT-PhysicsBAS-results-20260605-182321-paper-466fc89.{tar.gz,zip}`) is a **source snapshot of the `main` tree at 466fc89** (build files, `src/`, `simulator/`, `benchmark/` scenarios incl. the new `custom9`) — it contains **no result CSVs**; all measured artifacts live on the `results` branch.
- Per-cell training summary regenerated to `sweep17_training_summary.csv`; collision verified by MD5 over `metrics_*`, `qtable_final_*_{zone1,visits,trust}`, and `iv_stats_*` for custom7 vs custom8.
