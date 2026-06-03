package tools;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;

import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntModelSpec;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.ModelFactory;

/**
 * StereotypeReasoner — SPARQL-based ontology reasoning for Q-table initialization
 * and runtime action masking.
 *
 * Replaces hardcoded stereotype rules by querying lab-ontology.ttl:
 *   - Discovers actuatable components, their zones, IVs, costs, WoT URIs
 *   - Discovers cross-zone brick:feeds topology (light spill)
 *   - Computes per-zone initialization penalties for decomposed Q-tables
 *   - Provides runtime action applicability filtering
 *
 * This is a plain Java class (NOT a CArtAgO artifact), instantiated by QLearner.
 */
public class StereotypeReasoner {

    private static final Logger LOGGER = Logger.getLogger(StereotypeReasoner.class.getName());

    // -----------------------------------------------------------------------
    // Inner data structures
    // -----------------------------------------------------------------------

    /** Per-action metadata discovered from the ontology. */
    public static class ActionInfo {
        public int actionIndex;
        public String wotActionType;   // e.g. "http://example.org/was#SetZ1Light"
        public boolean wotValue;       // true for ON/OPEN, false for OFF/CLOSE
        public String wotStateType;    // e.g. "http://example.org/was#Z1Light"
        public int stateVecBitIndex;   // which bit in state vector this controls (-1 for DO_NOTHING)
        public int expectedBitValue;   // value the bit would have AFTER action (1=ON, 0=OFF)
        public Set<Integer> affectedZones; // 0-based zone indices this action affects
        public boolean hasIV;          // true if mechanism has independent variable
        public int ivStateVecIndex;    // which state vec element is the IV (e.g. IDX_SUNSHINE)
        public int ivMinRank = 1;      // KG-9: minimum IV rank at which Mediates effect is meaningful
                                       //       (ws:ivMinRank in the ontology; defaults to 1 when absent)
        public String label;           // human-readable label

        public ActionInfo() {
            affectedZones = new HashSet<>();
        }
    }

    /** Cross-zone effect: action in zone A spills to zone B. */
    public static class CrossZoneEffect {
        public int actionIndex;
        public int sourceZoneIdx;  // 0-based
        public int targetZoneIdx;  // 0-based
    }

    // -----------------------------------------------------------------------
    // State vector layout (data-driven from wot-mappings.ttl slot registry)
    // -----------------------------------------------------------------------
    // Populated by loadStateSlotRegistry() during construction.
    private int[] domainSizes;        // domainSizes[svIdx] = cardinality of slot
    private int[] zoneLevelIndices;   // zoneLevelIndices[zoneIdx0Based] = state-vector slot
    private int   sunshineIndex = -1; // -1 if no sunshine slot

    // -----------------------------------------------------------------------
    // SPARQL queries
    // -----------------------------------------------------------------------

    private static final String PREFIXES =
        "PREFIX brick: <https://brickschema.org/schema/Brick#>\n" +
        "PREFIX elem:  <http://w3id.org/elementary#>\n" +
        "PREFIX ws:    <http://example.org/was/lab/stereotypes#>\n" +
        "PREFIX lab:   <http://example.org/was/lab#>\n" +
        "PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>\n";

    /**
     * Discover all actuatable components via elem:hasComponentAction: those with a
     * stereotype whose mechanism has a manipulated variable AND that affect the
     * target DV (illuminance). Each row is one action (ON or OFF).
     */
    private static final String ACTUATOR_DISCOVERY_QUERY = PREFIXES +
        "SELECT ?comp ?zone ?zoneIdx ?dvLabel ?iv ?ivMinRank " +
        "       ?wotActionType ?wotStateType ?actionValue\n" +
        "WHERE {\n" +
        "  ?comp  brick:isLocatedIn             ?zone .\n" +
        "  ?zone  a                             lab:Workstation .\n" +
        "  ?zone  ws:zoneIndex                  ?zoneIdx .\n" +
        "  ?comp  elem:hasBehavioralStereotype  ?stereo .\n" +
        "  ?stereo elem:hasPhysicalMechanism    ?mech .\n" +
        "  ?mech  elem:hasManipulatedVariable   ?mv .\n" +
        "  ?mech  elem:hasDependentVariable     ?dv .\n" +
        "  ?dv    rdfs:label                    ?dvLabel .\n" +
        "  FILTER EXISTS { ?dv elem:hasQuantity <http://qudt.org/vocab/quantitykind/Illuminance> }\n" +
        "  ?comp  elem:hasComponentAction       ?action .\n" +
        "  ?action ws:actionValue               ?actionValue .\n" +
        "  OPTIONAL {\n" +
        "    ?mech elem:hasIndependentVariable ?iv .\n" +
        "  }\n" +
        "  OPTIONAL { ?mech ws:ivMinRank ?ivMinRank . }\n" +
        "  OPTIONAL { ?comp ws:hasWoTActionSemanticType ?wotActionType . }\n" +
        "  OPTIONAL { ?comp ws:hasWoTStateSemanticType  ?wotStateType . }\n" +
        "}\n" +
        "ORDER BY ?zoneIdx ?wotActionType ?actionValue";

