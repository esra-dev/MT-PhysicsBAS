# Phase 1 protocol-v2 registration addendum 2026-07-21a

**Status: frozen before any protocol-v2 corrective campaign dispatch.**

[VERIFIED] The main corrective registration is
`docs/phase1_correction_registration_2026-07-21.md`, committed as `87ae528`. No
corrected Phase 1 workflow had been dispatched, and no corrected campaign data existed or
had been inspected, when this addendum was committed. The only protocol-v2 execution was
the explicitly non-inferential lab1 engineering smoke in CI run `29843626596`; CI run
`29845949046` was still executing the same non-inferential gate. Evidence: GitHub Actions
run chronology and the main registration, section 9.

## Operational defect found before dispatch

[VERIFIED] The registered plan requires all four workflows to be queued and retained.
The frozen workflow used one shared GitHub Actions concurrency group, `phase1`, with
`cancel-in-progress: false`. GitHub Actions retains at most one running and one pending
run in a concurrency group; adding another pending run replaces the older pending run.
Submitting all four registered workflows to the one group could therefore cancel two
campaigns before they ran. Evidence: `.github/workflows/phase1.yml` at commit `87ae528`,
lines 43-45; GitHub Actions concurrency semantics.

## Frozen correction

[VERIFIED] The concurrency key is changed to
`phase1-${{ github.event.inputs.run_mode || 'phase1_v2_kg_only' }}`. The four registered
modes therefore have four distinct queues, while a same-mode accidental duplicate remains
serialized and visible. `cancel-in-progress` remains false.

[VERIFIED] Both the training and benchmark matrices now set `max-parallel: 10`. With four
mode workflows, no more than 40 data-producing matrix jobs are intentionally requested at
once. Setup occurs before a mode's training matrix, and aggregation occurs after its
benchmark matrix, so those jobs do not add to the data-producing matrix maximum.

[VERIFIED] Nothing else changes. The four modes, labs, seeds, arm pairing, 3,000-episode
horizon, five-test family, statistical procedure, inspection embargo, failure rule,
archiving plan, and reporting commitments in the main registration remain frozen exactly
as written.

[VERIFIED] The registered-head CI gate must be green again on the commit containing this
addendum and the concurrency correction before any of the four Phase 1 workflows is
dispatched. The dispatched head recorded by all four runs must be that same commit.
