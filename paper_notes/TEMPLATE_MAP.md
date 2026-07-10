# Stage 1 Template Map

## Stage 1 Refresh 2 - Template Recheck

This section is the current Stage 1 template-routing authority after the
Stage 0R2 repository refresh. The older template-routing sections below remain
AUDIT HISTORY.

- [DERIVED] External template root remains
  `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport`.
  The tree contains `18` regular files and `200324` bytes.
  Inputs: external template root and
  `local-sha256:c51fa5b147f93587839482e15e695dcc65b550005084fc370097028005820fdd:paper_notes/TREE_SHA256_V1.mjs:L1-L76`.
  Exact command:
  `node paper_notes\TREE_SHA256_V1.mjs 'C:\Users\esrad\Downloads\Template-ThesisReport\Template-ThesisReport'`.
- [INTERPRETATION] The current evidence-routing destination remains the same as
  the Stage 1 refresh: repository evidence is mapped into the template as notes,
  tables, figure specifications, and evidence records, not polished thesis prose.
  Locators:
  `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L14`;
  `local-sha256:0fc9679a9ab9f5b53a2ce5ae9fcb4ee654c29a1111e4135defdd6cd3df03da1c:paper_notes/TEMPLATE_MAP.md:L28-L52`.

### Stage 1R2 Evidence-to-Template Routing

| Template destination | Current evidence categories | Boundary |
|---|---|---|
| `content/01_chapter1.tex` / Introduction | Requirement source, final research problem, scoped three-phase trajectory, contribution overview | Use only source-backed claims; no result values from dirty docs |
| `content/02_chapter2.tex` / Background and Related Work | MAS/JaCaMo, Q-learning, Semantic Web/KG, RDF/Turtle, WoT/BRICK, stereotypes, process dynamics, related systems | Keep background foundations separate from related-work comparison; external literature still needs ledgers |
| `content/03_chapter3.tex` / Contributions | Clean-lab ladder, semantic prior mechanism, cross-zone structural prior, Phase 2 expected-vs-actual detector/blacklist/re-learning, Phase 3 response-delay learning and KG writeback | Separate conceptual approach from implementation detail |
| `content/04_chapter4.tex` / Evaluation | Experiment records, baselines/treatments, variables/controls, scenarios, seeds/replicas, metrics, statistical scripts, run IDs, committed CSV/JSON rows, unexpected results, follow-up analyses | Every numeric result requires CSV/JSON/Actions row locators or complete derived-chain records |
| `content/05_chapter5.tex` / Conclusions | Final active claim-ledger rows, bounded limitations, future work | Superseded and exploratory findings remain explicitly labeled |
| `content/abstract.tex` / Abstract | Problem, method, strongest supported result slots, strongest limitation | Fill after evidence extraction; Stage 1 routing claims are excluded |
| `content/appendix.tex` / Appendix | Reproduction commands, workflows, run/artifact provenance, profile/config matrices, schemas, full tables/figures, gap/audit indexes | Dependencies, caches, build products, and runtime directories excluded unless uniquely evidentiary |

## Stage 1 Refresh - Current Template Routing

This section is the current Stage 1 routing authority for the external
`Template-ThesisReport` tree. The earlier Stage 1 template map below remains
AUDIT HISTORY.

- [DERIVED] External template root:
  `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport`.
- [DERIVED] The refreshed template tree contains `18` regular files and
  `200324` bytes.
  Inputs: external template root and
  `local-sha256:c51fa5b147f93587839482e15e695dcc65b550005084fc370097028005820fdd:paper_notes/TREE_SHA256_V1.mjs:L1-L76`.
  Exact command:
  `node paper_notes\TREE_SHA256_V1.mjs 'C:\Users\esrad\Downloads\Template-ThesisReport\Template-ThesisReport'`.
  Command-log locator:
  `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L27-L27`.
- [DIRECT] The template was read only and was not edited in this refresh.
  Locator:
  `local-sha256:0267e8c94e34bf9a433bc971980a20e6ad1838b1213a7ccd7d891c22d9bc9586:paper_notes/STAGE1_REFRESH_WORKTREE_STATUS_20260616T194231Z.md:L15-L16`.

### Current Template File Routing

