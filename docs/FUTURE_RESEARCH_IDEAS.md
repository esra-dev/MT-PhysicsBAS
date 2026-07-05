# Future Research, Testing & Evaluation Ideas

> **Status:** ideas only — described, **not** implemented. This document
> collects candidate extensions for the stereotype/KG-guided Q-learning smart-
> building thesis, organised by theme, each with a research question, a sketch
> of the setup, the expected finding, and a rough effort/risk estimate. It is
> meant as a menu for the next iterations after Phase 2.5 (the monitor
> emergency-fallback lab, see `docs/PHASE2_5_MONITOR_EMERGENCY.md`).

## Where the project stands (recap of what motivates these ideas)

- **Phase 1 (clean ladder, lab1→lab3):** a KG prior over component *stereotypes*
  (Causes / Mediates mechanisms) accelerates tabular Q-learning convergence.
- **Phase 2 (fault handling):** a pre-trained agent DETECTS a component whose
  behaviour contradicts the KG (dead / inverted), BLACKLISTS it, and RE-LEARNS
  over the survivors. The KG-primed agent re-aligns faster and more reliably.
  Extended with: blind (IV-gated) faults via an **active KG self-test**;
  symmetric well-posed cells; a two-tier confirmatory/descriptive analysis; and
  **Phase 2.5 — the monitor emergency-fallback lab** (using an unconventional
  side-effect light source when the primary lamp dies).
- **Phase 3 (process dynamics):** the agent learns per-actuator *response delays*
  online and exploits them for deadline-bounded goals.
- **Phase 4 (hidden knowledge):** hidden power dependencies (smart-plug AND-gate)
  and energy-cost differentiation that only a KG-primed agent can exploit.

The through-line is: **symbolic physics knowledge (a KG of component
stereotypes) lets an RL agent generalise, recover, and act more efficiently than
a tabula-rasa learner.** The ideas below stress-test, broaden, and deepen that
claim.

---

## Theme A — Richer fault models (robustness of detect → blacklist → re-learn)

### A1. Intermittent / transient faults (flicker)
- **Question:** does instant blacklisting over-react to a fault that comes and
  goes? Should a blacklisted component be *re-validated* and un-blacklisted?
- **Setup:** a fault flow that toggles the fault on/off every *k* episodes (e.g.
  a loose connector). Add an optional *probation* mechanism: a blacklisted
  Causes actuator is periodically re-probed (reuse the Phase-2 active self-test)
  and reinstated if it passes.
- **Expected:** the KG agent, by re-probing on physics grounds, recovers a
  transiently-faulty lever a vanilla agent would abandon permanently.
- **Effort/Risk:** medium / medium (needs un-blacklist + re-probe logic).

### A2. Partial / degraded faults (aging lamp)
- **Question:** the current model is binary (dead / inverted). What about a lamp
  that still works at *reduced* output (+200 instead of +400)?
- **Setup:** fault flow that scales a contribution (`z1l ? 400` → `z1l ? 200`).
  The rank-response detector may NOT flag it (still crosses a boundary), so the
  agent must *re-optimise* around a weaker-but-alive actuator.
- **Expected:** the KG's magnitude-agnostic "this raises illuminance" prior
  still helps re-planning; quantify the detection blind-spot for sub-rank
  degradation and whether adaptive-trust re-calibrates the effective strength.
- **Effort/Risk:** low / low (one flow + one profile).

### A3. Gradual drift / concept drift (lifelong learning)
- **Question:** if the physics drifts slowly (seasonal sun, lamp decay), does the
  KG-primed agent stay calibrated better than tabula-rasa?
- **Setup:** a simulator that decays a coefficient over training; measure
  tracking error and re-convergence lag. Tie into the adaptive-trust calibrator.
- **Expected:** KG priors give a warm bias that shortens re-tracking after each
  drift step; vanilla lags.
- **Effort/Risk:** medium / medium (time-varying flow, continual-learning metrics).

### A4. Sensor faults (fault on the *sensing* side)
- **Question:** detection today only adjudicates *actuators*. What if the
  illuminance **sensor** is stuck / biased / noisy?
- **Setup:** corrupt the reported `Z1Level` (stuck value, additive bias, noise).
  Add a KG cross-check: predicted-vs-sensed illuminance from the known actuator
  states flags a sensor whose reading contradicts the physics.
