import React, { useEffect, useRef, useState } from 'react';
import LabView from './LabView.jsx';
import { SUN_LEVELS, offState } from '../lib/physics.js';

/**
 * Interactive lab: click actuators, pick the episode sun, watch the physics.
 * Optional props:
 *  faults  – {compId: 'dead'|'inverted'} simulator-side fault injection
 *  slow    – {delayTicks, secondsPerTick, delayed: [ids]} phase-3 response delay
 *  initial – preset actuator state; initialSun – preset sun lux
 *  showPower – render the power meter (lab4/lab5); budget – energy budget line
 */
export default function Sandbox({ lab, faults = {}, slow = null, initial = null, initialSun = 400, showPower = false, budget = null }) {
  const [sun, setSun] = useState(initialSun);
  const [commanded, setCommanded] = useState(initial || offState(lab));
  const [applied, setApplied] = useState(initial || offState(lab));
  const [pending, setPending] = useState({}); // id -> ticks left
  const timer = useRef(null);

  // reset when the lab or preset changes
  useEffect(() => {
    const s = initial || offState(lab);
    setCommanded(s); setApplied(s); setPending({});
  }, [lab.id, initial]);

  // phase-3 delay clock: 1 UI tick every 350 ms
  useEffect(() => {
    if (!slow) return undefined;
    timer.current = setInterval(() => {
      setPending((p) => {
        const next = {};
        let changed = false;
        for (const [id, t] of Object.entries(p)) {
          if (t > 1) next[id] = t - 1; else changed = true;
        }
        if (changed) {
          setApplied((a) => {
            const na = { ...a };
            for (const [id, t] of Object.entries(p)) if (t <= 1) na[id] = commandedRef.current[id];
            return na;
          });
        }
        return next;
      });
    }, 350);
    return () => clearInterval(timer.current);
  }, [slow, lab.id]);

  const commandedRef = useRef(commanded);
  commandedRef.current = commanded;

  const toggle = (id) => {
    const nextVal = !commanded[id];
    const nc = { ...commanded, [id]: nextVal };
    setCommanded(nc);
    if (slow && slow.delayed.includes(id)) {
      setPending((p) => ({ ...p, [id]: slow.delayTicks }));
    } else {
      setApplied((a) => ({ ...a, [id]: nextVal }));
    }
  };

  const reset = () => {
    const s = initial || offState(lab);
    setCommanded(s); setApplied(s); setPending({});
  };

  const power = showPower && lab.power ? lab.power(applied) : null;

  return (
    <div>
      <div className="toolbar">
        <div className="sunpick" role="group" aria-label="episode sunshine">
          <span className="sunmeta" style={{ fontSize: 12.5, color: 'var(--muted)' }}>episode sun:</span>
          {SUN_LEVELS.map((s) => (
            <button key={s} type="button" className={`opt ${s === sun ? 'sel' : ''}`} onClick={() => setSun(s)}>
              {s === 0 ? 'night · 0' : `${s} lux`}
            </button>
          ))}
        </div>
        <button type="button" className="btn ghost" onClick={reset} style={{ marginLeft: 'auto' }}>reset</button>
      </div>

      <LabView lab={lab} state={applied} sun={sun} faults={faults}
        pending={pending} onToggle={toggle}
        power={power} budget={budget} />

      <div className="formula" style={{ marginTop: 10 }}>{lab.formula}</div>
      {slow && (
        <p className="note">
          Motorized blinds take <b>{slow.delayTicks} ticks × {slow.secondsPerTick} s = {slow.delayTicks * slow.secondsPerTick} s of simulated time</b> to
          actuate (animated here at ~3 ticks/s); lamps and the spotlight act on the next tick. This delay exists only in the
          simulator — the static KG doesn't know it until the agent measures it and writes <code>ws:responseDelay</code> back.
        </p>
      )}
    </div>
  );
}
