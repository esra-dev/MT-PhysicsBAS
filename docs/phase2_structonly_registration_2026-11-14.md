# Phase 2 structure-only fault-detection registration (2026-11-14)

**Status: BINDING pre-data registration for the Phase-2 structure-only
campaign (`phase2_v3_structonly`).** Committed on branch
`phase2-structonly-2026-11` (cut from `main` at `4700e4fc`) after the
implementation freeze commit named in §4 and before any cell of this campaign
is dispatched. Nothing in the 2026-07 corrected record
(`phase2_v2_corrected/`) or the 2026-11 delivered low-sun record
(`phase2_v3_lowsun/`) is edited, re-analysed, or relabelled.

## 1. The registered prediction (stated first)

THESIS_STATE_REPORT Addendum 2026-11-10 (the Phase-1 Brick-structure-only
registration) named this campaign in advance:

> **Out of scope here (named for the record):** a Phase-2 dispatch of the same
> flag on a dead-lamp lab, where the Brick arm cannot abstain on IV-gated
> components and is predicted to blacklist healthy blinds at night. That is
> the sharper Elementary test and would need its own registration.

This document is that registration.

- **P1 (primary, directional).** With the adaptation step's knowledge layer
  switched to BRICK, the fault detector wrongly blacklists healthy
  components — specifically blinds adjudicated below sun rank 2, where the
  full layer's IV-gate abstains and the Brick layer cannot. Registered as the
  WrongBlameEvents family (§6): a member supports the prediction iff
  q ≤ 0.05 and Δ = structonly − record > 0. The two pinned low-sun members
  are the cleanest exposure: every episode runs at sun rank 1, where the full
  layer never adjudicates a blind and the Brick layer adjudicates every
  falsifiable OPEN. The runs of record have **zero** false-positive blacklist
  events in all four cells, so any wrong blame is attributable to the layer.
- **P1b (registered descriptive).** The wrongly blamed components in the
  structure-only low-sun members are predominantly blind components
  (`SetZ1Blinds`/`SetZ2Blinds`), per the component histogram of §7.
- **The DetectEpisode and RecoveryEpisodes families carry NO directional
  prediction.** For the dead-blind cells two mechanisms oppose each other:
  the Brick layer loses the active blind self-test (slower detection) but
  also loses the sun-rank gate on blind adjudication (faster, unsound
  detection of the genuinely dead blind). Both families are reported
  two-sided under the frozen decision rule of §6.

## 2. Mechanism: exactly what the BRICK layer removes from the detector

Frozen reading of the code at the freeze commit (all paths verified):

1. **IV-gated abstention.** `QLearner.observeForFaults` adjudicates IV-gated
   (blind) components only on their OPEN action and only at sun rank ≥ 2
   (`IV_DETECT_MIN_SUN_RANK`). The IV-gated set comes from the reasoner's IV
   bindings; the BRICK layer binds no independent variable
   (`config/golden_registry/brick_only/`: `hasIV=false`, `ivIdx=-1` on every
   blind), so the gate is vacuous and blinds are adjudicated like lamps in
   every state — CLOSE actions and darkness included. A healthy blind opened
   in the dark produces the expected null rank response, which the ungated
   detector reads as dead.
2. **Active self-test.** `QLearner.getDiagnosticProbeAction` probes only
   IV-gated components; under BRICK none exist, so dead blinds are no longer
   actively probed and their detection depends on the policy happening to
   open them.
3. **Weak-coupling classification.** `BRICK_CROSS_ZONE_FEEDS_QUERY` sees the
   same `brick:feeds` arcs but not the `ws:WeakOpticalCoupling` stereotype,
   so every cross-zone arc is consumed as PRIMARY. `getActionPrediction` then
   co-signs directional rank claims on neighbour zones that the full layer
   deliberately withholds (a weak spill does not reliably move a discretised
   rank), and the detector-v2 masking abstention sees additional co-feeders.
   The net direction of this change is not predicted.

