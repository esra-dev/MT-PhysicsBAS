# Phase 2 — Fault Detection, Blacklisting, and Re-Learning

> **Thesis chapter draft** (2026-07-12). Confirmatory numbers are the
> post-inversion runs of record (`pre_registration.md` §9.10, commit `6c727b6`,
> CI runs 29148475671 / 29151540231 / 29155539633 / 29157197853 / 29163456132);
> source CSVs `analysis/out_phase2_registered_postinv/phase2_recovery_paired.csv`
> and `phase2_recovery_ci.csv`. The superseded pre-inversion measurement is
> reported side by side in §5.4 per the registration. Every table caption names
> its run ID and CSV.

## 1 Introduction and claim

Phase 1 established that priming a tabular Q-learner with structural physics
knowledge from a component-stereotype Knowledge Graph accelerates learning on a
clean two-zone lab, and that the same prior becomes an exploration tax where
the structure it promotes is real but never required for the goal. Phase 2
turns to the setting the advisor's brief singles out: a **pre-trained** agent
placed in a lab where one or more components have silently broken. The agent
must not learn around the fault; it must *recognize* that an action produced
behaviour that contradicts its physics knowledge, recheck against that
knowledge, immediately discard (blacklist) the faulty component, alert the
user, and re-learn a policy over the surviving components — degrading the goal
gracefully, with notification, when the nominal goal has become unreachable.

This chapter makes two claims, one architectural and one empirical.

**Architectural.** The detect → blacklist → alert → re-learn loop works as
specified, across two mechanism classes and up to two simultaneous faults:
detection recall is 100 % in every cell of the fault matrix (episode 0 for
every lamp fault; episode ≈ 6–8, bounded by the first sufficiently sunny
episode, for every sun-gated blind fault); there are no false positives; both
polarities of a broken component are removed on first unambiguous evidence;
and when blacklisting makes the nominal goal unreachable, a deterministic
reachability probe *proves* it, lowers the effective goal to the best
achievable rank, and notifies the user.

**Empirical.** The registered recovery-speed hypothesis — that the KG-primed
agent re-converges faster than an identically-equipped tabula-rasa agent after
the fault is removed — holds **selectively, not universally**. On the final,
capability-equalized instrument, 3 of the 8 pre-registered confirmatory cells
show a significant KG advantage (with a fourth marginal and six of eight
point estimates negative), and the significant cells are precisely those in
which recovery requires **re-ranking multiple surviving actuators**. Where a
single deterministic survivor makes the post-fault problem trivial, or where
re-learning is dominated by unavoidable exploration, the advantage shrinks to
zero or reverses. We compress this into the chapter's organizing statement:

> **Structural knowledge pays where it is the binding constraint on recovery —
> and only there.**

This is a weaker headline than the one an earlier version of our instrument
produced (§5.4), and we consider the revision a result in its own right: the
earlier "KG always recovers faster" reading conflated a genuine knowledge
effect with an action-space asymmetry that our infrastructure later removed.
The strongest independent support for the binding-constraint reading comes
from an experiment that varies *only the documentation* while holding physics
constant — the KG-silent monitor contrast of §7.

## 2 Problem setting and the fault ladder

### 2.1 Fault taxonomy

Every faulty lab is generated deterministically from its clean Phase-1 parent
by literal replacement in the simulator's physics function
(`simulator/generate_faulty_flows.ps1`); the faulty profile reuses the
parent's Thing Description, ontology, port, scenario sets and discretization
bounds, and warm-loads the parent's converged clean Q-table
(`adapt_source/2`). Two fault modes are injected — **dead** (the component's
lux contribution is zeroed) and **inverted** (negated: the component "works",
in the wrong direction) — across two mechanism classes:

| Family | Cells | Physics edit (example) |
|---|---|---|
| Single lamp (Causes) | `lab1_f1dead`, `lab2_f1dead/f1inv`, `lab3_f1dead/f1inv`, `lab3_f1dead_z2/f1inv_z2` | `z1l ? 400` → `z1l ? 0` / `? -400` (incl. cross-zone term in lab3) |
| Multi-lamp | `lab2_f2dead/f2inv`, `lab3_f2dead/f2inv` | both lamps' own + cross terms zeroed / negated |
| Single blind (Mediates, IV-gated) | `lab3_f1bdead/f1binv`, `lab2_f1bdead/f1binv` | `z1b ? 0.50*sun` → `0` / `-0.50*sun` (+ cross term in lab3) |
| Multi-blind (exploratory, §2.3) | `lab3_f2bdead` | both blinds' own + cross terms zeroed |
| Monitor fallback | `labmon_f1dead` | only rank-3 lever dead → goal unreachable, monitor is the best-effort fallback |
| Degraded multi-survivor | `lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun` | both lamps dead **and** sun pinned to rank 1 → rank 3 provably unreachable every episode |

