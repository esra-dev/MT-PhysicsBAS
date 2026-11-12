# Phase 2 low-sun re-execution registration (2026-11-11)

**Status: BINDING pre-data registration for the Phase-2 low-sun re-execution
(campaign `phase2_v3_lowsun`).** Committed on branch `round3-rerun-2026-11`
after the implementation freeze commit `86ab4cdd` and before any cell of
this campaign is dispatched. Results replace the current "intended treatment
not delivered / unknown" classification of the two registered low-sun cells
regardless of direction. Nothing in the 2026-07 corrected record
(`phase2_v2_corrected/`) is edited, re-analysed, or relabelled.

## 1. Why a re-execution is required

Round-2 audit findings R2-001 (critical) and R2-002 (high)
(`docs/final_state/AUDIT_RESOLUTION.md`): the registered low-sun manipulation of
the Tier-1 cells `lab3_f2dead_lowsun` and `labmon2_f2dead_lowsun` lived only in
the simulator's episode-reset sampler (`Sunshine = 100`), which the protocol-v2
explicit settled scenario starts bypass. Both profiles mapped to their clean
parents' training schedules (`train_scenarios_lab3.json`,
`train_scenarios_labmon2.json`), whose Sunshine values are {0, 100, 400, 900}.
Consequently `lab3_f2dead_lowsun` is byte-identical to `lab3_f2dead` (both
arms, all 20 seeds), and `labmon2_f2dead_lowsun` delivered its dual dead-lamp
fault but not the pin. The corrected record therefore contains **no low-sun
result**; the design premise of both cells (nominal goal unreachable on every
episode, forcing re-valuation of the Spotlight / Monitor) was never in force.

## 2. Previously seen results (full disclosure; none may influence the sample)

- Corrected 2026-07 record for the SAME cell names under the delivered
  **mixed-sun** schedule (`phase2_v2_corrected/analysis/registered/`):
  `lab3_f2dead_lowsun` Δ = +3654.15 (adverse; KG detection 0/20, KG recovery
  censored 20/20; 21/40 records report BestEffortRank = 3, impossible under a
  100-lux pin), `labmon2_f2dead_lowsun` Δ = −168.75 (q = 1.15e-3, supported for
  the delivered full-sun-schedule condition; detection 20/20 both arms).
- Withdrawn protocol-v1 records (sighted, not citable): §9.10 post-inversion
  `lab3_f2dead_lowsun` −71.4, `labmon2_f2dead_lowsun` −147.6; the superseded
  pinned-sun run 28866807391. Under protocol v1 the episode-reset sampler WAS
  the start mechanism, so those runs did pin the sun but carry the withdrawn
  v1 defects (unseeded random resets on missing scenario IDs, pre-settle
  start reads, detector v1). They are the only sighted evidence about a
  delivered low-sun condition and they point towards "supported"; this
  registration fixes seeds, families and decision rules so that expectation
  cannot shape the analysis.

## 3. Frozen implementation (commit `86ab4cdd`)

- **Scenario-level treatment.** New schedules
  `benchmark/train_scenarios_lab3_lowsun.json` (SHA-256
  `119dc7556fd874d34b876c56c2738fb86d767e6da366c5be9b7fbb16ba260c43`) and
  `benchmark/train_scenarios_labmon2_lowsun.json` (SHA-256
  `8e9f54673edaeb740db007fdd0f5a58803258d0ad155f1e8e8171b538ba656e6`), derived
  deterministically by `analysis/build_lowsun_scenarios.py` from the parents:
  identical ids, order and actuator start states; `Sunshine = 100` in every
  scenario; declared levels recomputed with the clean physics (the simulator
  recomputes zone levels from actuator state on every tick, so start levels are
  transient). The schedule hash (comma-joined ids) is unchanged by construction
  (lab3 `fd9853f1…`, labmon2 `c0400237…`); the file hash distinguishes the
  treatment.
- **Mapping.** `config/run_config.json` `phase2.train_scenarios_map` and
  `src/agt/lab_profiles.asl` `train_scenarios(...)` point all four `*_lowsun`
  profiles (the two registered cells and the two KG-silent variants) at the
  pinned files. The faulty flows and `simulator/generate_faulty_flows.ps1` are
  unchanged (the reset-sampler pin is now redundant and harmless).
