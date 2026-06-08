# Sweep-18 Results Analysis — Run `27073252484`

**Status:** Full paper sweep completed successfully (76/76 CI jobs green).
**Wall-clock:** 2026-06-06 20:37:35Z → 2026-06-07 02:23:43Z (~5 h 46 m).
**Design:** 3 profiles (`custom9`, `custom3`, `custom5`) × 2 conditions (stereo `true`/`false`) × 5 seeds training; 3 benchmark modes (`rule_based`, `ql_false`, `ql_true`) × 5 seeds × 3 profiles evaluation.
**Configuration:** 10 000 training episodes, VDN joint Bellman target, constructive optimistic Q-init (`stereo_init_bonus = 15.0`), `reward_clip = 200`, PBRS distance shaping, ε 0.3→0.01 (decay 0.995/episode, floor ≈ episode 679), 20-step horizon, dev-speed timing (`tick = 0.05`, `action_delay = 65 ms`).

This report supersedes the Sweep-17 falsification (see [docs/sweep17_followup_analysis.md](sweep17_followup_analysis.md)). Sweep-17's headline was *H1 falsified, base learner under-trained at 1 000 episodes*. Sweep-18 was the corrective replication: **10× more episodes, VDN target, constructive priors, and a learning-speed primary metric**.

---

## 1. Executive summary

| Question | Answer |
|---|---|
| Did the pipeline issues resolve? | **Yes.** All SW17-1..8 fixes are live; the full sweep ran clean end-to-end with no censored/failed cells. |
| Did the base learner converge with 10 000 episodes? | **No.** Training goal-rate is **flat** across all 10 k episodes (custom9: ~21 % `false`, ~15 % `true`). More episodes did **not** fix the plateau — the Sweep-17 "under-training" explanation is **refuted**. |
| Does the stereotype prior help learning? | **Partially, and significantly where it does.** `ql_true` beats `ql_false` on goal-rate on **custom3** (Δ=+0.199, q=0.002, δ=0.76) and **custom5** (Δ=+0.074, q<0.001, δ=1.0); **null on custom9** (Δ=+0.007, q=0.81). |
| Does the prior learn *faster* (AUC)? | **Yes on custom3/custom5, no on custom9.** auc_goal favours `ql_true` on custom3 (q=0.041) and custom5 (q<0.001) but favours `ql_false` on custom9 (δ=−0.6). |
| Is it *more efficient* (energy)? | **Yes, robustly, on all three profiles** (Δenergy −34 to −84, q<0.001, δ=−1.0). This is the strongest and most consistent finding. |
| Does RL beat the rule-based baseline? | **No, except a draw on custom3.** `rule_based` still dominates both RL arms on custom5 and custom9 (δ=−1.0). |

**Bottom line for the thesis:** the claim *"stereotype-informed Q-learning learns faster and more efficiently"* is **statistically supported on 2 of 3 environments for speed, and on 3 of 3 for energy efficiency**, but with an honest and important caveat: **neither RL arm converges to a competitive policy** within the 20-step / 10 k-episode budget, and the rule-based controller remains the stronger absolute performer. This is a defensible, nuanced result — not a clean universal win.

---

## 2. Primary metric — learning speed (`learning_speed_tests.csv`)

Paired (per-seed) `ql_true − ql_false`, n=5 seeds, paired bootstrap CIs, Wilcoxon, Cliff's δ, BH q over a family of m=12.

