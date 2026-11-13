# Phase 1 corrective protocol-v2 campaign

This directory is the permanent data of record for the registered correction campaign.
The four campaign workflows ran from commit `d3442385c91fbe11a5714bd15ca83add8f81f115`, using
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

## Knowledge-ladder control arm (added 2026-11-13)

A fifth run adds the Brick-structure-only arm registered in
`docs/_audit/THESIS_STATE_REPORT.md`, Addendum 2026-11-10. It ran from commit
`140906f2b325aefdb32b6c00ffaae063507f215e` with the same labs, seeds, horizon, and protocol.

| Mode | GitHub run | Local archive |
|---|---:|---|
| Brick structure only | 42834963612 | `run_42834963612/` |

The registered two-test ladder output is
`analysis/registered/phase1_v2_knowledge_ladder_family.csv`, with its descriptive ladder in
`analysis/registered/phase1_v2_knowledge_ladder_descriptives.csv` and the category summary in
`analysis/registered/phase1_v2_knowledge_ladder.json`. The four-arm registered family and
decomposition above are unchanged by the fifth run. The campaign descriptor table
`analysis/phase1_v2_controls_and_descriptives.csv` keeps its 144 four-arm rows verbatim and
gains 36 rows for the Brick arm; `analysis/phase1_v2_protocol_gate_summary.json` gains the
fifth run. Treatment-delivery and cross-run comparability evidence is under
`run_42834963612/verification/`.

Reproduce all numeric tables from the committed raw data with:

```text
python analysis/reproduce_phase1_v2.py phase1_v2_corrected
```

The command validates all five archives, rebuilds every per-mode analysis table, the
registered family, and the ladder family, canonicalizes numeric CSV text to 12 significant
digits to eliminate cross-platform floating-representation noise, and byte-compares the
canonical output. The seed-directory ordering and canonicalization execution corrections are
disclosed in `docs/phase1_correction_analysis_deviation_2026-07-22.md`.
