# Evidence Gaps

## Open Gaps

### GAP-001: Original advisor-authored source provenance remains limited

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: `AUDIT HISTORY` and research requirements
- Observation: Stage 2R2 located and hashed the external local file
  `C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt`, which contains the
  advisor quotations and the user's explanatory project-history narrative.
  The original advisor-authored meeting document, email, scan, or exported note
  remains `NOT FOUND`.
- Risk: later notes could treat the external local compilation as the original
  advisor-authored artifact or as empirical result evidence.
- Resolution: cite the hashed external local file as requirement and pivot
  evidence only; continue to search for the original advisor-authored artifact if
  a stricter provenance source is required.
- Stage 2 update: the exact pivot time remains `NOT FOUND`. The observable
  implementation pivot is bounded by the June 8 old-line brief and the June 10
  clean-lab workflow commit, but that interval must not be presented as the
  advisor-meeting date. Evidence: `CLM-S2-003` and
  `paper_notes/CHRONOLOGY.md` section `Chronological Audit History`.
- Stage 2R2 update: advisor-note content is now hash-addressed as
  `SRC-S2R2-001`; original advisor-authored source provenance and exact pivot
  timestamp remain unresolved. Evidence: `CLM-S2R2-001`.

### GAP-002: Extracted directories are not cryptographically tied to artifact ZIPs

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Phase 1, Phase 2, Sweep 18, and n10 result roots
- Observation: canonical local tree hashes were computed and documents declare
  mappings to GitHub Actions runs. For v4, GitHub artifact ID `7636716341` and
  digest `sha256:278dd690109934a7d4813d1dd991e768ee08c4b3e2e29ca5dfb7e8d32c70c5b1`
  are recorded by `SRC-0043`, but anonymous download failed because no GitHub CLI
  authentication token is configured. ZIP digest and fresh-extraction comparison
  remain unverified for every result root.
- Risk: a local file could have been added, removed, or recomputed after download.
- Resolution: re-download each consolidated artifact into a fresh directory when
  API limits permit; capture the Actions artifact ID and digest; hash the fresh
  extraction; compare file manifests with the existing local root.

### GAP-003: `benchmark/results_full_seed1` is a mixed local root

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: local benchmark evidence
- Observation: the directory contains 1,398 files and 3,436,890,371 bytes, with
  modification times spanning May 21 through June 10, 2026, across several
  profiles. No single `RUN_MANIFEST.json` was found.
- Risk: values from different code states or executions may be combined.
- Resolution: reconstruct each profile's command, code SHA, configuration, and
  run time from logs and markers, or exclude this root from manuscript evidence.

### GAP-004: Two untracked analysis roots contain placeholder output

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: `analysis/out_full` and `analysis/out_kg_only`
- Observation: each root contains a zero-byte `summary_table.csv` and a 70-byte
  `weakness_heatmap.csv`; both roots have the same tree hash.
- Risk: they may be mistaken for valid completed analyses.
- Resolution: identify the generating command and inputs, or mark the roots
  permanently unusable.

### GAP-005: `tmp_paper_results` has mixed and incomplete provenance

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: one child is named `recover_26981739883`, tying it nominally to a
  failed Actions run. The sibling `sweep-paper-consolidated` is not yet mapped to
  one exact run.
- Resolution: compare its file manifest with candidate Actions artifacts and
  inspect any retained download command or shell history.

### GAP-007: Untracked documents and scripts are mutable

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: pivot notes, Phase 1 analysis notes, meeting briefs, demo files, and two
  analysis scripts.
- Observation: SHA-256 hashes stabilize the Stage 0 snapshot, but the files are not
  committed and have no Git history.
- Risk: chronology and authorship cannot be reconstructed from Git alone.
- Resolution: preserve the current hashes; later compare with backups, Actions
  artifacts, file history, and relevant commits. Do not silently replace a ledger
  row when a file changes.

### GAP-008: n10 artifact is structurally missing six training markers

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Root: `tmp_sweep_n10_results`
- Observation: all ten `results_seed*` directories exist, but only 54 of 60
  expected `TRAINING_OK.json` files are present. Missing paths are the true and
  false training markers for custom3, custom5, and custom9 under seed 8.
- Risk: local artifact completeness cannot be assumed even if aggregate analysis
  files exist.
- Resolution: inspect run `27094219403` job/artifact inventory and re-download the
  six seed-8 training artifacts or determine why they were omitted.

### GAP-009: Full Actions artifact metadata snapshot was rate-limited

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: run metadata and artifact totals were captured, but repeated REST
  requests reached the unauthenticated API rate limit before all consolidated
  artifact IDs and digests could be recorded. The v4 consolidated artifact is now
  captured by `SRC-0043`; earlier consolidated artifacts remain incomplete.
- Resolution: authenticate GitHub CLI or retry after rate-limit reset; collect only
  the consolidated artifact metadata needed for the ledger.
- Stage 2 update: selected run and artifact endpoints were queried at
  `2026-06-15T15:50:57.8683740Z`. Run metadata was captured in `SRC-S2-008` and
  partial artifact metadata in `SRC-S2-010`, but all six jobs endpoints returned
  HTTP 504/invalid JSON (`SRC-S2-009`, `CLM-S2-009`). Artifact capture was limited
  to `per_page=100` and is not a completeness statement.

### GAP-010: Ignored experiment roots lack immutable code-state links

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Roots: `tmp_step0_h5`, `tmp_step0_optB`, `tmp_step0_probeA_v3`,
  `tmp_step0_rep`, `tmp_step0_rep_v2`, and `tmp_step2_validation`.
- Observation: all roots are hashed, but exact commands and source SHAs are not yet
  linked.
- Resolution: inspect scripts, logs, pre-registration deviations, and Git history
  during the chronology stage.

### GAP-011: Template is outside the repository

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: the thesis template is hashed and readable under
  `C:/Users/esrad/Downloads/Template-ThesisReport`, but is not versioned with this
  project's evidence notes.
- Resolution: preserve its current hashes and later decide whether to create a
  separately versioned paper workspace. Do not alter the external template during
  evidence extraction.

### GAP-012: Phase 2 v5 final metadata and result root ingested with limitations

- Status: `CLOSED_WITH_LIMITATION`
- Label: `[DIRECT]`
- Run locator: `RUN-27547019772`; claim `CLM-S0-016`.
- Observation: run `27547019772` was `in_progress` at
  `2026-06-15T13:16:13.0678419Z` on head
  `985c7a18558b6d5cb96c018a395b0aae6389f410`.
- Risk: v4 must not be described as the final Phase 2 evidence after a later run
  has started.
- Resolution: after completion, capture final run/job/artifact metadata, download
  into a new root, verify the archive digest, compute the canonical tree hash, and
  add the successor run/source rows. Do not analyze its result values in Stage 0.
- Stage 1 update: GitHub reported status `queued`, conclusion `null`, head SHA
  `985c7a18558b6d5cb96c018a395b0aae6389f410`, and updated time
  `2026-06-15T13:20:38Z` at observation
  `2026-06-15T13:46:11.9819313Z` (`CLM-S1-007`). No artifact was ingested.
- Stage 2 update: the run remained `in_progress` at observation
  `2026-06-15T15:50:57.8683740Z`; its metadata was last updated at
  `2026-06-15T15:21:12Z`. Partial per-cell artifact metadata existed, but no
  completed conclusion or final ingested result root existed. Evidence:
  `SRC-S2-008`, `SRC-S2-010`, and `CLM-S2-008`.