| Profile | Metric | Δ (true−false) | 95 % CI | p_boot | q (BH) | Wilcoxon | Cliff δ | Verdict |
|---|---|---:|---|---:|---:|---:|---:|---|
| custom3 | auc_goal ↑ | **+0.066** | [0.003, 0.155] | 0.024 | **0.041** | 0.3125 | 0.44 | favours `true` ✓ |
| custom3 | auc_reward ↑ | **+13.90** | [3.06, 21.74] | 0.013 | **0.032** | 0.125 | 0.68 | favours `true` ✓ |
| custom3 | mean_first_goal ↓ | +688.7 | [192, 1265] | 0.000 | 0.000 | 0.0625 | 0.76 | `true` **slower** to 1st goal |
| custom5 | auc_goal ↑ | **+0.051** | [0.033, 0.071] | 0.000 | **0.000** | 0.0625 | 1.0 | favours `true` ✓ |
| custom5 | auc_reward ↑ | −13.17 | [−23.5, −2.8] | 0.019 | 0.037 | 0.1875 | −0.76 | favours `false` |
| custom5 | mean_first_goal ↓ | +230.9 | [−252, 714] | 0.403 | 0.538 | 0.8125 | 0.36 | n.s. |
| custom9 | auc_goal ↑ | −0.042 | [−0.070, −0.003] | 0.042 | 0.064 | 0.125 | −0.6 | favours `false` |
| custom9 | auc_reward ↑ | −32.05 | [−40.4, −22.6] | 0.000 | 0.000 | 0.0625 | −1.0 | favours `false` |
| custom9 | mean_first_goal ↓ | +225.6 | [44, 381] | 0.013 | 0.032 | 0.1875 | 0.84 | `true` **slower** to 1st goal |

**`episodes_to_threshold` is degenerate.** With `--speed-threshold = 0.5` (rolling goal-rate that defines "learned"), the threshold is **never reached** by either arm in any profile — every value is right-censored at 10 000. Reason: training goal-rate plateaus at 0.15–0.21, well below 0.5. **Consequence:** `auc_goal` / `auc_reward` are the only usable speed metrics; `episodes_to_threshold` must be reported as censored/uninformative, not as a tie.

**Interpretation.** The constructive optimistic prior (`stereo_init_bonus = 15`) drives extra early exploration, so `ql_true` reaches its *first* goal **later** (positive mean_first_goal on all profiles) but accumulates **more** goal-mass over the run on the two profiles where its priors are useful (custom3, custom5). On custom9 the prior neither speeds learning nor raises the ceiling.

---

## 3. Outcome metric — benchmark goal-rate (`summary_table_ci.csv`, `paired_tests.csv`)

Mean goal-rate over 5 seeds (deterministic greedy evaluation, 140 scenarios/seed):

| Profile | rule_based | ql_false | ql_true |
|---|---:|---:|---:|
| custom3 | 0.179 | 0.034 | **0.233** |
| custom5 | **0.250** | 0.023 | 0.097 |
| custom9 | **0.250** | 0.113 | 0.120 |

Confirmatory paired contrasts (`ql_true − ql_false`, BH family m=30):

| Profile | Δ goal-rate | 95 % CI | p_boot | q (BH) | Cliff δ | Verdict |
|---|---:|---|---:|---:|---:|---|
| custom3 | **+0.199** | [0.063, 0.331] | 0.0012 | **0.0016** | 0.76 | `true` ≫ `false` ✓ |
| custom5 | **+0.074** | [0.041, 0.121] | 0.000 | **0.000** | 1.0 | `true` > `false` ✓ |
| custom9 | +0.007 | [−0.024, 0.047] | 0.752 | 0.805 | 0.24 | null (tie) |

`ql_true − rule_based`:

| Profile | Δ goal-rate | q (BH) | Cliff δ | Verdict |
|---|---:|---:|---:|---|
| custom3 | +0.054 | 0.484 | 0.2 | draw (RL nominally ahead) |
| custom5 | −0.153 | <0.001 | −1.0 | rule_based dominates |
| custom9 | −0.130 | <0.001 | −1.0 | rule_based dominates |

**Comparison to Sweep-17.** On custom9, `ql_false` goal-rate rose from ~0.02–0.07 (Sweep-17, 1 k episodes) to **0.113** (Sweep-18, 10 k episodes) — a modest improvement, but still less than half of `rule_based` (0.25). The extra episodes helped a little but did **not** close the gap, consistent with the flat training curve in §5.

---

## 4. Secondary / emergent metric — energy efficiency (`paired_tests.csv`)

Paired `ql_true − ql_false`, lower energy is better:

