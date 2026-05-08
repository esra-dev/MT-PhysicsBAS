package tools;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

import org.apache.jena.ontology.OntModel;
import org.apache.jena.ontology.OntModelSpec;
import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.QuerySolution;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.RDFNode;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;

/**
 * OntologyArtifact — CArtAgO artifact that exposes SPARQL-based reasoning
 * over a combined BRICK + Elementary Ontology knowledge graph to Jason agents.
 *
 * Implements the approach from:
 *   Cecconi et al., "Reasoning about Physical Processes in Buildings
 *   through Component Stereotypes", CPS-IoT Week 2023.
 *
 * Design goals:
 *   - All component discovery is fully dynamic: no component names, zone names,
 *     or action types are hardcoded in Java or in the agent.
 *   - discoverZones()        → returns all lab:Workstation URIs + ws:zoneIndex values.
 *   - discoverZoneQuantity() → finds the quantity (DV) that actuators in a zone
 *                              influence and that the zone's light sensor measures.
 *                              The agent's goal is named after this quantity label.
 *   - queryBestIncreaseAction() / queryBestDecreaseAction()
 *                            → filter by zone URI + target DV URI; return the WoT
 *                              action URI directly from the ontology so the agent
 *                              dispatches without any if-elif chain.
 */
public class OntologyArtifact extends Artifact {

    private static final Logger LOGGER =
            Logger.getLogger(OntologyArtifact.class.getName());

    // ----------------------------------------------------------------
    // SPARQL prefix block
    // ----------------------------------------------------------------

    private static final String PREFIXES =
            "PREFIX owl:   <http://www.w3.org/2002/07/owl#> " +
            "PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " +
            "PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#> " +
            "PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#> " +
            "PREFIX brick: <https://brickschema.org/schema/Brick#> " +
            "PREFIX elem:  <http://w3id.org/elementary#> " +
            "PREFIX ws:    <http://example.org/was/lab/stereotypes#> " +
            "PREFIX lab:   <http://example.org/was/lab#> ";

    /** Base namespace for lab instances. */
    private static final String LAB_NS = "http://example.org/was/lab#";

    // ----------------------------------------------------------------
    // SPARQL queries
    // ----------------------------------------------------------------

    /**
     * Discovers all lab:Workstation instances, their ws:zoneIndex ordinals, and
     * their ws:targetIlluminanceRank. Results are ordered by zone index so
     * positional pairing across returned arrays is deterministic.
     */
    private static final String DISCOVER_ZONES_QUERY =
            PREFIXES +
            "SELECT ?zone ?idx " +
            "WHERE { " +
            "  ?zone a lab:Workstation . " +
            "  ?zone ws:zoneIndex ?idx . " +
            "} ORDER BY ?idx";

    /**
     * For a given zone URI (%s), finds the observable quantity (process variable)
     * that the zone's light sensors use as their independent variable (what they
     * sense) AND that at least one actuatable mechanism produces as its dependent
     * variable. This shared variable is the semantic bridge between goal and sensor.
     */
    private static final String DISCOVER_ZONE_QUANTITY_QUERY =
            PREFIXES +
            "SELECT ?quantityURI ?quantityLabel " +
            "WHERE { " +
            "  ?sensor  brick:isLocatedIn    <%s> . " +
            "  ?sensor  elem:hasBehavioralStereotype   ?sensorStereo . " +
            "  ?sensorStereo elem:hasPhysicalMechanism ?sensMech . " +
            "  ?sensMech elem:hasIndependentVariable   ?quantityURI . " +
            "  ?quantityURI  rdfs:label                ?quantityLabel . " +
            "  ?actMech elem:hasDependentVariable   ?quantityURI . " +
            "  ?actMech elem:hasManipulatedVariable ?anyMv . " +
            // Restrict to illuminance quantities so that temperature sensors
            // introduced alongside radiators do not interfere with zone discovery.
            // elem:luminiscence already declares elem:hasQuantity qudtqk:Illuminance
            // in the ontology — no new properties required.
            "  FILTER EXISTS { ?quantityURI elem:hasQuantity <http://qudt.org/vocab/quantitykind/Illuminance> } " +
            "} LIMIT 1";

