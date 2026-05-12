import React from 'react';

const RANK_COLORS = ['#1c2230', '#3a3a52', '#bda13a', '#f6c453']; // dark / dim / medium / bright
const RANK_NAMES = ['dark', 'dim', 'medium', 'bright'];

function lampIcon(on, kind = 'light') {
  if (kind === 'blind') return on ? '▲' : '▼';
  return on ? '●' : '○';
}

function ZoneCard({ z, data, target, levelDomain, observedDelta, mismatched }) {
  const lvl = data?.Level ?? 0;
  const cls = ['zone-card'];
  if (target != null) {
    if (lvl === target) cls.push('zone-ok');
    else if (Math.abs(lvl - target) === 1) cls.push('zone-warn');
    else cls.push('zone-miss');
  }
  if (mismatched) cls.push('zone-firing');
  const color = RANK_COLORS[Math.min(lvl, RANK_COLORS.length - 1)];

  return (
    <div className={cls.join(' ')}>
      <div className="zone-head">
        <span className="zone-name">{z}</span>
        {target != null && <span className="zone-target">target {RANK_NAMES[target]}</span>}
      </div>
      <div className="zone-lux" style={{ background: color }}>
        <div className="zone-lux-rank">{RANK_NAMES[Math.min(lvl, RANK_NAMES.length - 1)]}</div>
        <div className="zone-lux-num">rank {lvl}/{(levelDomain || 4) - 1}</div>
        {observedDelta != null && observedDelta !== 0 && (
          <div className={`zone-delta ${observedDelta > 0 ? 'up' : 'down'}`}>
            {observedDelta > 0 ? '▲' : '▼'} {Math.abs(observedDelta)}
          </div>
        )}
      </div>
      <div className="zone-actuators">
        {data?.Light != null && (
          <span className={`act ${data.Light ? 'on' : 'off'}`} title="Task light">
            {lampIcon(data.Light)} light
          </span>
        )}
        {data?.Blinds != null && (
          <span className={`act ${data.Blinds ? 'on' : 'off'}`} title="Blinds">
            {lampIcon(data.Blinds, 'blind')} blinds
          </span>
        )}
        {data?.Temp != null && (
          <span className="act temp" title="Temperature">🌡 {data.Temp}</span>
        )}
        {data?.Radiator != null && (
          <span className={`act ${data.Radiator ? 'on' : 'off'}`} title="Radiator">
            {data.Radiator ? '🔥' : '·'} rad
          </span>
        )}
      </div>
    </div>
  );
}

export default function ZoneGrid({ schema, view, observed, mismatchSlots }) {
  const zones = ['Z1', 'Z2', 'Z3', 'Z4'];
  const slotIdx = (name) => (schema.slots || []).indexOf(name);
  const mismSet = new Set(mismatchSlots || []);

  return (
    <div className="zone-panel">
      <div className="panel-title">
        <span className="dot dot-blue" /> 4-Zone Lab View
      </div>
      <div className="zone-grid">
        {zones.map((z) => {
          const data = view.zones[z];
          if (!data) return <div key={z} className="zone-card zone-empty">{z}<div className="muted">not in trace</div></div>;
          const target = schema.targets ? schema.targets[z] : null;
          const lvlSlot = `${z}Level`;
          const od = observed?.[slotIdx(lvlSlot)] ?? 0;
          const mismatched = ['Level', 'Light', 'Blinds', 'Temp', 'Radiator']
            .some((k) => mismSet.has(`${z}${k}`));
          return (
            <ZoneCard
              key={z}
              z={z}
              data={data}
              target={target}
              levelDomain={schema.levelDomain}
              observedDelta={od}
              mismatched={mismatched}
            />
          );
        })}
      </div>
      {Object.keys(view.shared).length > 0 && (
        <div className="shared">
          <div className="shared-title">Shared / environment</div>
          <div className="shared-row">
            {Object.entries(view.shared).map(([k, v]) => (
              <span key={k} className={`chip ${v ? 'chip-on' : 'chip-off'} ${mismSet.has(k) ? 'chip-fire' : ''}`}>
                <strong>{k}</strong> <span>{String(v)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
