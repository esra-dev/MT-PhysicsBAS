// Illuminance Controller Agent — Ontology-Driven Dynamic Control
// MT-Esra Project
//
// All zone discovery, goal mapping, and actuator dispatch are resolved at
// runtime from the BRICK + Elementary Ontology knowledge graph.
// No component names, zone names, or WoT action URIs are hardcoded here.

/* ============================================
 * Initial Beliefs
 * ============================================ */

// WoT Thing Description URLs
lab_environment_simulated("https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab.ttl").
lab_environment_real("https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab-real.ttl").
lab_environment_custom("classpath:interactions-lab-custom.ttl").

// Target illuminance rank per zone (0 = dark … 3 = bright). Keyed by ws:zoneIndex value.
// Edit these beliefs to set different target ranks per workstation.
zone_target(1, 3).
zone_target(2, 2).

// Maximum control attempts to prevent infinite loops
max_control_attempts(10).

// Delay between actions in milliseconds (for environment to stabilise)
action_delay(2000).

/* ============================================
 * Initial Goals
 * ============================================ */

!start. // The agent has the goal to start

/* ============================================
 * @start Plan — Initialise artifacts and discover zones from ontology
 * ============================================
 * ENVIRONMENT SELECTION: change LabURL = SimulatedURL to switch environments.
 *   SimulatedURL — original simulated lab (port 1880, fetched from GitHub)
 *   CustomURL    — custom lab with spotlight + radiators (port 1881, local TD)
 *   RealURL      — physical lab
 */
@start
+!start : lab_environment_simulated(SimulatedURL)
        & lab_environment_custom(CustomURL)
        & lab_environment_real(RealURL) <-

    // ========================================
    // ENVIRONMENT SELECTION — change here to switch
    // ========================================
    // LabURL = SimulatedURL;
    // Custom lab (port 1881, spotlight + radiators):
    LabURL = CustomURL;
    // Real lab:
    // LabURL = RealURL;
    // ========================================

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT — DYNAMIC DISCOVERY");
    .print("   Architecture: BRICK + Elementary Ontology via SPARQL");
    .print("   Ref: Cecconi et al., Component Stereotypes (2023)");
    .print("==========================================================");

    // Create the LabEnvironment artifact (loads WoT Thing Description)
    makeArtifact("lab", "tools.LabEnvironment", [LabURL], LabArtifactId);
    +lab_artifact(LabArtifactId);
    .print("Lab artifact created (WoT Thing Description loaded).");

    // Create the OntologyArtifact (loads lab-ontology.ttl into Apache Jena)
    makeArtifact("ontology", "tools.OntologyArtifact", ["lab-ontology.ttl"], OntArtifactId);
    +ontology_artifact(OntArtifactId);
    .print("Ontology artifact created. KG loaded from lab-ontology.ttl.");
    .print("  Three-layer Elementary Ontology: Mechanism -> Stereotype -> Instance");
    .print("  SPARQL drives all discovery: no component names hardcoded.");

    // ┌───────────────────────────────────────────────────────────────┐
    // │  Discretisation Bounds — read from ontology, configure LabEnv    │
    // └───────────────────────────────────────────────────────────────┘
    getDiscretizationBounds("http://w3id.org/elementary#luminiscence",
        LightBounds)[artifact_id(OntArtifactId)];
    getDiscretizationBounds("http://example.org/was/lab/stereotypes#outdoorIlluminance",
        SunshineBounds)[artifact_id(OntArtifactId)];
    configureDiscretization(LightBounds, SunshineBounds)[artifact_id(LabArtifactId)];
    .print("  Discretisation bounds from ontology: light=", LightBounds,
           " sunshine=", SunshineBounds);

    // ┌───────────────────────────────────────────────────────────────┐
    // │  Zone Discovery — queries ws:zoneIndex, returns sorted parallel arrays   │
    // │  ZoneURIs  = ["http://…/lab#Zone1", "http://…/lab#Zone2"]              │
    // │  ZoneIdxs  = [1, 2]                                                       │
    // └───────────────────────────────────────────────────────────────┘
    discoverZones(ZoneURIs, ZoneIdxs)[artifact_id(OntArtifactId)];
    .length(ZoneURIs, NZones);
    .print("Discovered ", NZones, " zone(s) from ontology: ", ZoneURIs);

    // ┌───────────────────────────────────────────────────────────────┐
    // │  For each zone, discover the actuatable process variable              │
    // │  (DV of actuators = IV of sensors = "Indoor illuminance               │
    // │   level"). Build zone_goal/5 beliefs paired with targets.            │
    // └───────────────────────────────────────────────────────────────┘
    !setup_zone_goals(ZoneURIs, ZoneIdxs);

    .print("Zone goals established. Starting control loop.");
    .print("----------------------------------------------------------");
    !control_illuminance(0).

