# Phase 2 — Fault Detection, Blacklisting, and Re-Learning

> **Thesis chapter draft, corrected protocol-v2 record (2026-07-27).**
> The empirical record is the prospectively registered correction campaign
> archived under `phase2_v2_corrected/` (runs `30001857104`,
> `30001867521`, `30001878310`, and `30001888910`; head `19f4f3ff`).
> Protocol-v1 and post-inversion convenience results are historical only.
> The binding withdrawal and correction documents are
> `docs/PHASE2_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md` and
> `docs/phase2_correction_registration_2026-07-22.md`.

## 1. Motivation and relation to Phase 1

The thesis studies whether qualitative component knowledge can help a
reinforcement learner act in a building-automation system. In clean
environments, the corrected Phase-1 and Phase-1b results impose a deliberately
bounded interpretation. Knowledge-derived priors produce repeatable learning
accelerations, but the confirmed Phase-1b effects are between roughly 8 and
70 times smaller than their registered smallest effects of interest. The
relevance slope is genuinely knowledge-layer rather than a redundancy
analogue; state fragmentation and dependency ordering are partly reproduced
by an ontology-free redundancy control; and the two new qualitative consumers
change no registered outcome.

Phase 2 asks a different question. A policy trained in a clean environment is
placed in a changed environment where one or more components are dead or
inverted. The agent must expose the fault, blacklist both action polarities of
the component, alert the user, and adapt over the surviving actions. The
registered comparison is between a knowledge-primed learner (KG) and an
otherwise identical tabula-rasa learner (TR).

The corrected result is two-stage:

1. the current policy determines whether the detector ever receives an
   unmasked, chargeable observation of a dead component; and
2. conditional on detection, the inherited Q-table and surviving topology
   determine how difficult re-ranking and re-learning are.

These stages must not be collapsed. A censored failure to detect is not slow
post-detection recovery.

## 2. Faults and adaptation mechanism

### 2.1 Fault profiles

Faulty profiles reuse their clean parent topology, action registry, scenario
schedule, state encoding, and reward. The simulator changes only the named
component effects. A dead fault removes the component's contribution; an
inverted fault reverses the contribution. Registered cells cover lamps,
sun-gated blinds, monitor fallback topologies, cross-coupled zones, and
degraded low-sun conditions.

The eight Tier-1 cells fixed by the correction registration are:

1. `lab3_f1dead`;
2. `lab3_f1dead_z2`;
3. `lab3_f1bdead`;
4. `lab3_f1binv`;
5. `lab2_f1bdead`;
6. `labmon_f1dead`;
7. `lab3_f2dead_lowsun`; and
8. `labmon2_f2dead_lowsun`.

### 2.2 Detector v2

After each action, the detector compares the observed transition with the
component's falsifiable qualitative claims. Opposite-sign evidence can support
an inverted verdict directly. A no-response observation can support a dead
verdict only when no healthy co-feeder could mask the missing contribution.
For sun-gated blinds, a deterministic active probe creates a falsifiable
observation when the registered environmental preconditions hold.

On a verdict, both action polarities of the faulty component are removed, the
Q-columns for those actions are cleared, exploration is boosted, the prior
decay clock is reset, and the user is notified. If the nominal goal may be
unreachable, an exhaustive physical reachability probe establishes the best
achievable goal before adaptation is assessed.

The maskability guard has a real trade-off. It eliminated the healthy-component
blacklists found in the withdrawn record, but it also made recall dependent on
the policy visiting a state in which every co-feeder is inactive. That
dependency is central to the corrected result.

## 3. Corrected registered protocol

The correction campaign used strict by-position scenario scheduling, fatal
missing-scenario handling, settled start-state recording, fixed 3,000-episode
clean parents, paired seeds 1–20, detector `fault-detector-v2`, complete
blacklist-event recording, and explicit censoring at horizon + 1. Every
adaptation cell carries an `ADAPT_OK` manifest linking it to its exact parent
profile, seed, scenario-schedule digest, Q-table file-set digest, and detector
version.

The primary recovery outcome is:

```text
RecoveryEpisodes = ReconvergeEpisode - DetectEpisode
```

Lower is better. A value of 4,001 is the registered censoring bound and means
that the arm never detected and therefore never began recovery. The eight
Tier-1 contrasts form one registered family, analysed over all 20 paired
seeds with exact paired sign-flip tests and Benjamini–Hochberg correction.
Detection is a separate registered family under the new detector.

The current source tables are:

- `phase2_v2_corrected/analysis/registered/phase2_v2_registered_family.csv`;
- `phase2_v2_corrected/analysis/registered/phase2_v2_detection_family.csv`.

They reproduce from the archived per-seed manifests and outcomes with:

```text
python analysis/reproduce_phase2_v2.py phase2_v2_corrected
```

## 4. Results of record

### 4.1 Recovery

| Cell | KG mean | TR mean | Mean Δ (KG − TR) | 95% CI | BH q | Verdict |
|---|---:|---:|---:|---:|---:|---|
| `lab2_f1bdead` | 58.8 | 151.4 | −92.65 | [−141.80, −50.25] | 1.017×10⁻⁵ | Supported |
| `labmon2_f2dead_lowsun` | 184.8 | 353.6 | −168.75 | [−246.30, −92.95] | 1.148×10⁻³ | Supported |
| `lab3_f1dead` | 4001.0 | 1934.6 | +2066.40 | [+1300.75, +2836.45] | 1.563×10⁻³ | Adverse |
| `lab3_f1dead_z2` | 4001.0 | 489.0 | +3512.00 | [+3062.70, +3807.80] | 1.017×10⁻⁵ | Adverse |
| `lab3_f2dead_lowsun` | 4001.0 | 346.9 | +3654.15 | [+3252.00, +3869.65] | 1.017×10⁻⁵ | Adverse |
| `lab3_f1bdead` | 116.0 | 136.0 | −19.95 | [−76.60, +30.00] | 0.595 | Null |
| `lab3_f1binv` | 175.2 | 191.7 | −16.45 | [−82.75, +58.90] | 0.673 | Null |
| `labmon_f1dead` | 557.9 | 776.5 | −218.60 | [−653.65, +288.05] | 0.302 | Null |

The registered outcome is therefore **two supported, three adverse, and three
null**. The three adverse cells are not evidence that KG re-learning was
slower: KG never detected in any of their 20 seeds, so every KG observation
is censored. TR detected in 11/20, 19/20, and 19/20 seeds respectively.

### 4.2 Detection and censoring

The complete `BlacklistEvents` record contains zero false-positive blacklists
across 38 cells × 20 replicas × two arms. This establishes the
false-positive-free property for detector v2, not for the withdrawn detector.

Recall is not universal:

- all lab1/lab2 faults detect in both arms;
- blind faults detect through the shared active probe, typically after five
  or six episodes;
- inverted lamp faults detect at approximately episode zero because
  opposite-sign evidence is not gated; and
- dead lamps in cross-coupled lab3 profiles are detectable only when all
  co-feeders are off.

In those cross-coupled profiles, the KG policy tends to restore light through
the spotlight, blinds, or cross-zone actuator. Those healthy actions keep the
fault masked, so the policy shaped by valid structural knowledge can prevent
the detector from observing the failure. TR's noisier policy more often visits
an unmasked state. This is a policy-dependent observability limitation, not a
false positive and not a post-detection learning effect.

### 4.3 Recovery conditional on detection

Where both arms detect in every corrected seed, the clean recovery panel is
`lab3_f1bdead`, `lab3_f1binv`, `lab2_f1bdead`, and
`labmon2_f2dead_lowsun`. Two cells show a supported KG advantage and two are
null. This supports a bounded descriptive interpretation: inherited
structural priors can help after detection when the fault removes a
previously relied-on route and promotes a survivor that the clean policy
under-ranked. It does not support a universal recovery advantage.

The archives do not retain a complete post-detection state trace.
Consequently, they cannot directly measure the Q-value burden at the exact
blacklisting state. Phase 2b-A therefore evaluated a pre-fault **start-state
Q-gap proxy** and a separate deterministic detector-opportunity descriptor.
The retrospective is explicitly hypothesis-generating and cannot change
either this registered Phase-2 result or the registered Phase-1b bounded-effect
conclusion.

