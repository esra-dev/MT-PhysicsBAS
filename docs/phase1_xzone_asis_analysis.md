# Phase 1 — Statistical Analysis of the `phase1_kg_xzone` Run (cross-zone spill *as-is*)

> **HISTORICAL, PROTOCOL-AFFECTED (2026-07-21).** In addition to the provenance limits
> below, the scheduler and metric defects withdraw this run as thesis-final evidence.
> The corrected protocol-v2 results supersede it regardless of direction.

> **PROVENANCE (2026-07-19) — pre-inversion, superseded-physics record.** This run
> predates the action-space inversion of 2026-07-10 (`docs/ACTION_SPACE_INVERSION.md`),
> and its lab3 spill physics — the original **+50 lux / 0.25·Sun** stated below — was
> superseded on 2026-07-08 by the current intermediate magnitudes (**+100 lux /
> 0.30·Sun**). Quote the numbers below only as pre-inversion, original-physics
> measurements. The phrase “headline of record” below means the historical 2026-07-19
> status only. The current record is `docs/phase1_results_v2.md`.

**Run:** GitHub Actions *Phase 1 #11*, workflow `phase1.yml`
**Ref / commit:** `kg-crosszone-coupling` @ `866297d`
**Profile (`run_mode`):** `phase1_kg_xzone` — KG structural prior **ON** + Part-B cross-zone
exploration prior (`cross_zone_bonus = 3.0`); PBRS **off**, adaptive-trust **off**.
**Design:** paired, `n = 10` seeds (1…10), three labs (lab1 trivial → lab2 medium →
lab3 complex), three policies per lab (`rule_based`, `ql_false` = tabula-rasa Q-learning,
`ql_true` = KG-primed Q-learning).
**Simulator physics:** cross-zone spill **unchanged** (lamp bleed `+50` lux; blind bleed
`0.25·Sun`). This is the *baseline magnitude* arm of the planned A/B.
**Wall-clock:** 48 m 47 s · **Artifacts:** 152 · **Status:** Success.
**Consolidated data:** `phase1_xzone_asis/analysis/out/`.

---

## 1. Executive summary

| Lab | Hypothesis (KG faster, fewer redundant, equal success) | Verdict |
|---|---|---|
| **lab1** (trivial, 1 zone) | Expected *null* — nothing to accelerate | **Confirmed null** (both agents optimal, identical) |
| **lab2** (medium, 2 independent zones) | KG faster + fewer redundant + equal success | **Confirmed — strong, BH-significant** |
| **lab3** (complex, cross-zone spill) | KG faster *because it knows the spill structure* | **Not confirmed at this magnitude** — KG ≈ or slightly **worse** on the primary learning-speed metric; success parity preserved |

**Bottom line.** The anchor finding of the thesis — *"a physics-primed Q-learner learns
faster and wastes fewer actions than a tabula-rasa Q-learner, at equal task success, in a
clean environment"* — is **cleanly and significantly demonstrated on lab2** and behaves
exactly as expected (null) on the trivial lab1. **lab3 does not yet show the predicted KG
advantage** with the spill magnitude *as-is*: the cross-zone coupling is **sub-rank**
(below the discretiser's resolution), so the structural prior has *no learnable value to
exploit*, and the Part-B exploration bonus slightly **increases cycling** without a
corresponding speed gain. This is a scientifically clean, expected limitation — and it is
the precise empirical motivation for the controlled **magnitude-bump A/B** (§7).

The run **worked correctly** in every mechanical sense (all 150 cells passed, feature code
byte-clean, negative-control lab1 behaved as designed). The lab3 outcome is a *true
result*, not a bug.

---

## 2. Method & statistics (for reproducibility)

* **Pairing.** Each seed `s` produces a `ql_true` and a `ql_false` policy from an
  *identical* environment seed; metrics are differenced within-seed (`Δ = ql_true −
  ql_false`), removing between-seed variance. `n = 10` paired observations per test.
* **Estimator & interval.** Mean paired difference with a **bias-corrected bootstrap 95 %
  CI** (10 000 resamples). A CI excluding 0 ⇒ a directional effect.
* **Tests.** Two-sided bootstrap `p`, one-sided *favorable* `p`, exact **Wilcoxon
  signed-rank** `p`, and **Cliff's δ** (non-parametric effect size; |δ|: 0.15 small, 0.33
  medium, 0.47 large).
