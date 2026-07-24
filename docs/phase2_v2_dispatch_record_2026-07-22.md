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

## Amendment 2026-07-23b — second pre-data failure and third dispatch

The 09:00 re-dispatches **also failed pre-data, from the same symptom with a
different cause**: the `680f25a9` alias fix read `$Cfg`, a variable that does
not exist in `run_full_project.ps1` (its config object is `$RunConfig`), and
PowerShell silently treats an undefined variable as `$null` — so the alias
no-oped and every `labmon2_nostereo` clean-training cell in B1
(`29993484405`) and B2 (`29993497191`) failed with the identical
`Protocol-v2 scenario file missing` error; their adapt matrices were skipped.
A1 (`29993457632`) and A2 (`29993470827`) were **cancelled pre-data** as
doomed to the same failure in their three variant parents. As before, no
adaptation cell ran in any round-2 run — no data-bearing cell exists or was
replaced.

Fix (commit `19f4f3ff`): the alias is exposed on the `Read-RunConfig` result
and read from `$RunConfig`; the scenario JSON is parsed by parameter passing
(a piped `ConvertFrom-Json` collapses the array under Windows PowerShell 5.1
— a latent incompatibility the new check exposed); and a
`-ScenarioProvenanceCheckOnly` switch executes the REAL resolution path for
all 14 known profiles — verified green locally on PS 5.1 and added to the CI
preflight job. CI run `30000661399` green on the fix head before dispatch.

Third dispatches (2026-07-23, 11:06 UTC, dispatch head `19f4f3ff`,
byte-identical inputs):

| Dispatch | Round-1 run | Round-2 run | Round-3 run |
|---|---|---|---|
| A1 | `29923594983` | `29993457632` (cancelled) | `30001857104` |
| A2 | `29923609054` | `29993470827` (cancelled) | `30001867521` |
| B1 | `29923621835` | `29993484405` | `30001878310` |
| B2 | `29923634620` | `29993497191` | `30001888910` |
