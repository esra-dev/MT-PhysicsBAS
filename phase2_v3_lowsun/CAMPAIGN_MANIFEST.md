# Phase-2 low-sun re-execution campaign (v3, 2026-11)

Registration: `docs/phase2_lowsun_rerun_registration_2026-11-11.md` (BINDING,
commit `0f93d4eb`; amendment A1 of 2026-11-12 is post-data and disclosed).
Dispatch record: `docs/phase2_lowsun_rerun_dispatch_record_2026-11-11.md`. One
registered dispatch, `run_43099277363/` (both cells, seeds 1–20), green on head
`77e7791f`. Registered outputs: `analysis/registered/
phase2_lowsun_v3_recovery_family.csv`, `phase2_lowsun_v3_detection_family.csv`,
`phase2_lowsun_v3_per_seed.csv`.

Reproduction: `python analysis/reproduce_phase2_lowsun_v3.py phase2_v3_lowsun`
validates the archive with the treatment-delivery gate enabled and rebuilds the
three tables byte-equivalently (canonical numeric form) from the committed
archive alone.

## Why this campaign exists

Round-2 audit findings R2-001/R2-002: in the 2026-07 corrected campaign the two
registered low-sun Tier-1 cells never ran at low sun (the pin lived only in the
simulator reset sampler, which protocol-v2 explicit scenario starts bypass).
Here the pin is delivered at scenario level (every scenario `Sunshine = 100`),
evidenced per cell in the ADAPT_OK manifests, and gated by the validator.

## Registered outcome (n = 20, exact sign-flip, BH m = 2 per family)

**Low-sun RecoveryEpisodes family: 0 supported, 2 adverse, 0 null.**

| Cell | Mean KG | Mean TR | Mean Δ (KG − TR) | 95% CI | Exact p | BH q (m=2) | Rank-biserial | Censors KG/TR | Verdict |
|---|---:|---:|---:|---|---:|---:|---:|---|---|
| lab3_f2dead_lowsun | 4001.0 | 1848.0 | +2153.0 | [1367.3, 2939.2] | 9.77×10⁻⁴ | 1.95×10⁻³ | 1.000 | 20/9 | **Adverse** (KG never detects) |
| labmon2_f2dead_lowsun | 1277.4 | 189.6 | +1087.8 | [314.1, 1877.6] | 0.0312 | 0.0312 | 0.029 | 6/0 | **Adverse** (KG fails to detect in 6/20) |

**Low-sun DetectEpisode family (m = 2): both adverse** — lab3 Δ = +2200.55
(q = 1.95×10⁻³; KG 0/20 detections vs TR 11/20), labmon2 Δ = +1199.95
(q = 0.0312; KG 14/20 vs TR 20/20; TR detects at episode 0.35 on average, KG at
0.0 when it detects at all).

Reading (registration §8): H-P2 (KG re-converges faster) is **not supported**
in either delivered low-sun cell; both are adverse under the frozen decision
rule. The adverse deltas are detection-censoring effects, not slower
relearning: every KG censor is a never-detected fault (recovery and detection
censors coincide), and in labmon2 the 14 KG records that did detect did so at
episode 0 and the paired rank-biserial is ≈0.03, i.e. the two arms are
indistinguishable once the fault is seen. The knowledge-shaped policy keeps
co-feeders (lab3: spotlight/blinds; labmon2: monitors) active, so the
structural-maskability abstain of detector v2 never releases an unmasked
no-response verdict in lab3 and only sometimes in labmon2.

Relation to the 2026-07 record (descriptive, never confirmatory): under the
delivered mixed-sun schedule the same two cell names were adverse
(lab3, +3654.15, identical to `lab3_f2dead`) and supported (labmon2, −168.75).
Pinned low sun therefore turns the labmon2 result from supported into adverse
and leaves lab3 adverse. The 2026-07 rows keep their classification in the
dossier; the two conditions are never merged into one count.

## Descriptives (registered, no q)

- Detection: lab3 KG 0/20, TR 11/20; labmon2 KG 14/20, TR 20/20.
- Recovered goal rate (mean over seeds): lab3 KG 0.000 / TR 0.550; labmon2
  KG 0.700 / TR 0.980 (best-effort rank 2 is the only reachable target).
- Degraded mode entered in 45/45 detected records (best-effort rank 2,
  shortfall 1); never in the 35 never-detected records (instrument property,
  amendment A1).
- Blacklist events: 88 in 80 records (lab3 TR 21, KG 0; labmon2 TR 39, KG 28),
  all naming the two genuinely dead lamps (`SetZ1Light` 44, `SetZ2Light` 44);
  **zero false-positive events**.
- Parent provenance: the 80 re-trained clean parents are byte-identical to the
  2026-07 archived parents (400/400 Q-table files; lab3 `parent_qtable_sha256`
  identical 40/40; the labmon2 manifest hash differs only because the 2026-07
  glob also swept the `labmon2_infoonly` tables).
- Treatment delivery: 80/80 manifests `lowsun_pin_delivered=true`,
  `scenario_sunshine_values=[100]`, pinned-file hashes `119dc755…` (lab3) /
  `8e9f5467…` (labmon2); preflight and strict validator pass.

## Not covered

The KG-silent variants `labmon2_infoonly_f2dead_lowsun` /
`labmon2_nostereo_f2dead_lowsun` were not re-executed (descriptive-only in the
record; their 2026-07 datasets remain mixed-sun and byte-identical to each
other).
