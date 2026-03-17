package tools;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
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
 * At init() time the artifact loads lab-ontology.ttl (which must be on the
 * Java classpath, i.e., in src/resources/) into an Apache Jena OntModel with
 * OWL Micro Rule inference (RDFS + OWL-micro entailment).
 *
 * The two main operations each:
 *   1. Run a SPARQL SELECT to fetch all components in the requested zone
 *      together with their Elementary Ontology stereotype metadata
 *      (mechanism, MV label, DV label, IV label, IV type).
 *   2. Filter results in Java using runtime state (lightOn, blindsUp, sunshine).
 *   3. Return the first candidate's metadata via OpFeedbackParam to the agent.
 *
 * Usage in illuminance_controller_agent.asl:
 *   makeArtifact("ontology", "tools.OntologyArtifact", ["lab-ontology.ttl"], OntId);
 *   queryBestIncreaseAction(Zone, LightOn, BlindsUp, Sunshine,
 *       CompId, Mechanism, MvLabel, DvLabel, IvLabel)[artifact_id(OntId)];
 */
public class OntologyArtifact extends Artifact {

    private static final Logger LOGGER =
            Logger.getLogger(OntologyArtifact.class.getName());

    /** Shared SPARQL prefix block prepended to every query. */
    private static final String PREFIXES =
            "PREFIX owl:   <http://www.w3.org/2002/07/owl#> " +
            "PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " +
            "PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#> " +
            "PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#> " +
            "PREFIX brick: <https://brickschema.org/schema/Brick#> " +
            "PREFIX elem:  <http://w3id.org/elementary#> " +
            "PREFIX ws:    <http://example.org/was/lab/stereotypes#> " +
            "PREFIX lab:   <http://example.org/was/lab#> ";

    /** Base namespace for lab instances — used to build zone URIs. */
    private static final String LAB_NS = "http://example.org/was/lab#";

    /** SPARQL SELECT that retrieves ALL components in a zone with their metadata.
     *  Traverses the three-layer Elementary Ontology architecture:
     *    ?comp --(elem:hasStereotype)--> ?stereo
     *          --(elem:hasProcessMechanism)--> ?mech
     *          --(elem:hasManipulatedVariable / hasDependentVariable / hasIndependentVariable)--> variables
     *  The zone URI is injected as a string literal into the query at call time.
     *  ivLabel is OPTIONAL (absent for mechanisms with no IV; Java defaults it to "none").
     *  Note: the new ontology uses elem:hasProcessMechanism (not hasPhysicalMechanism)
     *  and does not carry elem:hasIVType — IV presence is detected by ivLabel != "none". */
    private static final String ZONE_COMPONENTS_QUERY =
            PREFIXES +
            "SELECT ?comp ?mechanism ?mvLabel ?dvLabel ?ivLabel " +
            "WHERE { " +
            "  ?comp  brick:isLocatedIn          <%s> . " +   // %s = zone URI
            "  ?comp  elem:hasStereotype         ?stereo . " +
            "  ?stereo elem:hasProcessMechanism  ?mech . " +
            "  ?mech  rdfs:label                 ?mechanism . " +
            "  ?mech  elem:hasManipulatedVariable ?mv . " +
            "  ?mv    rdfs:label                  ?mvLabel . " +
            "  ?mech  elem:hasDependentVariable   ?dv . " +
            "  ?dv    rdfs:label                  ?dvLabel . " +
            "  OPTIONAL { " +
            "    ?mech elem:hasIndependentVariable ?iv . " +
            "    ?iv   rdfs:label                  ?ivLabel . " +
            "  } " +
            "}";

    private OntModel ontModel;

    // ----------------------------------------------------------------
    // CArtAgO operations
    // ----------------------------------------------------------------

    /**
     * Load the RDF/Turtle ontology file from the Java classpath.
     *
     * @param ttlResourcePath  Classpath resource name, e.g. "lab-ontology.ttl".
     *                         Place the file in src/resources/ so Gradle copies
     *                         it onto the runtime classpath automatically.
     */
    @OPERATION
    public void init(String ttlResourcePath) {
        // OWL_MEM_MICRO_RULE_INF applies RDFS entailment + OWL Micro rules
        // (subclass/subproperty/owl:hasValue) without full OWL-DL reasoning.
        // Enables rdfs:subClassOf/subPropertyOf traversal (e.g. elem:manipulates
        // as a sub-property of elem:isRelatedToVariable) and class membership inference.
        ontModel = ModelFactory.createOntologyModel(OntModelSpec.OWL_MEM_MICRO_RULE_INF);

        InputStream in = getClass().getClassLoader().getResourceAsStream(ttlResourcePath);
        if (in != null) {
            ontModel.read(in, null, "TURTLE");
            long tripleCount = ontModel.size();
            LOGGER.info("OntologyArtifact: loaded '" + ttlResourcePath +
                        "'. Base triples: " + tripleCount);
        } else {
            LOGGER.severe("OntologyArtifact: resource NOT found on classpath: '" +
                          ttlResourcePath + "'. Ensure the file is in src/resources/.");
        }
    }

