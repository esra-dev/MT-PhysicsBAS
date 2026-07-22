# Phase 1 corrective protocol-v2 campaign

This directory is the permanent data of record for the registered correction campaign.
All four workflows ran from commit `d3442385c91fbe11a5714bd15ca83add8f81f115`, using
labs `lab1,lab2,lab3`, seeds 1–20, exactly 3,000 training episodes per cell, and protocol
`phase1-v2`.

| Mode | GitHub run | Local archive |
|---|---:|---|
| Arm C / KG only | 29848584965 | `run_29848584965/` |
| Redundancy only | 29848587274 | `run_29848587274/` |
| Baseline label control | 29848589682 | `run_29848589682/` |
| PBRS-only label control | 29848592010 | `run_29848592010/` |

The registered five-test output is
`analysis/registered/phase1_v2_registered_family.csv`; the frozen decomposition is
`analysis/registered/phase1_v2_decomposition.json`. The original artifact inventories are
retained under each run at `analysis/out/SHA256SUMS.csv`. The campaign-level
`SHA256SUMS.csv` inventories every archive, analysis output, and manifest.

Reproduce all numeric tables from the committed raw data with:

```text
python analysis/reproduce_phase1_v2.py phase1_v2_corrected
```

The command validates all four archives, rebuilds every per-mode analysis table and the
registered family, canonicalizes numeric CSV text to 12 significant digits to eliminate
cross-platform floating-representation noise, and byte-compares the canonical output.
The seed-directory ordering and canonicalization execution corrections are disclosed in
`docs/phase1_correction_analysis_deviation_2026-07-22.md`.
