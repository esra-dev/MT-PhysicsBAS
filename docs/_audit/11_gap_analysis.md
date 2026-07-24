# 11 — Gap Analysis: Requirements (10_requirements.md) × Implementation × Evidence

**Generated:** 2026-07-07 · branch `phase2-instant-blacklist` @ `ba0303e`
**Inputs:** `docs/_audit/10_requirements.md` (REQ-1…REQ-54) and `docs/_audit/00–05*.md`, plus
targeted verification greps into `src/agt/illuminance_controller_agent_adapt.asl`,
`docs/phase1_results_n10.md`, `docs/PHASE1_TO_PHASE2_CHANGES.md`, `docs/PHASE2_TO_PHASE3_CHANGES.md`,
`docs/PHASE2_5B_BEST_EFFORT_DEGRADATION.md`, `docs/phase1_xzone_bumped_analysis.md`, and `git log`.
**Era:** all implementation/evidence rows below are **NEW era** (phase-based approach) unless
explicitly marked [OLD]. OLD-era numbers (custom8/custom9, W1–W6, pre_registration) are never used
as evidence for a REQ.

**Verdict rules applied:** KEEP = implementation AND supporting result both cited.
ADJUST = implemented but result weak/mixed OR design deviates from the advisor's framing.
MISSING = no implementation found.

**Canonical evidence runs** (from `docs/_audit/05_results_index.md`):
Phase 1 headline = run 27336756264 (`phase1_kg_only`) + `phase1` run, both in `docs/phase1_results_n10.md`;
cross-zone A/B = runs 27440842780 / 27461188614; Phase 2 = runs 28590019536 (§20) + 28745352239 (§21)
+ 28866807391 / 28884717500 (Phase 2.5b, commits `71d5798` / `ba0303e`); Phase 3 = run 27621106006 (§19.4).

---

## A. Cross-cutting / meta (REQ-1 … REQ-4)

