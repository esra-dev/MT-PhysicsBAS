# =============================================================================
#  generate_flows.ps1
#  ----------------------------------------------------------------------------
#  Emits six Node-Red flow JSON files (one per weakness lab):
#     simulator_flow_custom2.json â€¦ simulator_flow_custom7.json
#
#  All six share the SAME 4-zone physics base (matching the agent-side TD
#  shape declared in src/resources/interactions-lab-custom2.ttl).  Each flow
#  injects exactly ONE weakness into the per-tick "Update environment"
#  function so that the agent's nominal ontology (which is identical across
#  all six labs) systematically MIS-PREDICTS the observed Î” for that one
#  failure mode.
#
#  Re-run after editing this file:
#     powershell -ExecutionPolicy Bypass -File simulator/generate_flows.ps1
#
#  Each flow is launched on its dedicated port:
#     custom2  W1  port 1882    custom5  W4  port 1885
#     custom3  W2  port 1883    custom6  W5  port 1886
#     custom4  W3  port 1884    custom7  W6  port 1887
#  e.g. node-red --userDir .node-red-1882 --port 1882 simulator/simulator_flow_custom2.json
# =============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

# ---------------------------------------------------------------------------
# Per-weakness "patch" scripts â€” each is the JS body INSERTED at the marker
# `// __WEAKNESS_PATCH__` inside the canonical environment function.
# By convention these patches MAY:
#   â€¢ read & override locals z1level..z4level (illuminance contributions)
#   â€¢ read & override locals energy, z*temp (side-effect channels)
#   â€¢ use flow.get/set for additional persistent state
#   â€¢ flag `weaknessFired = true` when the weakness perturbed this tick
# ---------------------------------------------------------------------------
$weaknessPatches = @{
  "custom2" = @"
// â”€â”€ W1 missing-stereotype: Hidden CorridorLight bleed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// CorridorLight in this lab leaks +30 lux to ALL zones whenever the hour
// is in the diurnal "occupied" window 8..18 â€” but the TD/ontology declare
// only its nominal +150 lux contribution.  Agents must learn the bleed.
var hour = flow.get('Hour');
if (flow.get('CorridorLight') && hour >= 8 && hour < 18) {
    z1level += 30; z2level += 30; z3level += 30; z4level += 30;
    weaknessFired = true;
}
"@
  "custom3" = @"
// â”€â”€ W2 context-dependent inversion: Blind_Z2 sun-flip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// At Sunshine rank â‰¥3 (>500 lux), Blind_Z2's bleed contribution to Z1
// INVERTS sign (it shades neighbouring zones at high glare).  The
// ontology models a single positive coefficient â€” agents must learn the
// regime-switch.
if (flow.get('Z2Blinds') && sun >= 500) {
    z1level -= 2 * (sun * 0.25);   // undo positive contrib + go negative
    weaknessFired = true;
}
"@
  "custom4" = @"
// â”€â”€ W3 dynamics: per-lamp ramp(3) + residual(2) + hysteresis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Each task light needs 3 ticks to reach full brightness after a Fâ†’T
// edge, and continues to emit for 2 ticks after a Tâ†’F edge.  Tracked in
// flow context via objects keyed by lamp name.
var dyn = flow.get('dynamics_state') || {};
['Z1Light','Z2Light','Z3Light','Z4Light'].forEach(function(lamp) {
    var raw = flow.get(lamp);                  // commanded state
    var st  = dyn[lamp] || { ramp: 0, residual: 0, last: false };
    if (raw && !st.last)            st.ramp     = 3;       // Fâ†’T edge
    if (!raw && st.last)            st.residual = 2;       // Tâ†’F edge
    st.last = raw;
    var emitting = raw || st.residual > 0;
    var brightness = emitting ? Math.max(0.1, 1 - st.ramp / 3.0) : 0;
    if (st.ramp     > 0) st.ramp--;
    if (st.residual > 0) st.residual--;
    dyn[lamp] = st;
    if (raw && brightness < 1)        weaknessFired = true;  // ramping
    if (!raw && st.residual > 0)      weaknessFired = true;  // residual
    // adjust contribution: difference between effective and full brightness
    var z = parseInt(lamp.charAt(1), 10);
    var primary = 400, bleed = 50;
    var full = primary;
    var actual = brightness * primary;
    if (z===1)      { z1level += (actual - (raw ? full : 0)); }
    else if (z===2) { z2level += (actual - (raw ? full : 0)); }
    else if (z===3) { z3level += (actual - (raw ? full : 0)); }
    else            { z4level += (actual - (raw ? full : 0)); }
});
flow.set('dynamics_state', dyn);
"@
  "custom5" = @"
// â”€â”€ W4 shared resource: 7-unit power cap with priority dropout â”€â”€â”€â”€â”€â”€â”€â”€
// Total instantaneous power demand across all ON lamps must fit a 7-unit
// budget.  When exceeded, lamps are dropped in priority order
// (corridor â†’ spotlights â†’ task lights of highest-numbered zones).
// Dropped lamps contribute nothing this tick (but keep their commanded
// flow state so user-visible status is consistent).
var demand = [];
if (flow.get('CorridorLight')) demand.push({ p: 1, name: 'CorridorLight', cost: 2 });
if (flow.get('Spotlight'))     demand.push({ p: 2, name: 'Spotlight',    cost: 3 });
if (flow.get('SpotlightCD'))   demand.push({ p: 2, name: 'SpotlightCD',  cost: 3 });
['Z4Light','Z3Light','Z2Light','Z1Light'].forEach(function(l, idx){
    if (flow.get(l)) demand.push({ p: 3 + idx, name: l, cost: 1 });
});
demand.sort(function(a, b) { return a.p - b.p; });
var budget = 7, allowed = {};
for (var i = 0; i < demand.length; i++) {
    if (budget - demand[i].cost >= 0) { allowed[demand[i].name] = true; budget -= demand[i].cost; }
    else                              { allowed[demand[i].name] = false; weaknessFired = true; }
}
// undo any contribution from dropped lamps
['Z1Light','Z2Light','Z3Light','Z4Light'].forEach(function(lamp) {
    if (flow.get(lamp) && allowed[lamp] === false) {
        var z = parseInt(lamp.charAt(1), 10);
        if (z===1) { z1level -= 400; }
        else if (z===2) { z2level -= 400; }
        else if (z===3) { z3level -= 400; }
        else { z4level -= 400; }
    }
});
if (flow.get('Spotlight')   && allowed['Spotlight']     === false) { z1level -= 250; z2level -= 250; }
if (flow.get('SpotlightCD') && allowed['SpotlightCD']   === false) { z3level -= 250; z4level -= 250; }
if (flow.get('CorridorLight') && allowed['CorridorLight'] === false) { z1level -= 150; z2level -= 150; z3level -= 150; z4level -= 150; }
"@
  "custom6" = @"
// â”€â”€ W5 dynamic topology: Partition23 toggles every 5 ticks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// When OPEN, four extra cross-zone bleeds activate (Z1â†”Z3, Z2â†”Z4 mid-
// strength).  When CLOSED no extra coupling.  Toggle period = 5 sim ticks
// implemented via a counter in flow context.
var pcnt = flow.get('partition_counter') || 0;
var open = flow.get('partition_open');
if (open === undefined) open = false;
pcnt = (pcnt + 1) % 5;
if (pcnt === 0) { open = !open; flow.set('partition_open', open); }
flow.set('partition_counter', pcnt);
if (open) {
    var bleed = 80;
    if (flow.get('Z1Light')) { z3level += bleed; }
    if (flow.get('Z3Light')) { z1level += bleed; }
    if (flow.get('Z2Light')) { z4level += bleed; }
    if (flow.get('Z4Light')) { z2level += bleed; }
    weaknessFired = true;
}
"@
  "custom7" = @"
// â”€â”€ W6 multi-objective heat: lamps add +0.1 Â°C/tick to zone temp â”€â”€â”€â”€â”€â”€
// Spotlights only +0.05 Â°C (smaller, distributed).  This couples the
// otherwise-independent illuminance and thermal channels â€” the agent's
// ontology says lamps affect ONLY illuminance, so any thermal drift is
// the unmodelled side-effect.
var deltas = [0, 0, 0, 0];
if (flow.get('Z1Light')) deltas[0] += 0.10;
if (flow.get('Z2Light')) deltas[1] += 0.10;
if (flow.get('Z3Light')) deltas[2] += 0.10;
if (flow.get('Z4Light')) deltas[3] += 0.10;
if (flow.get('Spotlight'))   { deltas[0] += 0.05; deltas[1] += 0.05; }
if (flow.get('SpotlightCD')) { deltas[2] += 0.05; deltas[3] += 0.05; }
if (deltas[0] || deltas[1] || deltas[2] || deltas[3]) weaknessFired = true;
z1temp += deltas[0]; z2temp += deltas[1]; z3temp += deltas[2]; z4temp += deltas[3];
"@
}