The switch applies to the WHOLE adaptation step in BOTH arms (the layer is a
per-JVM property). In the `ql_false` arm the re-learn is tabula-rasa, so its
members isolate the detector-pipeline change almost cleanly; in the `ql_true`
arm the re-learn priors change too (Brick priors; no IV-aware penalties; all
arcs primary). The clean warm-start training is NOT switched: parents are
trained in-run under `phase1_v2_kg_only` exactly as in the runs of record, so
both sides of every pair start from the same policies (§7 verifies this).

## 3. Previously seen results (full disclosure; none may influence the sample)

- Corrected 2026-07 record (head `19f4f3ff`): `lab2_f1bdead` Δ = −92.65
  (q = 1.017×10⁻⁵, supported), `lab3_f1bdead` Δ = −19.95 (q = 0.595, null);
  zero false-positive blacklist events in all 38 cells × 20 seeds × both
  arms; blind cells detect in 5–6 episodes in both arms (probe-driven).
- Delivered low-sun record (head `77e7791f`): `lab3_f2dead_lowsun`
  Δ = +2153.0 (q = 1.95×10⁻³, adverse; KG detects 0/20 vs TR 11/20),
  `labmon2_f2dead_lowsun` Δ = +1087.8 (q = 0.0312, adverse; KG 14/20 vs TR
  20/20); 88 blacklist events, all naming the two genuinely dead lamps; zero
  false positives.
- Withdrawn protocol-v1 records (sighted, not citable): under detector v1 the
  post-inversion runs DID blacklist healthy components (the v2 structural
  abstention removed exactly that); those runs carry the withdrawn v1 defects
  and are never compared against.
- Phase-1 Brick-structure-only campaign and the Phase-4 knowledge ladder
  (Brick structure reproduces 93–98 % of the Phase-4 effect): seen, and the
  motivation for this test; neither contains any fault-detection outcome.

## 4. Frozen implementation

The treatment is ONE flag; no agent code, profile, scenario file, or golden
registry changes:

- `run_phase2_adapt.ps1 -KnowledgeLayer full|brick|redundancy` (default
  `full` forwards nothing, keeping the runs-of-record path byte-identical).
  A non-default layer is forwarded to `taskAdapt` as
  `-Pstereo.knowledgeLayer` — the same flag the training runner uses — which
  `build.gradle` injects into the adapt JVM as a system property.
- Treatment delivery is verified per cell at run time: the layer the adapt
  JVM actually constructed is read back from the `StereotypeReasoner:
  knowledge layer = …` banner in the cell log; a mismatch fails the cell.
  Every ADAPT_OK manifest records `knowledge_layer` (requested) and
  `knowledge_layer_delivered` (log-derived).
- `.github/workflows/phase2.yml` exposes `knowledge_layer` (validated
  fail-fast in the setup job), passes it to the orchestrator and into
  `analysis/out/workflow_inputs.json` (`--knowledge-layer`).
- `analysis/validate_phase2_v2_archive.py --require-knowledge-layer brick`
  makes the delivery evidence mandatory for every cell of this campaign.
- Guards: `analysis/tests/test_phase2_structonly_pipeline.py` pins the whole
  chain (orchestrator, workflow, Gradle forwarding, validator gate, frozen
  analysis constants against the faulty-flow generator).
- Everything else is the corrected protocol unchanged: protocol `phase2-v2`,
  detector `fault-detector-v2`, by-position scheduling, settled start
  recording, `fault.recover.window = 50`, per-profile `training_params`,
  parents trained in-run under `phase1_v2_kg_only` (protocol `phase1-v2`),
  low-sun schedules and gates exactly as in the round-3 campaign.
- Freeze commit: `c4334b2a` (this branch). The dispatch head is recorded in
  the dispatch record.
- A pipeline smoke on the NON-campaign cell `lab2_f1dead` (smoke budget,
  cold start, `-KnowledgeLayer brick`) verifies flag delivery and manifest
  fields before dispatch; its outcomes are not part of any family and are
  not reported beyond the dispatch record.

