# Stage 1 Repository Evidence Map

## Stage 1 Refresh 2 - Stage 0R2 Reconciliation

This section is the current Stage 1 routing authority after the Stage 0 refresh
observed at `2026-06-17T06:51:11.3582240Z`. The older Stage 1 refresh and
Stage 4 inventory sections below remain AUDIT HISTORY.

- [DIRECT] Current committed repository anchor: branch
  `phase3-process-dynamics`, HEAD
  `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`, upstream
  `origin/phase3-process-dynamics`, divergence `+1/-0`.
  Locator:
  `local-sha256:cb539c624bb31ce1e1b6b940d9a7a5182614e9b6563a37b0418304ddb6600ffa:paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md:L5-L15`.
- [DIRECT] Current local-worktree boundary at the Stage 0R2 observation:
  `0` staged tracked changes, `2` unstaged tracked changes, `2343` normal
  untracked files across `26` top-level paths, `19243` ignored files across
  `226` top-level paths, and a `.pytest_cache` permission warning.
  Locator:
  `local-sha256:cb539c624bb31ce1e1b6b940d9a7a5182614e9b6563a37b0418304ddb6600ffa:paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md:L16-L31`.
- [DIRECT] Current local inventory basis: Stage 0R2 hashed `29` local
  result/result-like/runtime roots and `15` individual files; no experimental
  result values, effect sizes, statistical tests, workflow dispatch, or
  experimental run were analyzed in that refresh.
  Locators:
  `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 2-30; named columns path,path_kind,provenance_class,verification_status,content_hash,file_count,byte_count,limitations`;
  `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 2-16; named columns path,path_kind,git_state,provenance_class,sha256,byte_count,line_count,limitations`;
  `local-sha256:f62721f9d6c23dc70fc1372b95bb1dbdb87751c08605bcfd2677d3dabb665035:paper_notes/STAGE0_REFRESH_HANDOFF_20260617T065111Z.md:L5-L8`.

### Stage 0R2 Evidence-Root Routing

| Root group | Current Stage 1 routing | Product scope | Locator |
|---|---|---|---|
| `analysis/out_full`, `analysis/out_kg_only`, `benchmark/results_full_seed1` | Local generated or accumulated outputs with missing unified run identity; exclude from manuscript evidence until primary run/command tracing exists | AUDIT HISTORY | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 2-4; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations` |
| `phase1_xzone_asis`, `phase1_xzone_bumped`, `phase1_xzone_bumped_s11_20`, `phase1_xzone_ablation` | Candidate Phase 1 evidence roots after row-level extraction; local tree hashes do not verify ZIP byte identity | MANUSCRIPT EVIDENCE candidate; AUDIT HISTORY until extraction | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 5-8; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations` |
| `phase2_results`, `phase2_results_v2`, `phase2_results_v3`, `phase2_results_v4`, `phase2_results_v5` | `phase2_results_v5` is the latest local Phase 2 candidate; earlier Phase 2 roots are audit/correction history unless explicitly cited for superseded findings | MANUSCRIPT EVIDENCE candidate for v5; AUDIT HISTORY for earlier roots | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 9-13; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,classification_basis,limitations`; committed result row source: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19` |
| `phase3_download`, `phase3_download_n10` | `phase3_download_n10` is the latest local Phase 3 candidate; `phase3_download` is superseded for final inference by run `27621106006`; local roots remain not ZIP-byte-verified | MANUSCRIPT EVIDENCE candidate for n10 via committed rows; AUDIT HISTORY for superseded n5 | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 14-15; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,classification_basis,limitations`; committed result row source: `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9` |
| `tmp_sweep18_results`, `tmp_sweep_n10_results`, `tmp_paper_results`, `tmp_step0_*`, `tmp_step2_validation` | Pre-pivot, mixed, unknown-provenance, or local probe roots; keep audit-only unless a later stage reconstructs exact code/run/command relevance | AUDIT HISTORY | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 16-24; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,classification_basis,limitations` |
| `.node-red-lab1`, `.node-red-lab2`, `.node-red-lab2_f1dead`, `.node-red-lab2_slow`, `.node-red-lab3`, `.node-red-lab3_slow` | Runtime directories only; prefer committed simulator flows and run-scoped result artifacts for manuscript evidence | AUDIT HISTORY | `local-sha256:1b7f33abac94f48649560fbf48fab7b09fd3aaaf4c873bd3e673770231e19e67:paper_notes/STAGE0_LOCAL_TREE_HASHES_20260617T065111Z.csv:rows 25-30; named columns path,path_kind,provenance_class,verification_status,content_hash,file_count,byte_count,limitations` |
| Dirty docs: `docs/PHASE1_TO_PHASE2_CHANGES.md`, `docs/PHASE2_TO_PHASE3_CHANGES.md` | Stage-specific documentation and leads only; empirical prose and numbers require primary CSV/JSON/Actions/result-branch extraction before manuscript use | AUDIT HISTORY; MANUSCRIPT EVIDENCE only after verification | `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 2-3; named columns path,git_state,sha256,byte_count,line_count,limitations` |
| Root-level Phase 3 runtime CSV/TTL files | Local generated files with exact command/run/artifact identity `NOT FOUND`; prefer run-scoped Actions or `origin/results` copies | AUDIT HISTORY | `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 5-16; named columns path,path_kind,git_state,provenance_class,sha256,byte_count,line_count,limitations` |

### Stage 0R2 Manuscript Routing

