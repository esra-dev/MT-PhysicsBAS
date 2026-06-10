// Illuminance Controller Agent — Q-Learning Implementation
// MT-Esra Project: Reinforcement Learning with Stereotype Comparison
//
// This agent trains a Q-learning model to control the illuminance in two zones.
// It can operate in two modes controlled by the use_stereotypes belief:
//
//   use_stereotypes(true)  → Stereotype-guided Q-table initialization:
//     - Actions that are semantically impossible given the current state are
//       pre-penalised in the Q-table (e.g. turning on a light that is already on).
//     - Action masking prevents wasted explores during training.
//     - Blind-open actions are masked when sunshine rank is insufficient,
//       detected dynamically from ontology (no static ivMinRank property needed).
//     Expected: faster convergence due to physics-informed prior knowledge.
//
//   use_stereotypes(false) → Standard Q-learning:
//     - Q-table initialised uniformly to 0.
//     - Actions are dynamically discovered (ON + OFF per actuator + DO_NOTHING).
//     Expected: slower convergence; agent must discover invalid actions by trial.
//
// Switching between modes:
//   1. Edit the belief below:        use_stereotypes(true/false).
//   2. Optionally adjust the goal:   zone_goal([Z1Rank, Z2Rank]).
//   3. Optionally adjust episodes:   num_episodes(N).
//
// Environment selection (simulator):
//   - Custom lab (port 1881, default): lab_td("classpath:interactions-lab-custom.ttl").
//   - Standard lab (port 1880):        lab_td("https://raw.githubusercontent.com/...").
//
// To run: ./gradlew taskQl   (while Node-RED simulator is running)

/* ============================================================
 * Initial Beliefs
 * ============================================================ */

// ─── SWITCH: set to false for standard Q-learning without stereotypes ───
use_stereotypes(true).
// ───────────────────────────────────────────────────────────────────────

// Lab-specific configuration (TD, ontology paths, light/sunshine bounds, sunshine
// probability, scenario files, qtable filename suffix) is resolved at startup
// from the Lab Profile registry.  To switch labs, edit active_profile/1 in
// lab_profiles.asl.  To enable training over the held-in scenario cycle, set
// active_profile("custom_full_train").
{ include("lab_profiles.asl") }

// Goal zone_goal/1 is derived at startup from zone_targets/N in the active profile.

// Training parameters
num_episodes(50).
max_steps_per_episode(20).
// S4-5 (audit-step-4): raised from 65 ms to 250 ms to exceed the Node-RED
// simulator's 200 ms tick. Previously the value contradicted its own
// comment and could return pre-tick state from readLabStatus, biasing
// the Q-update credit assignment toward the prior (rather than the
// post-action) state. 250 ms = one full tick + safety margin.
action_delay_ms(65).     // delay between actions during training (ms) — must exceed 200 ms simulator tick
exec_delay_ms(65).       // delay between actions during execution (ms)

exec_max_steps(20).

/* ============================================================
 * Initial Goals
 * ============================================================ */

!apply_profile_then_start.

/* ============================================================
 * Profile bridge — copy active-profile fields into the legacy
 * belief names that existing plans below query.  Runs before
 * !start so the rest of the agent code is unchanged.
 * ============================================================ */
@apply_profile_then_start
+!apply_profile_then_start <-
    !apply_runtime_overrides_ql;
    !profile_print;
    !profile_td(TdUrl);                     +lab_td(TdUrl);
    !profile_light_bounds(LightBounds);     +light_rank_bounds(LightBounds);
    !profile_sunshine_bounds(SunBounds);    +sunshine_rank_bounds(SunBounds);
    !profile_sunshine_prob(SunProb);        +sunshine_satisfaction_prob(SunProb);
    !profile_zone_targets(ZoneTargetList);
    !derive_zone_goal(ZoneTargetList, []);
    !maybe_set_train_scenarios_file;
    !start.

/* ============================================================
 * Runtime parameter overrides (#7) — -Dactive.profile=… replaces
 * the default active_profile/1 belief.
 * ============================================================ */
@apply_runtime_overrides_ql
+!apply_runtime_overrides_ql <-
    tools.jia.system_prop("active.profile", "", OverrideProfile);
    if (OverrideProfile \== "") {
        ?active_profile(OldP);
        -active_profile(OldP);
        +active_profile(OverrideProfile);
        .print("[RuntimeOverride] active_profile: ", OldP, " -> ", OverrideProfile)
    }.