In the four-cell clean-detection panel, the primary mean-burden proxy ordered
opposite to the proposed recovery prediction (cell-level Spearman
`ρ = −0.738`; paired-seed stability interval `[-0.949, −0.211]`). The frozen
signed-gap-median sensitivity instead ordered positively (`ρ = +0.600`), so
the mechanism-proxy direction is not stable across the predeclared summaries.
All four leave-one-cell-out primary associations remained negative. The
detector-opportunity audit separately reproduced the qualitative observability
boundary: the KG policy had zero deterministic opportunity and zero observed
detections in each of the three detector-censored adverse dead-lamp cells,
whereas the TR policy had nonzero opportunity and detected some or all seeds.
This is model-based detectability context, not an adaptation replay.

Only the artifact/non-degeneracy and predictor-spread screening conditions
passed. The association, pairwise-concordance, sensitivity, and
non-censored-panel conditions failed. A prospective recovery-ordering campaign
is therefore deferred; these descriptive results do not establish a general
Q-gap mechanism.

## 5. Interpretation

The corrected campaign establishes that knowledge can help and hurt through
different causal stages:

- **Detectability:** knowledge shapes the policy, and the policy shapes which
  component effects become observable. In cross-coupled dead-lamp cells this
  suppresses detection.
- **Adaptation after detection:** in `lab2_f1bdead` and
  `labmon2_f2dead_lowsun`, the KG arm reaches a stable recovered policy faster.
- **No general mechanism law:** the remaining cleanly detected cells are
  null, the start-state Q-gap proxy did not robustly order recovery in the
  predicted direction, and the number of distinct topologies is small.

The resulting claim is narrower and more useful than “knowledge always
accelerates recovery.” Qualitative structural knowledge is operationally
valuable only when it is both relevant to the post-fault action ordering and
exposed to a detector that can observe the fault. A policy can be effective at
maintaining the goal while being poor at diagnosis.

## 6. Limitations and validity boundaries

1. **Simulator scope.** All values are conditional on deterministic
   discretised lux simulators; no real-building effect size is claimed.
2. **Policy-dependent measurement.** Dead-fault evidence depends on state
   visitation. Detector opportunity and recovery must be reported separately.
3. **Censoring.** Horizon + 1 is a detection failure, not an imputed recovery
   duration.
4. **Rounded Q-tables.** Saved Q-values have two-decimal precision. Any
   retrospective proxy must preserve exact serialized values and expose ties.
5. **Few physical designs.** Twenty seeds do not create twenty independent
   mechanisms. Cell-level ordering and parent-profile sensitivity are
   necessary for mechanistic retrospectives.
6. **Historical protocol defects.** Protocol-v1 scenario substitution,
   unsettled start states, and false-positive blacklists invalidate its
   empirical values. It remains available in Git history only as an audit
   record.

## 7. Bridge to later phases

The corrected Phase-3 run of record is `29926328852`. It reproduces the delay
headline: the slowest-actuator estimate is 12.125–12.1875 ticks for a
12-tick truth (1.04–1.56% relative error). Deadline compliance is 59/60 and
60/60 for the KG arm in `lab2_slow` and `lab3_slow`, compared with 30/60 for
the zero-delay baseline in both; tick-integrated energy is descriptive only.

The corrected Phase-4 runs are `29926341581` and `29926354783`. KG reduces
redundant actuation by approximately 0.7 actions in each dependency topology
and improves lab5 energy compliance by 0.04313. The registered dependency-
growth contrast is null: the corrected advantage is approximately constant,
not monotone with depth.

Together with Phase 1b, these records bound the thesis conclusion. Qualitative
knowledge can produce precise and repeatable improvements, but most are small,
some are reproduced by simpler structural controls, and policy shaping can
create diagnostic blind spots. The contribution is therefore the measured
conditions and failure modes of knowledge-guided control, not an unqualified
claim of superiority.
