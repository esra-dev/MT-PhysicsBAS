# 00 — Factual Inventory

**Generated:** 2026-07-07  
**Working branch at time of audit:** `phase2-instant-blacklist`  
**HEAD commit:** `ba0303e35616e59c8fbcfd6bed48592943e746a4` — 2026-07-07 19:55 +0200  
**Era note:** All items are labelled **[OLD]** (custom8/custom9 era, W1–W6 weakness labs, sweep-dev/sweep-paper/sweep-ablation workflows) or **[NEW]** (phase-based approach, lab1/lab2/lab3/labmon/lab4/lab5 labs, phase1–4 workflows).  

---

## A. Top-Level Folder / File Structure

| Path | Era | Purpose |
|---|---|---|
| `src/` | both | JaCaMo application source (`agt/`, `env/`, `resources/`, `test/`) |
| `config/` | [NEW] | Runtime config (`run_config.json`, `run_config.schema.json`) |
| `simulator/` | both | Node-RED flow JSON files for all lab profiles and faulty variants |
| `benchmark/` | both | Scenario JSON files; `results/` archive of per-cell CSV/JSONL artefacts |
| `analysis/` | both | Python analysis scripts (sweep report, phase-specific aggregators, tests) |
| `docs/` | both | Design docs, phase transition notes, pre-registration, lab reference |
| `dashboard/` | both | Vite-based React monitoring dashboard |
| `scripts/` | [NEW] | Shared PowerShell helpers (config reader, artifact versioner, watchdog) |
| `.github/workflows/` | both | CI/CD workflows |
| `.node-red-<profile>/` | both | Per-profile Node-RED working directories (one per clean or faulty variant) |
| `log/` | both | JVM heap-dump target and runtime log output |
| `bin/` | both | Gradle build intermediate output |
| `build/` | both | Gradle compiled class output |
| `.gradle/` | both | Gradle wrapper cache |
| `.vscode/` | both | VS Code workspace settings |
| `.githooks/` | both | Local git hook scripts |
| `paper_notes/` | both | Loose notes for the paper |
| **Root-level CSV files** | [NEW] | Most-recent training/benchmark run outputs (metrics, Q-tables, coverage, first-goal, recovery, dynamics-delay, timebounded results) — see §F |
| `THESIS_PIVOT_MASTER.md` | [NEW] | Master design document for the Phase 1–4 pivot |
| `README.md` | both | Project overview |
| `task.jcm` | both | JaCaMo launch descriptor — rule-based agent |
| `task_ql.jcm` | [NEW] | JaCaMo launch descriptor — QL training agent |
| `task_bench.jcm` | both | JaCaMo launch descriptor — benchmark agent |
| `task_adapt.jcm` | [NEW] | JaCaMo launch descriptor — Phase-2 adapt agent |
| `task_dynamics.jcm` | [NEW] | JaCaMo launch descriptor — Phase-3 dynamics agent |
| `logging.properties` | both | JUL logging config |
| `build.gradle` | both | Gradle build file |
| `gradle.properties` | both | Gradle JVM/network properties |
| `gradlew` / `gradlew.bat` | both | Gradle wrapper scripts |

**Source sub-structure** (`src/`):

| Path | Purpose |
|---|---|
| `src/agt/` | Jason agent source files (`.asl`) |
| `src/env/tools/` | CArtAgO artifact Java sources (QLearner, LabEnvironment, etc.) |
| `src/env/tools/jia/` | Jason internal-action helpers (SystemProp, system_prop, system_prop_num) |
| `src/resources/` | Turtle ontology files (building KGs, interaction descriptions, WoT mappings) |
| `src/test/` | JUnit 5 unit tests |

**Results / phase output directories at root level** (all [NEW]):

| Directory | Contents |
|---|---|
| `phase1_xzone_ablation/`, `phase1_xzone_asis/`, `phase1_xzone_bumped/`, `phase1_xzone_bumped_s11_20/` | Phase-1 cross-zone ablation run artefacts |
| `phase2_binv_backfill/`, `phase2_ext_results/`, `phase2_results/`, `phase2_results_v2/` … `v6/` | Phase-2 fault-adapt run artefacts (multiple iterations) |
| `phase3_download/`, `phase3_download_n10/` | Phase-3 dynamics run artefacts |
| `phase4_confirm_download/`, `phase4_n20_download/`, `phase4_smoke_download/` | Phase-4 dependency/energy run artefacts |
| `tmp_step0_*`, `tmp_step2_validation/`, `tmp_sweep18_results/`, `tmp_sweep_n10_results/` | [OLD/audit] Temporary step-0 probe and sweep validation results |
| `labmon_ci_results/` | [NEW] labmon Phase-2.5 CI run artefacts |

---

## B. Build System

### `build.gradle`
**Source:** [build.gradle](../build.gradle)