The blind cells are the interesting half of the taxonomy. A blind is a
*Mediates* mechanism: its manipulated variable gates an independent-variable
transfer (outdoor illuminance → indoor illuminance), so a blind fault is only
*falsifiable* when the blind is opened under sufficient sun — and, because
the deterministic lamp is always sufficient for the goal and energy is not in
the reward, a converged clean policy never opens blinds on its own. A blind
fault is undetectable by passive monitoring by construction (§3.2).

### 2.2 Well-posedness and tiers

A recovery-*speed* comparison is only defined where a recovered policy is
possible: the **well-posed** set (frozen by enumeration,
`analysis/phase2_recovery.py::_WELL_POSED_RECOVERY`) contains the cells with a
deterministic post-fault survivor path. Within it, a cell is
**Tier-1 (confirmatory)** if the recovered policy actually reaches the
(effective) goal in ≥ 50 % of greedy evaluation episodes *in both arms*, and
**Tier-2 (descriptive)** otherwise — a stable-but-futile policy is not a
recovery, so its timing carries no q-value. The stratifier is a property of
the environment, identical across arms, so conditioning on it cannot bias the
KG-vs-vanilla contrast. Cells outside the set (e.g. the lab2 lamp faults,
whose only survivor is the sun-gated blind) are reported descriptively as
ill-posed.

### 2.3 The exploratory multi-blind cell

The multi-fault family above injects Causes lamps only, and none of its cells
is well-posed (the lamp `f2*` cells leave only sun-gated survivors; the
`_lowsun` cells are degraded by design). We therefore added — after the
confirmatory campaign closed, and registered as such
(`pre_registration.md` §9.11) — one **exploratory** cell, `lab3_f2bdead`:
both lab3 blinds dead. It is the first multi-fault cell in the Mediates class
(the active self-test must fire twice, and blacklisting iterates) and the
first well-posed multi-fault cell (survivors Z1 lamp, Z2 lamp, spotlight keep
both zones deterministically at rank 3). Because the registered families are
frozen by enumeration, this cell can never enter them: it is reported with
full paired statistics and no q-value, as a designed probe of the
binding-constraint reading (§6.4). At the time of writing it has not yet been
dispatched.

## 3 The adaptation machinery

### 3.1 Physics recheck and instant blacklist

On every adapt step the agent compares the observed transition against the
KG's falsifiable claims for the action just taken (`observeForFaults`):
**DEAD** if the actuator bit dropped or every falsifiable claimed zone showed
zero rank response; **INVERTED** if any claimed zone moved against the KG's
asserted sign. There is no evidence counter: a component is blacklisted on its
**first** unambiguous, falsifiable, component-attributable anomaly. False
positives are prevented structurally rather than statistically — only
falsifiable claims are scored, IV-gated blinds are adjudicated only on OPEN
under sun rank ≥ 2 with headroom, zones contaminated by a concurrent suspect
are skipped, and the detector abstains when a co-feeder could mask the
response. On detection, both polarities of the component's actions are
removed from the applicable set and the user is alerted (console, belief,
CSV record).

### 3.2 The active self-test for IV-gated actuators

Because a blind fault generates zero falsifiable observations under a
converged policy (§2.1), the adapt agent runs a KG-directed diagnostic probe:
whenever the current state satisfies the falsifiability preconditions (blind
closed, sun rank ≥ 2, zone below saturation, component neither blacklisted nor
verified), it takes the OPEN action as a one-off self-test instead of its
greedy action. A healthy blind is verified on its first sound probe and never
probed again; a faulty one is instantly blacklisted. The probe is shared
instrumentation — both arms run it identically, so it cannot tilt the
contrast — and it is itself an instance of the advisor's "recheck against the
physics knowledge" being *active*: the KG tells the agent which components are
IV-gated and what would falsify them. In the runs of record it puts every
blind-fault detection at episode ≈ 6–8 in both arms (the wait is for the first
episode whose sunshine draw reaches rank 2), at a cost of one action per
blind, with zero false positives.

