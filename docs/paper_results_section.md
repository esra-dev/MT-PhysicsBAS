# Results

## Phase 1: Knowledge-guided learning in clean simulated laboratories

Phase 1 was rerun under corrective protocol v2 after the legacy scenario scheduler,
first-goal outcome, and wall-clock energy metric were found to be invalid. Four registered
workflow runs compared the bundled knowledge-graph (KG) prior, a cheap redundancy-only
heuristic, and two label controls across three laboratories and 20 paired seeds. Every cell
used the same declared scenario schedule, zero random fallbacks, and a fixed 3,000-episode
horizon. The current data are runs `29848584965`, `29848587274`, `29848589682`, and
`29848592010`; protocol-v1 results are historical only.

The registered five-test family gives a narrower conclusion than the earlier draft. In
lab2, the KG-prior arm increased the fraction of successful training episodes by
`0.003700` (95% bootstrap CI `[0.002700,0.004917]`, two-sided exact sign-flip
`p=1.91×10⁻⁶`, BH `q=9.54×10⁻⁶`, paired rank-biserial `r=1.00`). The ontology-free
redundancy heuristic produced `+0.002583` (`q=1.72×10⁻⁴`, `r=0.914`). Its mean was 69.8%
of arm C's mean, crossing the registered two-thirds threshold: cheap redundancy information
reproduces **most** of the effect. Arm C still exceeded redundancy by `+0.001117`
(`[0.000767,0.001467]`, `q=7.63×10⁻⁵`, `r=1.00`). Thus the lab2 result supports a small
additional bundled KG-prior effect, but the ontology cannot honestly receive credit for the
whole advantage.

The corrected lab3 outcomes overturn the old headline. The KG arm's mean first-success
difference is only `+0.110` scenario presentations (`[-0.060,+0.305]`, `q=0.304`), and its
cycling difference is `+0.07375` (`[-0.02313,+0.17375]`, `q=0.215`). Neither differs from
zero. The old `+53.30 episode` first-goal regression was dominated by the broken legacy
measurement and is not evidence.

The registered descriptives are mixed. On lab2, arm C improves final benchmark goal rate
by `+0.04875`, reduces steps by `1.33375`, deviation by `3.67313`, deterministic policy
energy by `1.28000`, and cycling by `0.38312`. On lab3, however, its full-horizon training
success fraction is slightly lower (`auc_goal −0.002300`,
`[-0.003467,−0.001067]`). Final benchmark goal rate and cycling do not differ, while
deterministic policy energy is `+1.0744` policy-cost units higher
(`[+0.5981,+1.5394]`). The energy outcome is credible as a deterministic step metric but
is descriptive, uses arbitrary actuator weights, and is not watt-hours.

The baseline and PBRS-only controls are exactly equal between labels for all corrected
training and benchmark outcomes. Only the deliberately retained legacy wall-clock energy
diagnostic varies slightly, confirming why it was withdrawn. Lab1 is a saturated null in
both arm C and redundancy-only.

In short, the corrected experiment supports a small lab2 advantage inside this discrete
simulator. Most of the mean effect comes from cheaply derivable redundancy suppression; a
smaller residual arm-C advantage remains. Phase 1 does not support the old lab3 first-goal
or cycling penalty, but it does expose a small adverse lab3 training-success difference and
a descriptive policy-energy cost. It cannot establish real-building benefit or that a KG
is cheaper than an equivalent hand-coded table.

Source: `docs/phase1_results_v2.md` and
`phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv`.

---

## Phase 1b: Which kinds of prior knowledge change learning?

Phase 1b tested three proposed knowledge-layer mechanisms under a prospectively
frozen protocol: relevance filtering as irrelevant actions are added, resistance
to state fragmentation, and dependency-order knowledge. Four arms separated a
tabula-rasa baseline, an ontology-free redundancy heuristic, the frozen KG
consumer, and an extended KG consumer. The confirmatory campaign used 20 paired
seeds. Five members formed the registered BH family; M5 was prospectively
exploratory under the frozen power rule and was not included in that family.

