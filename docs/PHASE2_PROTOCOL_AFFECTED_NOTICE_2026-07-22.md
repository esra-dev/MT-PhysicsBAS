# Phase 2 protocol-affected evidence notice (2026-07-22)

**Status: binding withdrawal notice, committed before the Phase 2 protocol-v2 rerun.**

The existing Phase 2 numerical results are historical, protocol-affected findings. They
must not be presented as thesis-final evidence. In particular, this notice withdraws the
current interpretation of the §9.10 post-inversion record (3 of 8 Tier-1 recovery cells
significant; detection family null), every per-cell recovery/detection value in
`docs/thesis_chapter_phase2.md` §5–§7, the Phase 2.6 KG-silent descriptives (run
29157197853), the Phase 2.7 multi-blind exploratory result (run 29187088096), and every
"zero false positives" / "detection recall 100%" claim.

The reasons are material, not cosmetic:

1. **Adaptation scenario scheduler.** The adaptation loop and the greedy goal-rate
   certification loop both requested integer scenario IDs from 1 through the scenario
   count (`illuminance_controller_agent_adapt.asl`, adaptation loop and
   `greedy_eval_loop`), although every faulty profile's scenario file uses non-contiguous
   IDs. At the runs of record, a missing ID silently invoked an unseeded random reset:
   approximately 27.3% of lab2-family, 30.0% of lab3/labmon2-family, and 16.7% of
   lab1/labmon-family adaptation episodes drew unseeded random start states, breaking
   per-seed pairing of the ql_true/ql_false contrast. (On current code the same requests
   hard-fail instead; the legacy runs cannot be innocently reproduced.)
2. **Pre-settle start-state recording.** The adaptation loop read the simulator state
   immediately after the scenario write and only then waited 250 ms, so recorded episode
   start states could be stale pre-settle values.
3. **Detector false positives on healthy components.** The no-response ("dead") verdict
   abstains only when a rank-masking co-feeder is already *fault-suspect*
   (`QLearner.observeForFaults`; `zoneHasSuspectCoFeeder`). A **healthy, active**
   co-feeder that holds a zone's discretised rank across the probed component's toggle
   (for example an open blind under strong sun holding a zone at rank 3 while a healthy
   lamp switches off) produces a false "dead" verdict and an instant blacklist of the
   healthy component, followed by a warm restart that wipes learned Q-columns. Verified
   against the committed runs of record (`SecondaryDetectEpisode >= 0` in single-fault
   cells; last row per cell):
   - lab3_f1dead 20/20, lab3_f1inv 10/10, lab3_f1dead_z2 10/10, lab3_f1inv_z2 10/10 —
     in **both** arms, a second (healthy) component was blacklisted in **every** replica.
   - lab2_f1bdead: 4/10 vanilla replicas (seeds 1, 5, 6, 7) vs **0/10** KG replicas —
     a treatment-correlated instrument artifact inside the strongest registered cell
     (Δ = −306.5), including one replica whose recorded **primary** defect is the healthy
     `SetZ2Light` rather than the injected dead blind.
   - lab2_f1binv 8/10 vanilla and 9/10 KG (one wrong primary in the KG arm);
     lab2_f1dead 0/10 vanilla vs 5/10 KG; lab2_f1inv 4/10 vs 6/10.
   - lab3_f2dead_lowsun (a genuine two-fault cell where a second detection is *correct*):
     the KG arm recorded the second genuinely dead lamp in only 5/10 replicas — missed
     detections in the other five.
   These events sit inside the primary metric: every spurious blacklist removes a healthy
   lever from the surviving action set and triggers a warm restart, so the recovery
   trajectories of the affected cells measured re-learning after losing a healthy
   component, asymmetrically between arms in lab2_f1bdead.
4. **Blacklist events are under-recorded.** The recovery CSV schema stores only the
   primary `DefectComponent` and the episode (not the identity) of any secondary
   blacklist, so the runs of record cannot even name which healthy component was removed.
   The corrected schema must record every blacklist event with component and episode.
5. **Structural detection blind spot (disclosed, retained).** The multi-zone Spotlight is
   never adjudicated by design (`QLearner.observeForFaults` multi-zone guard). A genuine
   Spotlight/co-feeder fault would be undetectable. This is a scope limit of the detector,
   not a defect being repaired; it must be stated wherever detection coverage is claimed.
6. **Warm-start training.** The clean parent Q-tables for the runs of record were trained
   under the Phase-1 protocol-v1 scheduler (silent random resets), so the adaptation
   starting points inherit the Phase-1 protocol defects.

The correction campaign is defined by the pre-data registration that will be committed on
this branch after protocol-v2 adaptation code (by-position scheduling, settled start-state
recording, detector v2 with a structural-maskability abstain, full blacklist-event
recording) and its tests are frozen, and before any corrected experiment is dispatched.
The corrected campaign uses seeds 1–20 and detector v2; its detection-family results are a
new instrument and are not comparable to the withdrawn detection record. Corrected results
replace the historical narrative regardless of whether they are favourable, adverse, or
null. Historical files, commits, tags, and run archives remain available for provenance
and are not being rewritten.

**Reading rule:** until a document is rewritten with protocol-v2 results, every Phase 2
number in it must be read as superseded/protocol-affected unless it is explicitly a code
or configuration constant rather than an empirical result.
