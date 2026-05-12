// Trace parsing and schema resolution.
//
// MT-Esra benchmark traces are JSONL with one record per step. The dashboard
// also accepts an optional first-line metadata header containing a `$schema`
// field — when present, it describes slot names, level domain, action labels,
// targets and provenance ("isDemo": true) so the UI can stay generic.

export const DEFAULT_SCHEMA_8 = {
  slots: ['Z1Level', 'Z2Level', 'Z1Light', 'Z2Light', 'Z1Blinds', 'Z2Blinds', 'Spotlight', 'Sunshine'],
  levelDomain: 4,
  targets: { Z1: 2, Z2: 2 },
  actions: {},
  isDemo: false,
  label: 'Real benchmark trace (default 8-slot Q-learner schema)',
};

export const DEFAULT_SCHEMA_GENERIC = (n) => ({
  slots: Array.from({ length: n }, (_, i) => `s${i}`),
  levelDomain: 4,
  targets: {},
  actions: {},
  isDemo: false,
  label: `Generic ${n}-slot trace`,
});

export function parseTrace(text) {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  let schema = null;
  const steps = [];
  for (const line of lines) {
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      continue;
    }
    if (obj.$schema) {
      schema = obj;
      continue;
    }
    steps.push(obj);
  }
  if (!schema && steps.length > 0) {
    const len = (steps[0].stateBefore || []).length;
    schema = len === 8 ? DEFAULT_SCHEMA_8 : DEFAULT_SCHEMA_GENERIC(len);
  }
  if (!schema) schema = DEFAULT_SCHEMA_8;
  return { schema, steps };
}

export function slotIndex(schema, name) {
  return schema.slots ? schema.slots.indexOf(name) : -1;
}

// Group slots into a per-zone view: { Z1: {Level, Light, Blinds, Temp?}, ... }
// plus a `shared` map for everything else.
export function viewState(schema, vec) {
  const zones = {};
  const shared = {};
  if (!Array.isArray(vec)) return { zones, shared };
  schema.slots.forEach((name, idx) => {
    const m = name.match(/^Z(\d)(Level|Light|Blinds|Temp|Radiator|Window)$/);
    const v = vec[idx];
    if (m) {
      const z = `Z${m[1]}`;
      zones[z] = zones[z] || {};
      zones[z][m[2]] = v;
    } else {
      shared[name] = v;
    }
  });
  return { zones, shared };
}

export function actionLabel(schema, idx) {
  if (idx == null || idx < 0) return 'none';
  const lbl = schema.actions && schema.actions[String(idx)];
  return lbl ? lbl : `action #${idx}`;
}
