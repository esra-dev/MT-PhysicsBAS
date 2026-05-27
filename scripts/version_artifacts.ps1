<#
.SYNOPSIS
    Snapshots learned artifacts (Q-tables, stereotype TTLs, metrics) from a
    benchmark run into a dedicated `results` branch and tags `main` with a
    timestamped tag. Phase 12 #10.

.DESCRIPTION
    1. Computes a tag name: results-<utc>-<runMode>-<gitShortSha>.
    2. Copies the freshly produced artifacts plus a RUN_MANIFEST.json
       (containing parameters, profiles, modes, and wall-clock timing)
       into a scratch git worktree on the orphan `results` branch.
    3. Commits with a structured message.
    4. Optionally lightweight-tags the current main commit.
    5. Pushes only when -PublishResults is supplied.

.PARAMETER RunMode
    The RunMode used by run_full_project.ps1 (e.g. dev, paper). Embedded in
    the tag name and manifest.

.PARAMETER Profiles
    Comma-separated list of profiles included in this run.

.PARAMETER Modes
    Comma-separated list of bench modes (rule_based, ql_false, ql_true).

.PARAMETER PublishResults
    Push the new commit to origin/results. Default: off (commit locally).

.PARAMETER ResultsBranch
    Override branch name (default: results).

.EXAMPLE
    .\scripts\version_artifacts.ps1 -RunMode dev -Profiles "custom2,custom3" -Modes "ql_true"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$RunMode,
    [Parameter(Mandatory=$true)] [string]$Profiles,
    [string]$Modes = "rule_based,ql_false,ql_true",
    [switch]$PublishResults,
    [string]$ResultsBranch = "results"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

# Verify git repo.
$null = & git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) { throw "version_artifacts: not a git repository: $repoRoot" }

$shortSha  = (& git rev-parse --short HEAD).Trim()
$utcStamp  = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$tagName   = "results-$utcStamp-$RunMode-$shortSha"

Write-Host "version_artifacts: tag=$tagName" -ForegroundColor Cyan

# Stage artifact list.
$candidatePatterns = @(
    "qtable_final_stereotypes_*.csv",
    "qtable_initial_stereotypes_*.csv",
    "learned_stereotypes_*.ttl",
    "metrics_stereotypes_*.csv",
    "iv_stats_stereotypes_*.json",
    "benchmark_results_*.csv",
    "bench_step_log_*.csv"
)

$stageDir = Join-Path ([System.IO.Path]::GetTempPath()) "mt-esra-results-$tagName"
if (Test-Path $stageDir) { Remove-Item -Recurse -Force $stageDir }
New-Item -ItemType Directory -Force -Path $stageDir | Out-Null

$copied = @()
foreach ($pat in $candidatePatterns) {
    Get-ChildItem -Path $repoRoot -Filter $pat -File -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName -Destination $stageDir -Force
        $copied += $_.Name
    }
}
# Also pull benchmark/results subtree (per-cell archived artifacts).
$benchResults = Join-Path $repoRoot "benchmark" "results"
if (Test-Path $benchResults) {
    Copy-Item -Path $benchResults -Destination (Join-Path $stageDir "benchmark_results") -Recurse -Force
    $copied += "benchmark/results/**"
}

# Manifest.
$manifest = [pscustomobject]@{
    tag           = $tagName
    utc           = $utcStamp
    runMode       = $RunMode
    profiles      = ($Profiles -split ',' | ForEach-Object { $_.Trim() })
    bench_modes   = ($Modes -split ',' | ForEach-Object { $_.Trim() })
    git_sha       = (& git rev-parse HEAD).Trim()
    git_short_sha = $shortSha
    git_branch    = (& git rev-parse --abbrev-ref HEAD).Trim()
    artifact_count = $copied.Count
    artifacts     = $copied
    host          = $env:COMPUTERNAME
    user          = $env:USERNAME
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stageDir "RUN_MANIFEST.json") -Encoding UTF8

if ($copied.Count -eq 0) {
    Write-Warning "version_artifacts: no artifacts found to version. Manifest will be committed alone."
}

# Set up worktree on the results branch.
$worktreePath = Join-Path ([System.IO.Path]::GetTempPath()) "mt-esra-results-wt-$tagName"
if (Test-Path $worktreePath) { Remove-Item -Recurse -Force $worktreePath }

$branchExists = (& git ls-remote --exit-code --heads origin $ResultsBranch 2>$null)
if ($LASTEXITCODE -eq 0) {
    & git fetch origin "${ResultsBranch}:${ResultsBranch}" 2>$null
} else {
    # Local-only branch handling.
    $localExists = (& git rev-parse --verify "refs/heads/$ResultsBranch" 2>$null)
}

try {
    if (& git rev-parse --verify "refs/heads/$ResultsBranch" 2>$null) {
        & git worktree add $worktreePath $ResultsBranch
    } else {
        # Create orphan branch.
        & git worktree add --detach $worktreePath HEAD
        Push-Location $worktreePath
        & git checkout --orphan $ResultsBranch
        & git rm -rf . 2>$null | Out-Null
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) { throw "git worktree add failed" }

    $tagDir = Join-Path $worktreePath $tagName
    New-Item -ItemType Directory -Force -Path $tagDir | Out-Null
    Copy-Item -Path (Join-Path $stageDir '*') -Destination $tagDir -Recurse -Force

    Push-Location $worktreePath
    & git add .
    $msg = "results: $tagName ($Profiles | $Modes)"
    & git -c user.email="bot@local" -c user.name="version_artifacts" commit -m $msg | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Nothing to commit on $ResultsBranch."
    } else {
        Write-Host "Committed snapshot to branch '$ResultsBranch'." -ForegroundColor Green
    }

    if ($PublishResults) {
        & git push -u origin $ResultsBranch
        if ($LASTEXITCODE -ne 0) { throw "Push to origin/$ResultsBranch failed." }
        Write-Host "Pushed origin/$ResultsBranch." -ForegroundColor Green
    }
    Pop-Location

    # Tag main commit (lightweight, local).
    & git tag $tagName HEAD
    Write-Host "Tagged HEAD as '$tagName'." -ForegroundColor Green
    if ($PublishResults) {
        & git push origin $tagName
    }
}
finally {
    if (Test-Path $worktreePath) {
        Push-Location $repoRoot
        & git worktree remove --force $worktreePath 2>$null | Out-Null
        Pop-Location
    }
    if (Test-Path $stageDir) { Remove-Item -Recurse -Force $stageDir }
}
