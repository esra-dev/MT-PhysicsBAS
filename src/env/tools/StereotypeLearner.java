package tools;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.logging.Logger;

import cartago.Artifact;
import cartago.OPERATION;

/**
 * StereotypeLearner — CArtAgO artifact that observes (state, action, next-state)
 * triples during Q-learning and accumulates a per-(action, state-slot) running
 * mean and variance of the observed Δ using Welford's algorithm.
 *
 * Once enough samples have been collected, it can dump those (action, slot)
 * pairs whose mean Δ is large relative to its standard error as a Turtle
 * "discovered effect" file. The intention is to surface ontology gaps:
 * effects the simulator exhibits that are not declared in the original lab
 * stereotype definitions (a learning-side counterpart to the bench-agent's
 * weakness fingerprints in {@link QLearner#classifyWeaknesses}).
 *
 * Operations:
 *   • initLearner(numActions, stateVecLen, actionUris, actionValues, actionLabels)
 *   • initLearner(…, svBits, expectedBits) — Phase 5 overload, enables the
 *     flip-conditioned admission gate (see below)
 *   • observe(stateBefore, actionIdx, stateAfter)
 *   • saveLearnedStereotypes(filename) — writes Turtle
 *   • saveRawStats(filename) — Phase 5: dumps the raw Welford accumulators as
 *     CSV for offline overlay synthesis (tools.OverlaySynthesizer)
 *   • resetStats()
 *   • printStats()
 *
 * Statistical thresholds (defaults; override via -D system properties):
 *   stereotype.learner.minSamples   (default 30)   — minimum samples per (a,slot)
 *   stereotype.learner.zCutoff      (default 3.0)  — |mean| / SEM must exceed this
 *   stereotype.learner.minEffect    (default 0.05) — |mean| must exceed this (rank units)
 *
 * Phase 5 — flip-conditioned admission (gated instrument):
 *   -Dstereotype.learner.flipConditioned=true (default false, read at
 *   initLearner time) admits a (state, action, next-state) sample into the
 *   accumulators ONLY when the action's commanded state-vector bit actually
 *   flipped to its expected post-action value. This conditions the per-slot Δ
 *   estimate on real actuation (a redundant ON command on an already-ON device
 *   contributes no Δ evidence and would otherwise dilute the mean toward 0).
 *   Requires the 7-argument initLearner overload; with the legacy 5-argument
 *   init the gate is inert (no svBit metadata → every sample admitted).
 *   Samples for actions without a commanded bit (DO_NOTHING) are always
 *   admitted. Both learner arms run the identical instrument.
 *
 * Note: the test is |mean| / SEM (standard error of the mean = stddev / sqrt(n)),
 * which is the correct "is the mean different from zero?" test for an online
 * Welford accumulator.  An earlier version used |mean| / stddev, which is
 * roughly sqrt(n) times stricter and rejected nearly every real effect.
 */
public class StereotypeLearner extends Artifact {

    private static final Logger LOGGER = Logger.getLogger(StereotypeLearner.class.getName());

    private static final int    MIN_SAMPLES = getIntProp ("stereotype.learner.minSamples", 30);
    private static final double Z_CUTOFF    = getDblProp ("stereotype.learner.zCutoff",    3.0);
    private static final double MIN_EFFECT  = getDblProp ("stereotype.learner.minEffect",  0.05);
    private static final double EPS         = 1e-9;

    private static int getIntProp(String k, int d) {
        try { return Integer.parseInt(System.getProperty(k, Integer.toString(d))); }
        catch (NumberFormatException e) { return d; }
    }
    private static double getDblProp(String k, double d) {
        try { return Double.parseDouble(System.getProperty(k, Double.toString(d))); }
        catch (NumberFormatException e) { return d; }
    }

    // Configuration
    private int numActions   = 0;
    private int stateVecLen  = 0;
    private String[]  actionUris   = new String[0];
    private boolean[] actionValues = new boolean[0];
    private String[]  actionLabels = new String[0];

    // Phase 5 — per-action commanded-bit metadata (7-arg initLearner overload).
    // svBits[a] = state-vector slot the action commands (-1 = none/DO_NOTHING);
    // expectedBits[a] = bit value AFTER a successful command (-1 = unknown).
    private int[] svBits       = new int[0];
    private int[] expectedBits = new int[0];
    // Flip-conditioned admission gate; read from
    // -Dstereotype.learner.flipConditioned at initLearner time (per instance,
    // so tests can toggle it), inert unless svBits metadata was supplied.
    private boolean flipConditioned = false;
    // Admission counters (diagnostics; dumped by saveRawStats).
    private long admittedSamples = 0;
    private long rejectedNoFlip  = 0;

