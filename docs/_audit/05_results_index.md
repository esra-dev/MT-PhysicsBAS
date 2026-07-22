# 05 — Results Index: CI Runs → Artefacts

**Generated:** 2026-07-07 · **Delta-refreshed:** 2026-07-08 (Batches 1–5: Phase-2 §9
registration + pooled seed-paired re-analysis, Phase-1 provenance restoration + pbrs_only
re-dispatch, lab3 intermediate-bleed rerun)  
**Scope:** Map from GitHub Actions run IDs to local download folders, raw CSV files, analysis
scripts, and docs write-up sections for every phase of the NEW era (Phase 1–4). OLD-era
result files in the repo root are identified at the end.  
**Era note:** All content below is **[NEW]** (lab1/lab2/lab3/labmon/lab4/lab5 phase-based
approach, `phase1.yml`–`phase4.yml` workflows). OLD-era sweep results are flagged explicitly.

---

## 0. How to read this document

Each section lists:

| Column | Meaning |
|---|---|
| **CI workflow file** | `.github/workflows/<name>.yml` (verified present) |
| **Final run ID** | The GitHub Actions run the write-up section calls canonical |
| **Download folder** | Local directory where `gh run download -n <consolidated>` was extracted |
| **Raw CSV families** | Per-cell CSV files inside the download folder |
| **Consolidated CSVs** | Analysis-output CSVs in `<folder>/analysis/out/` |
| **Analysis script** | `analysis/<script>.py` that reads raw CSVs → consolidated CSVs |
| **Docs section** | `docs/<file>.md` section that contains the write-up |

Verification method: every path below was confirmed by `list_dir` on the local workspace.
Run IDs were cross-referenced against the docs files at the cited line numbers.

---

## 1. Phase 1 — KG Acceleration on Clean Labs

### 1.1 CI Workflow

**File:** [`.github/workflows/phase1.yml`](../../.github/workflows/phase1.yml)  
**Name (line 1):** `Phase 1 (KG acceleration, clean labs)`  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase1` (one run at a time, cancel-in-progress: false)
— [`.github/workflows/phase1.yml#L43-L45`](../../.github/workflows/phase1.yml#L43)

**Default parameters** (all verified at lines 22–42 of phase1.yml):

| Input | Default |
|---|---|
| `profiles` | `lab1,lab2,lab3` |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` |
| `run_mode` | `phase1` |
| `publish_results` | `true` |

### 1.2 Run Map — Headline + Controls (Phase 1 lab1/lab2/lab3)

These runs are documented in [`docs/phase1_results_n10.md`](../phase1_results_n10.md).
**UPDATE 2026-07-08 (Batch 2):** the consolidated artefacts were restored from CI into
[`phase1_headline_download/`](../../phase1_headline_download/) (sub-folders `kg_only/`,
`ib5/`, `baseline/`, `pbrs_only/`, each with `analysis/out/`), and the failed `pbrs_only`
control was re-dispatched and completed green as run **28929859927**. Every §§8–20+ headline
number is now value-verified against a local CSV row in
[`phase1_headline_download/PROVENANCE.md`](../../phase1_headline_download/PROVENANCE.md)
(68 values ✅; only the non-headline §§1–7 full-stack run 27305796237 remains without local
backing, `PROVENANCE.md#L217`, `#L225-L227`). The root-level `analysis/out/`,
`analysis/out_full/`, and `analysis/out_kg_only/` directories still contain local re-runs,
not the canonical CI data.

| Run ID | Mode | Commit | Status | Section | Local download folder |
|---|---|---|---|---|---|
| **27336756264** | `phase1_kg_only` (arm C vs arm A, KG isolated, PBRS off) | `55c0106` | **success** | `docs/phase1_results_n10.md` §8–§11 | [`phase1_headline_download/kg_only/`](../../phase1_headline_download/kg_only/) ✓ (restored 2026-07-08) |
| 27344626272 | `phase1_baseline` (arm A, negative control, all off) | `7ac37a1` | success | §16–§19 | [`phase1_headline_download/baseline/`](../../phase1_headline_download/baseline/) ✓ (restored 2026-07-08) |
| 27342571251 | `phase1_kg_only_ib5` (arm C, init_bonus 5) | `7ac37a1` | success | §13–§15 | [`phase1_headline_download/ib5/`](../../phase1_headline_download/ib5/) ✓ (restored 2026-07-08) |
| ~~27347962788~~ **28929859927** | `phase1_pbrs_only` (arm B control, PBRS on, KG off) | — | 27347962788 **FAILED**; re-dispatched 2026-07-08T08:47Z, completed 09:32Z **SUCCESS** | `PROVENANCE.md` §§20+ (all learning-speed and confirmatory contrasts null — negative control passes, closing the three-arm isolation argument) | [`phase1_headline_download/pbrs_only/`](../../phase1_headline_download/pbrs_only/) ✓ |

