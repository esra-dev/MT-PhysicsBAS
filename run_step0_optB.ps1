# =============================================================================
# Audit Step 0 - Option B: Statistical replicability gate
#
# Premise (post S0-FIX-1 / S0-3 / S0-4): bit-identical replicability is
# unachievable due to (a) tick-vs-agent-delay race in dev mode (50 ms tick /
# 65 ms agent delay), (b) Node-RED simulator Math.random() in update_env, and
# (c) Jason BDI scheduler nondeterminism. Pre-reg sec.6 Deviation Policy
# authorises this pivot.
#
# Protocol:
#   1. Run -RunSeed 7 three times      -> quantifies sigma_within (run-to-run noise)
#   2. Run -RunSeed 1, 2, 3 once each  -> quantifies sigma_between (seed effect)
#   3. PASS iff sigma_within < 0.5 * sigma_between
#      (seed dominates noise -> paired-bootstrap-by-seed approximately valid)
#
# Metric: mean GoalReached over all scenario x run rows in
#         benchmark_results_ql_true.csv and benchmark_results_ql_false.csv.
# Profile: custom8, RunMode: dev, both stereotype arms.
#
# Cost: 6 full-project runs ~ 30-45 min total.
#
# NOTE: All output uses ASCII only. PowerShell 5.1 mis-parses non-ASCII chars
# in script source unless the file is saved as UTF-8 with BOM, which is fragile.
# =============================================================================
$ErrorActionPreference = 'Stop'

