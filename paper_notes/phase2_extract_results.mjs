#!/usr/bin/env node
/*
 * Stage 8 Phase 2 result extractor/verifier.
 *
 * Inputs are a fresh extraction of origin/results@22a448... and the aggregate
 * CSVs committed there. The script intentionally avoids Python dependencies so
 * it can run in the current Windows shell where python.exe is only the Store
 * shim. It verifies deterministic metrics from raw recovery rows, plus exact
 * Wilcoxon, Cliff's delta, and BH q-values from the aggregate p-values. It does
 * not reimplement NumPy PCG64 bootstrap resampling; bootstrap CI and bootstrap
 * p fields are carried as direct analysis outputs and marked not independently
 * resampled.
 */

import fs from "node:fs";
import path from "node:path";

const COMMIT = "22a448be5d9829751badd341904e36ed582f091f";
const REF = `origin/results@${COMMIT}`;
const RUN_PATH = "phase2/27547019772-20260615-183138";
const GOAL_THRESHOLD = 0.5;
const WELL_POSED = new Set(["lab3_f1dead", "lab3_f1inv"]);
const URI = "http://example.org/was#";

const args = parseArgs(process.argv.slice(2));
const root = args.root;
const outPath = args.out;
if (!root || !outPath) {
  die("Usage: node paper_notes/phase2_extract_results.mjs --root ROOT --out paper_notes/PHASE2_TABLES.csv");
}

const runRoot = path.join(root, RUN_PATH);
const recoveryRoot = path.join(runRoot, "recovery_root");
const analysisRoot = path.join(runRoot, "analysis_out");
if (!fs.existsSync(recoveryRoot)) die(`Missing recovery root: ${recoveryRoot}`);
if (!fs.existsSync(analysisRoot)) die(`Missing analysis root: ${analysisRoot}`);

const rawRows = readRawRows(recoveryRoot);
const cells = buildCells(rawRows);
const ciRows = readCsv(path.join(analysisRoot, "phase2_recovery_ci.csv"));
const pairedRows = readCsv(path.join(analysisRoot, "phase2_recovery_paired.csv"));

const table = [];
for (const [idx, row] of ciRows.entries()) {
  addCiRows(table, row, idx + 2, cells);
}
for (const [idx, row] of pairedRows.entries()) {
  addPairedRows(table, row, idx + 2, cells, pairedRows);
}
for (const cell of [...cells.values()].sort((a, b) => keyOfCell(a).localeCompare(keyOfCell(b)))) {
  addRawCellRows(table, cell);
}

writeCsv(outPath, table, [
  "table_id",
  "stage",
  "product_scope",
  "evidence_label",
  "research_status",
  "record_type",
  "profile",
  "mode",
  "metric",
  "value",
  "unit_or_scale",
  "source_locator",
  "verification_status",
  "derived_value",
  "derived_inputs",
  "notes",
]);

const statusCounts = new Map();
for (const row of table) statusCounts.set(row.verification_status, (statusCounts.get(row.verification_status) ?? 0) + 1);
console.log(`Wrote ${table.length} rows -> ${outPath}`);
for (const [k, v] of [...statusCounts.entries()].sort()) console.log(`${k}: ${v}`);

function parseArgs(argv) {
  const parsed = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--root" || a === "--out") parsed[a.slice(2)] = argv[++i];
  }
  return parsed;
}

function die(message) {
  console.error(message);
  process.exit(1);
}

function readRawRows(dir) {
  const files = walk(dir).filter((p) => /recovery_stereotypes_(true|false)_.+\.csv$/i.test(path.basename(p))).sort();
  const rows = [];
  for (const file of files) {
    const rel = slash(path.relative(root, file));
    const parts = rel.split("/");
    const seedPart = parts.find((p) => /^seed\d+$/.test(p));
    const seed = seedPart ? Number(seedPart.replace("seed", "")) : Number.NaN;
    const m = path.basename(file).match(/^recovery_stereotypes_(true|false)_(.+)\.csv$/);
    if (!m) continue;
    const mode = m[1] === "true" ? "ql_true" : "ql_false";
    const profile = m[2];
    const csvRows = readCsv(file);
    for (const [idx, r] of csvRows.entries()) {
      rows.push({
        ...r,
        seed,
        mode,
        profile,
        file,
        relFromExtract: rel,
        sourcePath: `${RUN_PATH}/${slash(path.relative(runRoot, file))}`,
        csvRowNumber: idx + 2,
      });
    }
  }
  return rows;
}

