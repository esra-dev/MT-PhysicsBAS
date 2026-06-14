// Illuminance Controller Agent — Phase 2 Fault-Adaptation Implementation
// MT-Esra Project: Fault Detection, Blacklisting & Warm-Restart Re-learning
//
// This agent loads a Phase-1 CLEAN-trained Q-table and is placed into a FAULTY
// variant of the same lab (same ontology = nominal physics; the simulator
// injects a hardware fault — a DEAD or an INVERTED component). It then:
//
//   1. MONITOR  — runs episodes in the faulty lab, and on every transition
//                 performs a strict Expected-vs-Actual check (observeForFaults):
//                 the Knowledge-Graph prediction for the action is compared to
//                 the observed Δ. Repeated contradictions accumulate per-
//                 component evidence (dead = no zone response; inverted =
//                 opposite response).
//   2. DETECT   — when a component crosses its detection threshold it is flagged
//                 DEFECTIVE; the agent ALERTS the user (MAS console + belief +
//                 recovery CSV).
//   3. BLACKLIST— blacklistComponent removes BOTH the ON and OFF actions of the
//                 defective component from the action space entirely.
//   4. RE-LEARN — warmRestart re-primes learning over the surviving actions and
//                 the agent continues training until it re-converges. Detection
//                 stays active so additional faults (several-dead / several-
//                 faulty) are caught and blacklisted iteratively.
//
// The headline Phase-2 metric is RecoveryEpisodes = ReconvergeEpisode −
// DetectEpisode, written by saveRecoveryLog. The thesis claim is that a
// KG-primed learner (use_stereotypes=true) re-aligns faster than a tabula-rasa
// one (use_stereotypes=false) after a component fails.
//
// Run:  ./gradlew taskAdapt -Pprofile=lab2_f1dead -Pmode=ql_true
//       (with the matching faulty Node-RED simulator flow running)

/* ============================================================
 * Initial Beliefs
 * ============================================================ */

// Default stereotype mode; overridden at startup by -Pmode (ql_true/ql_false).
use_stereotypes(true).

// Lab Profile registry (shared with the QL / bench agents). The active profile
// is a FAULTY profile (e.g. lab2_f1dead); adapt_source/2 maps it to the clean
// parent's qtable_suffix so the right Phase-1 Q-table is warm-loaded.
{ include("lab_profiles.asl") }

// Adaptation parameters (num_episodes is overridden per-profile at startup).
num_episodes(2000).
max_steps_per_episode(20).
action_delay_ms(65).      // delay between actions (ms) — must exceed 200 ms simulator tick

/* ============================================================
 * Initial Goals
 * ============================================================ */

!apply_profile_then_start_adapt.

/* ============================================================
 * Profile bridge — copy active-profile fields into the legacy
 * belief names the plans below query, then start adaptation.
 * ============================================================ */
@apply_profile_then_start_adapt
+!apply_profile_then_start_adapt <-
    !apply_runtime_overrides_adapt;
    !profile_print;
    !profile_td(TdUrl);                     +lab_td(TdUrl);
    !profile_light_bounds(LightBounds);     +light_rank_bounds(LightBounds);
    !profile_sunshine_bounds(SunBounds);    +sunshine_rank_bounds(SunBounds);
    !profile_sunshine_prob(SunProb);        +sunshine_satisfaction_prob(SunProb);
    !profile_zone_targets(ZoneTargetList);
    !derive_zone_goal(ZoneTargetList, []);
    !maybe_set_train_scenarios_file;
    !start_adapt.

/* ============================================================
 * Runtime parameter overrides (#7):
 *   -Dactive.profile=…  replaces active_profile/1
 *   -Dadapt.mode=ql_true|ql_false  sets use_stereotypes
 * ============================================================ */
@apply_runtime_overrides_adapt
+!apply_runtime_overrides_adapt <-
    tools.jia.system_prop("active.profile", "", OverrideProfile);
    if (OverrideProfile \== "") {
        ?active_profile(OldP);
        -active_profile(OldP);
        +active_profile(OverrideProfile);
        .print("[RuntimeOverride] active_profile: ", OldP, " -> ", OverrideProfile)
    };
    tools.jia.system_prop("adapt.mode", "", ModeOverride);
    if (ModeOverride \== "") {
        ?use_stereotypes(OldS);
        -use_stereotypes(OldS);
        if (ModeOverride == "ql_false") {
            +use_stereotypes(false);
            .print("[RuntimeOverride] use_stereotypes -> false (ql_false)")
        } else {
            +use_stereotypes(true);
            .print("[RuntimeOverride] use_stereotypes -> true (ql_true)")
        }
    }.
