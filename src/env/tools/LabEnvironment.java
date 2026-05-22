package tools;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

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

    private double[] lightBounds    = {75.0, 200.0, 400.0};
    private double[] sunshineBounds = {50.0, 200.0, 700.0};

    /** Fault-tolerant HTTP client shared by all simulator POSTs (#5). */
    private final SimulatorHttpClient simHttp = new SimulatorHttpClient();
    /** WoT-TD-driven input validator built once at init() (#8). */
    private WotInputValidator validator;
    /** When true, all simulator-mutating operations short-circuit (#12). */
    private volatile boolean dryRun = false;

    /**
     * Initialize the artifact with a W3C WoT Thing Description URL.
     * 
     * @param tdUrl URL to the Thing Description (simulated or real lab)
     */
    @OPERATION
    public void init(String tdUrl) {
        // #4: route java.util.logging through Logback (idempotent).
        LoggingBootstrap.install();
        // #1: pick up simulator HTTP tuning from system properties so that
        // config/run_config.json (forwarded by Gradle as -Dsim.http.*) takes
        // effect without an explicit configureHttp call from ASL.
        applyHttpSystemProperties();
        try {
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
                    // Strip a leading UTF-8 BOM (U+FEFF) if present — the RDF4J Turtle
                    // parser does not skip it and would fail with
                    // "Expected ':', found '@' [line 1]".
                    if (!content.isEmpty() && content.charAt(0) == '\uFEFF') {
                        content = content.substring(1);
                    }
                    this.td = TDGraphReader.readFromString(TDFormat.RDF_TURTLE, content);
                    this.validator = new WotInputValidator(this.td);
                    LOGGER.info("LabEnvironment initialized with Thing Description from: " + tdUrl);
                }
            } else {
                this.td = TDGraphReader.readFromURL(TDFormat.RDF_TURTLE, tdUrl);
                this.validator = new WotInputValidator(this.td);
                LOGGER.info("LabEnvironment initialized with Thing Description from: " + tdUrl);
            }

        } catch (IOException e) {
            // Fail fast: leaving `td` / `validator` null would only surface as an
            // opaque NullPointerException on the first @OPERATION call. Signal
            // the failure through CArtAgO so the agent can handle it cleanly.
            LOGGER.severe("Failed to initialize LabEnvironment: " + e.getMessage());
            failed("td_load_failed", tdUrl, e.getMessage());
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
     * Configure the simulator HTTP client (#5). Re-tuneable at runtime so
     * agents can tighten or relax timeouts per scenario without restarting.
     *
     * @param connectMs   Connect-phase timeout (ms). 0 disables.
     * @param responseMs  Response-wait timeout (ms). 0 disables.
     * @param maxRetries  Number of *additional* attempts after the first failure.
     * @param backoffMs   Base backoff in ms; effective delay = base * 2^attempt.
     */
    @OPERATION
    public void configureHttp(int connectMs, int responseMs, int maxRetries, int backoffMs) {
        simHttp.configure(connectMs, responseMs, maxRetries, backoffMs);
    }

    /**
     * Apply HTTP tuning supplied via {@code -Dsim.http.*} system properties
     * (sourced from {@code config/run_config.json}'s {@code http_client}
     * block via Gradle). Falls back silently to defaults when unset or
     * non-numeric. Called once from {@link #init(String)}.
     */
    private void applyHttpSystemProperties() {
        try {
            Integer c = Integer.getInteger("sim.http.connectMs");
            Integer r = Integer.getInteger("sim.http.responseMs");
            Integer n = Integer.getInteger("sim.http.maxRetries");
            Integer b = Integer.getInteger("sim.http.backoffMs");
            if (c == null && r == null && n == null && b == null) {
                return;  // nothing to apply
            }
            int connectMs  = (c != null) ? c : 2000;
            int responseMs = (r != null) ? r : 5000;
            int retries    = (n != null) ? n : 3;
            int backoffMs  = (b != null) ? b : 200;
            simHttp.configure(connectMs, responseMs, retries, backoffMs);
            LOGGER.info("SimulatorHttpClient configured from -Dsim.http.*: connect="
                + connectMs + "ms response=" + responseMs + "ms retries="
                + retries + " backoff=" + backoffMs + "ms");
        } catch (RuntimeException e) {
            LOGGER.warning("applyHttpSystemProperties: ignored bad value (" + e.getMessage() + ")");
        }
    }

    /**
     * Toggle dry-run mode (#12). When enabled, mutating simulator calls
     * ({@code resetLab}, {@code setLabState*}, {@code invokeAction}) are
     * logged but not dispatched over HTTP. Read paths remain live.
     */
    @OPERATION
    public void configureDryRun(boolean enabled) {
        this.dryRun = enabled;
        LOGGER.info("Dry-run mode " + (enabled ? "ENABLED" : "disabled"));
    }

    // ----------------------------------------------------------------
    // Raw status and reset helpers (shared by readLabStatus + calibrate)
    // ----------------------------------------------------------------

    /**
     * Fetch the raw simulator status via HTTP and return a map of
     * URI-keyed values (Double for numerics, Boolean for booleans).
     */
    private Map<String, Object> fetchRawStatus() throws IOException {
        Optional<PropertyAffordance> p =
                this.td.getFirstPropertyBySemanticType("https://example.org/was#Status");
        if (!p.isPresent()) throw new IOException("Status property not found in TD");

        Optional<Form> f = p.get().getFirstFormForOperationType(TD.readProperty);
        if (!f.isPresent()) throw new IOException("No form for Status property");

        TDHttpRequest request = new TDHttpRequest(f.get(), TD.readProperty);
        TDHttpResponse response = request.execute();

        Optional<String> rawOpt = response.getPayload();
        if (!rawOpt.isPresent()) throw new IOException("Empty response payload");

        Map<String, Object> status = new HashMap<>();
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
        return status;
    }

    /**
     * Internal reset — sends POST to the simulator's /reset endpoint.
     * Shared by the public resetLab() operation and calibrate().
     */
    private void doReset() {
        String resetUrl = deriveSimulatorUrl("/reset");
        if (resetUrl == null) {
            LOGGER.warning("doReset: could not derive reset URL — skipping");
            return;
        }
        if (dryRun) {
            LOGGER.info("doReset[dry-run]: would POST " + resetUrl);
            return;
        }
        try {
            SimulatorHttpClient.Result r = simHttp.postJson(resetUrl, "{}");
            LOGGER.fine("doReset: POST " + resetUrl + " → " + r.code);
            if (r.code >= 400) {
                LOGGER.warning("doReset: simulator returned HTTP " + r.code + " body=" + r.body);
            }
        } catch (SimulatorHttpClient.SimulatorUnreachableException e) {
            LOGGER.severe("doReset: " + e.getMessage());
            failed("simulator_unreachable", "reset", resetUrl);
        } catch (IOException e) {
            LOGGER.warning("doReset: POST failed: " + e.getMessage());
        }
    }

    // ----------------------------------------------------------------
    // Calibration — learn discretisation bounds from live observations
    // ----------------------------------------------------------------

    /**
     * Run a calibration phase: reset the simulator {@code numSamples} times,
     * collect raw sensor values, and compute equal-frequency (percentile)
     * rank boundaries.  Sets the internal lightBounds / sunshineBounds
     * arrays so that subsequent readLabStatus calls use the learned bounds.
     *
     * <p>This replaces the static ws:rankBound_N triples in the ontology.
     *
     * @param numSamples          Number of reset-and-read cycles (e.g. 50).
     * @param learnedLightBounds  Output: Double[3] learned [b1, b2, b3] for indoor lux.
     * @param learnedSunshineBounds Output: Double[3] learned [b1, b2, b3] for sunshine.
     */
    @OPERATION
    public void calibrate(int numSamples,
                          OpFeedbackParam<Object[]> learnedLightBounds,
                          OpFeedbackParam<Object[]> learnedSunshineBounds) {

        LOGGER.info("calibrate: starting with " + numSamples + " samples");
        List<Double> zoneLevelSamples = new ArrayList<>();
        List<Double> sunshineSamples = new ArrayList<>();
        Pattern zonePattern = Pattern.compile(".+#Z(\\d+)Level$");

        for (int i = 0; i < numSamples; i++) {
            doReset();
            try { Thread.sleep(500); } catch (InterruptedException ignored) {}

            try {
                Map<String, Object> status = fetchRawStatus();
                for (Map.Entry<String, Object> entry : status.entrySet()) {
                    if (entry.getValue() instanceof Double) {
                        Matcher m = zonePattern.matcher(entry.getKey());
                        if (m.matches()) {
                            zoneLevelSamples.add((Double) entry.getValue());
                        }
                    }
                }
                Object sun = status.get("http://example.org/was#Sunshine");
                if (sun instanceof Double) {
                    sunshineSamples.add((Double) sun);
                }
            } catch (IOException e) {
                LOGGER.warning("calibrate: sample " + i + " failed: " + e.getMessage());
            }
        }

        double[] lb = computePercentileBounds(zoneLevelSamples, new double[]{50.0, 100.0, 300.0});
        double[] sb = computePercentileBounds(sunshineSamples, new double[]{50.0, 200.0, 700.0});

        this.lightBounds = lb;
        this.sunshineBounds = sb;

        learnedLightBounds.set(new Object[]{lb[0], lb[1], lb[2]});
        learnedSunshineBounds.set(new Object[]{sb[0], sb[1], sb[2]});

        LOGGER.info("calibrate: lightBounds=" + Arrays.toString(lb) +
                    " sunshineBounds=" + Arrays.toString(sb) +
                    " (" + zoneLevelSamples.size() + " level samples, " +
                    sunshineSamples.size() + " sunshine samples)");
    }

    /**
     * Compute three percentile boundaries (25th, 50th, 75th) that split
     * the observed values into four roughly equal-frequency bins (ranks 0–3).
     *
     * @param values   observed raw sensor values.
     * @param fallback default bounds if no samples were collected.
     * @return double[3] with strictly increasing boundaries.
     */
    private double[] computePercentileBounds(List<Double> values, double[] fallback) {
        if (values.isEmpty()) {
            LOGGER.warning("computePercentileBounds: no samples — using fallback " +
                           Arrays.toString(fallback));
            return fallback;
        }
        Collections.sort(values);
        int n = values.size();
        double p25 = values.get(Math.max(0, (int) (n * 0.25) - 1));
        double p50 = values.get(Math.max(0, (int) (n * 0.50) - 1));
        double p75 = values.get(Math.max(0, (int) (n * 0.75) - 1));
        // Ensure strictly increasing
        if (p50 <= p25) p50 = p25 + 1.0;
        if (p75 <= p50) p75 = p50 + 1.0;
        return new double[]{p25, p50, p75};
    }

    // ----------------------------------------------------------------
    // CArtAgO operations
    // ----------------------------------------------------------------

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

        try {
            Map<String, Object> status = fetchRawStatus();

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

    /**
     * Read raw zone temperatures from the simulator status.
     * Parses every property whose URI matches {@code .+#Z<n>Temp$} and returns
     * the values ordered by zone index (1-based in the URI). Used by the
     * bench agent to detect W6 (heat / comfort) directly from the simulator
     * instead of fingerprinting it from action effects.
     *
     * Returns an empty array if the simulator does not publish Z<n>Temp keys
     * (the legacy 2-zone simulator on port 1881).
     *
     * @param zoneTemperatures Output: Object[] of Double, one per zone, in
     *                         ascending zone-index order.
     */
    @OPERATION
    public void readZoneTemperatures(OpFeedbackParam<Object[]> zoneTemperatures) {
        try {
            Map<String, Object> status = fetchRawStatus();
            Pattern tempPattern = Pattern.compile(".+#Z(\\d+)Temp$");
            TreeMap<Integer, Double> tempMap = new TreeMap<>();
            for (Map.Entry<String, Object> entry : status.entrySet()) {
                Matcher m = tempPattern.matcher(entry.getKey());
                if (m.matches() && entry.getValue() instanceof Double) {
                    tempMap.put(Integer.parseInt(m.group(1)), (Double) entry.getValue());
                }
            }
            zoneTemperatures.set(tempMap.values().toArray());
        } catch (IOException e) {
            LOGGER.warning("readZoneTemperatures failed: " + e.getMessage());
            zoneTemperatures.set(new Object[0]);
        }
    }

    /**
     * Reset the simulator to a random initial state for a new Q-learning episode.
     * Delegates to the shared doReset() helper.
     */
    @OPERATION
    public void resetLab() {
        doReset();
    }

    /**
     * Pin the simulator to a deterministic state for benchmark scenarios.
     * Posts to the /setState endpoint (must be present in the Node-RED flow).
     * Also resets TotalEnergyCost to 0 on the simulator side.
     *
     * <p>Legacy 2-zone signature retained for backwards compatibility with the
     * old "custom" lab scenario files. New 4-zone callers should populate the
     * {@link #setLabStateFromMap(Object[], Object[])} variant instead, which
     * accepts arbitrary key/value pairs and forwards them verbatim.
     *
     * @param stateValues Object[8]: [Z1Level(lux), Z2Level(lux), Z1Light(bool),
     *                    Z2Light(bool), Z1Blinds(bool), Z2Blinds(bool),
     *                    Spotlight(bool), Sunshine(lux)]
     */
    @OPERATION
    public void setLabState(Object[] stateValues) {
        if (stateValues == null || stateValues.length < 8) {
            LOGGER.warning("setLabState: expected 8 elements, got "
                          + (stateValues == null ? 0 : stateValues.length) + " — skipping");
            return;
        }
        Object[] keys = {"Z1Level","Z2Level","Z1Light","Z2Light",
                          "Z1Blinds","Z2Blinds","Spotlight","Sunshine"};
        Object[] values = new Object[8];
        System.arraycopy(stateValues, 0, values, 0, 8);
        setLabStateFromMap(keys, values);
    }

    /**
     * Generic /setState dispatcher. Builds a JSON body from the parallel
     * {@code keys[]} / {@code values[]} arrays and POSTs it to the simulator.
     * Numeric values are emitted as JSON numbers, booleans as JSON booleans,
     * everything else is stringified.  Ideal for 4-zone lab profiles whose
     * scenario files carry a variable set of fields (Z1..Z4 levels/lights/
     * blinds, Spotlight, SpotlightCD, CorridorLight, Sunshine).
     */
    @OPERATION
    public void setLabStateFromMap(Object[] keys, Object[] values) {
        if (validator != null) {
            try {
                validator.validateStateMap(keys, values);
            } catch (WotInputValidator.ValidationException ve) {
                LOGGER.warning("setLabStateFromMap rejected: " + ve.getMessage());
                failed("invalid_input", ve.actuator, ve.expected, ve.actual);
                return;
            }
        }
        String setStateUrl = deriveSimulatorUrl("/setState");
        if (setStateUrl == null) {
            LOGGER.warning("setLabStateFromMap: could not derive setState URL — skipping");
            return;
        }
        String body = jsonObjectFromKV(keys, values);
        postSetState(setStateUrl, body);
    }

    /** Build a JSON object string from parallel keys/values arrays. */
    private String jsonObjectFromKV(Object[] keys, Object[] values) {
        StringBuilder sb = new StringBuilder("{");
        int len = Math.min(keys == null ? 0 : keys.length,
                           values == null ? 0 : values.length);
        boolean first = true;
        for (int i = 0; i < len; i++) {
            if (keys[i] == null) continue;
            String k = String.valueOf(keys[i]);
            Object v = values[i];
            if (v == null) continue;
            if (!first) sb.append(",");
            sb.append("\"").append(k).append("\":");
            if (v instanceof Boolean) {
                sb.append(((Boolean) v) ? "true" : "false");
            } else if (v instanceof Number) {
                sb.append(v.toString());
            } else {
                sb.append("\"").append(String.valueOf(v).replace("\"","\\\"")).append("\"");
            }
            first = false;
        }
        sb.append("}");
        return sb.toString();
    }

    /** Internal POST helper for /setState. */
    private void postSetState(String setStateUrl, String body) {
        if (dryRun) {
            LOGGER.info("postSetState[dry-run]: would POST " + setStateUrl + " body=" + body);
            return;
        }
        try {
            SimulatorHttpClient.Result r = simHttp.postJson(setStateUrl, body);
            LOGGER.info("setLabState: POST " + setStateUrl + " → " + r.code + " body=" + body);
            if (r.code >= 400) {
                LOGGER.warning("setLabState: simulator returned HTTP " + r.code + " body=" + r.body);
            }
        } catch (SimulatorHttpClient.SimulatorUnreachableException e) {
            LOGGER.severe("postSetState: " + e.getMessage());
            failed("simulator_unreachable", "setState", setStateUrl);
        } catch (IOException e) {
            LOGGER.warning("setLabState: POST failed: " + e.getMessage());
        }
    }

    /**
     * Extract all data fields from a scenario JSON object (skipping the meta
     * keys "id", "description", "comment"). Boolean and number primitives are
     * preserved as Java {@link Boolean} / {@link Double}; everything else is
     * stringified.  Used by {@link #setRandomLabState} and
     * {@link #setScenarioLabState} to support arbitrary 4-zone field sets
     * without hard-coding a fixed 8-element ordering.
     */
    private void extractScenarioKV(com.google.gson.JsonObject obj,
                                   List<String> keysOut,
                                   List<Object> valuesOut) {
        for (Map.Entry<String, com.google.gson.JsonElement> e : obj.entrySet()) {
            String k = e.getKey();
            if ("id".equals(k) || "description".equals(k) || "comment".equals(k)) continue;
            com.google.gson.JsonElement val = e.getValue();
            if (val == null || val.isJsonNull()) continue;
            if (val.isJsonPrimitive()) {
                com.google.gson.JsonPrimitive p = val.getAsJsonPrimitive();
                if (p.isBoolean()) {
                    keysOut.add(k);
                    valuesOut.add(p.getAsBoolean());
                } else if (p.isNumber()) {
                    keysOut.add(k);
                    valuesOut.add(p.getAsDouble());
                } else {
                    keysOut.add(k);
                    valuesOut.add(p.getAsString());
                }
            }
        }
    }

    /**
     * Pick a random scenario from benchmark/train_scenarios.json and pin the simulator
     * to that state via setLabState. Used during QL training to expose the agent
     * to diverse starting conditions across all sunshine ranks and zone configurations.
     * Uses a separate training set to prevent train/test contamination with the
     * benchmark/scenarios.json test set.
     */
    @OPERATION
    public void setRandomLabState() {
        try (java.io.FileReader fr = new java.io.FileReader("benchmark/train_scenarios.json")) {
            com.google.gson.JsonArray arr = com.google.gson.JsonParser.parseReader(fr).getAsJsonArray();
            // Collect only objects that have an "id" field (skip comment-only entries)
            List<com.google.gson.JsonObject> scenarios = new ArrayList<>();
            for (com.google.gson.JsonElement el : arr) {
                if (el.isJsonObject() && el.getAsJsonObject().has("id")) {
                    scenarios.add(el.getAsJsonObject());
                }
            }
            if (scenarios.isEmpty()) {
                LOGGER.warning("setRandomLabState: no scenarios found in benchmark/train_scenarios.json — falling back to resetLab");
                doReset();
                return;
            }
            int idx = (int)(Math.random() * scenarios.size());
            com.google.gson.JsonObject s = scenarios.get(idx);
            List<String> keys = new ArrayList<>();
            List<Object> vals = new ArrayList<>();
            extractScenarioKV(s, keys, vals);
            setLabStateFromMap(keys.toArray(new Object[0]), vals.toArray(new Object[0]));
            LOGGER.info("setRandomLabState: scenario " + s.get("id").getAsInt()
                        + " — " + (s.has("description") ? s.get("description").getAsString() : ""));
        } catch (IOException e) {
            LOGGER.warning("setRandomLabState: failed to read train_scenarios.json — " + e.getMessage() + " — falling back to resetLab");
            doReset();
        }
    }

    /**
     * Set the lab to a specific scenario from a JSON file, identified by its numeric ID.
     * Useful for full-scenario training ablation where the agent cycles through a fixed
     * set of scenarios deterministically.
     *
     * @param scenarioFile  Path to the scenario JSON file (e.g. "benchmark/train_scenarios_full.json").
     * @param scenarioId    The integer "id" field of the scenario to load.
     */
    @OPERATION
    public void setScenarioLabState(String scenarioFile, int scenarioId) {
        try (java.io.FileReader fr = new java.io.FileReader(scenarioFile)) {
            com.google.gson.JsonArray arr = com.google.gson.JsonParser.parseReader(fr).getAsJsonArray();
            com.google.gson.JsonObject found = null;
            for (com.google.gson.JsonElement el : arr) {
                if (el.isJsonObject()) {
                    com.google.gson.JsonObject obj = el.getAsJsonObject();
                    if (obj.has("id") && obj.get("id").getAsInt() == scenarioId) {
                        found = obj;
                        break;
                    }
                }
            }
            if (found == null) {
                LOGGER.warning("setScenarioLabState: scenario id=" + scenarioId
                              + " not found in " + scenarioFile + " — falling back to resetLab");
                doReset();
                return;
            }
            List<String> keys = new ArrayList<>();
            List<Object> vals = new ArrayList<>();
            extractScenarioKV(found, keys, vals);
            setLabStateFromMap(keys.toArray(new Object[0]), vals.toArray(new Object[0]));
            LOGGER.info("setScenarioLabState: loaded scenario " + scenarioId
                       + " — " + (found.has("description") ? found.get("description").getAsString() : ""));
        } catch (IOException e) {
            LOGGER.warning("setScenarioLabState: failed to read " + scenarioFile
                          + " — " + e.getMessage() + " — falling back to resetLab");
            doReset();
        }
    }

    /**
     * Enumerate all scenario IDs in the given scenario JSON file (in file order).
     * Returns an empty array if the file is missing or contains no scenarios.
     * Used by the bench agent to dynamically build its run list per profile.
     *
     * @param scenarioFile Path to the scenario JSON file.
     * @param ids          Output: Object[] of Integer scenario ids.
     */
    @OPERATION
    public void getScenarioIds(String scenarioFile, OpFeedbackParam<Object[]> ids) {
        List<Integer> result = new ArrayList<>();
        try (java.io.FileReader fr = new java.io.FileReader(scenarioFile)) {
            com.google.gson.JsonArray arr = com.google.gson.JsonParser.parseReader(fr).getAsJsonArray();
            for (com.google.gson.JsonElement el : arr) {
                if (el.isJsonObject() && el.getAsJsonObject().has("id")) {
                    result.add(el.getAsJsonObject().get("id").getAsInt());
                }
            }
        } catch (IOException e) {
            LOGGER.warning("getScenarioIds: failed to read " + scenarioFile + " — " + e.getMessage());
        }
        ids.set(result.toArray());
        LOGGER.info("getScenarioIds(" + scenarioFile + "): " + result.size() + " scenarios");
    }

    /**
     * Read the cumulative energy cost accrued since the last reset/setState.
     *
     * @param totalCost Output: cumulative energy cost as a double.
     */
    @OPERATION
    public void readEnergyCost(OpFeedbackParam<Double> totalCost) {
        try {
            Map<String, Object> status = fetchRawStatus();
            Object v = status.get("http://example.org/was#TotalEnergyCost");
            double cost = (v instanceof Double) ? (Double) v : 0.0;
            totalCost.set(cost);
            LOGGER.info("readEnergyCost: TotalEnergyCost=" + cost);
        } catch (IOException e) {
            LOGGER.warning("readEnergyCost: failed: " + e.getMessage());
            totalCost.set(0.0);
        }
    }

    /**
     * Derive a simulator URL by replacing the path suffix of the action endpoint.
     * Handles both http:// and classpath: TD sources. Returns null if the URL
     * cannot be determined.
     */
    private String deriveSimulatorUrl(String path) {
        Optional<ActionAffordance> anyAction = this.td.getFirstActionBySemanticType(
                "http://example.org/was#SetZ1Light");
        if (anyAction.isPresent()) {
            Optional<Form> f = anyAction.get().getFirstFormForOperationType(TD.invokeAction);
            if (f.isPresent()) {
                return f.get().getTarget().replaceAll("/action$", path);
            }
        }
        return null;
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
        if (validator != null) {
            try {
                validator.validateAction(wotSemanticType, Boolean.valueOf(value));
            } catch (WotInputValidator.ValidationException ve) {
                LOGGER.warning("invokeAction rejected: " + ve.getMessage());
                failed("invalid_input", ve.actuator, ve.expected, ve.actual);
                return;
            }
        }
        if (dryRun) {
            LOGGER.info("invokeAction[dry-run]: " + wotSemanticType + " = " + value + " (no HTTP)");
            return;
        }
        LOGGER.info("invokeAction: " + wotSemanticType + " = " + value);
        performBooleanAction(wotSemanticType, value);
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

    private double[] toDoubleArray(Object[] arr) { return Converters.toDoubleArray(arr); }

    private int discretize(double value, double[] bounds) {
        if (value < bounds[0]) return 0;
        if (value < bounds[1]) return 1;
        if (value < bounds[2]) return 2;
        return 3;
    }
}
