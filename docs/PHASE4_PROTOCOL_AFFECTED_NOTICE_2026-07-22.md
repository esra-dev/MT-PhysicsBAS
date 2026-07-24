# Phase 4 protocol-affected evidence notice (2026-07-22)

**Status: binding withdrawal notice, committed before the Phase 4 protocol-v2 rerun.**

The existing Phase 4 numerical results are historical, protocol-affected findings. They
must not be presented as thesis-final evidence. In particular, this notice withdraws the
post-inversion ladder record (run `29193486193`, commit `d336fdf`, n=20 — `avg_redundant`
−0.33 / −0.93 / −1.46 across lab4 / lab4dual / lab4chain; lab5 `energy_compliance`
+0.096 with `mean_steady_power` −0.431), the pre-inversion record (run `27905392725`),
and every per-cell value in `docs/PHASE4.md` §10/§10a and
`docs/PHASE4_DEPENDENCY_LADDER.md` §10.

The reasons are material, not cosmetic:

1. **Training scheduler.** At the run-of-record commit the shared training loop
   requested contiguous scenario IDs 1..count against non-contiguous files
   (`train_scenarios_lab4/lab4dual/lab4chain/lab5.json` all miss IDs 3, 4, 8) and
   silently substituted unseeded random resets — approximately 30% of every cell's
   training episodes — while declared training scenarios 11, 13, and 16 were **never
   presented**. This is the same defect that invalidated Phase 1 protocol v1.
2. **Legacy benchmark schema.** The committed benchmark CSVs carry the legacy schema:
   `avg_energy` is the wall-clock `TotalEnergyCost` accumulator (withdrawn metric class)
   and `mean_first_goal` is the invalid legacy first-goal definition (pre-settle states,
   success-selected sets).
3. **Stacked run mode.** The `phase4` run mode layered PBRS and adaptive trust on the KG
   prior — the arm-D bundling whose attribution the Phase-1 correction showed to be
   unreliable. The corrected mode uses the arm-C convention (KG prior only) plus the
   lab5 energy prior, so corrected Phase-4 effects are attributable to the same
   treatment as corrected Phase 1.
4. **Deterministic-but-downstream steady power.** `phase4_energy.py` measures a
   deterministic steady-state power from the final actuator state and is not itself
   timing-confounded, but at the runs of record it scored policies trained under
   defect 1 — so its results are withdrawn with the rest.
5. **Policy-energy blind spot.** The deterministic per-decision `PolicyEnergyCost`
   metric recognised only lamp/spotlight substrings: lab5's efficient and inefficient
   lamps (`Z1Eff`/`Z1Ineff`) and the dependency actuators (`PlugZ1`, `MasterSwitch`)
   all cost 0, making the per-decision energy trace meaningless exactly where energy is
   the phase's subject. The corrected mode supplies ordered token weights
   (ineff 4, eff 1, spotlight 2, plugs/breaker/blinds 0, lamps 1) mirroring the KG's
   `ws:energyCost` declarations.

The correction campaign is defined by the pre-data registration committed on this branch
after the corrected mode (`phase4_v2`), weights, and tests are frozen and before any
corrected experiment is dispatched. Corrected results replace the historical narrative
regardless of whether they are favourable, adverse, or null. Historical files, commits,
tags, and run archives remain available for provenance and are not being rewritten.

**Reading rule:** until a document is rewritten with protocol-v2 results, every Phase 4
number in it must be read as superseded/protocol-affected unless it is explicitly a code
or configuration constant rather than an empirical result.
