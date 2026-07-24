# Phase-3 protocol-v2 archive — run 29926328852

- **Workflow:** `.github/workflows/phase3.yml`, GitHub Actions run `29926328852`
  (completed success, 2026-07-22), head `90e53f8b087fc390a7ad51a0187b81c89c21c64e`,
  branch `phase234-correction-2026-07-22`.
- **Registration:** `docs/phase3_correction_registration_2026-07-22.md`
  (commit `8010e49f`, contained in the dispatch head). Dispatch record:
  `docs/phase34_v2_dispatch_record_2026-07-22.md`.
- **Inputs:** `dynamics_profiles=lab2_slow,lab3_slow`, `replicas=1..10`,
  `probes=0` (config default 8), `publish_results=true`
  (`analysis/out/workflow_inputs.json`).
- **Source artifact:** `phase3-consolidated`, id `8532999058`,
  `sha256:056b232386a0849f813772da133aa9a4b172205b1743fae251a7849e2c522ce7`.
- **Contents:** `dynamics_root/rep{1..10}/` (per-cell DYNAMICS_OK gate
  manifests, delay tables, time-bounded results with
  tick_energy/tick_span/energy_meter=tick-v1, learned-dynamics TTLs) and
  `analysis/out/` (delay-accuracy, compliance CI/paired tables,
  `workflow_inputs.json`).
- **Gates:** `python analysis/validate_phase3_v2_archive.py <this dir>
  --profiles lab2_slow,lab3_slow --replicas 1-10` passes;
  `python analysis/reproduce_phase3_v2.py phase3_v2_corrected` rebuilds all
  three tables canonically byte-equivalent.
- **Publish:** results branch only — the Phase-3 workflow creates no results
  tag (long-standing publish mechanism, disclosed); the immutable provenance
  anchor is the run ID + artifact digest above.
- **Inventory:** `SHA256SUMS.csv` (163 data files + this manifest's inventory
  was generated before the manifest itself).
