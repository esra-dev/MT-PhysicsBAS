import React from 'react';
import { WEAKNESS_DEFS } from '../lib/weakness.js';

export default function WeaknessPanel({ classification, histogram }) {
  const fired = new Set(classification.tags || []);
  return (
    <div className="weakness-panel">
      <div className="panel-title">
        <span className="dot dot-red" /> Weakness Detector
      </div>
      <div className="weakness-grid">
        {WEAKNESS_DEFS.map((w) => {
          const on = fired.has(w.tag);
          const count = histogram?.[w.id] || 0;
          return (
            <div key={w.id} className={`w-card ${on ? 'w-on' : ''}`}>
              <div className="w-head">
                <span className="w-id">{w.id}</span>
                <span className="w-count" title="firings across whole trace">{count}×</span>
              </div>
              <div className="w-title">{w.title}</div>
              <div className="w-short">{w.short}</div>
              {on && <div className="w-flag">FIRED THIS STEP</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
