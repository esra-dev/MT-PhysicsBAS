import React, { useMemo, useState } from 'react';
import { LABS, offState } from '../lib/physics.js';
import Sandbox from '../components/Sandbox.jsx';
import Replay from '../components/Replay.jsx';
import { HBarChart, Legend, Tile } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';

// Certified n = 20 results, CI run 27905392725 (docs/PHASE4.md §10a).
const LAB5_CERT = [
  { metric: 'energy_compliance', t: 0.784, f: 0.683, d: '+0.101', ci: '[0.066, 0.138]', p: '0.00093', delta: '0.69', q: '≈0', primary: true },
  { metric: 'mean_steady_power', t: 1.148, f: 1.539, d: '−0.391', ci: '[−0.599, −0.183]', p: '0.0038', delta: '−0.47', q: '0.00024' },
  { metric: 'over_budget_rate', t: 0.208, f: 0.298, d: '−0.090', ci: '[−0.131, −0.051]', p: '0.00092', delta: '−0.64', q: '≈0' },
  { metric: 'goal_rate', t: 0.991, f: 0.975, d: '+0.016', ci: '[−0.003, 0.034]', p: '0.13 (ns)', delta: '0.21', q: '—' },
];
const LAB4_CERT = [
  { metric: 'avg_steps', d: '−0.496', p: '0.0045', delta: '−0.43', q: '≈0' },
  { metric: 'avg_dev', d: '−0.589', p: '0.0089', delta: '−0.51', q: '≈0' },
  { metric: 'avg_wasted', d: '−0.504', p: '0.0051', delta: '−0.46', q: '≈0' },
  { metric: 'avg_redundant', d: '−0.558', p: '0.0051', delta: '−0.44', q: '≈0' },
  { metric: 'goal / energy compliance', d: '+0.023', p: '0.014', delta: '0.35', q: '0.00024' },
];

function Lab4Trap() {
  const lab = LABS.lab4;
  const trap = useMemo(() => ({ ...offState(lab), Z1Light: true, PlugZ1: false }), []);
  return (
    <div className="card">
      <div className="cardhead">
        <h3>The signature trap — lamp switch ON, smart plug OFF</h3>
        <span className="hint">benchmark scenarios 3 & 11 start exactly like this</span>
      </div>
      <p className="note" style={{ marginTop: 0 }}>
        Z1 stays dark although its lamp switch is already ON — the fix is to toggle the <b>plug</b>, not the lamp.
        The KG holds <code>PlugZ1 ws:powerGates Z1Light</code>, so the primed agent enables the plug first; the tabula-rasa
        agent flips a lamp that does nothing and pays the no-effect penalty. Try it: turn the plug on.
      </p>
      <Sandbox lab={lab} initial={trap} initialSun={0} showPower budget={null} />
    </div>
  );
}