| Member | Registered contrast | Mean paired statistic | 95% bootstrap CI | Exact sign-flip / BH result | Registered reading |
|---|---|---:|---:|---:|---|
| M1 | frozen-KG relevance slope (`auc_goal` per decoy) | +9.88×10⁻⁶ | [+5.36×10⁻⁶, +1.46×10⁻⁵] | `p=0.0039`, `q=0.0065` | Detectable, about **70× below** the SESOI |
| M2 | incremental relevance slope, extended − frozen | 0 | [0, 0] | `p=1`, `q=1` | New irrelevance channel changed nothing |
| M3 | fragmentation difference-in-differences | +0.0013 | [+0.0010, +0.0016] | `p=1.91×10⁻⁶`, `q=9.54×10⁻⁶` | Detectable, about **8× below** the SESOI |
| M4 | band-mirror channel, extended − frozen `auc_goal` | 0 | [0, 0] | `p=1`, `q=1` | New direction channel changed nothing on the registered endpoint |
| M5 | full extended stack − baseline deviation | −0.1625 | [−0.334, −0.001] | exploratory `p=0.078`; no BH q-value | Underpowered and does not isolate the direction channel |
| M6 | depth-3 chain frozen − baseline first-success RMST | −0.5 presentations | [−0.64, −0.36] | `p=7.63×10⁻⁶`, `q=1.91×10⁻⁵` | Detectable, **50× below** the corrected −25-presentation SESOI |

The Phase-1b conclusion is therefore bounded by the registration's own
scientific thresholds. The frozen KG produced statistically clean relevance,
fragmentation, and dependency-order accelerations, but all three confirmed
effects were 8–70 times smaller than the effects declared thesis-relevant in
advance. M1 had nine positive paired differences and eleven exact ties; it
must not be described as positive in all 20 seeds.

The ontology-free control separates the mechanisms further. Its relevance
slope analogue is null (`−2.4×10⁻⁶`, descriptive `p≈0.46`), so the already tiny
M1 signal is genuinely knowledge-layer rather than redundancy mimicry. By
contrast, redundancy reproduces approximately 60% of M3
(`+0.000783` of `+0.0013`) and 45% of M6 (`−0.225` of `−0.5`). The extended
consumer machinery engaged, but M2 and M4 were identically zero in every
seed. M5 cannot rescue a direction-channel claim: frozen and extended had the
same mean band deviation, and the full-stack exploratory contrast was
underpowered. The registered within-episode overshoot event count was not
present in the run-of-record output and remains explicitly unmeasured.

This result supports a narrow thesis statement: qualitative stereotype
knowledge can create reproducible accelerations in these simulators, but the
observed gains are scientifically small under the registered SESOIs; some
structural gains are partly available from a much cheaper redundancy rule,
and the two newly implemented qualitative channels add no measurable benefit
on their registered members.

Sources: `docs/phase1b_results_2026-07-27.md`,
`docs/phase1b_decision_memo_2026-07-27.md`, and
`phase1b_corrected/analysis/registered/phase1b_registered_family.csv`.

---

## Phase 2: Fault detection, blacklisting, and re-learning

Phase 2 was rerun under protocol v2 after the legacy scheduler, unsettled
start-state record, and detector were found to invalidate the earlier
campaign. The corrected experiment used strict by-position scheduling,
settled start states, protocol-v2 clean parents, a fixed 4,000-episode
adaptation horizon, explicit censoring at horizon plus one, and detector v2.
Four registered dispatches covered 20 paired seeds. The two pre-data failure
rounds are retained in the dispatch record but contributed no result cells.

