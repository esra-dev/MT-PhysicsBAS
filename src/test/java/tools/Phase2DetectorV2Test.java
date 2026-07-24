package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.junit.jupiter.api.Test;

/**
 * Fault-detector v2 — the structural-maskability abstain.
 *
 * The protocol-v1 runs of record blacklisted HEALTHY components because the
 * no-response ("dead") verdict abstained only when a rank-masking co-feeder
 * was already fault-suspect. These tests reproduce the masking configurations
 * observed in the committed data at the decision level: a healthy ACTIVE
 * co-feeder of the adjudicated zone must now force an abstain, while an
 * unmasked no-response (all co-feeders inactive) must remain chargeable so
 * genuinely dead components are still isolated instantly.
 */
class Phase2DetectorV2Test {

    // State-vector bit layout used by the synthetic registries below.
    private static final int BIT_Z1_LIGHT = 2;
    private static final int BIT_Z1_BLINDS = 3;
    private static final int BIT_Z2_LIGHT = 4;
    private static final int BIT_Z2_BLINDS = 5;
    private static final int BIT_SPOTLIGHT = 6;

    private static StereotypeReasoner.ActionInfo action(int index, String type,
            boolean value, int bit, Integer... zones) {
        StereotypeReasoner.ActionInfo info = new StereotypeReasoner.ActionInfo();
        info.actionIndex = index;
        info.wotActionType = type;
        info.wotValue = value;
        info.stateVecBitIndex = bit;
        info.affectedZones.addAll(Set.of(zones));
        info.label = type + "=" + value;
        return info;
    }

    /** lab2-like registry: two disjoint zones, lamp + blind per zone. */
    private static StereotypeReasoner.ActionInfo[] lab2Registry() {
        StereotypeReasoner.ActionInfo[] infos = new StereotypeReasoner.ActionInfo[9];
        infos[0] = new StereotypeReasoner.ActionInfo(); // DO_NOTHING (null type)
        infos[1] = action(1, "was#SetZ1Light", true, BIT_Z1_LIGHT, 0);
        infos[2] = action(2, "was#SetZ1Light", false, BIT_Z1_LIGHT, 0);
        infos[3] = action(3, "was#SetZ1Blinds", true, BIT_Z1_BLINDS, 0);
        infos[4] = action(4, "was#SetZ1Blinds", false, BIT_Z1_BLINDS, 0);
        infos[5] = action(5, "was#SetZ2Light", true, BIT_Z2_LIGHT, 1);
        infos[6] = action(6, "was#SetZ2Light", false, BIT_Z2_LIGHT, 1);
        infos[7] = action(7, "was#SetZ2Blinds", true, BIT_Z2_BLINDS, 1);
        infos[8] = action(8, "was#SetZ2Blinds", false, BIT_Z2_BLINDS, 1);
        return infos;
    }

    private static int[] state(boolean z1l, boolean z1b, boolean z2l, boolean z2b,
                               boolean spotlight) {
        // Slots 0-1 are zone ranks (unused by the predicate); 2-6 actuator bits.
        return new int[] {3, 3, z1l ? 1 : 0, z1b ? 1 : 0, z2l ? 1 : 0,
                          z2b ? 1 : 0, spotlight ? 1 : 0};
    }

    @Test
    void healthyOpenBlindMasksLampToggle_lab2F1bdeadTrace() {
        // The committed lab2_f1bdead vanilla replicas: Z1 lamp toggled OFF while
        // the (dead-but-open) Z1 blind bit was active under strong sun; the zone
        // rank held and the healthy lamp was charged dead. v2 must abstain
        // whenever ANY other component actively feeds the zone.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        int[] before = state(true, true, false, false, false);
        assertTrue(QLearner.maskingCoFeederPresent(infos, null, 0, 2, before),
                "active Z1 blind must mask the Z1 lamp's no-response evidence");
    }

