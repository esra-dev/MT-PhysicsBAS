# 14 — Presentation Rules

**Generated:** 2026-07-08 · branch `phase2-instant-blacklist`
**Purpose:** Guidance for thesis presentation of fault-matrix coverage and related structural
arguments. Companion to `13_logic_report.md` §3 items 7–10.

---

## Phase-2 fault-matrix coverage

### `lab1_f1inv` — structural-coverage argument (no new cell required)

Lab 1 is a single-actuator environment containing exactly one controllable lamp; the
fault-matrix cell `lab1_f1inv` (inverted lamp in a trivial lab) is structurally
unreachable as a meaningful recovery scenario.
Blacklisting the lone lamp leaves the agent with an empty action set and no recovery
lever — there is no surviving actuator to re-learn a policy over, so the cell would
measure only detection (which is already confirmed by the clean-parent `lab1` cells)
and would produce a degenerate RecoveryEpisodes distribution.
Multi-fault coverage is likewise impossible with one actuator: the fault matrix
requires at least two independent actuators to produce a meaningful multi-fault cell
(one dead, one inverted or two simultaneously dead), a condition that is architecturally
absent in Lab 1 by design.
The thesis should note this explicitly: Lab 1 serves as a complexity-floor control
establishing detection recall, not as a recovery testbed; fault-recovery evidence begins
at Lab 2, where the two-actuator layout first provides a non-degenerate recovery lever.

---

## Phase C2 presentation rules (final-report drafting)

These rules are **binding on Phase C2** (final-report drafting). They encode the
presentation-level fixes from `13_logic_report.md` §3 items 3–4, 5, 8, and 11. Each rule
cites its source line in `13_logic_report.md` (with the pass-through citation into
`11_gap_analysis.md` / `12_stats_review.md` where the underlying number lives). Phase C2
must obey all of them; do not soften a claim past what its cited evidence supports.

1. **lab3 is a characterized weakness and the bridge to Phase 2 — never a clean win.**
   Present lab2 as the clean win and lab3 as the point where the KG prior *over-explores
   2048 states* (characterized via the init-bonus sweep); this cost-of-priors finding is
   what motivates Phase 2's "recheck with physics" and must be written as the explicit
   transition, not hidden. Do **not** frame lab3 as a spillage win: the headline arms run
   with `cross_zone_bonus = 0.0`, `auc_goal` is null-to-negative, and the KG agent is slower
   to first goal. (`13_logic_report.md` §3 items 3–4, `#L115`–`#L116`; §1 Phase 1 `#L23`–`#L31`;
   §6 `#L165`–`#L169`; pass-through `11_gap_analysis.md#L39`, `#L52`, `#L59`;
   `12_stats_review.md#L102`–`#L109`.)

2. **Phase-3 deadline compliance is a worked demonstration (counts), not inference.**
   Report it as `6/6 vs 3/6` deadline compliance, identical across all 10 replicas, and state
   that the planner is deterministic so the replicas are copies, not independent samples. Do
   **not** attach significance language (no "significant at p = 0.00195"); the tabulated
   `p_wilcoxon = 0.001953125` is the mechanical `2 / 2¹⁰` signed-rank floor and carries no
   inferential weight here. Register the m = 2-per-metric family deviation.
   (`13_logic_report.md` §3 item 5, `#L117`; §1 Phase 3 `#L61`–`#L65`; §5 `#L152`;
   §6 `#L173`–`#L176`; pass-through `12_stats_review.md#L244`–`#L262`, `#L272`–`#L279`.)

3. **Statistical methods, applied consistently across every phase:** the **paired bootstrap
   is the primary test**; **Wilcoxon signed-rank is a tie-fragile sensitivity check** (it hits
   a hard floor at small n — `2 / 2ⁿ`, i.e. `0.0625` at n = 5, so goal-rate/compliance cells
   near ceiling have effective n ≈ 5 after zero-dropping and cannot clear 0.05 below n = 6);
   and **Cliff's δ is the effect size**. State this once in a Methods paragraph and apply it
   uniformly — never let a Wilcoxon floor read as weak evidence when bootstrap + δ already
   establish the effect. (`13_logic_report.md` §3 item 8, `#L120`; KEEP §2 item 8
   `#L100`–`#L102`; pass-through `12_stats_review.md#L50`–`#L66`, `#L408`–`#L411`.)

4. **REQ-53 narrative alignment — "stereotypes lack dynamics" is demonstrated in the Phase-3
   `_slow` labs, not in the Phase-1 weakness labs.** The advisor phrased the dynamics-failure
   as appearing "in part 1", but the repo demonstrates it in the Phase-3 `_slow` environments
   (where the KG arm meets tight deadlines and the zero-delay arm does not). Align the thesis
   wording to where the mechanism and evidence actually live. (`13_logic_report.md` §3 item 11,
   `#L123`; §1 Phase 3 `#L63`–`#L64`; pass-through `11_gap_analysis.md#L100`.)

5. **lab3 spillage claim — D1 decision is REFRAME (item 3 option (b)), confirmed by the
   intermediate-magnitude rerun: lead with `auc_reward`, state the ceiling caveat, disclose
   all three magnitude runs.** The item-3(a) rerun was executed on 2026-07-08 (GH run
   `28941204656`, branch `kg-crosszone-coupling-mid` @ `ad3cb3b`: lamp bleed 100 lux, blind
   bleed 0.30·sun — derived from the trivialisation threshold 25 + b·900 ≥ 300 → b ≥ 0.306,
   not swept for significance — with `cross_zone_bonus = 3.0` active in the headline arm) and
   the KG arm **still regressed** on the rank-moving metrics: `mean_first_goal` Δ = +23.95
   [+7.68, +39.95], q = 0.011 (slower); `avg_cycling` Δ = +0.575 [0.25, 0.93], q ≈ 0;
   `auc_goal` null (Δ = −0.00045, q = 1.0); `goal_rate` tie (Δ = +0.006, q = 1.0). Therefore
   the report leads lab3 with the **`auc_reward` win, robust at every tested magnitude**
   (as-is +14.5 / intermediate +12.7 / bumped +14.3; all q ≈ 0, δ = 0.88–1.0), framed as:
   *structure knowledge does not buy learning speed on the complex lab — the bumped run's
   "penalty removal" came from trivialising the task (`auc_goal` at the ≈0.99 ceiling for
   both arms), and at non-trivialising magnitudes the KG pays the exploration cost of rule 1.*
   Never present lab3 `auc_goal` or first-goal as a KG win at any magnitude, and disclose all
   three magnitude runs (as-is `27440842780`, intermediate `28941204656`, bumped
   `27461188614`) — omitting the intermediate run would be file-drawering.
   (`13_logic_report.md` §3 item 3, `#L115`; §6 `#L165`–`#L169`; pass-through
   `11_gap_analysis.md#L59`; `12_stats_review.md#L102`–`#L109`; new evidence:
   `phase1_xzone_mid/analysis/out/learning_speed_tests.csv` + `paired_tests.csv`, verified
   locally identical to the CI aggregate of run `28941204656`.)