- Stage 2 continuation: run `27547019772` completed `success` on attempt `2`,
  published artifact `phase2-consolidated` (`7647220538`, digest
  `sha256:8be79a29338d49ca54a869b6e610fbec2a7fc074cc375a74b1658344657ae102`),
  and was committed to `origin/results` at
  `22a448be5d9829751badd341904e36ed582f091f`. Evidence: `SRC-S2-021`,
  `SRC-S2-023`, `SRC-S2-027`, and `CLM-S2-011`.
- Remaining limitation: artifact ZIP byte identity and a downloaded local tree
  hash are still `NOT FOUND`; committed result CSV rows are the authoritative
  source until an archive verification stage is run.

### GAP-013: Full GitHub Actions chronology is only partially complete

- Status: `PARTIALLY_RESOLVED`
- Label: `[UNRESOLVED]`
- Observation: Stage 2 captured and appended all `117` runs visible to the public
  run-list API at `2026-06-15T15:34:50.3118706Z`, including failed, cancelled,
  successful, and in-progress executions (`SRC-S2-002` through `SRC-S2-006`,
  `CLM-S2-004`). A continuation capture at `2026-06-16T13:36:09.2345198Z`
  captured `125` visible runs and summarized `2` successful Phase 3 workflow
  runs (`SRC-S2-017` through `SRC-S2-020`, `CLM-S2-018`). Deleted/API-invisible
  runs, workflow_dispatch input payloads, expired logs, and artifact ZIP bytes
  remain `NOT FOUND`.
- Risk: audit history could omit failed attempts relevant to protocol deviations or
  selective-reporting assessment.
- Resolution: retain the hashed Stage 2 snapshot; authenticate/retry the jobs and
  artifact endpoints; capture dispatch inputs where the API exposes them; and
  preserve any later-discovered/deleted-run evidence as additive ledger rows.

### GAP-015: Per-experiment design records require result-stage verification

- Status: `CLOSED_WITH_LIMITATIONS`
- Label: `[UNRESOLVED]`
- Observation: Stage 2 created design records `EXP-PRE-01` through `EXP-P2-05` in
  `paper_notes/CHRONOLOGY.md`, covering research question, prior expectation,
  baseline/treatment, variables/controls, metrics/statistics, unexpected results,
  follow-up, runs, and research status.
- Risk: interpreting outputs before these records exist could retroactively alter
  hypotheses or confuse engineering validation with confirmatory evidence.
- Remaining limitation: numeric result claims and some final statistical-method
  details still require row-level verification against authoritative artifacts in
  later result-extraction stages. The Phase 2 v5 design record has no result.

### GAP-016: Conference-paper target format is not identified

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: the available external template is an HSG master-thesis template
  with an abstract, five chapters, bibliography, appendix, and declaration
  include. No conference name, call for papers, page limit, anonymization rules,
  or conference LaTeX class was found.
- Evidence: `SRC-S1-015`, `CLM-S1-004`, and `paper_notes/TEMPLATE_MAP.md`.
- Risk: thesis-structure routing may not match the later conference-paper format.
- Resolution: identify the target venue and hash/version its official author kit;
  keep evidence notes format-neutral until then.
- Stage 1 refresh: this remains open. The refreshed template map still routes
  evidence into the external thesis template, not a verified conference author
  kit. Evidence: `CLM-S1R-004` and
  `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport`.

### GAP-017: Thesis Phase 3 implementation and results located with limitations

- Status: `CLOSED_WITH_LIMITATION`
- Label: `[DIRECT]`
- Observation: the pivot document specifies learned temporal/process dynamics and
  a possible `responseDelay` KG property, but the Stage 1 repository search found
  no matching implementation or experiment. Occurrences of "Phase 3" in runners
  denote internal pipeline stages rather than the thesis Phase 3.
- Evidence: `CLM-S1-006`; requirement locator
  `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L48-L56`.
- Risk: manuscript notes could incorrectly present planned work as completed.
- Resolution: either locate and hash the implementation/run evidence or retain
  Phase 3 only as future work with `NOT FOUND` implementation status.
- Stage 2 continuation: Phase 3 implementation is present in commit
  `7137f8870881017a9eedd40c837e517481d0e9ce`, merged to `origin/main` at
  `3bb5289c36cb3093228ec0609fe57ec676b1ee53`; final n10 results are present on
  `origin/results` at `0372ecd5864fa6555ebfce7d05e05d9aaab96994` for run
  `27621106006`. Evidence: `SRC-S2-025`, `SRC-S2-026`, `SRC-S2-029`,
  `CLM-S2-012`, and `CLM-S2-015` through `CLM-S2-017`.
- Remaining limitation: exact `workflow_dispatch` input payload for run
  `27621106006` is `NOT FOUND`; n10 execution is verified from result rows and
  job/artifact matrices, not from exposed dispatch inputs (`CLM-S2-014`).
- Stage 1 refresh: the original Stage 1 `NOT FOUND` claim for Phase 3
  implementation is superseded by current committed sources. Evidence:
  `CLM-S1R-003`,
  `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/DynamicsLearner.java:L13-L60`,
  `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/illuminance_controller_agent_dynamics.asl:L1-L83`,
  `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/phase3_dynamics.py:L1-L55`, and
  `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L1-L70`.

### GAP-018: Local log tree mixes executions

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: `log/` has canonical tree hash
  `4b2a846600b09d29f8ef221089a24a36bd2643ce320dba41662cea5205488305`,
  but the tree combines training, benchmark, adaptation, JSONL, and diagnostics
  without one run manifest.
- Evidence: `SRC-S1-016`, `CLM-S1-003`.
- Risk: log lines may be attributed to the wrong code state or execution.
- Resolution: partition logs by execution using timestamps, command banners,
  process IDs, profiles, and matching output hashes; otherwise use for audit-only
  debugging.

### GAP-019: Root-level generated artifacts lack one immutable grouping

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: the repository root contains mutable Q-tables, metrics, coverage,
  first-goal, IV-statistics, learned-Turtle, benchmark CSV, step-log, and plain-log
  files. Their schemas are documented, but Stage 1 did not establish one exact
  run/code/command identity for the current collection.
- Evidence: output schemas at
  `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L92-L150`.
- Risk: manuscript extraction could mix outputs from different local runs.
- Resolution: hash and ledger individual files only when linked to a run, or
  exclude them in favor of run-scoped Actions/result-branch snapshots.

### GAP-020: Candidate PDF lacks bibliographic identity

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: `3600100.3623737.pdf` is preserved as
  `local-sha256:8da47a5f099e88bd8aa8e527ad35aa285bbddd05810f30e9b3337d87776412ee:3600100.3623737.pdf`,
  but its title, authors, venue, and role were not extracted in Stage 1.
- Evidence: `SRC-S1-018`, `CLM-S1-009`.
- Risk: an unidentified local PDF could be cited incorrectly or omitted from the
  related-work source audit.
- Resolution: extract metadata/text, verify against a publisher or DOI source,
  and add a bibliographic source record before manuscript use.

### GAP-021: Formal post-pivot preregistration is not found

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Observation: the named-ref search found inherited `docs/pre_registration.md`
  copies, but no commit to that file after the June 10 clean-lab implementation
  and no searched post-pivot identifiers (`lab1`, `lab2`, `lab3`, fault detection,
  blacklist, warm restart, re-learn, cross-zone, or Phase 1/2 run-mode names).
- Evidence: `SRC-S2-011`, `SRC-S2-012`, and `CLM-S2-005`; derived output
  `local-sha256:054ec14d3ece1950cb8f00bcb739728481e1d8c7a50120579c554172faf95cab:paper_notes/POST_PIVOT_PREREG_SEARCH_20260615.txt:L1-L49`.
