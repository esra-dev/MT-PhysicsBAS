# 12 — Statistical Review: Results vs Research Best Practice

**Generated:** 2026-07-07
**Scope:** Judge the NEW-era Phase 1–4 confirmatory results against research best practice:
n per cell, paired vs unpaired inference, choice of test, multiple-comparison correction
(BH-FDR family sizing), the Wilcoxon small-n floor, effect sizes, pre-registration compliance,
and single-instrument claims.
**Inputs read:** `docs/_audit/05_results_index.md`, `docs/pre_registration.md`,
`analysis/sweep_report.py`, `analysis/phase2_recovery.py`, `analysis/phase3_dynamics.py`,
`analysis/phase4_energy.py`, plus the consolidated result CSVs in the canonical download
folders named by 05_results_index §7.
**Era note:** All verdicts below concern the **[NEW]** phase-based results. OLD-era material
(custom8/custom9, H1–H5, Sweeps 17/18) is referenced only where the pre-registration ledger
(§6) requires it.
**Rule:** every number below was read from a file in this workspace and is cited as
`path#Lstart-Lend` (line numbers = the CSV/script line as stored). Absent items are marked
NOT FOUND.

---

## 0. Verdict summary

| Phase | Claim | Verdict | Required action |
|---|---|---|---|
| 1 (xzone bumped + s11–20 replication) | KG prior → faster learning / fewer redundant actions on lab2; auc_reward advantage on lab3 | **STATISTICALLY SOUND** (with 4 mandatory disclosures, §2.5) | Disclose post-hoc registration, Wilcoxon tie-floor, lab3 `auc_goal` null; re-download the four §1.2 headline runs' artefacts |
| 1 (headline runs 27336756264 / 27344626272 / 27342571251) | KG-only acceleration, baseline + ib5 controls | **UNVERIFIABLE LOCALLY** — no artefacts in workspace (05_results_index §1.2) | Restore consolidated CSVs from the `results` branch before citing in the thesis |
| 2 (fault detect / blacklist / re-learn, all iterations) | KG re-aligns faster after blacklisting | **NEEDS-RERUN (analysis only, same data)** | Fix seed-pairing bug, freeze one pooled BH family, pre-declare tier rules (§3.6) |
| 3 — delay-learning accuracy (H-P3a) | ≤5 % relative error, correct classification | **STATISTICALLY SOUND** | none |
| 3 — deadline compliance (H-P3b) | ql_true 2× compliance | **RE-FRAME AS DESCRIPTIVE** — outcome is deterministic by design; p-values are vacuous | Report counts + the D-P3-2 caveat; drop significance language |
| 4 — lab5 energy compliance (primary) | KG arm +0.101 compliance, −25 % power | **STATISTICALLY SOUND** (with 2 mandatory disclosures, §5.5) | Disclose data-dependent n=10→20 escalation; fix the unsupported "pre-registered" label |
| 4 — lab4 dependency efficiency | fewer steps/redundant actions | **STATISTICALLY SOUND** (minor family-inflation note, §5.3) | none blocking |
| 4 — KG-QL vs LLM | KG beats LLM proxy on energy compliance | **EXPLORATORY / DESCRIPTIVE ONLY** — single deterministic instrument, no inference | Label exploratory; no CI or test exists for it |

---

## 1. The shared statistical machinery (all phases)

All four scripts route inference through the same helpers in `analysis/sweep_report.py`
(imported by the other three: `analysis/phase2_recovery.py#L62-L70`,
`analysis/phase3_dynamics.py#L76-L86`, `analysis/phase4_energy.py#L67-L75`):

