package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * Phase 4 regression gate. Loads the two NEW self-contained lab ontologies
 * (building_4_smartplug.ttl and building_5_energy.ttl) through the production
 * {@link StereotypeReasoner.ClasspathOntologyLoader} and asserts that the two
 * additive discovery features introduced for Phase 4 work end-to-end:
 *
 * <ul>
 *   <li><b>lab4 smart-plug power gate</b> — the Z1 ceiling lamp's ON action is
 *       bound (via ws:powerGates) to the plug's state-vector slot as an
 *       independent variable with ivMinRank=1, reusing the generic IV
 *       machinery. The plug's own ON action stays IV-free (it is the enabler).</li>
 *   <li><b>lab5 energy cost</b> — ws:energyCost is parsed onto each actuator's
 *       ON action (efficient lamp = 1, inefficient lamp = 4, spotlight = 2).</li>
 * </ul>
 *
 * Because these ontologies are self-contained (loaded WITHOUT lab-ontology.ttl
 * or wot-mappings.ttl), this test doubles as a Turtle-syntax + slot-registry
 * smoke test for both files: a malformed triple or a missing ws:stateVecIndex
 * fails the build here rather than in a benchmark run.
 */
class Phase4KgDiscoveryTest {

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

    // ------------------------------------------------------------------ lab4

