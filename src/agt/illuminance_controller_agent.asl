// Illuminance Controller Agent - Simplified Rule-Based Control
// MT-Esra Project

/*
 * This agent controls the illuminance in two workstations (Zone 1 and Zone 2)
 * using rule-based logic instead of Q-learning.
 * 
 * The agent interacts with:
 * - Light sensors in each workstation
 * - Weather station (sunshine level)
 * - Blinds in each workstation (up/down)
 * - Ceiling lights in each workstation (on/off)
 */

/* ============================================
 * URL Configuration
 * ============================================
 * To switch between simulated and real environments, change the LabURL assignment
 * in the @start plan below.
 */

//* Initial beliefs *//

// Simulated lab WoT Thing Description URL
lab_environment_simulated("https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab.ttl").

// Real lab WoT Thing Description URL
lab_environment_real("https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab-real.ttl").

// Target illuminance levels for each workstation
// Zone 1 target: Rank 2 (medium illuminance: 100-300 lux)
// Zone 2 target: Rank 3 (high illuminance: >= 300 lux)
task_requirements([2, 3]).

// Maximum control attempts to prevent infinite loops
max_control_attempts(10).

// Delay between actions in milliseconds (for environment to stabilize)
action_delay(2000).

/* ============================================
 * Helper Rules - Illuminance Level Discretization
 * ============================================
 * Converts continuous lux values to discrete ranks (0-3)
 */

// Light level ranks:
// Rank 0: < 50 lux (very dark)
// Rank 1: 50-100 lux (dim)
// Rank 2: 100-300 lux (medium)
// Rank 3: >= 300 lux (bright)
light_rank(Value, 0) :- Value < 50.
light_rank(Value, 1) :- Value >= 50 & Value < 100.
light_rank(Value, 2) :- Value >= 100 & Value < 300.
light_rank(Value, 3) :- Value >= 300.

// Sunshine level ranks:
// Rank 0: < 50 lux (overcast/night)
// Rank 1: 50-200 lux (cloudy)
// Rank 2: 200-700 lux (partly sunny)
// Rank 3: >= 700 lux (sunny)
sunshine_rank(Value, 0) :- Value < 50.
sunshine_rank(Value, 1) :- Value >= 50 & Value < 200.
sunshine_rank(Value, 2) :- Value >= 200 & Value < 700.
sunshine_rank(Value, 3) :- Value >= 700.

// Rule to check if goal is achieved for both zones
goal_achieved(CurrentZ1, CurrentZ2, TargetZ1, TargetZ2) :-
    CurrentZ1 == TargetZ1 & CurrentZ2 == TargetZ2.

// Rule to check if a single zone has achieved its target
zone_goal_achieved(Current, Target) :- Current == Target.

// Rule to check if zone needs more light
needs_more_light(Current, Target) :- Current < Target.

// Rule to check if zone needs less light
needs_less_light(Current, Target) :- Current > Target.

//* Initial goals *//

!start. // The agent has the goal to start

/* ============================================
 * Main Plans
 * ============================================
 */

/* 
 * Plan: start
 * Initializes the agent and starts the illuminance control process.
 * 
 * IMPORTANT: To switch between simulated and real environments,
 * change the line "LabURL = SimulatedURL;" to "LabURL = RealURL;"
 */