- **Delivery gates.** `run_phase2_adapt.ps1` refuses to start any `*_lowsun`
  cell whose schedule does not pin 100 in every scenario, and refuses any
  profile whose config and ASL scenario files disagree; every ADAPT_OK manifest
  now records `scenario_file_sha256`, `scenario_sunshine_values` and
  `lowsun_pin_delivered`. `analysis/validate_phase2_v2_archive.py
  --require-treatment-delivery` makes that evidence mandatory;
  `analysis/tests/test_lowsun_treatment_delivery.py` pins the whole chain.
- **Everything else is the 2026-07 corrected protocol**: protocol `phase2-v2`,
  detector `fault-detector-v2`, by-position scheduling, settled start
  recording, `fault.recover.window = 50`, per-profile `training_params`
  (lab3 4000 episodes; labmon2 4000), parents trained in-run under
  `phase1_v2_kg_only` (protocol `phase1-v2`, 3000 episodes). The Spotlight
  multi-zone adjudication exclusion is retained and disclosed as before.
- The implementation commit also contains the Phase-1b forwarding fix and its
  gates (`docs/phase1b_extended_rerun_registration_2026-11-11.md`); those
  knobs are 0.0 in every Phase-2 mode and do not touch this campaign.

## 4. Frozen estimands (unchanged from the 2026-07-22 registration §4)

- **RecoveryEpisodes** = `ReconvergeEpisode − DetectEpisode` from the LAST row
  of the cell's recovery CSV; **DetectEpisode** = episode of primary detection.
- **Censoring (binding):** a negative value is censored at
  `adapt_episodes_effective + 1` and KEPT; `n = 20` per cell, no pair dropped.
- Paired difference `ql_true − ql_false` per seed; exact two-sided sign-flip
  test (`analysis/exact_paired_stats.py`), exact sign test, paired
  rank-biserial, 10,000-draw fixed-seed bootstrap CI; no p/q reported as zero.

## 5. Frozen families, decision rule, and delivery signature

- **Low-sun RecoveryEpisodes family (m = 2):** `lab3_f2dead_lowsun`,
  `labmon2_f2dead_lowsun`. **Low-sun DetectEpisode family (m = 2):** the same
  two cells. BH within each family separately.
- **Hypothesis H-P2 (unchanged):** after detection and blacklisting, the
  KG-primed arm re-converges in fewer episodes: mean paired difference < 0.
  Decision rule per cell: supported iff q ≤ 0.05 and Δ < 0; adverse iff
  q ≤ 0.05 and Δ > 0; otherwise null. Two-sided tests. The campaign statement
  is the count of supported / adverse / null cells; no pooling.
- **The original m = 8 families are not recomputed.** Their rows for these two
  cell names remain classified as "delivered mixed-sun / treatment not
  delivered" in the dossier; the new m = 2 results are reported alongside as
  the delivered low-sun condition. No numerical comparison between the two is
  confirmatory.
- **Registered delivery signature (voiding rule):** under pinned sun 100 with
  both task lamps dead the nominal rank-3 goal is unreachable in both zones of
  both labs (lab3 ceiling 25 + 150 + 50 + 30 = 255 lux; labmon2 ceiling
  25 + 200 + 50 = 275 lux). Any record of either cell with
  `BestEffortRank = 3` or `RankShortfall = 0` falsifies treatment delivery and
  voids the campaign (instrument bug to be fixed and disclosed, never
  analysed around). The per-seed table written by the frozen analysis exposes
  these columns.
- **Registered descriptives (no q):** detection counts per arm, censor counts,
  recovered goal rates, degradation columns, blacklist-event counts, and
  byte-level comparison of the re-trained parents with the archived 2026-07
  parents (expected identical: deterministic simulator and seeded training).
- Frozen analysis code: `analysis/phase2_lowsun_v3_family.py`; archive gates:
  `analysis/validate_phase2_v2_archive.py --require-treatment-delivery`; full
  reproduction: `python analysis/reproduce_phase2_lowsun_v3.py phase2_v3_lowsun`.

## 6. Campaign: seeds, dispatch, failure rules

