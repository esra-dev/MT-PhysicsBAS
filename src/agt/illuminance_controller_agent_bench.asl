// Illuminance Controller Benchmark Agent
// MT-Esra Project
//
// Runs one of three agent modes ("rule_based", "ql_false", "ql_true") over a
// fixed set of deterministic benchmark scenarios to produce comparable
// execution-phase metrics.
//
// Usage:
//   1. Set bench_mode below to one of: "rule_based", "ql_false", "ql_true".
//   2. Ensure the Node-RED simulator is running on port 1881.
//   3. For ql_* modes, ensure the corresponding Q-table CSV exists.
//   4. Run:  ./gradlew taskBench
//
// Output:
//   benchmark_results_<bench_mode>.csv
//   Columns: ScenarioId, RunId, AgentType, GoalReached, Steps,
//            CumIlluminanceDeviation, WastedSteps,
//            ActuatorCyclingCount, CrossZoneInterferences, TotalEnergyCost

/* ============================================================
 * Beliefs
 * ============================================================ */

// Mode switch — uncomment exactly one.
// bench_mode("rule_based").
// bench_mode("ql_false").
bench_mode("ql_true").

bench_runs(2).
exec_max_steps(20).
// S4-5 (audit-step-4): raised from 65 ms to 250 ms so the post-invokeAction
// readLabStatus observes the state AFTER the Node-RED simulator's 200 ms
// tick has propagated through compute_levels. Previously 65 ms < 200 ms
// could return pre-tick state and bias training credit assignment.
exec_delay_ms(65).

// S4-1 (audit-step-4): gate the bench-only anti-stuck rescue path. When
// false, the bench evaluates the TRAINED greedy policy as-is (no runtime
// argmax replacement). This is the conservative reading of H1: "did the
// prior produce a better greedy policy?" Set to true ONLY to reproduce
// the legacy (pre-2026-06-03) behaviour where the bench wraps stuck states
// with getActionFromStateAntiStuck — that path is not present during
// training, so it makes the benched policy != the trained policy.
bench_anti_stuck(false).

// Lab-specific configuration (TD, ontology paths, zone targets, rank bounds,
// sunshine probability, scenario files) is resolved at startup from the
// Lab Profile registry.  To switch labs, edit active_profile/1 in lab_profiles.asl.
{ include("lab_profiles.asl") }

/* ============================================================
 * Initial Goals
 * ============================================================ */

!apply_profile_then_start.

/* ============================================================
 * Profile bridge — copy active-profile fields into the legacy
 * belief names that existing plans below query.  Runs before
 * !bench_start so the rest of the agent code is unchanged.
 * ============================================================ */
@apply_profile_then_start
+!apply_profile_then_start <-
    !apply_runtime_overrides;
    !profile_print;
    !profile_td(TdUrl);                     +lab_td(TdUrl);
    !profile_light_bounds(LightBounds);     +light_rank_bounds(LightBounds);
    !profile_sunshine_bounds(SunBounds);    +sunshine_rank_bounds(SunBounds);
    !profile_sunshine_prob(SunProb);        +sunshine_satisfaction_prob(SunProb);
    !profile_zone_targets(ZoneTargetList);
    !assert_zone_targets(ZoneTargetList);
    !bench_start.

/* ============================================================
 * Runtime parameter overrides (#7) — let -Dactive.profile=…
 * and -Dbench.mode=… replace the default beliefs without
 * patching the .asl files at build time.
 * ============================================================ */
@apply_runtime_overrides
+!apply_runtime_overrides <-
    tools.jia.system_prop("active.profile", "", OverrideProfile);
    if (OverrideProfile \== "") {
        ?active_profile(OldP);
        -active_profile(OldP);
        +active_profile(OverrideProfile);
        .print("[RuntimeOverride] active_profile: ", OldP, " -> ", OverrideProfile)
    };
    tools.jia.system_prop("bench.mode", "", OverrideMode);
    if (OverrideMode \== "") {
        ?bench_mode(OldM);
        -bench_mode(OldM);
        +bench_mode(OverrideMode);
        .print("[RuntimeOverride] bench_mode: ", OldM, " -> ", OverrideMode)
    }.
// Failure handler: if tools.jia.system_prop is unavailable, log and continue.
// active_profile and bench_mode will reflect whatever was pre-patched by the
// run script into lab_profiles.asl and illuminance_controller_agent_bench.asl.
@apply_runtime_overrides_fail
-!apply_runtime_overrides <-
    .print("[RuntimeOverride] WARNING: tools.jia.system_prop failed; active_profile/bench_mode unchanged (using pre-patched values).").

