package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

/**
 * The effective-knob report is the treatment-delivery evidence the runner
 * copies into TRAINING_OK.json (audit AUD-001). It must be parseable JSON
 * and must reflect the values actually in force, not the requested ones.
 */
class StereotypeEffectivePropsTest {

    @AfterEach
    void resetKnobs() {
        StereotypeReasoner.setIrrelevantDvPriorForTest(0.0);
        StereotypeReasoner.setBandMirrorInitForTest(0.0);
        StereotypeReasoner.setBandMirrorPriorForTest(0.0);
    }

    private static JsonObject parse() {
        return JsonParser.parseString(StereotypeReasoner.effectivePropsJson()).getAsJsonObject();
    }

    @Test
    void reportsDefaultsAsOff() {
        JsonObject json = parse();
        assertEquals(0.0, json.get("stereo.irrelevantDvPrior").getAsDouble(), 0.0);
        assertEquals(0.0, json.get("stereo.bandMirrorInit").getAsDouble(), 0.0);
        assertEquals(0.0, json.get("stereo.bandMirrorPrior").getAsDouble(), 0.0);
        assertTrue(json.has("stereo.redundancyOnly"));
    }

    @Test
    void reportsValuesInForce() {
        StereotypeReasoner.setIrrelevantDvPriorForTest(2.0);
        StereotypeReasoner.setBandMirrorInitForTest(5.0);
        StereotypeReasoner.setBandMirrorPriorForTest(2.0);
        JsonObject json = parse();
        assertEquals(2.0, json.get("stereo.irrelevantDvPrior").getAsDouble(), 0.0);
        assertEquals(5.0, json.get("stereo.bandMirrorInit").getAsDouble(), 0.0);
        assertEquals(2.0, json.get("stereo.bandMirrorPrior").getAsDouble(), 0.0);
    }

    @Test
    void markerIsStable() {
        assertEquals("STEREO_EFFECTIVE_PROPS", StereotypeReasoner.EFFECTIVE_PROPS_MARKER);
    }
}