    @Test
    void lab4SmartPlugGatesTheZ1Lamp() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_4_smartplug.ttl" }),
            0.75);

        // The gated lamp (Z1 ceiling light) must now be IV-gated on the plug
        // slot. PlugZ1 is declared at ws:stateVecIndex 7 in §10 of the KG.
        StereotypeReasoner.ActionInfo lampOn = findOnAction(reasoner, "SetZ1Light");
        assertNotNull(lampOn, "Z1 lamp ON action must be discovered");
        assertTrue(lampOn.hasIV,
            "Z1 lamp ON must be IV-gated by the smart plug (ws:powerGates)");
        assertEquals(7, lampOn.ivStateVecIndex,
            "Z1 lamp ON must be gated on the PlugZ1 slot (stateVecIndex 7)");
        assertEquals(1, lampOn.ivMinRank,
            "Power-gate ivMinRank must be 1 (plug ON enables the lamp)");

        // The plug's own ON action is the ENABLER: it must NOT be IV-gated,
        // so it can receive the unconditional constructive bonus.
        StereotypeReasoner.ActionInfo plugOn = findOnAction(reasoner, "SetPlugZ1");
        assertNotNull(plugOn, "Smart-plug ON action must be discovered");
        assertTrue(!plugOn.hasIV,
            "Smart-plug ON must NOT be IV-gated (it is the enabler)");

        // lab4 declares no ws:energyCost — the energy prior must stay inert.
        assertEquals(0.0, lampOn.energyCost, 1e-9,
            "lab4 actuators must carry no energyCost (energy prior inert)");
    }

    // -------------------------------------------------------------- lab4dual

    @Test
    void lab4dualGatesBothLampsOnTheirOwnPlugs() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_8_dualplug.ttl" }),
            0.75);

        // BOTH lamps must be IV-gated, each on ITS OWN plug slot.
        // §10 of building_8_dualplug.ttl: PlugZ1 = slot 7, PlugZ2 = slot 8.
        StereotypeReasoner.ActionInfo lamp1On = findOnAction(reasoner, "SetZ1Light");
        assertNotNull(lamp1On, "Z1 lamp ON action must be discovered");
        assertTrue(lamp1On.hasIV,
            "Z1 lamp ON must be IV-gated by SmartPlug_Z1 (ws:powerGates)");
        assertEquals(7, lamp1On.ivStateVecIndex,
            "Z1 lamp ON must be gated on the PlugZ1 slot (stateVecIndex 7)");
        assertEquals(1, lamp1On.ivMinRank,
            "Power-gate ivMinRank must be 1 (plug ON enables the lamp)");

        StereotypeReasoner.ActionInfo lamp2On = findOnAction(reasoner, "SetZ2Light");
        assertNotNull(lamp2On, "Z2 lamp ON action must be discovered");
        assertTrue(lamp2On.hasIV,
            "Z2 lamp ON must be IV-gated by SmartPlug_Z2 (ws:powerGates)");
        assertEquals(8, lamp2On.ivStateVecIndex,
            "Z2 lamp ON must be gated on the PlugZ2 slot (stateVecIndex 8)");
        assertEquals(1, lamp2On.ivMinRank,
            "Power-gate ivMinRank must be 1 (plug ON enables the lamp)");

        // Both plugs are ENABLERS: neither ON action may be IV-gated.
        StereotypeReasoner.ActionInfo plug1On = findOnAction(reasoner, "SetPlugZ1");
        StereotypeReasoner.ActionInfo plug2On = findOnAction(reasoner, "SetPlugZ2");
        assertNotNull(plug1On, "SmartPlug_Z1 ON action must be discovered");
        assertNotNull(plug2On, "SmartPlug_Z2 ON action must be discovered");
        assertTrue(!plug1On.hasIV,
            "SmartPlug_Z1 ON must NOT be IV-gated (it is an enabler)");
        assertTrue(!plug2On.hasIV,
            "SmartPlug_Z2 ON must NOT be IV-gated (it is an enabler)");

        // lab4dual declares no ws:energyCost — the energy prior must stay inert.
        assertEquals(0.0, lamp1On.energyCost, 1e-9,
            "lab4dual actuators must carry no energyCost (energy prior inert)");
    }

    // ------------------------------------------------------------- lab4chain

    @Test
    void lab4chainAppliesTheTwoLevelPowerChain() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_9_chainplug.ttl" }),
            0.75);

        // Level 2 of the chain: the Z1 lamp's ON action is gated on the PLUG
        // slot. §10 of building_9_chainplug.ttl: PlugZ1 = slot 7.
        StereotypeReasoner.ActionInfo lampOn = findOnAction(reasoner, "SetZ1Light");
        assertNotNull(lampOn, "Z1 lamp ON action must be discovered");
        assertTrue(lampOn.hasIV,
            "Z1 lamp ON must be IV-gated by SmartPlug_Z1 (ws:powerGates level 2)");
        assertEquals(7, lampOn.ivStateVecIndex,
            "Z1 lamp ON must be gated on the PlugZ1 slot (stateVecIndex 7)");
        assertEquals(1, lampOn.ivMinRank,
            "Power-gate ivMinRank must be 1 (plug ON enables the lamp)");

        // Level 1 of the chain: the PLUG's ON action is itself gated on the
        // BREAKER slot. §10: MasterSwitch = slot 8. This is what makes the
        // dependency a CHAIN rather than two parallel gates.
        StereotypeReasoner.ActionInfo plugOn = findOnAction(reasoner, "SetPlugZ1");
        assertNotNull(plugOn, "SmartPlug_Z1 ON action must be discovered");
        assertTrue(plugOn.hasIV,
            "SmartPlug_Z1 ON must be IV-gated by MasterSwitch (ws:powerGates level 1)");
        assertEquals(8, plugOn.ivStateVecIndex,
            "SmartPlug_Z1 ON must be gated on the MasterSwitch slot (stateVecIndex 8)");
        assertEquals(1, plugOn.ivMinRank,
            "Power-gate ivMinRank must be 1 (breaker ON enables the plug)");

        // The breaker is the chain ROOT enabler: its ON action must NOT be
        // IV-gated, so it receives the unconditional constructive bonus and
        // the KG-primed agent learns the order breaker -> plug -> lamp.
        StereotypeReasoner.ActionInfo masterOn = findOnAction(reasoner, "SetMasterSwitch");
        assertNotNull(masterOn, "MasterSwitch ON action must be discovered");
        assertTrue(!masterOn.hasIV,
            "MasterSwitch ON must NOT be IV-gated (it is the chain root enabler)");

        // The Z2 lamp is OUTSIDE the chain — directly actionable, no IV.
        StereotypeReasoner.ActionInfo lamp2On = findOnAction(reasoner, "SetZ2Light");
        assertNotNull(lamp2On, "Z2 lamp ON action must be discovered");
        assertTrue(!lamp2On.hasIV,
            "Z2 lamp ON must NOT be IV-gated (it is outside the chain)");

        // lab4chain declares no ws:energyCost — the energy prior must stay inert.
        assertEquals(0.0, lampOn.energyCost, 1e-9,
            "lab4chain actuators must carry no energyCost (energy prior inert)");
    }

    // ------------------------------------------------------------------ lab5

    @Test
    void lab5ParsesPerActuatorEnergyCost() {
        StereotypeReasoner reasoner = new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(
                new String[] { "building_5_energy.ttl" }),
            0.75);

        StereotypeReasoner.ActionInfo effOn = findOnAction(reasoner, "SetZ1Eff");
        StereotypeReasoner.ActionInfo ineffOn = findOnAction(reasoner, "SetZ1Ineff");
        StereotypeReasoner.ActionInfo spotOn = findOnAction(reasoner, "SetSpotlight");
        assertNotNull(effOn, "Z1 efficient lamp ON action must be discovered");
        assertNotNull(ineffOn, "Z1 inefficient lamp ON action must be discovered");
        assertNotNull(spotOn, "Spotlight ON action must be discovered");

        assertEquals(1.0, effOn.energyCost, 1e-9,
            "Efficient lamp must carry ws:energyCost 1");
        assertEquals(4.0, ineffOn.energyCost, 1e-9,
            "Inefficient lamp must carry ws:energyCost 4");
        assertEquals(2.0, spotOn.energyCost, 1e-9,
            "Spotlight must carry ws:energyCost 2");

        // The two lamps are optically identical (same +400 lux) but differ ONLY
        // in energy — exactly the contrast the energy prior must exploit.
        assertTrue(ineffOn.energyCost > effOn.energyCost,
            "Inefficient lamp must cost strictly more than the efficient lamp");
    }
}