| Component | Implementation | Assessment |
|---|---|---|
| Bootstrap CI (per-arm mean) | percentile bootstrap, 10 000 resamples, fixed RNG seed `0xC1`, NaN when n<2 — `analysis/sweep_report.py#L315-L346` | Good: deterministic, no normality assumption. Known caveat: percentile bootstrap under-covers at n=10 (nominal 95 % ≈ 91–93 % actual); acceptable here because every confirmatory claim is triangulated with Wilcoxon + Cliff's δ |
| Paired bootstrap diff + p | pairwise resample of within-seed differences; two-sided p = doubled tail **anchored on the observed sign**, plus both one-sided tails — `analysis/sweep_report.py#L440-L492` (anchoring at `#L471-L474`) | The anchored convention is a registered deviation (pre-reg D6-2, `docs/pre_registration.md#L315-L327`) and agrees with the min-tail convention wherever the mean and bootstrap median share a sign — true for every significant cell inspected. Acceptable |
| Wilcoxon signed-rank | `scipy.stats.wilcoxon`, two-sided, `zero_method="wilcox"` (zeros dropped) — `analysis/sweep_report.py#L495-L507` | Correct implementation, but zero-dropping re-creates the small-n floor under ties (§1.1) |
| Cliff's δ | exact pairwise count — `analysis/sweep_report.py#L510-L521` | Effect size reported for every paired row in every phase CSV ✓ |
| BH-FDR | monotone step-up, NaN-preserving — `analysis/sweep_report.py#L524-L539`; family membership and per-row `bh_family_m` recorded — `#L605-L614` | Mechanically correct. Family *definitions* are the problem in Phase 2 (§3.3) and mildly in Phase 4 (§5.3) |

### 1.1 The Wilcoxon floor — where it bites

The two-sided signed-rank p-value cannot go below `2/2^n`. Floors: n=5 → 0.0625; n=6 →
0.03125; n=9 → 0.0039; n=10 → 0.001953. The project knows this (registered as D-P3-1,
`docs/pre_registration.md#L675`) and bumped Phase 3 to n=10 accordingly. **But the floor
re-enters through ties**: `zero_method="wilcox"` (`analysis/sweep_report.py#L504`) drops
zero differences, so a cell with n_paired=10 and 5 tied seeds has an *effective* n of 5 and
a floor of 0.0625 > 0.05.

Observed instance: Phase 1 bumped run, lab2 `goal_rate`, `n_paired=10`, `p_wilcoxon=0.0625`
(exactly `2/2^5`) while the bootstrap gives q=0.0090
(`phase1_xzone_bumped/analysis/out/paired_tests.csv#L5`); identical 0.0625 in the s11–20
replication (`phase1_xzone_bumped_s11_20/analysis/out/paired_tests.csv`, lab2 goal_rate row).
Consequence: **for low-variance bounded metrics (goal_rate near ceiling), the Wilcoxon column
is structurally uninformative and must not be cited as the decisive test.** The bootstrap +
Cliff's δ carry those cells — which is how the scripts already rank them; the thesis text
just has to say so.

### 1.2 Pairing discipline

Phase 1 / Phase 4 sweep-report tests pair strictly by seed id
(`analysis/sweep_report.py#L574-L578`: intersection of seeds, values indexed by seed key) and
record `seeds_paired` per row ✓. Phase 3 pairs by replica list position, which is safe there
because every replica produced a row (n=10/10 in every cell,
`phase3_download_n10/.../phase3_compliance_ci.csv#L2-L5`). **Phase 2 pairs by truncated list
position after success-filtering, which is not safe — see §3.2, the most serious defect in
this review.**

---

## 2. Phase 1 — KG acceleration on clean labs (runs 27440842780 / 27461188614 / 27462446044 / 27464846574)

### 2.1 Design and n

10 paired training seeds per cell (seeds 1–10 headline, 11–20 replication), 3 modes, 3 labs;
paired contrast is `ql_true − ql_false` within seed
(`phase1_xzone_bumped/analysis/out/paired_tests.csv` — every row shows `n_paired=10`,
`seeds_paired=1;…;10`). Confirmatory family m=42 (all benchmark paired tests, 2 confirmatory
mode-pairs), exploratory family m=21, learning-speed family m=12 — matching the registered
family table (`docs/pre_registration.md#L581-L589`) and recorded per row (`bh_family_m`
columns). n=10 paired, with an independent 10-seed replication, is adequate for the observed
effect sizes (δ = 0.5–1.0 on the significant cells).

### 2.2 Hypothesis outcomes against pre-registration §7.3

