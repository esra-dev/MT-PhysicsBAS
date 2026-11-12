# Curate the Phase-1b extended-arm re-execution seed-half runs into the
# permanent campaign archive phase1b_extended_v3/run_<id>/ (registration
# docs/phase1b_extended_rerun_registration_2026-11-11.md S6):
#   1. gh run download each run's phase1-consolidated artifact into a FRESH
#      staging dir,
#   2. promote analysis/out/... + benchmark/results_seed<N>/... to the run root,
#   3. print the artifact id + digest for the archive manifest,
#   4. write SHA256SUMS.csv via analysis/phase1_archive_inventory.py,
#   5. validate at --stage confirmatory WITH the treatment-delivery gates:
#      --require-effective-props (every TRAINING_OK reports 2.0/5.0/2.0) and
#      --divergence-against the frozen comparator halves (labrel16/labband
#      stereo-true initial Q-tables must differ for every seed).
# The frozen comparator is the locally archived 2026-07 campaign WITH raw
# files (default .worktrees/phase1b-finish/phase1b_corrected relative to the
# main checkout; pass -Comparator explicitly from a worktree).
param(
    [Parameter(Mandatory = $true)][string[]]$RunIds,
    [string]$OutRoot = "phase1b_extended_v3",
    [string]$Comparator = ".worktrees/phase1b-finish/phase1b_corrected",
    [string[]]$FrozenRuns = @("run_30199257204", "run_30199260042")
)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptRoot)
# Interpreter: prefer the Windows launcher (py -3) when present, else python.
$PyCmd = @("python")
if (Get-Command py -ErrorAction SilentlyContinue) { $PyCmd = @("py", "-3") }
function Invoke-Py { if ($PyCmd.Count -gt 1) { & $PyCmd[0] $PyCmd[1] @args } else { & $PyCmd[0] @args } }

$frozen = @()
foreach ($r in $FrozenRuns) {
    $p = Join-Path $Comparator $r
    if (-not (Test-Path (Join-Path $p "analysis\out\workflow_inputs.json"))) { throw "frozen comparator archive missing: $p" }
    $frozen += $p
}

$failed = 0
foreach ($id in $RunIds) {
    $dest = Join-Path $OutRoot "run_$id"
    if (Test-Path (Join-Path $dest "analysis\out\workflow_inputs.json")) {
        Write-Host "skip $dest (already curated)"
    } else {
        $staging = Join-Path $OutRoot "_staging_$id"
        if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
        New-Item -ItemType Directory -Force -Path $staging | Out-Null
        Write-Host "downloading run $id ..."
        gh run download $id --dir $staging --name phase1-consolidated
        if ($LASTEXITCODE -ne 0) { throw "gh run download failed for $id" }
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Move-Item (Join-Path $staging "analysis")  (Join-Path $dest "analysis")
        Move-Item (Join-Path $staging "benchmark") (Join-Path $dest "benchmark")
        Remove-Item -Recurse -Force $staging
        Write-Host "artifact provenance for run $id ..."
        $arts = (gh api "repos/{owner}/{repo}/actions/runs/$id/artifacts" | ConvertFrom-Json).artifacts
        foreach ($a in $arts) { if ($a.name -eq "phase1-consolidated") { Write-Host ("  artifact id {0}  digest {1}  size {2}" -f $a.id, $a.digest, $a.size_in_bytes) } }
    }
    if (-not (Test-Path (Join-Path $dest "SHA256SUMS.csv"))) {
        Write-Host "inventory for run $id ..."
        Invoke-Py analysis/phase1_archive_inventory.py --root $dest --out (Join-Path $dest "SHA256SUMS.csv") --include "analysis/**" --include "benchmark/**"
        if ($LASTEXITCODE -ne 0) { throw "inventory failed for $id" }
    }
    Write-Host "validating run $id (effective-props + initial-Q divergence gates ON) ..."
    Invoke-Py analysis/validate_phase1b_archive.py $dest --stage confirmatory --require-effective-props --divergence-against @frozen
    if ($LASTEXITCODE -ne 0) { $failed++; Write-Host "VALIDATION FAILED: $dest" }
}
if ($failed -gt 0) { throw "$failed archive(s) failed validation" }
Write-Host "all curated extended archives validate with treatment delivery evidenced."
