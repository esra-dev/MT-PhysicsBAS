# Phase-1b confirmatory registration (2026-07-26)

> **Post-results arithmetic/measurement notice (2026-07-27):** The frozen
> implementation derives M6's horizon from six training first-success
> scenarios, so H=3000/6=500 and the −5% SESOI is −25 presentations. The
> original text used the eight benchmark scenarios (H=375, SESOI=−18.75).
> Zero censoring makes the observed RMST statistic and tests invariant to this
> correction, and power/member selection remain unchanged. The same audit
> established that the registered within-episode labband overshoot-event
> outcome was not captured by the run artifacts. Full correction ledger:
> `docs/phase1b_post_audit_corrections_2026-07-27.md`.

**Status: BINDING pre-data registration for the Phase-1b confirmatory
campaign.** Committed on branch `phase1b-labs-2026-07` after the Stage-1
implementation freeze (`a8d3cb40`), after the pilot (runs
30171111962/30171112970/30171113750/30171114580, seeds 1001–1010,
PILOT_ONLY) and its frozen power analysis, and BEFORE any confirmatory seed
is dispatched. Every value below was fixed by the pre-committed procedure in
`docs/PHASE1B_POWER_PROTOCOL.md`; no pilot effect direction or arm-labelled
mean was inspected (the pilot was read exclusively through
`phase1b_report.py --pilot-diagnostics`; the diagnostic report, power inputs
and power report are committed under `phase1b_pilot/`).

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
  dispatches must use THE COMMIT THAT ADDS THIS REGISTRATION (its sha is
  recorded in the confirmatory dispatch record) or a descendant whose
  changes relative to it are documentation/archive-tooling only — no change
  to implementation, physics, scenarios, metrics, or learner
  hyperparameters.
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

## 4. Frozen estimands and family (m = 5)

Members M1–M6 exactly as implemented in `analysis/phase1b_report.py::FAMILY`
(per-seed statistics, exact paired sign-flip tests via the frozen
`analysis/exact_paired_stats.py`, BH over the retained members, no p/q ever 0):

1. M1 labrel stateless K-slope, frozen−baseline `auc_goal` — predicted positive.
2. M2 labrel incremental K-slope, extended−frozen `auc_goal` — predicted positive.
3. M3 labrel8s vs labrel8 fragmentation DiD — predicted positive.
4. M4 labband extended−frozen `auc_goal` — predicted positive.
5. M5 labband extended−baseline `CumIlluminanceDeviation` — predicted negative.
6. M6 lab4chain3 frozen−baseline RMST at corrected horizon H = 3000/6 = 500
   presentations — predicted negative; switches to benchmark goal rate
   (predicted positive) under the frozen >25% pooled-censoring rule.

**Retained confirmatory members: M1, M2, M3, M4, M6 — BH family m = 5.**
**M5 is prospectively relabelled EXPLORATORY** under the protocol's frozen
selection rule: with its pilot centred-residual SD 0.3019 and pooled-scale
SESOI −0.0616 (10% of the arm-blind pooled labband deviation mean 0.615938,
n = 6400 pooled cells), simulated power is 0.133/0.194/0.239 at
N = 20/30/40 — below 0.80 at every candidate N. M5 remains a registered
outcome, is computed and reported from the same archives with the same
frozen statistics, and its (low-powered) result may never be presented as
evidence of no effect. The relabelling is power-derived only; no pilot
effect direction was seen.

SESOIs per docs/PHASE1B_POWER_PROTOCOL.md §2. Supporting outcomes
(redundancy-only analogues, per-rung descriptives, first-success curves,
deterministic `PolicyEnergyCost`, within-episode overshoot events, cycling) are registered
supporting outcomes and never enlarge the BH family. Member order is not
evidential.

Power analysis outcome (`analysis/phase1b_power.py`, 10,000 replicates, RNG
seed 0x1B5EED, CLT sign-flip approximation as frozen in the protocol;
committed at `phase1b_pilot/power_report.txt` with inputs
`phase1b_pilot/power_inputs.csv`):

| Member | SD (centred residuals) | SESOI | Power N=20 | N=30 | N=40 |
|---|---|---|---|---|---|
| M1 | 1.0351e-5 /decoy | +6.94e-4 /decoy | 1.000 | 1.000 | 1.000 |
| M2 | 0 (degenerate, flagged) | +6.94e-4 /decoy | 1.000 | 1.000 | 1.000 |
| M3 | 9.223e-4 | +0.0111 | 1.000 | 1.000 | 1.000 |
| M4 | 0 (degenerate, flagged) | +0.0111 | 1.000 | 1.000 | 1.000 |
| M5 | 0.3019 | −0.0616 | 0.133 | 0.194 | 0.239 |
| M6 | 0.4067 (RMST; zero censoring) | −25 (corrected H=500) | 1.000† | 1.000† | 1.000† |

† The pre-data power run used the mistaken −18.75 SESOI and already returned
1.000 at every candidate N. Correcting its magnitude to −25 can only increase
power and does not change the registered selection decision.

Pilot protocol-health facts disclosed with this registration: censoring is 0
in every (scenario × seed × arm) cell of every profile, so M6's endpoint is
RMST; members M2 and M4 carry the `zero_variance_paired_differences`
degeneracy flag (their per-seed differences were identical across all 10
pilot seeds — by construction the blinded diagnostic cannot and did not
reveal whether that constant is zero or non-zero); the stateless rungs
labrel0/4/8 show zero cross-seed `auc_goal` variance in every mode and arm,
as do several kg-arm cells of labrel16/labrel8s/lab4chain3. Under the frozen
procedure these facts permit no change to labs, hypotheses, directions,
coefficients, or hyperparameters. If confirmatory data reproduce a
degenerate (all-identical) difference for a member, the exact sign-flip test
remains well-defined and is reported as-is.

## 5. Campaign

- Confirmatory **N = 20** (the smallest candidate with ≥0.80 simulated power
  for every RETAINED member — all five are at 1.000); seeds exactly
  `1,2,...,20`, both stereo arms, every (mode × profile) cell; no optional
  extension.
- Pilot block 1001–1010 is permanently disjoint; the workflow seed gate
  (`phase1b_stage=confirmatory`) rejects pilot seeds and out-of-range seeds.
- Dispatch list (each exactly once, `.github/workflows/phase1.yml`, ref
  `phase1b-labs-2026-07`):
  `profiles=labrel0,labrel4,labrel8,labrel16,labrel8s,labband,lab4chain3`,
  `seeds=1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20`,
  `phase1b_stage=confirmatory`, `publish_results=true`,
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
