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

## Phase 3: Learning Process Dynamics and Time-Bounded Control

The previous phases established that the knowledge graph primes the agent's
exploration in a useful direction. Phase 3 asks a separate question: can the
same KG infrastructure support **online learning of physical process dynamics**,
and can that knowledge be used for **time-bounded control** — executing goals with
explicit response-time constraints?

The setting adds two slow-lab variants of the existing two-zone rooms
(`lab2_slow`, `lab3_slow`) where a motorised blind takes **12 simulation ticks =
60 simulated seconds** to settle, while a lamp activates in ≤ 2 ticks ≈ 10 s.
The agent runs in two phases: (A) eight probe episodes per actuator, recording
empirical settle times via `DynamicsLearner` and writing the result into the KG
as `learned:learned_delay_sec`; then (B) exploitation episodes with time-bounded
goals — "make the room bright within 45 s" (tight) or "within 120 s" (loose).
Two arms are compared: `ql_true` reads `learned_delay_sec` from the KG and
chooses the lamp for tight deadlines; `ql_false` ignores the KG and defaults to
the blind. Ten replicas were run per lab; the planner is deterministic given the
learned table, so replicas resample tick-quantisation jitter rather than a random
policy.

**Delay learning is fast and accurate.** After only 8 probe episodes, the agent
estimates the blind delay to within **≤ 1.77 % relative error** across both labs
(learned: 12.11–12.21 ticks vs ground truth 12). Instantaneous actuators are
correctly estimated at ~1.14 ticks. Classification accuracy is 100 %: every
actuator is correctly labelled instant vs delayed across all replicas and both
arms. The small residual error (< 0.25 ticks) stems from tick-quantisation —
the precise moment the blind passes threshold depends on the exact tick phase
at episode start — and is stable across replicas.

**Time-bounded compliance is binary and complete.** `ql_true` meets 100 % of all
goals, including all tight-deadline goals, in both labs. `ql_false` meets 100 %
of loose goals (the 120 s window is wide enough for a blind) but 0 % of tight
goals (a 60 s blind cannot satisfy a 45 s deadline). The headline compliance table:

| Lab | Mode | Overall | Tight | Loose | Σ energy (mean) | Mean actual delay |
|---|---|---|---|---|---|---|
| lab2_slow | ql_false | 0.50 | **0.00** | 1.00 | 0.0 | 60.6 s |
| lab2_slow | ql_true | **1.00** | **1.00** | 1.00 | 3.2 | 33.3 s |
| lab3_slow | ql_false | 0.50 | **0.00** | 1.00 | 0.0 | 60.6 s |
| lab3_slow | ql_true | **1.00** | **1.00** | 1.00 | 3.3 | 33.1 s |

The statistical test (within-replica paired bootstrap, Wilcoxon, Cliff's δ,
BH-FDR; family m = 4) confirms the result with no ambiguity:

| Metric | Mean diff | 95 % CI | p_boot | p_wilcoxon | Cliff's δ | q_BH |
|---|---|---|---|---|---|---|
| overall_compliance (both labs) | +0.50 | [0.50, 0.50] | 0.000 | **0.00195** | **1.00** | 0.000 |
| tight_compliance (both labs) | +1.00 | [1.00, 1.00] | 0.000 | **0.00195** | **1.00** | 0.000 |
| loose_compliance | 0.00 | [0.00, 0.00] | 1.000 | 1.000 | 0.00 | 1.000 |
| total_energy (↑ in ql_true) | +3.2 / +3.3 | [3.0, 3.5] / [3.0, 3.6] | 0.000 | 0.00195 | 1.00 | 0.000 |

*n = 10 replicas per lab, CI run `27621106006`. p_wilcoxon = 2/2¹⁰ = 0.001953 (exact floor for n = 10 all-positive paired differences).*

Degenerate compliance CIs are expected, not cherry-picked: the planner is
deterministic given the learned KG, so every replica reaches the same decision.
The genuine stochasticity (tick-jitter) appears only in the delay accuracy CIs,
where it produces a small but non-zero variance.

The energy cost (+3.2–3.3 units) is the correct and legible trade-off: the agent
switches from a free-but-slow blind to a costly-but-fast lamp to honour the tight
deadline, and the framework surfaces this decision explicitly. In `lab3_slow` the
agent also demonstrated emergent cross-zone exploitation — satisfying a zone-2 goal
via `Z1Blinds` because the probe phase had measured a valid cross-zone effect
from data, independently rediscovering the cross-zone coupling that earlier phases
had required a hand-asserted KG prior to encode. This validates that the learned
KG generalises beyond delay timing alone.

**Summary.** Eight probe episodes suffice to learn a 60 s delay to < 2 % error.
The KG-integrated learned dynamics converts a 50 % failing agent into a
100 %-compliant one, with a transparent energy trade-off and no change to the core
QL policy. The result holds across two labs, two compliance tiers, and 10 replicas,
with Cliff's δ = 1.0 and q_BH < 0.001 throughout.

Full analysis: [`docs/PHASE2_TO_PHASE3_CHANGES.md`](PHASE2_TO_PHASE3_CHANGES.md) §§16–19.
Pre-registration: [`docs/pre_registration.md`](pre_registration.md) §8.

---

## Source Index

Phase 1 numbers above are read from the following committed protocol-v2 files. All paths
are relative to the workspace root.

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
