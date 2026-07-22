# 10 — Requirements Checklist (from ThesisGoalDescription_important.txt)

**Era: NEW (advisor redirection).** This document enumerates the requirements stated in
`ThesisGoalDescription_important.txt`. That file is **not present in the repository**
(verified via glob over the whole tree on 2026-07-07); it was supplied externally alongside
this audit. All quotes below are verbatim from that document. Line citations are therefore
not possible; each REQ instead quotes its source sentence(s).

Scope note: this file only *enumerates* requirements. It does not evaluate whether the
codebase satisfies them — that is a later audit step.

---

## Cross-cutting / meta requirements

**REQ-1 — Implementations must follow the three-phase redirection closely.**
> "This redirection of the thesis (the provided description of the three-part process) is the most important instruction/information we have. Our current implementations have to follow these directions closely"

**REQ-2 — Tests must actually test the stated aims.**
> "the tests have to actually test what we aim for"

**REQ-3 — Results must be defendable.**
> "and the results have to actually be defendable."

**REQ-4 — ANTI-requirement: the OLD "deliberate errors + adapt around them" approach is explicitly rejected.** The system must not be evaluated on adapting *around* deliberately introduced errors.
> Advisor quote: "The introduction of deliberate errors and adaptation to these errors is a failure mode that I would specifically not think that a stereotype-based system is apt to handle. Hence I don't understand why this is done and what it should show."

---

## Phase 1 — Clean labs: KG-primed Q-learner vs plain Q-learner

### Advisor note (verbatim anchor)
> "(1) write down your (re-)evaluation of the performance of Q Learner + Physics knowledge that showed that it is indeed better in terms of time taken to achieve the goal and avoidance of redundant actions. It was same in terms of success in achieving the goal. Put short description and result table(s). Core direction of thesis is important as anchor finding."

**REQ-5 — Produce a written (re-)evaluation of Q-Learner + physics knowledge vs plain Q-Learner.**
> "write down your (re-)evaluation of the performance of Q Learner + Physics knowledge"

**REQ-6 — Show the KG-primed agent is better in time taken to achieve the goal.**
> "it is indeed better in terms of time taken to achieve the goal"

**REQ-7 — Show the KG-primed agent is better in avoidance of redundant actions.**
> "better in terms of ... avoidance of redundant actions"

