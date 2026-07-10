# Phase 3 Methods Evidence Notes

Stage: `10A`
Created: `2026-06-18T09:59:42Z`
Scope: evidence extraction only. This is not polished thesis prose.

## Control Record

| item | label | evidence record |
|---|---|---|
| Protocol discipline | [DIRECT] | Evidence extraction requires separate `AUDIT HISTORY` and `MANUSCRIPT EVIDENCE`, immutable locators, derived-result commands, and unresolved gap records. Locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236`. |
| Stage 9 handoff read | [DIRECT] | Stage 9 required Stage 10A to read protocol, Stage 9 notes/tables/script/git audit, Phase 1/2 result products, and ledgers. Locator: `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L100-L117`. |
| Required carry-forward gaps | [UNRESOLVED] | Exact Phase 1/2 dispatch inputs, Phase 1/2 artifact ZIP identity, Stage 6/8 resampling reproduction, formal post-pivot preregistration, lab3 stale-magnitude documentation, and dirty-doc numeric-source limits remain open. Locator: `local-sha256:26a38dee69a3084e63b91796dad640761cf2948609ff43c663ff083243e2f589:paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md:L93-L99`. |

## Source Anchors

| anchor | label | locator |
|---|---|---|
| P3-PROTOCOL | [DIRECT] | `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L1-L236` |
| P3-ADVISOR | [DIRECT] | `local-sha256:dfaa0d69824f99afc55422f384899a9a9ab128a1a50aff9cd0266bbc0635b8e1:C:/Users/esrad/Downloads/advisor_notes_and_other_info.txt:L21-L24` |
| P3-PIVOT | [DIRECT] | `local-sha256:530c856971c8250db4c27f312468a424c24d77f285004594b6d68d9f243b8029:THESIS_PIVOT_MASTER.md:L48-L56` |
| P3-RUN-SOURCE | [DIRECT] | Actual n=10 run head SHA: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53`. Phase 3 source/config locators below use this commit unless stated otherwise. |
| P3-RESULT-N10 | [DIRECT] | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`. |
| P3-RAW-N10 | [DIRECT] | `local-tree-sha256:2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945:phase3_download_n10/phase3-consolidated`. |
| P3-ANALYSIS | [DIRECT] | `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L1-L575`. |

## Conceptual Approach

| item | label | evidence |
|---|---|---|
| Research opportunity | [DIRECT] | Advisor notes frame Phase 3 as learning process dynamics, adding response-time knowledge to the KG, and using temporal goals such as immediate versus within five minutes. Locator: `P3-ADVISOR`. |
| Project goal | [DIRECT] | Pivot master states Phase 3 should learn actuation delays, write `ws:responseDelay` / `ResponseDelay` back to the KG, and use it for time-bounded goals. Locator: `P3-PIVOT`. |
| Conceptual separation | [DIRECT] | `task_dynamics.jcm` says the agent does not train a Q-table; it probes actuators, writes learned `ws:responseDelay`, and then exploits that knowledge. Locator: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:task_dynamics.jcm:L10-L18`. |
| Baseline and treatment | [DIRECT] | `ql_true` is KG-primed and uses learned per-actuator delay; `ql_false` is tabula-rasa and assumes zero delay. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:task_dynamics.jcm:L16-L18`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L94-L99`. |

## Experiment Record

