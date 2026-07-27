package tools;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;

import org.junit.jupiter.api.Test;

/**
 * Runtime-level proof for the four clean parent layouts used by the frozen
 * Phase-2b-A start-state Q-gap proxy.
 *
 * <p>The test configures the production {@link QLearner} from each committed
 * parent ontology, inspects the layout and strides that QLearner actually
 * installed, and invokes its private mixed-radix encoder. The expected
 * constants are frozen independently here; this does not reimplement the
 * encoder and compare two copies of the same test-side formula.</p>
 */
class Phase2QGapStateEncodingTest {

    private static final String WAS = "http://example.org/was#";

    private static final class ActionCase {
        final String label;
        final String actionType;
        final String stateType;
        final boolean targetValue;
        final int expectedBitValue;
        final int stateBitIndex;

        ActionCase(
                String label,
                String actionType,
                String stateType,
                boolean targetValue,
                int expectedBitValue,
                int stateBitIndex) {
            this.label = label;
            this.actionType = actionType;
            this.stateType = stateType;
            this.targetValue = targetValue;
            this.expectedBitValue = expectedBitValue;
            this.stateBitIndex = stateBitIndex;
        }
    }

    private static final class LayoutCase {
        final String profile;
        final String ontology;
        final Object[] goal;
        final int[] domains;
        final int[] strides;
        final int[] zoneLevelIndices;
        final int sunshineIndex;
        final int stateCount;
        final Object[] representativeState;
        final int representativeIndex;
        final ActionCase[] actions;

        LayoutCase(
                String profile,
                String ontology,
                Object[] goal,
                int[] domains,
                int[] strides,
                int[] zoneLevelIndices,
                int sunshineIndex,
                int stateCount,
                Object[] representativeState,
                int representativeIndex,
                ActionCase[] actions) {
            this.profile = profile;
            this.ontology = ontology;
            this.goal = goal;
            this.domains = domains;
            this.strides = strides;
            this.zoneLevelIndices = zoneLevelIndices;
            this.sunshineIndex = sunshineIndex;
            this.stateCount = stateCount;
            this.representativeState = representativeState;
            this.representativeIndex = representativeIndex;
            this.actions = actions;
        }
    }

    private static final List<LayoutCase> CASES = Arrays.asList(
        new LayoutCase(
            "lab2",
            "building_2_intermediate.ttl",
            new Object[] {3, 3},
            new int[] {4, 4, 2, 2, 2, 2, 4},
            new int[] {256, 64, 32, 16, 8, 4, 1},
            new int[] {0, 1},
            6,
            1024,
            new Object[] {3, 1, 1, 0, 1, 0, 2},
            874,
            new ActionCase[] {
                action("SetZ1Blinds=OFF", "SetZ1Blinds", "Z1Blinds", false, 4),
                action("SetZ1Blinds=ON", "SetZ1Blinds", "Z1Blinds", true, 4),
                action("SetZ1Light=OFF", "SetZ1Light", "Z1Light", false, 2),
                action("SetZ1Light=ON", "SetZ1Light", "Z1Light", true, 2),
                action("SetZ2Blinds=OFF", "SetZ2Blinds", "Z2Blinds", false, 5),
                action("SetZ2Blinds=ON", "SetZ2Blinds", "Z2Blinds", true, 5),
                action("SetZ2Light=OFF", "SetZ2Light", "Z2Light", false, 3),
                action("SetZ2Light=ON", "SetZ2Light", "Z2Light", true, 3),
                doNothing()
            }),
        new LayoutCase(
            "lab3",
            "building_3_complex.ttl",
            new Object[] {3, 3},
            new int[] {4, 4, 2, 2, 2, 2, 2, 4},
            new int[] {512, 128, 64, 32, 16, 8, 4, 1},
            new int[] {0, 1},
            7,
            2048,
            new Object[] {2, 3, 1, 0, 1, 1, 0, 3},
            1499,
            new ActionCase[] {
                action("SetSpotlight=OFF", "SetSpotlight", "Spotlight", false, 6),
                action("SetSpotlight=ON", "SetSpotlight", "Spotlight", true, 6),
                action("SetZ1Blinds=OFF", "SetZ1Blinds", "Z1Blinds", false, 4),
                action("SetZ1Blinds=ON", "SetZ1Blinds", "Z1Blinds", true, 4),
                action("SetZ1Light=OFF", "SetZ1Light", "Z1Light", false, 2),
                action("SetZ1Light=ON", "SetZ1Light", "Z1Light", true, 2),
                action("SetZ2Blinds=OFF", "SetZ2Blinds", "Z2Blinds", false, 5),
                action("SetZ2Blinds=ON", "SetZ2Blinds", "Z2Blinds", true, 5),
                action("SetZ2Light=OFF", "SetZ2Light", "Z2Light", false, 3),
                action("SetZ2Light=ON", "SetZ2Light", "Z2Light", true, 3),
                doNothing()
            }),
        new LayoutCase(
            "labmon",
            "building_6_monitor.ttl",
            new Object[] {3},
            new int[] {4, 2, 2},
            new int[] {4, 2, 1},
            new int[] {0},
            -1,
            16,
            new Object[] {2, 1, 0},
            10,
            new ActionCase[] {
                action("SetZ1Light=OFF", "SetZ1Light", "Z1Light", false, 1),
                action("SetZ1Light=ON", "SetZ1Light", "Z1Light", true, 1),
                action("SetZ1Monitor=OFF", "SetZ1Monitor", "Z1Monitor", false, 2),
                action("SetZ1Monitor=ON", "SetZ1Monitor", "Z1Monitor", true, 2),
                doNothing()
            }),
        new LayoutCase(
            "labmon2",
            "building_7_dualmonitor.ttl",
            new Object[] {3, 3},
            new int[] {4, 4, 2, 2, 2, 2, 2, 2, 4},
            new int[] {1024, 256, 128, 64, 32, 16, 8, 4, 1},
            new int[] {0, 1},
            8,
            4096,
            new Object[] {1, 3, 1, 0, 1, 1, 0, 1, 2},
            1974,
            new ActionCase[] {
                action("SetZ1Blinds=OFF", "SetZ1Blinds", "Z1Blinds", false, 6),
                action("SetZ1Blinds=ON", "SetZ1Blinds", "Z1Blinds", true, 6),
                action("SetZ1Light=OFF", "SetZ1Light", "Z1Light", false, 2),
                action("SetZ1Light=ON", "SetZ1Light", "Z1Light", true, 2),
                action("SetZ1Monitor=OFF", "SetZ1Monitor", "Z1Monitor", false, 4),
                action("SetZ1Monitor=ON", "SetZ1Monitor", "Z1Monitor", true, 4),
                action("SetZ2Blinds=OFF", "SetZ2Blinds", "Z2Blinds", false, 7),
                action("SetZ2Blinds=ON", "SetZ2Blinds", "Z2Blinds", true, 7),
                action("SetZ2Light=OFF", "SetZ2Light", "Z2Light", false, 3),
                action("SetZ2Light=ON", "SetZ2Light", "Z2Light", true, 3),
                action("SetZ2Monitor=OFF", "SetZ2Monitor", "Z2Monitor", false, 5),
                action("SetZ2Monitor=ON", "SetZ2Monitor", "Z2Monitor", true, 5),
                doNothing()
            })
    );