@apply_runtime_overrides_adapt_fail
-!apply_runtime_overrides_adapt <-
    .print("[RuntimeOverride] WARNING: tools.jia.system_prop failed; using pre-patched beliefs.").

// Build zone_goal/1 belief as a list of target ranks (sorted by zone idx).
@derive_zone_goal_done
+!derive_zone_goal([], Acc) <-
    .reverse(Acc, Goal);
    +zone_goal(Goal).
@derive_zone_goal_step
+!derive_zone_goal([target(_, T)|R], Acc) <-
    !derive_zone_goal(R, [T|Acc]).

// Enable fixed-scenario cycling when the profile carries a train_scenarios path.
@maybe_set_train_scenarios_file_full
+!maybe_set_train_scenarios_file
    : active_profile(P)
    & lab_profile(P, _, _, _, train_scenarios(File), _, _, _, _, _, _, qtable_suffix(QS), _)
    & QS \== "" & File \== "" <-
    +train_scenarios_file(File);
    .print("[Profile] train_scenarios_file enabled: ", File).
@maybe_set_train_scenarios_file_none
+!maybe_set_train_scenarios_file <- true.

// adapt_source/2 accessor — which clean qtable_suffix to warm-load from.
@profile_adapt_source_ok
+!profile_adapt_source(CleanSuffix)
    : active_profile(P) & adapt_source(P, CleanSuffix) <- true.
@profile_adapt_source_missing
+!profile_adapt_source(_) <-
    .print("[Adapt] FATAL: no adapt_source/2 mapping for active profile — cannot warm-load a clean Q-table.");
    .fail.

/* ============================================================
 * @start_adapt — create artifacts, warm-load clean Q-table,
 * then begin the adaptation loop.
 * ============================================================ */
@start_adapt
+!start_adapt : active_profile(ActiveP)
        & use_stereotypes(UseStereotypes)
        & lab_td(TdUrl)
        & zone_goal(Goal)
        & sunshine_satisfaction_prob(SunProb)
        & light_rank_bounds(LightBounds)
        & sunshine_rank_bounds(SunshineBounds) <-

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT - PHASE 2 ADAPTATION");
    .print("   Profile:  ", ActiveP, "  (faulty)");
    .print("   Stereo:   ", UseStereotypes);
    .print("   Goal:     ", Goal);
    .print("==========================================================");

    // Create the LabEnvironment artifact (faulty simulator endpoint).
    makeArtifact("lab", "tools.LabEnvironment", [TdUrl], LabId);
    +lab_artifact(LabId);
    .print("[probe] Checking simulator HTTP reachability ...");
    readLabStatus(_PZL, _PSR, _PSK, _PSV)[artifact_id(LabId)];
    .print("[probe] Simulator reachable — proceeding.");
    if (train_scenarios_file(ScenariosFile)) {
        getScenarioIds(ScenariosFile, ScIds)[artifact_id(LabId)];
        .length(ScIds, TCount);
        +train_scenarios_count(TCount);
        .print("[Profile] train_scenarios_count=", TCount)
    };
    configureDiscretization(LightBounds, SunshineBounds)[artifact_id(LabId)];
    .print("[Config] Discretisation bounds (static): light=", LightBounds,
           " sunshine=", SunshineBounds);

    // Create + configure the QLearner with the SAME ontology as the clean
    // parent so the state/action space matches the saved Q-table exactly.
    makeArtifact("qlearner", "tools.QLearner", [], QlId);
    +qlearner_artifact(QlId);
    !profile_ont(OntPaths);
    configureQLearner(Goal, UseStereotypes, OntPaths, SunProb)[artifact_id(QlId)];
    .print("QLearner artifact created and initialised.");

    // Per-profile re-learn budget + epsilon decay. The budget is overridable at
    // launch via -Dadapt.episodes=<N> (e.g. a fast smoke run) without mutating
    // lab_profiles.asl; default = the profile's training_params value.
    !profile_training_params(NumEps, EpDecay);
    tools.jia.system_prop_num("adapt.episodes", NumEps, Budget);
    -+num_episodes(Budget);
    setEpsilonDecay(EpDecay)[artifact_id(QlId)];
    setTrainingBudgetEpisodes(Budget)[artifact_id(QlId)];
    .print("[Profile] Re-learn params: num_episodes=", Budget,
           " (profile default ", NumEps, ") epsilonDecay=", EpDecay);

    // Warm-load the Phase-1 clean-trained Q-table (per-zone files + sidecars).
    !profile_adapt_source(CleanSuffix);
    !sx_filename("qtable_final_stereotypes_", UseStereotypes, CleanSuffix, ".csv", CleanFile);
    loadQTable(CleanFile)[artifact_id(QlId)];
    .print("[Adapt] Warm-loaded clean Q-table from ", CleanFile);

    // Create the StereotypeLearner (parity with training; feeds dynamics stats).
    makeArtifact("learner", "tools.StereotypeLearner", [], LId);
    +learner_artifact(LId);
    getNumActions(NumActions)[artifact_id(QlId)];
    getStateVecLen(StateVecLen)[artifact_id(QlId)];
    getActionMetadataForLearner(ActUris, ActVals, ActLabels)[artifact_id(QlId)];
    initLearner(NumActions, StateVecLen, ActUris, ActVals, ActLabels)[artifact_id(LId)];
    getNumApplicableActions(App0)[artifact_id(QlId)];
    .print("[Adapt] Ready. Action space size (pre-fault) = ", App0,
           " of ", NumActions, " total.");
    !adapt(0).

