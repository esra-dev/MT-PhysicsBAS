import React from 'react';
import { rankOf, sunRank, RANK_NAMES } from '../lib/physics.js';
import { actuatorIcon, SunIcon, MoonIcon } from './icons.jsx';

function ActRow({ act, on, fault, blacklisted, pendingTicks, onToggle, disabled }) {
  const cls = ['actrow', on ? 'on' : 'off', fault ? 'fault' : '', blacklisted ? 'blacklisted' : '']
    .filter(Boolean).join(' ');
  const body = (
    <>
      <span className="aicon">{actuatorIcon(act.kind, on && !blacklisted)}</span>
      <span className="alabel">{act.label}</span>
      {fault && <span className="fbadge">{fault === 'dead' ? 'DEAD' : 'INVERTED'}</span>}
      {blacklisted && <span className="fbadge" style={{ background: '#52514e' }}>BLACKLISTED</span>}
      {pendingTicks > 0 && <span className="pending">moving · {pendingTicks} ticks</span>}
      <span className="amech">{act.mech}</span>
      <span className="astate">{on ? 'ON' : 'OFF'}</span>
    </>
  );
  if (onToggle && !disabled) {
    return (
      <button type="button" className={cls} onClick={() => onToggle(act.id)}
        title={`${act.id} — click to switch ${on ? 'off' : 'on'}`}>
        {body}
      </button>
    );
  }
  return <div className={cls}>{body}</div>;
}

/**
 * Visual state of one lab: sun strip, zone cards (lux, rank meter, target),
 * per-zone actuators, shared actuators below.
 *
 * props:
 *  lab        – lab definition (physics.js)
 *  state      – actuator flags {Z1Light: true, ...}
 *  sun        – sun lux (number)
 *  lux        – optional {Z1: lux, Z2: lux}; computed from physics if omitted
 *  faults     – {compId: 'dead'|'inverted'}
 *  blacklist  – Set/array of blacklisted component ids
 *  pending    – {compId: ticksLeft} (phase-3 slow blinds)
 *  onToggle   – click handler → sandbox mode; omit for read-only replay
 *  power/budget – optional energy meter (lab4/lab5)
 */
export default function LabView({
  lab, state, sun, lux, faults = {}, blacklist = [], pending = {},
  onToggle, power = null, budget = null, compact = false,
}) {
  const zones = lab.zones;
  const luxByZone = lux || lab.compute(state, sun, faults);
  const bl = new Set(blacklist);
  const sRank = sunRank(sun);

  return (
    <div className="labview" style={{ '--nz': zones.length }}>
      <div className="skyrow">
        <span className="sunicon">{sRank === 0 ? <MoonIcon /> : <SunIcon />}</span>
        <span className="sunval">Sun {Math.round(sun)} lux</span>
        <span className="sunmeta">rank {sRank} · pinned for the episode · blinds harvest {sRank === 0 ? 'nothing at night' : 'daylight'}</span>
        {power != null && (
          <span className="sunmeta" style={{ marginLeft: 'auto', fontWeight: 600, color: budget != null && power > budget ? 'var(--critical)' : 'var(--good-text)' }}>
            power {power}{budget != null ? ` / budget ${budget}` : ''}
          </span>
        )}
      </div>

      <div className="zones">
        {zones.map((z) => {
          const lv = Math.round(luxByZone[z]);
          const rank = rankOf(lv);
          const target = lab.targets[z];
          const at = rank === target;
          return (
            <div key={z} className={`zone ${at ? 'at' : 'off'}`}>
              <div className="zhead">
                <span className="zname">Zone {z.slice(1)}</span>
                <span className={`chip ${at ? 'ok' : 'warn'}`}>{at ? 'at target' : `target ${RANK_NAMES[target]}`}</span>
              </div>
              <div className="lux">{lv}<small>lux · rank {rank} ({RANK_NAMES[rank]})</small></div>
              <div className="rankmeter" title={`rank ${rank} of 3 — target ${target}`}>
                {[0, 1, 2, 3].map((r) => (
                  <span key={r} className={`seg ${r <= rank ? 'on' : ''} ${r <= rank && at ? 'hit' : ''}`} />
                ))}
              </div>
              {!compact && (
                <div className="acts">
                  {lab.actuators.filter((a) => a.zone === z).map((a) => (
                    <ActRow key={a.id} act={a} on={!!state[a.id]}
                      fault={faults[a.id]} blacklisted={bl.has(a.id)}
                      pendingTicks={pending[a.id] || 0}
                      onToggle={onToggle} disabled={bl.has(a.id)} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!compact && lab.actuators.some((a) => a.zone === 'shared') && (
        <div className="sharedrow">
          <span className="sunmeta" style={{ fontWeight: 600 }}>shared</span>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {lab.actuators.filter((a) => a.zone === 'shared').map((a) => (
              <ActRow key={a.id} act={a} on={!!state[a.id]}
                fault={faults[a.id]} blacklisted={bl.has(a.id)}
                pendingTicks={pending[a.id] || 0}
                onToggle={onToggle} disabled={bl.has(a.id)} />
            ))}
          </div>
        </div>
      )}

      {!compact && lab.crossNote && <div className="crossnote">⇄ {lab.crossNote}</div>}
    </div>
  );
}
