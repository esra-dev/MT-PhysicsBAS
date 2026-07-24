# Phase 2 correction registration (2026-07-22)

**Status: binding pre-data registration for the Phase-2 protocol-v2 corrective
campaign.** Committed on branch `phase234-correction-2026-07-22` after the
corrective implementation was frozen and before any corrected Phase-2
experiment was dispatched. The campaign is defined by this document; corrected
results replace the withdrawn record regardless of direction.

## 1. Why a corrective campaign is required

The defects are documented in `docs/PHASE2_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md`:
the adaptation and certification loops requested contiguous scenario IDs against
non-contiguous files (silent unseeded random resets in ~17–30% of episodes at the
runs of record), start states were recorded before the settle wait, the fault
detector blacklisted healthy components (treatment-correlated inside the strongest
registered cell), the recovery schema could not name secondary blacklists, and the
warm-start parents were trained under the withdrawn Phase-1 protocol v1.

## 2. Previously seen results (full disclosure; all sighted, all withdrawn)

Every corrected cell is a re-run of a sighted cell under a corrected instrument.
Nothing below may influence the corrected sample, which is fixed at seeds 1–20
with no optional extension.

§9.10 post-inversion Tier-1 record (`analysis/out_phase2_registered_postinv/
phase2_recovery_paired.csv`; paired bootstrap q, m=8): lab2_f1bdead −306.5
(q=0.0000), lab3_f2dead_lowsun −71.4 (q=0.0000), labmon2_f2dead_lowsun −147.6
(q=0.0021), lab3_f1dead_z2 −60.2 (q=0.0664, n=9), lab3_f1bdead −90.0 (q=0.365),
lab3_f1binv −6.5 (q=0.929), labmon_f1dead +22.2 (q=0.328), lab3_f1dead +85.0
(q=0.276, seeds 11–20, n=9). Headline: 3 of 8 supported. Detection family: all
null (min q = 0.656). Descriptives sighted: lab3_f1inv +189.2, lab3_f1inv_z2
+30.5, lab2_f1binv +155.75 (n=4). Phase 2.6 KG-silent descriptives (run
29157197853): 172.0 vs 370.2, 162.6 vs 364.0, 51.3 vs 71.5 (both variants).
Phase 2.7 exploratory lab3_f2bdead (run 29187088096): 570.0 vs 447.7,
Δ=+122.3, ns. The pre-inversion 8/8-significant record and every earlier v1–v5
iteration are also sighted history.

Two known instrument artifacts in the sighted record are disclosed as motivating
evidence and expected to change under the corrected instrument: (a) healthy-
component blacklists (notice item 3) — their removal may move any cell in either
direction; (b) silently dropped non-recovered pairs (n=9/9/4 rows above) — the
corrected estimand censors instead of dropping.

## 3. Frozen implementation

Commit `b773a183` (this branch) froze: by-position scenario scheduling with fatal
missing IDs in both adapt-agent loops; settled start-state recording;
fault-detector v2 (`fault-detector-v2`: structural-maskability abstain on
no-response evidence — any active co-feeder of the adjudicated zone, via
`affectedZones` or cross-zone feeds arcs, forces an abstain; inverted evidence
ungated; instant isolation preserved for unmasked evidence); full blacklist-event
recording (`BlacklistEvents` column); ADAPT_OK gate manifests per cell; parent
training under run-mode `phase1_v2_kg_only` (protocol `phase1-v2`: fixed
3,000-episode horizon, TRAINING_OK manifests, zero fallbacks). Unit tests:
`src/test/java/tools/Phase2DetectorV2Test.java` (masking configurations observed
in the withdrawn record; unmasked evidence remains chargeable).

The Spotlight multi-zone adjudication exclusion is retained by design and
disclosed as a detection blind spot; detector v2 does not change it.

## 4. Frozen estimands

- **RecoveryEpisodes** = `ReconvergeEpisode − DetectEpisode`, from the LAST row
  of the cell's recovery CSV (computed in `QLearner.saveRecoveryLog`;
  reconvergence = greedy policy stable for `fault.recover.window` = 50
  episodes; detection = first blacklist event).
- **DetectEpisode** = episode of the primary detection.
- **Censoring (binding):** a negative value (never reconverged / never
  detected) is censored at `adapt_episodes_effective + 1` from the cell's
  ADAPT_OK manifest and KEPT. A seed pair is never dropped; `n = 20` for every
  registered cell. Censored counts are reported per cell and arm.
- One outcome per (cell, arm, seed); the paired difference is
  `ql_true − ql_false` per seed.

## 5. Frozen families and statistics

- **Tier-1 RecoveryEpisodes family (m=8, membership unchanged from §9.5):**
  lab3_f1dead, lab3_f1dead_z2, lab3_f1bdead, lab3_f1binv, lab2_f1bdead,
  labmon_f1dead, lab3_f2dead_lowsun, labmon2_f2dead_lowsun.