function buildCells(rows) {
  const cells = new Map();
  for (const row of rows) {
    const key = `${row.profile}||${row.mode}`;
    if (!cells.has(key)) cells.set(key, { profile: row.profile, mode: row.mode, rows: [] });
    cells.get(key).rows.push(row);
  }
  for (const cell of cells.values()) {
    cell.rows.sort((a, b) => a.sourcePath.localeCompare(b.sourcePath));
    cell.nRuns = cell.rows.length;
    cell.detectEpisodes = cell.rows.map((r) => asNumber(r.DetectEpisode)).filter((v) => Number.isFinite(v) && v >= 0);
    cell.recoveryEpisodes = cell.rows.map((r) => asNumber(r.RecoveryEpisodes)).filter((v) => Number.isFinite(v) && v >= 0);
    cell.goalRates = cell.rows.map((r) => asNumber(r.RecoveredGoalRate)).filter((v) => Number.isFinite(v) && v >= 0);
    cell.goalReaching = cell.rows.filter((r) => asNumber(r.RecoveryEpisodes) >= 0 && asNumber(r.RecoveredGoalRate) >= GOAL_THRESHOLD);
    cell.defects = [...new Set(cell.rows.map((r) => (r.DefectComponent ?? "").trim()).filter(Boolean))].sort();
    const expected = expectedComponents(cell.profile);
    cell.expectedDefectComponent = expected.join(";");
    cell.aggregateDefectSetMatches = cell.defects.join(";") === cell.expectedDefectComponent;
    cell.unexpectedComponentRows = cell.rows.filter((r) => {
      const actual = normalizeComponents(r.DefectComponent);
      return actual.some((component) => !expected.includes(component));
    });
  }
  return cells;
}

function addCiRows(table, row, sourceRow, cells) {
  const cell = cells.get(`${row.profile}||${row.mode}`);
  const derived = {
    n_runs: cell?.nRuns,
    defect_component: cell?.defects.join(";"),
    well_posed_recovery: String(WELL_POSED.has(row.profile)),
    detection_rate: cell ? cell.detectEpisodes.length / cell.nRuns : Number.NaN,
    reconverge_rate: cell ? cell.recoveryEpisodes.length / cell.nRuns : Number.NaN,
    n_detected: cell?.detectEpisodes.length,
    n_reconverged: cell?.recoveryEpisodes.length,
    greedy_goal_rate_mean: mean(cell?.goalRates ?? []),
    n_goal_reaching: cell?.goalReaching.length,
    goal_reaching_rate: cell ? cell.goalReaching.length / cell.nRuns : Number.NaN,
    RecoveryEpisodes_mean: mean(cell?.recoveryEpisodes ?? []),
    DetectEpisode_mean: mean(cell?.detectEpisodes ?? []),
  };
  const cols = Object.keys(row).filter((c) => c !== "profile" && c !== "mode");
  for (const col of cols) {
    const isBootstrap = /_ci_(lo|hi)$/.test(col);
    const hasDerived = Object.hasOwn(derived, col);
    const verified = hasDerived ? compareValues(row[col], derived[col]) : false;
    const status = isBootstrap
      ? "DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED"
      : (verified ? "VERIFIED_DETERMINISTIC_FROM_RAW" : "CHECK_FAILED_OR_NOT_RECOMPUTED");
    table.push({
      table_id: "T-P2-STAGE8-FINAL-CI-LONG",
      stage: "8",
      product_scope: "MANUSCRIPT_EVIDENCE",
      evidence_label: isBootstrap ? "UNRESOLVED" : (verified ? "DERIVED" : "UNRESOLVED"),
      research_status: "ENGINEERING_VALIDATION",
      record_type: "final_ci_metric",
      profile: row.profile,
      mode: row.mode,
      metric: col,
      value: row[col],
      unit_or_scale: unitFor(col),
      source_locator: `${REF}:${RUN_PATH}/analysis_out/phase2_recovery_ci.csv:row ${sourceRow}; named columns profile=${row.profile}; mode=${row.mode}; ${col}=${row[col]}`,
      verification_status: status,
      derived_value: hasDerived ? formatValue(derived[col]) : "NOT RECOMPUTED",
      derived_inputs: cell ? rawInputs(cell.rows) : "NOT FOUND",
      notes: isBootstrap ? "Bootstrap interval field not independently resampled because Python/NumPy is unavailable in this environment." : "",
    });
  }
}