| Manuscript section | Evidence categories to route | Boundary |
|---|---|---|
| Introduction | Requirement/pivot sources, final research problem, and scoped three-phase trajectory | Do not import branch chronology or dirty-doc empirical numbers without primary-source extraction |
| Background | MAS/JaCaMo, Q-learning, Semantic Web/KG, RDF/Turtle, WoT/BRICK, stereotypes, process-dynamics foundations | External literature still requires source-ledger entries before citation |
| Contributions | Clean-lab ladder, semantic prior mechanism, cross-zone structural prior, Phase 2 expected-vs-actual detection/blacklist/re-learning, Phase 3 response-delay learning and KG writeback | Separate conceptual approach from implementation details |
| Evaluation | Experiment records, baselines/treatments, variables/controls, scenarios, seeds/replicas, metrics, statistical scripts, selected run IDs, committed result rows | Every numeric result must cite CSV/JSON/Actions rows or a complete derived chain |
| Conclusions | Final active claim-ledger rows, limitations, and bounded future work | Superseded findings remain AUDIT HISTORY |
| Abstract | Problem, method, principal supported result slots, strongest limitation | Fill last; Stage 1 inventory claims are not abstract content |
| Appendix | Reproduction commands, workflow/run/artifact provenance, profile/config matrices, schemas, full tables/figures, audit index | Dependencies, caches, build products, and runtime directories stay excluded unless uniquely evidentiary |

### Stage 0R2 Current Exclusion Decisions

| Area | Decision | Locator |
|---|---|---|
| Dependencies, caches, ordinary build products, and unreadable `.pytest_cache` contents | Exclude unless a later stage identifies unique run evidence; `.pytest_cache` access remained limited by a permission warning | `local-sha256:cb539c624bb31ce1e1b6b940d9a7a5182614e9b6563a37b0418304ddb6600ffa:paper_notes/STAGE0_WORKTREE_STATUS_20260617T065111Z.md:L29-L31` |
| Artifact ZIP byte identity for local result roots | `OPEN` unresolved; local tree hashes identify current local bytes only | `local-sha256:f62721f9d6c23dc70fc1372b95bb1dbdb87751c08605bcfd2677d3dabb665035:paper_notes/STAGE0_REFRESH_HANDOFF_20260617T065111Z.md:L29-L33`; `local-sha256:96394472cd5f8380c46f3cba083468e6cd172070fc95a3e23a6ee51fc65e2dd1:paper_notes/EVIDENCE_GAPS.md:L399-L414` |
| Root-level Phase 3 runtime files | `OPEN` unresolved for exact command, run, and artifact identity | `local-sha256:f62721f9d6c23dc70fc1372b95bb1dbdb87751c08605bcfd2677d3dabb665035:paper_notes/STAGE0_REFRESH_HANDOFF_20260617T065111Z.md:L33-L36`; `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 5-16; named columns path,path_kind,provenance_class,sha256,limitations` |
| Dirty stage-specific documentation | Documentation-only until every empirical claim and numeric value is checked against primary CSV/JSON/Actions/committed result sources | `local-sha256:532bb1b786ad6b794706277f228302d12664faa33cc371039a84247db086bdeb:paper_notes/STAGE0_FILE_HASHES_20260617T065111Z.csv:rows 2-3; named columns path,git_state,sha256,line_count,limitations` |

## Stage 1 Refresh - Current Repository Map

This section is the current Stage 1 routing authority for the
`phase3-process-dynamics` checkout. The older Stage 1 map below is preserved as
AUDIT HISTORY, including its now-superseded Phase 3 `NOT FOUND` observation.

- [DIRECT] Refresh snapshot: branch `phase3-process-dynamics`, HEAD
  `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`, ahead of
  `origin/phase3-process-dynamics` by `1` local commit, with dirty tracked
  documentation files `docs/PHASE1_TO_PHASE2_CHANGES.md` and
  `docs/PHASE2_TO_PHASE3_CHANGES.md` before note edits.
  Locator:
  `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L3-L11`.
- [DIRECT] Stage 1 remains inventory-only; result values, effect sizes,
  hypothesis verdicts, and headline findings are not selected in this refresh.
  Locator:
  `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L14`.
- [DIRECT] No branch switch, reset, clean, deletion, artifact overwrite, or
  experimental run was performed during this Stage 1 refresh.
  Locator:
  `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L15-L28`.

### Current Evidence-Bearing Directory Map

