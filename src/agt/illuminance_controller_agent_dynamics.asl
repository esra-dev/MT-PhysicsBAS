// Illuminance Controller Agent — Phase 3: Learning Process Dynamics
// MT-Esra Project: response-delay learning + deadline-aware exploitation
//
// This agent does NOT train a Q-table. It reuses the QLearner artifact purely
// to enumerate the action space (numActions / per-action WoT metadata) for the
// active "slow" lab, and the LabEnvironment artifact to drive the simulator. It
// then runs two phases:
//
//   PHASE A — PROBE (learn the dynamics)
//     For every actuator it runs controlled probe trials: pin a baseline (the
//     target zone dark, the sun high so the motorized blind is effective, all
//     actuators off), read the simulator Tick clock, toggle exactly ONE actuator
//     ON, and poll until a zone illuminance rank rises. The tick difference is
//     one response-delay sample (folded into DynamicsLearner via Welford). The
//     fast task lamp settles in ~0 ticks; the motorized blind in ~12 ticks. Each
//     probe also records, empirically, WHICH zones the actuator drives and to
//     what rank (action_effect/3) and its holding ENERGY cost (action_cost/2) —
//     so the planner is fully data-driven (no hard-coded actuator identities).
//     Learned delays are written back to the Knowledge Graph as ws:responseDelay
//     (learned_dynamics_<bool>_<profile>.ttl) and a flat CSV for analysis.
//
//   PHASE B — EXPLOIT (use the dynamics)
//     For each time-bounded goal ("reach zone Z rank >= R within D seconds") a
//     deadline-aware planner enumerates the actuators that reach the target,
//     filters those whose BELIEVED delay fits the deadline, and picks the
//     lowest-energy survivor (the passive blind is free; the lamp costs energy
//     every tick). The KG-primed arm (dynamics.mode=ql_true) uses the LEARNED
//     delay; the tabula-rasa arm (ql_false) assumes zero delay and therefore
//     always grabs the cheapest actuator — missing tight deadlines because it
//     does not know the blind is slow. The chosen actuator is executed and the
//     ACTUAL time-to-target measured; met=1 iff the target rank is reached
//     within the deadline. Rows are written to timebounded_results_<bool>_<P>.csv.
//
// Run:  ./gradlew taskDynamics -Pprofile=lab2_slow -Pmode=ql_true
//       (with the matching slow Node-RED simulator flow running on its port)

/* ============================================================
 * Initial Beliefs
 * ============================================================ */

// Drives QLearner action-space construction only (no learning happens). Kept
// true so the full action set is enumerated; it does NOT affect the planner.
use_stereotypes(true).

// Planner mode (KG-primed vs tabula-rasa). Overridden at startup by -Pmode:
//   ql_true  -> use the LEARNED per-actuator response delay.
//   ql_false -> assume zero delay (no dynamics knowledge).
use_dynamics_kg(true).
mode_label("ql_true").
mode_bool("true").

// Lab Profile registry (shared with the QL / bench / adapt agents).
{ include("lab_profiles.asl") }

// ---- Dynamics / probe parameters (overridable via -D system properties) ----
seconds_per_tick(5.0).        // wall-clock-equivalent seconds per environment tick
probe_settle_ms(400).         // settle time after pinning a baseline (ms)
probe_poll_ms(50).            // status poll cadence (ms) — matches the 50 ms env tick
probe_max_wait_ticks(60).     // max polls awaiting an effect before giving up
probe_hold_ticks(16).         // polls to hold an actuator ON to accrue its energy cost
probes_per_actuator(8).       // delay samples per actuator
action_delay_ms(65).          // settle after an action dispatch (ms)

// ---- Probe baselines (per profile): all actuators OFF, sun HIGH so the blind
//      is effective. Keys are simulator status fields (validated by the TD).  ----
probe_baseline("lab2_slow",
               ["Z1Light","Z2Light","Z1Blinds","Z2Blinds","Sunshine"],
               [false,false,false,false,900]).
probe_baseline("lab3_slow",
               ["Z1Light","Z2Light","Z1Blinds","Z2Blinds","Spotlight","Sunshine"],
               [false,false,false,false,false,900]).

