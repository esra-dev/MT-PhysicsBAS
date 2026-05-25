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
active_profile("custom2").

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