// Compose <Prefix><Bool><Suffix><Ext> into a single filename.
@sx_filename
+!sx_filename(Prefix, Bool, Suffix, Ext, Out) <-
    .concat(Prefix, Bool,  S1);
    .concat(S1,    Suffix, S2);
    .concat(S2,    Ext,    Out).

/* ============================================================
 * Adaptation loop — episodes
 * ============================================================ */
@adapt
+!adapt(N) : num_episodes(MaxEpisodes) & N < MaxEpisodes <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);

    // Set start state: cycle fixed scenarios if configured, else random.
    if (train_scenarios_file(ScenariosFile)) {
        ?train_scenarios_count(TCount);
        ScenarioId = (N mod TCount) + 1;
        setScenarioLabState(ScenariosFile, ScenarioId)[artifact_id(LabId)];
        readLabStatus(ZLStart, SRStart, SKStart, SVStart)[artifact_id(LabId)];
        encodeState(ZLStart, SRStart, SKStart, SVStart, StartStateVec)[artifact_id(QlId)];
        beginEpisodeFromState(StartStateVec)[artifact_id(QlId)]
    } else {
        setRandomLabState[artifact_id(LabId)];
        beginEpisode[artifact_id(QlId)]
    };
    .wait(250); // let the sim settle after state change (> 200 ms tick)

    !run_episode_adapt(N, 0);

    readLabStatus(ZLEnd, SREnd, SKEnd, SVEnd)[artifact_id(LabId)];
    encodeState(ZLEnd, SREnd, SKEnd, SVEnd, FinalState)[artifact_id(QlId)];
    isTerminal(FinalState, GoalReached)[artifact_id(QlId)];
    endEpisode(N, GoalReached)[artifact_id(QlId)];
    decayEpsilon[artifact_id(QlId)];

    Pct = ((N + 1) * 100) / MaxEpisodes;
    if (MaxEpisodes <= 100 | ((N + 1) mod 10) == 0) {
        .print("[Adapt] ep ", N + 1, "/", MaxEpisodes, " (", Pct, "%) goal=", GoalReached)
    };

    // Re-convergence is only meaningful AFTER a fault has been detected and a
    // component blacklisted (the warm restart resets the recovery detector).
    // Phase 2.1: recovery = the greedy policy over the SURVIVING action set has
    // been stable for `fault.recover.window` consecutive episodes. This argmax
    // test settles where the old 1e-3 Bellman-stability test could not (residual
    // ε-boost noise + only-stochastically-reachable, sun-gated goals).
    if (detected(_)) {
        updateRecoveryDetector[artifact_id(QlId)];
        hasRecovered(Recovered)[artifact_id(QlId)];
        if (Recovered & not reconverged(_)) {
            +reconverged(N);
            .print("[Adapt] RE-CONVERGED (greedy policy stable) after fault at episode ", N + 1, " — finishing.");
            !adapt(MaxEpisodes)   // jump to @adapt_done
        } else {
            !adapt(N + 1)
        }
    } else {
        !adapt(N + 1)
    }.

@adapt_done
+!adapt(N) : num_episodes(MaxEpisodes) & N >= MaxEpisodes <-
    .print("");
    .print("==========================================================");
    .print("   Adaptation complete after ", N, " episodes.");
    .print("==========================================================");
    !adapt_finish.

/* ============================================================
 * Episode execution
 * ============================================================ */