| Template path | Direct role | Current evidence routing | Immutable locator |
|---|---|---|---|
| `thesis.tex` | Main assembly, front matter, chapter includes, bibliography, appendix, declaration include | Assembly target only; do not embed evidence notes until manuscript-writing stage | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L101-L168` |
| `content/abstract.tex` | Abstract placeholder | Fill last from final active claim-ledger rows only | `local-sha256:8ecddd6b428abf6e1535ba6f14c4560bdfccae017b265cc2d783a1536f7d1b2b:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/abstract.tex:L1-L6` |
| `content/01_chapter1.tex` | Introduction placeholder | Problem, scope, research questions, contributions, and roadmap; no numeric results until row extraction | `local-sha256:da0e8717e7a3d474eaf268040d1d3fb524c0413c830f4afdabcc1f0c26485166:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/01_chapter1.tex:L1-L2` |
| `content/02_chapter2.tex` | Background and Related Work placeholder | Foundations first; related-work comparison in distinct subsections | `local-sha256:fef5a72e4a35c44ba72f4ef81c0adf657d2038ad1706654dbf06157a362faa81:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/02_chapter2.tex:L1-L4` |
| `content/03_chapter3.tex` | Contributions placeholder | Conceptual approach: clean lab, semantic prior, fault recognition, process dynamics; implementation/reproducibility subsection after mechanisms | `local-sha256:278fff839b8eab0c7fa810f94acc960a20d5e2daa6fab34fd3792f3783a38474:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/03_chapter3.tex:L1-L2` |
| `content/04_chapter4.tex` | Evaluation placeholder | Experiment records, metrics, statistical procedures, results, unexpected observations, follow-up analyses, threats to validity | `local-sha256:9253ea9c86c28f37e24ebc51405931292d7b0d5686e77975dc388d6354b9a5b0:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/04_chapter4.tex:L1-L2` |
| `content/05_chapter5.tex` | Conclusions placeholder | Supported RQ answers, contribution summary, limitations, future work | `local-sha256:cf218913c4698a8c5bfaf6b25381d8f804a964da7d9d032faeaaf48ab16b53f3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/05_chapter5.tex:L1-L2` |
| `content/appendix.tex` | Appendix placeholder | Reproduction commands, profile/config matrices, schemas, run/artifact provenance, full tables, supplementary figures, audit index | `local-sha256:6203cfe7864a04577cf766f12fa28991ac2336f82a0958f2f38f952c3b19579d:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/appendix.tex:L1-L1` |
| `references.bib`, `memoir-format/`, `figures/hsg-logo/`, `HSGlogo.sty` | Bibliography, layout, logo, and formatting support | Bibliographic and formatting infrastructure only; project-local PDF identity still requires separate source audit | `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport` |

### Current Evidence-to-Section Map

| Template destination | Evidence categories to route | Source boundary |
|---|---|---|
| Introduction | Advisor/user requirement source, pivot requirement, final three-part research trajectory, contribution list, scope limitations | Requirement and documentation sources are not empirical evidence |
| Background and Related Work | MAS/JaCaMo, RL/Q-learning, Semantic Web/KG, stereotypes, WoT/BRICK, process dynamics, related systems | External literature sources still need source-ledger entries before citation |
| Contributions | Lab ladder, semantic prior mechanism, cross-zone structural prior, Phase 2 detector/blacklist/re-learn, Phase 3 response-delay learning and KG writeback | Keep conceptual approach separate from code-level implementation details |
| Evaluation | Per-experiment records, run IDs, baselines/treatments, variables/controls, metrics, statistical scripts, verified rows, unexpected results, follow-up analysis | Every number must cite committed result rows, Actions rows, or a complete derived chain |
| Conclusions | Final active claim-ledger rows and bounded limitations | Superseded findings remain audit history |
| Abstract | Problem, method, principal supported result slots, strongest limitation | Fill after result extraction, not from Stage 1 inventory |
| Appendix | Commands, configs, schemas, full tables/figures, run/artifact ledgers, deviations, provenance audit | Dependencies/caches excluded unless uniquely evidentiary |

## Template Snapshot

- [DERIVED] External template root:
  `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport`.
- [DERIVED] Snapshot contains 18 regular files and 200324 bytes.
  Inputs: external template root and
  `local-sha256:c51fa5b147f93587839482e15e695dcc65b550005084fc370097028005820fdd:paper_notes/TREE_SHA256_V1.mjs`.
  Exact command:
  `node paper_notes/TREE_SHA256_V1.mjs 'C:\Users\esrad\Downloads\Template-ThesisReport\Template-ThesisReport'`.
  Runtime: Node.js `v22.14.0`.
- [DIRECT] The external template was read only and was not edited in Stage 1.

## File Structure

| Template path | Direct role | Proposed evidence routing | Immutable locator |
|---|---|---|---|
| `thesis.tex` | Document class, packages, metadata, front matter, chapter includes, bibliography, appendix, declaration | Main assembly only; no research notes should be embedded here until manuscript-writing stage | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L1-L168` |
| `content/abstract.tex` | Abstract placeholder | Final problem, approach, principal findings, and limitations after claim review | `local-sha256:8ecddd6b428abf6e1535ba6f14c4560bdfccae017b265cc2d783a1536f7d1b2b:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/abstract.tex:L1-L6` |
| `content/01_chapter1.tex` | Introduction chapter | Motivation, problem, research questions, scope, contributions, roadmap | `local-sha256:da0e8717e7a3d474eaf268040d1d3fb524c0413c830f4afdabcc1f0c26485166:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/01_chapter1.tex:L1-L2` |
| `content/02_chapter2.tex` | Combined Background and Related Work chapter | Foundations first; related-work comparison in a distinct later subsection | `local-sha256:fef5a72e4a35c44ba72f4ef81c0adf657d2038ad1706654dbf06157a362faa81:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/02_chapter2.tex:L1-L4` |
| `content/03_chapter3.tex` | Contributions chapter | Conceptual approach, lab design, mechanisms, then implementation/reproducibility subsection | `local-sha256:278fff839b8eab0c7fa810f94acc960a20d5e2daa6fab34fd3792f3783a38474:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/03_chapter3.tex:L1-L2` |
| `content/04_chapter4.tex` | Evaluation chapter | Research design, experiments, metrics/statistics, results, critical discussion, threats | `local-sha256:9253ea9c86c28f37e24ebc51405931292d7b0d5686e77975dc388d6354b9a5b0:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/04_chapter4.tex:L1-L2` |
| `content/05_chapter5.tex` | Conclusions chapter | Answers to RQs, contribution summary, limitations, future work | `local-sha256:cf218913c4698a8c5bfaf6b25381d8f804a964da7d9d032faeaaf48ab16b53f3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/05_chapter5.tex:L1-L2` |
| `content/appendix.tex` | Appendix chapter | Reproduction package, full tables, supplementary figures, configs, schemas, run ledger excerpts | `local-sha256:6203cfe7864a04577cf766f12fa28991ac2336f82a0958f2f38f952c3b19579d:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/appendix.tex:L1-L1` |
| `references.bib` | Bibliography database | Background and related-work sources; project-local PDF identity must be resolved before entry | `local-tree-sha256:a60bff22cc24edeb04ef85a1c47d5cfc34e10535ed68898f674a2d194d428e9e:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport` |
| `memoir-format/*.tex`, `HSGlogo.sty` | Layout, theorem, macro, and package support | Formatting infrastructure only | Same template-tree locator |
| `figures/hsg-logo/*` | Institutional logo assets | Front matter only | Same template-tree locator |