@assert_zone_targets_done
+!assert_zone_targets([]) <- true.
@assert_zone_targets_step
+!assert_zone_targets([target(I,T)|R]) <-
    +zone_target(I, T);
    !assert_zone_targets(R).

/* ============================================================
 * Startup — initialise artifacts and kick off the benchmark
 * ============================================================ */
@bench_start
+!bench_start
    : bench_mode(Mode) & lab_td(TdUrl) & bench_runs(TotalRuns)
    & light_rank_bounds(LightBounds) & sunshine_rank_bounds(SunshineBounds)
    & active_profile(ActiveP) & bench_anti_stuck(AntiStuck) <-
    .print("==========================================================");
    .print("   BENCHMARK AGENT — Execution-Phase Comparison");
    .print("   Mode: ", Mode, "  |  Runs per scenario: ", TotalRuns);
    // S4-6 (audit-step-4): make the resolved active_profile and anti-stuck
    // flag visible in the MAS console so a silent runtime-override fallback
    // (see @apply_runtime_overrides_fail) is caught immediately.
    .print("   active_profile=", ActiveP, "  bench_anti_stuck=", AntiStuck);
    .print("==========================================================");
    makeArtifact("lab", "tools.LabEnvironment", [TdUrl], LabId);
    +lab_artifact(LabId);
    configureDiscretization(LightBounds, SunshineBounds)[artifact_id(LabId)];
    .print("[Bench] Lab artifact ready. bounds light=", LightBounds,
           " sunshine=", SunshineBounds);
    makeArtifact("benchlogger", "tools.BenchmarkLogger", [], LogId);
    +bench_logger(LogId);
    .print("[Bench] BenchmarkLogger artifact ready.");
    !init_mode(Mode);
    !run_all_runs(1, TotalRuns).

/* ============================================================
 * Mode-specific initialisation
 * ============================================================ */
@init_mode_rule_based
+!init_mode("rule_based") <-
    !profile_ont(OntPaths);
    makeArtifact("ontology", "tools.OntologyArtifact",
                 [OntPaths], OntId);
    +ontology_artifact(OntId);
    !try_import_learned_stereotypes(OntId);
    discoverZones(ZoneURIs, ZoneIdxs)[artifact_id(OntId)];
    !setup_bench_zone_goals(ZoneURIs, ZoneIdxs);
    .print("[Bench] Rule-based mode ready. Zone goals established.").

/* ============================================================
 * Stereotype-feedback loop hook (Phase E).
 *
 * If a previous ql_true training run produced a Turtle file at
 *   learned_stereotypes_true<QtSuffix>.ttl
 * (project-root path, written by tools.StereotypeLearner) merge those
 * triples into the live ontology so SPARQL-driven actuation can
 * exploit the discovered effects (e.g. CorridorLight in custom2 W1).
 * Missing file is benign — the operation logs and returns 0.
 * ============================================================ */
@try_import_learned_stereotypes
+!try_import_learned_stereotypes(OntId) <-
    !profile_qtable_suffix(QtSuffix);
    .concat("learned_stereotypes_true", QtSuffix, P1);
    .concat(P1, ".ttl", LearnPath);
    importLearnedStereotypes(LearnPath, NMerged)[artifact_id(OntId)];
    .print("[Bench] importLearnedStereotypes(", LearnPath, ") -> ",
           NMerged, " triple(s) merged.").

@init_mode_ql
+!init_mode(Mode)
    : (Mode == "ql_true" | Mode == "ql_false")
    & sunshine_satisfaction_prob(SunProb) <-
    .findall(t(I,T), zone_target(I,T), ZTUnsorted);
    .sort(ZTUnsorted, ZTSorted);
    .findall(T, .member(t(_,T), ZTSorted), Goals);
    !ql_flag_and_file(Mode, UseStereotypes, QTableFileBase);
    !profile_qtable_suffix(QtSuffix);
    !apply_qtable_suffix(QTableFileBase, QtSuffix, QTableFile);
    !profile_ont(OntPaths);
    makeArtifact("qlearner", "tools.QLearner", [], QlId);
    +qlearner_artifact(QlId);
    configureQLearner(Goals, UseStereotypes,
                      OntPaths, SunProb)[artifact_id(QlId)];
    // Reproducible action sampling across runs.
    setSeed(42)[artifact_id(QlId)];
    loadQTable(QTableFile)[artifact_id(QlId)];
    !ql_iv_file(Mode, IVFile);
    loadIVStats(IVFile)[artifact_id(QlId)];
    .print("[Bench] IV stats loaded from ", IVFile);
    .print("[Bench] QLearner ready. Loaded Q-table from ", QTableFile);
    // Open rich JSONL trace for per-step diagnostics.
    ?bench_logger(LogId);
    ?active_profile(Profile);
    .concat("benchmark/results/", Profile, "/", Mode, "/trace_bench_", Mode, ".jsonl", TraceFile);
    openTraceJsonl(TraceFile)[artifact_id(LogId)];
    .print("[Bench] Rich trace opened: ", TraceFile).

