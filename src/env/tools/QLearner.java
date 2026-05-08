package tools;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.logging.Logger;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.OpFeedbackParam;

/**
 * QLearner — CArtAgO artifact implementing decomposed tabular Q-learning for
 * multi-zone illuminance control.
 *
 * State space (8 components):
 *   [Z1Level(0-3), Z2Level(0-3), Z1Light(0/1), Z2Light(0/1),
 *    Z1Blinds(0/1), Z2Blinds(0/1), Spotlight(0/1), sunshine(0-3)]
 *
 * Q-table indexing (all 8 components, sunshine included): 2048 states.
 *   index = Z1Level×512 + Z2Level×128 + Z1Light×64 + Z2Light×32
 *         + Z1Blinds×16 + Z2Blinds×8 + Spotlight×4 + sunshine
 *
 * Action space (dynamically discovered from ontology via StereotypeReasoner):
 *   For each actuator: ON action + OFF action, plus DO_NOTHING as last action.
 *   Action count (nActions) and ordering determined by SPARQL discovery.
 *
 * Decomposed Q-tables (one per zone, N-zone support):
 *   qTables[numZones][N_STATES][nActions]
 *   Action selection uses combinedQ = sum over all zones.
 *
 * Stereotype mode (useStereotypes=true):
 *   - StereotypeReasoner loads lab-ontology.ttl via SPARQL, derives all
 *     initialization penalties and action masks dynamically.
 *   - Replaces all hardcoded rules.
 *
 * Standard mode (useStereotypes=false):
 *   - Q-tables initialized to 0.0, all actions always applicable.
 */
public class QLearner extends Artifact {

    private static final Logger LOGGER = Logger.getLogger(QLearner.class.getName());

    // -----------------------------------------------------------------------
    // Q-learning hyperparameters
    // -----------------------------------------------------------------------
    private double alpha   = 0.1;
    private double gamma   = 0.9;
    private double epsilon = 0.3;
    private double epsilonDecay = 0.995;
    private final double epsilonMin   = 0.01;

    // -----------------------------------------------------------------------
    // State / action dimensions (data-driven from StereotypeReasoner slot registry)
    // -----------------------------------------------------------------------
    // Populated in configureQLearner() after the reasoner has parsed
    // wot-mappings.ttl. nStates = product(domainSizes); strides[i] = product
    // of domainSizes[i+1 .. end]. Replaces the legacy hardcoded N_STATES=2048
    // and IDX_* constants.
    private int   nStates;
    private int   stateVecLen;
    private int[] domainSizes;       // [stateVecLen]
    private int[] strides;           // [stateVecLen] — strides[stateVecLen-1] == 1
    private int[] zoneLevelIndices;  // zone 0-based → state-vector slot
    private int   sunshineIndex;     // -1 if no sunshine slot
    private int nActions;  // dynamically set from StereotypeReasoner

    // -----------------------------------------------------------------------
    // Fields
    // -----------------------------------------------------------------------
    private double[][][] qTables;    // Per-zone decomposed Q-tables [numZones][N_STATES][nActions]
    private int[]        goal;       // target rank per zone, length = numZones
    private boolean    useStereotypes;
    private boolean    maskStrict = false; // if true, hard masking for ablation (default: soft priors)
    private Random     rng;
    private int        firstGoalEpisode = -1;
    private int        goalCount        = 0;

    // StereotypeReasoner — always instantiated for structural discovery
    private StereotypeReasoner reasoner;
    // Action metadata from reasoner (indexed by action index)
    private StereotypeReasoner.ActionInfo[] actionInfos;

    // Convergence metrics
    private List<double[]> episodeMetrics = new ArrayList<>();
    private double episodeCumRewardZ1 = 0;
    private double episodeCumRewardZ2 = 0;
    private int episodeSteps = 0;
    // Wasted-action counters (reset each episode)
    private int episodeWastedByPenalty  = 0; // penalty component fired (regression/no-effect/lost-goal)
    private int episodeWastedByNoEffect = 0; // state vector unchanged after action

    // Last dispatched action index (set by notifyActionDispatched; used by bench cross-zone check)
    private int lastDispatchedAction = -1;

    // Last Bellman update magnitude — max |q_new - q_old| across zones for the
    // most recent calculateQ() invocation. Read by trace plumbing.
    private double lastBellmanDelta      = 0.0;
    private double episodeMaxBellmanDelta = 0.0; // max Bellman delta across all steps in current episode

    // Coverage tracking: per-(state, action) visit counts accumulated during training
    private long[][] visitCounts; // [N_STATES][nActions] — allocated after nActions is known

    // Per-scenario first-goal tracking: map from state-index → first episode number
    private final Map<Integer, Integer> firstGoalByStartState = new java.util.LinkedHashMap<>();
    private int currentEpisodeStartState = -1; // set by beginEpisode(startStateVec)

    // Convergence detection: track max |Q| delta over the last 100 episodes
    private double prevMaxAbsQ      = 0.0;
    private int    convergenceWindow = 100;
    private int    convergenceCount  = 0; // consecutive episodes within threshold
    private static final double CONVERGENCE_THRESHOLD = 1e-3;

    // -----------------------------------------------------------------------
    // CArtAgO initialisation
    // -----------------------------------------------------------------------

