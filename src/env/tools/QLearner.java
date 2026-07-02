package tools;

import java.io.BufferedWriter;
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

    // Per-step reward clip (override with -Dreward.clip=...)
    private static final double REWARD_CLIP = parseDoubleProp("reward.clip", 50.0);
    // Multiplier applied to stereotype priors during greedy selection
    // (override with -Dstereo.priorScale=...).
    // Audit Step 3b §S3b-4: default lowered from 5.0 → 1.0 so the bench-time
    // soft-prior magnitude on an IV-unsat action becomes O(combinedQ Bellman
    // swing per visit) instead of dominating it. Sysprop / run_config still
    // overrides; H5 ablation uses 0.0.
    private static final double STEREO_PRIOR_SCALE = parseDoubleProp("stereo.priorScale", 1.0);
    // Phase 4 (lab5 energy): weight of the NON-FADING energy prior. Unlike the
    // stereotype prior above (which decays over episodes and fades per visited
    // cell so Bellman learning can override it), this term is a PERMANENT
    // structural bias of magnitude ENERGY_PRIOR_WEIGHT * ws:energyCost
    // subtracted from the greedy Q of every activation action that drives a
    // costed actuator. Energy is deliberately NOT part of the Q-reward, so this
    // is the ONLY channel through which a KG-primed agent can prefer the cheaper
    // of two optically-identical lamps (or zero-energy blinds) — including at
    // benchmark, once the stereotype prior has faded to its floor. Default
    // 0.0 = OFF; only lab5's KG declares ws:energyCost, so labs 1-4 are
    // unaffected even when this is > 0. The run_config "phase4" profile sets
    // stereo.energyPriorWeight=2.0 (override with -Dstereo.energyPriorWeight).
    private static final double ENERGY_PRIOR_WEIGHT = parseDoubleProp("stereo.energyPriorWeight", 0.0);
    // Total episodes used to decay the stereotype prior weight to its floor.
    // S2-3 (audit Step 2): made non-final so it can be coupled to num_episodes
    // at runtime via setPriorDecayEpisodes() / setTrainingBudgetEpisodes().
    // -1 (default) means "auto: 0.25 * num_episodes once the agent reports it";
    // any positive value from -Dstereo.priorDecayEpisodes wins and disables auto.
    private static final int    PRIOR_DECAY_EPISODES_PROP =
        parseIntProp("stereo.priorDecayEpisodes", -1);
    private int                 priorDecayEpisodes        =
        PRIOR_DECAY_EPISODES_PROP > 0 ? PRIOR_DECAY_EPISODES_PROP : 2500;
    // Floor for the prior weight at the end of decay.
    // Audit Step 3b §S3b-2: default lowered from 0.1 → 0.0 so the late-training
    // and bench (post-S3b-1) regimes do not carry a permanent prior bias.
    // Sysprop / run_config still overrides for ablations.
    private static final double PRIOR_DECAY_FLOOR    = parseDoubleProp("stereo.priorDecayFloor", 0.0);
    // S2-4 (audit Step 2): per-(state,action) visit threshold above which the
    // stereotype prior fades to zero. min(1, fadeVisits / visits[s][a]).
    // 0 (default) disables the per-cell fade and preserves legacy behaviour.
    // Recommended value: 25 — above this the local Bellman target ±12.5 has had
    // enough averaging weight to out-vote the prior on its own.
    private static final int    PRIOR_FADE_VISITS = parseIntProp("stereo.priorFadeVisits", 25);

    // -----------------------------------------------------------------------
    // Reward shaping (Ng, Harada & Russell 1999 — Potential-Based Reward
    // Shaping). When reward.shaping=pbrs, every per-zone Bellman update
    // receives an extra term F_z = gamma * Phi_z(s') - Phi_z(s) with
    //   Phi_z(s) = -|level_z(s) - target_z|
    // This shaping is *policy-invariant* (PBRS theorem): the converged
    // optimal policy is identical with and without shaping, so it cannot
    // bias asymptotic performance — only the convergence path. Use this
    // as the safe knob to test whether stereotype-driven potentials can
    // accelerate learning without risking the W1-W6 "wrong prior" failure.
    private static final String  REWARD_SHAPING        = System.getProperty("reward.shaping", "none");
    private static final boolean REWARD_SHAPING_PBRS   = "pbrs".equalsIgnoreCase(REWARD_SHAPING);

    // -----------------------------------------------------------------------
    // Adaptive trust on the stereotype prior. When stereo.adaptiveTrust=true,
    // we maintain a per-action calibration score in [0,1] computed online as
    // the fraction of zone-level slots where the ontology-predicted sign of
    // the change agreed with the observed sign. After at least
    // stereo.adaptiveTrust.minSamples observations of an action, the
    // calibration is used as a multiplier on that action's prior (clamped
    // below at stereo.adaptiveTrust.floor). Actions whose ontology
    // prediction is consistently wrong (W1-W6) get their prior down-weighted
    // automatically; actions whose prediction is correct keep their boost.
    private static final boolean ADAPTIVE_TRUST               = Boolean.parseBoolean(System.getProperty("stereo.adaptiveTrust", "false"));
    private static final int     ADAPTIVE_TRUST_MIN_SAMPLES   = parseIntProp   ("stereo.adaptiveTrust.minSamples", 50);
    private static final double  ADAPTIVE_TRUST_FLOOR         = parseDoubleProp("stereo.adaptiveTrust.floor",      0.1);

    // Per-run seed override (XORed into the deterministic base seed). Lets
    // the orchestrator run N independent replicas with -Prun.seed=1..N to
    // build confidence intervals across seeds.
    private static final long    RUN_SEED                     = parseLongProp("run.seed", 0L);

    private static double parseDoubleProp(String key, double dflt) {
        try {
            String v = System.getProperty(key);
            return (v == null || v.isEmpty()) ? dflt : Double.parseDouble(v);
        } catch (Exception e) { return dflt; }
    }
    private static int parseIntProp(String key, int dflt) {
        try {
            String v = System.getProperty(key);
            return (v == null || v.isEmpty()) ? dflt : Integer.parseInt(v);
        } catch (Exception e) { return dflt; }
    }
    private static long parseLongProp(String key, long dflt) {
        try {
            String v = System.getProperty(key);
            return (v == null || v.isEmpty()) ? dflt : Long.parseLong(v);
        } catch (Exception e) { return dflt; }
    }
    /** SplitMix64 finalizer — spreads a small seed across all 64 bits so
     *  XOR-mixing tiny run.seed values (1..N) still flips most bits of the
     *  base seed and yields well-separated PRNG streams. */
    private static long mix64(long z) {
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }

    // Current episode number — incremented by beginEpisode / beginEpisodeFromState
    // (NOT endEpisode) and used by greedyAction to compute prior-decay weight.
    // Audit Step 3b §4-1: at bench the training agent's counter is lost; the
    // bench agent restores it via setEpisodeCounter() (called automatically by
    // loadQTable) so priorWeight is at floor rather than at maximum.
    private int currentEpisodeNum = 0;

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

    // Adaptive-trust calibration accumulators (only used when ADAPTIVE_TRUST=true).
    // S2-8 (audit Step 2): keyed by (action, sunshineBucket) so labs where the
    // ontology is correct at sun rank 3 but wrong at sun rank 0 (e.g. blind
    // activation) can still trust the prior in the state where it's right.
    // The original 1-D version averaged across all sun ranks and therefore
    // could never recover per-state — a single sun=0 false-positive would
    // poison the calibration for sun=3 evaluation. Indexed [action][sunBucket];
    // when sunshineIndex is unavailable or domainSizes[sunshineIndex]==1 the
    // table collapses to the legacy single-column behaviour.
    private double[][] actionCalSum;
    private long[][]   actionCalN;

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
    // Phase 2 — fault detection, blacklisting & warm-restart re-learning
    // -----------------------------------------------------------------------
    // Phase 2.3 — INSTANT isolation (NO evidence-accumulation threshold). A
    // component is flagged DEFECTIVE the FIRST time the Knowledge-Graph
    // prediction for one of its actions is contradicted by the observed
    // transition:
    //   • DEAD     — the actuator bit flips as commanded (or is silently
    //                dropped) but the zone illuminance it should move does not
    //                respond.
    //   • INVERTED — the zone moves in the OPPOSITE direction to the KG sign.
    // A SINGLE unambiguous, component-attributable observation of either mode is
    // sufficient: the advisor's design is that the agent recognises an action in
    // its policy produced UNEXPECTED behaviour, discards that artifact, and
    // re-learns — there is no "how many times was it faulty" counter. False
    // alarms are prevented STRUCTURALLY rather than statistically: only
    // FALSIFIABLE claims are scored (the action must make a non-zero KG bit-claim
    // and the zone it should move must not already be saturated at the boundary),
    // a zone fed by an already-blacklisted Causes actuator is skipped
    // (contamination guard), and a no-response on a zone with a fault-SUSPECT
    // co-feeder is abstained.
    // Only CAUSES actuators are adjudicated: a MEDIATES / IV-gated actuator
    // (e.g. a sunshine-gated blind) has no unconditional sign, and its null
    // response is expected whenever the IV is low or the zone is lamp-saturated,
    // so observeForFaults skips it (the fault model — dead / inverted lux —
    // targets Causes lamps). Once flagged, blacklistComponent() removes BOTH the
    // ON and OFF actions of the component, and warmRestart() re-primes learning
    // over the survivors.
    private boolean[] blacklisted;     // [nActions] — true → removed from action space
    private int[]     faultObsN;       // [nActions] — falsifiable observations of the action
    private int[]     faultDeadN;      // [nActions] — observations with no zone response (dead)
    private int[]     faultInvertN;    // [nActions] — observations with inverted zone response
    // Phase 2.2 — component-attributable residual guard. When a Causes actuator
    // is blacklisted its physical state is frozen (e.g. a stuck inverted lamp
    // that keeps subtracting lux), so the ZONES it feeds no longer carry a
    // trustworthy baseline for adjudicating a DIFFERENT component. observeForFaults
    // skips contaminated zones, so a healthy survivor (e.g. the shared Spotlight)
    // is never blamed for a zone whose baseline is corrupted by a stuck
    // blacklisted neighbour. This eliminates the lab3_f2inv double-inversion
    // Spotlight false positive without weakening genuine detection (the culprit
    // is adjudicated BEFORE it is blacklisted, i.e. before it contaminates).
    private boolean[] zoneCauseContaminated;  // [nZones] — zone fed by a blacklisted Causes actuator
    // wotActionType of every MEDIATES / IV-gated component (both ON and OFF
    // actions share one wotActionType, but hasIV is only set on the activation
    // action, so this set lets the detector skip BOTH polarities of a blind).
    private java.util.Set<String> ivGatedComponents = new java.util.HashSet<>();
    // Phase 2.3 — INSTANT isolation: a component is blacklisted on its FIRST
    // unambiguous fault observation, so the minSamples / dead-rate / inv-rate /
    // anomaly-rate accumulation thresholds have been removed. False positives are
    // held off by the structural falsifiability + contamination + suspect-
    // co-feeder guards below, not by counting repeated anomalies.
    private static final double FAULT_EPS_BOOST    = parseDoubleProp("fault.relearn.epsBoost",   0.30);
    // Phase 2.2 — combined dead+inverted observations for an actuator to count as
    // a fault SUSPECT that can mask a co-located healthy actuator's zone response
    // (primary-detection-time component attribution). Kept small — and paired with
    // a single-inverted-observation fast path in isFaultSuspect — so a genuine
    // fault is recognised as "suspect", and its masking effect discounted, before
    // the neighbour it corrupts is itself (instantly) mis-flagged.
    private static final int    FAULT_SUSPECT_MIN  = parseIntProp   ("fault.detect.suspectMin",   2);

    // Phase 2.1 — policy-stability recovery detector (adapt regime).
    // "Recovered" = the greedy policy (jointArgmax over surviving, non-blacklisted
    // actions) has not changed for RECOVERY_WINDOW consecutive episodes AFTER the
    // fault was blacklisted. This replaces the Phase-1 Bellman-stability test for
    // the post-fault regime: it tracks the RANKING of actions, so it is robust to
    // (a) the residual ε-boost exploration noise that keeps perturbing TD targets
    // and (b) goals that are only stochastically reachable (sun-gated survivors),
    // neither of which let the 1e-3 Bellman test settle. It needs no lab redesign.
    private int[]  recoveryPolicy      = null;  // last greedy policy snapshot
    private int    recoveryStableCount = 0;     // consecutive episodes with no policy change
    private static final int RECOVERY_WINDOW = parseIntProp("fault.recover.window", 50);

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
        // Seed mixes stereo flag so stereotype-on / stereotype-off runs explore
        // different action sequences (prior fix: identical FirstGoalEpisode bug).
        // RUN_SEED (sysprop -Drun.seed=N) is XORed in so independent replicas
        // for confidence-interval analysis explore different trajectories.
        long baseSeed = 42L ^ (useStereotypes ? 0x5A5A5A5A5A5A5A5AL : 0xA5A5A5A5A5A5A5A5L);
        if (RUN_SEED != 0L) baseSeed ^= mix64(RUN_SEED);
        this.rng            = new Random(baseSeed);

        // Convert Object[] to String[]
        String[] paths = new String[ontologyPaths.length];
        for (int i = 0; i < ontologyPaths.length; i++) {
            paths[i] = ontologyPaths[i].toString();
        }

        // Always instantiate StereotypeReasoner for structural discovery
        // (action list, WoT mappings). Only init penalties and masking are mode-gated.
        reasoner = new StereotypeReasoner(paths, sunshineSatisfactionProb);
        if (reasoner.isDegraded()) {
            LOGGER.warning("============================================================");
            LOGGER.warning("  StereotypeReasoner is in DEGRADED mode: state-slot registry");
            LOGGER.warning("  could not be loaded from the ontology. Falling back to the");
            LOGGER.warning("  legacy 8-slot layout. Stereotype-guided Q-init may not match");
            LOGGER.warning("  the simulator topology — results should be treated as");
            LOGGER.warning("  diagnostic, not as a valid stereotype-init comparison.");
            LOGGER.warning("============================================================");
        }
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
        // Phase 2: per-action blacklist + fault-evidence counters.
        blacklisted  = new boolean[nActions];
        faultObsN    = new int[nActions];
        faultDeadN   = new int[nActions];
        faultInvertN = new int[nActions];
        zoneCauseContaminated = new boolean[zoneLevelIndices.length];
        // Map out MEDIATES / IV-gated components so the fault detector can skip
        // BOTH polarities (hasIV is only set on the activation action, but the
        // ON and OFF actions share one wotActionType).
        ivGatedComponents.clear();
        for (StereotypeReasoner.ActionInfo ai : actionInfos) {
            if (ai != null && ai.hasIV && ai.wotActionType != null) {
                ivGatedComponents.add(ai.wotActionType);
            }
        }
        int sunBuckets = (sunshineIndex >= 0 && sunshineIndex < domainSizes.length)
                       ? Math.max(1, domainSizes[sunshineIndex]) : 1;
        actionCalSum = new double[nActions][sunBuckets];
        actionCalN   = new long[nActions][sunBuckets];

        if (useStereotypes && STEREO_PRIOR_SCALE > 0.0) {
            initWithStereotypes();
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: ON (ontology-driven)");
            LOGGER.info("  Decomposed Q-tables with per-zone penalties from SPARQL.");
        } else if (useStereotypes) {
            // S0-3 (audit Finding 6/7): with priorScale==0 the greedy soft
            // prior is gone, but raw ontology init penalties (−50..−150) would
            // still keep ql_true diverged from ql_false, defeating H5. When
            // the operator explicitly disables the prior, also skip the init
            // bias so the H5 ablation is a true no-op overlay.
            for (double[][] zt : qTables) for (double[] row : zt) Arrays.fill(row, 0.0);
            LOGGER.info("QLearner initialised — STEREOTYPE MODE: ON, priorScale=0 → zero Q-init (H5 ablation)");
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
        LOGGER.info("  Reward: clip=" + REWARD_CLIP
                  + " shaping=" + REWARD_SHAPING
                  + " priorScale=" + STEREO_PRIOR_SCALE
                  + " priorDecayEps=" + priorDecayEpisodes
                  + (PRIOR_DECAY_EPISODES_PROP <= 0 ? " (auto)" : "")
                  + " priorDecayFloor=" + PRIOR_DECAY_FLOOR
                  + " priorFadeVisits=" + PRIOR_FADE_VISITS
                  + " adaptiveTrust=" + ADAPTIVE_TRUST
                  + (ADAPTIVE_TRUST
                        ? " (minSamples=" + ADAPTIVE_TRUST_MIN_SAMPLES + " floor=" + ADAPTIVE_TRUST_FLOOR + ")"
                        : "")
                  + " runSeed=" + RUN_SEED);
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

        // Decomposed per-zone Bellman updates.
        // Each per-zone reward is clipped to [-REWARD_CLIP, +REWARD_CLIP] and
        // divided by the number of zones so the *total* reward fed into the
        // Q-update stays within the same per-step range regardless of zone count.
        double[] rewards = new double[goal.length];
        boolean anyZoneWastedByPenalty = false;
        double maxAbsDelta = 0.0;
        double zoneNorm = 1.0 / Math.max(1, goal.length);
        // VDN joint bootstrap target (audit Step-3a R-1): all zones must commit
        // to ONE shared action, so the per-zone independent max_a Q_z[s'][a]
        // over-estimates the achievable next value. Use the single action that
        // maximises the SUM of zone Q-values at s' (the joint greedy action),
        // and evaluate every zone's bootstrap at that same action.
        int aStarNext = jointArgmaxAction(sNext);
        for (int z = 0; z < goal.length; z++) {
            RewardResult rr = computeZoneReward(z, stateVec, action, nextStateVec);
            double rClipped = Math.max(-REWARD_CLIP, Math.min(REWARD_CLIP, rr.reward));
            double rForQ    = rClipped * zoneNorm;
            // Potential-Based Reward Shaping (Ng/Harada/Russell 1999).
            // F = gamma * Phi(s') - Phi(s),  Phi_z(s) = -|level_z(s) - target_z|.
            // Policy-invariant: the optimal Q* under r + F equals Q* under r
            // plus the static term Phi(s), so the greedy policy is identical.
            // Only the convergence path changes; safe to enable everywhere.
            if (REWARD_SHAPING_PBRS
                    && z < zoneLevelIndices.length
                    && zoneLevelIndices[z] >= 0
                    && zoneLevelIndices[z] < stateVec.length) {
                int slot = zoneLevelIndices[z];
                int prevLevel = toInt(stateVec[slot]);
                int nextLevel = toInt(nextStateVec[slot]);
                int target    = goal[z];
                double phiPrev = -Math.abs(prevLevel - target);
                double phiNext = -Math.abs(nextLevel - target);
                double F = gamma * phiNext - phiPrev;
                rForQ += F * zoneNorm;
            }
            rewards[z] = rClipped;
            if (rr.wastedByPenalty) anyZoneWastedByPenalty = true;
            double maxNextQz = qTables[z][sNext][aStarNext];
            double oldQz = qTables[z][sIdx][action];
            double newQz = oldQz + alpha * (rForQ + gamma * maxNextQz - oldQz);
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

        // Adaptive trust: compare per-action ontology-predicted Δ sign against
        // observed Δ sign on zone-level slots. Used by greedyAction to scale
        // each action's prior down if the ontology is systematically wrong.
        // S2-8: bucketed by sun rank so state-dependent priors (e.g. blind ON,
        // which is correct at sun=3 and wrong at sun=0) are tracked separately.
        if (ADAPTIVE_TRUST && useStereotypes && actionCalSum != null) {
            int[] pred = reasoner.getActionPrediction(prevSvArr, action);
            int matched = 0, considered = 0;
            for (int z = 0; z < zoneLevelIndices.length; z++) {
                int slot = zoneLevelIndices[z];
                if (slot < 0 || slot >= pred.length) continue;
                int predSign   = Integer.signum(pred[slot]);
                if (predSign == 0) continue; // action makes no claim on this zone
                int actualSign = Integer.signum(nextSvArr[slot] - prevSvArr[slot]);
                considered++;
                if (predSign == actualSign) matched++;
            }
            if (considered > 0) {
                int sunBucket = sunBucketOf(prevSvArr);
                actionCalSum[action][sunBucket] += (double) matched / considered;
                actionCalN[action][sunBucket]   += 1;
            }
        }

        if (LOGGER.isLoggable(java.util.logging.Level.FINE)) {
            StringBuilder rbuf = new StringBuilder();
            for (int z = 0; z < goal.length; z++) {
                if (z > 0) rbuf.append(' ');
                rbuf.append("rZ").append(z + 1).append('=')
                    .append(String.format("%.1f", rewards[z]));
            }
            LOGGER.fine("calculateQ: s=" + sIdx + " a=" + action + " " + rbuf
                      + " s'=" + sNext);
        }
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
     * Anti-stuck variant of {@link #getActionFromState}. When the bench agent
     * detects that the last 3 observed state vectors were identical (i.e. the
     * policy has stalled on a single action whose effect has no visible result
     * — e.g. flipping an already-saturated actuator), it calls this op with
     * the recent action ids to exclude. Logic:
     *   - If recentActions is empty, behaves exactly like greedy getActionFromState.
     *   - Otherwise computes argmax over applicable \ recentActions (and over
     *     DO_NOTHING, which is also excluded when stuck). Ties broken by random
     *     pick. stuckFired is true iff a recentActions exclusion actually took
     *     effect.
     */
    @OPERATION
    public void getActionFromStateAntiStuck(Object[] stateVec,
                                            Object[] recentActions,
                                            OpFeedbackParam<Integer> action,
                                            OpFeedbackParam<Boolean> stuckFired) {
        int sIdx = stateVecToIndex(stateVec);
        int[] applicable = computeApplicableActions(stateVec);

        // Build the exclusion set from recentActions + DO_NOTHING action ids.
        // DO_NOTHING actions have wotActionType == null.
        boolean[] excluded = new boolean[nActions];
        boolean anyExclude = false;
        if (recentActions != null) {
            for (Object o : recentActions) {
                int a = toInt(o);
                if (a >= 0 && a < nActions) { excluded[a] = true; anyExclude = true; }
            }
        }
        if (anyExclude) {
            for (int a = 0; a < nActions; a++) {
                if (actionInfos[a].wotActionType == null) excluded[a] = true;
            }
        }

        // Filter applicable down to non-excluded actions.
        int[] filtered = applicable;
        if (anyExclude) {
            int n = 0;
            int[] buf = new int[applicable.length];
            for (int a : applicable) if (!excluded[a]) buf[n++] = a;
            if (n > 0) {
                filtered = new int[n];
                System.arraycopy(buf, 0, filtered, 0, n);
            } else {
                // All applicable actions were excluded — fall back to full set
                // and do NOT signal stuckFired (we couldn't actually act).
                anyExclude = false;
            }
        }

        int chosen = greedyAction(sIdx, filtered);
        action.set(chosen);
        stuckFired.set(anyExclude);
        if (anyExclude) {
            LOGGER.info("getActionFromStateAntiStuck: STUCK fired → chose action=" + chosen
                      + " (excluded " + java.util.Arrays.toString(recentActions) + ")");
        }
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

    // -----------------------------------------------------------------------
    // Phase 2 — fault detection, blacklisting & warm-restart re-learning
    // -----------------------------------------------------------------------

    /**
     * Strict Expected-vs-Actual check for ONE transition. Compares the
     * Knowledge-Graph prediction for {@code actionIdx} in {@code stateVecBefore}
     * against the observed Δ to {@code stateVecAfter}. Phase 2.3 — INSTANT
     * isolation: the FIRST time a falsifiable, component-attributable observation
     * shows the underlying component is DEAD (no response) or INVERTED (opposite
     * response), {@code newlyDefective} is set to the component's WoT action-type
     * URI; otherwise it is set to the empty string. There is no accumulation
     * threshold — a single unambiguous anomaly is sufficient to isolate it.
     *
     * Only falsifiable observations are counted: the action must make a non-zero
     * KG bit-claim (i.e. it is not redundant in this state), and a zone the
     * action claims to move must not already be saturated at the boundary. This
     * prevents already-ON / already-saturated steps from producing false "dead"
     * evidence.
     *
     * Only CAUSES actuators (unconditional {@code elem:increases} sign) are
     * adjudicated. MEDIATES / IV-gated actuators (e.g. blinds, whose effect is
     * gated by sunshine and is rank-masked when a co-located lamp saturates the
     * zone) are skipped: their null response is expected healthy behaviour, not
     * fault evidence, so adjudicating them yields false DEFECTIVE verdicts.
     *
     * Pure accumulation — does NOT mutate the policy. Call
     * {@link #blacklistComponent} + {@link #warmRestart} to act on a defect.
     */
    @OPERATION
    public void observeForFaults(Object[] stateVecBefore, int actionIdx,
                                 Object[] stateVecAfter,
                                 OpFeedbackParam<String> newlyDefective) {
        newlyDefective.set("");
        if (actionIdx < 0 || actionIdx >= nActions) return;
        StereotypeReasoner.ActionInfo ai = actionInfos[actionIdx];
        if (ai == null || ai.wotActionType == null) return;          // DO_NOTHING — no claim
        if (blacklisted != null && blacklisted[actionIdx]) return;   // already removed
        // Only CAUSES actuators (unconditional elem:increases) are adjudicated.
        // A MEDIATES / IV-gated actuator (e.g. a blind, whose effect is
        // 0.5·sunshine) has NO unconditional sign: its zone response is absent
        // when the IV is low AND is rank-masked whenever a co-located lamp
        // already saturates the zone at its target rank. A null response is
        // therefore EXPECTED healthy behaviour, not fault evidence, so scoring
        // it manufactures false DEFECTIVE verdicts (observed: a healthy blind
        // flagged at deadRate=1.00 because Z2 was lamp-pinned at its rank-3
        // target). The injected fault model (dead / inverted lux) only applies
        // to Causes lamps; detecting a broken Mediates actuator from discretised
        // ranks alone is unsound, so it is deliberately out of detector scope.
        // NB: hasIV is set only on the activation action, so we test the whole
        // component (both ON and OFF actions share one wotActionType).
        if (ivGatedComponents.contains(ai.wotActionType)) return;

        // Phase 2.3 — INSTANT detection adjudicates ONLY single-zone (dominant)
        // Causes actuators. A shared MULTI-ZONE Causes feeder (the Spotlight,
        // affectedZones=[0,1]) contributes only a MARGINAL amount to each zone, so
        // a healthy toggle may fail to cross a discretised rank boundary — a no-op
        // that single-observation detection would mis-read as "dead" (observed:
        // the healthy Spotlight flagged in lab3_f1dead) — and its net per-zone
        // response is confounded by co-feeders (an inverted co-lamp flooring a
        // shared zone reads as "inverted"). Such an actuator is NOT falsifiable at
        // rank resolution and is NEVER fault-injected (the model targets single-
        // zone lamps), so adjudicating it only manufactures false positives. A
        // single-zone lamp is the DOMINANT feeder of its zone, so its rank response
        // IS a sound falsifiable signal and stays fully adjudicated. (Verified: in
        // every lab, SetZxLight feeds exactly one zone; only SetSpotlight is multi-
        // zone.) This is the structural guard that makes threshold-free instant
        // isolation safe.
        if (ai.affectedZones != null && ai.affectedZones.size() > 1) return;

        int[] before = toIntArray(stateVecBefore);
        int[] after  = toIntArray(stateVecAfter);
        int[] pred   = reasoner.getActionPrediction(before, actionIdx);

        int bitSlot = ai.stateVecBitIndex;
        if (bitSlot < 0 || bitSlot >= before.length) return;
        int bitPred = (bitSlot < pred.length) ? pred[bitSlot] : 0;
        if (bitPred == 0) return; // actuator already in target state — not falsifiable
        int bitObs = after[bitSlot] - before[bitSlot];

        boolean dead = false;
        boolean inverted = false;
        if (bitObs == 0) {
            // Command silently dropped — the actuator did not even toggle.
            dead = true;
        } else if (bitObs == bitPred) {
            // Bit flipped as commanded. Did the zone(s) it should move respond?
            int claimed = 0, noResp = 0, opp = 0;
            boolean ambiguous = false;   // a zone's null response was explained away by a suspect co-feeder
            for (int z = 0; z < zoneLevelIndices.length; z++) {
                int slot = zoneLevelIndices[z];
                if (slot < 0 || slot >= before.length) continue;
                // Phase 2.2: a zone fed by an already-blacklisted Causes actuator
                // has a frozen/untrustworthy baseline, so a residual there is not
                // attributable to THIS component — abstain rather than mis-charge.
                if (zoneCauseContaminated != null && z < zoneCauseContaminated.length
                        && zoneCauseContaminated[z]) continue;
                int predD = (slot < pred.length) ? pred[slot] : 0;
                if (predD == 0) continue;
                int maxRank = (slot < domainSizes.length) ? domainSizes[slot] - 1 : 3;
                if (predD > 0 && before[slot] >= maxRank) continue; // can't rise — not falsifiable
                if (predD < 0 && before[slot] <= 0)       continue; // can't fall — not falsifiable
                int obsD = after[slot] - before[slot];
                if (obsD != 0 && (long) obsD * (long) predD < 0L) {
                    // OPPOSITE-sign response — an INVERTED actuator. Trustworthy
                    // even in a cross-coupled lab: only the toggled actuator
                    // changed this step, so its own contribution sets the sign.
                    // This evidence is NEVER gated (see below).
                    claimed++;
                    opp++;
                } else if (obsD == 0) {
                    // NO rank response. Before charging THIS component with a
                    // dead/no-response, check whether a DIFFERENT, fault-suspect
                    // actuator co-feeds this zone. In lab3_f2inv both task lamps are
                    // INVERTED yet still active: they subtract large lux and hold the
                    // two shared zones at the rank FLOOR, so a healthy Spotlight's
                    // +150 can no longer lift the discretised rank — its correct
                    // toggle then reads as a dead/no-response. When a suspect
                    // co-feeder is present that null response is NOT attributable to
                    // this component, so abstain. This primary-detection-time
                    // attribution rule removes the healthy-Spotlight false positive.
                    // It does NOT weaken real detection: an inverted fault is caught
                    // by the ungated opp branch above, and the injected DEAD fault
                    // (the lamp flag still toggles but its lux contribution is zeroed)
                    // reaches THIS branch on the lamp's OWN primary zone, which has no
                    // suspect co-feeder — lamps have DISJOINT primary zones and the
                    // only shared multi-zone feeder is the healthy Spotlight — so a
                    // genuine dead lamp is never gated.
                    if (zoneHasSuspectCoFeeder(z, actionIdx)) { ambiguous = true; continue; }
                    claimed++;
                    noResp++;
                } else {
                    // Correct-direction response — a healthy, falsifiable claim.
                    claimed++;
                }
            }
            if (opp > 0) {
                // Positive proof of inversion from this actuator's own toggle —
                // never gated, never abstained.
                inverted = true;
            } else if (ambiguous) {
                // At least one zone's null response may be a suspect co-feeder
                // masking this actuator's real effect (the floored-Spotlight case).
                // We cannot conclude "dead", so abstain on the whole observation
                // rather than charge a partial dead verdict from the surviving
                // zone(s). This shuts the one-lamp-suspect race that previously let
                // a healthy multi-zone Spotlight be flagged before BOTH inverted
                // lamps crossed the suspect threshold.
                return;
            } else if (claimed > 0) {
                if (noResp == claimed) dead = true;
                // else: partial/correct response — a non-anomalous observation.
            } else {
                return; // every claim was unfalsifiable here — ignore this step
            }
        } else {
            return; // bitObs neither 0 nor == bitPred (shouldn't happen for a 0/1 bit)
        }

        // Maintain the per-action counters BEFORE flagging: the suspect-co-feeder
        // guard (isFaultSuspect) reads faultInvertN / faultDeadN to attribute
        // masking on shared zones, and faultObsN bounds-guards that lookup.
        faultObsN[actionIdx]++;
        if (dead)     faultDeadN[actionIdx]++;
        if (inverted) faultInvertN[actionIdx]++;

        // Phase 2.3 — INSTANT isolation. A single unambiguous, component-
        // attributable fault observation (a dead/no-response OR an
        // inverted/opposite-response on the actuator's own falsifiable claim)
        // blacklists the component immediately — there is no accumulation
        // threshold. Every false-positive guard above has already run and
        // `return`ed on any unfalsifiable / saturated / suspect-co-feeder /
        // contaminated-zone step, so only a genuine anomaly reaches this point.
        if (dead || inverted) {
            newlyDefective.set(ai.wotActionType);
            LOGGER.warning(String.format(
                "observeForFaults: component %s flagged DEFECTIVE via action %d (%s) "
              + "on FIRST anomalous observation [%s]",
                ai.wotActionType, actionIdx, ai.label,
                dead ? "dead/no-response" : "inverted/opposite-response"));
        }
    }

    /**
     * Phase 2.2 — is action {@code b} currently carrying enough anomaly evidence to
     * be treated as a fault SUSPECT whose corruption of a shared zone should be
     * discounted when adjudicating a co-located actuator? Deliberately an EARLY,
     * low bar so a real fault is recognised as suspect the moment it shows any
     * anomaly, before the neighbour it corrupts is itself (instantly) mis-flagged
     * (the lab3_f2inv race). Two triggers:
     *   • a SINGLE opposite-direction (inverted) observation — essentially
     *     impossible for a healthy actuator on its own zone, so it alone suffices;
     *   • OR {@code FAULT_SUSPECT_MIN} combined dead+inverted observations.
     * Over-suspicion is safe here: the only actuator the co-feeder gate can ever
     * spare is the shared multi-zone Spotlight (lamps have DISJOINT primary zones
     * and so never gate each other), and the Spotlight is healthy in every injected
     * profile, so a false "suspect" can never hide a genuine lamp fault.
     */
    private boolean isFaultSuspect(int b) {
        if (faultObsN == null || b < 0 || b >= faultObsN.length) return false;
        if (faultInvertN[b] >= 1) return true;   // one inverted obs = strong evidence
        return (faultDeadN[b] + faultInvertN[b]) >= FAULT_SUSPECT_MIN;
    }

    /**
     * Phase 2.2 — does any actuator OTHER than {@code selfAction}'s component
     * structurally feed {@code zone} AND currently look fault-suspect? Used to
     * abstain on a zone's no-response evidence when a faulty neighbour may be
     * masking it (component-attributable adjudication). Co-feeders are matched on
     * the static {@code affectedZones} coupling; both the ON and OFF actions of
     * the component under test are excluded via their shared wotActionType.
     */
    private boolean zoneHasSuspectCoFeeder(int zone, int selfAction) {
        StereotypeReasoner.ActionInfo self =
            (selfAction >= 0 && selfAction < nActions) ? actionInfos[selfAction] : null;
        String selfType = (self != null) ? self.wotActionType : null;
        for (int b = 0; b < nActions; b++) {
            if (b == selfAction) continue;
            StereotypeReasoner.ActionInfo bi = actionInfos[b];
            if (bi == null || bi.wotActionType == null) continue;
            if (selfType != null && selfType.equals(bi.wotActionType)) continue; // same component
            if (bi.affectedZones == null || !bi.affectedZones.contains(zone)) continue;
            if (isFaultSuspect(b)) return true;
        }
        return false;
    }

    /**
     * Blacklist a defective component: remove BOTH its ON and OFF actions from
     * the action space so the policy can never select them again. DO_NOTHING is
     * never removed, and the last surviving actuator action is protected so the
     * action space can never be emptied. Sets {@code nRemoved} to the number of
     * action indices actually removed (0, 1 or 2).
     */
    @OPERATION
    public void blacklistComponent(String wotActionType, OpFeedbackParam<Integer> nRemoved) {
        int removed = 0;
        if (wotActionType == null || wotActionType.isEmpty() || blacklisted == null) {
            nRemoved.set(0);
            return;
        }
        for (int a = 0; a < nActions; a++) {
            StereotypeReasoner.ActionInfo ai = actionInfos[a];
            if (ai == null || ai.wotActionType == null) continue;       // never DO_NOTHING
            if (!wotActionType.equals(ai.wotActionType) || blacklisted[a]) continue;
            // Guarantee at least one non-DO_NOTHING action survives the removal.
            int surviving = 0;
            for (int b = 0; b < nActions; b++) {
                if (b == a) continue;
                StereotypeReasoner.ActionInfo bi = actionInfos[b];
                if (bi != null && bi.wotActionType != null && !blacklisted[b]) surviving++;
            }
            if (surviving < 1) {
                LOGGER.warning("blacklistComponent: refusing to remove the last actuator action "
                             + a + " (" + ai.label + ")");
                continue;
            }
            blacklisted[a] = true;
            removed++;
            LOGGER.warning("blacklistComponent: removed action " + a + " (" + ai.label + ")");
        }
        // Phase 2.2: the blacklisted component's physical state is now frozen, so
        // every zone it Causes-feeds is no longer a trustworthy baseline for
        // adjudicating OTHER components — mark those zones contaminated.
        if (removed > 0 && zoneCauseContaminated != null) {
            for (int a = 0; a < nActions; a++) {
                StereotypeReasoner.ActionInfo ai = actionInfos[a];
                if (ai == null || ai.wotActionType == null) continue;
                if (!wotActionType.equals(ai.wotActionType) || ai.affectedZones == null) continue;
                for (int z : ai.affectedZones)
                    if (z >= 0 && z < zoneCauseContaminated.length) zoneCauseContaminated[z] = true;
            }
        }
        nRemoved.set(removed);
    }

    /**
     * Warm-restart re-learning after a component has been blacklisted (master
     * plan §3.1). Does NOT wipe the whole Q-table — it surgically removes the
     * dependence on the pruned action and re-primes exploration:
     *   1. Zero Q(s,a*) and visit counts for every blacklisted action a*.
     *   2. Halve the surviving Q-values in "poisoned" states — those whose old
     *      greedy action was a blacklisted action — so re-learning can re-rank
     *      the survivors quickly without fighting a stale optimum.
     *   3. Boost ε to {@code fault.relearn.epsBoost} so the agent re-explores
     *      the reduced action set.
     *   4. Reset the prior-decay clock so the KG priors regain weight over the
     *      surviving actions during re-learning (ql_true; no-op for ql_false).
     *   5. Reset the convergence detector for the new regime.
     */
    @OPERATION
    public void warmRestart() {
        if (blacklisted == null) return;
        // Snapshot poisoned states using the ORIGINAL Q (before any wipe).
        boolean[] poisonedState = new boolean[nStates];
        int poisoned = 0;
        for (int s = 0; s < nStates; s++) {
            int oldArg = unfilteredArgmax(s);
            if (oldArg >= 0 && blacklisted[oldArg]) { poisonedState[s] = true; poisoned++; }
        }
        // (1) Wipe blacklisted action columns + their visit counts.
        int wiped = 0;
        for (int a = 0; a < nActions; a++) {
            if (!blacklisted[a]) continue;
            wiped++;
            for (int z = 0; z < qTables.length; z++)
                for (int s = 0; s < nStates; s++) qTables[z][s][a] = 0.0;
            for (int s = 0; s < nStates; s++) visitCounts[s][a] = 0L;
        }
        // (2) Decay poisoned states' surviving Q toward 0.
        for (int s = 0; s < nStates; s++) {
            if (!poisonedState[s]) continue;
            for (int z = 0; z < qTables.length; z++)
                for (int a = 0; a < nActions; a++) qTables[z][s][a] *= 0.5;
        }
        // (3) ε boost, (4) prior-decay reset, (5) convergence reset.
        epsilon = Math.max(epsilon, FAULT_EPS_BOOST);
        currentEpisodeNum = 0;
        convergenceCount = 0;
        // (6) Reset the policy-stability recovery detector so the recovery window
        //     starts fresh from the warm-restart point (the post-fault baseline).
        recoveryPolicy = null;
        recoveryStableCount = 0;
        // (7) Phase 2.2 — re-baseline fault evidence (per-component sequential
        //     isolation). Evidence accumulated while the just-blacklisted
        //     component was still active is discarded so the NEXT component is
        //     adjudicated afresh in the reduced action space. This stops a
        //     corrupted residual (e.g. a stuck inverted lamp depressing a zone)
        //     from being carried across the isolation boundary and mis-charged
        //     to a healthy survivor.
        if (faultObsN != null) {
            java.util.Arrays.fill(faultObsN, 0);
            java.util.Arrays.fill(faultDeadN, 0);
            java.util.Arrays.fill(faultInvertN, 0);
        }
        LOGGER.warning(String.format(
            "warmRestart: wiped %d action column(s), decayed %d poisoned state(s), "
          + "ε←%.3f, episodeClock←0, convergence reset",
            wiped, poisoned, epsilon));
    }

    /** Number of actions currently selectable (excludes blacklisted). */
    @OPERATION
    public void getNumApplicableActions(OpFeedbackParam<Integer> n) {
        int c = 0;
        for (int a = 0; a < nActions; a++) if (blacklisted == null || !blacklisted[a]) c++;
        n.set(c);
    }

    /** True iff any action of the given component is currently blacklisted. */
    @OPERATION
    public void isComponentBlacklisted(String wotActionType, OpFeedbackParam<Boolean> result) {
        boolean any = false;
        if (wotActionType != null && blacklisted != null) {
            for (int a = 0; a < nActions; a++) {
                StereotypeReasoner.ActionInfo ai = actionInfos[a];
                if (ai != null && wotActionType.equals(ai.wotActionType) && blacklisted[a]) {
                    any = true;
                    break;
                }
            }
        }
        result.set(any);
    }

    /**
     * Append one recovery-metric row to a CSV (creating it with a header if
     * absent). RecoveryEpisodes = ReconvergeEpisode − DetectEpisode is the
     * headline Phase-2 metric: how many episodes the agent took to re-converge
     * after the fault was detected and the component blacklisted.
     *
     * Phase 2.2: {@code recoveredGoalRate} is the fraction of greedy (ε=0)
     * evaluation episodes the FINAL policy reaches the goal in. It distinguishes
     * a policy that merely STOPPED CHANGING (stable) from one that actually
     * REACHES the goal (goal-reaching), closing the stability≠optimality gap.
     */
    @OPERATION
    public void saveRecoveryLog(String filename, int detectEp, int reconvergeEp,
                                int secondaryDetectEp, double recoveredGoalRate,
                                String blacklistedLabel) {
        boolean exists = new java.io.File(filename).exists();
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename, true))) {
            if (!exists) pw.println("DefectComponent,DetectEpisode,ReconvergeEpisode,RecoveryEpisodes,SecondaryDetectEpisode,RecoveredGoalRate");
            int rec = (reconvergeEp >= 0 && detectEp >= 0) ? (reconvergeEp - detectEp) : -1;
            pw.printf("%s,%d,%d,%d,%d,%.4f%n",
                blacklistedLabel == null ? "" : blacklistedLabel,
                detectEp, reconvergeEp, rec, secondaryDetectEp, recoveredGoalRate);
            LOGGER.info("saveRecoveryLog: appended recovery row to " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveRecoveryLog: failed " + filename + " — " + e.getMessage());
        }
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
        currentEpisodeNum++;
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
        currentEpisodeNum++;
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
     * Phase 2.1 — advance the policy-stability recovery detector by ONE episode.
     * Call once per adapt episode (after {@link #endEpisode}) once a fault has
     * been blacklisted. Snapshots the current greedy policy ({@link
     * #jointArgmaxAction} over every state, which excludes blacklisted actions)
     * and counts how many consecutive episodes the policy stays identical. The
     * argmax ignores ε and ignores whether the (possibly sun-gated) goal was
     * reachable this episode, so it settles where the 1e-3 Bellman test cannot.
     */
    @OPERATION
    public void updateRecoveryDetector() {
        int[] pol = new int[nStates];
        for (int s = 0; s < nStates; s++) pol[s] = jointArgmaxAction(s);
        if (recoveryPolicy != null && java.util.Arrays.equals(pol, recoveryPolicy)) {
            recoveryStableCount++;
        } else {
            recoveryStableCount = 0;
            recoveryPolicy = pol;
        }
    }

    /**
     * Phase 2.1 — true once the greedy policy has been stable for
     * {@code fault.recover.window} (default 50) consecutive episodes, i.e. the
     * agent has re-converged onto a fixed policy over the surviving action set.
     *
     * @param recovered  Output: true if the post-fault policy has re-converged.
     */
    @OPERATION
    public void hasRecovered(OpFeedbackParam<Boolean> recovered) {
        recovered.set(recoveryStableCount >= RECOVERY_WINDOW);
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
            try {
                saveQTableToFile(base + "_zone" + (z + 1) + ".csv", actionNames, false, qTables[z]);
            } catch (Throwable t) {
                LOGGER.log(java.util.logging.Level.SEVERE,
                    "saveQTable: zone " + (z + 1) + " threw: " + t.getClass().getName()
                    + " - " + t.getMessage(), t);
            }
        }
        // Audit Step 3b §S3b-3: persist sidecars so the bench can restore
        // visit counts (per-cell prior fade) and adaptive-trust calibrations.
        saveVisitCountsSidecar(base + "_visits.csv");
        saveAdaptiveTrustSidecar(base + "_trust.csv");
    }

    private void saveVisitCountsSidecar(String filename) {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(filename), 1 << 20);
             PrintWriter pw = new PrintWriter(bw)) {
            StringBuilder row = new StringBuilder(256);
            row.append("StateIndex");
            for (int a = 0; a < nActions; a++) row.append(",a").append(a);
            pw.println(row);
            long rowsWritten = 0;
            for (int s = 0; s < nStates; s++) {
                long sum = 0;
                for (int a = 0; a < nActions; a++) sum += visitCounts[s][a];
                if (sum == 0) continue;
                row.setLength(0);
                row.append(s);
                for (int a = 0; a < nActions; a++) row.append(',').append(visitCounts[s][a]);
                pw.println(row);
                rowsWritten++;
            }
            LOGGER.info("saveVisitCountsSidecar: " + rowsWritten + " rows → " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveVisitCountsSidecar: failed " + filename + " — " + e.getMessage());
        }
    }

    private void saveAdaptiveTrustSidecar(String filename) {
        if (actionCalSum == null || actionCalN == null) return;
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("Action,SunBucket,Sum,N");
            long rowsWritten = 0;
            for (int a = 0; a < actionCalN.length; a++) {
                for (int sb = 0; sb < actionCalN[a].length; sb++) {
                    if (actionCalN[a][sb] == 0) continue;
                    pw.println(a + "," + sb + "," + actionCalSum[a][sb] + "," + actionCalN[a][sb]);
                    rowsWritten++;
                }
            }
            LOGGER.info("saveAdaptiveTrustSidecar: " + rowsWritten + " rows → " + filename);
        } catch (IOException e) {
            LOGGER.warning("saveAdaptiveTrustSidecar: failed " + filename + " — " + e.getMessage());
        }
    }

    private void saveQTableToFile(String filename, String[] actionNames,
                                  boolean combined, double[][] singleTable) {
        // Use a large BufferedWriter and a reused StringBuilder row buffer.
        // Avoid String.format / Formatter per cell (28M+ allocations across
        // the 5 init CSVs); use Locale-stable manual rounding to 2 decimals.
        // This keeps allocation pressure low enough that the JVM does not
        // spend most of its time in GC and never gets killed by the
        // surrounding launcher / IDE process supervisor.
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(filename), 1 << 20);
             PrintWriter pw = new PrintWriter(bw)) {
            StringBuilder row = new StringBuilder(512);
            row.append("StateIndex");
            for (String a : actionNames) { row.append(',').append(a); }
            pw.println(row);
            long rowsWritten = 0;
            for (int s = 0; s < nStates; s++) {
                boolean anyNonZero = false;
                for (int a = 0; a < nActions; a++) {
                    double v = combined ? combinedQ(s, a) : singleTable[s][a];
                    if (v != 0.0) { anyNonZero = true; break; }
                }
                if (!anyNonZero) continue;
                row.setLength(0);
                row.append(s);
                for (int a = 0; a < nActions; a++) {
                    double v = combined ? combinedQ(s, a) : singleTable[s][a];
                    row.append(',');
                    appendRounded2(row, v);
                }
                pw.println(row);
                rowsWritten++;
            }
            LOGGER.info("saveQTable: written to " + filename + " (" + rowsWritten + " rows)");
        } catch (IOException e) {
            LOGGER.warning("saveQTable: failed to write " + filename + " - " + e.getMessage());
        } catch (Throwable t) {
            LOGGER.log(java.util.logging.Level.SEVERE,
                "saveQTable: unexpected error writing " + filename
                + " (type=" + t.getClass().getName() + ", msg=" + t.getMessage() + ")", t);
        }
    }

    /** Append v rounded to 2 decimals (HALF_UP) to sb, no Locale dependency. */
    private static void appendRounded2(StringBuilder sb, double v) {
        if (Double.isNaN(v)) { sb.append("NaN"); return; }
        if (Double.isInfinite(v)) { sb.append(v > 0 ? "Infinity" : "-Infinity"); return; }
        // Round half-up to 2 decimals.
        long scaled = (long) Math.floor(Math.abs(v) * 100.0 + 0.5);
        if (v < 0 && scaled != 0) sb.append('-');
        sb.append(scaled / 100);
        sb.append('.');
        long frac = scaled % 100;
        if (frac < 10) sb.append('0');
        sb.append(frac);
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
     * Audit Step 2 note: this operation has zero call sites in production .asl
     * agents, .json scenario files, or .ps1 orchestration scripts. The strict
     * mask path in {@link #getApplicableActions} is therefore effectively dead
     * code in current sweeps. Retained for ablation reproducibility (future
     * experiments may invoke it programmatically); the behavioural difference
     * is intentionally preserved so prior result tables remain reproducible.
     *
     * @param strict  true → hard masking, false → soft priors.
     */
    @OPERATION
    public void setMaskStrict(boolean strict) {
        this.maskStrict = strict;
        LOGGER.info("QLearner.setMaskStrict: maskStrict=" + strict);
    }

    /**
     * Couple the prior-decay horizon to the training budget.
     * Audit Step 2 §S2-3: the legacy PRIOR_DECAY_EPISODES=2500 default was
     * arbitrary — with 10k-episode profiles like custom8 the prior reached
     * its floor at ep 2500, leaving 7500 episodes with prior pinned at
     * STEREO_PRIOR_SCALE*PRIOR_DECAY_FLOOR = 0.5; with 50-episode quick
     * sanity runs the prior never decayed at all. This operation sets the
     * horizon to 0.25 × numEpisodes (so the prior shape is identical across
     * training budgets). Honours an explicit -Dstereo.priorDecayEpisodes
     * override: when the sysprop is positive it wins and this call is a no-op.
     *
     * @param numEpisodes  total planned training episodes (e.g. from
     *                     lab_profiles training_params).
     */
    @OPERATION
    public void setTrainingBudgetEpisodes(int numEpisodes) {
        if (PRIOR_DECAY_EPISODES_PROP > 0) {
            LOGGER.info("QLearner.setTrainingBudgetEpisodes: ignored (sysprop"
                      + " -Dstereo.priorDecayEpisodes=" + PRIOR_DECAY_EPISODES_PROP
                      + " wins). priorDecayEpisodes=" + priorDecayEpisodes);
            return;
        }
        int newDecay = Math.max(1, numEpisodes / 4);
        this.priorDecayEpisodes = newDecay;
        LOGGER.info("QLearner.setTrainingBudgetEpisodes: numEpisodes=" + numEpisodes
                  + " → priorDecayEpisodes=" + newDecay + " (auto = 25% of budget)");
    }

    /**
     * Audit Step 3b §S3b-1: set the episode counter consumed by
     * {@link #greedyAction}'s prior-decay schedule. The training agent
     * increments this via {@link #beginEpisode}; the bench agent never
     * calls beginEpisode, so without this op {@code currentEpisodeNum=0}
     * at bench and {@code priorWeight=STEREO_PRIOR_SCALE} (the MAXIMUM,
     * not the floor). {@link #loadQTable} now calls this automatically
     * with {@code priorDecayEpisodes} so bench operates in the documented
     * floor regime.
     *
     * @param n  New value of {@code currentEpisodeNum}.
     */
    @OPERATION
    public void setEpisodeCounter(int n) {
        this.currentEpisodeNum = Math.max(0, n);
        LOGGER.info("QLearner.setEpisodeCounter: currentEpisodeNum=" + this.currentEpisodeNum
                  + " (priorDecayEpisodes=" + priorDecayEpisodes
                  + " → priorWeight at floor=" + (this.currentEpisodeNum >= priorDecayEpisodes) + ")");
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

        // Audit Step 3b §S3b-1: align bench-time prior-decay state with the
        // training-time end-state. Without this, currentEpisodeNum=0 at bench
        // produces priorWeight=STEREO_PRIOR_SCALE (maximum), contradicting the
        // greedyAction documentation and producing a 10×-too-strong bench prior.
        this.currentEpisodeNum = priorDecayEpisodes;
        LOGGER.info("loadQTable: currentEpisodeNum ← priorDecayEpisodes="
                  + priorDecayEpisodes + " (bench prior at floor regime)");

        // Audit Step 3b §S3b-3: restore visit counts and adaptive-trust
        // calibration from sidecar files if present. Without these the
        // per-cell fade (PRIOR_FADE_VISITS) and per-action trust (calMul)
        // mechanisms are structurally dead at bench. Missing files are
        // tolerated to preserve backwards compatibility with old Q-tables.
        loadVisitCountsSidecar(base + "_visits.csv");
        loadAdaptiveTrustSidecar(base + "_trust.csv");
    }

    private void loadVisitCountsSidecar(String filename) {
        java.io.File f = new java.io.File(filename);
        if (!f.exists()) {
            LOGGER.info("loadVisitCountsSidecar: not found " + filename
                      + " (cellMul fade will be inactive at bench)");
            return;
        }
        try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.FileReader(f))) {
            String header = br.readLine();
            if (header == null) return;
            String[] cols = header.split(",");
            int numActionCols = cols.length - 1;
            String line;
            long rowsLoaded = 0;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] parts = line.split(",");
                int stateIdx = Integer.parseInt(parts[0].trim());
                if (stateIdx < 0 || stateIdx >= nStates) continue;
                for (int a = 0; a < Math.min(numActionCols, nActions); a++) {
                    visitCounts[stateIdx][a] = Long.parseLong(parts[a + 1].trim());
                }
                rowsLoaded++;
            }
            LOGGER.info("loadVisitCountsSidecar: loaded " + rowsLoaded + " rows from " + filename);
        } catch (IOException | NumberFormatException e) {
            LOGGER.warning("loadVisitCountsSidecar: failed " + filename + " — " + e.getMessage());
        }
    }

    private void loadAdaptiveTrustSidecar(String filename) {
        java.io.File f = new java.io.File(filename);
        if (!f.exists()) {
            LOGGER.info("loadAdaptiveTrustSidecar: not found " + filename
                      + " (calMul adaptive trust will be inactive at bench)");
            return;
        }
        try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.FileReader(f))) {
            String header = br.readLine(); // Action,SunBucket,Sum,N
            if (header == null) return;
            String line;
            long rowsLoaded = 0;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] parts = line.split(",");
                if (parts.length < 4) continue;
                int a   = Integer.parseInt(parts[0].trim());
                int sb  = Integer.parseInt(parts[1].trim());
                double sum = Double.parseDouble(parts[2].trim());
                long   n   = Long.parseLong(parts[3].trim());
                if (a < 0 || a >= nActions) continue;
                if (sb < 0 || sb >= actionCalN[a].length) continue;
                actionCalSum[a][sb] = sum;
                actionCalN[a][sb]   = n;
                rowsLoaded++;
            }
            LOGGER.info("loadAdaptiveTrustSidecar: loaded " + rowsLoaded + " rows from " + filename);
        } catch (IOException | NumberFormatException e) {
            LOGGER.warning("loadAdaptiveTrustSidecar: failed " + filename + " — " + e.getMessage());
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

        // Terminal: once-only bonus on transition INTO target (prevents
        // +200/step compounding that saturated reward at +5970).
        if (prevLevel != target && nextLevel == target) {
            r += 200.0;
        } else if (nextLevel == target) {
            // Small holding reward while staying at target — bounded by clip.
            r += 5.0;
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

    /** Combined Q-value (sum over all zones) for action selection. */
    private double combinedQ(int stateIdx, int action) {
        double sum = 0.0;
        for (double[][] zt : qTables) sum += zt[stateIdx][action];
        return sum;
    }

    /**
     * Joint greedy action at a state: argmax_a over the SUM of per-zone
     * Q-values (VDN value decomposition). Used as the bootstrap target in
     * {@link #calculateQ} so all zones share one next-action, matching the
     * single shared action the policy must actually take. Iterates all
     * nActions (parity with the legacy per-zone max). Ties broken
     * by lowest action index for determinism.
     */
    private int jointArgmaxAction(int stateIdx) {
        int best = -1;
        double bestVal = Double.NEGATIVE_INFINITY;
        for (int a = 0; a < nActions; a++) {
            if (blacklisted != null && blacklisted[a]) continue; // Phase 2: skip defective actions
            double v = combinedQ(stateIdx, a);
            if (v > bestVal) { bestVal = v; best = a; }
        }
        if (best < 0) best = 0; // safety: DO_NOTHING is never blacklisted, so unreachable
        return best;
    }

    /**
     * Argmax over ALL actions including blacklisted ones (combined Q). Used by
     * {@link #warmRestart} to identify "poisoned" states whose old greedy action
     * was the now-removed defective action.
     */
    private int unfilteredArgmax(int stateIdx) {
        int best = -1;
        double bestVal = Double.NEGATIVE_INFINITY;
        for (int a = 0; a < nActions; a++) {
            double v = combinedQ(stateIdx, a);
            if (v > bestVal) { bestVal = v; best = a; }
        }
        return best;
    }

    /**
     * Compute applicable actions. Delegates to StereotypeReasoner for masking
     * in stereotype mode; returns all actions in standard mode.
     * In soft-prior mode (maskStrict=false), always returns all actions so that
     * exploration is unblocked — the prior bias only affects greedy selection.
     */
    private int[] computeApplicableActions(Object[] stateVec) {
        if (!useStereotypes || !maskStrict) {
            // All non-blacklisted actions applicable — priors are applied in
            // greedy selection only. Phase 2: a blacklisted (defective) action
            // is removed from the action space entirely.
            int n = 0;
            int[] buf = new int[nActions];
            for (int i = 0; i < nActions; i++) {
                if (blacklisted == null || !blacklisted[i]) buf[n++] = i;
            }
            return Arrays.copyOf(buf, n);
        }
        // Hard masking for ablation (mask_strict=true)
        int[] sv = toIntArray(stateVec);
        int[] masked = reasoner.getApplicableActions(sv);
        if (blacklisted == null) return masked;
        int n = 0;
        int[] buf = new int[masked.length];
        for (int a : masked) if (!blacklisted[a]) buf[n++] = a;
        return Arrays.copyOf(buf, n);
    }

    /** Select greedy action from applicable set using combined Q + soft priors. */
    private int greedyAction(int stateIdx, int[] applicable) {
        // Retrieve priors only in soft-prior stereotype mode
        double[] priors = null;
        double   priorWeight = 0.0;
        int      sunBucket = 0;
        if (useStereotypes && !maskStrict) {
            // Decode state vector from index (needed for priors)
            int[] sv = decodeState(stateIdx);
            sunBucket = sunBucketOf(sv);
            priors = reasoner.getActionPriors(sv);
            // Linearly decay the prior weight from STEREO_PRIOR_SCALE down to
            // STEREO_PRIOR_SCALE * PRIOR_DECAY_FLOOR over priorDecayEpisodes
            // so stereotypes shape early exploration but learning dominates
            // late. Audit Step 3b §S3b-1: at bench, loadQTable explicitly sets
            // currentEpisodeNum = priorDecayEpisodes so this expression evaluates
            // to STEREO_PRIOR_SCALE * PRIOR_DECAY_FLOOR (the floor, as intended).
            // Without S3b-1 the bench counter is 0 and priorWeight is MAX.
            double frac = priorDecayEpisodes <= 0 ? 1.0
                        : Math.min(1.0, (double) currentEpisodeNum / priorDecayEpisodes);
            double w = 1.0 - frac * (1.0 - PRIOR_DECAY_FLOOR);
            priorWeight = STEREO_PRIOR_SCALE * w;
        }

        // Collect top-Q actions (tie-break random among ties) so a single
        // numerically-equal Q row doesn't pin the policy on the first index.
        double bestQ = Double.NEGATIVE_INFINITY;
        int[] tieBuf = new int[applicable.length];
        int   tieN   = 0;
        for (int a : applicable) {
            double effectivePrior = 0.0;
            if (priors != null) {
                double calMul = 1.0;
                if (ADAPTIVE_TRUST && actionCalN != null
                        && a < actionCalN.length
                        && sunBucket < actionCalN[a].length
                        && actionCalN[a][sunBucket] >= ADAPTIVE_TRUST_MIN_SAMPLES) {
                    double cal = actionCalSum[a][sunBucket] / actionCalN[a][sunBucket];
                    calMul = Math.max(ADAPTIVE_TRUST_FLOOR, cal);
                }
                // S2-4: per-cell visit fade — once a (state,action) cell has
                // been visited PRIOR_FADE_VISITS times its accumulated Q has
                // enough data to stand on its own, so the prior contribution
                // is faded out for that cell. Prevents the permanent floor
                // bias of STEREO_PRIOR_SCALE*PRIOR_DECAY_FLOOR*prior from
                // pinning the benchmark policy even after convergence.
                double cellMul = 1.0;
                if (PRIOR_FADE_VISITS > 0 && visitCounts != null) {
                    long v = visitCounts[stateIdx][a];
                    if (v > 0) {
                        cellMul = Math.min(1.0, (double) PRIOR_FADE_VISITS / v);
                    }
                }
                effectivePrior = priorWeight * priors[a] * calMul * cellMul;
            }
            double q = combinedQ(stateIdx, a) + effectivePrior;
            // Phase 4 (lab5): non-fading energy prior (see ENERGY_PRIOR_WEIGHT).
            // Triple-gated so it stays inert unless stereotypes are on, the knob
            // is set, and this action activates an actuator the KG marks as
            // costed (ws:energyCost > 0). Independent of priorWeight/cellMul, so
            // it persists through prior decay and into the benchmark — exactly
            // where the KG-primed agent must still prefer the efficient lamp.
            if (useStereotypes && ENERGY_PRIOR_WEIGHT > 0.0
                    && actionInfos != null && a < actionInfos.length
                    && actionInfos[a] != null
                    && actionInfos[a].wotValue
                    && actionInfos[a].energyCost > 0.0) {
                q -= ENERGY_PRIOR_WEIGHT * actionInfos[a].energyCost;
            }
            if (q > bestQ + 1e-9) {
                bestQ = q;
                tieN  = 0;
                tieBuf[tieN++] = a;
            } else if (Math.abs(q - bestQ) <= 1e-9) {
                tieBuf[tieN++] = a;
            }
        }
        if (tieN <= 1) return tieBuf[0];
        return tieBuf[rng.nextInt(tieN)];
    }

    /**
     * Map a state vector to its sun-rank bucket index. Returns 0 when the
     * sunshine slot is unavailable so the legacy single-column adaptive trust
     * behaviour is preserved.
     */
    private int sunBucketOf(int[] sv) {
        if (sv == null || sunshineIndex < 0 || sunshineIndex >= sv.length) return 0;
        int b = sv[sunshineIndex];
        if (b < 0) return 0;
        int max = (sunshineIndex < domainSizes.length) ? domainSizes[sunshineIndex] : 1;
        if (b >= max) return Math.max(0, max - 1);
        return b;
    }

    // ---- primitive coercion helpers (delegate to Converters) -------------

    private static int[] toIntArray(Object[] arr) { return Converters.toIntArray(arr); }

    private static int toInt(Object o) { return Converters.toInt(o); }

    private static int clamp(int v, int lo, int hi) { return Converters.clamp(v, lo, hi); }
}