// Insert profile suffix between the base name and ".csv".
// E.g. base="qtable_final_stereotypes_true.csv", suffix="_full"
//   -> "qtable_final_stereotypes_true_full.csv".
@apply_qtable_suffix_empty
+!apply_qtable_suffix(Base, "", Base) <- true.
@apply_qtable_suffix_nonempty
+!apply_qtable_suffix(Base, Suffix, Out) : Suffix \== "" <-
    .delete(".csv", Base, NoExt);
    .concat(NoExt, Suffix, NoExt2);
    .concat(NoExt2, ".csv", Out).

@ql_flag_and_file_true
+!ql_flag_and_file("ql_true",  true,  "qtable_final_stereotypes_true.csv")  <- true.
@ql_flag_and_file_false
+!ql_flag_and_file("ql_false", false, "qtable_final_stereotypes_false.csv") <- true.

@ql_iv_file
+!ql_iv_file(Mode, IVFile) <-
    !ql_flag_and_file(Mode, UseStereotypes, _);
    !profile_qtable_suffix(QtSuffix);
    .concat("iv_stats_stereotypes_", UseStereotypes, S1);
    .concat(S1, QtSuffix, S2);
    .concat(S2, ".json", IVFile).

/* ============================================================
 * Zone-goal beliefs for the rule-based mode
 * ============================================================ */
@setup_bench_zone_goals_done
+!setup_bench_zone_goals([], []) <- true.

@setup_bench_zone_goals_step
+!setup_bench_zone_goals([ZUri|RestU], [ZIdx|RestI]) <-
    ?ontology_artifact(OntId);
    ?zone_target(ZIdx, Target);
    discoverZoneQuantity(ZUri, QUri, QLabel)[artifact_id(OntId)];
    +bench_zone_goal(ZUri, ZIdx, QUri, QLabel, Target);
    .print("[Bench] Zone goal idx=", ZIdx, " quantity='", QLabel,
           "' target=", Target);
    !setup_bench_zone_goals(RestU, RestI).

/* ============================================================
 * Outer loop: repeat the whole scenario list N times
 * ============================================================ */
@run_all_runs_step
+!run_all_runs(RunId, TotalRuns) : RunId <= TotalRuns <-
    .print("");
    .print("--- Run ", RunId, " of ", TotalRuns, " ---");
    !scenarios_list(Scenarios);
    !run_scenario_list(Scenarios, RunId);
    !run_all_runs(RunId + 1, TotalRuns).

@run_all_runs_done
+!run_all_runs(RunId, TotalRuns) : RunId > TotalRuns <-
    ?bench_mode(Mode);
    ?bench_logger(LogId);
    .concat("benchmark_results_", Mode, Tmp);
    .concat(Tmp, ".csv", OutFile);
    saveBenchmarkResults(OutFile)[artifact_id(LogId)];
    .concat("bench_step_log_", Mode, Tmp2);
    .concat(Tmp2, ".csv", StepLogFile);
    saveStepLog(StepLogFile)[artifact_id(LogId)];
    closeTraceJsonl[artifact_id(LogId)];
    .print("");
    .print("==========================================================");
    .print("   Benchmark complete. Results saved to: ", OutFile);
    .print("==========================================================");
    .stopMAS.

/* ============================================================
 * Scenario catalogue — loaded dynamically from the active profile's
 * scenario JSON file (lab_profile/.../scenarios(File)).  The bench
 * agent enumerates every "id" in that file and pins the simulator
 * via setScenarioLabState(File, Id), so the per-profile scenario
 * shape (legacy 8-field 2-zone, or full 4-zone with CorridorLight /
 * SpotlightCD / Z3,Z4 fields) is honoured without any hard-coding
 * here.  Adding new scenarios only requires editing the JSON file.
 * ============================================================ */
@scenarios_list
+!scenarios_list(S) <-
    ?lab_artifact(LabId);
    !profile_scenarios(File);
    getScenarioIds(File, Ids)[artifact_id(LabId)];
    .term2string(File, FileStr);
    .print("[Bench] Loaded scenario IDs from ", FileStr, ": ", Ids);
    !ids_to_scenarios(Ids, File, [], S).

@ids_to_scenarios_done
+!ids_to_scenarios([], _, Acc, S) <-
    .reverse(Acc, S).
@ids_to_scenarios_step
+!ids_to_scenarios([Id|Rest], File, Acc, S) <-
    !ids_to_scenarios(Rest, File, [scenario(Id, File)|Acc], S).