    /**
     * Finds all actuatable components in zone (%1$s) whose mechanism produces
     * the target DV URI (%2$s). Returns per-candidate:
     *   ?comp, ?mechanism, ?mvLabel, ?dvLabel, ?ivLabel (OPTIONAL),
     *   ?wotActionType (from ws:hasWoTActionSemanticType),
     *   ?actuatorKind  (from ws:actuatorStateKind on the stereotype).
     */
    private static final String ZONE_COMPONENTS_QUERY =
            PREFIXES +
            "SELECT ?comp ?mechanism ?mvLabel ?dvLabel ?ivLabel ?wotActionType ?wotStateType " +
            "WHERE { " +
            "  ?comp  brick:isLocatedIn          <%1$s> . " +
            "  ?comp  elem:hasBehavioralStereotype ?stereo . " +
            "  ?stereo elem:hasPhysicalMechanism  ?mech . " +
            "  ?mech  rdfs:label                 ?mechanism . " +
            "  ?mech  elem:hasManipulatedVariable ?mv . " +
            "  ?mv    rdfs:label                  ?mvLabel . " +
            "  ?mech  elem:hasDependentVariable   <%2$s> . " +
            "  <%2$s> rdfs:label                  ?dvLabel . " +
            "  OPTIONAL { " +
            "    ?mech elem:hasIndependentVariable ?iv . " +
            "    ?iv   rdfs:label                 ?ivLabel . " +
            "  } " +
            "  OPTIONAL { ?comp ws:hasWoTActionSemanticType ?wotActionType . } " +
            "  OPTIONAL { ?comp ws:hasWoTStateSemanticType  ?wotStateType . } " +
            "} ORDER BY (IF(BOUND(?iv), 1, 0)) ?comp";

    /**
     * For a given process variable URI (%s), fetches the three rank boundary values
     * stored as ws:rankBound_1, ws:rankBound_2, ws:rankBound_3.
     */
    private static final String DISCRETIZATION_BOUNDS_QUERY =
            PREFIXES +
            "SELECT ?b1 ?b2 ?b3 " +
            "WHERE { <%s> ws:rankBound_1 ?b1 ; ws:rankBound_2 ?b2 ; ws:rankBound_3 ?b3 . }";

    private OntModel ontModel;

    /**
     * Cache for {@link #queryZoneComponents}: the (zoneUri, dvUri) → candidate
     * row list mapping is stable for the lifetime of the loaded ontology, so
     * memoising avoids re-running the (relatively expensive) DL-rule-inferred
     * SELECT on every benchmark step. Cache is invalidated whenever the
     * ontology model is mutated (see {@link #invalidateComponentCache}).
     */
    private final Map<String, List<Map<String, String>>> componentCache =
            new ConcurrentHashMap<>();

    // ----------------------------------------------------------------
    // CArtAgO operations
    // ----------------------------------------------------------------

    /**
     * Load one or more RDF/Turtle ontology files from the Java classpath.
     *
     * @param ttlResourcePaths  Classpath resource names, e.g. "lab-ontology.ttl", "wot-mappings.ttl".
     */
    @OPERATION
    public void init(Object[] ttlResourcePaths) {
        ontModel = ModelFactory.createOntologyModel(OntModelSpec.OWL_MEM_MICRO_RULE_INF);
        for (Object pathObj : ttlResourcePaths) {
            String path = pathObj.toString();
            InputStream in = getClass().getClassLoader().getResourceAsStream(path);
            if (in != null) {
                ontModel.read(in, null, "TURTLE");
                LOGGER.info("OntologyArtifact: loaded '" + path +
                            "'. Triples: " + ontModel.size());
            } else {
                LOGGER.severe("OntologyArtifact: resource NOT found: '" + path + "'.");
            }
        }
    }

