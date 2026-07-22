# Phase 3 Results Evidence Notes

Stage: `10A`
Created: `2026-06-18T09:59:42Z`
Scope: evidence extraction only. This is not polished thesis prose.

## AUDIT HISTORY

| record | label | evidence |
|---|---|---|
| P3-AH-001 | [DIRECT] | Current worktree branch during Stage 10A was `phase3-process-dynamics`, HEAD `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433`; `origin/results` was `0372ecd5864fa6555ebfce7d05e05d9aaab96994`. Locators: local commands `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse origin/results`. |
| P3-AH-002 | [DIRECT] | n=10 run `27621106006` was a successful `workflow_dispatch` of workflow `Phase 3 (process dynamics, response-delay learning)` on `main` with head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, attempt `1`, created `2026-06-16T13:29:35Z`, updated `2026-06-16T13:33:10Z`. GitHub Actions locator: workflow/run `https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/27621106006`; head SHA as above; observed `2026-06-18T09:59:42Z`; command `gh run view 27621106006 --json databaseId,displayTitle,event,status,conclusion,headBranch,headSha,attempt,createdAt,updatedAt,url,workflowName,jobs`. |
| P3-AH-003 | [DIRECT] | n=10 run aggregate job `81670617760` completed successfully and uploaded `phase3-consolidated`; artifact id `7668397627`, digest `sha256:a882677d1689d2f25470591771fd1ef80035de560e837e9ab01857381e9f9416`, size `58495`, artifact count for run `42`. GitHub Actions locator: workflow/run/job/artifact as in P3-AH-002; command `gh api repos/esra-dev/MT-PhysicsBAS/actions/runs/27621106006/artifacts`. |
| P3-AH-004 | [DIRECT] | n=10 results were published to `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994` under `phase3/27621106006-20260616-133306/`. Locators: `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:L1-L5`; `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:L1-L9`. |
| P3-AH-005 | [DERIVED] | Local n=10 extracted tree `phase3_download_n10` has `415` files and `2719726` bytes with `TREE-SHA256-V1=5fe3c3e8c57c1ea1da0338fe888161006b99e26a7f50d6cbabc7850ab3848d2c`; nested `phase3-consolidated` has `123` files and `137205` bytes with `TREE-SHA256-V1=2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945`. Script locator: `local-sha256:13bcc1aedb7a50cba1e81933017ba229bda2642db059f89ab0938ed9e7d5bd93:paper_notes/00_PROTOCOL.md:L82-L103`; exact commands: `node paper_notes/TREE_SHA256_V1.mjs phase3_download_n10`; `node paper_notes/TREE_SHA256_V1.mjs phase3_download_n10/phase3-consolidated`. |
| P3-AH-006 | [SUPERSEDED] | Earlier n=5 run `27598417789` was successful but superseded for final Phase 3 authority because paired headline rows have `n_paired=5` and `p_wilcoxon=0.0625`. Locators: GitHub Actions run `https://github.com/esra-dev/MT-PhysicsBAS/actions/runs/27598417789`, head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, artifact `phase3-consolidated` id `7658950188`, digest `sha256:42b38654a85adad350f1a9316a2cd7aafc4d95fafda839a22703e8dd7c316736`; committed CSV `origin/results@abc66fcb9bf0be36d7a36ac1608c2049887cc738:phase3/27598417789-20260616-062513/analysis_out/phase3_compliance_paired.csv:L1-L9`. |
| P3-AH-007 | [UNRESOLVED] | Run `27621106006` head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53` still has workflow `replicas` dispatch default `1,2,3,4,5`; later branch commit `eda6ca1ffa026e723ad1a18a2bdb3aed927e7433` changes the default to `1..10`. The n=10 run is supported by the 10-replica artifacts and raw tree, not by the run-head default. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L46-L49`; `phase3-process-dynamics@eda6ca1ffa026e723ad1a18a2bdb3aed927e7433:.github/workflows/phase3.yml:L46-L49`; raw count row `P3T-012`. |

## MANUSCRIPT EVIDENCE

### Result Authority

