# Related Work Evidence Notes

Stage: `10B`
Created: `2026-06-18T10:46:19Z`
Scope: related-work evidence extraction only. This is not polished thesis prose.

## Control Record

| item | label | evidence record |
|---|---|---|
| Protocol discipline | [DIRECT] | Evidence extraction requires separate `AUDIT HISTORY` and `MANUSCRIPT EVIDENCE`, immutable locators, derived-result commands, and unresolved gap records. Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236`. |
| Stage input bundle read | [DIRECT] | Stage 10B read Stage 10A Phase 3 products and ledgers as related-work context, not as literature sources. Source locators already recorded in `SRC-S10A-P3-001` through `SRC-S10A-P3-014`; key rows: `local-sha256:6f52ebe57ffbbc85fccd28e495538129b086d94c3483f594bb2daf6e5d9ac0ee:paper_notes/PHASE3_METHODS.md:L1-L75`; `local-sha256:4c823e93e6d5306ea273508e2420b4b8b5380eace9f48c5e8c7d7bc4eb676f56:paper_notes/PHASE3_RESULTS.md:L1-L121`; `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:L1-L36`; `local-sha256:d8e7b1953499f3e0a951d1c85c5b3dcb0128285c7f0bb38783680ed76dc778dd:paper_notes/PHASE3_FIGURES.md:L1-L25`. |
| Implementation anchors read | [DIRECT] | Stage 10B read `analysis/phase3_dynamics.py`, `config/run_config.json`, `.github/workflows/phase3.yml`, `src/agt/illuminance_controller_agent_dynamics.asl`, `src/env/tools/DynamicsLearner.java`, and `phase3_download_n10/phase3-consolidated/`. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L1-L575`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L322-L365`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L39-L59`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L1-L495`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L1-L366`; `local-tree-sha256:2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945:phase3_download_n10/phase3-consolidated`. |
| Bibliographic ledger | [DIRECT] | Stage 10B created `paper_notes/BIBLIOGRAPHIC_LEDGER.csv` with related-work records `BIB-S10B-001` through `BIB-S10B-016` and rejected-candidate row `BIB-S10B-REJ-001`. Locator: `local-sha256:7c7c58608dd8e1d617b721323c1e701b299f5fa154cf77d60b2ff14dd4f9b641:paper_notes/BIBLIOGRAPHIC_LEDGER.csv:L1-L18`; rows `2-18`, named columns `bib_id,topic_bucket,evidence_label,source_type,primary_status,title,year,venue,doi,arxiv_id,url,source_locator,source_status,project_mapping,notes`. |
| Research status boundary | [UNRESOLVED] | Formal post-pivot preregistration remains `NOT FOUND`; Phase 3 run `27621106006` remains `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`, not `PRE_REGISTERED_CONFIRMATORY`. Locators: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:rows 34-36; named columns evidence_id,claim_or_object,metric,value,statistical_integrity_status`; `local-sha256:432d7caff9e424eb87a1cb53a48df0f60ad8a51ced67d959ba0ee9df886d3d05:paper_notes/EVIDENCE_GAPS.md:L881-L921`. |

## AUDIT HISTORY

| record | label | evidence |
|---|---|---|
| RW-AH-001 | [DIRECT] | Read-only git provenance checked Phase 3 introduction commit, merge commit, later workflow-default update, and diff-stat without branch switching. Locators: local commands `git show --stat --oneline --decorate 7137f88`; `git show --stat --oneline --decorate 3bb5289`; `git show --stat --oneline --decorate eda6ca1`; `git diff --stat 3bb5289c36cb3093228ec0609fe57ec676b1ee53 eda6ca1ffa026e723ad1a18a2bdb3aed927e7433 -- .github/workflows/phase3.yml docs/PHASE2_TO_PHASE3_CHANGES.md paper_notes`. |
| RW-AH-002 | [DIRECT] | Phase 3 implementation was introduced in commit `7137f88` with new dynamics workflow, analysis script, dynamics agent, DynamicsLearner artifact, slow lab resources, and orchestrator. Locator: local command `git show --stat --oneline --decorate 7137f88`. |
| RW-AH-003 | [DIRECT] | Later commit `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` changes Phase 3 workflow defaults and adds documentation, but the n10 manuscript candidate run head is `3bb5289c36cb3093228ec0609fe57ec676b1ee53`. Locators: local command `git show --stat --oneline --decorate eda6ca1`; Stage 10A run locator in `P3T-008` and `P3T-010`. |
| RW-AH-004 | [SUPERSEDED] | Candidate Brick DOI `10.1016/j.apenergy.2017.10.091` was rejected because Crossref returned an unrelated Applied Energy title. Corrected Brick DOI is `10.1016/j.apenergy.2018.02.091`. Locator: `paper_notes/BIBLIOGRAPHIC_LEDGER.csv:row BIB-S10B-REJ-001`; successor `BIB-S10B-010`. |

## MANUSCRIPT EVIDENCE

### Source Classification Matrix

| bucket | direct bibliographic records | use boundary |
|---|---|---|
| MAS / BDI | `BIB-S10B-001`; `BIB-S10B-002`; `BIB-S10B-007` | Use to position BDI/JaCaMo/MAS implementation framing. Do not use to claim RL efficacy. |
| Q-learning for building automation | `BIB-S10B-003`; `BIB-S10B-004`; `BIB-S10B-005`; `BIB-S10B-006`; `BIB-S10B-007` | Use to compare building-control RL work against project clean-lab KG acceleration, Phase 2 adaptation, and Phase 3 dynamics. |
| Knowledge-graph / stereotype priors | `BIB-S10B-008`; `BIB-S10B-009`; `BIB-S10B-010`; `BIB-S10B-011`; `BIB-S10B-012` | Use to separate semantic building/actuator metadata and KG-as-prior ideas from the project-specific stereotype ontology. |
| Physics-informed learning | `BIB-S10B-013`; `BIB-S10B-014` | Use to compare physics/model-assisted RL against symbolic KG priors and explicit response-delay writeback. |
| Anomaly / fault detection | `BIB-S10B-014`; `BIB-S10B-015`; `BIB-S10B-016` | Use to position Phase 2 expected-vs-actual defect detection and relearning; keep separate from Phase 3 process dynamics. |
| Learned temporal / process dynamics | `BIB-S10B-005`; `BIB-S10B-006`; `BIB-S10B-013`; `BIB-S10B-008` | Use to position Phase 3 learned response delays and time-bounded goals. |

### MAS / BDI

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-MAS-001 | [DIRECT] | `BIB-S10B-001` records AgentSpeak(L) as a BDI agent-programming source with DOI and venue metadata. | Phase 3 agent source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L1-L495`. | Project uses BDI-style plans and beliefs to organize probing, KG writeback, and deadline exploitation. | Treat as implementation-foundation related work, not empirical comparison. |
| RW-MAS-002 | [DIRECT] | `BIB-S10B-002` records JaCaMo multi-agent oriented programming with DOI and venue metadata. | Dynamics artifact and `.jcm` task locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L1-L366`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:task_dynamics.jcm:L1-L25`. | Project fits a JaCaMo-like split between agent plans and artifacts. | Do not imply JaCaMo literature itself supplies KG-prior or delay-learning evidence. |
| RW-MAS-003 | [INTERPRETATION] | `BIB-S10B-007` records MARL HVAC control; `BIB-S10B-002` records MAS programming. | Stage 10A method row `P3T-004`: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 5; named columns evidence_id,claim_or_object,metric,value,input_sources`. | The project is MAS-implemented but Phase 3 is not multi-agent RL training; `ql_true`/`ql_false` are planner modes. | Avoid conflating MAS software architecture with MARL algorithmic comparison. |

### Q-Learning For Building Automation

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-QB-001 | [DIRECT] | `BIB-S10B-003` records Q-learning as the foundational RL algorithm. | Phase 3 reuses `QLearner` for action-space enumeration only: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L41-L49`. | Use Q-learning source for Phase 1/2 learning foundation and to clarify Phase 3 is dynamics learning, not Q-table training. | Do not use Watkins-Dayan convergence theorem as proof that project experiments converge. |
| RW-QB-002 | [DIRECT] | `BIB-S10B-004` records DRL for building HVAC control evaluated in EnergyPlus and compared with rule-based control. | Project Phase 3 profiles are `lab2_slow` and `lab3_slow`, not HVAC EnergyPlus tasks: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L323-L365`. | Good comparison for building-control RL motivation. | Domain/actuator mismatch must be stated. |
| RW-QB-003 | [DIRECT] | `BIB-S10B-005` records model-free control for district-heating TCLs; `BIB-S10B-006` records sparse-observation direct-load control. | Project outcome metrics for Phase 3 are delay accuracy and deadline compliance: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L21-L51`. | These works emphasize building-control policies under dynamics/observability constraints. | Project contribution is not thermal-load scheduling; it is learned actuator response-delay knowledge used by a BDI planner. |