// ---- Time-bounded exploit goals: tb_goal(Id, Zone, TargetRank, DeadlineSec).
//      Sun is pinned high so the blind is EFFECTIVE; the only differentiator is
//      its response delay vs the deadline. Mirror config/run_config.json
//      ("phase3".timebounded_goals) — keep in sync. blind delay = 12 ticks * 5 s
//      = 60 s, so deadlines < 60 s are "tight" (lamp only) and >= 60 s "loose". ----
tb_goal("g1", 1, 3, 15.0).
tb_goal("g2", 1, 3, 45.0).
tb_goal("g3", 1, 3, 90.0).
tb_goal("g4", 1, 3, 300.0).
tb_goal("g5", 2, 3, 15.0).
tb_goal("g6", 2, 3, 300.0).

/* ============================================================
 * Rules
 * ============================================================ */

// True if some position in the second rank list strictly exceeds the same
// position in the first (i.e. a zone illuminance rank rose).
list_increased([B|_], [N|_]) :- N > B.
list_increased([_|BR], [_|NR]) :- list_increased(BR, NR).

// Believed delay (seconds) a candidate actuator has, per planner mode.
//   KG-primed  -> the LEARNED delay materialised as learned_delay_sec/2.
//   tabula-rasa -> zero (no knowledge of any delay).
believed_delay(A, true,  D) :- learned_delay_sec(A, D).
believed_delay(_, false, 0).

// Feasibility flag for the planner sort key: 0 = fits the deadline, 1 = not.
key_infeas(B, Deadline, 0) :- B <= Deadline.
key_infeas(B, Deadline, 1) :- B >  Deadline.

/* ============================================================
 * Initial Goal
 * ============================================================ */

!apply_profile_then_start_dynamics.

/* ============================================================
 * Profile bridge — copy active-profile fields into the legacy
 * belief names the plans query, then start the dynamics run.
 * ============================================================ */
@apply_profile_then_start_dynamics
+!apply_profile_then_start_dynamics <-
    !apply_runtime_overrides_dyn;
    !load_probe_params;
    !profile_print;
    !profile_td(TdUrl);                     +lab_td(TdUrl);
    !profile_light_bounds(LightBounds);     +light_rank_bounds(LightBounds);
    !profile_sunshine_bounds(SunBounds);    +sunshine_rank_bounds(SunBounds);
    !profile_sunshine_prob(SunProb);        +sunshine_satisfaction_prob(SunProb);
    !profile_zone_targets(ZoneTargetList);
    !derive_zone_goal(ZoneTargetList, []);
    !start_dynamics.

/* ============================================================
 * Runtime overrides:
 *   -Dactive.profile=…           replaces active_profile/1
 *   -Ddynamics.mode=ql_true|ql_false  sets use_dynamics_kg + labels
 * ============================================================ */
@apply_runtime_overrides_dyn
+!apply_runtime_overrides_dyn <-
    tools.jia.system_prop("active.profile", "", OverrideProfile);
    if (OverrideProfile \== "") {
        ?active_profile(OldP);
        -active_profile(OldP);
        +active_profile(OverrideProfile);
        .print("[RuntimeOverride] active_profile: ", OldP, " -> ", OverrideProfile)
    };
    tools.jia.system_prop("dynamics.mode", "", ModeOverride);
    if (ModeOverride \== "") {
        ?use_dynamics_kg(OldK); -use_dynamics_kg(OldK);
        -mode_label(_); -mode_bool(_);
        if (ModeOverride == "ql_false") {
            +use_dynamics_kg(false); +mode_label("ql_false"); +mode_bool("false");
            .print("[RuntimeOverride] dynamics planner -> tabula-rasa (ql_false)")
        } else {
            +use_dynamics_kg(true);  +mode_label("ql_true");  +mode_bool("true");
            .print("[RuntimeOverride] dynamics planner -> KG-primed (ql_true)")
        }
    }.
@apply_runtime_overrides_dyn_fail
-!apply_runtime_overrides_dyn <-
    .print("[RuntimeOverride] WARNING: tools.jia.system_prop failed; using defaults.").

