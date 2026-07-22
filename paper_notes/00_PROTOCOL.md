# Evidence Extraction Protocol

## 1. Purpose

This directory is the durable audit layer for turning the repository into
scientific-paper notes. It records evidence and provenance; it does not replace
the repository, GitHub Actions artifacts, raw data, or the thesis template.

Stage 0 is inventory-only. No experimental result is interpreted here.

## 2. Required Products

Maintain two separate products throughout the project:

1. **AUDIT HISTORY**: branches, commits, workflow runs, failed attempts,
   corrections, downloaded artifacts, local experiments, and superseded claims.
2. **MANUSCRIPT EVIDENCE**: only evidence needed to explain the final research
   problem, approach, evaluation, findings, limitations, and related work.

Chronological evidence may be essential to the audit while remaining absent
from the final manuscript.

## 3. Evidence Labels

- `[DIRECT]`: explicitly present in a cited source.
- `[DERIVED]`: calculated from cited inputs with an exact method and command.
- `[INTERPRETATION]`: a bounded scientific interpretation supported by cited
  direct or derived evidence.
- `[UNRESOLVED]`: not established, incomplete, conflicting, or missing.
- `[SUPERSEDED]`: historically valid as a record of what was concluded, but no
  longer authoritative for the final research claim.

Labels describe epistemic status, not statistical significance.

## 4. Research Status

Every experiment and claim must also be classified as one of:

- `PRE_REGISTERED_CONFIRMATORY`
- `REGISTERED_DEVIATION_CONFIRMATORY`
- `POST_HOC_EXPLORATORY`
- `ENGINEERING_VALIDATION`
- `NOT_APPLICABLE`
- `UNRESOLVED`

Do not retroactively call an exploratory result confirmatory.

## 5. Provenance Classes

- `COMMITTED`: content is addressable by full Git commit SHA and path.
- `ACTIONS_DERIVED`: content is declared or verified as extracted from a GitHub
  Actions artifact. The run, head SHA, artifact, and local tree hash are tracked.
- `LOCAL_GENERATED`: produced locally, with no verified Actions artifact identity.
- `DOCUMENTATION`: local or committed notes; claims inside still require checking
  against primary code, configuration, raw results, or run metadata.
- `EXTERNAL_LOCAL`: a local file outside this repository, identified by SHA-256.
- `UNKNOWN_PROVENANCE`: origin or generation command is not established.

`ACTIONS_DERIVED` does not by itself prove that a local extracted directory is
byte-identical to the current artifact ZIP. That requires an artifact digest or
download verification and must be stated separately.

## 6. Immutable Source Locators

Use the most specific applicable locator.

### 6.1 Committed text or code

`branch@FULL_COMMIT_SHA:path:Lx-Ly`

The full SHA is authoritative. The branch is descriptive because branches move.

### 6.2 Local untracked or external file

`local-sha256:SHA256:path:Lx-Ly`

For a whole binary file, omit line numbers. A local path without a hash is not an
immutable locator.

### 6.3 Local directory

`local-tree-sha256:TREE_HASH:path`

Use the file-level locator inside the directory when citing a value.

### 6.4 CSV

`SOURCE_LOCATOR:row N; column_a=value; column_b=value`

Rows are counted with the header as row 1 unless a note explicitly states
otherwise. Name columns; do not cite a bare cell coordinate.

### 6.5 JSON or JSONL

`SOURCE_LOCATOR:Lx-Ly; JSONPath=$....`

For JSONL, also state the one-based record number.

### 6.6 GitHub Actions

`repo; workflow; run ID; run URL; head SHA; job; artifact; artifact file; row/path`

Record the observation timestamp for mutable run status. Completed run metadata
is still cited with the immutable run ID and head SHA.

### 6.7 Derived evidence

State all input locators, the analysis script at a full commit SHA or local file
hash, the exact command, software/runtime versions where material, and the output
locator. A derived value without this chain is `[UNRESOLVED]`.

## 7. TREE-SHA256-V1

Stage 0 directory hashes use `TREE-SHA256-V1`, computed with Node.js v22.14.0:

1. Recursively enumerate regular files only.
2. Normalize relative path separators to `/`.
3. Sort normalized relative paths with JavaScript `localeCompare` using locale
   `en` and `sensitivity: variant`.
4. Compute lowercase SHA-256 for each file's bytes.
5. Feed the tree SHA-256 with UTF-8 bytes for each record in order:
   `relative_path\0decimal_byte_length\0file_sha256\n`
6. In step 5, `\0` and `\n` are literal two-character separators (backslash plus
   character), not NUL and newline bytes.
7. File modification times are recorded for inventory but excluded from the hash.