    /**
     * Query the KG for the best component to INCREASE illuminance in a zone.
     *
     * Algorithm:
     *   1. SPARQL SELECT: fetch all components in zone with their stereotype metadata.
     *   2. Java filter — IV satisfaction: skip component if its IV type is "sunshine"
     *      AND sunshineRank < 1 (blind cannot increase illuminance without solar input).
     *   3. Java filter — current state: skip if already in the activated state
     *      (light already ON, or blind already UP — nothing to do).
     *   4. Return the first candidate that passes both filters.
     *
     * @param zone          Zone number (1 or 2).
     * @param lightOn       Current state: is the ceiling light ON?
     * @param blindsUp      Current state: are the blinds UP (open)?
     * @param sunshineRank  Current sunshine discretised rank (0–3).
     * @param componentId   Output: local name of selected component, or "none".
     * @param mechanism     Output: mechanism name (e.g. "light_throttling").
     * @param mvLabel       Output: MV human-readable label.
     * @param dvLabel       Output: DV human-readable label.
     * @param ivLabel       Output: IV human-readable label, or "none".
     */
    @OPERATION
    public void queryBestIncreaseAction(
            int zone, boolean lightOn, boolean blindsUp, int sunshineRank,
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel) {

        LOGGER.info("queryBestIncreaseAction: zone=" + zone +
                    " lightOn=" + lightOn + " blindsUp=" + blindsUp +
                    " sunshine=" + sunshineRank);

        List<Map<String, String>> candidates = queryZoneComponents(zone);

        for (Map<String, String> c : candidates) {
            String cId      = c.get("compId");
            String ivLabelVal = c.get("ivLabel");

            // --- Filter 1: IV satisfaction ---
            // If the mechanism has an IV (ivLabel != "none"), it is outdoor illuminance
            // (sunshine). The blind can only increase illuminance if sunshineRank >= 1.
            boolean ivOk = ivLabelVal.equals("none") || sunshineRank >= 1;
            if (!ivOk) {
                LOGGER.info("  Skipping " + cId + ": IV '" + ivLabelVal +
                            "' not satisfied (sunshine=" + sunshineRank + ")");
                continue;
            }

            // --- Filter 2: Current state actionability for INCREASE ---
            // A light can increase illuminance only if it is currently OFF (can turn ON).
            // A blind can increase illuminance only if it is currently DOWN (can raise UP).
            boolean stateOk;
            if (cId.toLowerCase().contains("light")) {
                stateOk = !lightOn;
            } else if (cId.toLowerCase().contains("blind")) {
                stateOk = !blindsUp;
            } else {
                stateOk = false;
            }
            if (!stateOk) {
                LOGGER.info("  Skipping " + cId + ": already in target state for increase " +
                            "(lightOn=" + lightOn + " blindsUp=" + blindsUp + ")");
                continue;
            }

            // --- Candidate selected ---
            setOutputs(componentId, mechanism, mvLabel, dvLabel, ivLabel, c);
            LOGGER.info("  Selected: " + cId + " (mechanism=" + c.get("mechanism") + ")");
            return;
        }

        setNoResult(componentId, mechanism, mvLabel, dvLabel, ivLabel);
        LOGGER.info("  No actionable component found for increase in zone " + zone);
    }