| Hypothesis | Registered test | Bumped run (27461188614) | s11–20 replication (27462446044) | Verdict |
|---|---|---|---|---|
| H-CL1: lab2 `auc_goal` ↑ | paired bootstrap, q≤0.05, CI>0 | Δ=+0.0197, CI [0.0147, 0.0245], q=0.0, δ=1.0 — `phase1_xzone_bumped/analysis/out/learning_speed_tests.csv#L6` | Δ=+0.0182, CI [0.0106, 0.0273], q=0.0, δ=1.0 — `phase1_xzone_bumped_s11_20/analysis/out/learning_speed_tests.csv#L6` | **Confirmed, replicated** |
| H-CL2: lab1 null control | zero cells reject | all lab1 rows q=1.0, Δ=0 or CI spans 0 — `paired_tests.csv#L2,L11,L20,L29,L38,L47,L56` and `learning_speed_tests.csv#L2-L5` | same | **Confirmed** |
| H-CL3: lab2 `avg_redundant` ↓ | CI<0, q≤0.05 | Δ=−0.983, CI [−1.590, −0.399], q=0.0, δ=−0.72 — `paired_tests.csv#L59` | Δ=−1.001, CI [−1.525, −0.500], q=0.0, δ=−0.70 (PowerShell extract of s11–20 `paired_tests.csv`) | **Confirmed, replicated** |
| H-CL4: lab3 `auc_reward` ↑ | CI>0, q≤0.05 | Δ=+14.26, CI [11.23, 17.20], q=0.0, δ=1.0 — `learning_speed_tests.csv#L11` | Δ=+18.85, CI [16.21, 21.19], q=0.0, δ=1.0 — s11–20 `learning_speed_tests.csv#L11` | **Confirmed, replicated** |

Honest negative that must stay in the thesis: on lab3 the **primary** learning-speed metric
`auc_goal` is directionally *negative* in both runs (bumped: Δ=−0.00375, q=0.296, δ=−0.4 —
`learning_speed_tests.csv#L10`; replication: Δ=−0.0032, q=0.58, δ=−0.53). The lab3 claim
rests entirely on `auc_reward`, exactly as H-CL4's ceiling rationale anticipated
(`docs/pre_registration.md#L572-L579`) — legitimate because it was written down as the lab3
primary before analysis, but the thesis must not describe lab3 as showing a *goal-rate*
speed advantage. lab3 `goal_rate` itself is null (q=0.41 bumped `paired_tests.csv#L8`;
q=1.0 replication).

### 2.3 Registration timing

§7 of the pre-registration is explicitly **confirmatory-with-post-hoc-registration**: the
addendum was written after data collection, with hypotheses fixed before analysis but not
committed before the first CI result was seen (`docs/pre_registration.md#L525-L529`). This
is disclosed per Munafò et al. — best practice given the pivot — but the thesis Results
section must repeat the disclosure, not cite §7 as if it were pre-data.

### 2.4 Provenance gap (headline §1.2 runs)

The four flat-lab Phase-1 runs (27336756264 kg_only headline, 27344626272 baseline,
27342571251 ib5, 27347962788 pbrs_only-FAILED) have **no local artefacts**; their numbers
exist only in `docs/phase1_results_n10.md` and on the results branch
(`docs/_audit/05_results_index.md#L52-L79`). Any thesis table built from them currently
rests on a single non-verifiable transcription. The pbrs_only control **failed** and was
never re-dispatched (`05_results_index.md#L63`), so the claimed three-arm isolation
(KG vs PBRS vs baseline) is missing its PBRS arm. Fix: re-download the consolidated CSVs
into the workspace (or re-dispatch pbrs_only) before the thesis cites these runs.

### 2.5 Phase 1 verdict

