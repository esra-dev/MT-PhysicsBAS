# Phase-1b extended-KG re-execution registration (2026-11-11)

**Status: BINDING pre-data registration for the Phase-1b extended-arm
re-execution (campaign `phase1b_extended_v3`).** Committed on branch
`round3-rerun-2026-11` after the implementation freeze commit `86ab4cdd`
and before any seed is dispatched. Results replace the current "intended
treatment effect unknown" classification of members M2, M4 and (exploratory)
M5 regardless of direction. The 2026-07 archives are not edited or relabelled.

## 1. Why a re-execution is required

Round-1 audit finding AUD-001 (critical) (`docs/final_state/AUDIT_RESOLUTION.md`):
`run_full_project.ps1` passed the three extended knobs as Gradle project
properties (`-Pstereo.irrelevantDvPrior=2.0 -Pstereo.bandMirrorInit=5.0
-Pstereo.bandMirrorPrior=2.0`), but the `build.gradle` JavaExec forwarding
allow-list `_httpKeys` omitted all three names, and `StereotypeReasoner`
reads JVM system properties with 0.0 defaults. The archived "extended" runs
30199263213 / 30199266427 therefore executed effective frozen KG: 1,120/1,120
primitives and 140/140 initial Q-tables are byte-identical to the frozen runs
30199257204 / 30199260042. M2 and M4 were never measured; M5 is only an
effective frozen-versus-baseline descriptive.

## 2. Previously seen results (full disclosure)

- Stored 2026-07 M2 = 0 and M4 = 0 (identity artefacts, p = q = 1), stored M5
  = −0.1625 (exact p = 0.0778; effective frozen-minus-baseline). M1 / M3 / M6
  (frozen-minus-baseline) are sighted registered results and are NOT re-tested
  here; they do not depend on the extended arm.
- The pilot (seeds 1001–1010) showed zero variance for M2/M4 for the same
  reason; its "power 1.000" for those members is meaningless and no power
  claim is made for this campaign (§4).
- No value of a correctly delivered extended arm has ever been observed.

## 3. Frozen implementation (commit `86ab4cdd`)

- `build.gradle`: `_httpKeys` now contains `stereo.irrelevantDvPrior`,
  `stereo.bandMirrorInit`, `stereo.bandMirrorPrior`. No other change to the
  learner, physics, scenarios, metrics, or hyperparameters; the requested
  extended values stay 2.0 / 5.0 / 2.0 (`config/run_config.json`,
  `phase1b_v2_extended.learning_overrides`, unchanged since freeze `a8d3cb40`).
- Treatment-delivery evidence chain: `StereotypeReasoner` logs
  `STEREO_EFFECTIVE_PROPS {json}` with the values in force;
  `run_full_project.ps1` parses it, FAILS the cell before any manifest is
  written if a requested value did not reach the JVM, and records
  `stereo_requested_props` / `stereo_effective_props` in `TRAINING_OK.json`
  (`docs/audit/gate_manifest_schema.md`).
  `analysis/validate_phase1b_archive.py --require-effective-props` re-checks
  archives against the mode's registered values and
  `--divergence-against <frozen archives>` requires the stereo-true initial
  Q-tables of `labrel16` and `labband` to differ byte-wise from the frozen
  archive for every seed. `analysis/tests/test_gradle_property_forwarding.py`
  makes any runner-emitted property missing from the allow-list a CI failure;
  `analysis/tests/test_phase1b_treatment_gates.py` covers the gates.
- **Comparator arms are the archived 2026-07 frozen (30199257204 /
  30199260042) and baseline (30199243656 / 30199247467) runs; they are NOT
  re-run.** Rationale (disclosed as a cross-head comparison): the only source
  difference between dispatch heads that can affect a learner is the
  forwarding of three knobs the frozen and baseline modes never request;
  their effective values were 0.0 then and are 0.0 now (Java defaults), which
  the archived identity of frozen and nominal-extended runs demonstrates. The
  comparator raw files are gitignored and live in the locally archived copy
  `.worktrees/phase1b-finish/phase1b_corrected` (SHA-256 inventories verified
  by the reproducer before use).