    // Welford accumulators per (action, slot)
    private long[][]   count;   // [numActions][stateVecLen]
    private double[][] mean;    // [numActions][stateVecLen]
    private double[][] m2;      // [numActions][stateVecLen]

    /**
     * Initialise the learner. Idempotent — re-init zeroes all accumulators.
     *
     * @param numActionsIn   Total action count (incl. DO_NOTHING).
     * @param stateVecLenIn  Length of the state vector.
     * @param uris           Object[] of String — WoT action type URI per action.
     * @param values         Object[] of Boolean — activation flag per action.
     * @param labels         Object[] of String — human-readable label per action.
     */
    @OPERATION
    public void initLearner(int numActionsIn,
                            int stateVecLenIn,
                            Object[] uris,
                            Object[] values,
                            Object[] labels) {
        initLearner(numActionsIn, stateVecLenIn, uris, values, labels,
                    new Object[0], new Object[0]);
    }

    /**
     * Phase 5 overload: additionally seed per-action commanded-bit metadata so
     * the flip-conditioned admission gate can operate. Back-compatible — the
     * legacy 5-argument operation delegates here with empty arrays (svBit /
     * expectedBit default to -1 per action, which keeps the gate inert).
     *
     * @param svBitsIn       Object[] of Integer — state-vector slot the action
     *                       commands (-1 for DO_NOTHING / unknown).
     * @param expectedBitsIn Object[] of Integer — bit value after a successful
     *                       command (1=ON, 0=OFF, -1 unknown).
     */
    @OPERATION
    public void initLearner(int numActionsIn,
                            int stateVecLenIn,
                            Object[] uris,
                            Object[] values,
                            Object[] labels,
                            Object[] svBitsIn,
                            Object[] expectedBitsIn) {
        this.numActions  = numActionsIn;
        this.stateVecLen = stateVecLenIn;
        this.actionUris   = new String[numActions];
        this.actionValues = new boolean[numActions];
        this.actionLabels = new String[numActions];
        this.svBits       = new int[numActions];
        this.expectedBits = new int[numActions];
        for (int a = 0; a < numActions; a++) {
            actionUris[a]   = (a < uris.length   && uris[a]   != null) ? String.valueOf(uris[a])   : "";
            actionValues[a] = (a < values.length && values[a] != null) && toBoolean(values[a]);
            actionLabels[a] = (a < labels.length && labels[a] != null) ? String.valueOf(labels[a]) : ("action_" + a);
            svBits[a]       = (a < svBitsIn.length       && svBitsIn[a]       != null) ? toInt(svBitsIn[a])       : -1;
            expectedBits[a] = (a < expectedBitsIn.length && expectedBitsIn[a] != null) ? toInt(expectedBitsIn[a]) : -1;
        }
        this.flipConditioned =
            Boolean.parseBoolean(System.getProperty("stereotype.learner.flipConditioned", "false"));
        this.admittedSamples = 0;
        this.rejectedNoFlip  = 0;
        count = new long[numActions][stateVecLen];
        mean  = new double[numActions][stateVecLen];
        m2    = new double[numActions][stateVecLen];
        LOGGER.info("StereotypeLearner: init numActions=" + numActions
                  + " stateVecLen=" + stateVecLen
                  + " flipConditioned=" + flipConditioned);
    }

    /**
     * Update Welford accumulators with one (state, action, next-state) sample.
     * No-op if {@link #initLearner} was not called or the indices are out of range.
     */
    @OPERATION
    public void observe(Object[] stateBefore, int actionIdx, Object[] stateAfter) {
        if (count == null || actionIdx < 0 || actionIdx >= numActions) return;
        int len = Math.min(stateBefore.length, Math.min(stateAfter.length, stateVecLen));
        // Phase 5 — flip-conditioned admission: with the gate enabled and a
        // commanded bit known for this action, admit the sample only if that
        // bit actually flipped to its expected post-action value. Actions
        // without a commanded bit (DO_NOTHING) are always admitted.
        if (flipConditioned && actionIdx < svBits.length && svBits[actionIdx] >= 0) {
            int bit = svBits[actionIdx];
            if (bit >= len) { rejectedNoFlip++; return; }
            int before = toInt(stateBefore[bit]);
            int after  = toInt(stateAfter[bit]);
            boolean flipped = before != after
                && (expectedBits[actionIdx] < 0 || after == expectedBits[actionIdx]);
            if (!flipped) { rejectedNoFlip++; return; }
        }
        admittedSamples++;
        for (int s = 0; s < len; s++) {
            double delta = toInt(stateAfter[s]) - toInt(stateBefore[s]);
            // Welford online update
            count[actionIdx][s] += 1;
            double n = count[actionIdx][s];
            double oldMean = mean[actionIdx][s];
            double newMean = oldMean + (delta - oldMean) / n;
            mean[actionIdx][s] = newMean;
            m2[actionIdx][s]  += (delta - oldMean) * (delta - newMean);
        }
    }

