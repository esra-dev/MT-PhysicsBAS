# 13 — Logic Report: Decision Memo

**Generated:** 2026-07-07 · branch `phase2-instant-blacklist` @ `ba0303e`
**Inputs:** `docs/_audit/11_gap_analysis.md` (REQ-level gap analysis) and
`docs/_audit/12_stats_review.md` (statistical review). Underlying citations pass through
from those two documents; where a number appears below, its primary source is the
`path#L` citation given in 11/12 at the referenced section.
**Audience:** the student. Internal decision memo — blunt by design, not advisor-facing.
**Era:** all statements concern the NEW phase-based approach unless marked [OLD].

---

## 1. Does the implementation match ThesisGoalDescription_important.txt?

### Phase 1 — clean labs, KG-primed vs tabula-rasa: **Partially aligned**

The machinery is exactly what the advisor asked for: two fresh Q-learners in the same
deterministic lab, one primed via the KG, a complexity ladder lab1→lab2→lab3, blind IV
threshold learned rather than asserted, spillage as structure-without-values in the KG
(REQ-12, REQ-16–25 all KEEP — 11_gap_analysis.md#L45-L58). **Strongest evidence:** the lab2
headline — `auc_goal` Δ=+0.0197, CI [0.0147, 0.0245], q=0.0, δ=1.0, independently replicated
on seeds 11–20 (Δ=+0.0182, q=0.0, δ=1.0) — a confirmed, replicated, pre-declared primary
(12_stats_review.md#L97). **Weakest evidence:** lab3, the lab the advisor singles out as
"where we expect the RL to truly kick in" with a KG spillage advantage, is the one place the
KG agent is *slower to first goal* (+38 to +42.6 episodes, q=0 in the kg_only arm;
`auc_goal` directionally negative in both bumped runs, q=0.296/0.58), and the headline arms
run with `cross_zone_bonus = 0.0` — the spillage knowledge the advisor's hypothesis is about
is switched off in the flagship configuration (11_gap_analysis.md#L39, #L59;
12_stats_review.md#L102-L109). The lab3 claim currently survives only on `auc_reward`.
Verdict: the *design* is aligned; the *lab3 result* diverges from the advisor's stated
expectation and must be presented as a characterized weakness, not a win.

### Phase 2 — recognize → discard → alert → re-learn: **Aligned (design); evidence not yet confirmatory**

This phase is the advisor's redirection, and the implementation follows it almost to the
letter: no fault counter (thresholds deleted from the code, detection at episode ≈ 0), per-step
physics recheck against KG claims, instant complete blacklist that removes both action
polarities, user alert (console + belief + CSV), warm-restart re-learning with and without
physics, fault matrix dead/inverted × single/multiple × lab1–3, blinds included, monitor
fallback without an artificial cost, proof-gated best-effort degradation with user
notification (REQ-27–47: 20 of 21 KEEP — 11_gap_analysis.md#L63-L87). **Strongest evidence:**
REQ-35 — the exact behaviour the advisor demanded ("no counter, immediate blacklist") is
verified present, with 100 % detection recall across all 18 lamp and 4 blind confirmatory
cells and five significant Tier-1 recovery cells at 2.5–9.4× speed-up
(11_gap_analysis.md#L68, #L73, #L75). **Weakest evidence:** none of those significance
statements is currently defensible as confirmatory, because the analysis script pairs
success-filtered lists by position rather than by seed (misaligned pairs whenever one arm
drops a replica), the BH family was redefined in every result iteration (m=2→8→0→1), and no
Phase-2 registration exists (12_stats_review.md#L143-L238). The data are fine; the analysis
layer is not.

### Phase 3 — learn process dynamics, write back to KG: **Aligned**

Delivered end-to-end, including the optional extension: probe-based delay learner, learned
blind delay 60.0 s — literally the advisor's "60 seconds response delay" example — written
back to the KG as `ws:responseDelay`, with temporal goals where the KG arm meets every tight
deadline and the zero-delay arm meets none (REQ-48–54 all KEEP except one text-level item —
11_gap_analysis.md#L93-L101). **Strongest evidence:** delay accuracy 0.94–1.77 % relative
error against ground truth across all four (profile, arm) cells with real replica variance —
statistically sound as registered (12_stats_review.md#L264-L270). **Weakest evidence:** the
deadline-compliance "p=0.00195" is vacuous — the planner is deterministic given the delay
table, so ten replicas contribute the information of one; the result must be reframed as a
worked demonstration, and the advisor's framing that dynamics-failure appears "in part 1"
does not match where the repo demonstrates it (Phase-3 `_slow` labs) (12_stats_review.md#L244-L262;
11_gap_analysis.md#L100).

### Phase 4 — lab4/lab5/LLM: **Out of scope (extension)**

Maps to no requirement in the advisor's three-phase redirection. Keepable as a clearly
labelled extension chapter, but it must not be presented as satisfying Phase 1–3, and it
carries its own wording problems ("pre-registered" label with no registration artefact,
data-dependent n=10→20 escalation, LLM comparison with zero uncertainty quantification)
(11_gap_analysis.md#L105-L113; 12_stats_review.md#L336-L369).

---

## 2. KEEP — solid and defensible as-is

1. **The three-phase pipeline itself** — each phase has a completed confirmatory CI run
   (P1: 27336756264 + xzone family; P2: 28590019536/28745352239 + 2.5b runs; P3: 27621106006)
   (11_gap_analysis.md#L27).
2. **Phase-1 lab2 anchor result** — confirmed and independently replicated, pre-declared
   primary, δ=1.0; plus the lab1 null control confirming the floor (12_stats_review.md#L95-L100).
3. **The factorial/ablation design** — arms A–D isolating KG vs PBRS vs trust, seeded
   reproducibility, negative control confirming nulls when the prior is zeroed
   (11_gap_analysis.md#L47). This is a genuine methodological strength; give it a methods
   subsection.
4. **Phase-2 mechanism, wholesale** — instant blacklist (no counter), physics-recheck
   detector with structural guards (0 false positives on confirmatory cells), both-polarity
   discard, user alert, warm-restart re-learn, clean-parent Q-table warm-start mapping
   (11_gap_analysis.md#L67-L79). This is the advisor's Phase-2 paragraph rendered in code.
   **[WITHDRAWN 2026-07-22: the "0 false positives on confirmatory cells" verification is
   contradicted by the committed runs of record — healthy components were blacklisted in
   every replica of all four lab3 single-lamp cells and in 4/10 lab2_f1bdead vanilla
   replicas. See `docs/PHASE2_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md` item 3.]**
5. **Blind-fault active probe** — converts an off-policy undetectable fault into one caught
   within ~6–8 episodes, 100 % detection, 3 of 4 cells significant at 4.2–9.4×
   (11_gap_analysis.md#L80). Worth its own thesis subsection.
6. **Monitor stereotype + fallback + best-effort degradation** — multiple DVs with
   luminiscence as side-effect, no fictional cost, proof-gated goal degradation with user
   notification, validated in three CI cells (11_gap_analysis.md#L81-L87).
7. **Phase-3 delay learning + KG write-back** — the advisor's example reproduced exactly
   (60 s), ≤1.77 % error, statistically sound as registered (12_stats_review.md#L264-L270).
8. **The shared statistical machinery** — paired bootstrap + Wilcoxon + Cliff's δ + BH-FDR,
   deterministic seeding, `seeds_paired` discipline in sweep_report; the defects are in how
   Phase 2 *uses* it, not in the helpers (12_stats_review.md#L38-L48).
9. **The practice of honest caveats** — lab3 blemish, Tier-2 precision boundary, labmon
   single-survivor null are already disclosed in the docs. Keep every one of them in the
   thesis; they are what makes the rest believable (11_gap_analysis.md#L29, #L73).

---

## 3. ADJUST — exists but needs a change, ranked

| # | Item | Concrete action | Effort |
|---|---|---|---|
| 1 | **Phase-2 analysis is not confirmatory** (pairing bug + BH family drift + no registration) | (a) In `analysis/phase2_recovery.py`, extract the seed token from the artefact path (pattern already exists in `phase4_energy.py#L219-L224`), pair by seed key, emit `seeds_paired`; (b) write a §9 Phase-2 addendum to `docs/pre_registration.md` freezing hypothesis, RecoveryEpisodes definition, 0.5 threshold, tier rules, and ONE pooled Tier-1 BH family; (c) re-run the script once over the union of all raw recovery CSVs; (d) drop the degenerate DetectEpisode=0 rows from the detection family (12_stats_review.md#L161-L238) | 1–2 days, **analysis only, no new CI runs** (unless a q-value flips across 0.05 — then rerun the affected cell) |
| 2 | **Phase-1 headline provenance** — runs 27336756264/27344626272/27342571251 have no local artefacts; pbrs_only control failed and was never re-dispatched | Re-download the consolidated CSVs from the results branch into the workspace; re-dispatch pbrs_only or drop the three-arm isolation claim from the text (12_stats_review.md#L119-L128) | Hours (download) + optionally one CI run (pbrs_only) |
| 3 | **REQ-26 spillage advantage not demonstrated** — the one claim the advisor's lab3 story rests on | Either (a) rerun lab3 with an intermediate spill magnitude ("helpful but not trivialising", the doc's own suggestion) and `cross_zone_bonus` active in the headline arm, or (b) reframe the claim as "structure knowledge removes the penalty once spillage is rank-moving; magnitude advantage limited by ceiling" and lead with `auc_reward` (11_gap_analysis.md#L59; 12_stats_review.md#L102-L109) | (a) one CI run + analysis, ~1 day; (b) text-only, hours. Decide before writing the lab3 section |
| 4 | **lab3 mixed result must be framed as the bridge to Phase 2** — the REQ-19 narrative (complexity → failure → weakness definition) is currently implicit | Write the transition explicitly: lab2 = clean win; lab3 = KG prior over-explores 2048 states (characterized via init-bonus sweep); this cost-of-priors finding motivates Phase-2's "recheck with physics" rather than being hidden (11_gap_analysis.md#L52) | Text-only, half a day |
| 5 | **Phase-3 compliance reframe** — deterministic outcome dressed as inference | Report counts (6/6 vs 3/6, identical across 10 replicas) as a worked demonstration; delete "significant at p=0.00195"; register the m=2-per-metric family deviation (12_stats_review.md#L244-L262, #L272-L279) | Text-only, hours |
| 6 | **Phase-4 wording** (if the chapter stays) | Remove "pre-registered" or add a post-hoc §9-style addendum; disclose the n=10→20 escalation and its trigger; demote the LLM table to exploratory; drop the duplicate lab4 row (12_stats_review.md#L322-L357) | Text + one addendum section, half a day |
| 7 | **lab1 un-modelled `0.10·sun` ambient term** — breaks the "clean lab fully aligns with KG" premise (REQ-11), the advisor's own definition of Phase 1 | Model it in `building_1_trivial.ttl` or delete it from `simulator_flow_lab1.json`; if deleted, re-run the (cheap, saturated) lab1 cells (11_gap_analysis.md#L44) | Small; TTL edit or flow edit + one fast CI cell |
| 8 | **Wilcoxon tie-floor disclosure** — goal_rate cells near ceiling have effective n ≈ 5 after zero-dropping (floor 0.0625) | One Methods paragraph: bootstrap is the primary test, Wilcoxon a tie-fragile sensitivity check, δ the effect size; apply consistently (12_stats_review.md#L50-L66, #L408-L411) | Text-only, an hour |
| 9 | **Instrument hygiene leftovers** — `action_delay_ms(65)` contradicts its own ">200 ms" comment; `_lowsun` benchmark scenarios reused from clean parents; stale labmon "backup lamp" comments | Fix the delay constant or its comment; add a written caveat that `_lowsun` pins training resets only; delete stale comments (11_gap_analysis.md#L28) | Small code/comment edits, hours |
| 10 | **lab1_f1inv missing** from the fault matrix (REQ-38) | Add the cell (generator already exists) or state the structural-coverage argument (multi-fault impossible with one actuator) in the thesis (11_gap_analysis.md#L78) | One CI cell or one paragraph |
| 11 | **REQ-53 narrative alignment** — "stereotypes lack dynamics" demonstrated in Phase-3 `_slow` labs, not Phase-1 weakness labs as the advisor phrased it | Align the thesis narrative (text-only; the mechanism and evidence exist) (11_gap_analysis.md#L100) | Text-only, an hour |

---

## 4. BUILD NEW — genuine gaps

Effectively **none at the implementation level**: every requirement in
`10_requirements.md` has an implementation; all gaps are adjustments of existing work
(11_gap_analysis.md#L177-L180). The only genuinely new *artefacts* required are documents:

1. **Phase-2 registration addendum (§9 of `docs/pre_registration.md`)** — does not exist in
   any form and is the precondition for calling any Phase-2 result confirmatory
   (12_stats_review.md#L145-L159). This is item #1 in §3 above, listed here because the
   document itself is a from-scratch build.
2. **Phase-4 registration addendum** — only if the extension chapter keeps significance
   language (12_stats_review.md#L350-L357).
3. *(Optional)* `lab1_f1inv` fault cell — an addition to an existing matrix, not a missing
   capability.

---

## 5. Statistical readiness per phase

| Phase | Readiness | What stands between it and "thesis-ready" |
|---|---|---|
| 1 (xzone bumped + s11–20 + ablation) | **SOUND** with 4 mandatory disclosures | Post-hoc registration timing; Wilcoxon tie-floor; lab3 `auc_goal`/`goal_rate` null next to the `auc_reward` win; the bump + targeted bonus presented inside the as-is/untargeted containing story (12_stats_review.md#L130-L139) |
| 1 (flat headline runs §1.2) | **UNVERIFIABLE LOCALLY** | Restore artefacts from the results branch; resolve the failed pbrs_only arm (12_stats_review.md#L119-L128) |
| 2 (all iterations) | **NOT CONFIRMATORY YET — analysis rerun required** | Seed-key pairing, frozen pooled BH family, §9 registration, degenerate detection rows dropped. Data volume is adequate; flagship effects are large (Δ ≈ −205 to −227 episodes, δ ≈ −0.7 to −0.9) and will likely survive, but "likely" is not auditable today (12_stats_review.md#L224-L238) |
| 3 delay accuracy | **SOUND** | Nothing |
| 3 deadline compliance | **RE-FRAME AS DESCRIPTIVE** | Counts + D-P3-2 caveat; drop significance language; register the family deviation (12_stats_review.md#L292-L298) |
| 4 lab5 / lab4 | **SOUND, conditional** | Disclose n-escalation; fix "pre-registered" label; demote LLM comparison to exploratory (12_stats_review.md#L371-L377) |

---

## 6. The 5 highest-risk items before showing the advisor

1. **Phase 2 has no defensible confirmatory statistic — and Phase 2 is the advisor's
   redirection.** The behaviour is exactly what they asked for, but if they (or a committee
   statistician) ask "how was this tested?", the honest answer today is: pairs may be
   seed-misaligned, the correction family changed with each result, and nothing was
   registered. Fix #1 in §3 is cheap (analysis-only) and must happen before any Phase-2
   number is shown (12_stats_review.md#L161-L238).
2. **lab3 is where the advisor expects the KG to shine, and it is where the KG looks worst.**
   First-goal regression, `auc_goal` null-to-negative, spillage bonus off by default in the
   headline arms. If this reaches the advisor framed as a win, it will read like the last
   meeting's problem again — results not showing what is claimed. Decide §3 item 3 (rerun vs
   reframe) and write the §3 item 4 bridge *before* the meeting (11_gap_analysis.md#L39, #L59).
3. **Phase-1 headline numbers are currently a non-verifiable transcription** — no local
   artefacts, and the PBRS control arm failed and was never re-run, so the three-arm
   isolation story has a hole. Restore or re-dispatch before citing (12_stats_review.md#L119-L128).
4. **Phase-3 compliance significance is vacuous** (deterministic outcome, p-value from ten
   copies of the same number). A statistically literate reader will spot this in minutes;
   presented as counts it is a *strong* result, presented as p=0.00195 it is an easy kill
   (12_stats_review.md#L244-L262).
5. **The word "pre-registered" appears where no registration exists** (PHASE4.md), and the
   n=10→20 escalation was triggered by an observed p-value. Individually minor, but it is a
   credibility risk that contaminates the genuinely well-registered Phase-1/3 work if the
   advisor finds it first. Fix the wording or add the addendum before anything is shared
   (12_stats_review.md#L336-L357).

**Bottom line:** nothing needs to be rebuilt. The system does what the advisor asked in all
three phases; Phase 3 is the strongest deliverable, Phase 2 needs a ~2-day analysis rerun
plus a registration addendum, and Phase 1 needs artefact restoration plus an honest lab3
framing decision. The dominant risk is not missing work — it is presenting existing work
with claims one notch stronger than the evidence, which is precisely what triggered the
advisor's original correction.