function addPairedRows(table, row, sourceRow, cells, allPairedRows) {
  const metric = row.metric;
  const trueCell = cells.get(`${row.profile}||ql_true`);
  const falseCell = cells.get(`${row.profile}||ql_false`);
  const a = metricValues(trueCell, metric);
  const b = metricValues(falseCell, metric);
  const n = Math.min(a.length, b.length);
  const aa = a.slice(0, n);
  const bb = b.slice(0, n);
  const meanDiff = mean(aa) - mean(bb);
  const derived = {
    n_paired: n,
    ql_true_mean: mean(aa),
    ql_false_mean: mean(bb),
    mean_diff_true_minus_false: meanDiff,
    p_wilcoxon: wilcoxonTwoSided(aa, bb),
    cliffs_delta: cliffsDelta(aa, bb),
    ql_true_faster: String(meanDiff < 0),
    q_bootstrap_bh: bhForRow(row, allPairedRows),
    bh_family_m: allPairedRows.filter((r) => r.metric === metric).length,
  };
  const cols = Object.keys(row).filter((c) => c !== "profile" && c !== "metric");
  for (const col of cols) {
    const isBootstrap = col === "p_bootstrap" || col === "p_bootstrap_one_sided_true_faster" || col === "ci_lo" || col === "ci_hi";
    const hasDerived = Object.hasOwn(derived, col);
    const verified = hasDerived ? compareValues(row[col], derived[col]) : false;
    const status = isBootstrap
      ? "DIRECT_ANALYSIS_OUTPUT_RESAMPLING_NOT_RECOMPUTED"
      : (verified ? "VERIFIED_DETERMINISTIC_OR_EXACT_TEST" : "CHECK_FAILED_OR_NOT_RECOMPUTED");
    table.push({
      table_id: "T-P2-STAGE8-FINAL-PAIRED-LONG",
      stage: "8",
      product_scope: "MANUSCRIPT_EVIDENCE",
      evidence_label: isBootstrap ? "UNRESOLVED" : (verified ? "DERIVED" : "UNRESOLVED"),
      research_status: "ENGINEERING_VALIDATION",
      record_type: "final_paired_metric",
      profile: row.profile,
      mode: "ql_true_vs_ql_false",
      metric: `${metric}.${col}`,
      value: row[col],
      unit_or_scale: unitFor(col),
      source_locator: `${REF}:${RUN_PATH}/analysis_out/phase2_recovery_paired.csv:row ${sourceRow}; named columns profile=${row.profile}; metric=${metric}; ${col}=${row[col]}`,
      verification_status: status,
      derived_value: hasDerived ? formatValue(derived[col]) : "NOT RECOMPUTED",
      derived_inputs: trueCell && falseCell ? `${rawInputs(trueCell.rows)} || ${rawInputs(falseCell.rows)}` : "NOT FOUND",
      notes: isBootstrap ? "Bootstrap field not independently resampled because Python/NumPy is unavailable in this environment." : "",
    });
  }
}

