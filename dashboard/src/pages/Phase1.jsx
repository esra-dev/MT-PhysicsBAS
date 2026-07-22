import React, { useState } from 'react';
import { LABS } from '../lib/physics.js';
import Sandbox from '../components/Sandbox.jsx';
import { Tile } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';

const P1_LABS = ['lab1', 'lab2', 'lab3'];

function LabTabs({ cur, set }) {
  return (
    <div className="toolbar" role="tablist">
      {P1_LABS.map((id) => (
        <button key={id} type="button" role="tab" aria-selected={cur === id}
          className={`btn ${cur === id ? 'primary' : ''}`} onClick={() => set(id)}>
          {LABS[id].name}
        </button>
      ))}
    </div>
  );
}

function LabResult({ labId, data }) {
  const row = data.labs[labId];
  const isLab1 = labId === 'lab1';
  const isLab2 = labId === 'lab2';
  return (
    <>
      <h3>{row.headline}</h3>
      <div className="tiles">
        <Tile label="training auc_goal Δ (true − false)"
          value={fmt(row.auc_goal, 6)}
          delta={isLab1 ? 'exact saturated null' : 'fraction of 3,000 successful training episodes'}
          deltaDir={row.auc_goal > 0 ? 'up' : (row.auc_goal < 0 ? 'down' : 'flat')} />
        <Tile label="first-goal presentations Δ"
          value={fmt(row.first_goal_presentations, 3)}
          delta="negative is earlier; includes terminal starts and censoring"
          deltaDir={row.first_goal_presentations < 0 ? 'up' : 'flat'} />
        {!isLab1 && <Tile label="benchmark goal-rate Δ"
          value={fmt(row.benchmark_goal_rate, 5)}
          delta="registered descriptive"
          deltaDir={row.benchmark_goal_rate > 0 ? 'up' : 'flat'} />}
        {!isLab1 && <Tile label="deterministic policy-energy Δ"
          value={fmt(row.benchmark_policy_energy, 4)}
          delta="policy-cost units, not watt-hours; lower is better"
          deltaDir={row.benchmark_policy_energy < 0 ? 'up' : 'down'} />}
        {!isLab1 && <Tile label="benchmark cycling Δ"
          value={fmt(row.benchmark_cycling, 5)}
          delta={isLab2 ? 'descriptively lower' : 'registered primary: null'}
          deltaDir={row.benchmark_cycling < 0 ? 'up' : 'flat'} />}
      </div>
    </>
  );
}

function RegisteredFamily({ rows }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data">
        <thead><tr><th>registered member</th><th className="num">mean Δ</th>
          <th className="num">95% CI</th><th className="num">exact p</th>
          <th className="num">BH q</th><th>verdict</th></tr></thead>
        <tbody>{rows.map((row) => (
          <tr key={row.name} className={row.verdict === 'supported' ? 'hl' : ''}>
            <td>{row.name}</td>
            <td className="num">{fmt(row.mean, 6)}</td>
            <td className="num">[{fmt(row.ci_lo, 6)}, {fmt(row.ci_hi, 6)}]</td>
            <td className="num">{fmt(row.p, 7)}</td>
            <td className="num">{fmt(row.q, 7)}</td>
            <td>{row.verdict}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export default function Phase1() {
  const [labId, setLabId] = useState('lab2');
  const { data } = useData('phase1.json');
  const lab = LABS[labId];
  if (!data) return <p className="loading">loading corrected Phase 1 evidence…</p>;
  return (
    <div className="page">
      <h1>Phase 1 · Corrected Clean-Lab Experiment</h1>
      <div className="q"><b>Current evidence:</b> protocol <code>{data.protocol_version}</code>,
        20 paired seeds, fixed 3,000-episode training, four registered controls.</div>
      <div className="warn"><b>Protocol-v1 results are withdrawn.</b> The former
        +53.30-episode first-goal and wall-clock-energy claims are historical only.</div>

      <LabTabs cur={labId} set={setLabId} />
      <p className="lede" style={{ marginTop: 0 }}>{lab.tagline} · {lab.states.toLocaleString('en-US')} states</p>
      <div className="card">
        <div className="cardhead"><h3>Physics sandbox</h3>
          <span className="hint">current simulator equations</span></div>
        <Sandbox lab={lab} />
        <p className="note"><b>KG content:</b> {lab.kg}</p>
      </div>

      <div className="card"><LabResult labId={labId} data={data} /></div>

      <h2>Registered family of five</h2>
      <div className="card">
        <RegisteredFamily rows={data.registered_family} />
        <p className="note">Two-sided paired sign-flip tests; bootstrap intervals estimate
          means; BH correction is applied once across these five rows. No bootstrap
          pseudo-p-values are used.</p>
      </div>

      <div className="card">
        <h3>Attribution and controls</h3>
        <p>Redundancy-only reproduces <b>{fmt(100 * data.decomposition.redundancy_share, 1)}%</b>
          of arm C's lab2 mean effect: “most” under the frozen rule. Arm C still has a
          smaller positive residual. Baseline and PBRS-only have zero nonzero corrected
          label contrasts; only the withdrawn timing-dependent energy diagnostic varies.</p>
        <p className="note">The lab3 deterministic policy-energy increase is adverse but
          descriptive. Policy-cost weights are arbitrary and are not watt-hours. These toy
          simulations do not establish real-building benefit or the necessity of RDF/SPARQL.</p>
        <p className="note">Sources: runs 29848584965, 29848587274, 29848589682, and
          29848592010; <code>docs/phase1_results_v2.md</code>.</p>
      </div>
    </div>
  );
}
