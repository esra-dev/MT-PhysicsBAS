import React from 'react';
import { Legend } from '../components/charts.jsx';

const MODES = [
  { color: 'var(--kg)', label: 'ql_true — KG-primed Q-learning (the treatment arm)' },
  { color: 'var(--tr)', label: 'ql_false — tabula-rasa Q-learning (the control arm)' },
  { color: 'var(--ctx)', label: 'rule_based — hand-written oracle (reference)' },
];

const PHASES = [
  {
    id: 'phase1', num: 'PHASE 1', title: 'Clean ladder — acceleration',
    body: 'Three strictly clean labs of rising complexity. Does priming the Q-learner with physics knowledge from the KG make it learn faster than the same learner starting from scratch?',
    stat: 'lab2 + lab3: primary learning-speed endpoint significant, q < 0.01 (n = 10 paired seeds)',
  },
  {
    id: 'phase2', num: 'PHASE 2', title: 'Faulty ladder — detect, don’t adapt',
    body: 'A component silently breaks. The agent must notice reality diverging from the KG prior, blacklist the component, alert the user, and re-learn with what survives.',
    stat: 'All 8 registered Tier-1 cells: KG arm recovers significantly faster (max q = 0.0012)',
  },
  {
    id: 'phase3', num: 'PHASE 3', title: 'Slow ladder — learn the dynamics',
    body: 'Blinds take 60 s to move but the static KG doesn’t know it. The agent measures each actuator’s response delay, writes it back into the KG, and plans against deadlines.',
    stat: 'Delay learned to ≤0.7 ticks of truth · tight-deadline compliance 100% vs 50%',
  },
  {
    id: 'phase4', num: 'PHASE 4', title: 'Knowledge ladder — facts only the KG has',
    body: 'A hidden smart-plug dependency and a per-lamp energy datasheet that trial-and-error cannot see. The KG-primed agent exploits both — and beats an LLM’s general knowledge.',
    stat: 'Energy compliance 0.784 vs 0.683 (Wilcoxon p = 0.00093, δ = 0.69, n = 20)',
  },
];

export default function Overview({ go }) {
  return (
    <div className="page">
      <h1>MT-Esra · Knowledge-Guided Reinforcement Learning for Building Automation</h1>
      <p className="lede">
        A JaCaMo multi-agent system controls the lighting of simulated labs (Node-RED). The learner is plain tabular
        Q-learning — the experimental variable is a <b>Knowledge Graph of physics stereotypes</b> (“lamps <i>Cause</i> light;
        blinds <i>Mediate</i> sunshine”) used to prime it. Four phases ask four questions about what that knowledge buys.
      </p>

      <div className="q">
        <b>The core stance:</b> physics priors describe <b>normal</b> physics. They should <b>accelerate</b> learning in clean
        environments — and when something breaks, the agent should <b>detect</b> the fault (reality diverges from the prior),
        not silently learn around it.
      </div>

      <h2>The three agents compared in every lab</h2>
      <Legend items={MODES} />
      <p className="note">Same Q-learner, same reward, same seeds — the only difference between the two learning arms is the KG prior.
        Every headline is the paired within-lab <code>ql_true − ql_false</code> contrast.</p>

      <h2>The four phases</h2>
      <div className="phasecards">
        {PHASES.map((p) => (
          <button type="button" key={p.id} className="phasecard" onClick={() => go(p.id)}>
            <span className="pnum">{p.num}</span>
            <h3>{p.title}</h3>
            <p>{p.body}</p>
            <div className="stat">✓ {p.stat}</div>
          </button>
        ))}
      </div>

      <h2>The lab ladder</h2>
      <div className="ladder">
        <div className="rung"><b>lab1 · Trivial</b>1 zone, 1 lamp · 8 states<br />the smallest acceleration test</div>
        <span className="arrow">→</span>
        <div className="rung"><b>lab2 · Intermediate</b>2 zones · lamp + blind · 1,024 states<br />adds the <i>Mediates(blind, sun)</i> stereotype</div>
        <span className="arrow">→</span>
        <div className="rung"><b>lab3 · Complex</b>+ cross-zone spill + shared spotlight · 2,048 states<br />the template all later labs fork</div>
        <span className="arrow">→</span>
        <div className="rung"><b>Phase 2 forks</b>lab1/2/3 with one silently broken lamp or blind (dead / inverted)</div>
        <span className="arrow">→</span>
        <div className="rung"><b>Phase 3 forks</b>lab2/3_slow — blinds respond after 60 s</div>
        <span className="arrow">→</span>
        <div className="rung"><b>Phase 4</b>lab4 smart-plug AND-gate · 4,096 states<br />lab5 efficient-vs-inefficient lamps · 8,192 states</div>
      </div>
      <p className="note">
        Every lab is a smart-lighting problem: drive each zone to its target brightness rank (0 dark · 1 dim · 2 medium ·
        3 bright, bounds 50/100/300 lux) within a 20-step episode. Sunshine is pinned per episode from {'{0, 100, 400, 900}'} lux —
        blinds only harvest daylight, which is the central sun-conditioned stereotype. Each phase page has an <b>interactive
        physics sandbox</b> (click the actuators!), a <b>replay of the real trained agents</b> side by side, and the
        <b> statistical findings</b> from the multi-seed CI runs.
      </p>

      <h2>How a decision flows</h2>
      <div className="ladder">
        <div className="rung"><b>Node-RED simulator</b>ground-truth physics per lab (the formulas shown in each sandbox)</div>
        <span className="arrow">→</span>
        <div className="rung"><b>CArtAgO artifacts</b>WoT Thing Description actions · SPARQL over the KG</div>
        <span className="arrow">→</span>
        <div className="rung"><b>Jason BDI agent</b>tabular Q-learning; the KG prior biases Q-init / action priors</div>
        <span className="arrow">→</span>
        <div className="rung"><b>Knowledge Graph</b>BRICK topology + stereotype mechanisms (Causes / Mediates, powerGates, energyCost)</div>
      </div>
    </div>
  );
}