The registered Tier-1 `RecoveryEpisodes` family contains eight cells
(exact paired sign-flip tests, BH `m=8`). A value of `4001` is the censoring
bound: the fault was not detected during the horizon, so post-detection
adaptation never began.

| Cell | KG mean | Tabula-rasa mean | Mean Δ (KG − TR) | 95% bootstrap CI | BH q | Censored KG / TR | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `lab2_f1bdead` | 58.8 | 151.45 | −92.65 | [−141.80, −50.25] | 1.017×10⁻⁵ | 0 / 0 | Supported |
| `labmon2_f2dead_lowsun` | 184.8 | 353.55 | −168.75 | [−246.30, −92.95] | 0.001148 | 0 / 0 | Supported |
| `lab3_f1dead` | 4001.0 | 1934.6 | +2066.40 | [+1300.75, +2836.45] | 0.001563 | 20 / 9 | **Adverse** |
| `lab3_f1dead_z2` | 4001.0 | 489.0 | +3512.00 | [+3062.70, +3807.80] | 1.017×10⁻⁵ | 20 / 1 | **Adverse** |
| `lab3_f2dead_lowsun` | 4001.0 | 346.85 | +3654.15 | [+3252.00, +3869.65] | 1.017×10⁻⁵ | 20 / 1 | **Adverse** |
| `lab3_f1bdead` | 116.05 | 136.0 | −19.95 | [−76.60, +30.00] | 0.595 | 0 / 0 | Null |
| `lab3_f1binv` | 175.25 | 191.7 | −16.45 | [−82.75, +58.90] | 0.673 | 0 / 0 | Null |
| `labmon_f1dead` | 557.85 | 776.45 | −218.60 | [−653.65, +288.05] | 0.302 | 7 / 10 | Null |

The corrected family therefore contains **two supported, three adverse, and
three null** cells. The three adverse outcomes are detection-censoring
outcomes, not evidence that post-detection re-learning was slower. Detector
v2 abstains from a dead verdict while another actuator could mask the
suspect's contribution. In the cross-coupled lab3 dead-lamp cells, the
knowledge-shaped policy keeps such co-feeders active and never reaches an
unmasked state: KG-arm detection is `0/20` in each cell, versus `11/20`,
`19/20`, and `19/20` detections in the tabula-rasa arm.

Detector v2 removes the opposite failure mode in the withdrawn record:
the complete blacklist-event record contains **zero false-positive
blacklists across 38 cells × 20 replicas × both arms**. That specificity has
a disclosed recall cost. Blind faults are probe-detected identically in both
arms at about episodes 5–6, inverted faults detect at about episode 0 because
opposite-sign evidence is never masked, and all lab1/lab2 faults detect in
both arms. Dead-lamp recall in cross-coupled labs is policy-dependent.

The registered result supports a two-sided conclusion. Knowledge is associated
with faster recovery in the two cells where detection succeeds
(`lab2_f1bdead`, about 2.6× by the arm means, and
`labmon2_f2dead_lowsun`, about 1.9×), but the same policy-shaping knowledge
can suppress the observations
needed to detect dead faults. Detection opportunity and post-detection
re-learning must therefore remain separate stages. The campaign does not
support a universal recovery advantage. The completed Phase-2b-A retrospective
also does not establish the proposed Q-gap mechanism: in the four-cell
clean-detection panel, the primary mean start-state Q-gap proxy had a negative
cell-level ordering with recovery (`ρ = −0.738`, paired-seed stability interval
`[-0.949, −0.211]`), whereas the frozen signed-gap-median sensitivity was
positive (`ρ = +0.600`). This direction instability, four rather than five of
six sighted-reference pairwise concordances, and negative leave-one-cell-out
primary associations caused four of the six prospective-screening gates to
fail. C2 is therefore deferred.

The separate detector-opportunity descriptor is consistent with the corrected
observability boundary: the KG arm had zero deterministic opportunity and
zero detections in all three detector-censored adverse dead-lamp cells, while
TR had nonzero opportunity and detected at least some seeds. That descriptor
is model-based context, not a replay of stochastic adaptation.

