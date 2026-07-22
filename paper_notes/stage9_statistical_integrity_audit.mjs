#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";

const outPath = process.argv[2] || "paper_notes/STAGE9_STATISTICAL_INTEGRITY_TABLES_20260618T092317Z.csv";
const scriptPath = slash(path.relative(process.cwd(), process.argv[1] || "paper_notes/stage9_statistical_integrity_audit.mjs"));
const scriptHash = sha256(scriptPath);
const scriptLines = lineCount(scriptPath);
const scriptRef = `local-sha256:${scriptHash}:${scriptPath}:L1-L${scriptLines}`;
const exactCommand = `node paper_notes/stage9_statistical_integrity_audit.mjs ${outPath}`;

const files = {
  phase1Table: "paper_notes/PHASE1_TABLES.csv",
  phase1R2Table: "paper_notes/PHASE1_TABLES_R2_20260618T075201Z.csv",
  phase2Table: "paper_notes/PHASE2_TABLES.csv",
  phase2R2Table: "paper_notes/PHASE2_TABLES_R2_20260618T090000Z.csv",
  phase2Actions: "paper_notes/PHASE2_ACTIONS_STAGE8.csv",
  phase2Jobs: "paper_notes/PHASE2_ACTIONS_STAGE8_JOBS.csv",
  evidenceGaps: "paper_notes/EVIDENCE_GAPS.md",
};

const loc = Object.fromEntries(
  Object.entries(files).map(([key, file]) => [key, localLocator(file)])
);

const phase1 = readCsv(files.phase1Table);
const phase2 = readCsv(files.phase2R2Table);
const actions = readCsv(files.phase2Actions);
const jobs = readCsv(files.phase2Jobs);

const rows = [];

add("S9T-001", "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "DERIVED", "POST_HOC_EXPLORATORY;ENGINEERING_VALIDATION",
  "Phase 2 R2 evidence table data-row count", loc.phase2R2Table, "data_rows", phase2.length,
  "ROW_COUNT_FROM_CSV", "COUNT_REPRODUCED_BY_STAGE9_SCRIPT",
  "Header is excluded from data-row count.");

for (const [status, count] of sortedCounts(groupCount(phase2, "verification_status"))) {
  add(`S9T-00${rows.length + 1}`, "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY",
    status === "DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED" ? "UNRESOLVED" : "DERIVED",
    "ENGINEERING_VALIDATION",
    `Phase 2 R2 verification-status count: ${status}`, loc.phase2R2Table,
    `verification_status=${status}`, count, "GROUP_COUNT_FROM_CSV",
    status === "DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED"
      ? "BOOTSTRAP_OUTPUT_NOT_INDEPENDENTLY_RESAMPLED"
      : "RECOMPUTED_OR_EXACT_CHECKED_BY_STAGE8_EXTRACTOR",
    "Counts reproduce the Stage 8/R2 verification-status partition.");
}

const failed = phase2.filter((r) => r.verification_status === "CHECK_FAILED_OR_NOT_RECOMPUTED").length;
add("S9T-005", "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", failed === 0 ? "DERIVED" : "UNRESOLVED",
  "ENGINEERING_VALIDATION", "Phase 2 R2 check-failed row count", loc.phase2R2Table,
  "verification_status=CHECK_FAILED_OR_NOT_RECOMPUTED", failed, "FILTER_COUNT_FROM_CSV",
  failed === 0 ? "NO_CHECK_FAILURE_ROWS_IN_STAGE9_INPUT_TABLE" : "CHECK_FAILURE_PRESENT",
  "This audits the Stage 8/R2 verifier output, not the original Python bootstrap.");

for (const [recordType, count] of sortedCounts(groupCount(
  phase2.filter((r) => r.verification_status === "DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED"),
  "record_type"
))) {
  add(`S9T-00${rows.length + 1}`, "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "UNRESOLVED",
    "ENGINEERING_VALIDATION", `Phase 2 bootstrap-output fields by record type: ${recordType}`,
    loc.phase2R2Table, `record_type=${recordType}; verification_status=DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED`,
    count, "FILTER_GROUP_COUNT_FROM_CSV", "BOOTSTRAP_OUTPUT_NOT_INDEPENDENTLY_RESAMPLED",
    "These are CI and bootstrap-p fields carried from analysis CSVs.");
}

const recoveryRows = readGitCsv("22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv")
  .filter((r) => r.metric === "RecoveryEpisodes");
add("S9T-008", "MANUSCRIPT_EVIDENCE", "DIRECT", "ENGINEERING_VALIDATION;POST_HOC_EXPLORATORY",
  "Phase 2 well-posed RecoveryEpisodes paired-family size", "origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12",
  "metric=RecoveryEpisodes; row_count", recoveryRows.length, "FILTER_COUNT_FROM_COMMITTED_CSV",
  "RECOVERY_FAMILY_RESTRICTED_TO_WELL_POSED_PROFILES",
  "Rows are lab3_f1dead and lab3_f1inv only.");