**STATISTICALLY SOUND** for the xzone-bumped + replication + ablation set, conditional on
four disclosures: (1) §7 post-hoc registration timing; (2) Wilcoxon tie-floor → bootstrap is
the decisive test for goal_rate cells (§1.1); (3) lab3 `auc_goal`/`goal_rate` null reported
alongside the `auc_reward` win; (4) the environment "bump" (rank-moving spill magnitude) and
targeted cross-zone bonus are design changes made after the as-is run — the as-is control
(27440842780) and untargeted ablation (27464846574, registered exploratory,
`docs/pre_registration.md#L611-L613`) must be presented as the containing story. The §1.2
headline runs are separately **UNVERIFIABLE LOCALLY** until re-downloaded.

---

## 3. Phase 2 — fault detection / blacklist / re-learn (runs 27547019772 v5, 28590019536 v6, 28745352239 ext, backfill, 28863439179 labmon)

### 3.1 No pre-registration exists for Phase 2

`docs/pre_registration.md` contains addenda for Phase 1 (§7, L511) and Phase 3 (§8, L619)
— **there is no Phase 2 section**. The hypothesis ("recovery(ql_true) < recovery(ql_false)"),
the primary metric (RecoveryEpisodes), the well-posed cell set, the goal-reaching threshold
0.5 (`analysis/phase2_recovery.py#L135-L136`), and the tier system were all defined and
*revised across result iterations* (v1→v5→v6→ext→backfill→labmon,
`docs/_audit/05_results_index.md#L171-L181`). The script's own comment records that the
well-posed gate was introduced because unrestricted cells "previously produced misleading
significant 'KG slower' rows" (`analysis/phase2_recovery.py#L83-L87`) — i.e. the
confirmatory family was narrowed after seeing unfavourable results. The stratifier arguments
(achievability is an environment property, arm-symmetric — `#L163-L166`) are scientifically
defensible, but under Munafò-style standards every Phase-2 significance statement is
**post-hoc/exploratory until the rules are frozen in a registration addendum and applied
once to the full data**.

### 3.2 Pairing bug: "paired" statistics are not seed-paired after any dropout

`collect_arm` reduces each arm to **success-only** value lists (detected: rows with
`DetectEpisode ≥ 0`, reconverged: `RecoveryEpisodes ≥ 0` — `analysis/phase2_recovery.py#L257-L261`).
`write_paired_table` then truncates both lists to the shorter length and zips **by list
position** (`#L387-L392`). File discovery is `sorted(root.rglob(fname))`
(`#L206-L210`), i.e. lexicographic seed order (seed1, seed10, seed2, …); the order is
consistent across arms, so pairing is genuinely by-seed **only when both arms have all
replicas**. The moment one arm drops a row, every subsequent "pair" is two different seeds,
and the paired bootstrap / Wilcoxon / Cliff's δ are computed on misaligned data.

Concrete affected cells (n_paired < 10 ⇒ misalignment risk realised):
- v5 `lab3_f1inv` RecoveryEpisodes n_paired=9 — `phase2_results_v5/analysis/out/phase2_recovery_paired.csv#L3`
- v6 `lab3_f1inv` RecoveryEpisodes n_paired=7 — `phase2_results_v6/analysis/out/phase2_recovery_paired.csv#L3`
- ext `lab3_f1dead` (n=9, ql_true reconverged 9/10 — `phase2_ext_results/analysis/out/phase2_recovery_ci.csv#L21`), `lab3_f1inv_z2` (n=9), `lab3_f1binv` (n=9, ql_true n_runs=9 — CI CSV `#L19`), `lab2_f1binv` (n=9, ql_false n_runs=9 — CI CSV `#L6`) — `phase2_ext_results/analysis/out/phase2_recovery_paired.csv#L2,L5,L7,L9`

The headline confirmatory cells happen to be full-n (v5 `lab3_f1dead` n=10, ext blind-fault
cells `lab3_f1bdead`/`lab2_f1bdead` n=10, labmon n=10), so the flagship numbers are probably
correct — but "probably" is not auditable. **Fix (mandatory): extract the seed token from the
artefact path (as `phase4_energy.py#L219-L224` already does), pair by seed key, and emit a
`seeds_paired` column like sweep_report does. Then re-run `phase2_recovery.py` over the
existing raw `recovery_root/` data — no new CI runs are needed.**

### 3.3 BH family drift across iterations

The RecoveryEpisodes BH family had four different definitions across the published CSVs:

| Iteration | Family content | m | Evidence |
|---|---|---|---|
| v5 (27547019772) | 2 well-posed lamp cells | 2 | `phase2_results_v5/analysis/out/phase2_recovery_paired.csv#L2-L3` (`bh_family_m=2`) |
| ext (28745352239) | all 8 well-posed cells **including** inverted-lamp cells later classed descriptive | 8 | `phase2_ext_results/analysis/out/phase2_recovery_paired.csv#L2-L9` (`bh_family_m=8`, no `recovery_tier` column — pre-tier script) |
| binv backfill | tier-gated: descriptive cell excluded, family empty | 0 (q=nan) | `phase2_binv_backfill/phase2-consolidated/analysis/out/phase2_recovery_paired.csv#L2` |
| labmon (28863439179) | single confirmatory cell | 1 | `labmon_ci_results/phase2-consolidated/analysis/out/phase2_recovery_paired.csv#L2` |

With m=1, BH is a no-op — the labmon "q≈0" is just the raw bootstrap p. And because each CI
run correct only within itself, the *cross-run* multiplicity of ~10+ recovery contrasts spread
over five runs is completely uncorrected. **Fix: one final pooled analysis over the union of
all Phase-2 raw CSVs with a single, pre-declared confirmatory family (all Tier-1 cells), and
report the per-run tables as history only.** The current script's tier machinery
(`analysis/phase2_recovery.py#L167-L178`, BH gating `#L421-L424`) already supports this; it
just has to be run once over everything.

### 3.4 Degenerate detection family (v6 onward)

Under instant blacklisting, DetectEpisode collapses to 0 in both arms for 7 of 9 lamp
profiles (Δ=0, p=1.0 — `phase2_results_v6/analysis/out/phase2_recovery_paired.csv#L4-L8,L11-L12`).
Those rows are not evidence of parity; they are a constant. Detection-latency claims should be
restricted to cells where detection is non-trivial (lab3 lamp faults, blind faults) and the
v6 zero-rows dropped from the family (they currently dilute m=9).

### 3.5 Instrument dependence

RecoveryEpisodes is defined by the *policy-stability* reconvergence criterion, which changed
across iterations (run 1: goal-based → 0 % recovery; v2: policy-stability; v3: +
`RecoveredGoalRate` certification — `docs/_audit/05_results_index.md#L173-L175`). The final
claims therefore rest on one instrument (stability window) gated by a second
(`RecoveredGoalRate ≥ 0.5`, `analysis/phase2_recovery.py#L135-L136`). This is acceptable
**only if** the thesis states the criterion explicitly and reports `RecoveredGoalRate` per
arm next to every recovery time (the CI CSVs already carry it, e.g. ext CI `#L16-L23`).
Note the inverted-lamp cells show why: `lab3_f1inv` goal_reaching_rate is 0.0/0.1
(`phase2_ext_results/analysis/out/phase2_recovery_ci.csv#L24-L25`) — its "recovery time"
measures time-to-stable-futility, not recovery.

### 3.6 Phase 2 verdict

**NEEDS-RERUN — analysis only.** The data volume (n=10 replicas per cell, paired design) is
adequate and the flagship effects are large (v5 `lab3_f1dead`: Δ=−212.9 episodes,
CI [−271.9, −148.3], p_wil=0.0039, δ=−0.86 — `phase2_results_v5/.../phase2_recovery_paired.csv#L2`;
ext `lab2_f1bdead`: Δ=−226.7, CI [−333.6, −141.5], p_wil=0.00195, δ=−0.92 — ext paired CSV
`#L8`). But no significance statement is currently defensible as confirmatory because
(a) pairs can be seed-misaligned (§3.2), (b) the BH family was redefined per run (§3.3), and
(c) there is no registration (§3.1). Specific fix, in order: (1) pair by seed key;
(2) write a Phase-2 addendum (§9) to `docs/pre_registration.md` freezing hypothesis, tier
rules, threshold 0.5, and the pooled family; (3) re-run `phase2_recovery.py` once over the
union of all raw recovery CSVs; (4) drop the degenerate v6 detection rows from the detection
family. Post-index runs 28866807391 (lab3_f2dead_lowsun) and 28884717500
(labmon2_f2dead_lowsun) — commits `71d5798`, `ba0303e` — use the same single-cell m=1
families and inherit every finding in this section.