// Pull probe parameters from -D system properties (fall back to the beliefs).
@load_probe_params
+!load_probe_params <-
    tools.jia.system_prop_num("seconds.per.tick",     5.0, SPT); -+seconds_per_tick(SPT);
    tools.jia.system_prop_num("probe.settle.ms",      400, S);   -+probe_settle_ms(S);
    tools.jia.system_prop_num("probe.poll.ms",        50,  P);   -+probe_poll_ms(P);
    tools.jia.system_prop_num("probe.max.wait.ticks", 60,  MW);  -+probe_max_wait_ticks(MW);
    tools.jia.system_prop_num("probe.hold.ticks",     16,  H);   -+probe_hold_ticks(H);
    tools.jia.system_prop_num("probe.count",          8,   C);   -+probes_per_actuator(C);
    ?seconds_per_tick(SPTv); ?probes_per_actuator(Cv);
    .print("[Dynamics] params: secondsPerTick=", SPTv, " probesPerActuator=", Cv).
@load_probe_params_fail
-!load_probe_params <-
    .print("[Dynamics] WARNING: system_prop_num failed; using default probe params.").

// Build zone_goal/1 (list of target ranks sorted by zone idx) for configureQLearner.
@derive_zone_goal_done
+!derive_zone_goal([], Acc) <- .reverse(Acc, Goal); +zone_goal(Goal).
@derive_zone_goal_step
+!derive_zone_goal([target(_, T)|R], Acc) <- !derive_zone_goal(R, [T|Acc]).

/* ============================================================
 * @start_dynamics — create artifacts, enumerate the action
 * space, then run the probe + exploit phases.
 * ============================================================ */
@start_dynamics
+!start_dynamics : active_profile(ActiveP)
        & use_stereotypes(UseStereotypes)
        & use_dynamics_kg(UseKg)
        & lab_td(TdUrl)
        & zone_goal(Goal)
        & sunshine_satisfaction_prob(SunProb)
        & light_rank_bounds(LightBounds)
        & sunshine_rank_bounds(SunshineBounds) <-

    .print("==========================================================");
    .print("   ILLUMINANCE CONTROLLER AGENT - PHASE 3 DYNAMICS");
    .print("   Profile:  ", ActiveP, "  (slow / delayed actuator)");
    .print("   Planner:  ", UseKg, "  (true=KG-primed, false=tabula-rasa)");
    .print("   Goal:     ", Goal);
    .print("==========================================================");

    // LabEnvironment (slow simulator endpoint).
    makeArtifact("lab", "tools.LabEnvironment", [TdUrl], LabId);
    +lab_artifact(LabId);
    .print("[probe] Checking simulator HTTP reachability ...");
    readLabStatusTimed(_PZL, _PSR, _PTick)[artifact_id(LabId)];
    .print("[probe] Simulator reachable — proceeding.");
    configureDiscretization(LightBounds, SunshineBounds)[artifact_id(LabId)];

    // QLearner — used ONLY to enumerate the action space for this lab.
    makeArtifact("qlearner", "tools.QLearner", [], QlId);
    +qlearner_artifact(QlId);
    !profile_ont(OntPaths);
    configureQLearner(Goal, UseStereotypes, OntPaths, SunProb)[artifact_id(QlId)];

    // DynamicsLearner — accumulates per-actuator response-delay statistics.
    makeArtifact("dynamics", "tools.DynamicsLearner", [], DId);
    +dyn_artifact(DId);
    getNumActions(NumActions)[artifact_id(QlId)];
    getActionMetadataForLearner(ActUris, ActVals, ActLabels)[artifact_id(QlId)];
    ?seconds_per_tick(SPT);
    initDynamics(NumActions, ActUris, ActVals, ActLabels, SPT)[artifact_id(DId)];
    +action_meta(ActUris, ActVals, ActLabels);
    !assert_action_labels(0, NumActions, ActLabels);
    .print("[Dynamics] action space size = ", NumActions);

    // Build the list of ON-actuator action indices to probe.
    !collect_probe_actions(0, NumActions, ActUris, ActVals, [], ProbeList);
    .print("[Dynamics] probe targets (ON-actuator action ids) = ", ProbeList);

    // PHASE A — probe every actuator.
    !probe_all(ProbeList);
    printStats[artifact_id(DId)];

    // Write learned dynamics back to the KG + analysis CSV.
    ?mode_bool(Bool);
    .concat("learned_dynamics_", Bool, "_", ActiveP, ".ttl", DynTtl);
    saveLearnedDynamics(DynTtl)[artifact_id(DId)];
    .concat("dynamics_delays_", Bool, "_", ActiveP, ".csv", DelayCsv);
    saveDelayTable(DelayCsv)[artifact_id(DId)];
    .print("[Dynamics] wrote ", DynTtl, " and ", DelayCsv);

    // Materialise learned per-action delays as beliefs for the planner.
    !materialise_delays(ProbeList);

    // PHASE B — deadline-aware exploitation.
    .findall(tb_goal(Id, Z, T, D), tb_goal(Id, Z, T, D), Goals);
    !exploit_all(Goals);
    .concat("timebounded_results_", Bool, "_", ActiveP, ".csv", ResCsv);
    saveExploitResults(ResCsv)[artifact_id(DId)];
    .print("[Dynamics] wrote ", ResCsv);

    .print("==========================================================");
    .print("   PHASE 3 DYNAMICS COMPLETE for ", ActiveP, " (", Bool, ")");
    .print("==========================================================");
    !dynamics_finish.