    /**
     * Initialise the Q-learner with decomposed per-zone Q-tables.
     *
     * @param goal                     Jason list [Z1TargetRank, Z2TargetRank].
     * @param useStereotypes           true → ontology-guided init + action masking.
     * @param ontologyPaths            Jason list of classpath resource names, e.g. ["lab-ontology.ttl", "wot-mappings.ttl"].
     * @param sunshineSatisfactionProb P(sunshine >= rank 1), e.g. 0.75.
     */
    @OPERATION
    public void configureQLearner(Object[] goal, boolean useStereotypes,
                                  Object[] ontologyPaths, double sunshineSatisfactionProb) {
        this.goal = new int[goal.length];
        for (int i = 0; i < goal.length; i++) this.goal[i] = toInt(goal[i]);
        this.useStereotypes = useStereotypes;
        // Deterministic-by-default; bench/training agents may override via setSeed().
        this.rng            = new Random(42L);

        // Convert Object[] to String[]
        String[] paths = new String[ontologyPaths.length];
        for (int i = 0; i < ontologyPaths.length; i++) {
            paths[i] = ontologyPaths[i].toString();
        }

        // Always instantiate StereotypeReasoner for structural discovery
        // (action list, WoT mappings). Only init penalties and masking are mode-gated.
        reasoner = new StereotypeReasoner(paths, sunshineSatisfactionProb);
        nActions = reasoner.getNumActions();
        actionInfos = reasoner.getAllActions();

        // Pull the state-vector layout from the reasoner slot registry and
        // build strides for the flat Q-table index.
        domainSizes      = reasoner.getStateDomainSizes();
        zoneLevelIndices = reasoner.getZoneLevelIndices();
        sunshineIndex    = reasoner.getSunshineIndex();
        stateVecLen      = domainSizes.length;
        strides          = new int[stateVecLen];
        int prod = 1;
        for (int i = stateVecLen - 1; i >= 0; i--) {
            strides[i] = prod;
            prod *= domainSizes[i];
        }
        nStates = prod;

        int numZones = this.goal.length;
        qTables = new double[numZones][nStates][nActions];
        visitCounts = new long[nStates][nActions];

        if (useStereotypes) {
            initWithStereotypes();
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: ON (ontology-driven)");
            LOGGER.info("  Decomposed Q-tables with per-zone penalties from SPARQL.");
        } else {
            for (double[][] zt : qTables) for (double[] row : zt) Arrays.fill(row, 0.0);
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: OFF (standard zero-init)");
        }

        LOGGER.info("  Goal: " + Arrays.toString(this.goal));
        LOGGER.info("  States=" + nStates + " Actions=" + nActions);
        LOGGER.info("  StateLayout: domain=" + Arrays.toString(domainSizes)
                  + " strides=" + Arrays.toString(strides)
                  + " zoneLevel=" + Arrays.toString(zoneLevelIndices)
                  + " sunshine=" + sunshineIndex);
        LOGGER.info("  α=" + alpha + " γ=" + gamma + " ε=" + epsilon);
    }

    /**
     * Pre-initialise decomposed Q-tables using StereotypeReasoner.
     * Each cell gets a per-zone penalty derived from ontology knowledge.
     */
    private void initWithStereotypes() {
        for (int s = 0; s < nStates; s++) {
            int[] fullSv = decodeState(s);
            for (int z = 0; z < goal.length; z++) {
                for (int a = 0; a < nActions; a++) {
                    qTables[z][s][a] = reasoner.getInitPenaltyForZone(fullSv, a, z, goal);
                }
            }
        }
    }

    // -----------------------------------------------------------------------
    // State encoding / decoding
    // -----------------------------------------------------------------------

    /**
     * Encode raw lab state into an integer state vector of length 8.
     *
     * @param zoneLevels      Integer[] per-zone illuminance ranks.
     * @param sunshineRank    Sunshine rank 0–3.
     * @param boolStateKeys   WoT status URI strings from readLabStatus.
     * @param boolStateValues Corresponding boolean values.
     * @param stateVec        Output: int[8] state vector.
     */
    @OPERATION
    public void encodeState(
            Object[] zoneLevels,
            int      sunshineRank,
            Object[] boolStateKeys,
            Object[] boolStateValues,
            OpFeedbackParam<Object[]> stateVec) {

        // Build state vector dynamically from the slot registry layout
        Object[] sv = new Object[stateVecLen];
        // Initialise all slots to 0
        for (int i = 0; i < stateVecLen; i++) sv[i] = 0;

        // Zone illuminance levels at the slots declared as "zone_level"
        for (int z = 0; z < zoneLevelIndices.length && z < zoneLevels.length; z++) {
            sv[zoneLevelIndices[z]] = toInt(zoneLevels[z]);
        }

        // Sunshine rank
        if (sunshineIndex >= 0 && sunshineIndex < stateVecLen) {
            sv[sunshineIndex] = sunshineRank;
        }

        // Populate boolean component states from WoT state URI → state vector index map
        Map<String, Integer> wotMap = reasoner.getWotStateToSvIndexMap();
        for (int i = 0; i < boolStateKeys.length; i++) {
            String uri = String.valueOf(boolStateKeys[i]);
            Integer svIdx = wotMap.get(uri);
            if (svIdx != null && svIdx < stateVecLen) {
                boolean val = boolStateValues[i] instanceof Boolean
                        ? (Boolean) boolStateValues[i]
                        : Boolean.parseBoolean(String.valueOf(boolStateValues[i]));
                sv[svIdx] = val ? 1 : 0;
            }
        }

        stateVec.set(sv);
        LOGGER.fine("encodeState: " + Arrays.toString(sv));
    }

    // -----------------------------------------------------------------------
    // Core Q-learning operations
    // -----------------------------------------------------------------------

