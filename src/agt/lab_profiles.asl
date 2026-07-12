// ============================================================
//  Lab Profile Registry
//  MT-Esra Project
//
//  Single source of truth for all lab-environment configuration.
//  A "lab profile" bundles every path / parameter that varies
//  between physical lab setups so that switching labs is a
//  one-line change to the active_profile/1 belief.
//
//  Profile schema:
//    lab_profile(Name,
//                td(TdUrl),                            // WoT Thing Description (classpath:... or http://)
//                ont(OntologyPaths),                   // Jason list of TTL classpath resources
//                scenarios(BenchScenariosFile),        // Held-out benchmark scenarios JSON
//                train_scenarios(TrainScenariosFile),  // Held-in training scenarios JSON (optional)
//                sim_port(Port),                       // Node-RED simulator port (informational)
//                light_bounds(LightRankBounds),        // [r1Upper, r2Upper, r3Upper] in lux
//                sunshine_bounds(SunshineRankBounds),  // same structure
//                zone_targets(ZoneTargetList),         // list of target(ZIdx, Rank) pairs
//                sunshine_prob(SunProb),               // P(sunshine >= rank 1)
//                weakness_flags(Flags),                // list of atoms: [w1, w2, ...] for stress-tests
//                qtable_suffix(Suffix),                // string appended to qtable_final_stereotypes_<bool><Suffix>.csv
//                training_params(NumEpisodes, EpsilonDecay)). // per-profile training budget and decay rate
//
//  Switching: change `active_profile("name").` belief once.
//  No agent code below the belief layer needs to be touched.
// ============================================================

/* ============================================================
 * Active profile selector — change this single line to switch labs.
 * ============================================================ */
active_profile("lab1").

/* ============================================================
 * Registered profiles
 * ============================================================ */

// ── Default 2-zone custom lab (port 1881) ───────────────────
lab_profile("custom",
            td("classpath:interactions-lab-custom.ttl"),
            ont(["lab-ontology.ttl", "wot-mappings.ttl"]),
            scenarios("benchmark/scenarios.json"),
            train_scenarios("benchmark/train_scenarios.json"),
            sim_port(1881),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1, 3), target(2, 2)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix(""),
            training_params(2500, 0.9950)).

// ── Same lab but trained over fixed train_scenarios cycle ───
//    (Phase 0.3: ql_full_train ablation).  Q-tables get a "_full" suffix
//    so they don't overwrite the random-state Q-tables.
lab_profile("custom_full_train",
            td("classpath:interactions-lab-custom.ttl"),
            ont(["lab-ontology.ttl", "wot-mappings.ttl"]),
            scenarios("benchmark/scenarios.json"),
            train_scenarios("benchmark/train_scenarios.json"),
            sim_port(1881),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1, 3), target(2, 2)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_full"),
            training_params(2500, 0.9950)).

// ── 4-zone weakness labs (one ontology, six simulator flows) ───────────
//   The agent's nominal belief is the SAME ontology
//   ([lab-ontology.ttl, lab-ontology-custom2.ttl, wot-mappings-custom2.ttl])
//   for all six labs.  The simulator (Node-RED on ports 1882..1887) IS
//   the ground truth, and each flow injects exactly ONE weakness so the
//   observed Δ vs. predicted Δ is the experimental signal.
//
//   weakness_flags is consumed by the bench agent to enable the matching
//   per-step weakness fingerprint check (see illuminance_controller_agent_bench.asl).

//   custom2 → W1 missing-stereotype  (Hidden_Bleed corridor +30 lux not in TD)
lab_profile("custom2",
            td("classpath:interactions-lab-custom2.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom2.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1882),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w1]),
            qtable_suffix("_custom2"),
            training_params(10000, 0.9990)).

//   custom3 → W2 context-dependent  (Blind_Z2 sun-flip at sunRank≥3)
lab_profile("custom3",
            td("classpath:interactions-lab-custom3.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom3.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1883),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_custom3"),
            training_params(10000, 0.9990)).

//   custom4 → W3 dynamics  (ramp 3 / residual 2 / hysteresis)
lab_profile("custom4",
            td("classpath:interactions-lab-custom4.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom4.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1884),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w3]),
            qtable_suffix("_custom4"),
            training_params(10000, 0.9990)).

//   custom5 → W4 shared resource  (7-unit power cap; lowest priority dropped)
lab_profile("custom5",
            td("classpath:interactions-lab-custom5.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom5.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1885),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_custom5"),
            training_params(10000, 0.9990)).

//   custom6 → W5 dynamic topology  (Partition23 toggles every 5 ticks)
lab_profile("custom6",
            td("classpath:interactions-lab-custom6.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom6.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1886),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w5]),
            qtable_suffix("_custom6"),
            training_params(10000, 0.9990)).

//   custom7 → W6 multi-objective heat  (+0.1 °C/tick per ON lamp)
lab_profile("custom7",
            td("classpath:interactions-lab-custom7.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom7.json"),
            train_scenarios("benchmark/train_scenarios_custom2.json"),
            sim_port(1887),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.75),
            weakness_flags([w6]),
            qtable_suffix("_custom7"),
            training_params(10000, 0.9990)).

//   custom8 → W7 IV-coupling demonstration lab.
//   PURE clean dynamics (no hidden weakness) with scenarios that cover
//   all 4 sunshine ranks uniformly. Stereotype priors (which encode
//   Mediates(blind, sunshine)) should beat the non-stereotype baseline
//   by learning sunshine-conditioned action selection. sunshine_prob 0.50
//   widens the distribution so rank-0 / rank-3 cases dominate equally.
lab_profile("custom8",
            td("classpath:interactions-lab-custom8.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom8.json"),
            train_scenarios("benchmark/train_scenarios_custom8.json"),
            sim_port(1888),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.50),
            weakness_flags([]),
            qtable_suffix("_custom8"),
            training_params(10000, 0.9990)).

//   custom9 → CLEAN lab with sun-DEPENDENT optimum (audit Step 5, S5-3).
//   Forked from custom8 but Spotlight & SpotlightCD are DISABLED in the
//   simulator's compute_levels block. This forces the agent to harvest
//   lux via task lights (always available, cost=1) or blinds (sun-
//   conditioned, cost~0). At sun=rank3 the cheap optimum uses blinds-open;
//   at sun=rank0 the only feasible policy is task-lights-on. Therefore
//   the Mediates(blind, sunshine) stereotype prior is *constructive*
//   here (unlike custom8 where the prior has no positive lever — see
//   audit-step-1b §3 and audit-step-5 §4 #4). custom9 is the lab on
//   which H1 (priors help on clean dynamics) is mechanically testable.
//   Reachability proof must be re-run before this profile enters the
//   sweep (mirror Step 1b for custom8).
lab_profile("custom9",
            td("classpath:interactions-lab-custom9.ttl"),
            ont(["lab-ontology.ttl", "lab-ontology-custom2.ttl", "wot-mappings-custom2.ttl"]),
            scenarios("benchmark/scenarios_custom9.json"),
            train_scenarios("benchmark/train_scenarios_custom9.json"),
            sim_port(1889),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2), target(3,3), target(4,2)]),
            sunshine_prob(0.50),
            weakness_flags([]),
            qtable_suffix("_custom9"),
            training_params(10000, 0.9990)).

