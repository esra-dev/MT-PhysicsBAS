# Stage 2 Refresh Handoff - 20260617T074205Z

## Status

- [DIRECT] Stage 2 refresh captured current Git refs and visible GitHub Actions
  run metadata at `2026-06-17T07:42:05.4344461Z`.
  Locator:
  `local-sha256:6d6d994bb1a4a73680f18b3fcb52136d53279fbe0611f2543e945e34e9b1be27:paper_notes/GIT_AUDIT_20260617T074205Z.txt:L1-L13`.
- [DERIVED] The refreshed Actions table contains `125` visible runs and `2`
  successful Phase 3 workflow runs; the latest visible run row remains
  `27621106006`.
  Locators:
  `local-sha256:865583cb352036e55a15a71b74a5057cde62c49cf4abbce5eeb9694ba7b86456:paper_notes/ACTIONS_RUNS_20260617T074205Z.csv:rows 2-126; named columns databaseId,workflowName,status,conclusion,headSha,updatedAt,url`;
  `local-sha256:b469ae75fcbf835d02fe24b4e318118fa4c73b899baca7e9872c1f19451ef556:paper_notes/ACTIONS_SUMMARY_20260617T074205Z.csv:rows 2,12; named columns workflow,conclusion,run_count`.
- [DIRECT] No branch switch, reset, clean, deletion, artifact overwrite,
  workflow dispatch, experimental run, result-value analysis, effect-size
  analysis, or statistical-test analysis was performed in this Stage 2 refresh.
  Locator:
  `local-sha256:cb539c624bb31ce1e1b6b940d9a7a5182614e9b6563a37b0418304ddb6600ffa:paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md:L34-L40`.

## Completed Work

- [DIRECT] Read `paper_notes/00_PROTOCOL.md`, Stage 0R2 files, the Stage 1
  refresh handoffs, `REPOSITORY_MAP.md`, `TEMPLATE_MAP.md`, and the three
  ledgers before updating Stage 2.
- [DIRECT] Created new Stage 2 refresh captures:
  `paper_notes/ACTIONS_RUNS_20260617T074205Z.json`,
  `paper_notes/ACTIONS_RUNS_20260617T074205Z.csv`,
  `paper_notes/GIT_AUDIT_20260617T074205Z.txt`, and
  `paper_notes/ACTIONS_SUMMARY_20260617T074205Z.csv`.
- [DIRECT] Updated `paper_notes/CHRONOLOGY.md` with a Stage 2 refresh section
  that reconciles Stage 0R2/Stage 1R2 routing, current refs, visible Actions
  runs, local-root limitations, dirty-doc status, and root-level runtime-file
  limitations.
- [DIRECT] Updated `paper_notes/EVIDENCE_GAPS.md` with `GAP-030`, identifying
  Stage 2R as chronology/authority routing rather than experiment extraction.
- [DIRECT] Updated `SOURCE_LEDGER.csv`, `CLAIM_LEDGER.csv`, and
  `RUN_LEDGER.csv` with Stage 2R rows.

## Unresolved Issues

1. [UNRESOLVED] Local result roots are still not ZIP-byte-verified against
   GitHub Actions artifact archives.
   Locator:
   `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 13,15; named columns path,verification_status,content_hash,limitations`.
2. [UNRESOLVED] Root-level Phase 3 runtime CSV/TTL files still lack exact
   command, run, and artifact identity.
   Locator:
   `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 5-16; named columns path,provenance_class,sha256,limitations`.
3. [UNRESOLVED] Per-experiment Evaluation records still need primary-row
   extraction before manuscript findings are written.
   Locator:
   `local-sha256:d65e80cd0833782f413a99ebf74de3ac6a4d08c5e6520866645c4e537c0e652d:paper_notes/STAGE1_REFRESH2_HANDOFF_20260617T071703Z.md:L42-L56`.

## Exact Files The Next Stage Must Read

Read these first, in order:

1. `paper_notes/00_PROTOCOL.md`
2. `paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md`
3. `paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv`
4. `paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv`
5. `paper_notes/SOURCE_LEDGER.csv`
6. `paper_notes/CLAIM_LEDGER.csv`
7. `paper_notes/RUN_LEDGER.csv`
8. `paper_notes/EVIDENCE_GAPS.md`
9. `paper_notes/STAGE0_REFRESH_HANDOFF_20260617T065111Z.md`
10. `paper_notes/STAGE1_REFRESH_HANDOFF_20260616T194231Z.md`
11. `paper_notes/REPOSITORY_MAP.md`
12. `paper_notes/TEMPLATE_MAP.md`
13. `paper_notes/STAGE1_REFRESH2_HANDOFF_20260617T071703Z.md`

Then read the Stage 2 refresh products:

14. `paper_notes/CHRONOLOGY.md`
15. `paper_notes/ACTIONS_RUNS_20260617T074205Z.csv`
16. `paper_notes/ACTIONS_SUMMARY_20260617T074205Z.csv`
17. `paper_notes/GIT_AUDIT_20260617T074205Z.txt`
18. `paper_notes/STAGE2_REFRESH_HANDOFF_20260617T074205Z.md`

Continue with per-experiment extraction. Do not write polished thesis prose;
write evidence records, tables, figure specifications, and gap records only.
