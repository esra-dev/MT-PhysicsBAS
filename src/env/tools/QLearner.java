package tools;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.logging.Logger;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;

/**
 * QLearner — CArtAgO artifact implementing tabular Q-learning for the illuminance
 * controller agent.
 *
 * State space (7 components, following the assignment spec):
 *   [Z1Level(0-3), Z2Level(0-3), Z1Light(0/1), Z2Light(0/1),
 *    Z1Blinds(0/1), Z2Blinds(0/1), sunshine(0-3)]
 *
 * Q-table indexing: sunshine is normalized out (256 states, not 1024), matching
 * the assignment specification. Sunshine is still used at runtime for action masking
 * (stereotype mode) and reward shaping.
 *   index = Z1Level×64 + Z2Level×16 + Z1Light×8 + Z2Light×4 + Z1Blinds×2 + Z2Blinds
 *
 * Action space (9 actions):
 *   0: Turn on  lights  Z1    (Z1Light  = true)
 *   1: Turn off lights  Z1    (Z1Light  = false)
 *   2: Turn on  lights  Z2    (Z2Light  = true)
 *   3: Turn off lights  Z2    (Z2Light  = false)
 *   4: Open  blinds Z1        (Z1Blinds = true)
 *   5: Close blinds Z1        (Z1Blinds = false)
 *   6: Open  blinds Z2        (Z2Blinds = true)
 *   7: Close blinds Z2        (Z2Blinds = false)
 *   8: Do nothing
 *
 * Stereotype mode (useStereotypes=true):
 *   - Q-table is pre-initialized with penalties (−100) for actions that are
 *     immediately inferrable as redundant/invalid from the current state.
 *     This mirrors the ontology knowledge in lab-ontology.ttl:
 *       * ws:pm_daylight_ingress has ws:ivMinRank 1 → blinds must have sunshine ≥ rank 1
 *       * Turning on an already-on light / opening an already-open blind is wasteful
 *   - getApplicableActions() masks semantically invalid actions using the same rules.
 *
 * Standard mode (useStereotypes=false):
 *   - Q-table initialized uniformly to 0.0.
 *   - getApplicableActions() always returns all 9 actions.
 *   - Agent must learn these constraints from scratch via reward signals.
 *
 * WoT action type URIs match LabEnvironment / interactions-lab-custom.ttl:
 *   "http://example.org/was#SetZ1Light"  / SetZ2Light / SetZ1Blinds / SetZ2Blinds
 */
public class QLearner extends Artifact {

    private static final Logger LOGGER = Logger.getLogger(QLearner.class.getName());

    // -----------------------------------------------------------------------
    // Q-learning hyperparameters (default values, overridable via init)
    // -----------------------------------------------------------------------
    private double alpha   = 0.1;   // learning rate
    private double gamma   = 0.9;   // discount factor
    private double epsilon = 0.3;   // exploration rate
    private final double epsilonDecay = 0.995;
    private final double epsilonMin   = 0.01;

    // -----------------------------------------------------------------------
    // State / action dimensions
    // -----------------------------------------------------------------------
    private static final int N_STATES  = 256; // 4×4×2×2×2×2 (sunshine excluded from index)
    private static final int N_ACTIONS = 9;

    // -----------------------------------------------------------------------
    // State vector indices
    // -----------------------------------------------------------------------
    private static final int IDX_Z1LEVEL   = 0;
    private static final int IDX_Z2LEVEL   = 1;
    private static final int IDX_Z1LIGHT   = 2;
    private static final int IDX_Z2LIGHT   = 3;
    private static final int IDX_Z1BLINDS  = 4;
    private static final int IDX_Z2BLINDS  = 5;
    private static final int IDX_SUNSHINE  = 6;

    // -----------------------------------------------------------------------
    // Action constants
    // -----------------------------------------------------------------------
    private static final int ACT_Z1LIGHT_ON   = 0;
    private static final int ACT_Z1LIGHT_OFF  = 1;
    private static final int ACT_Z2LIGHT_ON   = 2;
    private static final int ACT_Z2LIGHT_OFF  = 3;
    private static final int ACT_Z1BLINDS_OPEN  = 4;
    private static final int ACT_Z1BLINDS_CLOSE = 5;
    private static final int ACT_Z2BLINDS_OPEN  = 6;
    private static final int ACT_Z2BLINDS_CLOSE = 7;
    private static final int ACT_DO_NOTHING     = 8;

