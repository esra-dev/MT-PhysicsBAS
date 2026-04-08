package tools;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.hc.client5.http.impl.DefaultConnectionKeepAliveStrategy;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.http.impl.DefaultConnectionReuseStrategy;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;
import ch.unisg.ics.interactions.wot.td.ThingDescription;
import ch.unisg.ics.interactions.wot.td.ThingDescription.TDFormat;
import ch.unisg.ics.interactions.wot.td.affordances.ActionAffordance;
import ch.unisg.ics.interactions.wot.td.affordances.Form;
import ch.unisg.ics.interactions.wot.td.affordances.PropertyAffordance;
import ch.unisg.ics.interactions.wot.td.clients.TDHttpRequest;
import ch.unisg.ics.interactions.wot.td.clients.TDHttpResponse;
import ch.unisg.ics.interactions.wot.td.io.TDGraphReader;
import ch.unisg.ics.interactions.wot.td.schemas.DataSchema;
import ch.unisg.ics.interactions.wot.td.schemas.ObjectSchema;
import ch.unisg.ics.interactions.wot.td.vocabularies.TD;

/**
 * LabEnvironment artifact for interacting with the lab environment.
 * Provides operations to read the current state and perform actions
 * on the lights and blinds in both workstations.
 * 
 * Works with both simulated and real lab environments via W3C WoT Thing Descriptions.
 */
public class LabEnvironment extends Artifact {

    private ThingDescription td;
    private static final Logger LOGGER = Logger.getLogger(LabEnvironment.class.getName());

    private double[] lightBounds    = {50.0, 100.0, 300.0};
    private double[] sunshineBounds = {50.0, 200.0, 700.0};