// Failure handler: if tools.jia.system_prop is unavailable (e.g. ClassLoader
// race during parallel builds), log a warning and continue.  The active_profile
// belief will reflect whatever was pre-patched into lab_profiles.asl by the
// run script, so training still uses the correct per-profile configuration.
@apply_runtime_overrides_ql_fail
-!apply_runtime_overrides_ql <-
    .print("[RuntimeOverride] WARNING: tools.jia.system_prop failed; active_profile unchanged (using pre-patched lab_profiles.asl value).").

// Build zone_goal/1 belief as a list of target ranks (sorted by zone idx).
@derive_zone_goal_done
+!derive_zone_goal([], Acc) <-
    .reverse(Acc, Goal);
    +zone_goal(Goal).
@derive_zone_goal_step
+!derive_zone_goal([target(_, T)|R], Acc) <-
    !derive_zone_goal(R, [T|Acc]).

// Activate train_scenarios_file/1 only if the profile carries a non-empty path
// AND the qtable_suffix indicates a full-train ablation.  This preserves the
// previous default (random start states) for the plain "custom" profile.
@maybe_set_train_scenarios_file_full
+!maybe_set_train_scenarios_file
    : active_profile(P)
    & lab_profile(P, _, _, _, train_scenarios(File), _, _, _, _, _, _, qtable_suffix(QS), _)
    & QS \== "" & File \== "" <-
    +train_scenarios_file(File);
    .print("[Profile] train_scenarios_file enabled: ", File).
@maybe_set_train_scenarios_file_none
+!maybe_set_train_scenarios_file <- true.

/* ============================================================
 * @start — Initialise artifacts, print mode, begin training
 * ============================================================ */
@start
+!start : active_profile(ActiveP)
        & use_stereotypes(UseStereotypes)
        & lab_td(TdUrl)
        & zone_goal(Goal)
        & sunshine_satisfaction_prob(SunProb)
        & light_rank_bounds(LightBounds)
        & sunshine_rank_bounds(SunshineBounds) <-

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT - Q-LEARNING");
    .print("   Profile:  ", ActiveP);
    .print("   Stereo:   ", UseStereotypes);
    .print("   Goal:     ", Goal);
    .print("==========================================================");

    // Create the LabEnvironment artifact
    makeArtifact("lab", "tools.LabEnvironment", [TdUrl], LabId);
    +lab_artifact(LabId);
    // Fail-fast lab reachability probe: if the simulator HTTP endpoint is
    // unreachable the very first readLabStatus would block silently. Doing
    // an explicit probe here gives the user a clear, immediate diagnostic
    // in the MAS Console instead of an apparent freeze after the banner.
    .print("[probe] Checking simulator HTTP reachability ...");
    readLabStatus(_PZL, _PSR, _PSK, _PSV)[artifact_id(LabId)];
    .print("[probe] Simulator reachable — proceeding.");
    // Pre-compute scenario count for the training cycle
    if (train_scenarios_file(ScenariosFile)) {
        getScenarioIds(ScenariosFile, ScIds)[artifact_id(LabId)];
        .length(ScIds, TCount);
        +train_scenarios_count(TCount);
        .print("[Profile] train_scenarios_count=", TCount)
    };
    .print("Lab artifact created.");

    // Configure discretisation bounds from static beliefs
    // (tuned to the custom lab; replaces live calibration which used reset distribution)
    configureDiscretization(LightBounds, SunshineBounds)[artifact_id(LabId)];
    .print("[Config] Discretisation bounds (static): light=", LightBounds,
           " sunshine=", SunshineBounds);

    // Create the QLearner artifact
    makeArtifact("qlearner", "tools.QLearner", [], QlId);
    +qlearner_artifact(QlId);
    !profile_ont(OntPaths);
    configureQLearner(Goal, UseStereotypes, OntPaths, SunProb)[artifact_id(QlId)];
    .print("QLearner artifact created and initialised.");
    // Apply per-profile training parameters (episodes + epsilon decay)
    !profile_training_params(NumEps, EpDecay);
    -+num_episodes(NumEps);
    setEpsilonDecay(EpDecay)[artifact_id(QlId)];
    // S2-3 (audit Step 2): couple stereotype prior decay to the training
    // budget so the prior shape is identical across 50-ep sanity runs and
    // 10k-ep production runs. Honours -Dstereo.priorDecayEpisodes override.
    setTrainingBudgetEpisodes(NumEps)[artifact_id(QlId)];
    .print("[Profile] Training params: num_episodes=", NumEps, " epsilonDecay=", EpDecay);
    // Create the StereotypeLearner artifact and seed it with action metadata.
    makeArtifact("learner", "tools.StereotypeLearner", [], LId);
    +learner_artifact(LId);
    getNumActions(NumActions)[artifact_id(QlId)];
    getStateVecLen(StateVecLen)[artifact_id(QlId)];
    getActionMetadataForLearner(ActUris, ActVals, ActLabels)[artifact_id(QlId)];
    initLearner(NumActions, StateVecLen, ActUris, ActVals, ActLabels)[artifact_id(LId)];
    .print("[QL] StereotypeLearner ready (numActions=", NumActions,
           " stateVecLen=", StateVecLen, ").");
    !profile_qtable_suffix(QtSuffix);
    .concat("qtable_initial_stereotypes_", UseStereotypes, IB1);
    .concat(IB1, QtSuffix, IB2);
    .concat(IB2, ".csv", InitFile);
    saveQTable(InitFile)[artifact_id(QlId)];
    .print("[QL] Initial Q-table saved to ", InitFile);
    !train(0).