    /**
     * Decomposed Bellman update — updates both per-zone Q-tables internally.
     * Computes per-zone rewards internally (agent no longer computes reward).
     *
     * @param stateVec     Current state vector (int[8]).
     * @param action       Action taken (0–10).
     * @param nextStateVec Next state vector (int[8]).
     */
    @OPERATION
    public void calculateQ(Object[] stateVec, int action, Object[] nextStateVec) {
        int sIdx  = stateVecToIndex(stateVec);
        int sNext = stateVecToIndex(nextStateVec);

        // Decomposed per-zone Bellman updates
        double[] rewards = new double[goal.length];
        boolean anyZoneWastedByPenalty = false;
        double maxAbsDelta = 0.0;
        for (int z = 0; z < goal.length; z++) {
            RewardResult rr = computeZoneReward(z, stateVec, action, nextStateVec);
            rewards[z] = rr.reward;
            if (rr.wastedByPenalty) anyZoneWastedByPenalty = true;
            double maxNextQz = maxQ(qTables[z], sNext);
            double oldQz = qTables[z][sIdx][action];
            double newQz = oldQz + alpha * (rewards[z] + gamma * maxNextQz - oldQz);
            qTables[z][sIdx][action] = newQz;
            double absDelta = Math.abs(newQz - oldQz);
            if (absDelta > maxAbsDelta) maxAbsDelta = absDelta;
        }
        lastBellmanDelta = maxAbsDelta;
        if (maxAbsDelta > episodeMaxBellmanDelta) episodeMaxBellmanDelta = maxAbsDelta;

        // Track cumulative rewards for metrics
        episodeCumRewardZ1 += (goal.length > 0) ? rewards[0] : 0;
        episodeCumRewardZ2 += (goal.length > 1) ? rewards[1] : 0;
        episodeSteps++;

        // Track wasted actions: by penalty (regression / no-effect / lost-goal fired)
        if (anyZoneWastedByPenalty) episodeWastedByPenalty++;
        int[] prevSvArr = toIntArray(stateVec);
        int[] nextSvArr = toIntArray(nextStateVec);
        if (Arrays.equals(prevSvArr, nextSvArr)) episodeWastedByNoEffect++;

        // Increment per-(state, action) visit counter for coverage tracking
        visitCounts[sIdx][action]++;

        // Feed action outcome to IV effectiveness tracker (learns ivMinRank at runtime)
        reasoner.recordActionOutcome(action, prevSvArr, nextSvArr);

        LOGGER.fine("calculateQ: s=" + sIdx + " a=" + action +
                    " rZ1=" + String.format("%.1f", (goal.length > 0 ? rewards[0] : 0.0)) +
                    " rZ2=" + String.format("%.1f", (goal.length > 1 ? rewards[1] : 0.0)) +
                    " s'=" + sNext);
    }

    /**
     * Select an action using ε-greedy policy over combined Q-values (Q1+Q2).
     *
     * @param stateVec  Current state vector (int[8]).
     * @param explore   true → ε-greedy, false → greedy.
     * @param action    Output: selected action index (0–10).
     */
    @OPERATION
    public void getActionFromState(Object[] stateVec, boolean explore,
                                   OpFeedbackParam<Integer> action) {
        int sIdx = stateVecToIndex(stateVec);
        int[] applicable = computeApplicableActions(stateVec);

        int chosen;
        if (explore && rng.nextDouble() < epsilon) {
            chosen = applicable[rng.nextInt(applicable.length)];
            LOGGER.fine("getActionFromState: EXPLORE → action=" + chosen);
        } else {
            chosen = greedyAction(sIdx, applicable);
            LOGGER.fine("getActionFromState: EXPLOIT → action=" + chosen);
        }
        action.set(chosen);
    }

    /**
     * Return the list of applicable actions for the current state.
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
     * Return cross-zone target zones for a given action index.
     * Result is an Integer[] of 0-based zone indices that this action spills into
     * (zones other than the action's primary zone).  Empty array = no cross-zone effects.
     *
     * @param actionIdx  Action index (0–nActions-1).
     * @param targetZones  Output: Integer[] of cross-zone target zone indices (0-based).
     */
    @OPERATION
    public void getCrossZoneEffectForAction(int actionIdx,
                                            OpFeedbackParam<Object[]> targetZones) {
        List<StereotypeReasoner.CrossZoneEffect> effects = reasoner.getCrossZoneEffects();
        List<Integer> result = new ArrayList<>();
        for (StereotypeReasoner.CrossZoneEffect cz : effects) {
            if (cz.actionIndex == actionIdx) {
                result.add(cz.targetZoneIdx);
            }
        }
        Object[] arr = new Object[result.size()];
        for (int i = 0; i < result.size(); i++) arr[i] = result.get(i);
        targetZones.set(arr);
    }

    /**
     * Notify the QLearner that a specific action was just dispatched during execution.
     * Stores the index so the bench agent can query cross-zone effects after the step.
     *
     * @param actionIdx  Action index that was dispatched.
     */
    @OPERATION
    public void notifyActionDispatched(int actionIdx) {
        lastDispatchedAction = actionIdx;
    }

    /**
     * Retrieve the action index recorded by the last notifyActionDispatched() call.
     * Returns −1 if never set.
     */
    @OPERATION
    public void getLastDispatchedAction(OpFeedbackParam<Integer> actionIdx) {
        actionIdx.set(lastDispatchedAction);
    }

    /**
     * Per-slot ontology prediction for the change a given action SHOULD cause.
     * Delegates to {@link StereotypeReasoner#getActionPrediction(int[], int)}.
     * Returns an Integer[] of length stateVecLen with values in {-1, 0, +1}
     * (see {@code StereotypeReasoner.getActionPrediction} for semantics).
     *
     * @param stateVec    Current state vector (Object[]).
     * @param actionIdx   Candidate action index.
     * @param predDelta   Output: Object[] of Integer per slot (directional Δ).
     */
    @OPERATION
    public void getPredictedDelta(Object[] stateVec, int actionIdx,
                                  OpFeedbackParam<Object[]> predDelta) {
        int[] sv = toIntArray(stateVec);
        int[] pred = reasoner.getActionPrediction(sv, actionIdx);
        Object[] out = new Object[pred.length];
        for (int i = 0; i < pred.length; i++) out[i] = pred[i];
        predDelta.set(out);
    }

    /**
     * Magnitude of the most recent Bellman update — max |q_new − q_old| across
     * zones from the latest {@link #calculateQ}. 0.0 if no update has run.
     */
    @OPERATION
    public void getLastQDelta(OpFeedbackParam<Double> qDelta) {
        qDelta.set(lastBellmanDelta);
    }

    /** Number of actions currently configured. */
    @OPERATION
    public void getNumActions(OpFeedbackParam<Integer> n) {
        n.set(nActions);
    }

    /**
     * Reseed the action-selection RNG. Called once after configureQLearner
     * to make ε-greedy exploration reproducible across benchmark runs.
     */
    @OPERATION
    public void setSeed(long seed) {
        this.rng = new Random(seed);
        LOGGER.info("QLearner RNG reseeded with seed=" + seed);
    }

    /** Length of the state vector. */
    @OPERATION
    public void getStateVecLen(OpFeedbackParam<Integer> n) {
        n.set(stateVecLen);
    }

