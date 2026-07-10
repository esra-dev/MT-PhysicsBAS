import React, { useMemo, useState } from 'react';
import { LABS } from '../lib/physics.js';
import Sandbox from '../components/Sandbox.jsx';
import Replay from '../components/Replay.jsx';
import { LineChart, Legend, Tile } from '../components/charts.jsx';
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

function EarlyTraining({ labId }) {
  const { data } = useData('training.json');
  const series = useMemo(() => {
    if (!data || !data[labId]) return null;
    const mk = (arm, color, name) => ({
      name, color,
      points: (data[labId][arm]?.episodes || []).map((e) => ({
        x: e.ep, y: e.steps, extra: e.goal ? 'goal reached' : 'goal missed (cap 20)',
      })),
    });
    return [mk('ql_false', 'var(--tr)', 'tabula-rasa'), mk('ql_true', 'var(--kg)', 'KG-primed')];
  }, [data, labId]);
  if (!series) return <p className="loading">loading training…</p>;
  return (
    <>
      <Legend items={[{ color: 'var(--kg)', label: 'KG-primed (ql_true)' }, { color: 'var(--tr)', label: 'tabula-rasa (ql_false)' }]} />
      <LineChart series={series} xLabel="training episode" yLabel="steps to goal (20 = failed)" yMax={21} />
      <p className="note">First 50 training episodes, seed 1 (single-seed illustration — the confirmatory n = 10 curves are below).
        Lower is better; a low flat blue line from episode 0 is the prior doing its job.</p>
      <details className="tblview"><summary>table view</summary><div className="inner">
        <table className="data"><thead><tr><th>episode</th><th className="num">KG-primed steps</th><th className="num">tabula-rasa steps</th></tr></thead>
          <tbody>{series[1].points.map((p, i) => (
            <tr key={p.x}><td>{p.x}</td><td className="num">{p.y}</td><td className="num">{series[0].points[i]?.y ?? '–'}</td></tr>
          ))}</tbody></table>
      </div></details>
    </>
  );
}