* **Multiplicity.** Benjamini–Hochberg FDR within pre-registered families
  (`q_bootstrap_bh`); confirmatory family `m = 42`, learning-speed family `m = 12`. **All
  significance claims below use the BH-corrected `q`.**
* **Metric tiers.** *Primary* learning-speed metric = `auc_goal` (area under the
  goal-achieved-vs-episode training curve; ↑ = reaches goal earlier/more often during
  learning). *Secondary* = `auc_reward`, `mean_first_goal`. Benchmark (final-policy)
  metrics from `summary_table_ci.csv`: `goal_rate` (success), `avg_steps` (time-to-goal),
  `avg_redundant` / `avg_wasted` / `avg_cycling` (action economy), `avg_energy`.

---

## 3. Final-policy benchmark (n = 10, mean [95 % CI])

From `phase1_xzone_asis/analysis/out/summary_table_ci.csv` · branch `kg-crosszone-coupling`@`866297d` · GH run `27440842780` · `analysis/sweep_report.py::aggregate_seeds`. **Lower is better** for every column except `goal_rate`.

| Lab | Policy | goal_rate | avg_steps | avg_redundant | avg_cycling | avg_energy |
|---|---|---|---|---|---|---|
| lab1 | ql_false | 1.000 [1.00,1.00] | 0.500 | 0.463 | 0.000 | 4.44 |
| lab1 | **ql_true** | 1.000 [1.00,1.00] | 0.500 | 0.470 | 0.000 | 4.35 |
| lab1 | rule_based | 1.000 | 0.500 | 0.468 | 0.000 | 4.32 |
| lab2 | ql_false | 0.981 [0.96,1.00] | 1.631 [1.31,2.01] | 2.164 [1.81,2.58] | 0.588 | 11.01 |
| lab2 | **ql_true** | 1.000 [1.00,1.00] | **1.169 [1.13,1.21]** | **1.581 [1.50,1.66]** | **0.481** | **9.86** |
| lab2 | rule_based | 1.000 | 0.938 | 1.126 | 0.250 | 9.84 |
| lab3 | ql_false | 0.963 [0.94,0.99] | 1.900 [1.45,2.36] | 2.466 [2.03,2.93] | 0.625 | 17.21 |
| lab3 | **ql_true** | 0.988 [0.97,1.00] | 1.525 [1.27,1.83] | 2.406 [1.90,3.00] | **0.963** | 16.57 |
| lab3 | rule_based | 1.000 | 0.875 | 1.135 | 0.313 | 12.69 |

`rule_based` is an oracle upper bound (hand-coded optimal controller); neither learner is
expected to beat it, only to approach it.

---

## 4. Confirmatory paired tests — `ql_true` vs `ql_false` (BH-corrected)

From `phase1_xzone_asis/analysis/out/paired_tests.csv` · confirmatory family, BH `m = 42` · `analysis/sweep_report.py::_bh_qvalues`. Negative `mean_diff` = KG **better** for
lower-is-better metrics.

| Lab | Metric | mean_diff (Δ) | 95 % CI | Wilcoxon p | Cliff's δ | **q (BH)** | KG verdict |
|---|---|---|---|---|---|---|---|
| lab2 | avg_steps | **−0.463** | [−0.83, −0.15] | 0.0039 | −0.68 | **0.000** | **faster ✓** |
| lab2 | avg_redundant | **−0.582** | [−0.96, −0.26] | 0.0020 | −0.76 | **0.000** | **fewer redundant ✓** |
| lab2 | avg_wasted | **−0.476** | [−0.84, −0.16] | 0.0020 | −0.79 | **0.000** | **less wasted ✓** |
| lab2 | avg_cycling | **−0.106** | [−0.18, −0.04] | 0.039 | −0.50 | **0.0037** | **less cycling ✓** |
| lab2 | avg_energy | **−1.151** | [−2.21, −0.22] | 0.049 | −0.62 | **0.018** | **less energy ✓** |
| lab2 | goal_rate | +0.0188 | [0.00, 0.038] | 0.25 | +0.30 | 0.120 | parity (trend ↑) |
| lab3 | avg_steps | −0.375 | [−0.96, 0.26] | 0.281 | −0.20 | 0.399 | n.s. (trend faster) |
| lab3 | avg_redundant | −0.060 | [−0.83, 0.86] | 0.625 | −0.08 | 1.000 | **no difference** |
| lab3 | avg_cycling | **+0.338** | [0.06, 0.67] | 0.0996 | +0.50 | **0.025** | **worse (more cycling) ✗** |
| lab3 | goal_rate | +0.025 | [−0.013, 0.063] | 0.359 | +0.32 | 0.399 | parity (trend ↑) |