- Risk: prospectively configured follow-ups could be mislabeled as formally
  pre-registered confirmatory experiments.
- Resolution: locate and hash any external registration/advisor-approved protocol;
  otherwise retain Phase 1/2 as post-hoc exploratory or engineering validation,
  with replication/ablation described only as prospective checks within that line.
- Stage 2 continuation: local commit
  `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` records a pre-run Phase 3 n10
  expectation and command, but it is not a formal external preregistration and
  run `27621106006` reports head SHA
  `3bb5289c36cb3093228ec0609fe57ec676b1ee53`. Keep Phase 3 n10 labelled
  `CONFIRMATORY_RELATIVE_TO_LOCAL_PRE_RUN_PLAN`, not formally pre-registered.
  Evidence: `SRC-S2-021`, `SRC-S2-026`, and `CLM-S2-014`.
- Stage 3 update: `RESEARCH_MODEL.md` and `CLAIM_DEPENDENCY_MAP.md` preserve the
  same distinction: Phase 1 and Phase 2 remain post-hoc/engineering-validation
  lines after the pivot, and Phase 3 n10 remains confirmatory only relative to
  the local pre-run plan. Evidence: `SRC-S3-001`, `SRC-S3-002`,
  `CLM-S3-003`, and `CLM-S3-008`.

### GAP-023: Phase 1 final numeric result extraction is completed with limitations

- Status: `CLOSED_WITH_LIMITATION`
- Label: `[DERIVED]`
- Scope: Phase 1 manuscript evidence
- Observation: Stage 3 reconstructed the Phase 1 research question, variables,
  controls, and implementation boundary, but did not select and row-extract final
  numeric Phase 1 speedup, redundancy, energy, or final-success claims.
- Risk: the manuscript could overstate the clean-lab anchor before the result
  rows and statistical-family boundaries are selected.
- Resolution: in the result-extraction stage, select the authoritative Phase 1
  result run(s), cite CSV row numbers and named columns for every numeric value,
  and mark superseded/as-is/bump/replication/ablation outputs separately.
- Evidence: `SRC-S3-001`, `SRC-S3-002`, and `CLM-S3-004`.
- Stage 1 refresh: still open; the refreshed maps inventory Phase 1 sources and
  local result roots only. No Phase 1 numeric outcome was selected or
  interpreted. Evidence: `CLM-S1R-006` and
  `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L15-L16`.
- Stage 6 update: Phase 1 row-level numeric extraction is now completed in
  `PHASE1_RESULTS.md` and `PHASE1_TABLES.csv`. Deterministic final-policy means,
  final-policy paired mean differences, learning-speed condition means, and
  learning-speed paired mean differences were recomputed from raw local CSV files
  and matched the analysis rows. Remaining limitations are tracked under
  `GAP-035`.