    /**
     * Initialize the artifact with a W3C WoT Thing Description URL.
     * 
     * @param tdUrl URL to the Thing Description (simulated or real lab)
     */
    @OPERATION
    public void init(String tdUrl) {
        try {
            CloseableHttpClient httpClient = HttpClients.custom()
                .setConnectionManager(new PoolingHttpClientConnectionManager())
                .setConnectionReuseStrategy(DefaultConnectionReuseStrategy.INSTANCE)
                .setKeepAliveStrategy(DefaultConnectionKeepAliveStrategy.INSTANCE)
                .build();

            // Resolve classpath: URIs so local TD files bundled in src/resources/
            // can be referenced as "classpath:interactions-lab-custom.ttl".
            if (tdUrl.startsWith("classpath:")) {
                String resourcePath = tdUrl.substring("classpath:".length());
                try (java.io.InputStream is = getClass().getClassLoader()
                        .getResourceAsStream(resourcePath)) {
                    if (is == null) {
                        throw new IOException("Classpath resource not found: " + tdUrl);
                    }
                    String content = new String(is.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
                    this.td = TDGraphReader.readFromString(TDFormat.RDF_TURTLE, content);
                    LOGGER.info("LabEnvironment initialized with Thing Description from: " + tdUrl);
                }
            } else {
                this.td = TDGraphReader.readFromURL(TDFormat.RDF_TURTLE, tdUrl);
                LOGGER.info("LabEnvironment initialized with Thing Description from: " + tdUrl);
            }

        } catch (IOException e) {
            LOGGER.severe("Failed to initialize LabEnvironment: " + e.getMessage());
        }
    }

    /**
     * Configure discretisation thresholds from ontology-provided arrays.
     * Called once at startup after getDiscretizationBounds is queried.
     *
     * @param lBounds  Double[3] rank boundaries for indoor light level.
     * @param sBounds  Double[3] rank boundaries for sunshine.
     */
    @OPERATION
    public void configureDiscretization(Object[] lBounds, Object[] sBounds) {
        this.lightBounds    = toDoubleArray(lBounds);
        this.sunshineBounds = toDoubleArray(sBounds);
        LOGGER.info("Discretisation configured: light=" + Arrays.toString(lightBounds) +
                    " sunshine=" + Arrays.toString(sunshineBounds));
    }

    /**
     * Read the current state of the lab in a single HTTP call.
     *
     * Returns:
     *   zoneLevels       — discretised illuminance rank per zone, ordered by zone index.
     *   sunshineRank     — discretised outdoor sunshine rank (0–3), shared across zones.
     *   boolStateKeys    — all WoT status property URIs carrying boolean values.
     *   boolStateValues  — current boolean value for each key (parallel array).
     *
     * @param zoneLevels      Output: Integer[] of per-zone illuminance ranks.
     * @param sunshineRank    Output: sunshine rank.
     * @param boolStateKeys   Output: WoT status URI strings.
     * @param boolStateValues Output: corresponding boolean values.
     */
    @OPERATION
    public void readLabStatus(
            OpFeedbackParam<Object[]> zoneLevels,
            OpFeedbackParam<Integer>  sunshineRank,
            OpFeedbackParam<Object[]> boolStateKeys,
            OpFeedbackParam<Object[]> boolStateValues) {

        Optional<PropertyAffordance> p =
                this.td.getFirstPropertyBySemanticType("https://example.org/was#Status");

        if (p.isPresent()) {
            Optional<Form> f = p.get().getFirstFormForOperationType(TD.readProperty);

            if (f.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.readProperty);
                try {
                    TDHttpResponse response = request.execute();

                    // Build status map directly from raw JSON (Gson) so that all
                    // properties — including ones wot-td-java's RDF schema parser
                    // may miss — are reliably present.  getPayload() is called once
                    // here before anything else can consume the response body.
                    Optional<String> rawOpt = response.getPayload();
                    if (!rawOpt.isPresent()) {
                        failed("readLabStatus: empty response payload");
                        return;
                    }
                    Map<String, Object> status = new java.util.HashMap<>();
                    JsonElement root = JsonParser.parseString(rawOpt.get());
                    if (root.isJsonObject()) {
                        for (Map.Entry<String, JsonElement> e :
                                root.getAsJsonObject().entrySet()) {
                            String uri = "http://example.org/was#" + e.getKey();
                            JsonElement val = e.getValue();
                            if (val.isJsonPrimitive()) {
                                if (val.getAsJsonPrimitive().isBoolean()) {
                                    status.put(uri, val.getAsBoolean());
                                } else if (val.getAsJsonPrimitive().isNumber()) {
                                    status.put(uri, val.getAsDouble());
                                }
                            }
                        }
                    }

                    // Collect zone illuminance levels keyed by zone index
                    Pattern zonePattern = Pattern.compile(".+#Z(\\d+)Level$");
                    TreeMap<Integer, Integer> zoneMap = new TreeMap<>();
                    List<String>  bKeys = new ArrayList<>();
                    List<Boolean> bVals = new ArrayList<>();

                    for (Map.Entry<String, Object> entry : status.entrySet()) {
                        String key   = entry.getKey();
                        Object value = entry.getValue();

                        Matcher m = zonePattern.matcher(key);
                        if (m.matches()) {
                            int zIdx = Integer.parseInt(m.group(1));
                            zoneMap.put(zIdx, discretize((Double) value, lightBounds));
                        } else if (value instanceof Boolean) {
                            bKeys.add(key);
                            bVals.add((Boolean) value);
                        }
                    }

                    int sun = discretize(
                            (Double) status.get("http://example.org/was#Sunshine"),
                            sunshineBounds);

                    zoneLevels.set(zoneMap.values().toArray());
                    sunshineRank.set(sun);
                    boolStateKeys.set(bKeys.toArray());
                    boolStateValues.set(bVals.toArray());

                    LOGGER.info("readLabStatus: zones=" + zoneMap +
                                " sunshine=" + sun + " boolStates=" + bKeys);

                } catch (IOException e) {
                    LOGGER.severe("readLabStatus failed: " + e.getMessage());
                    failed("readLabStatus: " + e.getMessage());
                }
            }
        }
    }

    /**
     * Generic action dispatch: looks up the WoT action affordance by its
     * semantic type URI (as stored in ws:hasWoTActionSemanticType) and
     * invokes it with the given boolean value.
     *
     * Replaces the per-component setZ1Light / setZ2Light / … convenience
     * operations for the dynamic, ontology-driven control path.
     *
     * @param wotSemanticType  Full action @type URI, e.g.
     *                         "http://example.org/was#SetZ1Light".
     * @param value            true = activate / open; false = deactivate / close.
     */
    @OPERATION
    public void invokeAction(String wotSemanticType, boolean value) {
        LOGGER.info("invokeAction: " + wotSemanticType + " = " + value);
        performBooleanAction(wotSemanticType, value);
    }

