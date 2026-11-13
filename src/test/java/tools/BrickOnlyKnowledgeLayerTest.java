package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import tools.StereotypeReasoner.ActionInfo;
import tools.StereotypeReasoner.CrossZoneEffect;
import tools.StereotypeReasoner.KnowledgeLayer;

/**
 * Operational proof for the Brick-only knowledge-ladder arm (registered in
 * THESIS_STATE_REPORT.md Addendum 2026-11-10; run profile
 * {@code phase1_v2_brick_only}, JVM flag {@code -Dstereo.knowledgeLayer=brick}).
 *
 * The arm's claim to be a clean contrast rests on three invariants that this
 * test pins on the clean Phase-1 labs (lab1/lab2/lab3):
 *
 * <ol>
 *   <li><b>Same structural claims as the FULL arm.</b> Action key set, labels,
 *       state-vector bits, {@code affectedZones}, and KG-silent flags are
 *       identical. Whatever Δ(FULL − BRICK) the campaign measures is therefore
 *       NOT attributable to "which actuator influences which zone".</li>
 *   <li><b>No Elementary mechanism knowledge.</b> Every BRICK action has
 *       {@code hasIV == false}; the Q-init table has no −100 IV wells (Rule 2)
 *       and the IV-unsat soft prior can never fire, while the FULL arm on the
 *       same lab does gate the blinds on sunshine.</li>
 *   <li><b>Untyped coupling.</b> BRICK sees the same {@code brick:feeds}
 *       cross-zone arcs as FULL but every arc is PRIMARY (no
 *       {@code ws:WeakOpticalCoupling} reading).</li>
 * </ol>
 */
class BrickOnlyKnowledgeLayerTest {

    private static final String[][] CLEAN_LABS = {
        { "building_1_trivial.ttl" },
        { "building_2_intermediate.ttl" },
        { "building_3_complex.ttl" },
    };

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

    private static ActionInfo findOn(StereotypeReasoner r, String fragment) {
        for (ActionInfo ai : r.getAllActions()) {
            if (ai.wotActionType != null && ai.wotActionType.contains(fragment) && ai.wotValue) return ai;
        }
        return null;
    }

    @AfterEach
    void clearProps() {
        System.clearProperty("stereo.knowledgeLayer");
    }

    // ------------------------------------------------------------ invariant 1

    @Test
    void brickArmMakesTheSameStructuralClaimsAsFullArmOnCleanLabs() {
        for (String[] onts : CLEAN_LABS) {
            StereotypeReasoner full  = build(onts, KnowledgeLayer.FULL);
            StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
            String lab = Arrays.toString(onts);

            assertEquals(KnowledgeLayer.BRICK, brick.getKnowledgeLayer());
            assertEquals(full.getNumActions(), brick.getNumActions(), lab + ": action count");
            assertArrayEqualsMsg(full.getStateDomainSizes(), brick.getStateDomainSizes(), lab + ": slot layout");

            Map<String, ActionInfo> f = byKey(full), b = byKey(brick);
            assertEquals(f.keySet(), b.keySet(), lab + ": action key set");
            for (String k : f.keySet()) {
                ActionInfo fa = f.get(k), ba = b.get(k);
                assertEquals(fa.label,            ba.label,            lab + " " + k + ": label");
                assertEquals(fa.wotStateType,     ba.wotStateType,     lab + " " + k + ": wotStateType");
                assertEquals(fa.stateVecBitIndex, ba.stateVecBitIndex, lab + " " + k + ": svBit");
                assertEquals(fa.expectedBitValue, ba.expectedBitValue, lab + " " + k + ": expectedBit");
                assertEquals(fa.affectedZones,    ba.affectedZones,    lab + " " + k + ": affectedZones");
                assertEquals(fa.kgSilent,         ba.kgSilent,         lab + " " + k + ": kgSilent");
                assertEquals(0.0, ba.energyCost, 1e-12,                lab + " " + k + ": BRICK energyCost");
            }
        }
    }

    // ------------------------------------------------------------ invariant 2

