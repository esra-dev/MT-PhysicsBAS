import React, { useMemo, useState } from 'react';
import { LABS, offState } from '../lib/physics.js';
import Sandbox from '../components/Sandbox.jsx';
import Replay from '../components/Replay.jsx';
import { HBarChart, Legend, Tile } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';

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

function RegisteredFamily({ rows }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data">
        <thead><tr><th>registered member</th><th className="num">KG</th>
          <th className="num">TR</th><th className="num">mean Δ</th>
          <th className="num">95% CI</th><th className="num">exact p</th>
          <th className="num">BH q</th><th>verdict</th></tr></thead>
        <tbody>{rows.map((row) => (
          <tr key={row.name} className={row.verdict === 'supported' ? 'hl' : ''}>
            <td>{row.name}</td>
            <td className="num">{fmt(row.mean_ql_true, 4)}</td>
            <td className="num">{fmt(row.mean_ql_false, 4)}</td>
            <td className="num">{fmt(row.mean, 5)}</td>
            <td className="num">[{fmt(row.ci_lo, 5)}, {fmt(row.ci_hi, 5)}]</td>
            <td className="num">{fmt(row.p, 7)}</td>
            <td className="num">{fmt(row.q, 7)}</td>
            <td>{row.verdict}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function LadderTrend({ rows }) {
  return (
    <div className="card">
      <h3>The ladder-growth prediction did not survive the correction</h3>
      <div style={{ overflowX: 'auto' }}>
        <table className="data">
          <thead><tr><th>depth contrast (Δ of per-seed Δs)</th><th>role</th>
            <th className="num">mean</th><th className="num">95% CI</th>
            <th className="num">exact p</th></tr></thead>
          <tbody>{rows.map((row) => (
            <tr key={row.contrast}>
              <td>{row.contrast.replaceAll('_', ' ')}</td>
              <td>{row.role === 'registered_ordered_secondary' ? 'registered secondary' : 'descriptive'}</td>
              <td className="num">{fmt(row.mean, 5)}</td>
              <td className="num">[{fmt(row.ci_lo, 5)}, {fmt(row.ci_hi, 5)}]</td>
              <td className="num">{fmt(row.p, 3)}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <p className="note">The withdrawn record showed the redundancy advantage growing monotonically with
        dependency depth (−0.33 / −0.93 / −1.46). Under the corrected protocol the advantage is
        approximately <b>constant (~−0.7) at every depth</b> — every depth contrast is null. The
        monotone pattern was an artifact of the defective scheduler, not a property of dependency depth.</p>
    </div>
  );
}

function EnergyResult({ lab5 }) {
  const groups = [{
    name: 'energy compliance',
    note: 'goal reached AND steady power ≤ budget (higher better; n = 20 seeds)',
    bars: [
      { label: 'KG-primed', value: lab5.mean_ql_true, color: 'var(--kg)' },
      { label: 'tabula-rasa', value: lab5.mean_ql_false, color: 'var(--tr)' },
    ],
  }];
  return (
    <>
      <Legend items={[
        { color: 'var(--kg)', label: 'KG-primed (ql_true, n = 20 seeds)' },
        { color: 'var(--tr)', label: 'tabula-rasa (ql_false, n = 20 seeds)' }]} />
      <HBarChart groups={groups} xMax={1} fmt={(v) => fmt(v, 3)} />
      <p className="note">
        The energy cost is <b>not in the reward</b> — the only path to energy-awareness is the KG's
        <code> ws:energyCost</code> datasheet (efficient lamp 1, inefficient 4, spotlight 2, blinds 0),
        applied as a non-fading prior on greedy action choice. The corrected benefit
        (+{fmt(lab5.mean, 4)}, q = {fmt(lab5.q, 4)}) is smaller than the withdrawn +0.096 but remains
        supported. Compliance uses the deterministic steady power of the final actuator state against
        the per-scenario budget — never the withdrawn wall-clock accumulator.
      </p>
    </>
  );
}

export default function Phase4() {
  const [labId, setLabId] = useState('lab4');
  const { data } = useData('phase4.json');
  const lab = LABS[labId];
  if (!data) return <p className="loading">loading corrected Phase 4 evidence…</p>;
  const lab5 = data.registered_family.find((row) => row.cell === 'lab5');
  return (
    <div className="page">
      <h1>Phase 4 · The Knowledge Ladder</h1>
      <div className="q"><b>Current evidence:</b> protocol <code>{data.run_mode}</code>, runs {data.runs.seeds_1_10} +
        {' '}{data.runs.seeds_11_20}, 20 paired seeds, fixed 3,000-episode training, registered m=4 family.</div>
      <div className="warn"><b>Protocol-v1 results are withdrawn.</b> The former ladder-growth headline
        (−0.33/−0.93/−1.46) and all wall-clock energy figures are historical only — see
        docs/PHASE4_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md.</div>
      <div className="q"><b>Question:</b> can the KG encode facts a tabula-rasa learner <b>fundamentally cannot
        see</b> — a hidden wiring dependency and a per-device energy datasheet — and does the primed agent
        measurably exploit them?</div>

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
          <div className="card">
            <EnergyResult lab5={lab5} />
          </div>
        </>
      )}

      <h2>Registered family of four (corrected)</h2>
      <div className="card">
        <RegisteredFamily rows={data.registered_family} />
        <p className="note">Two-sided exact paired sign-flip tests over seeds 1–20; bootstrap intervals estimate
          means; BH correction is applied once across these four rows. Negative Δ is favourable for the
          redundancy cells, positive for lab5 energy compliance. The corrected claim: knowing the dependency
          structure buys a stable reduction in redundant actuation wherever a hidden gate exists, and the
          energy datasheet buys a small within-budget gain — all simulator-conditional.</p>
      </div>

      <LadderTrend rows={data.ladder_trend} />

      <p className="note">Sources: runs {data.runs.seeds_1_10} and {data.runs.seeds_11_20};
        {' '}<code>{data.source}</code>; docs/PHASE4_DEPENDENCY_LADDER.md §11.</p>
    </div>
  );
}
