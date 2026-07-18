# Phase 3 — post-inversion run of record

**Run ID:** `29166356524`
**Workflow:** `.github/workflows/phase3.yml` ("Phase 3 (process dynamics, response-delay learning)")
**Branch / head SHA:** `kg-crosszone-coupling-mid` / `6c727b699ee1fb39209f659b38cbf2b21f857863`
**Dispatched:** 2026-07-11 20:03:55Z
**Conclusion:** success — 42 / 42 jobs green
**Run URL:** https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/29166356524

## Dispatch inputs (workflow defaults)

| Input | Value |
|---|---|
| `dynamics_profiles` | `lab2_slow,lab3_slow` |
| `replicas` | `1..10` (Wilcoxon n ≥ 6 convention) |
| `probes` | `0` → config `phase3.probe.probes_per_actuator` (8) |

## Provenance of the archived files

- Source artifact: **`phase3-consolidated`** (artifact id `8252282750`,
  58,575 bytes,
  `sha256:cede3a0a17e6253c9bff9249de7498d09abcf542bb423f607701475348975df2`,
  GitHub expiry 2026-10-09). Downloaded and extracted 2026-07-18.
- ⚠️ Unlike Phases 1/2/4, this run has **no `results`-branch tag** — before this
  in-repo archive, the expiring CI artifact was the only off-disk copy. The
  artifact tree is archived here **in full** (no pruning; 123 files, ~360 KB).

```
analysis/out/    phase3_compliance_paired.csv, phase3_compliance_ci.csv,
                 phase3_delay_accuracy.csv  (the citable statistics)
dynamics_root/rep<1..10>/
                 dynamics_delays_{true,false}_{lab2_slow,lab3_slow}.csv
                 timebounded_results_{true,false}_{...}.csv
                 learned_dynamics_{true,false}_{...}.ttl
```

## Standing of this run

Interpreted in `THESIS_STATE_REPORT.md`, Addendum 2026-07-13: Phase 3
**replicates pre-inversion** — expected, since the dynamics agent never used the
stereotype-gated action discovery that the action-space inversion replaced. The
Phase-3 chapter (§7) conclusions can be cited as-is with the run ID updated to
`29166356524`.
