# Download the four Phase-1b PILOT runs into phase1b_pilot/run_<id>/ and
# stamp every run dir PILOT_ONLY. Pilot artifacts are read exclusively via
#   python analysis/phase1b_report.py --pilot-diagnostics ...
# (docs/PHASE1B_POWER_PROTOCOL.md §1).
param(
    [string[]]$RunIds = @("30171111962","30171112970","30171113750","30171114580"),
    [string]$OutRoot = "phase1b_pilot"
)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ScriptRoot)

foreach ($id in $RunIds) {
    $dest = Join-Path $OutRoot "run_$id"
    if (Test-Path $dest) {
        Write-Host "skip $dest (exists)"
        continue
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Write-Host "downloading run $id -> $dest"
    gh run download $id --dir $dest
    if ($LASTEXITCODE -ne 0) { throw "gh run download failed for $id" }
    $mode = (gh run view $id --json displayTitle,databaseId | ConvertFrom-Json).displayTitle
    @{
        marker      = "PILOT_ONLY"
        run_id      = "$id"
        downloaded  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
        note        = "Phase-1b pilot block seeds 1001-1010; never pool with confirmatory results."
    } | ConvertTo-Json | Out-File -Encoding utf8 (Join-Path $dest "PILOT_ONLY.json")
}
Write-Host "done."
