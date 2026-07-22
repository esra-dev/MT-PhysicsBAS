# Phase 1 Impact Analysis — Clean-Lab Progression (KG-primed vs. Tabula-rasa)

## Pivot Summary — Old vs. New

| Aspect | OLD thesis (rejected) | NEW thesis (this pivot) |
|---|---|---|
| Role of the KG / stereotypes | Priors that help the agent **silently adapt** to W1–W6 weakness labs (inverted sensors, power caps, wrong-prior, hidden bleed, etc.) | Priors that **accelerate learning in clean physics** only; they are **NOT** allowed to "rescue" broken physics |
| Lab design | 1 baseline + 6 weakness labs (custom2…custom7) running side-by-side | **Phase 1:** strictly clean-physics ladder (Simple → Medium → Complex). **Phase 2 (later):** isolated faulty labs with detect-blacklist-retrain, **never** silent adaptation. **Phase 3 (later):** learn temporal dynamics and write them back to KG |
| Headline metric | Robustness to weaknesses (W1–W6 deltas) | Phase 1: time-to-first-goal, AUC reward, redundant actions, iters-to-convergence — **KG-primed vs. tabula-rasa on clean labs** |
| Code paradigm | Fault-aware reward shaping, weakness fingerprinting, adaptive trust as a "weakness softener" | Clean separation: KG = physics accelerator; faults = first-class detection event; dynamics = KG enrichment |

The `custom9s` lab (built 2026-06-08; clean 2-zone, blind↔sun mediation, converges in ~1000 eps) is already aligned with the new direction — it's effectively a working draft of "Lab_Medium" / "Lab_Complex".

---

## Phase 1 Impact Map

### A. Node-RED simulator flows (the ground-truth physics)

| Lab | File | Action | Notes |
|---|---|---|---|
| `Lab_Simple` (1 zone, 1 lamp, 1 sensor) | `simulator/simulator_flow_simple.json` | **CREATE** (new) | New port (e.g. 1892). Must include `/health` endpoint (preflight gotcha — see `/memories/repo/custom9s-simple-lab-build.md`). Single TaskLight, single zone lux node, single illuminance sensor. No blinds, no spotlight, no sun coupling. |
| `Lab_Medium` (2 zones, independent lamps) | `simulator/simulator_flow_medium.json` | **CREATE** (new, port ~1893) | Two zones, two independent TaskLights, no cross-zone bleed, no shared spotlight, blinds optional/disabled. Simplest 2-zone separability test. |
| `Lab_Complex` (2 zones, shared spotlights + blinds + bleed) | `simulator/simulator_flow_complex.json` | **CREATE** or **PROMOTE** `simulator/simulator_flow_custom9s.json` | `custom9s` already matches the spec (shared CorridorLight, 2 zones, blind/sun coupling, bleed). Cheapest path: rename/alias it and freeze its design. Port stays 1891. |
| `simulator/simulator_flow_custom2.json … custom7.json` | **DEPRECATE (keep on disk, exclude from sweeps)** | The 6 weakness flows belong to Phase 2 — do not run them in Phase 1. Do **not** delete; we'll reuse them as faulty labs later. |
| `simulator/simulator_flow_custom8.json`, `custom9.json` | **KEEP for now, EXCLUDE from Phase 1 sweeps** | custom8/9 are "clean" but were designed as marginal-IV experiments from the previous audit. Re-classify after Phase 1 decision. |
| `.node-red-customX/` data dirs | **CREATE** matching `.node-red-simple/`, `.node-red-medium/`, `.node-red-complex/` | Each Node-RED instance needs its own data directory; orchestrator passes `--userDir`. |

### B. Ontologies / WoT Thing Descriptions

| File | Action | Notes |
|---|---|---|
| `src/resources/lab-ontology.ttl` | **REUSE as-is** | Generic schema — agent-side stereotype reasoner is dynamic via SPARQL, no hardcoded names. |
| `src/resources/wot-mappings.ttl` | **REUSE as-is** | Already drives 2-zone labs (custom, custom9s). |
| `src/resources/lab-ontology-custom2.ttl`, `wot-mappings-custom2.ttl` | **NOT NEEDED for Phase 1** (4-zone schema for the weakness labs). Keep on disk. |
| `src/resources/interactions-lab-simple.ttl` | **CREATE** (new) | Minimal 1-zone TD with one TaskLight action + one illuminance property. Port 1892. |
| `src/resources/interactions-lab-medium.ttl` | **CREATE** (new) | 2-zone TD without spotlight/blinds (port 1893). Or reuse the 2-zone `interactions-lab-custom.ttl` and constrain the simulator. |
| `src/resources/interactions-lab-complex.ttl` | **REUSE** `src/resources/interactions-lab-custom9s.ttl` | Already exists and is correct. |

### C. Jason agents (`src/agt/*.asl`)

| File | Action | Notes |
|---|---|---|
| `src/agt/lab_profiles.asl` | **MODIFY** | Add 3 new `lab_profile/13` records: `simple`, `medium`, `complex`. All carry `weakness_flags([])`. Pick `training_params` per lab (simple ≪ medium ≪ complex episode budget). The schema/accessor block is unchanged. |
| `src/agt/illuminance_controller_agent_ql.asl` | **REUSE as-is** | Already profile-driven — switching labs is one belief change. The `use_stereotypes(true/false)` belief is exactly the Phase-1 lever for KG-primed vs. tabula-rasa. |
| `src/agt/illuminance_controller_agent_bench.asl` | **MODIFY (surgical)** | The `!fingerprint_weakness(...)` plan at L360 and `fp_record(w1..w6, ...)` plans at L713+ fire on every step. They are **already gated** by `weakness_flags([])` (empty list ⇒ no fingerprint recorded), so for Phase 1 they're effectively no-ops. **Recommendation:** add an early-out guard `if WF == []` that skips the `classifyWeaknesses` call entirely, to avoid the per-step Java round-trip on clean labs. Do not delete the plans (Phase 2 reuses them). |
| `src/agt/illuminance_controller_agent.asl` | **NO CHANGE** | Already marked "interactive demo only" — not used by benchmarks. |

