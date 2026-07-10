import React, { useEffect, useMemo, useRef, useState } from 'react';
import LabView from './LabView.jsx';
import { LABS, FAULTS, offState, rankOf } from '../lib/physics.js';
import { AlertIcon } from './icons.jsx';

// real detection constants from the agent (illuminance_controller_agent_adapt.asl)
const MIN_SAMPLES = 20;
const DEAD_RATE = 0.80;

const STAGES = ['monitor', 'evidence', 'blacklist', 'alert', 'warm restart', 're-learn'];

// smallest set of surviving actuators that reaches every target at this sun
function recoveredPolicy(lab, faults, blacklist, sun) {
  const survivors = lab.actuators.map((a) => a.id).filter((id) => !blacklist.has(id));
  const n = survivors.length;
  let best = null;
  for (let mask = 0; mask < (1 << n); mask += 1) {
    const s = offState(lab);
    let bits = 0;
    for (let i = 0; i < n; i += 1) if (mask & (1 << i)) { s[survivors[i]] = true; bits += 1; }
    const lux = lab.compute(s, sun, faults);
    const ok = lab.zones.every((z) => rankOf(lux[z]) === lab.targets[z]);
    if (ok && (best === null || bits < best.bits)) best = { state: s, bits };
  }
  return best ? best.state : null;
}