| field | evidence note |
|---|---|
| Experiment id | `EXP-P3-DYN-N10`. |
| Research status | `ENGINEERING_VALIDATION; POST_HOC_EXPLORATORY`. The n=10 sweep is a confirmatory top-up in local documentation, but formal post-pivot preregistration remains `NOT FOUND`; do not label as `PRE_REGISTERED_CONFIRMATORY`. Gap locator: `local-sha256:cee8c61e08079b529e9e782b31f43c41d2cd68bb8bf78884d32a70e38ba77c80:paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv:row 20; named columns evidence_id,value,statistical_integrity_status`; dirty-doc expectation locator: `local-sha256:0d30b28c54c818173f40e817480682d62c67b267bfbf018d6dd9233ee311a4e4:docs/PHASE2_TO_PHASE3_CHANGES.md:L632-L634`. |
| Research question | Whether a MAS agent can probe actuator response delays, write learned temporal dynamics into the KG, and use that knowledge to satisfy time-bounded illuminance goals better than a delay-blind planner. Sources: P3-ADVISOR; P3-PIVOT; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L21-L29`. |
| Prior expectation | Learned blind delay should approximate configured `blind_delay_ticks=12`; `ql_true` should meet tight deadlines while `ql_false` should miss tight deadlines because it assumes zero delay. Sources: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L323-L365`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L21-L33`. |
| Baseline | `ql_false`: tabula-rasa planner, learned table may exist on disk but planner belief sets delay to zero. Source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L94-L99`. |
| Treatment | `ql_true`: KG-primed planner uses materialised learned delays from the probe phase. Sources: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L94-L99`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L390-L398`. |
| Independent variables | Profile: `lab2_slow`, `lab3_slow`; mode: `ql_true`, `ql_false`. Source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L324-L325`. |
| Dependent variables | Delay accuracy fields in `phase3_delay_accuracy.csv`; compliance and energy fields in `phase3_compliance_ci.csv`; paired differences and tests in `phase3_compliance_paired.csv`. Source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L48-L51`. |
| Controlled variables | `seconds_per_tick=5.0`, `blind_delay_ticks=12`, `probes_per_actuator=8`, `settle_ms=400`, `poll_ms=50`, `max_wait_ticks=60`, target rank `3`, probe sun rank `900`, six time-bounded goals. Source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L326-L365`. |
| Replicas and stopping | n=10 authority has 10 replica directories and 40 delay CSVs plus 40 timebounded CSVs. Derived from `P3-RAW-N10` by `Get-ChildItem` and `Import-Csv`: delay files `40`, delay rows `180`, timebounded files `40`, timebounded rows `240`, TTL files `40`, rep dirs `10`. Table row: `P3T-012`. |
| Metrics | Delay accuracy: slowest learned blind ticks versus ground-truth ticks and response class split. Compliance: per-replica overall/tight/loose compliance, total energy, mean actual delay. Paired metrics: `ql_true - ql_false`, bootstrap CI/p, Wilcoxon p, Cliff's delta, BH q-values. Source: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L21-L51`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L366-L471`. |
| Statistical method | Bootstrap CI and paired bootstrap use helpers from `analysis.sweep_report` where available; fallback seed is `0xC1`; Wilcoxon, Cliff's delta, and BH q-values are computed in `write_compliance_paired`. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L66-L86`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L394-L471`. |
| Exclusions | No Stage 10A exclusion of raw Phase 3 rows. `phase3_dynamics.py` skips unreadable/empty CSVs and continues best-effort; in the n=10 local raw tree, Stage 10A counted 40/40 expected delay and timebounded CSVs. Sources: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L205-L216`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L275-L283`; table row `P3T-012`. |
| Unexpected or nuanced observations | Lab3 `ql_true` loose-goal blind labels are not actuator-label bit-identical across all n=10 replicas: goals `g3`, `g4`, and `g6` split 5/5 between `SetZ1Blinds=ON` and `SetZ2Blinds=ON`, while met outcomes remain stable. Derived row: `P3T-031`. |
| Follow-up analysis | Stage 10A reran `analysis/phase3_dynamics.py` on n=10 and n=5 raw trees. n=10 command: `python analysis/phase3_dynamics.py --root phase3_download_n10/phase3-consolidated/dynamics_root --out paper_notes/stage10a_phase3_recompute_n10`. n=5 command: `python analysis/phase3_dynamics.py --root phase3_download/phase3-consolidated/dynamics_root --out paper_notes/stage10a_phase3_recompute_n5`. Script: `P3-ANALYSIS`. |

## Implementation Mapping

| component | label | method evidence |
|---|---|---|
| Runtime config | [DIRECT] | `phase3` block declares profiles, modes, timing constants, probe budget, simulator flow/port map, expected state dimensions, and six time-bounded goals. Locator: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:config/run_config.json:L322-L365`. |
| CI workflow | [DIRECT] | Run-head workflow is `workflow_dispatch`; inputs include profiles, replicas, probes, and `publish_results`. At run head `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, the workflow default for replicas is `1,2,3,4,5`; the n=10 run therefore must be supported by artifact/run evidence rather than run-head default. Locator: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L39-L59`; run evidence: `P3T-008` through `P3T-012`. |
| Current default after n=10 top-up | [DIRECT] | Later branch commit `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` changes the workflow `replicas` dispatch default from `1..5` to `1..10`. Locator: `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L46-L49`; diff locator: local command `git diff 3bb5289c36cb3093228ec0609fe57ec676b1ee53 eda6ca1ffa026e723ad1a18a2bdb3aed927e7433 -- .github/workflows/phase3.yml`. |
| Orchestrator | [DIRECT] | `run_phase3_dynamics.ps1` starts the matching slow Node-RED flow, runs `gradlew taskDynamics`, forwards probe parameters, watches for result CSV completion, parses delay/results tables, and summarizes `Met`, `Energy`, and `BlindTicks`. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:run_phase3_dynamics.ps1:L6-L33`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:run_phase3_dynamics.ps1:L227-L296`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:run_phase3_dynamics.ps1:L370-L451`. |
| Agent probe phase | [DIRECT] | Agent enumerates action metadata, probes actuator-bearing actions, records first-effect delays and action effects/costs, writes learned dynamics TTL and delay CSV. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L207-L238`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L293-L388`. |
| Agent exploit phase | [DIRECT] | Planner chooses the lowest-energy actuator whose believed delay fits the deadline; `ql_true` uses learned delay and `ql_false` assumes zero. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L403-L469`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/agt/illuminance_controller_agent_dynamics.asl:L428-L443`. |
| DynamicsLearner | [DIRECT] | CArtAgO artifact accumulates delay samples with Welford mean/variance, writes `ws:responseDelay`, `ws:responseDelayTicks`, sample count, std ticks, response class, delay table, and exploit-result table. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L13-L52`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L121-L155`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L176-L220`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L241-L320`. |
| Slow lab ontologies | [DIRECT] | `building_2_slow.ttl` and `building_3_slow.ttl` define response-delay vocabulary but do not assert numeric delay values; motorized blind is qualitatively delayed. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_2_slow.ttl:L38-L44`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_2_slow.ttl:L78-L102`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_3_slow.ttl:L39-L44`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/building_3_slow.ttl:L82-L106`. |
| Slow TDs and flows | [DIRECT] | TDs expose status `Tick` and blind action affordances; Node-RED flows implement 12-tick blind lag and deterministic physics. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/interactions-lab2_slow.ttl:L10-L15`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/interactions-lab2_slow.ttl:L27-L51`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/interactions-lab3_slow.ttl:L10-L15`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/resources/interactions-lab3_slow.ttl:L27-L53`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:simulator/simulator_flow_lab2_slow.json:L130-L130`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:simulator/simulator_flow_lab3_slow.json:L130-L130`. |

## Methods Boundary Notes

- [DIRECT] Phase 3 does not modify Phase 1/2 result claims; the Stage 10A manuscript scope is the final Phase 3 problem, approach, evaluation design, findings, and limitations. Evidence protocol: `P3-PROTOCOL`.
- [UNRESOLVED] Exact Phase 3 dispatch input payload for run `27621106006` is `NOT FOUND` in Stage 10A. Run metadata and artifacts prove a successful `workflow_dispatch`, head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, and 10 replica directories. Evidence rows: `P3T-008` through `P3T-012`.
- [UNRESOLVED] Artifact digest exists for `phase3-consolidated`, but Stage 10A did not redownload the ZIP and verify local extracted bytes against artifact digest. Evidence row: `P3T-033`.
- [INTERPRETATION] Use `n=10 authority candidate` for manuscript results; use n=5 only in `AUDIT HISTORY` as superseded by the Wilcoxon-floor top-up. Evidence row: `P3T-032`.