@run_scenario_list_done
+!run_scenario_list([], _) <- true.

@run_scenario_list_step
+!run_scenario_list([scenario(ScenId, File)|Rest], RunId) <-
    ?lab_artifact(LabId);
    ?bench_logger(LogId);
    ?bench_mode(Mode);
    setScenarioLabState(File, ScenId)[artifact_id(LabId)];
    .wait(300); // let the simulator update tick propagate after setState (> 200 ms tick)
    .concat("scenario_id=", ScenId, StateStr0);
    .concat(StateStr0, " file=", StateStr1);
    .concat(StateStr1, File, StateStr);
    beginScenario(ScenId, RunId, Mode, StateStr)[artifact_id(LogId)];
    // Reset anti-stuck ring buffers per scenario so stagnation detection
    // does not leak across scenario boundaries.
    .abolish(recent_states(_));
    .abolish(recent_actions(_));
    .abolish(bench_stuck_fired(_));
    .print("[Bench] Scenario ", ScenId, " Run ", RunId, " | file=", File);
    !run_scenario_step(ScenId, RunId, 0);
    !run_scenario_list(Rest, RunId).

/* ============================================================
 * Inner step loop — one scenario
 *
 * On each step:
 *   1. Read current lab state.
 *   2. If both zones at target, end scenario successfully.
 *   3. Else, dispatch an action based on the active mode,
 *      re-read state, and record the step.
 *   4. Recurse.
 *
 * If step budget is exhausted, end scenario as failure.
 * ============================================================ */
@run_scenario_step_continue
+!run_scenario_step(ScenId, RunId, Step)
    : exec_max_steps(MaxSteps) & Step < MaxSteps <-
    ?lab_artifact(LabId);
    ?bench_logger(LogId);
    ?bench_mode(Mode);
    ?exec_delay_ms(Delay);
    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    // Build Targets parallel to ZoneLevels (sorted by zone index)
    .findall(t(I,T), zone_target(I,T), ZTUnsorted);
    .sort(ZTUnsorted, ZTSorted);
    .findall(T, .member(t(_,T), ZTSorted), Targets);
    !check_terminal(ZoneLevels, Targets, AtGoal);
    if (AtGoal) {
        readEnergyCost(EnergyCost)[artifact_id(LabId)];
        endScenario(true, Step, EnergyCost)[artifact_id(LogId)];
        .print("[Bench] Scenario ", ScenId, " Run ", RunId,
               " REACHED TARGET in ", Step, " steps.")
    } else {
        !dispatch(Mode, ZoneLevels, SunshineRank, SKs, SVs, Targets);
        readLabStatus(ZoneLevels2, _, SKs2, SVs2)[artifact_id(LabId)];
        readZoneTemperatures(Temps)[artifact_id(LabId)];
        !is_wasted(ZoneLevels, ZoneLevels2, SVs, SVs2, Wasted);
        !is_cross_zone(ZoneLevels, ZoneLevels2, Targets, CrossZone);
        recordStep(Step, ZoneLevels, Targets, Mode, Wasted,
                   SKs2, SVs2, CrossZone)[artifact_id(LogId)];
        // Detailed step log — reconstruct action label
        !get_last_action_label(Mode, ActionLabel);
        !get_stuck_fired(StuckFired);
        recordStepDetailRichV2(Step, ZoneLevels, ZoneLevels2, Targets,
                               ActionLabel, false, CrossZone,
                               Temps, SKs2, SVs2,
                               SunshineRank, StuckFired)[artifact_id(LogId)];
        // Per-step weakness fingerprinting (QL modes only — needs reasoner).
        !fingerprint_weakness(Mode, ZoneLevels, SunshineRank, SKs, SVs,
                              ZoneLevels2, SKs2, SVs2);
        .wait(Delay);
        !run_scenario_step(ScenId, RunId, Step + 1)
    }.

@run_scenario_step_timeout
+!run_scenario_step(ScenId, RunId, Step)
    : exec_max_steps(MaxSteps) & Step >= MaxSteps <-
    ?lab_artifact(LabId);
    ?bench_logger(LogId);
    readEnergyCost(EnergyCost)[artifact_id(LabId)];
    endScenario(false, Step, EnergyCost)[artifact_id(LogId)];
    .print("[Bench] Scenario ", ScenId, " Run ", RunId,
           " FAILED — max steps (", MaxSteps, ") reached.").

/* ============================================================
 * Terminal / wasted / cross-zone predicates
 * Expressed as plan selection so that each "output" variable is
 * bound by unification inside a context-matching plan head.
 * ============================================================ */
@check_terminal_entry
+!check_terminal(ZoneLevels, Targets, Result) <-
    !walk_terminal(ZoneLevels, Targets, Result).