    /**
     * Bulk action metadata for the {@code StereotypeLearner} initialisation.
     * Each output array has length {@code nActions} and is indexed by action
     * index. Strings are returned for the WoT URI / state URI / label fields;
     * the activation flag is returned as Boolean per slot.
     *
     * @param wotActionTypes  Output: Object[] of String (wot:actionType URI per action).
     * @param actionValues    Output: Object[] of Boolean (true=ON/OPEN, false=OFF/CLOSE).
     * @param actionLabels    Output: Object[] of String (human label).
     */
    @OPERATION
    public void getActionMetadataForLearner(OpFeedbackParam<Object[]> wotActionTypes,
                                            OpFeedbackParam<Object[]> actionValues,
                                            OpFeedbackParam<Object[]> actionLabels) {
        Object[] uris   = new Object[nActions];
        Object[] vals   = new Object[nActions];
        Object[] labels = new Object[nActions];
        for (int i = 0; i < nActions; i++) {
            StereotypeReasoner.ActionInfo ai = actionInfos[i];
            uris[i]   = (ai.wotActionType != null) ? ai.wotActionType : "";
            vals[i]   = ai.wotValue;
            labels[i] = (ai.label != null) ? ai.label : ("action_" + i);
        }
        wotActionTypes.set(uris);
        actionValues.set(vals);
        actionLabels.set(labels);
    }

    /**
     * Classify which weakness fingerprints fired during a single (before, action,
     * after) transition. Returns a deduplicated Object[] of String fingerprint
     * names drawn from {@code w1_unmodelled, w2_inversion, w3_delayed,
     * w4_dropped, w5_topology}. The bench agent intersects this with the active
     * profile's weakness_flags belief to gate which signals to actually record.
     *
     * Each tag has a single, distinct trigger so heatmap counts are
     * discriminative within a lab (not just across labs):
     *   • w1_unmodelled — zone delta in a zone the action's stereotype declares
     *                     it affects but with zero predicted Δ (hidden ambient
     *                     effect), OR any zone delta when the action is
     *                     DO_NOTHING (uncorrelated background change).
     *   • w5_topology   — zone delta in a zone NOT in {@code ai.affectedZones}
     *                     (cross-zone feed missing from ontology graph).
     *   • w2_inversion  — observed and predicted Δ have opposite signs.
     *   • w3_delayed    — predicted Δ ≠ 0 but observed Δ = 0 in this tick AND
     *                     the actuator bit DID flip as predicted (so the
     *                     command executed but its effect is delayed).
     *   • w4_dropped    — actuator bit was predicted to flip but did not flip
     *                     (command silently dropped, e.g. by power budget).
     * W6 (heat / comfort) is NOT classified here; it is measured directly
     * from zone temperatures by the bench agent via recordComfortDeviation.
     */
    @OPERATION
    public void classifyWeaknesses(Object[] stateVecBefore,
                                   Object[] stateVecAfter,
                                   int actionIdx,
                                   OpFeedbackParam<Object[]> fired) {
        java.util.LinkedHashSet<String> tags = new java.util.LinkedHashSet<>();
        if (actionIdx < 0 || actionIdx >= nActions) {
            fired.set(new Object[0]);
            return;
        }
        int[] before = toIntArray(stateVecBefore);
        int[] after  = toIntArray(stateVecAfter);
        int[] pred   = reasoner.getActionPrediction(before, actionIdx);
        StereotypeReasoner.ActionInfo ai = actionInfos[actionIdx];

        // DO_NOTHING (no actuator bit) — only background drift can fire,
        // which is the hallmark of W1 (hidden / unmodelled effect).
        if (ai.stateVecBitIndex < 0) {
            for (int z = 0; z < zoneLevelIndices.length; z++) {
                int slot = zoneLevelIndices[z];
                if (slot < 0 || slot >= before.length) continue;
                if (after[slot] - before[slot] != 0) {
                    tags.add("w1_unmodelled");
                    break;
                }
            }
            fired.set(tags.toArray(new Object[0]));
            return;
        }

        // Did the actuator bit flip as predicted? Used by W3/W4 split.
        boolean bitFlippedAsPredicted = false;
        boolean bitDropped            = false;
        int bitSlot = ai.stateVecBitIndex;
        if (bitSlot >= 0 && bitSlot < before.length && bitSlot < after.length) {
            int bitPred = (bitSlot < pred.length) ? pred[bitSlot] : 0;
            int bitObs  = after[bitSlot] - before[bitSlot];
            if (bitPred != 0) {
                if (bitObs == bitPred) bitFlippedAsPredicted = true;
                else if (bitObs == 0)  bitDropped            = true;
            }
        }
        if (bitDropped) {
            tags.add("w4_dropped");
        }

        // Per-zone-level diagnostics — each tag fires on a distinct condition.
        java.util.Set<Integer> aff =
                (ai.affectedZones != null) ? ai.affectedZones : java.util.Collections.emptySet();
        for (int z = 0; z < zoneLevelIndices.length; z++) {
            int slot = zoneLevelIndices[z];
            if (slot < 0 || slot >= before.length) continue;
            int obsD  = after[slot] - before[slot];
            int predD = (slot < pred.length) ? pred[slot] : 0;

            // W2 inversion: opposite-sign Δ in any zone.
            if (obsD != 0 && predD != 0 && (long) obsD * (long) predD < 0L) {
                tags.add("w2_inversion");
            }
            // W1 vs W5: zone moved but ontology didn't predict it.
            //   - zone IS in stereotype's footprint  → W1 (effect under-modelled)
            //   - zone is NOT in stereotype's footprint → W5 (cross-zone feed missing)
            if (obsD != 0 && predD == 0) {
                if (aff.contains(z)) tags.add("w1_unmodelled");
                else                 tags.add("w5_topology");
            }
            // W3 delayed: predicted Δ but observed Δ is much smaller in
            // magnitude than predicted this tick (ramp not complete), AND the
            // actuator bit flipped as expected (so the command went through —
            // the response is just deferred). Threshold |obsD| < 0.5*|predD|
            // covers both obsD == 0 and partial-ramp cases (e.g. brightness
            // 1/5, 2/5, 3/5 of full while bit is on but level still climbing).
            // If the bit was dropped, that's W4, not W3, so we already
            // recorded it above and skip here.
            if (predD != 0 && Math.abs(obsD) < 0.5 * Math.abs(predD)
                    && bitFlippedAsPredicted) {
                tags.add("w3_delayed");
            }
        }

        Object[] out = tags.toArray(new Object[0]);
        fired.set(out);
    }

