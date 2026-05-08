package tools;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

import cartago.Artifact;
import cartago.OPERATION;

/**
 * BenchmarkLogger — CArtAgO artifact for recording execution-phase benchmark metrics.
 *
 * Collects per-step data for each scenario run (scenario ID × run ID × agent type)
 * and accumulates the following metrics:
 *
 *   GoalReached              — whether the agent reached both zone targets
 *   Steps                    — total actions dispatched before terminal or budget
 *   CumIlluminanceDeviation  — Σ_t Σ_z |level_z(t) − target_z|  (lower = better)
 *   WastedSteps              — actions that left all zone levels and actuator states unchanged
 *   ActuatorCyclingCount     — number of actuator state reversals (ON→OFF or OFF→ON)
 *                              across the scenario (proxy for wear)
 *   CrossZoneInterferences   — steps where an action moved a non-target zone away from its target
 *   TotalEnergyCost          — cumulative energy cost reported by the simulator
 *
 * Usage:
 *   beginScenario(id, runId, agentType, initialState)
 *   [for each step:] recordStep(step, zoneLevels, targets, actionType,
 *                               wasted,
 *                               currActuatorStates,
 *                               crossZoneInterference)
 *   endScenario(goalReached, totalSteps, totalEnergyCost)
 *   [after all scenarios:] saveBenchmarkResults(filename)
 */
public class BenchmarkLogger extends Artifact {

    private static final Logger LOGGER = Logger.getLogger(BenchmarkLogger.class.getName());

    // -----------------------------------------------------------------------
    // Per-scenario accumulator fields
    // -----------------------------------------------------------------------
    private int     currentScenarioId;
    private int     currentRunId;
    private String  currentAgentType;
    private double  cumIlluminanceDeviation = 0.0;
    private int     wastedSteps             = 0;
    private int     actuatorCyclingCount    = 0;
    private int     crossZoneInterferences  = 0;

    // ── Phase 3 weakness-aware counters ─────────────────────────────────
    private int     silentlyDropped         = 0;  // W4: action took effect but lamp was budget-dropped
    private int     delayedEffectSteps      = 0;  // W3: action with no immediate effect (count of)
    private int     unmodelledZoneEffect    = 0;  // W1/W6: cross-zone change unexplained by ontology
    private int     conditionInversions     = 0;  // W2: action sign opposite of ontology prediction
    private int     topologyMismatches      = 0;  // W5: feeds-arc disagreement vs ontology
    private double  comfortDeviation        = 0.0;// W6: Σ |temp - target| (lower better)

    // Track previous actuator states for cycling detection (parallel arrays: name → bool)
    private Object[] lastActuatorKeys   = new Object[0];
    private Object[] lastActuatorValues = new Object[0];
    private boolean  firstStep          = true;

    // -----------------------------------------------------------------------
    // Completed scenario records
    // -----------------------------------------------------------------------
    private static class ScenarioRecord {
        int    scenarioId;
        int    runId;
        String agentType;
        boolean goalReached;
        int    steps;
        double cumIlluminanceDeviation;
        int    wastedSteps;
        int    actuatorCyclingCount;
        int    crossZoneInterferences;
        double totalEnergyCost;
        int    silentlyDropped;
        int    delayedEffectSteps;
        int    unmodelledZoneEffect;
        int    conditionInversions;
        int    topologyMismatches;
        double comfortDeviation;
    }

    private final List<ScenarioRecord> records = new ArrayList<>();

    // -----------------------------------------------------------------------
    // CArtAgO operations
    // -----------------------------------------------------------------------