## Main Assembly Order

| Order | Included file | Locator |
|---:|---|---|
| 1 | `content/abstract.tex` | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L101-L119` |
| 2 | `content/01_chapter1.tex` | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L142-L153` |
| 3 | `content/02_chapter2.tex` | same locator as order 2 |
| 4 | `content/03_chapter3.tex` | same locator as order 2 |
| 5 | `content/04_chapter4.tex` | same locator as order 2 |
| 6 | `content/05_chapter5.tex` | same locator as order 2 |
| 7 | Bibliography from `references.bib` | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L156-L157` |
| 8 | `content/appendix.tex` | `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L160-L162` |

## Proposed Note Slots

The following is a Stage 1 routing specification, not manuscript prose.

### `content/01_chapter1.tex` - Introduction

| Proposed subsection | Evidence categories | Required status before writing |
|---|---|---|
| Problem context | Smart-building control, MAS, semantic descriptions, RL exploration | Background sources and project requirement source verified |
| Research problem | Clean-lab benefit of physics/KG priors; fault recognition and post-fault re-learning | Advisor source gap disclosed; final RQs extracted from primary requirement documents |
| Research questions | Phase 1 acceleration; Phase 2 recognition/recovery; Phase 3 only if implemented | One atomic claim record per RQ; Phase 3 currently `NOT FOUND` |
| Contributions | Lab ladder, semantic prior mechanism, fault-management mechanism, reproducible pipeline | Mapped to committed implementation sources |
| Scope | Clean versus faulty environments; exclusions; no automatic Phase 3 claim | Explicit limitations and gap records |
| Thesis structure | Chapter roadmap | Template mapping only |

Primary routing sources:
`local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L5-L61`;
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/PHASE1_TO_PHASE2_CHANGES.md:L10-L31`.