    /**
     * Query the KG for the best component to DECREASE illuminance in a zone.
     *
     * Algorithm:
     *   1. SPARQL SELECT: fetch all components in zone with their stereotype metadata.
     *   2. Java filter — current state: skip if already in the deactivated state
     *      (light already OFF, or blind already DOWN — nothing to deactivate).
     *      No IV filter needed for deactivation.
     *   3. Return the first candidate that passes the state filter.
     *
     * @param zone          Zone number (1 or 2).
     * @param lightOn       Current state: is the ceiling light ON?
     * @param blindsUp      Current state: are the blinds UP (open)?
     * @param sunshineRank  Current sunshine rank (passed through for logging only).
     * @param componentId   Output: local name of selected component, or "none".
     * @param mechanism     Output: mechanism name.
     * @param mvLabel       Output: MV label.
     * @param dvLabel       Output: DV label.
     * @param ivLabel       Output: IV label.
     */
    @OPERATION
    public void queryBestDecreaseAction(
            int zone, boolean lightOn, boolean blindsUp, int sunshineRank,
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel) {

        LOGGER.info("queryBestDecreaseAction: zone=" + zone +
                    " lightOn=" + lightOn + " blindsUp=" + blindsUp);

        List<Map<String, String>> candidates = queryZoneComponents(zone);

        for (Map<String, String> c : candidates) {
            String cId = c.get("compId");

            // --- Filter: Current state actionability for DECREASE ---
            // A light can decrease illuminance only if it is currently ON (can turn OFF).
            // A blind can decrease illuminance only if it is currently UP (can lower DOWN).
            boolean stateOk;
            if (cId.toLowerCase().contains("light")) {
                stateOk = lightOn;
            } else if (cId.toLowerCase().contains("blind")) {
                stateOk = blindsUp;
            } else {
                stateOk = false;
            }
            if (!stateOk) {
                LOGGER.info("  Skipping " + cId + ": not in deactivatable state " +
                            "(lightOn=" + lightOn + " blindsUp=" + blindsUp + ")");
                continue;
            }

            setOutputs(componentId, mechanism, mvLabel, dvLabel, ivLabel, c);
            LOGGER.info("  Selected: " + cId + " (mechanism=" + c.get("mechanism") + ")");
            return;
        }

        setNoResult(componentId, mechanism, mvLabel, dvLabel, ivLabel);
        LOGGER.info("  No actionable component found for decrease in zone " + zone);
    }

    // ----------------------------------------------------------------
    // Private helpers
    // ----------------------------------------------------------------

    /**
     * Execute the zone-components SPARQL SELECT and return results as a list
     * of property maps.
     *
     * Each map contains the keys:
     *   compId, mechanism, mvLabel, dvLabel, ivType, ivLabel
     */
    private List<Map<String, String>> queryZoneComponents(int zone) {
        String zoneUri = LAB_NS + "Zone" + zone;
        String sparql  = String.format(ZONE_COMPONENTS_QUERY, zoneUri);

        LOGGER.fine("SPARQL:\n" + sparql);

        List<Map<String, String>> results = new ArrayList<>();
        Query q = QueryFactory.create(sparql);

        try (QueryExecution qe = QueryExecutionFactory.create(q, ontModel)) {
            ResultSet rs = qe.execSelect();
            while (rs.hasNext()) {
                QuerySolution sol = rs.nextSolution();
                Map<String, String> row = new LinkedHashMap<>();

                // Component local name — extracted from the resource URI
                // e.g. <http://example.org/was/lab#CeilingLight_Z1> → "CeilingLight_Z1"
                row.put("compId",    sol.getResource("comp").getLocalName());
                row.put("mechanism", sol.getLiteral("mechanism").getString());
                row.put("mvLabel",   sol.getLiteral("mvLabel").getString());
                row.put("dvLabel",   sol.getLiteral("dvLabel").getString());

                // ivLabel is OPTIONAL: only present when the mechanism has an IV.
                // Mechanisms without an IV (e.g. ws:illumination) produce no binding;
                // Java defaults to "none". When present (ws:daylighting), ivLabel is
                // "Outdoor illuminance (sunshine)" — used as the IV-presence signal.
                RDFNode ivNode = sol.get("ivLabel");
                row.put("ivLabel", (ivNode != null && ivNode.isLiteral())
                        ? ivNode.asLiteral().getString()
                        : "none");

                results.add(row);
                LOGGER.fine("  SPARQL row: " + row);
            }
        } catch (Exception e) {
            LOGGER.severe("SPARQL query failed for zone " + zone + ": " + e.getMessage());
        }

        LOGGER.info("queryZoneComponents(zone=" + zone + "): " +
                    results.size() + " candidate(s) found.");
        return results;
    }

    /** Set all five output parameters from a candidate result map. */
    private void setOutputs(
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel,
            Map<String, String> c) {
        componentId.set(c.get("compId"));
        mechanism.set(c.get("mechanism"));
        mvLabel.set(c.get("mvLabel"));
        dvLabel.set(c.get("dvLabel"));
        ivLabel.set(c.get("ivLabel"));
    }

    /** Set all five output parameters to "none" when no component is found. */
    private void setNoResult(
            OpFeedbackParam<String> componentId,
            OpFeedbackParam<String> mechanism,
            OpFeedbackParam<String> mvLabel,
            OpFeedbackParam<String> dvLabel,
            OpFeedbackParam<String> ivLabel) {
        componentId.set("none");
        mechanism.set("none");
        mvLabel.set("none");
        dvLabel.set("none");
        ivLabel.set("none");
    }
}