//   custom9s → SIMPLE 2-zone CONSTRUCTIVE sibling of custom9 (blind <-> sun).
//   Exploratory simple-lab track (see docs/simple_labs_design.md §3). Reduces
//   custom9 to 2 zones so the base learner CONVERGES in ~1000 episodes, making
//   the stereotype prior's faster-learning benefit measurable (the 4-zone
//   custom9 plateaus at goal-rate 0.11–0.21 even at 10k episodes). Same 8-slot
//   2-zone schema as the default `custom` lab (ont = lab-ontology + wot-mappings),
//   so the WoT contract is unchanged; only the simulator (port 1891) differs.
//   The `Spotlight` actuator is repurposed by the simulator as a shared
//   CorridorLight (+150 lux both zones). Doubles as the testbed for the
//   ws:ivMinRank=3 gate fix (see docs/custom9_rediagnosis.md).
//   NOTE: training_params episodes (1000) are OVERRIDDEN per run-mode by the
//   orchestrator (run_full_project.ps1 patches training_params with run_config
//   num_episodes); the 1000 is the design target for a focused convergence run.
lab_profile("custom9s",
            td("classpath:interactions-lab-custom9s.ttl"),
            ont(["lab-ontology.ttl", "wot-mappings.ttl"]),
            scenarios("benchmark/scenarios_custom9s.json"),
            train_scenarios("benchmark/train_scenarios_custom9s.json"),
            sim_port(1891),
            light_bounds([75, 200, 400]),
            sunshine_bounds([50, 150, 500]),
            zone_targets([target(1,3), target(2,2)]),
            sunshine_prob(0.50),
            weakness_flags([]),
            qtable_suffix("_custom9s"),
            training_params(1000, 0.9920)).
// ── Phase 1 CLEAN LADDER (Knowledge-Guided Acceleration) ────────────────────
//   lab1/lab2/lab3 are STRICTLY-CLEAN labs with NO hidden weaknesses, used to
//   prove that a KG-primed Q-learner converges faster than a tabula-rasa one.
//   Each loads ONLY its own self-contained building_*.ttl (schema + topology +
//   WoT mappings + slot registry). lab-ontology.ttl is deliberately NOT loaded
//   so nothing outside the file can leak into actuator discovery — guaranteeing
//   zero extra actuators and zero spurious cross-zone priors. weakness_flags is
//   [] for all three (the bench agent skips weakness fingerprinting).
//
//   Feature ladder (each step adds exactly one mechanism class):
//     lab1 Trivial      → 1 zone,  1 Causes lamp                        (8 states)
//     lab2 Intermediate → 2 zones, lamps (Causes) + blinds (Mediates)   (1024 states)
//     lab3 Complex      → lab2 + cross-zone spill + shared spotlight     (2048 states)
//
//   Sunshine is sampled once per episode from {0,100,400,900} and PINNED, so the
//   physics is a deterministic function of flow state (no PRNG in the env tick).

//   lab1 → Trivial (port 1892): single Causes actuator. H1 acceleration baseline.
lab_profile("lab1",
            td("classpath:interactions-lab1.ttl"),
            ont(["building_1_trivial.ttl"]),
            scenarios("benchmark/scenarios_lab1.json"),
            train_scenarios("benchmark/train_scenarios_lab1.json"),
            sim_port(1892),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab1"),
            training_params(1000, 0.9920)).

//   lab2 → Intermediate (port 1893): adds the Mediates (blind <-> sun) mechanism.
lab_profile("lab2",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab2"),
            training_params(2000, 0.9960)).