function EnergyResults() {
  const { data } = useData('phase4.json');
  const llm = data?.llm_summary?.find((r) => r.profile === 'lab5');
  const groups = [
    {
      name: 'energy compliance',
      note: 'goal reached AND steady power ≤ budget (higher better)',
      bars: [
        { label: 'KG-primed', value: 0.784, color: 'var(--kg)' },
        { label: 'tabula-rasa', value: 0.683, color: 'var(--tr)' },
        { label: 'LLM (general knowledge)', value: llm ? +llm.energy_compliance : 0.556, color: 'var(--ctx)' },
      ],
    },
    {
      name: 'steady-state power',
      note: 'power units after the episode settles (lower better, budget = 2)',
      bars: [
        { label: 'KG-primed', value: 1.148, color: 'var(--kg)' },
        { label: 'tabula-rasa', value: 1.539, color: 'var(--tr)' },
        { label: 'LLM (general knowledge)', value: llm ? +llm.mean_steady_power : 3.39, color: 'var(--ctx)' },
      ],
    },
  ];
  return (
    <>
      <Legend items={[
        { color: 'var(--kg)', label: 'KG-primed (ql_true, n = 20 seeds)' },
        { color: 'var(--tr)', label: 'tabula-rasa (ql_false, n = 20 seeds)' },
        { color: 'var(--ctx)', label: 'LLM proxy (deterministic, exploratory)' }]} />
      <HBarChart groups={groups} xMax={4} fmt={(v) => fmt(v, 2)} />
      <p className="note">
        The energy cost is <b>not in the reward</b> — the only path to energy-awareness is the KG's
        <code> ws:energyCost</code> datasheet (efficient lamp 1, inefficient 4, spotlight 2, blinds 0), applied as a
        non-fading prior on greedy action choice. The LLM proxy reaches the goal but, without the lab-specific datasheet,
        lands on the inefficient lamp: seed-1 trace for scenario 1 is <code>SetZ1Ineff, SetZ2Ineff</code> → power 8, budget 2.
        LLM rows are single deterministic outputs (no CI) — illustrative framing, not a confirmatory test.
      </p>
      <details className="tblview"><summary>table view — certified lab5 paired tests (n = 20, run 27905392725)</summary><div className="inner">
        <table className="data">
          <thead><tr><th>metric</th><th className="num">KG</th><th className="num">TR</th><th className="num">Δ</th><th className="num">95% CI</th><th className="num">Wilcoxon p</th><th className="num">Cliff δ</th><th className="num">BH q</th></tr></thead>
          <tbody>
            {LAB5_CERT.map((r) => (
              <tr key={r.metric} className={r.primary ? 'hl' : ''}>
                <td>{r.metric}{r.primary ? ' (primary)' : ''}</td>
                <td className="num">{r.t}</td><td className="num">{r.f}</td><td className="num">{r.d}</td>
                <td className="num">{r.ci}</td><td className="num">{r.p}</td><td className="num">{r.delta}</td><td className="num">{r.q}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div></details>
    </>
  );
}

export default function Phase4() {
  const [labId, setLabId] = useState('lab4');
  const lab = LABS[labId];
  return (
    <div className="page">
      <h1>Phase 4 · The Knowledge Ladder</h1>
      <div className="q"><b>Question (the thesis core):</b> can the KG encode facts a tabula-rasa learner <b>fundamentally cannot
        see</b> — a hidden wiring dependency and a per-device energy datasheet — and does the primed agent exploit them,
        provably, better than an LLM's general knowledge?</div>

      <div className="toolbar" role="tablist">
        {['lab4', 'lab5'].map((id) => (
          <button key={id} type="button" role="tab" aria-selected={labId === id}
            className={`btn ${labId === id ? 'primary' : ''}`} onClick={() => setLabId(id)}>
            {LABS[id].name}
          </button>
        ))}
      </div>
      <p className="lede" style={{ marginTop: 0 }}>{lab.tagline} · {lab.states.toLocaleString('en-US')} states · port {lab.port}</p>

      {labId === 'lab4' ? (
        <>
          <Lab4Trap />
          <div className="card">
            <div className="cardhead"><h3>Full sandbox</h3><span className="hint">the plug draws no power itself — it only gates the lamp</span></div>
            <Sandbox lab={lab} showPower />
            <p className="note"><b>What the KG encodes:</b> {lab.kg}</p>
          </div>
          <div className="card">
            <Replay lab={lab} title="Replay — watch the tabula-rasa agent fight the AND-gate" />
          </div>
          <h2>Certified result — efficiency under a hidden dependency (n = 20)</h2>
          <div className="card">
            <div style={{ overflowX: 'auto' }}>
              <table className="data">
                <thead><tr><th>metric (Δ = KG − TR, lower better except last)</th><th className="num">Δ</th><th className="num">Wilcoxon p</th><th className="num">Cliff δ</th><th className="num">BH q</th></tr></thead>
                <tbody>{LAB4_CERT.map((r) => (
                  <tr key={r.metric}><td>{r.metric}</td><td className="num">{r.d}</td><td className="num">{r.p}</td><td className="num">{r.delta}</td><td className="num">{r.q}</td></tr>
                ))}</tbody>
              </table>
            </div>
            <p className="note">Both arms eventually solve lab4 (goal-rate parity is the design) — the finding is the KG arm gets
              there with materially <b>fewer steps, less deviation, and fewer wasted/redundant actions</b>, because it never
              wastes moves on a power-gated lamp. Source: run 27905392725, docs/PHASE4.md §10a.</p>
          </div>
        </>
      ) : (
        <>
          <div className="card">
            <div className="cardhead">
              <h3>Sandbox — two lamps, same light, 4× the power</h3>
              <span className="hint">watch the power meter vs the budget of 2</span>
            </div>
            <Sandbox lab={lab} showPower budget={lab.energyBudget} initialSun={0} />
            <p className="note"><b>What the KG encodes:</b> {lab.kg}</p>
          </div>
          <div className="card">
            <Replay lab={lab} title="Replay — which lamp does each agent reach for?" />
          </div>
          <h2>Certified result — energy compliance only the KG can buy (n = 20)</h2>
          <div className="tiles">
            <Tile label="energy compliance (primary endpoint)" value="0.784"
              delta="vs 0.683 tabula-rasa · Wilcoxon p = 0.00093 · Cliff δ = 0.69" deltaDir="up" />
            <Tile label="steady-state power" value="1.15" unit="units"
              delta="vs 1.54 tabula-rasa (−25%) · vs 3.4 LLM proxy (−66%)" deltaDir="up" />
            <Tile label="goal-rate cost of the energy win" value="none"
              delta="+0.016 (ns) — the saving is not bought with failures" deltaDir="flat" />
          </div>
          <div className="card">
            <EnergyResults />
          </div>
        </>
      )}
    </div>
  );
}
