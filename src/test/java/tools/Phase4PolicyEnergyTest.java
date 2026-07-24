package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

/**
 * Config-driven policy-energy weights for Phase-4 protocol v2.
 *
 * The Phase-1 default (no overrides) must stay byte-identical — the archived
 * corrected Phase-1 results depend on it. The phase4_v2 override list must
 * weight the lab5 efficient/inefficient lamps 1/4 (mirroring ws:energyCost)
 * and keep plugs/breakers/blinds passive.
 */
class Phase4PolicyEnergyTest {

    private static final String PHASE4_SPEC =
            "ineff:4,eff:1,spotlight:2,plug:0,masterswitch:0,light:1,blind:0";

    @Test
    void defaultRuleIsUnchangedWithoutOverrides() {
        Object[] keys = {"was#Z1Light", "was#Spotlight", "was#Z1Blinds",
                         "was#Z1Eff", "was#Z1Ineff", "was#PlugZ1"};
        Object[] on = {true, true, true, true, true, true};
        // Legacy rule: light=1, spotlight=2, everything else 0.
        assertEquals(3.0,
                Phase1PolicyEnergy.instantaneousCost(keys, on, List.of()), 1e-12);
    }

    @Test
    void phase4WeightsCoverLab5AndDependencyActuators() {
        List<Map.Entry<String, Double>> weights =
                Phase1PolicyEnergy.parseWeights(PHASE4_SPEC);
        Object[] keys = {"was#Z1Eff", "was#Z1Ineff", "was#Spotlight",
                         "was#PlugZ1", "was#MasterSwitch", "was#Z2Light",
                         "was#Z1Blinds"};
        Object[] on = {true, true, true, true, true, true, true};
        // 1 (Eff) + 4 (Ineff) + 2 (Spotlight) + 0 + 0 + 1 (Light) + 0 (Blind)
        assertEquals(8.0,
                Phase1PolicyEnergy.instantaneousCost(keys, on, weights), 1e-12);
    }

    @Test
    void orderMatters_ineffBeforeEff_spotlightBeforeLight() {
        List<Map.Entry<String, Double>> weights =
                Phase1PolicyEnergy.parseWeights(PHASE4_SPEC);
        assertEquals(4.0, Phase1PolicyEnergy.instantaneousCost(
                new Object[]{"was#Z2Ineff"}, new Object[]{true}, weights), 1e-12);
        assertEquals(1.0, Phase1PolicyEnergy.instantaneousCost(
                new Object[]{"was#Z2Eff"}, new Object[]{true}, weights), 1e-12);
        assertEquals(2.0, Phase1PolicyEnergy.instantaneousCost(
                new Object[]{"was#Spotlight"}, new Object[]{true}, weights), 1e-12);
    }

    @Test
    void inactiveActuatorsCostNothing() {
        List<Map.Entry<String, Double>> weights =
                Phase1PolicyEnergy.parseWeights(PHASE4_SPEC);
        Object[] keys = {"was#Z1Ineff", "was#Z1Eff"};
        Object[] off = {false, false};
        assertEquals(0.0, Phase1PolicyEnergy.instantaneousCost(keys, off, weights), 1e-12);
    }

    @Test
    void parserRejectsMalformedEntriesAndAcceptsEmpty() {
        assertTrue(Phase1PolicyEnergy.parseWeights("").isEmpty());
        assertTrue(Phase1PolicyEnergy.parseWeights(null).isEmpty());
        assertThrows(IllegalArgumentException.class,
                () -> Phase1PolicyEnergy.parseWeights("noweight"));
        assertThrows(IllegalArgumentException.class,
                () -> Phase1PolicyEnergy.parseWeights("token:"));
    }
}
