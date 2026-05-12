// Weakness detector: combines the `weaknessFired` tags emitted by
// BenchmarkLogger with client-side computed evidence so we can render
// presentation-ready explanation text per step.
//
// W1 unmodelled cross-zone effect : observed Δ on a slot the ontology said 0
// W2 condition inversion          : predicted +k, observed −k (or vice-versa)
// W3 delayed effect               : action dispatched, no observed Δ this step
// W4 silently dropped action      : prediction said Δ≠0 everywhere, observed Δ=0
// W5 topology mismatch            : feeds-arc disagreement vs ontology (tag only)
// W6 thermal comfort / heat       : Temp/Radiator slot moved unexpectedly

import { slotIndex } from './parseTrace.js';

export const WEAKNESS_DEFS = [
  { id: 'W1', tag: 'w1_unmodelled_cross_zone',
    title: 'Unmodelled cross-zone effect',
    short: 'Reality changed a zone the ontology said it would not touch.' },
  { id: 'W2', tag: 'w2_condition_inversion',
    title: 'Condition inversion',
    short: 'Observed change has the opposite sign of the ontology prediction.' },
  { id: 'W3', tag: 'w3_delayed',
    title: 'Delayed effect',
    short: 'Action took no immediate effect; reality lags the model.' },
  { id: 'W4', tag: 'w4_silently_dropped',
    title: 'Silently dropped action',
    short: 'Action was budget-/safety-dropped — predicted Δ never landed.' },
  { id: 'W5', tag: 'w5_topology_mismatch',
    title: 'Topology mismatch',
    short: 'Feeds-arc disagreement between ontology and simulator.' },
  { id: 'W6', tag: 'w6_thermal',
    title: 'Thermal / comfort effect',
    short: 'Heat/temperature moved unexpectedly relative to comfort target.' },
];

export function diff(a, b) {
  const n = Math.max((a || []).length, (b || []).length);
  const out = new Array(n);
  for (let i = 0; i < n; i++) out[i] = (b?.[i] ?? 0) - (a?.[i] ?? 0);
  return out;
}

// Produce per-step evidence + classification.
export function classifyStep(step, schema) {
  const observed = diff(step.stateBefore, step.stateAfter);
  const predicted = step.predictedDelta || new Array(observed.length).fill(0);
  const tags = new Set(step.weaknessFired || []);
  const reasons = [];

  // Slot-by-slot analysis
  const mismatches = [];
  for (let i = 0; i < observed.length; i++) {
    const o = observed[i] || 0;
    const p = predicted[i] || 0;
    if (o !== p) {
      mismatches.push({ slot: schema.slots[i] || `s${i}`, predicted: p, observed: o });
    }
  }

  // Auto-fire (without overriding logger tags) for the demo / when tags absent
  for (const m of mismatches) {
    if (m.predicted === 0 && m.observed !== 0) tags.add('w1_unmodelled_cross_zone');
    if (m.predicted !== 0 && m.observed !== 0 && Math.sign(m.predicted) !== Math.sign(m.observed)) tags.add('w2_condition_inversion');
    if (/Temp|Radiator/.test(m.slot)) tags.add('w6_thermal');
  }
  const hasAction = (step.actionIdx ?? -1) >= 0 &&
    !((schema.actions && /DO_NOTHING/i.test(schema.actions[String(step.actionIdx)] || '')));
  const anyObserved = observed.some((v) => v !== 0);
  const anyPredicted = predicted.some((v) => v !== 0);
  if (hasAction && !anyObserved && anyPredicted) tags.add('w4_silently_dropped');
  if (hasAction && !anyObserved && !anyPredicted) tags.add('w3_delayed');

  // Build human-readable reasons
  if (tags.has('w1_unmodelled_cross_zone')) {
    const offenders = mismatches.filter((m) => m.predicted === 0 && m.observed !== 0);
    if (offenders.length) {
      reasons.push(
        `Observed ${offenders.map((o) => `${o.slot} (${o.observed > 0 ? '+' : ''}${o.observed})`).join(', ')} changed, but the ontology prediction did not include ${offenders.map((o) => o.slot).join(', ')}. This is classified as an unmodelled cross-zone effect (W1).`
      );
    }
  }
  if (tags.has('w2_condition_inversion')) {
    const inv = mismatches.filter((m) => m.predicted * m.observed < 0);
    if (inv.length) {
      reasons.push(
        `Ontology predicted ${inv.map((o) => `${o.slot} ${o.predicted > 0 ? '+' : ''}${o.predicted}`).join(', ')} but the simulator showed ${inv.map((o) => `${o.slot} ${o.observed > 0 ? '+' : ''}${o.observed}`).join(', ')} — opposite sign (W2).`
      );
    }
  }
  if (tags.has('w3_delayed')) {
    reasons.push('Action dispatched but no slot changed this step. Effect may surface in a later step (W3).');
  }
  if (tags.has('w4_silently_dropped')) {
    reasons.push('Ontology predicted a Δ but nothing changed — likely a budget- or safety-drop in the simulator (W4).');
  }
  if (tags.has('w5_topology_mismatch')) {
    reasons.push('Feeds-arc / topology disagreement between ontology and simulator (W5).');
  }
  if (tags.has('w6_thermal')) {
    const t = mismatches.filter((m) => /Temp|Radiator/.test(m.slot));
    if (t.length) reasons.push(`Thermal/comfort slot(s) ${t.map((x) => x.slot).join(', ')} moved unexpectedly (W6).`);
  }

  return { observed, predicted, mismatches, tags: Array.from(tags), reasons };
}

// Aggregate which weaknesses ever fire across the whole trace.
export function weaknessHistogram(steps, schema) {
  const counts = Object.fromEntries(WEAKNESS_DEFS.map((w) => [w.id, 0]));
  for (const s of steps) {
    const { tags } = classifyStep(s, schema);
    for (const t of tags) {
      const def = WEAKNESS_DEFS.find((w) => w.tag === t);
      if (def) counts[def.id]++;
    }
  }
  return counts;
}