@run_episode_adapt
+!run_episode_adapt(EpN, Step) <-
    ?qlearner_artifact(QlId);
    ?lab_artifact(LabId);
    ?max_steps_per_episode(MaxSteps);

    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)[artifact_id(QlId)];
    isTerminal(StateVec, Terminal)[artifact_id(QlId)];

    if (not Terminal & Step < MaxSteps) {
        !do_step_adapt(EpN, Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs)
    }.

/* ============================================================
 * Single step — choose, act, observe, learn, and run the strict
 * Expected-vs-Actual fault check.
 * ============================================================ */
@do_step_adapt
+!do_step_adapt(EpN, Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs) <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);
    ?action_delay_ms(Delay);
    ?max_steps_per_episode(MaxSteps);

    // ε-greedy action over the CURRENT (possibly reduced) action space.
    getActionFromState(StateVec, true, Action)[artifact_id(QlId)];
    actionToWoT(Action, WotType, WotValue)[artifact_id(QlId)];
    if (WotType \== "none") {
        invokeAction(WotType, WotValue)[artifact_id(LabId)]
    };
    .wait(Delay);

    // Observe next state.
    readLabStatus(ZoneLevels2, SunshineRank2, SKs2, SVs2)[artifact_id(LabId)];
    encodeState(ZoneLevels2, SunshineRank2, SKs2, SVs2, NextState)[artifact_id(QlId)];

    // Learn (Bellman update + dynamics stats).
    calculateQ(StateVec, Action, NextState)[artifact_id(QlId)];
    ?learner_artifact(LId);
    observe(StateVec, Action, NextState)[artifact_id(LId)];

    // STRICT Expected-vs-Actual check: does the KG prediction for this action
    // match what actually happened? Accumulates per-component fault evidence.
    observeForFaults(StateVec, Action, NextState, NewlyDefective)[artifact_id(QlId)];
    if (NewlyDefective \== "") {
        !on_defect(NewlyDefective, EpN)
    };

    isTerminal(NextState, Terminal)[artifact_id(QlId)];
    if (Terminal) {
        notifyGoalReached(EpN)[artifact_id(QlId)]
    };
    if (not Terminal & Step + 1 < MaxSteps) {
        !run_episode_adapt(EpN, Step + 1)
    }.

/* ============================================================
 * Fault response — ALERT, BLACKLIST, WARM-RESTART (re-learn).
 * Guarded by `not defective(Comp)` so each component is handled once.
 * ============================================================ */
@on_defect_new
+!on_defect(Comp, EpN) : not defective(Comp) <-
    ?qlearner_artifact(QlId);
    +defective(Comp);
    .print("==========================================================");
    .print("   [FAULT] DEFECTIVE component detected: ", Comp);
    .print("   Detected at episode ", EpN + 1, ". Blacklisting + re-learning.");
    .print("==========================================================");
    // Record the FIRST detection episode + the PRIMARY defect label. Recovery
    // is measured from this point, so the recovery log must report THIS
    // component (not a later-detected one) to keep DefectComponent consistent
    // with DetectEpisode.
    if (not detected(_)) {
        +detected(EpN);
        +primary_defect(Comp)
    } else {
        // A second DISTINCT defective component (multi-fault lab). Log the
        // episode so iterative-isolation latency is quantifiable; recovery is
        // still measured from the PRIMARY detection to keep the metric aligned.
        if (not secondary_detect(_)) {
            +secondary_detect(EpN);
            .print("[Adapt] SECONDARY defect detected at episode ", EpN + 1, ": ", Comp)
        }
    };
    // Remove BOTH ON and OFF actions of the defective component.
    blacklistComponent(Comp, NRemoved)[artifact_id(QlId)];
    getNumApplicableActions(AppNow)[artifact_id(QlId)];
    .print("[Adapt] Blacklisted ", NRemoved, " action(s); action space now = ", AppNow);
    // Re-prime learning over the surviving actions (master plan §3.1).
    warmRestart[artifact_id(QlId)];
    .print("[Adapt] Warm restart complete — re-learning over surviving components.").
@on_defect_dup
+!on_defect(_, _) <- true.   // component already known — ignore.

/* ============================================================
 * Finish — save adapted artifacts + the recovery metric, stop MAS.
 * ============================================================ */