    // -----------------------------------------------------------------------
    // Fields
    // -----------------------------------------------------------------------
    private double[][] qTable;       // qTable[stateIndex][action]
    private int[]      goal;         // [Z1TargetRank, Z2TargetRank]
    private boolean    useStereotypes;
    private Random     rng;

    // WoT action type URIs — must match interactions-lab-custom.ttl and
    // interactions-lab.ttl action affordances (same type URIs in both).
    private static final String[] WOT_ACTION_TYPES = {
        "http://example.org/was#SetZ1Light",   // 0: Z1Light on
        "http://example.org/was#SetZ1Light",   // 1: Z1Light off
        "http://example.org/was#SetZ2Light",   // 2: Z2Light on
        "http://example.org/was#SetZ2Light",   // 3: Z2Light off
        "http://example.org/was#SetZ1Blinds",  // 4: Z1Blinds open
        "http://example.org/was#SetZ1Blinds",  // 5: Z1Blinds close
        "http://example.org/was#SetZ2Blinds",  // 6: Z2Blinds open
        "http://example.org/was#SetZ2Blinds",  // 7: Z2Blinds close
        null                                   // 8: do nothing
    };
    private static final boolean[] WOT_ACTION_VALUES = {
        true, false, true, false, true, false, true, false, false
    };

    // -----------------------------------------------------------------------
    // CArtAgO initialisation
    // -----------------------------------------------------------------------

    /**
     * Initialise the Q-learner.
     *
     * @param goal           Jason list [Z1TargetRank, Z2TargetRank], e.g. [3, 2].
     * @param useStereotypes true  → stereotype-guided init + action masking.
     *                       false → standard zero-init + full action space.
     */
    @OPERATION
    public void init(Object[] goal, boolean useStereotypes) {
        this.goal           = new int[]{toInt(goal[0]), toInt(goal[1])};
        this.useStereotypes = useStereotypes;
        this.rng            = new Random(42);

        qTable = new double[N_STATES][N_ACTIONS];

        if (useStereotypes) {
            initWithStereotypes();
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: ON");
            LOGGER.info("  Pre-penalised impossible/redundant actions: Q = -100 for"
                      + " already-active state/action pairs.");
            LOGGER.info("  Action masking active: blinds blocked when sunshine < rank 1.");
        } else {
            // Standard zero-initialisation
            for (double[] row : qTable) Arrays.fill(row, 0.0);
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: OFF (standard zero-init)");
        }

        LOGGER.info("  Goal: Z1=" + this.goal[0] + " Z2=" + this.goal[1]);
        LOGGER.info("  States=" + N_STATES + " Actions=" + N_ACTIONS);
        LOGGER.info("  α=" + alpha + " γ=" + gamma + " ε=" + epsilon);
    }

