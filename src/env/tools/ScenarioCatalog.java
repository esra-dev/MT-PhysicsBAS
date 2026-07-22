package tools;

import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/** Strict, ordered loader for protocol-v2 training and benchmark scenarios. */
public final class ScenarioCatalog {
    private final List<Integer> orderedIds;
    private final List<JsonObject> orderedScenarios;
    private final Map<Integer, JsonObject> byId;

    private ScenarioCatalog(List<Integer> ids, List<JsonObject> scenarios,
                            Map<Integer, JsonObject> byId) {
        this.orderedIds = Collections.unmodifiableList(ids);
        this.orderedScenarios = Collections.unmodifiableList(scenarios);
        this.byId = Collections.unmodifiableMap(byId);
    }

    public static ScenarioCatalog load(Path path) throws IOException {
        return load(path, true);
    }

    /** Legacy compatibility for older catalogues that contain comment-only rows. */
    public static ScenarioCatalog loadAllowingMetadata(Path path) throws IOException {
        return load(path, false);
    }

    private static ScenarioCatalog load(Path path, boolean missingIdIsFatal) throws IOException {
        final JsonElement root;
        try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            root = JsonParser.parseReader(reader);
        } catch (RuntimeException e) {
            throw new IOException("Invalid scenario JSON: " + path + ": " + e.getMessage(), e);
        }
        if (!root.isJsonArray()) {
            throw new IOException("Scenario file must contain a JSON array: " + path);
        }

        JsonArray array = root.getAsJsonArray();
        List<Integer> ids = new ArrayList<>();
        List<JsonObject> scenarios = new ArrayList<>();
        Map<Integer, JsonObject> byId = new LinkedHashMap<>();
        for (JsonElement element : array) {
            if (!element.isJsonObject()) {
                throw new IOException("Every scenario entry must be an object: " + path);
            }
            JsonObject object = element.getAsJsonObject();
            if (!object.has("id")) {
                if (missingIdIsFatal) {
                    throw new IOException("Scenario entry is missing integer id in " + path);
                }
                continue; // legacy comment-only metadata row
            }
            final int id;
            try {
                double raw = object.get("id").getAsDouble();
                if (!Double.isFinite(raw) || raw != Math.rint(raw)
                        || raw < Integer.MIN_VALUE || raw > Integer.MAX_VALUE) {
                    throw new NumberFormatException("not an integer");
                }
                id = (int) raw;
            } catch (RuntimeException e) {
                throw new IOException("Scenario id must be an integer in " + path, e);
            }
            if (byId.containsKey(id)) {
                throw new IOException("Duplicate scenario id " + id + " in " + path);
            }
            ids.add(id);
            scenarios.add(object);
            byId.put(id, object);
        }
        if (ids.isEmpty()) {
            throw new IOException("Scenario file contains no scenarios: " + path);
        }
        return new ScenarioCatalog(ids, scenarios, byId);
    }

    public List<Integer> orderedIds() {
        return orderedIds;
    }

    public int size() {
        return orderedIds.size();
    }

    public JsonObject scenarioAt(int zeroBasedPosition) {
        if (zeroBasedPosition < 0 || zeroBasedPosition >= orderedScenarios.size()) {
            throw new IndexOutOfBoundsException("Scenario position " + zeroBasedPosition
                    + " outside [0," + (orderedScenarios.size() - 1) + "]");
        }
        return orderedScenarios.get(zeroBasedPosition);
    }

    public JsonObject scenarioById(int id) {
        JsonObject scenario = byId.get(id);
        if (scenario == null) {
            throw new IllegalArgumentException("Unknown scenario id " + id);
        }
        return scenario;
    }

    public int idAt(int zeroBasedPosition) {
        return orderedIds.get(zeroBasedPosition);
    }

    public String scheduleSha256() {
        String canonical = String.join(",", orderedIds.stream()
                .map(String::valueOf).toArray(String[]::new));
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(canonical.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(64);
            for (byte b : digest) hex.append(String.format("%02x", b));
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }
}