@adapt_finish
+!adapt_finish <-
    ?qlearner_artifact(QlId);
    ?use_stereotypes(UseStereotypes);
    !profile_qtable_suffix(QtSuffix);
    // Adapted Q-table + metrics.
    !sx_filename("qtable_adapted_stereotypes_", UseStereotypes, QtSuffix, ".csv", AdaptedFile);
    saveQTable(AdaptedFile)[artifact_id(QlId)];
    .print("[Adapt] Adapted Q-table saved to ", AdaptedFile);
    !sx_filename("metrics_adapted_stereotypes_", UseStereotypes, QtSuffix, ".csv", MetricsFile);
    saveMetrics(MetricsFile)[artifact_id(QlId)];
    .print("[Adapt] Adaptation metrics saved to ", MetricsFile);
    // Recovery metric (DetectEpisode → ReconvergeEpisode).
    !get_detect_episode(DetectEp);
    !get_reconverge_episode(ReconvergeEp);
    !get_secondary_detect_episode(SecondaryEp);
    !get_defect_label(DefectLabel);
    !sx_filename("recovery_stereotypes_", UseStereotypes, QtSuffix, ".csv", RecoveryFile);
    saveRecoveryLog(RecoveryFile, DetectEp, ReconvergeEp, SecondaryEp, DefectLabel)[artifact_id(QlId)];
    .print("[Adapt] Recovery metric saved to ", RecoveryFile,
           " (detect=", DetectEp, " reconverge=", ReconvergeEp, " secondary=", SecondaryEp, ")");
    if (not detected(_)) {
        .print("[Adapt] NOTE: no fault was detected within the budget.")
    };
    if (detected(_) & not reconverged(_)) {
        .print("[Adapt] NOTE: fault detected but did NOT re-converge within the budget.")
    };
    .print("[Adapt] All done — stopping MAS.");
    .stopMAS.

// Recovery-metric getters with safe defaults (−1 / "none").
@get_detect_episode_hit
+!get_detect_episode(E) : detected(E) <- true.
@get_detect_episode_miss
+!get_detect_episode(-1) <- true.
@get_reconverge_episode_hit
+!get_reconverge_episode(E) : reconverged(E) <- true.
@get_reconverge_episode_miss
+!get_reconverge_episode(-1) <- true.
@get_secondary_detect_episode_hit
+!get_secondary_detect_episode(E) : secondary_detect(E) <- true.
@get_secondary_detect_episode_miss
+!get_secondary_detect_episode(-1) <- true.
@get_defect_label_hit
+!get_defect_label(L) : primary_defect(L) <- true.
@get_defect_label_miss
+!get_defect_label("none") <- true.

/* ============================================================
 * Failure handling
 * ============================================================ */
-!start_adapt[error(Err), error_msg(Msg)] <-
    .print("ERROR -!start_adapt: ", Err, " - ", Msg).
-!start_adapt <-
    .print("ERROR: Failed to start adaptation. Check that the FAULTY simulator is");
    .print("       running and the clean Phase-1 Q-table exists on disk.").

-!adapt(N)[error(Err), error_msg(Msg)] <-
    .print("[adapt-fail] -!adapt(", N, "): ", Err, " - ", Msg, " — retrying in 1s");
    .wait(1000);
    !retry_adapt(N, 1).
-!adapt(N) <-
    .print("[adapt-fail] WARNING: Adaptation step failed at N=", N, " — retrying in 1s");
    .wait(1000);
    !retry_adapt(N, 1).
@retry_adapt_ok
+!retry_adapt(N, Attempt) : Attempt <= 3 <-
    .print("[adapt-fail] retry attempt ", Attempt, "/3 at N=", N);
    !adapt(N).
@retry_adapt_giveup
+!retry_adapt(N, Attempt) <-
    .print("[adapt-fail] giving up after ", Attempt - 1, " retries at N=", N, " — finishing");
    !adapt_finish.
-!retry_adapt(N, Attempt)[error(Err), error_msg(Msg)] <-
    .print("[adapt-fail] retry(", N, ",", Attempt, ") failed: ", Err, " - ", Msg, " — next attempt in 1s");
    .wait(1000);
    NextAttempt = Attempt + 1;
    !retry_adapt(N, NextAttempt).

-!run_episode_adapt(EpN, Step)[error(Err), error_msg(Msg)] <-
    .print("WARNING -!run_episode_adapt(", EpN, ",", Step, "): ", Err, " - ", Msg).
-!run_episode_adapt(_, _) <-
    .print("WARNING: adaptation episode step failed.").
-!do_step_adapt(EpN, Step, _, _, _, _, _)[error(Err), error_msg(Msg)] <-
    .print("WARNING -!do_step_adapt(ep=", EpN, " step=", Step, "): ", Err, " - ", Msg).
-!do_step_adapt(_, _, _, _, _, _, _) <-
    .print("WARNING: do_step_adapt failed - skipping step.").
-!on_defect(Comp, _) <-
    .print("WARNING: fault-response failed for component ", Comp, ".").