@start_dynamics_missing
+!start_dynamics <-
    .print("[Dynamics] FATAL: prerequisites missing (profile/td/goal beliefs). Aborting.");
    !dynamics_finish.

/* ============================================================
 * Action-metadata helpers
 * ============================================================ */

// Assert action_label_b(Idx, Label) for every action (for logging).
@assert_action_labels_done
+!assert_action_labels(I, N, _) : I >= N <- true.
@assert_action_labels_step
+!assert_action_labels(I, N, Labels) : I < N <-
    .nth(I, Labels, L);
    +action_label_b(I, L);
    !assert_action_labels(I + 1, N, Labels).

// Accessor: label for an action id (falls back to a generic token).
@action_label_known
+!action_label(A, L) : action_label_b(A, L) <- true.
@action_label_unknown
+!action_label(A, L) <- .concat("action_", A, L).

// Collect every actuator-bearing action index (a real WoT URI). Both ON and OFF
// variants are probed; the inert OFF variant simply yields no effect and is
// dropped from the candidate set, so we never rely on decoding the WoT boolean.
@collect_probe_actions_done
+!collect_probe_actions(I, N, _, _, Acc, Out) : I >= N <- .reverse(Acc, Out).
@collect_probe_actions_step
+!collect_probe_actions(I, N, Uris, Vals, Acc, Out) : I < N <-
    .nth(I, Uris, U);
    if (U \== "" & U \== "none") {
        !collect_probe_actions(I + 1, N, Uris, Vals, [I|Acc], Out)
    } else {
        !collect_probe_actions(I + 1, N, Uris, Vals, Acc, Out)
    }.

/* ============================================================
 * PHASE A — probing
 * ============================================================ */
@probe_all_done
+!probe_all([]) <- .print("[Probe] all actuators probed.").
@probe_all_step
+!probe_all([A|Rest]) <-
    !action_label(A, L);
    .print("[Probe] actuator action ", A, " (", L, ") ...");
    ?probes_per_actuator(K);
    !characterise(A);            // 1 delay sample + effect zones + energy cost
    // Only an actuator that actually drove a zone gets the remaining delay
    // samples — this skips the inert OFF-actions for free (and is robust to how
    // the WoT boolean payload is represented across the artifact boundary).
    if (action_effect(A, _, _)) {
        !delay_only(A, K - 1)
    } else {
        .print("[Probe]   action ", A, " produced no effect — inert (single pass).")
    };
    !probe_all(Rest).

// Characterise one actuator: pin baseline, fire it, hold to accrue energy,
// record the first-rise delay, the driven zones, and the holding cost.
@characterise
+!characterise(A) <-
    ?lab_artifact(LabId); ?qlearner_artifact(QlId); ?dyn_artifact(DId);
    ?active_profile(P); ?probe_baseline(P, BKeys, BVals);
    ?probe_settle_ms(SettleMs); ?probe_hold_ticks(HoldTicks);
    setLabStateFromMap(BKeys, BVals)[artifact_id(LabId)];
    .wait(SettleMs);
    readLabStatusTimed(ZL0, _SR0, Tick0)[artifact_id(LabId)];
    actionToWoT(A, WotType, WotValue)[artifact_id(QlId)];
    invokeAction(WotType, WotValue)[artifact_id(LabId)];
    !hold_and_measure(A, ZL0, Tick0, HoldTicks, -1, Delay);
    readEnergyCost(Energy)[artifact_id(LabId)];
    readLabStatusTimed(ZLf, _SRf, _Tf)[artifact_id(LabId)];
    if (Delay >= 0) { recordDelaySample(A, Delay)[artifact_id(DId)] };
    +action_cost(A, Energy);
    !record_effect_zones(A, 1, ZL0, ZLf);
    .print("[Probe]   action ", A, " first-effect delay=", Delay,
           " ticks, holding energy=", Energy).

