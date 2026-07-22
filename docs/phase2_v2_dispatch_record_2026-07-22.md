# Phase 2 protocol-v2 dispatch record (2026-07-22)

The four registered dispatches of `docs/phase2_correction_registration_2026-07-22.md`
§6 were queued on 2026-07-22 (13:22 UTC) from branch
`phase234-correction-2026-07-22`, dispatch head `8010e49f` (contains the
registration commit `7a6b5a71`; CI run `29922310955` was green on the
registration head before dispatch). Identical inputs across dispatches:
`run_mode=phase1_v2_kg_only`, `adapt_episodes=0`, `publish_results=true`.

| Dispatch | GitHub Actions run | adapt_profiles | seeds |
|---|---|---|---|
| A1 | `29923594983` | Group A (12): lab1_f1dead, lab2_f1dead, lab2_f1inv, lab2_f2dead, lab2_f2inv, lab2_f1bdead, lab2_f1binv, labmon_f1dead, labmon_infoonly_f1dead, labmon_nostereo_f1dead, labmon2_f2dead_lowsun, labmon2_infoonly_f2dead_lowsun | 1–10 |
| A2 | `29923609054` | Group A (12) | 11–20 |
| B1 | `29923621835` | Group B (11): lab3_f1dead, lab3_f1inv, lab3_f2dead, lab3_f2inv, lab3_f1dead_z2, lab3_f1inv_z2, lab3_f1bdead, lab3_f1binv, lab3_f2bdead, lab3_f2dead_lowsun, labmon2_nostereo_f2dead_lowsun | 1–10 |
| B2 | `29923634620` | Group B (11) | 11–20 |

Until all four aggregates complete, only operational status is inspected.
Failed cells/dispatches are preserved and documented; any re-dispatch uses
byte-identical inputs with both run IDs recorded here.
