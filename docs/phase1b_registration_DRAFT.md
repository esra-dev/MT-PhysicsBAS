# Phase-1b confirmatory registration — DRAFT (not yet binding)

**Status: DRAFT.** This document becomes binding only when it is renamed to
`phase1b_registration_<date>.md` with the pilot-power-derived sample size
filled in, a dated pointer is added to `docs/pre_registration.md`, and the
commit lands BEFORE any confirmatory seed is dispatched
(docs/PHASE1B_POWER_PROTOCOL.md §5). Every `⟨PENDING⟩` placeholder must be
resolved at freeze; none may be resolved from pilot effect directions.

## 1. Why this campaign

The corrected protocol-v2 results showed the original clean labs under-test
the thesis hypothesis (lab1 saturated null; lab2's benefit ~70% reproduced by
the ontology-free redundancy arm; lab3 knowledge tax; flat Phase-4 depth
trend; selective Phase-2 recovery). Phase 1b isolates WHICH qualitative fact
improves learning: relevance (labrel ladder), state-dependent conditionality
and qualitative direction (labband), and dependency order (lab4chain3).

## 2. Frozen implementation

- Branch `phase1b-labs-2026-07`; implementation freeze commit `a8d3cb40`
  (lineage bbb3c814 → 4db7f842 → b9bf5551 → a8d3cb40); confirmatory
  dispatches must use head `⟨PENDING: registration commit sha⟩` or a
  descendant containing it whose only additions are registration documents.
- Reachability certificates: 34/34 PASS, index sha256
  `8444d7d798d675c662ff044be171f5b1c473f9e8c12cb5d198391529e81195db`
  (`config/reachability_certificates/`). A failed or ambiguous certificate
  blocks the campaign.
- Knowledge-provenance contract: `docs/KNOWLEDGE_PROVENANCE.md` +
  `config/knowledge_provenance.csv` (layer wording is binding for every
  claim; `ws:ivMinRank` is never goal-sufficiency).

## 3. Arms (run modes; definitions frozen in config/run_config.json)

1. `phase1b_v2_baseline` — flags copied from `phase1_v2_baseline`.
2. `phase1b_v2_redundancy_only` — flags copied from `phase1_v2_redundancy_only`.
3. `phase1b_v2_kg_frozen` — stereotype Q-init and prior consumer
   byte-identical to `phase1_v2_kg_only`; the Phase-1b knobs stay 0.0.
4. `phase1b_v2_extended` — kg_frozen plus ONLY
   `stereo_irrelevant_dv_prior=2.0`, `stereo_band_mirror_init=5.0`,
   `stereo_band_mirror_prior=2.0` (frozen pre-pilot at Stage-1 freeze).

The stereo-true arm of each mode is the arm of record; stereo-false is the
paired within-mode control (`common-seed-v1` pairing). A result from the
extended arm is never attributed to the frozen Phase-1 agent.

## 4. Frozen estimands and family (m = ⟨PENDING: retained members ≤ 6⟩)

Members M1–M6 exactly as implemented in `analysis/phase1b_report.py::FAMILY`
(per-seed statistics, exact paired sign-flip tests via the frozen
`analysis/exact_paired_stats.py`, BH over the retained members, no p/q ever 0):

1. M1 labrel stateless K-slope, frozen−baseline `auc_goal` — predicted positive.
2. M2 labrel incremental K-slope, extended−frozen `auc_goal` — predicted positive.
3. M3 labrel8s vs labrel8 fragmentation DiD — predicted positive.
4. M4 labband extended−frozen `auc_goal` — predicted positive.
5. M5 labband extended−baseline `CumIlluminanceDeviation` — predicted negative.
6. M6 lab4chain3 frozen−baseline RMST at horizon H = 3000/8 = 375
   presentations — predicted negative; switches to benchmark goal rate
   (predicted positive) under the frozen >25% pooled-censoring rule.

SESOIs per docs/PHASE1B_POWER_PROTOCOL.md §2. Supporting outcomes
(redundancy-only analogues, per-rung descriptives, first-success curves,
deterministic `PolicyEnergyCost`, overshoot proxy, cycling) are registered
supporting outcomes and never enlarge the BH family. Member order is not
evidential.

Power analysis outcome: `⟨PENDING: per-member power table, retained member
list, any prospectively-exploratory relabelling⟩` produced by
`analysis/phase1b_power.py` from the allow-listed pilot diagnostics only.

## 5. Campaign

- Confirmatory N = `⟨PENDING: smallest N ∈ {20,30,40} with ≥0.80 power for
  every retained member⟩`; seeds exactly `1..N`, both stereo arms, every
  (mode × profile) cell; no optional extension.
- Pilot block 1001–1010 is permanently disjoint; the workflow seed gate
  (`phase1b_stage=confirmatory`) rejects pilot seeds and out-of-range seeds.
- Dispatch list (each exactly once, `.github/workflows/phase1.yml`, ref
  `phase1b-labs-2026-07`):
  `profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
  `seeds=1..N`, `phase1b_stage=confirmatory`, `publish_results=true`,
  `run_mode` ∈ the four arms of §3. Duplicate mode/seed/profile tuples are
  invalid; pre-data dispatch failures are amended in place in the dispatch
  record with byte-identical inputs.

## 6. Archives and completion gates

- Archive under `phase1b_corrected/run_<actions_run_id>/` (one per arm) with
  `workflow_inputs.json`, `SHA256SUMS.csv`, and raw artifacts; campaign
  tables under `phase1b_corrected/analysis/registered/`.
- Gates: `analysis/validate_phase1b_archive.py` (TRAINING_OK stamps, paired
  schedule identity, labrel cross-rung schedule identity, seed-block
  disjointness), byte-reproduction via `analysis/reproduce_phase1b.py`,
  results-branch copies verified ON THE REMOTE, and a new additive
  `check_provenance.py` phase1b block (existing pins untouched).

## 7. Reading rules

Confirmatory results are read only from the archived registered tables. The
frozen-vs-baseline contrast speaks to what the existing consumer already
uses; extended-vs-frozen speaks to the new channels. No monotonic-depth or
solve-versus-fail claim for lab4chain3. A low-powered or null member is
reported as such, never as evidence of no effect.
