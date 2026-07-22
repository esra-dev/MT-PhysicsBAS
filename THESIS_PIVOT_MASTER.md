# THESIS PIVOT MASTER DOCUMENT
**Project State:** Pivoting from "Adaptation to Faults" to "Knowledge-Guided Acceleration, Fault Detection, and Dynamics Learning."
**Stack:** MAS (JaCaMo / AgentSpeak / CArtAgO) + Q-Learning + Knowledge Graph (KG / stereotypes) + Node-RED labs.

## 1. The Core Philosophy (The "Why")
The previous architecture forced the Q-learning agent to adapt to broken environments (e.g., inverted sensors, power caps), using KG stereotypes as priors to "hack" around faults. The advisors rejected this as scientifically flawed: priors represent *normal* physics, so by definition they should not help when physics break. A stereotype-guided system is NOT meant to work around broken physics.

**The New Paradigm:**
1. Physics knowledge (Knowledge Graph / Stereotypes) accelerates learning in *clean* environments.
2. When faults occur, the agent should NOT adapt to the fault. It should *detect* the fault (because reality diverges from the physics prior), *blacklist* the broken component, alert the user, and *re-learn* using only the remaining working components.
3. The agent should exploit its learning capability to discover *temporal dynamics* (delays) missing from the static Knowledge Graph, and write them back into the KG.

## 2. Phase 1: The Baseline Proof — Clean Lab Progression (The Anchor)
*   **Goal:** Prove that KG-primed Q-Learning is faster, converges better, and avoids redundant actions compared to tabula-rasa Q-Learning, in strictly normal (non-faulty) environments.
*   **Action Plan:**
    *   Strip out / disable the `custom2` through `custom9` weakness labs temporarily. No injected weaknesses in Phase 1.
    *   Create a strictly "clean" progression of Node-RED labs, scaling up gradually:
        *   `Lab_Simple`: 1 Zone, 1 Lamp, 1 Sensor. (Prove basic convergence.)
        *   `Lab_Medium`: 2 Zones, independent lamps.
        *   `Lab_Complex`: 2 Zones, shared spotlights, window blinds (cross-zone spillage / bleed).
    *   Train a standard (tabula-rasa) Q-learner vs. a KG-primed Q-learner on each lab.
    *   **Metrics:** Time to first goal, Area Under Curve (AUC) for reward, total energy / redundant actions, iterations to convergence.

## 3. Phase 2: Anomaly Detection, Blacklisting & Retraining (Faulty Labs)
*   **Goal:** Use the stereotype prior as an anomaly detector. The agent must *not* try to silently work around faults via standard RL exploration — it must *detect* them, *prune* them, and *retrain*.
*   **Action Plan:**
    *   Introduce a fault in a separate set of labs (e.g., a lamp that breaks and does nothing when actuated).
    *   The agent uses `StereotypeLearner.java` (Z-score outlier detection) to realize that an action's result contradicts the KG physics prior — e.g., "I turned on the lamp, but lux did not increase as the KG predicted."
    *   **Crucial Change:** The agent must
        1. Flag the component as broken,
        2. Explicitly discard / blacklist this actuator (remove it from the action space),
        3. Alert the user,
        4. Trigger a **warm restart** (NOT a full Q-table wipe) and re-learn over the reduced action space — see 3.1.
    *   Prove that the KG-guided agent detects the anomaly and realigns to the new reality (recovering from the component loss) faster than the baseline.

### 3.1 Warm Restart Policy (instead of full Q-table reset)
A full reset throws away all the valid Q-values the agent learned for the still-working components and erases the KG-priming advantage — making the "faster recovery" claim trivially false. Simply continuing to learn is also wrong: it is silent fault-adaptation (the exact behavior the advisors rejected), and stale `max_a Q(s,a)` bootstrapping over the dead actuator leaves the policy poisoned for many episodes.

When `StereotypeLearner` flags actuator `a*` as broken, the `QLearner` must perform a **targeted warm restart**:

1. **Prune the action space:** remove `a*` from the set of selectable actions for all future steps.
2. **Drop the column:** delete / mask `Q(s, a*)` for every `s` so it can never be selected and never appear in any `max_a` operation.
3. **Decay the poisoned states (don't zero them):** for states where `a*` was previously argmax, shrink `Q(s, a)` for the surviving actions by a decay factor (e.g., 0.5), or recompute `V(s)` from the new max over surviving actions. This removes the optimistic bias inherited from the dead action without destroying rank ordering among the good ones.
4. **Re-prime from the KG** over the reduced action space. This is the KG agent's structural advantage in Phase 2 — the tabula-rasa baseline has nothing to re-prime with.
5. **Boost exploration temporarily:** set `ε ← max(ε, ε_boost)` (e.g., 0.3) and decay back down on the normal schedule, so the agent re-explores paths that no longer route through `a*`.
6. **Log recovery as a separate metric:** episodes / steps between fault injection and re-convergence to the new optimum. This is the headline number for the Phase-2 plot (KG-guided vs. baseline recovery speed).

## 4. Phase 3: Learning Temporal Dynamics / Process Dynamics (Expanding the KG)
*   **Goal:** The current stereotypes lack temporal / process dynamics (e.g., actuation delays). The agent learns these from interaction and enriches the KG.
*   **Action Plan:**
    *   Introduce a delay in a Node-RED lab (e.g., blinds take 60s to fully open).
    *   The agent tracks the time delta (ticks / wall-clock) between executing an action and observing the expected environmental effect.
    *   Add a new property to the KG (e.g., `ws:responseDelay` / `ResponseDelay`, value such as `60s`) and have the agent write the learned dynamic back into the Knowledge Graph.
    *   Add time-bounded goals to demonstrate use of the learned dynamic, e.g.:
        *   "Brighten room *immediately*" → agent prefers lamps (low `responseDelay`).
        *   "Brighten room in 5 mins" / "Make room bright in < 2 mins" → agent may use blinds (higher `responseDelay` is acceptable).

## 5. Architectural Rules of Engagement
*   Preserve the JaCaMo (BDI) + CArtAgO + Node-RED pipeline.
*   Preserve the statistical rigor: multi-seed pipeline, bootstrap CIs, sound metrics logging for speed, iterations, and redundancy.
*   Maintain a **strict separation** between the clean labs (Phase 1) and the faulty labs (Phase 2).
*   When refactoring, **surgically remove** old "fault adaptation / reward shaping" logic that was built for the previous setup — do not delete code blindly. Refactor or comment out until the new pipeline is stable.
*   Do NOT rewrite everything at once — we execute step-by-step.
*   Always ask for clarification before modifying core files like `QLearner.java` or `StereotypeReasoner.java`.