**REQ-8 — Show both agents are the same in success in achieving the goal** (advisor's stated prior finding; the explanation text adds "maybe even more successfully?" as an open possibility — see REQ-13).
> "It was same in terms of success in achieving the goal."

**REQ-9 — Deliverable format: short description plus result table(s).**
> "Put short description and result table(s)."

**REQ-10 — This comparison is the anchor finding / core direction of the thesis.**
> "Core direction of thesis is important as anchor finding." / "This is the most important part of the thesis."

### Experimental setup

**REQ-11 — The clean lab must fully align with the KG: no "weaknesses", no unexpected effects or unmodeled behaviors.**
> "Have an Environment that we know fully, meaning that aligns fully with the Knowledge Graph. This means a lab without any 'weaknesses'. The lab will react according to how we documented it in the KG and there are no unexpected effects or behaviors."

**REQ-12 — Two fresh agents in the *same* clean lab: (a) a Q-learning agent with no previous knowledge; (b) a fresh Q-learning agent primed with physics-based knowledge from the KG.**
> "Then we put a qlearning Agent without any previous knowledge into that environment and let it learn. Then we put a second fresh Qlearning agent into the environment that receives physics-based knowledge about the lab environment through the Knowledge Graph. Primed with this knowledge, we let this second agent learn in the same clean lab."

**REQ-13 — Expected outcome to demonstrate: the KG-primed agent learns better — faster, avoiding redundant actions, possibly more successfully.**
> "The result we expect is that the Qlearning agent with more knowledge (specifically, knowledge about physics) learns better (faster, avoids redundant actions, maybe even more successfully?) than the Qlearning agent without any additional knowledge."

**REQ-14 — Implementation must follow best research practices.**
> "It has to be implemented according to best research practices."

**REQ-15 — Results must be statistically significant / provable with correct statistical foundations, methods, and analysis.**
> "The results have to be statistically significant/provable with the right statistical foundations, methods and analysis according to best research practices."

### Lab progression

**REQ-16 — Demonstrate the effect first in a simple lab: one room/zone, few components.**
> "We want to show this exact thing first in a simple lab (one room/zone, few components)"

**REQ-17 — Then increase complexity up to an advanced lab: two rooms/zones, several components in both zones, spillage/effects from components that affect both zones.**
> "making them more complex until we have a more advanced lab (two rooms/zones, several components in both rooms/zones, spillage/effects from components that effect both zones)"

**REQ-18 — Start with a trivial, fast-converging case to demonstrate the mechanism cleanly.**
> "The idea is to start with smaller, faster-converging labs to demonstrate the mechanism cleanly. So we start with a trivial case that it can learn (and hopefully learn even better with the physics knowledge/KG)"

**REQ-19 — Increase complexity *until the approach fails*, and use the failure to define the weaknesses of stereotype-guided Q-learning (transition into Phase 2).**
> "and then increase the complexity (until it fails (this should then lead to us being able to define the weaknesses of the stereotype-guided Qlearning which we implemented in the current 'weakness labs')). This will lead into the second part of the thesis."

### Blinds / threshold learning

**REQ-20 — In complex labs, the blind stereotype defines: independent variable = outdoorIlluminance (not manipulable); manipulated variable = blindApertureRatio (manipulable); both affect dependent variable = luminiscence.**
> "In the more complex labs we have blinds whose Stereotype define that the independent variable (outdoorIlluminance, not manipulable) and the manipulated variable (blindApertureRatio, manipulable) affect the dependent variable (luminiscence)."

**REQ-21 — Blinds only have an effect when the independent variable exceeds a threshold (enough sunlight outside).**
> "But the blinds only have an effect if the value of the independent variable is above a certain threshold (logic: it has only an effect to open the blinds if there is a certain amount of sunlight outside)."

**REQ-22 — The threshold is NOT quantified in the KG; the Q-learning agent must learn the threshold value.**
> "The threshold is not known in advance (aka not quantified in the KG), which means the Qlearning Agent has to learn that threshold value."

### Cross-zone spillage (lab3)

**REQ-23 — The most complex lab (lab3) has cross-zone spillage: light from one zone (e.g. a lamp) spills into the other zone.**
> "In the most complex lab (lab3) we have cross-zone spillage. Where a bit of light from one zone (like when the lamp is on) spills into the other zone."

**REQ-24 — The RL agent must learn the cross-zone effect automatically from observation.**
> "This is where we expect the Reinforcement Learning to truly kick in. It should learn automatically from observing, that turning something on in one zone effects the other zone."

**REQ-25 — Spillage is modelled in the KG as *structure* (what affects what), not actual values — the values are to be learned.**
> "And this spillage is also modelled in the KG. ... it already knows about the spillage structure (what effects what, not actual values because they will be learned)."

**REQ-26 — Not all components cause spillage; the KG agent is expected to outperform the plain agent because it knows the spillage structure in advance.**
> "Because not all components cause spilling, we expect that the Qlearning agent with KG learns better than the Qlearning agent without, because it already knows about the spillage structure"

---

## Phase 2 — Weakness labs: fault detection, blacklist, re-learning

### Advisor note (verbatim anchor)
> "(2) The adapting to fault scenario is to be reconsidered: the agent will not try to work around a fault, but recognize that an action in its policy resulted in unexpected behavior. At this point it can recheck with physics knowledge. It then discards this artifact, and re-learns (again with and without physics). Expected is that the agent manages to realign faster with physics knowledge."

**REQ-27 — The agent must NOT try to work around a fault (must not learn a new solution *using* the faulty components).**
> "the agent will not try to work around a fault" / "the agents should not learn to find a new solution using these faulty components"

**REQ-28 — The agent must recognize that an action in its (pre-trained) policy resulted in unexpected behavior.**
> "recognize that an action in its policy resulted in unexpected behavior"

**REQ-29 — Upon detecting unexpected behavior, the agent can recheck with physics knowledge.**
> "At this point it can recheck with physics knowledge."

**REQ-30 — The agent then discards (blacklists) the faulty artifact/component.**
> "It then discards this artifact" / "the agent should recognize which components do not behave as expected, discard that artifact"

**REQ-31 — The agent must inform/alert the user that it has found a defect component.**
> "discard that artifact and let the user know that it has found a defect component"

**REQ-32 — After discarding, both variants re-learn (again with and without physics) in the reduced-component situation.**
> "and re-learns (again with and without physics)" / "Then we want the agents to re-train in these new situations where less components are actionable."

**REQ-33 — Expected outcome to demonstrate: the KG-supported agent realigns better and/or faster than the plain agent.**
> "Expected is that the agent manages to realign faster with physics knowledge." / "we expect and want to show that in this situation as well, the Qlearning agent with knowledge of the physics/stereotypes/KG realigns better and/or faster"

### Pre-training and trigger semantics

**REQ-34 — The agents placed into weakness labs must be the ones successfully pre-trained on the clean labs.**
> "In the second part we put both agents (with and without knowledge of the physics/stereotypes/KG) that are successfully trained on the 'clean' labs into the 'weakness' labs."

**REQ-35 — NO fault counter / threshold-based trigger: adaptation must start immediately once something is wrong.**
> "I do not want a counter that counts how many faults were there and trains after the threshold is reached. The pre-trained agents (from the clean lab) start adapting in the faulty labs immediately once something is wrong and adaption is needed."

**REQ-36 — A component must be *completely blacklisted as soon as it is faulty*, and the blacklisting must itself trigger re-learning of the pre-trained agents.**
> "This means a component should be completely blacklisted, as soon as it is faulty and trigger relearning of the pre-trained agents."

### Weakness-lab matrix

**REQ-37 — Weakness-lab variety must cover: (a) one component dead; (b) several components dead; (c) one component faulty (works, but does something undesired); (d) several components faulty.**
> "There should be labs where one component does not work, where several components do not work, where one component works but is faulty (does something we do not want), where several components are faulty, etc."

**REQ-38 — Each fault type must appear across the different complexities (lab1, lab2, lab3 from Phase 1).**
> "And each of these in different complexities (lab1, lab2, lab3 from phase 1)."

**REQ-39 — For each weakness lab, the agent must have been previously trained on the *clean version of that same lab*.**
> "It is important that for each 'weakness lab' the agent was previously trained on the 'clean' version of that lab and we put it into the 'weakness' version of the lab to adapt."

**REQ-40 — Blind-fault scenarios: defected/inverted blinds must be detected and blacklisted analogously to the lamps.**
> "I also want to add scenarios where some of the blinds are defected/inverted and need to be detected and blacklisted (analog to what is happening with the lamps."

### Monitor extension

**REQ-41 — Add a new stereotype for the monitor to the KG.**
> "This means that we have to add a new stereotype for the monitor."

**REQ-42 — Monitor stereotype structure: electricity as input (the text calls it "manipulated variable (input) electricity (analog to the lamp)" — note the lamp's electrical input is its MV) and *several* dependent variables (outputs).**
> "The monitor as manipulated variable (input) electricity (analog to the lamp) and several dependent variables (output)."

**REQ-43 — One of the monitor's effects is brightening the room (analog to a lamp), but this is NOT its main/desired effect.**
> "One of the effects of the monitor is that it brightens up the room (analog to a lamp). But this is not the main effect/the desired effect that we usually or willingly use to brighten our room."

**REQ-44 — Demonstrate the monitor as an emergency fallback: when none of the other options work, the system manages to use the monitor even though it is not a primary method.**
> "But we want to see whether in emergency where none of the other options work, the system manages to use the monitor as a fallback-option even though we know it is not a primary method."

**REQ-45 — The monitor must not be modelled as inherently more costly (no artificial cost penalty to force fallback ordering).**
> "Remember a monitor is not inherently more costly."

### Unreachable-goal behavior

**REQ-46 — Include a scenario where the goal state is unreachable with the available components (especially faulty labs): agents must get as close as possible AND inform the user about the situation.**
> "I want a scenario where agents cannot reach the goal state with the available components (especially in faulty labs), they try to get as close as possible and inform the user about this."

**REQ-47 — The monitor does not have to be bright enough to reach the goal illuminance ranks; it may be used to get as close as possible (e.g. all other components dead, or lamps dead and blinds useless because it is dark outside).**
> "This would mean that the monitor does not have to be bright enough to reach the goal illuminance ranks but can be used to get as close as possible (for example when all other components do not work or the lamps do not work and the blinds are useless because it is dark outside)."

---

## Phase 3 — Learning process dynamics (response delays)

### Advisor note (verbatim anchor)
> "And finally (3) we spoke about the opportunity that a learner presents - namely, to learn the process dynamics. you can make a simple implementation where the agent learns the response times (how long does it take to make the room bright after raising the blinds). it adds this knowledge to KG. depending on the time you have left you can elegantly put this to use: goals that also come with temporal specification (make the room bright immediately vs max in 5 mins) will be facilitated by the added knowledge."

**REQ-48 — Exploit the learner's opportunity: learn the process dynamics of the lab.**
> "the opportunity that a learner presents - namely, to learn the process dynamics"

**REQ-49 — Simple implementation: the agent learns response times (e.g. how long it takes to make the room bright after raising the blinds).**
> "you can make a simple implementation where the agent learns the response times (how long does it take to make the room bright after raising the blinds)"

**REQ-50 — The learned dynamics knowledge must be added back to the KG.**
> "it adds this knowledge to KG."

**REQ-51 — A new variable (e.g. "Response Delay") is introduced into the KG, and the Q-Learner learns its accurate value (e.g. 60 seconds for the lamp).**
> "We introduce a new variable into the KG (for example called 'Response Delay'), for which the QLearner will learn the accurate value (60 seconds response delay in the case of the lamp for example)."

**REQ-52 — Optional (time permitting): support goals with temporal specification (e.g. "make the room bright immediately" vs "max in 5 mins"), facilitated by the added dynamics knowledge.**
> "depending on the time you have left you can elegantly put this to use: goals that also come with temporal specification (make the room bright immediately vs max in 5 mins) will be facilitated by the added knowledge."

**REQ-53 — Framing requirement: the thesis must show that stereotypes lack dynamics — there is currently no way to describe lab dynamics (action-to-effect delays) in the KG via stereotypes — and that this gap motivates Phase 3.**
> "The Stereotypes lack dynamics (this is what we show in the first part of the thesis where we let the agent fail in the weakness lab due to introducing dynamics into the lab, creating the more complex scenarios), meaning there is no way currently to describe inside the KG using the Stereotypes, any dynamics that occur in the lab."

**REQ-54 — Definition constraint: "dynamics" means delays between the agent's interaction with a component and the effect occurring (e.g. light turns on only after a one-minute delay).**
> "In our context 'dynamics' refers to delays between the agent interacting with a component (like turning it on or off) and the effect to happen (like the light might only turn on after a delay of one minute for example)."

---

## Summary counts

| Group | REQs |
|---|---|
| Cross-cutting / meta | REQ-1 … REQ-4 (4) |
| Phase 1 | REQ-5 … REQ-26 (22) |
| Phase 2 | REQ-27 … REQ-47 (21) |
| Phase 3 | REQ-48 … REQ-54 (7) |
| **Total** | **54** |