- The implementation commit also contains the Phase-2 low-sun fix
  (`docs/phase2_lowsun_rerun_registration_2026-11-11.md`); it does not touch
  the Phase-1b labs, modes, or scenario files.

## 4. Frozen estimands, family, and reading of power

Members exactly as implemented in `analysis/phase1b_report.py` (per-seed
statistics, exact paired sign-flip and sign tests via the frozen
`analysis/exact_paired_stats.py`, matched-pairs rank-biserial, fixed-seed
10,000-draw bootstrap CI with the original member offsets, no p/q of zero):

1. **M2** `labrel_incremental_slope` — within-seed OLS slope over
   K ∈ {0, 4, 8, 16} of `auc_goal[labrelK, extended] − auc_goal[labrelK, frozen]`;
   predicted positive; SESOI +0.000694 per decoy.
2. **M4** `labband_extended_vs_frozen_auc` — `auc_goal[labband, extended] −
   auc_goal[labband, frozen]`; predicted positive; SESOI +0.0111.
3. **M5** `labband_extended_vs_baseline_dev` — mean `CumIlluminanceDeviation`
   extended − baseline on labband; predicted negative; SESOI −0.0616;
   **exploratory** (no q), exactly as in the 2026-07-26 registration.

**Confirmatory BH family: {M2, M4}, m = 2.** Decision per member: supported iff
q ≤ 0.05 and the sign matches the prediction; adverse iff q ≤ 0.05 with the
opposite sign; otherwise null. Every member is additionally read against its
SESOI (point estimate and bootstrap CI); a significant effect below SESOI is
reported as "detectable but below the practical threshold", as for M1/M3/M6.

N = 20 is fixed by pairing with the archived comparator seeds 1–20. **No power
statement is made**: the only prior variance estimate for M2/M4 is the
non-delivery artefact (zero). A null result is therefore reported as "not
detected at N = 20", never as evidence of no effect.

Supporting outcomes (descriptive, outside the family): per-rung `auc_goal` of
the extended arm, the per-seed primitives table, the effective-props values
recorded in every manifest, and the initial-Q divergence per profile.

## 5. Campaign

- Workflow `.github/workflows/phase1.yml`, ref `round3-rerun-2026-11`, at or
  after the registration head; **two dispatches** (amendment-A1 seed halves,
  256-job matrix limit): `run_mode=phase1b_v2_extended`,
  `phase1b_stage=confirmatory`,
  `profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
  `publish_results=true`, `seeds=1,…,10` and `seeds=11,…,20`.
- Until both aggregates complete only operational status is inspected.
- Failure rule: a failed cell or dispatch is preserved and documented; any
  re-dispatch uses byte-identical inputs and both run IDs are recorded.

## 6. Archives and completion gates

Archive under `phase1b_extended_v3/run_<run_id>/` (one per half) with
`workflow_inputs.json`, `SHA256SUMS.csv`, the raw per-cell artifacts and the
stereo-true initial Q-tables of every profile (force-added despite the
`qtable_*.csv` ignore rule: they are the treatment-delivery evidence).
Completion requires: both aggregates green; every TRAINING_OK reports
effective 2.0 / 5.0 / 2.0; `labrel16` and `labband` initial Q-tables differ
from the frozen archive for all 20 seeds; comparator inventories verify;
`python analysis/reproduce_phase1b_extended_v3.py phase1b_extended_v3
--comparator <phase1b_corrected with raw files>` rebuilds
`phase1b_extended_v3_registered_family.csv` and
`phase1b_extended_v3_primitives.csv` byte-equivalently; results tags verified
on the remote.

## 7. Reading rules

Results are read only from the archived registered tables. M2 and M4 speak
to the irrelevance-prior and band-mirror channels on top of the frozen
consumer; M5 remains exploratory. The 2026-07 frozen-minus-baseline results
M1/M3/M6 and their q-values are unchanged and are not re-ranked by this
family. The `phase1b_decision_memo_2026-07-27.md` deferrals that cited the
"double null on M2/M4" are annotated as having rested on an unmeasured
contrast, whatever this campaign finds.
