# Phase-1b confirmatory results (2026-07-27)

Campaign: registration `docs/phase1b_registration_2026-07-26.md` (BINDING,
pre-data, N=20, BH family m=5, M5 prospectively exploratory by the frozen
power rule). Archives: `phase1b_corrected/` (eight seed-half runs of record;
see `CAMPAIGN_MANIFEST.md`). Every number below rebuilds byte-equivalently
via `analysis/reproduce_phase1b.py`; post-audit metadata corrections are
documented in `docs/phase1b_post_audit_corrections_2026-07-27.md`.

## Registered family (n = 20 paired seeds; exact paired sign-flip tests; BH m=5)

| Member | Statistic | Mean | 95% CI | p (sign-flip) | q (BH m=5) | Verdict vs SESOI |
|---|---|---|---|---|---|---|
| M1 relevance K-slope (frozen−baseline `auc_goal`/decoy) | +9.88e-6 | [+5.36e-6, +1.46e-5] | 0.0039 | 0.0065 | **significant, ~70× BELOW the SESOI** (6.94e-4/decoy) |
| M2 incremental K-slope (extended−frozen) | 0 (identically, all 20 seeds) | [0, 0] | 1 | 1 | **null — the new irrelevance channel changed nothing** |
| M3 fragmentation DiD (labrel8s−labrel8) | +0.0013 | [+0.0010, +0.0016] | 1.9e-6 | 9.5e-6 | **significant, ~8× below the SESOI** (0.0111) |
| M4 labband extended−frozen `auc_goal` | 0 (identically) | [0, 0] | 1 | 1 | **null — the band-mirror channel changed nothing on `auc_goal`** |
| M5 labband extended−baseline deviation (EXPLORATORY) | −0.1625 | [−0.334, −0.001] | 0.078 | — | full-stack contrast moved in the predicted direction, not significant (power 0.13–0.24); does not isolate direction |
| M6 chain3 frozen−baseline RMST | −0.5 presentations | [−0.64, −0.36] | 7.6e-6 | 1.9e-5 | **significant, 50× below the corrected SESOI** (−25 presentations; −5% of H=500) |

Censoring was zero in every (scenario × seed × arm) cell, so M6's endpoint is
RMST. Rank-biserial was ±1 for M1/M3/M6 because every **non-zero** paired
difference had the predicted sign. M1 specifically had 9 positive seeds and
11 exact ties; it is incorrect to describe all 20 seeds as positive.

## Reading (per the registration's own SESOI framing)

1. **The frozen KG's advantages are real but far below the registered
   smallest effect sizes of interest.** The relevance ladder shows a
   statistically clean positive K-slope (M1) and a clean fragmentation gain
   (M3), and the depth-3 chain shows a clean speed-up (M6) — but each is one
   to two orders of magnitude smaller than the SESOI the protocol declared
   thesis-relevant. Under the registration's reading rules these are
   "statistically detectable, scientifically below the registered
   threshold", echoing the corrected Phase-1 pattern.
2. **The extended channels (three-valued relevance prior + band mirror)
   contributed exactly nothing** on their registered confirmatory members:
   M2 and M4 are identically zero in every seed. The extended arm's
   machinery verifiably engaged (registry/priors confirmed at Stage 0) but
   never altered outcomes at these lab scales.
3. **M5 (exploratory) does not isolate the direction channel.** The full
   extended arm reduced band deviation relative to baseline without reaching
   significance, but frozen and extended had the same mean deviation
   (0.650625). The incremental extended−frozen direction-channel contrast on
   this outcome is therefore zero. Per protocol, M5 remains underpowered and
   cannot support either an effect or no-effect claim.

## Disclosures

- Registration §4 glossed M6's horizon as "H = 3000/8 = 375" using the
  BENCHMARK scenario count; the frozen implementation (which the
  registration declares governing, "exactly as implemented") uses the
  training first-success schedule count, H = 3000/6 = 500. With zero
  censoring the horizon is inert — the RMST estimate and tests are identical
  under either H. The corrected −5% SESOI is −25 presentations, making the
  observed −0.5 effect 50× smaller. The original −18.75 pilot power input
  still gave power 1.000, so this arithmetic correction does not change
  member selection or N.
- `analysis/phase1b_report.py` was mechanically aligned post-registration to
  emit the REGISTERED BH family (m=5, M5 exploratory) — its pre-registration
  version computed BH over all six members. The change implements the
  registration text verbatim and touches no member statistic.
- Dispatch history: round-1 failed pre-data (280-cell matrix > platform
  256-job limit; amendment A1 → eight seed-half runs). Two half-runs needed
  failed-job re-runs for infrastructure reasons only (publish push race; an
  `npm ECONNRESET` env-setup flake, then a platform cross-attempt
  artifact-download error; amendment A2). No data-bearing cell was ever
  replaced; kg_frozen 1–10's results-branch snapshot was appended manually
  (`ede943b2`).

## Supporting outcomes

`phase1b_corrected/analysis/registered/phase1b_supporting.csv` carries the
redundancy-only analogues, per-rung descriptives, first-success curves,
deterministic `PolicyEnergyCost`, a historical unusable overshoot-proxy
placeholder, and cycling. The registered **within-episode overshoot event
count was not measured**: the run-of-record benchmark output has no
within-episode rank trajectory, so no valid event count can be reconstructed.
Current `analysis/phase1b_report.py` output marks it `REGISTERED BUT
UNMEASURED` rather than emitting the proxy.

Headline observations (descriptive, uncorrected): the redundancy-only
analogue of the relevance K-slope is null (−2.4e-6, p≈0.46) — the tiny M1
slope is genuinely knowledge-layer, NOT redundancy mimicry — while
redundancy reproduces roughly 60% of the fragmentation DiD (+7.8e-4 of
+1.3e-3) and roughly 45% of the chain RMST speed-up (−0.225 of −0.5),
extending the Phase-1 partial-mimicry pattern to those two members.