const detectRows = readGitCsv("22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv")
  .filter((r) => r.metric === "DetectEpisode");
add("S9T-009", "MANUSCRIPT_EVIDENCE", "DIRECT", "ENGINEERING_VALIDATION;POST_HOC_EXPLORATORY",
  "Phase 2 DetectEpisode paired-family size", "origin/results@22a448be5d9829751badd341904e36ed582f091f:phase2/27547019772-20260615-183138/analysis_out/phase2_recovery_paired.csv:L1-L12",
  "metric=DetectEpisode; row_count", detectRows.length, "FILTER_COUNT_FROM_COMMITTED_CSV",
  "DETECTION_LATENCY_FAMILY_INCLUDES_ALL_PROFILES",
  "This is descriptive engineering evidence, not the headline recovery-speed family.");

add("S9T-010", "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "DERIVED", "POST_HOC_EXPLORATORY",
  "Phase 1 evidence table data-row count", loc.phase1Table, "data_rows", phase1.length,
  "ROW_COUNT_FROM_CSV", "COUNT_REPRODUCED_BY_STAGE9_SCRIPT",
  "Header is excluded from data-row count.");

for (const [status, count] of sortedCounts(groupCount(phase1, "recompute_status"))) {
  add(`S9T-0${rows.length + 1}`, "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "DERIVED",
    "POST_HOC_EXPLORATORY", `Phase 1 recompute-status count: ${status}`, loc.phase1Table,
    `recompute_status=${status}`, count, "GROUP_COUNT_FROM_CSV",
    status.includes("MISMATCH") ? "RECOMPUTE_MISMATCH_PRESENT" : "MEAN_OR_MEAN_DIFF_MATCHED_FROM_RAW",
    "This audits deterministic means and mean differences, not bootstrap resampling.");
}

const p1Mismatch = phase1.filter((r) => /MISMATCH|NOT_FOUND/.test(r.recompute_status || "")).length;
add("S9T-013", "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", p1Mismatch === 0 ? "DERIVED" : "UNRESOLVED",
  "POST_HOC_EXPLORATORY", "Phase 1 recompute mismatch/not-found row count", loc.phase1Table,
  "recompute_status contains MISMATCH or NOT_FOUND", p1Mismatch, "FILTER_COUNT_FROM_CSV",
  p1Mismatch === 0 ? "NO_DETERMINISTIC_RECOMPUTE_FAILURE_ROWS" : "DETERMINISTIC_RECOMPUTE_FAILURE_PRESENT",
  "This does not close the Stage 6 independent-resampling gap.");

for (const [note, count] of sortedCounts(groupCount(phase1, "notes"))) {
  add(`S9T-0${rows.length + 1}`, "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "UNRESOLVED",
    "POST_HOC_EXPLORATORY", `Phase 1 statistical-source note count`, loc.phase1Table,
    `notes=${note}`, count, "GROUP_COUNT_FROM_CSV", "BOOTSTRAP_AND_TEST_OUTPUTS_NOT_INDEPENDENTLY_RESAMPLED",
    "Rows copy CI and/or p/q fields from analysis CSVs.");
}

const jobCounts = Object.fromEntries(actions.filter((r) => r.recordType === "job_count").map((r) => [r.key, r.value]));
add("S9T-016", "AUDIT_HISTORY", "SUPERSEDED", "NOT_APPLICABLE",
  "Phase 2 v5 job-inventory limitation remains superseded", `${loc.phase2Actions}; ${loc.phase2Jobs}`,
  "job_count(all_jobs,adapt,clean,aggregate,compile)", `all_jobs=${jobCounts.all_jobs}; adapt=${jobCounts.adapt}; clean=${jobCounts.clean}; aggregate=${jobCounts.aggregate}; compile=${jobCounts.compile}`,
  "DIRECT_FROM_ACTIONS_CAPTURE", "JOB_INVENTORY_NOT_REOPENED",
  "Remaining workflow provenance gaps are dispatch inputs and artifact ZIP byte identity.");

const artifactAttempt = actions.find((r) => r.recordType === "download_attempt" && r.key === "artifact_zip_identity");
add("S9T-017", "AUDIT_HISTORY;MANUSCRIPT_EVIDENCE", "UNRESOLVED", "UNRESOLVED",
  "Phase 2 artifact ZIP byte identity", loc.phase2Actions, "artifact_zip_identity",
  artifactAttempt?.value || "NOT FOUND", "DIRECT_FROM_ACTIONS_CAPTURE",
  "ZIP_BYTE_IDENTITY_NOT_VERIFIED",
  "Artifact digest metadata is recorded separately; local ZIP byte verification remains unresolved.");

const runMeta = actions.find((r) => r.recordType === "run" && r.key === "run_metadata");
add("S9T-018", "AUDIT_HISTORY;MANUSCRIPT_EVIDENCE", "UNRESOLVED", "UNRESOLVED",
  "Phase 2 workflow_dispatch input payload", loc.phase2Actions, "workflow_dispatch.inputs",
  "NOT FOUND", "DIRECT_GAP_RECORD", "DISPATCH_INPUT_PAYLOAD_NOT_FOUND",
  `Run metadata row: ${runMeta?.value || "NOT FOUND"}`);

