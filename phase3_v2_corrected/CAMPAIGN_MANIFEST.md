# Phase-3 protocol-v2 corrected campaign

Registration: `docs/phase3_correction_registration_2026-07-22.md`. One
registered dispatch; archive `run_29926328852/` (see its ARCHIVE_MANIFEST.md).

Reproduction: `python analysis/reproduce_phase3_v2.py phase3_v2_corrected`
validates every gate manifest and rebuilds `phase3_delay_accuracy.csv`,
`phase3_compliance_ci.csv`, and `phase3_compliance_paired.csv`
byte-equivalently (canonical numeric form) from the committed archive alone.

Registered outcome summary (details in the corrected result tables; the
corrected run governs):
- Delay-learning accuracy reproduces the withdrawn headline: slowest-actuator
  learned delay 12.125–12.1875 ticks vs ground truth 12 (rel. error
  1.04–1.56%) in all four profile×arm cells; lamps/spotlight classified
  instantaneous everywhere.
- Deadline compliance reproduces with one disclosed deviation: KG arm 59/60
  goal-attempts met on lab2_slow (one tight-goal miss in one replica;
  overall_compliance 0.9833) and 60/60 on lab3_slow, vs the zero-delay
  baseline's 30/60 in both profiles (all tight goals missed). The withdrawn
  record showed 6/6 vs 3/6 in every replica.
- Tick-integrated energy (descriptive, meter `tick-v1`, no hypothesis tests
  permitted): the KG arm buys the tight deadlines with 3.1–3.7 tick-energy
  units per replica vs 0 for the baseline.