- Stage 6 evidence:
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L1-L133`;
  `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`;
  `local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520`.

### GAP-024: Dirty stage documents contain unverified result prose

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 4 documentation inventory
- Observation: the current worktree has dirty tracked documentation files
  `docs/PHASE1_TO_PHASE2_CHANGES.md` and `docs/PHASE2_TO_PHASE3_CHANGES.md`.
  They are hashed as `SRC-S4-004` and `SRC-S4-005`, but Stage 4 did not analyze
  or verify their empirical numeric claims.
- Risk: manuscript notes could accidentally cite local prose instead of primary
  CSV rows, Actions metadata, or committed result snapshots.
- Resolution: treat these files as documentation/routing sources only until every
  result claim is re-extracted from committed `origin/results` CSV rows or
  verified Actions artifacts.
- Evidence: `SRC-S4-003`, `SRC-S4-004`, `SRC-S4-005`, and `CLM-S4-005`.

### GAP-025: Stage 4 local download roots are not ZIP-byte-verified

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: local result/download roots
- Observation: `phase2_results_v5`, `phase3_download`, and
  `phase3_download_n10` were hashed and classified as declared Actions-derived
  local roots, but Stage 4 did not verify byte identity against the GitHub
  Actions artifact ZIP digests.
- Risk: a local extracted directory could differ from the archived artifact while
  sharing the same broad run family.
- Resolution: download artifacts by run ID with recorded artifact IDs/digests,
  verify archive digest where available, then compare extracted file hashes or use
  committed `origin/results` snapshots for manuscript evidence.
- Evidence: `SRC-R014`, `SRC-R015`, `SRC-R016`, `SRC-S4-002`,
  `CLM-S4-003`, and `CLM-S4-004`.
- Stage 1 refresh: unchanged. The current repository map routes
  `phase2_results_v5` and `phase3_download_n10` as local candidates only and
  prefers committed `origin/results` rows for manuscript values until archive
  verification is added. Evidence:
  `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 13-15; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations`.

### GAP-026: Root-level Phase 3 runtime files lack run identity

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: ignored Phase 3 runtime files at repository root
- Observation: Stage 4 hashed 12 root-level Phase 3 runtime files, but their exact
  command, run, and artifact identity remain `NOT FOUND`.
- Risk: root-level files could be mistaken for authoritative run-scoped evidence.
- Resolution: exclude these files from manuscript evidence unless linked to a
  specific command and code state; prefer `origin/results` or verified Actions
  artifacts.
- Evidence: `SRC-S4-003` and `CLM-S4-006`.

### GAP-027: Phase 3 slow-lab Node-RED directories are runtime state

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: `.node-red-lab2_slow` and `.node-red-lab3_slow`
- Observation: Stage 4 hashed the two untracked Phase 3 slow-lab Node-RED runtime
  directories, but they are local runtime directories rather than result sources.
- Risk: runtime configuration/state could be over-cited as empirical evidence.
- Resolution: use committed simulator flow JSON and run-scoped result artifacts for
  manuscript evidence; keep these directories audit-only unless a future stage
  establishes a reproducible runtime-state requirement.
- Evidence: `SRC-R017`, `SRC-R018`, and `SRC-S4-002`.

### GAP-028: Stage 0 refresh remains local-hash only for result roots

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 0 refresh observed at `2026-06-17T06:51:11.3582240Z`
- Observation: the refresh rehashed `23` result/result-like roots and `6`
  Node-RED runtime directories in
  `paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv`, but did not
  download or byte-verify GitHub Actions artifact ZIPs.
- Risk: local directory hashes prove the current local bytes only; they do not
  prove identity to the remote artifact archives.
- Resolution: for manuscript values, prefer committed `origin/results` snapshots
  or download artifacts by run ID and artifact ID, verify archive digest where
  available, then compare extracted file hashes.
- Evidence: `SRC-S0R2-003`, `CLM-S0R2-003`, and
  `CLM-S0R2-005`.

### GAP-029: Stage 1R2 maps are routing-only evidence

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 1 Refresh 2 repository/template routing after Stage 0R2
- Observation: Stage 1R2 updates map current evidence categories and template
  destinations, but does not extract experiment-level result values, effect
  sizes, statistical tests, or manuscript findings.
- Risk: routing notes could be mistaken for completed experiment records or
  result claims.
- Resolution: before writing Evaluation findings, create per-experiment records
  with research question, prior expectation, baseline, treatment, variables,
  controls, metrics, statistical method, unexpected results, follow-up analysis,
  and confirmatory/exploratory status.
- Evidence: `CLM-S1R2-001`, `CLM-S1R2-004`, and `CLM-S1R2-005`.

### GAP-030: Stage 2R chronology refresh is not experiment extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 2 refresh observed at `2026-06-17T07:42:05.4344461Z`
- Observation: Stage 2R captured current Git refs and visible GitHub Actions run
  metadata, reconciled Stage 0R2/Stage 1R2 routing into `CHRONOLOGY.md`, and
  created a handoff, but it did not extract new experimental result values,
  effect sizes, statistical tests, or per-experiment manuscript findings.
- Risk: chronology evidence could be mistaken for final Evaluation evidence.
- Resolution: use Stage 2R for AUDIT HISTORY and authority routing only; before
  writing Evaluation findings, create per-experiment evidence records from
  committed CSV/JSON rows or verified Actions artifacts.
- Evidence: `CLM-S2R-001`, `CLM-S2R-002`, `CLM-S2R-003`, and `CLM-S2R-004`.

### GAP-031: Stage 3R refresh is claim-structure reconciliation only

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 3 refresh observed at `2026-06-17T08:07:55.6279417Z`
- Observation: Stage 3R updated the research model and claim dependency map
  against Stage 0R2, Stage 1R2, and Stage 2R routing. It did not execute a
  workflow, run an experiment, perform result-value analysis, compute effect
  sizes, compute statistical tests, or complete Phase 1 final numeric row
  extraction.
- Risk: later manuscript work could mistake refreshed claim structure for
  completed Evaluation extraction.
- Resolution: use Stage 3R for research-question and claim-dependency routing
  only. Evaluation notes must still cite primary committed result CSV rows,
  verified artifact rows, or derived chains with script hashes and exact
  commands.
- Evidence: `CLM-S3R-001`, `CLM-S3R-002`, `CLM-S3R-003`, `CLM-S3R-004`,
  `CLM-S3R-005`, and `CLM-S3R-006`.

### GAP-032: Stage 4 architecture mapping is not evaluation extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 4 architecture extraction observed at `2026-06-17T08:36:30Z`
- Observation: Stage 4 mapped the implementation architecture, output contracts,
  diagrams, and research construct-to-code relationships, but it did not execute
  a workflow, run an experiment, extract new result values, compute effect sizes,
  compute statistical tests, or close Phase 1 final numeric row-level extraction.
  Stage 4 also records a Phase 3 provenance mismatch: the current workflow's
  `replicas` input default is `1,2,3,4,5,6,7,8,9,10`, while the environment
  fallback for `REPLICAS` is `1,2,3,4,5`; exact `workflow_dispatch` inputs for
  run `27621106006` remain `NOT FOUND`.
- Risk: later manuscript work could mistake implementation mapping or workflow
  comments for verified Evaluation results or fully resolved Phase 3 run
  provenance.
- Resolution: use `ARCHITECTURE_NOTES.md` for Approach/Implementation mapping
  only. Evaluation notes must still cite primary CSV/JSON rows, verified
  GitHub Actions artifact paths, or derived chains with script hashes and exact
  commands. Resolve the Phase 3 dispatch-input question from GitHub metadata if
  available; otherwise keep it as `NOT FOUND`.
- Evidence: `CLM-S4A-001`, `CLM-S4A-004`, `CLM-S4A-005`, `CLM-S4A-006`, and
  `CLM-S4A-007`.
- Source locators:
  `local-sha256:647979c8cf7776031457a33258cfcb4a80e20c31b6c2349379611851ee56d25e:paper_notes/ARCHITECTURE_NOTES.md:L1-L149`;
  `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L46-L70`;
  `local-sha256:f681041d5fa9eee31746f6d938a5fc6c6c11d40f241bb2d6bb3be3238629df35:paper_notes/STAGE3_REFRESH_HANDOFF_20260617T080755Z.md:L33-L36`.

### GAP-033: Stage 5 Phase 1 methods reconstruction is not result extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 5 Phase 1 methods extraction observed at
  `2026-06-17T12:14:13.4273918Z`
- Observation: Stage 5 reconstructed clean-lab methods, treatments, controls,
  KG information, simulator physics, state/action spaces, scenarios,
  termination rules, Q-learning settings, rewards, and statistical-analysis
  plans. It did not extract final Phase 1 result CSV rows, compute effect sizes,
  compute statistical-test values, verify artifact ZIP byte identity for local
  Phase 1 result roots, or recover exact workflow_dispatch inputs for visible
  Phase 1 Actions runs.
- Risk: later manuscript work could cite Stage 5 methods notes as if they
  established Phase 1 empirical findings.
- Resolution: use `PHASE1_METHODS.md` for Methods and design provenance only.
  Evaluation claims still require primary CSV/JSON rows or derived chains with
  script hash and exact command.
- Evidence: `CLM-S5P1-001`, `CLM-S5P1-003`, `CLM-S5P1-004`,
  `CLM-S5P1-006`, and `CLM-S5P1-007`.
- Source locators:
  `local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L43-L45`;
  `local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L157-L161`;
  `local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L178-L187`.

### GAP-034: Lab3 bumped physics has stale magnitude documentation

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Phase 1 lab3 clean-lab methods source at
  `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1`
- Observation: the operational lab3 simulator uses bumped cross-zone values
  `150` and `0.40*sun`, while `building_3_complex.ttl` comments and
  `benchmark/scenarios_lab3.json` comments/initial state rows still contain
  pre-bump magnitude text or values such as `50` and `0.25*Sun`.
- Risk: a manuscript or figure could cite ontology/scenario comments as the
  final lab3 physics, conflicting with the simulator that actually ran.
- Resolution: use `simulator/simulator_flow_lab3.json` as the operational
  physics authority. Before using lab3 scenario initial levels as result
  evidence, verify row-level step logs from the selected run.
- Evidence: `CLM-S5P1-005`.
- Source locators:
  `local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L85-L89`;
  `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:simulator/simulator_flow_lab3.json:L5-L7`;
  `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:simulator/simulator_flow_lab3.json:L125-L130`;
  `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:src/resources/building_3_complex.ttl:L24-L31`;
  `kg-crosszone-coupling-bump@8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1:benchmark/scenarios_lab3.json:L1-L12`.
- Stage 6 update: this remains open. `PHASE1_RESULTS.md` uses selected result
  CSV rows and does not cite lab3 scenario initial-state rows or stale TTL/scenario
  magnitude text as result evidence.
- Stage 6 evidence:
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L124-L128`.

### GAP-035: Stage 6 Phase 1 result extraction has remaining provenance and resampling limits

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 6 Phase 1 result extraction observed at
  `2026-06-17T12:40:12.6739618Z`
- Observation: Stage 6 selected and extracted Phase 1 numeric evidence from
  local `phase1_xzone_*` roots and generated `PHASE1_TABLES.csv`. Local-root
  TREE-SHA256 hashes exist, but artifact ZIP byte identity remains `NOT VERIFIED`;
  exact `workflow_dispatch` inputs remain `NOT FOUND`; one failed ablation pre-run
  has live artifact/job counts `NOT FOUND` after unauthenticated GitHub API
  rate-limiting; and Stage 6 did not independently recompute bootstrap intervals,
  p-values, Wilcoxon values, Cliff's delta, or BH q-values.
- Risk: manuscript Evaluation could overstate provenance if it treats local roots
  as byte-identical Actions artifacts or treats analysis-CSV p/q fields as
  independently recomputed Stage 6 statistics.
- Resolution: before final archival release, authenticate GitHub CLI, re-download
  selected Phase 1 artifacts by run ID/artifact ID, verify ZIP digests and fresh
  extraction hashes, recover dispatch inputs if the API/logs expose them, and rerun
  or containerize the statistical analysis environment. Until then, cite Stage 6
  result values as derived from hashed local roots with explicit limitations.
