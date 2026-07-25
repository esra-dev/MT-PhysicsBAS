package tools;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

/**
 * Phase-1b mandatory regression gate (plan §Verification gates): the exact
 * state spaces of the seven Phase-1b labs, and the inertness of the extended
 * relevance/direction channels on lab4chain3's UNKNOWN decoys — asserted
 * against the REAL committed ontologies through the production loader.
 */
class Phase1bStateSpaceTest {

    private static StereotypeReasoner load(String ttl) {
        return new StereotypeReasoner(
            new StereotypeReasoner.ClasspathOntologyLoader(new String[] {ttl}), 0.75);
    }

    private static long stateCount(StereotypeReasoner r) {
        long n = 1;
        for (int d : r.getStateDomainSizes()) n *= d;
        return n;
    }

    @Test
    void statelessLabrelRungsAllHaveEightStates() {
        for (String ttl : new String[] {
                "building_10_labrel0.ttl", "building_10_labrel4.ttl",
                "building_10_labrel8.ttl", "building_10_labrel16.ttl" }) {
            StereotypeReasoner r = load(ttl);
            assertEquals(2, r.getStateVecLength(),
                ttl + ": stateless rungs observe only [Z1Level, Z1Light]");
            assertEquals(8, stateCount(r), ttl + ": 4 x 2 = 8 states");
        }
    }

    @Test
    void labrel8sHas2048States() {
        StereotypeReasoner r = load("building_10_labrel8s.ttl");
        assertEquals(10, r.getStateVecLength());
        assertEquals(2048, stateCount(r), "4 x 2^9 = 2048");
    }

    @Test
    void labbandHas256StatesAndChain3Has128() {
        assertEquals(256, stateCount(load("building_11_labband.ttl")), "4 x 2^4 x 4");
        assertEquals(128, stateCount(load("building_12_chain3.ttl")), "4 x 2^5");
    }

    @Test
    void actionCountsMatchTheLadder() {
        assertEquals(3,  load("building_10_labrel0.ttl").getNumActions());
        assertEquals(11, load("building_10_labrel4.ttl").getNumActions());
        assertEquals(19, load("building_10_labrel8.ttl").getNumActions());
        assertEquals(35, load("building_10_labrel16.ttl").getNumActions());
        assertEquals(19, load("building_10_labrel8s.ttl").getNumActions());
        assertEquals(9,  load("building_11_labband.ttl").getNumActions());
        assertEquals(11, load("building_12_chain3.ttl").getNumActions());
    }

    @Test
    void extendedChannelsAreInertOnChain3UnknownDecoys() {
        StereotypeReasoner r = load("building_12_chain3.ttl");
        StereotypeReasoner.setIrrelevantDvPriorForTest(2.0);
        StereotypeReasoner.setBandMirrorInitForTest(5.0);
        try {
            for (StereotypeReasoner.ActionInfo ai : r.getAllActions()) {
                if (ai.wotActionType == null) continue;
                boolean decoy = ai.wotActionType.endsWith("#SetAuxA")
                             || ai.wotActionType.endsWith("#SetAuxB");
                if (!decoy) continue;
                assertEquals(StereotypeReasoner.Relevance.UNKNOWN, ai.relevance,
                    ai.label + " must classify UNKNOWN (incomplete description)");
                assertEquals(0, ai.illumDirection, ai.label + " has no direction claim");
                assertTrue(ai.ivGates.isEmpty(), ai.label + " collects no IV gates");
                // With both extended knobs ON, a non-redundant decoy action
                // must still receive a strictly zero init prior in every
                // non-goal state we probe (decoys start OFF -> ON action is
                // non-redundant at all-zero state).
                if (ai.wotValue) {
                    double p = r.getInitPenaltyForZone(
                        new int[] {0, 0, 0, 0, 0, 0}, ai.actionIndex, 0, new int[] {3});
                    assertEquals(0.0, p, 1e-12,
                        ai.label + ": extended channels must be inert on UNKNOWN decoys");
                }
            }
        } finally {
            StereotypeReasoner.setIrrelevantDvPriorForTest(0.0);
            StereotypeReasoner.setBandMirrorInitForTest(0.0);
        }
        assertNotNull(r);
    }
}
