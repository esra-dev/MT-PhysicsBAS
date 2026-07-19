// Deterministic re-implementation of every lab's simulator physics
// (source of truth: simulator/simulator_flow_lab*.json, documented in
// docs/LAB_REFERENCE.md). All labs share: ambient 25 lux, rank bounds
// [50, 100, 300], sunshine pinned per episode from {0, 100, 400, 900}.

export const LIGHT_BOUNDS = [50, 100, 300];
export const SUN_LEVELS = [0, 100, 400, 900];
export const RANK_NAMES = ['dark', 'dim', 'medium', 'bright'];

export function rankOf(lux) {
  if (lux >= LIGHT_BOUNDS[2]) return 3;
  if (lux >= LIGHT_BOUNDS[1]) return 2;
  if (lux >= LIGHT_BOUNDS[0]) return 1;
  return 0;
}

export function sunRank(sunLux) {
  if (sunLux >= 600) return 3;
  if (sunLux >= 200) return 2;
  if (sunLux >= 50) return 1;
  return 0;
}

// contribution of one actuator, honouring an injected fault
function contrib(on, value, fault) {
  if (!on) return 0;
  if (fault === 'dead') return 0;
  if (fault === 'inverted') return -value;
  return value;
}

// Each lab definition:
//  zones      – zone ids
//  targets    – target rank per zone
//  actuators  – [{id, kind: lamp|blind|spot|plug, zone|shared, label, note}]
//  compute(state, sun, faults) -> {Z1: lux, Z2: lux}
//  power(state) -> steady-state power units (only labs that track energy)
export const LABS = {
  lab1: {
    id: 'lab1', phase: 1, port: 1892, states: 8,
    name: 'lab1 · Trivial',
    tagline: '1 zone, 1 lamp — the smallest acceleration test',
    zones: ['Z1'], targets: { Z1: 3 },
    actuators: [
      { id: 'Z1Light', kind: 'lamp', zone: 'Z1', label: 'Ceiling lamp', mech: 'Causes +400' },
    ],
    formula: 'Z1 = 25 + 0.10·Sun + (Z1Light ? 400)',
    kg: 'Z1Light Causes Z1Level — “switch the lamp on”. Sun is a pure distractor (≤ 90 lux).',
    compute(s, sun, f = {}) {
      return { Z1: 25 + 0.10 * sun + contrib(s.Z1Light, 400, f.Z1Light) };
    },
  },

  lab2: {
    id: 'lab2', phase: 1, port: 1893, states: 1024,
    name: 'lab2 · Intermediate',
    tagline: '2 independent zones, lamp + daylight-harvesting blind',
    zones: ['Z1', 'Z2'], targets: { Z1: 3, Z2: 3 },
    actuators: [
      { id: 'Z1Light', kind: 'lamp', zone: 'Z1', label: 'Lamp', mech: 'Causes +400' },
      { id: 'Z1Blinds', kind: 'blind', zone: 'Z1', label: 'Blind', mech: 'Mediates 0.50·Sun' },
      { id: 'Z2Light', kind: 'lamp', zone: 'Z2', label: 'Lamp', mech: 'Causes +400' },
      { id: 'Z2Blinds', kind: 'blind', zone: 'Z2', label: 'Blind', mech: 'Mediates 0.50·Sun' },
    ],
    formula: 'Zn = 25 + (ZnLight ? 400) + (ZnBlinds ? 0.50·Sun)',
    kg: 'Lamps Cause light unconditionally; blinds Mediate sunshine — light only when the sun is up. The blind is the free, sun-conditioned optimum at sun 900.',
    compute(s, sun, f = {}) {
      return {
        Z1: 25 + contrib(s.Z1Light, 400, f.Z1Light) + contrib(s.Z1Blinds, 0.5 * sun, f.Z1Blinds),
        Z2: 25 + contrib(s.Z2Light, 400, f.Z2Light) + contrib(s.Z2Blinds, 0.5 * sun, f.Z2Blinds),
      };
    },
  },

  lab3: {
    id: 'lab3', phase: 1, port: 1894, states: 2048,
    name: 'lab3 · Complex',
    tagline: 'cross-zone light spill + a shared spotlight trap',
    zones: ['Z1', 'Z2'], targets: { Z1: 3, Z2: 3 },
    actuators: [
      // current intermediate spill physics (retuned 2026-07-08): lamp +100, blind 0.30·Sun
      { id: 'Z1Light', kind: 'lamp', zone: 'Z1', label: 'Lamp', mech: 'Causes +400 (+100 spill)' },
      { id: 'Z1Blinds', kind: 'blind', zone: 'Z1', label: 'Blind', mech: '0.50·Sun (0.30 spill)' },
      { id: 'Z2Light', kind: 'lamp', zone: 'Z2', label: 'Lamp', mech: 'Causes +400 (+100 spill)' },
      { id: 'Z2Blinds', kind: 'blind', zone: 'Z2', label: 'Blind', mech: '0.50·Sun (0.30 spill)' },
      { id: 'Spotlight', kind: 'spot', zone: 'shared', label: 'Spotlight', mech: '+150 to BOTH zones' },
    ],
    crossNote: 'Each lamp leaks +100 lux and each blind 0.30·Sun into the other zone (current physics, retuned 2026-07-08 — rank-moving but never enough for bright on its own).',
    formula: 'Z1 = 25 + (Z1Light?400) + (Z2Light?100) + (Z1Blinds?0.50·Sun) + (Z2Blinds?0.30·Sun) + (Spot?150)',
    kg: 'The spotlight (+150) can never reach bright (≥300) on its own — the KG-primed agent learns to avoid the tempting-but-useless shared actuator.',
    traceNote: 'Replay traces below were recorded 2026-06-10 under the original spill physics (+50 lux / 0.25·Sun, retuned 2026-07-08 to +100 / 0.30) and the pre-inversion action registry — illustrative only, not the confirmatory data.',
    compute(s, sun, f = {}) {
      const z1 = 25 + contrib(s.Z1Light, 400, f.Z1Light) + contrib(s.Z2Light, 100, f.Z2Light)
        + contrib(s.Z1Blinds, 0.5 * sun, f.Z1Blinds) + contrib(s.Z2Blinds, 0.3 * sun, f.Z2Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      const z2 = 25 + contrib(s.Z2Light, 400, f.Z2Light) + contrib(s.Z1Light, 100, f.Z1Light)
        + contrib(s.Z2Blinds, 0.5 * sun, f.Z2Blinds) + contrib(s.Z1Blinds, 0.3 * sun, f.Z1Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      return { Z1: z1, Z2: z2 };
    },
  },

  lab4: {
    id: 'lab4', phase: 4, port: 1897, states: 4096,
    name: 'lab4 · Smart-plug',
    tagline: 'hidden AND-gate: the Z1 lamp only works if its plug is on',
    zones: ['Z1', 'Z2'], targets: { Z1: 3, Z2: 3 },
    actuators: [
      { id: 'PlugZ1', kind: 'plug', zone: 'Z1', label: 'Smart plug', mech: 'powerGates Z1 lamp' },
      { id: 'Z1Light', kind: 'lamp', zone: 'Z1', label: 'Lamp (gated)', mech: '+400 iff plug ON' },
      { id: 'Z1Blinds', kind: 'blind', zone: 'Z1', label: 'Blind', mech: '0.50·Sun (0.40 spill)' },
      { id: 'Z2Light', kind: 'lamp', zone: 'Z2', label: 'Lamp (direct)', mech: '+400 (+150 spill)' },
      { id: 'Z2Blinds', kind: 'blind', zone: 'Z2', label: 'Blind', mech: '0.50·Sun (0.40 spill)' },
      { id: 'Spotlight', kind: 'spot', zone: 'shared', label: 'Spotlight', mech: '+150 to BOTH zones' },
    ],
    crossNote: 'Richer coupling than lab3: lamp spill +150, blind spill 0.40·Sun.',
    formula: 'z1lamp = Z1Light AND PlugZ1 · Z1 = 25 + (z1lamp?400) + (Z2Light?150) + (Z1Blinds?0.50·Sun) + (Z2Blinds?0.40·Sun) + (Spot?150)',
    kg: 'The KG holds ws:powerGates — “PlugZ1 power-gates the Z1 lamp”. The primed agent enables the plug first; a tabula-rasa agent toggles a dead lamp.',
    compute(s, sun, f = {}) {
      const lampOn = s.Z1Light && s.PlugZ1;
      const z1 = 25 + contrib(lampOn, 400, f.Z1Light) + contrib(s.Z2Light, 150, f.Z2Light)
        + contrib(s.Z1Blinds, 0.5 * sun, f.Z1Blinds) + contrib(s.Z2Blinds, 0.4 * sun, f.Z2Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      const z2 = 25 + contrib(s.Z2Light, 400, f.Z2Light) + contrib(lampOn, 150, f.Z1Light)
        + contrib(s.Z2Blinds, 0.5 * sun, f.Z2Blinds) + contrib(s.Z1Blinds, 0.4 * sun, f.Z1Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      return { Z1: z1, Z2: z2 };
    },
    power(s) {
      return ((s.Z1Light && s.PlugZ1) ? 1 : 0) + (s.Z2Light ? 1 : 0) + (s.Spotlight ? 2 : 0);
    },
  },

  lab5: {
    id: 'lab5', phase: 4, port: 1898, states: 8192,
    name: 'lab5 · Energy',
    tagline: 'two identical-looking lamps per zone — one costs 4× more',
    zones: ['Z1', 'Z2'], targets: { Z1: 3, Z2: 3 },
    energyBudget: 2,
    actuators: [
      { id: 'Z1Eff', kind: 'lamp', zone: 'Z1', label: 'Efficient lamp', mech: '+400 · cost 1' },
      { id: 'Z1Ineff', kind: 'lampBad', zone: 'Z1', label: 'Inefficient lamp', mech: '+400 · cost 4' },
      { id: 'Z1Blinds', kind: 'blind', zone: 'Z1', label: 'Blind', mech: '0.50·Sun · cost 0' },
      { id: 'Z2Eff', kind: 'lamp', zone: 'Z2', label: 'Efficient lamp', mech: '+400 · cost 1' },
      { id: 'Z2Ineff', kind: 'lampBad', zone: 'Z2', label: 'Inefficient lamp', mech: '+400 · cost 4' },
      { id: 'Z2Blinds', kind: 'blind', zone: 'Z2', label: 'Blind', mech: '0.50·Sun · cost 0' },
      { id: 'Spotlight', kind: 'spot', zone: 'shared', label: 'Spotlight', mech: '+150 both · cost 2' },
    ],
    crossNote: 'anyLamp = Eff OR Ineff adds +400 once (both on = pure waste); lamp spill +150, blind spill 0.40·Sun.',
    formula: 'Z1 = 25 + (z1anyLamp?400) + (z2anyLamp?150) + (Z1Blinds?0.50·Sun) + (Z2Blinds?0.40·Sun) + (Spot?150) · power = Eff·1 + Ineff·4 + Spot·2',
    kg: 'Optically the two lamps are identical — the 1-vs-4 energy cost exists ONLY in the KG (ws:energyCost), and energy is NOT in the reward. Only the KG-primed agent can prefer the cheap lamp.',
    compute(s, sun, f = {}) {
      const a1 = s.Z1Eff || s.Z1Ineff;
      const a2 = s.Z2Eff || s.Z2Ineff;
      const z1 = 25 + (a1 ? 400 : 0) + (a2 ? 150 : 0)
        + contrib(s.Z1Blinds, 0.5 * sun, f.Z1Blinds) + contrib(s.Z2Blinds, 0.4 * sun, f.Z2Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      const z2 = 25 + (a2 ? 400 : 0) + (a1 ? 150 : 0)
        + contrib(s.Z2Blinds, 0.5 * sun, f.Z2Blinds) + contrib(s.Z1Blinds, 0.4 * sun, f.Z1Blinds)
        + contrib(s.Spotlight, 150, f.Spotlight);
      return { Z1: z1, Z2: z2 };
    },
    power(s) {
      return (s.Z1Eff ? 1 : 0) + (s.Z1Ineff ? 4 : 0) + (s.Z2Eff ? 1 : 0)
        + (s.Z2Ineff ? 4 : 0) + (s.Spotlight ? 2 : 0);
    },
  },
};

// initial all-off actuator state for a lab
export function offState(lab) {
  const s = {};
  for (const a of lab.actuators) s[a.id] = false;
  return s;
}

// Phase-2 fault catalogue (simulator-side; the KG keeps believing nominal physics)
export const FAULTS = {
  lab1_f1dead: { base: 'lab1', label: 'lab1_f1dead — the only lamp dies', faults: { Z1Light: 'dead' }, note: 'Degenerate case: after blacklisting, no lever survives. The agent detects + alerts but cannot recover.' },
  lab2_f1dead: { base: 'lab2', label: 'lab2_f1dead — Z1 lamp dead', faults: { Z1Light: 'dead' }, note: 'The Z1 blind and all of Z2 survive — rank 3 in Z1 stays reachable on sunny episodes.' },
  lab2_f1inv: { base: 'lab2', label: 'lab2_f1inv — Z1 lamp inverted', faults: { Z1Light: 'inverted' }, note: 'Mis-wired lamp: subtracts light when the zone is lit — opposite-sign evidence.' },
  lab3_f1dead: { base: 'lab3', label: 'lab3_f1dead — Z1 lamp dead', faults: { Z1Light: 'dead' }, note: 'Richest survivors: spotlight + cross-zone spill + blinds keep recovery possible.' },
  lab3_f1bdead: { base: 'lab3', label: 'lab3_f1bdead — Z1 blind dead', faults: { Z1Blinds: 'dead' }, note: 'A dead blind: both arms stay goal-reaching via the lamp — the cleanest recovery-speed comparison.' },
  lab3_f2dead: { base: 'lab3', label: 'lab3_f2dead — BOTH lamps dead', faults: { Z1Light: 'dead', Z2Light: 'dead' }, note: 'Multi-fault: only spotlight + blinds survive. Full recovery only on sunny episodes (best-effort otherwise).' },
};

// Phase-3 slow-lab config (physics identical to parent; blinds get a delay)
export const SLOW = {
  lab2_slow: { base: 'lab2', delayTicks: 12, secondsPerTick: 5, delayed: ['Z1Blinds', 'Z2Blinds'] },
  lab3_slow: { base: 'lab3', delayTicks: 12, secondsPerTick: 5, delayed: ['Z1Blinds', 'Z2Blinds'] },
};

export const SUN_RANK_TO_LUX = { 0: 0, 1: 100, 2: 400, 3: 900 };
