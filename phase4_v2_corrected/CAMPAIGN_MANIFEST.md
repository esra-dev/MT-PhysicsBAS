# Phase-4 protocol-v2 corrected campaign

Registration: `docs/phase4_correction_registration_2026-07-22.md`. Two
registered dispatches (seed halves), both green on head `90e53f8b`:
`run_29926341581/` (seeds 1–10) and `run_29926354783/` (seeds 11–20); see the
per-run ARCHIVE_MANIFEST.md files. Registered outputs:
`analysis/registered/phase4_v2_registered_family.csv` and
`phase4_v2_ladder_trend.csv`.

Reproduction: `python analysis/reproduce_phase4_v2.py phase4_v2_corrected`
validates every gate manifest in both archives and rebuilds both registered
tables byte-equivalently (canonical numeric form) from the committed archives
alone.

Registered outcome summary (the corrected run governs):
- **All four frozen family members are supported in the favourable
  direction** (n=20, exact sign-flip, BH m=4): lab4 `avg_redundant`
  −0.69500 (q=5.09×10⁻⁶, rank-biserial −0.990), lab4dual −0.74500
  (q=5.09×10⁻⁶, −0.990), lab4chain −0.73438 (q=5.09×10⁻⁶, −1.000), lab5
  `energy_compliance` +0.04313 (q=0.0094, +0.683).
- **The withdrawn ladder-growth headline does NOT reproduce.** The registered
  ordered secondary d(lab4chain) − d(lab4) is null (−0.03938,
  CI [−0.35813, +0.28812], p=0.823); both descriptive depth contrasts are
  also null. The corrected advantage is approximately constant (~−0.7) at
  every dependency depth — the withdrawn monotone pattern
  (−0.33/−0.93/−1.46) was an artifact of the defective protocol.
- The corrected lab5 energy-compliance benefit (+0.043) is smaller than the
  withdrawn +0.096 but remains supported.