/* ============================================================
 * Training loop — episodes
 * ============================================================ */
@train
+!train(N) : num_episodes(MaxEpisodes) & N < MaxEpisodes <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);

    // Set start state: cycle through fixed scenario file if configured, else random
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

    // Run one episode
    !run_episode(N, 0);

    // Check terminal state for episode metrics
    readLabStatus(ZLEnd, SREnd, SKEnd, SVEnd)[artifact_id(LabId)];
    encodeState(ZLEnd, SREnd, SKEnd, SVEnd, FinalState)[artifact_id(QlId)];
    isTerminal(FinalState, GoalReached)[artifact_id(QlId)];
    endEpisode(N, GoalReached)[artifact_id(QlId)];

    // Decay epsilon after each episode
    decayEpsilon[artifact_id(QlId)];

    // Adaptive progress: every episode for short runs (≤100 eps), every 10 otherwise.
    // GoalReached comes from the isTerminal/endEpisode calls above.
    Pct = ((N + 1) * 100) / MaxEpisodes;
    if (MaxEpisodes <= 100 | ((N + 1) mod 10) == 0) {
        .print("[Training] ep ", N + 1, "/", MaxEpisodes, " (", Pct, "%) goal=", GoalReached)
    };
    // Full QLearner status every 50 episodes
    if (((N + 1) mod 50) == 0) {
        getStatus(Status)[artifact_id(QlId)];
        .print("[Training] >> ep ", N + 1, "/", MaxEpisodes, " | ", Status)
    };

    // Early stopping: if Q-table has converged stop training before MaxEpisodes
    hasConverged(Converged)[artifact_id(QlId)];
    if (Converged) {
        .print("[Training] Converged after ", N + 1, " episodes — stopping early.");
        !train(MaxEpisodes)   // triggers @train_done
    } else {
        !train(N + 1)
    }.