- Evidence: `CLM-S6P1-001` through `CLM-S6P1-011`.
- Source locators:
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L118-L128`;
  `local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:L1-L12`;
  `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`;
  `local-sha256:0ba4c44ae05443c525fed6bf5c66ae582da6413178c149e263e8e56bf6242e61:paper_notes/PHASE1_ORIGIN_RESULTS_STAGE6.txt:L1-L79`.

### GAP-036: Stage 7 Phase 2 methods extraction has remaining run-provenance and statistical-verification limits

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 7 Phase 2 methods and implementation evidence extraction observed
  at `2026-06-17T13:10:41Z`
- Observation: Stage 7 created `paper_notes/PHASE2_METHODS.md` and verified
  Phase 2 clean pretraining, warm-load, fault scenarios, unexpected-behaviour
  detection, component attribution, blacklisting, warm restart, relearning,
  recovery criteria, goal-rate certification, and false-positive guards against
  committed source and selected v5 result-row locators. Artifact ZIP byte
  identity for `phase2-consolidated`, exact workflow_dispatch inputs for run
  `27547019772`, a complete v5 job inventory or aggregate-job row from the
  Stage 7 job snapshot, and independent resampling of Phase 2 bootstrap,
  Wilcoxon, Cliff's delta, and BH q-values remain unresolved.
- Risk: manuscript methods could overstate Phase 2 provenance if it treats the
  local or committed result tree as a byte-verified Actions artifact, treats
  workflow defaults as exact dispatch inputs, treats the partial job snapshot as
  complete, or treats analysis-CSV statistical fields as independently
  recomputed during Stage 7.
- Resolution: before final archival release, authenticate and capture full
  GitHub Actions run inputs/jobs/logs where available, download the
  `phase2-consolidated` artifact by ID `7647220538`, verify archive digest
  `sha256:8be79a29338d49ca54a869b6e610fbec2a7fc074cc375a74b1658344657ae102`,
  compare extracted file hashes to `origin/results@22a448be5d9829751badd341904e36ed582f091f`,
  and rerun or containerize `analysis/phase2_recovery.py` for independent
  statistical reproduction.
- Evidence: `CLM-S7P2-001` through `CLM-S7P2-006` once Stage 7 ledger rows are
  appended.
- Source locators:
  `local-sha256:4d200a0a2ba6e505c7df67e1069dc127710d6b946a697d4c7e1b8e3b8345e505:paper_notes/ACTIONS_SELECTED_RUNS_20260616T133627Z.csv:row 2`;
  `local-sha256:0e849b3f1501c74b1f4f7edc632e34d541ffdbb9875290ff64a356b31040d05c:paper_notes/ACTIONS_ARTIFACTS_20260616T133627Z.csv:row 101`;
  `local-sha256:303d147e2a5dd72c1bb3075fd0b0e7a9655df369a8e94dde6f41dcc232130f20:paper_notes/ACTIONS_JOBS_20260616T133627Z.csv:row 2`;
  `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19`;
  `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12`.
- Stage 8 update: complete v5 job inventory and aggregate-job proof are now
  resolved for run `27547019772`: Stage 8 captured `242` jobs, including
  `180` adapt jobs, `60` clean jobs, `1` aggregate job, and `1` compile job;
  aggregate job `81495756019` completed successfully. Evidence:
  `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:rows 3-8`;
  `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:rows 2-243`.
- Stage 8 remaining limitations: artifact ZIP byte identity is still NOT
  VERIFIED, exact workflow_dispatch inputs remain NOT FOUND, NumPy bootstrap
  CI/p-value resampling is not independently reproduced, and formal Phase 2
  preregistration remains NOT FOUND. Successor gap: `GAP-037`.

### GAP-037: Stage 8 Phase 2 result extraction has remaining artifact/input/bootstrap/preregistration limits

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 8 Phase 2 result evidence extraction observed at
  `2026-06-17T15:10:00Z`
- Observation: Stage 8 created `PHASE2_RESULTS.md`, `PHASE2_TABLES.csv`,
  `PHASE2_ACTIONS_STAGE8.csv`, and `PHASE2_ACTIONS_STAGE8_JOBS.csv`.
  It established v5 as the final Phase 2 result authority, verified final
  deterministic metrics from committed raw recovery rows, and independently
  checked Wilcoxon p-values, Cliff's delta, and BH q-values. It did not verify
  the `phase2-consolidated` artifact ZIP bytes, recover exact
  workflow_dispatch inputs, reproduce NumPy bootstrap CI/p-values, or find a
  formal Phase 2 preregistration.
- Risk: manuscript Evaluation could overstate provenance if it treats
  committed result rows as byte-verified artifact ZIP contents, treats workflow
  defaults as exact dispatch inputs, or treats bootstrap intervals/p-values as
  independently reproduced by Stage 8.
- Resolution: authenticate GitHub CLI or otherwise obtain the artifact archive
  by artifact ID `7647220538`, verify archive digest
  `sha256:8be79a29338d49ca54a869b6e610fbec2a7fc074cc375a74b1658344657ae102`,
  compare a fresh extraction with `origin/results@22a448be5d9829751badd341904e36ed582f091f`,
  recover dispatch inputs if exposed in logs/API, and rerun bootstrap
  resampling in a Python/NumPy environment matching the workflow.
- Evidence: `CLM-S8P2-001` through `CLM-S8P2-008` once Stage 8 ledger rows are
  appended.
- Source locators:
  `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L1-L133`;
  `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`;
  `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:L1-L10`;
  `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:L1-L243`.

### GAP-038: Stage 3R2 claim-model reconciliation is not empirical re-extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 3R2 research-question and claim-structure reconciliation observed
  at `2026-06-17T15:32:49.8337247Z`
- Observation: Stage 3R2 updates the research model and claim dependency map to
  reflect the hashed external advisor-note source, Stage 6 Phase 1 result-product
  availability, Stage 8 Phase 2 result-product availability, and implemented
  Phase 3 n10 routing. It does not execute a workflow, dispatch an experiment,
  compute new effect sizes, run statistical tests, or independently re-extract
  Stage 6/Stage 8 result values.
- Risk: manuscript notes could overstate Stage 3R2 as a result-validation stage
  rather than a claim-structure reconciliation stage, or could treat Stage 3R2's
  routing tables as primary numeric evidence.
- Resolution: for manuscript values, use Stage 6 Phase 1 rows/script/command,
  Stage 8 Phase 2 rows/script/command, and committed Phase 3 n10 result rows or
  later verified artifact downloads. Preserve GAP-001, GAP-035, GAP-037, and the
  Phase 3 dispatch-input/artifact-identity limitations.
- Evidence: `CLM-S3R2-001` through `CLM-S3R2-008` once Stage 3R2 ledger rows are
  appended.
- Source locators:
  `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L1-L26`;
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L1-L133`;
  `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`;
  `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L1-L133`;
  `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES.csv:L1-L522`;
  `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`;
  `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:L1-L5`;
  `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`.

### GAP-039: Stage 4R2 architecture refresh is not empirical re-extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 4R2 architecture and implementation source tracing observed at
  `2026-06-17T18:51:33Z`
- Observation: Stage 4R2 refreshes the architecture notes against the Stage3R2
  handoff bundle and creates R2 component/data-flow diagrams. It traces Phase 1,
  Phase 2, and Phase 3 code paths, marks older Stage 4 Phase 1/Phase 2
  pending-extraction routing as superseded by Stage 6/Stage 8 products, and
  documents the Phase 3 response-delay learning stack including `DynamicsLearner`,
  slow profiles, `taskDynamics`, `run_phase3_dynamics.ps1`, `phase3.yml`, and
  `analysis/phase3_dynamics.py`.
