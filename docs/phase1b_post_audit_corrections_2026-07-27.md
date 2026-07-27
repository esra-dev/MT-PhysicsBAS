# Phase-1b post-audit corrections (2026-07-27)

Status: non-outcome-changing correction record. The eight run-of-record
archives and their SHA-256 inventories are unchanged.

## Corrected interpretations

1. M1 has 9 positive per-seed slopes and 11 exact ties, not 20 positive
   slopes. Every non-zero slope favors frozen KG. The exact sign tests and
   rank-biserial calculation discard or remain insensitive to zero pairs, so
   the registered statistic, p-value, q-value, and verdict are unchanged.
2. M5 is extended-minus-baseline and cannot isolate the newly added direction
   consumer. Frozen and extended have identical mean labband deviation
   (0.650625); the observed incremental direction contrast on this outcome is
   zero. M5 remains exploratory and underpowered.
3. M6 uses six training first-success scenarios. Its implementation horizon is
   H=3000/6=500, not 3000/8=375, and the −5% SESOI is therefore −25
   presentations. Zero censoring makes the observed −0.5 RMST contrast and
   its tests invariant to H. The pre-data power run already returned 1.000
   using the smaller −18.75 threshold, so member selection and N are
   unchanged. The effect is 50 times smaller than the corrected SESOI.

## Measurement and metadata corrections

- The registered supporting outcome was the count of within-episode labband
  overshoot events. Benchmark artifacts do not contain the necessary
  within-episode rank trajectory. The outcome is therefore **registered but
  unmeasured**; the historical final-rank-proxy `NA` rows are not a substitute.
- M1–M4's registered positive directions were accidentally blank in the
  archived family CSV. Current `analysis/phase1b_report.py` output populates
  them. The immutable archived bytes remain unchanged.
- `analysis/reproduce_phase1b.py` invokes the report's explicit
  `--legacy-archive-format` switch to reproduce the historical blank fields
  and proxy placeholders for byte comparison only. Normal report output uses
  the corrected metadata and the explicit unmeasured-outcome row. No numeric
  member or supporting statistic differs.

## Implementation scope

The Phase-1b reasoner represents qualitative direction and IV gates once per
WoT action. It does not maintain a per-zone/per-DV direction-and-gate map.
This is sufficient for the seven registered labs, whose tested actions have
one relevant illuminance response with consistent mechanisms. Mixed multi-DV
actions with different directions or gates are outside the implemented and
tested claim. Adding them requires a new representation and a separately
frozen campaign.

## Workflow and reproducibility hardening

- `analysis/validate_phase1b_dispatch.py` rejects duplicate tokens, wrong
  profiles, unknown Phase-1b modes, and any seed block other than pilot
  1001..1010 or confirmatory amendment-A1 halves 1..10 / 11..20. It also
  checks uniqueness of the materialized training and benchmark tuples.
- Non-archive source/configuration files changed by the Phase-1b branch are
  normalized to LF through `.gitattributes`. Byte-frozen pilot/confirmatory
  evidence is excluded.
- `scripts/Run-Phase1bFlowSmoke.ps1` and
  `analysis/phase1b_flow_smoke.py` reproducibly launch and exercise all seven
  Node-RED flows through `/health`, `/reset`, `/setState`, `/action`, and
  `/status`, including deterministic relevance, band, and chain physics
  checkpoints.
- The retained local run record is
  `docs/audit/phase1b_live_flow_smoke_2026-07-27.json`; CI repeats the same
  smoke and uploads its JSON evidence.