    private static ActionCase action(
            String label,
            String actionType,
            String stateType,
            boolean targetValue,
            int stateBitIndex) {
        return new ActionCase(
            label,
            WAS + actionType,
            WAS + stateType,
            targetValue,
            targetValue ? 1 : 0,
            stateBitIndex);
    }

    private static ActionCase doNothing() {
        return new ActionCase("DO_NOTHING", null, null, false, -1, -1);
    }

    @Test
    void frozenParentLayoutsAndRepresentativeIndicesMatchProductionQLearner()
            throws Exception {
        Method stateVecToIndex =
            QLearner.class.getDeclaredMethod("stateVecToIndex", Object[].class);
        stateVecToIndex.setAccessible(true);

        for (LayoutCase expected : CASES) {
            QLearner learner = new QLearner();
            learner.configureQLearner(
                expected.goal,
                false,
                new Object[] {expected.ontology},
                0.75);

            assertFalse(
                reasoner(learner).isDegraded(),
                expected.profile + ": production ontology load must not fall back");
            assertArrayEquals(
                expected.domains,
                intArrayField(learner, "domainSizes"),
                expected.profile + ": state domains changed");
            assertArrayEquals(
                expected.strides,
                intArrayField(learner, "strides"),
                expected.profile + ": mixed-radix strides changed");
            assertArrayEquals(
                expected.zoneLevelIndices,
                intArrayField(learner, "zoneLevelIndices"),
                expected.profile + ": zone-level slots changed");
            assertEquals(
                expected.sunshineIndex,
                intField(learner, "sunshineIndex"),
                expected.profile + ": sunshine slot changed");
            assertEquals(
                expected.stateCount,
                intField(learner, "nStates"),
                expected.profile + ": state count changed");

            StereotypeReasoner.ActionInfo[] actualActions =
                reasoner(learner).getAllActions();
            assertEquals(
                expected.actions.length,
                actualActions.length,
                expected.profile + ": runtime action count/order changed");
            for (int actionIndex = 0; actionIndex < expected.actions.length;
                    actionIndex++) {
                ActionCase expectedAction = expected.actions[actionIndex];
                StereotypeReasoner.ActionInfo actualAction =
                    actualActions[actionIndex];
                String message = expected.profile + ": action " + actionIndex;
                assertEquals(
                    actionIndex,
                    actualAction.actionIndex,
                    message + " runtime index changed");
                assertEquals(
                    expectedAction.label,
                    actualAction.label,
                    message + " label changed");
                assertEquals(
                    expectedAction.actionType,
                    actualAction.wotActionType,
                    message + " component action type changed");
                assertEquals(
                    expectedAction.stateType,
                    actualAction.wotStateType,
                    message + " component state type changed");
                assertEquals(
                    expectedAction.targetValue,
                    actualAction.wotValue,
                    message + " target polarity changed");
                assertEquals(
                    expectedAction.expectedBitValue,
                    actualAction.expectedBitValue,
                    message + " expected bit value changed");
                assertEquals(
                    expectedAction.stateBitIndex,
                    actualAction.stateVecBitIndex,
                    message + " component-to-state-bit mapping changed");
            }

            int actualIndex = (Integer) stateVecToIndex.invoke(
                learner, (Object) expected.representativeState);
            assertEquals(
                expected.representativeIndex,
                actualIndex,
                expected.profile + ": representative state encoded differently");
        }
    }

    private static int[] intArrayField(QLearner learner, String name)
            throws ReflectiveOperationException {
        Field field = QLearner.class.getDeclaredField(name);
        field.setAccessible(true);
        return ((int[]) field.get(learner)).clone();
    }

    private static int intField(QLearner learner, String name)
            throws ReflectiveOperationException {
        Field field = QLearner.class.getDeclaredField(name);
        field.setAccessible(true);
        return field.getInt(learner);
    }

    private static StereotypeReasoner reasoner(QLearner learner)
            throws ReflectiveOperationException {
        Field field = QLearner.class.getDeclaredField("reasoner");
        field.setAccessible(true);
        return (StereotypeReasoner) field.get(learner);
    }
}
