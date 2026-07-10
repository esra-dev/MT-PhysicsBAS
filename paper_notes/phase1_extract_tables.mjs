import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const roots = [
  {
    rootId: "P1-ASIS",
    label: "as-is cross-zone magnitude",
    localRoot: "phase1_xzone_asis",
    runId: "27440842780",
    branch: "kg-crosszone-coupling",
    headSha: "866297d54750c91f4595962f9c975d2f1704f629",
    treeHash: "75a9c8ccea76c0bd52cef6cd0dad34bf2f4ffe8c13501690b59f8cbe186b52a9",
    researchStatus: "POST_HOC_EXPLORATORY",
    evidenceLabel: "SUPERSEDED",
  },
  {
    rootId: "P1-BUMP-S1-10",
    label: "bumped targeted cross-zone seeds 1-10",
    localRoot: "phase1_xzone_bumped",
    runId: "27461188614",
    branch: "kg-crosszone-coupling-bump",
    headSha: "8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1",
    treeHash: "e9d706b2f7828bb65bdb9d091269681b0f9acddd263c7d438777340b8a5b5343",
    researchStatus: "POST_HOC_EXPLORATORY",
    evidenceLabel: "DIRECT",
  },
  {
    rootId: "P1-BUMP-S11-20",
    label: "bumped targeted cross-zone seeds 11-20",
    localRoot: "phase1_xzone_bumped_s11_20",
    runId: "27462446044",
    branch: "kg-crosszone-coupling-bump",
    headSha: "8a98cd82d64d6e4003c767a2b5a3a6d48a744ad1",
    treeHash: "f80a117fac11c1db5ce3d545b04a4e418590f97c66d3ccc8ff44c6c8cc71152e",
    researchStatus: "POST_HOC_EXPLORATORY",
    evidenceLabel: "DIRECT",
  },
  {
    rootId: "P1-ABLATION-UNTARGETED",
    label: "bumped untargeted cross-zone ablation seeds 1-10",
    localRoot: "phase1_xzone_ablation",
    runId: "27464846574",
    branch: "kg-crosszone-ablation",
    headSha: "e8d63e09be504f1dc206737ca8feb05299fe1031",
    treeHash: "7c114de88374bb003264a994a50db753edc89113258a4a9a1d7f64831911c638",
    researchStatus: "POST_HOC_EXPLORATORY",
    evidenceLabel: "DIRECT",
  },
];

const metricKeys = [
  "goal_rate",
  "avg_steps",
  "avg_dev",
  "avg_energy",
  "avg_wasted",
  "avg_cycling",
  "avg_redundant",
];

const learningMetrics = [
  "auc_goal",
  "auc_reward",
  "episodes_to_threshold",
  "mean_first_goal",
];

