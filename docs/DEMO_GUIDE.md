# Demo guide — what to run, what it shows, what to say

> **⚠ Superseded (2026-07-09):** the primary demo is now the **phase-oriented web demo** in
> [`dashboard/`](../dashboard/README.md) — `cd dashboard && npm install && npm run dev`. It covers all four
> thesis phases with interactive lab sandboxes, side-by-side trained-agent replays, the Phase-2 fault
> walk-through, and the registered/certified results. The "Demo B — Agent Trace Cockpit" described below was
> the pre-pivot W1–W6 weakness dashboard and no longer exists in that form. Demo A (the terminal decision
> explainer) still works as documented.

Two complementary demos make the agents' decisions visible for the meeting. **Demo A** (terminal)
narrates *why* the agent picks each action in plain language from real benchmark logs. **Demo B**
(dashboard) shows the *zone-by-zone state evolution* of a real run in a browser. Both run on real,
already-collected data — **nothing needs to be retrained for the meeting.**

---

## Demo A — Decision Explainer (terminal, zero dependencies)

**What it is.** A stdlib-only Python script that reads the per-step benchmark logs
(`bench_step_log_<mode>.csv`) and prints a step-by-step narration of each action, translating raw
actuator toggles into the stereotype reasoning behind them (Causes vs. Mediates, blind↔sun,
disabled actuators, energy cost) and whether the zone ranks moved toward the target.

**Why it's the headline demo.** It directly answers the advisor's "show what decisions the agents
make and why" — side by side, you can show the **informed** agent reaching the goal with a
**blind** (cheap, sun-harvesting) while the **uninformed** agent flails.

### Run it

> **Use the authoritative n=10 sweep data**, not the local `benchmark/results/custom9/` folder. The
> local folder is a single stale dev run whose start states are saturated (everything already on, sun
> at night) — `--auto` will land on a dull scenario where *both* agents fail. The compelling
> bright-sun story (scenario 19) lives in `tmp_sweep_n10_results/`.

```powershell
# Side-by-side, auto-pick the most illustrative scenario:
python analysis/demo_decision_explainer.py `
  --true  "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_true/bench_step_log_ql_true.csv" `
  --false "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_false/bench_step_log_ql_false.csv" `
  --auto

# A specific scenario (e.g. the bright-sun one where the blind shines):
python analysis/demo_decision_explainer.py `
  --true  "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_true/bench_step_log_ql_true.csv" `
  --false "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_false/bench_step_log_ql_false.csv" `
  --scenario 19

# Write a clean Markdown transcript for slides (no console emoji issues):
python analysis/demo_decision_explainer.py `
  --true  "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_true/bench_step_log_ql_true.csv" `
  --false "tmp_sweep_n10_results/benchmark/results_seed4/custom9/ql_false/bench_step_log_ql_false.csv" `
  --auto --md docs/demo_walkthrough_custom9.md
```

A pre-rendered transcript is already saved at
[demo_walkthrough_custom9.md](demo_walkthrough_custom9.md) — open it directly if you'd rather not
run anything live.

### How to read / narrate it

- Each `t<N>` line is one benchmark step: the action chosen, a plain-language gloss, and the
  **zone ranks before → after** (rank 3 = bright, 2 = medium, the targets).
- **Causes** actions (`Z*Light`) = lamps: always add light, reliable, cost 100 energy each.
- **Mediates** actions (`Z*Blinds`) = blinds: add light *only when the sun is up* — the
  sun-conditioned lever the stereotype encodes; cheaper than lamps when sun is high.
- Lines flagged **disabled in custom9** (`Spotlight*`) are no-ops — picking them is a tell-tale of a
  **non-converged** policy (useful to point out for the uninformed agent).

### Talking points it supports

- "On scenario 19 (bright sun) the informed agent reaches **all four** zone targets at **step 1** by
  opening a blind to harvest daylight, then one lamp — total energy 100."
- "The uninformed agent, same scenario, opens a blind but then toggles a lamp **off** and never
  converges — it stays stuck at ranks (2,2,2,2) for all 20 steps. That is the learning-speed gap,
  made concrete on a single trajectory."

> **Note on console characters.** The script writes UTF-8 and reconfigures stdout, so emoji render
> in a normal terminal. If you pipe it through `Select-Object`/`more`, the glyphs may garble — use
> `--md` for slide-ready text instead.

---

## Demo B — Agent Trace Cockpit (browser dashboard)

**What it is.** A React/Vite dashboard that replays a **real custom9 `ql_true` benchmark trace**
(seed 4), showing each zone's predicted vs. observed level change as the agent steps through a
scenario. The trace file is `dashboard/public/demo-traces/custom9-ql-true-demo.jsonl` (2 432 real
steps) with a schema header that tells the dashboard the 13 state slots, the level domain, and the
per-zone targets.

### Run it

```powershell
cd dashboard
npm install      # first time only
npm run dev      # then open the printed URL, usually http://localhost:5173
```

In the app header click **`load demo (custom9)`**. (The **`load demo (W1)`** button still loads the
original wrong-prior fixture if you want to contrast.)

### How to read / narrate it

- The grid shows the **four zones**; each cell tracks the zone's level rank and whether it hit
  target. `Sunshine` is shown as a shared signal (the IV that gates the blinds).
- Step through the timeline to watch the informed agent converge the zones toward their targets.
- Action labels appear as `action #N` (the dashboard cannot recover the reasoner's HashMap label
  ordering) — that's expected; the **zone grid + predicted/observed deltas are the story** here.
  For exact action *names*, use Demo A.

### Talking points it supports

- "This is a *real* benchmark trajectory, not a mock-up — the agent's predicted deltas come from the
  stereotype reasoner, the observed deltas from the simulator."
- "You can see the per-zone targets being satisfied and the sunshine signal that drives the blind
  decisions."

---

## Suggested 5-minute meeting flow

1. **Open Demo A** (`--scenario 19` or the saved transcript). Walk one informed-vs-uninformed
   scenario. Land the line: *blind beats lamp at bright sun → energy gap is real.* (≈2 min)
2. **Switch to Demo B**, load the custom9 trace, step through a couple of scenarios to show the live
   zone convergence. (≈2 min)
3. **Pivot to the storyline** using [thesis_meeting_2026-06-08.md](thesis_meeting_2026-06-08.md): the
   mechanism works (custom3/custom5, energy on all labs), the headline custom9 negative is a
   *training-distribution coverage bug* (sun pinned to rank 2 — see
   [simple_labs_design.md](simple_labs_design.md) §3.2), and the simple-lab track is the fix. (≈1 min)

---

## Files at a glance

| File | Role |
|---|---|
| [analysis/demo_decision_explainer.py](../analysis/demo_decision_explainer.py) | Demo A script |
| [docs/demo_walkthrough_custom9.md](demo_walkthrough_custom9.md) | Pre-rendered Demo A transcript |
| `dashboard/public/demo-traces/custom9-ql-true-demo.jsonl` | Demo B real trace (seed 4) |
| [dashboard/src/App.jsx](../dashboard/src/App.jsx) | Dashboard entry (has the custom9 button) |
| [docs/thesis_meeting_2026-06-08.md](thesis_meeting_2026-06-08.md) | The meeting brief / storyline |
| [docs/simple_labs_design.md](simple_labs_design.md) | Simple-lab track + custom9 fix arithmetic |
