# Phase 2 structure-only campaign — dispatch record (2026-11-14)

Registration: `docs/phase2_structonly_registration_2026-11-14.md` (BINDING,
commit `d43dd41b`; implementation freeze `c4334b2a`).

## Pre-dispatch pipeline smoke (non-campaign cell)

One local smoke of `run_phase2_adapt.ps1 -Smoke -AdaptProfiles lab2_f1dead
-Modes ql_true -KnowledgeLayer brick -RunSeed 1` (200-episode budget, cold
start, not a member of any registered family) verified the treatment chain
end to end before dispatch: the orchestrator echoed the layer, the adapt JVM
logged `StereotypeReasoner: knowledge layer = BRICK`, and the ADAPT_OK
manifest recorded `knowledge_layer = brick`,
`knowledge_layer_delivered = brick`. Timeline, for the record: the smoke was
launched after the registration document was written; its output was first
sighted after the registration text was finalized, and no registered rule
was changed afterwards. The smoke's outcome is reported here once and
nowhere else: the cell completed (detect = episode 1 of the presentation
convention, reconverge = 61), and its first blacklist named the HEALTHY
`SetZ2Blinds` before the genuinely dead `SetZ1Light` — consistent with the
registered mechanism, on a cell outside every family, under a cold start
that no campaign cell uses. It carries no evidential weight for the
registered families.

## Registered dispatch

- Run ID **43590832041**, dispatched 2026-11-14 ~11:25 UTC+1 via
  `gh workflow run phase2.yml --ref phase2-structonly-2026-11`.
- Head `b5bf2146d5f45d0a73b1c2905d38d347ead555e0` (registration `d43dd41b`
  plus one mechanical Phase-1 claim-ledger rebuild for the registration
  addendum's own lines; CI run 43589459398 green on that head — the first
  CI run, 43587830789, failed only the stale-ledger gate, pre-data).
- Inputs, exactly as registered (§8):
  `adapt_profiles=lab2_f1bdead,lab3_f1bdead,lab3_f2dead_lowsun,labmon2_f2dead_lowsun`,
  `seeds=1,…,20`, `run_mode=phase1_v2_kg_only`, `adapt_episodes=0`,
  `knowledge_layer=brick`, `publish_results=true`.
- Expected matrix: 120 clean training cells (lab2, lab3, labmon2 × 2 stereo
  × 20 seeds) + 160 adaptation cells (4 cells × 2 arms × 20 seeds) + setup +
  aggregate = 282 jobs.
- Until the aggregate completes only operational status is inspected.
