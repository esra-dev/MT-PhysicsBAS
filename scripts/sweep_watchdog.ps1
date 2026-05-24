<#
.SYNOPSIS
    Inspect the most recent GitHub Actions runs of the paper-mode sweep and
    print a compact health report suitable for the thesis appendix.

.DESCRIPTION
    Uses the `gh` CLI (https://cli.github.com/) which must be authenticated.
    For each of the recent runs of `sweep-paper.yml` (and optionally
    `sweep-ablation.yml`), prints:

        - run id, status, conclusion, age
        - failed job names with their web URLs (for quick triage)
        - per-seed completion ratio (train + bench cells expected vs. uploaded)

    No GitHub API token is hard-coded; `gh` handles authentication.

.PARAMETER Workflow
    Workflow file name(s) to inspect. Defaults to the two sweep workflows.

.PARAMETER Limit
    Number of most-recent runs to inspect per workflow. Default 5.

.PARAMETER Seeds
    Number of seeds the most recent run is expected to have (default 5).
    Used to compute per-seed coverage.

.PARAMETER Profiles
    Number of profiles to expect (default 7: custom2..custom8).

.EXAMPLE
    pwsh ./scripts/sweep_watchdog.ps1

.EXAMPLE
    pwsh ./scripts/sweep_watchdog.ps1 -Limit 3 -Seeds 5

.NOTES
    Exits 0 if all inspected runs succeeded; exits 1 if any run failed or is
    still in_progress past the expected window.
#>

[CmdletBinding()]
param(
    [string[]] $Workflow = @('sweep-paper.yml', 'sweep-ablation.yml'),
    [int]      $Limit    = 5,
    [int]      $Seeds    = 5,
    [int]      $Profiles = 7
)

$ErrorActionPreference = 'Stop'

# Verify gh CLI is available and authenticated.
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Error "gh CLI not found on PATH. Install from https://cli.github.com/"
    exit 2
}
$null = & gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "gh CLI is not authenticated. Run: gh auth login"
    exit 2
}

$exitCode = 0

foreach ($wf in $Workflow) {
    Write-Host "=== Workflow: $wf ===" -ForegroundColor Cyan
    $raw = & gh run list --workflow=$wf --limit $Limit `
        --json 'databaseId,status,conclusion,createdAt,headBranch,event,displayTitle,url' 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        Write-Warning "No runs (or no permission) for workflow $wf"
        continue
    }
    $runs = $raw | ConvertFrom-Json
    if (-not $runs) {
        Write-Host "  (no recent runs)" -ForegroundColor DarkGray
        continue
    }

    foreach ($r in $runs) {
        $created = [datetime]$r.createdAt
        $ageMin  = [int]((Get-Date).ToUniversalTime() - $created.ToUniversalTime()).TotalMinutes
        $tag = switch ($r.conclusion) {
            'success'   { '[OK]   ' }
            'failure'   { '[FAIL] ' }
            'cancelled' { '[CAN]  ' }
            $null       { if ($r.status -eq 'in_progress') { '[RUN]  ' } else { '[?]    ' } }
            default     { "[$($r.conclusion)] " }
        }
        Write-Host ("  {0}#{1}  age={2}min  {3}  ({4})" -f `
            $tag, $r.databaseId, $ageMin, $r.displayTitle, $r.url)

        if ($r.conclusion -eq 'failure') {
            $exitCode = 1
            $jobsJson = & gh run view $r.databaseId --json 'jobs' 2>$null
            if ($LASTEXITCODE -eq 0 -and $jobsJson) {
                $jobs = ($jobsJson | ConvertFrom-Json).jobs
                $failed = $jobs | Where-Object { $_.conclusion -eq 'failure' }
                foreach ($j in $failed) {
                    Write-Host ("      x {0}  ->  {1}" -f $j.name, $j.url) -ForegroundColor Red
                }
            }
        } elseif ($r.status -eq 'in_progress' -and $ageMin -gt 360) {
            # Sweeps shouldn't take more than ~6 hours; flag stuck runs.
            Write-Warning ("Run #{0} running for {1} min (>6h); inspect for stuck jobs" -f $r.databaseId, $ageMin)
            $exitCode = 1
        }
    }

    # Coverage check for the most recent run only.
    $mostRecent = $runs[0]
    if ($wf -eq 'sweep-paper.yml' -and $mostRecent.conclusion -in @('success', 'failure', 'cancelled')) {
        $expectedTrain = $Profiles * 2 * $Seeds      # stereo true/false * seeds
        $expectedBench = $Profiles * 3 * $Seeds      # 3 modes * seeds
        Write-Host ("  expected artefacts: train={0}, bench={1}" -f `
            $expectedTrain, $expectedBench) -ForegroundColor DarkGray

        $artsJson = & gh run view $mostRecent.databaseId --json 'artifacts' 2>$null
        if ($LASTEXITCODE -eq 0 -and $artsJson) {
            $arts = ($artsJson | ConvertFrom-Json).artifacts
            $trainArts = @($arts | Where-Object { $_.name -like 'train-*-seed-*' })
            $benchArts = @($arts | Where-Object { $_.name -like 'bench-*-seed-*' })
            $tColor = if ($trainArts.Count -ge $expectedTrain) { 'Green' } else { 'Yellow' }
            $bColor = if ($benchArts.Count -ge $expectedBench) { 'Green' } else { 'Yellow' }
            Write-Host ("  uploaded:           train={0}, bench={1}" -f `
                $trainArts.Count, $benchArts.Count) -ForegroundColor $tColor
            if ($trainArts.Count -lt $expectedTrain -or $benchArts.Count -lt $expectedBench) {
                Write-Host "  (incomplete coverage; rerun missing cells)" -ForegroundColor $bColor
            }
        }
    }
}

exit $exitCode
