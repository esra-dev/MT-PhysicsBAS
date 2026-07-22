# Phase 2.5B Results — `lab3_f2dead_lowsun`: a confirmatory KG recovery-speed advantage

**CI run:** [`28866807391`](https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/28866807391) · conclusion **success** · dispatched 2026-07-07.
**Design:** N = 10 seeds × 2 arms (`ql_true` = knowledge-graph priors, `ql_false` = vanilla warm-start), paired by seed.
**Branch:** `phase2-instant-blacklist`.
**Companion design note:** [PHASE2_5B_LAB3_MULTISURVIVOR_DEGRADATION.md](PHASE2_5B_LAB3_MULTISURVIVOR_DEGRADATION.md).

---

## 1. Executive summary

`lab3_f2dead_lowsun` is the first cell in the Phase-2 programme to yield a
**statistically significant, large-effect recovery-speed advantage** for the
knowledge-graph (KG) structural priors. After a symmetric two-lamp hardware
fault forces both zones into a degraded best-effort mode, the KG arm re-converges
on the degraded-optimal policy in **69.4 episodes** versus **134.3 episodes** for
the vanilla arm — a **1.9× speed-up** (48.3 % fewer episodes).

| Quantity | `ql_true` (KG) | `ql_false` (vanilla) |
|---|---:|---:|
| Recovery episodes — mean | **69.4** | 134.3 |
| Recovery episodes — 95 % CI | [59.0, 80.2] | [107.6, 163.1] |
| Recovery episodes — median | 64 | 119.5 |
| Recovery episodes — range | 50 – 98 | 67 – 220 |
| Detection rate | 1.0 | 1.0 |
| Detect episode | 0 | 0 |
| Re-converge rate | 1.0 | 1.0 |
| Degraded rate | 1.0 | 1.0 |
| Best-effort rank / nominal | 2 / 3 | 2 / 3 |
| Recovered goal rate | 1.0 | 1.0 |
| Recovery tier | confirmatory | confirmatory |

**Paired contrast (true − false), 10 seeds:** mean difference **−64.9 episodes**,
95 % bootstrap CI **[−97.3, −34.0]** (excludes 0); two-sided bootstrap
**p ≈ 0** (BH-adjusted q ≈ 0, family m = 1); Wilcoxon signed-rank
**p = 0.0039**; **Cliff's δ = −0.88** (large). **9 of 10 seeds** favour the KG arm.

This is the recovery-**speed** contrast that the single-survivor `labmon`
cell structurally could not produce (§5), obtained here without changing the
degradation *mechanism* — which remains identical across arms.

---

## 2. What was measured, and why the design isolates the effect

The fault kills **both** task lamps (`SetZ1Light`, `SetZ2Light`) and **pins the
episode sun to 100 lux (rank 1)**. Under those conditions the nominal goal (both
zones strictly > 300 lux = rank 3) is **robustly unreachable on every episode**,
while three actuators survive — `Z1Blinds`, `Z2Blinds`, and the `Spotlight` —
giving 2³ = 8 reachability-probe combinations and a **genuine triage** to
perform in *both* zones. The degraded-optimal outcome is **rank 2 in both
zones**, reached principally via the Spotlight (+150), the single largest
surviving lever at low sun.

Both arms warm-start Phase 2 from the *same* clean `lab3` Q-table, in which the
Spotlight was learned to be **redundant and therefore avoided**. The fault
**inverts the Spotlight's value** from redundant to essential. The recovery task
is thus a *re-valuation of a previously-suppressed actuator* — the exact setting
in which a structural "Spotlight *Causes* light" prior should pay off (see the
design note, §3). Because the degradation mechanism, detection timing, final
rank, and goal rate are all **identical across arms** (Table in §1), the only
free variable is the *speed* of re-convergence.

`RecoveryEpisodes` is defined as `ReconvergeEpisode − DetectEpisode`. Detection
is instant in this cell (`DetectEpisode = 0` for all 20 runs), so
`RecoveryEpisodes = ReconvergeEpisode`.

---

## 3. Per-seed results (paired by seed)