/* ============================================
 * Zone Goal Setup — recursive
 * Asserts zone_goal(ZoneURI, ZoneIdx, QUri, QLabel, Target) for each zone
 * ============================================ */
@setup_zone_goals_done
+!setup_zone_goals([], []) <-
    .print("Zone goal setup complete.").

@setup_zone_goals_step
+!setup_zone_goals([ZoneURI|RestURIs], [ZoneIdx|RestIdx]) <-
    ?ontology_artifact(OntId);
    ?zone_target(ZoneIdx, Target);
    // discoverZoneQuantity traverses: sensor IV -> actuator DV -> shared variable
    discoverZoneQuantity(ZoneURI, QUri, QLabel)[artifact_id(OntId)];
    +zone_goal(ZoneURI, ZoneIdx, QUri, QLabel, Target);
    .print("  zone_goal: idx=", ZoneIdx, " quantity='", QLabel,
           "' target=", Target, " zone=", ZoneURI);
    !setup_zone_goals(RestURIs, RestIdx).

/* ============================================
 * Main Control Loop
 * ============================================ */
@control_illuminance_loop
+!control_illuminance(Attempt)
    : max_control_attempts(MaxAttempts)
    & Attempt < MaxAttempts <-

    .print("");
    .print("--- Control Attempt ", Attempt + 1, " of ", MaxAttempts, " ---");

    // Collect all current zone goals
    .findall(goal(ZUri, ZIdx, QUri, QLabel, Target),
             zone_goal(ZUri, ZIdx, QUri, QLabel, Target),
             ZoneGoals);

    // Reset the "all satisfied" flag (optimistic: assume done until a zone is not)
    -all_zones_satisfied(_);
    +all_zones_satisfied(true);

    // Read state and adjust each zone; updates all_zones_satisfied if any is off-target
    !process_zone_list(ZoneGoals);

    ?all_zones_satisfied(Done);
    -all_zones_satisfied(_);

    if (Done) {
        .print("");
        .print("==========================================================");
        .print("   SUCCESS! All zones have reached target illuminance!");
        .print("==========================================================");
    } else {
        ?action_delay(Delay);
        .wait(Delay);
        !control_illuminance(Attempt + 1);
    }.

@control_illuminance_max_reached
+!control_illuminance(Attempt)
    : max_control_attempts(MaxAttempts)
    & Attempt >= MaxAttempts <-
    .print("==========================================================");
    .print("   Maximum control attempts (", MaxAttempts, ") reached.");
    .print("==========================================================").

/* ============================================
 * Zone List Processor
 * One HTTP call per cycle; dispatches to per-zone step plans.
 * Also stores lab state as agent beliefs (P14).
 * ============================================ */
@process_zone_list
+!process_zone_list(ZoneGoals) <-
    ?lab_artifact(LabId);
    // Single HTTP call: all zone levels, sunshine rank, all boolean WoT states.
    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    -+lab_sunshine(SunshineRank);
    -+lab_bool_state(SKs, SVs);
    .print("[Lab snapshot] sunshine=", SunshineRank, " active_states=", SKs);
    // readLabStatus returns levels in ascending zone-index order (TreeMap in Java).
    // Collect and sort zone indices the same way, then pass both sorted lists into
    // process_zone_steps so each goal can look up its level by index directly.
    .findall(I, zone_goal(_, I, _, _, _), ZIdxUnsorted);
    .sort(ZIdxUnsorted, ZIdxSorted);
    !process_zone_steps(ZoneGoals, ZIdxSorted, ZoneLevels, SunshineRank, SKs, SVs).

/* ============================================
 * Level lookup — walks two parallel sorted lists (indices, levels) until the
 * requested index is found. Pure unification: no arithmetic, no belief mutations.
 * Works for any number of zones.
 * ============================================ */
@get_zone_level_found
+!get_zone_level([ZIdx|_], [Level|_], ZIdx, Level) <- true.

@get_zone_level_search
+!get_zone_level([_|RestIdx], [_|RestLevels], ZIdx, Level) <-
    !get_zone_level(RestIdx, RestLevels, ZIdx, Level).

@process_zone_steps_empty
+!process_zone_steps([], _, _, _, _, _) <- true.

