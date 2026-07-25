# Phase-1b PILOT dispatch record (2026-07-25)

Status: **PILOT_ONLY** — every artifact produced by these runs belongs to the
pilot block and may never be pooled with confirmatory results
(docs/PHASE1B_POWER_PROTOCOL.md §1).

## Frozen state at dispatch

- Branch: `phase1b-labs-2026-07`, head `a8d3cb40`
  ("phase1b: Stage 1 freeze — preflight green, pilot gate, schedule-identity pins").
- Freeze lineage: `bbb3c814` (Stage 0 channels) → `4db7f842` (LF pin)
  → `b9bf5551` (Stage 1 labs) → `a8d3cb40` (freeze).
- Reachability certificate index sha256 (34/34 PASS):
  `8444d7d798d675c662ff044be171f5b1c473f9e8c12cb5d198391529e81195db`.
- Verification at freeze: `gradlew test` green; `gradlew preflight`
  (7/7 phase1b profiles, static + validateTurtle + verifyActionRegistry,
  24 ontology sets CONTRACT HOLDS) green; analysis pytest 75/75;
  `validate_phase1_scenarios.py` green for all 11 lab units;
  `reproduce_phase{1,2,3,4}_v2.py` byte-equivalent on the canonical archive
  host; deterministic flow smoke 7/7 (health + transition arithmetic).

## Dispatches (workflow `.github/workflows/phase1.yml`, ref `phase1b-labs-2026-07`)

Inputs common to all four: `profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
`seeds=1001,1002,1003,1004,1005,1006,1007,1008,1009,1010` (the frozen
pilot-only block), `phase1b_stage=pilot` (seed-gate enforced in the workflow),
`publish_results=true`.

| Arm (run_mode) | Actions run ID |
|---|---|
| `phase1b_v2_baseline` | 30171111962 |
| `phase1b_v2_redundancy_only` | 30171112970 |
| `phase1b_v2_kg_frozen` | 30171113750 |
| `phase1b_v2_extended` | 30171114580 |

Dispatched 2026-07-25 ≈19:11Z, all four accepted and in progress.

## Amendment 2026-07-25a — post-dispatch non-behavioral commits (disclosed)

After the four dispatches (which run from head `a8d3cb40`), three commits
landed on the branch: `451e0ab5` (this dispatch record), `938730c3`
(explicitly non-binding registration DRAFT + pilot download tooling), and
`b819fb04` (Phase1bStateSpaceTest — regression tests that assert the ALREADY
FROZEN behavior — plus a documentation-only correction of the labband state
count from a mistaken 1024 to the true 256 = 4·2⁴·4; the lab's TTL, config
dimension 6, certificates, and physics were always 256 and are unchanged).
None of these commits touches implementation, physics, scenarios, metrics,
learner hyperparameters, or any test of behavior that the pilot exercises;
the frozen lineage through `a8d3cb40` is intact, golden registries and the
certificate index hash are unchanged. Recorded here so the freeze boundary
stays auditable; the pilot's power inputs are considered valid under the
protocol's change rule because no frozen artifact changed.

Commit-content note: commits `b819fb04` and `6d952070` additionally swept in
the concurrently-authored Phase-1b ARCHIVE tooling
(`analysis/validate_phase1b_archive.py`, `analysis/reproduce_phase1b.py`,
`analysis/tests/test_validate_phase1b_archive.py`) whose commit messages do
not mention them — a broad `git add -A` while two work streams shared the
worktree. The files are exactly their authors' final versions (analysis
pytest suite 92/92 green including their 17 tests) and are likewise
non-behavioral for the pilot: they validate/reproduce ARCHIVES and are
exercised by no training or benchmark path.

## Reading rules

Pilot artifacts are read ONLY through
`analysis/phase1b_report.py --pilot-diagnostics` (allow-listed report:
protocol health, runtime/artifact size, censoring fractions, metric
degeneracy, centred-residual variances). No arm-labelled means, effect
directions, p-values, or comparative curves may be produced before the
confirmatory registration commit. Amendments for any pre-data dispatch
failure are appended here in place, per the established dispatch-record
convention.