### `content/02_chapter2.tex` - Background and Related Work

| Proposed subsection | Evidence categories | Boundary |
|---|---|---|
| Multi-Agent Systems and JaCaMo | Jason agents, CArtAgO artifacts, environment interaction | Foundations only; no project evaluation |
| Reinforcement learning | Tabular Q-learning, exploration, convergence/learning speed | General theory plus project notation |
| Semantic Web and knowledge graphs | RDF/Turtle, SPARQL, WoT TDs, BRICK/ontology concepts | General foundations before project-specific KG |
| Component stereotypes | Prior/action constraints and expected effects | Explain concept; project mechanism belongs in Contributions |
| Hybrid semantic-RL systems | Literature comparison | Requires external source ledger; repository docs alone are insufficient |
| Fault-aware/adaptive control | Literature comparison for detection, isolation, recovery | Distinct from project implementation |

[INTERPRETATION] The template combines Background and Related Work in one file;
the two functions should remain separate subsections.
Locator: `local-sha256:fef5a72e4a35c44ba72f4ef81c0adf657d2038ad1706654dbf06157a362faa81:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/content/02_chapter2.tex:L1-L4`.

### `content/03_chapter3.tex` - Contributions

| Proposed subsection | Repository evidence | Boundary |
|---|---|---|
| Research design overview | Clean lab ladder -> fault ladder | Conceptual design only |
| Environment and knowledge model | `src/resources`, `simulator`, profiles | Explain modeled physics and semantic structure |
| Stereotype-guided Q-learning | `QLearner`, `StereotypeReasoner`, QL agent | No result values |
| Cross-zone structural prior | coupling branches, KG resources, mechanism audit | Separate design from empirical effect |
| Fault recognition and isolation | detector, blacklist, attribution/abstention | Explain expected-vs-actual mechanism |
| Warm restart and re-learning | adapt agent, recovery policy, survivor action set | Explain mechanism and criteria |
| Implementation and reproducibility | tasks, config, workflows, versioning | Concrete mapping after conceptual sections |
| Phase 3 status | `NOT FOUND` implementation/result evidence | Do not present as a contribution |

Key locators:
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L18-L45`;
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/env/tools/QLearner.java:L229-L293`;
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:src/agt/lab_profiles.asl:L305-L482`;
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/PHASE1_TO_PHASE2_CHANGES.md:L33-L189`.

### `content/04_chapter4.tex` - Evaluation

| Proposed subsection | Evidence categories | Required experiment record fields |
|---|---|---|
| Evaluation questions and status | Pre-registration, registered deviations, post-hoc studies | research question, prior expectation, confirmatory/exploratory classification |
| Experimental system | labs, profiles, scenarios, workflows, run heads | baseline, treatment, variables, controls |
| Metrics | training, benchmark, detection, recovery, goal-rate | definitions and source columns |
| Statistical method | bootstrap CIs, paired tests, Wilcoxon, effect sizes, BH families | exact script SHA and command |
| Phase 1 experiments | clean-lab comparisons, controls, mechanism follow-ups, replication | one design record per run/experiment |
| Phase 2 experiments | fault profiles, detection, recovery, measurement corrections | preserve superseded iterations in audit only |
| Results | final verified tables and figures | every number cites CSV row/columns or derived chain |
| Critical discussion | unexpected results, failed assumptions, follow-ups | separate from result statements |
| Threats to validity | provenance, simulator realism, seed/sample limits, exclusions | source-backed and bounded |