// Hold an actuator ON for PollsLeft polls, capturing the first-rise delay.
@hold_and_measure_done
+!hold_and_measure(_, _, _, 0, DelaySoFar, DelaySoFar) <- true.
@hold_and_measure_step
+!hold_and_measure(A, ZL0, Tick0, PollsLeft, DelaySoFar, Out) : PollsLeft > 0 <-
    ?probe_poll_ms(PollMs);
    .wait(PollMs);
    ?lab_artifact(LabId);
    readLabStatusTimed(ZLn, _SR, Tickn)[artifact_id(LabId)];
    if (DelaySoFar < 0 & list_increased(ZL0, ZLn)) {
        !hold_and_measure(A, ZL0, Tick0, PollsLeft - 1, Tickn - Tick0, Out)
    } else {
        !hold_and_measure(A, ZL0, Tick0, PollsLeft - 1, DelaySoFar, Out)
    }.

// Record action_effect(A, Zone, FinalRank) for each zone whose rank rose.
@record_effect_zones_done
+!record_effect_zones(_, _, [], []) <- true.
@record_effect_zones_step
+!record_effect_zones(A, Z, [B|BR], [F|FR]) <-
    if (F > B) { +action_effect(A, Z, F) };
    !record_effect_zones(A, Z + 1, BR, FR).

// Remaining delay-only probe trials (no hold; exit on first rise).
@delay_only_done
+!delay_only(_, K) : K <= 0 <- true.
@delay_only_step
+!delay_only(A, K) : K > 0 <-
    ?lab_artifact(LabId); ?qlearner_artifact(QlId); ?dyn_artifact(DId);
    ?active_profile(P); ?probe_baseline(P, BKeys, BVals);
    ?probe_settle_ms(SettleMs); ?probe_max_wait_ticks(MaxW);
    setLabStateFromMap(BKeys, BVals)[artifact_id(LabId)];
    .wait(SettleMs);
    readLabStatusTimed(ZL0, _SR0, Tick0)[artifact_id(LabId)];
    actionToWoT(A, WotType, WotValue)[artifact_id(QlId)];
    invokeAction(WotType, WotValue)[artifact_id(LabId)];
    !measure_delay(A, ZL0, Tick0, MaxW, 0, Delay);
    if (Delay >= 0) { recordDelaySample(A, Delay)[artifact_id(DId)] };
    !delay_only(A, K - 1).

// Poll until any zone rank rises (delay in ticks) or the poll budget is spent.
@measure_delay_hit
+!measure_delay(A, ZL0, Tick0, MaxW, Waited, Out) : Waited < MaxW <-
    ?probe_poll_ms(PollMs);
    .wait(PollMs);
    ?lab_artifact(LabId);
    readLabStatusTimed(ZLn, _SR, Tickn)[artifact_id(LabId)];
    if (list_increased(ZL0, ZLn)) {
        Out = Tickn - Tick0
    } else {
        !measure_delay(A, ZL0, Tick0, MaxW, Waited + 1, Out)
    }.
@measure_delay_timeout
+!measure_delay(_, _, _, MaxW, Waited, -1) : Waited >= MaxW <- true.

// Materialise learned per-action delays (seconds) as beliefs for the planner.
@materialise_delays_done
+!materialise_delays([]) <- true.
@materialise_delays_step
+!materialise_delays([A|Rest]) <-
    ?dyn_artifact(DId);
    getDelaySecondsForAction(A, Sec)[artifact_id(DId)];
    +learned_delay_sec(A, Sec);
    !materialise_delays(Rest).

/* ============================================================
 * PHASE B — deadline-aware exploitation
 * ============================================================ */
@exploit_all_done
+!exploit_all([]) <- .print("[Exploit] all time-bounded goals evaluated.").
@exploit_all_step
+!exploit_all([tb_goal(Id, Zone, Target, Deadline)|Rest]) <-
    !exploit_goal(Id, Zone, Target, Deadline);
    !exploit_all(Rest).

