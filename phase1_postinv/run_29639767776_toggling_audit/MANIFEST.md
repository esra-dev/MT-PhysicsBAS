# Test A — §5.4.1 toggling micro-mechanism audit (registered 2026-07-18c §1)

Offline audit of run of record **29639767776** (lab3, seeds 1–10, both arms),
executed 2026-07-19 per the pre-data registration in
`docs/_audit/THESIS_STATE_REPORT.md` Addendum 2026-07-18c §1 (commit
`02ed6c1`). **Outcome: INDETERMINATE (insufficient toggling to instrument)** —
see Addendum 2026-07-19a for the reporting record.

## inputs/ — retrieved per-seed lab3 subset (registration-listed files)

Source: CI artifact **`phase1-consolidated`** (artifact id `8428536694`,
6,408,834 bytes), re-downloaded 2026-07-19; sha256 verified equal to the value
recorded in `../run_29639767776/MANIFEST.md`:
`4029c69365f28741554cde915ae1eea5c51f9322199cc37b4ffaaacd6961d29f`.
The `results`-branch publish commit `077541b` (tag
`results-20260718-102423-phase1_kg_only-e631877`) carries only the root
convenience copies for this run, not the per-seed files, so the CI artifact is
the retrieval source; `benchmark_results_*.csv` spot-checked byte-identical to
the pruned in-repo archive (`../run_29639767776/`).

Layout (per seed n = 1..10, per mode ql_true / ql_false):

```
results_seed<n>/lab3/<mode>/
    bench_step_log_<mode>.csv                       rich per-step log
    benchmark_results_<mode>.csv                    G1 reference counts
    qtable_final_stereotypes_<arm>_lab3.csv         frozen combined table
    qtable_final_stereotypes_<arm>_lab3_zone1.csv   per-zone tables
    qtable_final_stereotypes_<arm>_lab3_zone2.csv
    qtable_final_stereotypes_<arm>_lab3_visits.csv  training visit counts
```

The qtable copies are byte-identical between a seed's ql_true/ and ql_false/
artifact directories (verified); one copy per arm is kept, taken from the
mode directory whose bench loaded it.

## regen_init/ — G3 initial-table regenerations (archive head e631877)

`harness/InitDumpHarness.java` (scratch scaffolding, not part of the build)
drives the unmodified `QLearner.configureQLearner → initWithStereotypes →
saveQTable` code path headlessly with the lab3 profile constants
(goal [3,3], ont ["building_3_complex.ttl"], sunshine_prob 0.75), compiled and
run inside a scratch `git archive` export of commit **`e631877`** (the KG file
`building_3_complex.ttl` changed after that head — commit `5d5c170` — so
regeneration at HEAD would not be faithful). Invocation: gradle `JavaExec` on
`sourceSets.main.runtimeClasspath`, once with `-Drun.seed=101` (`regen_A/`)
and once with `-Drun.seed=202` (`regen_B/`).

- **G3 PASS:** all regenerated files bit-identical between regen_A and regen_B
  (sha256 in `out/audit_results.json`).
- **Faithfulness anchor (descriptive):** regenerated
  `qtable_initial_stereotypes_true_lab3{,_zone1,_zone2}.csv` are
  content-identical (LF-normalised; local files are CRLF) to the run's own
  archived initial dumps on the results branch (`077541b`).
- `state_layout.json` — slot registry + action metadata dumped from the same
  reasoner: slots [Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds,
  Spotlight, sunshine], domain [4,4,2,2,2,2,2,4] → strides
  [512,128,64,32,16,8,4,1]; 11 actions in Q-table column order.

## out/ — audit outputs (`analysis/toggling_micromech_audit.py`)

| file | content |
|---|---|
| `audit_results.json` | all gate/prediction values + decision |
| `SUMMARY.md` | human-readable gate table |
| `toggle_events_ql_true.csv` / `_ql_false.csv` | every D1 flip event, annotated (D2/D3 flags, state, action) |
| `toggle_pairs_ql_true.csv` | the 13 pooled unique KG-arm greedy toggle pairs (visits, init-argmax membership) |
| `g1_reconciliation.csv` | per-episode computed vs recorded ActuatorCyclingCount (800 + 800 episodes, all exact) |
| `g2_failures.csv` | qualifying steps failing the argmax check (empty — 1885/1885 pass) |

Deterministic: fixed MC seed 20260718, 100 000 draws, stdlib only; re-running
the script reproduces every number bit-for-bit.