    /**
     * Pre-initialise Q-table using stereotype-derived prior knowledge.
     *
     * Rules derived directly from lab-ontology.ttl semantics:
     *  1. Turning on a light that is already on is a no-op → penalise.
     *  2. Turning off a light that is already off is a no-op → penalise.
     *  3. Opening  a blind that is already open  is a no-op → penalise.
     *  4. Closing  a blind that is already closed is a no-op → penalise.
     *  5. Opening  a blind when sunshine < rank 1 (ws:ivMinRank = 1 for
     *     ws:pm_daylight_ingress) adds no illuminance → penalise.
     *
     * These penalties bias learning away from wasted actions, mirroring how the
     * OntologyArtifact uses SPARQL to filter applicable actuators in the reactive
     * agent.  Convergence should be faster because the agent starts with the
     * equivalent of "common-sense" physics knowledge.
     */
    private void initWithStereotypes() {
        for (int s = 0; s < N_STATES; s++) {
            Arrays.fill(qTable[s], 0.0);

            int[] sv = decodeState(s);
            int z1Light  = sv[IDX_Z1LIGHT];
            int z2Light  = sv[IDX_Z2LIGHT];
            int z1Blinds = sv[IDX_Z1BLINDS];
            int z2Blinds = sv[IDX_Z2BLINDS];

            // Rule 1+2: light already in target state
            if (z1Light == 1) qTable[s][ACT_Z1LIGHT_ON]  = -100.0; // already on
            if (z1Light == 0) qTable[s][ACT_Z1LIGHT_OFF] = -100.0; // already off
            if (z2Light == 1) qTable[s][ACT_Z2LIGHT_ON]  = -100.0;
            if (z2Light == 0) qTable[s][ACT_Z2LIGHT_OFF] = -100.0;

            // Rule 3+4: blind already in target state
            if (z1Blinds == 1) qTable[s][ACT_Z1BLINDS_OPEN]  = -100.0; // already open
            if (z1Blinds == 0) qTable[s][ACT_Z1BLINDS_CLOSE] = -100.0; // already closed
            if (z2Blinds == 1) qTable[s][ACT_Z2BLINDS_OPEN]  = -100.0;
            if (z2Blinds == 0) qTable[s][ACT_Z2BLINDS_CLOSE] = -100.0;

            // Rule 5: opening blinds is useless when sunshine rank < 1
            // (ws:pm_daylight_ingress → ws:ivMinRank = 1 in lab-ontology.ttl)
            // Note: sunshine is NOT part of the 256-state index, so we penalise
            // blind-open actions globally here.  The runtime action mask enforces
            // the per-step sunshine check precisely during execution.
            qTable[s][ACT_Z1BLINDS_OPEN] = Math.min(qTable[s][ACT_Z1BLINDS_OPEN], -50.0);
            qTable[s][ACT_Z2BLINDS_OPEN] = Math.min(qTable[s][ACT_Z2BLINDS_OPEN], -50.0);
        }
    }

    // -----------------------------------------------------------------------
    // State encoding / decoding
    // -----------------------------------------------------------------------

    /**
     * Encode the raw lab state (as returned by LabEnvironment.readLabStatus) into
     * an integer state vector of length 7 suitable for Q-table lookups.
     *
     * @param zoneLevels      Integer[] per-zone illuminance ranks (parallel to sorted zone indices).
     * @param sunshineRank    Sunshine rank 0–3.
     * @param boolStateKeys   WoT status URI strings from readLabStatus.
     * @param boolStateValues Corresponding boolean values.
     * @param stateVec        Output: int[7] state vector
     *                        [Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, sunshine].
     */
    @OPERATION
    public void encodeState(
            Object[] zoneLevels,
            int      sunshineRank,
            Object[] boolStateKeys,
            Object[] boolStateValues,
            OpFeedbackParam<Object[]> stateVec) {

        int z1Level = toInt(zoneLevels[0]);
        int z2Level = (zoneLevels.length > 1) ? toInt(zoneLevels[1]) : 0;

        // Resolve boolean states by their WoT URI
        boolean z1Light  = getBoolState(boolStateKeys, boolStateValues,
                                        "http://example.org/was#Z1Light");
        boolean z2Light  = getBoolState(boolStateKeys, boolStateValues,
                                        "http://example.org/was#Z2Light");
        boolean z1Blinds = getBoolState(boolStateKeys, boolStateValues,
                                        "http://example.org/was#Z1Blinds");
        boolean z2Blinds = getBoolState(boolStateKeys, boolStateValues,
                                        "http://example.org/was#Z2Blinds");

        Object[] sv = new Object[]{
            z1Level,
            z2Level,
            z1Light  ? 1 : 0,
            z2Light  ? 1 : 0,
            z1Blinds ? 1 : 0,
            z2Blinds ? 1 : 0,
            sunshineRank
        };
        stateVec.set(sv);
        LOGGER.fine("encodeState: " + Arrays.toString(sv));
    }

    // -----------------------------------------------------------------------
    // Core Q-learning operations
    // -----------------------------------------------------------------------