- Risk: manuscript notes could treat Stage 4R2 architecture/source tracing as a
  new empirical validation stage, or cite architecture notes for numeric result
  values instead of row-level Stage 6, Stage 8, or committed Phase 3 result rows.
- Resolution: use `ARCHITECTURE_NOTES.md` only for architecture and construct-to-code
  mapping. For manuscript values, cite Stage 6 Phase 1 extracted rows and command,
  Stage 8 Phase 2 extracted rows and command, or committed Phase 3 n10 analysis
  rows unless a later verified extraction supersedes them.
- Evidence: `CLM-S4R2A-001` through `CLM-S4R2A-006` once Stage 4R2 ledger rows are
  appended.
- Source locators:
  `local-sha256:a9c7575fa7eab03b3148db31cb9f1f63ac66007babc995adfca27d8f64c61472:paper_notes/ARCHITECTURE_NOTES.md:L153-L284`;
  `local-sha256:686cb1cf647d8fa1dd53f82aaf4fe26ef157f262839d386916587fd9ad97934e:paper_notes/ARCHITECTURE_COMPONENT_DIAGRAM_R2_20260617T185133Z.mmd:L1-L100`;
  `local-sha256:b34d62b3e15e44bf6acdf163203a3c2717465c2fb00e5780abd3fcb2b57ae2a9:paper_notes/ARCHITECTURE_DATAFLOW_DIAGRAM_R2_20260617T185133Z.mmd:L1-L67`;
  `local-sha256:4ee238a741e8a4ca7fd02b582d7c3602f84b77b76c2a0963fee275c2dde9bd18:paper_notes/STAGE4_R2_ARCHITECTURE_HANDOFF_20260617T185133Z.md:L1-L53`;
  `local-sha256:73ade353d433f46a5e8beaec51eb6e542abca16b5ece8f7aa7f9e0dd85d33263:paper_notes/RESEARCH_MODEL.md:L147-L165`;
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L1-L133`;
  `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L1-L133`;
  `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`.

### GAP-040: Stage 5R2 Phase 1 methods refresh is not a new result extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Scope: Stage 5R2 Phase 1 clean-lab methods refresh observed at
  `2026-06-18T07:37:03Z`
- Observation: Stage 5R2 appends a methods/routing addendum to
  `PHASE1_METHODS.md`, reconciling the prior Stage 5 method reconstruction with
  Stage 6 Phase 1 row-level result products, Stage3R2 claim routing, and Stage
  4R2 architecture routing. It marks the old Stage 5 "Phase 1 final numeric
  extraction pending" boundary as superseded by Stage 6 products.
- Risk: manuscript notes could cite the Stage 5R2 methods addendum as if it were
  a new empirical extraction, or could treat Stage 6 bootstrap intervals,
  p-values, Wilcoxon values, Cliff's delta, and BH q-values as independently
  resampled by Stage 5R2.
- Resolution: cite Stage 5R2 only for methods, audit history, and result-routing
  corrections. For Phase 1 numeric values, use Stage 6 row-level locators in
  `PHASE1_TABLES.csv` and the exact Stage 6 extractor command. Preserve the
  unresolved limits for formal post-pivot preregistration, exact dispatch
  inputs, artifact ZIP byte identity, Stage 6 resampling reproduction, lab3
  stale magnitude documentation, and the old `PHASE1_RESULTS.md` locator to the
  prior Stage 5 `PHASE1_METHODS.md` snapshot.
- Evidence: `CLM-S5P1R2-001` through `CLM-S5P1R2-005` once Stage 5R2 ledger rows
  are appended.
- Source locators:
  `local-sha256:b68dfdf6341ccb3fbf72e2706a7cf8dd04560e9518d1f1509d4caeca4b2f3523:paper_notes/PHASE1_METHODS.md:L228-L336`;
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L57-L58`;
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L102-L119`;
  `local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481`;
  `local-sha256:f9e158c2c5587bdbf433761f43a6bb1e48e5d6ca2b47970d95f1d6e1c1568624:paper_notes/phase1_extract_tables.mjs:L1-L520`;
  `local-sha256:440aa36d3121a1fda187368957c4125f2e2ed6d8802c6d8509cbc5982f586fa4:paper_notes/STAGE3_R2_HANDOFF_20260617T153249Z.md:L20-L29`;
  `local-sha256:4ee238a741e8a4ca7fd02b582d7c3602f84b77b76c2a0963fee275c2dde9bd18:paper_notes/STAGE4_R2_ARCHITECTURE_HANDOFF_20260617T185133Z.md:L17-L24`.

### GAP-041: Stage 6R2 Phase 1 result refresh is not a new statistical extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product: `AUDIT HISTORY`; `MANUSCRIPT EVIDENCE`
- Observation: Stage 6R2 created non-overwriting Phase 1 result, table-index,
  figure-specification, and git-audit artifacts; the Stage 6
  `PHASE1_TABLES.csv` remains the authoritative numeric result table. R2 did
  not independently resample confidence intervals, p-values, Wilcoxon values,
  Cliff's delta, or BH q-values; did not recover exact workflow_dispatch inputs;
  did not verify artifact ZIP byte identity; and did not resolve the lab3
  stale-magnitude documentation gap.
- Required action: Treat R2 artifacts as routing/index/specification evidence.
  Numeric manuscript claims must continue to cite Stage 6 row locators in
  `PHASE1_TABLES.csv` plus the Stage 6 extractor command, or the corresponding
  R2 index rows that themselves cite those Stage 6 rows.
- Evidence: `SRC-S6P1R2-001` through `SRC-S6P1R2-005` and
  `CLM-S6P1R2-001` through `CLM-S6P1R2-005` in the updated source and claim
  ledgers.
- Source locators:
  `local-sha256:5790b3132caa0143560c1ade1e20e450e30b0ed182cdd50cc86ab6ceb0f48cbd:paper_notes/PHASE1_RESULTS_R2_20260618T075201Z.md:L41-L57`;
  `local-sha256:a6004ae672bfbb32c746d907e4c1855ec54c540d98063c06d6339258411a06b0:paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv:L1-L15`;
  `local-sha256:d7ffc30e83ef10fca0e79f32ae66ce65eeb6e2a4a68c974cabde52ea4e576094:paper_notes/PHASE1_FIGURES_R2_20260618T075201Z.md:L1-L27`;
  `local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L102-L119`;
  `local-sha256:b68dfdf6341ccb3fbf72e2706a7cf8dd04560e9518d1f1509d4caeca4b2f3523:paper_notes/PHASE1_METHODS.md:L301-L307`.

### GAP-042: Stage 7R2 Phase 2 methods refresh is routing reconciliation, not empirical re-extraction

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product: `AUDIT HISTORY`; `MANUSCRIPT EVIDENCE`
- Observation: Stage 7R2 appended a non-overwriting routing refresh to
  `PHASE2_METHODS.md`. The refresh re-read the required R2 bundle, rechecked
  Phase 2 git chronology with read-only `git log` and `git diff --stat`
  commands, marked the original Stage 7 complete-job-inventory limitation as
  superseded by Stage 8 job evidence, and preserved the split between selected
  v5 method authority and Stage 8 result-row authority.
- Required action: Treat Stage 7R2 as a methods/routing addendum only. Numeric
  Phase 2 manuscript claims must continue to cite Stage 8 row-level sources in
  `PHASE2_TABLES.csv`, Stage 8 result notes in `PHASE2_RESULTS.md`, the
  Stage 8 extraction script, and the exact Stage 8 command.
- Remaining unresolved limits: Stage 7R2 did not dispatch a workflow, recover
  exact Phase 1 or Phase 2 `workflow_dispatch` inputs, verify artifact ZIP byte
  identity, independently reproduce Stage 6 Phase 1 resampling, independently
  reproduce Stage 8 Phase 2 NumPy bootstrap CI/bootstrap-p resampling, locate a
  formal post-pivot preregistration, resolve lab3 stale-magnitude
  documentation, or clear dirty-doc numeric-source limits.
- Evidence: `SRC-S7P2R2-001` through `SRC-S7P2R2-005` and
  `CLM-S7P2R2-001` through `CLM-S7P2R2-005` in the updated source and claim
  ledgers.
- Source locators:
  `local-sha256:29a0283decbc6967d15d72a2080722c314c035c343b8ff3ac4a44dcead113f9b:paper_notes/PHASE2_METHODS.md:L157-L232`;
  `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L43-L47`;
  `local-sha256:9558a5edb27b1a45c7968bf04ee23abf764085598045d98f5a9ab651d743cbd7:paper_notes/PHASE2_RESULTS.md:L102-L133`;
  `local-sha256:0c78a5971e1019354be336ed5dc84fac7c0db662ed78dee1718be678dc0aa058:paper_notes/PHASE2_ACTIONS_STAGE8.csv:rows 3-10, named columns recordType,key,value`;
  `local-sha256:8b80dd33ef399d80b14a16b49f63d9095a3e28a03abfc51974b275e33f389f96:paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv:rows 2-243, named columns runId,jobId,jobName,jobKind,jobStatus,jobConclusion`.

### GAP-043: Stage 8R2 Phase 2 results refresh is non-overwriting verification and figure specification, not new empirical execution

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product: `AUDIT HISTORY`; `MANUSCRIPT EVIDENCE`
- Observation: Stage 8R2 preserved the Stage 8 base `PHASE2_RESULTS.md` and
  `PHASE2_TABLES.csv`, generated a byte-identical duplicate extraction
  `PHASE2_TABLES_R2_20260618T090000Z.csv`, created the missing standalone
  `PHASE2_FIGURES.md`, and created
  `PHASE2_RESULTS_R2_20260618T090000Z.md` plus a read-only git audit snapshot.
  It did not dispatch a workflow, produce new experimental data, verify artifact
  ZIP bytes, recover exact dispatch inputs, or reproduce NumPy bootstrap
  resampling.
- Evidence: `SRC-S8P2R2-001` through `SRC-S8P2R2-005` and
  `CLM-S8P2R2-001` through `CLM-S8P2R2-007` once Stage 8R2 ledger rows are
  appended.
- Source locators:
  `local-sha256:c6387763f14c05d1a9ea0cf1fcaf97006f7129b56d71bc140c21e90187fdd681:paper_notes/PHASE2_RESULTS_R2_20260618T090000Z.md:L1-L144`;
  `local-sha256:bc961fae6f9f4420a15c6442a2b92851bdd0e44357832868bc39d289d84350df:paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv:L1-L522`;
  `local-sha256:3d080caceafb1580846f350bdee1b7a7b4b2290c73250ab3bda3315bbc229711:paper_notes/PHASE2_FIGURES.md:L1-L34`;
  `local-sha256:54bc472e7fa3ecdcbe15e2743ded077e196056cdbe373b78abc325464a03429c:paper_notes/PHASE2_GIT_AUDIT_R2_20260618T090000Z.txt:L1-L32`.
- Remaining unresolved limits: exact Phase 1/Phase 2 `workflow_dispatch` input
  payloads remain `NOT FOUND`; Phase 1/Phase 2 artifact ZIP byte identity
  remains not verified; Stage 6 Phase 1 and Stage 8 Phase 2 bootstrap
  resampling remain not independently reproduced; formal post-pivot
  preregistration remains `NOT FOUND`; lab3 stale-magnitude documentation and
  dirty-doc numeric-source limits remain active.
- Required action: use Stage 8/8R2 row-level products for Phase 2 numeric
  manuscript notes, but preserve the unresolved labels above until direct
  evidence closes them.

### GAP-044: Stage 9 statistical integrity audit separates deterministic checks from unresolved resampling

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product: `AUDIT HISTORY`; `MANUSCRIPT EVIDENCE`
- Observation: Stage 9 created a non-experimental statistical-integrity audit
  table and git audit snapshot. It confirms that Phase 2 deterministic/exact
  checks and Phase 1 deterministic mean/mean-difference checks have no failed
  rows in the Stage 9 input tables, while Phase 1 and Phase 2 bootstrap
  resampling remains not independently reproduced.
- Evidence: `paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md`;
  `paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv`;
  `paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt`; Stage 9 source, claim,
  and run ledger rows once appended.
- Source locators:
  `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L1-L117`;
  `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:L1-L22`;
  `local-sha256:698680a425a28a7c5f7e854f69b33772bf34c17fdf79da2db980f2f3b4f56ef4:paper_notes/STAGE9_GIT_AUDIT_20260618T092847Z.txt:L1-L30`.
- Remaining unresolved limits: exact Phase 1/Phase 2 `workflow_dispatch` input
  payloads remain `NOT FOUND`; Phase 1/Phase 2 artifact ZIP byte identity
  remains not verified; Stage 6 Phase 1 and Stage 8 Phase 2 bootstrap
  resampling remain not independently reproduced; formal post-pivot
  preregistration remains `NOT FOUND`; lab3 stale-magnitude documentation and
  dirty-doc numeric-source limits remain active.
- Supersession boundary: the older v5 job-inventory limitation remains
  superseded and is not reopened; remaining workflow provenance gaps are
  dispatch inputs and artifact ZIP identity.

### GAP-045: Stage 10A Phase 3 authority candidate keeps provenance and preregistration limits visible

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product: `AUDIT HISTORY`; `MANUSCRIPT EVIDENCE`
- Observation: Stage 10A treats Phase 3 GitHub Actions run `27621106006`
  as the n=10 authority candidate because its artifact metadata, committed
  `origin/results` CSVs, local extracted tree, raw CSV row counts, and
  recomputation checks agree. The exact `workflow_dispatch` input payload is
  still `NOT FOUND`, the local extracted artifact tree is not ZIP-byte-verified
  against the GitHub artifact digest, and formal post-pivot preregistration
  remains `NOT FOUND`. The run-head workflow default still lists five replicas;
  the ten-replica status is therefore supported by artifacts and raw result
  directories rather than by the run-head default.
- Evidence: `paper_notes/PHASE3_METHODS.md`;
  `paper_notes/PHASE3_RESULTS.md`; `paper_notes/PHASE3_TABLES.csv`;
  `paper_notes/PHASE3_FIGURES.md`; Stage 10A source, claim, and run ledger
  rows once appended.
- Source locators:
  `local-sha256:6f52ebe57ffbbc85fccd28e495538129b086d94c3483f594bb2daf6e5d9ac0ee:paper_notes/PHASE3_METHODS.md:L1-L75`;
  `local-sha256:4c823e93e6d5306ea273508e2420b4b8b5380eace9f48c5e8c7d7bc4eb676f56:paper_notes/PHASE3_RESULTS.md:L1-L121`;
  `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:L1-L36`;
  `local-sha256:d8e7b1953499f3e0a951d1c85c5b3dcb0128285c7f0bb38783680ed76dc778dd:paper_notes/PHASE3_FIGURES.md:L1-L25`;
  GitHub Actions: workflow=`Phase 3 (process dynamics, response-delay learning)`;
  run ID=`27621106006`;
  URL=`https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/27621106006`;
  head SHA=`3bb5289c36cb3093228ec0609fe57ec676b1ee53`;
  job=`Aggregate dynamics & publish`;
  job ID=`81670617760`;
  artifact=`phase3-consolidated`;
  artifact ID=`7668397627`;
  artifact digest=`sha256:a882677d1689d2f25470591771fd1ef80035de560e837e9ab01857381e9f9416`;
  `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`.
- Remaining unresolved limits: exact Phase 3 `workflow_dispatch` input payload
  remains `NOT FOUND`; Phase 3 local artifact ZIP byte identity remains not
  verified; formal post-pivot preregistration remains `NOT FOUND`; Stage 9
  carried Phase 1/Phase 2 provenance and resampling gaps remain open.
- Required action: use `origin/results` run `27621106006` plus
  `PHASE3_TABLES.csv` rows `P3T-008` through `P3T-033` as Phase 3 result
  authority, keep the unresolved labels above in manuscript notes, and do not
  cite dirty documentation as a primary numeric source.

### GAP-046: Stage 10B related-work bibliography is primary-source scoped but full-text limited

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product scope: `AUDIT_HISTORY;MANUSCRIPT_EVIDENCE`
- Observation: Stage 10B produced related-work notes and a bibliographic ledger
  using primary academic DOI, venue, publisher, arXiv, and Crossref metadata
  records. Rows with DOI-only Crossref verification were not expanded into
  full-text article audits; therefore Stage 10B can support bibliographic
  positioning and coarse conceptual mapping, but not fine-grained claims about
  method internals beyond the recorded source abstracts/metadata.
- Evidence records:
  `paper_notes/RELATED_WORK_NOTES.md`;
  `paper_notes/BIBLIOGRAPHIC_LEDGER.csv`;
  Stage 10B source, claim, and run ledger rows once appended.
- Source locators:
  `local-sha256:2d3a6860a0c3cbc43d98688f9ffbadf1008d05de7946718e62cb960913e3804e:paper_notes/RELATED_WORK_NOTES.md:L1-L143`;
  `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:L1-L18`;
  `paper_notes/BIBLIOGRAPHIC_LEDGER.csv:rows 2-18; named columns bib_id,topic_bucket,evidence_label,source_type,primary_status,title,year,venue,doi,arxiv_id,url,source_locator,source_status,project_mapping,notes`.
- Remaining unresolved limits: full-text article locators were not obtained for
  DOI-only Crossref rows; PhysQ DOI remained `NOT FOUND`; SOSA DOI remained
  `NOT VERIFIED`; the wrong Brick DOI candidate
  `10.1016/j.apenergy.2017.10.091` is preserved as `[SUPERSEDED]` rather than
  reused. All Stage 10A carry-forward gaps remain unchanged: exact Phase 3
  `workflow_dispatch` input payload `NOT FOUND`, Phase 3 local ZIP byte
  identity `NOT VERIFIED`, formal post-pivot preregistration `NOT FOUND`, and
  Stage 9 Phase 1/Phase 2 provenance and bootstrap-resampling gaps remain open.
- Required action: before using Stage 10B for polished related-work prose, either
  retain the current coarse mapping labels or conduct targeted full-text audits
  for the specific papers whose method details are needed.

### GAP-047: Stage 11 template-population notes are evidence-routing products, not manuscript prose

- Status: `OPEN`
- Label: `[UNRESOLVED]`
- Product scope: `AUDIT_HISTORY;MANUSCRIPT_EVIDENCE`
- Scope: Stage 11 template-population and final-audit pass.
- Observation: Stage 11 produced `paper_notes/PAPER_SECTION_NOTES.md` and
  `paper_notes/APPENDIX_NOTES.md`, plus a compact read-only git audit at
  `paper_notes/STAGE11_GIT_AUDIT_20260618T112457Z.txt`. The notes route
  verified Phase 1, Phase 2, Phase 3, statistical-audit, and related-work
  material into the exact thesis-template destinations. They are detailed bullet
  notes, tables, figure specifications, and evidence records, not polished
  thesis prose.
- Evidence:
  `local-sha256:0f37cff3bbe7c40ee38d14fd855f9e31177832204c21a713b52fd3d9e03e09e9:paper_notes/PAPER_SECTION_NOTES.md:L1-L213`;
  `local-sha256:8ec60da54c73b48a9f1935ca7cd4dd94ae05592312ed02f7b8bb63790abf1e18:paper_notes/APPENDIX_NOTES.md:L1-L127`;
  `local-sha256:bc550ccaf4706201eba851203a59b176af5b1f70f63fae5cee379ce32923eeb4:paper_notes/STAGE11_GIT_AUDIT_20260618T112457Z.txt:L1-L66`.
- Remaining unresolved limits: Stage 11 did not edit the thesis template, render
  figures, re-run experimental workflows, redownload or byte-verify artifact
  ZIPs, recover workflow_dispatch input payloads, perform independent bootstrap
  resampling, or find a formal post-pivot preregistration. Phase 3 is routed as
  an evaluated contribution using the n10 authority candidate, while Phase 3.x
  extensions remain limitations/future work.
- Risk: polished manuscript writing could accidentally treat Stage 11 routing
  notes as prose, promote post-hoc/engineering-validation evidence to
  preregistered confirmatory evidence, or omit active provenance/statistical
  caveats.
- Required action: before writing final prose, read `PAPER_SECTION_NOTES.md`,
  `APPENDIX_NOTES.md`, the ledgers, and the cited Phase 1/2/3 row-level sources;
  preserve evidence labels and unresolved placeholders until the corresponding
  gaps are actually resolved.

## Closed Gaps

### GAP-022: Stage 2 capture normalization defects

- Status: `CLOSED`
- Label: `[SUPERSEDED]`
- Observation: the first normalized Actions CSV collapsed the API array into one
  `System.Object[]` row, and an intermediate Git audit truncated scalar ref output.
- Evidence: `SRC-S2-013`, `SRC-S2-014`, and `CLM-S2-010`.
- Resolution: both invalid artifacts and the invalid run-ledger row were preserved
  and labeled superseded; corrected successors are `SRC-S2-003` and `SRC-S2-004`.

### GAP-006: v4 Phase 2 result root ingested

- Status: `CLOSED_WITH_LIMITATION`
- Label: `[DIRECT]` and `[DERIVED]`
- Evidence: `SRC-0041`, `SRC-0042`, `SRC-0043`, `SRC-R013`, and claims
  `CLM-S0-013` through `CLM-S0-015`.
- Resolution: job and artifact metadata were captured; `phase2_results_v4` was
  canonically hashed and mapped to run `27529585379`.
- Remaining limitation: byte identity to the artifact ZIP remains open under
  `GAP-002`; later Phase 2 v5 authority is recorded under `GAP-012`.

### GAP-014: Initial tree hashes used native separators

- Status: `CLOSED`
- Label: `[SUPERSEDED]` and `[DERIVED]`
- Evidence: `CLM-S0-012`, `SRC-0039`, superseded source rows, and their `-R1`
  successors.
- Resolution: the initial nested-root hashes were reproduced with
  `--legacy-native-separators`, proving the implementation used Windows `\`
  paths contrary to the protocol. Canonical `/`-normalized replacement hashes
  were added without deleting the original audit records.