---

## 4. Phase 3 — response-delay learning (run 27621106006, n=10)

### 4.1 What is genuinely stochastic and what is not

The pre-registration itself says it: **the exploit planner is deterministic given the learned
delay table** — exactly 6/6 goals met by ql_true and 3/6 by ql_false per replica; only the
delay-accuracy numbers carry real (tick-quantisation) variance (D-P3-2,
`docs/pre_registration.md#L676`). The CSVs confirm it: every compliance CI is zero-width
(`overall_compliance` 1.0 [1.0, 1.0] vs 0.5 [0.5, 0.5];
`phase3_download_n10/phase3-consolidated/analysis/out/phase3_compliance_ci.csv#L2-L5`), and
every paired diff is a constant (+0.5 CI [0.5, 0.5], +1.0 CI [1.0, 1.0], p_boot=0.0,
p_wil=0.001953, δ=1.0 — `phase3_compliance_paired.csv#L2-L5`).

Judgement: applying a bootstrap and a signed-rank test to ten copies of the same
deterministic outcome produces *formally valid but scientifically vacuous* p-values — the
"n=10 replicas" contribute zero information to the compliance contrast beyond n=1. This is
**not underpowered** (no n fixes it) and does not need a rerun; it needs re-framing. The
compliance result is a *worked demonstration* that the learned delay changes planner
behaviour in the intended way, and should be reported as counts (6/6 vs 3/6 per replica,
identical across 10 replicas) with the D-P3-2 caveat, **not** as "significant at
p=0.00195". The Wilcoxon-only version of that claim must be dropped.

### 4.2 Delay accuracy (H-P3a) — the real statistical content

Learned blind delay vs ground truth 12 ticks: relative error 0.94–1.77 % across the four
(profile, arm) cells, classification instant-vs-delayed correct in all cells
(`phase3_download_n10/.../phase3_delay_accuracy.csv#L2-L5`). This satisfies the registered
prediction rel_err ≤ 5 % (`docs/pre_registration.md#L645-L648`) with real replica variance
behind it. **STATISTICALLY SOUND.**

### 4.3 Family-size deviation

Registered protocol: BH family m=4 (overall + tight × 2 labs, excluding the degenerate
loose tie — `docs/pre_registration.md#L641,L659-L671`). Implemented: BH is applied **per
metric across profiles**, m=2 per family, and it is also applied to the excluded
`loose_compliance` and `total_energy` metrics
(`analysis/phase3_dynamics.py#L405-L407,L450-L461`; CSV `bh_family_m=2` on every row).
With p=0.0 everywhere this changes nothing numerically, but it is an unregistered deviation
and per pre-reg §6 must be listed in the thesis Deviations subsection.

### 4.4 Registration timing

§8 was committed pre-analysis relative to the n=10 confirmatory run, but *after* the n=5
exploratory run was seen, and the H-P3b "prediction" restates the n=5 outcome to the third
decimal (diff +0.5, CI [0.5, 0.5], p_wil ≤ 0.002 — `docs/pre_registration.md#L653-L656`).
Given §4.1 (the outcome is deterministic), this is a replication statement, not a risky
prediction. Honest, but the thesis should call it what it is. The n=5→n=10 bump for the
Wilcoxon floor (D-P3-1, `#L675`) was made for a metric whose distribution is degenerate —
the floor was never the binding constraint.

### 4.5 Phase 3 verdict

**H-P3a (delay accuracy): STATISTICALLY SOUND.**
**H-P3b (compliance): RE-FRAME AS DESCRIPTIVE** — keep the numbers, drop the significance
framing, register the m-family deviation (§4.3). D-P3-4's energy-direction disclosure
(ql_true spends more energy by design; `phase3_compliance_paired.csv#L8-L9`) is already
handled correctly.

---