| Path / source category | Evidence role | Product scope | Manuscript routing | Immutable locator |
|---|---|---|---|---|
| `src/agt/lab_profiles.asl` | Lab-profile registry; clean ladder; slow Phase 3 ladder; faulty Phase 2 ladder and clean-source mapping | MANUSCRIPT EVIDENCE; AUDIT HISTORY for chronology | Introduction scope; Contributions lab design; Evaluation variables/controls; Appendix profile matrix | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L1-L27`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L242-L345`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L347-L534` |
| `config/run_config.json` | Runtime profile arms, Phase 1 clean-run parameters, Phase 2 adaptation matrix, Phase 3 dynamics matrix | MANUSCRIPT EVIDENCE | Evaluation design; Appendix reproducibility table | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:config/run_config.json:L49-L163`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:config/run_config.json:L250-L357` |
| `src/env/tools/QLearner.java` | Tabular Q-learning, ontology/stereotype prior use, Phase 2 Expected-vs-Actual detector, blacklist, warm restart, and recovery logic | MANUSCRIPT EVIDENCE | Contributions mechanism; Evaluation method; Appendix implementation detail | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/QLearner.java:L229-L293`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/QLearner.java:L932-L1248`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/QLearner.java:L1509-L1538`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/QLearner.java:L2182-L2205` |
| `src/env/tools/DynamicsLearner.java` and `src/agt/illuminance_controller_agent_dynamics.asl` | Phase 3 response-delay sampling, Welford aggregation, KG writeback, and deadline-aware exploitation agent | MANUSCRIPT EVIDENCE | Contributions Phase 3 approach; Evaluation Phase 3 method; Appendix implementation map | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/DynamicsLearner.java:L13-L60`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/env/tools/DynamicsLearner.java:L165-L230`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/illuminance_controller_agent_dynamics.asl:L1-L83` |
| `src/env/tools/StereotypeReasoner.java`, `OntologyArtifact.java`, `StereotypeLearner.java`, `src/resources/` | Semantic Web / ontology reasoning, action metadata, learned effect serialization, building resources, WoT mappings | MANUSCRIPT EVIDENCE | Background foundations; Contributions semantic-RL bridge; Appendix ontology/resource map | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L10-L23`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L242-L345` |
| `simulator/` | Canonical Node-RED flow files and generators for clean, faulty, weakness, and slow dynamics environments | MANUSCRIPT EVIDENCE | Contributions testbed; Evaluation treatments/controls; Appendix flow map | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:simulator/generate_faulty_flows.ps1:L16-L68`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:config/run_config.json:L266-L286`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:config/run_config.json:L333-L340` |
| `benchmark/*.json` | Training and held-out scenario definitions referenced by profiles | MANUSCRIPT EVIDENCE | Evaluation scenario definitions; Appendix scenario inventory | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L263-L295`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:src/agt/lab_profiles.asl:L371-L519` |
| `.github/workflows/phase1.yml` | Phase 1 matrix execution, training/benchmark artifacts, multi-seed reconstruction, analysis, and publication | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run identity | Evaluation reproducibility; Appendix workflow/run table | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase1.yml:L1-L35`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase1.yml:L114-L123`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase1.yml:L501-L568` |
| `.github/workflows/phase2.yml` | Phase 2 clean warm-start and adaptation matrices, analysis, consolidated artifacts | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run identity | Evaluation reproducibility; Appendix workflow/run table | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase2.yml:L1-L125`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase2.yml:L250-L390` |
| `.github/workflows/phase3.yml` | Phase 3 response-delay workflow, matrix, artifact upload, aggregation, summary, and results-branch publication | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run identity | Evaluation reproducibility; Appendix workflow/run table | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L1-L70`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L185-L213`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L241-L306`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L326-L338` |
| `run_full_project_parallel.ps1`, `run_phase2_adapt.ps1`, `run_phase3_dynamics.ps1`, `build.gradle`, `task*.jcm` | Local execution entry points for training, benchmark, adaptation, dynamics, and Gradle/JaCaMo task wiring | AUDIT HISTORY; MANUSCRIPT EVIDENCE for reproducibility | Appendix commands; Evaluation execution boundary | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:run_full_project_parallel.ps1:L102-L121`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:run_full_project_parallel.ps1:L572-L574`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:run_phase2_adapt.ps1:L1-L49`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:run_phase3_dynamics.ps1:L1-L55`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:run_phase3_dynamics.ps1:L220-L315`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:build.gradle:L198-L243`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:task_dynamics.jcm:L2-L18` |
| `analysis/sweep_report.py`, `analysis/phase2_recovery.py`, `analysis/phase3_dynamics.py` | Statistical aggregation, bootstrap CIs, paired tests, Wilcoxon, Cliff's delta, BH-FDR, result tables | MANUSCRIPT EVIDENCE after derived-chain verification | Evaluation statistical methods; Figures/tables; Appendix commands | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/sweep_report.py:L281-L405`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/sweep_report.py:L633-L1075`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/phase2_recovery.py:L1-L43`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/phase2_recovery.py:L202-L316`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/phase3_dynamics.py:L1-L55`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:analysis/phase3_dynamics.py:L333-L463` |
| `scripts/version_artifacts.ps1` and results branch snapshots | Result publication and run manifest pipeline | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run provenance | Appendix provenance pipeline | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:scripts/version_artifacts.ps1:L9-L18`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:scripts/version_artifacts.ps1:L94-L108`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9` |
| `docs/` | Pivot/change chronology, preregistration search leads, result notes, meeting notes | AUDIT HISTORY by default; manuscript use only after primary-source verification | Introduction requirements; Evaluation planning; Discussion limitations | Dirty docs: `local-sha256:0d30b28c54c818173f40e817480682d62c67b267bfbf018d6dd9233ee311a4e4:docs/PHASE2_TO_PHASE3_CHANGES.md:L1-L709`; `local-sha256:6885096decf6080cafec4f2c17f01197d18e7e400bc0fa5ccb9c6b0e65136943:docs/PHASE1_TO_PHASE2_CHANGES.md:L1-L1579`; committed preregistration: `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:docs/pre_registration.md:L1-L138` |
| `dashboard/` | Demonstration and trace visualization application | MANUSCRIPT EVIDENCE only for demonstration, not statistical claims | Contributions demonstration; Appendix/demo assets | `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:dashboard/README.md:L1-L80`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:dashboard/src/App.jsx:L1-L111` |
| `paper_notes/` | Protocol, ledgers, chronology, research model, maps, handoffs, Actions captures, local-root manifests | AUDIT HISTORY and MANUSCRIPT EVIDENCE index | Not manuscript prose; Appendix provenance reference only | `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L177`; `local-sha256:e9b8d8475ab30357a71e722eab49434abbb7c9ccdb16b7325de0ad0edb62c9c0:paper_notes/STAGE4_INVENTORY_HANDOFF.md:L1-L50` |

### Current Local Evidence Roots

| Root group | Current Stage 1 routing | Locator |
|---|---|---|
| Phase 1 run roots: `phase1_xzone_asis`, `phase1_xzone_bumped`, `phase1_xzone_bumped_s11_20`, `phase1_xzone_ablation` | Candidate Phase 1 manuscript evidence after row-level result extraction; local trees are not ZIP-byte-verified | `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 5-8; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations` |
| Phase 2 roots: `phase2_results` through `phase2_results_v5` | `phase2_results_v5` is the latest local Phase 2 candidate; earlier roots remain AUDIT HISTORY or superseded unless cited for corrections | `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 9-13; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations`; authoritative committed row source: `origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_ci.csv:L1-L19` |
| Phase 3 roots: `phase3_download`, `phase3_download_n10` | `phase3_download_n10` is the latest local Phase 3 candidate; `phase3_download` is superseded for final inference by run `27621106006`; local roots are not ZIP-byte-verified | `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 14-15; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations`; authoritative committed row source: `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9` |
| Pre-pivot and local probe roots: `tmp_sweep18_results`, `tmp_sweep_n10_results`, `tmp_step0_*`, `tmp_step2_validation`, `tmp_paper_results` | AUDIT HISTORY unless a later stage reconstructs exact code/run/command identity and relevance | `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 16-24; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations` |
| Runtime directories and root-level runtime files: `.node-red-lab2_slow`, `.node-red-lab3_slow`, `dynamics_delays_*`, `learned_dynamics_*`, `timebounded_results_*` | AUDIT HISTORY only; prefer run-scoped Actions or `origin/results` snapshots for manuscript evidence | Directories: `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 25-26; named columns path,provenance_class,verification_status,content_hash,file_count,byte_count,limitations`; files: `local-sha256:432252f1c15a4f88030783796ea42c66bbad7fa49b347684e8b4aacc489fab2e:paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv:rows 5-16; named columns path,path_kind,git_state,provenance_class,sha256,limitations` |

### Current Manuscript Section Routing

| Manuscript section | Evidence categories to route | Exclusions at this stage |
|---|---|---|
| Introduction | Research problem and scope from pivot/user requirement sources; final three-part trajectory only as supported by current committed evidence | Detailed branch chronology; result numbers not yet row-extracted |
| Background | MAS/JaCaMo, Q-learning, ontology/KG, RDF/Turtle, WoT, stereotypes, process dynamics terminology | Project performance claims; literature comparison without external bibliographic sources |
| Contributions | Clean-lab ladder, semantic prior mechanism, cross-zone structural prior, Phase 2 fault recognition/blacklist/re-learn, Phase 3 response-delay learning and KG writeback | Numeric outcomes; implementation diary |
| Evaluation | Experiment records, baselines/treatments, variables/controls, scenarios, seeds/replicas, metrics, statistical scripts, run IDs, committed result rows | Dirty result prose and local roots without ZIP or result-branch authority |
| Conclusions | Only final active claim-ledger rows with row-level or derived-chain support | Superseded runs and exploratory-only findings unless framed as limitations |
| Abstract | Problem, method, principal supported results, and limitation slots to be filled last | Stage 1 inventory claims |
| Appendix | Reproduction commands, full profile/config matrices, schemas, workflows, run/artifact provenance, supplementary tables/figures, audit index | Dependencies, caches, ordinary build outputs unless uniquely evidentiary |

### Current Exclusion Decisions

| Area | Decision | Locator |
|---|---|---|
| `.gradle/`, `.pytest_cache/`, `build/`, `bin/`, package caches, dependency folders | Exclude ordinary dependencies, caches, and build products unless later tied to a unique evidence artifact; `.pytest_cache/` also produced a permission warning | `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L12-L14` |
| `.node-red-*` runtime directories | Audit-only runtime state; canonical flows and flow maps live under committed `simulator/` and `config/` | `local-sha256:cfa80d377c9973977280e04150c64c883fe24c4902de631b4b47f69b6b17d3ce:paper_notes/STAGE4_LOCAL_TREE_HASHES_20260616T143435Z.csv:rows 25-26; named columns path,path_kind,provenance_class,limitations` |
| Dirty tracked documentation files | Documentation/routing sources only until empirical claims are checked against primary rows or committed source | `local-sha256:432252f1c15a4f88030783796ea42c66bbad7fa49b347684e8b4aacc489fab2e:paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv:rows 2-3; named columns path,git_state,sha256,line_count,limitations` |
| Root-level generated Q-tables, metrics, logs, Phase 3 runtime CSV/TTL files | Audit-only unless linked to exact run, code SHA, and command; prefer run-scoped snapshots | `local-sha256:432252f1c15a4f88030783796ea42c66bbad7fa49b347684e8b4aacc489fab2e:paper_notes/STAGE4_FILE_HASHES_20260616T143435Z.csv:rows 5-16; named columns path,path_kind,provenance_class,limitations` |

## Scope and Snapshot

- [DIRECT] Inventory baseline: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410`.
  Locator: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.`
- [DIRECT] Stage 1 is inventory-only. Result values, effect sizes, hypothesis
  verdicts, and headline findings are not selected here.
  Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L14`
- [DIRECT] Stage 2R2 located a hash-addressed external local advisor-note file;
  [UNRESOLVED] the original advisor-authored meeting artifact and exact pivot
  timestamp remain `NOT FOUND`.
  Locator: `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L1-L26`
- [DIRECT] Products remain separate:
  `AUDIT HISTORY` retains chronology, corrections, failures, and superseded
  material; `MANUSCRIPT EVIDENCE` retains only sources needed to explain the
  final problem, approach, evaluation, findings, limitations, and related work.
  Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L15-L25`

## Inventory Method

| Record | Status | Exact method | Inputs |
|---|---|---|---|
| Tracked tree | [DERIVED] | `git ls-tree -r --name-only 985c7a18558b6d5cb96c018a395b0aae6389f410` | Git object `985c7a18558b6d5cb96c018a395b0aae6389f410` |
| Ref comparison | [DERIVED] | `git diff --stat main...<ref>` and `git diff --name-status main...<ref>` | refs listed under **Audit History Ref Map** |
| Local result roots | [DIRECT] | Reused canonical `TREE-SHA256-V1` rows from `SOURCE_LEDGER.csv`; no root was re-written | `SRC-R001` through `SRC-I007-R1` and `SRC-R013` |
| Local logs | [DERIVED] | `node paper_notes/TREE_SHA256_V1.mjs log` | script `local-sha256:c51fa5b147f93587839482e15e695dcc65b550005084fc370097028005820fdd:paper_notes/TREE_SHA256_V1.mjs`; Node.js `v22.14.0` |
| External template | [DERIVED] | `node paper_notes/TREE_SHA256_V1.mjs 'C:\Users\esrad\Downloads\Template-ThesisReport\Template-ThesisReport'` | same script and runtime as above |

## Committed Evidence-Bearing Areas

| Path / source category | Evidence role | Product | Proposed manuscript destination | Immutable locator |
|---|---|---|---|---|
| `README.md` | Architecture index, declared agent modes, output schemas, project structure, run and analysis entry points | AUDIT HISTORY; verification lead only | Introduction orientation; Appendix reproducibility | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L7-L37`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L127-L195`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L271-L323`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L374-L443` |
| `src/agt/` | Agent plans: rule-based, Q-learning, benchmark, adaptation, and profile registry | MANUSCRIPT EVIDENCE | Contributions: agent behavior; Appendix: implementation mapping | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/lab_profiles.asl:L1-L32`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/illuminance_controller_agent_bench.asl:L1-L49`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/illuminance_controller_agent_adapt.asl:L1-L25` |
| `src/env/tools/QLearner.java` | Tabular Q-learning, KG prior use, action selection, training outputs, Phase 2 detection/blacklist/warm restart/recovery operations | MANUSCRIPT EVIDENCE | Contributions: conceptual mechanism; Appendix: concrete operations | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L18-L45`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L229-L293`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L932-L1197` |
| `src/env/tools/StereotypeReasoner.java`, `OntologyArtifact.java`, `StereotypeLearner.java` | Semantic reasoning, ontology queries, prior/action metadata, learned effect serialization | MANUSCRIPT EVIDENCE | Background foundations; Contributions: semantic-RL bridge | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L28-L37` |
| `src/env/tools/BenchmarkLogger.java` | Metric and trace emission | MANUSCRIPT EVIDENCE | Evaluation: metric definitions; Appendix: schemas | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L92-L150`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/illuminance_controller_agent_bench.asl:L1-L18` |
| `src/resources/` | Ontologies, WoT mappings, Thing Descriptions, clean-lab structure, cross-zone declarations | MANUSCRIPT EVIDENCE | Background: Semantic Web model; Contributions: lab/KG design; Appendix: resource inventory | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L177-L195`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/lab_profiles.asl:L10-L23` |
| `simulator/` | Canonical Node-RED physics, clean labs, weakness labs, and generated Phase 2 fault flows | MANUSCRIPT EVIDENCE | Contributions: experimental testbed; Evaluation: treatments and controls; Appendix: flow-to-profile mapping | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:simulator/README.md:L1-L25`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:simulator/generate_flows.ps1:L1-L21`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:simulator/generate_faulty_flows.ps1:L1-L71` |
| `benchmark/*.json` | Held-out benchmark scenarios and training scenario cycles | MANUSCRIPT EVIDENCE | Evaluation: scenarios, independent variables, controls | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/lab_profiles.asl:L10-L23`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:build.gradle:L336-L451` |
| `config/run_config.json` | Run profiles, factor arms, profile lists, modes, simulator maps, learning overrides, and Phase 2 profile mapping | MANUSCRIPT EVIDENCE | Evaluation design; Appendix reproducibility | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L4-L165`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L166-L241`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L242-L314` |
| `build.gradle`, `task*.jcm` | Executable task wiring for rule agent, Q-learning, benchmark sweep, adaptation, validation, and preflight | AUDIT HISTORY; MANUSCRIPT EVIDENCE for reproducibility | Appendix: execution entry points | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:build.gradle:L92-L181`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:build.gradle:L233-L312`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:build.gradle:L327-L451` |
| `run_full_project.ps1`, `run_full_project_parallel.ps1` | Local sequential/parallel training, benchmark, collection, and analysis orchestration | AUDIT HISTORY; MANUSCRIPT EVIDENCE for reproducibility | Appendix: local reproduction | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_full_project_parallel.ps1:L31-L47`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_full_project_parallel.ps1:L571-L573`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_full_project_parallel.ps1:L1015-L1069` |
| `run_phase2_adapt.ps1` | Local Phase 2 profile-by-mode orchestration and recovery CSV production | AUDIT HISTORY; MANUSCRIPT EVIDENCE for reproducibility | Evaluation method; Appendix command mapping | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_phase2_adapt.ps1:L1-L24`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_phase2_adapt.ps1:L198-L225`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:run_phase2_adapt.ps1:L261-L423` |
| `.github/workflows/phase1.yml` | Phase 1 matrix execution, consolidation, summary, artifact publication | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run identity | Evaluation reproducibility; Appendix | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/phase1.yml:L1-L130`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/phase1.yml:L510-L575` |
| `.github/workflows/phase2.yml` | Phase 2 clean warm-start and adaptation matrices, analysis, result publication | AUDIT HISTORY; MANUSCRIPT EVIDENCE for run identity | Evaluation reproducibility; Appendix | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/phase2.yml:L1-L125`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/phase2.yml:L250-L390` |
| `.github/workflows/sweep-paper.yml` | Pre-pivot multi-seed paper sweep and consolidated analysis | AUDIT HISTORY; candidate evidence only after relevance review | Audit chronology; possible Appendix | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/sweep-paper.yml:L1-L115`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/sweep-paper.yml:L419-L542` |
| `analysis/sweep_report.py` | Phase 1 aggregation, CIs, paired tests, correction families, tables, and figures | MANUSCRIPT EVIDENCE after derivation-chain verification | Evaluation: statistical method and Phase 1 figures/tables | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L1-L20`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L281-L405`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L1177-L1265` |
| `analysis/phase2_recovery.py` | Phase 2 recovery/detection aggregation and paired analysis | MANUSCRIPT EVIDENCE after derivation-chain verification | Evaluation: Phase 2 statistics and tables | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L1-L44`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L201-L316`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L360-L403` |
| Other `analysis/*.py` | Mechanism audits, learning curves, heatmaps, demos, and historical slide-only outputs | Mixed; inspect script-specific status before manuscript use | Evaluation figures or Appendix; slide-only scripts remain audit-only | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/learning_curves.py:L1-L22`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/qtable_init_heatmap.py:L1-L17`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/midterm_results.py:L1-L31` |
| `scripts/version_artifacts.ps1` | Results-branch snapshot and `RUN_MANIFEST.json` generation | AUDIT HISTORY | Appendix provenance pipeline | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:scripts/version_artifacts.ps1:L1-L14`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:scripts/version_artifacts.ps1:L64-L108`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:scripts/version_artifacts.ps1:L149-L179` |
| `dashboard/` | Decision-trace and weakness visualization application | MANUSCRIPT EVIDENCE only for system demonstration, not primary statistics | Contributions demonstration; Appendix/UI | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L154-L195` |
| `docs/` | Pre-registration, pivot/change chronology, result notes, meeting notes, and mechanism analyses | AUDIT HISTORY by default; individual claims require primary-source verification | Introduction requirements; Evaluation planning; Discussion limitations | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/pre_registration.md:L1-L138`; `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/PHASE1_TO_PHASE2_CHANGES.md:L1-L207` |
| `paper_notes/` | Durable evidence protocol, ledgers, maps, gaps, and handoffs | AUDIT HISTORY and MANUSCRIPT EVIDENCE index | Not manuscript text; Appendix provenance reference only | `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L177` |

## Local and Actions-Derived Evidence Roots

| Root(s) | Classification | Primary contents | Manuscript eligibility | Immutable source locator |
|---|---|---|---|---|
| `phase1_xzone_asis` | [DIRECT] Actions-derived, ZIP identity unresolved | seed-organized training/benchmark outputs plus `analysis/out` | Candidate Phase 1 evaluation evidence after run-design and derivation audit | `local-tree-sha256:75a9c8ccea76c0bd52cef6cd0dad34bf2f4ffe8c13501690b59f8cbe186b52a9:phase1_xzone_asis`; run `27440842780` |
| `phase1_xzone_bumped` | [DIRECT] Actions-derived, ZIP identity unresolved | Phase 1 treatment variant | Candidate Phase 1 mechanism/follow-up evidence | `local-tree-sha256:e9d706b2f7828bb65bdb9d091269681b0f9acddd263c7d438777340b8a5b5343:phase1_xzone_bumped`; run `27461188614` |
| `phase1_xzone_bumped_s11_20` | [DIRECT] Actions-derived, ZIP identity unresolved | independent-seed replication bundle | Candidate Phase 1 replication evidence | `local-tree-sha256:f80a117fac11c1db5ce3d545b04a4e418590f97c66d3ccc8ff44c6c8cc71152e:phase1_xzone_bumped_s11_20`; run `27462446044` |
| `phase1_xzone_ablation` | [DIRECT] Actions-derived, ZIP identity unresolved | randomized/untargeted cross-zone control | Candidate Phase 1 ablation evidence | `local-tree-sha256:7c114de88374bb003264a994a50db753edc89113258a4a9a1d7f64831911c638:phase1_xzone_ablation`; run `27464846574` |
| `phase2_results`, `phase2_results_v2`, `phase2_results_v3` | [SUPERSEDED] earlier Phase 2 iterations retained for chronology | recovery CSVs and analysis tables | AUDIT HISTORY; do not use as final evidence without explicit historical purpose | `local-tree-sha256:95744977ac3f2399a4c068a741bfe5d18051c2a230467f5a5c1d2269778eb1ff:phase2_results`; `local-tree-sha256:5354fe2bf014bca618e9eceaed3e40957cda7f85bbf53e5e75f7893bfde99a94:phase2_results_v2`; `local-tree-sha256:2b6c7b9292b7ae8ce2a9cbcbc0c44bc34945c57d2e9965e977b5dc5c2e676bf1:phase2_results_v3` |
| `phase2_results_v4` | [DIRECT] latest ingested completed Phase 2 root; later run still incomplete | recovery CSVs and Phase 2 analysis tables | Candidate evidence, not final while run `27547019772` is incomplete | `local-tree-sha256:0b65bb2d54dcb5b06a8c179f518480622d715a3688153f53adea990661e41cf1:phase2_results_v4`; run `27529585379` |
| `tmp_sweep18_results`, `tmp_sweep_n10_results` | [DIRECT] Actions-derived plus local recomputation | pre-pivot multi-seed raw and derived outputs | AUDIT HISTORY first; manuscript use requires relevance and complete provenance review | `local-tree-sha256:4bfb50bc9eb5481ac27362441c9215b44535ae0650784b46fb20133988ee0de9:tmp_sweep18_results`; `local-tree-sha256:0defe493b63063a9dc9dc5315fc394510c6b0ed23ecb3ef8266ba98f43811cdf:tmp_sweep_n10_results` |
| `benchmark/results_full_seed1` | [UNRESOLVED] mixed local root | profile-level training and benchmark artifacts | Exclude from manuscript until per-profile code/run identity is reconstructed | `local-tree-sha256:be0d54fb7873e9d06b9873380106e5fd5db5c93e5a690d3d69a5b6b7dc66f382:benchmark/results_full_seed1` |
| `analysis/out_full`, `analysis/out_kg_only` | [UNRESOLVED] placeholder local outputs | empty summary plus minimal heatmap CSV | Exclude | `local-tree-sha256:4e29a5214ea3d152e7e09dd859a7dffe4d4fbc86f836f29edc8a3dda21d4854d:analysis/out_full`; same hash for `analysis/out_kg_only` |
| `tmp_paper_results` | [UNRESOLVED] mixed/unknown provenance | recovered ZIP and extracted result material | AUDIT HISTORY only until mapped to one run | `local-tree-sha256:dda0bcc75be228facafa9d242008455b764a0525aad5123c119292f48c9355ba:tmp_paper_results` |
| `tmp_step0_*`, `tmp_step2_validation` | [DIRECT] local generated probes with missing exact generation chains | sanity probes, replications, and validation outputs | AUDIT HISTORY; possible methods appendix only after reconstruction | `SRC-I002-R1` through `SRC-I007-R1` in `SOURCE_LEDGER.csv` |
| `log/` | [DIRECT] mixed local logs | training, benchmark, adaptation, JSONL execution, and diagnostic logs | AUDIT HISTORY; individual records may support debugging but not numeric claims without run linkage | `local-tree-sha256:4b2a846600b09d29f8ef221089a24a36bd2643ce320dba41662cea5205488305:log` |

## Root-Level Generated Evidence Files

| Pattern | Meaning | Status | Locator |
|---|---|---|---|
| `qtable_initial_*`, `qtable_final_*` | Local training state snapshots and sidecars | [UNRESOLVED] until tied to one run/code SHA | Declared schema: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L136-L152`; current files remain mutable local artifacts |
| `metrics_*`, `coverage_*`, `first_goal_*`, `iv_stats_*`, `learned_*` | Training metrics, state-action coverage, first-goal records, IV statistics, learned Turtle | [UNRESOLVED] until tied to one run/code SHA | Same locator as above |
| `benchmark_results_*`, `bench_step_log_*` | Execution summaries and per-step traces | [UNRESOLVED] until tied to one run/code SHA | `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L92-L134` |
| `run_full_project*.log`, `run_phase2_adapt.log`, `bench_*.log`, `sp_*.log` | Local orchestration/debug chronology | AUDIT HISTORY | `NOT FOUND` as one immutable grouped source; see `GAP-019` |
| `3600100.3623737.pdf` | Local candidate literature/background PDF | [UNRESOLVED] bibliographic identity not extracted in Stage 1 | `local-sha256:8da47a5f099e88bd8aa8e527ad35aa285bbddd05810f30e9b3337d87776412ee:3600100.3623737.pdf` |

## Audit History Ref Map

| Ref | Tip | Audit role | Manuscript rule |
|---|---|---|---|
| `feature/qlearning-stereotype-comparison` | `9cfe38c292983347e08f6b6773243ee40fe5a001` | Pre-pivot implementation/meeting state | Chronology only unless a final mechanism still originates here |
| `main` | `7ac37a10fe3b3c23bc2b54159c40142fd367e821` | Phase 1 factorial baseline line | Use only with matching run-head artifacts |
| `kg-crosszone-coupling` | `866297d54750c91f4595962f9c975d2f1704f629` | Cross-zone mechanism branch | Candidate Phase 1 mechanism source |
| `kg-crosszone-coupling-bump` | `293bb07df96a2b51fcf9f68adfcd6f0245713682` | Adjusted simulator/mechanism and final Phase 1 checkpoint | Candidate Phase 1 follow-up source |
| `kg-crosszone-ablation` | `e8d63e09be504f1dc206737ca8feb05299fe1031` | Cross-zone control/ablation branch | Candidate ablation source |
| `phase2-fault-detection` | `985c7a18558b6d5cb96c018a395b0aae6389f410` | Current Phase 2 implementation line | Current code map; results still require matching run head |
| `origin/results` | `e9b9e3529cd71fce3ad9dfe5fa29c64793898b2e` | Committed run snapshots for selected Phase 1/Phase 2 executions | Primary artifact source where path/run mapping is verified |

Derived ref inspection command: `git show --no-patch <ref>` plus
`git diff --stat main...<ref>` and `git diff --name-status main...<ref>`.
Runtime: Git `2.54.0.windows.1`.

## Evidence Data Flow

1. [DIRECT] Profile and run parameters originate in `lab_profiles.asl` and
   `config/run_config.json`.
   Locators: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/lab_profiles.asl:L1-L32`;
   `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:config/run_config.json:L4-L165`.
2. [DIRECT] Node-RED flows provide clean, weakness, or faulty environment
   behavior through REST status/action endpoints.
   Locator: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:simulator/README.md:L1-L10`.
3. [DIRECT] JaCaMo agents call Java artifacts; the Q-learner uses ontology-derived
   state/action structure and optionally stereotype priors.
   Locator: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L18-L45`.
4. [DIRECT] Training emits Q-tables, metrics, coverage, first-goal, IV statistics,
   and learned Turtle artifacts.
   Locator: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L136-L152`.
5. [DIRECT] Benchmark execution emits scenario summaries and per-step traces.
   Locator: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L92-L134`.
6. [DIRECT] Analysis scripts transform raw artifacts into tables, tests, and
   figures.
   Locators: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L1-L20`;
   `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L1-L44`.
7. [DIRECT] Workflows consolidate artifacts; the versioning script can write
   run snapshots and manifests to the results branch.
   Locators: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:.github/workflows/sweep-paper.yml:L419-L542`;
   `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:scripts/version_artifacts.ps1:L93-L108`.

## Manuscript Section Routing

| Manuscript section | Evidence categories to route | Exclusions at this stage |
|---|---|---|
| Introduction | Advisor/pivot requirement, final research problem, clean-lab anchor, fault-recognition motivation, stated contributions | Detailed branch chronology; numeric results |
| Background | MAS/JaCaMo, Q-learning, ontology/KG, stereotypes, WoT/BRICK foundations | Project-specific performance claims; related-work comparison without literature sources |
| Contributions | Clean-lab progression design, semantic prior mechanism, cross-zone mechanism, fault detection/blacklist/warm restart, testbed design | Statistical outcomes; file-by-file diary |
| Evaluation | Pre-registration/deviations, treatments/baselines, scenarios, seeds, controls, metrics, statistical scripts, verified run artifacts | Mutable draft result prose; mixed local roots |
| Conclusions | Only findings and limitations later supported by final claim records | In-progress run; superseded Phase 2 verdicts |
| Abstract | Final problem/method/result/limitation claims only after evidence review | Any Stage 1 inventory claim |
| Appendix | Reproduction commands, config matrices, schemas, ontology/profile map, workflow/run IDs, supplementary figures/tables | Dependencies and caches unless uniquely evidentiary |

## Excluded or Audit-Only Areas

| Area | Decision | Reason / locator |
|---|---|---|
| `.gradle/`, `.pytest_cache/`, `build/`, `bin/` | Exclude ordinary dependency/cache/build output | No unique scientific evidence identified; test report paths are reproducible from `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:README.md:L407-L421` |
| `.node-red-*` runtime user directories | Audit-only; exclude dependencies and mutable runtime state | Canonical flows are committed under `simulator/`; Stage 0 hashes exist for selected lab directories (`SRC-0020` through `SRC-0023`) |
| `dashboard/node_modules`, Node-RED `node_modules`, Python caches | Exclude dependencies/caches | Reconstructible dependencies; no unique run evidence identified |
| Historical slide outputs from `midterm_results.py` | Audit-only | Script explicitly marks them not for thesis figures: `phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/midterm_results.py:L1-L31` |
| Untracked result-note documents | Documentation leads, not primary empirical evidence | `SRC-0030` through `SRC-0038`; claims must be checked against raw artifacts and run-head code |

## Phase Boundary Record

| Thesis phase | Repository state | Stage 1 status |
|---|---|---|
| Phase 1: clean-lab KG acceleration | Implemented with clean lab ladder, factor arms, workflows, raw/derived result roots | [DIRECT] mapped; experimental records still required before result interpretation |
| Phase 2: fault recognition, blacklist, warm restart, re-learning | Implemented with faulty profiles, flows, agent, analysis, workflow, and multiple completed iterations | [DIRECT] mapped; run `27547019772` remains incomplete at the latest valid observation |
| Phase 3: learned temporal/process dynamics written back to the KG | Requirement exists in the local pivot document; matching implementation/result evidence was `NOT FOUND` in the Stage 1 repository search | [UNRESOLVED]; do not describe as implemented |

Phase 3 requirement locator:
`local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L48-L56`.
Search command and gap: `GAP-017`.

## Stage 1 Evidence Records

- [DIRECT] Repository map is anchored to full commit
  `985c7a18558b6d5cb96c018a395b0aae6389f410`.
- [DIRECT] All listed local result roots preserve their Stage 0 canonical hashes;
  none was modified during Stage 1.
- [INTERPRETATION] `docs/` is an audit/history source by default, while `src/`,
  `simulator/`, `benchmark/`, `config/`, workflows, and run artifacts form the
  primary evidence chain for manuscript claims.
- [UNRESOLVED] No result root is freshly byte-verified against its Actions ZIP.
- [UNRESOLVED] The newest Phase 2 run has not produced an ingested successor root.