    /**
     * Discover cross-zone feed arcs: actuatable components that feed sensors
     * in a different zone (light spill).
     */
    private static final String CROSS_ZONE_FEEDS_QUERY = PREFIXES +
        "SELECT ?sourceComp ?sourceZoneIdx ?targetZoneIdx ?wotActionType\n" +
        "WHERE {\n" +
        "  ?sourceComp brick:feeds ?targetSensor .\n" +
        "  ?sourceComp brick:isLocatedIn ?sourceZone .\n" +
        "  ?sourceZone ws:zoneIndex ?sourceZoneIdx .\n" +
        "  ?targetSensor brick:isLocatedIn ?targetZone .\n" +
        "  ?targetZone ws:zoneIndex ?targetZoneIdx .\n" +
        "  ?sourceComp elem:hasBehavioralStereotype ?stereo .\n" +
        "  ?stereo elem:hasPhysicalMechanism ?mech .\n" +
        "  ?mech elem:hasManipulatedVariable ?mv .\n" +
        "  ?sourceComp ws:hasWoTActionSemanticType ?wotActionType .\n" +
        "  FILTER (?sourceZoneIdx != ?targetZoneIdx)\n" +
        "}";

    // -----------------------------------------------------------------------
    // Fields
    // -----------------------------------------------------------------------
    private ActionInfo[] actions;
    private List<CrossZoneEffect> crossZoneEffects;
    private double sunshineSatisfactionProb;
    private int numActions;

    /**
     * True if the state-slot registry could not be loaded from the ontology
     * and the reasoner is operating on the legacy hard-coded fallback layout.
     * In this mode stereotype-guided initialisation is still functional but
     * may not reflect the simulator topology — callers should log a banner.
     */
    private boolean degraded = false;

    // Maps WoT action URI -> set of 0-based zone indices
    private Map<String, Set<Integer>> wotActionToZones;
    // Maps WoT state URI -> state vector bit index
    private Map<String, Integer> wotStateToSvIndex;

    // -----------------------------------------------------------------------
    // IV effectiveness tracker — learns ivMinRank at runtime
    // -----------------------------------------------------------------------
    // For each action that has an IV: per IV rank (0–3), track how many times
    // the action was tried and how many times it caused a positive DV change.
    // Once enough samples are collected, compute the minimum effective rank.
    private int[][] ivTrialCount;     // [numActions][4]
    private int[][] ivSuccessCount;   // [numActions][4]
    /**
     * Minimum number of trials at a given IV rank before we trust the data.
     * Override with -Dstereo.ivMinSamples=N.
     * Audit Step 2 §S2-6: kept at 10 — sample budget at sun rank 1 on custom8
     * is ~50 trials over the full training horizon (50% sun-saturation × 10k
     * episodes × ~1 blind activation/episode), so 10 is a defensible floor.
     */
    private static final int IV_MIN_SAMPLES =
        Integer.parseInt(System.getProperty("stereo.ivMinSamples", "10"));
    /**
     * An action is considered effective if success rate exceeds this threshold.
     * Override with -Dstereo.ivEffectivenessThreshold=...
     * Audit Step 2 §S2-6: default lowered from 0.10 → 0.05 because custom8's
     * rank-discretisation (boundary gap 75 lux at the [75,200,400] bounds)
     * makes a true single-step rank crossing structurally rare at sun rank 1.
     * The proper fix is a lux-Δ criterion (requires plumbing raw lux through
     * recordActionOutcome); the lower threshold is the minimally-invasive
     * approximation. Set to 0.10 to restore the original (overly strict) gate.
     */
    private static final double IV_EFFECTIVENESS_THRESHOLD =
        Double.parseDouble(System.getProperty("stereo.ivEffectivenessThreshold", "0.05"));

    /**
     * Magnitude of the soft prior applied to actions that are redundant in
     * the current state (actuator already in target state).
     * Override with -Dstereo.priorRedundant=...  (default 1.0 → returned as -1.0).
     * Audit Step 3b §S3b-4: default lowered from 5.0 → 1.0 so the magnitude
     * is comparable to the per-step combinedQ Bellman swing (~5) and a
     * handful of positive samples can out-vote it. Combined with
     * STEREO_PRIOR_SCALE=1.0 the bench-time bias on a redundant action is
     * -1.0 instead of the historical -25.
     */
    private static final double PRIOR_REDUNDANT_MAG =
        Double.parseDouble(System.getProperty("stereo.priorRedundant", "1.0"));
    /**
     * Magnitude of the soft prior applied to activation actions whose IV is
     * not satisfied (e.g. blind ON at sun rank 0).
     * Override with -Dstereo.priorIVUnsat=...  (default 5.0 → returned as -5.0).
     * Audit Step 3b §S3b-4: default lowered from 25.0 → 5.0 (10% of
     * REWARD_CLIP); bench-time bias on an IV-unsat action becomes -5.0 instead
     * of the historical -125.
     */
    private static final double PRIOR_IV_UNSAT_MAG =
        Double.parseDouble(System.getProperty("stereo.priorIVUnsat", "5.0"));
    /**
     * Multiplicative scale applied to ALL ontology-driven Q-init penalties
     * computed in {@link #getInitPenaltyForZone}. Override with
     * -Dstereo.initPenaltyScale=... (default 0.5).
     * Audit Step 2 §S2-5: original code returned penalties up to -250 per cell
     * stacked, which required ~80 cell visits to escape — but mean visits per
     * (s,a) on custom8 is ~9. Softening by 2× brings the worst-case well to
     * -125 (and the most common -100 redundancy to -50), which the Bellman
     * target ±12.5 per zone can reasonably overcome under the training budget.
     * Set to 1.0 to restore the original magnitudes (used by H5 ablations).
     */
    private static final double INIT_PENALTY_SCALE =
        Double.parseDouble(System.getProperty("stereo.initPenaltyScale", "0.5"));

    // -----------------------------------------------------------------------
    // Ontology loading — injectable for testability (#11 DI refactor)
    // -----------------------------------------------------------------------

    /**
     * Strategy for producing the merged OntModel that the reasoner queries.
     * Production code uses {@link ClasspathOntologyLoader}; unit tests use
     * {@link InMemoryOntologyLoader} with synthetic Turtle fixtures.
     */
    public interface OntologyLoader {
        OntModel load();
    }