# ---------------------------------------------------------------------------
# Canonical 4-zone "Update environment" function body.
# The marker `// __WEAKNESS_PATCH__` is replaced per-lab with one of the
# patches above.  Physics constants match interactions-lab-custom2.ttl.
# ---------------------------------------------------------------------------
$envFnBaseTemplate = @"
var z1level = 0, z2level = 0, z3level = 0, z4level = 0;
var energy = flow.get('TotalEnergyCost');
var sun = flow.get('Sunshine');
var hr = flow.get('Hour');
if (hr >= 24) hr = 0;
flow.set('Hour', hr + 0.1);

if (!flow.get('SunshinePinned')) {
    flow.set('Sunshine', 150 + 50 * Math.random());
    sun = flow.get('Sunshine');
}

// â”€â”€ Primary task lights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
z1level += flow.get('Z1Light') ? 400 : 0;
z2level += flow.get('Z2Light') ? 400 : 0;
z3level += flow.get('Z3Light') ? 400 : 0;
z4level += flow.get('Z4Light') ? 400 : 0;

// â”€â”€ Bleed task lights (each light contributes +50 lux to OTHER zones) â”€
var taskOn = [flow.get('Z1Light'), flow.get('Z2Light'), flow.get('Z3Light'), flow.get('Z4Light')];
for (var i = 0; i < 4; i++) {
    for (var j = 0; j < 4; j++) {
        if (i !== j && taskOn[i]) {
            if (j===0) z1level += 50;
            else if (j===1) z2level += 50;
            else if (j===2) z3level += 50;
            else z4level += 50;
        }
    }
}