Empty directories, ACLs, alternate data streams, and directory timestamps are
not represented. Recompute after any file content, path, or length change.

## 8. Ledger Rules

- `SOURCE_LEDGER.csv` identifies sources and provenance state.
- `CLAIM_LEDGER.csv` contains atomic claims. One row must not combine several
  independently falsifiable claims.
- `RUN_LEDGER.csv` identifies experimental and workflow executions.
- `EVIDENCE_GAPS.md` records missing, conflicting, or weak provenance.
- Never delete a superseded ledger row. Change its status and link its successor.
- Separate source statements from verification. Documentation can prove that a
  statement was made, not that the statement is empirically true.
- Do not cite file modification time as proof of a run, download, or generation.
- Do not use an uncommitted document as the sole support for an empirical number.
- Use `NOT FOUND` rather than completing a missing value by inference.

## 9. Experiment Record Requirements

Before results are interpreted, every experiment must document:

- research question or hypothesis;
- prior expectation;
- treatment and baseline;
- independent, dependent, and controlled variables;
- seeds, scenarios, stopping conditions, and exclusions;
- metric definitions and statistical method;
- adversarial or failure scenarios;
- unexpected observations;
- follow-up experiments;
- confirmatory, deviation, exploratory, or engineering status.

## 10. Paper-Structure Boundaries

- **Background**: terminology and foundations required to understand the work.
- **Related work**: comparison with alternative research approaches.
- **Approach**: conceptual mechanism and design, not a file-by-file implementation
  diary and not evaluation results.
- **Implementation/Reproducibility**: concrete technology and code mapping, often
  shortened in the main text and expanded in an appendix.
- **Evaluation**: study design, metrics, statistical procedures, results, and
  direct explanations of observed behavior.
- **Discussion**: limitations, threats to validity, failure cases, scope, and
  generalizability.

## 11. Stage 0 Repository Snapshot

- Observed at: `2026-06-15T11:14:16.7677252Z`
- Repository: `https://github.com/esra-dev/MT-PhysicsBAS.git`
- Branch: `phase2-fault-detection`
- HEAD: `2aab559a027468b929cdb5bc83fc402519ccefb2`
- Upstream divergence: `+0/-0`
- Tracked unstaged changes: none
- Tracked staged changes: none
- Untracked paths before creating `paper_notes/`: 33
- Git: `2.54.0.windows.1`
- GitHub CLI: `2.92.0`
- PowerShell: `5.1.26100.8655`
- Node.js: `22.14.0`

The normal Git status could not inspect `.pytest_cache/` because access was
denied. That cache is excluded from the scientific evidence inventory.

## 12. Required CSV Schemas

### 12.1 `SOURCE_LEDGER.csv`

`source_id, stage, product_scope, evidence_label, source_type,
provenance_class, verification_status, ref_or_run, path, locator,
hash_algorithm, content_hash, file_count, byte_count, observed_at_utc,
description, limitations`

- One row identifies one immutable source snapshot or one explicitly
  superseded snapshot.
- `verification_status` must distinguish declared mappings, byte verification,
  text-normalized comparison, and unresolved provenance.
- A corrected hash receives a new source row. The prior row is retained with
  `evidence_label=SUPERSEDED` and a successor named in `limitations`.

### 12.2 `CLAIM_LEDGER.csv`

`claim_id, stage, product_scope, evidence_label, research_status, claim_text,
claim_status, source_ids, source_locators, derivation_method,
analysis_script_ref, exact_command, review_status, notes`

- Claims are atomic and independently falsifiable.
- `source_ids` and `source_locators` are mandatory; use `NOT FOUND` where the
  required source does not exist.
- A derived claim must name every input, the script hash, and the exact command.

### 12.3 `RUN_LEDGER.csv`

`run_id, stage, phase, experiment_label, workflow, run_url, event, status,
conclusion, head_branch, head_sha, run_attempt, created_at_utc, updated_at_utc,
job_name, job_id, job_url, artifact_name, artifact_id, artifact_digest,
artifact_count, local_root, local_tree_hash, provenance_status,
research_status, observed_at_utc, notes`

- Mutable run status is always paired with `observed_at_utc`.
- Artifact metadata must not be treated as proof that a local extraction is
  byte-identical unless the downloaded archive digest and extracted tree were
  verified.

## 13. Stage 0 Continuation Snapshot

The continuation snapshot is recorded by `SRC-0040` and claims
`CLM-S0-009` through `CLM-S0-012`. It preserves the original snapshot above
and records the later branch head, dirty-worktree inventory, corrected tree
hashes, the ingested v4 result root, and the subsequent in-progress workflow
run without interpreting experimental outcomes.
