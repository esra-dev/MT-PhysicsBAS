# Phase-2 protocol-v2 corrected campaign

Registration: `docs/phase2_correction_registration_2026-07-22.md`. Four
registered dispatches (round 3; the two documented pre-data failure rounds
are in the dispatch record): `run_30001857104/` (A1, seeds 1–10),
`run_30001867521/` (A2, 11–20), `run_30001878310/` (B1, 1–10),
`run_30001888910/` (B2, 11–20), all green on head `19f4f3ff`. Registered
outputs: `analysis/registered/phase2_v2_registered_family.csv` and
`phase2_v2_detection_family.csv`.

Reproduction: `python analysis/reproduce_phase2_v2.py phase2_v2_corrected`
validates every gate manifest in all four archives and rebuilds both
registered tables byte-equivalently (canonical numeric form) from the
committed archives alone.

## Registered outcome summary (n=20, exact sign-flip, BH m=8 per family; the corrected run governs)

**Tier-1 RecoveryEpisodes family: 2 supported, 3 adverse, 3 null.**

| Cell | Mean Δ (KG − TR) | BH q | Verdict |
|---|---:|---:|---|
| lab2_f1bdead | −92.65 | 1.017×10⁻⁵ | Supported (KG faster) |
| labmon2_f2dead_lowsun | −168.75 | 1.148×10⁻³ | Supported |
| lab3_f1dead | +2066.40 | 1.563×10⁻³ | **Adverse** (KG never detects; censored 20/20 vs 9/20) |
| lab3_f1dead_z2 | +3512.00 | 1.017×10⁻⁵ | **Adverse** (censored 20/20 vs 1/20) |
| lab3_f2dead_lowsun | +3654.15 | 1.017×10⁻⁵ | **Adverse** (censored 20/20 vs 1/20) |
| lab3_f1bdead | −19.95 | 0.595 | Null |
| lab3_f1binv | −16.45 | 0.673 | Null |
| labmon_f1dead | −218.60 | 0.302 | Null (partial detection both arms: 7/20 vs 10/20 censored) |

**Detection family (detector v2 — new instrument, not comparable to the
withdrawn record):** blind cells identical in both arms (probe-driven, 5–6
episodes); inverted-lamp cells ≈0 in both arms (opposite-sign evidence is
never gated); the two dead-lamp members are adverse because the KG arm never
reaches an unmasked state.

## The false-positive/false-negative trade, exactly quantified

- **Zero false-positive blacklist events in all 38 cells × 20 replicas ×
  both arms** (full `BlacklistEvents` record; the withdrawn record's healthy-
  component blacklists are gone). The withdrawn "zero false positives" claim
  becomes true under detector v2 — at a disclosed price:
- **Recall is policy-dependent.** Structural abstention refuses dead-verdicts
  while any co-feeder of the zone is active. In cross-coupled lab3 (spotlight
  + cross-zone arcs) and labmon (monitor co-feeder), a dead lamp is
  detectable only from states with all maskers off. The knowledge-primed
  policy — using exactly its structural knowledge to restore light via
  spotlight/blinds/cross-lamp — never visits such states: KG-arm detection is
  0/20 in every lab3 dead-lamp cell (tabula-rasa: 11–20/20). Inverted faults
  and all lab1/lab2 faults detect perfectly in both arms.

The corrected Phase-2 claim is therefore two-sided: knowledge accelerates
recovery where detection succeeds (daylight-substitution and dual-zone triage
cells), and the same knowledge suppresses dead-fault detectability in
cross-coupled labs by keeping masking actuators active. No pooling across
cells; every value is simulator-conditional.