    /**
     * Begin a new benchmark scenario. Resets all per-scenario accumulators.
     *
     * @param scenarioId   Unique scenario identifier (1-based).
     * @param runId        Run repetition index (1-based; 1–5 for 5-run benchmark).
     * @param agentType    Label for the agent: "rule_based", "ql_false", or "ql_true".
     * @param initialState Descriptor string (logged only, for traceability).
     */
    @OPERATION
    public void beginScenario(int scenarioId, int runId, String agentType, String initialState) {
        currentScenarioId         = scenarioId;
        currentRunId              = runId;
        currentAgentType          = agentType;
        cumIlluminanceDeviation   = 0.0;
        wastedSteps               = 0;
        actuatorCyclingCount      = 0;
        crossZoneInterferences    = 0;
        silentlyDropped           = 0;
        delayedEffectSteps        = 0;
        unmodelledZoneEffect      = 0;
        conditionInversions       = 0;
        topologyMismatches        = 0;
        comfortDeviation          = 0.0;
        lastActuatorKeys          = new Object[0];
        lastActuatorValues        = new Object[0];
        firstStep                 = true;
        LOGGER.info("BenchmarkLogger.beginScenario: id=" + scenarioId
                    + " run=" + runId + " agent=" + agentType
                    + " state=" + initialState);
    }

    /**
     * Record one step within the current scenario.
     *
     * @param step                  0-based step index.
     * @param zoneLevels            Current discretised illuminance ranks (Integer[]).
     * @param targets               Target ranks per zone (Integer[]).
     * @param actionType            WoT action type URI dispatched, or "none".
     * @param wasted                true if the action left all zone levels and actuator states unchanged.
     * @param currActuatorKeys      Actuator state URIs AFTER this action (Object[]).
     * @param currActuatorValues    Actuator boolean values AFTER this action (Object[]).
     * @param crossZoneInterference true if this action moved another zone away from its target.
     */
    @OPERATION
    public void recordStep(int step,
                           Object[] zoneLevels,
                           Object[] targets,
                           String   actionType,
                           boolean  wasted,
                           Object[] currActuatorKeys,
                           Object[] currActuatorValues,
                           boolean  crossZoneInterference) {

        // Illuminance deviation: Σ_z |level_z − target_z|
        for (int z = 0; z < zoneLevels.length && z < targets.length; z++) {
            int level  = toInt(zoneLevels[z]);
            int target = toInt(targets[z]);
            cumIlluminanceDeviation += Math.abs(level - target);
        }

        if (wasted) wastedSteps++;
        if (crossZoneInterference) crossZoneInterferences++;

        // Actuator cycling: count reversals relative to previous step's actuator states
        if (!firstStep && lastActuatorKeys.length > 0 && currActuatorKeys.length > 0) {
            actuatorCyclingCount += countReversals(
                    lastActuatorKeys, lastActuatorValues,
                    currActuatorKeys, currActuatorValues);
        }
        // Store current actuator state for next-step comparison
        lastActuatorKeys   = currActuatorKeys;
        lastActuatorValues = currActuatorValues;
        firstStep = false;

        LOGGER.fine("BenchmarkLogger.recordStep: step=" + step
                    + " deviation=" + cumIlluminanceDeviation
                    + " wasted=" + wastedSteps
                    + " cycling=" + actuatorCyclingCount
                    + " cross_zone=" + crossZoneInterferences
                    + " action=" + actionType);
    }

