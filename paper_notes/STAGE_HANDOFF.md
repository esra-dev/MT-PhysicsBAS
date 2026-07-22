# Stage 0 Handoff

## Status

Stage 0 is complete for the `2026-06-15T13:04:27.3504583Z` observation
(`SRC-0040`). No experimental metric, effect, statistical test, or scientific
outcome was interpreted. A later Phase 2 run was still in progress, so its
successor artifact requires a continuation pass (`CLM-S0-016`).

## Completed

- Preserved the original baseline at
  `phase2-fault-detection@2aab559a027468b929cdb5bc83fc402519ccefb2` and added
  the continuation baseline at
  `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410`.
- Confirmed the continuation worktree had no staged or unstaged tracked changes
  and had 35 normal-status untracked top-level paths (`CLM-S0-010` and
  `CLM-S0-011`).
- Inspected refs, logs, the results branch, and the diff from `2aab559a...` to
  `985c7a1...` without switching branches or changing tracked files.
- Added reproducible `TREE_SHA256_V1.mjs` and canonically rehashed 13 visible
  result roots plus seven ignored result-like roots.
- Preserved 17 incorrect nested-root hashes as `[SUPERSEDED]`; they used native
  Windows separators. Added slash-normalized successor rows (`CLM-S0-012`).
- Ingested and hashed `phase2_results_v4`, captured run/job/artifact metadata for
  run `27529585379`, and linked the local root to the committed results snapshot.
- Recorded that the local v4 text is normalization-equivalent to results commit
  `e9b9e3529cd71fce3ad9dfe5fa29c64793898b2e`, but is not byte-identical and is
  not verified against the artifact ZIP (`CLM-S0-015`).
- Added two known cancelled Phase 2 dispatches and the current in-progress run
  `27547019772` to `RUN_LEDGER.csv`.
- Preserved the external writing-guide and thesis-template source hashes from the
  original Stage 0 snapshot.

## Result-Root Inventory

| Root | Classification | Files | Bytes | Canonical TREE-SHA256-V1 |
|---|---|---:|---:|---|
| `analysis/out_full` | local generated | 2 | 70 | `4e29a5214ea3d152e7e09dd859a7dffe4d4fbc86f836f29edc8a3dda21d4854d` |
| `analysis/out_kg_only` | local generated | 2 | 70 | `4e29a5214ea3d152e7e09dd859a7dffe4d4fbc86f836f29edc8a3dda21d4854d` |
| `benchmark/results_full_seed1` | local generated/mixed | 1,398 | 3,436,890,371 | `be0d54fb7873e9d06b9873380106e5fd5db5c93e5a690d3d69a5b6b7dc66f382` |
| `phase1_xzone_asis` | Actions-derived, run 27440842780 | 2,520 | 50,096,910 | `75a9c8ccea76c0bd52cef6cd0dad34bf2f4ffe8c13501690b59f8cbe186b52a9` |
| `phase1_xzone_bumped` | Actions-derived, run 27461188614 | 2,520 | 50,004,016 | `e9d706b2f7828bb65bdb9d091269681b0f9acddd263c7d438777340b8a5b5343` |
| `phase1_xzone_bumped_s11_20` | Actions-derived, run 27462446044 | 2,474 | 49,213,186 | `f80a117fac11c1db5ce3d545b04a4e418590f97c66d3ccc8ff44c6c8cc71152e` |
| `phase1_xzone_ablation` | Actions-derived, run 27464846574 | 2,520 | 50,690,039 | `7c114de88374bb003264a994a50db753edc89113258a4a9a1d7f64831911c638` |
| `phase2_results` | Actions-derived, run 27470382799 | 92 | 12,938 | `95744977ac3f2399a4c068a741bfe5d18051c2a230467f5a5c1d2269778eb1ff` |
| `phase2_results_v2` | Actions-derived, run 27499405083 | 182 | 28,532 | `5354fe2bf014bca618e9eceaed3e40957cda7f85bbf53e5e75f7893bfde99a94` |
| `phase2_results_v3` | Actions-derived, run 27507087176 | 362 | 9,767,277 | `2b6c7b9292b7ae8ce2a9cbcbc0c44bc34945c57d2e9965e977b5dc5c2e676bf1` |
| `phase2_results_v4` | Actions-derived, run 27529585379 | 362 | 10,365,101 | `0b65bb2d54dcb5b06a8c179f518480622d715a3688153f53adea990661e41cf1` |
| `tmp_sweep18_results` | Actions-derived plus recomputation | 1,534 | 9,856,516,039 | `4bfb50bc9eb5481ac27362441c9215b44535ae0650784b46fb20133988ee0de9` |
| `tmp_sweep_n10_results` | Actions-derived plus recomputation | 2,883 | 18,402,357,137 | `0defe493b63063a9dc9dc5315fc394510c6b0ed23ecb3ef8266ba98f43811cdf` |
| `tmp_paper_results` | ignored, unknown provenance | 179 | 1,535,759,802 | `dda0bcc75be228facafa9d242008455b764a0525aad5123c119292f48c9355ba` |
| `tmp_step0_h5` | ignored, local generated | 18 | 3,328,273 | `c357315f3abd4d401640c3867f8f5c1c4fc495a2644204a351a7cb9797adf6f4` |
| `tmp_step0_optB` | ignored, local generated | 32 | 4,755,449 | `b9954c2792e3b8364254b3f2ecb8b4ba3f783f5bd99d455857a9db9ff8a95577` |
| `tmp_step0_probeA_v3` | ignored, local generated | 17 | 2,343,586 | `d33f1fe9694c0622ddf241037f5a319ba4aa0796ab52f5db578a75976db184a5` |
| `tmp_step0_rep` | ignored, local generated | 4 | 807,598 | `7b31cce1ee1457e1b50cc8515fc2d9eaac62276d4b91393fa09cb1104ede68bd` |
| `tmp_step0_rep_v2` | ignored, local generated | 4 | 807,585 | `391beac4397d612516b99783a09daec18017ef29c1684362c84a5118491e034b` |
| `tmp_step2_validation` | ignored, local generated | 7 | 1,116,977 | `fc2ac3983c5e30a88b5466c0e8015bc2666de7e45797a83862f5c5e775f95c42` |

