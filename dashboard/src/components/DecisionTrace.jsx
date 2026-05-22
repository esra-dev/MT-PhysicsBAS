import React from 'react';
import { actionLabel } from '../lib/parseTrace.js';

function VecRow({ label, vec, slots, highlight }) {
  return (
    <div className="vec-row">
      <div className="vec-label">{label}</div>
      <div className="vec-cells">
        {(vec || []).map((v, i) => {
          const isHi = highlight && highlight.has(slots[i]);
          return (
            <span key={i} className={`vec-cell ${isHi ? 'hi' : ''} ${v < 0 ? 'neg' : v > 0 ? 'pos' : ''}`} title={slots[i] || `s${i}`}>
              <span className="vec-name">{(slots[i] || `s${i}`).replace(/^Z(\d)/, 'Z$1·')}</span>
              <span className="vec-val">{v}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default function DecisionTrace({ schema, step, classification, totalSteps, index }) {
  if (!step) return null;
  const slots = schema.slots || [];
  const hi = new Set((classification.mismatches || []).map((m) => m.slot));

  return (
    <div className="trace-panel">
      <div className="panel-title">
        <span className="dot dot-purple" /> Agent Decision · step {index + 1}/{totalSteps}
      </div>

      <div className="trace-headline">
        <div className="action-pill">
          <span className="action-pre">action</span>
          <span className="action-name">{actionLabel(schema, step.actionIdx)}</span>
          <span className="action-idx">#{step.actionIdx}</span>
        </div>
        <div className="meta-row">
          <span className="kv"><b>scenario</b>{step.scenarioId}</span>
          <span className="kv"><b>run</b>{step.runId}</span>
          <span className="kv"><b>step</b>{step.step}</span>
          {step.qDelta != null && <span className="kv"><b>|Δq|</b>{Number(step.qDelta).toFixed(3)}</span>}
        </div>
      </div>

      <VecRow label="state before" vec={step.stateBefore} slots={slots} highlight={hi} />
      <VecRow label="state after"  vec={step.stateAfter}  slots={slots} highlight={hi} />
      <VecRow label="ontology Δ"   vec={step.predictedDelta} slots={slots} highlight={hi} />
      <VecRow label="observed Δ"   vec={classification.observed} slots={slots} highlight={hi} />

      {classification.reasons.length > 0 && (
        <div className="explain">
          <div className="explain-title">Explanation</div>
          {classification.reasons.map((r, i) => (
            <div key={i} className="explain-line">{r}</div>
          ))}
        </div>
      )}

      {step.applicableActions && (
        <div className="applicable">
          <span className="muted">applicable: </span>
          {step.applicableActions.map((a) => (
            <span key={a} className={`mini ${a === step.actionIdx ? 'mini-sel' : ''}`} title={actionLabel(schema, a)}>
              {a}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