    /**
     * Dump learned stereotypes to a Turtle file. Emits one
     * {@code learned:DiscoveredEffect} blank node per (action, slot) pair
     * whose mean Δ exceeds {@link #Z_CUTOFF} standard deviations and whose
     * sample count is at least {@link #MIN_SAMPLES}.
     */
    @OPERATION
    public void saveLearnedStereotypes(String filename) {
        if (count == null) {
            LOGGER.warning("saveLearnedStereotypes: learner not initialised — skipping");
            return;
        }
        int written = 0;
        int considered = 0;
        int rejectedSamples = 0;
        int rejectedZ = 0;
        int rejectedEffect = 0;
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("@prefix learned: <http://example.org/was/learned#> .");
            pw.println("@prefix elem:    <http://w3id.org/elementary#> .");
            pw.println("@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .");
            pw.println();
            pw.println("# Auto-generated by tools.StereotypeLearner");
            pw.println("# test: |mean|/SEM > zCutoff  AND  |mean| >= minEffect  AND  n >= minSamples");
            pw.println("# zCutoff="  + Z_CUTOFF
                     + "  minSamples=" + MIN_SAMPLES
                     + "  minEffect="  + MIN_EFFECT);
            pw.println();
            for (int a = 0; a < numActions; a++) {
                for (int s = 0; s < stateVecLen; s++) {
                    long n = count[a][s];
                    considered++;
                    if (n < MIN_SAMPLES) { rejectedSamples++; continue; }
                    double mu  = mean[a][s];
                    double var = (n > 1) ? (m2[a][s] / (n - 1)) : 0.0;
                    double sd  = Math.sqrt(Math.max(var, 0.0));
                    // Standard error of the mean: sd / sqrt(n).  This is the
                    // correct denominator for testing whether the population
                    // mean differs from zero given n online samples.
                    double sem = sd / Math.sqrt(n);
                    double zScore = Math.abs(mu) / Math.max(sem, EPS);
                    if (zScore < Z_CUTOFF)               { rejectedZ++;      continue; }
                    if (Math.abs(mu) < MIN_EFFECT)       { rejectedEffect++; continue; }
                    pw.println("[] a learned:DiscoveredEffect ;");
                    if (!actionUris[a].isEmpty()) {
                        pw.println("   learned:action      <" + actionUris[a] + "> ;");
                    }
                    pw.println("   learned:actionValue \""
                             + (actionValues[a] ? "true" : "false")
                             + "\"^^xsd:boolean ;");
                    pw.println("   learned:actionLabel \"" + escapeTurtle(actionLabels[a]) + "\" ;");
                    pw.println("   learned:slotIndex   \"" + s + "\"^^xsd:int ;");
                    pw.println("   learned:meanDelta   \"" + String.format(java.util.Locale.ROOT, "%.4f", mu) + "\"^^xsd:double ;");
                    pw.println("   learned:stddev      \"" + String.format(java.util.Locale.ROOT, "%.4f", sd) + "\"^^xsd:double ;");
                    pw.println("   learned:sem         \"" + String.format(java.util.Locale.ROOT, "%.4f", sem) + "\"^^xsd:double ;");
                    pw.println("   learned:zScore      \"" + String.format(java.util.Locale.ROOT, "%.2f", zScore) + "\"^^xsd:double ;");
                    pw.println("   learned:samples     \"" + n + "\"^^xsd:int .");
                    pw.println();
                    written++;
                }
            }
            LOGGER.info("saveLearnedStereotypes: " + written + " effects written to " + filename
                      + " (considered=" + considered
                      + " rejected: samples=" + rejectedSamples
                      + ", z=" + rejectedZ
                      + ", effect=" + rejectedEffect + ")");
        } catch (IOException e) {
            LOGGER.warning("saveLearnedStereotypes: failed to write " + filename
                         + " — " + e.getMessage());
        }
    }

    /**
     * Phase 5 — dump the RAW Welford accumulators (every (action, slot) cell,
     * no significance gating) plus the action metadata as CSV. This is the
     * hand-off artifact consumed offline by {@link OverlaySynthesizer}, which
     * applies the emission gates and synthesizes the learned KG overlay TTL.
     * The legacy {@link #saveLearnedStereotypes} Turtle dump is unchanged.
     *
     * Format (version header + key=value comment lines, then one CSV row per
     * (action, slot) cell; mean/sd are written with Double.toString for exact
     * round-trip):
     * <pre>
     *   # stereotype_learner_raw_stats_v1
     *   # numActions=5
     *   # stateVecLen=3
     *   # flipConditioned=true
     *   # admittedSamples=1234
     *   # rejectedNoFlip=56
     *   actionIdx,wotActionUri,actionValue,actionLabel,svBit,expectedBit,slot,n,mean,sd
     * </pre>
     */
    @OPERATION
    public void saveRawStats(String filename) {
        if (count == null) {
            LOGGER.warning("saveRawStats: learner not initialised — skipping");
            return;
        }
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("# stereotype_learner_raw_stats_v1");
            pw.println("# numActions=" + numActions);
            pw.println("# stateVecLen=" + stateVecLen);
            pw.println("# flipConditioned=" + flipConditioned);
            pw.println("# admittedSamples=" + admittedSamples);
            pw.println("# rejectedNoFlip=" + rejectedNoFlip);
            pw.println("actionIdx,wotActionUri,actionValue,actionLabel,svBit,expectedBit,slot,n,mean,sd");
            for (int a = 0; a < numActions; a++) {
                int svBit  = (a < svBits.length)       ? svBits[a]       : -1;
                int expBit = (a < expectedBits.length) ? expectedBits[a] : -1;
                for (int s = 0; s < stateVecLen; s++) {
                    long n = count[a][s];
                    double mu  = mean[a][s];
                    double var = (n > 1) ? (m2[a][s] / (n - 1)) : 0.0;
                    double sd  = Math.sqrt(Math.max(var, 0.0));
                    pw.println(a + ","
                             + actionUris[a] + ","
                             + actionValues[a] + ","
                             + actionLabels[a].replace(',', ';') + ","
                             + svBit + ","
                             + expBit + ","
                             + s + ","
                             + n + ","
                             + mu + ","
                             + sd);
                }
            }
            LOGGER.info("saveRawStats: " + (numActions * stateVecLen)
                      + " cells written to " + filename
                      + " (flipConditioned=" + flipConditioned
                      + " admitted=" + admittedSamples
                      + " rejectedNoFlip=" + rejectedNoFlip + ")");
        } catch (IOException e) {
            LOGGER.warning("saveRawStats: failed to write " + filename
                         + " — " + e.getMessage());
        }
    }

    /** Reset all Welford accumulators to zero (configuration is preserved). */
    @OPERATION
    public void resetStats() {
        if (count == null) return;
        for (int a = 0; a < numActions; a++) {
            java.util.Arrays.fill(count[a], 0L);
            java.util.Arrays.fill(mean[a], 0.0);
            java.util.Arrays.fill(m2[a],   0.0);
        }
        admittedSamples = 0;
        rejectedNoFlip  = 0;
    }

    /** Print a short summary of accumulated samples for diagnostics. */
    @OPERATION
    public void printStats() {
        if (count == null) {
            LOGGER.info("StereotypeLearner: not initialised");
            return;
        }
        long total = 0;
        int  filled = 0;
        for (int a = 0; a < numActions; a++) {
            for (int s = 0; s < stateVecLen; s++) {
                total += count[a][s];
                if (count[a][s] > 0) filled++;
            }
        }
        LOGGER.info("StereotypeLearner stats: total samples=" + total
                  + " populated cells=" + filled
                  + "/" + (numActions * stateVecLen));
    }

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------

    private static int toInt(Object o) { return Converters.toInt(o); }

    private static boolean toBoolean(Object o) { return Converters.toBoolean(o); }

    private static String escapeTurtle(String s) {
        if (s == null) return "";
        StringBuilder sb = new StringBuilder(s.length() + 2);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n");  break;
                case '\r': sb.append("\\r");  break;
                case '\t': sb.append("\\t");  break;
                default:   sb.append(c);
            }
        }
        return sb.toString();
    }
}