### Knowledge-Graph / Stereotype Priors

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-KG-001 | [DIRECT] | `BIB-S10B-008` and `BIB-S10B-009` record semantic sensor/actuator ontology sources. | Project slow-lab interaction TDs and learned dynamics TTL: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/interactions-lab2_slow.ttl:L27-L51`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L176-L220`. | Use to position RDF/ontology descriptions of sensors, actuators, observations, and actuations. | Project uses custom `ws:` vocabulary; do not claim SSN/SOSA compliance unless verified later. |
| RW-KG-002 | [DIRECT] | `BIB-S10B-010` records Brick as smart-building metadata schema. | Project uses custom building stereotype files such as `building_2_slow.ttl` and `building_3_slow.ttl`: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_2_slow.ttl:L16-L45`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_3_slow.ttl:L16-L45`. | Brick is related as portable smart-building metadata; project ontology is task-specific and stereotype-oriented. | Avoid saying the project extends Brick. |
| RW-KG-003 | [INTERPRETATION] | `BIB-S10B-011` records KG-enhanced Q-learning in recommender systems; `BIB-S10B-012` records equivalence between potential shaping and Q-value initialization. | Phase 1 KG-prior mechanics route through `QLearner` and Phase 1 methods, while Phase 3 uses learned delays: Stage 10A source `SRC-S10A-P3-006`; Stage 10A method note `P3T-004`. | Use as analogical support for structured prior knowledge improving sample efficiency/action selection. | KGQR is not building automation; Wiewiora is theoretical shaping/Q-init, not semantic KG. |

