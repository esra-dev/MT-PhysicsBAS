# Post-Phase-1b decision memo (2026-07-27)

Basis: the reproduced Phase-1b confirmatory results
(`docs/phase1b_results_2026-07-27.md`; archives `phase1b_corrected/`, all
gates green, tables byte-reproduced). This memo executes Stage 4 of the
Phase-1b plan: each gated candidate gets an explicit proceed / defer /
descope decision. No later campaign is auto-authorised; anything "proceed"
still receives its own freeze, certificates, pilot block, power analysis,
and registration.

## What Phase 1b established

1. **Relevance knowledge is real but negligible at these scales.** The
   frozen KG's advantage grows with decoy count (M1: +9.9e-6 auc/decoy,
   q=0.0065; 9 seeds positive and 11 exact ties, with every non-zero
   difference positive) and — decisively — its redundancy-only analogue is
   null (−2.4e-6, p≈0.46), so this is genuine knowledge-layer signal, not
   registry mimicry. But it is ~70× below the registered SESOI: at K=16 the
   total advantage is ~1.6e-4 auc against an anchor of 0.0111.
2. **State fragmentation is where knowledge pays most.** M3 (+0.0013,
   q=9.5e-6) is the largest confirmed effect, and redundancy reproduces only
   ~60% of it. Still ~8× below the SESOI.
3. **Dependency-order knowledge yields a reliable but tiny speed-up.** M6:
   −0.5 presentations RMST (q=1.9e-5), zero censoring, ~45% reproduced by
   redundancy alone, and 50× below the corrected −5%-of-H SESOI
   (H=500, SESOI=−25). No basis for a depth cliff.
4. **The newly implemented extended consumers changed nothing.** M2 and M4
   are identically zero in all 20 seeds. Exploratory M5 compares the full
   extended stack with baseline and therefore cannot be attributed to the
   direction channel; frozen and extended have identical mean band
   deviation, so the incremental direction-channel contrast is zero.

Thesis-level reading: qualitative stereotype knowledge produces
statistically clean but scientifically small accelerations; its structural
components (fragmentation, dependency) partially survive the ontology-free
control, its relevance component is genuine but negligible, and the two new
qualitative channels add nothing measurable on their registered members.

## Decisions

| Candidate | Decision | Reason |
|---|---|---|
| `labiv1/2/3` conditional-route ladder (+ energy-reward plumbing) | **DEFER** | Its question (state-conditional route choice) is adjacent to M6's confirmed-but-tiny structure effect; the energy plumbing is expensive; revisit only if a thesis chapter needs the conditional-route claim specifically. |
| `labmag` magnitude-oracle boundary | **DEFER** | The double null on the new qualitative channels (M2/M4) makes the qualitative/quantitative boundary the one *untested* channel with headroom — but the same nulls lower the prior that another prior-channel moves outcomes. Not descoped: it is the only remaining boundary claim. |
| `lab4chain4` depth-4 extension (Phase 4b) | **DESCOPE** | Corrected Phase-4 trend flat AND depth-3 effect confirmed tiny (−0.5 presentations). Nothing suggests a nonlinear cliff worth 256-state × 4-arm × N=20 cost. |
| `lab5r` energy-in-reward (Phase 4b) | **DEFER** | Independent, well-specified question; untouched by Phase-1b outcomes; sequenced behind thesis writing. |
| C1 Q-gap retrospective (Phase 2b) | **PROCEED** (descriptive only) | Cheap, uses existing archives, explicitly hypothesis-generating; freeze the Q-gap definition doc before running, per its spec. |
| C2 prospective recovery ordering (Phase 2b) | **DEFER** | Gated on C1's frozen retrospective ordering. |
| C3 exact wrong-KG dose ladder (Phase 2b) | **DESCOPE in current form** | Its primary estimand corrupts the direction metadata consumed by the extended channel — which Phase 1b just measured at exactly zero effect on its confirmatory members (M2/M4). Corrupting an outcome-inert channel cannot produce the registered crossover. Any revival must first redesign the consumer or target the frozen consumer's inputs. |

## Sequencing

Merge the Phase-1b package to `main` (PR from `phase1b-labs-2026-07`),
then C1 as the only immediately-proceeding item; thesis-chapter integration
of the Phase-1b results comes first. The backlog
(`docs/LAB_DESIGN_PROPOSALS_2026-07-24.md`) remains authoritative; nothing
here deletes a proposal.
