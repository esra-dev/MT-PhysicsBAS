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

## Amendment 2026-07-23 — pre-data dispatch failure and re-dispatch

All four dispatches above **failed pre-data**: `Get-Phase1ScenarioProvenance`
derived the protocol-v2 scenario file from the profile name, but the four
monitor-variant parents (`labmon_infoonly`, `labmon_nostereo`,
`labmon2_infoonly`, `labmon2_nostereo`) share their base lab's scenario file
— every such clean-training cell threw
`Protocol-v2 scenario file missing: benchmark/train_scenarios_<variant>.json`
and the entire adapt matrix was skipped (`needs: train_clean`). **No
adaptation cell ran in any of the four runs, so no data-bearing cell exists
or was replaced.** The failed runs are preserved as operational history.

Fix (commit `680f25a9`): config `train_scenarios_alias` maps each variant
profile to its base lab, mirroring the `lab_profiles.asl` mapping the agent
itself uses; the runner records the resolved file in TRAINING_OK; a new guard
test (`analysis/tests/test_runner_allowlists.py`) makes an unresolvable
scenario file a local test failure. CI run `29987410238` green on the fix
head before re-dispatch.

Re-dispatches (2026-07-23, 09:00 UTC, dispatch head `680f25a9`,
byte-identical inputs):

| Dispatch | Failed run (pre-data) | Re-dispatch run |
|---|---|---|
| A1 | `29923594983` | `29993457632` |
| A2 | `29923609054` | `29993470827` |
| B1 | `29923621835` | `29993484405` |
| B2 | `29923634620` | `29993497191` |