    /**
     * Read the current state for a single zone.
     *
     * @deprecated Use {@link #readLabStatus} instead to collect all zones in one HTTP call.
     *
     * @param zoneIndex       Zone index (1 or 2).
     * @param level           Output: illuminance rank for the zone.
     * @param sunshineRank    Output: sunshine rank.
     * @param boolStateKeys   Output: WoT status URI strings.
     * @param boolStateValues Output: corresponding boolean values.
     */
    @Deprecated
    @OPERATION
    public void readZoneState(int zoneIndex,
                              OpFeedbackParam<Integer> level,
                              OpFeedbackParam<Integer> sunshineRank,
                              OpFeedbackParam<Object[]> boolStateKeys,
                              OpFeedbackParam<Object[]> boolStateValues) {

        Optional<PropertyAffordance> p =
                this.td.getFirstPropertyBySemanticType("https://example.org/was#Status");

        if (p.isPresent()) {
            Optional<Form> f = p.get().getFirstFormForOperationType(TD.readProperty);
            DataSchema ds = p.get().getDataSchema();

            if (f.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.readProperty);
                try {
                    TDHttpResponse response = request.execute();
                    Map<String, Object> status =
                            response.getPayloadAsObject((ObjectSchema) ds);

                    String base = "http://example.org/was#Z" + zoneIndex;
                    level.set(discretize(
                            (Double) status.get(base + "Level"), lightBounds));
                    sunshineRank.set(discretize(
                            (Double) status.get("http://example.org/was#Sunshine"),
                            sunshineBounds));

                    // Collect all boolean entries so OntologyArtifact can look up
                    // each actuator's current state by its WoT state semantic type URI.
                    java.util.List<String>  keys = new java.util.ArrayList<>();
                    java.util.List<Boolean> vals = new java.util.ArrayList<>();
                    for (Map.Entry<String, Object> entry : status.entrySet()) {
                        if (entry.getValue() instanceof Boolean) {
                            keys.add(entry.getKey());
                            vals.add((Boolean) entry.getValue());
                        }
                    }
                    boolStateKeys.set(keys.toArray());
                    boolStateValues.set(vals.toArray());

                    LOGGER.info("readZoneState(Z" + zoneIndex + "): level=" +
                            level.get() + " sunshine=" + sunshineRank.get() +
                            " boolStates=" + keys);

                } catch (IOException e) {
                    LOGGER.severe("readZoneState Z" + zoneIndex +
                                  " failed: " + e.getMessage());
                }
            }
        }
    }

    /**
     * Helper method to perform a boolean action on the lab.
     * Gets the property name from the Thing Description schema.
     */
    private void performBooleanAction(String actionType, boolean value) {
        Optional<ActionAffordance> a = this.td.getFirstActionBySemanticType(actionType);

        if (a.isPresent()) {
            Optional<Form> f = a.get().getFirstFormForOperationType(TD.invokeAction);
            Optional<DataSchema> ds = a.get().getInputSchema();

            if (f.isPresent() && ds.isPresent()) {
                TDHttpRequest request = new TDHttpRequest(f.get(), TD.invokeAction);
                
                // Get the property name from the schema (e.g., "Z1Light" not the full URI)
                Map<String, DataSchema> props = ((ObjectSchema) ds.get()).getProperties();
                Map<String, Object> payload = new HashMap<>();
                
                // Use the first property name from the schema
                for (String propName : props.keySet()) {
                    payload.put(propName, value);
                    LOGGER.info("Action payload: {" + propName + ": " + value + "}");
                }
                
                request.setObjectPayload((ObjectSchema) ds.get(), payload);

                try {
                    TDHttpResponse response = request.execute();
                    LOGGER.info("Action executed successfully. Response code: " + response.getStatusCode());
                } catch (IOException e) {
                    LOGGER.severe("Failed to perform action " + actionType + ": " + e.getMessage());
                }
            }
        } else {
            LOGGER.warning("Action not found in Thing Description: " + actionType);
        }
    }

    private double[] toDoubleArray(Object[] arr) {
        double[] d = new double[arr.length];
        for (int i = 0; i < arr.length; i++) d[i] = ((Number) arr[i]).doubleValue();
        return d;
    }

    private int discretize(double value, double[] bounds) {
        if (value < bounds[0]) return 0;
        if (value < bounds[1]) return 1;
        if (value < bounds[2]) return 2;
        return 3;
    }

    /**
     * Maps lux values to light levels using configured bounds.
     */
    private int discretizeLightLevel(Double value) {
        return discretize(value, lightBounds);
    }

    /**
     * Maps sunshine values to levels using configured bounds.
     */
    private int discretizeSunshine(Double value) {
        return discretize(value, sunshineBounds);
    }
}