//   lab3 → Complex (port 1894): adds cross-zone coupling + shared spotlight.
//   Deterministic, leak-free replacement for the custom9s PRNG-tick flow.
lab_profile("lab3",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab3"),
            training_params(3000, 0.9970)).

// ── Phase 4 KNOWLEDGE LADDER (Hidden Dependencies & Energy) ─────────────────
//   lab4/lab4dual/lab4chain/lab5 extend the Phase-1 clean ladder with KG-encoded
//   knowledge that a tabula-rasa learner cannot see but a KG-primed learner can
//   exploit. All are STRICTLY-CLEAN (no hidden weakness): the simulator physics
//   is fully aligned with the building_*.ttl, so every difference between
//   ql_true and ql_false is attributable to the prior knowledge in the Knowledge
//   Graph. weakness_flags is [] (the bench agent skips weakness fingerprinting).
//   Same discretisation and pinned-sunshine regime as lab3.
//
//   DEPENDENCY LADDER — cells vary how many components carry a power
//   dependency and how deep the dependency chain is:
//     lab3       0 gated components (Phase-1 anchor)
//     lab4       1 gated component  (Z1 lamp behind one plug)
//     lab4dual   2 gated components (BOTH lamps, one plug each)
//     lab4chain  1 gated component, DEPTH-2 chain (breaker -> plug -> lamp)
//
//     lab4 Smart-Plug → lab3 + a hidden POWER dependency: the Z1 ceiling lamp is
//                       wired through SmartPlug_Z1 (ws:powerGates) and emits light
//                       only when BOTH the lamp switch AND the plug are ON. A
//                       KG-primed agent reads ws:powerGates and enables the plug
//                       first; a tabula-rasa agent must discover the AND-gate by
//                       trial and error.                                (4096 states)
//
//     lab4dual Dual   → lab4 + a SECOND plug: EACH zone's lamp is behind its own
//                       plug (two independent ws:powerGates arcs). Doubles the
//                       number of components with a dependency.        (8192 states)
//
//     lab4chain Chain → lab4 + an UPSTREAM circuit breaker: breaker gates plug,
//                       plug gates the Z1 lamp (two CHAINED ws:powerGates arcs;
//                       the lamp lights only when breaker AND plug AND switch are
//                       all ON). Deepens the dependency to a 2-level chain the
//                       KG-primed agent can traverse breaker->plug->lamp.
//                                                                       (8192 states)
//
//     lab5 Energy     → lab3 + two directly-actionable lamps per zone with the
//                       SAME light output (+400) but different ws:energyCost
//                       (efficient = 1/tick, inefficient = 4/tick). Energy is NOT
//                       in the Q-reward; only a KG-primed agent (reading
//                       ws:energyCost, applied as a non-fading energy prior) learns
//                       to prefer the cheap lamp / zero-energy blinds. Compliance is
//                       scored at benchmark time (goal reached AND steady-state
//                       power <= energyBudget).                          (8192 states)

//   lab4 → Smart-Plug dependency (port 1897). powerGates AND-gate on the Z1 lamp.
lab_profile("lab4",
            td("classpath:interactions-lab4.ttl"),
            ont(["building_4_smartplug.ttl"]),
            scenarios("benchmark/scenarios_lab4.json"),
            train_scenarios("benchmark/train_scenarios_lab4.json"),
            sim_port(1897),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab4"),
            training_params(3000, 0.9970)).

//   lab4dual → DUAL Smart-Plug dependency (port 1901). Two ws:powerGates arcs:
//   each zone's lamp behind its own plug. Same budget as lab4 so the dependency
//   ladder (0 -> 1 -> 2 gated components) holds the training budget constant.
lab_profile("lab4dual",
            td("classpath:interactions-lab4dual.ttl"),
            ont(["building_8_dualplug.ttl"]),
            scenarios("benchmark/scenarios_lab4dual.json"),
            train_scenarios("benchmark/train_scenarios_lab4dual.json"),
            sim_port(1901),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab4dual"),
            training_params(3000, 0.9970)).

//   lab4chain → CHAINED power dependency (port 1902). Two CHAINED ws:powerGates
//   arcs: breaker -> plug -> Z1 lamp (the lamp needs ALL THREE switches ON).
//   Same budget as lab4/lab4dual for the ladder contrast.
lab_profile("lab4chain",
            td("classpath:interactions-lab4chain.ttl"),
            ont(["building_9_chainplug.ttl"]),
            scenarios("benchmark/scenarios_lab4chain.json"),
            train_scenarios("benchmark/train_scenarios_lab4chain.json"),
            sim_port(1902),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab4chain"),
            training_params(3000, 0.9970)).

//   lab5 → Energy differentiation (port 1898). Two lamps/zone, ws:energyCost 1 vs 4.
lab_profile("lab5",
            td("classpath:interactions-lab5.ttl"),
            ont(["building_5_energy.ttl"]),
            scenarios("benchmark/scenarios_lab5.json"),
            train_scenarios("benchmark/train_scenarios_lab5.json"),
            sim_port(1898),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab5"),
            training_params(3000, 0.9970)).

