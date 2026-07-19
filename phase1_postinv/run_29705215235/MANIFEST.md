# Exploratory run — `lab2noise` robustness pilot (Addendum 2026-07-19f)

**EXPLORATORY — nothing here is confirmatory; never pool or compare numerically
with clean-lab2 estimates (19f reading rule iv).**

- **GitHub Actions run:** 29705215235 (`phase1.yml`, `workflow_dispatch`),
  2026-07-19 ~22:00 UTC, **success 27/27 jobs** (dispatch 2; dispatch 1 = run
  29705065298 failed pre-data at the `-OnlyProfiles` KnownProfiles allow-list,
  fixed in `08bcd6c`).
- **Inputs:** `run_mode=phase1_kg_only`, `profiles=lab2noise`, `seeds=1,…,5`,
  `publish_results=true`. Head `08bcd6c` (contains Addendum 2026-07-19f).
- **Results tag:** `results-20260719-222137-phase1_kg_only-08bcd6c` verified on
  origin (points at `08bcd6c`).
- **CI artifact:** `phase1-consolidated`, id 8447910059,
  sha256 `a754bb6824c8cb885632ef986c6c7b22270e66bdd629730208623f50fc47e590`.
- **Guard:** `run_mode: "phase1_kg_only"` in all 10 per-cell `TRAINING_OK.json`.
- **Curation:** per-seed `qtable_*` / `metrics_*` / `bench_step_log*` pruned
  (same rule as the other phase1_postinv archives).

## Result (exploratory, n = 5)

lab2noise `auc_goal` Δ (ql_true − ql_false) = **+0.019540**
[+0.012738, +0.028776], p_boot < 10⁻⁴, δ = 1.0 — sign-consistent with the clean
anchor. `auc_reward` +11.96 [9.86, 14.06], δ = 1.0.

## ⚠️ Design finding — the ±10% noise is structurally sub-threshold

The pilot's stated purpose (δ deflation under noise) was **not achieved, for a
structural reason**: with light bounds [50, 100, 300] and lab2's achievable
ideal lux lattice {25, 75, 225, 425, 475, 625, 875}, **no value's ±10%
multiplicative band contains any rank bound** (nearest crossings need −29.4%
on 425 or ±33% on 75/225). The agent observes ranks, so the injected noise
never reaches its observation space, and this run is effectively a clean-lab2
replicate at n = 5 (hence δ = 1.0). **Do not cite this run as "the anchor
survives sensor noise."** A meaningful noise test requires ≥ ~30% multiplicative
noise, additive noise scaled to the bound gaps, or per-episode sun jitter that
crosses sunshine-rank bounds. Recorded in Addendum 2026-07-19f (Result note)
and audit Part E.10.