    /** Default loader: reads Turtle files from the classpath. */
    public static class ClasspathOntologyLoader implements OntologyLoader {
        private final String[] paths;
        public ClasspathOntologyLoader(String[] paths) { this.paths = paths; }
        @Override public OntModel load() {
            OntModel model = ModelFactory.createOntologyModel(OntModelSpec.OWL_MEM_MICRO_RULE_INF);
            for (String path : paths) {
                InputStream is = getClass().getClassLoader().getResourceAsStream(path);
                if (is == null) {
                    throw new RuntimeException(
                        "StereotypeReasoner: ontology not found on classpath: " + path);
                }
                model.read(is, null, "TURTLE");
                LOGGER.info("StereotypeReasoner: loaded ontology from " + path);
            }
            return model;
        }
    }

    /** Test loader: parses one or more in-memory Turtle strings. */
    public static class InMemoryOntologyLoader implements OntologyLoader {
        private final String[] turtleSources;
        public InMemoryOntologyLoader(String... turtleSources) { this.turtleSources = turtleSources; }
        @Override public OntModel load() {
            OntModel model = ModelFactory.createOntologyModel(OntModelSpec.OWL_MEM_MICRO_RULE_INF);
            for (int i = 0; i < turtleSources.length; i++) {
                model.read(new java.io.ByteArrayInputStream(
                    turtleSources[i].getBytes(java.nio.charset.StandardCharsets.UTF_8)), null, "TURTLE");
                LOGGER.fine("StereotypeReasoner: loaded in-memory ontology source #" + i);
            }
            return model;
        }
    }

    // -----------------------------------------------------------------------
    // Constructors
    // -----------------------------------------------------------------------

    /**
     * Back-compat constructor: load Turtle files from the classpath.
     *
     * @param ontologyResourcePaths    classpath resource paths (e.g. "lab-ontology.ttl", "wot-mappings.ttl")
     * @param sunshineSatisfactionProb P(sunshine >= rank 1) from simulator distribution
     */
    public StereotypeReasoner(String[] ontologyResourcePaths, double sunshineSatisfactionProb) {
        this(new ClasspathOntologyLoader(ontologyResourcePaths), sunshineSatisfactionProb);
    }

    /**
     * DI constructor: supply any {@link OntologyLoader}. Used by unit tests
     * with synthetic fixtures via {@link InMemoryOntologyLoader}.
     *
     * @param loader                   strategy that returns the merged OntModel
     * @param sunshineSatisfactionProb P(sunshine >= rank 1) from simulator distribution
     */
    public StereotypeReasoner(OntologyLoader loader, double sunshineSatisfactionProb) {
        this.sunshineSatisfactionProb = sunshineSatisfactionProb;
        this.crossZoneEffects = new ArrayList<>();
        this.wotActionToZones = new HashMap<>();
        this.wotStateToSvIndex = new HashMap<>();

        OntModel model = loader.load();

        // Build WoT state URI → state vector index map dynamically from ws:stateVecIndex triples
        // in wot-mappings.ttl (Bug 15: replaces hardcoded map entries).
        String svIdxQuery = PREFIXES +
            "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\n" +
            "SELECT ?stateType ?svIdx WHERE {\n" +
            "  ?comp ws:hasWoTStateSemanticType ?stateType ;\n" +
            "        ws:stateVecIndex           ?svIdx .\n" +
            "}";
        try (QueryExecution qe = QueryExecutionFactory.create(svIdxQuery, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                String stateType = qs.getLiteral("stateType").getString();
                int svIdx = qs.getLiteral("svIdx").getInt();
                wotStateToSvIndex.put(stateType, svIdx);
                LOGGER.fine("  wotStateToSvIndex: " + stateType + " -> " + svIdx);
            }
        } catch (Exception e) {
            LOGGER.severe("StereotypeReasoner: failed to build wotStateToSvIndex from ontology: "
                          + e.getMessage());
        }
        if (wotStateToSvIndex.isEmpty()) {
            LOGGER.warning("StereotypeReasoner: wotStateToSvIndex is empty! " +
                           "Ensure wot-mappings.ttl is loaded and contains ws:stateVecIndex triples.");
        }

        // Build state-vector layout (domainSizes[], zoneLevelIndices[], sunshineIndex)
        // from the slot registry triples (ws:stateVecIndex + ws:stateDomainSize +
        // ws:stateSlotRole [+ ws:zoneIndex]) in wot-mappings.ttl. This replaces the
        // hardcoded IDX_* constants and N_STATES so QLearner is data-driven.
        loadStateSlotRegistry(model);

        // Discover actuators and build action registry
        discoverActuators(model);

        // Discover cross-zone feeds
        discoverCrossZoneFeeds(model);

        model.close();

        // Initialise IV effectiveness tracking arrays
        ivTrialCount   = new int[numActions][4];
        ivSuccessCount = new int[numActions][4];

        LOGGER.info("StereotypeReasoner: " + numActions + " actions, "
                   + crossZoneEffects.size() + " cross-zone effects");
    }

    // -----------------------------------------------------------------------
    // Ontology discovery
    // -----------------------------------------------------------------------