### Physics-Informed Learning

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-PHYS-001 | [DIRECT] | `BIB-S10B-013` records PhysQ as physics-informed RL for building control. | Project Phase 1/2 use symbolic physics/stereotype knowledge; Phase 3 learns response-delay facts and writes TTL: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L176-L220`. | PhysQ is close in motivation: prior physical knowledge improves building-control learning. | Difference: project uses explicit RDF/KG priors and tabular/BDI mechanisms, not physics-informed neural representations. |
| RW-PHYS-002 | [DIRECT] | `BIB-S10B-014` records model-assisted learning for sensor-fault-tolerant HVAC control. | Phase 2 and Phase 3 project sources keep fault adaptation and process dynamics separate: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:rows 34-36`; Stage 9 carried gaps `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L93-L99`. | Use to compare learning aided by abstract physical models under building faults. | Do not merge Phase 2 fault adaptation with Phase 3 delay learning in the manuscript structure. |

### Anomaly / Fault Detection

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-FAULT-001 | [DIRECT] | `BIB-S10B-015` records transfer learning for HVAC system fault detection. | Phase 2 selected result authority is run `27547019772` and result commit `22a448be5d9829751badd341904e36ed582f091f`: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:rows 2-10`. | Related by fault-detection problem setting and data scarcity. | Project does not train a transfer classifier; it uses KG expected-vs-actual logic and relearning after blacklist. |
| RW-FAULT-002 | [DIRECT] | `BIB-S10B-014` records sensor fault-tolerant HVAC control; `BIB-S10B-016` records KG-assisted industrial root-cause diagnosis. | Phase 2 expected-vs-actual source routing is in Stage 7/8/9 notes; Phase 3 source is separate. | Use as adjacent literature for fault tolerance and KG-based diagnosis. | Keep fault diagnosis related work out of the Phase 3 process-dynamics claim unless contrasting project phases. |

### Learned Temporal / Process Dynamics

| rw_note | label | bibliographic evidence | project anchor | comparison note | manuscript-use boundary |
|---|---|---|---|---|---|
| RW-DYN-001 | [DIRECT] | `BIB-S10B-005` and `BIB-S10B-006` record model-free control under temporal dynamics / sparse observations. | Phase 3 config declares `seconds_per_tick`, `blind_delay_ticks`, probe settings, and time-bounded goals: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L326-L365`. | Related work learns or controls systems with temporal state/dynamics; project learns explicit per-actuator response delay and materializes it. | Do not claim project learns full building thermal dynamics. |
| RW-DYN-002 | [DIRECT] | `BIB-S10B-013` records PhysQ; `BIB-S10B-008` records SOSA actuation/observation semantics. | DynamicsLearner writes `ws:responseDelay`, response class, sample count, delay table, and time-bounded result table: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L176-L220`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L241-L320`. | Combined positioning: temporal process knowledge can be learned and then represented for downstream control. | Phrase as bounded to tested slow-lab actuator response delays. |
| RW-DYN-003 | [INTERPRETATION] | `BIB-S10B-004`; `BIB-S10B-005`; `BIB-S10B-013`. | n10 manuscript candidate results: `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`. | Related-work gap statement candidate: building-control RL often optimizes policies directly; project evaluates whether learned symbolic response-delay knowledge can be written back and used by a deadline-aware BDI planner. | Keep as bounded interpretation supported by project and bibliographic sources; do not overclaim novelty until advisor/reviewer check. |

