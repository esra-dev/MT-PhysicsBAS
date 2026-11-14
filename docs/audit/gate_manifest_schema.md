# Gate-manifest schema (`*_OK.json`)

Every corrected-protocol campaign cell must write exactly one gate manifest.
An archive validator rejects any cell whose manifest is missing, inconsistent,
or carries a nonzero fallback count; aggregate analyses may only consume cells
that pass. The Phase-1 v2 `TRAINING_OK.json` (validated by
`analysis/validate_phase1_v2_archive.py`) is the reference implementation; the
Phase-2/3/4 manifests extend the same contract.

## Common keys (all manifest kinds)

| Key | Type | Meaning |
|---|---|---|
| `protocol_version` | string | Corrected-protocol tag for the cell (`phase1-v2` for training/benchmark cells that use the shared ql/bench agents; `phase2-v2` for adapt cells; `phase3-v2` for dynamics cells). |
| `run_seed` | int | The cell's RNG seed (or replica index for Phase 3). |
| `scenario_fallback_count` | int | MUST be `0`. Any silent scenario substitution is a protocol violation. |
| `ordered_scenario_ids` | int[] | The actual (possibly non-contiguous) scenario IDs in file order, when the cell cycles a scenario catalogue. |
| `scenario_schedule_sha256` | string | SHA-256 of the comma-joined ordered IDs (`ScenarioCatalog.scheduleSha256`). Paired arms must match exactly. |
| `metric_schema` | string | Schema tag of every metric row the cell wrote. |

## `TRAINING_OK.json` — Phase-1 v2 training cells (also Phase-2 v2 parents, Phase-4 v2 training)

Existing schema: common keys plus `fixed_horizon_episodes` (3000),
`paired_rng_version` (`common-seed-v1`), `run_mode`. Phase-4 v2 cells add
`policy_energy_weights_sha256` (hash of the config-driven weight map).

Treatment-delivery keys (added 2026-11 after audit AUD-001, written by every
training cell since):

| Key | Meaning |
|---|---|
| `stereo_requested_props` | The stereotype knob values the run mode requested (`stereo.irrelevantDvPrior`, `stereo.bandMirrorInit`, `stereo.bandMirrorPrior`; 0.0 when not requested). |
| `stereo_effective_props` | The values the JVM actually used, parsed from the `STEREO_EFFECTIVE_PROPS {json}` line `StereotypeReasoner` logs at construction (also carries `stereo.redundancyOnly`). The runner FAILS the cell before writing the manifest if any requested value differs from the effective one. `analysis/validate_phase1b_archive.py --require-effective-props` re-checks the archive against the mode's registered values. |

## `ADAPT_OK.json` — Phase-2 v2 adaptation cells

Common keys plus:

| Key | Meaning |
|---|---|
| `profile` / `parent_profile` | Faulty profile and its clean parent. |
| `parent_qtable_sha256` | Hash of the warm-loaded clean Q-table file(s), binding the adapt cell to its exact parent artifact. |
| `adapt_horizon_episodes` | The cell's re-learn budget. |
| `detector_version` | `fault-detector-v2` (structural-maskability abstain). |
| `settled_start_state` | MUST be `true`: start states recorded only after the 250 ms settle. |
| `mode` | `ql_true` or `ql_false`. |
| `scenario_file_sha256` | (since 2026-11, audit R2-001/R2-002) SHA-256 of the committed scenario file bytes. The schedule hash covers IDs only, so a pinned-sun file derived from its parent hashes identically there; the file hash distinguishes the delivered environmental treatment. |
| `scenario_sunshine_values` | (since 2026-11) sorted unique `Sunshine` values of the scenario file the explicit starts actually used. |
| `lowsun_pin_delivered` | (since 2026-11) for `*_lowsun` profiles: `true` iff every scenario pins `Sunshine = 100`; `null` for every other profile. `analysis/validate_phase2_v2_archive.py --require-treatment-delivery` makes the evidence mandatory for low-sun cells. |
| `knowledge_layer` | (since 2026-11-14, structure-only campaign) the KG layer REQUESTED for the adapt JVM: `full` (runs-of-record default), `brick`, or `redundancy`. |
| `knowledge_layer_delivered` | (since 2026-11-14) the layer the adapt JVM ACTUALLY constructed, read back from the `StereotypeReasoner: knowledge layer = …` banner in the cell log (`unknown` when absent, which fails the cell). `analysis/validate_phase2_v2_archive.py --require-knowledge-layer <layer>` makes both keys mandatory and equal for every cell. |

## `DYNAMICS_OK.json` — Phase-3 v2 dynamics cells

Common keys (scenario keys omitted — Phase 3 has no scenario catalogue) plus:

| Key | Meaning |
|---|---|
| `profile` / `mode` / `replica` | Cell coordinates. |
| `energy_meter` | `tick-v1`: energy integrated over simulator Tick deltas, never wall-clock. |
| `blind_delay_ticks` / `seconds_per_tick` | Ground-truth constants in force. |

## `BENCH_OK.json` — Phase-4 v2 benchmark cells

Common keys plus `profile`, `mode` (`rule_based`/`ql_false`/`ql_true`), and
`policy_energy_weights_sha256`. `metric_schema` must be
`phase1-benchmark-v2`.