    @Test
    void brickArmBindsNoIndependentVariableAnywhere() {
        for (String[] onts : CLEAN_LABS) {
            StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
            for (ActionInfo ai : brick.getAllActions()) {
                assertFalse(ai.hasIV, Arrays.toString(onts) + " " + key(ai) + ": BRICK must not bind an IV");
                assertEquals(-1, ai.ivStateVecIndex, Arrays.toString(onts) + " " + key(ai) + ": ivStateVecIndex");
            }
        }
        // Sanity: the contrast is non-empty — FULL does gate the blinds on
        // lab2 and lab3 (otherwise Δ(FULL − BRICK) would be trivially zero).
        for (String[] onts : new String[][] { CLEAN_LABS[1], CLEAN_LABS[2] }) {
            StereotypeReasoner full = build(onts, KnowledgeLayer.FULL);
            ActionInfo blind = findOn(full, "SetZ1Blinds");
            assertNotNull(blind, Arrays.toString(onts) + ": blind ON action");
            assertTrue(blind.hasIV, Arrays.toString(onts) + ": FULL must IV-gate the blind");
            assertEquals(full.getSunshineIndex(), blind.ivStateVecIndex);
        }
    }

    @Test
    void lab2InitialQTableHasNoIvWellsAndKeepsBlindBonusAtNightUnderBrick() {
        String[] onts = CLEAN_LABS[1];
        StereotypeReasoner full  = build(onts, KnowledgeLayer.FULL);
        StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
        int[] goal = { 3, 3 };
        int[] dom  = brick.getStateDomainSizes();
        int sun    = brick.getSunshineIndex();
        assertTrue(sun >= 0, "lab2 must declare a sunshine slot");

        ActionInfo blindOnB = findOn(brick, "SetZ1Blinds");
        ActionInfo blindOnF = findOn(full,  "SetZ1Blinds");
        ActionInfo lampOnB  = findOn(brick, "SetZ1Light");
        assertNotNull(blindOnB); assertNotNull(blindOnF); assertNotNull(lampOnB);

        // Spot signature at the all-dark, sun-rank-0 state (the 19e-style proof):
        int[] dark = new int[dom.length]; // all zeros: levels 0, actuators off, sun 0
        double scale = 0.5, bonus = 15.0; // stereo.initPenaltyScale / stereo.initBonus defaults
        assertEquals(-100.0 * scale,
            full.getInitPenaltyForZone(dark, blindOnF.actionIndex, 0, goal), 1e-9,
            "FULL: Rule 2 IV well on blind ON at sun 0");
        assertEquals(bonus * 3 * scale,
            brick.getInitPenaltyForZone(dark, blindOnB.actionIndex, 0, goal), 1e-9,
            "BRICK: Rule 5 constructive bonus on blind ON even at sun 0 (no IV gate)");
        assertEquals(bonus * 3 * scale,
            brick.getInitPenaltyForZone(dark, lampOnB.actionIndex, 0, goal), 1e-9,
            "BRICK: Rule 5 constructive bonus on lamp ON");

        // Exhaustive: over the whole lab2 state space, a non-redundant blind
        // activation NEVER receives a negative Q-init under BRICK (no −100 IV
        // well, no other rule targets a single-zone blind), whereas FULL
        // produces the well in every sun-rank-0 state.
        int total = 1;
        for (int d : dom) total *= d;
        int brickNegative = 0, fullWells = 0, nonRedundant = 0;
        for (int idx = 0; idx < total; idx++) {
            int[] sv = decode(idx, dom);
            if (sv[blindOnB.stateVecBitIndex] == 1) continue; // redundant: Rule 1 in both arms
            nonRedundant++;
            double pb = brick.getInitPenaltyForZone(sv, blindOnB.actionIndex, 0, goal);
            double pf = full.getInitPenaltyForZone(sv, blindOnF.actionIndex, 0, goal);
            if (pb < 0) brickNegative++;
            if (sv[sun] == 0 && Math.abs(pf - (-100.0 * scale)) < 1e-9) fullWells++;
        }
        assertTrue(nonRedundant > 0);
        assertEquals(0, brickNegative, "BRICK must emit no negative Q-init for a non-redundant blind ON");
        assertEquals(nonRedundant / dom[sun], fullWells,
            "FULL must emit the −" + (100.0 * scale) + " IV well in every sun-rank-0 non-redundant state");
    }

    @Test
    void ivUnsatSoftPriorNeverFiresUnderBrickEvenAfterFailedTrials() {
        String[] onts = CLEAN_LABS[1];
        StereotypeReasoner full  = build(onts, KnowledgeLayer.FULL);
        StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);
        int[] dom = brick.getStateDomainSizes();
        int[] dark = new int[dom.length];
        ActionInfo bF = findOn(full, "SetZ1Blinds"), bB = findOn(brick, "SetZ1Blinds");

