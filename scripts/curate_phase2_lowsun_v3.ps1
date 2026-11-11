# Curate Phase-2 low-sun re-execution run(s) into the permanent campaign
# archive phase2_v3_lowsun/run_<id>/ (registration
# docs/phase2_lowsun_rerun_registration_2026-11-11.md S7):
#   1. gh run download the phase2-consolidated artifact into a FRESH staging dir,
#   2. promote analysis/out, recovery_root and _artifacts/clean to the run root,
#   3. print the artifact id + digest for ARCHIVE_MANIFEST.md,
#   4. write SHA256SUMS.csv via analysis/phase1_archive_inventory.py,
#   5. validate with the treatment-delivery gate ENABLED (every *_lowsun cell
#      must carry lowsun_pin_delivered=true and Sunshine values [100]).
# The registered analysis then continues with analysis/phase2_lowsun_v3_family.py
# and analysis/reproduce_phase2_lowsun_v3.py.
param(
    [Parameter(Mandatory = $true)][string[]]$RunIds,
    [string]$OutRoot = "phase2_v3_lowsun"
)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptRoot)

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
        gh run download $id --dir $staging --name phase2-consolidated
        if ($LASTEXITCODE -ne 0) { throw "gh run download failed for $id" }
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        foreach ($part in @("analysis", "recovery_root", "_artifacts")) {
            $src = Join-Path $staging $part
            if (-not (Test-Path $src)) { throw "artifact of run $id lacks $part/" }
            Move-Item $src (Join-Path $dest $part)
        }
        Remove-Item -Recurse -Force $staging
        Write-Host "artifact provenance for run $id ..."
        $arts = (gh api "repos/{owner}/{repo}/actions/runs/$id/artifacts" | ConvertFrom-Json).artifacts
        foreach ($a in $arts) { if ($a.name -eq "phase2-consolidated") { Write-Host ("  artifact id {0}  digest {1}  size {2}" -f $a.id, $a.digest, $a.size_in_bytes) } }
        Write-Host "inventory for run $id ..."
        python analysis/phase1_archive_inventory.py --root $dest --out (Join-Path $dest "SHA256SUMS.csv") --include "analysis/**" --include "recovery_root/**" --include "_artifacts/**"
        if ($LASTEXITCODE -ne 0) { throw "inventory failed for $id" }
    }
    $inputs = Get-Content -Raw (Join-Path $dest "analysis\out\workflow_inputs.json") | ConvertFrom-Json
    $profiles = $inputs.profiles
    if ($profiles -is [array]) { $profiles = $profiles -join "," }
    $seeds = $inputs.seeds
    if ($seeds -is [array]) { $seeds = $seeds -join "," }
    Write-Host "validating run $id (treatment-delivery gate ON) ..."
    python analysis/validate_phase2_v2_archive.py $dest --profiles $profiles --seeds $seeds --require-treatment-delivery
    if ($LASTEXITCODE -ne 0) { $failed++; Write-Host "VALIDATION FAILED: $dest" }
}
if ($failed -gt 0) { throw "$failed archive(s) failed validation" }
Write-Host "all curated low-sun archives validate with treatment delivery evidenced."
