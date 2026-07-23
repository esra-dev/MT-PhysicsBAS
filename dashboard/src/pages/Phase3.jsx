import React, { useState } from 'react';
import { LABS, SLOW } from '../lib/physics.js';
import Sandbox from '../components/Sandbox.jsx';
import { HBarChart, Legend, Tile } from '../components/charts.jsx';
import { useData, fmt } from '../lib/useData.js';
import { LampIcon, BlindIcon } from '../components/icons.jsx';

function DeadlinePlanner() {
  const [goal, setGoal] = useState(null); // 'now' | 'later'
  return (
    <div className="card">
      <div className="cardhead">
        <h3>Using the learned delay — deadline-aware planning</h3>
        <span className="hint">sunny episode (sun 900) · both actuators reach bright</span>
      </div>
      <div className="toolbar">
        <span className="sunmeta" style={{ fontSize: 13 }}>Goal:</span>
        <button type="button" className={`btn ${goal === 'now' ? 'primary' : ''}`} onClick={() => setGoal('now')}>“bright immediately”</button>
        <button type="button" className={`btn ${goal === 'later' ? 'primary' : ''}`} onClick={() => setGoal('later')}>“bright within 5 minutes”</button>
      </div>
      {goal && (
        <div className="grid2">
          <div className={`pane ${goal === 'now' ? '' : ''}`} style={{ borderColor: goal === 'now' ? 'var(--good)' : undefined }}>
            <div className="phead"><span className="who"><LampIcon on size={18} /> Lamp</span>
              {goal === 'now' && <span className="chip ok">chosen</span>}</div>
            <p className="note" style={{ marginTop: 0 }}>learned <code>ws:responseDelay ≈ 5 s</code> (1 tick) · energy 1/tick.
              Meets the deadline instantly{goal === 'later' ? ', but burns energy the blind would save' : ''}.</p>
          </div>
          <div className="pane" style={{ borderColor: goal === 'later' ? 'var(--good)' : undefined }}>
            <div className="phead"><span className="who"><BlindIcon on size={18} /> Blind</span>
              {goal === 'later' && <span className="chip ok">chosen</span>}</div>
            <p className="note" style={{ marginTop: 0 }}>learned <code>ws:responseDelay ≈ 60 s</code> (12 ticks) · energy 0.
              {goal === 'now' ? ' Too slow for “immediately” — correctly rejected.' : ' 60 s < 5 min, so the free daylight harvest wins.'}</p>
          </div>
        </div>
      )}
      {!goal && <p className="note">Pick a goal — the planner reads the <b>learned</b> per-actuator delay from the enriched KG and
        chooses the cheapest actuator that still meets the deadline.</p>}
    </div>
  );
}

function DelayResults() {
  const { data } = useData('phase3.json');
  if (!data) return <p className="loading">loading results…</p>;
  const groups = data.delay.map((r) => ({
    name: `${r.profile} · ${r.mode === 'ql_true' ? 'KG agent' : 'baseline agent'}`,
    note: `slowest ${r.slowest_label.replace('Set', '').replace('=ON', '')} · err ${fmt(+r.abs_err_ticks, 2)} ticks`,
    bars: [
      { label: 'learned blind delay', value: +r.slowest_learned_ticks, color: 'var(--kg)' },
      { label: 'learned lamp/spotlight delay', value: +r.mean_instant_ticks, color: 'var(--ctx)' },
    ],
  }));
  const comp = (profile, mode) => data.compliance.find((r) => r.profile === profile && r.mode === mode);
  return (
    <>
      <HBarChart groups={groups} unit="ticks" refValue={12} refLabel="ground truth: 12 ticks (60 s)"
        fmt={(v) => fmt(v, 1)} xMax={15} />
      <p className="note">The dynamics agent probes each actuator, measures ticks from actuation to observed effect, and writes
        <code> ws:responseDelay</code> back into <code>learned_dynamics_*.ttl</code>. Blinds are recovered at ≈12 ticks
        (max error 0.7 ticks ≈ 3.5 s of simulated time); lamps and spotlight at ≈1 tick, correctly classified instantaneous.</p>

      <h3>Deadline compliance with the learned delays (6 timed goals per lab)</h3>
      <div className="tiles">
        {['lab2_slow', 'lab3_slow'].map((p) => {
          const t = comp(p, 'ql_true'); const f = comp(p, 'ql_false');
          if (!t || !f) return null;
          return (
            <React.Fragment key={p}>
              <Tile label={`${p} — tight deadlines (“immediately”), delay-aware planner`}
                value={`${Math.round(+t.tight_compliance_mean * 100)}%`}
                delta={`delay-blind baseline: ${Math.round(+f.tight_compliance_mean * 100)}% — it opens the blind and the deadline passes while the motor crawls`}
                deltaDir="up" />
              <Tile label={`${p} — mean realised delay on timed goals`}
                value={`${fmt(+t.mean_actual_delay_mean, 0)} s`}
                delta={`baseline ${fmt(+f.mean_actual_delay_mean, 0)} s`}
                deltaDir="up" />
            </React.Fragment>
          );
        })}
      </div>
      <p className="note">Loose deadlines (“within 5 min”) are met by both planners (100%) — the contrast is <i>tight</i> goals,
        where only the delay-aware planner knows the blind cannot deliver in time. Ten replicas per cell under
        protocol phase3-v2 (deterministic planner; replicas sample measurement jitter); reported descriptively,
        not as a significance test. Energy is the deterministic tick-integrated meter (tick-v1) — the withdrawn
        wall-clock accumulator survives only as a labelled legacy diagnostic.</p>
    </>
  );
}

export default function Phase3() {
  const [slowId, setSlowId] = useState('lab2_slow');
  const cfg = SLOW[slowId];
  const lab = LABS[cfg.base];
  return (
    <div className="page">
      <h1>Phase 3 · The Slow Ladder</h1>
      <div className="q"><b>Current evidence:</b> protocol <code>phase3-v2</code>, run 29926328852, replicas 1–10,
        tick-integrated energy (tick-v1). Earlier Phase-3 runs are historical, protocol-affected records —
        see docs/PHASE3_PROTOCOL_AFFECTED_NOTICE_2026-07-22.md.</div>
      <div className="q"><b>Question:</b> the static KG knows <i>what</i> each actuator does but not <i>how fast</i>. Can the agent
        <b> measure</b> each actuator's response delay online, <b>write it back</b> into the KG (<code>ws:responseDelay</code>), and
        <b> use it</b> to satisfy time-bounded goals?</div>

      <div className="toolbar" role="tablist">
        {Object.keys(SLOW).map((id) => (
          <button key={id} type="button" role="tab" aria-selected={slowId === id}
            className={`btn ${slowId === id ? 'primary' : ''}`} onClick={() => setSlowId(id)}>
            {id} <span style={{ opacity: .7 }}>(forks {SLOW[id].base})</span>
          </button>
        ))}
      </div>

      <div className="card">
        <div className="cardhead">
          <h3>Physics sandbox — feel the delay</h3>
          <span className="hint">toggle a blind, then watch the countdown — the lux only moves when the motor finishes</span>
        </div>
        <Sandbox lab={lab} slow={cfg} initialSun={900} />
      </div>

      <DeadlinePlanner />

      <h2>Result — the delay is learnable, and it pays</h2>
      <div className="card">
        <Legend items={[{ color: 'var(--kg)', label: 'delayed actuators (blinds)' }, { color: 'var(--ctx)', label: 'instantaneous actuators (lamps, spotlight)' }]} />
        <DelayResults />
      </div>
    </div>
  );
}
