# Phase-1b extended-arm re-execution campaign (v3, 2026-11)

Registration: `docs/phase1b_extended_rerun_registration_2026-11-11.md` (BINDING,
commit `0f93d4eb`; implementation freeze `86ab4cdd`). Dispatch record (incl.
the attempt-2 amendment): `docs/phase1b_extended_rerun_dispatch_record_2026-11-11.md`.
Two seed-half runs of `run_mode=phase1b_v2_extended` on head `77e7791f`:
`run_43099281565/` (seeds 1–10) and `run_43099286057/` (seeds 11–20).
Comparator arms are the UNCHANGED 2026-07 archives `phase1b_corrected/`
(frozen KG 30199257204/30199260042, baseline 30199243656/30199247467); their
raw per-cell files are gitignored and live in the locally archived copy
`.worktrees/phase1b-finish/phase1b_corrected` (SHA-256 inventories verified).
Registered outputs: `analysis/registered/phase1b_extended_v3_registered_family.csv`
and `phase1b_extended_v3_primitives.csv`.

Reproduction: `python analysis/reproduce_phase1b_extended_v3.py phase1b_extended_v3
--comparator <phase1b_corrected with raw files>` validates both extended halves
with the effective-props and initial-Q-divergence gates, the comparator halves
with their gates and inventories, stages the three modes, and rebuilds both
tables byte-equivalently (canonical numeric form).

## Why this campaign exists

Round-1 audit AUD-001: the 2026-07 "extended" runs executed effective frozen KG
because the three extended knobs never reached the JVM. Here the knobs are
forwarded, every TRAINING_OK records the effective values (2.0 / 5.0 / 2.0 in
all 280 manifests), and the stereo-true initial Q-tables of every profile
differ from the frozen archive (seed 1: labrel16 259/324 cells, labband
400/2570, labrel8s 17,152/40,980, labrel8 131/180, labrel4 67/108, lab4chain3
144/1,548, labrel0 3/36).

## Registered outcome (N = 20 paired seeds, exact sign-flip, BH m = 2 over {M2, M4}; M5 exploratory)

| Member | Statistic (extended − comparator, arm of record) | Mean | Median | 95% bootstrap CI | Exact p | BH q (m=2) | Rank-biserial | SESOI | Verdict |
|---|---|---:|---:|---|---:|---:|---:|---:|---|
| M2 `labrel_incremental_slope` | OLS slope over K∈{0,4,8,16} of `auc_goal` extended − frozen | 0.0 | 0.0 | [0.0, 0.0] | 1.0 | 1.0 | 0.0 | +0.000694/decoy | **null at ceiling** |
| M4 `labband_extended_vs_frozen_auc` | `auc_goal` extended − frozen | −0.00025 | 0.0 | [−0.000517, −0.0000167] | 0.0903 | 0.1807 | −0.571 | +0.0111 | null |
| M5 `labband_extended_vs_baseline_dev` (exploratory) | mean `CumIlluminanceDeviation` extended − baseline | −0.26625 | −0.200 | [−0.484, −0.0588] | 0.0238 (uncorrected) | — | −0.579 | −0.0616 | exploratory, predicted direction, 4.3× SESOI |

Reading (registration §7):

- **M2 is a genuine exact null, but at a ceiling.** With the treatment
  delivered, training `auc_goal` is 1.000 for every labrel rung, both arms,
  all 20 seeds (one distinct value per cell), so the slope is identically zero
  although the extended arm started from a different initial policy. The
  relevance ladder cannot register an irrelevance-prior effect because every
  training episode already reaches the goal; this is "not detectable at this
  ceiling", not evidence of no effect.
- **M4 is null** and numerically slightly negative (labband `auc_goal` 0.99965
  extended vs 0.99990 frozen; 7/20 seeds identical), ~44× below its SESOI in
  magnitude and in the wrong direction.
- **M5 (exploratory, no q):** the band-mirror channel reduces the labband
  illuminance deviation from 0.8131 (baseline) to 0.5469 (extended), −0.266
  per seed with 13/20 seeds negative and an uncorrected exact p = 0.024; the
  effect is 4.3× its SESOI and in the predicted direction. Descriptive context
  (never confirmatory): frozen KG 0.6506 (2026-07 archive), redundancy-only
  0.5869, so extended − frozen ≈ −0.104 and the extended arm is the lowest of
  the four. Under the registration this remains exploratory: N = 20, no power
  statement, one uncorrected test, and a cross-head comparator.

## Delivery and provenance

- 280/280 TRAINING_OK: `stereo_requested_props` = `stereo_effective_props` =
  {irrelevantDvPrior 2.0, bandMirrorInit 5.0, bandMirrorPrior 2.0}.
- Initial-Q divergence gate (labrel16, labband vs frozen, 20/20 seeds) passed.
- Artifacts: E1 `phase1-consolidated` id 13927831370
  (`sha256:a67a5b99…c5faa`), E2 id 13930787358 (`sha256:5c658b83…2ff38`);
  results-branch commits `78f2cf06` / `0975fcf6` and tags
  `results-20261112-083254-phase1b_v2_extended-77e7791f` /
  `results-20261112-092836-phase1b_v2_extended-77e7791f` verified on the remote.
- Inventories: 5,480 files per half (`SHA256SUMS.csv`); stereo-true initial
  Q-tables (140 files, 5.9 MB) are committed as treatment-delivery evidence
  despite the generic ignore pattern; other raw CSV/Q-table files are local
  and hash-inventoried, as in 2026-07.
- Cross-head comparison disclosed: the comparator arms were not re-run; the
  only learner-affecting source change between heads is the forwarding of
  three knobs those arms never request.

## What changes in the record

The 2026-07 nominal-extended archives remain classified as invalid for their
intended role. The intended extended-channel effect is no longer "unknown":
M2 is an exact null at a saturated endpoint, M4 is null, and M5 is an
exploratory, suggestive reduction of illuminance deviation. The
`phase1b_decision_memo_2026-07-27.md` deferrals that cited "the double null on
M2/M4" rested on an unmeasured contrast; after delivery, M2's null is a
ceiling artefact of the relevance ladder rather than a measured absence.
