# Phase-2 Registered Re-Analysis — Results Delta Note

**Date:** 2026-07-08 · branch `phase2-instant-blacklist`
**Registration:** `docs/pre_registration.md` §9 (written before this re-analysis ran)
**Script:** `analysis/phase2_recovery.py` (seed-keyed pairing + frozen §9.5/§9.6 BH families)
**Command:** `python analysis/phase2_recovery.py --registered --out analysis/out_phase2_registered`
**Outputs:** `analysis/out_phase2_registered/phase2_recovery_{ci,paired}.csv`

## 1. What changed in the analysis

1. **Pairing is now by seed key** (path `seed<N>` token), never by list position.
   Previously, whenever one arm dropped a replica (non-reconvergence or flake), every
   subsequent "pair" was two different seeds (audit `docs/_audit/12_stats_review.md` §3.2).
   The `seeds_paired` column now records the exact seeds used per contrast.
2. **One frozen Tier-1 BH family, m = 8** (§9.5), replacing the per-run families
   (m = 2 → 8 → 0 → 1 across iterations, audit §3.3).
3. **Detection family frozen at m = 8 non-degenerate cells** (§9.6); the 10 cells with
   `DetectEpisode ≡ 0` in both arms are excluded as constants (audit §3.4).
4. **One run of record per cell** (§9.7); superseded instrument eras (v1–v5), v6's
   `lab3_f1dead`/`lab3_f1inv` (pre-probe monitoring instrument) and ext's flaked
   `lab2_f1binv` are history, not confirmatory inputs.

## 2. Before → after, Tier-1 recovery family (RecoveryEpisodes, ql_true − ql_false)

"Before" = the published per-run artefact for that cell's run of record (positional
pairing, per-run BH family). "After" = the pooled seed-paired registered analysis
(m = 8). Δ < 0 means the KG-primed arm recovers faster.

| Cell | Before: Δ · 95 % CI · p_wil · δ · q (family) | After: Δ · 95 % CI · p_wil · δ · q (m = 8) | Same side of 0.05? |
|---|---|---|---|
| `lab3_f1dead` | −61.6 · [−102.8, −12.0] · 0.055 · −0.63 · **q = 0.028** (ext, m=8 positional) | −67.4 · [−130.7, **+1.1**] · 0.098 · −0.63 · **q = 0.053** | **NO — flips sig → ns** |
| `lab3_f1dead_z2` | −95.7 · [−140.9, −54.9] · 0.004 · −0.84 · q = 0.000 (ext) | −95.7 · [−141.2, −55.2] · 0.004 · −0.84 · q = 0.000 | yes |
| `lab3_f1bdead` | −426.5 · [−1183.8, −20.3] · 0.027 · −0.55 · q = 0.003 (ext) | −426.5 · [−1183.2, −19.3] · 0.027 · −0.55 · q = 0.001 | yes |
| `lab3_f1binv` | −940.6 · [−2156.7, −79.7] · 0.012 · −0.49 · q = 0.000 (ext, n=9 misaligned) | −908.9 · [−2138.8, −48.0] · 0.027 · −0.47 · q = 0.001 | yes |
| `lab2_f1bdead` | −226.7 · [−333.6, −141.5] · 0.002 · −0.92 · q = 0.000 (ext) | −226.7 · [−328.7, −142.5] · 0.002 · −0.92 · q = 0.000 | yes |
| `labmon_f1dead` | −6.2 · [−8.5, −4.2] · 0.002 · −0.86 · q = 0.000 (m=1) | −6.2 · [−8.5, −4.2] · 0.002 · −0.86 · q = 0.000 | yes |
| `lab3_f2dead_lowsun` | −64.9 · [−97.3, −34.0] · 0.004 · −0.88 · q ≈ 0 (m=1) | −64.9 · [−97.3, −34.4] · 0.004 · −0.88 · q = 0.000 | yes |
| `labmon2_f2dead_lowsun` | −148.5 · δ = −0.75 · q ≈ 0 (m=1, `docs/PHASE2_5_LABMON2_RESULTS.md`) | −148.5 · [−208.1, −78.7] · 0.006 · −0.75 · q = 0.000 | yes |

Tier-2 descriptive cells (no q by registration, direction unchanged): `lab3_f1inv`
Δ = −54.0 (ns), `lab3_f1inv_z2` Δ = −160.7 (ns), `lab2_f1binv` Δ = −43.3 (ns).

## 3. Before → after, detection family (DetectEpisode, m = 8)

