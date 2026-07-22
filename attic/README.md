# attic/ — fenced non-evidence files

Created 2026-07-19 (Phase-1 audit, to-do D8). Nothing in this directory is
run-of-record evidence. Do not cite anything below in the thesis or the state
report.

## local_outputs/ (untracked, gitignored)

Local, uncommitted working outputs swept from the repository root on
2026-07-19: smoke-test training metrics (e.g. 55-episode `metrics_*.csv`),
single-run bench logs, q-table/visit sidecars from local runs, OLD-era
coverage/first-goal CSVs, learned-TTL snapshots, PowerShell transcript logs.
They were never part of any archived run of record; every citable number lives
in the `phase1_postinv/` / `phase2_postinv/` / `phase3_postinv/` /
`phase4_postinv/` archives or the per-run download trees, each with a MANIFEST.
Local Gradle/Node-RED runs will regenerate files like these at the repo root;
sweep them back here if they accumulate.

## Why not delete?

The audit requires that nothing at the repo root can be mistaken for
run-of-record output. Moving rather than deleting preserves the ability to
inspect what the stale files contained (e.g. the 55-episode smoke metrics that
previously sat at the root and did not match any archived run).
