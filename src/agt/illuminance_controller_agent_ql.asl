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
//     - Blind-open actions are masked when sunshine < rank 1 (reflecting
//       ws:pm_daylight_ingress ws:ivMinRank=1 from lab-ontology.ttl).
//     Expected: faster convergence due to physics-informed prior knowledge.
//
//   use_stereotypes(false) → Standard Q-learning:
//     - Q-table initialised uniformly to 0.
//     - All 9 actions always eligible for selection.
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

// Environment selection — comment/uncomment to switch:
lab_td("classpath:interactions-lab-custom.ttl").
// lab_td("https://raw.githubusercontent.com/Interactions-HSG/example-tds/was/tds/interactions-lab.ttl").

// Goal: [Z1TargetRank, Z2TargetRank]  (ranks 0=dark … 3=bright)
zone_goal([3, 2]).

// Training parameters
num_episodes(500).
max_steps_per_episode(75).
action_delay_ms(250).       // delay between actions during training (ms)
exec_delay_ms(2000).        // delay between actions during execution (ms)

// Internal counter (do not edit)
training_episode(0).
exec_max_steps(30).

/* ============================================================
 * Initial Goals
 * ============================================================ */

!start.

/* ============================================================
 * @start — Initialise artifacts, print mode, begin training
 * ============================================================ */
@start
+!start : use_stereotypes(UseStereotypes)
        & lab_td(TdUrl)
        & zone_goal(Goal) <-

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT — Q-LEARNING");
    if (UseStereotypes) {
        .print("   STEREOTYPE MODE: ON  (ontology-informed initialisation)");
        .print("   Pre-penalties applied for redundant/invalid actions.");
        .print("   Action masking: blinds blocked when sunshine < rank 1.");
    } else {
        .print("   STEREOTYPE MODE: OFF (standard zero-initialisation)");
        .print("   All 9 actions always eligible. Agent learns from scratch.");
    };
    .print("   Goal: ", Goal);
    .print("==========================================================");

    // Create the LabEnvironment artifact
    makeArtifact("lab", "tools.LabEnvironment", [TdUrl], LabId);
    +lab_artifact(LabId);
    .print("Lab artifact created.");

    // Create the QLearner artifact
    makeArtifact("qlearner", "tools.QLearner", [], QlId);
    +qlearner_artifact(QlId);
    .nth(0, Goal, G1);
    .nth(1, Goal, G2);
    configureQLearner([G1, G2], UseStereotypes)[artifact_id(QlId)];
    .print("QLearner artifact created and initialised.");
    if (UseStereotypes) { InitFile = "qtable_initial_stereotypes.csv" } else { InitFile = "qtable_initial_standard.csv" };
    saveQTable(InitFile)[artifact_id(QlId)];
    .print("[QL] Initial Q-table saved to ", InitFile);

    !train.

/* ============================================================
 * Training loop — episodes
 * ============================================================ */
@train
+!train : num_episodes(MaxEpisodes) & training_episode(N) & N < MaxEpisodes <-
    ?lab_artifact(LabId);
    ?qlearner_artifact(QlId);

    // Reset the simulator to a random state for this episode
    resetLab[artifact_id(LabId)];
    .wait(300); // let the sim settle after reset

    // Run one episode
    !run_episode(0);

    // Decay epsilon after each episode
    decayEpsilon[artifact_id(QlId)];

    // Advance counter
    NNext is N + 1;
    -training_episode(_);
    +training_episode(NNext);

    // Progress log every 50 episodes
    if ((NNext mod 50) =:= 0) {
        getStatus(Status)[artifact_id(QlId)];
        .print("[Training] Episode ", NNext, "/", MaxEpisodes, " | ", Status)
    };

    !train.