// â”€â”€ Blinds: primary 0.50*sun, bleed 0.25*sun to others â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
var blOn = [flow.get('Z1Blinds'), flow.get('Z2Blinds'), flow.get('Z3Blinds'), flow.get('Z4Blinds')];
for (var i = 0; i < 4; i++) {
    if (blOn[i]) {
        if (i===0) z1level += sun * 0.50; else if (i===1) z2level += sun * 0.50;
        else if (i===2) z3level += sun * 0.50; else z4level += sun * 0.50;
        for (var j = 0; j < 4; j++) {
            if (i !== j) {
                if (j===0) z1level += sun * 0.25;
                else if (j===1) z2level += sun * 0.25;
                else if (j===2) z3level += sun * 0.25;
                else z4level += sun * 0.25;
            }
        }
    }
}

// â”€â”€ Shared luminaires â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (flow.get('Spotlight'))     { z1level += 250; z2level += 250; }       // north row
if (flow.get('SpotlightCD'))   { z3level += 250; z4level += 250; }       // south row
if (flow.get('CorridorLight')) { z1level += 150; z2level += 150; z3level += 150; z4level += 150; }

// â”€â”€ Ambient floor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
z1level += 25; z2level += 25; z3level += 25; z4level += 25;

// â”€â”€ Energy per tick â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
energy += flow.get('Z1Light') ? 1 : 0;
energy += flow.get('Z2Light') ? 1 : 0;
energy += flow.get('Z3Light') ? 1 : 0;
energy += flow.get('Z4Light') ? 1 : 0;
energy += flow.get('Spotlight')     ? 3 : 0;
energy += flow.get('SpotlightCD')   ? 3 : 0;
energy += flow.get('CorridorLight') ? 2 : 0;

// â”€â”€ Temperature decay (radiators are dummies â€” RL doesn't drive them) â”€
var z1temp = flow.get('Z1Temp'), z2temp = flow.get('Z2Temp');
var z3temp = flow.get('Z3Temp'), z4temp = flow.get('Z4Temp');
z1temp -= 0.02; z2temp -= 0.02; z3temp -= 0.02; z4temp -= 0.02;