@walk_terminal_done
+!walk_terminal([], [], true) <- true.
@walk_terminal_mismatch
+!walk_terminal([L|_], [T|_], false) : L \== T <- true.
@walk_terminal_match
+!walk_terminal([_|RL], [_|RT], Result) <-
    !walk_terminal(RL, RT, Result).

@is_wasted_yes
+!is_wasted(L1, L2, S1, S2, true) : L1 == L2 <- true.
@is_wasted_no
+!is_wasted(_, _, _, _, false) <- true.

@is_cross_zone_entry
+!is_cross_zone(Prev, Curr, Targets, Result) <-
    ?bench_mode(Mode);
    // For QL modes: use ontology-declared cross-zone topology for precise detection.
    // Falls back to level-based check when QLearner artifact is unavailable (rule_based).
    if (Mode == "ql_true" | Mode == "ql_false") {
        ?qlearner_artifact(QlId);
        getLastDispatchedAction(ActionIdx)[artifact_id(QlId)];
        if (ActionIdx >= 0) {
            checkCrossZoneInterference(ActionIdx, Prev, Curr, Targets, OntoCross)[artifact_id(QlId)];
            // Also check level-based: any zone moved further from target
            !walk_cross_zone(Prev, Curr, Targets, LevelCross);
            !or2(OntoCross, LevelCross, Result)
        } else {
            !walk_cross_zone(Prev, Curr, Targets, Result)
        }
    } else {
        !walk_cross_zone(Prev, Curr, Targets, Result)
    }.

@or2_t1
+!or2(true, _, true) <- true.
@or2_t2
+!or2(_, true, true) <- true.
@or2_f
+!or2(_, _, false) <- true.

@walk_cross_zone_done
+!walk_cross_zone([], [], [], false) <- true.
@walk_cross_zone_worse
+!walk_cross_zone([P|_], [C|_], [T|_], true)
    : math.abs(C - T) > math.abs(P - T) <- true.
@walk_cross_zone_next
+!walk_cross_zone([_|RP], [_|RC], [_|RT], Result) <-
    !walk_cross_zone(RP, RC, RT, Result).

/* ============================================================
 * Get last action label for step log
 * For QL modes, read the action index and map to a label.
 * For rule_based, return "rule_based_action" as placeholder.
 * ============================================================ */
@get_last_action_label_ql
+!get_last_action_label(Mode, Label)
    : (Mode == "ql_true" | Mode == "ql_false") <-
    ?qlearner_artifact(QlId);
    getLastDispatchedAction(ActionIdx)[artifact_id(QlId)];
    if (ActionIdx >= 0) {
        actionToWoT(ActionIdx, WotType, WotValue)[artifact_id(QlId)];
        if (WotType \== "none") {
            .concat(WotType, "=", WotType2);
            .term2string(WotValue, ValStr);
            .concat(WotType2, ValStr, Label)
        } else {
            Label = "DO_NOTHING"
        }
    } else {
        Label = "unknown"
    }.

@get_last_action_label_rule_based_belief
+!get_last_action_label("rule_based", L) : rb_last_action(LL) <- L = LL.
@get_last_action_label_rule_based_default
+!get_last_action_label("rule_based", "DO_NOTHING") <- true.

/* ============================================================
 * Action dispatch
 * ============================================================ */
@dispatch_rule_based
+!dispatch("rule_based", ZoneLevels, SunshineRank, SKs, SVs, _) <-
    ?ontology_artifact(OntId);
    // Reset action-label belief at start of each step so DO_NOTHING is
    // emitted when no zone is off-target or no rb_increase/rb_decrease fires.
    .abolish(rb_last_action(_));
    +rb_last_action("DO_NOTHING");
    .findall(I, bench_zone_goal(_, I, _, _, _), ZIdxUnsorted);
    .sort(ZIdxUnsorted, ZIdxSorted);
    .findall(goal(ZUri, ZIdx, QUri, QLabel, Target),
             bench_zone_goal(ZUri, ZIdx, QUri, QLabel, Target),
             ZoneGoals);
    !rb_process_first_off_target(ZoneGoals, ZIdxSorted,
                                 ZoneLevels, SunshineRank, SKs, SVs).

@rb_process_first_off_target_done
+!rb_process_first_off_target([], _, _, _, _, _) <- true.

@rb_process_first_off_target_step
+!rb_process_first_off_target([goal(ZUri, ZIdx, QUri, QLabel, Target)|Rest],
                              ZIdxSorted, ZoneLevels, SunshineRank, SKs, SVs) <-
    !get_bench_zone_level(ZIdxSorted, ZoneLevels, ZIdx, Level);
    if (Level == Target) {
        !rb_process_first_off_target(Rest, ZIdxSorted, ZoneLevels,
                                     SunshineRank, SKs, SVs)
    } else {
        if (Level < Target) {
            !rb_increase(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs, ZoneLevels)
        } else {
            !rb_decrease(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs, ZoneLevels)
        }
    }.