| Seed | KG recovery (`ql_true`) | Vanilla recovery (`ql_false`) | Δ (KG − vanilla) | KG faster? | KG secondary-detect |
|---:|---:|---:|---:|:--:|---:|
| 1  | 50 | 160 | −110 | ✓ | −1 (pre-empted) |
| 2  | 94 | 173 | −79  | ✓ | 44 |
| 3  | 62 | 220 | −158 | ✓ | 12 |
| 4  | 64 | 117 | −53  | ✓ | 14 |
| 5  | 50 | 182 | −132 | ✓ | −1 (pre-empted) |
| 6  | 98 | 107 | −9   | ✓ | 48 |
| 7  | 74 | 67  | +7   | ✗ | 24 |
| 8  | 50 | 102 | −52  | ✓ | −1 (pre-empted) |
| 9  | 64 | 93  | −29  | ✓ | 14 |
| 10 | 88 | 122 | −34  | ✓ | 38 |
| **mean** | **69.4** | **134.3** | **−64.9** | 9/10 | — |

Two observations:

1. **The advantage is broad, not driven by outliers.** 9 of 10 seeds favour the
   KG arm; the single reversal (seed 7) is a 7-episode margin, within
   run-to-run noise. The vanilla arm, by contrast, carries the heavy tail
   (seeds 3, 5, 2 at 220/182/173 episodes) that the KG arm never exhibits — the
   KG maximum (98) is *below* the vanilla median (119.5).

2. **Structural pre-emption of the symmetric second fault.** On 3 of 10 KG
   seeds (1, 5, 8) the `SecondaryDetectEpisode` is **−1**: no distinct
   second-lamp detection event was recorded, and those seeds re-converged in the
   minimum window (≈ 50 episodes). Every vanilla seed, in contrast, logged a
   positive secondary-detection episode (1–10) — it empirically re-discovered
   the second dead lamp before it could stabilise. This is direct mechanistic
   evidence that the KG prior **generalises the first lamp-fault to the
   symmetric second lamp** (both are `SetLight` actuators sharing the same
   *Causes-light* structural signal), collapsing a two-stage empirical
   detection into one.

---

## 4. Statistical analysis

The aggregate was produced by `analysis/phase2_recovery.py` (per-cell 95 %
bootstrap CIs; seed-paired bootstrap + Wilcoxon signed-rank; Benjamini–Hochberg
FDR across the confirmatory family).

| Test | Statistic | Value | Interpretation |
|---|---|---:|---|
| Paired mean difference (true − false) | Δ̄ | −64.9 episodes | KG recovers ~65 episodes sooner |
| Bootstrap 95 % CI of Δ̄ | [lo, hi] | [−97.3, −34.0] | excludes 0 → significant |
| Bootstrap p (two-sided) | p | ≈ 0 | reject H₀ (no difference) |
| BH-adjusted q | q | ≈ 0 | survives FDR (family m = 1) |
| Wilcoxon signed-rank | p | 0.0039 | non-parametric confirmation |
| Cliff's δ | δ | −0.88 | **large** effect |
| Sign count | — | 9/10 | direction consistent |

The **detection** contrast is null by construction — both arms detect at
episode 0 (`DetectEpisode` diff = 0, CI [0, 0]) — confirming the recovery-speed
effect is *not* an artefact of differential fault detection but of differential
*re-learning* speed.

**Recovery tier = confirmatory.** The cell satisfies the well-posedness gate
(`well_posed_recovery = True`): the nominal goal is robustly unreachable every
episode, the degradation is stable (rank 2, goal rate 1.0), and N = 10 paired
seeds meet the confirmatory threshold. Defect components recorded:
`SetZ1Light; SetZ2Light`.

---

## 5. Discussion — the hypothesis, confirmed

The Phase-2 thesis thread sought a lab in which KG structural priors deliver a
measurable **recovery-speed** advantage after a hardware fault. Two earlier
cells set up the contrast:

- **`labmon_f1dead`** (CI `28863439179`) validated the best-effort degradation
  *mechanism* perfectly but returned a **null** recovery-speed result (KG 84.5
  vs vanilla 62.3; CI crosses 0; p = 0.248). Root cause: `labmon` is a
  **single-survivor** degradation — after the primary lamp is blacklisted, only
  one actuator path can reach the best-effort rank, so there is **no triage** for
  a structural prior to accelerate.
