# Phase 1 — Plan B **pooled-20 reanalysis** (registered primary, Addendum 2026-07-18c §2)

**What this is:** the registered primary inference for the arm-C headline-family
seed extension — seeds 1–10 (run `29639767776`, head `e631877`) pooled with
seeds 11–20 (run `29692725784`, head `02ed6c1`), lab2 + lab3, `phase1_kg_only`
(arm C), recomputed locally 2026-07-19 with the §5.2 instrument. Reported in
**Addendum 2026-07-19c** of `THESIS_STATE_REPORT.md`.

## Inputs (per-seed sources; both sha256-verified against the GitHub artifact digests)

| Run | Seeds | CI artifact (`phase1-consolidated`) | sha256 | Expiry |
|---|---|---|---|---|
| `29639767776` | 1–10 | id `8428536694` (6,408,834 B) | `4029c69365f28741554cde915ae1eea5c51f9322199cc37b4ffaaacd6961d29f` | 2026-10-16 |
| `29692725784` | 11–20 | id `8444359131` (5,678,938 B) | `3bf6c4a8c993b22dd5b68bde66374cdda796d90e21d7e927d576807266acf0f5` | 2026-10-17 |

The CI artifacts are the per-seed sources because the committed run archives
prune per-seed training `metrics_stereotypes_*.csv` (needed for `auc_goal`).
Merged tree: `benchmark/results_seed{1..20}/{lab2,lab3}/**` — the two runs'
seed roots copied side by side, lab1 excluded per the registration.

## Instrument (identical to the §5.2 runs of record)

- `analysis/sweep_report.py`, unchanged since commit `7543d15` (2026-06-10);
  byte-identical at `e631877`, `02ed6c1`, and the analysis commit.
- Invocation (same flags as the CI aggregate step):
  `python analysis/sweep_report.py --root <merged>/benchmark/results --out … --seeds-mode --ci-bootstrap-iters 10000`
- Deterministic paired bootstrap (RNG seed `0xC1`, NumPy PCG64), Wilcoxon,
  Cliff's δ. Local environment: Python NumPy 2.4.4 / SciPy 1.17.1.
- **m = 3 BH post-step:** `analysis/pooled20_registered_family.py` extracts the
  three registered rows and re-applies `sweep_report._bh_qvalues` within the
  registered family only (guards: every row must have n_paired = 20, seeds
  exactly 1;…;20). Output: `pooled20_registered_family.csv`.

## Registered primary result (pooled n = 20, ql_true − ql_false, BH within m = 3)

| Registered cell | Δ (pooled 20) | 95% CI | p_boot | q (m = 3) | Cliff's δ | n = 10 record |
|---|---|---|---|---|---|---|
| lab2 `auc_goal` (anchor) | **+0.018773** | [0.013663, 0.024183] | 0 | **0** | 1.0 | +0.01679, q = 0 |
| lab3 `mean_first_goal` (timing tax) | **+53.302** | [26.545, 81.165] | 0 | **0** | 0.585 | +67.56, q = 0.0104 |
| lab3 `avg_cycling` (policy-quality tax) | **+0.7375** | [0.40625, 1.0375] | 0.0002 | **0.0002** | 0.77 | +0.744, q = 0.0154 |

All three registered contrasts are confirmed at pooled n = 20 with the original
signs. Per the pre-committed reporting rules these pooled estimates **supersede
the n = 10 citations** for these three contrasts (§5.2 note, §5.4, §10.3,
thesis). The registered secondary (seeds-11–20-only subset, from run
`29692725784`'s own `analysis/out/`) agrees in sign for all three cells, so
"replicates" is claimable for each. ⚠️ These m = 3 q-values are **not
comparable** to §5.2's m = 12 / m = 42 families, nor to the m = 8 / m = 28
families in `analysis_out/` here (which cover all lab2+lab3 cells and are
descriptive context only).

## Contents

```
MANIFEST.md                          this file
pooled20_registered_family.csv       the registered m = 3 result (table above)
analysis_out/                        full sweep_report output over the merged
                                     20-seed tree (m = 8 / m = 28 families,
                                     descriptive; learning curves lab2/lab3)
```

**No other cell, lab, or metric here acquires confirmatory status** (Addendum
2026-07-18c §2). Single-shot rule: seeds 11–20 was the one registered
extension; any further extension requires a fresh registration disclosing this
outcome first.