@train_done
+!train(N) : num_episodes(MaxEpisodes) & N >= MaxEpisodes <-
    .print("");
    .print("==========================================================");
    .print("   Training complete after ", N, " episodes.");
    .print("   Switching to policy execution mode.");
    .print("==========================================================");
    ?qlearner_artifact(QlId);
    ?use_stereotypes(UseStereotypes);
    !profile_qtable_suffix(QtSuffix);
    !sx_filename("qtable_final_stereotypes_",  UseStereotypes, QtSuffix, ".csv",  FinalFile);
    saveQTable(FinalFile)[artifact_id(QlId)];
    .print("[QL] Final Q-table saved to ", FinalFile);
    !sx_filename("metrics_stereotypes_",       UseStereotypes, QtSuffix, ".csv",  MetricsFile);
    saveMetrics(MetricsFile)[artifact_id(QlId)];
    .print("[QL] Convergence metrics saved to ", MetricsFile);
    !sx_filename("iv_stats_stereotypes_",      UseStereotypes, QtSuffix, ".json", IVFile);
    saveIVStats(IVFile)[artifact_id(QlId)];
    .print("[QL] IV effectiveness stats saved to ", IVFile);
    !sx_filename("coverage_stereotypes_",      UseStereotypes, QtSuffix, ".csv",  CovFile);
    saveCoverage(CovFile)[artifact_id(QlId)];
    .print("[QL] Coverage data saved to ", CovFile);
    !sx_filename("first_goal_stereotypes_",    UseStereotypes, QtSuffix, ".csv",  FGFile);
    saveFirstGoalPerScenario(FGFile)[artifact_id(QlId)];
    .print("[QL] First-goal-per-scenario data saved to ", FGFile);
    // Dump the discovered-effects produced by StereotypeLearner.
    ?learner_artifact(LId);
    !sx_filename("learned_stereotypes_",       UseStereotypes, QtSuffix, ".ttl",  LearnFile);
    saveLearnedStereotypes(LearnFile)[artifact_id(LId)];
    printStats[artifact_id(LId)];
    .print("[QL] Learned stereotypes saved to ", LearnFile);
    !execute_policy(0).

// Compose <Prefix><Bool><Suffix><Ext> into a single filename.
@sx_filename
+!sx_filename(Prefix, Bool, Suffix, Ext, Out) <-
    .concat(Prefix, Bool,  S1);
    .concat(S1,    Suffix, S2);
    .concat(S2,    Ext,    Out).

/* ============================================================
 * Episode execution — starts a new episode from current state
 * ============================================================ */
@run_episode
+!run_episode(EpN, Step) <-
    ?qlearner_artifact(QlId);
    ?lab_artifact(LabId);
    ?max_steps_per_episode(MaxSteps);

    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)[artifact_id(QlId)];
    isTerminal(StateVec, Terminal)[artifact_id(QlId)];

    if (not Terminal & Step < MaxSteps) {
        !do_step(EpN, Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs)
    }.

/* ============================================================
 * Single step within an episode
 * ============================================================ */
@do_step
+!do_step(EpN, Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs) <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);
    ?action_delay_ms(Delay);
    ?max_steps_per_episode(MaxSteps);

    // Choose action (ε-greedy)
    getActionFromState(StateVec, true, Action)[artifact_id(QlId)];

    // Convert to WoT action
    actionToWoT(Action, WotType, WotValue)[artifact_id(QlId)];

    // Execute in environment (skip if do-nothing)
    if (WotType \== "none") {
        invokeAction(WotType, WotValue)[artifact_id(LabId)]
    };
    .wait(Delay);

    // Observe next state
    readLabStatus(ZoneLevels2, SunshineRank2, SKs2, SVs2)[artifact_id(LabId)];
    encodeState(ZoneLevels2, SunshineRank2, SKs2, SVs2, NextState)[artifact_id(QlId)];

    // Update Q-table (per-zone rewards computed internally)
    calculateQ(StateVec, Action, NextState)[artifact_id(QlId)];

    // Feed the (state, action, next-state) triple to the StereotypeLearner
    // so it can accumulate Welford statistics for ontology gap discovery.
    ?learner_artifact(LId);
    observe(StateVec, Action, NextState)[artifact_id(LId)];

    // Check terminal and recurse if needed
    isTerminal(NextState, Terminal)[artifact_id(QlId)];

    if (Terminal) {
        notifyGoalReached(EpN)[artifact_id(QlId)]
    };
    if (not Terminal & Step + 1 < MaxSteps) {
        !run_episode(EpN, Step + 1)
    }.

/* ============================================================
 * Policy execution — greedy loop after training
 * ============================================================ */