@exploit_goal
+!exploit_goal(Id, Zone, Target, Deadline) <-
    !choose_action(Zone, Target, Deadline, ChosenA, Believed, Cost);
    if (ChosenA >= 0) {
        !execute_and_measure(ChosenA, Zone, Target, Deadline, ActualSec, EnergyUsed, Met);
        ?dyn_artifact(DId);
        getDelaySecondsForAction(ChosenA, LearnedSec)[artifact_id(DId)];
        ?active_profile(P); ?mode_label(Mode);
        !action_label(ChosenA, Label);
        recordExploitResult(P, Mode, Id, Zone, Target, Deadline, Label,
                            Believed, LearnedSec, ActualSec, EnergyUsed, Met)[artifact_id(DId)];
        .print("[Exploit] ", Id, " zone ", Zone, " >=", Target, " in ", Deadline,
               "s -> ", Label, " (believed ", Believed, "s) actual=", ActualSec,
               "s energy=", EnergyUsed, " met=", Met)
    } else {
        .print("[Exploit] ", Id, " — no feasible actuator; skipped.")
    }.

// Choose the lowest-energy actuator that (believes it can) reach the target in
// time. Sort key = key(Infeasible, Cost, BelievedDelay, ActionId): feasible
// before infeasible, then cheapest, then fastest. .min picks the best.
@choose_action
+!choose_action(Zone, Target, Deadline, ChosenA, Believed, Cost) <-
    ?use_dynamics_kg(UseKg);
    .findall(key(Infeas, C, B, A),
             ( action_effect(A, Zone, FR) & FR >= Target
             & action_cost(A, C)
             & believed_delay(A, UseKg, B)
             & key_infeas(B, Deadline, Infeas) ),
             Keys);
    !pick_key(Keys, Zone, Target, ChosenA, Believed, Cost).
@pick_key_ok
+!pick_key(Keys, _, _, ChosenA, Believed, Cost) : Keys \== [] <-
    .min(Keys, key(_Infeas, Cost, Believed, ChosenA)).
@pick_key_empty
+!pick_key([], Zone, Target, -1, 0, 0) <-
    .print("[Exploit] WARNING: no candidate actuator reaches zone ", Zone,
           " rank ", Target).

// Execute the chosen actuator from a fresh baseline and measure the ACTUAL
// time-to-target. met=1 iff the target rank is reached within the deadline.
@execute_and_measure
+!execute_and_measure(A, Zone, Target, Deadline, ActualSec, EnergyUsed, Met) <-
    ?lab_artifact(LabId); ?qlearner_artifact(QlId);
    ?active_profile(P); ?probe_baseline(P, BKeys, BVals);
    ?probe_settle_ms(SettleMs); ?probe_max_wait_ticks(MaxW); ?seconds_per_tick(SPT);
    setLabStateFromMap(BKeys, BVals)[artifact_id(LabId)];
    .wait(SettleMs);
    readLabStatusTimed(_ZL0, _SR0, Tick0)[artifact_id(LabId)];
    actionToWoT(A, WotType, WotValue)[artifact_id(QlId)];
    invokeAction(WotType, WotValue)[artifact_id(LabId)];
    !measure_target(Zone, Target, Tick0, MaxW, 0, ReachTicks);
    readEnergyCost(EnergyUsed)[artifact_id(LabId)];
    if (ReachTicks >= 0) {
        ActualSec = ReachTicks * SPT;
        if (ActualSec <= Deadline) { Met = 1 } else { Met = 0 }
    } else {
        ActualSec = -1.0;
        Met = 0
    }.

// Poll until the target zone reaches the target rank (delay in ticks) or timeout.
@measure_target_hit
+!measure_target(Zone, Target, Tick0, MaxW, Waited, Out) : Waited < MaxW <-
    ?probe_poll_ms(PollMs);
    .wait(PollMs);
    ?lab_artifact(LabId);
    readLabStatusTimed(ZLn, _SR, Tickn)[artifact_id(LabId)];
    Idx = Zone - 1;
    .nth(Idx, ZLn, Rank);
    if (Rank >= Target) {
        Out = Tickn - Tick0
    } else {
        !measure_target(Zone, Target, Tick0, MaxW, Waited + 1, Out)
    }.
@measure_target_timeout
+!measure_target(_, _, _, MaxW, Waited, -1) : Waited >= MaxW <- true.

/* ============================================================
 * Shutdown
 * ============================================================ */
@dynamics_finish
+!dynamics_finish <-
    .print("[Dynamics] run finished — stopping MAS.");
    .wait(200);
    .stopMAS.
