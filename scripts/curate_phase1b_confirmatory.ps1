# Curate the eight Phase-1b confirmatory seed-half runs into the permanent
# campaign archive phase1b_corrected/run_<id>/ :
#   1. gh run download each run into a staging dir,
#   2. promote the phase1-consolidated artifact to the run root
#      (analysis/out/... + benchmark/results_seed<N>/...),
#   3. write SHA256SUMS.csv via analysis/phase1_archive_inventory.py,
#   4. validate every archive at --stage confirmatory.
# Registered gates (registration 2026-07-26 S6) then continue with
# phase1b_report.py + reproduce_phase1b.py.
param(
    [string[]]$RunIds = @("30199243656","30199247467","30199251189","30199254246",
                          "30199257204","30199260042","30199263213","30199266427"),
    [string]$OutRoot = "phase1b_corrected"
)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptRoot)

$failed = 0
foreach ($id in $RunIds) {
    $dest = Join-Path $OutRoot "run_$id"
    if (Test-Path (Join-Path $dest "analysis\out\workflow_inputs.json")) {
        Write-Host "skip $dest (already curated)"
        continue
    }
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
    Write-Host "inventory for run $id ..."
    python analysis/phase1_archive_inventory.py --root $dest --out (Join-Path $dest "SHA256SUMS.csv") --include "analysis/**" --include "benchmark/**"
    if ($LASTEXITCODE -ne 0) { throw "inventory failed for $id" }
    Write-Host "validating run $id ..."
    python analysis/validate_phase1b_archive.py $dest --stage confirmatory
    if ($LASTEXITCODE -ne 0) { $failed++; Write-Host "VALIDATION FAILED: $dest" }
}
if ($failed -gt 0) { throw "$failed archive(s) failed validation" }
Write-Host "all curated archives validate (confirmatory)."