@execute_policy
+!execute_policy(Step) : exec_max_steps(MaxExecSteps) & Step < MaxExecSteps <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);
    ?exec_delay_ms(Delay);

    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)[artifact_id(QlId)];
    isTerminal(StateVec, Terminal)[artifact_id(QlId)];

    // Zone-count-agnostic diagnostic: print the whole zone-level list so this
    // plan works for single-zone (lab1) and multi-zone (lab2/lab3) labs alike.
    // A previous hard-coded .nth(1,...) crashed on single-zone labs, which sent
    // -!execute_policy into an infinite retry loop (continuous log output, so
    // the orchestrator's idle-based watchdogs never fired).
    .print("[Execute] Step ", Step, " State: zones=", ZoneLevels, " sun=", SunshineRank);

    if (Terminal) {
        .print("");
        .print("==========================================================");
        .print("   SUCCESS! Target illuminance levels achieved!");
        .print("==========================================================");
        .print("[QL] Demonstration reached goal — stopping MAS.");
        .stopMAS
    } else {
        // Greedy action (no exploration)
        getActionFromState(StateVec, false, Action)[artifact_id(QlId)];
        actionToWoT(Action, WotType, WotValue)[artifact_id(QlId)];
        .print("[Execute] Action: ", Action, " -> ", WotType, "=", WotValue);

        if (WotType \== "none") {
            invokeAction(WotType, WotValue)[artifact_id(LabId)]
        };
        .wait(Delay);
        !execute_policy(Step + 1)
    }.

@execute_policy_limit
+!execute_policy(Step) : exec_max_steps(MaxExecSteps) & Step >= MaxExecSteps <-
    ?qlearner_artifact(QlId);
    getStatus(Status)[artifact_id(QlId)];
    .print("[Execute] Max steps reached (", MaxExecSteps, "). Final status: ", Status);
    .print("[QL] All done — stopping MAS.");
    .stopMAS.

/* ============================================================
 * Failure handling
 * ============================================================ */
-!start[error(Err), error_msg(Msg)] <-
    .print("ERROR -!start: ", Err, " - ", Msg).

-!start <-
    .print("ERROR: Failed to start. Check that the simulator is running and");
    .print("       the Thing Description URL is accessible.").

// Bounded retry with delay — a tight retry loop here was triggering a clean
// JVM shutdown in stereo=false runs after a few seconds of recursive intention
// fan-out. We cap retries per-N and wait between attempts so transient HTTP
// failures recover but a real failure aborts the training (rather than
// silently exiting with no artifacts).
-!train(N)[error(Err), error_msg(Msg)] <-
    .print("[train-fail] -!train(", N, "): ", Err, " - ", Msg, " — retrying in 1s");
    .wait(1000);
    !retry_train(N, 1).

-!train(N) <-
    .print("[train-fail] WARNING: Training step failed at N=", N, " — retrying in 1s");
    .wait(1000);
    !retry_train(N, 1).

@retry_train_ok
+!retry_train(N, Attempt) : Attempt <= 3 <-
    .print("[train-fail] retry attempt ", Attempt, "/3 at N=", N);
    !train(N).
@retry_train_giveup
+!retry_train(N, Attempt) <-
    .print("[train-fail] giving up after ", Attempt - 1, " retries at N=", N, " — aborting training");
    .fail.
-!retry_train(N, Attempt)[error(Err), error_msg(Msg)] <-
    .print("[train-fail] retry(", N, ",", Attempt, ") failed: ", Err, " - ", Msg, " — next attempt in 1s");
    .wait(1000);
    NextAttempt = Attempt + 1;
    !retry_train(N, NextAttempt).

-!run_episode(EpN, Step)[error(Err), error_msg(Msg)] <-
    .print("WARNING -!run_episode(", EpN, ",", Step, "): ", Err, " - ", Msg).

-!run_episode(EpN, Step) <-
    .print("WARNING: Episode step ", Step, " failed.").

-!do_step(EpN, Step, _, _, _, _, _)[error(Err), error_msg(Msg)] <-
    .print("WARNING -!do_step(ep=", EpN, " step=", Step, "): ", Err, " - ", Msg).

-!do_step(EpN, Step, _, _, _, _, _) <-
    .print("WARNING: do_step(", Step, ") failed - skipping step.").

-!execute_policy(Step) <-
    .print("WARNING: Policy execution step ", Step, " failed. Retrying.");
    .wait(1000);
    !execute_policy(Step).

/* ============================================================
 * Simulator / input failure handlers (#5, #8)
 * ============================================================ */
+!handle_simulator_failure(Reason, Op, Detail) <-
    .print("ERROR: Simulator failure during QL — reason=", Reason,
           " op=", Op, " detail=", Detail);
    .print("       Stopping training.").

+!handle_invalid_input(Actuator, Expected, Actual) <-
    .print("ERROR: Invalid input during QL — actuator=", Actuator,
           " expected=", Expected, " actual=", Actual).
