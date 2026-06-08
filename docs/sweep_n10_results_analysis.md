# Sweep n=10 confirmatory replication — results & statistical analysis

**Run:** GitHub Actions `sweep-paper.yml` run `27094219403` (commit `9b2bc9b`, branch `main`).
**Design:** paper profile (10 000 episodes, VDN 4-zone learner, constructive optimistic init
`stereo_init_bonus=15`, `reward_clip=200`, PBRS shaping), profiles `{custom3, custom5, custom9}`,
two conditions `stereo ∈ {true, false}`, **seeds 1–10** (n = 10), 5 benchmark runs × 140 scenarios.
**Outcome:** 152/152 CI jobs green; wall-clock ≈ 9 h 40 m (queued in waves; per-cell < 6 h).
**This run is the SW18-B confirmatory replication** registered in
[pre_registration.md §6.7](pre_registration.md). It doubles the n=5 Sweep-18 sample to clear the
Wilcoxon signed-rank floor (at n=5 the smallest attainable two-sided p is 0.0625, which cannot
reach 0.05; at n=10 the floor drops to 0.00195).

> **Data-recovery note (provenance / honesty).** The aggregate `sweep-paper-consolidated`
> artifact had two consolidation flakes: `results_seed9` was absent and `results_seed8` was
> missing its `custom5`/`custom9`/`rule_based` benchmark CSVs. All 152 *jobs* succeeded, so the
> underlying per-job artifacts were intact; the missing trees were re-downloaded from the
> individual `*-seed-8` / `*-seed-9` artifacts and merged back, then the aggregation was re-run.
> The tables below are the clean **n = 10** result (every contrast `seeds_paired = 1…10`). The
> learning-speed metrics use the corrected `analysis/sweep_report.py` (AUC declared primary;
> `episodes_to_threshold` flagged `censored_frac = 1.0`).

---

## 1. Executive summary

The n=10 replication **confirms and sharpens** every Sweep-18 (n=5) conclusion, and now does so
at the strongest significance the test can produce:

1. **The stereotype prior helps on `custom3` and `custom5`** — higher benchmark goal-rate, faster
   learning (AUC), and lower energy, all at q ≤ 0.002.
2. **On the registered headline lab `custom9` the prior does *not* help goal-rate (null) and
   *significantly hurts* learning speed** (AUC Δ = −0.062, q ≈ 0). This is no longer a weak
   unfavourable trend (n=5: Δ −0.042) — at n=10 it is a clean, significant negative.