    /**
     * Update the Q-value for (state, action) using the standard Bellman equation:
     *   Q(S,A) ← Q(S,A) + α [ R + γ · max_a Q(S',a) − Q(S,A) ]
     *
     * @param stateVec     Current state vector (int[7]).
     * @param action       Action taken (0–8).
     * @param reward       Observed reward.
     * @param nextStateVec Next state vector (int[7]).
     */
    @OPERATION
    public void calculateQ(Object[] stateVec, int action, double reward, Object[] nextStateVec) {
        int sIdx  = stateVecToIndex(stateVec);
        int sNext = stateVecToIndex(nextStateVec);

        double maxNextQ = maxQ(sNext);
        double oldQ     = qTable[sIdx][action];
        double newQ     = oldQ + alpha * (reward + gamma * maxNextQ - oldQ);
        qTable[sIdx][action] = newQ;

        LOGGER.fine("calculateQ: s=" + sIdx + " a=" + action +
                    " r=" + reward + " s'=" + sNext + " Q: " + oldQ + " → " + newQ);
    }

    /**
     * Select an action using ε-greedy policy.
     *
     * @param stateVec  Current state vector (int[7]).
     * @param explore   true  → ε-greedy (explore during training).
     *                  false → greedy (exploit learned policy during execution).
     * @param action    Output: selected action index (0–8).
     */
    @OPERATION
    public void getActionFromState(Object[] stateVec, boolean explore,
                                   OpFeedbackParam<Integer> action) {
        int sIdx = stateVecToIndex(stateVec);
        int[] applicable = computeApplicableActions(stateVec);

        int chosen;
        if (explore && rng.nextDouble() < epsilon) {
            // Random exploration within applicable actions
            chosen = applicable[rng.nextInt(applicable.length)];
            LOGGER.fine("getActionFromState: EXPLORE → action=" + chosen);
        } else {
            // Greedy within applicable actions
            chosen = greedyAction(sIdx, applicable);
            LOGGER.fine("getActionFromState: EXPLOIT → action=" + chosen);
        }
        action.set(chosen);
    }

    /**
     * Return the list of applicable actions for the current state.
     * In stereotype mode this masks semantically invalid actions (see
     * initWithStereotypes for the derivation from lab-ontology.ttl).
     *
     * @param stateVec   Current state vector (int[7]).
     * @param actions    Output: Integer[] of applicable action indices.
     */
    @OPERATION
    public void getApplicableActions(Object[] stateVec,
                                     OpFeedbackParam<Object[]> actions) {
        int[] a = computeApplicableActions(stateVec);
        Object[] result = new Object[a.length];
        for (int i = 0; i < a.length; i++) result[i] = a[i];
        actions.set(result);
    }

    /**
     * Map a numeric action index to the WoT action type URI and boolean value
     * needed to invoke it via LabEnvironment.invokeAction.
     *
     * @param action    Action index (0–8).
     * @param wotType   Output: WoT action @type URI, or "none" for do-nothing.
     * @param value     Output: boolean payload for the action.
     */
    @OPERATION
    public void actionToWoT(int action,
                            OpFeedbackParam<String>  wotType,
                            OpFeedbackParam<Boolean> value) {
        if (action < 0 || action >= N_ACTIONS) {
            wotType.set("none");
            value.set(false);
            return;
        }
        String uri = WOT_ACTION_TYPES[action];
        wotType.set(uri != null ? uri : "none");
        value.set(WOT_ACTION_VALUES[action]);
    }