function Stats({ labId }) {
  const { data } = useData('phase1.json');
  if (!data) return <p className="loading">loading stats…</p>;
  const rows = data.learning_speed.filter((r) => r.profile === labId);
  const pick = (m) => rows.find((r) => r.metric === m);
  const auc = pick('auc_goal'); const first = pick('mean_first_goal');
  const sig = auc && +auc.q_bootstrap_bh < 0.05;
  const bench = data.summary_ci.filter((r) => r.profile === labId && r.mode !== 'rule_based');
  const b = (mode, k) => { const r = bench.find((x) => x.mode === mode); return r ? +r[k] : null; };
  return (
    <>
      <div className="tiles">
        <Tile label="learning-speed AUC (goal-rate) Δ true−false — the primary endpoint"
          value={auc ? (+auc.mean_diff_true_minus_false).toFixed(3) : '–'}
          delta={auc ? `95% CI [${fmt(+auc.ci_lo, 3)}, ${fmt(+auc.ci_hi, 3)}] · BH q = ${fmt(+auc.q_bootstrap_bh, 4)}${sig ? ' — significant' : ' (no headroom in this trivial lab)'}` : ''}
          deltaDir={sig ? 'up' : 'flat'} />
        <Tile label="mean first-goal episode Δ true−false (negative = KG reaches the goal earlier)"
          value={first ? fmt(+first.mean_diff_true_minus_false, 1) : '–'}
          delta={first ? `95% CI [${fmt(+first.ci_lo, 1)}, ${fmt(+first.ci_hi, 1)}] · q = ${fmt(+first.q_bootstrap_bh, 3)}` : ''}
          deltaDir={first && +first.mean_diff_true_minus_false < 0 && +first.q_bootstrap_bh < 0.05 ? 'up' : 'flat'} />
        <Tile label="final goal-rate (benchmark, both arms)"
          value={`${fmt(100 * b('ql_true', 'goal_rate_mean'), 0)}%`}
          delta={`tabula-rasa ${fmt(100 * b('ql_false', 'goal_rate_mean'), 0)}% — parity by design; the prior buys speed, not a different optimum`}
          deltaDir="flat" />
      </div>
      <h3>Trained-policy benchmark (n = 10 seeds, mean ± bootstrap 95% CI)</h3>
      <div style={{ overflowX: 'auto' }}>
        <table className="data">
          <thead><tr><th>arm</th><th className="num">goal rate</th><th className="num">avg steps</th><th className="num">avg deviation</th><th className="num">avg redundant actions</th></tr></thead>
          <tbody>
            {['ql_true', 'ql_false'].map((m) => (
              <tr key={m} className={m === 'ql_true' ? 'hl' : ''}>
                <td>{m === 'ql_true' ? 'KG-primed' : 'tabula-rasa'}</td>
                <td className="num">{fmt(b(m, 'goal_rate_mean'), 3)}</td>
                <td className="num">{fmt(b(m, 'avg_steps_mean'), 2)} [{fmt(b(m, 'avg_steps_ci_lo'), 2)}, {fmt(b(m, 'avg_steps_ci_hi'), 2)}]</td>
                <td className="num">{fmt(b(m, 'avg_dev_mean'), 2)}</td>
                <td className="num">{fmt(b(m, 'avg_redundant_mean'), 2)} [{fmt(b(m, 'avg_redundant_ci_lo'), 2)}, {fmt(b(m, 'avg_redundant_ci_hi'), 2)}]</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">Source: <code>phase1_headline_download/kg_only</code> — the <b>clean KG-only factorial</b> (prior on vs off,
        shaping off on both arms), 10 paired seeds, bootstrap CIs, BH-FDR. </p>
    </>
  );
}

export default function Phase1() {
  const [labId, setLabId] = useState('lab2');
  const lab = LABS[labId];
  return (
    <div className="page">
      <h1>Phase 1 · The Clean Ladder</h1>
      <div className="q"><b>Question:</b> does priming the Q-learner with the Knowledge Graph make it converge <b>faster</b> than
        an identical tabula-rasa learner, on clean labs where the physics exactly matches the KG?</div>

      <LabTabs cur={labId} set={setLabId} />
      <p className="lede" style={{ marginTop: 0 }}>{lab.tagline} · {lab.states.toLocaleString('en-US')} states · Node-RED port {lab.port}</p>

      <div className="card">
        <div className="cardhead">
          <h3>Physics sandbox — how this lab behaves</h3>
          <span className="hint">click actuators · exact simulator formulas</span>
        </div>
        <Sandbox lab={lab} />
        <p className="note"><b>What the KG encodes here:</b> {lab.kg}</p>
      </div>

      <div className="card">
        <Replay lab={lab} />
      </div>

      <h2>Did the knowledge accelerate learning?</h2>
      <div className="card">
        <h3>Watching the first 50 episodes of training</h3>
        <EarlyTraining labId={labId} />
      </div>
      <div className="card">
        <h3>Confirmatory result — {lab.name}</h3>
        <Stats labId={labId} />
        <h3>Learning curves, n = 10 paired seeds (CI artifact)</h3>
        <img className="figure" src={`${import.meta.env.BASE_URL}data/img/p1_curve_${labId}.png`}
          alt={`n=10 learning curves for ${labId}`} style={{ maxWidth: 720 }} />
        <p className="note">Goal-rate over training episodes, mean over 10 seeds per arm, from the Phase-1 <code>kg_only</code> CI run.
          lab1 is deliberately trivial (both arms solve it almost immediately — a sanity anchor); the KG advantage appears
          exactly when the state space grows (lab2: 1,024 states; lab3: 2,048 states with the spotlight trap).</p>
      </div>
    </div>
  );
}