    /**
     * Close the current scenario and commit its record to the results list.
     *
     * @param goalReached     Whether both zone targets were met within the step budget.
     * @param totalSteps      Number of steps taken (including the terminal step).
     * @param totalEnergyCost Cumulative energy cost from the simulator's TotalEnergyCost field.
     */
    @OPERATION
    public void endScenario(boolean goalReached, int totalSteps, double totalEnergyCost) {
        ScenarioRecord r = new ScenarioRecord();
        r.scenarioId              = currentScenarioId;
        r.runId                   = currentRunId;
        r.agentType               = currentAgentType;
        r.goalReached             = goalReached;
        r.steps                   = totalSteps;
        r.cumIlluminanceDeviation = cumIlluminanceDeviation;
        r.wastedSteps             = wastedSteps;
        r.actuatorCyclingCount    = actuatorCyclingCount;
        r.crossZoneInterferences  = crossZoneInterferences;
        r.totalEnergyCost         = totalEnergyCost;
        r.silentlyDropped         = silentlyDropped;
        r.delayedEffectSteps      = delayedEffectSteps;
        r.unmodelledZoneEffect    = unmodelledZoneEffect;
        r.conditionInversions     = conditionInversions;
        r.topologyMismatches      = topologyMismatches;
        r.comfortDeviation        = comfortDeviation;
        records.add(r);
        LOGGER.info("BenchmarkLogger.endScenario: id=" + currentScenarioId
                    + " run=" + currentRunId + " goalReached=" + goalReached
                    + " steps=" + totalSteps + " cumDev=" + String.format("%.1f", cumIlluminanceDeviation)
                    + " energy=" + String.format("%.1f", totalEnergyCost));
    }