    /**
     * Map a WoT action type URI to the corresponding action index.
     * Returns −1 if not found.
     */
    @OPERATION
    public void wotTypeToActionIndex(String wotType, boolean wotValue,
                                     OpFeedbackParam<Integer> actionIdx) {
        for (int i = 0; i < nActions; i++) {
            StereotypeReasoner.ActionInfo ai = actionInfos[i];
            if (wotType.equals(ai.wotActionType) && ai.wotValue == wotValue) {
                actionIdx.set(i);
                return;
            }
        }
        actionIdx.set(-1);
    }

    /**
     * Check whether an action has cross-zone effects (true/false).
     * A cross-zone spill step means the action was dispatched and it nominally
     * targets at least one zone but also feeds another zone according to the ontology.
     */
    @OPERATION
    public void actionHasCrossZoneEffect(int actionIdx, OpFeedbackParam<Boolean> hasCrossZone) {
        List<StereotypeReasoner.CrossZoneEffect> effects = reasoner.getCrossZoneEffects();
        for (StereotypeReasoner.CrossZoneEffect cz : effects) {
            if (cz.actionIndex == actionIdx) {
                hasCrossZone.set(true);
                return;
            }
        }
        hasCrossZone.set(false);
    }

    /**
     * Check if a cross-zone action moved the spill-target zone away from its goal.
     * Combines ontology cross-zone topology with observed level changes.
     *
     * @param actionIdx       Index of the dispatched action.
     * @param prevZoneLevels  Zone levels before the action (Object[]).
     * @param currZoneLevels  Zone levels after the action (Object[]).
     * @param zoneTargets     Target ranks per zone (Object[]).
     * @param interference    Output: true if cross-zone action pushed a spill-zone away from target.
     */
    @OPERATION
    public void checkCrossZoneInterference(int actionIdx,
                                           Object[] prevZoneLevels,
                                           Object[] currZoneLevels,
                                           Object[] zoneTargets,
                                           OpFeedbackParam<Boolean> interference) {
        List<StereotypeReasoner.CrossZoneEffect> effects = reasoner.getCrossZoneEffects();
        for (StereotypeReasoner.CrossZoneEffect cz : effects) {
            if (cz.actionIndex != actionIdx) continue;
            int tz = cz.targetZoneIdx;
            if (tz < 0 || tz >= prevZoneLevels.length) continue;
            int prev   = toInt(prevZoneLevels[tz]);
            int curr   = toInt(currZoneLevels[tz]);
            int target = toInt(zoneTargets[tz]);
            // Interference: zone moved further from target, OR was at target and moved away
            if (Math.abs(curr - target) > Math.abs(prev - target)
                    || (prev == target && curr != target)) {
                interference.set(true);
                return;
            }
        }
        interference.set(false);
    }

    /**
     * Map a numeric action index to WoT action type URI and boolean value.
     *
     * @param action    Action index (0–10).
     * @param wotType   Output: WoT action URI, or "none" for do-nothing.
     * @param value     Output: boolean payload.
     */
    @OPERATION
    public void actionToWoT(int action,
                            OpFeedbackParam<String>  wotType,
                            OpFeedbackParam<Boolean> value) {
        if (action < 0 || action >= nActions) {
            wotType.set("none");
            value.set(false);
            return;
        }
        StereotypeReasoner.ActionInfo ai = actionInfos[action];
        wotType.set(ai.wotActionType != null ? ai.wotActionType : "none");
        value.set(ai.wotValue);
    }

    /**
     * Check whether both zone levels match the goal (terminal state).
     */
    @OPERATION
    public void isTerminal(Object[] stateVec, OpFeedbackParam<Boolean> terminal) {
        boolean t = true;
        for (int z = 0; z < goal.length; z++) {
            if (toInt(stateVec[zoneLevelIndices[z]]) != goal[z]) { t = false; break; }
        }
        terminal.set(t);
    }

    /**
     * Override the epsilon decay rate. Call after configureQLearner() to apply
     * per-profile training parameters.
     */
    @OPERATION
    public void setEpsilonDecay(double decay) {
        this.epsilonDecay = decay;
        LOGGER.info("setEpsilonDecay: epsilonDecay=" + decay);
    }

    /**
     * Decay ε by the configured decay factor. Call once per episode.
     */
    @OPERATION
    public void decayEpsilon() {
        epsilon = Math.max(epsilonMin, epsilon * epsilonDecay);
        LOGGER.fine("decayEpsilon: ε=" + epsilon);
    }

    /**
     * Record that the goal was reached during a training episode.
     */
    @OPERATION
    public void notifyGoalReached(int episodeNum) {
        goalCount++;
        if (firstGoalEpisode < 0) {
            firstGoalEpisode = episodeNum;
            LOGGER.info("notifyGoalReached: first goal reached in episode " + episodeNum);
        }
        // Track first-goal per start-state (for per-scenario sample-efficiency analysis)
        if (currentEpisodeStartState >= 0
                && !firstGoalByStartState.containsKey(currentEpisodeStartState)) {
            firstGoalByStartState.put(currentEpisodeStartState, episodeNum);
        }
        LOGGER.fine("notifyGoalReached: ep=" + episodeNum + " totalGoals=" + goalCount);
    }

    // -----------------------------------------------------------------------
    // Convergence metrics
    // -----------------------------------------------------------------------

    /**
     * Reset per-episode accumulators. Call at start of each training episode.
     */
    @OPERATION
    public void beginEpisode() {
        episodeCumRewardZ1 = 0;
        episodeCumRewardZ2 = 0;
        episodeSteps = 0;
        episodeWastedByPenalty  = 0;
        episodeWastedByNoEffect = 0;
        currentEpisodeStartState = -1;
        episodeMaxBellmanDelta = 0.0;
    }