## 5. Phase 4 — energy-aware goals + KG-vs-LLM (run 27905392725, n=20; prior run 27903687624, n=10)

### 5.1 Design and n

20 paired seeds, 80 scenario-runs per replica, 3 arms
(`phase4_n20_download/.../phase4_energy_ci.csv#L2-L7`: `n_replicas=20`,
`mean_scenarios=80`). Paired contrast ql_true−ql_false only; rule_based reported as ceiling
outside the family (`analysis/phase4_energy.py#L134-L137`). n=20 paired is the best-powered
cell in the project.

### 5.2 The lab5 primary result is solid on its face

`energy_compliance`: Δ=+0.1012, CI [0.0656, 0.1381], p_boot=0.0, p_wil=0.00093, δ=0.69,
q=0.0 (`phase4_n20_download/.../phase4_energy_paired.csv#L5`); `mean_steady_power`
Δ=−0.391 CI [−0.599, −0.183]; `over_budget_rate` Δ=−0.090 CI [−0.131, −0.051]; `goal_rate`
null (q=0.147, `#L4`) — so the energy win is not bought with goal-rate, as the write-up
says (`docs/PHASE4.md#L268`). All three tests + effect size agree; direction replicates the
independent n=10 run.

### 5.3 Family-sizing notes (minor)

(a) For lab4 (no energy budget) the script sets `energy_compliance = goal_rate`
(`analysis/phase4_energy.py#L341-L347`) and then emits **both** as separate rows in the BH
family — rows 2 and 3 of `phase4_energy_paired.csv` are bit-identical (Δ=0.023125,
p=0.0002). The same test is counted twice in m=6 (`#L455-L459` computes BH over all emitted
rows). Effect: q-values are slightly *conservative* (m inflated by 1), so no claim is
endangered; fix by dropping the duplicate row.
(b) The sweep-report family for Phase 4 is m=28 (2 labs × 7 metrics × 2 pairs,
`phase4_n20_download/.../paired_tests.csv` `bh_family_m=28`), while the energy family is a
separate m=6. `goal_rate` therefore appears in two families (q=0.174 in sweep-report vs
q=0.147 in energy). Harmless but the thesis should cite one file per metric, not shop
between them.

### 5.4 The n=10 → n=20 escalation is data-dependent (optional stopping)

Sequence, per the repo's own documents: the n=10 run (27903687624) gave energy_compliance
bootstrap p=0.043 but Wilcoxon p=0.086 (`docs/PHASE4.md#L293`;
`docs/_audit/05_results_index.md#L371`), and the workflow doc then recommends n=20 because
the primary "has ties that need **n = 20** to cross p<0.05"
(`docs/PHASE4.md#L209`). That is sampling-until-significant on the Wilcoxon: a stopping rule
conditioned on the observed p-value inflates the type-I error of the test it targets. Two
mitigating facts: the registered-everywhere-else *primary* instrument (paired bootstrap) was
already significant at n=10, and the n=20 sample subsumes rather than cherry-picks the n=10
seeds with a consistent direction and a large δ. The claim survives, but the thesis must
(1) disclose the escalation and its trigger, and (2) present the bootstrap CI + δ as the
primary evidence, with the n=20 Wilcoxon as a sensitivity check — not as "all pre-registered
thresholds met".

### 5.5 "Pre-registered primary" — NOT FOUND

`docs/PHASE4.md#L259` calls lab5 `energy_compliance` the "pre-registered primary", and
`#L209` repeats "pre-registered". **`docs/pre_registration.md` contains no Phase 4 addendum**
(the file ends with §8, Phase 3). No other registration artefact for Phase 4 was found. The
label is currently unsupported. Fix: either add a §9 Phase 4 addendum (post-hoc-registered,
like §7, stating hypothesis, primary metric, family, and the n-escalation history) or delete
the word "pre-registered" from PHASE4.md and the thesis.

### 5.6 KG-vs-LLM comparison — single instrument, no inference