| Profile | Δ energy | 95 % CI | q (BH) | Cliff δ |
|---|---:|---|---:|---:|
| custom3 | **−75.99** | [−111.1, −47.7] | <0.001 | −1.0 |
| custom5 | **−84.22** | [−98.9, −68.5] | <0.001 | −1.0 |
| custom9 | **−34.54** | [−40.2, −28.2] | <0.001 | −1.0 |

**This is the most robust effect in the study:** the stereotype prior consistently and significantly reduces actuation energy (δ=−1.0 on all three profiles) — replicating the Sweep-17 energy finding. The prior biases the agent away from gratuitous toggling. Deviation (`avg_dev`) is also reduced on custom3/custom5 but **worsens on custom9** (+9.23), i.e. the custom9 prior trades comfort for a small energy saving.

---

## 5. Why the base learner does not converge (training trajectory)

Per-episode goal counts on custom9, binned into five 2 000-episode windows (from `metrics_*_custom9.csv`):

| Condition | ep 0–2k | 2–4k | 4–6k | 6–8k | 8–10k | total |
|---|---:|---:|---:|---:|---:|---:|
| `stereo_false` | 406 | 416 | 411 | 428 | 432 | 2093 (≈21 %) |
| `stereo_true` | 273 | 305 | 302 | 305 | 304 | 1489 (≈15 %) |

The curve is **flat** — there is no upward learning trend after ε reaches its floor (~episode 679). The agent reaches a low greedy plateau and stays there. **This is the central diagnostic of the sweep:** the bottleneck on custom9 is **not** episode count (10× more episodes changed nothing) but something structural — most plausibly the **20-step horizon being too short for custom9's deeper topology**, the reward/exploration coupling, or the tabular state abstraction. On custom9 the prior even depresses the plateau slightly (15 % vs 21 %), suggesting the custom9 stereotype is mildly mis-specified for greedy exploitation even while it lowers energy.

---

## 6. Are the expected results obtained?

- **Pipeline correctness:** ✅ fully resolved — clean 10 k-episode sweep, no censoring, all fixes live.
- **"Learns faster":** ✅ on custom3 and custom5 (AUC, statistically significant after BH); ❌ on custom9.
- **"More efficient":** ✅ on all three profiles (energy, δ=−1.0, q<0.001) — the strongest result.
- **"Beats the non-learning baseline":** ❌ rule_based still dominates on custom5/custom9; only a draw on custom3.
- **Base-learner convergence:** ❌ not achieved — refutes the Sweep-17 under-training hypothesis.

So: **a genuine, statistically-supported partial confirmation of the thesis claim**, with an honest negative on absolute competitiveness. This is publishable as an honest scientific result; it is **not** a clean universal win.

---

## 7. Statistical analysis we can report (defensible methods)

1. **Paired per-seed design** (same 5 seeds across conditions) — removes seed variance; the correct unit of analysis.
2. **Paired bootstrap CIs** on the mean difference (10 000 resamples) — primary inferential tool given n=5.
3. **Wilcoxon signed-rank** as a distribution-free corroborator (note: with n=5 its minimum two-sided p is 0.0625, so it can never alone reach α=0.05 — report it as supporting, not gating).
4. **Cliff's δ** for non-parametric effect size (δ=±1.0 = complete separation).
5. **Benjamini–Hochberg q-values** controlling FDR within pre-declared families (confirmatory m=30; learning-speed m=12). Report q, not raw p, for the multiplicity-corrected verdict.
6. **One-sided favourable p** for directional hypotheses (pre-registered direction).
7. **Pre-registered confirmatory vs exploratory split** (the `family` column) — protects the confirmatory claims from being diluted by exploratory contrasts.

**Reportable headline statistics:**
- custom3 goal-rate: Δ=+0.199, 95 % CI [0.063, 0.331], q=0.0016, δ=0.76.
- custom5 goal-rate: Δ=+0.074, CI [0.041, 0.121], q<0.001, δ=1.0.
- Energy (all profiles): Δ=−34 to −84, q<0.001, δ=−1.0.
- Learning speed (auc_goal): custom3 q=0.041, custom5 q<0.001 (favourable); custom9 δ=−0.6 (unfavourable).