An analogous extension to Causes actuators (probing each unverified lamp
once) was considered while the pre-inversion instrument showed a small
adverse detection contrast on one cell; the post-inversion re-run dissolved
that motivation — every lamp-fault cell now detects at episode 0 in both arms
(§5.1) — and the extension was dropped.

### 3.3 Warm restart

Blacklisting triggers a warm restart rather than a cold one: Q-columns of
blacklisted actions are wiped, values in states poisoned by the fault are
halved, exploration is boosted back to the initial ε = 0.30, and the KG
prior's decay clock is reset so structural knowledge regains influence exactly
when the agent must re-plan. Recovery is then declared when the greedy joint
policy has been identical for 50 consecutive episodes; the primary metric is
**RecoveryEpisodes = ReconvergeEpisode − DetectEpisode** (lower is better),
certified by **RecoveredGoalRate** — the greedy goal-rate of the final policy
— so that "stopped changing" is never mistaken for "recovered".

### 3.4 Proof-gated best-effort degradation

If the nominal goal rank may have become unreachable, the agent does not
guess: it enumerates the ON/OFF combinations of the *surviving* actuators,
drives the real lab into each one, and records the observed ranks. Only if no
combination reaches the nominal rank does it lower the effective goal to the
best achieved rank and notify the user. The probe is physical, not
KG-derived, so it works even for components the KG is silent about (§7). In
the degenerate `lab1_f1dead` cell (a one-lamp lab whose only actuator dies)
the agent detects, alerts, proves rank 0 is all that remains, and stabilizes
at the floor in both arms — detect-and-alert-only, by design.

## 4 Registered evaluation protocol

Phase 2 is governed by a frozen registration (`docs/pre_registration.md` §9):
hypothesis H-P2 (*recovery(ql_true) < recovery(ql_false) in every Tier-1
cell*), metric definitions as coded, tier rules, and two BH-FDR families
frozen **by enumeration** — a recovery family of m = 8 Tier-1 cells and a
detection family of m = 8 non-degenerate cells (cells whose DetectEpisode is
identically 0 in both arms are a constant, not evidence of parity, and are
excluded). Statistics: paired bootstrap (10 000 resamples) on seed-keyed
pairs, Wilcoxon and Cliff's δ as backups, q ≤ 0.05 within the frozen family.
One run of record per cell; superseded instrument iterations (a goal-based
reconvergence criterion, counter-based detection) are registered as history
and never pooled.

**The instrument change (§9.10).** After the confirmatory campaign first
completed, an infrastructure audit changed how *both* arms obtain their action
space: previously it was discovered through the stereotype SPARQL layer, so
part of any measured "KG advantage" could in principle be action-space
asymmetry rather than knowledge; after the inversion, the action space is
enumerated from the WoT Thing-Description contract alone and the stereotype
layer is a pure knowledge-enrichment pass (`docs/ACTION_SPACE_INVERSION.md`).
Because a faulty cell must never warm-load a Q-table trained under a different
code state, every Phase-2 cell was re-run wholesale on the new instrument
(commit `6c727b6`), under a registered amendment that left every hypothesis,
metric, tier rule and family unchanged. The re-run is the confirmatory record;
the pre-inversion measurement is reported alongside (§5.4). One further
amendment (§9.11) registers the exploratory multi-blind cell of §2.3.

## 5 Results of record

### 5.1 Detection: a solved problem — and a null family

Detection recall is 1.0 in every cell and both arms. Every lamp-fault cell —
including all multi-lamp cells and the monitor/degraded cells — detects at
**episode 0 in both arms**: the warm-started policy's first use of the broken
lamp is its first falsifiable execution, and the instant blacklist needs
exactly one. The four blind-fault cells detect at episode ≈ 6–8 in both arms,
bounded by the first sufficiently sunny episode rather than by either arm's
knowledge. The registered detection family is accordingly **entirely null**
(min q = 0.656, m = 8), with four of its cells realizing degenerate 0-vs-0
detection post-inversion (kept in the family per the no-silent-change rule and
reported as a realized-deviation). The reading is architectural, not
competitive: with structural false-positive prevention and an instant
trigger, detection latency is set by *exposure* — when a falsifiable execution
first occurs — which the probe pins for blinds and the warm-started policy
pins for lamps, identically in both arms. Knowledge differences between the
arms play no measurable role in noticing faults; they can only matter for
what comes after.