3. **Energy efficiency is the universal, maximally-significant win:** `ql_true` cuts average
   energy on all three labs (Cliff's δ = −1.0, q ≈ 0 everywhere).
4. **The hand-written `rule_based` controller still dominates RL** on `custom5`/`custom9`
   (δ = −1.0) and draws on `custom3`.

The thesis claim *"stereotype-informed Q-learning learns faster and more efficiently"* is
**supported on 2/3 labs for speed and 3/3 for energy**, but is **contradicted for learning speed
on the headline lab `custom9`**. The custom9 result remains confounded (prior-misleads vs
task-unsolvable) and motivates the SW18-A horizon ablation.

---

## 2. Primary confirmatory outcome — H1 benchmark goal-rate

Paired `ql_true − ql_false` across seeds, Benjamini–Hochberg q over the confirmatory family.

| Profile | goal-rate `ql_false` | goal-rate `ql_true` | Δ (true−false) | Wilcoxon p | Cliff's δ | BH q |
|---|---|---|---|---|---|---|
| custom3 | 0.048 [0.033, 0.069] | 0.211 [0.129, 0.296] | **+0.163** | 0.0078 | 0.62 | **0.000** ✓ |
| custom5 | 0.026 [0.018, 0.036] | 0.090 [0.074, 0.111] | **+0.064** | 0.0020 | 0.99 | **0.000** ✓ |
| custom9 | 0.107 [0.091, 0.123] | 0.105 [0.082, 0.127] | −0.002 | 0.89 | 0.05 | 0.872 (null) |

- **custom3 / custom5:** robust positive effect of the prior, both q = 0.000. custom5's δ = 0.99
  means the prior helped on essentially every seed.
- **custom9:** dead null (Δ ≈ 0, δ ≈ 0.05). The prior neither helps nor hurts the final
  goal-rate on the headline lab — consistent with n=5 (Δ +0.007 there).

## 3. Primary learning-speed metric — AUC of the goal-rate curve (pre-declared primary)

`auc_goal` = normalised mean height of the per-episode goal-rate learning curve (higher = faster
learning). Paired `ql_true − ql_false`; `episodes_to_threshold` is omitted from inference because
it is right-censored at the 10 000-episode horizon for every arm (`censored_frac = 1.0`, see §6.7
of the pre-registration — threshold deliberately not retuned).

| Profile | `auc_goal` false | `auc_goal` true | Δ (true−false) | 95% CI | Wilcoxon p | δ | BH q | verdict |
|---|---|---|---|---|---|---|---|---|
| custom3 | 0.0895 | 0.1620 | **+0.073** | [0.024, 0.126] | 0.037 | 0.64 | **0.0016** | favourable ✓ |
| custom5 | 0.0467 | 0.0873 | **+0.041** | [0.019, 0.059] | 0.020 | 0.84 | **0.0016** | favourable ✓ |
| custom9 | 0.1697 | 0.1080 | **−0.062** | [−0.082, −0.036] | 0.0039 | −0.84 | **0.000** | **unfavourable** ✗ |

This is the headline statistical result of the replication. On `custom9` the **base learner
without the prior learns *faster*** (AUC 0.170 vs 0.108): the optimistic stereotype initialisation
actively suppresses the goal-rate curve. At n=5 this was a δ = −0.6 trend; at n=10 it is
significant (q ≈ 0) with a large effect size.

### Secondary learning-speed metrics

| Profile | `auc_reward` Δ (q) | `mean_first_goal` Δ (q) — higher = slower to first goal |
|---|---|---|
| custom3 | +19.3 (q 0.0016) ✓ | +805 (q 0.000) — **slower** to first goal under prior |
| custom5 | −1.6 (q 1.0, ns) | +119 (q 0.55, ns) |
| custom9 | −27.0 (q 0.000) ✗ | +117 (q 0.11, ns) |

`mean_first_goal` is *higher* (slower) under the prior wherever it is significant — the
optimistic-init exploration cost: the agent explores more before its first success, even on labs
where the prior ultimately helps the asymptote (custom3). This is the expected, honest trade-off
of constructive optimistic initialisation.

## 4. Energy efficiency (`avg_energy`, paired `ql_true − ql_false`)

| Profile | Δ avg_energy (true−false) | Wilcoxon p | Cliff's δ | BH q |
|---|---|---|---|---|
| custom3 | **−81.8** | 0.0020 | −1.0 | 0.000 |
| custom5 | **−71.4** | 0.0020 | −1.0 | 0.000 |
| custom9 | **−47.1** | 0.0020 | −1.0 | 0.000 |

The most robust finding in the thesis: the stereotype prior reduces average energy on **every lab,
every seed** (δ = −1.0), at the maximum significance n=10 permits (p = 0.00195). Even on `custom9`,
where the prior hurts learning speed, it still saves energy — the agent reaches comparable
goal-rates via lower-energy trajectories.

## 5. RL vs hand-written controller (`rule_based`)

Paired `ql_true − rule_based` goal-rate:

| Profile | Δ (ql_true − rule) | Wilcoxon p | δ | verdict |
|---|---|---|---|---|
| custom3 | +0.032 | 0.65 | 0.20 | draw (slight RL edge, ns) |
| custom5 | −0.160 | 0.0020 | −1.0 | rule_based dominates |
| custom9 | −0.145 | 0.0020 | −1.0 | rule_based dominates |

The expert controller still beats the learner on the two harder labs. The honest framing remains:
**stereotype priors deliver sample-efficiency and energy benefits to the learner; they do not make
the tabular RL agent beat hand-written expert control on these tasks.**

---

## 6. What n=10 changed vs n=5 (Sweep-18)

| Result | n=5 (Sweep-18) | n=10 (this run) | change |
|---|---|---|---|
| custom3 goal-rate | Δ+0.199, q 0.0016 | Δ+0.163, **q 0.000** | confirmed, tighter |
| custom5 goal-rate | Δ+0.074, q<0.001 | Δ+0.064, q 0.000, δ 0.99 | confirmed |
| custom9 goal-rate | Δ+0.007, q 0.81 | Δ−0.002, q 0.87 | confirmed null |
| custom9 `auc_goal` | Δ−0.042, δ−0.6 (trend) | **Δ−0.062, q 0.000, δ−0.84** | now **significant** |
| energy (all labs) | δ−1.0, q<0.001 | δ−1.0, **q 0.000** (p-floor) | confirmed, maximal |
| Wilcoxon floor | 0.0625 (can't reach .05) | **0.00195** | **floor problem solved** |

The n=10 replication did exactly what it was registered to do: it cleared the Wilcoxon
signed-rank floor, so the custom9 unfavourable learning-speed effect and all energy effects now
reach significance, and it confirmed the custom3/custom5 positives without surprises.

---

## 7. Reportable statistics (paste-ready for the thesis)

- **H1 (prior improves benchmark goal-rate):** supported on custom3 (Δ +0.16, q < 0.001, δ 0.62)
  and custom5 (Δ +0.06, q < 0.001, δ 0.99); null on the headline lab custom9 (Δ −0.002, q = 0.87).
  Paired bootstrap (10 000 iters) + Wilcoxon signed-rank, BH-corrected, n = 10 seeds.
- **Learning speed (primary = AUC of goal-rate curve):** prior accelerates learning on custom3
  (Δ +0.073, q = 0.002) and custom5 (Δ +0.041, q = 0.002), but *significantly slows* it on
  custom9 (Δ −0.062, 95 % CI [−0.082, −0.036], q < 0.001, δ −0.84).
- **Energy efficiency:** prior reduces average energy on all three labs (Δ −47 to −82 units,
  δ = −1.0, q < 0.001) — the most robust effect in the study.
- **Method note:** `episodes_to_threshold` is right-censored at the horizon for all arms
  (goal-rate plateaus 0.10–0.21 < 0.50 threshold); AUC is the pre-declared primary speed metric
  and the threshold was not retuned (no HARKing).

---

## 8. Remaining issues & open questions

1. **The custom9 confound is now a *significant negative*, not just a null.** The prior makes the
   learner *slower* on custom9 (AUC: false 0.170 > true 0.108). Two hypotheses remain entangled:
   (a) the optimistic stereotype init pushes the agent toward an unhelpful region of policy space
   on this lab; or (b) custom9 is not solvable in the 20-step horizon by the tabular learner, so
   any prior just adds exploration overhead. **The SW18-A horizon ablation is required to
   disentangle these.**
2. **Non-convergence persists.** The base custom9 learner plateaus (~17 % goal-rate AUC) — raising
   the budget to 10 000 episodes (SW17-3) did not unlock convergence, consistent with Sweep-18.
3. **rule_based still wins on 2/3 labs** — the thesis must be framed around sample-efficiency and
   energy, not raw task performance vs expert control.

## 9. Best next actions

In priority order:

1. **Launch the SW18-A horizon ablation now** (it is the single experiment that resolves the
   custom9 confound — the most important open question after this run). Configs are already
   prepared (`paper_h40`, `paper_h60` in `config/run_config.json`; `run_mode` input in the
   workflow). Run one at a time (the `sweep-paper` concurrency group serialises them), do **not**
   publish (keep n=10 as the canonical `results` branch):
   ```powershell
   gh workflow run sweep-paper.yml -f profiles=custom9 -f run_mode=paper_h40 -f publish_results=false
   # after it finishes:
   gh workflow run sweep-paper.yml -f profiles=custom9 -f run_mode=paper_h60 -f publish_results=false
   ```
   - If a longer horizon lets the *base* learner converge on custom9 → the null/negative is a
     **prior problem** (the stereotype misleads on this lab).
   - If custom9 stays flat even at 40/60 steps → the lab is **unsolvable for the tabular learner**
     and the custom9 result should be reported as out-of-scope rather than a prior failure.
2. **Publish the n=10 run to the `results` branch** as the canonical confirmatory dataset (re-run
   with `publish_results=true`, or version it), so the thesis cites a single immutable artifact.
3. **Write up the confirmatory results** using §7 — the statistics are now thesis-grade
   (BH-corrected, n=10, pre-registered primary metrics).
4. **Frame the contribution honestly:** stereotype priors are a *sample-efficiency and
   energy-efficiency* mechanism that helps on 2/3 labs and saves energy universally — not a
   method that beats expert control. The custom9 negative is a genuine, reportable finding about
   where ontology-derived priors can mislead.

---

*Provenance: run `27094219403`, commit `9b2bc9b`; analysis regenerated locally with the corrected
`analysis/sweep_report.py` (metric_tier / censored_frac); per-seed trees reconstructed in
`tmp_sweep_n10_results/benchmark/results_seed{1..10}/`, aggregates in
`tmp_sweep_n10_results/analysis_n10/`.*