Sources: `docs/thesis_chapter_phase2.md` §§4–6,
`docs/phase2_correction_registration_2026-07-22.md`,
`phase2_v2_corrected/analysis/registered/phase2_v2_registered_family.csv`,
`phase2_v2_detection_family.csv`, and
`phase2b_qgap/analysis/PHASE2_QGAP_RETROSPECTIVE_RESULTS.md`.

---

## Phase 3: Learning process dynamics and time-bounded control

Phase 3 asks whether the KG infrastructure can acquire actuator response
delays online and use those learned values for time-bounded control. The
protocol-v2 campaign uses two slow-lab variants (`lab2_slow`, `lab3_slow`).
A motorised blind takes 12 simulation ticks, or 60 simulated seconds, to
settle while lamps and the spotlight are instantaneous. The agent probes each
actuator eight times, estimates its delay, writes the measurement back as
`ws:responseDelay`, and then selects actions for six tight or loose
deadline-constrained goals. The corrected run of record is `29926328852`
with ten replicas per profile and arm.

The corrected delay estimates reproduce the intended measurement result:

| Profile | Arm | Slowest learned delay (ticks) | Ground truth | Relative error |
|---|---|---:|---:|---:|
| `lab2_slow` | zero-delay baseline | 12.1875 | 12 | 1.56% |
| `lab2_slow` | KG learned-delay arm | 12.1250 | 12 | 1.04% |
| `lab3_slow` | zero-delay baseline | 12.1375 | 12 | 1.15% |
| `lab3_slow` | KG learned-delay arm | 12.1750 | 12 | 1.46% |

All lamps and spotlights were classified as instantaneous. The corrected
deadline-compliance and tick-integrated energy descriptives are:

| Profile | Arm | Overall compliance | Tight | Loose | Met goal-attempts | Mean tick-energy | Mean actual delay |
|---|---|---:|---:|---:|---:|---:|---:|
| `lab2_slow` | zero-delay baseline | 0.5000 | 0.0000 | 1.0000 | 30/60 | 0.0 | 60.92 s |
| `lab2_slow` | KG learned-delay arm | 0.9833 | 0.9667 | 1.0000 | 59/60 | 3.7 | 33.83 s |
| `lab3_slow` | zero-delay baseline | 0.5000 | 0.0000 | 1.0000 | 30/60 | 0.0 | 60.50 s |
| `lab3_slow` | KG learned-delay arm | 1.0000 | 1.0000 | 1.0000 | 60/60 | 3.1 | 33.42 s |

The corrected run thus reproduces the practical deadline result with one
deviation from the withdrawn record: one KG-arm replica missed one tight goal
in `lab2_slow`, so that cell is `59/60`, not universally `6/6` in every
replica. The zero-delay baseline missed every tight goal in both profiles.

The inferential boundary is important. The deadline planner is deterministic
given the learned delay table, so compliance is reported as a worked
demonstration with descriptive intervals, not as a hypothesis test. The
tick-integrated energy meter (`tick-v1`) shows the cost of choosing the
instantaneous lamp for tight goals, but energy is registered as descriptive
only: no Phase-3 energy quantity receives a p- or q-value. Legacy cumulative
wall-clock energy is diagnostic and is not evidence.

Sources: `docs/phase3_correction_registration_2026-07-22.md`,
`phase3_v2_corrected/CAMPAIGN_MANIFEST.md`, and the three corrected tables
under `phase3_v2_corrected/run_29926328852/analysis/out/`.

---

## Phase 4: Hidden dependencies and energy-aware goals