    /**
     * Merge a Turtle file from the local filesystem into the live ontology
     * model.  Used by the stereotype-feedback loop: a previous training run
     * writes <code>learned_stereotypes_*.ttl</code> via
     * {@link tools.StereotypeLearner#saveLearnedStereotypes(String)}, and a
     * subsequent run imports those triples here so SPARQL queries (and the
     * downstream agent reasoning) can see the discovered effects.
     *
     * <p>The file is loaded as plain RDF triples; no schema validation is
     * performed — the Turtle is expected to use the
     * <code>learned:</code> / <code>elem:</code> vocabularies emitted by the
     * StereotypeLearner.  After merging, the SPARQL component cache is
     * invalidated so the next zone-component lookup re-derives candidates
     * with the new triples in scope.
     *
     * @param ttlPath  Filesystem path to the Turtle file to merge. If the
     *                 file does not exist the operation is a no-op (count=0)
     *                 and a warning is logged — this lets the agent call the
     *                 operation unconditionally on startup.
     * @param count    Output: number of new triples merged (or 0 on miss).
     */
    @OPERATION
    public void importLearnedStereotypes(String ttlPath,
                                         OpFeedbackParam<Integer> count) {
        if (ontModel == null) {
            LOGGER.warning("importLearnedStereotypes: ontology not initialised — skipping");
            count.set(0);
            return;
        }
        java.io.File f = new java.io.File(ttlPath);
        if (!f.exists() || !f.isFile()) {
            LOGGER.info("importLearnedStereotypes: '" + ttlPath
                      + "' not found — feedback loop inactive (first run)");
            count.set(0);
            return;
        }
        long sizeBefore = ontModel.size();
        try (java.io.InputStream in = new java.io.FileInputStream(f)) {
            ontModel.read(in, null, "TURTLE");
        } catch (java.io.IOException e) {
            LOGGER.warning("importLearnedStereotypes: failed to read '"
                         + ttlPath + "' — " + e.getMessage());
            count.set(0);
            return;
        }
        long added = ontModel.size() - sizeBefore;
        LOGGER.info("importLearnedStereotypes: merged " + added
                  + " triple(s) from '" + ttlPath + "'");
        invalidateComponentCache();
        count.set((int) added);
    }

    // ----------------------------------------------------------------
    // Zone / goal discovery operations
    // ----------------------------------------------------------------