---

## 5. Learning-speed tests — `ql_true` vs `ql_false` (BH-corrected)

From `phase1_xzone_asis/analysis/out/learning_speed_tests.csv` · learning-speed family, BH `m = 12` · `analysis/sweep_report.py::learning_speed_tests`.

| Lab | Metric (tier) | dir | Δ (true−false) | 95 % CI | **q (BH)** | Cliff's δ | KG verdict |
|---|---|---|---|---|---|---|---|
| lab1 | auc_goal (primary) | ↑ | 0.000 | [0,0] | 1.000 | 0.00 | null (saturated) |
| lab2 | **auc_goal (primary)** | ↑ | **+0.0123** | [0.009, 0.016] | **0.000** | **+1.00** | **faster ✓** |
| lab3 | **auc_goal (primary)** | ↑ | **−0.0089** | [−0.014, −0.003] | **0.0072** | **−0.67** | **slower ✗** |
| lab1 | auc_reward (sec) | ↑ | +0.92 | [0.01, 1.80] | 0.107 | +0.50 | trend ↑ |
| lab2 | auc_reward (sec) | ↑ | **+7.54** | [4.18, 11.15] | **0.000** | +0.72 | **higher ✓** |
| lab3 | auc_reward (sec) | ↑ | **+14.51** | [7.47, 21.86] | **0.000** | +0.80 | **higher ✓** |
| lab2 | mean_first_goal (sec) | ↓ | −10.3 | [−40.2, 18.5] | 0.990 | −0.20 | n.s. |
| lab3 | mean_first_goal (sec) | ↓ | −0.95 | [−18.1, 15.3] | 1.000 | +0.04 | n.s. |

---

## 6. Interpretation per lab

### 6.1 lab1 — expected null (sanity floor)
Both learners and the oracle reach `goal_rate = 1.0` in `0.5` mean steps with identical
action economy; `auc_goal` is saturated at `1.0` for both, so Δ = 0 by construction. With
a single zone and one dominant actuator there is **nothing for a physics prior to
accelerate** — the task is solved on essentially the first informed action. This is the
designed negative-control floor and it passes. *(Secondary `auc_reward` shows a small KG
trend, q = 0.11, not significant.)*

### 6.2 lab2 — the anchor finding, confirmed and statistically robust
This is the textbook result the thesis is built on. With KG priming the agent is, at
**equal success** (`goal_rate` 1.00 vs 0.98, parity):

* **faster** — `avg_steps` −0.46 (q = 0.000, δ = −0.68, *large*); `auc_goal` +0.0123
  (q = 0.000, δ = **+1.00**, i.e. KG wins on *every* seed);
* **more action-economical** — `avg_redundant` −0.58 (≈ 27 % fewer; q = 0.000, δ = −0.76),
  `avg_wasted` −0.48 (q = 0.000), `avg_cycling` −0.11 (q = 0.0037), `avg_energy` −1.15
  (q = 0.018);
* **higher cumulative reward during learning** — `auc_reward` +7.54 (q = 0.000).

Every one of these survives BH-FDR correction. This directly satisfies the advisor's
requested anchor: *"better in time taken to achieve the goal and avoidance of redundant
actions; same in success."* lab2 is the clean, reportable demonstration.

### 6.3 lab3 — KG does *not* accelerate at the as-is spill magnitude
At **equal success** (`goal_rate` 0.988 vs 0.963, parity, q = 0.399) the KG arm shows a
**mixed-to-negative** learning profile:

* **Primary metric goes the wrong way:** `auc_goal` −0.0089 (q = 0.0072, δ = −0.67) — the
  KG agent reaches the goal in a *slightly smaller* fraction of training episodes.
* **More cycling:** `avg_cycling` +0.34 (q = 0.025, δ = +0.50) — the agent toggles
  actuators on/off more, the signature of unproductive exploration.
* **No redundant-action win** (Δ = −0.06, q = 1.0) and **no significant speed win**
  (`avg_steps` Δ = −0.375, q = 0.399).