| Item | Value | Line(s) |
|---|---|---|
| Default task | `task` (rule-based agent) | [build.gradle#L10](../build.gradle#L10) |
| Java plugin | `apply plugin: 'java'` | [build.gradle#L13](../build.gradle#L13) |
| Eclipse plugin | `apply plugin: 'eclipse'` | [build.gradle#L14](../build.gradle#L14) |
| Project version | `1.0` | [build.gradle#L16](../build.gradle#L16) |
| Project group | `org.jacamo` | [build.gradle#L17](../build.gradle#L17) |
| JVM heap (all JavaExec tasks) | `maxHeapSize = '4g'` | [build.gradle#L266](../build.gradle#L266) |
| JVM extra arg | `-XX:+HeapDumpOnOutOfMemoryError`, `-XX:HeapDumpPath=${rootDir}/log` | [build.gradle#L267-L268](../build.gradle#L267) |

**Gradle tasks:**

| Task | Type | JCM file | Description | Source line |
|---|---|---|---|---|
| `task` (default) | `JavaExec` | `task.jcm` | Rule-based illuminance controller | [build.gradle#L103](../build.gradle#L103) |
| `taskQl` | `JavaExec` | `task_ql.jcm` | QL training agent; `-Pprofile=<id>` → `active.profile` system property | [build.gradle#L113](../build.gradle#L113) |
| `taskBench` | `JavaExec` | `task_bench.jcm` | Benchmark agent; `-Pmode=<mode>` → `bench.mode` system property | [build.gradle#L130](../build.gradle#L130) |
| `taskAdapt` | `JavaExec` | `task_adapt.jcm` | [NEW] Phase-2 fault-detect/blacklist/re-learn; `-Pprofile` → `active.profile`, `-Pmode` → `adapt.mode`, `-Padapt.episodes` → `adapt.episodes` | [build.gradle#L148](../build.gradle#L148) |
| `taskDynamics` | `JavaExec` | `task_dynamics.jcm` | [NEW] Phase-3 response-delay learning; `-Pprofile` → `active.profile`, `-Pmode` → `dynamics.mode` | [build.gradle#L185](../build.gradle#L185) |
| `runFullSweep` | custom `doLast` | `task_bench.jcm` (via `javaexec`) | [OLD] Phase-5 sweep: iterates over `profiles × modes`, archives per-cell CSVs to `benchmark/results/<profile>/<mode>/` | [build.gradle#L305](../build.gradle#L305) |
| `validateTurtle` | `JavaExec` | — | Parses every `*.ttl` under `src/resources` via Jena; CI gate | [build.gradle#L373](../build.gradle#L373) |
| `preflight` | `doLast` (depends on `validateTurtle`) | — | Profile/scenario/port health checks before long sweep | [build.gradle#L382](../build.gradle#L382) |
| `test` | `Test` | — | JUnit 5 platform; tests under `src/test/java` | [build.gradle#L66](../build.gradle#L66) |

**`_httpKeys` forwarded to every JavaExec** (system properties passed from `-P` Gradle flags):  
`sim.http.connectMs`, `sim.http.responseMs`, `sim.http.maxRetries`, `sim.http.backoffMs`, `reward.clip`, `stereo.priorScale`, `stereo.priorDecayEpisodes`, `stereo.priorDecayFloor`, `stereo.priorRedundant`, `stereo.priorIVUnsat`, `stereo.initBonus`, `stereo.crossZoneBonus`, `stereo.energyPriorWeight`, `reward.shaping`, `stereo.adaptiveTrust`, `stereo.adaptiveTrust.minSamples`, `stereo.adaptiveTrust.floor`, `run.seed`, `seconds.per.tick`, `probe.settle.ms`, `probe.poll.ms`, `probe.max.wait.ticks`, `probe.hold.ticks`, `probe.count`, `dynamics.learner.minSamples`, `dynamics.instant.threshold.sec`  
**Source:** [build.gradle#L224-L244](../build.gradle#L224)

**Source sets:**

| Source set | Java dirs | Resources dirs |
|---|---|---|
| `main` | `src/env`, `src/agt`, `src/org`, `src/int`, `src/java` | `src/resources` |
| `test` | `src/test/java` | `src/test/resources` |

**Source:** [build.gradle#L80-L101](../build.gradle#L80)

### `gradle.properties`
**Source:** [gradle.properties](../gradle.properties)

| Property | Value |
|---|---|
| `org.gradle.problems.report` | `false` (disables incubating HTML report to avoid Windows VS Code import failures) |
| `systemProp.org.gradle.internal.http.connectionTimeout` | `120000` (ms) |
| `systemProp.org.gradle.internal.http.socketTimeout` | `120000` (ms) |

---

## C. Libraries and Dependencies

**Source:** [build.gradle#L37-L62](../build.gradle#L37)  
**Era:** [NEW] (current; also present in OLD era)

| Dependency | Version / Ref | Scope | Notes |
|---|---|---|---|
| `com.github.GiugAles:jacamo` | `SS2025` (JitPack snapshot) | `implementation` | JaCaMo multi-agent framework |
| `com.github.GiugAles:jacamo-hypermedia` | `SS2025-1` (JitPack snapshot) | `implementation` | JaCaMo Hypermedia extension |
| `com.github.Interactions-HSG:wot-td-java` | `master-SNAPSHOT` (JitPack snapshot) | `implementation` | W3C WoT Thing Description Java lib |
| `com.google.guava:guava` | `23.5-jre` | `implementation` | Google Guava utilities |
| `org.apache.httpcomponents.client5:httpclient5` | `5.0` | `implementation` | Apache HTTP Client 5 |
| `org.apache.httpcomponents.client5:httpclient5-fluent` | `5.0` | `implementation` | Apache HTTP Client 5 fluent API |
| `org.apache.jena:jena-arq` | `4.10.0` | `implementation` | Apache Jena RDF + SPARQL engine; used by `OntologyArtifact` |
| `ch.qos.logback:logback-classic` | `1.5.6` | `implementation` | SLF4J implementation (single logging provider) |
| `net.logstash.logback:logstash-logback-encoder` | `7.4` | `implementation` | JSON log lines for ELK/Loki |
| `org.slf4j:jul-to-slf4j` | `2.0.13` | `implementation` | Routes `java.util.logging` through SLF4J |
| `org.junit.jupiter:junit-jupiter` | `5.10.2` | `testImplementation` | JUnit 5 test platform |
| `org.mockito:mockito-core` | `5.11.0` | `testImplementation` | Mocking framework |

**Excluded transitive bindings** (SLF4J deduplication):  
`org.slf4j:slf4j-nop`, `org.slf4j:slf4j-log4j12`, `org.slf4j:slf4j-reload4j`  
**Source:** [build.gradle#L30-L35](../build.gradle#L30)

**Repositories:**  
`mavenCentral()`, `https://raw.githubusercontent.com/jacamo-lang/mvn-repo/master`, `https://repo.gradle.org/gradle/libs-releases`, `https://jitpack.io`  
**Source:** [build.gradle#L20-L25](../build.gradle#L20)

---

## D. GitHub Actions Workflows

All workflows live under [.github/workflows/](.github/workflows/).

### D.1 `ci.yml` — [OLD+NEW] Continuous Integration
**Source:** [.github/workflows/ci.yml](.github/workflows/ci.yml)  
**Triggers:** `push` to `main`, `pull_request` to `main`, `workflow_dispatch`  
**Java:** temurin 21, Node 20  

| Job | `needs` | What it does |
|---|---|---|
| `build-test` | — | Compiles (`gradlew classes`, 3-retry JitPack guard), runs `gradlew test`, uploads JUnit report |
| `validate-resources` | — | Runs `gradlew validateTurtle`, validates scenario JSONs in `benchmark/`, builds dashboard (`npm ci && npm run build`) |
| `preflight-offline` | `build-test`, `validate-resources` | Preflight gate with `skipSimProbe` (no running simulator required) |

**Produces:** JUnit HTML report artifact `junit-report`

---

### D.2 `phase1.yml` — [NEW] Phase 1: KG Acceleration on Clean Labs
**Source:** [.github/workflows/phase1.yml](.github/workflows/phase1.yml)  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase1` (cancel-in-progress: false)

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `profiles` | `lab1,lab2,lab3` | Comma-separated clean labs |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` | RNG seeds (Wilcoxon needs n≥6) |
| `run_mode` | `phase1` | run_config.json profile name |
| `publish_results` | `true` | Push to `results` branch |

**Job DAG:**

```
setup
  └─ train [profile × stereo × seed matrix]  (timeout: 180 min)
       └─ bench [profile × mode × seed matrix]  (timeout: 60 min)
            └─ aggregate  (sweep_report.py, phase1_results_*.md)
```

**setup outputs:** `profiles_json` (JSON array), `seeds_json` (JSON array of integers)  
**train matrix:** `profile ∈ inputs.profiles`, `stereo ∈ ["true","false"]`, `seed ∈ inputs.seeds`  
**bench matrix:** same `profile` × `mode ∈ ["rule_based","ql_false","ql_true"]` × `seed`  
**Produces:** per-cell training and benchmark artifacts uploaded via `actions/upload-artifact@v4`; consolidated results optionally pushed to `results` branch

---

### D.3 `phase2.yml` — [NEW] Phase 2: Fault Detection, Blacklist, Re-learn
**Source:** [.github/workflows/phase2.yml](.github/workflows/phase2.yml)  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase2`  
**Self-contained:** generates its own clean warm-start Q-tables per seed; does NOT require Phase 1 to have run first.

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `adapt_profiles` | 15 faulty profiles (lab1–3 f1dead/f1inv/f2dead/f2inv/f1dead_z2/f1inv_z2/f1bdead/f1binv, lab2 blind variants) | Comma-separated faulty profiles |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` | RNG seeds |
| `run_mode` | `phase1` | run_config.json profile for the clean warm-start training |
| `adapt_episodes` | `0` (use profile default; recovery ends on greedy-stable window) | Re-learn budget |
| `publish_results` | `true` | Push to `results` branch |

**Job DAG:**

```
setup
  ├─ train_clean [parent × stereo × seed]      (generates clean Q-tables)
  └─ (after train_clean) adapt [profile × mode × seed]  (warm-loads clean Q-table, runs taskAdapt)
       └─ aggregate  (phase2_recovery.py: per-cell CI + paired bootstrap + BH-FDR)
```

**Headline metric:** `RecoveryEpisodes = ReconvergeEpisode − DetectEpisode`

---

### D.4 `phase3.yml` — [NEW] Phase 3: Process Dynamics, Response-Delay Learning
**Source:** [.github/workflows/phase3.yml](.github/workflows/phase3.yml)  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase3`  
**No Q-table training phase** — dynamics agent probes actuator timing only.

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `dynamics_profiles` | `lab2_slow,lab3_slow` | Comma-separated slow profiles |
| `replicas` | `1,2,3,4,5,6,7,8,9,10` | Repeat cells to sample measurement jitter for CIs |
| `probes` | `0` (use config default) | Per-actuator delay-sample budget |
| `publish_results` | `true` | Push to `results` branch |

**Job DAG:**

```
setup
  └─ dynamics [profile × mode × replica]  (start slow Node-RED flow, run taskDynamics, upload TTL + CSV)
       └─ aggregate  (phase3_dynamics.py: delay accuracy + compliance CI + paired bootstrap + BH-FDR)
```

**Headline metrics:** (1) learned blind delay ≈ ground-truth; (2) deadline compliance(ql_true) > compliance(ql_false) on tight goals

---

### D.5 `phase4.yml` — [NEW] Phase 4: Hidden Dependencies + Energy-Aware Goals
**Source:** [.github/workflows/phase4.yml](.github/workflows/phase4.yml)  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase4`

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `profiles` | `lab4,lab5` | Phase-4 labs |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` | RNG seeds |
| `run_mode` | `phase4` | run_config.json profile (adds `stereo_energy_prior_weight=2.0`) |
| `run_llm_baseline` | `true` | Also run `analysis/phase4_llm_baseline.py` |
| `publish_results` | `true` | Push to `results` branch |

**Job DAG:**

```
setup
  └─ train [profile × stereo × seed]
       └─ bench [profile × mode × seed]
            └─ aggregate  (sweep_report.py + phase4_energy.py + phase4_llm_baseline.py)
```

**Three analyses in aggregate:** learning-speed (sweep_report.py), energy-budget compliance (phase4_energy.py), offline LLM baseline comparison (phase4_llm_baseline.py)

---

### D.6 `sweep-dev.yml` — [OLD] Dev-Mode Full Sweep
**Source:** [.github/workflows/sweep-dev.yml](.github/workflows/sweep-dev.yml)  
**Triggers:** `workflow_dispatch`, `schedule` (cron `0 2 * * *` — nightly 02:00 UTC)  
**Run mode:** `dev` (hardcoded)  
**Default profiles:** `custom2,custom3,custom4,custom5,custom6,custom7,custom8,custom9`  
**No seed matrix** — single-seed dev run

**Job DAG:**

```
setup
  └─ train [profile × stereo]  (14 cells)
       └─ bench [profile × mode]  (21 cells)
            └─ aggregate  (sweep_report.py)
```

**Concurrency group:** `sweep-dev`

---

### D.7 `sweep-paper.yml` — [OLD] Paper-Mode Sweep
**Source:** [.github/workflows/sweep-paper.yml](.github/workflows/sweep-paper.yml)  
**Trigger:** `workflow_dispatch` only (weekly schedule commented out)  

**Inputs:**

| Input | Default | Description |
|---|---|---|
| `profiles` | `custom9,custom3,custom5` | Reduced confirmatory set (pre_registration §6.6 SW17-2) |
| `seeds` | `1,2,3,4,5` | RNG seeds (n=10 confirmatory replication = SW18) |
| `run_mode` | `paper` | `paper` (10k×20) \| `paper_h40` (5k×40) \| `paper_h60` (3.3k×60) |
| `publish_results` | `true` | Push to `results` branch |

**Job DAG:** same setup → train → bench → aggregate as sweep-dev; adds `seeds` matrix dimension  
**Concurrency group:** `sweep-paper`

---

### D.8 `sweep-ablation.yml` — [OLD] Paper-Mode Ablation
**Source:** [.github/workflows/sweep-ablation.yml](.github/workflows/sweep-ablation.yml)  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `sweep-ablation-<ablation>` (different ablation types may run in parallel)

**Inputs:**

| Input | Choices | Default |
|---|---|---|
| `ablation` | `noPBRS` \| `noTrust` \| `noPrior` | `noPBRS` |
| `profiles` | any comma list | all 8 custom profiles |
| `seeds` | any comma list | `1,2,3` |
| `dry_run` | boolean | `false` |

**Ablation config patches applied in `setup` job:**
- `noPBRS` → `learning.reward_shaping = "none"` (PBRS disabled, trust on)
- `noTrust` → `learning.adaptive_trust = false` (trust disabled, PBRS on)  
- `noPrior` → `learning.stereo_prior_scale = 0.0` (zero prior; ql_true ≈ ql_false)

**Job DAG:** setup (patches config.json) → train → bench → aggregate

---

## E. `config/run_config.json` Keys

**Source:** [config/run_config.json](../config/run_config.json)  
**Schema:** [config/run_config.schema.json](../config/run_config.schema.json) (JSON Schema 2020-12)

### Top-level keys

| Key | Type | Required | Description |
|---|---|---|---|
| `description` | string | no | Human-readable doc string |
| `profiles` | object | yes | Named run-mode profiles (see below) |
| `profiles_to_run` | array\<string\> | yes | Default profiles list (currently `["lab1","lab2","lab3"]`) |
| `stereo_modes` | array\<"true"\|"false"\> | yes | Stereotype modes to sweep |
| `bench_modes` | array\<string\> | yes | Benchmark modes (`rule_based`, `ql_false`, `ql_true`) |
| `simulator_port_map` | object | yes | Profile name → Node-RED port mapping |
| `simulator_flow_map` | object | yes | Profile name → simulator flow filename |
| `qtable_suffix_map` | object | yes | Profile name → Q-table file suffix |
| `expected_state_vec_dim` | object | yes | Profile name → state vector dimension (used by preflight sanity check) |
| `http_client` | object | no | HTTP client timeouts and retry settings |
| `learning` | object | no | Default learning hyperparameters (see below) |
| `phase2` | object | no | Phase-2 adapt-profiles, modes, port/flow maps, clean-source map |
| `phase3` | object | no | Phase-3 dynamics profiles, probe settings |

### Named `profiles` declared (each requires: `tick`, `num_episodes`, `max_steps_per_episode`, `action_delay_ms`, `exec_delay_ms_ql`, `exec_max_steps_ql`, `bench_runs`, `exec_max_steps_bench`, `exec_delay_ms_bench`)

| Profile name | Era | `num_episodes` | `max_steps_per_episode` | `bench_runs` | Notes |
|---|---|---|---|---|---|
| `dev` | both | 50 | 20 | 2 | Fast smoke/dev check |
| `paper` | [OLD] | 10000 | 20 | 5 | Full paper-quality run |
| `paper_h40` | [OLD] | 5000 | 40 | 5 | Horizon ablation (h=40) |
| `paper_h60` | [OLD] | 3300 | 60 | 5 | Horizon ablation (h=60) |
| `phase1` | [NEW] | 3000 | 20 | 5 | Clean-lab KG acceleration |
| `phase1_baseline` | [NEW] | 3000 | 20 | 5 | Arm A: KG+PBRS+trust OFF (stereo_prior_scale=0, stereo_init_bonus=0) |
| `phase1_kg_only` | [NEW] | 3000 | 20 | 5 | Arm C HEADLINE: KG prior ON, PBRS OFF, trust OFF |
| `phase1_kg_only_ib5` | [NEW] | 3000 | 20 | 5 | Arm C variant: init_bonus 15→5 |
| `phase1_pbrs_only` | [NEW] | 3000 | 20 | 5 | Arm B: PBRS ON, KG zeroed |
| `phase1_full` | [NEW] | 3000 | 20 | 5 | Arm D: KG ON, PBRS ON, trust ON |
| `phase1_kg_xzone` | [NEW] | 3000 | 20 | 5 | KG-X: adds `cross_zone_bonus=3.0` |
| `phase4` | [NEW] | 3000 | 20 | 5 | lab4/lab5; adds `stereo_energy_prior_weight=2.0` |

All profiles use `tick = "0.05"`, `action_delay_ms = 65`, `exec_delay_ms_ql = 100`, `exec_delay_ms_bench = 100`.  
**Source:** [config/run_config.json#L3-L195](../config/run_config.json#L3)

### `simulator_port_map` (full table)

| Profile | Port | Profile | Port |
|---|---|---|---|
| `custom2` | 1882 | `lab1` | 1892 |
| `custom3` | 1883 | `lab2` | 1893 |
| `custom4` | 1884 | `lab3` | 1894 |
| `custom5` | 1885 | `lab2_slow` | 1895 |
| `custom6` | 1886 | `lab3_slow` | 1896 |
| `custom7` | 1887 | `lab4` | 1897 |
| `custom8` | 1888 | `lab5` | 1898 |
| `custom9` | 1889 | `labmon` | 1899 |
| `custom9s` | 1891 | `labmon2` | 1900 |

**Source:** [config/run_config.json](../config/run_config.json) `simulator_port_map` block

### `expected_state_vec_dim`

| Profile | Dim | Profile | Dim |
|---|---|---|---|
| custom2–custom8, custom9 | 13 | lab1 | 2 |
| custom9s | 8 | lab2, lab2_slow | 7 |
| labmon | 3 | lab3, lab3_slow | 8 |
| lab4 | 9 | lab5 | 10 |
| labmon2 | 9 | | |

**Source:** [config/run_config.json](../config/run_config.json) `expected_state_vec_dim` block

### `http_client` defaults

| Key | Value |
|---|---|
| `connect_timeout_ms` | 2000 |
| `response_timeout_ms` | 5000 |
| `max_retries` | 3 |
| `backoff_base_ms` | 200 |

### `learning` defaults

| Key | Value | Corresponding system property |
|---|---|---|
| `reward_clip` | 200.0 | `reward.clip` |
| `stereo_prior_scale` | 1.0 | `stereo.priorScale` |
| `stereo_prior_decay_episodes` | 10000 | `stereo.priorDecayEpisodes` |
| `stereo_prior_decay_floor` | 0.0 | `stereo.priorDecayFloor` |
| `stereo_prior_redundant` | 1.0 | `stereo.priorRedundant` |
| `stereo_prior_iv_unsat` | 5.0 | `stereo.priorIVUnsat` |
| `stereo_init_bonus` | 15.0 | `stereo.initBonus` |
| `cross_zone_bonus` | 0.0 | `stereo.crossZoneBonus` |
| `stereo_energy_prior_weight` | 0.0 | `stereo.energyPriorWeight` |
| `reward_shaping` | `"pbrs"` | `reward.shaping` |
| `adaptive_trust` | `true` | `stereo.adaptiveTrust` |
| `adaptive_trust_min_samples` | 50 | `stereo.adaptiveTrust.minSamples` |
| `adaptive_trust_floor` | 0.1 | `stereo.adaptiveTrust.floor` |

**Source:** [config/run_config.json](../config/run_config.json) `learning` block

### `run_config.schema.json` — JSON Schema 2020-12
**Source:** [config/run_config.schema.json](../config/run_config.schema.json)  
Validates: `profiles` (each profile object requires all 9 timing keys; `additionalProperties: false`), `profiles_to_run`, `stereo_modes`, `bench_modes`, `simulator_port_map`, `simulator_flow_map`, `qtable_suffix_map`, `expected_state_vec_dim`, `http_client` (4 integer keys; `additionalProperties: false`), optional `dry_run` boolean. Top-level `additionalProperties: true` (allows `learning`, `phase2`, `phase3`, notes).

---

## F. PowerShell Runner Scripts

### F.1 `run_full_project.ps1` — Sequential Single-Process Orchestrator
**Source:** [run_full_project.ps1](../run_full_project.ps1)  
**Era:** both (handles both OLD custom profiles and NEW lab profiles via `-RunMode`)  
**Target shell:** Windows PowerShell 5.1+ (also PS7; no PS7-only syntax)

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `-RunMode` | ValidateSet | `"dev"` | Selects a profile from `run_config.json`; ValidateSet includes all 12 named profiles |
| `-OnlyProfiles` | string | `""` | Comma-separated profile subset (used by parallel orchestrator) |
| `-OnlyStereo` | ValidateSet `true/false/both` | `"both"` | Stereotype loop filter |
| `-OnlyModes` | string | `""` | Comma-separated bench-mode subset |
| `-SkipTraining` | switch | off | Skip Phase 3 (training) |
| `-SkipBenchmark` | switch | off | Skip Phase 4+5 |
| `-SkipPreflight` | switch | off | Skip preflight gate |
| `-VersionResults` | switch | off | Snapshot Q-tables to `results` branch |
| `-PublishResults` | switch | off | Push snapshot to origin |
| `-DryRun` | switch | off | Informational dry-run mode |
| `-RunSeed` | int | `0` | Per-run RNG seed (0 = unchanged; non-zero XORed into `baseSeed`) |

**Phases executed:** (1) Timing/episode patches, (2) Node-RED simulators start, (3) QL training, (4) Benchmark sweep, (5) Analysis; Cleanup restores ASL state and stops simulators.  
**Log file:** `run_full_project.log`

---

### F.2 `run_full_project_parallel.ps1` — Parallel Clone Orchestrator
**Source:** [run_full_project_parallel.ps1](../run_full_project_parallel.ps1)  
**Era:** both  
**Purpose:** Avoids shared-file corruption by giving each profile its own git clone (`<root>-clones/<profile>/`), then running clones concurrently (throttled by `-MaxParallel`).

**Parameters (excerpt):**

| Parameter | Default | Description |
|---|---|---|
| `-RunMode` | `"dev"` | Forwarded to each clone's `run_full_project.ps1` |
| `-MaxParallel` | `3` | Max concurrent clone jobs (recommended for 16 GB RAM) |
| `-SkipTraining` / `-SkipBenchmark` | off | Phase skip flags |
| `-RefreshClones` | off | Force `/MIR` re-sync of every clone |
| `-Fresh` | off | Delete generated results/logs + clones before start |
| `-ClonesRoot` | sibling `<dir>-clones` | Clone root directory |
| `-Seeds` | (single) | Comma-separated seeds; creates separate `benchmark/results_seed<N>/` per seed |

**Phases:** A. Pre-flight, B. Simulators, C. Clone sync (`robocopy /MIR`), D. Parallel training, E. Pull artefacts, F. Parallel benchmarking, G. Pull results, H. Analysis, I. Cleanup.

---

### F.3 `run_phase2_adapt.ps1` — Phase 2 Fault-Adapt Orchestrator
**Source:** [run_phase2_adapt.ps1](../run_phase2_adapt.ps1)  
**Era:** [NEW]  
**Per-cell flow:** start faulty Node-RED flow → wait `/health` → `gradlew taskAdapt` → watchdog → parse recovery metric → stop flow.  
**Log file:** `run_phase2_adapt.log`

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `-AdaptProfiles` | `""` (all from config `phase2.adapt_profiles`) | Comma-separated faulty profiles |
| `-Modes` | `"ql_true,ql_false"` | Arms to run |
| `-Episodes` | `0` (use profile default) | Re-learn budget override |
| `-Smoke` | off | Fast check using `config.phase2.smoke_episodes` (200) |
| `-WatchdogIdleSec` | `1200` | Idle timeout before killing JVM |
| `-SimReadyTimeoutSec` | `90` | Simulator health-check timeout |
| `-RunSeed` | `-1` (unset) | Per-run seed forwarded as `-Prun.seed` |

---

### F.4 `run_phase3_dynamics.ps1` — Phase 3 Dynamics Orchestrator
**Source:** [run_phase3_dynamics.ps1](../run_phase3_dynamics.ps1)  
**Era:** [NEW]  
**Per-cell flow:** start slow Node-RED flow → wait `/health` → `gradlew taskDynamics` → watchdog → parse delay table + timebounded results → stop flow.  
**Log file:** `run_phase3_dynamics.log` (implied by script pattern; NOT FOUND as explicit constant in the portion read)

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `-DynamicsProfiles` | `""` (all from config `phase3.dynamics_profiles`) | Comma-separated slow profiles |
| `-Modes` | `"ql_true,ql_false"` | Arms to run |
| `-Probes` | `0` (use config default) | Per-actuator sample budget |
| `-Smoke` | off | Use `config.phase3.smoke_probes` (3) |
| `-WatchdogIdleSec` | `600` | Idle timeout |
| `-SimReadyTimeoutSec` | `90` | Simulator health-check timeout |

---

### F.5 `run_step0_optB.ps1` — Audit Step 0 Replicability Gate  
**Source:** [run_step0_optB.ps1](../run_step0_optB.ps1)  
**Era:** [OLD] (custom8, pre-registration audit; statistical replicability probe)  
**Purpose:** 6 full-project runs (3× seed 7 + seeds 1,2,3) to measure σ_within vs σ_between; PASS iff σ_within < 0.5 × σ_between. Output deposited in `tmp_step0_optB/`.

---

### F.6 `run_step0_probeA_v3.ps1` — Audit Step 0 H5 Ablation Probe
**Source:** [run_step0_probeA_v3.ps1](../run_step0_probeA_v3.ps1)  
**Era:** [OLD] (custom8, pre-registration hypothesis H5)  
**Purpose:** Temporarily injects `stereo_prior_scale=0.0` into `run_config.json`, runs 3 seeds, verifies |mean(ql_true) − mean(ql_false)| < σ_within; restores config in `finally{}`. Output in `tmp_step0_probeA_v3/`.

---

### F.7 `scripts/Read-RunConfig.ps1` — Config Loader Library
**Source:** [scripts/Read-RunConfig.ps1](../scripts/Read-RunConfig.ps1)  
**Era:** [NEW]  
**Purpose:** Reads and validates `config/run_config.json`; returns a hashtable for the named profile. Returns `$null` if file missing (backward-compatible fallback). Used by other PS1 runners.  
**Parameters:** `-RunMode <string>` (required), `-ConfigPath <string>` (optional override).

---

### F.8 `scripts/version_artifacts.ps1` — Results Branch Snapshotter
**Source:** [scripts/version_artifacts.ps1](../scripts/version_artifacts.ps1)  
**Era:** [NEW] (Phase 12 #10)  
**Purpose:** Commits produced artefacts + `RUN_MANIFEST.json` to orphan `results` branch, optionally lightweight-tags `main`, optionally pushes to `origin/results`.  
**Parameters:** `-RunMode`, `-Profiles`, `-Modes`, `-PublishResults`, `-ResultsBranch`, `-OverwriteResultsBranch`.

---

### F.9 `scripts/sweep_watchdog.ps1` — CI Run Health Inspector
**Source:** [scripts/sweep_watchdog.ps1](../scripts/sweep_watchdog.ps1)  
**Era:** [OLD]  
**Purpose:** Uses `gh` CLI to inspect recent `sweep-paper.yml` and `sweep-ablation.yml` runs; reports failed jobs, per-seed completion ratio. Exits 0 if all runs succeeded, 1 if any failed or still running.  
**Parameters:** `-Workflow`, `-Limit` (default 5), `-Seeds` (default 5), `-Profiles` (default 7).

---

### F.10 `simulator/generate_faulty_flows.ps1` and `simulator/generate_flows.ps1`
**Source:** [simulator/generate_faulty_flows.ps1](../simulator/generate_faulty_flows.ps1), [simulator/generate_flows.ps1](../simulator/generate_flows.ps1)  
**Era:** [NEW]  
**Purpose:** Generator scripts that produce the Node-RED flow JSON files for clean and faulty lab profiles. (Content not fully read — noted for completeness.)

---

## G. Git Branches

**Source:** `git branch -a` output (audited 2026-07-07)  
**Active (checked-out) branch:** `phase2-instant-blacklist`

### Local branches

| Branch | Era | Purpose (inferred from name + commit log) |
|---|---|---|
| `main` | both | Integration branch; origin/HEAD points here |
| `backup/prepush-2026-05-08` | both | Safety backup before push on 2026-05-08 |
| `backup/prepush-2026-05-12` | both | Safety backup before push on 2026-05-12 |
| `docs-phase3-final` | [NEW] | Phase 3 documentation finalization (commit `ef7aaf2`) |
| `feature/qlearning-stereotype-comparison` | [OLD] | Early feature branch for QL + stereotype comparison |
| `kg-crosszone-ablation` | [NEW] | KG cross-zone ablation experiments |
| `kg-crosszone-coupling` | [NEW] | KG cross-zone coupling fix (see `docs/kg_crosszone_coupling_fix.md`) |
| `kg-crosszone-coupling-bump` | [NEW] | Bumped cross-zone coupling variant |
| `new-custom-lab-branch` | [OLD] | Custom lab development branch |
| `phase2-fault-detection` | [NEW] | Earlier Phase 2 fault-detection work (pre-instant-blacklist) |
| `phase2-instant-blacklist` | [NEW] | **Current branch.** Phase 2.3+: instant blacklist on first fault; also contains Phase 2.5 monitor-fallback labs (labmon, labmon2) |
| `phase3-process-dynamics` | [NEW] | Phase 3 response-delay learning |
| `phase4-dependencies-energy` | [NEW] | Phase 4 lab4 smart-plug + lab5 energy (commit `b775cdf`; merged content appears in current branch too) |

### Remote-only branches

| Branch | Era | Notes |
|---|---|---|
| `origin/copilot/fix-aggregate-publish-job` | [NEW] | CI fix for aggregate publish job |
| `origin/results` | [NEW] | Orphan branch holding versioned result artefacts (written by `scripts/version_artifacts.ps1`) |

### Recent commit log (most-recent 20 on `phase2-instant-blacklist`)

| Short SHA | Date | Subject |
|---|---|---|
| `ba0303e` | 2026-07-07 | docs(phase2): labmon2_f2dead_lowsun results — independent spotlight-free KG recovery replication |
| `71d5798` | 2026-07-07 | docs(phase2): lab3_f2dead_lowsun results — confirmatory KG recovery advantage |
| `20f1c62` | — | fix(ci): register labmon2 in run_full_project.ps1 profile maps |
| `5c734d7` | — | Add labmon2 dual-zone monitor-fallback lab |
| `82de32a` | — | phase2.5b: lab3_f2dead_lowsun multi-survivor degraded cell |
| `eab51e2` | — | labmon: confirmatory run 28863439179 results |
| `5ecae99` | — | labmon: proof-gated best-effort degradation |
| `1fb914c` | — | docs: fill S6 with confirmatory CI results (labmon_f1dead) |
| `f336318` | — | Phase 2.5: Monitor emergency-fallback lab (MonitorStereotype + labmon) |
| `f336318` | — | ... (continued) |
| `b775cdf` | — | (tag: results-20260621-135912-phase4) docs(phase4): certified n=20 results |

**Source:** `git log --oneline -20` output (HEAD = `ba0303e`)

### Which branch each phase primarily lives on

| Phase | Primary branch(es) |
|---|---|
| Phase 1 (KG acceleration, clean labs) | `main`, `kg-crosszone-ablation`, `kg-crosszone-coupling`, `kg-crosszone-coupling-bump` |
| Phase 2 (fault detection + adapt) | `phase2-fault-detection`, `phase2-instant-blacklist` (current; includes 2.5 monitor) |
| Phase 3 (process dynamics) | `phase3-process-dynamics`, `docs-phase3-final` |
| Phase 4 (dependencies + energy) | `phase4-dependencies-energy` |
| OLD (custom8/9, sweep, pre-registration) | `feature/qlearning-stereotype-comparison`, `new-custom-lab-branch`, `main` (historical) |

---

## OPEN QUESTIONS

1. `run_phase3_dynamics.ps1`: the log file name constant was not visible in the portion read — the actual log file name (implied `run_phase3_dynamics.log`) is NOT FOUND in source; needs verification.
2. `simulator/generate_faulty_flows.ps1` and `simulator/generate_flows.ps1`: content not read — their exact generation logic (template, parameters) is NOT FOUND here.
3. `scripts/sweep_watchdog.ps1` default `-Profiles 7` counts 7 profiles but `sweep-dev.yml` default is 8 (`custom2`..`custom9`) — whether this mismatch is intentional or stale is NOT FOUND in comments.
4. `sweep-dev.yml` lists `Set up Java 11` in the job name but sets `java-version: '21'` — likely a copy-paste label artefact; confirmed by reading the file but worth noting.
5. `config/run_config.json` `phase3` block: referenced in `run_phase3_dynamics.ps1` and `phase3.yml` but the full `phase3` object (dynamics_profiles, probe settings) was not fully read — its exact keys are NOT FOUND in the portion excerpted above.
6. Branch `phase4-dependencies-energy` appears as a local branch AND its latest commit (`b775cdf`) is also present in `phase2-instant-blacklist`'s log — whether Phase 4 content was merged into the current branch or the log entry is from a common ancestor is NOT FOUND without inspecting the merge graph.
7. `.node-red-lab2_f1dead/` and other faulty-variant Node-RED working directories exist at root but only the clean and slow variants have `.node-red-<profile>/` directories; the full list of faulty-variant working directories is NOT enumerated here.