@process_zone_steps_step
+!process_zone_steps([goal(ZUri, ZIdx, QUri, QLabel, Target)|RestGoals],
                     ZIdxSorted, ZoneLevels, SunshineRank, SKs, SVs) <-
    // Look up this zone's current level by index — order-independent.
    !get_zone_level(ZIdxSorted, ZoneLevels, ZIdx, Level);
    .print("[Zone ", ZIdx, "] '", QLabel, "' level=", Level, "/", Target,
           " sunshine=", SunshineRank);
    if (Level == Target) {
        .print("[Zone ", ZIdx, "] At target. No action needed.")
    } else {
        -all_zones_satisfied(_); +all_zones_satisfied(false);
        if (Level < Target) {
            !increase_zone(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs)
        } else {
            !decrease_zone(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs)
        }
    };
    !process_zone_steps(RestGoals, ZIdxSorted, ZoneLevels, SunshineRank, SKs, SVs).

-!process_zone_steps(_, _, _, _, _, _) <-
    .print("WARNING: Zone step processing encountered an error.").

/* ============================================
 * Ontology-Driven Actuator Selection and Dispatch
 * ============================================
 * queryBestIncreaseAction / queryBestDecreaseAction:
 *   Input:  zone URI, DV URI (from discoverZoneQuantity), current sensor states
 *   Output: CompId (ontology local name), mechanism/MV/DV/IV labels, WotActionType URI
 *
 * invokeAction:
 *   Sends the WoT action identified by its @type URI — no if-elif chain needed.
 * ============================================ */
@increase_zone
+!increase_zone(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    // SPARQL: filter components in zone whose DV = QUri, IV rank satisfied,
    // and current state (looked up via ws:hasWoTStateSemanticType) is inactive.
    queryBestIncreaseAction(ZUri, QUri, SunshineRank, SKs, SVs,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel, WotActionType)[artifact_id(OntId)];
    if (CompId \== "none") {
        .print("[Zone ", ZIdx, "] INCREASE '", QLabel, "' via: ", CompId);
        .print("  Mechanism : ", Mechanism);
        .print("  MV (input): ", MvLabel, " -> ACTIVATE");
        .print("  DV (goal) : ", DvLabel, " will INCREASE");
        .print("  IV (cond) : ", IvLabel, " | sunshine=", SunshineRank);
        .print("  WoT action: ", WotActionType);
        // Generic dispatch: WoT action URI comes from ontology, no component name needed
        invokeAction(WotActionType, true)[artifact_id(LabId)];
        .print("[DISPATCH] invokeAction(", WotActionType, ", true) -> sent")
    } else {
        .print("[Zone ", ZIdx, "] No component can INCREASE '", QLabel, "'.");
        .print("  Cause: IV rank unsatisfied or all components already active.");
        .print("  sunshine=", SunshineRank)
    }.

@decrease_zone
+!decrease_zone(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    // SPARQL: filter components in zone whose DV = QUri, and current state
    // (via ws:hasWoTStateSemanticType map lookup) is active (true).
    queryBestDecreaseAction(ZUri, QUri, SunshineRank, SKs, SVs,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel, WotActionType)[artifact_id(OntId)];
    if (CompId \== "none") {
        .print("[Zone ", ZIdx, "] DECREASE '", QLabel, "' via: ", CompId);
        .print("  Mechanism : ", Mechanism);
        .print("  MV (input): ", MvLabel, " -> DEACTIVATE");
        .print("  DV (goal) : ", DvLabel, " will DECREASE");
        .print("  WoT action: ", WotActionType);
        invokeAction(WotActionType, false)[artifact_id(LabId)];
        .print("[DISPATCH] invokeAction(", WotActionType, ", false) -> sent")
    } else {
        .print("[Zone ", ZIdx, "] No component can DECREASE '", QLabel, "'.");
        .print("  Cause: All components already deactivated.")
    }.

/* ============================================
 * Failure Handling Plans
 * ============================================ */

-!start <-
    .print("ERROR: Failed to start the illuminance controller agent.");
    .print("Check that the Thing Description URL is accessible and lab-ontology.ttl is in src/resources/.").

-!control_illuminance(Attempt) : max_control_attempts(MaxAttempts) & Attempt < MaxAttempts <-
    .print("WARNING: Control attempt ", Attempt + 1, " failed. Retrying.");
    ?action_delay(Delay);
    .wait(Delay);
    !control_illuminance(Attempt + 1).

-!control_illuminance(Attempt) <-
    .print("ERROR: Control loop permanently failed at attempt ", Attempt + 1, ".").

-!setup_zone_goals(_, _) <-
    .print("ERROR: Zone goal setup failed. Check OntologyArtifact logs.").

-!process_zone_list(_) <-
    .print("WARNING: Zone list processing encountered an error.").