* **One positive:** `auc_reward` +14.5 (q = 0.000, δ = 0.80) — higher cumulative reward,
  attributable to overshoot/energy avoidance from the *same-zone* prior + Rule-3 (not to
  the cross-zone lever).

**Why this is expected, not a failure.** lab3's cross-zone spill is **sub-rank** relative
to the fixed discretisation bounds `[50, 100, 300]` lux (materialised
`ws:rankBound_1/2/3`, *not* runtime-recalibrated, so the resolution is stable): a `+50` lux
lamp bleed or a `0.25·Sun` blind bleed almost never crosses a rank boundary. A standalone
structural audit over the entire lab3 transition space found the cross-zone direction
prediction is **wrong 80.5 %** of the time precisely because the rank does not move.
Consequently:

1. The cross-zone coupling carries **almost no learnable value** — the same-zone lamp
   (`+400` lux) alone reaches every goal, so cross-zone activation is *never required*.
2. The Part-B bonus (`cross_zone_bonus = 3.0`) nudges the agent to **try** the cross-zone
   lever anyway; RL correctly learns it is worthless, but the *exploration of a
   low-value action* costs extra cycling and a slightly worse goal-curve.

This reproduces — on a *third independent run* — the pattern already seen in
`phase1_kg_only` and `phase1_kg_only_ib5`: **KG isolates a clean win on lab2, but on lab3
the bare optimistic prior over-explores the 2048-state space and does not accelerate.**
The convergence of three runs on the same lab3 signature is strong evidence that the
limiting factor is the **environment magnitude**, not the prior's tuning.

---

## 7. Did it work? — answer to the two questions

**"Did it work correctly?"** — **Yes, mechanically and scientifically.** All 60 training
cells and 90 benchmark cells passed; the feature branch is byte-clean on the headline arm;
lab1 behaved as the designed null; lab2 reproduced the anchor finding with large,
FDR-significant effects; lab3 produced an interpretable, reproducible result consistent
with two prior runs. There is no defect to fix.

**"Are the results as we expected?"** — **Partially, and informatively:**
* lab1 ✓ (expected null), lab2 ✓✓ (expected and confirmed strongly).
* lab3 ✗ on the *primary* metric: we hoped the KG's knowledge of the spill **structure**
  would let it learn faster. It did not, **because at the current magnitude there is no
  spill value to learn** — the coupling is below the discretiser's resolution. The KG was
  *correct* (the cross-zone effect really is negligible), so it had nothing to gain.

This is exactly the situation the **magnitude bump** was designed to test: *if* the
cross-zone coupling is raised to a **rank-moving** size, the spill becomes a real,
learnable contributor, and the agent that **already knows which components spill** should
then convert that structural knowledge into a measurable learning-speed advantage — while
the tabula-rasa agent must first *discover* the cross-zone dependency by trial and error.
The as-is run is the **control**; the bumped run is the **treatment**. Running both and
comparing the two consolidated artifacts is the clean A/B that turns the lab3 limitation
into a positive, publishable result.

---

## 8. Threats to validity (stated honestly)

1. **Non-monotone prior strength.** Earlier sweeps showed the lab3 outcome is non-monotone
   in `stereo_init_bonus` (15 → 5 made lab3 *worse*, not better). The cross-zone result
   must therefore be read as *"at the standard prior strength"*; the bump changes the
   **environment**, not the prior, which is the cleaner intervention.
2. **`auc_reward` vs `auc_goal` divergence on lab3.** The KG arm earns more reward yet hits
   the binary goal slightly less often early. Reward includes energy/overshoot terms, so
   the two need not agree; the **pre-registered primary** metric is `auc_goal`, and that is
   the one reported as the headline for lab3.
3. **Single-seed snapshot is misleading.** `summary_table.csv` (seed 1 only) shows lab3
   `ql_true` much worse than `ql_false`; the `n = 10` `summary_table_ci.csv` does **not**
   reproduce that — seed 1 is an unrepresentative draw. Only the multi-seed CI is
   interpretable.
4. **Oracle gap on lab3.** Both learners trail `rule_based` on lab3 action economy; this is
   the expected cost of online exploration in a 2048-state space and is *not* a KG-specific
   defect (the tabula-rasa agent trails further on `avg_steps` and `goal_rate`).

---

## 9. Reproduction