        // Feed both arms 10 unsuccessful blind activations at sun rank 0; only
        // the IV-aware FULL arm can learn "ineffective at rank 0" from them.
        int[] after = dark.clone();
        after[bF.stateVecBitIndex] = 1; // blind now open, level unchanged
        for (int i = 0; i < 10; i++) {
            full.recordActionOutcome(bF.actionIndex, dark, after);
            brick.recordActionOutcome(bB.actionIndex, dark, after);
        }
        assertEquals(-5.0, full.getActionPriors(dark)[bF.actionIndex], 1e-9,
            "FULL: IV-unsat soft prior after 10 failed night trials");
        assertEquals(0.0, brick.getActionPriors(dark)[bB.actionIndex], 1e-9,
            "BRICK: IV-unsat soft prior must never fire");
        // Redundancy prior (registry-derived) is unaffected by the arm.
        after[bB.stateVecBitIndex] = 1;
        assertEquals(-1.0, brick.getActionPriors(after)[bB.actionIndex], 1e-9);
        assertEquals(-1.0, full.getActionPriors(after)[bF.actionIndex], 1e-9);
    }

    // ------------------------------------------------------------ invariant 3

    @Test
    void lab3CrossZoneArcsAreIdenticalButUntypedUnderBrick() {
        String[] onts = CLEAN_LABS[2];
        StereotypeReasoner full  = build(onts, KnowledgeLayer.FULL);
        StereotypeReasoner brick = build(onts, KnowledgeLayer.BRICK);

        List<String> fArcs = arcs(full), bArcs = arcs(brick);
        assertFalse(fArcs.isEmpty(), "lab3 must declare cross-zone feeds");
        assertEquals(fArcs, bArcs, "same brick:feeds arcs in both arms");
        for (CrossZoneEffect cz : full.getCrossZoneEffects()) {
            assertEquals(CrossZoneEffect.CouplingClass.SECONDARY, cz.couplingClass,
                "FULL reads ws:WeakOpticalCoupling on lab3 arcs");
        }
        for (CrossZoneEffect cz : brick.getCrossZoneEffects()) {
            assertEquals(CrossZoneEffect.CouplingClass.PRIMARY, cz.couplingClass,
                "BRICK must not read the Elementary coupling-class stereotype");
        }
    }

    // ------------------------------------------------------------ flag plumbing

    @Test
    void knowledgeLayerFlagResolution() {
        System.clearProperty("stereo.knowledgeLayer");
        assertEquals(KnowledgeLayer.FULL, StereotypeReasoner.defaultKnowledgeLayer());
        System.setProperty("stereo.knowledgeLayer", "brick");
        assertEquals(KnowledgeLayer.BRICK, StereotypeReasoner.defaultKnowledgeLayer());
        System.setProperty("stereo.knowledgeLayer", "FULL");
        assertEquals(KnowledgeLayer.FULL, StereotypeReasoner.defaultKnowledgeLayer());
        System.setProperty("stereo.knowledgeLayer", "redundancy");
        assertEquals(KnowledgeLayer.REDUNDANCY, StereotypeReasoner.defaultKnowledgeLayer());
        System.setProperty("stereo.knowledgeLayer", "elementary");
        assertThrows(IllegalArgumentException.class, StereotypeReasoner::defaultKnowledgeLayer);
    }

    // ------------------------------------------------------------ helpers

    private static int[] decode(int idx, int[] dom) {
        int[] sv = new int[dom.length];
        for (int i = dom.length - 1; i >= 0; i--) {
            sv[i] = idx % dom[i];
            idx /= dom[i];
        }
        return sv;
    }

    private static List<String> arcs(StereotypeReasoner r) {
        List<String> out = new ArrayList<>();
        ActionInfo[] all = r.getAllActions();
        for (CrossZoneEffect cz : r.getCrossZoneEffects()) {
            out.add(all[cz.actionIndex].label + ":" + cz.sourceZoneIdx + "->" + cz.targetZoneIdx);
        }
        java.util.Collections.sort(out);
        return out;
    }

    private static void assertArrayEqualsMsg(int[] a, int[] b, String msg) {
        assertEquals(Arrays.toString(a), Arrays.toString(b), msg);
    }
}