@start
+!start : lab_environment_simulated(SimulatedURL)
        & lab_environment_real(RealURL)
        & task_requirements([Z1Target, Z2Target]) <-

    // ========================================
    // ENVIRONMENT SELECTION - CHANGE HERE TO SWITCH
    // ========================================
    // For SIMULATED environment:
    LabURL = SimulatedURL;
    // For REAL environment, comment the line above and uncomment:
    // LabURL = RealURL;
    // ========================================

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT - STARTING");
    .print("   Architecture: BRICK + Elementary Ontology via SPARQL");
    .print("   Ref: Cecconi et al., Component Stereotypes (2023)");
    .print("==========================================================");
    .print("Target illuminance levels:");
    .print("  Zone 1: Rank ", Z1Target);
    .print("  Zone 2: Rank ", Z2Target);
    .print("Environment URL: ", LabURL);
    .print("----------------------------------------------------------");

    // Create the LabEnvironment artifact for interacting with the lab
    makeArtifact("lab", "tools.LabEnvironment", [LabURL], LabArtifactId);
    +lab_artifact(LabArtifactId);
    .print("Lab artifact created (WoT Thing Description loaded).");

    // Create the OntologyArtifact — loads lab-ontology.ttl (BRICK + Elementary Ontology)
    // into Apache Jena. All actuation decisions from this point on are driven by
    // SPARQL queries over this knowledge graph instead of hardcoded plan guards.
    makeArtifact("ontology", "tools.OntologyArtifact", ["lab-ontology.ttl"], OntArtifactId);
    +ontology_artifact(OntArtifactId);
    .print("Ontology artifact created. KG loaded from lab-ontology.ttl.");
    .print("  Architecture: Three-layer Elementary Ontology (Cecconi et al. 2023)");
    .print("  Layer 1 - PhysicalMechanism: ws:illumination (light), ws:daylighting (blind)");
    .print("  Layer 2 - Stereotypes     : ws:CeilingLightStereotype (MV=electricalPowerInput, IV=none)");
    .print("                              ws:BlindStereotype (MV=blindApertureRatio, IV=outdoorIlluminance)");
    .print("  Layer 3 - BRICK instances : lab:CeilingLight_Z1/Z2, lab:Blind_Z1/Z2 via elem:hasStereotype");
    .print("  Decisions: SPARQL traverses hasStereotype->hasProcessMechanism->MV/DV/IV + Java IV filter");
    .print("----------------------------------------------------------");

    // Start the control loop
    !control_illuminance(Z1Target, Z2Target, 0).

/* 
 * Plan: control_illuminance
 * Main control loop that reads current state and takes actions to achieve target.
 * Uses rule-based logic to decide which action to take.
 */
@control_illuminance_main
+!control_illuminance(Z1Target, Z2Target, Attempt) 
    : max_control_attempts(MaxAttempts) 
    & Attempt < MaxAttempts <-

    ?lab_artifact(LabId);
    
    .print("");
    .print("--- Control Attempt ", Attempt + 1, " of ", MaxAttempts, " ---");

    // Read current state from the lab
    readState(Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Sunshine)[artifact_id(LabId)];
    
    .print("Current State:");
    .print("  Zone 1: Level=", Z1Level, ", Light=", Z1Light, ", Blinds=", Z1Blinds);
    .print("  Zone 2: Level=", Z2Level, ", Light=", Z2Light, ", Blinds=", Z2Blinds);
    .print("  Sunshine: ", Sunshine);
    .print("Target: Zone1=", Z1Target, ", Zone2=", Z2Target);

    // Check if both goals are achieved
    if (goal_achieved(Z1Level, Z2Level, Z1Target, Z2Target)) {
        .print("");
        .print("==========================================================");
        .print("   SUCCESS! Both zones have reached target illuminance!");
        .print("==========================================================");
        .print("Final State: Zone1=", Z1Level, ", Zone2=", Z2Level);
    } else {
        // Determine and execute actions for each zone
        !adjust_zone(1, Z1Level, Z1Target, Z1Light, Z1Blinds, Sunshine);
        !adjust_zone(2, Z2Level, Z2Target, Z2Light, Z2Blinds, Sunshine);
        
        // Wait for environment to stabilize
        ?action_delay(Delay);
        .wait(Delay);
        
        // Continue control loop
        !control_illuminance(Z1Target, Z2Target, Attempt + 1);
    }.

/* 
 * Plan: control_illuminance (max attempts reached)
 * Handles the case when maximum attempts are reached.
 */
