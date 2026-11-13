package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;

import tools.StereotypeReasoner.ActionInfo;
import tools.StereotypeReasoner.KnowledgeLayer;

/**
 * What each knowledge layer delivers on the Phase-4 labs (knowledge-ladder
 * control arms {@code phase4_v2_redundancy_only} and
 * {@code phase4_v2_brick_only}, THESIS_STATE_REPORT.md Addendum 2026-11-13b).
 *
 * <ol>
 *   <li>All three layers make the same structural claims on lab4, lab4dual,
 *       lab4chain, and lab5: action keys, labels, state bits, affected zones,
 *       KG-silent flags. A difference between two arms is therefore not a
 *       difference in "which actuator influences which zone".</li>
 *   <li>Only the FULL layer reads {@code ws:powerGates}: the gated lamp (and,
 *       in lab4chain, the gated plug) is bound to its upstream switch. BRICK
 *       and REDUNDANCY bind no power gate.</li>
 *   <li>BRICK binds no independent variable at all and reads no
 *       {@code ws:energyCost}. REDUNDANCY still reads the cost through the
 *       full enrichment query, which is why that arm is not run on lab5.</li>
 *   <li>The initial Q-value of "lamp ON while its plug is OFF" is the Rule-2
 *       well under FULL, the Rule-5 bonus under BRICK, and zero under
 *       REDUNDANCY; the Rule-1 redundancy well is the same in all three.</li>
 * </ol>
 */
class Phase4KnowledgeLadderLayerTest {

    private static final Map<String, String[]> LABS = new LinkedHashMap<>();
    static {
        LABS.put("lab4",      new String[] { "building_4_smartplug.ttl" });
        LABS.put("lab4dual",  new String[] { "building_8_dualplug.ttl" });
        LABS.put("lab4chain", new String[] { "building_9_chainplug.ttl" });
        LABS.put("lab5",      new String[] { "building_5_energy.ttl" });
    }

    private static final double SCALE = 0.5;  // stereo.initPenaltyScale default
    private static final double BONUS = 15.0; // stereo.initBonus default

