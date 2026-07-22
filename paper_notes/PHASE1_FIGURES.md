# Phase 1 Figure Specifications

Evidence-extraction product only. These are figure build specs, not rendered
figures and not manuscript prose.

## Source Anchors

| Source id | Label | Source locator |
|---|---|---|
| S6P1-FIG-TABLES | [DERIVED] | local-sha256:368dc5acf4b6f9ed10d53df5a710178874ffa697cb38aef7a1d460c2a6909b2a:paper_notes/PHASE1_TABLES.csv:L1-L481 |
| S6P1-FIG-RESULTS | [DERIVED] | local-sha256:d0a73998b4bf4a46d78ae7525746908c77474865c33adf704d3c1ee329f03282:paper_notes/PHASE1_RESULTS.md:L1-L133 |
| S6P1-FIG-ACTIONS | [DIRECT] | local-sha256:6cf280d4099567023566ea7806d0a4b389dc2840f79af291825659c58f209604:paper_notes/PHASE1_ACTIONS_STAGE6.csv:L1-L12 |
| S6P1-FIG-METHODS | [DIRECT] | local-sha256:4cc2648fa5a08e9a12fa275cbbc3e8d0072a7da43f22751f6914d0725a8a7505:paper_notes/PHASE1_METHODS.md:L47-L151 |

## Figure Specs

| Figure id | Label | Product scope | Intended use | Required data rows | Required visual elements | Exclusions/caveats |
|---|---|---|---|---|---|---|
| FIG-P1-RES-1 | [DIRECT] | MANUSCRIPT EVIDENCE | Lab2 anchor summary. | EV-P1-RES-001 through EV-P1-RES-006 in `PHASE1_RESULTS.md`; PHASE1_TABLES rows `186`, `189`, `204`, `210`, `330`, `331`. | Forest/point estimate plot with CI bars for `auc_goal`, `avg_steps`, `avg_redundant`, `goal_rate`, and replication `auc_goal`/`auc_reward`; color higher-better and lower-better metrics distinctly; annotate q-values from the table rows. | Do not call this formally pre-registered; label `POST_HOC_EXPLORATORY`. Do not omit `goal_rate` because it supports equal-or-better success. |
| FIG-P1-RES-2 | [SUPERSEDED; DIRECT] | AUDIT HISTORY; optional MANUSCRIPT EVIDENCE as control | Lab3 as-is versus bumped A/B. | PHASE1_TABLES rows `82`, `94`, `202`, `214`, `215`; optionally row `335` for replication reward. | Two-panel contrast: panel A `auc_goal` as-is/bumped; panel B `avg_cycling` as-is/bumped; optional panel C `auc_reward` bumped and replication. Use labels `as-is control` and `bumped targeted`. | The as-is result is superseded for final lab3 performance claims but remains the A/B control. Do not plot stale TTL/scenario magnitude comments as physics values. |
| FIG-P1-RES-3 | [DIRECT] | MANUSCRIPT EVIDENCE | Lab3 mechanism ablation. | PHASE1_TABLES rows `215`, `454`, `455`; compare targeted row `215` with untargeted row `455`. | Bar or point+CI comparison for lab3 `auc_reward` targeted versus untargeted; small secondary marker for untargeted `auc_goal`. | Do not compute or display a retained-benefit percentage unless a separate derived row with exact command is added. |
| FIG-P1-RES-4 | [DIRECT] | AUDIT HISTORY | Phase 1 provenance and supersession map. | PHASE1_ACTIONS_STAGE6 rows `2` through `12`; GIT_AUDIT locators in `PHASE1_RESULTS.md`; PHASE1_ORIGIN_RESULTS_STAGE6 lines `1` through `79`. | Timeline or swimlane: initial main clean-lab/factorial runs, as-is control, bumped primary, bumped replication, failed ablation pre-run, successful ablation; distinguish `origin/results` baseline from local hashed roots. | Keep in audit appendix unless needed to explain result authority. Do not use chronology as a scientific finding. |
| FIG-P1-RES-5 | [UNRESOLVED] | MANUSCRIPT EVIDENCE limitations | Result-source limitations panel. | PHASE1_ACTIONS_STAGE6 rows `2` through `12`; PHASE1_RESULTS evidence record EV-P1-RESULT-005. | Compact provenance badges: dispatch inputs `NOT FOUND`; artifact ZIP byte identity `NOT VERIFIED`; deterministic means recomputed from raw CSV; resampling statistics sourced from analysis CSV. | Do not imply artifact archive bytes were downloaded or compared. |

## Table Specs For Manuscript Drafting

| Table id | Label | Required fields | Source rows |
|---|---|---|---|
| TAB-P1-RES-1 | [DIRECT] | Active Phase 1 result-set authority: root, run, branch, head SHA, role, label, local tree hash, artifact/job count, unresolved provenance fields. | `PHASE1_RESULTS.md` Result-Set Authority table; PHASE1_ACTIONS_STAGE6 rows `8` through `12`; STAGE0_LOCAL_TREE_HASHES rows `5` through `8`. |
| TAB-P1-RES-2 | [DIRECT] | Lab2 primary and replication outcomes: metric, direction, value, CI, q, Cliff's delta, recompute status, source locator. | PHASE1_TABLES rows `186`, `189`, `204`, `210`, `330`, `331`. |
| TAB-P1-RES-3 | [DIRECT; SUPERSEDED controls included] | Lab3 as-is/bumped/replication/ablation outcomes: metric, value, CI, q, label, manuscript handling. | PHASE1_TABLES rows `82`, `94`, `202`, `214`, `215`, `335`, `454`, `455`. |

## Handoff

Next figure-building stage must read:

1. `paper_notes/PHASE1_RESULTS.md`
2. `paper_notes/PHASE1_TABLES.csv`
3. `paper_notes/PHASE1_ACTIONS_STAGE6.csv`
4. `paper_notes/PHASE1_METHODS.md`
5. `paper_notes/EVIDENCE_GAPS.md`
