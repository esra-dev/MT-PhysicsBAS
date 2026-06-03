# =============================================================================
# Audit Step 0 - Probe A v3: H5 ablation (post S0-3 fix)
#
# Hypothesis H5 (pre-reg): setting stereo_prior_scale = 0 should make ql_true
# statistically indistinguishable from ql_false. Pre-S0-3 this was impossible
# because initWithStereotypes() installed negative ontology penalties
# independent of the scale parameter. S0-3 (2026-06-03) gates init on
# STEREO_PRIOR_SCALE > 0, so this probe is now testable.
#
# Protocol:
#   1. Backup config/run_config.json
#   2. Inject/overwrite learning.stereo_prior_scale = 0.0
#   3. Run -RunMode dev -OnlyProfiles custom8 for seeds 1, 2, 3
#   4. For each seed, compute mean(GoalReached) for ql_true and ql_false from
#      benchmark_results_ql_{true,false}.csv; report per-seed delta
#   5. Restore config/run_config.json (in finally{})
#
# PASS criterion (per arm, per seed):
#   |mean(ql_true) - mean(ql_false)| < SigmaWithinTol
#
# SigmaWithinTol defaults to 0.05 (5 pp goal-rate band) but should be set to
# the sigma_within measured by run_step0_optB.ps1 once that is run.
#
# Cost: 3 full-project runs ~ 15-25 min.
# ASCII-only output for PS5.1 compatibility.
# =============================================================================
[CmdletBinding()]
param(
    [double]$SigmaWithinTol = 0.05,
    [int[]]$Seeds = @(1,2,3)
)

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
        'first_goal_stereotypes_*_custom8.csv','coverage_stereotypes_*_custom8.csv',
        'qtable_final_stereotypes_*_custom8*.csv','learned_stereotypes_*_custom8.ttl')) {
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

# --------------- Phase 0: backup config and inject scale=0 ---------------
$cfgPath = Join-Path $PSScriptRoot 'config\run_config.json'
$bakPath = "$cfgPath.bak"
if (-not (Test-Path -LiteralPath $cfgPath)) {
    throw "config\run_config.json not found at $cfgPath"
}
Write-Host "==== Probe A v3: H5 ablation (stereo_prior_scale=0, S0-3 active) ====" -ForegroundColor Yellow
Write-Host "Tolerance (SigmaWithinTol): $SigmaWithinTol  | Seeds: $($Seeds -join ',')" -ForegroundColor Yellow

Copy-Item -LiteralPath $cfgPath -Destination $bakPath -Force
Write-Host "Backed up run_config.json -> $bakPath" -ForegroundColor DarkGray

try {
    # Read, mutate, write
    $cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($null -eq $cfg.learning) {
        $cfg | Add-Member -NotePropertyName learning -NotePropertyValue ([pscustomobject]@{}) -Force
    }
    $cfg.learning | Add-Member -NotePropertyName stereo_prior_scale -NotePropertyValue 0.0 -Force
    ($cfg | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $cfgPath -Encoding UTF8
    Write-Host "Injected learning.stereo_prior_scale = 0.0 into run_config.json" -ForegroundColor Green

    # --------------- Phase 1: runs ---------------
    $arc = "tmp_step0_probeA_v3"
    if (Test-Path $arc) { Remove-Item $arc -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $arc | Out-Null

    foreach ($s in $Seeds) {
        Write-Host "`n--- Probe A v3: seed $s (scale=0) ---" -ForegroundColor Cyan
        Clear-RunState
        .\run_full_project.ps1 -RunMode dev -OnlyProfiles custom8 -RunSeed $s
        Copy-RunArtefacts -Dst (Join-Path $arc "seed$s")
    }

    # --------------- Phase 2: aggregate and gate ---------------
    Write-Host "`n==== Probe A v3: aggregation ====" -ForegroundColor Yellow
    $rows = @()
    foreach ($s in $Seeds) {
        $d  = Join-Path $arc "seed$s"
        $gT = Get-GoalRate (Join-Path $d 'benchmark_results_ql_true.csv')
        $gF = Get-GoalRate (Join-Path $d 'benchmark_results_ql_false.csv')
        $delta   = if ($null -ne $gT -and $null -ne $gF) { $gT - $gF } else { $null }
        $absDelta = if ($null -ne $delta) { [Math]::Abs($delta) } else { $null }
        $verdict = if ($null -ne $absDelta -and $absDelta -lt $SigmaWithinTol) { 'PASS' } else { 'FAIL' }
        $rows += [pscustomobject]@{
            Seed     = $s
            ql_true  = $gT
            ql_false = $gF
            Delta    = $delta
            AbsDelta = $absDelta
            Verdict  = $verdict
        }
    }
    $rows | Format-Table -AutoSize | Out-String |
        Tee-Object -FilePath (Join-Path $arc 'h5_deltas.txt')

    $allPass = ($rows | Where-Object { $_.Verdict -ne 'PASS' } | Measure-Object).Count -eq 0
    $hasNull = ($rows | Where-Object { $null -eq $_.AbsDelta } | Measure-Object).Count -gt 0

    $overall = if ($hasNull) {
        'INDETERMINATE - one or more runs produced no benchmark CSV'
    } elseif ($allPass) {
        "PASS - all per-seed |ql_true - ql_false| < $SigmaWithinTol -> H5 supported (within tolerance)"
    } else {
        "FAIL - at least one seed exceeds tolerance -> H5 falsified or tolerance too tight"
    }

    $deltas = $rows | Where-Object { $null -ne $_.AbsDelta } | ForEach-Object { $_.AbsDelta }
    $meanAbs = if ($deltas.Count -gt 0) { ($deltas | Measure-Object -Average).Average } else { [double]::NaN }
    $maxAbs  = if ($deltas.Count -gt 0) { ($deltas | Measure-Object -Maximum).Maximum } else { [double]::NaN }

    $summary = @"

=== Probe A v3: H5 ablation verdict ===
Profile: custom8, RunMode: dev
Config:  learning.stereo_prior_scale = 0.0 (injected; restored after run)
Code:    S0-3 (initWithStereotypes() bypassed when scale==0) active
Seeds:   $($Seeds -join ',')
Tol:     SigmaWithinTol = $SigmaWithinTol

Per-seed |ql_true - ql_false|:  mean = {0:F4}   max = {1:F4}

Overall: {2}

Interpretation:
  - PASS means ql_true collapsed onto ql_false within timing noise, as
    predicted by H5. The stereotype-driven advantage on custom8 is entirely
    explained by the prior + init, not by any structural code-path difference.
  - FAIL means a residual difference remains even after removing both the
    soft prior (scale=0) and the init bias (S0-3). Possible causes: hidden
    ql_true / ql_false divergence in agent ASL plans, calibration MA paths,
    or tolerance set tighter than actual sigma_within.

Next steps if FAIL:
  - First, confirm sigma_within from run_step0_optB.ps1; re-run this probe
    with -SigmaWithinTol <measured value>.
  - If still FAIL, grep src/agt for `stereotypes_mode` branches that fire
    independently of priorScale.
"@ -f $meanAbs, $maxAbs, $overall

    $color = if ($overall -like 'PASS*') { 'Green' } elseif ($overall -like 'FAIL*') { 'Red' } else { 'Yellow' }
    Write-Host $summary -ForegroundColor $color
    $summary | Out-File -FilePath (Join-Path $arc 'verdict.txt') -Encoding ASCII

    Write-Host "`nArtefacts: $arc\{h5_deltas.txt, verdict.txt, seed{$($Seeds -join ',')}\}"
    Write-Host "Paste back: $arc\verdict.txt and $arc\h5_deltas.txt"
}
finally {
    if (Test-Path -LiteralPath $bakPath) {
        Move-Item -LiteralPath $bakPath -Destination $cfgPath -Force
        Write-Host "`nRestored run_config.json from backup." -ForegroundColor Green
    } else {
        Write-Host "`nWARNING: backup file $bakPath missing - config NOT restored!" -ForegroundColor Red
    }
}