- **`lab3_f2dead_lowsun`** was engineered specifically to add the missing
  ingredient: a **robustly-unreachable, multi-survivor** degradation with a
  **redundant → essential inversion** of the Spotlight.

The result confirms the design hypothesis. Where a genuine triage exists among
survivors, the KG's structural priors **re-bias post-fault exploration toward the
now-essential lever** and re-converge ~1.9× faster, with a large effect size and
9/10 seed consistency. The vanilla arm must instead *unlearn* the clean
"avoid-Spotlight" Q-values by trial and error, incurring the long tail visible in
seeds 3/5/2. The pre-emption evidence (§3.2) supplies the mechanism: the prior
transfers the first fault's lesson to the structurally-identical second fault.

**Contrast summary across the two cells:**

| Cell | Survivors | Triage? | KG mean | Vanilla mean | Speed-up | Significant? |
|---|---|:--:|---:|---:|---:|:--:|
| `labmon_f1dead` | 1 | no | 84.5 | 62.3 | 0.74× | no (p = 0.248) |
| `lab3_f2dead_lowsun` | 3 | **yes** | **69.4** | **134.3** | **1.9×** | **yes (q ≈ 0, δ = −0.88)** |

The two cells together form a clean **ablation of the mechanism**: identical
degradation machinery, opposite recovery-speed outcome, with *presence of triage*
as the single differentiating factor.

---

## 6. Threats to validity and limitations

- **Single degradation target.** The effect is demonstrated for the symmetric
  two-lamp / low-sun degradation. Generality across other multi-survivor faults
  (e.g. blind failures, cross-zone asymmetric faults) remains to be shown; the
  self-contained `labmon2` dual-zone monitor cell is the planned independent
  replication.
- **Pinned sun.** Sun is fixed at 100 lux to guarantee robust unreachability.
  This is a deliberate design choice to remove the sun-conditional confound that
  muddied plain `lab3_f2dead`; it also means the cell does not probe recovery
  under variable ambient light.
- **Warm-start dependence.** Both arms inherit the same clean Q-table, so the
  effect is conditional on the clean policy having *suppressed* the Spotlight.
  The magnitude of the advantage would shrink if the clean policy did not
  strongly avoid the redundant lever.
- **Secondary-detect semantics.** The `−1` pre-emption reading (§3.2) is an
  interpretation of the logged secondary-detection field; it is consistent with
  the reconverge timings (≈ 50 on those seeds) but is corroborative rather than a
  directly instrumented count of avoided detections.
- **N = 10.** Confirmatory by the project gate, but the Wilcoxon p is at the
  discrete floor for n = 10; a larger N would tighten the CI further. The
  bootstrap CI and large Cliff's δ already place the effect well clear of noise.

---

## 7. Reproduction

```powershell
# Dispatch (as run 28866807391)
gh workflow run phase2.yml --ref phase2-instant-blacklist `
  -f adapt_profiles=lab3_f2dead_lowsun `
  -f seeds=1,2,3,4,5,6,7,8,9,10 `
  -f run_mode=phase1 -f adapt_episodes=0

# Fetch + aggregate artefacts
gh run download 28866807391 -n phase2-consolidated -D out
python analysis/phase2_recovery.py --root out/recovery_root --out out/analysis
```

Aggregated outputs: `analysis/out/phase2_recovery_ci.csv` (per-cell) and
`analysis/out/phase2_recovery_paired.csv` (paired contrast). Per-seed evidence:
`recovery_root/seed<N>/recovery_stereotypes_{true,false}_lab3_f2dead_lowsun.csv`
and the per-episode `metrics_adapted_*` series.

---

## 8. Conclusion

`lab3_f2dead_lowsun` delivers the programme's first **confirmatory** evidence
that knowledge-graph structural priors accelerate post-fault recovery: a **1.9×
faster** re-convergence (69.4 vs 134.3 episodes), significant at q ≈ 0 with a
**large** effect (Cliff's δ = −0.88) and 9/10 seed agreement, achieved with an
identical degradation mechanism across arms. Paired against the single-survivor
`labmon` null, it isolates **triage among survivors** as the condition under
which the KG advantage materialises, and provides mechanistic evidence
(structural pre-emption of the symmetric second fault) for *why*.