Phase 4 is an extension beyond the advisor-defined three phases. Its corrected
protocol-v2 campaign compares the KG-primed and tabula-rasa learners on three
hidden-dependency labs (`lab4`, `lab4dual`, `lab4chain`) and the `lab5`
energy-budget lab. Two registered seed-half dispatches provide 20 paired
seeds. The frozen family contains three `avg_redundant` contrasts and one
`energy_compliance` contrast (exact paired sign-flip tests, BH `m=4`).

| Registered member | Mean Δ (KG − TR) | 95% bootstrap CI | Exact sign-flip p | BH q | Paired rank-biserial | Verdict |
|---|---:|---:|---:|---:|---:|---|
| `lab4` `avg_redundant` | −0.69500 | [−0.98562, −0.43750] | 3.815×10⁻⁶ | 5.086×10⁻⁶ | −0.990 | Supported |
| `lab4dual` `avg_redundant` | −0.74500 | [−0.97375, −0.53187] | 3.815×10⁻⁶ | 5.086×10⁻⁶ | −0.990 | Supported |
| `lab4chain` `avg_redundant` | −0.73438 | [−0.88500, −0.58500] | 1.907×10⁻⁶ | 5.086×10⁻⁶ | −1.000 | Supported |
| `lab5` `energy_compliance` | +0.04313 | [+0.01438, +0.07063] | 0.009399 | 0.009399 | +0.683 | Supported |

All four registered members are supported in the favourable direction, but
the corrected campaign rejects the earlier depth-gradient narrative. The
registered ordered secondary,
`d(lab4chain) − d(lab4) = −0.03938`, is null
(`95% CI [−0.35813,+0.28812]`, exact sign-flip `p=0.823`). The descriptive
depth contrasts are also null. The redundancy advantage is approximately
constant at `−0.7` actions across the three dependency designs; the withdrawn
`−0.33/−0.93/−1.46` monotone pattern was a protocol artifact. The corrected
lab5 benefit (`+0.043`) is smaller than the withdrawn `+0.096` but remains
supported.

The Phase-4 conclusion is consequently structural but not gradient-based:
knowing a hidden gate reduces redundant actuation in every tested dependency
lab, while the evidence does not show that the gain grows with dependency
depth. Knowing device energy costs produces a small increase in within-budget
goal attainment. These are simulator-conditional results and do not establish
real-building energy savings.

Sources: `docs/phase4_correction_registration_2026-07-22.md`,
`docs/PHASE4_DEPENDENCY_LADDER.md` §11,
`phase4_v2_corrected/analysis/registered/phase4_v2_registered_family.csv`,
and `phase4_v2_ladder_trend.csv`.

---

## Integrated reading

Across the corrected record, the empirical claim is narrower than a generic
"knowledge improves learning" statement. Phase 1 finds a small clean-lab
advantage whose majority component is reproduced by an ontology-free
redundancy rule. Phase 1b finds genuine relevance, fragmentation, and
dependency-order signals, but all confirmed magnitudes are below the
registered scientific thresholds, and the two new qualitative consumers are
exact nulls. Phase 2 shows both benefit and operational risk: knowledge can
speed recovery after detectable faults while a knowledge-shaped policy can
also prevent the observations required for detection. Phase 3 demonstrates
accurate symbolic delay acquisition and its use in deterministic deadline
planning, with energy kept descriptive. Phase 4 supports a stable reduction
in redundant actuation at hidden gates and a small energy-compliance benefit,
but not a growing effect with dependency depth.

All conclusions are limited to the registered discrete simulators and their
frozen instruments. Confirmatory results are identified above by their
registered families; supporting controls, mechanism readings, and Phase-3
energy remain descriptive, and the proposed Phase-2 Q-gap analysis remains a
future retrospective rather than confirmatory evidence.

---

## Source Index

All current numbers above are read from the following committed campaign
archives and registered outputs. All paths are relative to the workspace root.

### Phase 1 workflow runs