    /**
     * Write all accumulated scenario records to a CSV file.
     *
     * Columns:
     *   ScenarioId, RunId, AgentType, GoalReached, Steps,
     *   CumIlluminanceDeviation, WastedSteps,
     *   ActuatorCyclingCount, CrossZoneInterferences, TotalEnergyCost
     *
     * @param filename Target CSV filename (e.g. "benchmark_results_rule_based.csv").
     */
    @OPERATION
    public void saveBenchmarkResults(String filename) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println("ScenarioId,RunId,AgentType,GoalReached,Steps,"
                     + "CumIlluminanceDeviation,WastedSteps,"
                     + "ActuatorCyclingCount,CrossZoneInterferences,TotalEnergyCost,"
                     + "SilentlyDropped,DelayedEffectSteps,UnmodelledZoneEffect,"
                     + "ConditionInversions,TopologyMismatches,ComfortDeviation");
            for (ScenarioRecord r : records) {
                pw.printf("%d,%d,%s,%d,%d,%.2f,%d,%d,%d,%.2f,%d,%d,%d,%d,%d,%.2f%n",
                    r.scenarioId,
                    r.runId,
                    r.agentType,
                    r.goalReached ? 1 : 0,
                    r.steps,
                    r.cumIlluminanceDeviation,
                    r.wastedSteps,
                    r.actuatorCyclingCount,
                    r.crossZoneInterferences,
                    r.totalEnergyCost,
                    r.silentlyDropped,
                    r.delayedEffectSteps,
                    r.unmodelledZoneEffect,
                    r.conditionInversions,
                    r.topologyMismatches,
                    r.comfortDeviation);
            }
            LOGGER.info("BenchmarkLogger.saveBenchmarkResults: written " + records.size()
                        + " records to " + filename);
        } catch (IOException e) {
            LOGGER.warning("BenchmarkLogger.saveBenchmarkResults: failed to write "
                           + filename + " — " + e.getMessage());
        }
    }

    // -----------------------------------------------------------------------
    // Step-level debug log (bench_step_log_<mode>.csv)
    // -----------------------------------------------------------------------

    private static class StepLogRecord {
        int    scenarioId;
        int    runId;
        int    step;
        int[]  zoneLevelsBefore;
        int[]  targets;
        String actionLabel;
        int[]  zonelevelsAfter;
        boolean wasMasked; // reserved for QL stereotype mode
        boolean crossZoneInterference;
        // Rich-schema (Phase 1) — empty defaults so legacy recordStepDetail still works.
        double[]  temperatures   = new double[0];
        String[]  actuatorKeys   = new String[0];
        boolean[] actuatorVals   = new boolean[0];
        int       sunshineRank   = -1;
    }

    private final List<StepLogRecord> stepLog = new ArrayList<>();

    /**
     * Record a detailed per-step entry for the debug step log.
     *
     * @param step                  0-based step index.
     * @param zoneLevelsBefore      Zone ranks BEFORE the action.
     * @param zonelevelsAfter       Zone ranks AFTER the action.
     * @param targets               Target ranks per zone.
     * @param actionLabel           Human-readable action label (e.g. "SetZ1Light=ON").
     * @param wasMasked             Whether this action was masked/soft-penalised by stereotypes.
     * @param crossZoneInterference Whether a cross-zone interference was detected on this step.
     */
    @OPERATION
    public void recordStepDetail(int      step,
                                 Object[] zoneLevelsBefore,
                                 Object[] zonelevelsAfter,
                                 Object[] targets,
                                 String   actionLabel,
                                 boolean  wasMasked,
                                 boolean  crossZoneInterference) {
        StepLogRecord r = new StepLogRecord();
        r.scenarioId           = currentScenarioId;
        r.runId                = currentRunId;
        r.step                 = step;
        r.zoneLevelsBefore     = toIntArr(zoneLevelsBefore);
        r.zonelevelsAfter      = toIntArr(zonelevelsAfter);
        r.targets              = toIntArr(targets);
        r.actionLabel          = actionLabel;
        r.wasMasked            = wasMasked;
        r.crossZoneInterference = crossZoneInterference;
        stepLog.add(r);
    }

    /**
     * Rich variant of {@link #recordStepDetail} that also captures
     * per-zone temperatures, the post-action actuator snapshot, and the
     * sunshine rank. Used by the bench agent (Phase 2) so the slide-6
     * weakness predicates can be evaluated directly from the CSV.
     */
    @OPERATION
    public void recordStepDetailRich(int      step,
                                     Object[] zoneLevelsBefore,
                                     Object[] zonelevelsAfter,
                                     Object[] targets,
                                     String   actionLabel,
                                     boolean  wasMasked,
                                     boolean  crossZoneInterference,
                                     Object[] temperatures,
                                     Object[] actuatorKeys,
                                     Object[] actuatorVals,
                                     int      sunshineRank) {
        StepLogRecord r = new StepLogRecord();
        r.scenarioId           = currentScenarioId;
        r.runId                = currentRunId;
        r.step                 = step;
        r.zoneLevelsBefore     = toIntArr(zoneLevelsBefore);
        r.zonelevelsAfter      = toIntArr(zonelevelsAfter);
        r.targets              = toIntArr(targets);
        r.actionLabel          = actionLabel;
        r.wasMasked            = wasMasked;
        r.crossZoneInterference = crossZoneInterference;
        r.temperatures         = toDoubleArr(temperatures);
        r.actuatorKeys         = toStringArr(actuatorKeys);
        r.actuatorVals         = toBoolArr(actuatorVals);
        r.sunshineRank         = sunshineRank;
        stepLog.add(r);
    }

    /**
     * Write the accumulated step-log records to a CSV file.
     *
     * Columns: ScenarioId, RunId, Step, Z1Before, Z2Before, Z1Target, Z2Target,
     *          ActionLabel, Z1After, Z2After, WasMasked, CrossZoneInterference
     *
     * @param filename  Target CSV filename (e.g. "bench_step_log_ql_true.csv").
     */
    @OPERATION
    public void saveStepLog(String filename) {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            // Rich schema (Phase 1). Per-zone columns Z1..Z4 carry empty cells
            // when the active profile uses fewer zones.
            pw.println("ScenarioId,RunId,Step,"
                     + "Z1Before,Z2Before,Z3Before,Z4Before,"
                     + "Z1Target,Z2Target,Z3Target,Z4Target,"
                     + "ActionLabel,"
                     + "Z1After,Z2After,Z3After,Z4After,"
                     + "WasMasked,CrossZoneInterference,"
                     + "Z1Temp,Z2Temp,Z3Temp,Z4Temp,"
                     + "SunshineRank,ActuatorState");
            for (StepLogRecord r : stepLog) {
                StringBuilder sb = new StringBuilder();
                sb.append(r.scenarioId).append(',').append(r.runId).append(',').append(r.step).append(',');
                appendIntCell(sb, r.zoneLevelsBefore, 0); sb.append(',');
                appendIntCell(sb, r.zoneLevelsBefore, 1); sb.append(',');
                appendIntCell(sb, r.zoneLevelsBefore, 2); sb.append(',');
                appendIntCell(sb, r.zoneLevelsBefore, 3); sb.append(',');
                appendIntCell(sb, r.targets, 0); sb.append(',');
                appendIntCell(sb, r.targets, 1); sb.append(',');
                appendIntCell(sb, r.targets, 2); sb.append(',');
                appendIntCell(sb, r.targets, 3); sb.append(',');
                String label = r.actionLabel == null ? "" : r.actionLabel.replace(",", ";");
                sb.append(label).append(',');
                appendIntCell(sb, r.zonelevelsAfter, 0); sb.append(',');
                appendIntCell(sb, r.zonelevelsAfter, 1); sb.append(',');
                appendIntCell(sb, r.zonelevelsAfter, 2); sb.append(',');
                appendIntCell(sb, r.zonelevelsAfter, 3); sb.append(',');
                sb.append(r.wasMasked ? 1 : 0).append(',');
                sb.append(r.crossZoneInterference ? 1 : 0).append(',');
                appendDoubleCell(sb, r.temperatures, 0); sb.append(',');
                appendDoubleCell(sb, r.temperatures, 1); sb.append(',');
                appendDoubleCell(sb, r.temperatures, 2); sb.append(',');
                appendDoubleCell(sb, r.temperatures, 3); sb.append(',');
                if (r.sunshineRank >= 0) sb.append(r.sunshineRank);
                sb.append(',');
                sb.append(buildActuatorString(r.actuatorKeys, r.actuatorVals));
                pw.println(sb.toString());
            }
            LOGGER.info("BenchmarkLogger.saveStepLog: written " + stepLog.size()
                        + " records to " + filename);
        } catch (IOException e) {
            LOGGER.warning("BenchmarkLogger.saveStepLog: failed to write "
                           + filename + " — " + e.getMessage());
        }
    }

    private static void appendIntCell(StringBuilder sb, int[] arr, int i) {
        if (i < arr.length && arr[i] >= 0) sb.append(arr[i]);
    }

    private static void appendDoubleCell(StringBuilder sb, double[] arr, int i) {
        if (i < arr.length) sb.append(String.format(java.util.Locale.ROOT, "%.2f", arr[i]));
    }

    /**
     * Build a {@code key=val;key=val} string from parallel actuator arrays,
     * collapsing each URI to its fragment (text after '#'). Commas and
     * semicolons inside keys are stripped to keep the CSV column safe.
     */
    private static String buildActuatorString(String[] keys, boolean[] vals) {
        if (keys == null || keys.length == 0) return "";
        StringBuilder sb = new StringBuilder();
        int n = Math.min(keys.length, vals.length);
        for (int i = 0; i < n; i++) {
            String k = keys[i] == null ? "" : keys[i];
            int hash = k.lastIndexOf('#');
            if (hash >= 0) k = k.substring(hash + 1);
            k = k.replace(",", "").replace(";", "").replace("=", "");
            if (k.isEmpty()) continue;
            if (sb.length() > 0) sb.append(';');
            sb.append(k).append('=').append(vals[i]);
        }
        return sb.toString();
    }

    // -----------------------------------------------------------------------
    // Phase 3 — weakness-aware recording (called from bench agent)
    // -----------------------------------------------------------------------

    /**
     * Record a single weakness-flag observation against the current scenario.
     *
     * @param flag      One of: "w1_unmodelled", "w2_inversion",
     *                  "w3_delayed", "w4_dropped", "w5_topology".
     * @param magnitude Integer magnitude (e.g. number of dropped lamps,
     *                  number of inverted ranks). For boolean-style flags
     *                  pass 1.
     */
    @OPERATION
    public void recordWeakness(String flag, int magnitude) {
        if (flag == null) return;
        switch (flag) {
            case "w1_unmodelled":
            case "w6_unmodelled":
                unmodelledZoneEffect += magnitude; break;
            case "w2_inversion":   conditionInversions += magnitude; break;
            case "w3_delayed":     delayedEffectSteps  += magnitude; break;
            case "w4_dropped":     silentlyDropped     += magnitude; break;
            case "w5_topology":    topologyMismatches  += magnitude; break;
            default:
                LOGGER.warning("BenchmarkLogger.recordWeakness: unknown flag " + flag);
        }
    }

    /**
     * Accumulate W6 comfort deviation: caller passes |temp - target| for
     * the current step (summed across zones). Use 0.0 for steps that
     * don't advance the temperature signal.
     */
    @OPERATION
    public void recordComfortDeviation(double dev) {
        if (dev > 0.0) comfortDeviation += dev;
    }

    // -----------------------------------------------------------------------
    // Private helpers
    // -----------------------------------------------------------------------

    private static int[] toIntArr(Object[] arr) {
        int[] result = new int[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = toInt(arr[i]);
        return result;
    }

    private static double[] toDoubleArr(Object[] arr) {
        if (arr == null) return new double[0];
        double[] result = new double[arr.length];
        for (int i = 0; i < arr.length; i++) {
            Object o = arr[i];
            if (o instanceof Number) result[i] = ((Number) o).doubleValue();
            else {
                try { result[i] = Double.parseDouble(String.valueOf(o)); }
                catch (NumberFormatException e) { result[i] = Double.NaN; }
            }
        }
        return result;
    }

    private static String[] toStringArr(Object[] arr) {
        if (arr == null) return new String[0];
        String[] result = new String[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = String.valueOf(arr[i]);
        return result;
    }

    private static boolean[] toBoolArr(Object[] arr) {
        if (arr == null) return new boolean[0];
        boolean[] result = new boolean[arr.length];
        for (int i = 0; i < arr.length; i++) result[i] = toBoolean(arr[i]);
        return result;
    }

    /**
     * Count the number of actuator state reversals between two snapshots.
     * Two parallel key/value arrays represent actuator states; a reversal is
     * any key whose boolean value differs between prev and curr.
     */
    private int countReversals(Object[] prevKeys, Object[] prevVals,
                               Object[] currKeys, Object[] currVals) {
        int reversals = 0;
        for (int i = 0; i < prevKeys.length; i++) {
            String key = String.valueOf(prevKeys[i]);
            boolean prevVal = toBoolean(prevVals[i]);
            // Find matching key in curr
            for (int j = 0; j < currKeys.length; j++) {
                if (key.equals(String.valueOf(currKeys[j]))) {
                    boolean currVal = toBoolean(currVals[j]);
                    if (prevVal != currVal) reversals++;
                    break;
                }
            }
        }
        return reversals;
    }

    private static int toInt(Object o) {
        if (o instanceof Number) return ((Number) o).intValue();
        return Integer.parseInt(String.valueOf(o));
    }

    private static boolean toBoolean(Object o) {
        if (o instanceof Boolean) return (Boolean) o;
        if (o instanceof Number)  return ((Number) o).intValue() != 0;
        return Boolean.parseBoolean(String.valueOf(o));
    }

    // -----------------------------------------------------------------------
    // Rich JSONL trace (Phase F)
    //   Optional, append-only newline-delimited JSON file containing one
    //   record per benchmark step. Used by analysis/sweep_report.py for
    //   per-weakness fire-density plots and learning-curve diagnostics.
    //   Open with openTraceJsonl(filename); records are flushed per step.
    //   Closed implicitly when the agent terminates.
    // -----------------------------------------------------------------------

    private PrintWriter traceWriter = null;
    private String      traceFile   = null;

    /**
     * Open (or replace) a JSONL trace file. Each subsequent recordRichStep
     * call writes one line. Re-opening with the same name truncates.
     */
    @OPERATION
    public void openTraceJsonl(String filename) {
        try {
            if (traceWriter != null) {
                traceWriter.flush();
                traceWriter.close();
            }
            // Ensure the parent directory exists when callers pass a nested
            // path like "benchmark/results/<profile>/<mode>/trace_bench_…".
            java.io.File f = new java.io.File(filename);
            java.io.File parent = f.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();
            traceWriter = new PrintWriter(new FileWriter(f, false));
            traceFile   = filename;
            LOGGER.info("openTraceJsonl: writing rich trace to " + filename);
        } catch (IOException e) {
            LOGGER.warning("openTraceJsonl: failed to open " + filename + " — " + e.getMessage());
            traceWriter = null;
            traceFile   = null;
        }
    }

    /**
     * Append one rich-trace record. No-op if openTraceJsonl was not called.
     *
     * @param step                Step index (0-based).
     * @param stateBefore         State vector at start of step.
     * @param actionIdx           Action index dispatched (or -1).
     * @param applicableActions   Integer[] of action indices considered applicable.
     * @param predictedDelta      Per-slot ontology Δ prediction (Integer[]).
     * @param stateAfter          State vector after the step.
     * @param qDelta              max |q_new − q_old| across zones for this step.
     * @param weaknessFlagsFired  String[] of fingerprint names raised this step.
     */
    @OPERATION
    public void recordRichStep(int      step,
                               Object[] stateBefore,
                               int      actionIdx,
                               Object[] applicableActions,
                               Object[] predictedDelta,
                               Object[] stateAfter,
                               double   qDelta,
                               Object[] weaknessFlagsFired) {
        if (traceWriter == null) return;
        StringBuilder sb = new StringBuilder(256);
        sb.append('{')
          .append("\"scenarioId\":").append(currentScenarioId).append(',')
          .append("\"runId\":").append(currentRunId).append(',')
          .append("\"step\":").append(step).append(',')
          .append("\"actionIdx\":").append(actionIdx).append(',')
          .append("\"qDelta\":").append(qDelta).append(',');
        appendIntArr(sb, "stateBefore", stateBefore).append(',');
        appendIntArr(sb, "stateAfter",  stateAfter).append(',');
        appendIntArr(sb, "predictedDelta", predictedDelta).append(',');
        appendIntArr(sb, "applicableActions", applicableActions).append(',');
        appendStrArr(sb, "weaknessFired", weaknessFlagsFired);
        sb.append('}');
        traceWriter.println(sb.toString());
        traceWriter.flush();
    }

    /** Close the JSONL trace writer if open. */
    @OPERATION
    public void closeTraceJsonl() {
        if (traceWriter != null) {
            traceWriter.flush();
            traceWriter.close();
            traceWriter = null;
            LOGGER.info("closeTraceJsonl: closed " + traceFile);
            traceFile = null;
        }
    }

    private static StringBuilder appendIntArr(StringBuilder sb, String key, Object[] arr) {
        sb.append('"').append(key).append("\":[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(toInt(arr[i]));
        }
        return sb.append(']');
    }

    private static StringBuilder appendBoolArr(StringBuilder sb, String key, Object[] arr) {
        sb.append('"').append(key).append("\":[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(toBoolean(arr[i]) ? "true" : "false");
        }
        return sb.append(']');
    }

    private static StringBuilder appendStrArr(StringBuilder sb, String key, Object[] arr) {
        sb.append('"').append(key).append("\":[");
        for (int i = 0; i < arr.length; i++) {
            if (i > 0) sb.append(',');
            sb.append('"').append(escapeJson(String.valueOf(arr[i]))).append('"');
        }
        return sb.append(']');
    }

    private static String escapeJson(String s) {
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
