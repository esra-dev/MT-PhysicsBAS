package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

/**
 * Phase 2.5 regression gate for the MONITOR emergency-fallback lab. Loads the
 * new self-contained ontology {@code building_6_monitor.ttl} through the
 * production {@link StereotypeReasoner.ClasspathOntologyLoader} and asserts:
 *
 * <ul>
 *   <li>Both Causes actuators are discovered as ON/OFF pairs — the primary lamp
 *       ({@code SetZ1Light}) and the computer monitor ({@code SetZ1Monitor}).</li>
 *   <li>The monitor is a <b>Causes</b> light (unconditional positive sign):
 *       {@code hasIV == false}. Its multiple dependent variables (displayed
 *       information + luminiscence) collapse to exactly one lighting action
 *       because the discovery query keeps only the Illuminance-quantity DV.</li>
 *   <li>The reward-side cost {@code ws:rewardEnergyCost} is parsed: the monitor
 *       is costly (4) and the lamp is free (0), so both arms prefer the lamp in
 *       the clean lab.</li>
 *   <li>The state vector is length 3 ({@code [Z1Level, Z1Light, Z1Monitor]}) →
 *       16 states, and each actuator toggles a distinct bit.</li>
 * </ul>
 *
 * Because the ontology is self-contained (loaded WITHOUT lab-ontology.ttl or
 * wot-mappings.ttl), this test doubles as a Turtle-syntax + slot-registry smoke
 * test: a malformed triple or a missing ws:stateVecIndex fails the build here
 * rather than in a benchmark / CI run.
 */
class MonitorKgDiscoveryTest {

    private static StereotypeReasoner.ActionInfo findOnAction(
            StereotypeReasoner reasoner, String wotActionSubstring) {
        for (StereotypeReasoner.ActionInfo ai : reasoner.getAllActions()) {
            if (ai.wotActionType != null
                    && ai.wotActionType.contains(wotActionSubstring)
                    && ai.wotValue) {
                return ai;
            }
        }
        return null;
    }

    @Test
    void monitorLabDiscoversTwoCausesActuators() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_6_monitor.ttl" }),
            0.75);

        StereotypeReasoner.ActionInfo lampOn    = findOnAction(reasoner, "SetZ1Light");
        StereotypeReasoner.ActionInfo monitorOn = findOnAction(reasoner, "SetZ1Monitor");

        assertNotNull(lampOn,    "Primary lamp ON action must be discovered");
        assertNotNull(monitorOn, "Monitor ON action must be discovered (light side-effect)");

        // Both are Causes lights: unconditional positive sign, no IV gate.
        assertFalse(lampOn.hasIV,    "Primary lamp must be a Causes actuator (no IV)");
        assertFalse(monitorOn.hasIV, "Monitor must be a Causes actuator (light is a side-effect, no IV)");

        // No energyCost (KG prior) is declared in this lab — it uses the reward-side cost instead.
        assertEquals(0.0, monitorOn.energyCost, 1e-9,
            "labmon actuators carry no ws:energyCost (energy prior inert)");

        // Reward-side energy cost makes the monitor WASTEFUL and the lamp free,
        // so both arms prefer the primary lamp in the clean lab.
        assertEquals(4.0, monitorOn.rewardEnergyCost, 1e-9,
            "Monitor must carry ws:rewardEnergyCost 4 (wasteful to use for light)");
        assertEquals(0.0, lampOn.rewardEnergyCost, 1e-9,
            "Primary lamp must be free (ws:rewardEnergyCost 0) so it is the clean optimum");
    }

    @Test
    void monitorLabHasThreeSlotStateVectorWithDistinctBits() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_6_monitor.ttl" }),
            0.75);

        // [Z1Level, Z1Light, Z1Monitor] = 3 slots → 4*2*2 = 16 states.
        assertEquals(3, reasoner.getStateVecLength(),
            "Monitor lab state vector must have exactly 3 slots");
        int[] domains = reasoner.getStateDomainSizes();
        assertEquals(4, domains[0], "Slot 0 (Z1Level) must be a rank slot (domain 4)");
        assertEquals(2, domains[1], "Slot 1 (Z1Light) must be a boolean actuator");
        assertEquals(2, domains[2], "Slot 2 (Z1Monitor) must be a boolean actuator");

        StereotypeReasoner.ActionInfo lampOn    = findOnAction(reasoner, "SetZ1Light");
        StereotypeReasoner.ActionInfo monitorOn = findOnAction(reasoner, "SetZ1Monitor");

        // Each actuator toggles a distinct, in-range state bit.
        assertEquals(1, lampOn.stateVecBitIndex,    "Primary lamp toggles slot 1 (Z1Light)");
        assertEquals(2, monitorOn.stateVecBitIndex, "Monitor toggles slot 2 (Z1Monitor)");

        // 2 actuators × ON/OFF + DO_NOTHING = 5 actions.
        assertTrue(reasoner.getNumActions() >= 5,
            "Monitor lab must discover at least 2 actuator pairs + DO_NOTHING");
    }
}