export default function FaultLab() {
  const [profileId, setProfileId] = useState('lab3_f1dead');
  const profile = FAULTS[profileId];
  const lab = LABS[profile.base];
  const faultyIds = Object.keys(profile.faults);

  const [samples, setSamples] = useState({});     // id -> n observations
  const [blacklist, setBlacklist] = useState(new Set());
  const [log, setLog] = useState([]);
  const [stageIdx, setStageIdx] = useState(0);
  const [recovered, setRecovered] = useState(null);
  const [sun] = useState(900);
  const consoleRef = useRef(null);

  const reset = () => {
    setSamples({}); setBlacklist(new Set()); setLog([]); setStageIdx(0); setRecovered(null);
  };
  useEffect(reset, [profileId]);
  useEffect(() => {
    if (consoleRef.current) consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
  }, [log]);

  const observe = (times = 1) => {
    let s = { ...samples };
    const lines = [];
    for (let k = 0; k < times; k += 1) {
      for (const id of faultyIds) {
        if (blacklist.has(id)) continue;
        const n = (s[id] || 0) + 1;
        s[id] = n;
        const kind = profile.faults[id];
        const obs = kind === 'dead' ? '±0 lux' : 'NEGATIVE Δ';
        if (times === 1 || n % 5 === 0 || n >= MIN_SAMPLES) {
          lines.push({ cls: 'row', html: `actuate ${id}=ON   <span class="pred">KG predicts Δ +400 lux (Causes)</span> · <span class="obs-bad">observed ${obs}</span> · dead-evidence ${n}/${MIN_SAMPLES} (rate 1.00 ≥ ${DEAD_RATE})` });
        }
      }
      if (Object.values(s).some((n) => n >= MIN_SAMPLES)) break;
    }
    const detected = faultyIds.filter((id) => (s[id] || 0) >= MIN_SAMPLES && !blacklist.has(id));
    setSamples(s);
    if (detected.length) {
      const bl = new Set(blacklist);
      detected.forEach((id) => bl.add(id));
      setBlacklist(bl);
      detected.forEach((id) => {
        lines.push({ cls: 'sys', html: `[FAULT] DEFECTIVE component Set${id} — dead-rate 1.00 over ${MIN_SAMPLES} samples ⇒ BLACKLIST (remove ON+OFF actions)` });
        lines.push({ cls: 'sys', html: `[ALERT] user notified · warmRestart: drop Q(·, Set${id}), decay poisoned states ×0.5, ε ← max(ε, 0.30), re-prime prior over survivors` });
      });
      const remaining = faultyIds.filter((id) => !bl.has(id));
      setStageIdx(remaining.length ? 1 : 4);
    } else {
      setStageIdx(1);
    }
    setLog((l) => [...l, ...lines]);
  };

  const relearn = () => {
    const pol = recoveredPolicy(lab, profile.faults, blacklist, sun);
    setRecovered(pol);
    setStageIdx(5);
    setLog((l) => [...l, {
      cls: 'sys',
      html: pol
        ? `re-learned over survivors: ${Object.entries(pol).filter(([, v]) => v).map(([k]) => k).join(' + ') || 'nothing needed'} reaches every target at sun ${sun} — recovery complete`
        : `no surviving combination reaches the targets — best-effort degradation (alert stands, agent holds the best reachable rank)`,
    }]);
  };

  const allDetected = faultyIds.every((id) => blacklist.has(id));
  const stage = allDetected ? (recovered !== null ? 5 : 4) : stageIdx;
  const viewState = recovered || offState(lab);

  return (
    <div className="card">
      <div className="cardhead">
        <h3>Live fault walk-through — detect, blacklist, alert, re-learn</h3>
        <span className="hint">real thresholds: ≥{MIN_SAMPLES} samples · dead-rate ≥ {DEAD_RATE} (agent constants)</span>
      </div>

      <div className="toolbar">
        <select className="btn" value={profileId} onChange={(e) => setProfileId(e.target.value)} aria-label="fault profile">
          {Object.entries(FAULTS).map(([id, f]) => <option key={id} value={id}>{f.label}</option>)}
        </select>
        <button type="button" className="btn ghost" onClick={reset}>reset</button>
      </div>
      <p className="note" style={{ marginTop: 0 }}>{profile.note} The KG still believes the <i>nominal</i> physics — that mismatch is exactly the detection signal.</p>

      <div className="pipeline" aria-label="detection pipeline">
        {STAGES.map((s, i) => (
          <React.Fragment key={s}>
            {i > 0 && <span className="arr">→</span>}
            <span className={`stage ${i < stage ? 'done' : ''} ${i === stage ? 'now' : ''}`}>{s}</span>
          </React.Fragment>
        ))}
      </div>

      <div className="grid2">
        <div>
          <LabView lab={lab} state={viewState} sun={sun} faults={profile.faults}
            blacklist={[...blacklist]} />
        </div>
        <div>
          <div className="toolbar" style={{ marginTop: 0 }}>
            <button type="button" className="btn primary" onClick={() => observe(1)} disabled={allDetected}>
              actuate faulty lamp once
            </button>
            <button type="button" className="btn" onClick={() => observe(MIN_SAMPLES)} disabled={allDetected}>
              fast-forward to detection
            </button>
            <button type="button" className="btn" onClick={relearn} disabled={!allDetected || recovered !== null}>
              re-learn with survivors
            </button>
          </div>
          <div className="console" ref={consoleRef}>
            {log.length === 0 && <div className="row">// each actuation compares the KG-predicted Δ against the observed Δ…</div>}
            {log.map((l, i) => <div key={i} className={`row ${l.cls}`} dangerouslySetInnerHTML={{ __html: l.html }} />)}
          </div>
          {allDetected && (
            <div className="alertbanner">
              <AlertIcon />
              <span><b>[FAULT] DEFECTIVE {faultyIds.map((id) => `Set${id}`).join(', ')}.</b> Component{faultyIds.length > 1 ? 's' : ''} blacklisted
                and the user alerted. The agent does <b>not</b> silently adapt around broken physics — it prunes the action
                space, warm-restarts (Q-column dropped, poisoned states decayed, ε boosted to 0.30) and re-learns over the survivors.</span>
            </div>
          )}
          {recovered && (
            <p className="note"><b>Recovered policy shown on the left</b> — the smallest surviving actuator set that reaches
              every target at sun {sun}: {Object.entries(recovered).filter(([, v]) => v).map(([k]) => k).join(' + ') || 'none needed'}.</p>
          )}
        </div>
      </div>
    </div>
  );
}
