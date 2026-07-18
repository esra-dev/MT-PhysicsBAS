# Phase 1 — arm-C prior-decay E-sweep point **E = 3000** (`phase1_kg_only_e3000`)

**Run ID:** `29641899071`
**Workflow:** `.github/workflows/phase1.yml` ("Phase 1 (KG acceleration, clean labs)")
**Branch:** `kg-crosszone-coupling-mid`
**Head SHA:** `05dd83587cbe2771f50e2c7ab5dda7e1162f018c` (`05dd835`)
**Dispatched / completed:** 2026-07-18 11:03:18Z → 11:32:25Z
**Conclusion:** success — 52 / 52 jobs green
**Dispatch:** `run_mode=phase1_kg_only_e3000`, `profiles=lab2,lab3`,
`seeds=1..5`, `publish_results=true`; queued only after the E = 750 run
finished (phase1 concurrency group cancels older *pending* runs).
`run_mode: "phase1_kg_only_e3000"` verified in all 20 `TRAINING_OK.json`
cells (5 seeds × 2 labs × 2 arms).
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29641899071

## Standing of this run

**Exploratory sensitivity point, not a headline.** Second dispatch of the
registered E-decay sensitivity sweep (`THESIS_STATE_REPORT.md` Addendum
2026-07-18 item 4): identical to arm C (`phase1_kg_only`) except
`stereo_prior_decay_episodes = 3000` (= the lab3 training budget). Sweep
design and family-size caveats: see `run_29641043465/MANIFEST.md`.

Key numbers (Δ = ql_true − ql_false, seed-paired, n = 5), read verbatim from
`analysis/out/learning_speed_tests.csv` / `paired_tests.csv`:

- lab2 `auc_goal` **+0.01484** [0.00710, 0.02257], q = 0, δ = 1.0 — headline
  primary robust at E = 3000.
- lab2 `mean_first_goal` **−15.51** [−25.49, −5.04], q = 0.0064 (KG faster) —
  sign-unstable across E at n = 5 (E = 10000 seeds 1–5: +29.50, q = 0.0164);
  treat as secondary volatility.
- lab3 `auc_reward` **+17.81** [11.84, 23.54], q = 0, δ = 1.0 — robust.
- lab3 `auc_goal` **−0.00650** [−0.00950, −0.00350], q = 0, δ = −0.88 — a
  significant KG *deficit* on the lab3 primary, unique to this E point
  (ns at E = 750 and E = 10000); n = 5 exploratory, disclosed, not smoothed.
- lab3 `mean_first_goal` +19.58 (q = 0.604, ns) — the E = 10000 timing tax is
  absent at E = 3000.
- lab3 benchmark: `avg_cycling` **+1.2125** (q ≈ 0, δ = 1.0), `avg_redundant`
  **+2.425** (q ≈ 0, δ = 1.0), `goal_rate` **−0.05** (q = 0.0007, δ = −0.8) —
  the worst benchmark outcome of the three E points.

Interpretation (E trades the lab3 timing tax for a policy-quality tax; the
headline is E-robust): `THESIS_STATE_REPORT.md` Addendum 2026-07-18b.

## Provenance of the archived files

- Source artifact: **`phase1-consolidated`** (artifact id `8429105063`,
  3,179,346 bytes,
  `sha256:7b10766ca268eec70dc42f7bef6aa9b8323d2dd667a07c87e773332ed4d77704`,
  GitHub expiry 2026-10-16). Downloaded and extracted 2026-07-18.
- Also published to the **`results` branch** as commit `628c9a9`
  (tag `results-20260718-113217-phase1_kg_only_e3000-05dd835`, append mode,
  pushed by CI).

Curation rule and pruned-file list identical to
`phase1_postinv/run_29639767776/MANIFEST.md`.