function addRawCellRows(table, cell) {
  const rows = [
    ["aggregate_defect_set_matches_expected", String(cell.aggregateDefectSetMatches), "boolean", "Union of detected components across the cell equals the expected injected fault component set."],
    ["unexpected_component_row_count", cell.unexpectedComponentRows.length, "count", "Rows containing a detected component outside the expected injected fault component set."],
    ["detected_count", cell.detectEpisodes.length, "count", "DetectEpisode >= 0."],
    ["reconverged_count", cell.recoveryEpisodes.length, "count", "RecoveryEpisodes >= 0."],
    ["goal_reaching_count", cell.goalReaching.length, "count", `RecoveryEpisodes >= 0 and RecoveredGoalRate >= ${GOAL_THRESHOLD}.`],
  ];
  for (const [metric, value, unit, notes] of rows) {
    table.push({
      table_id: "T-P2-STAGE8-FINAL-RAW-CELL",
      stage: "8",
      product_scope: "MANUSCRIPT_EVIDENCE",
      evidence_label: "DERIVED",
      research_status: "ENGINEERING_VALIDATION",
      record_type: "final_raw_cell_verification",
      profile: cell.profile,
      mode: cell.mode,
      metric,
      value: String(value),
      unit_or_scale: unit,
      source_locator: "DERIVED_FROM_RAW_ROWS",
      verification_status: "VERIFIED_DETERMINISTIC_FROM_RAW",
      derived_value: String(value),
      derived_inputs: rawInputs(cell.rows),
      notes,
    });
  }
}

function metricValues(cell, metric) {
  if (!cell) return [];
  if (metric === "RecoveryEpisodes") return [...cell.recoveryEpisodes];
  if (metric === "DetectEpisode") return [...cell.detectEpisodes];
  return [];
}

function bhForRow(target, rows) {
  const family = rows.filter((r) => r.metric === target.metric);
  const pvals = family.map((r) => asNumber(r.p_bootstrap));
  const qs = bhQvalues(pvals);
  const idx = family.findIndex((r) => r.profile === target.profile && r.metric === target.metric);
  return qs[idx];
}

function bhQvalues(pvalues) {
  const indexed = pvalues.map((p, i) => ({ p, i })).filter((x) => Number.isFinite(x.p));
  indexed.sort((a, b) => a.p - b.p);
  const q = Array(pvalues.length).fill(Number.NaN);
  let prev = 1;
  for (let rank = indexed.length; rank >= 1; rank -= 1) {
    const { p, i } = indexed[rank - 1];
    const adj = (p * indexed.length) / rank;
    prev = Math.min(prev, adj);
    q[i] = Math.min(1, prev);
  }
  return q;
}

function wilcoxonTwoSided(a, b) {
  if (a.length !== b.length || a.length < 2) return Number.NaN;
  const diffs = a.map((v, i) => v - b[i]).filter((d) => d !== 0);
  if (diffs.length === 0) return 1;
  const abs = diffs.map(Math.abs);
  const ranks = rankAbs(abs);
  const total = ranks.reduce((s, r) => s + r, 0);
  const pos = ranks.reduce((s, r, i) => s + (diffs[i] > 0 ? r : 0), 0);
  const stat = Math.min(pos, total - pos);
  let extreme = 0;
  const combos = 1 << ranks.length;
  for (let mask = 0; mask < combos; mask += 1) {
    let s = 0;
    for (let i = 0; i < ranks.length; i += 1) {
      if (mask & (1 << i)) s += ranks[i];
    }
    if (Math.min(s, total - s) <= stat + 1e-12) extreme += 1;
  }
  return extreme / combos;
}

function rankAbs(values) {
  const items = values.map((v, i) => ({ v, i })).sort((a, b) => a.v - b.v);
  const ranks = Array(values.length);
  let i = 0;
  while (i < items.length) {
    let j = i + 1;
    while (j < items.length && items[j].v === items[i].v) j += 1;
    const rank = (i + 1 + j) / 2;
    for (let k = i; k < j; k += 1) ranks[items[k].i] = rank;
    i = j;
  }
  return ranks;
}