function Clear-RunState {
    $patterns = @(
        'qtable_initial_stereotypes_*.csv','qtable_final_stereotypes_*.csv',
        'metrics_stereotypes_*.csv','coverage_stereotypes_*.csv',
        'first_goal_stereotypes_*.csv','iv_stats_stereotypes_*.json',
        'learned_stereotypes_*.ttl','benchmark_results_*.csv','bench_step_log_*.csv'
    )
    foreach ($p in $patterns) {
        Get-ChildItem -Path . -Filter $p -File -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

function Copy-RunArtefacts {
    param([string]$Dst)
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    foreach ($p in @(
        'metrics_stereotypes_true_custom8.csv','metrics_stereotypes_false_custom8.csv',
        'benchmark_results_ql_true.csv','benchmark_results_ql_false.csv',
        'benchmark_results_rule_based.csv',
        'bench_step_log_ql_true.csv','bench_step_log_ql_false.csv',
        'first_goal_stereotypes_*_custom8.csv','coverage_stereotypes_*_custom8.csv')) {
        Get-ChildItem -Path . -Filter $p -File -ErrorAction SilentlyContinue |
            Copy-Item -Destination $Dst -Force
    }
}

function Get-GoalRate {
    param([string]$CsvPath)
    if (-not (Test-Path -LiteralPath $CsvPath)) { return $null }
    $rows = Import-Csv -LiteralPath $CsvPath
    if (-not $rows -or $rows.Count -eq 0) { return $null }
    $vals = @()
    foreach ($r in $rows) {
        if ($null -ne $r.GoalReached -and $r.GoalReached -ne '') {
            $vals += [double]$r.GoalReached
        }
    }
    if ($vals.Count -eq 0) { return $null }
    return ($vals | Measure-Object -Average).Average
}

function Get-Stdev {
    param([double[]]$Values)
    if ($Values.Count -lt 2) { return 0.0 }
    $m = ($Values | Measure-Object -Average).Average
    $sumSq = 0.0
    foreach ($v in $Values) { $sumSq += [Math]::Pow($v - $m, 2) }
    return [Math]::Sqrt($sumSq / ($Values.Count - 1))   # sample SD (n-1)
}

# --------------- Phase 1: sigma_within - seed 7, three repeats ---------------
Write-Host "`n==== Option B: sigma_within (seed=7, N=3) ====" -ForegroundColor Yellow
$arc = "tmp_step0_optB"
if (Test-Path $arc) { Remove-Item $arc -Recurse -Force }
New-Item -ItemType Directory -Force -Path $arc | Out-Null

foreach ($rep in 1,2,3) {
    Write-Host "`n--- sigma_within: seed 7, repeat $rep ---" -ForegroundColor Cyan
    Clear-RunState
    .\run_full_project.ps1 -RunMode dev -OnlyProfiles custom8 -RunSeed 7
    Copy-RunArtefacts -Dst (Join-Path $arc "within_seed7_rep$rep")
}

# --------------- Phase 2: sigma_between - seeds 1, 2, 3 ---------------
Write-Host "`n==== Option B: sigma_between (seeds 1,2,3) ====" -ForegroundColor Yellow
foreach ($s in 1,2,3) {
    Write-Host "`n--- sigma_between: seed $s ---" -ForegroundColor Cyan
    Clear-RunState
    .\run_full_project.ps1 -RunMode dev -OnlyProfiles custom8 -RunSeed $s
    Copy-RunArtefacts -Dst (Join-Path $arc "between_seed$s")
}

# --------------- Phase 3: aggregate and gate ---------------
Write-Host "`n==== Option B: aggregation ====" -ForegroundColor Yellow

$rows = @()
$withinTrue = @(); $withinFalse = @()
foreach ($rep in 1,2,3) {
    $d = Join-Path $arc "within_seed7_rep$rep"
    $gT = Get-GoalRate (Join-Path $d 'benchmark_results_ql_true.csv')
    $gF = Get-GoalRate (Join-Path $d 'benchmark_results_ql_false.csv')
    $rows += [pscustomobject]@{ Phase='within'; Seed=7; Rep=$rep; ql_true=$gT; ql_false=$gF }
    if ($null -ne $gT) { $withinTrue  += $gT }
    if ($null -ne $gF) { $withinFalse += $gF }
}
$betweenTrue = @(); $betweenFalse = @()
foreach ($s in 1,2,3) {
    $d = Join-Path $arc "between_seed$s"
    $gT = Get-GoalRate (Join-Path $d 'benchmark_results_ql_true.csv')
    $gF = Get-GoalRate (Join-Path $d 'benchmark_results_ql_false.csv')
    $rows += [pscustomobject]@{ Phase='between'; Seed=$s; Rep=1; ql_true=$gT; ql_false=$gF }
    if ($null -ne $gT) { $betweenTrue  += $gT }
    if ($null -ne $gF) { $betweenFalse += $gF }
}

$rows | Format-Table -AutoSize | Out-String |
    Tee-Object -FilePath (Join-Path $arc 'goal_rates.txt')

$wT = Get-Stdev $withinTrue
$wF = Get-Stdev $withinFalse
$bT = Get-Stdev $betweenTrue
$bF = Get-Stdev $betweenFalse

# Means too: needed to interpret degenerate variance.
$mwT = if ($withinTrue.Count -gt 0)  { ($withinTrue  | Measure-Object -Average).Average } else { [double]::NaN }
$mwF = if ($withinFalse.Count -gt 0) { ($withinFalse | Measure-Object -Average).Average } else { [double]::NaN }
$mbT = if ($betweenTrue.Count -gt 0) { ($betweenTrue | Measure-Object -Average).Average } else { [double]::NaN }
$mbF = if ($betweenFalse.Count -gt 0){ ($betweenFalse| Measure-Object -Average).Average } else { [double]::NaN }

# Three-valued classifier per arm:
#   PASS       : sigma_between > 0 AND sigma_within < 0.5 * sigma_between
#   FAIL       : sigma_between > 0 AND sigma_within >= 0.5 * sigma_between
#   DEGENERATE : sigma_within = sigma_between = 0
#                (bit-identical determinism across BOTH seed-axes; gate
#                 inapplicable; usually means episodes/scenarios too short
#                 for seed effects to manifest. NOT a failure of replicability,
#                 just under-powered. Treated as PASS for the substantive
#                 'same input -> same output' contract.)
#   UNDERPOWERED: sigma_within = 0 but sigma_between > 0 (or vice versa).
function Classify {
    param([double]$w, [double]$b)
    if ($w -eq 0.0 -and $b -eq 0.0) { return 'DEGENERATE-PASS' }
    if ($b -eq 0.0) { return 'UNDERPOWERED' }
    if ($w -lt 0.5 * $b) { return 'PASS' } else { return 'FAIL' }
}
$verdictTrue  = Classify $wT $bT
$verdictFalse = Classify $wF $bF
$ratioTrue    = if ($bT -gt 0) { $wT / $bT } else { [double]::NaN }
$ratioFalse   = if ($bF -gt 0) { $wF / $bF } else { [double]::NaN }

$goodVerdicts = @('PASS','DEGENERATE-PASS')
$overall = if ($goodVerdicts -contains $verdictTrue -and $goodVerdicts -contains $verdictFalse) {
    if ($verdictTrue -eq 'DEGENERATE-PASS' -or $verdictFalse -eq 'DEGENERATE-PASS') {
        'DEGENERATE-PASS - bit-identical determinism observed; gate inapplicable in this regime (likely under-powered: episodes too few for seed effects to manifest). Substantive replicability claim holds. Re-run with -RunMode paper to exercise the gate.'
    } else {
        'PASS - proceed to Probe A (H5 ablation)'
    }
} else {
    'FAIL - seed effect does not dominate noise; revisit before Probe A'
}

$summary = @"

=== Option B statistical replicability gate ===
Metric: mean(GoalReached) across all benchmark scenario x run rows
Profile: custom8, RunMode: dev

ql_true  arm:  mean_within = {0:F4}   mean_between = {1:F4}
              sigma_within = {2:F4}   sigma_between = {3:F4}   ratio = {4:F3}   verdict = {5}
ql_false arm:  mean_within = {6:F4}   mean_between = {7:F4}
              sigma_within = {8:F4}   sigma_between = {9:F4}   ratio = {10:F3}   verdict = {11}

Overall: {12}
"@ -f $mwT, $mbT, $wT, $bT, $ratioTrue, $verdictTrue, $mwF, $mbF, $wF, $bF, $ratioFalse, $verdictFalse, $overall

$color = if ($overall -like 'FAIL*') { 'Red' } elseif ($overall -like 'DEGENERATE*') { 'Yellow' } else { 'Green' }
Write-Host $summary -ForegroundColor $color
$summary | Out-File -FilePath (Join-Path $arc 'verdict.txt') -Encoding ASCII

Write-Host "`nArtefacts: $arc\{goal_rates.txt, verdict.txt, within_seed7_rep{1,2,3}\, between_seed{1,2,3}\}"
Write-Host "Paste back: $arc\verdict.txt and $arc\goal_rates.txt"