## Table Specifications

| table id | product | label | specification | source records |
|---|---|---|---|---|
| T-RW-1 | MANUSCRIPT_EVIDENCE | [DIRECT] | Related-work taxonomy table with rows: MAS/BDI, building-control RL, semantic building/KG metadata, physics-informed RL, fault/anomaly handling, temporal/process dynamics. Columns: representative source IDs, method family, project phase mapped, difference from project. | `BIB-S10B-001` through `BIB-S10B-016`; project anchors in this file. |
| T-RW-2 | MANUSCRIPT_EVIDENCE | [INTERPRETATION] | Contribution-positioning matrix: project Phase 1, Phase 2, Phase 3 as columns; literature buckets as rows; cells contain only supported comparison notes and boundaries. | `RW-QB-*`, `RW-KG-*`, `RW-PHYS-*`, `RW-FAULT-*`, `RW-DYN-*`. |
| T-RW-AUDIT-1 | AUDIT_HISTORY | [SUPERSEDED] | Bibliographic correction table showing rejected DOI candidate and corrected successor. | `BIB-S10B-REJ-001`; `BIB-S10B-010`. |

## Figure Specifications

| figure id | product | label | specification | source records |
|---|---|---|---|---|
| F-RW-1 | MANUSCRIPT_EVIDENCE | [INTERPRETATION] | Layered related-work map: bottom layer `MAS/BDI execution`; middle layer `KG/stereotype priors`; learning layer `Q-learning/building-control RL`; robustness branch `fault/anomaly detection`; dynamics branch `learned response-delay/process dynamics`; project contribution marker at intersection of KG priors, BDI planner, and learned temporal KG writeback. | `BIB-S10B-001` through `BIB-S10B-016`; Phase 3 source anchors in Control Record. |
| F-RW-2 | MANUSCRIPT_EVIDENCE | [INTERPRETATION] | Comparison heatmap: rows are bibliographic records; columns are `BDI/MAS`, `RL policy learning`, `building automation`, `semantic KG`, `physics prior`, `fault/anomaly`, `learned temporal dynamics`, `KG writeback`. Cell values are categorical only: present / adjacent / absent / unresolved. | `BIBLIOGRAPHIC_LEDGER.csv`; notes sections above. |

## Evidence Gaps