## 5. Frozen estimands

- **WrongBlameEvents** (new, primary): the number of `BlacklistEvents`
  entries in the LAST row of the cell's recovery CSV whose component URI
  fragment is NOT in the cell's injected set. Frozen injected sets
  (`simulator/generate_faulty_flows.ps1`): `lab2_f1bdead` → {SetZ1Blinds},
  `lab3_f1bdead` → {SetZ1Blinds}, `lab3_f2dead_lowsun` → {SetZ1Light,
  SetZ2Light}, `labmon2_f2dead_lowsun` → {SetZ1Light, SetZ2Light}. No
  censoring; an empty field counts 0.
- **DetectEpisode** and **RecoveryEpisodes**: from the LAST recovery row,
  censored at `adapt_episodes_effective + 1` and KEPT when negative, exactly
  as in the corrected campaign; n = 20 per member, no pair dropped.
- **Paired difference = structonly − record per seed** (seeds 1–20), per
  (cell, arm) member. Two-sided exact sign-flip test
  (`analysis/exact_paired_stats.py`), exact sign test, paired rank-biserial,
  10,000-draw fixed-seed bootstrap CI (base seed 20261114; a distinct stream
  per family and member); no p/q reported as zero (exact floor 2/2²⁰).
- **Frozen comparators** (full-layer runs of record, raw per-seed files):
  `lab2_f1bdead`, `lab3_f1bdead` → `phase2_v2_corrected/run_30001857104`,
  `run_30001867521`, `run_30001878310`, `run_30001888910`;
  `lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun` →
  `phase2_v3_lowsun/run_43099277363` ONLY (never the superseded mixed-sun
  rows of the corrected campaign). The loader fails on any duplicate.
- **Cross-head comparison, disclosed:** the records were produced at heads
  `19f4f3ff` (2026-07) and `77e7791f` (2026-11); the structure-only runs are
  produced at this branch's dispatch head. As in the round-3 campaign this
  cross-head pairing is disclosed, and §7's parent-identity and
  full-layer-invariance evidence bounds it.

## 6. Frozen families and decision rule

Three families, each with the same 8 members — (cell, arm) for the four cells
× {ql_true, ql_false} — BH within each family separately (m = 8):

1. **WrongBlameEvents family** (primary; P1).
2. **DetectEpisode family.**
3. **RecoveryEpisodes family.**

Decision rule per member (two-sided throughout): **elementary_adds** iff
q ≤ 0.05 and Δ > 0 (removing the physics layer makes the outcome worse:
more wrong blames / later detection / slower recovery — the physics layer
earns its place on that member); **elementary_costs** iff q ≤ 0.05 and
Δ < 0; otherwise **null**. The campaign statement is the count of
adds / costs / null members per family; no pooling across members, cells, or
arms. P1 is confirmed on a member iff that WrongBlameEvents member is
`elementary_adds`.

Frozen analysis code: `analysis/phase2_structonly_v3_family.py`; archive
gates: `analysis/validate_phase2_v2_archive.py --require-treatment-delivery
--require-knowledge-layer brick`; full reproduction:
`python analysis/reproduce_phase2_structonly_v3.py phase2_v3_structonly`.
The analysis is run ONCE on the curated archive and committed; the reproducer
must rebuild all four tables byte-equivalently (canonical numeric form).

## 7. Registered descriptives (no q)

- Component histogram of all blacklist events per member (URI fragment ×
  episode), separating injected from healthy components — the P1b check.
- Detection counts per member; censor counts per member and side.
- Parent identity: the `parent_qtable_sha256` of every structure-only cell
  equals the corresponding record cell's (expected identical: deterministic
  simulator, seeded training, full-layer parents on both sides). A mismatch
  is reported prominently and bounds the cross-head reading of §5.