// ── Phase 2.5 MONITOR EMERGENCY-FALLBACK LAB ───────────────────────────────
//   A single-zone lab with TWO Causes actuators: the primary task lamp and a
//   computer MONITOR whose light output is only a side-effect
//   (ws:MonitorStereotype). Fully deterministic (no sunshine, no blinds).
//   Clean optimum = the primary lamp alone (rank 3, 425 lux).
//   The emergency variant labmon_f1dead kills the primary lamp; the monitor
//   alone reaches rank 2 only (285 lux) — best-effort degradation. The
//   KG-primed agent should re-value the monitor as the fallback faster than a
//   tabula-rasa learner. State = [Z1Level, Z1Light, Z1Monitor] = 16 states.
//   Port 1899.
lab_profile("labmon",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon"),
            training_params(1500, 0.9950)).

// ── Phase 2.5 DUAL-ZONE MONITOR-FALLBACK LAB (labmon2, NO spotlight) ────────
//   Two INDEPENDENT workstations, each with a primary task lamp, a computer
//   MONITOR (light is a screen-backlight SIDE-EFFECT, ws:MonitorStereotype) and
//   a sun-mediated window BLIND. NO spotlight, NO cross-zone coupling. This is
//   the multi-survivor extension of labmon: when BOTH lamps fail and daylight is
//   low the goal (rank 3) is unreachable in both zones, and the monitor (rank 2
//   alone) is the essential best-effort fallback in EACH zone (4 survivors →
//   16 probe combos). Physics: Zi = 25 + (ZiLight?400) + (ZiMonitor?200) +
//   (ZiBlinds?0.50*Sun). At LOW sun the lamp is the ONLY rank-3 lever, so both
//   arms use it and its death is detected (no reward-cost / Q-init bias needed).
//   State = [Z1Level,Z2Level,Z1Light,Z2Light,Z1Monitor,Z2Monitor,Z1Blinds,
//   Z2Blinds,Sunshine] = 4096 states. Port 1900.
lab_profile("labmon2",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon2"),
            training_params(4000, 0.9975)).

// ── Phase 2.6 KG-SILENT MONITOR VARIANTS (misdocumented / undocumented) ─────
//   Forks of the monitor labs where the monitor STILL physically brightens the
//   room (identical simulator flows/ports as labmon / labmon2) but its light
//   effect is MISSING from the stereotype layer of the KG:
//     • *_infoonly  (variant A) — the monitor HAS a stereotype, but its only
//       dependent variable is displayed_information; the elem:luminiscence
//       side-effect (and the photon outlet) is absent. A MISDOCUMENTED KG.
//     • *_nostereo  (variant B) — the monitor has NO stereotype at all. An
//       UNDOCUMENTED component (instance + WoT mapping only).
//   In both variants the monitor's ON/OFF actions enter the action space via
//   the KG-SILENT fallback discovery (StereotypeReasoner) with EMPTY
//   affectedZones: no Q-init endorsement, no fault adjudication, no
//   Expected-vs-Actual prediction. Both learner arms must discover the
//   monitor's light effect from reward alone. The research question: when the
//   task lamp(s) die, do the agents still adopt the unmodeled monitor as the
//   best-effort fallback, and does the KG-primed arm (priors on everything
//   EXCEPT the monitor) still adapt better/faster than tabula-rasa?
//   The parent (fully-modeled) labmon/labmon2 profiles remain untouched, so
//   full-KG vs misdocumented-KG vs undocumented-KG is a 3-way contrast.

//   labmon_infoonly → CLEAN single-zone parent, info-only monitor stereotype.
lab_profile("labmon_infoonly",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor_infoonly.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon_infoonly"),
            training_params(1500, 0.9950)).

//   labmon_nostereo → CLEAN single-zone parent, monitor without any stereotype.
lab_profile("labmon_nostereo",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor_nostereo.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon_nostereo"),
            training_params(1500, 0.9950)).

//   labmon2_infoonly → CLEAN dual-zone parent, info-only monitor stereotypes.
lab_profile("labmon2_infoonly",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor_infoonly.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon2_infoonly"),
            training_params(4000, 0.9975)).

//   labmon2_nostereo → CLEAN dual-zone parent, monitors without any stereotype.
lab_profile("labmon2_nostereo",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor_nostereo.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_labmon2_nostereo"),
            training_params(4000, 0.9975)).

// ── Phase 3 SLOW LADDER (Learning Process Dynamics / response delay) ────────
//   Each slow profile is structurally IDENTICAL to its clean Phase-1 parent
//   (same agent-side ontology shape, zone targets and discretisation bounds, so
//   the Q-state space is unchanged) but its SIMULATOR flow gives the motorized
//   blind a TEMPORAL response delay (~60 s = 12 ticks). The lamp (and, in lab3,
//   the spotlight) stay instantaneous. The dynamics agent MEASURES the per-
//   actuator delay online and writes it back to the KG (learned_dynamics_*.ttl),
//   then exploits it for time-bounded ("bright immediately" vs "within 5 min")
//   goals. The slow labs use dedicated ports/ontologies, so Phase 1/2 are
//   untouched. Benchmark + training scenarios are reused from the clean parents
//   (the state schema is identical).