*Source — `analysis/out_phase2_registered_postinv/phase2_recovery_paired.csv`
(DetectEpisode rows) and `phase2_recovery_ci.csv`, runs 29148475671,
29151540231, 29155539633, 29163456132.*

### 5.2 Recovery: the confirmatory family

Recovery-speed contrasts over the frozen Tier-1 family (RecoveryEpisodes,
ql_true − ql_false, seed-paired bootstrap, BH within m = 8):

| Cell | n | ql_true | ql_false | Δ | 95 % CI | Cliff's δ | q | Verdict |
|---|---|---|---|---|---|---|---|---|
| `lab2_f1bdead` | 10 | 75.6 | 382.1 | **−306.5** | [−439.5, −174.6] | −0.92 | **0.0000** | significant, KG faster |
| `lab3_f2dead_lowsun` | 10 | 63.5 | 134.9 | **−71.4** | [−102.3, −41.3] | −0.84 | **0.0000** | significant, KG faster |
| `labmon2_f2dead_lowsun` | 10 | 187.1 | 334.7 | **−147.6** | [−230.9, −61.4] | −0.76 | **0.0021** | significant, KG faster |
| `lab3_f1dead_z2` | 9 | 511.1 | 571.3 | −60.2 | [−120.1, −4.3] | −0.28 | 0.0664 | marginal, ns |
| `lab3_f1bdead` | 10 | 198.1 | 288.1 | −90.0 | [−265.0, +86.5] | −0.33 | 0.365 | ns |
| `lab3_f1binv` | 10 | 398.5 | 405.0 | −6.5 | [−138.4, +116.0] | −0.02 | 0.929 | ns |
| `labmon_f1dead` | 10 | 84.5 | 62.3 | +22.2 | [−15.8, +57.2] | +0.05 | 0.328 | ns, sign flipped |
| `lab3_f1dead` (seeds 11–20) | 9 | 505.0 | 420.0 | +85.0 | [−31.6, +205.1] | +0.43 | 0.276 | ns, sign flipped |

*Caption — registered pooled analysis over the §9.10 runs of record (commit
`6c727b6`; runs 29151540231, 29155539633, 29163456132); source CSV
`analysis/out_phase2_registered_postinv/phase2_recovery_paired.csv`; frozen
Tier-1 family m = 8 (`pre_registration.md` §9.5). All 8 cells realized tier
`confirmatory` (goal-reaching in both arms).*

H-P2 as registered — *faster in every Tier-1 cell* — is **not supported**.
What is supported is a selective effect: three cells significant with large
effect sizes (up to 5.1× on `lab2_f1bdead`), one marginal, six of eight point
estimates negative. `lab3_f1dead` deserves its own sentence: its
pre-registered one-shot replication rule was re-instantiated on the new
instrument with fresh seeds 11–20, came out directionally *adverse* (+85.0,
ns), and the cell is therefore reported as **unsupported**, permanently — the
registration forbids further reruns, and the independent seeds-1–10
measurement from the same campaign (492.7 vs 420.0) points the same way.

### 5.3 Descriptive cells

The registered tiers behave as designed. The inverted-lamp cells remain
futile in both arms (goal-reaching 0.0–0.1; stable-but-futile policies after
≈ 960–1330 episodes) — an inverted lamp keeps dragging its zone in every
state the re-learner visits, and no amount of prior helps either arm. The
inverted-blind cell `lab2_f1binv` collapsed to n = 4 paired seeds
(reconvergence 0.6 in both arms) and stays descriptive. Notably, the
ill-posed multi-lamp cell `lab3_f2dead` — three surviving actuators, but
sun-conditional goal reachability — shows the KG arm reaching a stable policy
in 213.5 vs 416.1 episodes: no q-value by registration, but directionally
consistent with the multi-survivor pattern of §6. The best-effort machinery
fired wherever the nominal goal was unreachable: both `_lowsun` cells and
`labmon_f1dead` realized `degraded_rate = 1.0` with a proof-gated effective
goal of rank 2, and `lab1_f1dead` degraded to the floor with both arms
stabilizing at the 50-episode window minimum.

