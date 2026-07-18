# Derived reanalysis — arm-C run `29639767776` restricted to seeds 1–5, lab2/lab3

**Not a CI run.** This directory holds the **E = 10000 point of the prior-decay
E-sensitivity sweep** (`THESIS_STATE_REPORT.md` Addendum 2026-07-18 item 4 /
2026-07-18b): the registered design reuses the arm-C run of record
`29639767776` (E = 10000) on the seeds 1–5 / lab2+lab3 subset so the sweep is
seed- and layout-matched to the two dispatched points
(`run_29641043465` E = 750, `run_29641899071` E = 3000).

**Derivation (2026-07-18, local):** copied
`phase1_postinv/run_29639767776/benchmark/results_seed{1..5}/{lab2,lab3}` into
a scratch tree and ran the identical CI aggregation command on it:

```
python analysis/sweep_report.py --root benchmark/results --out analysis/out \
    --seeds-mode --ci-bootstrap-iters 10000
```

(`analysis/sweep_report.py` at working-tree state of `05dd835`; deterministic
bootstrap RNG per pre-reg §2 — the recomputation is bit-reproducible from the
archived per-seed files.)

Resulting families match the sweep runs (n = 5; learning-speed m = 8,
benchmark m = 28) and **differ from the headline run's m = 12 / m = 42** — the
q-values here are only for within-sweep comparison, never for citation as the
headline result.

Key rows (Δ = ql_true − ql_false, `analysis/out/learning_speed_tests.csv` /
`paired_tests.csv`):

- lab2 `auc_goal` +0.02224 [0.00764, 0.03685], q = 0, δ = 1.0
- lab3 `auc_reward` +16.57 [11.97, 21.17], q = 0, δ = 1.0
- lab3 `mean_first_goal` +80.18 [44.30, 118.11], q = 0, δ = 0.92 (KG slower)
- lab3 `avg_cycling` +0.675 (q = 0.270, ns); `avg_redundant` +0.388 (q = 0.815, ns)