    /**
     * Compute the reward signal for a state transition.
     *
     * Reward structure:
     *  +1000  Both zone levels match the goal (primary incentive).
     *  +20    Any zone level moved strictly closer to its target rank.
     *  −50    Turning on a light (action 0 or 2).
     *  −1     Opening a blind (action 4 or 6).
     *  −5     Do-nothing (action 8) when goal not reached (mild stagnation penalty).
     *
     * @param prevStateVec Previous state vector (int[7]).
     * @param action       Action taken.
     * @param nextStateVec Next state vector (int[7]).
     * @param reward       Output: computed reward value.
     */
    @OPERATION
    public void computeReward(Object[] prevStateVec, int action, Object[] nextStateVec,
                              OpFeedbackParam<Double> reward) {
        int prevZ1 = toInt(prevStateVec[IDX_Z1LEVEL]);
        int prevZ2 = toInt(prevStateVec[IDX_Z2LEVEL]);
        int nextZ1 = toInt(nextStateVec[IDX_Z1LEVEL]);
        int nextZ2 = toInt(nextStateVec[IDX_Z2LEVEL]);

        double r = 0.0;

        // Primary goal reward
        if (nextZ1 == goal[0] && nextZ2 == goal[1]) {
            r += 1000.0;
        }

        // Progress reward: sum of zone improvements
        int prevDist = Math.abs(prevZ1 - goal[0]) + Math.abs(prevZ2 - goal[1]);
        int nextDist = Math.abs(nextZ1 - goal[0]) + Math.abs(nextZ2 - goal[1]);
        if (nextDist < prevDist) {
            r += 20.0;
        }

        // Energy penalties
        if (action == ACT_Z1LIGHT_ON || action == ACT_Z2LIGHT_ON) {
            r -= 50.0;
        }
        if (action == ACT_Z1BLINDS_OPEN || action == ACT_Z2BLINDS_OPEN) {
            r -= 1.0;
        }

        // Oscillation / stagnation penalty
        if (action == ACT_DO_NOTHING && !(nextZ1 == goal[0] && nextZ2 == goal[1])) {
            r -= 5.0;
        }

        reward.set(r);
        LOGGER.fine("computeReward: a=" + action +
                    " prev=[" + prevZ1 + "," + prevZ2 + "]" +
                    " next=[" + nextZ1 + "," + nextZ2 + "]" +
                    " r=" + r);
    }

    /**
     * Check whether the current state is a terminal state, i.e. both zone
     * illuminance levels match the goal.
     *
     * @param stateVec   Current state vector (int[7]).
     * @param terminal   Output: true if terminal.
     */
    @OPERATION
    public void isTerminal(Object[] stateVec, OpFeedbackParam<Boolean> terminal) {
        boolean t = toInt(stateVec[IDX_Z1LEVEL]) == goal[0]
                 && toInt(stateVec[IDX_Z2LEVEL]) == goal[1];
        terminal.set(t);
    }

    /**
     * Decay the exploration rate ε by the configured decay factor.
     * Call once per training episode.
     */
    @OPERATION
    public void decayEpsilon() {
        epsilon = Math.max(epsilonMin, epsilon * epsilonDecay);
        LOGGER.fine("decayEpsilon: ε=" + epsilon);
    }

    /**
     * Return a one-line summary of the current epsilon value and mode.
     * Used by the agent for progress logging.
     *
     * @param summary Output: summary string.
     */
    @OPERATION
    public void getStatus(OpFeedbackParam<String> summary) {
        summary.set("mode=" + (useStereotypes ? "STEREOTYPE" : "STANDARD")
                  + " ε=" + String.format("%.4f", epsilon)
                  + " goal=[" + goal[0] + "," + goal[1] + "]");
    }

    // -----------------------------------------------------------------------
    // Private helpers
    // -----------------------------------------------------------------------

    /** Convert the state vector to a Q-table index (sunshine excluded). */
    private int stateVecToIndex(Object[] sv) {
        int z1L = clamp(toInt(sv[IDX_Z1LEVEL]),  0, 3);
        int z2L = clamp(toInt(sv[IDX_Z2LEVEL]),  0, 3);
        int z1Lt = clamp(toInt(sv[IDX_Z1LIGHT]),  0, 1);
        int z2Lt = clamp(toInt(sv[IDX_Z2LIGHT]),  0, 1);
        int z1B  = clamp(toInt(sv[IDX_Z1BLINDS]), 0, 1);
        int z2B  = clamp(toInt(sv[IDX_Z2BLINDS]), 0, 1);
        return z1L * 64 + z2L * 16 + z1Lt * 8 + z2Lt * 4 + z1B * 2 + z2B;
    }