- Knowledge-layer delivery: 160/160 manifests `knowledge_layer =
  knowledge_layer_delivered = brick`; per-cell banner evidence distilled from
  the adapt logs into `verification/adapt_log_knowledge_layer_evidence.csv`.
- Degradation columns (BestEffortRank / RankShortfall / DegradedMode) for the
  low-sun members, read under the round-3 Amendment A1 rule (conditional on
  detection; never an outcome-based voiding rule).

## 8. Campaign: seeds, dispatch, failure rules

- Seeds **1–20**, both arms, all four cells; no optional extension.
- One dispatch of `.github/workflows/phase2.yml`, ref
  `phase2-structonly-2026-11`, at or after the registration head:
  `adapt_profiles=lab2_f1bdead,lab3_f1bdead,lab3_f2dead_lowsun,labmon2_f2dead_lowsun`,
  `seeds=1,…,20`, `run_mode=phase1_v2_kg_only`, `adapt_episodes=0`,
  `knowledge_layer=brick`, `publish_results=true`. Matrix: 3 parents × 2
  stereo × 20 seeds = 120 clean training cells + 4 cells × 2 arms × 20 seeds
  = 160 adaptation cells.
- Until the aggregate completes only operational status is inspected.
- **Failure rule:** a failed cell or dispatch is preserved and documented; a
  re-dispatch uses byte-identical inputs and both run IDs are recorded in the
  dispatch record. No data-bearing cell is ever silently replaced.
- **Voiding rule (instrument-based only):** an adapt cell whose manifest does
  not carry `knowledge_layer = knowledge_layer_delivered = brick`, or a
  low-sun cell without the pinned-schedule evidence, voids that cell; the
  defect is fixed and the campaign re-dispatched with byte-identical inputs,
  both run IDs recorded. No outcome-based voiding rule is registered
  (round-3 Amendment A1 lesson).

## 9. Archives and completion gates

Archive under `phase2_v3_structonly/run_<run_id>/` via
`scripts/curate_phase2_structonly_v3.ps1` (consolidated artifact:
`recovery_root/`, `analysis/out/` incl. `workflow_inputs.json` with
`knowledge_layer = brick`, parent provenance under `_artifacts/clean/`; plus
`verification/adapt_log_knowledge_layer_evidence.csv` distilled from the
per-cell adapt logs), with `ARCHIVE_MANIFEST.md`, SHA-256 inventory and
`CAMPAIGN_MANIFEST.md`. The raw recovery CSVs are gitignored as in every
protocol-v2 campaign: the committed subset carries the manifests, metrics,
tables and inventories, and the complete extracted archive is kept locally
and in the 90-day workflow artifacts (downloaded promptly at curation).
Completion requires: aggregate green; every adapt cell passes the archive
validator WITH both strict gates; every parent cell carries a protocol
`phase1-v2` TRAINING_OK; the registered tables rebuild byte-equivalently via
the reproducer; results-branch copies verified on the remote.

## 10. Reading rules

- This is a WHOLE-PROCESS layer switch, not an isolated detector ablation:
  `ql_false` members isolate the detector pipeline (tabula-rasa re-learn);
  `ql_true` members measure the detector and prior changes jointly. The two
  readings are never merged.
- Results are reported whether they support, contradict, or miss the
  registered prediction, with the same prominence. An `elementary_costs` or
  null WrongBlameEvents family is reported as "the sharper Elementary test
  did not confirm the predicted protective role".
- Detection differences propagate mechanically into RecoveryEpisodes
  (= Reconverge − Detect, with shared censoring); recovery members are read
  with that coupling stated, as in the round-3 record.
- The 2026-07 and 2026-11 records keep their classifications; the
  structure-only condition is a new column of the record, never a
  re-analysis of the old ones. No numerical comparison between this campaign
  and the Phase-1/Phase-4 ladders is confirmatory.

**One-shot rule:** nothing above may be adjusted after data contact;
deviations must be labelled deviations in the reporting addendum.