- **DetectEpisode family (m=8, membership unchanged from §9.6):** lab3_f1dead,
  lab3_f1inv, lab3_f1dead_z2, lab3_f1inv_z2, lab3_f1bdead, lab3_f1binv,
  lab2_f1bdead, lab2_f1binv. Detector v2 makes this a **new instrument**: its
  corrected results stand alone and are never compared numerically to the
  withdrawn detection record.
- **Statistics (frozen; `analysis/exact_paired_stats.py`):** two-sided exact
  paired sign-flip test (full enumeration at n=20; smallest attainable p =
  2/2²⁰), exact two-sided sign test, paired rank-biserial, 10,000-draw
  bootstrap CI on the mean paired difference (fixed seeds), Benjamini-Hochberg
  within each m=8 family separately. No p/q may be reported as zero.
- **Decision rule per Tier-1 cell:** supported (KG faster) iff BH q ≤ 0.05 and
  the mean paired difference is negative; adverse iff q ≤ 0.05 and positive;
  otherwise null. All tests are two-sided. The campaign-level statement is the
  count of supported/adverse/null cells; no pooling across cells.
- **Registered descriptives (no q-values, never confirmatory):** lab1_f1dead
  (degenerate single-actuator control), lab2/lab3 f1dead/f1inv/f2dead/f2inv
  recovery, lab2_f1binv recovery, lab3_f1inv/f1inv_z2 recovery, all Phase-2.6
  KG-silent variants, lab3_f2bdead (exploratory multi-blind), all
  RecoveredGoalRate / degradation columns, and all blacklist-event counts.
  Blacklist-event counts per cell/arm WILL be reported (the corrected
  false-positive record) but define no hypothesis test.

The frozen analysis code is `analysis/phase2_v2_registered_family.py`; archive
gates are `analysis/validate_phase2_v2_archive.py`; full reproduction is
`python analysis/reproduce_phase2_v2.py phase2_v2_corrected`.

## 6. Campaign: seeds, dispatches, failure rules

- Seeds **1–20**, fixed, both arms, every cell; no optional extension. Seed
  pairing is by workflow seed (`-RunSeed`), identical for both arms of a cell.
- Workflow: `.github/workflows/phase2.yml` at or after the registration head;
  `run_mode=phase1_v2_kg_only`, `adapt_episodes=0` (per-profile defaults),
  `publish_results=true`.
- **Four registered dispatches** (matrix limit 256 jobs):

| Dispatch | adapt_profiles | seeds |
|---|---|---|
| A1 | Group A (12): lab1_f1dead, lab2_f1dead, lab2_f1inv, lab2_f2dead, lab2_f2inv, lab2_f1bdead, lab2_f1binv, labmon_f1dead, labmon_infoonly_f1dead, labmon_nostereo_f1dead, labmon2_f2dead_lowsun, labmon2_infoonly_f2dead_lowsun | 1–10 |
| A2 | Group A (12) | 11–20 |
| B1 | Group B (11): lab3_f1dead, lab3_f1inv, lab3_f2dead, lab3_f2inv, lab3_f1dead_z2, lab3_f1inv_z2, lab3_f1bdead, lab3_f1binv, lab3_f2bdead, lab3_f2dead_lowsun, labmon2_nostereo_f2dead_lowsun | 1–10 |
| B2 | Group B (11) | 11–20 |

- All four dispatches are queued after this registration is pushed and CI is
  green on the registration head. Until every aggregate completes, only
  operational status (job success/failure) is inspected — no data values.
- **Failure rule:** a failed cell or dispatch is preserved and documented; a
  re-dispatch uses byte-identical inputs and both run IDs are recorded. No
  data-bearing cell is ever silently replaced. A cell that hard-fails on a
  scenario lookup is an instrument bug to be fixed and disclosed, not skipped.

## 7. Archives and completion gates

Each run is archived permanently under `phase2_v2_corrected/run_<run_id>/`
(consolidated artifact: `recovery_root/`, `analysis/out/` including
`workflow_inputs.json`, parent provenance under `_artifacts/clean/`), with an
`ARCHIVE_MANIFEST.md` and SHA-256 inventory. Completion requires: all four
aggregates green; every adapt cell carries a passing ADAPT_OK (protocol
`phase2-v2`, detector `fault-detector-v2`, settled start state, zero
fallbacks, paired-arm schedule identity, non-empty parent-qtable hash); every
parent cell carries a protocol `phase1-v2` TRAINING_OK; the registered tables
rebuild byte-equivalently (canonical numeric form) from the committed archives
alone; results tags verified on the remote.

## 8. Reading rules

Corrected results replace the withdrawn narrative whether favourable, adverse,
or null. If fewer Tier-1 cells are supported than the withdrawn 3/8, that is
the finding. The corrected blacklist-event record replaces every
false-positive claim; "zero false positives" may only be asserted again if the
corrected record shows zero spurious events, with the Spotlight blind spot
stated alongside. Historical archives remain untouched for provenance.