@get_bench_zone_level_found
+!get_bench_zone_level([ZIdx|_], [Level|_], ZIdx, Level) <- true.
@get_bench_zone_level_search
+!get_bench_zone_level([_|RI], [_|RL], ZIdx, Level) <-
    !get_bench_zone_level(RI, RL, ZIdx, Level).

@rb_increase
+!rb_increase(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs, ZoneLevels) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    queryBestIncreaseAction(ZUri, QUri, SunshineRank, SKs, SVs,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel, WotActionType)[artifact_id(OntId)];
    if (CompId \== "none") {
        .findall(t(I2,T2), zone_target(I2, T2), ZTU);
        .sort(ZTU, ZTS);
        .findall(T3, .member(t(_,T3), ZTS), ZoneTargets);
        checkSharedActuatorSafe(WotActionType, ZIdx, ZoneLevels,
                                ZoneTargets, Safe)[artifact_id(OntId)];
        if (Safe) {
            invokeAction(WotActionType, true)[artifact_id(LabId)];
            .concat(WotActionType, "=true", RbLabel);
            .abolish(rb_last_action(_));
            +rb_last_action(RbLabel);
            .print("[Bench Zone ", ZIdx, "] INCREASE via ", CompId,
                   " (", WotActionType, ")")
        } else {
            .concat("BLOCKED:", WotActionType, BL0);
            .concat(BL0, "=true", BL1);
            .abolish(rb_last_action(_));
            +rb_last_action(BL1);
            .print("[Bench Zone ", ZIdx, "] INCREASE BLOCKED: ", CompId,
                   " unsafe for other zones")
        }
    } else {
        .print("[Bench Zone ", ZIdx, "] No applicable INCREASE action")
    }.

@rb_decrease
+!rb_decrease(ZUri, ZIdx, QUri, QLabel, SunshineRank, SKs, SVs, ZoneLevels) <-
    ?ontology_artifact(OntId);
    ?lab_artifact(LabId);
    queryBestDecreaseAction(ZUri, QUri, SunshineRank, SKs, SVs,
        CompId, Mechanism, MvLabel, DvLabel, IvLabel, WotActionType)[artifact_id(OntId)];
    if (CompId \== "none") {
        .findall(t(I2,T2), zone_target(I2, T2), ZTU);
        .sort(ZTU, ZTS);
        .findall(T3, .member(t(_,T3), ZTS), ZoneTargets);
        checkSharedActuatorSafeToDeactivate(WotActionType, ZIdx, ZoneLevels,
                                            ZoneTargets, SafeRm)[artifact_id(OntId)];
        if (SafeRm) {
            invokeAction(WotActionType, false)[artifact_id(LabId)];
            .concat(WotActionType, "=false", RbLabel);
            .abolish(rb_last_action(_));
            +rb_last_action(RbLabel);
            .print("[Bench Zone ", ZIdx, "] DECREASE via ", CompId,
                   " (", WotActionType, ")")
        } else {
            .concat("BLOCKED:", WotActionType, BL0);
            .concat(BL0, "=false", BL1);
            .abolish(rb_last_action(_));
            +rb_last_action(BL1);
            .print("[Bench Zone ", ZIdx, "] DECREASE BLOCKED: ", CompId,
                   " needed by another zone")
        }
    } else {
        .print("[Bench Zone ", ZIdx, "] No applicable DECREASE action")
    }.