| gap | label | record |
|---|---|---|
| Primary source full-text access | [UNRESOLVED] | For DOI-only Crossref rows `BIB-S10B-001`, `BIB-S10B-002`, `BIB-S10B-009`, and `BIB-S10B-010`, Stage 10B verified bibliographic metadata but did not inspect full text. Do not derive technical claims beyond title/venue/year/source metadata from those rows. |
| Exact Phase 3 dispatch payload | [UNRESOLVED] | Carried forward unchanged: `workflow_dispatch.inputs=NOT FOUND` for run `27621106006`. Locator: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 34; named columns evidence_id,claim_or_object,metric,value,statistical_integrity_status`. |
| Phase 3 local ZIP byte identity | [UNRESOLVED] | Carried forward unchanged: local extracted Phase 3 tree is not ZIP-byte-verified against GitHub artifact digest. Locator: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 34; named columns evidence_id,claim_or_object,metric,value,statistical_integrity_status`. |
| Formal post-pivot preregistration | [UNRESOLVED] | Carried forward unchanged: formal post-pivot preregistration remains `NOT FOUND`. Locator: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 35; named columns evidence_id,claim_or_object,metric,value,statistical_integrity_status`. |
| Stage 9 Phase 1/2 provenance and resampling | [UNRESOLVED] | Carried forward unchanged. Locator: `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L93-L99`. |
| n5 Phase 3 supersession | [SUPERSEDED] | Carried forward unchanged: n5 run `27598417789` is audit history only; n10 run `27621106006` is manuscript-evidence candidate. Locator: `local-sha256:14500d3591e5b6c3bebecc7c30da09faf2f5c4baae937b67f7b4c51e7d789ef1:paper_notes/PHASE3_TABLES.csv:row 33; named columns evidence_id,claim_or_object,metric,value,statistical_integrity_status`. |

## Handoff

Completed:
- [DIRECT] Created `paper_notes/BIBLIOGRAPHIC_LEDGER.csv` with DOI/arXiv/venue/source-locator fields and topic-bucket classification.
- [DIRECT] Created `paper_notes/RELATED_WORK_NOTES.md` with separate related-work maps for MAS/BDI, Q-learning for building automation, KG/stereotype priors, physics-informed learning, anomaly/fault detection, and learned temporal/process dynamics.
- [SUPERSEDED] Rejected wrong Brick DOI candidate and recorded corrected DOI.
- [DIRECT] No workflow, experiment, statistical recomputation, branch switch, reset, clean, delete, or artifact overwrite was performed.

Unresolved:
- [UNRESOLVED] DOI-only Crossref rows listed in Evidence Gaps need full-text review before technical details beyond metadata are used.
- [UNRESOLVED] Exact Phase 3 workflow_dispatch input payload remains `NOT FOUND`.
- [UNRESOLVED] Phase 3 local ZIP byte identity remains `NOT VERIFIED`.
- [UNRESOLVED] Formal post-pivot preregistration remains `NOT FOUND`.
- [UNRESOLVED] Stage 9 Phase 1/2 provenance and bootstrap-resampling gaps remain open.

Next stage must read:
- `paper_notes/00_PROTOCOL.md`
- `paper_notes/RELATED_WORK_NOTES.md`
- `paper_notes/BIBLIOGRAPHIC_LEDGER.csv`
- `paper_notes/PHASE3_METHODS.md`
- `paper_notes/PHASE3_RESULTS.md`
- `paper_notes/PHASE3_TABLES.csv`
- `paper_notes/PHASE3_FIGURES.md`
- `paper_notes/SOURCE_LEDGER.csv`
- `paper_notes/CLAIM_LEDGER.csv`
- `paper_notes/RUN_LEDGER.csv`
- `paper_notes/EVIDENCE_GAPS.md`
- `analysis/phase3_dynamics.py`
- `config/run_config.json`
- `.github/workflows/phase3.yml`
- `src/agt/illuminance_controller_agent_dynamics.asl`
- `src/env/tools/DynamicsLearner.java`
- `phase3_download_n10/phase3-consolidated/`