@train_done
+!train : num_episodes(MaxEpisodes) & training_episode(N) & N >= MaxEpisodes <-
    .print("");
    .print("==========================================================");
    .print("   Training complete after ", N, " episodes.");
    .print("   Switching to policy execution mode.");
    .print("==========================================================");
    ?qlearner_artifact(QlId);
    ?use_stereotypes(UseStereotypes);
    if (UseStereotypes) { FinalFile = "qtable_final_stereotypes.csv" } else { FinalFile = "qtable_final_standard.csv" };
    saveQTable(FinalFile)[artifact_id(QlId)];
    .print("[QL] Final Q-table saved to ", FinalFile);
    !execute_policy(0).

/* ============================================================
 * Episode execution — starts a new episode from current state
 * ============================================================ */
@run_episode
+!run_episode(Step) <-
    ?qlearner_artifact(QlId);
    ?lab_artifact(LabId);
    ?max_steps_per_episode(MaxSteps);

    readLabStatus(ZoneLevels, SunshineRank, SKs, SVs)[artifact_id(LabId)];
    encodeState(ZoneLevels, SunshineRank, SKs, SVs, StateVec)[artifact_id(QlId)];
    isTerminal(StateVec, Terminal)[artifact_id(QlId)];

    if (not Terminal & Step < MaxSteps) {
        !do_step(Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs)
    }.

/* ============================================================
 * Single step within an episode
 * ============================================================ */
@do_step
+!do_step(Step, StateVec, ZoneLevels, SunshineRank, SKs, SVs) <-
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

    // Compute reward and update Q-table
    computeReward(StateVec, Action, NextState, Reward)[artifact_id(QlId)];
    calculateQ(StateVec, Action, Reward, NextState)[artifact_id(QlId)];

    // Check terminal and recurse if needed
    isTerminal(NextState, Terminal)[artifact_id(QlId)];
    NextStep is Step + 1;

    if (Terminal) {
        ?training_episode(CurrentEp);
        notifyGoalReached(CurrentEp)[artifact_id(QlId)]
    };
    if (not Terminal & NextStep < MaxSteps) {
        !run_episode(NextStep)
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

    .nth(0, ZoneLevels, L1);
    .nth(1, ZoneLevels, L2);
    .print("[Execute] Step ", Step, " State: Z1=", L1, " Z2=", L2, " sun=", SunshineRank);

    if (Terminal) {
        .print("");
        .print("==========================================================");
        .print("   SUCCESS! Target illuminance levels achieved!");
        .print("==========================================================")
    } else {
        // Greedy action (no exploration)
        getActionFromState(StateVec, false, Action)[artifact_id(QlId)];
        actionToWoT(Action, WotType, WotValue)[artifact_id(QlId)];
        .print("[Execute] Action: ", Action, " \u2192 ", WotType, "=", WotValue);

        if (WotType \== "none") {
            invokeAction(WotType, WotValue)[artifact_id(LabId)]
        };
        .wait(Delay);
        NextExecStep is Step + 1;
        !execute_policy(NextExecStep)
    }.

@execute_policy_limit
+!execute_policy(Step) : exec_max_steps(MaxExecSteps) & Step >= MaxExecSteps <-
    ?qlearner_artifact(QlId);
    getStatus(Status)[artifact_id(QlId)];
    .print("[Execute] Max steps reached (", MaxExecSteps, "). Final status: ", Status).

/* ============================================================
 * Failure handling
 * ============================================================ */
-!start <-
    .print("ERROR: Failed to start. Check that the simulator is running and");
    .print("       the Thing Description URL is accessible.").

-!train <-
    .print("WARNING: Training step failed. Retrying.");
    !train.

-!run_episode(Step) <-
    .print("WARNING: Episode step ", Step, " failed.").

-!do_step(Step, _, _, _, _, _) <-
    .print("WARNING: do_step(", Step, ") failed — skipping step.").

-!execute_policy(Step) <-
    .print("WARNING: Policy execution step ", Step, " failed. Retrying.");
    .wait(1000);
    !execute_policy(Step).