    /**
     * Load the state-vector slot registry from wot-mappings.ttl. Each slot is
     * an entity carrying ws:stateVecIndex + ws:stateDomainSize + ws:stateSlotRole
     * triples (with optional ws:zoneIndex for zone_level slots). Populates
     * domainSizes[], zoneLevelIndices[], and sunshineIndex.
     *
     * Roles recognised:
     *   - "zone_level"        — illuminance rank slot for one zone
     *   - "boolean_actuator"  — boolean state slot for an actuator
     *   - "sunshine"          — daylight rank slot
     */
    private void loadStateSlotRegistry(OntModel model) {
        String slotQuery = PREFIXES +
            "SELECT ?slot ?svIdx ?dom ?role ?zoneIdx WHERE {\n" +
            "  ?slot ws:stateVecIndex   ?svIdx ;\n" +
            "        ws:stateDomainSize ?dom ;\n" +
            "        ws:stateSlotRole   ?role .\n" +
            "  OPTIONAL { ?slot ws:zoneIndex ?zoneIdx . }\n" +
            "}";
        // Collect rows first; we may see multiple slots at the same svIdx (e.g.
        // a zone-level slot and an actuator slot are at distinct indices, but the
        // map de-dupes by svIdx). Validate that domainSize is consistent.
        Map<Integer, Integer> svToDomain   = new HashMap<>();
        Map<Integer, String>  svToRole     = new HashMap<>();
        Map<Integer, Integer> zoneIdxToSv  = new java.util.TreeMap<>();
        int sunshineSv = -1;

        try (QueryExecution qe = QueryExecutionFactory.create(slotQuery, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                int svIdx = qs.getLiteral("svIdx").getInt();
                int dom   = qs.getLiteral("dom").getInt();
                String role = qs.getLiteral("role").getString();

                Integer prevDom = svToDomain.put(svIdx, dom);
                if (prevDom != null && prevDom != dom) {
                    LOGGER.warning("StereotypeReasoner: conflicting stateDomainSize at sv index "
                                   + svIdx + ": " + prevDom + " vs " + dom);
                }
                svToRole.putIfAbsent(svIdx, role);

                if ("zone_level".equals(role) && qs.contains("zoneIdx")) {
                    int zoneIdx1 = qs.getLiteral("zoneIdx").getInt();
                    zoneIdxToSv.put(zoneIdx1, svIdx);
                } else if ("sunshine".equals(role)) {
                    sunshineSv = svIdx;
                }
            }
        } catch (Exception e) {
            LOGGER.warning("StereotypeReasoner: failed to load state slot registry: " + e.getMessage()
                         + " — entering degraded mode (legacy 8-slot fallback).");
            this.degraded = true;
        }

        if (svToDomain.isEmpty()) {
            LOGGER.warning("StereotypeReasoner: state slot registry is empty! "
                         + "Falling back to legacy 8-slot layout [4,4,2,2,2,2,2,4].");
            this.degraded = true;
            domainSizes      = new int[]{4, 4, 2, 2, 2, 2, 2, 4};
            zoneLevelIndices = new int[]{0, 1};
            sunshineIndex    = 7;
            return;
        }

        // Determine state vector length: max sv index + 1
        int maxSv = -1;
        for (int sv : svToDomain.keySet()) if (sv > maxSv) maxSv = sv;
        int len = maxSv + 1;

        domainSizes = new int[len];
        // Default any missing slot to size 1 (single-value, no contribution)
        Arrays.fill(domainSizes, 1);
        for (Map.Entry<Integer, Integer> e : svToDomain.entrySet()) {
            domainSizes[e.getKey()] = e.getValue();
        }

        // Zone level indices in 0-based zone order
        zoneLevelIndices = new int[zoneIdxToSv.size()];
        int z0 = 0;
        for (Map.Entry<Integer, Integer> e : zoneIdxToSv.entrySet()) {
            // TreeMap key order = ascending zone index (1, 2, …)
            zoneLevelIndices[z0++] = e.getValue();
        }

        sunshineIndex = sunshineSv;

        LOGGER.info("StereotypeReasoner: state slot registry loaded — "
                  + "len=" + len + " domain=" + Arrays.toString(domainSizes)
                  + " zoneLevel=" + Arrays.toString(zoneLevelIndices)
                  + " sunshine=" + sunshineIndex);
    }