add("S9T-019", "AUDIT_HISTORY;MANUSCRIPT_EVIDENCE", "UNRESOLVED", "UNRESOLVED",
  "Formal post-pivot preregistration", loc.evidenceGaps, "formal_post_pivot_preregistration",
  "NOT FOUND", "DIRECT_GAP_RECORD", "DO_NOT_PROMOTE_TO_PREREGISTERED_CONFIRMATORY",
  "Stage 9 preserves existing gap status.");

add("S9T-020", "AUDIT_HISTORY;MANUSCRIPT_EVIDENCE", "UNRESOLVED", "UNRESOLVED",
  "Lab3 stale-magnitude documentation and dirty-doc numeric-source limits", loc.evidenceGaps,
  "lab3_stale_magnitude; dirty_doc_numeric_source_limits", "ACTIVE", "DIRECT_GAP_RECORD",
  "NUMERIC_MANUSCRIPT_VALUES_REQUIRE_PRIMARY_RESULT_ROWS",
  "Dirty docs remain routing/history sources only.");

add("S9T-021", "MANUSCRIPT_EVIDENCE;AUDIT_HISTORY", "DERIVED", "ENGINEERING_VALIDATION",
  "Phase 2 base and R2 table byte identity", `${loc.phase2Table}; ${loc.phase2R2Table}`,
  "sha256(PHASE2_TABLES.csv)==sha256(PHASE2_TABLES_R2_20260618T090000Z.csv)",
  String(sha256(files.phase2Table) === sha256(files.phase2R2Table)), "HASH_COMPARISON",
  "R2_TABLE_BYTE_IDENTICAL_TO_STAGE8_BASE_TABLE",
  `hash=${sha256(files.phase2Table)}`);

writeCsv(outPath, rows, [
  "evidence_id",
  "product_scope",
  "evidence_label",
  "research_status",
  "claim_or_object",
  "input_sources",
  "metric",
  "value",
  "derivation_method",
  "statistical_integrity_status",
  "analysis_script_ref",
  "exact_command",
  "notes",
]);

console.log(`Wrote ${rows.length} rows -> ${outPath}`);

function add(evidenceId, productScope, evidenceLabel, researchStatus, claimOrObject, inputSources, metric, value, derivationMethod, integrityStatus, notes) {
  rows.push({
    evidence_id: evidenceId,
    product_scope: productScope,
    evidence_label: evidenceLabel,
    research_status: researchStatus,
    claim_or_object: claimOrObject,
    input_sources: inputSources,
    metric,
    value: String(value),
    derivation_method: derivationMethod,
    statistical_integrity_status: integrityStatus,
    analysis_script_ref: scriptRef,
    exact_command: exactCommand,
    notes,
  });
}

function readGitCsv(spec) {
  const text = runGitShow(spec);
  return parseCsv(text).records;
}

function runGitShow(spec) {
  const result = spawnSync("git", ["show", spec], { encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`git show failed for ${spec}: ${result.stderr}`);
  }
  return result.stdout;
}

function localLocator(file) {
  return `local-sha256:${sha256(file)}:${slash(file)}:L1-L${lineCount(file)}`;
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function lineCount(file) {
  const text = fs.readFileSync(file, "utf8");
  if (text.length === 0) return 0;
  const lines = text.split(/\r\n|\n|\r/);
  if (lines[lines.length - 1] === "") lines.pop();
  return lines.length;
}

function readCsv(file) {
  return parseCsv(fs.readFileSync(file, "utf8")).records;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const clean = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < clean.length; i += 1) {
    const ch = clean[i];
    if (quoted) {
      if (ch === "\"") {
        if (clean[i + 1] === "\"") {
          field += "\"";
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === "\"") {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  const filtered = rows.filter((r) => r.some((v) => v !== ""));
  if (!filtered.length) return { header: [], records: [] };
  const header = filtered[0];
  return {
    header,
    records: filtered.slice(1).map((cols) => {
      const rec = {};
      header.forEach((h, i) => {
        rec[h] = cols[i] ?? "";
      });
      return rec;
    }),
  };
}

function groupCount(records, key) {
  const out = new Map();
  for (const rec of records) {
    const value = rec[key] || "NOT FOUND";
    out.set(value, (out.get(value) || 0) + 1);
  }
  return out;
}

function sortedCounts(map) {
  return [...map.entries()].sort((a, b) => String(a[0]).localeCompare(String(b[0])));
}

function writeCsv(file, records, header) {
  const lines = [header.join(",")];
  for (const rec of records) {
    lines.push(header.map((h) => csvEscape(rec[h] ?? "")).join(","));
  }
  fs.writeFileSync(file, `${lines.join("\n")}\n`, "utf8");
}

function csvEscape(value) {
  const s = String(value);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, "\"\"")}"` : s;
}

function slash(s) {
  return s.replace(/\\/g, "/");
}