    /**
     * Reset per-episode accumulators and record the starting state index.
     * Use this variant when training with fixed-scenario start states so that
     * first-goal tracking can be broken down per scenario.
     *
     * @param startStateVec  State vector (int[8]) at the beginning of this episode.
     */
    @OPERATION
    public void beginEpisodeFromState(Object[] startStateVec) {
        episodeCumRewardZ1 = 0;
        episodeCumRewardZ2 = 0;
        episodeSteps = 0;
        episodeWastedByPenalty  = 0;
        episodeWastedByNoEffect = 0;
        currentEpisodeStartState = stateVecToIndex(startStateVec);
        episodeMaxBellmanDelta = 0.0;
    }

    /**
     * Record episode metrics. Call at end of each training episode.
     * Columns: Episode, Steps, RewardZ1, RewardZ2, GoalReached, Epsilon, WastedByPenalty, WastedByNoEffect
     */
    @OPERATION
    public void endEpisode(int episodeNum, boolean goalReached) {
        episodeMetrics.add(new double[]{
            episodeNum,
            episodeSteps,
            episodeCumRewardZ1,
            episodeCumRewardZ2,
            goalReached ? 1.0 : 0.0,
            epsilon,
            episodeWastedByPenalty,
            episodeWastedByNoEffect
        });
        // Update convergence detector: use max per-step Bellman delta from this episode
        convergenceCount = (episodeMaxBellmanDelta < CONVERGENCE_THRESHOLD) ? convergenceCount + 1 : 0;
    }

    /**
     * Check whether the Q-table has converged (max |ΔQ| < 1e-3 for 100 consecutive episodes).
     *
     * @param converged  Output: true if converged, false otherwise.
     */
    @OPERATION
    public void hasConverged(OpFeedbackParam<Boolean> converged) {
        converged.set(convergenceCount >= convergenceWindow);
    }