    /**
     * Run ACTUATOR_DISCOVERY_QUERY and build the action registry.
     * With elem:hasComponentAction, each SPARQL result row is already one action
     * (ON or OFF) — no manual splitting needed. Multi-zone actuators appear in
     * multiple rows (one per zone), merged by (wotActionType + actionValue) key.
     * Then append DO_NOTHING as the final action.
     */
    private void discoverActuators(OntModel model) {
        // Key: wotActionType + "|" + actionValue → ActionInfo
        Map<String, ActionInfo> actionMap = new java.util.LinkedHashMap<>();

        try (QueryExecution qe = QueryExecutionFactory.create(ACTUATOR_DISCOVERY_QUERY, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                String wotAction = qs.contains("wotActionType") ? qs.getLiteral("wotActionType").getString() : null;
                String wotState = qs.contains("wotStateType") ? qs.getLiteral("wotStateType").getString() : null;
                int zoneIdx = qs.getLiteral("zoneIdx").getInt() - 1; // convert to 0-based
                boolean actionValue = qs.getLiteral("actionValue").getBoolean();
                boolean hasIV = qs.contains("iv") && qs.get("iv") != null;
                int ivMinRank = (qs.contains("ivMinRank") && qs.get("ivMinRank") != null)
                        ? qs.getLiteral("ivMinRank").getInt()
                        : 1; // KG-9 default per Audit Step 1

                if (wotAction == null) continue;

                String key = wotAction + "|" + actionValue;
                ActionInfo ai = actionMap.get(key);
                if (ai == null) {
                    ai = new ActionInfo();
                    ai.wotActionType = wotAction;
                    ai.wotValue = actionValue;
                    ai.wotStateType = wotState;
                    ai.hasIV = actionValue && hasIV; // IV only matters for activation
                    ai.ivStateVecIndex = (actionValue && hasIV) ? sunshineIndex : -1;
                    ai.ivMinRank = (actionValue && hasIV) ? ivMinRank : 1;
                    ai.expectedBitValue = actionValue ? 1 : 0;
                    String fragment = wotAction.substring(wotAction.lastIndexOf('#') + 1);
                    ai.label = fragment + "=" + (actionValue ? "ON" : "OFF");
                    actionMap.put(key, ai);
                }
                ai.affectedZones.add(zoneIdx);

                LOGGER.fine("  Discovered: " + wotAction + " value=" + actionValue
                          + " zone=" + zoneIdx + " hasIV=" + hasIV
                          + " ivMinRank=" + ivMinRank);
            }
        }

        // Also track zones per wotAction for cross-zone lookup
        for (ActionInfo ai : actionMap.values()) {
            Set<Integer> zones = wotActionToZones.computeIfAbsent(ai.wotActionType, k -> new HashSet<>());
            zones.addAll(ai.affectedZones);
        }

        // Assign sequential action indices and resolve state vector bit indices
        List<ActionInfo> actionList = new ArrayList<>();
        int idx = 0;
        for (ActionInfo ai : actionMap.values()) {
            ai.actionIndex = idx++;
            Integer svBitIdx = (ai.wotStateType != null) ? wotStateToSvIndex.get(ai.wotStateType) : null;
            ai.stateVecBitIndex = (svBitIdx != null) ? svBitIdx : -1;
            actionList.add(ai);
        }

        // DO_NOTHING as final action
        ActionInfo doNothing = new ActionInfo();
        doNothing.actionIndex = idx;
        doNothing.wotActionType = null;
        doNothing.wotValue = false;
        doNothing.wotStateType = null;
        doNothing.stateVecBitIndex = -1;
        doNothing.expectedBitValue = -1;
        doNothing.affectedZones = new HashSet<>();
        doNothing.hasIV = false;
        doNothing.ivStateVecIndex = -1;
        doNothing.label = "DO_NOTHING";
        actionList.add(doNothing);

        this.numActions = actionList.size();
        this.actions = actionList.toArray(new ActionInfo[0]);

        LOGGER.info("StereotypeReasoner: built " + numActions + " actions from "
                   + actionMap.size() + " component-actions");
        for (ActionInfo ai : actions) {
            LOGGER.info("  Action " + ai.actionIndex + ": " + ai.label
                      + " zones=" + ai.affectedZones
                      + " svBit=" + ai.stateVecBitIndex + " hasIV=" + ai.hasIV);
        }

        // S2-1 (audit Step 2): fail loud if SPARQL discovery yielded zero
        // actuator actions (numActions==1 means only the implicit DO_NOTHING
        // exists). Previously this silently produced a degenerate policy where
        // the agent could only no-op for the entire training run. The TTL is
        // almost certainly missing ws:hasWoTActionSemanticType /
        // elem:hasComponentAction / ws:actionValue triples.
        if (numActions <= 1) {
            throw new IllegalStateException(
                "StereotypeReasoner.discoverActuators: 0 actuator actions found in ontology."
              + " Check ws:hasWoTActionSemanticType / elem:hasComponentAction / ws:actionValue"
              + " triples in the lab + wot-mappings TTL files.");
        }
    }

