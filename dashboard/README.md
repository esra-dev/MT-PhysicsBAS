# MT-Esra Phase Demo — web interface for the four-phase thesis arc

A local React + Vite app that presents the whole project **phase by phase** for advisors:
what each lab is, how its physics behaves, what the trained agents actually did (side by
side), where the KG-primed and tabula-rasa agents differ, and the statistical findings.

> This replaces the old "Agent Trace Cockpit" (the pre-pivot W1–W6 weakness demo).

## Quick start

```powershell
cd dashboard
npm install        # first time only
npm run dev        # open the printed URL, usually http://localhost:5173
```

No simulator, no Gradle, no training run needed — everything is driven by data already
committed under `dashboard/public/data/`.

## Pages

| Page | What you can show |
|---|---|
| **Overview** | The pivot story, the three arms (`ql_true` / `ql_false` / `rule_based`), the lab ladder, one headline per phase. |
| **Phase 1 · Clean** | Per-lab (lab1/2/3) interactive **physics sandbox** (click actuators, set the episode sun — exact simulator formulas), **side-by-side replay** of the real trained agents on the held-out benchmark scenarios (divergence steps highlighted), first-50-episode training curves, and the confirmatory n = 10 `kg_only` statistics. |
| **Phase 2 · Faults** | A **live fault walk-through**: actuate a dead lamp, watch KG-predicted vs observed Δ evidence accumulate to the real thresholds (≥20 samples, dead-rate ≥ 0.8), then blacklist → alert → warm restart → re-learn (the recovered policy is computed live from the surviving actuators). Below: the registered 8-cell Tier-1 recovery-speed result with CIs and q-values. |
| **Phase 3 · Dynamics** | Slow-lab sandbox where blinds visibly take 12 ticks to move, a deadline-planner toy ("bright immediately" vs "within 5 min"), learned-vs-ground-truth delay chart, deadline-compliance results. |
| **Phase 4 · Knowledge** | lab4 smart-plug **trap scenario** (lamp ON, plug OFF) as an interactive sandbox + replay of the tabula-rasa agent fighting the AND-gate; lab5 energy sandbox with a live power-vs-budget meter + replay; certified n = 20 results and the KG-vs-LLM comparison. |

Every chart has a hover tooltip and a `table view` twin; agents are consistently colored
(blue = KG-primed, green = tabula-rasa, gray = rule-based/LLM context).

## Where the data comes from (all real, none mocked)

| File | Source |
|---|---|
| `public/data/replay_lab{1..5}.json` | `benchmark/results_full_seed1/lab{1,2,3}/ql_true/bench_step_log_*.csv`, `benchmark/results/lab{4,5}/ql_true/bench_step_log_*.csv` + `benchmark/scenarios_lab*.json` |
| `public/data/training.json` | `metrics_stereotypes_{true,false}_lab*.csv` (first 50 training episodes, seed 1) |
| `public/data/phase1.json` + `img/p1_curve_*.png` | `phase1_headline_download/kg_only/analysis/out/` (clean KG-only factorial, n = 10) |
| `public/data/phase2.json` | `analysis/out_phase2_registered/` (frozen §9 registered analysis, incl. the seed 11–20 replication) |
| `public/data/phase3.json` | `analysis/out/phase3_delay_accuracy.csv`, `phase3_compliance_ci.csv` |
| `public/data/phase4.json` | `analysis/out/summary_table.csv`, `phase4_llm_summary.csv`; certified n = 20 numbers hardcoded from `docs/PHASE4.md` §10a (run 27905392725) |

The **sandboxes** don't need data at all: `src/lib/physics.js` re-implements each lab's
exact simulator formulas (source of truth: `simulator/simulator_flow_lab*.json`,
documented in `docs/LAB_REFERENCE.md`).

To regenerate the JSON after new benchmark runs:

```powershell
python dashboard/scripts/prepare_data.py
```

## Suggested 10-minute advisor flow

1. **Overview** (1 min) — the stance: priors accelerate clean learning; faults are detected, not adapted to.
2. **Phase 1, lab2** (3 min) — sandbox: show the blind is free light only when the sun is up; replay: KG agent
   solves in 1 step where tabula-rasa needs 10; scroll to the n = 10 curves + AUC tiles.
3. **Phase 2** (3 min) — fast-forward the fault console to the `[FAULT]` alert, click *re-learn with survivors*;
   then the 8-cell chart: KG bars short and tight, tabula-rasa long and wild.
4. **Phase 3** (1 min) — toggle a blind, watch the 12-tick countdown; click both deadline goals.
5. **Phase 4, lab4 then lab5** (2 min) — the plug trap; the energy replay ("which lamp does each agent reach
   for?"); close on the certified compliance tiles and the LLM comparison.

## Project structure

```
dashboard/
├── scripts/prepare_data.py     # repo CSVs → public/data/*.json (stdlib only)
├── public/data/                # generated demo data (committed)
└── src/
    ├── App.jsx                 # sidebar + hash routing
    ├── lib/physics.js          # exact per-lab simulator physics + fault/slow variants
    ├── lib/useData.js          # fetch-with-cache hook
    ├── components/
    │   ├── LabView.jsx         # zones, rank meters, actuators, sun strip, power meter
    │   ├── Sandbox.jsx         # interactive physics (incl. slow-blind countdown)
    │   ├── Replay.jsx          # side-by-side trained-agent replay from bench logs
    │   ├── FaultLab.jsx        # Phase-2 detect→blacklist→re-learn walk-through
    │   ├── charts.jsx          # HBarChart / LineChart / tiles / tooltips
    │   └── icons.jsx
    └── pages/                  # Overview, Phase1..Phase4
```