```powershell
# Data downloaded to phase1_xzone_asis/analysis/out/
# Key files:
#   summary_table_ci.csv      final-policy benchmark, n=10 95% CI
#   paired_tests.csv          confirmatory ql_true vs ql_false (BH q)
#   learning_speed_tests.csv  auc_goal (primary) + auc_reward (secondary)
#   learning_curve_lab{1,2,3}.png   per-episode goal curves
```

The bumped-magnitude treatment run and its A/B comparison protocol are specified in
[kg_crosszone_coupling_fix.md](kg_crosszone_coupling_fix.md) §7 and in the run command
issued alongside this analysis.

---

## Source Index

All paths relative to the workspace root.

### CI run metadata

| Property | Value |
|---|---|
| GH Actions run | `27440842780` |
| Workflow | `.github/workflows/phase1.yml` |
| Branch | `kg-crosszone-coupling` |
| Commit | `866297d` |
| Profile (`run_mode`) | `phase1_kg_xzone` |
| Seeds | 1–10 |
| Role | **Control arm** of the magnitude A/B (as-is / sub-rank physics) |

### Data files

| File | Contents | Used in |
|---|---|---|
| `phase1_xzone_asis/analysis/out/summary_table_ci.csv` | Final-policy benchmark means + 95 % CI per (lab, mode), n=10 seeds. | §3 |
| `phase1_xzone_asis/analysis/out/paired_tests.csv` | `(lab, metric, mode_pair)` paired bootstrap tests, BH q (confirmatory m=42). | §4 |
| `phase1_xzone_asis/analysis/out/learning_speed_tests.csv` | `(lab, metric)` learning-speed paired tests, BH q (m=12). | §5 |

### Simulator & physics

| File | Role |
|---|---|
| `simulator/simulator_flow_lab3.json` | lab3 Node-RED flow. **As-is (sub-rank) magnitude:** lamp bleed `+50` lux; blind bleed `0.25·Sun`. Cross-zone wrong-prediction rate 80.5 % — see `analysis/crosszone_prediction_audit.py --structural-only`. |
| `simulator/simulator_flow_lab1.json` | lab1 (unchanged). |
| `simulator/simulator_flow_lab2.json` | lab2 (unchanged). |

### Ontology & knowledge graph

| File | Role |
|---|---|
| `src/resources/building_3_complex.ttl` | lab3 ontology: cross-zone `brick:feeds` arcs reified as `WeakOpticalCoupling` connection stereotypes. |
| `src/resources/lab-ontology.ttl` | Core ontology: rank bounds `[50,100,300]` lux, `ws:ivMinRank`, mechanism definitions. |
| `src/resources/wot-mappings.ttl` | Sensor/actuator → ontology URI mappings. |

### Agent & learning code

| File | Role |
|---|---|
| `src/env/tools/QLearner.java` | Q-learning core: `initWithStereotypes()`, `calculateQ()`, `computeZoneReward()`. |
| `src/env/tools/StereotypeReasoner.java` | `getActionPrediction()` (Part-A: SECONDARY arcs emit 0 prediction), `getInitPenaltyForZone()` Rules 1–6. |
| `src/agt/illuminance_controller_agent_ql.asl` | Training (`@train`) and benchmark (`@benchmark`) plans. |
| `src/agt/lab_profiles.asl` | `lab_profile("lab{1,2,3}",…)` — zone targets, bounds, episode budget. |

### Run configuration

| File | Key field | Value |
|---|---|---|
| `config/run_config.json` | `profiles.phase1_kg_xzone` | `cross_zone_bonus=3.0`, `reward_shaping=none`, `adaptive_trust=false`, `stereo_init_bonus=15.0` |
| `run_full_project.ps1` | `-RunMode phase1_kg_xzone` | Orchestrates training → benchmark → analysis. |
| `.github/workflows/phase1.yml` | `run_mode` input | `phase1_kg_xzone` |

### Analysis pipeline

| Script | Function | Output |
|---|---|---|
| `analysis/sweep_report.py` | `aggregate_seeds()`, `_bh_qvalues()`, `learning_speed_tests()` | `summary_table_ci.csv`, `paired_tests.csv`, `learning_speed_tests.csv` |
| `analysis/crosszone_prediction_audit.py` | `--structural-only` | 80.5 % cross-zone wrong-prediction figure (§6.3). |
| `analysis/learning_curves.py` | per-lab curve generation | `learning_curve_lab{1,2,3}.png` |