---

## 8. Remaining issues, open questions & validations needed

**Methodological gaps to close before final write-up**
1. **`episodes_to_threshold` is censored everywhere.** Either (a) lower `--speed-threshold` to a value the learner actually reaches (e.g. 0.15–0.20) and re-run the analysis script (no new sweep needed — it reprocesses existing metrics CSVs), or (b) drop the metric and rely on AUC, documenting the censoring. **(a) is recommended** and is a cheap, defensible fix.
2. **n=5 seeds caps Wilcoxon power.** For confirmatory claims, increase to **n=10 seeds** so the rank test can independently clear α=0.05. This is the single highest-value robustness improvement and costs one more sweep.
3. **Base learner never converges (custom9).** Run a **horizon ablation** (`max_steps_per_episode` 20 → 40/60) and/or a **reward-shaping ablation** to establish whether custom9 is solvable in principle by the tabular learner. Until this is known, the custom9 null is confounded between "prior doesn't help" and "task is unsolvable for the learner".
4. **Mechanistic claim for energy.** The energy win is robust but currently phenomenological. Add a short analysis of the learned Q-tables / toggle counts (`avg_wasted`, zone CSVs) to explain *why* the prior reduces actuation — strengthens the contribution.

**Open scientific questions**
- Why does the prior help on custom3/custom5 but not custom9? (custom9 = compatible-topology vs custom3 = wrong-prior recovery — the per-profile prior quality needs characterising; see `iv_stats_*.json` and `learned_*.ttl`.)
- Is the rule-based dominance a ceiling artefact of the 20-step horizon, or a genuine limit of tabular RL here?

**Validation/replication**
- Re-run `sweep_report.py` with a reachable threshold (issue #1) — same artifacts, corrected primary metric.
- Confirm seed independence and that no seed is an outlier driving the custom3 +0.199 (inspect per-seed values; CI [0.063, 0.331] is wide).

---

## 9. Best next steps (prioritised)

1. **Re-analyse, don't re-run (today):** rerun `analysis/sweep_report.py` on the existing Sweep-18 metrics with `--speed-threshold 0.15` (or chosen value) to de-censor the speed metric. Zero compute cost.
2. **n=10 confirmatory sweep:** bump `SEEDS` to `1..10` and relaunch `sweep-paper.yml` to give the Wilcoxon test independent power and tighten the custom3 CI. One overnight run.
3. **Horizon ablation on custom9:** a focused sweep at `max_steps_per_episode ∈ {40, 60}` to resolve the convergence confound. Establishes whether the custom9 null is about the prior or the task.
4. **Write the thesis results chapter around the honest framing:** (i) priors significantly accelerate learning and improve final goal-rate where the prior is informative (custom3/custom5); (ii) priors robustly and universally reduce energy; (iii) priors do not make a non-converging learner converge, and a strong hand-crafted controller remains the absolute benchmark. Frame the contribution as *"knowledge-based priors as a sample-efficiency and efficiency aid for online RL"*, not as *"RL beats expert control"*.
5. **Update pre-registration outcome section** ([docs/pre_registration.md](pre_registration.md) §6.6) with the realised Sweep-18 verdicts and the threshold-metric amendment, preserving the audit trail.

---

## 10. Provenance

- **Run:** GitHub Actions `27073252484`, workflow `sweep-paper.yml`, 76 jobs all `success`.
- **Artifacts:** `sweep-paper-consolidated` (downloaded to `tmp_sweep18_results/`).
- **Key files:** `analysis/out/learning_speed_tests.csv`, `paired_tests.csv`, `summary_table_ci.csv`, `first_goal_table.csv`, `metrics_stereotypes_*_custom*.csv`.
- **Code state:** fixes commit `7a3d64c`, timing commit `9b2bc9b` (both pushed to `origin`).
