# Phase 3 and Phase 4 protocol-v2 dispatch records (2026-07-22)

All dispatches were queued on 2026-07-22 (13:58 UTC) from branch
`phase234-correction-2026-07-22`, dispatch head `90e53f8b` (contains the
Phase-3 registration `8010e49f` and the Phase-4 registration `03bcc516`;
CI run `29924711758` was green on head `03bcc516` — the only commit between,
`90e53f8b`, touches claim-ledger tooling and no campaign code — before
dispatch).

## Phase 3 (registration §4: one dispatch)

| Dispatch | GitHub Actions run | inputs |
|---|---|---|
| P3 | `29926328852` | `dynamics_profiles=lab2_slow,lab3_slow` (default), `replicas=1..10` (default), `probes=0` (default), `publish_results=true` |

Dispatch note (disclosed): the dispatch command first attempted an input name
(`profiles`) that `phase3.yml` does not define and was rejected by the API
without queuing anything; the successful dispatch passed only
`publish_results=true`, taking the workflow's input defaults — which are
byte-identical to the registered inputs (`lab2_slow,lab3_slow`, replicas
1–10, probes 0).

## Phase 4 (registration §4: two dispatches)

| Dispatch | GitHub Actions run | inputs |
|---|---|---|
| P4-1 | `29926341581` | `profiles=lab4,lab4dual,lab4chain,lab5`, `seeds=1..10`, `run_mode=phase4_v2`, `publish_results=true` |
| P4-2 | `29926354783` | `profiles=lab4,lab4dual,lab4chain,lab5`, `seeds=11..20`, `run_mode=phase4_v2`, `publish_results=true` |

Until every aggregate completes, only operational status is inspected. Failed
cells/dispatches are preserved and documented; any re-dispatch uses
byte-identical inputs with both run IDs recorded here.