@control_illuminance_max_reached
+!control_illuminance(Z1Target, Z2Target, Attempt) 
    : max_control_attempts(MaxAttempts) 
    & Attempt >= MaxAttempts <-

    ?lab_artifact(LabId);
    readState(Z1Level, Z2Level, _, _, _, _, _)[artifact_id(LabId)];
    
    .print("");
    .print("==========================================================");
    .print("   Maximum control attempts reached (", MaxAttempts, ")");
    .print("==========================================================");
    .print("Final State: Zone1=", Z1Level, " (target: ", Z1Target, ")");
    .print("             Zone2=", Z2Level, " (target: ", Z2Target, ")");
    
    if (goal_achieved(Z1Level, Z2Level, Z1Target, Z2Target)) {
        .print("Status: SUCCESS - Goals achieved!");
    } else {
        .print("Status: PARTIAL - Goals not fully achieved.");
        .print("Consider adjusting max_control_attempts or checking environment constraints.");
    }.

/* ============================================
 * Zone Adjustment Plans — SPARQL / Ontology Driven
 * ============================================
 * Each plan calls OntologyArtifact to run a SPARQL SELECT over
 * lab-ontology.ttl (BRICK + Elementary Ontology knowledge graph).
 *
 * The artifact returns the best component matching three criteria:
 *   1. Located in the requested zone (brick:isLocatedIn)
 *   2. IV satisfied: "none" always OK; "sunshine" requires rank >= 1
 *   3. Current state actionable: not already in target position
 *
 * Results are ordered by IV type (components with satisfied IVs pass the filter
 * first). The agent picks the first candidate that passes both the IV check and
 * the current-state check.
 *
 * The agent prints the full mechanism trace (mechanism, MV, DV, IV)
 * from the SPARQL result before dispatching the physical WoT action.
 */

/* Zone goal already achieved — no actuation needed */
@adjust_zone_achieved
+!adjust_zone(Zone, CurrentLevel, TargetLevel, _, _, _)
    : zone_goal_achieved(CurrentLevel, TargetLevel) <-
    .print("[KG QUERY] Zone ", Zone, ": Goal met. illuminance rank=", CurrentLevel,
           " equals target=", TargetLevel, ". No mechanism activation needed.").

/* Need MORE illuminance — query KG for best increase action */
@adjust_zone_increase
+!adjust_zone(Zone, CurrentLevel, TargetLevel, LightOn, BlindsUp, Sunshine)
    : needs_more_light(CurrentLevel, TargetLevel) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    // SPARQL SELECT on lab-ontology.ttl:
    //   SELECT components in zone, ordered by natural SPARQL order
    //   Java filter: IV satisfaction (sunshine>=1 for blinds) + state check
    queryBestIncreaseAction(Zone, LightOn, BlindsUp, Sunshine,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel)[artifact_id(OntId)];
    if (CompId \== "none") {
        .print("[KG QUERY] Zone ", Zone, " needs MORE illuminance. SPARQL selected: ", CompId);
        .print("  Mechanism  : ", Mechanism);
        .print("  MV (action): ", MvLabel, " -> ACTIVATE");
        .print("  DV (effect): ", DvLabel, " will INCREASE");
        .print("  IV (check) : ", IvLabel, " | current sunshine rank = ", Sunshine);
        !dispatch_action(CompId, activate, LabId);
    } else {
        .print("[KG QUERY] Zone ", Zone, ": SPARQL found NO actionable component to increase illuminance.");
        .print("  -> All candidates eliminated: IV unsatisfied OR already in target state.");
        .print("  -> sunshine=", Sunshine, " | LightOn=", LightOn, " | BlindsUp=", BlindsUp);
        .print("  -> Waiting for external conditions (e.g. sunrise / cloud change).");
    }.