All table values are direct copies of the canonical successor rows in
`SOURCE_LEDGER.csv`; this table is an index, not a new derived result.

## Important Unresolved Items

1. The original advisor-authored notes remain `NOT FOUND` as an immutable source.
2. No local result root is byte-verified against a freshly downloaded artifact
   ZIP; the v4 artifact digest is known, but anonymous download was unavailable.
3. Run `27547019772` was still in progress at the final observation and has no
   ingested successor root.
4. `tmp_sweep_n10_results` lacks six expected seed-8 training markers
   (`CLM-S0-006`).
5. `benchmark/results_full_seed1` has no single run manifest.
6. Ignored local experiment roots lack exact generation commands and source SHAs.
7. The complete cross-workflow Actions chronology, including every failed and
   cancelled run, has not yet been exported.
8. Per-experiment design records must be completed before any result analysis.

See `EVIDENCE_GAPS.md` for resolution requirements.

## Exact Files the Next Stage Must Read

Read these first, in order:

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/TREE_SHA256_V1.mjs`
3. `paper_notes/SOURCE_LEDGER.csv`
4. `paper_notes/RUN_LEDGER.csv`
5. `paper_notes/CLAIM_LEDGER.csv`
6. `paper_notes/EVIDENCE_GAPS.md`
7. `paper_notes/STAGE_HANDOFF.md`

Then read these repository sources for Stage 1 mapping only, without interpreting
result values:

- `README.md`
- `THESIS_PIVOT_MASTER.md`
- `docs/pre_registration.md`
- `docs/PHASE1_TO_PHASE2_CHANGES.md`
- `docs/thesis_meeting_2026-05-22.tex`
- `.github/workflows/phase1.yml`
- `.github/workflows/phase2.yml`
- `.github/workflows/sweep-paper.yml`
- `build.gradle`
- `config/run_config.json`
- `run_full_project.ps1`
- `run_full_project_parallel.ps1`
- `run_phase2_adapt.ps1`
- external `C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex`
- external template files under `C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/`

## Next Stage Objective

Stage 1 should create a repository evidence map and template map. It should classify
all evidence-bearing directories, identify ownership and data flow, and map source
categories to proposed thesis sections. It must not yet select headline findings
or reproduce statistical results. Before leaving provenance work, it must refresh
run `27547019772`; if complete, ingest its artifact into a new directory and append
new source/run rows without overwriting `phase2_results_v4`.

## Stage 4 Continuation Pointer

- Status: `[SUPERSEDED]` for next-stage routing in the sections above.
- Reason: later Stage 2, Stage 3, and Stage 4 passes resolved or superseded several
  Stage 0 open items, including the Phase 2 v5 and Phase 3 n10 chronology.
- Current handoff to read first after the protocol:
  `paper_notes/STAGE4_INVENTORY_HANDOFF.md`.
- Current inventory files:
  `paper_notes/STAGE4_WORKTREE_STATUS_20260616T143435Z.md`,
  `paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv`, and
  `paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv`.

## Stage 1 Refresh Continuation Pointer

- Status: `[DIRECT]` current routing pointer after the Stage 1 refresh observed
  at `2026-06-16T19:42:31.0335226Z`.
- Current handoff to read first after the protocol:
  `paper_notes/STAGE1_REFRESH_HANDOFF_20260616T194231Z.md`.
- Current refreshed maps:
  `paper_notes/REPOSITORY_MAP.md` and `paper_notes/TEMPLATE_MAP.md`.
- Current snapshot:
  `paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md`.

## Stage 0 Refresh Continuation Pointer

- Status: `[DIRECT]` provenance-only refresh after the Stage 0 rerun request
  observed at `2026-06-17T06:51:11.3582240Z`.
- Current handoff to read first after the protocol:
  `paper_notes/STAGE0_REFRESH_HANDOFF_20260617T065111Z.md`.
- Current inventory files:
  `paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md`,
  `paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv`, and
  `paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv`.
- Boundary: no experimental result values were interpreted in this refresh.

## Stage 1 Refresh 2 Continuation Pointer

- Status: `[DIRECT]` current routing pointer after reconciling Stage 1 maps with
  the Stage 0 refresh observed at `2026-06-17T06:51:11.3582240Z`.
- Current handoff to read first after the Stage 0 refresh handoff:
  `paper_notes/STAGE1_REFRESH2_HANDOFF_20260617T071703Z.md`.
- Current refreshed maps:
  `paper_notes/REPOSITORY_MAP.md` and `paper_notes/TEMPLATE_MAP.md`.
- Boundary: no experimental result values were interpreted in this refresh.