| Mode | GitHub run | Commit | Seeds |
|---|---:|---|---:|
| KG only / arm C | `29848584965` | `d344238` | 1–20 |
| Redundancy only | `29848587274` | `d344238` | 1–20 |
| Baseline label control | `29848589682` | `d344238` | 1–20 |
| PBRS-only label control | `29848592010` | `d344238` | 1–20 |

### Phase 1 data and analysis files

| File | Content |
|---|---|
| `phase1_v2_corrected/analysis/registered/phase1_v2_registered_family.csv` | Frozen five-test family, intervals, exact tests, effect sizes, and BH q-values. |
| `phase1_v2_corrected/analysis/registered/phase1_v2_decomposition.json` | Registered one-third/two-thirds attribution rule and realized 69.8% share. |
| `phase1_v2_corrected/analysis/phase1_v2_controls_and_descriptives.csv` | Every corrected within-mode training and benchmark contrast with source run ID. |
| `phase1_v2_corrected/analysis/phase1_v2_protocol_gate_summary.json` | Cell counts, horizons, schemas, paired schedule checks, first-goal rows, and fallback totals. |
| `phase1_v2_corrected/run_*/analysis/out/SHA256SUMS.csv` | GitHub-produced artifact integrity inventories. |
| `phase1_v2_corrected/SHA256SUMS.csv` | Complete permanent campaign inventory. |

### Phase 1 statistics pipeline and disclosure

| File | Role |
|---|---|
| `analysis/phase1_v2_registered_family.py` | Exact registered family and decomposition. |
| `analysis/reproduce_phase1_v2.py` | Raw-data rebuild and canonical byte-equivalence gate. |
| `docs/phase1_results_v2.md` | Full corrected interpretation, including adverse and null outcomes. |
| `docs/phase1_correction_analysis_deviation_2026-07-22.md` | Post-download seed-order and cross-platform serialization corrections. |

All protocol-v1 Phase 1 reports and xzone analyses are historical protocol-affected
development records only. Their binding status is recorded in
`docs/PHASE1_PROTOCOL_AFFECTED_NOTICE_2026-07-21.md`.

### Phase 1b workflow runs

| Mode | GitHub runs | Dispatch head | Seeds |
|---|---|---|---:|
| Baseline | `30199243656`, `30199247467` | `c8e14a4b` | 1–10, 11–20 |
| Redundancy only | `30199251189`, `30199254246` | `c8e14a4b` | 1–10, 11–20 |
| Frozen KG | `30199257204`, `30199260042` | `c8e14a4b` | 1–10, 11–20 |
| Extended KG | `30199263213`, `30199266427` | `c8e14a4b` | 1–10, 11–20 |

### Phase 1b sources

| File | Role |
|---|---|
| `docs/phase1b_registration_2026-07-26.md` | Binding pre-data registration; confirmatory BH family `m=5`, with M5 prospectively exploratory. |
| `phase1b_corrected/CAMPAIGN_MANIFEST.md` | Run map, implementation/dispatch provenance, archive gates, and registered-output contract. |
| `phase1b_corrected/analysis/registered/phase1b_registered_family.csv` | M1–M6 paired statistics, intervals, exact tests, BH results, censoring, and RMST horizon. |
| `phase1b_corrected/analysis/registered/phase1b_supporting.csv` | Redundancy analogues and other registered supporting outcomes. |
| `docs/phase1b_results_2026-07-27.md` | Corrected confirmatory interpretation and required disclosures. |
| `docs/phase1b_decision_memo_2026-07-27.md` | Post-campaign thesis reading and proceed/defer/descope decisions. |
| `analysis/reproduce_phase1b.py` | Archive validation and byte-equivalent registered-table reproduction. |

### Phase 2 workflow runs

| Dispatch | GitHub run | Head | Seeds |
|---|---:|---|---:|
| A1 | `30001857104` | `19f4f3ff` | 1–10 |
| A2 | `30001867521` | `19f4f3ff` | 11–20 |
| B1 | `30001878310` | `19f4f3ff` | 1–10 |
| B2 | `30001888910` | `19f4f3ff` | 11–20 |