    /** Decode a flat state index back to a 6-element int array (without sunshine). */
    private int[] decodeState(int idx) {
        int z1L  = idx / 64;        idx %= 64;
        int z2L  = idx / 16;        idx %= 16;
        int z1Lt = idx / 8;         idx %= 8;
        int z2Lt = idx / 4;         idx %= 4;
        int z1B  = idx / 2;         idx %= 2;
        int z2B  = idx;
        return new int[]{z1L, z2L, z1Lt, z2Lt, z1B, z2B};
    }

    /** Maximum Q-value over all actions for a given state index. */
    private double maxQ(int stateIdx) {
        double max = Double.NEGATIVE_INFINITY;
        for (int a = 0; a < N_ACTIONS; a++) {
            if (qTable[stateIdx][a] > max) max = qTable[stateIdx][a];
        }
        return max;
    }

    /** Select the greedy action from the applicable set. */
    private int greedyAction(int stateIdx, int[] applicable) {
        int    best    = applicable[0];
        double bestQ   = qTable[stateIdx][applicable[0]];
        for (int a : applicable) {
            if (qTable[stateIdx][a] > bestQ) {
                bestQ = qTable[stateIdx][a];
                best  = a;
            }
        }
        return best;
    }

    /**
     * Compute the set of applicable actions for a state vector.
     *
     * Stereotype mode — filters based on lab-ontology.ttl semantics:
     *  - "turn on X" only when X is currently off
     *  - "turn off X" only when X is currently on
     *  - "open blind"  only when blind is closed AND sunshine ≥ rank 1
     *    (ws:pm_daylight_ingress → ws:ivMinRank = 1)
     *  - "close blind" only when blind is open
     *  - "do nothing"  always
     *
     * Standard mode — all 9 actions always applicable.
     */
    private int[] computeApplicableActions(Object[] stateVec) {
        if (!useStereotypes) {
            int[] all = new int[N_ACTIONS];
            for (int i = 0; i < N_ACTIONS; i++) all[i] = i;
            return all;
        }

        int z1Light  = toInt(stateVec[IDX_Z1LIGHT]);
        int z2Light  = toInt(stateVec[IDX_Z2LIGHT]);
        int z1Blinds = toInt(stateVec[IDX_Z1BLINDS]);
        int z2Blinds = toInt(stateVec[IDX_Z2BLINDS]);
        int sunshine = toInt(stateVec[IDX_SUNSHINE]);

        List<Integer> list = new ArrayList<>();

        // Lights
        if (z1Light == 0) list.add(ACT_Z1LIGHT_ON);
        if (z1Light == 1) list.add(ACT_Z1LIGHT_OFF);
        if (z2Light == 0) list.add(ACT_Z2LIGHT_ON);
        if (z2Light == 1) list.add(ACT_Z2LIGHT_OFF);

        // Blinds — IV constraint: ws:pm_daylight_ingress requires sunshine ≥ rank 1
        if (z1Blinds == 0 && sunshine >= 1) list.add(ACT_Z1BLINDS_OPEN);
        if (z1Blinds == 1)                  list.add(ACT_Z1BLINDS_CLOSE);
        if (z2Blinds == 0 && sunshine >= 1) list.add(ACT_Z2BLINDS_OPEN);
        if (z2Blinds == 1)                  list.add(ACT_Z2BLINDS_CLOSE);

        // Do nothing is always applicable
        list.add(ACT_DO_NOTHING);

        int[] result = new int[list.size()];
        for (int i = 0; i < list.size(); i++) result[i] = list.get(i);
        return result;
    }

    /** Look up a boolean value from two parallel WoT state arrays by URI. */
    private boolean getBoolState(Object[] keys, Object[] values, String targetUri) {
        for (int i = 0; i < keys.length; i++) {
            if (targetUri.equals(keys[i])) {
                return values[i] instanceof Boolean
                        ? (Boolean) values[i]
                        : Boolean.parseBoolean(String.valueOf(values[i]));
            }
        }
        return false; // default off if not found
    }

    private static int toInt(Object o) {
        if (o instanceof Number) return ((Number) o).intValue();
        return Integer.parseInt(String.valueOf(o));
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }
}
