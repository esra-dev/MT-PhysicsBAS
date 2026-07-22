# Phase 1 protocol-v2 analysis execution deviation — 2026-07-22

Status: post-artifact-download operational correction; no statistical rule, outcome,
seed, arm, laboratory, metric, or data-bearing file changed.

After all four registered runs had completed successfully and their consolidated archives
had passed protocol and SHA-256 validation, the command frozen in
`analysis/phase1_v2_registered_family.py` stopped before calculating a registered statistic.
The reader received all declared seed directories but compared their lexicographic path
order (`1,10,...,2,...`) with numeric order (`1,2,...,20`). It therefore rejected the
complete seed set as though it were incomplete.

The correction sorts the already-discovered `(seed, path)` pairs by integer seed before
checking that the set is exactly 1–20. The same helper is used for learning-speed and
cycling inputs. A regression test supplies the observed lexicographic order and requires
numeric output. The five registered formulas, two-sided tests, `m=5` family, effect sizes,
confidence-interval method, decomposition thresholds, and archived inputs remain exactly
as registered.

Chronology:

1. Four aggregates completed successfully on registered commit
   `d3442385c91fbe11a5714bd15ca83add8f81f115`.
2. Four `phase1-consolidated` artifacts were downloaded and their protocol/archive gates
   passed.
3. The registered-family command failed at the seed-order guard, before it wrote its
   registered-family CSV or decomposition JSON.
4. This narrow ordering correction and its regression test were added before rerunning
   that command.

This deviation must remain visible with the correction registration and final result
report. It is not a new registration and does not restore blindness; the campaign was
already explicitly registered as sighted with respect to protocol-v1 results.

## Cross-platform byte-reproduction correction

After the registered table had been produced, the full reproduction command stopped on
the first archived-versus-rebuilt CSV. Inspection showed that the values differed only in
the final binary floating-point representation digits—for example `4.419999999999999`
versus `4.42`, and `0.9506250000000002` versus `0.9506249999999999`. These are below the
precision of any reported estimate and arose from Linux-versus-Windows aggregation, not
from different rows, seeds, or formulas.

The reproduction gate now converts every numeric CSV cell to a canonical 12-significant-
digit representation in memory and compares the resulting bytes. Integer and text fields,
headers, row order, row count, and all scientifically meaningful numeric digits must still
match exactly. Tests prove that representation-only noise is accepted and a genuine change
from `0.0037` to `0.0038` is rejected. Original downloaded files and their GitHub-produced
SHA-256 inventories remain untouched.