    /**
     * Discover all workstation zones from the ontology.
     *
     * Returns two parallel arrays (same length, same index = same zone):
     *   zoneURIs    — full URI strings (e.g. "http://example.org/was/lab#Zone1")
     *   zoneIndices — ws:zoneIndex integer values
     *
     * Control targets are held as zone_target/2 beliefs in the agent.
     *
     * @param zoneURIs    Output: zone URI strings ordered by ws:zoneIndex.
     * @param zoneIndices Output: zone index integers matching zoneURIs order.
     */
    @OPERATION
    public void discoverZones(
            OpFeedbackParam<Object[]> zoneURIs,
            OpFeedbackParam<Object[]> zoneIndices) {

        LOGGER.info("discoverZones: querying ontology");
        List<String>  uris = new ArrayList<>();
        List<Integer> idxs = new ArrayList<>();

        Query q = QueryFactory.create(DISCOVER_ZONES_QUERY);
        try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution sol = rs.nextSolution();
                uris.add(sol.getResource("zone").getURI());
                idxs.add(sol.getLiteral("idx").getInt());
            }
        } catch (Exception e) {
            LOGGER.severe("discoverZones SPARQL failed: " + e.getMessage());
        }

        zoneURIs.set(uris.toArray());
        zoneIndices.set(idxs.toArray());
        LOGGER.info("discoverZones: found " + uris.size() + " zone(s): " + uris);
    }

    /**
     * Fetch the three discretisation rank boundaries for a process variable.
     * Reads ws:rankBound_1/2/3 from the ontology; falls back to {50, 100, 300}
     * with a warning if the triples are absent.
     *
     * @param pvUri  Full URI of the process variable.
     * @param bounds Output: Double[3] containing [rankBound_1, rankBound_2, rankBound_3].
     */
    @OPERATION
    public void getDiscretizationBounds(String pvUri,
            OpFeedbackParam<Object[]> bounds) {

        LOGGER.info("getDiscretizationBounds: pv=" + pvUri);
        String sparql = String.format(DISCRETIZATION_BOUNDS_QUERY, pvUri);
        Query q = QueryFactory.create(sparql);

        try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
            ResultSet rs = qe.execSelect();
            if (rs.hasNext()) {
                QuerySolution sol = rs.nextSolution();
                bounds.set(new Object[]{
                        sol.getLiteral("b1").getDouble(),
                        sol.getLiteral("b2").getDouble(),
                        sol.getLiteral("b3").getDouble()
                });
                LOGGER.info("  bounds: " + bounds.get()[0] + ", " +
                            bounds.get()[1] + ", " + bounds.get()[2]);
                return;
            }
        } catch (Exception e) {
            LOGGER.severe("getDiscretizationBounds SPARQL failed: " + e.getMessage());
        }

        LOGGER.warning("getDiscretizationBounds: no rankBound triples for " + pvUri +
                       ". Using defaults {50, 100, 300}.");
        bounds.set(new Object[]{50.0, 100.0, 300.0});
    }

    /**
     * For a given zone URI, discover the observable quantity (process variable)
     * that light sensors in the zone measure and that actuators can influence.
     * The agent maps its goal name to the returned quantity label.
     *
     * @param zoneUri       Full URI of the zone.
     * @param quantityUri   Output: URI of the shared DV/IV process variable.
     * @param quantityLabel Output: rdfs:label of that variable.
     */
    @OPERATION
    public void discoverZoneQuantity(
            String zoneUri,
            OpFeedbackParam<String> quantityUri,
            OpFeedbackParam<String> quantityLabel) {

        LOGGER.info("discoverZoneQuantity: zone=" + zoneUri);
        String sparql = String.format(DISCOVER_ZONE_QUANTITY_QUERY, zoneUri);
        Query q = QueryFactory.create(sparql);

        try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
            ResultSet rs = qe.execSelect();
            if (rs.hasNext()) {
                QuerySolution sol = rs.nextSolution();
                String uri   = sol.getResource("quantityURI").getURI();
                String label = sol.getLiteral("quantityLabel").getString();
                quantityUri.set(uri);
                quantityLabel.set(label);
                LOGGER.info("  quantity: " + uri + " (\"" + label + "\")");
                return;
            }
        } catch (Exception e) {
            LOGGER.severe("discoverZoneQuantity SPARQL failed: " + e.getMessage());
        }

        quantityUri.set("none");
        quantityLabel.set("none");
        LOGGER.warning("discoverZoneQuantity: no actuatable quantity found for " + zoneUri);
    }

    // ----------------------------------------------------------------
    // Actuation decision operations
    // ----------------------------------------------------------------

    /**
     * Query the KG for the best component to INCREASE the target quantity in a zone.
     *
     * Algorithm:
     *   1. SPARQL SELECT: fetch actuatable components in zone that produce dvUri.
     *   2. Java filter — IV satisfaction: if the mechanism has an IV, require
     *      sunshineRank >= ws:ivMinRank stored on the mechanism (default 1 if absent).
     *   3. Java filter — current state: look up ws:hasWoTStateSemanticType in the
     *      stateMap built from the parallel stateKeys/stateValues arrays returned by
     *      LabEnvironment.readZoneState. Skip if already active.
     *   4. Return first passing candidate including the WoT action URI.
     *
     * @param zoneUri       Full URI of the zone.
     * @param dvUri         URI of the target process variable (from discoverZoneQuantity).
     * @param sunshineRank  Current sunshine rank (0–3).
     * @param stateKeys     WoT status property URIs (from readZoneState).
     * @param stateValues   Corresponding boolean values (parallel to stateKeys).
     * @param componentId   Output: local name of selected component, or "none".
     * @param mechanism     Output: mechanism rdfs:label.
     * @param mvLabel       Output: MV rdfs:label.
     * @param dvLabel       Output: DV rdfs:label.
     * @param ivLabel       Output: IV rdfs:label, or "none".
     * @param wotActionType Output: WoT TD action @type URI for generic dispatch.
     */
    @OPERATION
    public void queryBestIncreaseAction(
            String zoneUri, String dvUri,
            int sunshineRank, Object[] stateKeys, Object[] stateValues,
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel,
            OpFeedbackParam<String> wotActionType) {

        LOGGER.info("queryBestIncreaseAction: zone=" + zoneUri + " dv=" + dvUri +
                    " sunshine=" + sunshineRank);

        Map<String, Boolean> stateMap = buildStateMap(stateKeys, stateValues);
        List<Map<String, String>> candidates = queryZoneComponents(zoneUri, dvUri);

        for (Map<String, String> c : candidates) {
            String cId          = c.get("compId");
            String ivVal        = c.get("ivLabel");
            String wotStateType = c.get("wotStateType");

            // Filter 1: IV satisfaction — if the mechanism has an independent variable
            // (e.g. blinds require outdoor illuminance), require sunshineRank >= 1.
            // Opening a blind when there is no sunshine contributes 0 lux; skipping it
            // avoids wasting an action slot and prevents an infinite increase-loop.
            if (!"none".equals(ivVal) && sunshineRank < 1) {
                LOGGER.info("  Skipping " + cId + ": IV not satisfied (sunshine rank "
                            + sunshineRank + " < 1, iv='" + ivVal + "')");
                continue;
            }

            // Filter 2: Current state — can we increase?
            // Look up via ws:hasWoTStateSemanticType → no if-elif on component names
            Boolean isActive = stateMap.get(wotStateType);
            if (!Boolean.FALSE.equals(isActive)) {  // null = URI missing; true = already ON/UP
                LOGGER.info("  Skipping " + cId + ": already in activated state "
                            + "(wotStateType=" + wotStateType + " isActive=" + isActive + ")");
                continue;
            }

            setOutputs(componentId, mechanism, mvLabel, dvLabel, ivLabel, wotActionType, c);
            LOGGER.info("  Selected: " + cId + " wotAction=" + c.get("wotActionType"));
            return;
        }

        setNoResult(componentId, mechanism, mvLabel, dvLabel, ivLabel, wotActionType);
        LOGGER.info("  No actionable component found for increase in zone " + zoneUri);
    }

    /**
     * Query the KG for the best component to DECREASE the target quantity in a zone.
     *
     * Algorithm:
     *   1. SPARQL SELECT: same as increase query.
     *   2. Java filter — current state: skip if already deactivated.
     *      State is looked up via ws:hasWoTStateSemanticType in stateMap.
     *   3. Return first passing candidate.
     *
     * @param zoneUri       Full URI of the zone.
     * @param dvUri         URI of the target process variable.
     * @param sunshineRank  Current sunshine rank (logged only).
     * @param stateKeys     WoT status property URIs (from readZoneState).
     * @param stateValues   Corresponding boolean values (parallel to stateKeys).
     * @param componentId   Output: local name of selected component, or "none".
     * @param mechanism     Output: mechanism rdfs:label.
     * @param mvLabel       Output: MV rdfs:label.
     * @param dvLabel       Output: DV rdfs:label.
     * @param ivLabel       Output: IV rdfs:label, or "none".
     * @param wotActionType Output: WoT TD action @type URI for generic dispatch.
     */
    @OPERATION
    public void queryBestDecreaseAction(
            String zoneUri, String dvUri,
            int sunshineRank, Object[] stateKeys, Object[] stateValues,
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel,
            OpFeedbackParam<String> wotActionType) {

        LOGGER.info("queryBestDecreaseAction: zone=" + zoneUri + " dv=" + dvUri +
                    " sunshine=" + sunshineRank);

        Map<String, Boolean> stateMap = buildStateMap(stateKeys, stateValues);
        List<Map<String, String>> candidates = queryZoneComponents(zoneUri, dvUri);

        for (Map<String, String> c : candidates) {
            String cId          = c.get("compId");
            String wotStateType = c.get("wotStateType");

            Boolean isActive = stateMap.get(wotStateType);
            if (!Boolean.TRUE.equals(isActive)) {  // null = URI missing; false = already OFF/DOWN
                LOGGER.info("  Skipping " + cId + ": not in deactivatable state "
                            + "(wotStateType=" + wotStateType + " isActive=" + isActive + ")");
                continue;
            }

            setOutputs(componentId, mechanism, mvLabel, dvLabel, ivLabel, wotActionType, c);
            LOGGER.info("  Selected: " + cId + " wotAction=" + c.get("wotActionType"));
            return;
        }

        setNoResult(componentId, mechanism, mvLabel, dvLabel, ivLabel, wotActionType);
        LOGGER.info("  No actionable component found for decrease in zone " + zoneUri);
    }

    // ----------------------------------------------------------------
    // Private helpers
    // ----------------------------------------------------------------

    /**
     * Execute the zone-components SPARQL SELECT filtered by target DV URI.
     * Returns a list of property maps with keys:
     *   compId, mechanism, mvLabel, dvLabel, ivLabel,
     *   wotActionType, wotStateType, ivMinRank
     */
    private List<Map<String, String>> queryZoneComponents(String zoneUri, String dvUri) {
        String cacheKey = zoneUri + "|" + dvUri;
        List<Map<String, String>> cached = componentCache.get(cacheKey);
        if (cached != null) {
            LOGGER.fine("queryZoneComponents: cache hit for " + cacheKey
                       + " (" + cached.size() + " candidate(s))");
            return cached;
        }
        String sparql = String.format(ZONE_COMPONENTS_QUERY, zoneUri, dvUri);
        LOGGER.fine("SPARQL:\n" + sparql);

        List<Map<String, String>> results = new ArrayList<>();
        Query q = QueryFactory.create(sparql);

        try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution sol = rs.nextSolution();
                Map<String, String> row = new LinkedHashMap<>();

                row.put("compId",    sol.getResource("comp").getLocalName());
                row.put("mechanism", sol.getLiteral("mechanism").getString());
                row.put("mvLabel",   sol.getLiteral("mvLabel").getString());
                row.put("dvLabel",   sol.getLiteral("dvLabel").getString());

                RDFNode ivNode = sol.get("ivLabel");
                row.put("ivLabel", (ivNode != null && ivNode.isLiteral())
                        ? ivNode.asLiteral().getString() : "none");

                RDFNode wotActNode = sol.get("wotActionType");
                row.put("wotActionType", (wotActNode != null && wotActNode.isLiteral())
                        ? wotActNode.asLiteral().getString() : "none");

                RDFNode wotStNode = sol.get("wotStateType");
                row.put("wotStateType", (wotStNode != null && wotStNode.isLiteral())
                        ? wotStNode.asLiteral().getString() : null);

                results.add(row);
                LOGGER.fine("  row: " + row);
            }
        } catch (Exception e) {
            LOGGER.severe("SPARQL query failed for zone " + zoneUri + ": " + e.getMessage());
        }

        LOGGER.info("queryZoneComponents(" + zoneUri + "): " + results.size() + " candidate(s)");
        componentCache.put(cacheKey, results);
        return results;
    }

    /**
     * Invalidate the {@link #componentCache} after the underlying ontology
     * model has been mutated (e.g. by {@link #importLearnedStereotypes}).
     */
    private void invalidateComponentCache() {
        if (!componentCache.isEmpty()) {
            LOGGER.info("OntologyArtifact: invalidating component cache ("
                      + componentCache.size() + " entries)");
            componentCache.clear();
        }
    }

    /**
     * Build a Boolean lookup map from the parallel stateKeys / stateValues arrays
     * returned by LabEnvironment.readZoneState.
     * Key: WoT status property URI (e.g. "http://example.org/was#Z1Light")
     * Value: current boolean state (true = on/up, false = off/down)
     */
    private Map<String, Boolean> buildStateMap(Object[] keys, Object[] values) {
        Map<String, Boolean> map = new LinkedHashMap<>();
        int len = Math.min(keys.length, values.length);
        for (int i = 0; i < len; i++) {
            if (keys[i] instanceof String && values[i] instanceof Boolean) {
                map.put((String) keys[i], (Boolean) values[i]);
            }
        }
        return map;
    }

    private void setOutputs(
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel,
            OpFeedbackParam<String> wotActionType,
            Map<String, String> c) {
        componentId.set(c.get("compId"));
        mechanism.set(c.get("mechanism"));
        mvLabel.set(c.get("mvLabel"));
        dvLabel.set(c.get("dvLabel"));
        ivLabel.set(c.get("ivLabel"));
        wotActionType.set(c.get("wotActionType"));
    }

    private void setNoResult(
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel,
            OpFeedbackParam<String> wotActionType) {
        componentId.set("none");
        mechanism.set("none");
        mvLabel.set("none");
        dvLabel.set("none");
        ivLabel.set("none");
        wotActionType.set("none");
    }

    // ----------------------------------------------------------------
    // Cross-zone conflict resolution operations
    // ----------------------------------------------------------------

    /** SPARQL query template: find all zone indices for a given WoT action type. */
    private static final String SHARED_ACTUATOR_ZONES_QUERY =
            PREFIXES +
            "SELECT DISTINCT ?zoneIdx WHERE { " +
            "  ?comp ws:hasWoTActionSemanticType \"%s\" . " +
            "  ?comp brick:isLocatedIn ?zone . " +
            "  ?zone a lab:Workstation . " +
            "  ?zone ws:zoneIndex ?zoneIdx . " +
            "} ORDER BY ?zoneIdx";

    /**
     * Check whether activating a shared actuator is safe, i.e. it would not push
     * any non-requesting zone above its target illuminance level.
     *
     * @param wotActionType    WoT action URI of the candidate actuator.
     * @param requestingZoneIdx 1-based zone index requesting the activation.
     * @param zoneLevels       Current zone illuminance levels (ordered by zone index).
     * @param zoneTargets      Target illuminance ranks (ordered by zone index).
     * @param safe             Output: true if activation is safe (no overshoot).
     */
    @OPERATION
    public void checkSharedActuatorSafe(
            String wotActionType, int requestingZoneIdx,
            Object[] zoneLevels, Object[] zoneTargets,
            OpFeedbackParam<Boolean> safe) {

        LOGGER.info("checkSharedActuatorSafe: action=" + wotActionType
                   + " requestingZone=" + requestingZoneIdx);

        // Find all zones this actuator affects
        String sparql = String.format(SHARED_ACTUATOR_ZONES_QUERY, wotActionType);
        List<Integer> affectedZoneIdxs = new ArrayList<>();

        try {
            Query q = QueryFactory.create(sparql);
            try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
                ResultSet rs = qe.execSelect();
                while (rs.hasNext()) {
                    QuerySolution sol = rs.nextSolution();
                    affectedZoneIdxs.add(sol.getLiteral("zoneIdx").getInt());
                }
            }
        } catch (Exception e) {
            LOGGER.severe("checkSharedActuatorSafe SPARQL failed: " + e.getMessage());
            safe.set(true); // fail-open: allow action if query fails
            return;
        }

        // If actuator affects only one zone, it's always safe
        if (affectedZoneIdxs.size() <= 1) {
            LOGGER.info("  Single-zone actuator — safe.");
            safe.set(true);
            return;
        }

        // Check each non-requesting zone: if already at or above target, overshoot risk
        for (int zIdx : affectedZoneIdxs) {
            if (zIdx == requestingZoneIdx) continue;
            // zoneLevels and zoneTargets are ordered by zone index (0-based array position)
            int arrayIdx = zIdx - 1; // convert 1-based zone idx to 0-based array index
            if (arrayIdx >= 0 && arrayIdx < zoneLevels.length && arrayIdx < zoneTargets.length) {
                int level = toInt(zoneLevels[arrayIdx]);
                int target = toInt(zoneTargets[arrayIdx]);
                if (level >= target) {
                    LOGGER.info("  Zone " + zIdx + " at level=" + level
                              + " (target=" + target + ") — would overshoot. UNSAFE.");
                    safe.set(false);
                    return;
                }
            }
        }

        LOGGER.info("  All non-requesting zones below target — safe.");
        safe.set(true);
    }

    /**
     * Check whether deactivating a shared actuator is safe, i.e. no other zone that
     * depends on this actuator is currently below its target illuminance level.
     *
     * <p>Semantics are the inverse of {@link #checkSharedActuatorSafe}:
     * <ul>
     *   <li>Single-zone actuator: always safe to deactivate ({@code safe=true}).</li>
     *   <li>Multi-zone, ALL non-requesting zones below target: unsafe — they still need
     *       the actuator ({@code safe=false}).</li>
     *   <li>Multi-zone, SOME non-requesting zone at/above target: safe to deactivate
     *       ({@code safe=true}).</li>
     * </ul>
     *
     * @param wotActionType     WoT action URI of the candidate actuator.
     * @param requestingZoneIdx 1-based zone index requesting the deactivation.
     * @param zoneLevels        Current zone illuminance levels (ordered by zone index).
     * @param zoneTargets       Target illuminance ranks (ordered by zone index).
     * @param safe              Output: true if deactivation is safe.
     */
    @OPERATION
    public void checkSharedActuatorSafeToDeactivate(
            String wotActionType, int requestingZoneIdx,
            Object[] zoneLevels, Object[] zoneTargets,
            OpFeedbackParam<Boolean> safe) {

        LOGGER.info("checkSharedActuatorSafeToDeactivate: action=" + wotActionType
                   + " requestingZone=" + requestingZoneIdx);

        String sparql = String.format(SHARED_ACTUATOR_ZONES_QUERY, wotActionType);
        List<Integer> affectedZoneIdxs = new ArrayList<>();

        try {
            Query q = QueryFactory.create(sparql);
            try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
                ResultSet rs = qe.execSelect();
                while (rs.hasNext()) {
                    QuerySolution sol = rs.nextSolution();
                    affectedZoneIdxs.add(sol.getLiteral("zoneIdx").getInt());
                }
            }
        } catch (Exception e) {
            LOGGER.severe("checkSharedActuatorSafeToDeactivate SPARQL failed: " + e.getMessage());
            safe.set(true); // fail-open: allow deactivation if query fails
            return;
        }

        // Single-zone actuator: deactivation never affects another zone
        if (affectedZoneIdxs.size() <= 1) {
            LOGGER.info("  Single-zone actuator — safe to deactivate.");
            safe.set(true);
            return;
        }

        // Multi-zone: deactivation is safe only when some non-requesting zone is
        // already at or above its target (that zone does not need this actuator).
        for (int zIdx : affectedZoneIdxs) {
            if (zIdx == requestingZoneIdx) continue;
            int arrayIdx = zIdx - 1;
            if (arrayIdx >= 0 && arrayIdx < zoneLevels.length && arrayIdx < zoneTargets.length) {
                int level = toInt(zoneLevels[arrayIdx]);
                int target = toInt(zoneTargets[arrayIdx]);
                if (level >= target) {
                    LOGGER.info("  Zone " + zIdx + " at level=" + level
                              + " (target=" + target + ") — does not need actuator. SAFE to deactivate.");
                    safe.set(true);
                    return;
                }
            }
        }

        LOGGER.info("  All non-requesting zones below target — UNSAFE to deactivate.");
        safe.set(false);
    }

    private static int toInt(Object o) {
        if (o instanceof Number) return ((Number) o).intValue();
        return Integer.parseInt(String.valueOf(o));
    }
}