const outPath = process.argv[2] || "paper_notes/PHASE1_TABLES.csv";
const commandText = "node paper_notes/phase1_extract_tables.mjs paper_notes/PHASE1_TABLES.csv";

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function csvParse(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          cell += '"';
          i++;
        } else {
          quoted = false;
        }
      } else {
        cell += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += ch;
    }
  }
  if (cell.length || row.length) {
    row.push(cell.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((r) => r.some((v) => v !== ""));
}

function readCsv(file) {
  const rows = csvParse(fs.readFileSync(file, "utf8"));
  if (!rows.length) return { header: [], records: [] };
  const header = rows[0];
  const records = rows.slice(1).map((cols, idx) => {
    const rec = { __rowNumber: idx + 2 };
    header.forEach((h, i) => {
      rec[h] = cols[i] ?? "";
    });
    return rec;
  });
  return { header, records };
}

function csvCell(value) {
  const s = value === undefined || value === null ? "" : String(value);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function writeCsv(file, rows) {
  const header = [
    "table_row_id",
    "section",
    "root_id",
    "run_id",
    "branch",
    "head_sha",
    "local_root",
    "local_tree_sha256",
    "analysis_file",
    "analysis_file_sha256",
    "analysis_file_row",
    "source_locator",
    "source_columns",
    "data_type",
    "profile",
    "mode_a",
    "mode_b",
    "condition",
    "metric",
    "metric_tier",
    "direction",
    "n",
    "seeds",
    "value",
    "ci_lo",
    "ci_hi",
    "p_value",
    "q_bootstrap_bh",
    "cliffs_delta",
    "recomputed_value",
    "recompute_input",
    "recompute_status",
    "research_status",
    "evidence_label",
    "notes",
    "derivation_command",
  ];
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(
    file,
    `${header.join(",")}\n${rows.map((r) => header.map((h) => csvCell(r[h])).join(",")).join("\n")}\n`,
    "utf8",
  );
}

function toNum(v) {
  if (v === undefined || v === null || v === "") return NaN;
  return Number(v);
}

function mean(xs) {
  const vals = xs.filter((v) => Number.isFinite(v));
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : NaN;
}

function closeEnough(a, b) {
  if (!Number.isFinite(a) && !Number.isFinite(b)) return true;
  return Math.abs(a - b) <= 1e-9;
}

function formatNum(v) {
  return Number.isFinite(v) ? String(v) : "";
}

function findSeedRoots(root) {
  const bench = path.join(root, "benchmark");
  if (!fs.existsSync(bench)) return [];
  return fs.readdirSync(bench, { withFileTypes: true })
    .filter((d) => d.isDirectory() && /^results_seed\d+$/.test(d.name))
    .map((d) => ({
      seed: Number(d.name.replace("results_seed", "")),
      dir: path.join(bench, d.name),
    }))
    .sort((a, b) => a.seed - b.seed);
}

function summariseBenchmark(csvFile) {
  if (!fs.existsSync(csvFile)) return null;
  const { records } = readCsv(csvFile);
  if (!records.length) return null;
  const n = records.length;
  const goals = records.filter((r) => r.GoalReached === "1").length;
  const col = (r, name) => toNum(r[name] || "0");
  const avgWasted = mean(records.map((r) => col(r, "WastedSteps")));
  const avgCycling = mean(records.map((r) => col(r, "ActuatorCyclingCount")));
  return {
    scenarios: n,
    goal_rate: goals / n,
    avg_steps: mean(records.map((r) => col(r, "Steps"))),
    avg_dev: mean(records.map((r) => col(r, "CumIlluminanceDeviation"))),
    avg_energy: mean(records.map((r) => col(r, "TotalEnergyCost"))),
    avg_wasted: avgWasted,
    avg_cycling: avgCycling,
    avg_redundant: avgWasted + avgCycling,
  };
}

function collectBenchmark(root) {
  const out = new Map();
  let files = 0;
  for (const { seed, dir } of findSeedRoots(root)) {
    for (const prof of ["lab1", "lab2", "lab3"]) {
      for (const mode of ["ql_false", "ql_true", "rule_based"]) {
        const file = path.join(dir, prof, mode, `benchmark_results_${mode}.csv`);
        const summary = summariseBenchmark(file);
        if (!summary) continue;
        files++;
        out.set(`${prof}|${mode}|${seed}`, summary);
      }
    }
  }
  return { out, files };
}

function aucNormalised(series) {
  if (!series.length) return NaN;
  if (series.length === 1) return series[0];
  let area = 0;
  for (let i = 0; i < series.length - 1; i++) {
    area += 0.5 * (series[i] + series[i + 1]);
  }
  return area / (series.length - 1);
}

function episodesToThreshold(goals, window = 100, thresh = 0.5) {
  if (!goals.length) return { value: NaN, censored: true };
  const w = Math.max(1, Math.min(window, goals.length));
  let run = 0;
  for (let i = 0; i < goals.length; i++) {
    run += goals[i];
    if (i >= w) run -= goals[i - w];
    const denom = Math.min(i + 1, w);
    if (i + 1 >= w && run / denom >= thresh) {
      return { value: i, censored: false };
    }
  }
  return { value: goals.length, censored: true };
}

function readEpisodeMetrics(file) {
  if (!fs.existsSync(file)) return null;
  const { records } = readCsv(file);
  const rows = records
    .filter((r) => r.Episode !== undefined && r.Episode !== "")
    .map((r) => ({
      ep: Number(r.Episode),
      goal: Number(r.GoalReached || 0),
      reward: Number(r.RewardZ1 || 0) + Number(r.RewardZ2 || 0),
    }))
    .filter((r) => Number.isFinite(r.ep))
    .sort((a, b) => a.ep - b.ep);
  if (!rows.length) return null;
  return {
    goals: rows.map((r) => r.goal),
    rewards: rows.map((r) => r.reward),
  };
}

function readFirstGoalMean(file) {
  if (!fs.existsSync(file)) return NaN;
  const { records } = readCsv(file);
  return mean(records
    .filter((r) => {
      const idx = String(r.StartStateIndex || "").trim();
      return idx !== "" && !idx.startsWith("#");
    })
    .map((r) => Number(r.FirstGoalEpisode)));
}

function collectLearning(root) {
  const out = new Map();
  let files = 0;
  for (const { seed, dir } of findSeedRoots(root)) {
    for (const prof of ["lab1", "lab2", "lab3"]) {
      for (const stereo of ["true", "false"]) {
        const cellDir = path.join(dir, prof, `training_stereo_${stereo}`);
        const metricsFile = path.join(cellDir, `metrics_stereotypes_${stereo}_${prof}.csv`);
        const metrics = readEpisodeMetrics(metricsFile);
        if (!metrics) continue;
        files++;
        const thr = episodesToThreshold(metrics.goals);
        const fg = readFirstGoalMean(path.join(cellDir, `first_goal_stereotypes_${stereo}_${prof}.csv`));
        out.set(`${prof}|ql_${stereo}|${seed}`, {
          auc_goal: aucNormalised(metrics.goals),
          auc_reward: aucNormalised(metrics.rewards),
          episodes_to_threshold: thr.value,
          mean_first_goal: fg,
        });
      }
    }
  }
  return { out, files };
}

function locator(file, hash, rowNumber, columns) {
  return `local-sha256:${hash}:${file}:row ${rowNumber}; named columns ${columns}`;
}

function addRow(rows, meta, sourceFile, sourceHash, sourceRow, columns, extra) {
  rows.push({
    table_row_id: `P1T-${String(rows.length + 1).padStart(4, "0")}`,
    root_id: meta.rootId,
    run_id: meta.runId,
    branch: meta.branch,
    head_sha: meta.headSha,
    local_root: meta.localRoot,
    local_tree_sha256: meta.treeHash,
    analysis_file: sourceFile,
    analysis_file_sha256: sourceHash,
    analysis_file_row: sourceRow,
    source_locator: locator(sourceFile, sourceHash, sourceRow, columns),
    source_columns: columns,
    research_status: meta.researchStatus,
    evidence_label: meta.evidenceLabel,
    derivation_command: commandText,
    ...extra,
  });
}

function rootTableRows(meta, rows) {
  const bench = collectBenchmark(meta.localRoot);
  const learning = collectLearning(meta.localRoot);

  const summaryFile = path.join(meta.localRoot, "analysis", "out", "summary_table_ci.csv");
  if (fs.existsSync(summaryFile)) {
    const hash = sha256(summaryFile);
    const { records } = readCsv(summaryFile);
    for (const rec of records) {
      const prof = rec.profile;
      const mode = rec.mode;
      for (const metric of metricKeys) {
        const value = toNum(rec[`${metric}_mean`]);
        const vals = findSeedRoots(meta.localRoot)
          .map(({ seed }) => bench.out.get(`${prof}|${mode}|${seed}`)?.[metric])
          .filter((v) => v !== undefined);
        const recomputed = mean(vals);
        addRow(rows, meta, summaryFile, hash, rec.__rowNumber,
          `profile=${prof}; mode=${mode}; n_seeds=${rec.n_seeds}; ${metric}_mean=${rec[`${metric}_mean`]}; ${metric}_ci_lo=${rec[`${metric}_ci_lo`]}; ${metric}_ci_hi=${rec[`${metric}_ci_hi`]}`,
          {
            section: "summary_table_ci",
            data_type: "final_policy_mean",
            profile: prof,
            condition: mode,
            metric,
            n: rec.n_seeds,
            value: rec[`${metric}_mean`],
            ci_lo: rec[`${metric}_ci_lo`],
            ci_hi: rec[`${metric}_ci_hi`],
            recomputed_value: formatNum(recomputed),
            recompute_input: `local-tree-sha256:${meta.treeHash}:${meta.localRoot}; raw benchmark_results CSV files=${bench.files}`,
            recompute_status: closeEnough(value, recomputed) ? "MEAN_MATCH_FROM_RAW" : "MEAN_MISMATCH_OR_NOT_FOUND",
            notes: "CI copied from analysis CSV; bootstrap interval not independently recomputed in Stage 6.",
          });
      }
    }
  }

  const pairedFile = path.join(meta.localRoot, "analysis", "out", "paired_tests.csv");
  if (fs.existsSync(pairedFile)) {
    const hash = sha256(pairedFile);
    const { records } = readCsv(pairedFile);
    for (const rec of records) {
      if (rec.mode_a !== "ql_true" || rec.mode_b !== "ql_false") continue;
      if (!metricKeys.includes(rec.metric)) continue;
      const prof = rec.profile;
      const metric = rec.metric;
      const diffs = findSeedRoots(meta.localRoot)
        .map(({ seed }) => {
          const a = bench.out.get(`${prof}|ql_true|${seed}`)?.[metric];
          const b = bench.out.get(`${prof}|ql_false|${seed}`)?.[metric];
          return a === undefined || b === undefined ? undefined : a - b;
        })
        .filter((v) => v !== undefined);
      const recomputed = mean(diffs);
      const value = toNum(rec.mean_diff);
      addRow(rows, meta, pairedFile, hash, rec.__rowNumber,
        `profile=${prof}; metric=${metric}; mode_a=${rec.mode_a}; mode_b=${rec.mode_b}; family=${rec.family}; n_paired=${rec.n_paired}; mean_diff=${rec.mean_diff}; ci_lo=${rec.ci_lo}; ci_hi=${rec.ci_hi}; p_bootstrap=${rec.p_bootstrap}; q_bootstrap_bh=${rec.q_bootstrap_bh}; cliffs_delta=${rec.cliffs_delta}`,
        {
          section: "paired_tests",
          data_type: "final_policy_paired_difference",
          profile: prof,
          mode_a: rec.mode_a,
          mode_b: rec.mode_b,
          metric,
          n: rec.n_paired,
          seeds: rec.seeds_paired,
          value: rec.mean_diff,
          ci_lo: rec.ci_lo,
          ci_hi: rec.ci_hi,
          p_value: rec.p_bootstrap,
          q_bootstrap_bh: rec.q_bootstrap_bh,
          cliffs_delta: rec.cliffs_delta,
          recomputed_value: formatNum(recomputed),
          recompute_input: `local-tree-sha256:${meta.treeHash}:${meta.localRoot}; raw benchmark_results CSV files=${bench.files}`,
          recompute_status: closeEnough(value, recomputed) ? "MEAN_DIFF_MATCH_FROM_RAW" : "MEAN_DIFF_MISMATCH_OR_NOT_FOUND",
          notes: "p/q/CI copied from analysis CSV; statistical resampling not independently recomputed in Stage 6.",
        });
    }
  }

  const speedFile = path.join(meta.localRoot, "analysis", "out", "learning_speed_tests.csv");
  if (fs.existsSync(speedFile)) {
    const hash = sha256(speedFile);
    const { records } = readCsv(speedFile);
    for (const rec of records) {
      if (!learningMetrics.includes(rec.metric)) continue;
      const prof = rec.profile;
      const metric = rec.metric;
      const diffs = findSeedRoots(meta.localRoot)
        .map(({ seed }) => {
          const a = learning.out.get(`${prof}|ql_true|${seed}`)?.[metric];
          const b = learning.out.get(`${prof}|ql_false|${seed}`)?.[metric];
          return a === undefined || b === undefined ? undefined : a - b;
        })
        .filter((v) => v !== undefined);
      const recomputed = mean(diffs);
      const value = toNum(rec.mean_diff_true_minus_false);
      addRow(rows, meta, speedFile, hash, rec.__rowNumber,
        `profile=${prof}; metric=${metric}; metric_tier=${rec.metric_tier}; direction=${rec.direction}; n_paired=${rec.n_paired}; mean_diff_true_minus_false=${rec.mean_diff_true_minus_false}; ci_lo=${rec.ci_lo}; ci_hi=${rec.ci_hi}; p_one_sided_favorable=${rec.p_one_sided_favorable}; q_bootstrap_bh=${rec.q_bootstrap_bh}; cliffs_delta=${rec.cliffs_delta}`,
        {
          section: "learning_speed_tests",
          data_type: "learning_speed_paired_difference",
          profile: prof,
          metric,
          metric_tier: rec.metric_tier,
          direction: rec.direction,
          n: rec.n_paired,
          seeds: rec.seeds_paired,
          value: rec.mean_diff_true_minus_false,
          ci_lo: rec.ci_lo,
          ci_hi: rec.ci_hi,
          p_value: rec.p_one_sided_favorable,
          q_bootstrap_bh: rec.q_bootstrap_bh,
          cliffs_delta: rec.cliffs_delta,
          recomputed_value: formatNum(recomputed),
          recompute_input: `local-tree-sha256:${meta.treeHash}:${meta.localRoot}; raw training metrics CSV files=${learning.files}`,
          recompute_status: closeEnough(value, recomputed) ? "MEAN_DIFF_MATCH_FROM_RAW" : "MEAN_DIFF_MISMATCH_OR_NOT_FOUND",
          notes: "p/q/CI copied from analysis CSV; statistical resampling not independently recomputed in Stage 6.",
        });
    }
  }

  const speedTableFile = path.join(meta.localRoot, "analysis", "out", "learning_speed_table.csv");
  if (fs.existsSync(speedTableFile)) {
    const hash = sha256(speedTableFile);
    const { records } = readCsv(speedTableFile);
    for (const rec of records) {
      if (!learningMetrics.includes(rec.metric)) continue;
      const prof = rec.profile;
      const condition = rec.condition;
      const metric = rec.metric;
      const vals = findSeedRoots(meta.localRoot)
        .map(({ seed }) => learning.out.get(`${prof}|${condition}|${seed}`)?.[metric])
        .filter((v) => v !== undefined);
      const recomputed = mean(vals);
      const value = toNum(rec.mean);
      addRow(rows, meta, speedTableFile, hash, rec.__rowNumber,
        `profile=${prof}; condition=${condition}; metric=${metric}; metric_tier=${rec.metric_tier}; direction=${rec.direction}; n_seeds=${rec.n_seeds}; mean=${rec.mean}; ci_lo=${rec.ci_lo}; ci_hi=${rec.ci_hi}`,
        {
          section: "learning_speed_table",
          data_type: "learning_speed_condition_mean",
          profile: prof,
          condition,
          metric,
          metric_tier: rec.metric_tier,
          direction: rec.direction,
          n: rec.n_seeds,
          value: rec.mean,
          ci_lo: rec.ci_lo,
          ci_hi: rec.ci_hi,
          recomputed_value: formatNum(recomputed),
          recompute_input: `local-tree-sha256:${meta.treeHash}:${meta.localRoot}; raw training metrics CSV files=${learning.files}`,
          recompute_status: closeEnough(value, recomputed) ? "MEAN_MATCH_FROM_RAW" : "MEAN_MISMATCH_OR_NOT_FOUND",
          notes: "CI copied from analysis CSV; bootstrap interval not independently recomputed in Stage 6.",
        });
    }
  }
}

const rows = [];
for (const meta of roots) {
  rootTableRows(meta, rows);
}
writeCsv(outPath, rows);
console.error(`wrote ${rows.length} rows to ${outPath}`);
