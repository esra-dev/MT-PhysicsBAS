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
 *   • observe(stateBefore, actionIdx, stateAfter)
 *   • saveLearnedStereotypes(filename) — writes Turtle
 *   • resetStats()
 *   • printStats()
 *
 * Statistical thresholds (defaults; override via -D system properties):
 *   stereotype.learner.minSamples   (default 30)   — minimum samples per (a,slot)
 *   stereotype.learner.zCutoff      (default 3.0)  — |mean| / SEM must exceed this
 *   stereotype.learner.minEffect    (default 0.05) — |mean| must exceed this (rank units)
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
        this.numActions  = numActionsIn;
        this.stateVecLen = stateVecLenIn;
        this.actionUris   = new String[numActions];
        this.actionValues = new boolean[numActions];
        this.actionLabels = new String[numActions];
        for (int a = 0; a < numActions; a++) {
            actionUris[a]   = (a < uris.length   && uris[a]   != null) ? String.valueOf(uris[a])   : "";
            actionValues[a] = (a < values.length && values[a] != null) && toBoolean(values[a]);
            actionLabels[a] = (a < labels.length && labels[a] != null) ? String.valueOf(labels[a]) : ("action_" + a);
        }
        count = new long[numActions][stateVecLen];
        mean  = new double[numActions][stateVecLen];
        m2    = new double[numActions][stateVecLen];
        LOGGER.info("StereotypeLearner: init numActions=" + numActions
                  + " stateVecLen=" + stateVecLen);
    }

    /**
     * Update Welford accumulators with one (state, action, next-state) sample.
     * No-op if {@link #initLearner} was not called or the indices are out of range.
     */
    @OPERATION
    public void observe(Object[] stateBefore, int actionIdx, Object[] stateAfter) {
        if (count == null || actionIdx < 0 || actionIdx >= numActions) return;
        int len = Math.min(stateBefore.length, Math.min(stateAfter.length, stateVecLen));
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

    /** Reset all Welford accumulators to zero (configuration is preserved). */
    @OPERATION
    public void resetStats() {
        if (count == null) return;
        for (int a = 0; a < numActions; a++) {
            java.util.Arrays.fill(count[a], 0L);
            java.util.Arrays.fill(mean[a], 0.0);
            java.util.Arrays.fill(m2[a],   0.0);
        }
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

    private static int toInt(Object o) {
        if (o instanceof Number) return ((Number) o).intValue();
        if (o instanceof Boolean) return ((Boolean) o) ? 1 : 0;
        return Integer.parseInt(String.valueOf(o));
    }

    private static boolean toBoolean(Object o) {
        if (o instanceof Boolean) return (Boolean) o;
        if (o instanceof Number)  return ((Number) o).intValue() != 0;
        return Boolean.parseBoolean(String.valueOf(o));
    }

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