Pre-registration locator:
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:docs/pre_registration.md:L17-L138`.
Analysis locators:
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/sweep_report.py:L281-L405`;
`phase2-fault-detection@985c7a18558b6d5cb96c018a395b0aae6389f410:analysis/phase2_recovery.py:L27-L40`.

### `content/05_chapter5.tex` - Conclusions

| Proposed subsection | Allowed evidence | Excluded evidence |
|---|---|---|
| Answers to research questions | Final ACTIVE claim-ledger rows only | Superseded or in-progress results |
| Contribution summary | Verified conceptual and empirical contributions | File chronology |
| Limitations | Final threat/gap records | Unsupported generalization |
| Future work | Phase 3 temporal dynamics may appear as future work while implementation remains `NOT FOUND` | Claim that Phase 3 was completed |

### `content/abstract.tex` - Abstract

Required evidence slots, to be filled last:

1. [UNRESOLVED] problem and scope;
2. [UNRESOLVED] method/contribution;
3. [UNRESOLVED] principal Phase 1 result;
4. [UNRESOLVED] principal Phase 2 result;
5. [UNRESOLVED] strongest limitation/qualification.

No abstract sentence should be drafted from Stage 1 inventory notes.

### `content/appendix.tex` - Appendix

| Proposed appendix block | Evidence |
|---|---|
| Reproduction commands and software versions | workflows, PowerShell runners, Gradle tasks |
| Complete profile/lab matrix | `lab_profiles.asl`, `run_config.json`, simulator flow map |
| Scenario and metric schemas | benchmark JSON, logger output definitions |
| Statistical commands and derivation chains | analysis scripts and exact commands |
| Full supplementary tables | verified CSV outputs |
| Additional figures | learning curves, heatmaps, mechanism diagnostics |
| Run and artifact provenance | run IDs, URLs, head SHAs, artifact IDs/digests, tree hashes |
| Deviations and superseded analyses | concise audit index; full chronology remains in `paper_notes` |

## Figure and Table Routing Specifications

| Artifact specification | Target | Candidate generator/source | Status |
|---|---|---|---|
| System architecture diagram: agent -> artifacts -> KG -> simulator -> logs | Contributions | committed architecture sources | [UNRESOLVED] figure not yet specified at node/edge level |
| Clean-lab progression diagram | Contributions/Evaluation | profiles and clean simulator flows | [UNRESOLVED] |
| Phase 2 detect -> blacklist -> warm restart -> certify flow | Contributions | QLearner + adapt agent + change document | [UNRESOLVED] |
| Experiment matrix table | Evaluation | config, profiles, workflows, run ledger | [UNRESOLVED] until experiment records complete |
| Phase 1 learning-speed/first-goal table | Evaluation | `analysis/sweep_report.py` outputs | [UNRESOLVED] final run selection pending |
| Phase 1 learning curves | Evaluation | `analysis/learning_curves.py` | [UNRESOLVED] derivation chain pending |
| Phase 2 detection/recovery table | Evaluation | `analysis/phase2_recovery.py` outputs | [UNRESOLVED] later run pending |
| Threats-to-validity table | Evaluation/Conclusions | gap ledger and experiment records | [UNRESOLVED] |

## Template Gaps and Decisions

- [DIRECT] No dedicated Implementation chapter is included by the template.
  Locator: `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L148-L153`.
- [INTERPRETATION] Place conceptual approach first in Contributions, followed by
  a bounded implementation/reproducibility subsection; move full technical detail
  to the Appendix.
- [DIRECT] No dedicated Discussion chapter is included by the template.
  Same locator as above.
- [INTERPRETATION] Place critical discussion and threats after Evaluation results,
  with only final synthesis in Conclusions.
- [UNRESOLVED] Conference-paper formatting requirements are `NOT FOUND`; this is
  an HSG thesis template, not a verified conference template.
- [UNRESOLVED] Declaration file `declaration-originality.pdf` is referenced by
  `thesis.tex` but was not present in the 18-file template tree.
  Locator: `local-sha256:e307ade8278833b506bbc44ac8a0f15f6fd508233cbf6de19d5c5b9396008ea3:C:/Users/esrad/Downloads/Template-ThesisReport/Template-ThesisReport/thesis.tex:L164-L168`.