//   lab2_slow → Lab 2 (Intermediate) + motorized-blind delay (port 1895).
lab_profile("lab2_slow",
            td("classpath:interactions-lab2_slow.ttl"),
            ont(["building_2_slow.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1895),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab2_slow"),
            training_params(2000, 0.9960)).

//   lab3_slow → Lab 3 (Complex) + motorized-blind delay on BOTH blinds (1896).
lab_profile("lab3_slow",
            td("classpath:interactions-lab3_slow.ttl"),
            ont(["building_3_slow.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1896),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([]),
            qtable_suffix("_lab3_slow"),
            training_params(3000, 0.9970)).

// ── Phase 2 FAULTY LADDER (Fault detection / blacklist / re-learn) ──────────
//   Each faulty profile is a clean Phase-1 lab (lab1/lab2/lab3) whose AGENT-SIDE
//   ontology, zone targets and discretisation bounds are IDENTICAL to the clean
//   parent (so the Knowledge-Graph "nominal physics" is unchanged) but whose
//   SIMULATOR flow injects exactly ONE hardware fault into ONE component:
//     • _f1dead  — a task lamp's lux contribution is forced to 0 (the relay
//                  closes / the actuator bit toggles, but the bulb emits
//                  nothing). The KG predicts +Δ; reality gives 0.
//     • _f1inv   — a task lamp's lux contribution is negated (mis-wired). The
//                  KG predicts +Δ; reality gives 0 (from rank 0) or −Δ (from an
//                  elevated zone). Caught by the combined anomaly-rate trigger.
//   The faulty flow is launched on the SAME port + TD as the clean parent (only
//   ONE lab variant runs at a time during adaptation), so no new TD is needed.
//   adapt_source/2 (below) maps each faulty profile to the clean parent's
//   qtable_suffix, so the adapt agent warm-loads the right Phase-1 Q-table.
//   weakness_flags is informational here (the adapt agent uses its own
//   observeForFaults detector, not the bench fingerprint plans).

//   lab1_f1dead → DEAD single lamp. Degenerate case: lab1 has only ONE actuator,
//   so after blacklisting there is NO surviving lever — the agent DETECTS +
//   ALERTS but cannot recover (recovery = N/A). Minimal detection showcase.
lab_profile("lab1_f1dead",
            td("classpath:interactions-lab1.ttl"),
            ont(["building_1_trivial.ttl"]),
            scenarios("benchmark/scenarios_lab1.json"),
            train_scenarios("benchmark/train_scenarios_lab1.json"),
            sim_port(1892),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab1_f1dead"),
            training_params(1000, 0.9920)).

//   lab2_f1dead → DEAD Z1 lamp in the 2-zone Intermediate lab. The blind (Z1)
//   plus the whole of Z2 survive, so the agent re-learns a recovered policy.
lab_profile("lab2_f1dead",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab2_f1dead"),
            training_params(2000, 0.9960)).

//   lab2_f1inv → INVERTED Z1 lamp in the 2-zone Intermediate lab.
lab_profile("lab2_f1inv",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab2_f1inv"),
            training_params(2000, 0.9960)).

//   lab3_f1dead → DEAD Z1 lamp in the 2-zone Complex lab (cross-zone + shared
//   spotlight). Survivors include the spotlight + Z2, giving a richer recovery.
lab_profile("lab3_f1dead",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f1dead"),
            training_params(4000, 0.9970)).

//   lab3_f1inv → INVERTED Z1 lamp in the Complex lab. The shared spotlight and
//   cross-zone spill keep Z1 elevated, so the inversion produces genuine
//   opposite-direction (opp) evidence, not just dead-looking Δ=0.
lab_profile("lab3_f1inv",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab3_f1inv"),
            training_params(4000, 0.9970)).

//   ── MULTI-FAULT variants (several components broken at once) ──────────────
//   These exercise the ITERATIVE detect→blacklist→warm-restart loop: the agent
//   detects each broken lamp in turn, removes it, and re-learns over what is
//   left. Only CAUSES lamps are injected (the detector ignores Mediates blinds),
//   and lab1 is omitted (it has a single lamp, so "several" is undefined there).

//   lab2_f2dead → BOTH task lamps (Z1Light + Z2Light) dead. After both are
//   blacklisted only the (healthy) blinds survive, so full rank-3 recovery is
//   only possible in sunny episodes — a medium-complexity SEVERAL-DEAD showcase
//   that proves multi-component detection + alert even when recovery is partial.
lab_profile("lab2_f2dead",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab2_f2dead"),
            training_params(2000, 0.9960)).

//   lab2_f2inv → BOTH task lamps inverted (mis-wired). Caught by the combined
//   anomaly-rate trigger; survivors are the blinds.
lab_profile("lab2_f2inv",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab2_f2inv"),
            training_params(2000, 0.9960)).

//   lab3_f2dead → BOTH task lamps (Z1Light + Z2Light) dead in the Complex lab.
//   The shared Spotlight (Causes, +150 both zones) and the blinds SURVIVE, so
//   the agent can re-learn a genuinely recovered policy — the cleanest
//   SEVERAL-DEAD-WITH-RECOVERY case.
lab_profile("lab3_f2dead",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f2dead"),
            training_params(4000, 0.9970)).

//   lab3_f2inv → BOTH task lamps inverted in the Complex lab. Spotlight +
//   cross-zone keep the zones elevated so the inversion yields real opposite-
//   direction evidence; survivors include the spotlight + blinds.
lab_profile("lab3_f2inv",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab3_f2inv"),
            training_params(4000, 0.9970)).

//   ── Phase 2 EXTENSION — additional well-posed lamp cells + blind faults ───
//   Two motivations (advisor request):
//     (1) MORE well-posed recovery data in lab3. lab3_f1dead/f1inv fault the Z1
//         lamp; the SYMMETRIC Z2-lamp variants below double the well-posed
//         recovery sample. Both are well-posed because after the broken task
//         lamp is blacklisted the target zone is still reachable DETERMINISTICALLY
//         (sun-independent) via the shared Spotlight (+150) plus the surviving
//         lamp's cross-zone spill (+150) = 325 ≥ 300 (rank 3).
//     (2) A NEW fault class — DEFECTIVE / INVERTED BLINDS. Blinds are Mediates
//         (IV-gated: lux = 0.50·sunshine), so their fault is only soundly
//         falsifiable on the OPEN action under sun rank ≥2 (QLearner conditional
//         IV-gate). The agent OPENS blinds during pre-detection ACTIVE MONITORING
//         (ε-greedy probe), observes the missing/inverted response, blacklists
//         the blind and re-learns over the surviving (lamp) levers. These cells
//         are well-posed: the task lamp survives as a deterministic rank-3 lever.

//   lab3_f1dead_z2 → DEAD Z2 lamp in the Complex lab (symmetric to lab3_f1dead).
lab_profile("lab3_f1dead_z2",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f1dead_z2"),
            training_params(4000, 0.9970)).

//   lab3_f1inv_z2 → INVERTED Z2 lamp in the Complex lab (symmetric to lab3_f1inv).
lab_profile("lab3_f1inv_z2",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab3_f1inv_z2"),
            training_params(4000, 0.9970)).

//   lab3_f1bdead → DEAD Z1 BLIND in the Complex lab. The blind's whole lux
//   contribution (own-zone 0.50·sun + cross-zone 0.40·sun) is zeroed. Detected
//   on the OPEN action under sun rank ≥2; survivors (Z1 lamp, spotlight) give a
//   deterministic rank-3 recovery. First Mediates-fault showcase.
lab_profile("lab3_f1bdead",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f1bdead"),
            training_params(4000, 0.9970)).

//   lab3_f1binv → INVERTED Z1 BLIND in the Complex lab (own + cross contributions
//   negated). Opening it under high sun SUBTRACTS lux; from an elevated zone this
//   is caught as an opposite-direction (inverted) response, from the rank floor
//   it clamps and reads as dead — either way the blind is isolated + blacklisted.
lab_profile("lab3_f1binv",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab3_f1binv"),
            training_params(4000, 0.9970)).

//   lab2_f1bdead → DEAD Z1 BLIND in the Intermediate lab (own-zone 0.50·sun
//   zeroed; lab2 has no cross-zone/spotlight). Well-posed: the Z1 lamp (+400)
//   survives as a deterministic rank-3 lever. Blind fault at medium complexity.
lab_profile("lab2_f1bdead",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab2_f1bdead"),
            training_params(2000, 0.9960)).

//   lab2_f1binv → INVERTED Z1 BLIND in the Intermediate lab (own-zone 0.50·sun
//   negated). Survivor: the Z1 lamp. Blind inversion at medium complexity.
lab_profile("lab2_f1binv",
            td("classpath:interactions-lab2.ttl"),
            ont(["building_2_intermediate.ttl"]),
            scenarios("benchmark/scenarios_lab2.json"),
            train_scenarios("benchmark/train_scenarios_lab2.json"),
            sim_port(1893),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w2]),
            qtable_suffix("_lab2_f1binv"),
            training_params(2000, 0.9960)).

//   ── Phase 2.7 — MULTI-BLIND fault cell (EXPLORATORY, post-registration) ───
//   lab3_f2bdead → BOTH blinds dead in the Complex lab (own-zone 0.50·sun and
//   cross-zone 0.30·sun contributions zeroed for each blind). Extends the
//   iterative multi-fault detect→blacklist→warm-restart loop to the Mediates
//   class: each dead blind is only falsifiable on the OPEN probe under sun
//   rank ≥2, so the agent must run the active self-test TWICE and blacklist
//   iteratively. Survivors (Z1 lamp, Z2 lamp, Spotlight) keep BOTH zones
//   deterministically rank-3 reachable (25+400+100+150) — the first WELL-POSED
//   multi-fault cell (the lamp f2* cells leave only sun-gated survivors).
//   Registered as an EXPLORATORY cell (pre_registration.md §9.11): full
//   statistics reported, never a member of the frozen §9.5/§9.6 BH families.
lab_profile("lab3_f2bdead",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f2bdead"),
            training_params(4000, 0.9970)).

//   labmon_f1dead → DEAD primary lamp in the Monitor emergency-fallback lab.
//   After the lamp is blacklisted, the ONLY surviving rank-3 path is
//   {Z1Monitor, Z1Backup} = 375 lux (deterministic, sun-independent). The
//   MONITOR is the necessary unconventional fallback; the KG-primed agent
//   (positive Causes-light priors on the monitor + backup ON actions) should
//   re-align faster than the tabula-rasa agent. Reuses the parent labmon
//   ont/td/port so the warm-loaded Q-table shape matches.
lab_profile("labmon_f1dead",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon_f1dead"),
            training_params(1500, 0.9950)).

//   lab3_f2dead_lowsun → BOTH task lamps dead AND the episode sun PINNED to
//   rank-1 (100 lux) in the Complex lab. Unlike lab3_f2dead (which is degraded
//   only on low-sun episodes because the blinds reach rank 3 at high sun), the
//   pinned low sun makes the nominal rank-3 goal UNREACHABLE in BOTH zones on
//   EVERY episode: per-zone ceiling = 25 + spotlight(150) + own-blind(50) +
//   cross-blind(40) = 265 lux = rank 2. This is the MULTI-SURVIVOR degradation
//   cell: after both lamps are blacklisted the survivors are Z1Blinds, Z2Blinds
//   and the Spotlight (3 actuators → 8 probe combos), and BOTH zones degrade to
//   rank 2. The Spotlight — REDUNDANT and avoided in the clean lab — becomes the
//   ESSENTIAL best-effort lever; the KG's structural prior should let it re-value
//   the spotlight and reconverge faster than the tabula-rasa agent. Reuses the
//   lab3 ont/td/port so the warm-loaded Q-table shape matches.
// NOTE: scenarios/train_scenarios reused from lab3 (clean parent); lowsun pins training resets only, not benchmark setState overrides.
lab_profile("lab3_f2dead_lowsun",
            td("classpath:interactions-lab3.ttl"),
            ont(["building_3_complex.ttl"]),
            scenarios("benchmark/scenarios_lab3.json"),
            train_scenarios("benchmark/train_scenarios_lab3.json"),
            sim_port(1894),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_lab3_f2dead_lowsun"),
            training_params(4000, 0.9970)).

//   labmon2_f2dead_lowsun → BOTH primary task lamps dead AND the episode sun
//   PINNED to rank-1 (100 lux) in the dual-zone monitor lab. With both lamps
//   gone and sun = 100 the per-zone ceiling = 25 + monitor(200) + blind(50)
//   = 275 lux = rank 2, so the nominal rank-3 goal is UNREACHABLE in BOTH zones
//   on EVERY episode. Survivors after the two lamps are blacklisted = Z1Monitor,
//   Z2Monitor, Z1Blinds, Z2Blinds (4 actuators → 16 probe combos), and BOTH
//   zones degrade to rank 2. The MONITOR (Causes light, rank 2 alone) is the
//   ESSENTIAL best-effort lever in each zone; the KG's structural prior (Monitor
//   Causes light) should let it re-value and reconverge faster than tabula-rasa.
//   Reuses the labmon2 ont/td/port so the warm-loaded Q-table shape matches.
// NOTE: scenarios/train_scenarios reused from labmon2 (clean parent); lowsun pins training resets only, not benchmark setState overrides.
lab_profile("labmon2_f2dead_lowsun",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon2_f2dead_lowsun"),
            training_params(4000, 0.9970)).

//   ── Phase 2.6 — FAULTY cells of the KG-SILENT monitor variants ────────────
//   Same fault injections (and simulator flows) as labmon_f1dead and
//   labmon2_f2dead_lowsun, but the agents' KG is the misdocumented (_infoonly)
//   or undocumented (_nostereo) variant, and they warm-load the Q-table
//   trained on the MATCHING clean variant. The monitor is now the essential
//   best-effort lever — but the KG never told either arm it emits light.

//   labmon_infoonly_f1dead → DEAD primary lamp; monitor (KG-silent, info-only
//   stereotype) is the only surviving lever → best-effort rank 2.
lab_profile("labmon_infoonly_f1dead",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor_infoonly.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon_infoonly_f1dead"),
            training_params(1500, 0.9950)).

//   labmon_nostereo_f1dead → DEAD primary lamp; monitor (KG-silent, no
//   stereotype) is the only surviving lever → best-effort rank 2.
lab_profile("labmon_nostereo_f1dead",
            td("classpath:interactions-labmon.ttl"),
            ont(["building_6_monitor_nostereo.ttl"]),
            scenarios("benchmark/scenarios_labmon.json"),
            train_scenarios("benchmark/train_scenarios_labmon.json"),
            sim_port(1899),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon_nostereo_f1dead"),
            training_params(1500, 0.9950)).

//   labmon2_infoonly_f2dead_lowsun → BOTH lamps dead + sun pinned to rank 1;
//   the KG-silent monitors are the essential best-effort levers in BOTH zones.
lab_profile("labmon2_infoonly_f2dead_lowsun",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor_infoonly.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon2_infoonly_f2dead_lowsun"),
            training_params(4000, 0.9970)).

//   labmon2_nostereo_f2dead_lowsun → BOTH lamps dead + sun pinned to rank 1;
//   the KG-silent monitors are the essential best-effort levers in BOTH zones.
lab_profile("labmon2_nostereo_f2dead_lowsun",
            td("classpath:interactions-labmon2.ttl"),
            ont(["building_7_dualmonitor_nostereo.ttl"]),
            scenarios("benchmark/scenarios_labmon2.json"),
            train_scenarios("benchmark/train_scenarios_labmon2.json"),
            sim_port(1900),
            light_bounds([50, 100, 300]),
            sunshine_bounds([50, 200, 600]),
            zone_targets([target(1, 3), target(2, 3)]),
            sunshine_prob(0.75),
            weakness_flags([w4]),
            qtable_suffix("_labmon2_nostereo_f2dead_lowsun"),
            training_params(4000, 0.9970)).

/* ============================================================
 * adapt_source/2 — maps a FAULTY profile to the clean parent's
 * qtable_suffix, so the Phase-2 adapt agent warm-loads the right
 * Phase-1 Q-table (qtable_final_stereotypes_<bool><CleanSuffix>.csv).
 * ============================================================ */
adapt_source("lab1_f1dead", "_lab1").
adapt_source("lab2_f1dead", "_lab2").
adapt_source("lab2_f1inv",  "_lab2").
adapt_source("lab3_f1dead", "_lab3").
adapt_source("lab3_f1inv",  "_lab3").
adapt_source("lab2_f2dead", "_lab2").
adapt_source("lab2_f2inv",  "_lab2").
adapt_source("lab3_f2dead", "_lab3").
adapt_source("lab3_f2inv",  "_lab3").
// Phase 2 extension — additional well-posed lamp cells + blind faults.
adapt_source("lab3_f1dead_z2", "_lab3").
adapt_source("lab3_f1inv_z2",  "_lab3").
adapt_source("lab3_f1bdead",   "_lab3").
adapt_source("lab3_f1binv",    "_lab3").
adapt_source("lab2_f1bdead",   "_lab2").
adapt_source("lab2_f1binv",    "_lab2").
// Phase 2.7 — multi-blind exploratory cell (pre_registration.md §9.11).
adapt_source("lab3_f2bdead",   "_lab3").
// Phase 2.5 — monitor emergency-fallback lab.
adapt_source("labmon_f1dead",  "_labmon").
// Phase 2.5B — lab3 multi-survivor degraded cell (both lamps dead + sun pinned).
adapt_source("lab3_f2dead_lowsun", "_lab3").
// Phase 2.5 — labmon2 dual-zone multi-survivor monitor fallback (both lamps dead + sun pinned).
adapt_source("labmon2_f2dead_lowsun", "_labmon2").
// Phase 2.6 — KG-silent monitor variants: each faulty cell warm-loads the
// Q-table trained on the MATCHING clean variant (same KG, same action space).
adapt_source("labmon_infoonly_f1dead",         "_labmon_infoonly").
adapt_source("labmon_nostereo_f1dead",         "_labmon_nostereo").
adapt_source("labmon2_infoonly_f2dead_lowsun", "_labmon2_infoonly").
adapt_source("labmon2_nostereo_f2dead_lowsun", "_labmon2_nostereo").

/* ============================================================
 * Convenience accessors — resolve one field of the active profile.
 * Each accessor unifies its single output argument with the
 * corresponding value in the lab_profile/13 record for the
 * profile currently named by active_profile/1.
 * ============================================================ */

@profile_td
+!profile_td(TdUrl)
    : active_profile(P) & lab_profile(P, td(TdUrl), _, _, _, _, _, _, _, _, _, _, _) <- true.

@profile_ont
+!profile_ont(Ont)
    : active_profile(P) & lab_profile(P, _, ont(Ont), _, _, _, _, _, _, _, _, _, _) <- true.

@profile_scenarios
+!profile_scenarios(File)
    : active_profile(P) & lab_profile(P, _, _, scenarios(File), _, _, _, _, _, _, _, _, _) <- true.

@profile_train_scenarios
+!profile_train_scenarios(File)
    : active_profile(P) & lab_profile(P, _, _, _, train_scenarios(File), _, _, _, _, _, _, _, _) <- true.

@profile_sim_port
+!profile_sim_port(Port)
    : active_profile(P) & lab_profile(P, _, _, _, _, sim_port(Port), _, _, _, _, _, _, _) <- true.

@profile_light_bounds
+!profile_light_bounds(B)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, light_bounds(B), _, _, _, _, _, _) <- true.