- Seeds **1–20**, both arms, both cells; no optional extension.
- Workflow `.github/workflows/phase2.yml`, ref `round3-rerun-2026-11`, at or
  after the registration head: `adapt_profiles=lab3_f2dead_lowsun,labmon2_f2dead_lowsun`,
  `seeds=1,…,20`, `run_mode=phase1_v2_kg_only`, `adapt_episodes=0`,
  `publish_results=true`. Matrix: 2 parents × 2 arms × 20 seeds = 80 clean
  training cells + 2 cells × 2 arms × 20 seeds = 80 adaptation cells.
- Until the aggregate completes only operational status is inspected.
- **Failure rule:** a failed cell or dispatch is preserved and documented; a
  re-dispatch uses byte-identical inputs and both run IDs are recorded in the
  dispatch record. No data-bearing cell is ever silently replaced.
- The two KG-silent variants (`labmon2_infoonly_f2dead_lowsun`,
  `labmon2_nostereo_f2dead_lowsun`) are mapped to the pinned schedule for
  consistency but are NOT part of this campaign (descriptive-only in the
  record; re-execution optional later, never confirmatory).

## 7. Archives and completion gates

Archive under `phase2_v3_lowsun/run_<run_id>/` (consolidated artifact:
`recovery_root/`, `analysis/out/` incl. `workflow_inputs.json`, parent
provenance under `_artifacts/clean/`), with `ARCHIVE_MANIFEST.md`, SHA-256
inventory and `CAMPAIGN_MANIFEST.md`. Completion requires: aggregate green;
every adapt cell carries a passing ADAPT_OK **with** `lowsun_pin_delivered =
true` and `scenario_sunshine_values = [100]`; every parent cell carries a
protocol `phase1-v2` TRAINING_OK; the delivery signature of §5 holds in every
record; the registered tables rebuild byte-equivalently from the committed
archive alone; results-branch copies verified on the remote.

## 8. Reading rules

Results replace the "unknown" classification whether supported, adverse, or
null. A supported result is a corrected-protocol low-sun finding and nothing
more; an adverse or null result is reported with the same prominence. The
2026-07 rows keep their classification, and the two conditions are never
merged into one count. Historical archives remain untouched.

## Amendment A1 (2026-11-12, POST-DATA, disclosed) — the §5 delivery signature was mis-specified

§5 registered a voiding rule: any record of either cell with `BestEffortRank = 3`
or `RankShortfall = 0` falsifies treatment delivery. After the run, 29/40
`lab3_f2dead_lowsun` records and 6/40 `labmon2_f2dead_lowsun` records carry
exactly those values while every manifest, file hash and the preflight show the
pinned schedule in force. Inspection of the instrument — not of the outcomes —
shows the rule itself was wrong: `BestEffortRank` reports `effectiveGoal`, which
starts equal to the nominal goal (`src/env/tools/QLearner.java`, constructor:
"effective (best-effort) goal starts equal to the nominal goal") and is lowered
ONLY by `finishReachabilityProbe`, which the adapt agent runs inside `!on_defect`
after a component has been blacklisted
(`src/agt/illuminance_controller_agent_adapt.asl`, best-effort degradation
block). A record whose cell never detected a fault therefore carries the
nominal rank by construction, at any sun. The 35 flagged records are exactly
the 35 never-detected records (lab3: 20 KG + 9 TR; labmon2: 6 KG), and all 45
detected records show `BestEffortRank = 2`, `RankShortfall = 1`,
`DegradedMode = 1` — the ceiling the pin predicts for both labs. The same
artefact explains the 21/40 (= 20 KG + 1 TR non-detections) that audit R2-001
read as a sun-mixing signature in the 2026-07 record; R2-001's non-delivery
finding rested on byte identity and stands.

**Decision:** the voiding rule is restated as *conditional on detection*: every
record in which a fault was detected must show a best-effort rank below the
nominal goal. Under the restated rule delivery is confirmed 45/45, in addition
to the manifest evidence. This amendment is made after seeing the data and is
reported as such. It changes no estimand, family membership, statistic, or
decision rule of H-P2; the recovery and detection outcomes are reported exactly
as the frozen analysis produced them.
