# custom9 re-diagnosis — night-dominated benchmark hypothesis

_Computed from 10 ql_true + 10 ql_false benchmark CSVs (n=10 seeds × 5 runs × scenarios). No new compute._

## Benchmark scenario mix by sun rank

| Sun rank | scenarios | share |
|---|---:|---:|
| 0 (night/none) | 9 | 32% |
| 1 (low) | 6 | 21% |
| 2 (medium) | 7 | 25% |
| 3 (bright) | 6 | 21% |

## Goal-rate per sun rank: informed (ql_true) vs naive (ql_false)

| Sun rank | n (true/false) | ql_true | ql_false | Δ (true−false) |
|---|---|---:|---:|---:|
| 0 (night/none) | 450/450 | 0.033 | 0.091 | -0.058 |
| 1 (low) | 300/300 | 0.060 | 0.080 | -0.020 |
| 2 (medium) | 350/350 | 0.014 | 0.171 | -0.157 |
| 3 (bright) | 300/300 | 0.363 | 0.083 | +0.280 |

## Observed vs sun-rank-uniform re-weighting

- **Observed overall goal-rate** (night-heavy mix): ql_true=0.105, ql_false=0.107, Δ=-0.002  (N_true=1400, N_false=1400)
- **Sun-rank-uniform re-weighted Δ** (each rank weighted equally): **+0.011**

## Verdict

- Δ at **rank 0 (night)** = -0.058 — this is the regime where the blind/sun lever has no leverage.
- Mean Δ at **ranks ≥ 2 (medium+bright)** = +0.061 — where the lever exists.
- Re-weighting sun ranks uniformly moves Δ from -0.002 to +0.011 (**favourable shift**), consistent with the night-dominated-benchmark hypothesis.

> Goal-rate here is a per-(scenario,run) terminal-success rate, not the AUC-of-learning-curve primary metric. It isolates *where in sun space* the prior helps or hurts at benchmark time; it does not replace the pre-registered AUC analysis.

---

## Interpretation (the real, data-backed diagnosis)

The auto-verdict above ("night-mix") is only *part* of the story and undersells the finding. The
per-rank breakdown reveals a sharper, more interesting mechanism:

| Sun rank | Δ (true−false) | What it means |
|---|---:|---|
| 3 (bright) | **+0.280** | **Hypothesis confirmed where the mechanism is active.** At sun ≥ 500 the blind contributes `0.5·sun ≥ 250` lux and (with the corridor +150) reaches a bright(3) target cheaply. The informed agent exploits this; the naive one does not (0.363 vs 0.083). |
| 2 (medium) | **−0.157** | **The prior MIS-FIRES.** At sun ∈ [150,500) the blind contributes only `0.5·sun ≈ 88–125` lux — *insufficient* to reach a bright(3) target even with the corridor (≈275 < 400). A task light (400) is required. But the prior still recommends blinds here, wasting exploration. |
| 1 (low) | −0.020 | Mild waste; lever weak. |
| 0 (night) | −0.058 | Mild waste; lever absent. |

**Root cause (verified in code, not a training gap).** The Mediates(blind, sunshine) mechanism has
`ivMinRank = 1` ([StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java) line 57 —
`ws:ivMinRank` in the ontology, default 1). So the prior treats the blind as "helpful" whenever
sun rank ≥ 1. But in `custom9` the blind only *reaches a bright target* at rank 3. The gate is
**too permissive by two ranks**: it recommends blinds across ranks 1–2 where they have partial-but-
insufficient leverage, which is precisely where the informed agent under-performs.

**Why the overall Δ is ≈ 0.** The benchmark mixes a strong rank-3 win (+0.280, 21% of scenarios)
against a strong rank-2 loss (−0.157, 25%) plus mild night/low losses. They nearly cancel →
observed Δ = −0.002. Uniform re-weighting barely helps (+0.011) *because the rank-2 mis-fire, not
the night mix, is the dominant drag.* The night-dominated-benchmark hypothesis is therefore **only
weakly supported**; the **IV-gate mis-fire at medium sun is the real driver.**

### Actionable, in-distribution fixes (no training-distribution change needed)

1. **Tighten the IV gate.** Set `ws:ivMinRank = 3` for the blind/sun Mediates mechanism in the
   custom9 ontology, so the prior only recommends blinds at rank 3 where they actually reach the
   target. Predicted effect: removes the −0.157 rank-2 drag while keeping the +0.280 rank-3 win →
   overall Δ should turn clearly favourable. **This is a one-line ontology change, testable in one
   sweep.**
2. **Let adaptive trust learn it.** The runtime IV-effectiveness tracker
   (`getLearnedIVMinRank`) is *designed* to discover that the blind fails below rank 3 and attenuate
   the prior. If it isn't doing so within the 20-step/10k-episode budget, that is itself a finding
   about the tracker's learning rate — worth reporting.
3. **Report the per-rank decomposition as a primary result.** The +0.280 at rank 3 is strong,
   honest evidence that the stereotype works *where its mechanism is active*; the −0.157 at rank 2
   is an equally honest illustration of the failure mode (a mis-calibrated IV gate). Together they
   are a sharper contribution than a flat "custom9 was null."

> **Note on the earlier retraction.** The retracted §4.1 of the meeting brief intuited "the blind
> underperforms at rank 2." That physical observation was *correct*; what was wrong was attributing
> it to a **training** coverage gap. The locus is the **evaluation** rank-2 scenarios combined with
> a too-permissive **IV gate** — both verified here from data and code.