`phase4_llm_summary.csv` is one deterministic offline proxy run: 16 scenarios per lab,
point estimates only (lab5 compliance 0.556, power 3.42 —
`phase4_n20_download/.../phase4_llm_summary.csv#L2-L3`), no seeds, no CI, no test — and the
PHASE4.md table compares it against the ql_true means (`docs/PHASE4.md#L282-L291`). The
"KG informs the agent better than the LLM's general knowledge" statement therefore rests on
a single instrument with zero uncertainty quantification, and the LLM is a proxy (offline
prompt log), not a tuned baseline. It is a legitimate illustrative comparison; it is not a
statistical result. **Label exploratory/descriptive in the thesis and exclude it from any
significance language.**

### 5.7 Phase 4 verdict

**STATISTICALLY SOUND** for the lab5 energy family and lab4 efficiency family (lab4:
avg_steps Δ=−0.496 q=0.0, avg_redundant Δ=−0.558 q=0.0 at m=28 — n20 `paired_tests.csv`
rows), **conditional on**: disclosing the n-escalation (§5.4), fixing the unsupported
"pre-registered" label (§5.5), and demoting the LLM comparison to exploratory (§5.6). The
duplicate lab4 row (§5.3a) is cosmetic.

---

## 6. Pre-registration compliance ledger

| Registered item | Honored? | Evidence |
|---|---|---|
| OLD H1–H5 (§1–§5, custom labs, 5 seeds) | Superseded; falsifications honestly retained (Sweep 17 H1/H3 negative kept, §6.6; Sweep 18 custom9 null kept, §6.7) | `docs/pre_registration.md#L61-L71,L372-L451,L453-L507` |
| Deviation policy §6 ("report, don't swap silently") | Followed for OLD era (D6-1..6, S0-3/4, KG-1..9) and Phase 3 (D-P3-1..4) | `#L129-L137,L139-L368,L673-L678` |
| Phase 1 addendum §7 (post-hoc registered, disclosed) | H-CL1 ✓, H-CL2 ✓, H-CL3 ✓, H-CL4 ✓ (§2.2); lab3 primary null honestly reportable | §2.2 above |
| Phase 2 registration | **NOT FOUND** — no addendum exists; family/tier rules evolved with the data | §3.1 |
| Phase 3 addendum §8 | H-P3a honored; H-P3b honored numerically but the registered m=4 family was implemented as m=2-per-metric (unregistered deviation, §4.3), and the "prediction" post-dates the n=5 data | §4 |
| Phase 4 registration | **NOT FOUND** — "pre-registered primary" label in PHASE4.md has no registration artefact; n=10→20 escalation undisclosed as a stopping rule | §5.4–5.5 |
| Closing rule (`#L682`: commit pre-reg before first CI summary) | Holds for the OLD-era design; §7/§8 addenda are explicitly post-data/post-implementation with disclosure; Phases 2/4 have nothing to which the rule could apply | `#L682` |

---

## 7. Prioritized fixes

1. **Phase 2 (blocking):** pair by seed key, freeze a §9-registered pooled BH family + tier
   rules, re-run `phase2_recovery.py` once over all raw recovery CSVs (§3.6). No new CI runs
   needed unless the seed-aligned re-analysis flips a q-value across 0.05.
2. **Phase 4 (blocking for wording):** add a Phase-4 registration addendum or remove
   "pre-registered"; disclose the n=20 escalation trigger; demote the LLM table to
   exploratory (§5.4–5.6).
3. **Phase 3 (wording):** report compliance as a deterministic demonstration (counts + D-P3-2),
   delete significance framing; register the m=2 family deviation (§4.1, §4.3).
4. **Phase 1 (provenance):** restore the §1.2 headline-run artefacts locally from the results
   branch; either re-dispatch the failed pbrs_only control or drop the three-arm isolation
   claim (§2.4). Add the four disclosures of §2.5 to the Results text.
5. **Global (wording):** state once, in Methods, that the paired percentile bootstrap
   (10 000 resamples, seed 0xC1) is the primary test, Wilcoxon is a tie-fragile sensitivity
   check (floor 2/2^n_effective after zero-dropping), and Cliff's δ is the effect size —
   then apply that hierarchy consistently in every phase's claims.
