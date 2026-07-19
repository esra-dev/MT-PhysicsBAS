# Action-Space Inversion — WoT-contract enumeration + stereotype enrichment

**Date:** 2026-07-10 (after the Phase 2.6 KG-silent monitor variants; before any
sweep that will be cited post-inversion).
**Status:** implemented, equivalence-audited, all local checks green. Every
result cited in the thesis from this point on must come from a post-inversion
run (see §6 runbook).

## 1. What changed and why

Before this change, the action space of BOTH learner arms was built by
`StereotypeReasoner`'s stereotype-based SPARQL discovery (a component needed a
behavioral stereotype whose mechanism has an Illuminance dependent variable),
with a Phase 2.6 fallback pass appending WoT-mapped but stereotype-silent
actuators. That was functionally correct but architecturally backwards: the
*capability* of the tabula-rasa agent nominally depended on the *knowledge*
layer, and the fallback made the true contract ("the TD defines the action
space") implicit.

The inversion makes the epistemic contract explicit and primary
([StereotypeReasoner.java](../src/env/tools/StereotypeReasoner.java),
`discoverActuators`):

1. **Pass 1 — capability layer** (`WOT_CONTRACT_ACTUATOR_QUERY`): the action
   space is enumerated from the WoT TD contract alone — every component with
   `ws:hasWoTActionSemanticType` + `elem:hasComponentAction`/`ws:actionValue`
   contributes one action per polarity, initially KG-SILENT (empty
   `affectedZones`, no IV binding, `kgSilent=true`). Canonical ordering is
   stereotype-free: `ORDER BY wotActionType, actionValue` (OFF before ON).
2. **Pass 2 — knowledge layer** (`ACTUATOR_DISCOVERY_QUERY`, unchanged SPARQL):
   now a pure *enrichment* pass. It annotates enumerated actions with physics
   knowledge — affected zones, Mediates IV binding + `ivMinRank`, energy cost —
   and clears `kgSilent`. It can no longer add or remove an action. A
   stereotype row without a WoT counterpart is logged and ignored (knowledge
   without capability is not actionable).

Everything downstream (Q-init priors, masking, fault detection, reachability
probe, cross-zone/power-gate discovery) consumes the same `ActionInfo` registry
and is unchanged.

**Thesis framing this buys:** *the Thing Description defines what both agents
can DO; the Knowledge Graph defines only what the KG-primed agent KNOWS about
doing it.* The tabula-rasa agent is now "without any previous knowledge" in the
exact RL sense — the action set is given (as it must be), the effects are not.

## 2. Equivalence audit (pre vs post)

`tools.ActionRegistryDump` snapshots every registered ontology set's registry
into a label-keyed golden CSV; `tools.RegistryGoldenCheck` compares live code
against goldens. The **contract** is the action-key set + per-action metadata
(label, state bit, zones, IV binding, energy cost, kgSilent). Action **indices
are explicitly NOT part of the contract** and are only reported.

One-time audit — new code checked against the pre-inversion snapshot
(`config/golden_registry/pre_inversion/`, full log in
`config/golden_registry/pre_vs_post_inversion_audit.txt`):

- **All 15 ontology sets: action sets and metadata bit-for-bit identical → CONTRACT HOLDS.**
- Index permutations in exactly 4 sets:
  - `custom` (6 moved: radiators now sort alphabetically instead of being appended),
  - `custom2` (28 moved: corridor light / spotlights / radiators interleave alphabetically),
  - `labmon2_infoonly`, `labmon2_nostereo` (6 moved each: the KG-silent monitors
    now sit at the SAME indices as in the fully-modeled parent labmon2 — the
    ordering caveat in PHASE2_6_KG_SILENT_MONITOR.md is obsolete).
- All Phase-1/2/3 ladder labs (lab1–lab5, lab2/3_slow, labmon, labmon2,
  labmon/labmon2 single-zone variants): **indices identical** too.

## 3. Label-keyed persistence (the correctness fix)

Q-table CSVs always carried action labels in their header, but every loader was
**positional** — an index permutation would have silently mis-mapped warm-loaded
values. All per-action persistence is now label-keyed on BOTH ends:

| Artifact | Save format | Load behaviour |
|---|---|---|
| `qtable_*_zoneN.csv` / combined | unchanged (labels already in header) | **remapped by header label**; unknown labels skipped with warning, uncovered actions stay at init |
| `*_visits.csv` sidecar | header now labels (was `a0,a1,…`) | remapped by label; **legacy positional file REFUSED** (ignored + prominent warning) |
| `*_trust.csv` sidecar | header `ActionLabel,SunBucket,Sum,N`, rows keyed by label (was index) | remapped by label; **legacy header `Action,…` REFUSED** |
| IV stats (`saveIVStats`) | v2: rows keyed by label (`# IV Stats v2` header) | v2 remapped by label; **legacy v1 positional file REFUSED** |

Refusal (not best-effort positional loading) is deliberate: positional data
cannot be trusted across a discovery-ordering change, and a silently mis-mapped
warm start is the worst failure mode. Consequence: **all pre-inversion trained
artifacts are retired** — re-train (they were going to be re-run anyway; see §6).

Verified by a round-trip smoke test: shuffled-column Q-table CSV loads
correctly by label; legacy visits/trust/IV-stats files are refused; labeled
sidecars and v2 IV stats round-trip identically.

## 4. Regression guard

- `gradlew verifyActionRegistry` — recomputes all 15 registries and checks them
  against `config/golden_registry/` (the post-inversion canonical goldens).
  Fails the build on any set/metadata difference; index permutations are
  informational. Now part of `gradlew preflight`, which CI already runs.
- `gradlew dumpActionRegistry` — regenerates the goldens. Run ONLY after an
  intended ontology/discovery change; review + commit the diff together with
  the change that caused it.
- `gradlew verifyActionRegistry -PregistryGolden=config/golden_registry/pre_inversion`
  — reproduces the one-time pre-vs-post audit.

## 5. Behavioural notes (what is NOT identical to pre-Phase-2.6)

- The JUnit suite (`gradlew test`, incl. `MonitorKgDiscoveryTest`,
  `Phase4KgDiscoveryTest`) passes unchanged — those tests locate actions by
  label and assert metadata, never positions.
- Relative to the ORIGINAL (pre-Phase-2.6) discovery, the `custom`/`custom2..9`
  legacy labs gained KG-silent actions (`SetZ*Radiator`, `SetCorridorLight`):
  the WoT mappings expose them, so they are now legitimately part of the action
  space as explorable no-ops/noise for the lighting task. This is the inversion
  semantics working as intended, but it does make those labs' RL problem
  slightly harder than in historical (pre-2.6) runs — one more reason the
  legacy custom results and the post-inversion results must not be mixed.
- RNG trajectories: even where indices are unchanged, treat EVERY
  pre-inversion metric as non-comparable to post-inversion metrics. Never mix
  them in one table.

## 6. Runbook — how to proceed from here

Order matters: **clean parent training and its faulty adaptation must both run
post-inversion** (a faulty cell must never warm-load a pre-inversion table; the
loader would refuse legacy sidecars and remap the Q-table, but the pairing
would still straddle two code states — scientifically unclean).

### 6.0 Preconditions (local, once — done in this change)
- `gradlew classes test validateTurtle verifyActionRegistry` all green.
- Pre-vs-post audit archived: `config/golden_registry/pre_vs_post_inversion_audit.txt`.
- Commit everything (code + goldens + audit + docs) as ONE commit so the
  inversion has a single citable SHA. All subsequent runs reference that SHA.

### 6.1 CI smoke (cheap, before any long sweep)
- Push the commit; `ci.yml` runs compile + `test` + `validateTurtle` +
  `preflight` (which now includes `verifyActionRegistry`).
- One pipeline smoke per phase locally or via dispatch with tiny budgets, e.g.:
  - `run_full_project.ps1 -OnlyProfiles lab1` with the dev run-mode, and
  - `run_phase2_adapt.ps1 -Smoke -AdaptProfiles lab2_f1dead -Modes ql_true`.
  Watch the logs for `mapHeaderToActions: … identity mapping` (fresh artifacts)
  and the absence of legacy-refusal SEVERE lines.

### 6.2 Phase 1 — clean-ladder re-run (anchor finding)
- GitHub Actions → **Phase 1** workflow (`phase1.yml`), defaults
  (`profiles=lab1,lab2,lab3`, `seeds=1..10`, `run_mode=phase1_kg_only`).
- ⚠️ **Correction (2026-07-18).** This step originally said `run_mode=phase1`.
  That profile has no `learning_overrides`, so it inherits the global
  `pbrs`+`adaptive_trust` stack and runs **factorial arm D**, not the arm-C
  headline (`phase1_kg_only`). Following the original wording produced run
  `29105464710` (archived at `phase1_postinv/`), which is arm-confounded and
  not a like-for-like §5.2 replacement — see `THESIS_STATE_REPORT.md`,
  Addendum 2026-07-13. `phase1.yml`'s default `run_mode` is now
  `phase1_kg_only`, so a defaults dispatch runs the correct arm.
- ✅ **Executed (2026-07-18).** The corrected defaults dispatch ran as
  **`29639767776`** (head `e631877`, 152/152 green, `run_mode` verified in all
  60 per-cell `TRAINING_OK.json`), archived at
  `phase1_postinv/run_29639767776/`, and is now the §5.2 headline of record —
  the lab2 anchor replicates like-for-like (Δ=+0.01679, q=0, δ=1.0). This
  closes §6.2. Arm-C adjudication of the arm-D deltas and the E-decay
  sensitivity sweep: `THESIS_STATE_REPORT.md` Addendum 2026-07-18b. (The
  registered seeds-11–20 extension later pooled this to the citable
  Δ=+0.01877, n=20 — Addendum 2026-07-19c.)
- This regenerates the headline learning-speed comparison (time-to-goal,
  redundant actions, success) on the post-inversion code and produces fresh
  labeled Q-table artifacts per seed.
- If lab4/lab5 results are cited: **Phase 4** workflow (`phase4.yml`) as well.

### 6.3 Phase 2 — fault/blacklist/re-learn re-run (registered families)
- GitHub Actions → **Phase 2** workflow (`phase2.yml`). It is self-contained
  (trains clean parents per seed, then adapts), so pairing is automatically
  post-inversion-consistent.
- Run 1 (registered §9 families): default 15-profile list, `seeds=1..10`.
- Run 2 (monitor cells): dispatch with
  `adapt_profiles=labmon_f1dead,labmon2_f2dead_lowsun,lab3_f2dead_lowsun`.
- Run 3 (Phase 2.6 KG-silent variants):
  `adapt_profiles=labmon_infoonly_f1dead,labmon_nostereo_f1dead,labmon2_infoonly_f2dead_lowsun,labmon2_nostereo_f2dead_lowsun`.
- Aggregate as usual (`analysis/phase2_recovery.py`, `--registered` mode for
  the frozen families) and compare the fresh confirmatory outcome against the
  §9 registration (see §6.5 documentation duties).

### 6.4 Phase 3 — dynamics re-run (if cited)
- GitHub Actions → **Phase 3** workflow (`phase3.yml`) for lab2_slow/lab3_slow.

### 6.5 Documentation / report adjustments
- **Pre-registration addendum (mandatory for defensibility):** add a
  "post-registration infrastructure change" section to the registered-analysis
  document: dated inversion commit SHA; statement that the change is
  registry-equivalence-audited (cite `pre_vs_post_inversion_audit.txt`: 15/15
  sets metadata-identical, 4 index-permuted, ladder labs index-identical);
  statement that all confirmatory numbers were re-generated post-inversion and
  whether each frozen §9 family's conclusion replicated. Do NOT edit the frozen
  §9 text itself.
- **Result tables:** every number in the thesis must state (footnote or methods
  section) that it comes from post-inversion runs; discard/clearly archive all
  pre-inversion CSVs (e.g. move `qtable_*/recovery_*/metrics_*` into an
  `archive/pre_inversion/` folder so they cannot be picked up by aggregation
  scripts).
- **Methods chapter:** describe discovery as two layers — action space =
  WoT TD contract; stereotype layer = knowledge overlay (priors, IV structure,
  predictions); KG-silent actions as the degenerate case. This replaces any
  older description of "stereotype-gated" action discovery.
- **Live docs to update** (historical `docs/_audit/*` snapshots stay frozen):
  - `docs/PHASE2_6_KG_SILENT_MONITOR.md` — updated with this change (fallback →
    enrichment wording; obsolete ordering caveat removed).
  - `docs/PHASE2_5_MONITOR_EMERGENCY.md`, `docs/PHASE2_5B_BEST_EFFORT_DEGRADATION.md`,
    `docs/PHASE1_TO_PHASE2_CHANGES.md`, `docs/PHASE2_TO_PHASE3_CHANGES.md`,
    `docs/phases_compilation.tex` — where they describe the "discovery gate" as
    stereotype-based, add a one-line pointer: "superseded by the action-space
    inversion, see ACTION_SPACE_INVERSION.md" rather than rewriting history.
  - `docs/_audit/THESIS_STATE_REPORT.md` — append a dated entry for the
    inversion (state reports are running logs; append, don't rewrite).
- **Tests to cite in the thesis' rigour section:** `gradlew test` (JUnit
  discovery/metadata tests), `gradlew verifyActionRegistry` (golden contract in
  CI), the archived equivalence audit, and the label-remap round-trip test.

### 6.6 Invalidation summary (what NOT to reuse)
| Artifact | Status |
|---|---|
| Pre-inversion `qtable_final_*.csv` | loadable via label remap, but retire anyway — pair-consistency across code states is not defensible |
| Pre-inversion `*_visits.csv`, `*_trust.csv`, IV-stats files | REFUSED by loaders (legacy positional) |
| Pre-inversion benchmark/recovery CSVs | keep archived for comparison, never mix into post-inversion tables |
| §9 registration text | frozen — addendum only |

## 7. Execution record (2026-07-12) — runbook §6.3 DONE, outcome changed

Commit chain (post history-rewrite SHAs): `6fffd41` + `8c386f8` (inversion) →
`a9530b9` (fault-flow generator sync with retuned lab3 physics) → `b1630b8`
(CI hardening: stale-CSV retirement, workspace scrub, cell-scoped artifact
globs) → `6c727b6` (runtime-classpath warm-up). Retired dispatches:
29107822998 (generator pattern failure), 29115969476 (aggregate contaminated
by stale committed CSVs).

Phase-2 campaign, all green on `6c727b6` (2026-07-11): 1A 29148475671,
1B 29151540231, Run 2 29155539633, Run 3 (Phase 2.6) 29157197853,
1C 29163456132 (`lab3_f1dead` seeds 11–20). 460/460 cells. Raw data:
`phase2_postinv/run_<id>/recovery_root/` (recovered from `phase2-consolidated`
artifacts after a Phase-4 `-OverwriteResultsBranch` publish wiped the
`results` branch). `_RUN_OF_RECORD` repointed wholesale; pooled output
`analysis/out_phase2_registered_postinv/`.

**Registered outcome (`pre_registration.md` §9.10):** recovery family 3/8
significant (`lab2_f1bdead`, `lab3_f2dead_lowsun`, `labmon2_f2dead_lowsun`),
1 marginal, 2 null, 2 sign-flipped ns (`labmon_f1dead`, `lab3_f1dead` —
the latter unsupported under the one-shot rule); detection family entirely
null. The pre-inversion 8/8 was thus partly action-space asymmetry — the
inversion did real scientific work. Phase 1 (29105464710) and Phase 3
(29166356524) post-inversion runs are green; their result extraction is the
remaining §6.2/§6.4 duty. *(Discharged: extraction 2026-07-13; the §6.2
arm-confound was then resolved by the arm-C re-run `29639767776` on
2026-07-18 — see the ✅ entry in §6.2 above. No §6 runbook duty remains open
for Phases 1–4.)*