| Cell | Before q (per-run) | After q (m = 8) | Same side? |
|---|---|---|---|
| `lab3_f1inv` | 0.006 (ext) — KG **slower** to detect, +3.0 eps | **0.005** — same direction | yes (significant both) |
| `lab3_f1dead` | 0.215 (ext) | 0.156 | yes (ns) |
| `lab3_f1dead_z2` | 0.620 (ext) | 0.609 | yes (ns) |
| `lab3_f1inv_z2` | 0.084 (ext) | 0.084 | yes (ns) |
| `lab3_f1bdead` | 0.349 (ext) | 0.273 | yes (ns) |
| `lab3_f1binv` | 0.349 (ext, misaligned) | 0.273 | yes (ns) |
| `lab2_f1bdead` | 0.620 (ext) | 0.609 | yes (ns) |
| `lab2_f1binv` | 0.057 (backfill, m=1) | 0.146 | yes (ns) |

The 10 degenerate instant-detection cells (`DetectEpisode ≡ 0` both arms) are excluded
from the family and reported descriptively (detection recall 100 % in every cell).

## 4. Why `lab3_f1dead` flips

The flip is driven by the **pairing fix**, not by the family change: in the ext run the
`ql_true` arm re-converged in 9/10 seeds (seed3 missing), so positional pairing matched
`ql_true` seed4…10 against `ql_false` seed3…9. The misaligned pairs happened to
*understate* the variance of the difference (published CI [−102.8, −12.0], p = 0.018;
correctly paired CI [−130.7, +1.1], p = 0.053). With m = 8 the BH-adjusted q lands at
0.053 — marginally above the 0.05 threshold.

Context (descriptive, not confirmatory): the superseded v6 measurement of the same cell
(pre-probe instrument, 10/10 pairs, seed-aligned by construction) showed Δ = −204.9,
q = 0.0 — the direction is independently replicated; the ext measurement is simply a
smaller, noisier effect (its vanilla arm recovered much faster: mean 252.9 vs v6's 342.3).

## 5. Verdict per §9 / audit item

**Not analysis-only:** one flagship cell crosses 0.05.

- **`lab3_f1dead` (Tier-1 cell #1)** flips from q = 0.028 (published, misaligned) to
  q = 0.053 (registered, seed-paired). Under the frozen registration this cell is
  currently **not significant** (direction preserved: Δ = −67.4, δ = −0.63,
  one-sided p = 0.026).
- All other 7 Tier-1 cells keep q ≤ 0.006. The detection family keeps the same
  significance side everywhere.

**A CI rerun would be needed for exactly one cell: `lab3_f1dead`** (e.g. seeds 11–20
under the current instrument, analysed as a registered replication). Nothing has been
dispatched. Alternative: keep the registered result and report `lab3_f1dead` honestly as
directionally consistent but marginal (q = 0.053), leaning on the blind-fault, labmon and
lowsun cells for the confirmatory Phase-2 claim.

**Decision (2026-07-08):** option (a) taken — the one-shot replication is registered in
`docs/pre_registration.md` §9.9 (seeds 11–20, frozen analysis and decision rule) before
dispatch.

## 6. §9.9 replication outcome (run 28913465680) — `lab3_f1dead` CONFIRMED

The registered replication (CI run
[`28913465680`](https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/28913465680),
commit `b9bf4cb` = the §9.9 registration commit, seeds 11–20, conclusion *success*)
completed with 10/10 detection, 10/10 reconvergence and 10/10 goal-reaching replicas in
both arms (`RecoveredGoalRate` 0.85–1.0). Raw data:
`phase2_lab3f1dead_replication/run_28913465680/recovery_root/`. Per the frozen §9.9 rule
it replaces run 28745352239 as the cell's run of record; the final pooled `--registered`
analysis gives:

| Cell | Δ (true − false) | 95 % CI | p_wil | δ | q (m = 8) | §9.9 verdict |
|---|---|---|---|---|---|---|
| `lab3_f1dead` (seeds 11–20) | **−121.1** (149.4 vs 270.5) | [−201.6, −51.8] | 0.0137 | −0.72 | **0.00027** | **confirmed** (Δ < 0, q ≤ 0.05) |

The superseded measurements remain reported alongside per §9.9: ext seeds 1–10
Δ = −67.4, q = 0.053 (marginal); v6 seeds 1–10 (pre-probe instrument) Δ = −204.9, q = 0.0.
Three independent seed sets agree on the direction; the replication makes the registered
family verdict unanimous.

**Final registered Phase-2 result: all 8 Tier-1 cells significant** (max q = 0.0012,
`lab3_f1bdead`), every Δ negative (KG-primed recovers faster), δ from −0.47 to −0.92.
Detection family unchanged: `lab3_f1inv` remains the one significant detection contrast
(KG slower to detect the inverted lamp, q = 0.0048); `lab3_f1dead`'s detection row now
comes from the replication (Δ = +1.7, q = 0.437, ns). H-P2 (§9.2) is **confirmed on every
cell of the frozen family**; no further Phase-2 reruns are permitted under §9.9.
