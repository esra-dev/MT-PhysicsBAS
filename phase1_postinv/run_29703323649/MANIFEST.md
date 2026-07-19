# Run of record — `phase1_redundancy_only` control arm (registered, Addendum 2026-07-19e)

- **GitHub Actions run:** 29703323649 (`phase1.yml`, `workflow_dispatch`),
  created 2026-07-19 ~20:52 UTC, **success 102/102 jobs**.
- **Inputs:** `run_mode=phase1_redundancy_only`, `profiles=lab2,lab3`,
  `seeds=1,…,10`, `publish_results=true` — verbatim the registered dispatch
  (dispatch 2; dispatch 1 = run 29703115983 failed pre-data at `-RunMode`
  ValidateSet, deviation note in Addendum 2026-07-19e).
- **Head SHA:** `e664f3f` — contains the Addendum 2026-07-19e registration
  (registration ⊂ dispatched tree).
- **Results tag:** `results-20260719-212249-phase1_redundancy_only-e664f3f`
  verified on origin via `git ls-remote` (points at `e664f3f`).
- **CI artifact:** `phase1-consolidated`, id 8447388203,
  sha256 `47c6c1c4c35af9da287219a8f9a69a46761d5721241e503e8f5857c9e3c38399`
  (GitHub-reported digest), 5 645 379 bytes.
- **Guard:** `run_mode: "phase1_redundancy_only"` verified in all 40 per-cell
  `TRAINING_OK.json`.
- **Curation:** same as `run_29692725784/` — per-seed `qtable_*`, `metrics_*`,
  and `bench_step_log*` pruned from `benchmark/results_seed*/`; archive-root
  convenience copies (seed 1) retained as staged by the CI aggregate.
- **verification/**: seed-1 lab2 KG-arm `qtable_initial_*_zone{1,2}.csv` from
  CI artifact `train-lab2-stereo-true-seed-1` — value distribution is exactly
  {0.0 ×5120, −50.0 ×4096} per zone (registry redundancy Rule 1 only; no
  +7.5·gap constructive bonus, no IV wells), vs a normal stereo-mode initial
  table's {−50, 0, +7.5, +15, +22.5}. This is the operational proof that
  `stereo.redundancyOnly=true` was in force in the run.

## Registered primary (Addendum 2026-07-19e §2) — outcome

lab2 `auc_goal` Δ_red (ql_true − ql_false, n = 10, seeds 1–10):
**+0.016656 [0.009803, 0.023258]**, p_boot < 10⁻⁴, p_wil = 0.0039, δ = 0.94
(`analysis/out/learning_speed_tests.csv`).

Seed-matched arm-C comparator: +0.01679 [0.00959, 0.02606] (run 29639767776).
Pre-committed rule: Δ_red significant and ≥ ⅔·Δ_KG (+0.01119) → **OUTCOME A**:
the trivially derivable redundancy heuristic reproduces ≈ 99% of the lab2
anchor point estimate. Reporting consequences: Addendum 2026-07-19g.

Do not swap this run into §5.2 — it is the registered *control* arm, not the
headline. Cite via Addendum 2026-07-19g.