    @Test
    void unmaskedNoResponseRemainsChargeable() {
        // Blind closed: the lamp is the only active feeder of zone 0, so a null
        // rank response is clean evidence — no abstain, instant isolation stays.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        int[] before = state(true, false, false, false, false);
        assertFalse(QLearner.maskingCoFeederPresent(infos, null, 0, 2, before),
                "no active co-feeder -> dead verdict must remain chargeable");
    }

    @Test
    void componentUnderTestNeverMasksItself() {
        // Adjudicating Z1Light OFF: the lamp's own bit is active (it is being
        // turned off), and its ON action shares the wotActionType — neither may
        // count as a masker.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        int[] before = state(true, false, false, false, false);
        assertFalse(QLearner.maskingCoFeederPresent(infos, null, 0, 1, before));
        assertFalse(QLearner.maskingCoFeederPresent(infos, null, 0, 2, before));
    }

    @Test
    void activeLampMasksBlindProbe() {
        // The symmetric configuration: probing the Z1 blind while the healthy
        // Z1 lamp is on. Its 400 lux can hold the rank across the blind toggle.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        int[] before = state(true, false, false, false, false);
        assertTrue(QLearner.maskingCoFeederPresent(infos, null, 0, 3, before));
    }

    @Test
    void otherZoneActuatorDoesNotMaskDisjointZone() {
        // Z2 actuators do not feed zone 0 in the lab2 registry (no cross-zone
        // arcs): an active Z2 lamp must not mask a zone-0 adjudication.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        int[] before = state(true, false, true, true, false);
        assertFalse(QLearner.maskingCoFeederPresent(infos, null, 0, 2, before));
    }

    @Test
    void crossZoneFeedArcMasks_lab3Coupling() {
        // lab3-like weak coupling: Z2Light spills into zone 0 via a KG feeds
        // arc. With the Z2 lamp active, a zone-0 no-response on the Z1 lamp is
        // maskable even though affectedZones does not link Z2Light to zone 0.
        StereotypeReasoner.ActionInfo[] infos = lab2Registry();
        List<StereotypeReasoner.CrossZoneEffect> arcs = new ArrayList<>();
        StereotypeReasoner.CrossZoneEffect arc = new StereotypeReasoner.CrossZoneEffect();
        arc.actionIndex = 5; // SetZ2Light=true
        arc.sourceZoneIdx = 1;
        arc.targetZoneIdx = 0;
        arc.couplingClass = StereotypeReasoner.CrossZoneEffect.CouplingClass.SECONDARY;
        arcs.add(arc);
        int[] before = state(true, false, true, false, false);
        assertTrue(QLearner.maskingCoFeederPresent(infos, arcs, 0, 2, before));
        // Same arcs, Z2 lamp off: no masking.
        int[] beforeOff = state(true, false, false, false, false);
        assertFalse(QLearner.maskingCoFeederPresent(infos, arcs, 0, 2, beforeOff));
    }

    @Test
    void activeMultiZoneSpotlightMasksBothZones() {
        StereotypeReasoner.ActionInfo[] infos = new StereotypeReasoner.ActionInfo[11];
        System.arraycopy(lab2Registry(), 0, infos, 0, 9);
        infos[9] = action(9, "was#SetSpotlight", true, BIT_SPOTLIGHT, 0, 1);
        infos[10] = action(10, "was#SetSpotlight", false, BIT_SPOTLIGHT, 0, 1);
        int[] before = state(true, false, true, false, true);
        assertTrue(QLearner.maskingCoFeederPresent(infos, null, 0, 2, before));
        assertTrue(QLearner.maskingCoFeederPresent(infos, null, 1, 6, before));
    }

    @Test
    void versionConstantsArePinned() {
        assertEquals("fault-detector-v2", QLearner.FAULT_DETECTOR_VERSION);
        assertEquals("phase2-v2", QLearner.PHASE2_PROTOCOL_VERSION);
    }
}