    private static StereotypeReasoner build(String[] onts, KnowledgeLayer layer) {
        return new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(onts), 0.75, layer);
    }

    private static String key(ActionInfo ai) {
        return ai.wotActionType == null ? "DO_NOTHING"
             : ai.wotActionType + "|" + (ai.wotValue ? "ON" : "OFF");
    }

    private static Map<String, ActionInfo> byKey(StereotypeReasoner r) {
        Map<String, ActionInfo> m = new HashMap<>();
        for (ActionInfo ai : r.getAllActions()) m.put(key(ai), ai);
        return m;
    }

    private static ActionInfo on(StereotypeReasoner r, String fragment) {
        for (ActionInfo ai : r.getAllActions()) {
            if (ai.wotActionType != null && ai.wotActionType.endsWith("#" + fragment) && ai.wotValue) return ai;
        }
        return null;
    }

    // ------------------------------------------------------------ invariant 1

    @Test
    void allLayersMakeTheSameStructuralClaimsOnThePhase4Labs() {
        for (Map.Entry<String, String[]> lab : LABS.entrySet()) {
            StereotypeReasoner full = build(lab.getValue(), KnowledgeLayer.FULL);
            Map<String, ActionInfo> f = byKey(full);
            for (KnowledgeLayer layer : new KnowledgeLayer[] { KnowledgeLayer.BRICK, KnowledgeLayer.REDUNDANCY }) {
                StereotypeReasoner other = build(lab.getValue(), layer);
                String where = lab.getKey() + "[" + layer + "]";
                assertEquals(layer, other.getKnowledgeLayer(), where);
                assertEquals(full.getNumActions(), other.getNumActions(), where + ": action count");
                int[] fd = full.getStateDomainSizes(), od = other.getStateDomainSizes();
                assertEquals(fd.length, od.length, where + ": slot count");
                for (int i = 0; i < fd.length; i++) assertEquals(fd[i], od[i], where + ": slot " + i);

                Map<String, ActionInfo> o = byKey(other);
                assertEquals(f.keySet(), o.keySet(), where + ": action key set");
                for (String k : f.keySet()) {
                    ActionInfo fa = f.get(k), oa = o.get(k);
                    assertEquals(fa.label,            oa.label,            where + " " + k + ": label");
                    assertEquals(fa.wotStateType,     oa.wotStateType,     where + " " + k + ": wotStateType");
                    assertEquals(fa.stateVecBitIndex, oa.stateVecBitIndex, where + " " + k + ": svBit");
                    assertEquals(fa.expectedBitValue, oa.expectedBitValue, where + " " + k + ": expectedBit");
                    assertEquals(fa.affectedZones,    oa.affectedZones,    where + " " + k + ": affectedZones");
                    assertEquals(fa.kgSilent,         oa.kgSilent,         where + " " + k + ": kgSilent");
                }
            }
        }
    }

    // ------------------------------------------------------------ invariant 2

    @Test
    void onlyTheFullLayerBindsPowerGates() {
        // lab4: Z1 lamp gated on the Z1 plug.
        StereotypeReasoner lab4 = build(LABS.get("lab4"), KnowledgeLayer.FULL);
        assertGatedOn(lab4, "SetZ1Light", "SetPlugZ1", "lab4");
        assertFalse(on(lab4, "SetZ2Light").hasIV, "lab4: the Z2 lamp has no plug");

        // lab4dual: each lamp gated on its own plug.
        StereotypeReasoner dual = build(LABS.get("lab4dual"), KnowledgeLayer.FULL);
        assertGatedOn(dual, "SetZ1Light", "SetPlugZ1", "lab4dual");
        assertGatedOn(dual, "SetZ2Light", "SetPlugZ2", "lab4dual");

        // lab4chain: lamp gated on the plug, plug gated on the master switch.
        StereotypeReasoner chain = build(LABS.get("lab4chain"), KnowledgeLayer.FULL);
        assertGatedOn(chain, "SetZ1Light", "SetPlugZ1", "lab4chain");
        assertGatedOn(chain, "SetPlugZ1", "SetMasterSwitch", "lab4chain");

        for (String name : new String[] { "lab4", "lab4dual", "lab4chain" }) {
            for (KnowledgeLayer layer : new KnowledgeLayer[] { KnowledgeLayer.BRICK, KnowledgeLayer.REDUNDANCY }) {
                StereotypeReasoner r = build(LABS.get(name), layer);
                for (String gated : new String[] { "SetZ1Light", "SetZ2Light", "SetPlugZ1" }) {
                    ActionInfo ai = on(r, gated);
                    assertNotNull(ai, name + ": " + gated);
                    assertFalse(ai.hasIV, name + "[" + layer + "] " + gated + ": no power gate may be bound");
                }
            }
        }
    }

    private static void assertGatedOn(StereotypeReasoner r, String gated, String gate, String lab) {
        ActionInfo g = on(r, gated), up = on(r, gate);
        assertNotNull(g, lab + ": " + gated);
        assertNotNull(up, lab + ": " + gate);
        assertTrue(g.hasIV, lab + ": FULL must gate " + gated + " on " + gate);
        assertEquals(up.stateVecBitIndex, g.ivStateVecIndex, lab + ": " + gated + " gate slot");
    }

    // ------------------------------------------------------------ invariant 3

    @Test
    void brickLayerBindsNoIndependentVariableAndReadsNoCost() {
        for (Map.Entry<String, String[]> lab : LABS.entrySet()) {
            StereotypeReasoner brick = build(lab.getValue(), KnowledgeLayer.BRICK);
            for (ActionInfo ai : brick.getAllActions()) {
                String where = lab.getKey() + " " + key(ai);
                assertFalse(ai.hasIV, where + ": BRICK must not bind an IV");
                assertEquals(-1, ai.ivStateVecIndex, where + ": ivStateVecIndex");
                assertTrue(ai.ivGates.isEmpty(), where + ": ivGates");
                assertEquals(0.0, ai.energyCost, 1e-12, where + ": energyCost");
            }
        }
    }

    @Test
    void lab5CostAnnotationReachesFullAndRedundancyButNotBrick() {
        String[] onts = LABS.get("lab5");
        for (KnowledgeLayer layer : new KnowledgeLayer[] { KnowledgeLayer.FULL, KnowledgeLayer.REDUNDANCY }) {
            StereotypeReasoner r = build(onts, layer);
            assertEquals(1.0, on(r, "SetZ1Eff").energyCost,     1e-12, layer + ": efficient lamp cost");
            assertEquals(4.0, on(r, "SetZ1Ineff").energyCost,   1e-12, layer + ": inefficient lamp cost");
            assertEquals(2.0, on(r, "SetSpotlight").energyCost, 1e-12, layer + ": spotlight cost");
            assertEquals(0.0, on(r, "SetZ1Blinds").energyCost,  1e-12, layer + ": blind cost");
        }
        StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
        assertEquals(0.0, on(brick, "SetZ1Ineff").energyCost, 1e-12, "BRICK: no cost annotation");
    }

    // ------------------------------------------------------------ invariant 4

    @Test
    void lab4InitialQValueOfTheGatedLampDiffersByLayerOnlyThroughTheGate() {
        String[] onts = LABS.get("lab4");
        int[] goal = { 3, 3 };
        StereotypeReasoner full  = build(onts, KnowledgeLayer.FULL);
        StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
        StereotypeReasoner red   = build(onts, KnowledgeLayer.REDUNDANCY);

        // All-off state: levels 0, every actuator off (plug off), sun rank 0.
        int[] off = new int[full.getStateDomainSizes().length];
        ActionInfo lampF = on(full, "SetZ1Light"), lampB = on(brick, "SetZ1Light"), lampR = on(red, "SetZ1Light");

        assertEquals(-100.0 * SCALE, full.getInitPenaltyForZone(off, lampF.actionIndex, 0, goal), 1e-9,
            "FULL: Rule 2 well on the gated lamp while its plug is off");
        assertEquals(BONUS * 3 * SCALE, brick.getInitPenaltyForZone(off, lampB.actionIndex, 0, goal), 1e-9,
            "BRICK: Rule 5 bonus on the lamp even though its plug is off");
        assertEquals(0.0, red.getInitPenaltyForZone(off, lampR.actionIndex, 0, goal), 1e-9,
            "REDUNDANCY: no rule fires on a non-redundant action");

        // Plug on: the gate is satisfied, FULL now gives the same bonus as BRICK.
        int[] plugOn = off.clone();
        plugOn[on(full, "SetPlugZ1").stateVecBitIndex] = 1;
        assertEquals(BONUS * 3 * SCALE, full.getInitPenaltyForZone(plugOn, lampF.actionIndex, 0, goal), 1e-9,
            "FULL: Rule 5 bonus once the plug is on");
        assertEquals(BONUS * 3 * SCALE, brick.getInitPenaltyForZone(plugOn, lampB.actionIndex, 0, goal), 1e-9);

        // Lamp already on: Rule 1 redundancy well, identical in all three layers.
        int[] lampOn = plugOn.clone();
        lampOn[lampF.stateVecBitIndex] = 1;
        assertEquals(-100.0 * SCALE, full.getInitPenaltyForZone(lampOn, lampF.actionIndex, 0, goal), 1e-9);
        assertEquals(-100.0 * SCALE, brick.getInitPenaltyForZone(lampOn, lampB.actionIndex, 0, goal), 1e-9);
        assertEquals(-100.0 * SCALE, red.getInitPenaltyForZone(lampOn, lampR.actionIndex, 0, goal), 1e-9);
    }
}