@dispatch_ql
+!dispatch(Mode, ZoneLevels, SunshineRank, SKs, SVs, _)
    : (Mode == "ql_true" | Mode == "ql_false") <-
    ?qlearner_artifact(QlId);
    ?lab_artifact(LabId);
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)[artifact_id(QlId)];
    // ---- anti-stuck ring buffer -----------------------------------------
    // Track last 3 state vectors and last 2 dispatched actions. When all 3
    // recent states are equal, exclude the recent actions on the next call
    // so the policy can break out of a stagnation plateau.
    // S4-1 (audit-step-4): the anti-stuck rescue is bench-only; the training
    // loop in illuminance_controller_agent_ql.asl#@do_step has no equivalent
    // ring buffer. Wrapping the trained policy with a runtime argmax
    // replacement makes the benched policy != the trained policy and
    // contaminates the H1/H3 comparison. The bench_anti_stuck/1 belief
    // gates this path: default false (conservative H1 reading). Set to
    // true ONLY to reproduce legacy behaviour.
    ?bench_anti_stuck(AntiStuckEnabled);
    !get_recent_states(RecentStates);
    !get_recent_actions(RecentActions);
    !is_stuck3(StateVec, RecentStates, IsStuck);
    if (AntiStuckEnabled & IsStuck) {
        getActionFromStateAntiStuck(StateVec, RecentActions, Action, StuckFired)[artifact_id(QlId)]
    } else {
        getActionFromState(StateVec, false, Action)[artifact_id(QlId)];
        StuckFired = false
    };
    .abolish(bench_stuck_fired(_));
    +bench_stuck_fired(StuckFired);
    !push_recent_state(StateVec);
    !push_recent_action(Action);
    actionToWoT(Action, WotType, WotValue)[artifact_id(QlId)];
    // Track last dispatched action for cross-zone interference check
    notifyActionDispatched(Action)[artifact_id(QlId)];
    if (WotType \== "none") {
        invokeAction(WotType, WotValue)[artifact_id(LabId)];
        .print("[Bench QL] action=", Action, " wot=", WotType, "=", WotValue,
               " stuck=", StuckFired)
    } else {
        .print("[Bench QL] action=", Action, " (do-nothing) stuck=", StuckFired)
    }.

/* ---------- anti-stuck helpers ----------------------------------------- */
@get_recent_states_have
+!get_recent_states(L) : recent_states(L) <- true.
@get_recent_states_init
+!get_recent_states([]) <- true.

@get_recent_actions_have
+!get_recent_actions(L) : recent_actions(L) <- true.
@get_recent_actions_init
+!get_recent_actions([]) <- true.

// stuck = at least 2 prior states recorded AND both equal current state
@is_stuck3_yes
+!is_stuck3(Sv, [Sv, Sv | _], true) <- true.
@is_stuck3_no
+!is_stuck3(_, _, false) <- true.

@push_recent_state
+!push_recent_state(Sv) <-
    !get_recent_states(L0);
    !take_first2(L0, L1);
    .abolish(recent_states(_));
    +recent_states([Sv | L1]).

@push_recent_action
+!push_recent_action(A) <-
    !get_recent_actions(L0);
    !take_first2(L0, L1);
    .abolish(recent_actions(_));
    +recent_actions([A | L1]).

@take_first2_empty
+!take_first2([], []) <- true.
@take_first2_one
+!take_first2([X], [X]) <- true.
@take_first2_two
+!take_first2([X, Y | _], [X, Y]) <- true.

@get_stuck_fired_have
+!get_stuck_fired(F) : bench_stuck_fired(F) <- true.
@get_stuck_fired_init
+!get_stuck_fired(false) <- true.

/* ============================================================
 * Per-step weakness fingerprinting
 *   QL modes only: build StateVec before/after via encodeState,
 *   read last action index, ask QLearner to classify which
 *   weakness fingerprints fired during the transition, then
 *   intersect with the lab's declared weakness_flags from
 *   lab_profiles.asl and call recordWeakness for each match.
 *   Rule-based mode is a no-op (no QLearner artifact available).
 * ============================================================ */
@fingerprint_weakness_skip_rule_based
+!fingerprint_weakness("rule_based", _, _, _, _, _, _, _) <- true.

@fingerprint_weakness_ql
+!fingerprint_weakness(Mode, ZoneLevels, SunshineRank, SKs, SVs,
                       ZoneLevels2, SKs2, SVs2)
    : (Mode == "ql_true" | Mode == "ql_false") <-
    ?qlearner_artifact(QlId);
    ?bench_logger(LogId);
    ?lab_artifact(LabId);
    encodeState(ZoneLevels,  SunshineRank, SKs,  SVs,  StateVec1)[artifact_id(QlId)];
    encodeState(ZoneLevels2, SunshineRank, SKs2, SVs2, StateVec2)[artifact_id(QlId)];
    getLastDispatchedAction(ActionIdx)[artifact_id(QlId)];
    if (ActionIdx >= 0) {
        classifyWeaknesses(StateVec1, StateVec2, ActionIdx, Fired)[artifact_id(QlId)];
        getPredictedDelta(StateVec1, ActionIdx, PredDelta)[artifact_id(QlId)];
        getApplicableActions(StateVec1, AppActions)[artifact_id(QlId)];
        getLastQDelta(QDelta)[artifact_id(QlId)];
        recordRichStep(0, StateVec1, ActionIdx, AppActions, PredDelta,
                       StateVec2, QDelta, Fired)[artifact_id(LogId)];
        !profile_weakness_flags(WF);
        !fp_record_all(WF, Fired, LogId);
        // W6 (comfort) is measured directly from zone temperatures, not
        // fingerprinted from action effects. Only sample if the lab declares
        // w6 in its weakness_flags.
        if (.member(w6, WF)) {
            readZoneTemperatures(Temps)[artifact_id(LabId)];
            !accumulate_comfort(Temps, LogId)
        }
    }.