**Source citations:**
- Run 27336756264 status: [`docs/phase1_results_n10.md#L242`](../phase1_results_n10.md#L242)
  `"Run ID: 27336756264 · Status: Success — ~48 min · Commit: 55c0106"`
- Run 27344626272 status: [`docs/phase1_results_n10.md#L542`](../phase1_results_n10.md#L542)
  `"Run ID: 27344626272 · Status: Success — 49 m 3 s, 152 artifacts"`
- Run 27342571251 status: [`docs/phase1_results_n10.md#L402`](../phase1_results_n10.md#L402)
  `"Run ID: 27342571251 · Status: Success — 32 m 40 s, 102 artifacts"`
- Run 27347962788 FAILED: `paper_notes/ACTIONS_RUNS_20260616T133609Z.csv` row 94
  `"conclusion","failure"` — confirmed in `paper_notes/PHASE1_RESULTS.md` row at run
  27347962788: `"Failed run retained in AUDIT HISTORY only."`
- Re-dispatched pbrs_only run 28929859927 SUCCESS:
  [`phase1_headline_download/PROVENANCE.md#L161-L162`](../../phase1_headline_download/PROVENANCE.md)
  `"Run ID: 28929859927 · Dispatched: 2026-07-08T08:47:47Z · Completed: 2026-07-08T09:32:44Z ·
  Status: SUCCESS"`; per-value verification tables at `PROVENANCE.md#L169-L209`.

> **Discrepancy flag (updated 2026-07-08):** The task prompt lists `phase1_xzone_*` as the
> Phase 1 download folders for the above runs. This is **incorrect**: those folders belong
> to a separate cross-zone coupling investigation (see §1.3 below). The runs above
> originally had no local download folder; since 2026-07-08 they live under
> `phase1_headline_download/` (see the table), which is distinct from the `phase1_xzone_*`
> folders.

### 1.3 Run Map — Cross-Zone Coupling Investigation (same phase1.yml, separate branch)

These runs were dispatched on a feature branch to investigate and confirm the cross-zone
spillage coupling fix. They ARE stored in local download folders.

| Run ID | Run-mode / branch | Commit | Status | Download folder | Consolidated CSVs present? |
|---|---|---|---|---|---|
| 27440842780 | `phase1_kg_only`, branch `kg-crosszone-coupling` | `866297d` | success | [`phase1_xzone_asis/`](../../phase1_xzone_asis/) | **YES** — `analysis/out/` ✓ |
| 27461188614 | `phase1_kg_xzone_targeted`, branch `kg-crosszone-coupling-bump` | `8a98cd8` | success | [`phase1_xzone_bumped/`](../../phase1_xzone_bumped/) | **YES** — `analysis/out/` ✓ |
| 27462446044 | seeds 11–20 replication of 27461188614, same branch | `8a98cd8` | success | [`phase1_xzone_bumped_s11_20/`](../../phase1_xzone_bumped_s11_20/) | **YES** — `analysis/out/` ✓ |
| 27464846574 | `phase1_kg_xzone_rand` (ablation: untargeted cross-zone bonus), branch `kg-crosszone-ablation` | `e8d63e0` | success | [`phase1_xzone_ablation/`](../../phase1_xzone_ablation/) | **YES** — `analysis/out/` ✓ |
| **28941204656** | intermediate-magnitude rerun (13_logic_report.md §3 item 3(a)): lamp bleed 100 lux, blind bleed 0.30·sun, `cross_zone_bonus = 3.0` active — branch `kg-crosszone-coupling-mid` | `ad3cb3b` | success (2026-07-08) | [`phase1_xzone_mid/`](../../phase1_xzone_mid/) | **YES** — `analysis/out/` ✓ (`learning_speed_tests.csv`, `paired_tests.csv` verified locally identical to the CI aggregate) |

> **UPDATE 2026-07-08 (Batch 3):** run 28941204656 is the only xzone run against the new
> lab3 physics (commit `ad3cb3b` changed the spill magnitudes; the four earlier runs used
> 150 / 0.40·sun). Outcome: the KG arm **still regressed** on rank-moving metrics
> (`mean_first_goal` Δ = +23.95, q = 0.011; `avg_cycling` Δ = +0.575, q ≈ 0; `auc_goal`
> null) while `auc_reward` remained a robust win (+12.7, q ≈ 0) — the D1 decision is
> REFRAME (lead with `auc_reward`, disclose all three magnitude runs). Full analysis and
> presentation rule: [`docs/_audit/14_presentation_rules.md#L73-L93`](14_presentation_rules.md).

**Source citations:**
- Run 27440842780: [`docs/phase1_xzone_asis_analysis.md#L64`](../phase1_xzone_asis_analysis.md#L64)
  `"GH run 27440842780"`
- Run 27461188614: [`docs/phase1_xzone_bumped_analysis.md#L63`](../phase1_xzone_bumped_analysis.md#L63)
  `"GH run 27461188614"`
- Run 27462446044: [`docs/phase1_xzone_replication_s11_20_analysis.md#L70`](../phase1_xzone_replication_s11_20_analysis.md#L70)
  `"GH run 27462446044"`
- Run 27464846574: [`docs/phase1_xzone_ablation_analysis.md#L3`](../phase1_xzone_ablation_analysis.md#L3)
  `"run 27464846574"`
- Run 28941204656: [`docs/_audit/14_presentation_rules.md#L75-L76`](14_presentation_rules.md)
  `"GH run 28941204656, branch kg-crosszone-coupling-mid @ ad3cb3b"`; local folder
  `phase1_xzone_mid/analysis/out/` (`#L92-L93`)

**Consolidated CSV files verified in every `phase1_xzone_*/analysis/out/` folder:**

| File | Purpose |
|---|---|
| `summary_table_ci.csv` | Per-(profile, arm) means + bootstrap 95 % CIs |
| `summary_table.csv` | Raw means without CIs |
| `paired_tests.csv` | Paired bootstrap ql_true − ql_false per (profile, metric) + BH q-values |
| `paired_tests.tex` | LaTeX version of `paired_tests.csv` |
| `first_goal_table.csv` | Mean first-goal-episode per (profile, arm) |
| `first_goal_wilcoxon.csv` | Wilcoxon signed-rank on first-goal |
| `learning_speed_table.csv` | AUC-goal and related learning-speed means |
| `learning_speed_tests.csv` | Bootstrap tests on learning-speed metrics |
| `weakness_heatmap.csv` | Weakness-flag fire counts per (profile, weakness) |
| `weakness_heatmap.png` | Visual heatmap |
| `learning_curve_lab{1,2,3}.png` | Per-profile reward curves |

**Analysis script:** [`analysis/sweep_report.py`](../../analysis/sweep_report.py)  
Module docstring lines 1–18: "Aggregate `runFullSweep` artefacts into headline charts and
tables." Input: `benchmark/results/<profile>/<mode>/metrics_stereotypes_*.csv` + related
families. Output: `analysis/out/summary_table_ci.csv`, `paired_tests.csv`, etc.

**Docs write-up:**

| Folder | Docs file | Key section |
|---|---|---|
| `phase1_xzone_asis/` | [`docs/phase1_xzone_asis_analysis.md`](../phase1_xzone_asis_analysis.md) | as-is control (no bump) |
| `phase1_xzone_bumped/` | [`docs/phase1_xzone_bumped_analysis.md`](../phase1_xzone_bumped_analysis.md) | targeted cross-zone bonus |
| `phase1_xzone_bumped_s11_20/` | [`docs/phase1_xzone_replication_s11_20_analysis.md`](../phase1_xzone_replication_s11_20_analysis.md) | seeds 11–20 replication |
| `phase1_xzone_ablation/` | [`docs/phase1_xzone_ablation_analysis.md`](../phase1_xzone_ablation_analysis.md) | untargeted ablation |

**Raw per-profile CSV families** (inside each xzone download folder, at root level of
folder):

| Pattern | Description |
|---|---|
| `metrics_stereotypes_{true,false}_lab{1,2,3}.csv` | Per-episode training metrics (verified in `phase1_xzone_asis/`) |
| `iv_stats_stereotypes_{true,false}_lab{1,2,3}.json` | IV-effectiveness JSON (verified in `phase1_xzone_asis/`) |
| `qtable_final_stereotypes_*_lab{1,2,3}*.csv` | Final Q-tables by zone + global (verified in `phase1_xzone_asis/`) |
| `learned_stereotypes_{true,false}_lab{1,2,3}.ttl` | Learned stereotype TTL (verified in `phase1_xzone_asis/`) |
| `benchmark/` | Per-cell benchmark scenario results (subdirectory) |

---

## 2. Phase 2 (Fault Detection / Blacklist / Re-Learn) — Iteration History

### 2.1 CI Workflow

**File:** [`.github/workflows/phase2.yml`](../../.github/workflows/phase2.yml)  
**Name (line 1):** `Phase 2 (fault detection, blacklist, re-learn)`  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** `phase2`  
Source: [`.github/workflows/phase2.yml#L55`](../../.github/workflows/phase2.yml#L55)

**Default parameters** (verified at lines 32–52 of phase2.yml):

| Input | Default |
|---|---|
| `adapt_profiles` | 15 faulty profiles (see workflow file) |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` |
| `run_mode` | `phase1` |
| `adapt_episodes` | `0` (each profile's default) |
| `publish_results` | `true` |

### 2.2 Run Map — All Phase 2 Iterations

The Phase 2 results evolved through multiple iterations. The table below maps every
run to its download folder and the docs section that reports it.

> **UPDATE 2026-07-08 (Batch 1) — registration anchor:** Phase 2 is now governed by the
> frozen registration addendum [`docs/pre_registration.md` §9](../pre_registration.md)
> (commit `b9bf4cb`, written before the pooled re-analysis ran). §9.7 freezes **one run of
> record per cell** and seed-keyed pairing; runs v1–v5 (27470382799…27547019772) are
> registered as **superseded instruments — history/replication only, never confirmatory
> inputs** (§9.7 "Excluded from confirmatory analysis"). The `RoR` column below marks each
> run's §9.7 status.

| Run ID | Phase 2 iteration | Commit | Status | Download folder | Consolidated CSVs present? | RoR (§9.7) |
|---|---|---|---|---|---|---|
| 27470382799 | Phase 2 Run 1 — detection works; recovery 0 % (wrong instrument) | `8ff250d` | success | [`phase2_results/`](../../phase2_results/) | **YES** — `analysis/out/` ✓ | superseded (v1) |
| 27499405083 | Phase 2.1 — policy-stability recovery criterion; first measurable recovery | `f4ac3fe` | success | [`phase2_results_v2/`](../../phase2_results_v2/) | **YES** — `analysis/out/` ✓ | superseded (v2) |
| 27507087176 | Phase 2.2 — goal-rate certified recovery (`RecoveredGoalRate` added) | `aa74486` | success | [`phase2_results_v3/`](../../phase2_results_v3/) | **YES** — `analysis/out/` ✓ | superseded (v3) |
| 27529585379 | Phase 2 v4 — component-attribution fix (primary-detection-time bug) | NOT FOUND | success | [`phase2_results_v4/`](../../phase2_results_v4/) | **YES** — `analysis/out/` ✓ | superseded (v4) |
| 27547019772 | Phase 2 v5 — certified lamp-fault results (§19) — counter-based detection instrument | `985c7a1` | success | [`phase2_results_v5/`](../../phase2_results_v5/) | **YES** — `analysis/out/` ✓ | superseded (v5) |
| 28590019536 | Phase 2.3 — instant blacklist on first fault (9 lamp profiles) | `b2adca1` | success | [`phase2_results_v6/`](../../phase2_results_v6/) | **YES** — `analysis/out/` ✓ | **RoR for 7 cells** (`lab1_f1dead`, `lab2_f1dead/f1inv/f2dead/f2inv`, `lab3_f2dead/f2inv`); its `lab3_f1dead`/`f1inv` cells superseded by 28745352239 |
| 28745352239 | Phase 2.4 — extended blind/z2 fault family (8 cells incl. bdead/binv) | `282acc4` | failure (1 cell flaked) | [`phase2_ext_results/`](../../phase2_ext_results/) | **YES** — `analysis/out/` ✓ | **RoR for 6 cells** (`lab3_f1inv`, `lab3_f1dead_z2`, `lab3_f1inv_z2`, `lab3_f1bdead`, `lab3_f1binv`, `lab2_f1bdead`); its `lab2_f1binv` cell → backfill, its `lab3_f1dead` cell → 28913465680 (§9.9) |
| 28750100413 (backfill) | Phase 2.4 §21.9 — re-dispatch of lab2_f1binv flaked seed | — | success | [`phase2_binv_backfill/`](../../phase2_binv_backfill/) | **YES** — `phase2-consolidated/analysis/out/` ✓ | **RoR for `lab2_f1binv`** |
| 28863439179 | Phase 2.5 labmon — monitor-emergency-fallback lab | `eab51e2` | success | [`labmon_ci_results/`](../../labmon_ci_results/) | **YES** — `phase2-consolidated/analysis/out/` ✓ | **RoR for `labmon_f1dead`** |
| 28866807391 | Phase 2.5b — lab3_f2dead_lowsun multi-survivor degraded cell | — (branch `phase2-instant-blacklist`, dispatched 2026-07-07) | success | [`phase2_lowsun_results/run_28866807391/`](../../phase2_lowsun_results/run_28866807391/) (raw CSVs committed at `b9bf4cb`) | **YES** — `analysis/out/` ✓ | **RoR for `lab3_f2dead_lowsun`** |
| 28884717500 | Phase 2.5 labmon2 — spotlight-free dual-zone replication | — (branch `phase2-instant-blacklist`, dispatched 2026-07-07) | success | [`phase2_lowsun_results/run_28884717500/`](../../phase2_lowsun_results/run_28884717500/) (raw CSVs committed at `b9bf4cb`) | **YES** — `analysis/out/` ✓ | **RoR for `labmon2_f2dead_lowsun`** |
| **28913465680** | **§9.9 registered replication — `lab3_f1dead`, seeds 11–20 (registered pre-dispatch)** | **`b9bf4cb`** | **success** | [**`phase2_lab3f1dead_replication/run_28913465680/`**](../../phase2_lab3f1dead_replication/run_28913465680/) | **YES** — `analysis/out/` ✓ | **RoR for `lab3_f1dead`** (replaces 28745352239's cell per frozen §9.9 rule) |

**Source citations (run IDs):**
- 27470382799: `paper_notes/RUN_LEDGER.csv` row 8
- 27499405083: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L411`](../PHASE1_TO_PHASE2_CHANGES.md#L411)
  `"Run: GitHub Actions phase2.yml #27499405083"`
- 27507087176: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L765`](../PHASE1_TO_PHASE2_CHANGES.md#L765)
  `"Run: GitHub Actions phase2.yml #27507087176"`
- 27529585379: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L999`](../PHASE1_TO_PHASE2_CHANGES.md#L999)
  `"## 17 Run #27529585379 ("v4")"`
- 27547019772: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L1331`](../PHASE1_TO_PHASE2_CHANGES.md#L1331)
  `"## 19 Run #27547019772 ("v5") — final certified results & Phase-2 sign-off"`
- 28590019536: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L1718`](../PHASE1_TO_PHASE2_CHANGES.md#L1718)
  `"### 20.6 Confirmatory CI results (run 28590019536)"`
- 28745352239: [`docs/PHASE1_TO_PHASE2_CHANGES.md#L1968`](../PHASE1_TO_PHASE2_CHANGES.md#L1968)
  `"### 21.7 Confirmatory CI results (run 28745352239)"`
- 28863439179: [`docs/_audit/00_inventory.md#L622`](_audit/../00_inventory.md#L622)
  `"eab51e2 — labmon: confirmatory run 28863439179 results"`;
  [`docs/PHASE2_5B_BEST_EFFORT_DEGRADATION.md#L281`](../PHASE2_5B_BEST_EFFORT_DEGRADATION.md#L281)
- 28866807391: [`docs/PHASE2_5B_LAB3_RESULTS.md#L3`](../PHASE2_5B_LAB3_RESULTS.md)
  `"CI run 28866807391 · conclusion success · dispatched 2026-07-07"`
- 28884717500: [`docs/PHASE2_5_LABMON2_RESULTS.md#L3`](../PHASE2_5_LABMON2_RESULTS.md)
  `"CI run 28884717500 · conclusion success · dispatched 2026-07-07"`
- 28913465680: [`docs/phase2_registered_reanalysis_delta.md#L94-L98`](../phase2_registered_reanalysis_delta.md)
  `"run 28913465680, commit b9bf4cb = the §9.9 registration commit, seeds 11–20, conclusion
  success"`; registration frozen pre-dispatch in
  [`docs/pre_registration.md` §9.9](../pre_registration.md)
- Run-of-record table: [`docs/pre_registration.md` §9.7](../pre_registration.md)
  ("Run of record per cell" table + "Excluded from confirmatory analysis" list)

> **Discrepancy flag — Phase 2.1 "final" run (updated 2026-07-08):** The task prompt names
> run **27499405083** as the "final" Phase 2.1 run and specifies
> `docs/PHASE1_TO_PHASE2_CHANGES.md §12` as the write-up. That is accurate for Phase 2.1
> (the first measurable recovery run), but this run is **not** the final Phase 2 result —
> and as of the §9 registration, neither is run 27547019772 ("v5"), whose counter-based
> detection instrument is superseded (§9.7). The confirmatory Phase-2 result is now the
> **pooled `--registered` analysis over the §9.7 runs of record** (28590019536, 28745352239,
> 28750100413, 28863439179, 28866807391, 28884717500, 28913465680), reported in
> [`docs/phase2_registered_reanalysis_delta.md`](../phase2_registered_reanalysis_delta.md)
> — see §2.4 below.

### 2.3 Content of the Phase 2.1 Canonical Download Folder (run 27499405083)

**Folder:** [`phase2_results_v2/`](../../phase2_results_v2/)

Sub-structure verified:

```
phase2_results_v2/
├── analysis/
│   └── out/
│       ├── phase2_recovery_ci.csv       ← per-(profile, arm) mean + bootstrap 95 % CI
│       └── phase2_recovery_paired.csv   ← per-(profile, metric) ql_true − ql_false + BH q
└── recovery_root/
    └── seed{1..10}/                     ← per-seed raw recovery CSVs
        └── recovery_stereotypes_{true,false}_<profile>.csv
```

**Raw per-cell CSV family** (under `recovery_root/seed<N>/`):

| File pattern | Description |
|---|---|
| `recovery_stereotypes_{true,false}_<profile>.csv` | One row per run: `DefectComponent`, `DetectEpisode`, `ReconvergeEpisode`, `RecoveryEpisodes`, `SecondaryDetectEpisode`, `RecoveredGoalRate` |
| `metrics_adapted_stereotypes_*.csv` | Per-episode adaptation training metrics |

**Consolidated CSVs** (in `phase2_results_v2/analysis/out/`):

| File | Description |
|---|---|
| `phase2_recovery_ci.csv` | Per-(profile, arm): mean detect/recover episodes + 95 % bootstrap CI |
| `phase2_recovery_paired.csv` | Per-(profile, metric): ql_true − ql_false paired bootstrap + BH q-values |

**Analysis script:** [`analysis/phase2_recovery.py`](../../analysis/phase2_recovery.py)
— **rewritten 2026-07-08 (commit `b9bf4cb`)**. Module docstring lines 1–55: discovers
`recovery_stereotypes_*.csv` files, treats each per-seed CSV as one replica **keyed by the
`seed<N>` token in its path** ("pairing is by seed key, never by list position",
`analysis/phase2_recovery.py#L30-L32`), emits a **`seeds_paired`** column per contrast
(`#L36`, `#L549`), and applies BH only over the **frozen §9.5/§9.6 families**
(`#L40-L44`). Partial (single-CI-run) invocations emit `q = nan` with a notice and carry
no confirmatory claim (`#L43-L44`, `#L564-L569`). Outputs `phase2_recovery_ci.csv` and
`phase2_recovery_paired.csv`.  
Single-run invocation: `python analysis/phase2_recovery.py --root . --out analysis/out`  
Registered pooled invocation: `python analysis/phase2_recovery.py --registered --out
analysis/out_phase2_registered` (`#L53-L54`) — resolves each cell to its §9.7 run of
record via the in-script `_RUN_OF_RECORD` map (`#L182-L210`).

**Docs write-up:** [`docs/PHASE1_TO_PHASE2_CHANGES.md`](../PHASE1_TO_PHASE2_CHANGES.md)  
**Section §12** (`## 12.1` through `## 12.11`) — lines 416–537.  
Key anchor: line 411 confirms run ID 27499405083.

### 2.4 Registered Pooled Re-Analysis (§9) — the confirmatory Phase-2 result (added 2026-07-08)

**Registration:** [`docs/pre_registration.md` §9](../pre_registration.md) (commit
`b9bf4cb`, frozen **before** the pooled re-analysis ran): hypothesis H-P2 (§9.2), metric
definitions (§9.3), tier rules (§9.4), **ONE pooled Tier-1 recovery BH family, m = 8 by
enumeration** (§9.5), **detection family m = 8** with the 10 degenerate
`DetectEpisode ≡ 0` cells excluded (§9.6), one run of record per cell + seed-keyed pairing
(§9.7), protocol (§9.8), and the pre-dispatch `lab3_f1dead` replication (§9.9).

**Outputs (local, committed):**
[`analysis/out_phase2_registered/`](../../analysis/out_phase2_registered/) —
`phase2_recovery_ci.csv` (per-(profile, arm) means + bootstrap CIs) and
`phase2_recovery_paired.csv` (per-(profile, metric) seed-paired diffs with `seeds_paired`,
`n_paired`, and frozen-family BH q-values).

**Delta vs the published per-run numbers:**
[`docs/phase2_registered_reanalysis_delta.md`](../phase2_registered_reanalysis_delta.md) —
the seed-pairing fix + frozen family moved exactly one cell across 0.05:
`lab3_f1dead` q = 0.028 (positional, ext) → **q = 0.053** (seed-paired, m = 8), driven by
the ext run's misaligned pairs (ql_true seed 3 missing; delta note §4). All other 7 Tier-1
cells kept q ≤ 0.006; the detection family kept the same significance side everywhere
(delta note §2–§3).

**§9.9 replication outcome (run 28913465680, seeds 11–20):** `lab3_f1dead` **CONFIRMED** —
Δ = −121.1 episodes (149.4 vs 270.5), 95 % CI [−201.6, −51.8], p_wil = 0.0137, δ = −0.72,
q = 0.00027 (delta note §6). **Final registered Phase-2 result: all 8 Tier-1 cells
significant** (max q = 0.0012, `lab3_f1bdead`), every Δ negative, δ from −0.47 to −0.92;
detection family: `lab3_f1inv` remains the one significant contrast (KG *slower* to detect,
q = 0.0048). No further Phase-2 reruns are permitted under §9.9.

---

## 3. Phase 3 — Process Dynamics / Response-Delay Learning

### 3.1 CI Workflow

**File:** [`.github/workflows/phase3.yml`](../../.github/workflows/phase3.yml)  
**Name (line 1):** `Phase 3 (process dynamics, response-delay learning)`  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** NOT FOUND in phase3.yml (no explicit concurrency block)

**Default parameters** (verified at lines 41–62 of phase3.yml):

| Input | Default |
|---|---|
| `dynamics_profiles` | `lab2_slow,lab3_slow` |
| `replicas` | `1,2,3,4,5,6,7,8,9,10` (bumped from 5 per §19 n≥6 requirement) |
| `probes` | `0` (use config `phase3.probe.probes_per_actuator = 8`) |
| `publish_results` | `true` |

### 3.2 Run Map

| Run ID | Design | Commit | Status | Download folder | Consolidated CSVs present? |
|---|---|---|---|---|---|
| 27598417789 | Preliminary n=5 (8 probes) | — | success | [`phase3_download/`](../../phase3_download/) | YES — `phase3-consolidated/analysis/out/` ✓ |
| **27621106006** | **Confirmatory n=10, 8 probes (§19.4)** | — | **success** | [**`phase3_download_n10/`**](../../phase3_download_n10/) | **YES — `phase3-consolidated/analysis/out/` ✓** |

**Source citations:**
- Run 27598417789: [`docs/PHASE2_TO_PHASE3_CHANGES.md#L542`](../PHASE2_TO_PHASE3_CHANGES.md#L542)
  `"## 16. Results — full CI sweep (run 27598417789, n = 5 replicas, 8 probes)"`
- Run 27621106006: [`docs/PHASE2_TO_PHASE3_CHANGES.md#L668`](../PHASE2_TO_PHASE3_CHANGES.md#L668)
  `"### 19.4 Confirmatory run results (run 27621106006, n = 10 replicas, 8 probes)"`
  and [`docs/PHASE2_TO_PHASE3_CHANGES.md#L601`](../PHASE2_TO_PHASE3_CHANGES.md#L601)

### 3.3 Content of the Canonical Download Folder (run 27621106006)

**Folder:** [`phase3_download_n10/`](../../phase3_download_n10/)

Sub-structure verified:

```
phase3_download_n10/
├── build-classes/
├── dynamics-lab2_slow-ql_{true,false}-rep-{1..10}/   ← 20 per-replica artefact sets
├── dynamics-lab3_slow-ql_{true,false}-rep-{1..10}/   ← 20 per-replica artefact sets
└── phase3-consolidated/
    ├── analysis/
    │   └── out/
    │       ├── phase3_delay_accuracy.csv
    │       ├── phase3_compliance_ci.csv
    │       └── phase3_compliance_paired.csv
    └── dynamics_root/
```

**Raw per-cell artefacts** (under `dynamics-<profile>-<mode>-rep-<N>/`):

| File pattern | Description |
|---|---|
| `dynamics_delays_{true,false}_<profile>.csv` | Learned per-actuator delay: `action_label`, `delay_ticks`, `delay_seconds`, `response_class` |
| `timebounded_results_{true,false}_<profile>.csv` | Per goal: `goal_id`, `deadline_sec`, `believed_delay_sec`, `learned_delay_sec`, `actual_delay_sec`, `energy_cost`, `met` |
| `learned_dynamics_{true,false}_<profile>.ttl` | KG with learned `ws:responseDelay` written back |

**Root-level equivalents** also present in workspace root (local single-run copies):
`dynamics_delays_{true,false}_lab{2,3}_slow.csv`,
`timebounded_results_{true,false}_lab{2,3}_slow.csv`,
`learned_dynamics_{true,false}_lab{2,3}_slow.ttl`

**Consolidated CSVs** (in `phase3_download_n10/phase3-consolidated/analysis/out/`):

| File | Description |
|---|---|
| `phase3_delay_accuracy.csv` | Per-(profile, arm): learned delay vs ground truth; relative error |
| `phase3_compliance_ci.csv` | Per-(profile, arm): overall/tight/loose compliance mean + 95 % CI |
| `phase3_compliance_paired.csv` | Per-(profile, metric): ql_true − ql_false + BH q-values + Wilcoxon + Cliff's δ |

**Analysis script:** [`analysis/phase3_dynamics.py`](../../analysis/phase3_dynamics.py)  
Module docstring lines 1–55: discovers `dynamics_delays_*.csv` and
`timebounded_results_*.csv`, computes delay accuracy and compliance statistics.  
Default invocation: `python analysis/phase3_dynamics.py --root . --out analysis/out`

**Docs write-up:** [`docs/PHASE2_TO_PHASE3_CHANGES.md`](../PHASE2_TO_PHASE3_CHANGES.md)  
Key sections:

| Section | Content |
|---|---|
| §16 (line 542) | n=5 preliminary results (run 27598417789) |
| §17 (line 607) | Interpretation of §16 |
| §18 (line 617) | Threats to validity |
| **§19 (line 619)** | **Confirmatory n≥6 design + §19.4 (line 668) = n=10 results for run 27621106006** |

**Download paths** referenced in docs:
- n=5: `phase3_download/phase3-consolidated/analysis/out/`
  — [`docs/PHASE2_TO_PHASE3_CHANGES.md#L395`](../PHASE2_TO_PHASE3_CHANGES.md#L395)
- n=10 (canonical): `phase3_download_n10/phase3-consolidated/analysis/out/`
  — [`docs/PHASE2_TO_PHASE3_CHANGES.md#L666`](../PHASE2_TO_PHASE3_CHANGES.md#L666)

---

## 4. Phase 4 — Dependencies, Energy-Aware Goals, KG vs LLM

### 4.1 CI Workflow

**File:** [`.github/workflows/phase4.yml`](../../.github/workflows/phase4.yml)  
**Name (line 1):** `Phase 4 (Dependencies + Energy, KG vs LLM framing)`  
**Trigger:** `workflow_dispatch` only  
**Concurrency group:** NOT FOUND in phase4.yml (no explicit concurrency block)

**Default parameters** (verified at lines 44–62 of phase4.yml):

| Input | Default |
|---|---|
| `profiles` | `lab4,lab5` |
| `seeds` | `1,2,3,4,5,6,7,8,9,10` |
| `run_mode` | `phase4` |
| `run_llm_baseline` | `true` |
| `publish_results` | `true` |

### 4.2 Run Map

| Run ID | Design | Status | Download folder | Consolidated CSVs present? |
|---|---|---|---|---|
| (smoke) | Phase 4 smoke | — | [`phase4_smoke_download/`](../../phase4_smoke_download/) | PRESENT (not primary) |
| 27903687624 | Confirmatory n=10 (first pass; `energy_compliance` bootstrap-sig but Wilcoxon 0.086) | success | [`phase4_confirm_download/`](../../phase4_confirm_download/) | **YES — `phase4-consolidated/analysis/out/` ✓** |
| **27905392725** | **Confirmatory n=20 (§10a — all pre-registered thresholds met, including Wilcoxon p=0.00093)** | **success** | [**`phase4_n20_download/`**](../../phase4_n20_download/) | **YES — `phase4-consolidated/analysis/out/` ✓** |

**Source citations:**
- Run 27903687624: `/memories/repo/phase4-n10-confirmatory-results.md` (repo memory);
  [`docs/PHASE4.md#L293`](../PHASE4.md#L293)
  `"The n = 10 dispatch (27903687624) reproduces the same directions"`
- Run 27905392725: [`docs/PHASE4.md#L255`](../PHASE4.md#L255)
  `"## 10a. Certified results (n = 20, run 27905392725)"`;
  [`docs/PHASE4.md#L293`](../PHASE4.md#L293) lists it as the source artefact run

### 4.3 Content of the Canonical Download Folder (run 27905392725)

**Folder:** [`phase4_n20_download/`](../../phase4_n20_download/)

Sub-structure verified:

```
phase4_n20_download/
├── build-classes/
├── bench-lab4-ql_{false,true,rule_based}-seed-{1..20}/   ← 60 benchmark artefact sets
├── bench-lab5-ql_{false,true,rule_based}-seed-{1..20}/   ← 60 benchmark artefact sets
├── train-lab4-stereo-{false,true}-seed-{1..20}/          ← 40 training artefact sets
├── train-lab5-stereo-{false,true}-seed-{1..20}/          ← 40 training artefact sets
└── phase4-consolidated/
    ├── analysis/
    │   └── out/
    │       ├── summary_table_ci.csv          ← sweep_report output
    │       ├── summary_table.csv
    │       ├── paired_tests.csv
    │       ├── paired_tests.tex
    │       ├── first_goal_table.csv
    │       ├── first_goal_wilcoxon.csv
    │       ├── learning_speed_table.csv
    │       ├── learning_speed_tests.csv
    │       ├── weakness_heatmap.csv / .png
    │       ├── learning_curve_lab4.png
    │       ├── learning_curve_lab5.png
    │       ├── phase4_energy_ci.csv          ← phase4_energy.py output
    │       ├── phase4_energy_paired.csv
    │       ├── phase4_llm_summary.csv        ← phase4_llm_baseline.py output
    │       ├── phase4_llm_detail_lab4.csv
    │       ├── phase4_llm_detail_lab5.csv
    │       ├── phase4_llm_prompts_lab4.jsonl
    │       └── phase4_llm_prompts_lab5.jsonl
    ├── benchmark/
    ├── metrics_stereotypes_{true,false}_lab{4,5}.csv     ← training metrics
    ├── iv_stats_stereotypes_{true,false}_lab{4,5}.json
    ├── learned_stereotypes_{true,false}_lab{4,5}.ttl
    └── qtable_final_stereotypes_{true,false}_lab{4,5}*.csv
```

**Raw per-cell CSV families** (inside `bench-*/` and `train-*/` per-seed directories, and in
`phase4-consolidated/` root):

| File pattern | Description |
|---|---|
| `metrics_stereotypes_{true,false}_lab{4,5}.csv` | Per-episode training metrics (verified in consolidated root) |
| `benchmark_results_{ql_false,ql_true,rule_based}.csv` (inside `bench-*/`) | Per-scenario benchmark results (seed-level) |
| `bench_step_log_{mode}.csv` (inside `bench-*/`) | Per-step benchmark log for energy scoring |
| `iv_stats_stereotypes_*.json` | IV-effectiveness JSON |
| `learned_stereotypes_*.ttl` | Learned stereotype TTL |
| `qtable_final_stereotypes_*_lab{4,5}*.csv` | Final Q-tables per zone + global |

**Consolidated CSVs** (in `phase4_n20_download/phase4-consolidated/analysis/out/`):

| File | Producing script | Description |
|---|---|---|
| `summary_table_ci.csv` | `sweep_report.py` | Per-(profile, mode) training-metric means + bootstrap 95 % CIs |
| `paired_tests.csv` | `sweep_report.py` | Paired bootstrap ql_true − ql_false per (profile, metric) + BH q |
| `first_goal_table.csv` / `first_goal_wilcoxon.csv` | `sweep_report.py` | First-goal-episode learning speed |
| `phase4_energy_ci.csv` | `phase4_energy.py` | Per-(profile, mode) energy-compliance mean + 95 % CI |
| `phase4_energy_paired.csv` | `phase4_energy.py` | Paired ql_true − ql_false on energy metrics + BH q |
| `phase4_llm_summary.csv` | `phase4_llm_baseline.py` | KG-QL vs LLM: goal_rate, compliance, steady_power per lab |
| `phase4_llm_detail_lab{4,5}.csv` | `phase4_llm_baseline.py` | Per-scenario LLM action trace |
| `phase4_llm_prompts_lab{4,5}.jsonl` | `phase4_llm_baseline.py` | Offline LLM prompt/response log |

**Analysis scripts:**

| Script | Purpose | Key invocation |
|---|---|---|
| [`analysis/sweep_report.py`](../../analysis/sweep_report.py) | Learning-speed and goal-rate tables (reused from Phase 1) | `python analysis/sweep_report.py --root benchmark --out analysis/out` |
| [`analysis/phase4_energy.py`](../../analysis/phase4_energy.py) | Energy-budget compliance — lab5 pre-registered primary metric | `python analysis/phase4_energy.py --root benchmark --out analysis/out` |
| [`analysis/phase4_llm_baseline.py`](../../analysis/phase4_llm_baseline.py) | Offline LLM baseline for KG-vs-LLM comparison | invoked by `phase4.yml` aggregate job with `run_llm_baseline=true` |

Script invocation confirmed in workflow comment:
[`docs/PHASE4.md#L145-L169`](../PHASE4.md#L145) — §5 lists all three scripts and their
respective output files.

**Docs write-up:** [`docs/PHASE4.md`](../PHASE4.md)  
Key sections:

| Section | Line | Content |
|---|---|---|
| §5.1 (line 147) | `phase4_energy.py` — energy-budget compliance |
| §5.2 (line 158) | `phase4_llm_baseline.py` — offline LLM baseline |
| §7 (line 200) | Phase-4 workflow structure |
| §10 (line 235) | Expected results |
| **§10a (line 255)** | **Certified n=20 results (run 27905392725) — PRIMARY REFERENCE** |

Source artefact statement in docs: [`docs/PHASE4.md#L293`](../PHASE4.md#L293)
`"Source artefacts: analysis/out/phase4_energy_paired.csv, phase4_energy_ci.csv,
paired_tests.csv, phase4_llm_summary.csv in the phase4-consolidated artifact of run
27905392725 (also published to the results branch)."`

**Note — n=10 download folder also contains consolidated CSVs:**  
`phase4_confirm_download/phase4-consolidated/analysis/out/` contains the same file list
as the n=20 folder. These are from run 27903687624 (n=10). The n=20 folder
(`phase4_n20_download/`) supersedes this for the certified result.

---

## 5. Root-Level CSV Files — OLD ERA (Orphaned / Superseded)

The following files at the repo root are from the **OLD era** (custom8/custom9 pre-pivot
sweep pipeline, run via `run_full_project.ps1` + `gradle runFullSweep`). They use the
3-mode format (`ql_false`, `ql_true`, `rule_based` as separate benchmark CSVs) from the
pre-pivot architecture. They are **not consumed by any Phase 1–4 analysis script** and
should not be treated as thesis results.

| File | Era | Provenance | Status |
|---|---|---|---|
| `benchmark_results_ql_false.csv` | [OLD] | OLD sweep pipeline; last local run of custom8 or Step 0 probe | **Orphaned** — superseded by per-seed CI consolidated artefacts |
| `benchmark_results_ql_true.csv` | [OLD] | Same | **Orphaned** |
| `benchmark_results_rule_based.csv` | [OLD] | Same | **Orphaned** |
| `bench_step_log_ql_false.csv` | [OLD] | OLD sweep pipeline step log | **Orphaned** |
| `bench_step_log_ql_true.csv` | [OLD] | Same | **Orphaned** |
| `bench_step_log_rule_based.csv` | [OLD] | Same | **Orphaned** |

**Source:** The format is described in [`analysis/sweep_report.py#L1-L18`](../../analysis/sweep_report.py#L1)
and the Step 0 audit probe in `/memories/repo/audit-step-0-sanity.md` §6 (which copies
`benchmark_results_ql_*.csv` as probe artefacts for the custom8 run).  
The OLD benchmark format (`benchmark_results_<mode>.csv` per-run) was replaced by per-cell
per-seed CI artefacts in the new phase pipeline.

---

## 6. Root-Level CSV Files — NEW ERA (Local Single-Seed Outputs, Not Canonical)

The root-level CSVs listed below are **[NEW] era** files produced by local single-seed runs
of the new phase pipeline (training, adaptation, or dynamics). They reflect the most recent
local run and **are not the canonical n=10 CI results**. The canonical n=10 CI results are
inside the download folders documented in §1–§4 above.

| File pattern | Phase | Type |
|---|---|---|
| `metrics_stereotypes_{true,false}_lab{1,2,3,4,5}.csv` | Phase 1 / Phase 4 | Local single-seed training metrics |
| `metrics_stereotypes_{true,false}_{custom9,custom9s,labmon,labmon2}.csv` | Phase 1 extensions | Local single-seed training metrics |
| `first_goal_stereotypes_{true,false}_*.csv` | Phase 1 | Local single-seed first-goal episode log |
| `coverage_stereotypes_{true,false}_*.csv` | Phase 1 | Local single-seed state-coverage log |
| `iv_stats_stereotypes_{true,false}_*.json` | Phase 1 | Local single-seed IV-effectiveness JSON |
| `qtable_{initial,final}_stereotypes_{true,false}_*.csv` | Phase 1 / Phase 4 | Local single-seed Q-table dumps |
| `learned_stereotypes_{true,false}_*.ttl` | Phase 1 / Phase 4 | Local single-seed learned stereotype TTL |
| `recovery_stereotypes_{true,false}_*.csv` | Phase 2 | Local single adaptation-run recovery CSVs |
| `metrics_adapted_stereotypes_{true,false}_*.csv` | Phase 2 | Local single adaptation-run training metrics |
| `qtable_adapted_stereotypes_{true,false}_*.csv` | Phase 2 | Local adapted Q-table dumps |
| `dynamics_delays_{true,false}_lab{2,3}_slow.csv` | Phase 3 | Local single-replica delay probe results |
| `timebounded_results_{true,false}_lab{2,3}_slow.csv` | Phase 3 | Local single-replica time-bounded results |
| `learned_dynamics_{true,false}_lab{2,3}_slow.ttl` | Phase 3 | Local single-replica learned dynamics TTL |

These files coexist with the CI consolidated results and will be overwritten by the next
local run. **Do not cite them as thesis results.**

---

## 7. Summary Table

| Phase | Canonical run ID | Download folder | Consolidated CSVs verified | Analysis script(s) | Docs section |
|---|---|---|---|---|---|
| **Phase 1 xzone-asis** | 27440842780 | `phase1_xzone_asis/` | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_xzone_asis_analysis.md` |
| **Phase 1 xzone-bumped** (headline) | 27461188614 | `phase1_xzone_bumped/` | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_xzone_bumped_analysis.md` |
| Phase 1 xzone-bumped s11–20 | 27462446044 | `phase1_xzone_bumped_s11_20/` | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_xzone_replication_s11_20_analysis.md` |
| Phase 1 xzone-ablation | 27464846574 | `phase1_xzone_ablation/` | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_xzone_ablation_analysis.md` |
| Phase 1 xzone-mid (intermediate bleed, new lab3 physics) | 28941204656 | `phase1_xzone_mid/` | ✓ `analysis/out/` | `sweep_report.py` | `docs/_audit/14_presentation_rules.md` §5 |
| Phase 1 kg_only headline | 27336756264 | `phase1_headline_download/kg_only/` (restored 2026-07-08) | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_results_n10.md` §8 + `phase1_headline_download/PROVENANCE.md` |
| Phase 1 baseline control | 27344626272 | `phase1_headline_download/baseline/` (restored 2026-07-08) | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_results_n10.md` §16 + `PROVENANCE.md` |
| Phase 1 ib5 sensitivity | 27342571251 | `phase1_headline_download/ib5/` (restored 2026-07-08) | ✓ `analysis/out/` | `sweep_report.py` | `docs/phase1_results_n10.md` §13 + `PROVENANCE.md` |
| Phase 1 pbrs_only control | ~~27347962788 FAILED~~ → **28929859927** (re-dispatch, success 2026-07-08) | `phase1_headline_download/pbrs_only/` | ✓ `analysis/out/` | `sweep_report.py` | `phase1_headline_download/PROVENANCE.md` §§20+ |
| Phase 2.1 (first measurable recovery; superseded instrument) | 27499405083 | `phase2_results_v2/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE1_TO_PHASE2_CHANGES.md` §12 |
| Phase 2 v5 (lamp-fault, counter-based instrument; superseded per §9.7) | 27547019772 | `phase2_results_v5/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE1_TO_PHASE2_CHANGES.md` §19 |
| Phase 2.3 instant blacklist (RoR ×7 cells) | 28590019536 | `phase2_results_v6/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE1_TO_PHASE2_CHANGES.md` §20 |
| Phase 2.4 blind/z2 extension (RoR ×6 cells) | 28745352239 | `phase2_ext_results/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE1_TO_PHASE2_CHANGES.md` §21 |
| Phase 2.4 binv backfill (RoR `lab2_f1binv`) | 28750100413 | `phase2_binv_backfill/` | ✓ `phase2-consolidated/analysis/out/` | `phase2_recovery.py` | `docs/PHASE1_TO_PHASE2_CHANGES.md` §21.9 |
| Phase 2.5 labmon (RoR `labmon_f1dead`) | 28863439179 | `labmon_ci_results/` | ✓ `phase2-consolidated/analysis/out/` | `phase2_recovery.py` | `docs/PHASE2_5B_BEST_EFFORT_DEGRADATION.md` |
| Phase 2.5b lowsun (RoR `lab3_f2dead_lowsun`) | 28866807391 | `phase2_lowsun_results/run_28866807391/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE2_5B_LAB3_RESULTS.md` |
| Phase 2.5 labmon2 (RoR `labmon2_f2dead_lowsun`) | 28884717500 | `phase2_lowsun_results/run_28884717500/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/PHASE2_5_LABMON2_RESULTS.md` |
| Phase 2 §9.9 replication (RoR `lab3_f1dead`) | 28913465680 | `phase2_lab3f1dead_replication/run_28913465680/` | ✓ `analysis/out/` | `phase2_recovery.py` | `docs/phase2_registered_reanalysis_delta.md` §6 |
| **Phase 2 registered pooled analysis (canonical)** | pooled over the §9.7 runs of record above | `analysis/out_phase2_registered/` | ✓ | `phase2_recovery.py --registered` | `docs/pre_registration.md` §9 + `docs/phase2_registered_reanalysis_delta.md` |
| Phase 3 n=5 (prelim) | 27598417789 | `phase3_download/` | ✓ `phase3-consolidated/analysis/out/` | `phase3_dynamics.py` | `docs/PHASE2_TO_PHASE3_CHANGES.md` §16 |
| **Phase 3 n=10 (canonical)** | 27621106006 | `phase3_download_n10/` | ✓ `phase3-consolidated/analysis/out/` | `phase3_dynamics.py` | `docs/PHASE2_TO_PHASE3_CHANGES.md` §19.4 |
| Phase 4 n=10 | 27903687624 | `phase4_confirm_download/` | ✓ `phase4-consolidated/analysis/out/` | `phase4_energy.py` + `phase4_llm_baseline.py` + `sweep_report.py` | `docs/PHASE4.md` §10 |
| **Phase 4 n=20 (canonical)** | 27905392725 | `phase4_n20_download/` | ✓ `phase4-consolidated/analysis/out/` | `phase4_energy.py` + `phase4_llm_baseline.py` + `sweep_report.py` | `docs/PHASE4.md` §10a |

---

## 8. Discrepancies vs Task Prompt

The following items differ from the anchor values supplied in the task prompt. All are based
on file evidence in the workspace; "NOT FOUND" entries mean the item is absent, not that the
data does not exist.

| Anchor claim | Verified fact | Evidence |
|---|---|---|
| "folders phase1_xzone_*" are Phase 1 download folders for runs 27336756264/27344626272/27342571251/27347962788 | INCORRECT — those four runs have no local download folder. The xzone folders belong to four separate cross-zone investigation runs (27440842780, 27461188614, 27462446044, 27464846574) | Folder `phase1_xzone_asis/analysis/out/` sources cite GH run 27440842780, not 27336756264 |
| "pbrs_only 27347962788" as a control with local data | FAILED run — `paper_notes/ACTIONS_RUNS_20260616T133609Z.csv` row 94 records `"conclusion","failure"`. No results section in docs. **RESOLVED 2026-07-08:** re-dispatched as run 28929859927 (success); local data in `phase1_headline_download/pbrs_only/`; all contrasts null (negative control passes). | `paper_notes/PHASE1_RESULTS.md`: `"Failed run retained in AUDIT HISTORY only"`; `phase1_headline_download/PROVENANCE.md#L161-L209` |
| "Phase 2.1 run 27499405083 = FINAL run" | 27499405083 is the FIRST Phase 2.1 run (recovery measurable for the first time). The FINAL certified lamp-fault Phase 2 result is run 27547019772 (§19, `phase2_results_v5/`). Extended to blind/z2 faults by run 28745352239 (§21). | `docs/PHASE1_TO_PHASE2_CHANGES.md#L1331`: `"## 19 Run #27547019772 ("v5") — final certified results & Phase-2 sign-off"` |
| "docs/PHASE1_TO_PHASE2_CHANGES.md §12" as Phase 2 write-up | §12 covers run 27499405083 only. §19 covers the final run 27547019772. The full write-up spans §11–§21. | `docs/PHASE1_TO_PHASE2_CHANGES.md#L416` (§12.1) and `#L1331` (§19) |