- **Expected:** the KG (which predicts the expected reading) can localise a
  sensor fault that a model-free agent cannot even represent.
- **Effort/Risk:** high / medium-high (new fault class + new detector path).

### A5. Adversarial / cascading fault timing
- **Question:** how resilient is warm-restart to worst-case fault *sequences*?
- **Setup:** inject fault A, let it recover, then inject fault B (and B on the
  survivor of A). Measure cumulative recovery cost and whether the agent ends in
  a still-goal-reaching policy or a dead end.
- **Expected:** characterises the graceful-degradation frontier and when the
  agent must *alert-and-give-up* (no survivor path).
- **Effort/Risk:** low / low (reuses existing machinery, new profiles).

---

## Theme B — Deepening the monitor / unconventional-fallback story (Phase 2.5+)

### B1. Cost-aware fallback (turn the energy prior on)
- **Question:** the monitor is power-hungry (energyCost 3). With the energy prior
  enabled, will the KG agent use the monitor **only in the emergency** and prefer
  the cheaper backup when both reach the goal?
- **Setup:** reuse `building_6_monitor.ttl`; declare `ws:energyCost` on each
  actuator and run with `stereo.energyPriorWeight > 0`. Score clean-lab monitor
  usage (should be ~0) vs emergency monitor usage (should be high).
- **Expected:** a clean demonstration of *necessity-gated* use of an inefficient
  fallback — the agent respects cost until cost must yield to task success.
- **Effort/Risk:** low / low (config + one prior weight; strong narrative payoff).

### B2. The fallback itself fails (monitor dead / backup dead)
- **Question:** graceful degradation when the *fallback* is also compromised.
- **Setup:** `labmon_f2dead` (lamp + backup dead → only the monitor, insufficient
  alone → ill-posed → must ALERT) and `labmon_mondead` (monitor dead → back to
  the lamp). Tests the alert-and-stop path and detection of the new stereotype.
- **Expected:** correct classification (ill-posed vs recoverable) and a clean
  user alert when no survivor path exists.
- **Effort/Risk:** low / low (two fault recipes).

### B3. Monitor as a competing objective (multi-objective RL)
- **Question:** a monitor used for *light* can't simultaneously serve its
  *primary* duty (displaying work). Model this as a soft penalty and make the
  agent trade off lighting-goal vs monitor-availability.
- **Setup:** add a second reward term for "monitor free for its primary use";
  the KG encodes the trade-off. Multi-objective / constrained RL.
- **Expected:** the agent uses the monitor for light only when the lighting goal
  is otherwise unreachable — a principled necessity threshold.
- **Effort/Risk:** high / medium (reward redesign; strongest thesis narrative).

### B4. Human-in-the-loop preference constraint
- **Question:** encode a user rule "do not use the monitor for lighting unless
  nothing else works" in the KG; does the agent honour it and only override under
  necessity?
- **Setup:** a KG-level soft-constraint prior (negative bias on the monitor ON
  action) that is *overridden* when the survivor analysis shows it is required.
- **Expected:** demonstrates preference-respecting behaviour with a physics-
  grounded escape hatch — an interpretable, auditable policy.
- **Effort/Risk:** medium / low.

---

## Theme C — Stress-testing the knowledge graph itself

### C1. Unknown actuator (no stereotype)
- **Question:** put an actuator in the lab that has **no** KG stereotype. Can the
  agent still discover its effect by exploration while exploiting the known ones?
- **Setup:** a lab with a known lamp + a mystery actuator (present in the WoT TD
  and flow but with no `elem:hasBehavioralStereotype`). Contrast with the monitor
  (which HAS a stereotype).
- **Expected:** quantifies the *value of the stereotype* — the known-unknown gap
  in time-to-exploit between a KG-described and an undescribed lever.
- **Effort/Risk:** medium / medium (discovery currently requires a stereotype;
  needs a "structural-only" action path).