/* Need LESS illuminance — query KG for best decrease action */
@adjust_zone_decrease
+!adjust_zone(Zone, CurrentLevel, TargetLevel, LightOn, BlindsUp, Sunshine)
    : needs_less_light(CurrentLevel, TargetLevel) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    // SPARQL SELECT on lab-ontology.ttl:
    //   Same query, filtered by current state only.
    queryBestDecreaseAction(Zone, LightOn, BlindsUp, Sunshine,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel)[artifact_id(OntId)];
    if (CompId \== "none") {
        .print("[KG QUERY] Zone ", Zone, " needs LESS illuminance. SPARQL selected: ", CompId);
        .print("  Mechanism  : ", Mechanism);
        .print("  MV (action): ", MvLabel, " -> DEACTIVATE");
        .print("  DV (effect): ", DvLabel, " will DECREASE");
        !dispatch_action(CompId, deactivate, LabId);
    } else {
        .print("[KG QUERY] Zone ", Zone, ": SPARQL found NO actionable component to decrease illuminance.");
        .print("  -> sunshine=", Sunshine, " | LightOn=", LightOn, " | BlindsUp=", BlindsUp);
        .print("  -> Waiting for external conditions to change.");
    }.

/* ============================================
 * Action Dispatch Plan
 * ============================================
 * Translates the component ID returned by SPARQL into a concrete
 * WoT action call on the LabEnvironment artifact.
 * CompId comes from the KG (lab:z1_light local name = "z1_light", etc.).
 * Direction is the atom 'activate' or 'deactivate'.
 */
@dispatch_action
+!dispatch_action(CompId, Direction, LabId) <-
    if      (CompId == "CeilingLight_Z1"  & Direction == activate)   {
        setZ1Light(true)[artifact_id(LabId)];
        .print("[DISPATCH] setZ1Light(true) -> WoT action sent");
    } elif  (CompId == "CeilingLight_Z1"  & Direction == deactivate) {
        setZ1Light(false)[artifact_id(LabId)];
        .print("[DISPATCH] setZ1Light(false) -> WoT action sent");
    } elif  (CompId == "CeilingLight_Z2"  & Direction == activate)   {
        setZ2Light(true)[artifact_id(LabId)];
        .print("[DISPATCH] setZ2Light(true) -> WoT action sent");
    } elif  (CompId == "CeilingLight_Z2"  & Direction == deactivate) {
        setZ2Light(false)[artifact_id(LabId)];
        .print("[DISPATCH] setZ2Light(false) -> WoT action sent");
    } elif  (CompId == "Blind_Z1" & Direction == activate)   {
        setZ1Blinds(true)[artifact_id(LabId)];
        .print("[DISPATCH] setZ1Blinds(true) -> WoT action sent");
    } elif  (CompId == "Blind_Z1" & Direction == deactivate) {
        setZ1Blinds(false)[artifact_id(LabId)];
        .print("[DISPATCH] setZ1Blinds(false) -> WoT action sent");
    } elif  (CompId == "Blind_Z2" & Direction == activate)   {
        setZ2Blinds(true)[artifact_id(LabId)];
        .print("[DISPATCH] setZ2Blinds(true) -> WoT action sent");
    } elif  (CompId == "Blind_Z2" & Direction == deactivate) {
        setZ2Blinds(false)[artifact_id(LabId)];
        .print("[DISPATCH] setZ2Blinds(false) -> WoT action sent");
    } else {
        .print("[DISPATCH] WARNING: Unknown component '", CompId, "' or direction '", Direction, "'.");
    }.

/* ============================================
 * Failure Handling Plans
 * ============================================
 */

-!start <-
    .print("ERROR: Failed to start the illuminance controller agent.");
    .print("Check that the Thing Description URL is accessible and lab-ontology.ttl is in src/resources/.").

-!control_illuminance(Z1Target, Z2Target, Attempt) <-
    .print("ERROR: Control loop failed at attempt ", Attempt);
    .print("Will retry...");
    .wait(5000);
    !control_illuminance(Z1Target, Z2Target, Attempt + 1).

-!adjust_zone(Zone, _, _, _, _, _) <-
    .print("WARNING: Failed to adjust Zone ", Zone, ". Check OntologyArtifact and LabEnvironment are running.").

-!dispatch_action(CompId, Direction, _) <-
    .print("WARNING: Failed to dispatch action for component '", CompId, "', direction '", Direction, "'.").