### D. CArtAgO artifacts (`src/env/tools/*.java`)

| File | Action | Notes |
|---|---|---|
| `src/env/tools/QLearner.java` | **DO NOT TOUCH** (per master doc rule §5). For Phase 1 it works as-is. The PBRS reward shaping (L80/L394–405) and adaptive trust (L92/L442–456/L1451–1490) are **policy-invariant accelerators** — they belong in the new "knowledge accelerates learning" story and should be **enabled** for the KG-primed arm. The `classifyWeaknesses` op at L766 only fires when the bench agent calls it; making the agent skip the call (item C) renders this dead-code-on-clean-labs without surgery. |
| `src/env/tools/StereotypeReasoner.java` | **DO NOT TOUCH** | The SPARQL-driven prior derivation is exactly what Phase 1 needs as the "physics knowledge" accelerator. |
| `src/env/tools/StereotypeLearner.java` | **NO CHANGE for Phase 1** | The Z-score outlier detection (`observe`, `printStats`, `saveLearnedStereotypes`) is Phase-2 anomaly-detection infrastructure. Keep dormant in Phase 1 (agent already calls it; the learned stereotypes are an artifact, not a feedback loop). |
| `src/env/tools/LabEnvironment.java`, `OntologyArtifact.java`, `BenchmarkLogger.java`, `SimulatorHttpClient.java` | **NO CHANGE** | All profile-/port-driven. |

### E. Orchestration & config

| File | Action | Notes |
|---|---|---|
| `config/run_config.json` | **MODIFY** | (1) Add `simple`, `medium`, `complex` entries to `simulator_port_map`, `simulator_flow_map`, `qtable_suffix_map`, `expected_state_vec_dim`. (2) Change `profiles_to_run` to `["simple", "medium", "complex"]`. (3) `bench_modes` drops `rule_based` if not desired as oracle, or keeps it as upper-bound reference (recommend keep). (4) `stereo_modes` keeps `["true","false"]` — that **is** Phase 1's headline contrast. |
| `run_full_project.ps1`, `run_full_project_parallel.ps1` | **MODIFY** | Add the 3 new profiles to `$TrainProfiles`, `$ProfileQtableSuffix`, and the `$Simulators` array (each with port + flow file + userDir). Remove or comment-out `custom2..custom7` from default sweep set. |
| `build.gradle` preflight task | **VERIFY** | Already probes `/health` per port — each new flow must implement `/health` (the documented gotcha). No code change if flows comply. |
| `task.jcm`, `task_ql.jcm`, `task_bench.jcm` | **NO CHANGE** | Profile is selected via `-Dactive.profile=simple/medium/complex`. |

### F. CI workflows (`.github/workflows/`)

| File | Action |
|---|---|
| `sweep-dev.yml`, `sweep-paper.yml` | **MODIFY** matrix: replace `custom2..custom7` with `simple,medium,complex`. Keep `stereo` matrix dim. |
| `ci.yml` | **NO CHANGE** (unit tests + Turtle validation are profile-agnostic). |

### G. Analysis (`analysis/`)

| File | Action |
|---|---|
| `analysis/sweep_report.py` | **REUSE** — bootstrap-CI aggregation is profile-agnostic. |
| `analysis/weakness_demo.py`, `analysis/weakness_per_lab.py` | **DEPRECATE for Phase 1** (move under `analysis/phase2/` or tag as "Phase 2 only"). |
| `qtable_init_heatmap.py` | **REUSE** — visualises KG priming, exactly the Phase-1 story. |
| **NEW**: `analysis/phase1_clean_ladder.py` | **CREATE** — produces the Phase 1 headline plots: time-to-first-goal, AUC reward, iterations-to-convergence, redundant-action count, all KG-primed vs. tabula-rasa, faceted by `{simple, medium, complex}`. |

### H. Formally deprecated (but **not deleted**) for Phase 1

- Weakness labs `custom2..custom7` (flows, `.node-red-customX/` dirs, scenario JSONs, `lab_profile/13` records) — held for Phase 2.
- `custom8`, `custom9` — held pending re-classification (audit notes flag them as marginal-IV; may or may not be a useful "Lab_Complex_v2").
- Bench-side `!fingerprint_weakness` is dormant (gated by `weakness_flags([])`), not removed.

---

## Open Decisions Before Implementation

1. **Lab_Complex source:**
   - (a) **Promote `custom9s` as-is** — zero new simulator work, only registry/config aliasing.
   - (b) **Fork into a new `simulator_flow_complex.json`** — leaves `custom9s` untouched in history.
2. **Accelerator features on the KG-primed arm:** Three policy-invariant accelerators exist:
   - (i) Stereotype Q-init bias (the core KG prior).
   - (ii) PBRS reward shaping (`reward_shaping: pbrs`).
   - (iii) Adaptive trust calibration.
   - Phase 1 with **only (i) ON** = cleanest attribution ("what is the KG itself contributing?").
   - Phase 1 with **(i)+(ii)+(iii) ON** = strongest accelerator stack, but muddier attribution.
   - Recommendation: run (i)-only as the headline arm, plus a `(i)+(ii)+(iii)` ablation if budget allows.
