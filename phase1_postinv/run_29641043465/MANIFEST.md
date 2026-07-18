# Phase 1 — arm-C prior-decay E-sweep point **E = 750** (`phase1_kg_only_e750`)

**Run ID:** `29641043465`
**Workflow:** `.github/workflows/phase1.yml` ("Phase 1 (KG acceleration, clean labs)")
**Branch:** `kg-crosszone-coupling-mid`
**Head SHA:** `05dd83587cbe2771f50e2c7ab5dda7e1162f018c` (`05dd835`)
**Dispatched / completed:** 2026-07-18 10:33:33Z → 11:02:06Z
**Conclusion:** success — 52 / 52 jobs green
**Dispatch:** `run_mode=phase1_kg_only_e750`, `profiles=lab2,lab3`,
`seeds=1..5`, `publish_results=true`. `run_mode: "phase1_kg_only_e750"`
verified in all 20 `TRAINING_OK.json` cells (5 seeds × 2 labs × 2 arms).
(First dispatch attempt `29640819045` failed pre-simulation: the runner
scripts' `-RunMode` ValidateSet did not yet admit the sweep profiles; fixed in
`05dd835`, this run is the valid re-dispatch.)
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29641043465

## Standing of this run

**Exploratory sensitivity point, not a headline.** One of the two dispatches of
the registered E-decay sensitivity sweep (`THESIS_STATE_REPORT.md` Addendum
2026-07-18 item 4): identical to arm C (`phase1_kg_only`) except
`stereo_prior_decay_episodes = 750` (the auto ¼-budget value, set explicitly).
The design is E ∈ {750, 3000, 10000} on lab2, lab3 × seeds 1–5; the E = 10000
point is the arm-C run of record `29639767776` restricted to seeds 1–5
(recomputed with the identical pipeline; archived at
`phase1_postinv/run_29639767776_seeds1-5_reanalysis/`). n = 5, BH family m = 8
(learning-speed) / m = 28 (benchmark) — smaller families than the headline run;
do not mix q-values across the two layouts.

Key numbers (Δ = ql_true − ql_false, seed-paired, n = 5), read verbatim from
`analysis/out/learning_speed_tests.csv` / `paired_tests.csv`:

- lab2 `auc_goal` **+0.02711** [0.01867, 0.03795], q = 0, δ = 1.0 — headline
  primary robust at E = 750.
- lab3 `auc_reward` **+12.55** [4.87, 19.62], q = 0.0016, δ = 0.92 — robust.
- lab3 `mean_first_goal` +10.10 (q = 0.678, ns) — the E = 10000 timing tax is
  absent at E = 750.
- lab3 benchmark: `avg_cycling` **+0.85** (q ≈ 0, δ = 0.96), `avg_redundant`
  **+1.48** (q ≈ 0, δ = 0.84) — the policy-quality tax is *larger* than at
  E = 10000 (ns on the same seeds).

Interpretation (E trades the lab3 timing tax for a policy-quality tax; the
headline is E-robust): `THESIS_STATE_REPORT.md` Addendum 2026-07-18b.

## Provenance of the archived files

- Source artifact: **`phase1-consolidated`** (artifact id `8428853523`,
  3,163,633 bytes,
  `sha256:0f2b8e2f04df4d904a41b4dcbb8b269952be91fe69cc1775ae661d7095a0c4f1`,
  GitHub expiry 2026-10-16). Downloaded and extracted 2026-07-18.
- Also published to the **`results` branch** as commit `da7f925`
  (tag `results-20260718-110158-phase1_kg_only_e750-05dd835`, append mode,
  pushed by CI).

Curation rule and pruned-file list identical to
`phase1_postinv/run_29639767776/MANIFEST.md`.