### Phase 2 sources

| File | Role |
|---|---|
| `docs/phase2_correction_registration_2026-07-22.md` | Binding protocol-v2 correction registration. |
| `docs/phase2_v2_dispatch_record_2026-07-22.md` | Two pre-data failure rounds and the four runs of record. |
| `phase2_v2_corrected/CAMPAIGN_MANIFEST.md` | Corrected campaign summary and archive/reproduction contract. |
| `phase2_v2_corrected/analysis/registered/phase2_v2_registered_family.csv` | Frozen Tier-1 recovery family, censoring counts, exact tests, and BH results. |
| `phase2_v2_corrected/analysis/registered/phase2_v2_detection_family.csv` | Detector-v2 family and policy-dependent detection outcomes. |
| `docs/thesis_chapter_phase2.md` §§4–6 | Full corrected result narrative and false-positive/false-negative trade-off. |
| `analysis/reproduce_phase2_v2.py` | Gate validation and canonical registered-table reproduction. |

All Phase-2 protocol-v1 values and KG-silent/multi-blind descriptives from the
withdrawn scheduler are historical only. They do not support current
mechanism or recovery claims.

### Phase 3 workflow run and sources

| GitHub run | Head | Replicas | Profiles × arms |
|---:|---|---:|---|
| `29926328852` | `90e53f8b` | 1–10 | `lab2_slow,lab3_slow × ql_true,ql_false` |

| File | Role |
|---|---|
| `docs/phase3_correction_registration_2026-07-22.md` | Binding protocol-v2 correction registration and descriptive-only energy rule. |
| `phase3_v2_corrected/CAMPAIGN_MANIFEST.md` | Run-of-record and corrected outcome summary. |
| `phase3_v2_corrected/run_29926328852/analysis/out/phase3_delay_accuracy.csv` | Corrected learned-delay values and instantaneous/delayed classifications. |
| `phase3_v2_corrected/run_29926328852/analysis/out/phase3_compliance_ci.csv` | Corrected descriptive compliance, tick-energy, and delay summaries. |
| `phase3_v2_corrected/run_29926328852/analysis/out/phase3_compliance_paired.csv` | Reproduced paired rows; the registration still requires compliance to be presented as a worked demonstration and energy without hypothesis tests. |
| `analysis/reproduce_phase3_v2.py` | Gate validation and canonical output reproduction. |

Runs `27621106006` and `29166356524`, their universal `6/6` compliance
wording, and their cumulative wall-clock energy values are withdrawn.

### Phase 4 workflow runs and sources

| GitHub run | Head | Seeds |
|---:|---|---:|
| `29926341581` | `90e53f8b` | 1–10 |
| `29926354783` | `90e53f8b` | 11–20 |

| File | Role |
|---|---|
| `docs/phase4_correction_registration_2026-07-22.md` | Binding protocol-v2 registration, frozen four-member family, and ordered ladder secondary. |
| `phase4_v2_corrected/CAMPAIGN_MANIFEST.md` | Seed-half run map and corrected result summary. |
| `phase4_v2_corrected/analysis/registered/phase4_v2_registered_family.csv` | Four registered paired effects, intervals, exact tests, effect sizes, and BH q-values. |
| `phase4_v2_corrected/analysis/registered/phase4_v2_ladder_trend.csv` | Registered depth contrast and descriptive adjacent contrasts. |
| `docs/PHASE4_DEPENDENCY_LADDER.md` §11 | Corrected interpretation; preceding sections are the withdrawn historical record. |
| `analysis/reproduce_phase4_v2.py` | Gate validation and byte-equivalent registered-table reproduction. |

The post-inversion run `29193486193` and its monotone
`−0.33/−0.93/−1.46` ladder are protocol-affected historical evidence, not
current Phase-4 results.