*Source — `analysis/out_phase2_registered_postinv/phase2_recovery_ci.csv`
(per-arm rows: recovery means, goal-reaching, degraded accounting).*

### 5.4 The superseded measurement, and what changed

On the pre-inversion instrument the same protocol had returned an
across-the-board result: all 8 Tier-1 cells significant (max q = 0.0012),
with speed-ups from 1.1× to 9.1×, and a confirmed `lab3_f1dead` replication.
We report it in full as a pre-inversion-instrument measurement (source
`analysis/out_phase2_registered/phase2_recovery_paired.csv`, runs enumerated
in `pre_registration.md` §9.7):

| Cell | Δ (pre-inversion) | q | Δ (post-inversion) | q |
|---|---|---|---|---|
| `lab3_f1dead` | −121.1 | 0.00027 | **+85.0** | 0.276 |
| `lab3_f1dead_z2` | −95.7 | 0.0000 | −60.2 | 0.0664 |
| `lab3_f1bdead` | −426.5 | 0.0012 | −90.0 | 0.365 |
| `lab3_f1binv` | −908.9 | 0.00091 | −6.5 | 0.929 |
| `lab2_f1bdead` | −226.7 | 0.0000 | **−306.5** | 0.0000 |
| `labmon_f1dead` | −6.2 | 0.0000 | +22.2 | 0.328 |
| `lab3_f2dead_lowsun` | −64.9 | 0.0000 | **−71.4** | 0.0000 |
| `labmon2_f2dead_lowsun` | −148.5 | 0.0000 | **−147.6** | 0.0021 |

*Caption — left pair: pre-inversion registered analysis
(`analysis/out_phase2_registered/`); right pair: post-inversion
(`analysis/out_phase2_registered_postinv/`). Only the right pair carries
confirmatory weight.*

The pattern of what survived is the finding. The three cells whose effects
are essentially **unchanged** by the inversion (`lab2_f1bdead`,
`lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun`) are those where recovery is a
genuine re-ranking problem over multiple surviving actuators. The cells whose
large effects **collapsed** (`lab3_f1bdead` −426.5 → −90.0, `lab3_f1binv`
−908.9 → −6.5) or **flipped** are those where, under the old code path, the
stereotype-gated action discovery itself — not the knowledge content — had
been shaping the search space the two arms faced. The inversion equalized
capability; what remained is the knowledge effect, and it lives exactly where
knowledge has a job to do.

## 6 Interpretation: where structural knowledge pays

### 6.1 The three significant cells are one phenomenon