function cliffsDelta(a, b) {
  if (!a.length || !b.length) return Number.NaN;
  let gt = 0;
  let lt = 0;
  for (const x of a) {
    for (const y of b) {
      if (x > y) gt += 1;
      else if (x < y) lt += 1;
    }
  }
  return (gt - lt) / (a.length * b.length);
}

function expectedComponents(profile) {
  if (profile.includes("_f2")) return [`${URI}SetZ1Light`, `${URI}SetZ2Light`];
  return [`${URI}SetZ1Light`];
}

function normalizeComponents(raw) {
  return String(raw ?? "").split(";").map((s) => s.trim()).filter(Boolean).sort();
}

function rawInputs(rows) {
  return rows.map((r) => {
    return `${REF}:${r.sourcePath}:row ${r.csvRowNumber}; named columns DefectComponent=${r.DefectComponent}; DetectEpisode=${r.DetectEpisode}; ReconvergeEpisode=${r.ReconvergeEpisode}; RecoveryEpisodes=${r.RecoveryEpisodes}; RecoveredGoalRate=${r.RecoveredGoalRate}`;
  }).join(" || ");
}

function sourceLocator(rel, rowNum, columns) {
  const named = Object.entries(columns).map(([k, v]) => `${k}=${v}`).join("; ");
  return `${REF}:${rel}:row ${rowNum}; named columns ${named}`;
}

function compareValues(actualRaw, expected) {
  const actual = String(actualRaw);
  if (typeof expected === "string") {
    const a = actual.toLowerCase();
    const e = expected.toLowerCase();
    if ((a === "true" || a === "false") && (e === "true" || e === "false")) return a === e;
    return actual === expected;
  }
  if (typeof expected === "boolean") return actual.toLowerCase() === String(expected).toLowerCase();
  if (!Number.isFinite(expected)) return actual.toLowerCase() === "nan" || actual === "";
  const got = asNumber(actual);
  return Number.isFinite(got) && Math.abs(got - expected) <= 1e-9;
}

function formatValue(v) {
  if (typeof v === "boolean") return String(v);
  if (typeof v === "string") return v;
  if (!Number.isFinite(v)) return "nan";
  return String(v);
}

function unitFor(col) {
  if (/rate|p_|q_|delta|faster|well_posed/.test(col)) return "ratio_or_boolean";
  if (/Episode|episodes|n_|count|m$/.test(col)) return "episodes_or_count";
  if (/component/.test(col)) return "URI_set";
  return "value";
}

function mean(values) {
  if (!values.length) return Number.NaN;
  return values.reduce((s, v) => s + v, 0) / values.length;
}

function asNumber(v) {
  const n = Number(String(v ?? "").trim());
  return Number.isNaN(n) ? Number.NaN : n;
}

function keyOfCell(cell) {
  return `${cell.profile}||${cell.mode}`;
}

function walk(dir) {
  const out = [];
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...walk(p));
    else if (ent.isFile()) out.push(p);
  }
  return out;
}

function readCsv(file) {
  const text = fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
  const rows = parseCsv(text);
  if (!rows.length) return [];
  const header = rows[0];
  return rows.slice(1).filter((r) => r.some((c) => c !== "")).map((r) => {
    const obj = {};
    header.forEach((h, i) => { obj[h] = r[i] ?? ""; });
    return obj;
  });
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === "\"") {
        if (text[i + 1] === "\"") {
          field += "\"";
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === "\"") {
      inQuotes = true;
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
  return rows;
}

function writeCsv(file, rows, cols) {
  const lines = [cols.join(",")];
  for (const row of rows) {
    lines.push(cols.map((c) => csvEscape(row[c] ?? "")).join(","));
  }
  fs.writeFileSync(file, `${lines.join("\n")}\n`, "utf8");
}

function csvEscape(v) {
  const s = String(v);
  if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, "\"\"")}"`;
  return s;
}

function slash(p) {
  return p.split(path.sep).join("/");
}