    /**
     * Run CROSS_ZONE_FEEDS_QUERY to find light spill arcs.
     * Maps each cross-zone feed to the corresponding ON action index.
     */
    private void discoverCrossZoneFeeds(OntModel model) {
        try (QueryExecution qe = QueryExecutionFactory.create(CROSS_ZONE_FEEDS_QUERY, model)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution qs = rs.next();
                int sourceZone = qs.getLiteral("sourceZoneIdx").getInt() - 1;
                int targetZone = qs.getLiteral("targetZoneIdx").getInt() - 1;
                String wotAction = qs.getLiteral("wotActionType").getString();

                // Find the ON action for this wotActionType
                for (ActionInfo ai : actions) {
                    if (wotAction.equals(ai.wotActionType) && ai.wotValue) {
                        CrossZoneEffect cz = new CrossZoneEffect();
                        cz.actionIndex = ai.actionIndex;
                        cz.sourceZoneIdx = sourceZone;
                        cz.targetZoneIdx = targetZone;
                        // Avoid duplicates
                        boolean exists = false;
                        for (CrossZoneEffect existing : crossZoneEffects) {
                            if (existing.actionIndex == cz.actionIndex
                                && existing.sourceZoneIdx == cz.sourceZoneIdx
                                && existing.targetZoneIdx == cz.targetZoneIdx) {
                                exists = true;
                                break;
                            }
                        }
                        if (!exists) {
                            crossZoneEffects.add(cz);
                            LOGGER.info("  Cross-zone: action " + ai.label
                                      + " zone" + sourceZone + "→zone" + targetZone);
                        }
                        break;
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------

    /** Expose the WoT state URI → state vector index mapping. */
    public Map<String, Integer> getWotStateToSvIndexMap() {
        return wotStateToSvIndex;
    }

    /**
     * State-vector layout: domain cardinality of each slot, indexed by
     * state-vector position. Length = state vector length.
     */
    public int[] getStateDomainSizes() {
        return domainSizes;
    }

    /** Length of the state vector (== domainSizes.length). */
    public int getStateVecLength() {
        return domainSizes != null ? domainSizes.length : 0;
    }

    /**
     * Mapping from 0-based zone index to its illuminance-level slot in the
     * state vector. Length = number of zones.
     */
    public int[] getZoneLevelIndices() {
        return zoneLevelIndices;
    }

    /** State-vector index of the sunshine slot, or -1 if absent. */
    public int getSunshineIndex() {
        return sunshineIndex;
    }

    /** Total number of actions (dynamically discovered from ontology + DO_NOTHING). */
    public int getNumActions() {
        return numActions;
    }

    /**
     * True when the state-slot registry could not be loaded from the ontology
     * and the reasoner is operating on the legacy 8-slot fallback layout.
     * Callers (e.g. {@code QLearner.configureQLearner}) should warn the user
     * because stereotype-guided init may no longer match the simulator topology.
     */
    public boolean isDegraded() {
        return degraded;
    }

    /** Get action metadata by index. */
    public ActionInfo getActionInfo(int actionIdx) {
        return actions[actionIdx];
    }

    /** Get all action infos (for building WoT arrays etc.). */
    public ActionInfo[] getAllActions() {
        return actions;
    }

    /** Get cross-zone effects list. */
    public List<CrossZoneEffect> getCrossZoneEffects() {
        return crossZoneEffects;
    }

    /**
     * Per-slot ontology prediction for the change a given action SHOULD cause
     * to the state vector, assuming nominal physics declared in the ontology.
     *
     * The returned array has the same length as the state vector. Each entry
     * is one of {-1, 0, +1} and represents a *direction* of change:
     *   • At slot {@code ai.stateVecBitIndex}: the difference
     *     {@code expectedBitValue - currentBit} (so an OFF→ON action toggles
     *     the actuator slot by +1, ON→OFF by -1, and a redundant action by 0).
     *   • At each {@code zoneLevelIndices[z]} for z in {@code ai.affectedZones}:
     *     +1 when the action activates an illuminance source ({@code wotValue}
     *     true), -1 when deactivating, 0 otherwise.
     *   • At each cross-zone target's level slot: same direction as the
     *     primary effect (cross-zone spills are co-signed with activation).
     *   • All other slots: 0 (ontology declares no effect).
     *
     * This is INTENTIONALLY directional only — magnitudes are simulator-side
     * physics and are not declared in the TD/ontology. The bench agent
     * compares this prediction to the observed Δ in order to fingerprint
     * the per-lab weakness (W1..W6).
     */
    public int[] getActionPrediction(int[] stateVec, int actionIdx) {
        int[] pred = new int[stateVec.length];
        if (actionIdx < 0 || actionIdx >= numActions) return pred;
        ActionInfo ai = actions[actionIdx];
        if (ai.stateVecBitIndex < 0) return pred;            // DO_NOTHING

        // 1. Actuator state-bit delta.
        int curr = stateVec[ai.stateVecBitIndex];
        pred[ai.stateVecBitIndex] = ai.expectedBitValue - curr;

        // 2. Direction of illuminance change at primary zones.
        int dir = ai.wotValue ? +1 : -1;
        for (Integer z : ai.affectedZones) {
            if (z != null && z >= 0 && z < zoneLevelIndices.length) {
                int slot = zoneLevelIndices[z];
                if (slot >= 0 && slot < pred.length) pred[slot] += dir;
            }
        }

        // 3. Cross-zone spills.
        for (CrossZoneEffect cz : crossZoneEffects) {
            if (cz.actionIndex == actionIdx
                    && cz.targetZoneIdx >= 0
                    && cz.targetZoneIdx < zoneLevelIndices.length) {
                int slot = zoneLevelIndices[cz.targetZoneIdx];
                if (slot >= 0 && slot < pred.length) pred[slot] += dir;
            }
        }
        return pred;
    }

    /**
     * Is the given action a no-op in the current state?
     * (actuator already in target position)
     */
    public boolean isRedundant(int[] stateVec, int actionIdx) {
        ActionInfo ai = actions[actionIdx];
        if (ai.stateVecBitIndex < 0) return false; // DO_NOTHING is never redundant
        return stateVec[ai.stateVecBitIndex] == ai.expectedBitValue;
    }

    /**
     * Does the independent variable meet the minimum rank for this action?
     *
     * Audit Step 1 finding KG-2 ("Mediates declared but discarded"): the
     * consumer must derive the per-state sign of a Mediates mechanism from
     * the current IV rank, NOT from an unconditional elem:increases triple.
     *
     * Design choice (Option B): the run-time action mask uses ONLY the
     * learned IV-effectiveness statistics. The static {@code ws:ivMinRank}
     * triple is still loaded into {@code ai.ivMinRank} and consumed by
     * {@link #getInitPenaltyForZone(int[], int, int, int[])} as the cold-start
     * Q-init prior, but it does NOT gate the mask here. This makes the static
     * triple a falsifiable hypothesis: the agent is free to explore at every
     * IV rank and {@link #getLearnedIVMinRank(int)} is therefore measured
     * end-to-end from observation, not pre-decided by the ontology.
     */
    public boolean isIVSatisfied(int[] stateVec, int actionIdx) {
        ActionInfo ai = actions[actionIdx];
        if (!ai.hasIV || ai.ivStateVecIndex < 0) return true;
        int ivRank = stateVec[ai.ivStateVecIndex];

        // Check learned effectiveness at this specific IV rank
        if (ivTrialCount[actionIdx][ivRank] >= IV_MIN_SAMPLES) {
            double effectiveness = (double) ivSuccessCount[actionIdx][ivRank]
                                 / ivTrialCount[actionIdx][ivRank];
            return effectiveness >= IV_EFFECTIVENESS_THRESHOLD;
        }
        // Not enough learned data yet — allow exploration so the agent can
        // collect samples at every IV rank and the learned threshold can
        // converge without being seeded by the static prior.
        return true;
    }

    /**
     * Record the outcome of an action for IV effectiveness learning.
     * Called after every Q-learning step. Only tracks actions whose mechanism
     * depends on an independent variable (e.g. blinds depend on sunshine).
     *
     * @param actionIdx  the action that was taken
     * @param prevState  state vector BEFORE the action (int[8])
     * @param nextState  state vector AFTER the action (int[8])
     */
    public void recordActionOutcome(int actionIdx, int[] prevState, int[] nextState) {
        ActionInfo ai = actions[actionIdx];
        if (!ai.hasIV || ai.ivStateVecIndex < 0) return;
        if (!ai.wotValue) return; // Only track activation actions (ON/OPEN)

        int ivRank = prevState[ai.ivStateVecIndex];
        if (ivRank < 0 || ivRank > 3) return;

        ivTrialCount[actionIdx][ivRank]++;

        // Check if any affected zone's level increased
        for (int zoneIdx : ai.affectedZones) {
            int levelIdx = zoneLevelIndices[zoneIdx];
            if (nextState[levelIdx] > prevState[levelIdx]) {
                ivSuccessCount[actionIdx][ivRank]++;
                break;
            }
        }

        // Log learning progress periodically
        int total = ivTrialCount[actionIdx][ivRank];
        if (total == IV_MIN_SAMPLES || total == 50 || total == 100) {
            double eff = (double) ivSuccessCount[actionIdx][ivRank] / total;
            LOGGER.info("IV learning [" + ai.label + " @ ivRank=" + ivRank + "]: "
                      + ivSuccessCount[actionIdx][ivRank] + "/" + total
                      + " effective (" + String.format("%.1f%%", eff * 100) + ")"
                      + (total >= IV_MIN_SAMPLES
                         ? " → mask=" + (eff < IV_EFFECTIVENESS_THRESHOLD)
                         : " (still exploring)"));
        }
    }

    /**
     * Get the currently learned IV minimum rank for a given action.
     * Scans upward from rank 0; returns the first rank where effectiveness
     * exceeds the threshold, or 0 if no data yet.
     *
     * Diagnostic only — not invoked by QLearner during action selection.
     * Read by {@link #saveIVStats} and trace plumbing so post-hoc analysis
     * can compare ontology-declared ws:ivMinRank against the empirical value.
     */
    public int getLearnedIVMinRank(int actionIdx) {
        ActionInfo ai = actions[actionIdx];
        if (!ai.hasIV) return 0;
        for (int rank = 0; rank <= 3; rank++) {
            if (ivTrialCount[actionIdx][rank] >= IV_MIN_SAMPLES) {
                double eff = (double) ivSuccessCount[actionIdx][rank]
                           / ivTrialCount[actionIdx][rank];
                if (eff >= IV_EFFECTIVENESS_THRESHOLD) {
                    return rank;
                }
            } else {
                return rank; // Not enough data at this rank — optimistic
            }
        }
        return 4; // Never effective (action always masked)
    }

    /**
     * Get all valid actions for the current state (runtime action masking).
     * Filters out: redundant actions, IV-unsatisfied activation actions.
     * DO_NOTHING is always applicable.
     *
     * Used in mask_strict mode (ablation) and for initialisation.
     */
    public int[] getApplicableActions(int[] stateVec) {
        List<Integer> applicable = new ArrayList<>();
        for (int i = 0; i < numActions; i++) {
            ActionInfo ai = actions[i];
            // DO_NOTHING always applicable
            if (ai.wotActionType == null) {
                applicable.add(i);
                continue;
            }
            // Skip redundant (already in target state)
            if (isRedundant(stateVec, i)) continue;
            // Skip IV-unsatisfied activation
            if (ai.wotValue && !isIVSatisfied(stateVec, i)) continue;
            applicable.add(i);
        }
        return applicable.stream().mapToInt(Integer::intValue).toArray();
    }

    /**
     * Compute soft action priors for the current state.
     * Returns an additive bias (double[numActions]) that is added to Q-values
     * during greedy action selection.  Values:
     *   0.0   — action is neutral (allowed or DO_NOTHING)
     *  -5.0   — soft-discouraged: redundant action (actuator already in target state)
     * -25.0   — soft-discouraged: activation action whose IV is not satisfied
     *
     * Unlike hard masking, all actions remain reachable during exploration.
     * The priors only influence the greedy (exploitation) path.
     */
    public double[] getActionPriors(int[] stateVec) {
        double[] priors = new double[numActions];
        for (int i = 0; i < numActions; i++) {
            ActionInfo ai = actions[i];
            if (ai.wotActionType == null) {
                priors[i] = 0.0; // DO_NOTHING: neutral
                continue;
            }
            // S2-2 (audit Step 2): the two branches are mutually exclusive by
            // construction — a redundant action's actuator is already in the
            // target state, so the IV-unsatisfied check on the same action
            // would never fire. The if/else-if ordering is therefore safe and
            // intentional (redundancy wins over IV gating).
            if (isRedundant(stateVec, i)) {
                priors[i] = -PRIOR_REDUNDANT_MAG; // soft-discouraged: redundant
            } else if (ai.wotValue && !isIVSatisfied(stateVec, i)) {
                priors[i] = -PRIOR_IV_UNSAT_MAG;  // soft-discouraged: IV not satisfied
            } else {
                priors[i] = 0.0;
            }
        }
        return priors;
    }

    /**
     * Compute Q-table initialization penalty for a specific zone's decomposed table.
     *
     * Rules derived from ontology:
     *   1. Redundancy (hard -100): action targets bit already in target state
     *   2. IV gate (Mediates): state-dependent -100 when stateVec[IV] < ai.ivMinRank
     *      (Audit Step 1 KG-2 — derive the sign of a Mediates mechanism from
     *      the current IV rank, not from an unconditional Causes shortcut).
     *   3. Cross-zone overshoot: if zone k is at/above goal and action spills to k
     *   4. Shared actuator conflict: multi-zone actuator ON when zone already at/above goal
     *
     * @param stateVec  decoded state vector (8 elements)
     * @param actionIdx action index
     * @param zoneIdx   0-based zone index for this Q-table
     * @param goal      [Z1TargetRank, Z2TargetRank]
     */
    public double getInitPenaltyForZone(int[] stateVec, int actionIdx, int zoneIdx, int[] goal) {
        ActionInfo ai = actions[actionIdx];
        double penalty = 0.0;

        // Rule 1: Redundancy — hard penalty (action is a no-op)
        if (ai.stateVecBitIndex >= 0) {
            if (stateVec[ai.stateVecBitIndex] == ai.expectedBitValue) {
                return -100.0 * INIT_PENALTY_SCALE; // Absolute worst — wasted action
            }
        }

        // Rule 2: IV gate (Mediates) — state-dependent hard penalty.
        // Only fires for activation actions whose mechanism has an IV AND whose
        // current IV rank is below the declared Mediates threshold (ws:ivMinRank).
        // When the IV is sufficient, the penalty is zero — the action is then
        // physically capable of changing the DV, exactly as Ramanathan & Mayer
        // §3.2 prescribes for a Mediates mechanism.
        if (ai.hasIV && ai.wotValue && ai.ivStateVecIndex >= 0) {
            int ivRank = stateVec[ai.ivStateVecIndex];
            if (ivRank < ai.ivMinRank) {
                penalty += -100.0;
            }
        }

        // Rule 3: Cross-zone overshoot penalty.
        // Note (audit Step 2): on custom8 the crossZoneEffects set is empty
        // because the lab TTL declares no brick:feeds arcs between zones —
        // each luminaire is single-zone. This rule is therefore dead-on for
        // custom8 but kept for labs where shared luminaires exist (custom2/3).
        for (CrossZoneEffect cz : crossZoneEffects) {
            if (cz.actionIndex == actionIdx && cz.targetZoneIdx == zoneIdx) {
                // This action spills into our zone from another zone
                int zoneLevelIdx = zoneLevelIndices[zoneIdx];
                if (stateVec[zoneLevelIdx] >= goal[zoneIdx]) {
                    // Zone already at or above goal — spill would overshoot
                    penalty += -50.0;
                }
            }
        }

        // Rule 4: Shared actuator at-goal penalty (e.g. Spotlight affects both zones)
        if (ai.affectedZones.size() > 1 && ai.wotValue) {
            int zoneLevelIdx = zoneLevelIndices[zoneIdx];
            if (stateVec[zoneLevelIdx] >= goal[zoneIdx]) {
                penalty += -75.0; // Strong discouragement when zone is already at goal
            }
        }

        // S2-5 (audit Step 2): apply global softening scale. The raw magnitudes
        // above are kept for clarity; INIT_PENALTY_SCALE (default 0.5) divides
        // all penalty wells so the per-zone Bellman target ±12.5 can reasonably
        // overcome them within the custom8 training budget.
        return penalty * INIT_PENALTY_SCALE;
    }

    // -----------------------------------------------------------------------
    // IV statistics persistence
    // -----------------------------------------------------------------------

    /**
     * Save ivTrialCount and ivSuccessCount to a simple CSV-based JSON file.
     * Format: two sections separated by a header comment line, each containing
     * numActions rows of 4 comma-separated integer values.
     *
     * @param filename  Destination file path.
     */
    public void saveIVStats(String filename) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("# IV Stats — ivTrialCount [numActions=" + numActions + "][4]");
            for (int a = 0; a < numActions; a++) {
                pw.println(ivTrialCount[a][0] + "," + ivTrialCount[a][1] + ","
                         + ivTrialCount[a][2] + "," + ivTrialCount[a][3]);
            }
            pw.println("# ivSuccessCount [numActions=" + numActions + "][4]");
            for (int a = 0; a < numActions; a++) {
                pw.println(ivSuccessCount[a][0] + "," + ivSuccessCount[a][1] + ","
                         + ivSuccessCount[a][2] + "," + ivSuccessCount[a][3]);
            }
            LOGGER.info("saveIVStats: written to " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveIVStats: failed to write " + filename + " — " + e.getMessage());
        }
    }

    /**
     * Load ivTrialCount and ivSuccessCount from a file written by saveIVStats().
     * If the file is missing or malformed the method logs a warning and returns
     * without modifying the arrays (allowing execution to proceed without stats).
     *
     * @param filename  Source file path.
     */
    public void loadIVStats(String filename) {
        try (BufferedReader br = new BufferedReader(new FileReader(filename))) {
            // Read ivTrialCount section
            String header1 = br.readLine(); // comment line
            if (header1 == null || !header1.startsWith("# IV Stats")) {
                LOGGER.warning("loadIVStats: unexpected format in " + filename + " — skipping");
                return;
            }
            for (int a = 0; a < numActions; a++) {
                String line = br.readLine();
                if (line == null) break;
                String[] parts = line.split(",");
                for (int r = 0; r < Math.min(4, parts.length); r++) {
                    ivTrialCount[a][r] = Integer.parseInt(parts[r].trim());
                }
            }
            // Read ivSuccessCount section
            String header2 = br.readLine(); // comment line
            if (header2 == null || !header2.startsWith("# ivSuccessCount")) {
                LOGGER.warning("loadIVStats: missing ivSuccessCount section in " + filename + " — trial counts loaded only");
                return;
            }
            for (int a = 0; a < numActions; a++) {
                String line = br.readLine();
                if (line == null) break;
                String[] parts = line.split(",");
                for (int r = 0; r < Math.min(4, parts.length); r++) {
                    ivSuccessCount[a][r] = Integer.parseInt(parts[r].trim());
                }
            }
            LOGGER.info("loadIVStats: loaded from " + filename);
        } catch (IOException | NumberFormatException e) {
            LOGGER.warning("loadIVStats: failed to load " + filename + " — " + e.getMessage() + " — IV stats will be empty");
        }
    }
}