- **`lab2_f1bdead`** (−306.5, 5.1×): the dead blind is blacklisted and the
  KG arm immediately re-ranks toward the deterministic lamp it *knows* causes
  light; the vanilla arm re-explores a space in which the lamp must be
  rediscovered against high-variance alternatives (its recovery CI spans
  254.8–505.8 episodes vs the KG arm's 58.8–95.2).
- **`lab3_f2dead_lowsun`** (−71.4, 2.1×): both lamps gone, sun pinned low;
  the previously *redundant* spotlight — an actuator the clean policy learned
  to avoid — becomes the essential best-effort lever. The KG's structural
  claim "spotlight causes light in both zones" lets the primed agent re-value
  an avoided action; the vanilla agent must unlearn its avoidance by
  exploration.
- **`labmon2_f2dead_lowsun`** (−147.6, 1.8×): the spotlight-free replication
  of the same triage, with four survivors (two monitors, two blinds) and
  16 probe combinations across two zones.

In all three, the post-fault problem is: *several survivors, at least one of
which the warm-started policy mis-ranks*. That is precisely the situation in
which a structural prior has information the Q-table does not.

### 6.2 The nulls and sign-flips are the complementary phenomenon

- **`labmon_f1dead`** (+22.2, ns): a single zone with effectively one
  fallback lever. The physical reachability probe hands *both* arms the
  answer; there is nothing left for knowledge to accelerate, and the KG arm's
  extra priors buy mild overhead instead.
- **`lab3_f1dead` / `lab3_f1dead_z2`** (+85.0 ns / −60.2 marginal): one dead
  lamp among healthy alternatives; recovery is dominated by re-learning a
  2048-state policy under boosted exploration, a cost both arms pay in full.
  The seesawing signs across the two symmetric cells mirror the
  exposure-timing artefact already visible in detection: which zone hosts the
  fault interacts with each arm's (legitimately different) warm-started
  policy and exploration stream.
- **`lab3_f1bdead` / `lab3_f1binv`** (ns): the lab3 blind cells lose their
  pre-inversion enormity; with the action space equalized, losing a blind in
  a lab where the own lamp, the neighbour's spill, and the spotlight all
  survive is simply not a hard re-ranking problem.

### 6.3 Why this reading is not post-hoc curve-fitting

Three disciplines back it. First, it is stated in the registration itself as
disclosed commentary (§9.10), separated from the frozen confirmatory claims.
Second, it retrodicts the *pre-inversion* collapse pattern (§5.4): the cells
carried by action-space asymmetry are the ones that fell. Third, it makes a
falsifiable prediction, which we registered before dispatch (§9.11): the
exploratory multi-blind cell `lab3_f2bdead` re-creates the multi-survivor
re-ranking situation in a new configuration (two iterative Mediates
blacklists, three deterministic survivors), so the reading predicts Δ < 0
there; a null would instead say the lost blinds were policy-irrelevant in
both arms. Either outcome is informative, and neither can touch the frozen
families.

### 6.4 Phase 1 and Phase 2 are the same finding

Phase 1's lab3 result — the KG prior as an exploration *tax* on structure
that is real but not required — and Phase 2's selective recovery advantage
are two sides of one statement: the value of structural knowledge is not a
property of the knowledge but of the *coupling between knowledge and task*.
Redundant structure priced into the prior costs episodes (Phase 1, lab3);
load-bearing structure priced into the prior saves them, in proportion to how
much re-ranking the fault demands (Phase 2, this section). The
`lab3_f2dead_lowsun` cell stages this inversion within a single experiment:
the identical spotlight triple that was dead weight in the clean lab becomes
the decisive advantage after the fault.

## 7 The KG-silent contrast: knowledge content, not machinery

The results above compare a primed learner against an unprimed one. That
leaves a confound: is the advantage carried by the *content* of the
structural knowledge, or by the machinery of having priors at all? Phase 2.6
(`docs/PHASE2_6_KG_SILENT_MONITOR.md`) answers with a manipulation that is
unique in our design in varying **only the documentation**: the monitor labs
are re-run with KGs in which the monitor's light side-effect is
*misdocumented* (a stereotype whose only dependent variable is
`displayed_information`) or *undocumented* (no stereotype at all). Physics,
flows, faults, ports, and both learner arms' code are byte-identical to the
full-KG parents; the monitor is simply a **KG-silent** action — enumerated
from the WoT contract, carrying no prior, no zone claim, and no fault
adjudication, learnable by reward only.

| Cell | ql_true | ql_false | Full-KG parent (ql_true / ql_false) |
|---|---|---|---|
| `labmon2_infoonly_f2dead_lowsun` | 172.0 | 370.2 | 187.1 / 334.7 |
| `labmon2_nostereo_f2dead_lowsun` | 162.6 | 364.0 | (same parent row) |
| `labmon_infoonly_f1dead` | 51.3 | 71.5 | 84.5 / 62.3 |
| `labmon_nostereo_f1dead` | 51.3 | 71.5 | (same parent row) |

*Caption — run 29157197853 (commit `6c727b6`, seeds 1–10), descriptive by
registration (not family members); parent rows from run 29155539633. Source
CSVs in `analysis/out_phase2_registered_postinv/`. Detection and
reconvergence 1.0 everywhere; best-effort degradation to rank 2 fired in
every cell regardless of KG variant.*

Three observations, each doing argumentative work:

1. **The advantage survives a silent KG exactly where the binding-constraint
   reading says it should.** In the dual-zone multi-survivor cells the primed
   arm recovers ≈ 2.1–2.2× faster than vanilla *even though the KG never
   mentions that the essential fallback lever emits light* — matching the
   full-KG parent's 1.8×. The advantage there is carried by structural
   knowledge of the *documented* survivors (the blinds' IV-gating, elimination
   of dead-end actions), not by a prior on the monitor itself. Structural
   knowledge pays because multi-actuator triage is the binding constraint —
   with or without the one lever's documentation.
2. **Where discovery is trivial, knowledge buys nothing — again.** In the
   single-zone cells the un-primed monitor is found almost immediately by
   reward alone (51.3 episodes), *faster* than the full-KG parent's primed
   arm (84.5): the parent's additional priors are pure overhead in a one-zone,
   one-lever problem, reproducing the `labmon_f1dead` sign-flip of §5.2 from
   the opposite direction.
3. **The representational gradation is behaviourally invisible.** The
   misdocumented and undocumented variants produce identical means in the
   single-zone family and seed-noise-level differences in the dual-zone
   family — a partial stereotype with no illuminance claim and no stereotype
   at all reduce to the same silent registry entry, as the architecture
   predicts. What matters to the learner is whether the KG makes a falsifiable
   claim, not how much RDF surrounds its silence.

Because reality is held constant while documentation varies, this contrast
isolates the explanatory variable of the whole chapter better than any
primed-vs-unprimed comparison can: the KG's value is the value of *what it
truthfully documents about the levers that matter* — no more (the silent
monitor forfeits nothing when other knowledge binds) and no less (the
advantage never comes for free from the prior machinery itself).

## 8 Limitations and threats to validity

1. **The instrument changed after the first confirmatory campaign.** The
   action-space inversion was a post-registration infrastructure change; we
   handled it by wholesale re-run under a registered amendment (§9.10) with
   families frozen, and we report both instruments' results side by side. The
   directionally weaker post-inversion outcome argues against the change
   having been favourable to the hypothesis.
2. **H-P2 is not supported as registered.** The universal claim failed; the
   selective claim is an interpretation, registered only as disclosed
   commentary. Its independent support (retrodiction of the collapse pattern,
   the Phase-2.6 contrast) is descriptive; its one pre-registered forward test
   (`lab3_f2bdead`, §9.11) is exploratory by construction and pending.
3. **Exposure, not sensing, sets detection timing** — so detection contrasts
   carry no information about knowledge, and the null detection family should
   not be read as parity of anything except instrumentation.
4. **Simulator magnitudes are instruments.** Monitor lux (260/200), spill
   coefficients, and the pinned-sun values were chosen so that degraded
   ceilings land in specific ranks; the stereotype claims, not the magnitudes,
   are the knowledge under test, and no magnitude is asserted in the KG.
5. **Small-n caveats.** `lab2_f1binv` collapsed to n = 4 paired seeds
   (descriptive anyway); `lab3_f1dead`'s replication pairs n = 9. The window
   constants (detection preconditions, 50-episode stability, ε-boost 0.30)
   are shared verbatim by both arms, so miscalibration shifts cells, not
   contrasts.
6. **One environment family.** All cells are Node-RED lux simulators with
   deterministic physics and episode-pinned sun; external validity beyond
   this class (sensor faults, drifting physics, continuous actuators) is
   future work (`docs/FUTURE_RESEARCH_IDEAS.md`, Themes A/C).

## 9 Summary, and the bridge to Phase 3

Phase 2 delivers the advisor's fault brief in full on the architectural side:
faults in both mechanism classes — including simultaneous ones — are detected
at their first falsifiable execution with zero false positives, blacklisted
instantly, alerted, and re-learned around, with unreachable goals proven
unreachable and degraded gracefully. On the empirical side it delivers
something more precise than the hypothesis it set out to confirm: structural
knowledge does not make a pre-trained agent recover faster *in general*; it
makes it recover faster **where recovery is knowledge-limited** — where the
fault forces a re-ranking of several surviving levers that the data alone,
warm-started on the wrong world, is slow to produce. Where recovery is
limited by something else — a single obvious survivor, or the brute cost of
re-learning a large policy — the same knowledge is inert or mildly costly,
consistent with Phase 1's exploration-tax finding, and demonstrably not an
artefact of the prior machinery (§7).

What the stereotype layer *cannot* say is how fast a healthy lever acts: the
KG asserts that a blind mediates daylight, not that its motor takes a minute.
Phase 3 turns to exactly that gap — learning actuator response dynamics
online, writing them back into the KG, and exploiting them for time-bounded
goals — completing the loop in which the learner repays the knowledge graph.