### C2. Wrong / misleading stereotype (KG error robustness)
- **Question:** real KGs are imperfect. If the KG asserts a FALSE stereotype
  (e.g. "this heater is a lamp", or "the monitor raises light" when it doesn't),
  does adaptive-trust down-weight the bad prior fast enough?
- **Setup:** deliberately mislabel one component; measure the penalty the wrong
  prior imposes and the recovery time of the adaptive-trust calibrator.
- **Expected:** bounds the *harm* of KG errors and validates the self-correcting
  trust mechanism — crucial for real-world credibility.
- **Effort/Risk:** low / low (mislabel + reuse adaptive-trust metrics).

### C3. Partial KG (missing edges)
- **Question:** how does performance degrade as the KG is progressively pruned
  (drop cross-zone couplings, drop IV gates, drop energy costs)?
- **Setup:** an ablation ladder over KG completeness; plot convergence/recovery
  vs KG coverage.
- **Expected:** a dose-response curve showing which KG facts matter most.
- **Effort/Risk:** low / low (config-driven ablations; great for the evaluation
  chapter).

---

## Theme D — Method & evaluation rigour

### D1. Cross-lab transfer (train on lab3, adapt on labmon)
- **Question:** the current warm-start requires the *same* lab structure. Can KG
  priors transfer *zero/few-shot* to a lab with a different topology?
- **Setup:** a state/action re-mapping layer keyed on stereotypes rather than
  slot indices; measure jump-start and asymptotic transfer.
- **Expected:** the KG (structure-agnostic) transfers where a raw Q-table cannot.
- **Effort/Risk:** high / high (Q-table is index-bound; needs a mapping layer).

### D2. Component-level ablation of the fallback speed-up
- **Question:** *which* KG fact drives the monitor-fallback advantage — the
  Causes-light prior on the monitor, the backup prior, or both?
- **Setup:** ablate the monitor's `elem:increases` edge alone, the backup's
  alone, and both; attribute the recovery speed-up.
- **Expected:** a causal decomposition of the KG benefit.
- **Effort/Risk:** low / low.

### D3. Model-based RL baseline
- **Question:** does a hand-authored KG beat a *learned* dynamics model (Dyna /
  small MBRL) at the same recovery task?
- **Setup:** add an MBRL arm; compare sample efficiency of KG-prior vs
  learned-model.
- **Expected:** situates the symbolic-KG contribution against modern MBRL;
  likely a KG-wins-early / MBRL-catches-up story.
- **Effort/Risk:** high / high (new learner).

### D4. Continuous / dimmable actuators
- **Question:** do the directional KG priors scale from on/off to *continuous*
  brightness (0–100 %)?
- **Setup:** dimmable lamp/monitor with a discretised or continuous action head;
  the monitor fallback can then be tuned to *exactly* clear the goal.
- **Expected:** the KG's sign prior generalises; tests precision of the fallback.
- **Effort/Risk:** high / high (action-space redesign).

### D5. Explanation / interpretability evaluation
- **Question:** the BDI+KG stack can *justify* its actions symbolically. Evaluate
  the quality of natural-language justifications ("primary lamp failed; the
  monitor is a known secondary light source; engaging it as a fallback").
- **Setup:** emit a per-decision rationale from the KG + BDI beliefs; score it
  (faithfulness, completeness) against the ground-truth cause.
- **Expected:** highlights the interpretability edge of KG+BDI over black-box RL.
- **Effort/Risk:** medium / low (mostly plumbing existing beliefs to text).

### D6. Statistical hardening
- **Question:** are the effects robust to more seeds, more labs, and pre-
  registered analysis?
- **Setup:** raise seeds (n≥20), add the monitor lab to the confirmatory family,
  keep the two-tier BH-FDR discipline (`analysis/phase2_recovery.py`), and pre-
  register the recovery-speed hypothesis.
- **Expected:** tighter CIs and a defensible confirmatory claim across the whole
  well-posed family (now including the monitor cell).
- **Effort/Risk:** low / low (compute only).

---

## Suggested near-term ordering (highest value / lowest risk first)

1. **B1 (cost-aware fallback)** — small change, strongest narrative extension of
   Phase 2.5; shows *necessity-gated* use of an inefficient device.
2. **C2 (wrong stereotype robustness)** — cheap, directly addresses the obvious
   reviewer question "what if the KG is wrong?".
3. **A2 (partial/degraded faults)** — cheap, closes the binary-fault gap.
4. **D2 + D6 (ablation + more seeds)** — cheap, hardens the causal + statistical
   claims for the thesis.
5. **B2 (fallback-fails / alert path)** — cheap graceful-degradation coverage.
6. Then the higher-effort deep dives: **B3 (multi-objective monitor)**,
   **A4 (sensor faults)**, **D1 (cross-lab transfer)**, **D3 (MBRL baseline)**.
