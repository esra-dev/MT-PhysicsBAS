# Phase-1 Methods — Registration & Disclosure (thesis-ready draft)

> **SUPERSEDED METHODS DRAFT (2026-07-21).** This describes protocol-v1 and must not be
> used as the final Phase 1 Methods section. Its empirical results and inferential claims
> are protocol-affected. See `docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md` and the
> forthcoming protocol-v2 correction registration.

**Status:** drop-in Methods subsection for the Phase-1 chapter. Drafted 2026-07-19
from THESIS_STATE_REPORT.md Addendum 2026-07-19b §3 (the canonical paragraph, quoted
verbatim in §1 below) plus the three additional disclosures required by the 2026-07-19
Phase-1 audit (`docs/audit/phase1_audit_2026-07-19.md`, Part B6/D5). Nothing in this
document changes any statistic; it is provenance only. All June-2026 run IDs cited
below are pre-inversion-instrument runs, cited here as historical timeline anchors.

---

## 1. Canonical registration-timing paragraph (use verbatim in Methods)

> **Registration timing (Phase 1).** The Phase-1 design addendum (§7 of the
> pre-registration document: hypotheses H-CL1–H-CL4, primary-metric tiers, and BH
> families) was committed as `ef7aaf2` and pushed on 2026-06-19 at 10:59 UTC. Timing
> here is anchored to GitHub Actions run-creation timestamps — assigned server-side
> at dispatch and not editable afterwards — rather than to git commit dates, which
> are client-set; the push instant is fixed by the CI runs that push itself
> triggered (27821722610, 27821723294). By this clock, registration postdates every
> Phase-1 training run analysed in the pre-inversion analysis documents: the first
> dispatch of the Phase-1 workflow (run 27305796237, 2026-06-10 20:56 UTC), the
> factorial-arm run behind the pre-inversion headline table (run 27336756264,
> 2026-06-11), and the cross-zone as-is, bumped, seeds-11–20, and mechanism-ablation
> runs (runs 27440842780, 27461188614, 27462446044, 27464846574; 2026-06-12 to
> 2026-06-13) — a lag of 8.6 days after the first dispatch and 6.0 days after the
> last of these runs. The addendum's own text moreover cites the completed analysis
> write-ups, so it postdates not only data collection but the written analyses; the
> statement that its hypotheses reflect pre-analysis intent rests on author
> assertion and is not supported by the commit record. All Phase-1 results from the
> June 2026 runs are therefore reported as confirmatory-with-post-hoc-registration
> (Munafò et al., 2017) and never as pre-registered. The Phase-1 headline of record
> stands on different footing: the post-inversion arm-C run 29639767776 was
> dispatched on 2026-07-18 at 09:48 UTC, 29 days after the §7 hypothesis and metric
> families were frozen, and the commit it executed (`e631877`, the run's
> server-recorded head) already contained both the frozen §7 families and the
> addendum registering that re-run as an outstanding duty — for the headline table,
> registration verifiably precedes dispatch.

## 2. Three additional disclosures (2026-07-19 audit; include in Methods, condensed if needed)

1. **Commit-message labeling.** The commit that added the §7 Phase-1 registration
   (`ef7aaf2`) carries the message *"docs(phase3): add §8 pre-registration addendum +
   Phase 3 results section to paper_results_section"* — it names only Phase 3,
   although the same commit added 171 lines to `docs/pre_registration.md` including
   the entire Phase-1 §7 addendum. A reader auditing the history by commit messages
   would not find the Phase-1 registration event; the thesis must not imply the
   registration was a separately visible, labelled act.

2. **Registered-vs-executed configuration mismatch.** §7.2 registers the
   configuration under test as run profile **`phase1_kg_xzone`** —
   `cross_zone_bonus = 3.0` (targeted) and `num_episodes = 10000`. The headline of
   record (arm C, **`phase1_kg_only`**, runs 29639767776 + 29692725784) executes
   `cross_zone_bonus = 0.0` and an **effective 3000-episode budget** (the CI runner
   patches every profile to the run-config `num_episodes`; see the budget-correction
   note in THESIS_STATE_REPORT.md §4.1). The H-CL1–H-CL4 hypotheses are
   metric-and-direction statements that carry over to the headline arm, but the
   frozen §7 configuration block does **not** describe the headline configuration.
   Registration cover for the headline arm comes from the later dated addenda: the
   arm-C re-run registered as an outstanding duty (Addendum 2026-07-13, contained in
   dispatched head `e631877`) and the seeds-11–20 extension + pooled-20 m = 3 family
   (Addendum 2026-07-18c, contained in dispatched head `02ed6c1`). State this
   two-layer structure explicitly rather than citing "§7" as if it covered the
   executed configuration.

3. **Family-assignment inconsistency inside §7.** The H-CL1 hypothesis text
   prescribes "BH family m = 42 (all benchmark paired tests)" for `auc_goal`, and
   H-CL4 does the same for `auc_reward` — but both metrics live in
   `learning_speed_tests.csv`, which §7.4 assigns to the **m = 12 learning-speed
   family**. The executed analyses used the per-file families as implemented in
   `analysis/sweep_report.py` (m = 12 learning-speed / m = 42 benchmark for a
   three-lab run), and the pooled-20 primary used the separately registered m = 3
   family. Report this as a drafting error in the registration, state the executed
   family next to every quoted q-value, and do not present the §7 text as if it were
   internally consistent.

## 3. Labeling rules for the results chapter (mandatory)

- **Every number from a June-2026 run** (27305796237 through 27464846574, incl. the
  pre-inversion headline 27336756264 and the xzone family) carries the label
  *confirmatory-with-post-hoc-registration* — and, since the action-space inversion
  of 2026-07-10, additionally *pre-inversion instrument, superseded as headline
  evidence*.
- **The June seeds-11–20 xzone replication (run 27462446044)** is labelled a
  *sighted, unregistered seed-replication* (dispatched 16 minutes after the
  seeds-1–10 results were available, with no registration in existence at either
  dispatch); it must not be called an independent pre-registered confirmation.
- **The July headline runs** (29639767776; extension 29692725784) are labelled
  *registered-at-dispatch* (registration ⊂ dispatched tree, verifiable from run
  metadata + `git show`), with the pooled-20 m = 3 family as the confirmatory
  statistics and everything else descriptive.
- **Single-shot rule:** seeds 11–20 was the one registered seed extension; any
  further extension requires a fresh registration that first discloses the pooled-20
  outcome (Addendum 2026-07-19c §5).

Cross-references: THESIS_STATE_REPORT.md §5.5 (caveats), Addenda 2026-07-19b
(timeline), 2026-07-18c (registration), 2026-07-19c (Plan B report), 2026-07-19d
(pooled-20 descriptive supersession); `docs/audit/phase1_audit_2026-07-19.md` Part B6.