    /**
     * Save convergence metrics to a CSV file.
     * Columns: Episode, Steps, RewardZ1, RewardZ2, GoalReached, Epsilon, WastedByPenalty, WastedByNoEffect
     */
    @OPERATION
    public void saveMetrics(String filename) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("Episode,Steps,RewardZ1,RewardZ2,GoalReached,Epsilon,WastedByPenalty,WastedByNoEffect");
            for (double[] m : episodeMetrics) {
                pw.printf("%d,%d,%.2f,%.2f,%d,%.6f,%d,%d%n",
                    (int) m[0], (int) m[1], m[2], m[3], (int) m[4], m[5],
                    (int) m[6], (int) m[7]);
            }
            pw.println();
            pw.println("# Summary");
            pw.println("# FirstGoalEpisode," + (firstGoalEpisode < 0 ? "none" : firstGoalEpisode));
            pw.println("# TotalGoalCount," + goalCount);
            int last100Goals = 0;
            int start = Math.max(0, episodeMetrics.size() - 100);
            for (int i = start; i < episodeMetrics.size(); i++) {
                if (episodeMetrics.get(i)[4] > 0.5) last100Goals++;
            }
            int window = episodeMetrics.size() - start;
            pw.println("# GoalRate_last100," + (window > 0 ? String.format("%.2f", (double) last100Goals / window) : "N/A"));
            LOGGER.info("saveMetrics: written to " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveMetrics: failed to write " + filename + " — " + e.getMessage());
        }
    }

    // -----------------------------------------------------------------------
    // Q-table save
    // -----------------------------------------------------------------------

    /**
     * Save combined Q-table (Q1+Q2) and per-zone tables to CSV files.
     */
    @OPERATION
    public void saveQTable(String filename) {
        // Build action names dynamically from reasoner-discovered metadata
        String[] actionNames = new String[nActions];
        for (int i = 0; i < nActions; i++) {
            actionNames[i] = actionInfos[i].label;
        }
        saveQTableToFile(filename, actionNames, true, null);
        String base = filename.replace(".csv", "");
        for (int z = 0; z < qTables.length; z++) {
            saveQTableToFile(base + "_zone" + (z + 1) + ".csv", actionNames, false, qTables[z]);
        }
    }

    private void saveQTableToFile(String filename, String[] actionNames,
                                  boolean combined, double[][] singleTable) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.print("StateIndex");
            for (String a : actionNames) pw.print("," + a);
            pw.println();
            for (int s = 0; s < nStates; s++) {
                boolean anyNonZero = false;
                for (int a = 0; a < nActions; a++) {
                    double v = combined ? combinedQ(s, a) : singleTable[s][a];
                    if (v != 0.0) { anyNonZero = true; break; }
                }
                if (!anyNonZero) continue;
                pw.print(s);
                for (int a = 0; a < nActions; a++) {
                    double v = combined ? combinedQ(s, a) : singleTable[s][a];
                    pw.print("," + String.format("%.2f", v));
                }
                pw.println();
            }
            LOGGER.info("saveQTable: written to " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveQTable: failed to write " + filename + " — " + e.getMessage());
        }
    }

    /**
     * Save IV effectiveness counters (ivTrialCount / ivSuccessCount) to a JSON file.
     * Must be called after training to persist stereotype runtime learning.
     *
     * @param filename  Destination path (e.g. "iv_stats_stereotypes_true.json").
     */
    @OPERATION
    public void saveIVStats(String filename) {
        reasoner.saveIVStats(filename);
    }

    /**
     * Load IV effectiveness counters from a JSON file saved by saveIVStats().
     * Must be called in bench mode before execution so the reasoner can use
     * the effectiveness data learned during training.
     *
     * @param filename  Source path (e.g. "iv_stats_stereotypes_true.json").
     */
    @OPERATION
    public void loadIVStats(String filename) {
        reasoner.loadIVStats(filename);
    }

    /**
     * Save per-(state, action) visit counts accumulated during training.
     * Columns: StateIndex, Action0, Action1, ..., ActionN  (only rows where any > 0).
     *
     * @param filename  Destination CSV path (e.g. "coverage_stereotypes_true.csv").
     */
    @OPERATION
    public void saveCoverage(String filename) {
        String[] actionNames = new String[nActions];
        for (int i = 0; i < nActions; i++) actionNames[i] = actionInfos[i].label;

        long visitedStates  = 0;
        long totalVisits    = 0;
        long visitedSA      = 0;

        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.print("StateIndex");
            for (String a : actionNames) pw.print("," + a);
            pw.println(",TotalVisits");

            for (int s = 0; s < nStates; s++) {
                long rowSum = 0;
                for (int a = 0; a < nActions; a++) rowSum += visitCounts[s][a];
                if (rowSum == 0) continue;
                visitedStates++;
                totalVisits += rowSum;
                pw.print(s);
                for (int a = 0; a < nActions; a++) {
                    pw.print("," + visitCounts[s][a]);
                    if (visitCounts[s][a] > 0) visitedSA++;
                }
                pw.println("," + rowSum);
            }

            pw.println();
            pw.println("# VisitedStates," + visitedStates + " / " + nStates);
            pw.println("# VisitedStateActionPairs," + visitedSA + " / " + (nStates * nActions));
            pw.println("# TotalVisits," + totalVisits);
            LOGGER.info("saveCoverage: " + visitedStates + " visited states, "
                       + visitedSA + " (s,a) pairs → " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveCoverage: failed to write " + filename + " — " + e.getMessage());
        }
    }

    /**
     * Save the first episode at which the goal was reached from each recorded start state.
     * Only populated if {@link #beginEpisodeFromState(Object[])} was used during training.
     *
     * Columns: StartStateIndex, FirstGoalEpisode
     *
     * @param filename  Destination CSV path (e.g. "first_goal_stereotypes_true.csv").
     */
    @OPERATION
    public void saveFirstGoalPerScenario(String filename) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("StartStateIndex,FirstGoalEpisode");
            for (Map.Entry<Integer, Integer> entry : firstGoalByStartState.entrySet()) {
                pw.println(entry.getKey() + "," + entry.getValue());
            }
            pw.println();
            pw.println("# TotalDistinctStartStates," + firstGoalByStartState.size());
            LOGGER.info("saveFirstGoalPerScenario: " + firstGoalByStartState.size()
                       + " entries → " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveFirstGoalPerScenario: failed to write " + filename
                          + " — " + e.getMessage());
        }
    }

    /**
     * Return a one-line status summary.
     */
    @OPERATION
    public void getStatus(OpFeedbackParam<String> summary) {
        summary.set("mode=" + (useStereotypes ? "STEREOTYPE" : "STANDARD")
                  + " maskStrict=" + maskStrict
                  + " ε=" + String.format("%.4f", epsilon)
                  + " goal=" + Arrays.toString(goal)
                  + " goalsReached=" + goalCount
                  + " firstGoalEp=" + (firstGoalEpisode < 0 ? "none" : firstGoalEpisode));
    }

    /**
     * Enable or disable strict hard-masking mode (for ablation studies).
     * When maskStrict=true: restores the original hard-masking behaviour (applicable
     * actions are filtered; invalid actions never explored).
     * When maskStrict=false (default): uses soft priors — all actions reachable
     * during exploration, but greedy selection adds additive bias from ontology.
     *
     * @param strict  true → hard masking, false → soft priors.
     */
    @OPERATION
    public void setMaskStrict(boolean strict) {
        this.maskStrict = strict;
        LOGGER.info("QLearner.setMaskStrict: maskStrict=" + strict);
    }

    /**
     * Load the combined Q-table from a CSV file saved by saveQTable().
     * Only the combined table (sum of per-zone tables) is stored, so this
     * distributes the loaded values equally across all zone tables.
     * Use this operation to restore a pre-trained policy for benchmark execution.
     *
     * @param filename  Path to the CSV file (e.g. "qtable_final_stereotypes_true.csv").
     */
    @OPERATION
    public void loadQTable(String filename) {
        // Prefer per-zone files (e.g. qtable_final_stereotypes_true_zone1.csv)
        // produced by saveQTable. Each zone file contains the learned Q-values
        // for that zone directly and avoids the lossy divide-by-numZones step.
        String base = filename.replace(".csv", "");
        boolean zoneFilesExist = true;
        for (int z = 0; z < qTables.length; z++) {
            if (!new java.io.File(base + "_zone" + (z + 1) + ".csv").exists()) {
                zoneFilesExist = false;
                break;
            }
        }
        if (zoneFilesExist) {
            for (int z = 0; z < qTables.length; z++) {
                loadQTableIntoZone(base + "_zone" + (z + 1) + ".csv", z);
            }
            LOGGER.info("loadQTable: loaded per-zone files for base=" + base);
        } else {
            // Fall back: load combined file, distribute equally across zones
            loadQTableCombined(filename);
        }
    }

    private void loadQTableIntoZone(String filename, int zoneIdx) {
        try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.FileReader(filename))) {
            String header = br.readLine();
            if (header == null) { LOGGER.warning("loadQTableIntoZone: empty " + filename); return; }
            String[] cols = header.split(",");
            int numActionCols = cols.length - 1;
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] parts = line.split(",");
                int stateIdx = Integer.parseInt(parts[0].trim());
                if (stateIdx < 0 || stateIdx >= nStates) continue;
                for (int a = 0; a < Math.min(numActionCols, nActions); a++) {
                    qTables[zoneIdx][stateIdx][a] = Double.parseDouble(parts[a + 1].trim());
                }
            }
            LOGGER.info("loadQTableIntoZone: loaded " + filename + " → zone " + zoneIdx);
        } catch (IOException | NumberFormatException e) {
            LOGGER.warning("loadQTableIntoZone: failed " + filename + " — " + e.getMessage());
        }
    }

    private void loadQTableCombined(String filename) {
        try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.FileReader(filename))) {
            String header = br.readLine();
            if (header == null) { LOGGER.warning("loadQTableCombined: empty " + filename); return; }
            String[] cols = header.split(",");
            int numActionCols = cols.length - 1;
            int numZones = qTables.length;
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] parts = line.split(",");
                int stateIdx = Integer.parseInt(parts[0].trim());
                if (stateIdx < 0 || stateIdx >= nStates) continue;
                for (int a = 0; a < Math.min(numActionCols, nActions); a++) {
                    double combined = Double.parseDouble(parts[a + 1].trim());
                    double perZone = combined / numZones;
                    for (int z = 0; z < numZones; z++) {
                        qTables[z][stateIdx][a] = perZone;
                    }
                }
            }
            LOGGER.info("loadQTableCombined: loaded from " + filename);
        } catch (IOException | NumberFormatException e) {
            LOGGER.severe("loadQTableCombined: failed " + filename + " — " + e.getMessage());
        }
    }

    // -----------------------------------------------------------------------
    // Per-zone reward computation
    // -----------------------------------------------------------------------

    /**
     * Carries the reward for one zone plus a diagnostic flag indicating whether
     * a penalty component (regression / no-effect / lost-goal) fired.
     * Used by calculateQ() to accurately track WastedByPenalty.
     */
    private static class RewardResult {
        final double  reward;
        final boolean wastedByPenalty;
        RewardResult(double reward, boolean wastedByPenalty) {
            this.reward = reward;
            this.wastedByPenalty = wastedByPenalty;
        }
    }

    private RewardResult computeZoneReward(int zoneIdx, Object[] prevStateVec,
                                           int action, Object[] nextStateVec) {
        // Zone level is stored at zoneLevelIndices[zoneIdx] in the state vector
        int prevLevel = toInt(prevStateVec[zoneLevelIndices[zoneIdx]]);
        int nextLevel = toInt(nextStateVec[zoneLevelIndices[zoneIdx]]);
        int target = goal[zoneIdx];

        double  r      = 0.0;
        boolean wasted = false;

        // Per-step cost encourages reaching goal quickly
        r -= 1.0;

        // Rank-distance-relative progress reward / regression penalty.
        // Using gap-change × 40 keeps the signal proportional to rank distance
        // and comparable across zones (both bounded by ±120 per step for rank 0–3).
        int prevDist = Math.abs(prevLevel - target);
        int nextDist = Math.abs(nextLevel - target);
        int gapChange = prevDist - nextDist; // positive = progress, negative = regression
        if (gapChange != 0) {
            r += gapChange * 40.0;
            if (gapChange < 0) wasted = true; // regression component fired
        }

        // Terminal: zone reached target
        if (nextLevel == target) {
            r += 200.0;
        }

        // Lost-goal penalty: was at target, now moved away
        if (prevLevel == target && nextLevel != target) {
            r -= 200.0;
            wasted = true;
        }

        // No-effect penalty (per-zone): action is supposed to affect this zone but
        // the zone level did not change and the zone is not at goal.
        // Uses affectedZones so that e.g. SetZ2Light=false only penalises Z2, not Z1.
        if (actionInfos[action].wotActionType != null
                && actionInfos[action].affectedZones.contains(zoneIdx)
                && prevLevel == nextLevel
                && nextLevel != target) {
            r -= 10.0;
            wasted = true; // no-effect component fired
        }

        // Stagnation penalty when not at goal
        if (actionInfos[action].wotActionType == null && nextLevel != target) {
            r -= 5.0;
        }

        return new RewardResult(r, wasted);
    }

    // -----------------------------------------------------------------------
    // Private helpers
    // -----------------------------------------------------------------------

    /** Convert state vector to flat Q-table index using ontology-driven strides. */
    private int stateVecToIndex(Object[] sv) {
        int idx = 0;
        for (int i = 0; i < stateVecLen; i++) {
            int v = clamp(toInt(sv[i]), 0, domainSizes[i] - 1);
            idx += v * strides[i];
        }
        return idx;
    }

    /** Decode a flat state index back to a state vector using strides. */
    private int[] decodeState(int idx) {
        int[] out = new int[stateVecLen];
        for (int i = 0; i < stateVecLen; i++) {
            out[i] = idx / strides[i];
            idx %= strides[i];
        }
        return out;
    }

    /** Maximum Q-value over all actions for a given table and state index. */
    private double maxQ(double[][] table, int stateIdx) {
        double max = Double.NEGATIVE_INFINITY;
        for (int a = 0; a < nActions; a++) {
            if (table[stateIdx][a] > max) max = table[stateIdx][a];
        }
        return max;
    }

    /** Combined Q-value (sum over all zones) for action selection. */
    private double combinedQ(int stateIdx, int action) {
        double sum = 0.0;
        for (double[][] zt : qTables) sum += zt[stateIdx][action];
        return sum;
    }

    /**
     * Compute applicable actions. Delegates to StereotypeReasoner for masking
     * in stereotype mode; returns all actions in standard mode.
     * In soft-prior mode (maskStrict=false), always returns all actions so that
     * exploration is unblocked — the prior bias only affects greedy selection.
     */
    private int[] computeApplicableActions(Object[] stateVec) {
        if (!useStereotypes || !maskStrict) {
            // All actions applicable — priors are applied in greedy selection only
            int[] all = new int[nActions];
            for (int i = 0; i < nActions; i++) all[i] = i;
            return all;
        }
        // Hard masking for ablation (mask_strict=true)
        int[] sv = toIntArray(stateVec);
        return reasoner.getApplicableActions(sv);
    }

    /** Select greedy action from applicable set using combined Q + soft priors. */
    private int greedyAction(int stateIdx, int[] applicable) {
        // Retrieve priors only in soft-prior stereotype mode
        double[] priors = null;
        if (useStereotypes && !maskStrict) {
            // Decode state vector from index (needed for priors)
            int[] sv = decodeState(stateIdx);
            priors = reasoner.getActionPriors(sv);
        }

        int    best  = applicable[0];
        double bestQ = combinedQ(stateIdx, applicable[0])
                     + (priors != null ? priors[applicable[0]] : 0.0);
        for (int a : applicable) {
            double q = combinedQ(stateIdx, a) + (priors != null ? priors[a] : 0.0);
            if (q > bestQ) {
                bestQ = q;
                best  = a;
            }
        }
        return best;
    }

    private static int[] toIntArray(Object[] arr) {
        int[] result = new int[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = toInt(arr[i]);
        return result;
    }

    private static int toInt(Object o) {
        if (o instanceof Number) return ((Number) o).intValue();
        return Integer.parseInt(String.valueOf(o));
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }
}