@profile_sunshine_bounds
+!profile_sunshine_bounds(B)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, sunshine_bounds(B), _, _, _, _, _) <- true.

@profile_zone_targets
+!profile_zone_targets(T)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, _, zone_targets(T), _, _, _, _) <- true.

@profile_sunshine_prob
+!profile_sunshine_prob(SP)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, _, _, sunshine_prob(SP), _, _, _) <- true.

@profile_weakness_flags
+!profile_weakness_flags(F)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, _, _, _, weakness_flags(F), _, _) <- true.

@profile_qtable_suffix
+!profile_qtable_suffix(S)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, _, _, _, _, qtable_suffix(S), _) <- true.

@profile_training_params
+!profile_training_params(NumEps, EpDecay)
    : active_profile(P) & lab_profile(P, _, _, _, _, _, _, _, _, _, _, _, training_params(NumEps, EpDecay)) <- true.

/* ============================================================
 * Diagnostic helper — print the active profile.
 * ============================================================ */
@profile_print
+!profile_print
    : active_profile(P)
    & lab_profile(P, td(Td), ont(Ont), scenarios(Sc), train_scenarios(Tr),
                  sim_port(Port), light_bounds(LB), sunshine_bounds(SB),
                  zone_targets(ZT), sunshine_prob(SP), weakness_flags(WF),
                  qtable_suffix(QS), training_params(NumEps, EpDecay)) <-
    .print("[Profile] active=", P);
    .print("[Profile]   td=", Td);
    .print("[Profile]   ont=", Ont);
    .print("[Profile]   scenarios=", Sc, "  train_scenarios=", Tr);
    .print("[Profile]   sim_port=", Port);
    .print("[Profile]   light_bounds=", LB, "  sunshine_bounds=", SB);
    .print("[Profile]   zone_targets=", ZT, "  sunshine_prob=", SP);
    .print("[Profile]   weakness_flags=", WF, "  qtable_suffix=", QS);
    .print("[Profile]   training_params: num_episodes=", NumEps, " epsilonDecay=", EpDecay).