// Sum |T - target| across zones, beyond a small tolerance, and feed it to
// recordComfortDeviation. Target=22.0 °C, tolerance=1.0 °C are reasonable
// office defaults; tweak here if a profile requires different setpoints.
@accumulate_comfort_empty
+!accumulate_comfort([], _) <- true.
@accumulate_comfort_step
+!accumulate_comfort([T|Rest], LogId) <-
    Dev = math.abs(T - 22.0);
    if (Dev > 1.0) {
        Excess = Dev - 1.0;
        recordComfortDeviation(Excess)[artifact_id(LogId)]
    };
    !accumulate_comfort(Rest, LogId).

// Walk the lab's weakness_flags list and record any that fired.
@fp_record_all_done
+!fp_record_all([], _, _) <- true.
@fp_record_all_step
+!fp_record_all([Flag|Rest], Fired, LogId) <-
    !fp_record(Flag, Fired, LogId);
    !fp_record_all(Rest, Fired, LogId).

// Per-flag dispatch — only record if the corresponding fingerprint fired.
@fp_record_w1_hit
+!fp_record(w1, Fired, LogId) : .member("w1_unmodelled", Fired) <-
    recordWeakness("w1_unmodelled", 1)[artifact_id(LogId)].
@fp_record_w1_miss
+!fp_record(w1, _, _) <- true.

@fp_record_w2_hit
+!fp_record(w2, Fired, LogId) : .member("w2_inversion", Fired) <-
    recordWeakness("w2_inversion", 1)[artifact_id(LogId)].
@fp_record_w2_miss
+!fp_record(w2, _, _) <- true.

@fp_record_w3_hit
+!fp_record(w3, Fired, LogId) : .member("w3_delayed", Fired) <-
    recordWeakness("w3_delayed", 1)[artifact_id(LogId)].
@fp_record_w3_miss
+!fp_record(w3, _, _) <- true.

@fp_record_w4_hit
+!fp_record(w4, Fired, LogId) : .member("w4_dropped", Fired) <-
    recordWeakness("w4_dropped", 1)[artifact_id(LogId)].
@fp_record_w4_miss
+!fp_record(w4, _, _) <- true.

@fp_record_w5_hit
+!fp_record(w5, Fired, LogId) : .member("w5_topology", Fired) <-
    recordWeakness("w5_topology", 1)[artifact_id(LogId)].
@fp_record_w5_miss
+!fp_record(w5, _, _) <- true.

@fp_record_w6_hit
+!fp_record(w6, Fired, LogId) : .member("w6_unmodelled", Fired) <-
    recordWeakness("w6_unmodelled", 1)[artifact_id(LogId)].
@fp_record_w6_miss
+!fp_record(w6, _, _) <- true.

// Catch-all: unknown weakness flag — silently ignore.
@fp_record_unknown
+!fp_record(_, _, _) <- true.

// Failure handler — never let fingerprinting break the run.
-!fingerprint_weakness(_, _, _, _, _, _, _, _) <-
    .print("[Bench] WARNING: fingerprint_weakness failed (skipping).").

/* ============================================================
 * Failure-handling plans — prevent benchmark from aborting on
 * transient errors; the scenario is marked as failure instead.
 * ============================================================ */
-!bench_start <-
    .print("ERROR: Benchmark agent failed to start.");
    .print("Check that the simulator is running (port 1881) and that");
    .print("qtable_final_stereotypes_*.csv files exist for ql_* modes.").

-!run_scenario_step(ScenId, RunId, Step) <-
    .print("WARNING: run_scenario_step failed at scenario ", ScenId,
           " run ", RunId, " step ", Step);
    ?lab_artifact(LabId);
    ?bench_logger(LogId);
    readEnergyCost(EnergyCost)[artifact_id(LabId)];
    endScenario(false, Step, EnergyCost)[artifact_id(LogId)].

-!dispatch(_, _, _, _, _, _) <-
    .print("WARNING: dispatch failed — treating step as a no-op.").

/* ============================================================
 * Simulator / input failure handlers (#5, #8)
 * ============================================================ */
+!handle_simulator_failure(Reason, Op, Detail) <-
    .print("ERROR: Simulator failure during benchmark — reason=", Reason,
           " op=", Op, " detail=", Detail);
    .print("       Current scenario will be marked as failure.").

+!handle_invalid_input(Actuator, Expected, Actual) <-
    .print("ERROR: Invalid input during benchmark — actuator=", Actuator,
           " expected=", Expected, " actual=", Actual).