var weaknessFired = false;

// __WEAKNESS_PATCH__

// â”€â”€ Clamp & write back â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
flow.set('Z1Level', Math.max(0, z1level));
flow.set('Z2Level', Math.max(0, z2level));
flow.set('Z3Level', Math.max(0, z3level));
flow.set('Z4Level', Math.max(0, z4level));
flow.set('Z1Temp', Math.min(35, Math.max(15, z1temp)));
flow.set('Z2Temp', Math.min(35, Math.max(15, z2temp)));
flow.set('Z3Temp', Math.min(35, Math.max(15, z3temp)));
flow.set('Z4Temp', Math.min(35, Math.max(15, z4temp)));
flow.set('TotalEnergyCost', energy);
flow.set('WeaknessFired', weaknessFired);

return msg;
"@

$initFn = @"
// 4-zone defaults â€” matches Custom2 TD shape.
['Z1Level','Z2Level','Z3Level','Z4Level'].forEach(function(k){ flow.set(k, 75); });
['Z1Light','Z2Light','Z3Light','Z4Light',
 'Z1Blinds','Z2Blinds','Z3Blinds','Z4Blinds',
 'Spotlight','SpotlightCD','CorridorLight',
 'Z1Radiator','Z2Radiator','Z3Radiator','Z4Radiator'].forEach(function(k){ flow.set(k, false); });
['Z1Temp','Z2Temp','Z3Temp','Z4Temp'].forEach(function(k){ flow.set(k, 21.0); });
flow.set('Sunshine', 150);
flow.set('SunshinePinned', false);
flow.set('TotalEnergyCost', 0);
flow.set('EnergyCost', 0);
flow.set('Hour', 0);
flow.set('WeaknessFired', false);
return msg;
"@

$statusFn = @"
msg.payload = {
    Z1Level: flow.get('Z1Level'), Z2Level: flow.get('Z2Level'),
    Z3Level: flow.get('Z3Level'), Z4Level: flow.get('Z4Level'),
    Z1Light: flow.get('Z1Light'), Z2Light: flow.get('Z2Light'),
    Z3Light: flow.get('Z3Light'), Z4Light: flow.get('Z4Light'),
    Z1Blinds: flow.get('Z1Blinds'), Z2Blinds: flow.get('Z2Blinds'),
    Z3Blinds: flow.get('Z3Blinds'), Z4Blinds: flow.get('Z4Blinds'),
    Spotlight: flow.get('Spotlight'),
    SpotlightCD: flow.get('SpotlightCD'),
    CorridorLight: flow.get('CorridorLight'),
    Z1Radiator: flow.get('Z1Radiator'), Z2Radiator: flow.get('Z2Radiator'),
    Z3Radiator: flow.get('Z3Radiator'), Z4Radiator: flow.get('Z4Radiator'),
    Z1Temp: flow.get('Z1Temp'), Z2Temp: flow.get('Z2Temp'),
    Z3Temp: flow.get('Z3Temp'), Z4Temp: flow.get('Z4Temp'),
    Sunshine: flow.get('Sunshine'),
    TotalEnergyCost: flow.get('TotalEnergyCost'),
    EnergyCost: flow.get('EnergyCost'),
    Hour: flow.get('Hour'),
    WeaknessFired: flow.get('WeaknessFired')
};
return msg;
"@

$actionFn = @"
msg.payload.cost = 0;
var actuators = {
    Z1Light: 100, Z2Light: 100, Z3Light: 100, Z4Light: 100,
    Z1Blinds: 5,  Z2Blinds: 5,  Z3Blinds: 5,  Z4Blinds: 5,
    Spotlight: 250, SpotlightCD: 250, CorridorLight: 80
};
Object.keys(actuators).forEach(function(name) {
    if (msg.payload[name] !== undefined) {
        var prev = flow.get(name);
        flow.set(name, msg.payload[name]);
        if (prev === false && msg.payload[name] === true) {
            msg.payload.cost = actuators[name];
            flow.set('EnergyCost', actuators[name]);
        }
    }
});
return msg;
"@