| REQ | Where implemented | Evidence it works | Verdict | Note |
|---|---|---|---|---|
| REQ-1 (follow 3-phase redirection) | NEW pipeline: `phase1.yml`/`phase2.yml`/`phase3.yml` (00_inventory §D.2–D.4), agents `_ql`/`_adapt`/`_dynamics` (03 §1.2/1.4/1.5), labs lab1–lab3 + faulty + `_slow` (04 §1–§3) | Each phase has a completed confirmatory CI run: 27336756264 (P1), 28590019536+28745352239 (P2), 27621106006 (P3) — 05 §7 | **KEEP** | Phase 4 (lab4/lab5/LLM, `phase4.yml`) is **beyond the advisor's Phase 1–3 scope** — see §E below. |
| REQ-2 (tests test the aims) | Pre-registered endpoints per phase: `auc_goal` primary (phase1_results_n10.md#L56), `RecoveryEpisodes = Reconverge−Detect` (QLearner.java#L1437-L1474, 02 §8), delay accuracy + deadline compliance (02 §10) | Phase-2 instrument was *fixed* to match the aim: accumulation detector removed, recovery is now pure re-learn speed (PHASE1_TO_PHASE2_CHANGES.md §20.6.1) | **ADJUST** | Residual validity flags: `action_delay_ms(65)` contradicts its own ">200 ms tick" comment (illuminance_controller_agent_ql.asl#L56, 03 §1.2); `*_lowsun` sun-pinning affects only training resets, benchmark scenarios reused from clean parents (04 §6.5); stale labmon "backup lamp" comments (04 §6.1). None invalidates a headline, but each needs a fix or a written caveat. |
| REQ-3 (defendable results) | n=10 seeds, paired bootstrap 95 % CI, BH-FDR, Wilcoxon signed-rank, Cliff's δ in every phase analysis script (`sweep_report.py`, `phase2_recovery.py`, `phase3_dynamics.py` — 05 §1–§3) | Honest scoping is already practiced: lab3 first-goal regression reported as a blemish (phase1_results_n10.md#L174), Tier-1/Tier-2 recovery stratification with disclosed precision boundary (PHASE1_TO_PHASE2_CHANGES.md §21.7.0/§21.7.4) | **KEEP** | Defendability depends on keeping the honest caveats (lab3, Tier-2, labmon-null) in the thesis text. |
| REQ-4 (ANTI: no "adapt around deliberate errors") | NEW Phase 2 = recognize → discard → alert → re-learn (02 §9); clean policy frozen until first fault observation (PHASE1_TO_PHASE2_CHANGES.md §20.6) | The old "work-around" behaviour is structurally impossible: blacklisted actions are removed from the applicable set (QLearner.java#L2517-L2537) | **KEEP** | [OLD] W1–W6 weakness-lab code, `sweep-*.yml`, `pre_registration.md` still exist in-tree (00 §D.6–D.8). Keep only as labelled history; do not cite their numbers. |

---

## B. Phase 1 — clean labs (REQ-5 … REQ-26)

| REQ | Where implemented | Evidence it works | Verdict | Note |
|---|---|---|---|---|
| REQ-5 (written re-evaluation) | `docs/phase1_results_n10.md` (runs 27336756264, 27344626272, 27342571251; 05 §1.2) | Document exists with per-lab result tables, CIs, q-values, synthesis (§3–§11) | **KEEP** | This is the advisor's "(re-)evaluation … put short description and result table(s)" deliverable. |
| REQ-6 (faster to goal) | KG prior machinery: init penalty/bonus + soft priors + decay/fade (01 §C.1–C.2, QLearner.java#L2539-L2620) | lab2: `auc_goal` +0.0193, q=0.000, δ=+1.00; first goal −26.5 ep (phase1_results_n10.md#L104-L105). **lab3: first goal +38 ep LATER (phase1 run, #L140); +42.6 ep, q=0 in `phase1_kg_only` (#L325)** | **ADJUST** | Honest mixed result: clean win on lab2, regression on lab3 speed-to-first-goal (final policy still better). Cross-zone A/B removes the lab3 penalty (`auc_goal` −0.0089 q=0.0072 → n.s., phase1_xzone_bumped_analysis.md#L128) but only by changing the lab3 physics (bleed 50→150 lux). Thesis must report lab3 as mixed, not a clean win. |
| REQ-7 (fewer redundant actions) | Same prior machinery; `avg_redundant` metric in benchmark (03 §2.3) | lab2: 2.15→1.49 (−30 %, phase1_results_n10.md#L97/#L120); kg_only lab2: −1.209, q=0.000, δ=−0.91 (−45 %, #L295); lab3 (phase1 run): 2.28→1.86 (#L131) | **ADJUST** | Holds on lab2 (strong) and lab3 in the `phase1` run, but in the `phase1_kg_only` arm lab3 redundant is +0.513 n.s. worse (#L335). Arm-dependent on lab3. |
| REQ-8 (same goal-success) | Bench `goal_rate` endpoint (05 §1.3 tables) | "Goal-success is never worse in any lab (tie in lab1, higher in lab2 and lab3)" (phase1_results_n10.md#L176-L177); lab3 +0.031, q=0.023 (#L146) | **KEEP** | Advisor's "same success" is met and exceeded (equal-or-better in all labs, both run families). |
| REQ-9 (short description + tables) | `docs/phase1_results_n10.md` §3 per-lab tables + §4 synthesis table | Tables verified present (#L70-L177) | **KEEP** | — |
| REQ-10 (anchor finding) | phase1_results_n10.md frames it as the anchor (#L36, §4) | Anchor demonstrated with n=10, primary endpoint pre-declared (#L184) | **KEEP** | Anchor rests primarily on lab2; lab3 is the disclosed blemish (REQ-6). |
| REQ-11 (clean lab fully aligns with KG) | Deterministic physics, no PRNG in env tick, sun pinned per episode (04 §0); self-contained `building_*.ttl` per lab (01 Part A) | lab2/lab3 physics terms all have KG counterparts (04 §1.2–1.3 vs 01 §A.2/A.5) | **ADJUST** | **lab1 has an un-modelled free ambient term `0.10·sun`** (simulator_flow_lab1.json#L130, flagged 04 §6.2) with no KG mechanism and no blind — a small unmodelled behaviour in the lab that is supposed to have none (90 lux max; does not change reachable rank). Either model it in `building_1_trivial.ttl` or remove it from the flow. |
| REQ-12 (two fresh agents, same lab) | `phase1.yml` train matrix `stereo ∈ {true,false}` × profile × seed (00 §D.2); `use_stereotypes` toggle (03 §1.2); zero-init when stereo off (QLearner.java#L439-L449) | 27336756264 success: lab1/lab2/lab3 × both arms × 10 seeds (05 §1.2) | **KEEP** | Arms use different base seeds by design (QLearner.java#L373, 02 §7); pairing is by `run.seed`. |
| REQ-13 (KG agent learns better) | Same as REQ-6/7/8 | lab2 all legs ✓; lab3 mixed (phase1_results_n10.md §4 synthesis table #L165-L177) | **ADJUST** | Identical caveat to REQ-6: true on lab1(null)/lab2, mixed on lab3. |
| REQ-14 (best research practices) | Factorial arms A–D isolating KG vs PBRS vs trust (run_config.json profiles, 00 §E); seeded SplitMix64 reproducibility (02 §7); config-driven pipeline | Negative control (arm A) confirms nulls (phase1_results_n10.md#L568-L575: all `auc_goal` diffs null when prior zeroed) | **KEEP** | The ablation/negative-control design is a genuine strength; keep it in the methods chapter. |
| REQ-15 (statistical significance) | `sweep_report.py`: paired bootstrap + BH-FDR + Wilcoxon + Cliff's δ (05 §1.3) | lab2 primary q=0.0000, δ=+1.00 (phase1_results_n10.md#L104) | **KEEP** | n=10 ≥ the n≥6 Wilcoxon floor noted in phase1.yml inputs (00 §D.2). |
| REQ-16 (simple lab first) | lab1: 1 zone, 1 lamp, 8 states (04 §1.1, building_1_trivial.ttl) | lab1 saturated/null exactly as designed (phase1_results_n10.md#L66-L87) | **KEEP** | Null is the *expected* floor — document it as such. |
| REQ-17 (progress to 2-zone + spillage) | lab2 (2 independent zones + blinds), lab3 (cross-zone spill + shared spotlight) (04 §1.2–1.3) | Both labs ran to completion in every Phase-1/2 CI run (05 §1, §2) | **KEEP** | — |
| REQ-18 (trivial fast-converging start) | lab1 8 states, 1000 episodes, ε-decay 0.9920 (03 §5 table) | Both arms goal_rate 1.000 (phase1_results_n10.md#L72) | **KEEP** | — |
| REQ-19 (increase complexity *until it fails* → define weaknesses → Phase 2) | The ladder does expose a failure mode: KG-only regresses on lab3 first-goal (phase1_results_n10.md#L307-L339); init-bonus sweep characterizes the cause (#L410-L525) | Failure characterized (optimistic init bonus over-explores 2048 states) and remedied two ways (PBRS companion §11; cross-zone magnitude A/B) | **ADJUST** | The failure found (prior-tuning/exploration cost) is **not** the same "weakness" family Phase 2 tests (component faults). The thesis narrative must bridge this explicitly: complexity-failure (lab3 speed) motivates *characterisation*, while the fault labs motivate Phase 2. As written the transition is implicit. |
| REQ-20 (blind stereotype IV/MV/DV) | `ws:pm_daylight_ingress`: IV=`ws:outdoorIlluminance`, MV=`ws:blindApertureRatio`, DV=`elem:luminiscence` (building_3_complex.ttl#L89-L94, 01 §A.2) | Parsed into `ActionInfo.hasIV/ivStateVecIndex/ivMinRank` (StereotypeReasoner.java#L568-L578, 01 §B.2) | **KEEP** | Exactly the advisor's variable naming. |
| REQ-21 (blind effect only above sun threshold) | Sim physics: blind term `0.50·sun` (zero at sun=0; rank-moving only at high sun) (04 §1.2); prior Rule 2 IV gate (01 §C.1) | Blind labs solved: lab2 goal_rate 1.000 (phase1_results_n10.md#L93); Phase-2 blind adjudication requires sun rank ≥2 and works (§21.7.1) | **KEEP** | — |
| REQ-22 (threshold NOT in KG; agent learns it) | KG asserts only `ws:ivMinRank 1` (structure); per-rank effectiveness learned via `ivTrialCount/ivSuccessCount`, `isIVSatisfied` ≥0.05 with ≥10 samples (01 §C.3–C.4); persisted in `iv_stats_*.json` | Learned IV gate drives the runtime prior and carries train→bench (01 §C.4 step 4); functionally validated by lab2 headline + 100 % blind-fault detection under the learned sun gate (§21.7.1) | **KEEP** | Note for the write-up: a *coarse* prior (`ivMinRank 1`) **is** in the KG; the operative numeric threshold (which sun rank actually works) is learned. This matches "structure in KG, values learned" if stated precisely. |
| REQ-23 (lab3 cross-zone spillage) | Physics: lamp +150 into other zone, blind 0.40·sun cross, spotlight +150 both (simulator_flow_lab3.json#L130, 04 §1.3) | Deterministic, verified against flow JSON (04 §0) | **KEEP** | — |
| REQ-24 (RL learns cross-zone from observation) | Q-learning over full state incl. both zones (VDN decomposition, 02 §1.2); `StereotypeLearner` Welford effect discovery per (action, slot) (03 §2.4) | `learned_stereotypes_true_lab3.ttl`: e.g. SetSpotlight→slot0 meanDelta 1.405, z=10.28, n=37 (01 §A.8) — cross-zone effects discovered with significance tests | **KEEP** | — |
| REQ-25 (spillage as structure in KG, no values) | Reified `elem:InternalConnection` arcs with `ws:WeakOpticalCoupling`; "gain/magnitude intentionally ABSENT — learned by the Q-agent" (building_3_complex.ttl#L349-L350, 01 §A.5) | `CROSS_ZONE_FEEDS_QUERY` reads it → PRIMARY/SECONDARY `CrossZoneEffect` (StereotypeReasoner.java#L145-L167, 01 §B.2) | **KEEP** | Exactly the advisor's "what affects what, not actual values". |
| REQ-26 (KG wins *because* it knows spillage) | `stereo.crossZoneBonus` prior Rule 6 (01 §C.1) + `phase1_kg_xzone` arm (00 §E) | As-is physics: **no** KG spillage advantage (lab3 penalty, phase1_xzone_bumped_analysis.md#L128 control column). Bumped physics + bonus 3.0: penalty removed but win is **n.s.** (`auc_goal` −0.00375, q=0.296, ceiling effect #L113/#L149-L172) | **ADJUST** | Not demonstrated as a positive result. Default `cross_zone_bonus = 0.0` (00 §E learning table) means the headline arms never *use* the spillage knowledge. Options: adopt the doc's own suggestion of an intermediate spill magnitude that is "helpful but not trivialising" (#L175-L177), or reframe the claim as "structure knowledge does not hurt and removes the penalty once spillage is learnable". |

---

## C. Phase 2 — weakness labs (REQ-27 … REQ-47)

| REQ | Where implemented | Evidence it works | Verdict | Note |
|---|---|---|---|---|
| REQ-27 (no work-around of faults) | Blacklist removes BOTH polarities of the faulty component; blacklisted actions excluded from applicable set and bootstrap (QLearner.java#L1306-L1346, #L2517-L2537; 02 §9) | Re-learning happens strictly over survivors: e.g. lab3_f1dead recovers via {Z2Light, Spotlight} path (§21.7.0 physics derivation) | **KEEP** | — |
| REQ-28 (recognize unexpected behaviour of policy action) | `observeForFaults` after every adapt step: dispatched action's KG prediction vs observed transition, DEAD/INVERTED verdicts (QLearner.java#L1078-L1253, 02 §9; wired in `@do_step_adapt`, 03 §1.4) | Detection recall 100 % in all 18 lamp cells (§20.6.2) and all 4 blind cells (§21.7.1); DetectEpisode ≈ 0 both arms (§20.6.1) | **KEEP** | **WITHDRAWN 2026-07-22; corrected 2026-07-24 (protocol v2, detector v2): recall is NOT 100% and is policy-dependent — KG-arm dead-lamp detection is 0/20 in every cross-coupled lab3 cell (maskability abstain); inverted faults and all lab1/lab2 cells detect perfectly in both arms; zero false positives anywhere. Current record: `docs/thesis_chapter_phase2.md` §10.** |
| REQ-29 (recheck with physics knowledge) | The detector *is* the physics recheck: per-step comparison against the KG-derived claim set (falsifiable zones, IV gates, structural guards) (02 §9 detection paragraph) | Structural guards (multi-zone feeder spared, IV-gated blinds adjudicated only under sun ≥2, contaminated zones skipped) produce 0 false positives on all confirmatory cells (§20.6.2, §21.7.4 Tier-1: 10/10 clean) | **KEEP** | **WITHDRAWN 2026-07-22; corrected 2026-07-24: detector v2's structural-maskability abstain achieves zero false-positive blacklist events in all 38 cells × 20 replicas × both arms — the FP claim becomes true — but recall becomes policy-dependent (KG-arm dead-lamp detection 0/20 in cross-coupled lab3 cells). Current record: `docs/thesis_chapter_phase2.md` §10.** |
| REQ-30 (discard the artifact) | `blacklistComponent` (QLearner.java#L1306-L1346, 02 §9) | Blacklisted component named in `DefectComponent` column of `recovery_log_*.csv`; exactly the injected component on every confirmatory cell (§20.6.2) | **KEEP** | — |
| REQ-31 (**alert the user**) | Adapt agent `@on_defect_new`: `.print("   [FAULT] DEFECTIVE component detected: ", Comp)` + `+defective(Comp)` belief (illuminance_controller_agent_adapt.asl#L384-L388; header contract #L15-L18 "the agent ALERTS the user (MAS console + belief"); degraded-mode alert `*** USER NOTIFIED. ***` (#L464) | Fault + degraded alerts fire in every detected cell (detection 100 %, §20.6.2/§21.7.1); defect label persisted to recovery CSV (#L525, PHASE2_5B #L155) | **KEEP** | The "user" channel is MAS console + belief + CSV column — adequate for the thesis claim, but say so explicitly (no external notification service). |
| REQ-32 (re-learn with AND without physics) | `phase2.yml` adapt matrix `mode ∈ {ql_true, ql_false}` (00 §D.3); warm restart re-learn loop (02 §9) | 180 adapt runs (§20.6), 160 more (§21.7), both arms everywhere | **KEEP** | — |
| REQ-33 (KG realigns better/faster) | KG priors re-weighted after warm restart (`currentEpisodeNum = 0` resets decay clock, QLearner.java#L1389) | **Five significant Tier-1 cells:** lab3_f1dead −204.9 ep = 2.49× (q<0.001, δ=−0.72, §20.6.3); lab3_f1dead_z2 −95.7 (q<0.001, δ=−0.84); lab3_f1bdead 7.9×; lab3_f1binv 9.4×; lab2_f1bdead 4.2× (all q≤0.002, §21.7.2–21.7.3). **Plus 2 degraded-mode replications:** lab3_f2dead_lowsun 1.9× (run 28866807391, commit `71d5798`), labmon2_f2dead_lowsun 1.68× (run 28884717500, commit `ba0303e`) | **KEEP** | Scope honestly: Tier-2 inverted cells n.s.; single-survivor `labmon_f1dead` shows **no** KG advantage (arms statistically tied, PHASE2_5B #L215-L219) because with one lever there is nothing to search — that null is explainable and should be reported. |
| REQ-34 (pre-trained on clean labs) | `phase2.yml` `train_clean` job generates clean Q-tables per (parent, arm, seed); adapt warm-loads them (00 §D.3; illuminance_controller_agent_adapt.asl#L175-L185) | Every confirmatory adapt run warm-started from its lab's clean Phase-1 Q-table (§20.6, §21.7 design paragraphs) | **KEEP** | — |
| REQ-35 (NO threshold counter; immediate adaptation) | Phase 2.3: evidence-accumulation thresholds (`fault.detect.minSamples/deadRate/invRate/anomalyRate`) **removed** — deletion recorded in code comment (QLearner.java#L306-L310); blacklist on first unambiguous anomaly (#L257-L281, #L1238-L1252; 02 §9) | DetectEpisode ≈ 0 for both arms in all 9 lamp cells (§20.6.1 table); the old detector's 90.5-vs-16.8-episode artefact dissolved (§20.6.1) | **KEEP** | This is the advisor's exact demand, verified absent from the current tree (02 "NOT FOUND" section). |
| REQ-36 (complete blacklist immediately + triggers relearn) | `blacklistComponent` → `warmRestart` in the same step; ε-boost 0.30, Q-wipe of blacklisted columns, poisoned-state decay, detector resets (QLearner.java#L1362-L1411, 02 §9; 03 §1.4) | Recovery measured from that instant; 10/10 reconvergence on dead-fault Tier-1 cells (§21.7.2) | **KEEP** | Deviation to note: the **last surviving actuator action is protected** from removal (#L1317-L1327), so in the degenerate lab1_f1dead the dead lamp cannot be fully removed — the cell is documented as detect-and-alert-only (lab_profiles.asl#L470-L472, 04 §2.1). |
| REQ-37 (fault matrix: 1 dead / several dead / 1 faulty / several faulty) | (a) `lab{1,2,3}_f1dead`; (b) `lab{2,3}_f2dead`; (c) `lab{2,3}_f1inv` (inverted = works but does the wrong thing); (d) `lab{2,3}_f2inv` (04 §2.1–2.2 tables, generator `generate_faulty_flows.ps1`) | All ran in confirmatory CI: 9 profiles × 2 × 10 (§20.6), recall 100 % everywhere | **KEEP** | — |
| REQ-38 (each fault type × each complexity lab1/lab2/lab3) | Full grid for lab2/lab3 (dead/inv × 1/2 components × lamp/blind); **lab1 has only `lab1_f1dead`** (04 §5 matrix) | lab1_f1dead ran (§20.6) | **ADJUST** | Multi-component faults are structurally impossible in lab1 (one actuator), but a `lab1_f1inv` (inverted single lamp) is possible and absent. Either add it or state the structural-coverage argument explicitly in the thesis. |
| REQ-39 (pre-trained on clean version of *that same* lab) | `adapt_source/2` maps every faulty profile to its clean parent's Q-table suffix (lab_profiles.asl#L817-L838, 03 §5; full mapping 04 §5) | Warm-load filename = `qtable_final_stereotypes_<bool><CleanSuffix>.csv` (03 §1.4) | **KEEP** | — |
| REQ-40 (blind faults detected + blacklisted like lamps) | `lab3_f1bdead`, `lab3_f1binv`, `lab2_f1bdead`, `lab2_f1binv` (04 §2.3); active diagnostic probe opens untested blinds under adequate sun (QLearner.java#L1011-L1047, 02 §9) | detection_rate = 1.00 in all 4 blind cells, both arms; DetectEpisode ~6–8 (§21.7.1); 3 of 4 cells show significant KG recovery advantage 4.2–9.4× (§21.7.2) | **KEEP** | The active self-test converts a previously undetectable off-policy fault into one caught within episodes — a highlight worth a thesis subsection. |
| REQ-41 (monitor stereotype in KG) | `ws:pm_monitor_operation` in `building_6_monitor.ttl#L112-L128` (01 §A.6); dual-zone variant `building_7_dualmonitor.ttl` | Discovered as exactly one ON/OFF pair via Illuminance DV filter (01 §A.6); `MonitorKgDiscoveryTest.java` exists (PHASE2_5B #L251) | **KEEP** | — |
| REQ-42 (MV electricity, several DVs) | MV=`ws:monitor_power_input`, DVs=`ws:displayed_information` + `elem:luminiscence` (building_6_monitor.ttl#L112-L128) | Multiple-DV structure verified in TTL (01 §A.6 quote) | **KEEP** | Two DVs — matches "several dependent variables (output)". |
| REQ-43 (light is side-effect, not main effect) | Primary DV = displayed_information ("NOT Illuminance → not actuated as a light"); luminiscence commented as SIDE-EFFECT (01 §A.6) | Reasoner keeps only the Illuminance DV, so the monitor still surfaces as a *weak* light action (01 §A.6) | **KEEP** | — |
| REQ-44 (monitor as emergency fallback) | `labmon`/`labmon_f1dead` (monitor 260 lux → 285 = rank 2 max) and `labmon2`/`labmon2_f2dead_lowsun` (04 §2.4) | labmon_f1dead: agent adopts monitor, reaches degraded rank 2 (run 28863439179, 05 §2.2); labmon2_f2dead_lowsun: greedy goal-rate 0.99 (KG) vs 0.925 with 1.68× KG recovery speed-up (run 28884717500, commit `ba0303e`) | **KEEP** | The fallback works in both arms; the KG *speed* advantage appears only in multi-survivor labs (see REQ-33 note). |
| REQ-45 (monitor NOT modelled as more costly) | Cost-based design explicitly removed: `ws:rewardEnergyCost` deleted from the TTL, `REWARD_ENERGY_INIT_WEIGHT` removed (PHASE2_5B #L3-L27, #L181, #L241-L246); monitor made physically *weak* instead | labmon energy accounting (monitor 3/tick) is "informational only; does NOT affect the reward" (simulator_flow_labmon.json#L130 comment, 04 §2.4) | **KEEP** | The redesign doc records the advisor's exact rationale ("'the monitor is costly' is a fiction"). |
| REQ-46 (unreachable goal → best effort + inform user) | Phase 2.5b: deterministic reachability probe over 2^k survivor combos → `effectiveGoal[zone]` lowered to closest achievable rank (QLearner.java#L1649-L1729, 02 §9); `+degraded_mode` belief + `[DEGRADED] Goal rank N UNREACHABLE — best effort rank …` + `*** USER NOTIFIED ***` (adapt.asl #L435-L464, PHASE2_5B #L135-L141); CSV columns `NominalGoal, BestEffortRank, RankShortfall, DegradedMode` (PHASE2_5B #L155-L158) | Three degraded cells validated in CI: labmon_f1dead (285→rank 2, run 28863439179), lab3_f2dead_lowsun (265→rank 2, 1.9×, run 28866807391), labmon2_f2dead_lowsun (275→rank 2, 1.68×, run 28884717500) | **KEEP** | Proof-gated: degradation happens only when the probe *proves* unreachability; `effectiveGoal == goal` in all other cells (PHASE2_5B #L93-L97), so clean results are untouched. |
| REQ-47 (monitor gets as-close-as-possible, not to goal) | labmon_f1dead ceiling 25+260 = 285 lux = rank 2 < rank-3 goal (04 §2.4, generate_faulty_flows.ps1#L104-L108) | Agent re-learns toward rank 2 and holds it (`RecoveredGoalRate` measured against `effectiveGoal`, PHASE2_5B #L161-L163) | **KEEP** | The "lamps dead + blinds useless (dark outside)" example is realised by `labmon2_f2dead_lowsun` (sun pinned 100 → blind adds only 50 lux, 04 §2.4). |

---

## D. Phase 3 — process dynamics (REQ-48 … REQ-54)

| REQ | Where implemented | Evidence it works | Verdict | Note |
|---|---|---|---|---|
| REQ-48 (learn process dynamics) | `DynamicsLearner.java` Welford per-action delay estimator; `_slow` labs with 12-tick blind lag (02 §10; 04 §3) | Run 27621106006 (n=10): learned blind delay 12.11–12.21 ticks vs truth 12, rel err ≤1.77 %; 100 % response-class accuracy (PHASE2_TO_PHASE3_CHANGES.md §19.4) | **KEEP** | — |
| REQ-49 (simple implementation: learn response times, e.g. blinds) | Probe protocol: pin baseline → toggle one actuator → poll sim `Tick` until rank reached, 8 probes/actuator (02 §10; agent 03 §1.5) | Blind (delayed, 60 s) vs lamps (~1.14 ticks, instantaneous) cleanly separated (§19.4 delay table) | **KEEP** | Advisor sanctioned "a simple implementation"; the dedicated probe agent (no Q-table training, 03 §1.5) is that. State in the thesis that the delay is measured by controlled probing, not by TD updates. |
| REQ-50 (add learned knowledge back to KG) | `saveLearnedDynamics` writes `learned:ResponseDynamic` Turtle with `ws:responseDelay` (seconds), ticks, samples, class (DynamicsLearner.java#L176-L230, 01 §A.8) | `learned_dynamics_true_lab2_slow.ttl`: `ws:responseDelay "60.0000"`, 12 ticks, class DelayedResponse (01 §A.8 example) | **KEEP** | — |
| REQ-51 (new KG variable "Response Delay", learner finds its value) | `ws:responseDelay` datatype property declared in `building_2_slow.ttl#L80-L101` — "LEARNABLE, deliberately given no value" (01 §A.7) | Learned value = **60.0 s for the blind** — literally the advisor's "60 seconds response delay" example (01 §A.8; ground truth 12 ticks × 5 s/tick, run_config.json phase3 block) | **KEEP** | The KG asserts only the qualitative class (`ws:hasResponseDynamic`, no Java reader — documentary, 01 Part D); the magnitude is 100 % measured. |
| REQ-52 (optional: temporal goals) | `tb_goal/4` goals g1–g6, deadlines 15/45/90/300 s; `believed_delay` planner rule: KG arm plans with learned delay, tabula-rasa assumes 0 (illuminance_controller_agent_dynamics.asl#L83-L99, 03 §1.5) | Run 27621106006: tight compliance **1.00 (ql_true) vs 0.00 (ql_false)**, overall 1.00 vs 0.50, p_wilcoxon=0.00195 (exact n=10 floor), δ=1.00, q=0 on both profiles (§19.4) | **KEEP** | The optional extension is fully delivered and is the strongest single result in the project. |
| REQ-53 (framing: stereotypes lack dynamics) | Stereotype vocabulary has no delay magnitude by design (01 §A.7); zero-delay assumption is the ql_false arm's belief (03 §1.5) | The agent *without* dynamics knowledge fails every tight deadline (tight compliance 0.00, §19.4) — the gap the framing requires | **ADJUST** | The mechanism and evidence exist, but the advisor's specific framing ("we let the agent fail in the weakness lab due to introducing dynamics **in part 1**") is not how the repo tells it: dynamics failure is demonstrated in Phase 3's `_slow` labs, not in Phase 1/2 weakness labs. Fixable purely in thesis text — align the narrative, no code change needed. |
| REQ-54 (dynamics = actuation→effect delays) | `stepBlind` countdown: commanded flag becomes effective aperture after DELAY=12 ticks ≈ 60 s (simulator_flow_lab2_slow.json#L130, 04 §3) | Matches the advisor's "light turns on after a one-minute delay" definition (blind variant) | **KEEP** | Only blinds are delayed; lamps/spotlight instantaneous — a reasonable single-mechanism instantiation. |

---

## E. Out-of-scope flag — Phase 4 (lab4 / lab5 / LLM baseline)

Phase 4 (smart-plug hidden dependency lab4, energy-differentiation lab5, `phase4.yml`, energy prior,
LLM baseline `phase4_llm_baseline.py`; 00 §D.5, 04 §4, 05 §4) maps to **no REQ** in
`10_requirements.md`. The advisor's redirection defines exactly three phases. 04 §4 already carries
the flag "EXTENSION, NOT REQUIRED BY THE ADVISOR'S PHASE 1–3 GOALS". Verdict: **keepable as a
clearly-labelled extension chapter/appendix** (it has certified n=20 results, run 27905392725), but
it must not be presented as satisfying any Phase 1–3 requirement, and it must not displace thesis
space needed for the REQ-6/REQ-26 honest caveats.

---

## F. Summary lists

### KEEP-AS-IS (45)
- REQ-1 — three-phase pipeline implemented with confirmatory runs per phase
- REQ-3 — statistical machinery + honest scoping practiced
- REQ-4 — old "adapt-around-errors" approach structurally replaced
- REQ-5 — written re-evaluation exists (phase1_results_n10.md)
- REQ-8 — goal-success equal-or-better in every lab
- REQ-9 — short description + result tables delivered
- REQ-10 — anchor-finding framing in place
- REQ-12 — fresh KG-primed vs tabula-rasa arms in same clean lab
- REQ-14 — factorial arms + negative control = best-practice design
- REQ-15 — bootstrap/BH/Wilcoxon/δ with n=10
- REQ-16 — lab1 simple-lab floor
- REQ-17 — complexity ladder to 2-zone spillage lab
- REQ-18 — trivial fast-converging start
- REQ-20 — blind stereotype IV/MV/DV exactly as specified
- REQ-21 — sun-threshold-gated blind effect
- REQ-22 — threshold learned (only coarse structure in KG)
- REQ-23 — lab3 cross-zone spillage physics
- REQ-24 — cross-zone effects learned from observation
- REQ-25 — spillage structure (not values) in KG
- REQ-27 — no work-around: faulty components removed from action space
- REQ-28 — instant recognition of unexpected policy-action outcome
- REQ-29 — physics recheck with structural false-positive guards
- REQ-30 — discard/blacklist implemented
- REQ-31 — user alert (console + belief + CSV) confirmed present
- REQ-32 — re-learn with and without physics
- REQ-33 — KG realigns faster: 5 significant Tier-1 cells + 2 degraded replications
- REQ-34 — adapt runs warm-start from clean-trained Q-tables
- REQ-35 — no fault counter; thresholds removed, detection at episode ~0
- REQ-36 — instant complete blacklist triggers warm-restart re-learning
- REQ-37 — dead/inverted × single/multiple fault matrix present
- REQ-39 — each weakness lab warm-starts from its own clean parent
- REQ-40 — blind faults detected (active probe) and blacklisted, 3/4 cells significant
- REQ-41 — monitor stereotype added to KG
- REQ-42 — monitor MV=electricity, multiple DVs
- REQ-43 — light as side-effect, not primary output
- REQ-44 — monitor fallback demonstrated (labmon, labmon2 CI runs)
- REQ-45 — no artificial monitor cost (cost design explicitly removed)
- REQ-46 — proof-gated best-effort degradation + user notification, 3 CI-validated cells
- REQ-47 — monitor reaches rank 2 best-effort below the rank-3 goal
- REQ-48 — process dynamics learned (≤1.77 % delay error)
- REQ-49 — simple probe-based response-time learner
- REQ-50 — learned delays written back to KG (Turtle)
- REQ-51 — `ws:responseDelay` learned as 60 s (advisor's exact example)
- REQ-52 — temporal goals: tight compliance 1.00 vs 0.00, p=0.00195
- REQ-54 — dynamics = actuation-to-effect delays (12-tick blind)

### NEEDS-ADJUSTMENT (9)
- REQ-2 — instruments mostly aligned, but fix/caveat: `action_delay_ms(65)` vs its own comment; `_lowsun` benchmark scenarios unchanged; stale labmon comments
- REQ-6 — faster-to-goal holds on lab2 but lab3 first-goal regresses (+38/+42.6 ep, q=0 in kg_only) — report as honest mixed result
- REQ-7 — fewer redundant actions clean on lab2 (−30 %/−45 %); lab3 arm-dependent (n.s. worse in kg_only)
- REQ-11 — clean-lab/KG alignment broken by lab1's un-modelled `0.10·sun` ambient term — model it or remove it
- REQ-13 — "learns better" overall verdict is lab-dependent (lab2 yes, lab3 mixed) — same caveat as REQ-6
- REQ-19 — complexity-failure → weakness-definition narrative bridge is implicit; make the Phase 1→2 motivation explicit in text
- REQ-26 — KG spillage-knowledge advantage not demonstrated (default cross_zone_bonus=0; bumped A/B removes penalty but win n.s. at ceiling) — rerun with intermediate spill magnitude or reframe claim
- REQ-38 — fault-type coverage incomplete at lab1 complexity: `lab1_f1inv` missing (multi-fault impossible structurally — state that)
- REQ-53 — "stereotypes lack dynamics" framing lives in Phase 3 `_slow` labs, not Phase 1 weakness labs as the advisor phrased it — align thesis narrative (text-only fix)

### MUST-BUILD-NEW (0)
- *(none — every REQ has an implementation; all gaps are adjustments of existing work. The only
  candidate new artefact is the optional `lab1_f1inv` cell under REQ-38, which is an adjustment to
  the existing fault matrix, not a missing requirement.)*