| item | label | locator |
|---|---|---|
| Final candidate Phase 3 run | [DIRECT] | `27621106006`, workflow `Phase 3 (process dynamics, response-delay learning)`, head SHA `3bb5289c36cb3093228ec0609fe57ec676b1ee53`, success. GitHub Actions locator in P3-AH-002. |
| Final candidate result commit | [DIRECT] | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/`. |
| Raw n=10 input tree | [DERIVED] | `local-tree-sha256:2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945:phase3_download_n10/phase3-consolidated`. |
| Recompute command | [DERIVED] | Script `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:analysis/phase3_dynamics.py:L1-L575`; exact command `python analysis/phase3_dynamics.py --root phase3_download_n10/phase3-consolidated/dynamics_root --out paper_notes/stage10a_phase3_recompute_n10`. |

### Delay-Learning Accuracy

| profile | mode | n_actuators | instant/delayed | slowest learned ticks | truth ticks | abs err ticks | rel err pct | label | evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lab2_slow | ql_false | 4 | 2 / 2 | 12.1125 | 12 | 0.1125 | 0.94 | [DIRECT] | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_delay_accuracy.csv:row 2; named columns profile,mode,n_actuators,n_instantaneous,n_delayed,slowest_learned_ticks,ground_truth_ticks,abs_err_ticks,rel_err_pct`. |
| lab2_slow | ql_true | 4 | 2 / 2 | 12.1875 | 12 | 0.1875 | 1.56 | [DIRECT] | Same CSV, row 3; named columns as above. |
| lab3_slow | ql_false | 5 | 3 / 2 | 12.2125 | 12 | 0.2125 | 1.77 | [DIRECT] | Same CSV, row 4; named columns as above. |
| lab3_slow | ql_true | 5 | 3 / 2 | 12.2125 | 12 | 0.2125 | 1.77 | [DIRECT] | Same CSV, row 5; named columns as above. |

[DERIVED] Across all n=10 raw delay rows, response class matched the action-label expectation in `180/180` rows: `80` delayed blind rows and `100` instantaneous non-blind rows. Input: `local-tree-sha256:2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945:phase3_download_n10/phase3-consolidated`. Exact command: PowerShell `Import-Csv` over `dynamics_delays_*.csv`, grouping `action_label` contains `Blinds` versus `response_class`. Evidence row: `P3T-019`.

### Deadline Compliance

