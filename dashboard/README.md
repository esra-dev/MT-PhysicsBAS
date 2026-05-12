# Agent Trace Cockpit — MT-Esra Dashboard

A local React + Vite dashboard for the **MT-Esra** thesis project (stereotype-guided
Q-learning for smart-building illuminance control). It is built for a mid-term
presentation: load a benchmark trace and explain, step by step, what the agent
saw, what the ontology predicted, what the simulator actually did, and which
weakness pattern (W1 – W6) fired.

## Quick start

```powershell
cd dashboard
npm install
npm run dev
```

Vite will print a local URL — typically <http://localhost:5173>. The dashboard
auto-loads the W1 demo fixture so it looks meaningful immediately.

## Two modes

### 1. Replay Mode (default)
Loads a JSONL benchmark trace produced by `BenchmarkLogger.recordRichStep` at
`benchmark/results/<profile>/<mode>/trace_bench_<mode>.jsonl`.

- Click **load .jsonl** to open any trace file from disk.
- Click **load demo (W1)** to load the bundled W1 CorridorLight hidden-bleed
  demo (`dashboard/public/demo-traces/custom2-w1-demo.jsonl`).

> ⚠ The demo fixture is **clearly labeled** as DEMO data (orange `DEMO FIXTURE`
> pill in the source strip). It is *not* real benchmark output. It exists
> because, at the time of writing, `benchmark/results/custom2/ql_true/trace_bench_ql_true.jsonl`
> was empty (the rich-trace JSONL has not yet been re-generated for custom2).
> Once you run the bench again the file is loadable directly.

### 2. Live Mode (optional)
Click **live mode** in the header. The dashboard polls
`GET /was/rl/status` and lets you POST `/was/rl/action` on a running Node-RED
simulator. Requests are proxied through Vite to avoid CORS:

| Vite request | Forwarded to |
| --- | --- |
| `/sim/was/rl/status` | `http://localhost:1882/was/rl/status` |
| `/sim/was/rl/action` | `http://localhost:1882/was/rl/action` |

To target a different simulator port (e.g. the default lab on `1880`), start
Vite with the `SIM_URL` env var:

```powershell
$env:SIM_URL = "http://localhost:1880"
npm run dev
```

## What you see

| Panel | What it shows |
| --- | --- |
| **Left – 4-Zone Lab View** | Z1–Z4 in a 2×2 grid, with current illuminance rank (dark / dim / medium / bright), target rank, light + blinds + temperature/radiator state when present. Green = at target, amber = ±1 rank, red = mismatch. A pink glow highlights zones whose state slot mismatched the ontology prediction this step. |
| **Center – Agent Decision Trace** | Selected step’s scenario / run / step / chosen action, state-before, state-after, ontology Δ, observed Δ, |Δq|, applicable actions, plus a plain-language **Explanation** block listing every weakness reason that fired. A collapsible **raw evidence** drawer shows the exact JSONL row. |
| **Right – Weakness Detector** | W1 – W6 cards. Cards light up pink when fired on the current step, and each card shows a per-trace count (`N×`). |
| **Bottom – Timeline** | Play / pause, prev / next, speed (0.5×–8×), and a clickable tick for every step. Steps where any weakness fired carry a pink `!` marker. |

## Demo story (priority W1 · custom2)

The bundled demo replays a CorridorLight hidden-bleed:

1. Steps 1–2: agent turns on Z1Light → Z2Light. Ontology predicts only the
   directly-modified slots; observed Δ matches.
2. **Step 4 – CorridorLight ON.** Ontology says only `CorridorLight` flips.
   The simulator instead lifts **Z3Level and Z4Level by one rank**.
   ⇒ `W1 unmodelled cross-zone effect` fires. The right panel highlights W1,
   the affected zones glow pink in the lab view, and the centre panel reads:
   *"Observed Z3Level (+1), Z4Level (+1) changed, but the ontology prediction
   did not include Z3Level, Z4Level. This is classified as an unmodelled
   cross-zone effect (W1)."*
3. **Step 6 – CorridorLight OFF.** The bleed reverses: Z3 and Z4 drop again.
   W1 fires a second time. The agent then has to spend two more steps turning
   on Z3Light and Z4Light.

This visualises the central thesis claim: **component-level stereotypes do not
generalise to whole-lab behaviour**, and the W1 firing is the evidence.

## Trace schema

Real benchmark traces are JSONL with one record per step:

```json
{"scenarioId":1,"runId":1,"step":0,"actionIdx":1,"qDelta":0.0,
 "stateBefore":[2,2,0,0,0,0,1,0],"stateAfter":[2,2,0,0,0,0,1,0],
 "predictedDelta":[0,0,0,0,0,0,0,0],"applicableActions":[0,1,...,10],
 "weaknessFired":[]}
```

The default 8-slot Q-learner schema is auto-applied:
`[Z1Level, Z2Level, Z1Light, Z2Light, Z1Blinds, Z2Blinds, Spotlight, Sunshine]`.

For richer fixtures (4-zone, custom actuators, action labels, targets) the
dashboard also accepts an **optional first-line metadata header**:

```json
{"$schema":"mt-esra/v1","slots":["Z1Level","Z2Level","Z3Level","Z4Level", "..."],
 "levelDomain":4,"targets":{"Z1":2,"Z2":2,"Z3":2,"Z4":2},
 "actions":{"0":"Z1Light ON","1":"Z1Light OFF","..."},
 "isDemo":true,"label":"DEMO ..."}
```

This header is dashboard-only; the Java `BenchmarkLogger` does **not** emit it
and is unaffected.

## Limitations

- **No live trace tail.** Replay mode loads the trace once; reload the file to
  see new rows.
- **Demo fixture is hand-authored.** Pink-highlighted W1 events on the demo are
  illustrative. Real benchmark runs may show different counts and patterns.
- **8-slot default.** If your trace has more slots and you don’t supply a
  `$schema` header, slots beyond Z2 are shown in the *Shared / environment*
  strip rather than as zones Z3 / Z4.
- **Live mode** assumes the simulator exposes `GET /was/rl/status` and
  `POST /was/rl/action` (as documented in `simulator/README.md`). If those
  routes 404, the modal will surface the HTTP error.

## Project structure

```
dashboard/
├── package.json
├── vite.config.js
├── index.html
├── public/
│   └── demo-traces/
│       └── custom2-w1-demo.jsonl
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── styles.css
    ├── components/
    │   ├── ZoneGrid.jsx
    │   ├── DecisionTrace.jsx
    │   ├── WeaknessPanel.jsx
    │   ├── Timeline.jsx
    │   ├── RawDrawer.jsx
    │   └── LiveMode.jsx
    └── lib/
        ├── parseTrace.js
        └── weakness.js
```

The Gradle / Jason / Node-RED parts of the project are **not** modified.