$resetFn = @"
var levels = [25, 75, 150, 500];
var sunshine = [0, 100, 400, 900];
['Z1Level','Z2Level','Z3Level','Z4Level'].forEach(function(k){
    flow.set(k, levels[Math.floor(Math.random() * levels.length)]);
});
['Z1Light','Z2Light','Z3Light','Z4Light',
 'Z1Blinds','Z2Blinds','Z3Blinds','Z4Blinds'].forEach(function(k){
    flow.set(k, Math.random() < 0.5);
});
flow.set('Spotlight',     Math.random() < 0.3);
flow.set('SpotlightCD',   Math.random() < 0.3);
flow.set('CorridorLight', Math.random() < 0.3);
flow.set('Sunshine', sunshine[Math.floor(Math.random() * sunshine.length)]);
flow.set('SunshinePinned', false);
flow.set('TotalEnergyCost', 0);
flow.set('EnergyCost', 0);
flow.set('WeaknessFired', false);
flow.set('dynamics_state', null);
flow.set('partition_counter', 0);
flow.set('partition_open', false);
msg.payload = { reset: true };
return msg;
"@

$setStateFn = @"
// Pin simulator to a deterministic state for benchmarking.
var p = msg.payload, keys = [
    'Z1Level','Z2Level','Z3Level','Z4Level',
    'Z1Light','Z2Light','Z3Light','Z4Light',
    'Z1Blinds','Z2Blinds','Z3Blinds','Z4Blinds',
    'Spotlight','SpotlightCD','CorridorLight'
];
keys.forEach(function(k){ if (p[k] !== undefined) flow.set(k, p[k]); });
if (p.Sunshine !== undefined) { flow.set('Sunshine', p.Sunshine); flow.set('SunshinePinned', true); }
flow.set('TotalEnergyCost', 0);
flow.set('EnergyCost', 0);
msg.payload = { status: 'ok' };
return msg;
"@

$healthFn = @"
// Idempotent liveness probe. Reports tab id, uptime since flow start,
// and which RL endpoints have been wired in this flow. Used by:
//   - run_full_project.ps1 Wait-Simulator
//   - gradle :preflight task
var started = flow.get('__startedAt');
if (!started) { started = Date.now(); flow.set('__startedAt', started); }
msg.payload = {
    status: 'ok',
    tab: '__TAB__',
    uptime_ms: Date.now() - started,
    endpoints: {
        status:   true,
        action:   true,
        reset:    true,
        setState: true
    }
};
msg.statusCode = 200;
msg.headers = { 'Content-Type': 'application/json' };
return msg;
"@