| profile | mode | n_replicas | goals/replica | overall | tight | loose | energy mean | mean actual delay | label | evidence |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| lab2_slow | ql_false | 10 | 6 | 0.5 | 0.0 | 1.0 | 0.0 | 60.583333333333336 | [DIRECT] | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_ci.csv:row 2; named columns profile,mode,n_replicas,n_goals_total,overall_compliance_mean,tight_compliance_mean,loose_compliance_mean,total_energy_mean,mean_actual_delay_mean`. |
| lab2_slow | ql_true | 10 | 6 | 1.0 | 1.0 | 1.0 | 3.2 | 33.33333333333333 | [DIRECT] | Same CSV, row 3; named columns as above. |
| lab3_slow | ql_false | 10 | 6 | 0.5 | 0.0 | 1.0 | 0.0 | 60.583333333333336 | [DIRECT] | Same CSV, row 4; named columns as above. |
| lab3_slow | ql_true | 10 | 6 | 1.0 | 1.0 | 1.0 | 3.3 | 33.08333333333333 | [DIRECT] | Same CSV, row 5; named columns as above. |

### Paired Statistics

| profile | metric | n | ql_true | ql_false | diff | CI | p_bootstrap | p_wilcoxon | Cliff_delta | q_BH | label | evidence |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| lab2_slow | overall_compliance | 10 | 1.0 | 0.5 | 0.5 | [0.5, 0.5] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | `origin/results@0372ecd5864fa6555ebfce7d05e05d9aaab96994:phase3/27621106006-20260616-133306/analysis_out/phase3_compliance_paired.csv:row 2; named columns profile,metric,n_paired,ql_true_mean,ql_false_mean,mean_diff_true_minus_false,ci_lo,ci_hi,p_bootstrap,p_wilcoxon,cliffs_delta,q_bootstrap_bh`. |
| lab3_slow | overall_compliance | 10 | 1.0 | 0.5 | 0.5 | [0.5, 0.5] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | Same CSV, row 3; named columns as above. |
| lab2_slow | tight_compliance | 10 | 1.0 | 0.0 | 1.0 | [1.0, 1.0] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | Same CSV, row 4; named columns as above. |
| lab3_slow | tight_compliance | 10 | 1.0 | 0.0 | 1.0 | [1.0, 1.0] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | Same CSV, row 5; named columns as above. |
| lab2_slow | loose_compliance | 10 | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 1.0 | 1.0 | 0.0 | 1.0 | [DIRECT] | Same CSV, row 6; named columns as above. |
| lab3_slow | loose_compliance | 10 | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 1.0 | 1.0 | 0.0 | 1.0 | [DIRECT] | Same CSV, row 7; named columns as above. |
| lab2_slow | total_energy | 10 | 3.2 | 0.0 | 3.2 | [3.0, 3.5] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | Same CSV, row 8; named columns as above plus lower_is_better and ql_true_better. |
| lab3_slow | total_energy | 10 | 3.3 | 0.0 | 3.3 | [3.0, 3.6] | 0.0 | 0.001953125 | 1.0 | 0.0 | [DIRECT] | Same CSV, row 9; named columns as above plus lower_is_better and ql_true_better. |

### Mechanism Records

| item | label | evidence |
|---|---|---|
| lab2_slow per-goal split | [DIRECT] | In rep1, `ql_true` met `6/6` goals and selected lights for tight goals `g1`, `g2`, `g5`; `ql_false` met `3/6` and missed tight goals `g1`, `g2`, `g5` after selecting blinds with believed delay `0.00`. Locators: `local-sha256:5fdeeddc4a56d0378f21e750dff3b8f9042286ce3c6bc8f8bac996f31af9c490:phase3_download_n10/phase3-consolidated/dynamics_root/rep1/timebounded_results_true_lab2_slow.csv:rows 2-7; named columns goal_id,deadline_sec,chosen_label,believed_delay_sec,actual_delay_sec,energy_cost,met`; `local-sha256:fe7e2d88222d79cd096b4d31f645a35ca2f69d8a6ceab31cb4730a98a164fc46:phase3_download_n10/phase3-consolidated/dynamics_root/rep1/timebounded_results_false_lab2_slow.csv:rows 2-7; named columns goal_id,deadline_sec,chosen_label,believed_delay_sec,actual_delay_sec,energy_cost,met`. |
| lab3_slow cross-zone/loose nuance | [DERIVED] | n=10 raw rows show lab3 `ql_true` loose-goal blind labels split `5/5` for goals `g3`, `g4`, and `g6`, while all corresponding outcomes remain `met=1`. Input: `local-tree-sha256:2c7a4523124ccdbe176cc88e0dd968a5759012db28eba6b267b40d6850e8b945:phase3_download_n10/phase3-consolidated`. Exact command: PowerShell `Import-Csv` over `timebounded_results_*.csv`, grouped by `profile,mode,goal_id,chosen_label,met`. Evidence row: `P3T-031`. |
| KG writeback artifact evidence | [DIRECT] | n=10 local tree contains `40` learned dynamics TTL files. Source: `P3T-012`. Example artifact family is generated by `saveLearnedDynamics` and uploaded by workflow. Locators: `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:src/env/tools/DynamicsLearner.java:L176-L220`; `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53:.github/workflows/phase3.yml:L200-L213`. |

### Interpretation Boundary

| interpretation | label | support |
|---|---|---|
| Delay learning works in the tested slow-lab landscape | [INTERPRETATION] | Supported by direct delay rows P3T-015 through P3T-018 and raw class check P3T-019. Scope is two slow profiles with one delayed actuator class at `12` ticks and instantaneous lamps/spotlight. |
| Learned delay is actionable for tight deadlines | [INTERPRETATION] | Supported by paired tight compliance rows P3T-026 and P3T-027: both profiles have `diff=1.0`, CI `[1.0,1.0]`, `p_wilcoxon=0.001953125`, Cliff's delta `1.0`, and `q_BH=0.0`. |
| Energy is a conditioned trade-off | [INTERPRETATION] | Supported by P3T-029 and compliance rows P3T-020 through P3T-023. `ql_true` spends more energy because it uses fast powered lamps for tight goals; lower energy is not the headline success metric. |
| n=10 is final candidate authority; n=5 is superseded | [INTERPRETATION] | Supported by P3T-032 and n=10 rows P3T-024 through P3T-027. n=5 remains audit history because `p_wilcoxon=0.0625` at n=5. |

## Unresolved Issues

| issue | label | evidence |
|---|---|---|
| Phase 3 exact dispatch input payload | [UNRESOLVED] | `gh run view` and artifact metadata establish workflow, run, head SHA, success, artifact count, and digest, but Stage 10A did not recover the exact `workflow_dispatch` input payload. Evidence row: `P3T-033`. |
| Phase 3 local artifact ZIP byte identity | [UNRESOLVED] | Artifact digest for `phase3-consolidated` is available (`sha256:a882677d1689d2f25470591771fd1ef80035de560e837e9ab01857381e9f9416`), and the extracted tree is hashed, but Stage 10A did not redownload the ZIP and verify extracted bytes against the digest. Evidence row: `P3T-033`. |
| Formal preregistration | [UNRESOLVED] | Formal post-pivot preregistration remains `NOT FOUND`; the dirty doc's expected-outcome note is not treated as formal preregistration. Evidence row: `P3T-034`. |
| Carried Stage 9 gaps | [UNRESOLVED] | Phase 1/2 dispatch input payloads, Phase 1/2 artifact ZIP byte identity, Stage 6/8 resampling reproduction, lab3 stale-magnitude documentation, and dirty-doc numeric-source limits remain open. Evidence row: `P3T-035`. |

## Handoff

Completed:
- [DIRECT] Read protocol and Stage 9 required handoff list.
- [DIRECT] Audited Phase 3 source/config/workflow at actual run head `main@3bb5289c36cb3093228ec0609fe57ec676b1ee53`.
- [DIRECT] Verified n=10 GitHub Actions run metadata, artifact metadata, and `origin/results` publication.
- [DERIVED] Recomputed n=10 and n=5 Phase 3 statistics from raw local CSVs using `analysis/phase3_dynamics.py`.
- [SUPERSEDED] Marked n=5 run `27598417789` as superseded audit history, not final manuscript authority.

Unresolved:
- [UNRESOLVED] Exact Phase 3 dispatch input payload is `NOT FOUND`.
- [UNRESOLVED] Phase 3 local extracted directory is not ZIP-byte-verified against the GitHub artifact digest.
- [UNRESOLVED] Formal post-pivot preregistration remains `NOT FOUND`.
- [UNRESOLVED] Stage 9 carried gaps remain open; older v5 job-inventory limitation remains superseded and is not reopened.

Next stage must read:
- `paper_notes/00_PROTOCOL.md`
- `paper_notes/STAGE9_STATISTICAL_INTEGRITY_AUDIT_20260618T092317Z.md`
- `paper_notes/PHASE3_METHODS.md`
- `paper_notes/PHASE3_RESULTS.md`
- `paper_notes/PHASE3_TABLES.csv`
- `paper_notes/PHASE3_FIGURES.md`
- `paper_notes/SOURCE_LEDGER.csv`
- `paper_notes/CLAIM_LEDGER.csv`
- `paper_notes/RUN_LEDGER.csv`
- `paper_notes/EVIDENCE_GAPS.md`
- `analysis/phase3_dynamics.py`
- `config/run_config.json`
- `.github/workflows/phase3.yml`
- `src/agt/illuminance_controller_agent_dynamics.asl`
- `src/env/tools/DynamicsLearner.java`
- `phase3_download_n10/phase3-consolidated/analysis/out/`
- `phase3_download_n10/phase3-consolidated/dynamics_root/`
