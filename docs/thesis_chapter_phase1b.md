# Phase 1b — Where Qualitative Knowledge Changes Learning

> **Thesis chapter draft (2026-07-27).** The binding registration is
> `docs/phase1b_registration_2026-07-26.md`; the corrected archives are under
> `phase1b_corrected/`; and the reproduced results and post-audit corrections
> are `docs/phase1b_results_2026-07-27.md` and
> `docs/phase1b_post_audit_corrections_2026-07-27.md`.

## 1. Aim

Earlier clean-lab experiments showed that a Knowledge Graph (KG) prior could
change tabular Q-learning, but they did not isolate which properties of the
knowledge caused the change. Phase 1b decomposes the claim into three
registered mechanisms:

1. **relevance:** whether a qualitative component description helps the
   learner ignore inert actions;
2. **state fragmentation:** whether knowledge helps when irrelevant state
   bits split otherwise identical experience; and
3. **dependency order:** whether a known chain of required actuators reduces
   the time needed to discover a successful action order.

It also tests two new qualitative consumers: an explicit three-valued
irrelevance channel and a target-direction/band-mirror channel. The design
separates frozen KG behaviour from an extended implementation and from an
ontology-free redundancy-only control.

## 2. Registered design

The confirmatory campaign used 20 paired seeds and a five-member
Benjamini–Hochberg family. The registered members were:

- M1: frozen-KG minus baseline relevance slope over inert decoy count;
- M2: extended-KG minus frozen-KG incremental relevance slope;
- M3: the `labrel8s` versus `labrel8` state-fragmentation
  difference-in-differences;
- M4: extended-KG minus frozen-KG `labband` goal-area contrast; and
- M6: frozen-KG minus baseline restricted mean presentation time to first
  success in the depth-3 chain.

M5, extended-KG minus baseline band deviation, was prospectively exploratory
because the frozen power rule found inadequate power for a confirmatory
member. Pilot seeds were disjoint from confirmatory seeds. The campaign
retained the registered smallest effects of interest (SESOIs), fixed
endpoints, censoring rule, action registries, physics, and scenario schedules.

The archive reproduces byte-equivalently with:

```text
python analysis/reproduce_phase1b.py phase1b_corrected
```

## 3. Results

| Member | Mean effect | 95% CI | BH q | Registered reading |
|---|---:|---:|---:|---|
| M1 relevance slope | +9.88×10⁻⁶ `auc_goal` per decoy | [+5.36×10⁻⁶, +1.46×10⁻⁵] | 0.0065 | Detected, about 70× below SESOI |
| M2 incremental relevance channel | 0 in all 20 seeds | [0, 0] | 1 | Null |
| M3 fragmentation DiD | +0.0013 `auc_goal` | [+0.0010, +0.0016] | 9.5×10⁻⁶ | Detected, about 8× below SESOI |
| M4 incremental band channel | 0 in all 20 seeds | [0, 0] | 1 | Null |
| M6 depth-3 chain RMST | −0.5 presentations | [−0.64, −0.36] | 1.9×10⁻⁵ | Detected, 50× below corrected SESOI |

There was no censoring in the chain member. For M1, nine seeds were positive
and eleven were exact ties; every non-zero paired difference had the predicted
sign. It would be incorrect to describe all 20 seeds as positive.

The supporting controls sharpen the attribution:

- the redundancy-only analogue of the relevance slope is null
  (−2.4×10⁻⁶, uncorrected p≈0.46), so the very small M1 slope is specifically
  knowledge-layer;
- redundancy reproduces about 60% of the fragmentation gain
  (+7.8×10⁻⁴ of +1.3×10⁻³); and
- redundancy reproduces about 45% of the chain gain
  (−0.225 of −0.5 presentations).

The exploratory full-stack band-deviation contrast moved in the predicted
direction (−0.1625) but did not isolate the new direction consumer. Frozen
and extended KG have the same mean deviation (0.650625), so the incremental
direction-channel effect on that outcome is zero.

## 4. Interpretation against the SESOIs

The primary conclusion is not “three significant effects.” The registration
defined scientific relevance through SESOIs, and every confirmed effect is
well below its corresponding threshold:

- relevance is about 70 times smaller than the registered per-decoy effect;
- fragmentation is about 8 times smaller; and
- dependency ordering is 50 times smaller than the corrected
  −25-presentation SESOI.

The data therefore support **statistically detectable but scientifically
small accelerations at these lab scales**. This conclusion is fixed by the
registration and cannot be enlarged by a later retrospective mechanism
analysis.

The control arms distinguish three cases. Relevance is a genuine but
negligible knowledge effect because the simpler redundancy control does not
reproduce it. Fragmentation and dependency order partly survive without the
ontology, showing that simpler action-registry structure accounts for a
substantial share of both effects. Finally, the new three-valued relevance
and band-mirror consumers are behaviourally inert on their registered
members despite being engaged by the implementation.

## 5. Scope and limitations

1. The conclusions concern small deterministic, discretised simulator
   topologies and tabular Q-learning.
2. Statistical detectability does not override the registered SESOI reading.
3. The within-episode overshoot event count was registered but not measured:
   the archived benchmark output lacks the required trajectory. No proxy is
   substituted.
4. The exploratory M5 contrast compares a full stack with baseline and cannot
   be attributed to the direction channel.
5. Redundancy controls explain part, but not all, of the fragmentation and
   dependency contrasts; they are not evidence that the KG has no effect.

## 6. Consequences for the thesis programme

The post-Phase-1b decision memo authorises only the descriptive Phase-2
start-state Q-gap proxy retrospective as the immediate continuation. It
defers the conditional-route, magnitude-oracle, and energy-in-reward
experiments; descopes the depth-4 chain and the current wrong-KG ladder; and
leaves any prospective recovery campaign gated on the retrospective.

The completed retrospective did not pass that gate: its primary start-state
Q-gap proxy ordered recovery in the opposite direction, its frozen sensitivity
changed direction, and four of six screening conditions failed. The
prospective recovery-ordering campaign is therefore deferred, with no change
to the Phase-1b bounded-effect conclusion.

This ordering follows the evidence. Adding more qualitative channels is not
the immediate bottleneck: both newly implemented consumers produced exact
nulls. The next useful question is mechanistic and bounded—whether the
pre-fault learned policy helps explain variation in fault detection and
post-detection adaptation—without changing the Phase-1b conclusion that the
confirmed clean-lab effects are far below the registered thesis-relevant
thresholds.