# ---------------------------------------------------------------------------
# Build one flow array (list of Node-Red node dicts) given a profile name.
# ---------------------------------------------------------------------------
function Build-Flow {
    param([string]$profile, [string]$tabLabel, [string]$envFnBody)

    $p = $profile  # short alias used as id prefix
    @(
        @{ id="${p}_tab"; type="tab"; label=$tabLabel; disabled=$false; info="Auto-generated by simulator/generate_flows.ps1. Run with: node-red --userDir .node-red-$p --port $($p -replace 'custom','')+1880 simulator/simulator_flow_$p.json" },
        @{ id="${p}_inject_start"; type="inject"; z="${p}_tab"; name="OnStart"; topic=""; payload=""; payloadType="date"; repeat=""; crontab=""; once=$true; onceDelay=0.1; x=200; y=240; wires=@(,@("${p}_init")) },
        @{ id="${p}_init"; type="function"; z="${p}_tab"; name="Initialization"; func=$initFn; outputs=1; noerr=0; x=430; y=240; wires=@(,@()) },
        @{ id="${p}_http_status"; type="http in"; z="${p}_tab"; name=""; url="/was/rl/status"; method="get"; upload=$false; swaggerDoc=""; x=230; y=340; wires=@(,@("${p}_status_fn")) },
        @{ id="${p}_status_fn"; type="function"; z="${p}_tab"; name="Status"; func=$statusFn; outputs=1; noerr=0; x=430; y=340; wires=@(,@("${p}_http_status_resp")) },
        @{ id="${p}_http_status_resp"; type="http response"; z="${p}_tab"; name=""; statusCode=""; headers=@{}; x=630; y=340; wires=@() },
        @{ id="${p}_http_action"; type="http in"; z="${p}_tab"; name=""; url="/was/rl/action"; method="post"; upload=$false; swaggerDoc=""; x=230; y=420; wires=@(,@("${p}_action_fn")) },
        @{ id="${p}_action_fn"; type="function"; z="${p}_tab"; name="Update action"; func=$actionFn; outputs=1; noerr=0; x=460; y=420; wires=@(,@("${p}_http_action_resp")) },
        @{ id="${p}_http_action_resp"; type="http response"; z="${p}_tab"; name=""; statusCode=""; headers=@{}; x=660; y=420; wires=@() },
        @{ id="${p}_inject_repeat"; type="inject"; z="${p}_tab"; name="Repeat"; topic=""; payload=""; payloadType="date"; repeat="0.2"; crontab=""; once=$true; onceDelay="1"; x=220; y=520; wires=@(,@("${p}_env_fn")) },
        @{ id="${p}_env_fn"; type="function"; z="${p}_tab"; name="Update environment"; func=$envFnBody; outputs=1; noerr=0; x=480; y=520; wires=@(,@()) },
        @{ id="${p}_http_reset"; type="http in"; z="${p}_tab"; name=""; url="/was/rl/reset"; method="post"; upload=$false; swaggerDoc=""; x=230; y=620; wires=@(,@("${p}_reset_fn")) },
        @{ id="${p}_reset_fn"; type="function"; z="${p}_tab"; name="Reset episode"; func=$resetFn; outputs=1; noerr=0; x=460; y=620; wires=@(,@("${p}_http_reset_resp")) },
        @{ id="${p}_http_reset_resp"; type="http response"; z="${p}_tab"; name=""; statusCode=""; headers=@{}; x=660; y=620; wires=@() },
        @{ id="${p}_http_setstate"; type="http in"; z="${p}_tab"; name=""; url="/was/rl/setState"; method="post"; upload=$false; swaggerDoc=""; x=230; y=700; wires=@(,@("${p}_setstate_fn")) },
        @{ id="${p}_setstate_fn"; type="function"; z="${p}_tab"; name="Set state (benchmark)"; func=$setStateFn; outputs=1; noerr=0; x=470; y=700; wires=@(,@("${p}_http_setstate_resp")) },
        @{ id="${p}_http_setstate_resp"; type="http response"; z="${p}_tab"; name=""; statusCode=""; headers=@{}; x=670; y=700; wires=@() },
        @{ id="${p}_http_health"; type="http in"; z="${p}_tab"; name=""; url="/health"; method="get"; upload=$false; swaggerDoc=""; x=230; y=780; wires=@(,@("${p}_health_fn")) },
        @{ id="${p}_health_fn"; type="function"; z="${p}_tab"; name="Health"; func=$healthFn.Replace("__TAB__", "${p}_tab"); outputs=1; noerr=0; x=440; y=780; wires=@(,@("${p}_http_health_resp")) },
        @{ id="${p}_http_health_resp"; type="http response"; z="${p}_tab"; name=""; statusCode=""; headers=@{}; x=640; y=780; wires=@() }
    )
}

# ---------------------------------------------------------------------------
$tabLabels = @{
  "custom2" = "Custom2 Lab â€” W1 missing-stereotype (port 1882)"
  "custom3" = "Custom3 Lab â€” W2 context-dependent (port 1883)"
  "custom4" = "Custom4 Lab â€” W3 dynamics (port 1884)"
  "custom5" = "Custom5 Lab â€” W4 shared resource (port 1885)"
  "custom6" = "Custom6 Lab â€” W5 dynamic topology (port 1886)"
  "custom7" = "Custom7 Lab â€” W6 multi-objective heat (port 1887)"
}

foreach ($profile in @("custom2","custom3","custom4","custom5","custom6","custom7")) {
    $envBody = $envFnBaseTemplate.Replace("// __WEAKNESS_PATCH__", $weaknessPatches[$profile])
    $flow = Build-Flow -profile $profile -tabLabel $tabLabels[$profile] -envFnBody $envBody
    $json = $flow | ConvertTo-Json -Depth 10
    $out = Join-Path -Path (Get-Location) -ChildPath "simulator_flow_$profile.json"
    $json | Set-Content -Path $out -Encoding utf8
    Write-Host "  wrote  $out  ($([Math]::Round((Get-Item $out).Length / 1024, 1)) KB)"
}

Write-Host "`nAll 6 simulator flow files written successfully."
