param(
    [string]$ObservedAtUtc = ([DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ"))
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom

function Invoke-CaptureCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )

    $output = & $FilePath @ArgumentList 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $FilePath $($ArgumentList -join ' ')`n$($output -join "`n")"
    }
    return ,@($output | ForEach-Object { $_.ToString() })
}

function Quote-CsvField {
    param([AllowNull()][object]$Value)
    if ($null -eq $Value) { return '""' }
    return '"' + ($Value.ToString() -replace '"', '""') + '"'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stamp = ([DateTime]::Parse($ObservedAtUtc).ToUniversalTime()).ToString("yyyyMMddTHHmmssZ")
$actionsJsonPath = Join-Path $PSScriptRoot "ACTIONS_RUNS_$stamp.json"
$actionsCsvPath = Join-Path $PSScriptRoot "ACTIONS_RUNS_$stamp.csv"
$gitAuditPath = Join-Path $PSScriptRoot "GIT_AUDIT_$stamp.txt"
$runLedgerPath = Join-Path $PSScriptRoot "RUN_LEDGER.csv"

foreach ($path in @($actionsJsonPath, $actionsCsvPath, $gitAuditPath)) {
    if (Test-Path -LiteralPath $path) {
        throw "Refusing to overwrite existing capture: $path"
    }
}

Push-Location $repoRoot
try {
    $actionsArgs = @(
        "run", "list",
        "--repo", "esra-dev/MT-PhysicsBAS",
        "--limit", "300",
        "--json", "databaseId,workflowName,displayTitle,event,status,conclusion,headBranch,headSha,attempt,createdAt,updatedAt,url"
    )
    $actionsJson = (Invoke-CaptureCommand -FilePath "gh" -ArgumentList $actionsArgs) -join "`n"
    [IO.File]::WriteAllText($actionsJsonPath, $actionsJson + "`n", $utf8NoBom)

    $parsedActions = $actionsJson | ConvertFrom-Json
    $actions = @($parsedActions | ForEach-Object { $_ } | Sort-Object createdAt, databaseId)
    $actions | Select-Object databaseId, workflowName, displayTitle, event, status,
        conclusion, headBranch, headSha, attempt, createdAt, updatedAt, url |
        Export-Csv -LiteralPath $actionsCsvPath -NoTypeInformation -Encoding UTF8

    $refs = @(
        "main",
        "origin/main",
        "feature/qlearning-stereotype-comparison",
        "kg-crosszone-coupling",
        "kg-crosszone-coupling-bump",
        "kg-crosszone-ablation",
        "phase2-fault-detection",
        "origin/results"
    )

    $audit = New-Object System.Collections.Generic.List[string]
    $audit.Add("observed_at_utc=$ObservedAtUtc")
    $audit.Add("repository=https://github.com/esra-dev/MT-PhysicsBAS.git")
    $audit.Add("capture_command=./paper_notes/STAGE2_CAPTURE.ps1 -ObservedAtUtc '$ObservedAtUtc'")
    $audit.Add("")
    $audit.Add("[REFS]")
    foreach ($ref in $refs) {
        $sha = (Invoke-CaptureCommand -FilePath "git" -ArgumentList @("rev-parse", $ref))[0]
        $audit.Add("$ref`t$sha")
    }
    $audit.Add("")
    $audit.Add("[MERGE_BASES_AGAINST_LOCAL_MAIN]")
    foreach ($ref in $refs | Where-Object { $_ -ne "origin/results" }) {
        $mergeBase = (Invoke-CaptureCommand -FilePath "git" -ArgumentList @("merge-base", "main", $ref))[0]
        $counts = (Invoke-CaptureCommand -FilePath "git" -ArgumentList @("rev-list", "--left-right", "--count", "main...$ref"))[0]
        $audit.Add("$ref`tmerge_base=$mergeBase`tmain...ref=$counts")
    }
    $audit.Add("")
    $audit.Add("[COMMITS]")
    $audit.AddRange([string[]](Invoke-CaptureCommand -FilePath "git" -ArgumentList @(
        "log", "--all", "--topo-order", "--date=iso-strict",
        "--pretty=format:%H`t%P`t%ad`t%an`t%D`t%s"
    )))
    $audit.Add("")
    $audit.Add("[TAGS]")
    $audit.AddRange([string[]](Invoke-CaptureCommand -FilePath "git" -ArgumentList @(
        "for-each-ref", "--sort=creatordate",
        "--format=%(refname:short)`t%(objecttype)`t%(objectname)`t%(*objectname)`t%(creatordate:iso-strict)`t%(subject)",
        "refs/tags"
    )))
    [IO.File]::WriteAllLines($gitAuditPath, $audit, $utf8NoBom)

    $existingIds = @{}
    foreach ($row in (Import-Csv -LiteralPath $runLedgerPath)) {
        $existingIds[$row.run_id] = $true
    }

    $header = (Get-Content -LiteralPath $runLedgerPath -TotalCount 1) -split ','
    $newLines = New-Object System.Collections.Generic.List[string]
    foreach ($run in $actions) {
        $id = $run.databaseId.ToString()
        if ($existingIds.ContainsKey($id)) { continue }

        $phase = switch ($run.workflowName) {
            "Phase 1 (KG acceleration, clean labs)" { "PHASE1" }
            "Phase 2 (fault detection, blacklist, re-learn)" { "PHASE2" }
            "Sweep (paper)" { "PRE_PIVOT" }
            "Sweep (ablation)" { "PRE_PIVOT_ABLATION" }
            default { "ENGINEERING" }
        }
        $researchStatus = if ($phase -eq "ENGINEERING") { "ENGINEERING_VALIDATION" } else { "UNRESOLVED" }
        $values = [ordered]@{
            run_id = $id
            stage = "2"
            phase = $phase
            experiment_label = $run.displayTitle
            workflow = $run.workflowName
            run_url = $run.url
            event = $run.event
            status = $run.status
            conclusion = $run.conclusion
            head_branch = $run.headBranch
            head_sha = $run.headSha
            run_attempt = $run.attempt
            created_at_utc = $run.createdAt
            updated_at_utc = $run.updatedAt
            job_name = "NOT FOUND"
            job_id = "NOT FOUND"
            job_url = "NOT FOUND"
            artifact_name = "NOT FOUND"
            artifact_id = "NOT FOUND"
            artifact_digest = "NOT FOUND"
            artifact_count = "NOT FOUND"
            local_root = "NOT FOUND"
            local_tree_hash = "NOT FOUND"
            provenance_status = "ACTIONS_RUN_METADATA_ONLY"
            research_status = $researchStatus
            observed_at_utc = $ObservedAtUtc
            notes = "Public Actions run-list snapshot $([IO.Path]::GetFileName($actionsJsonPath)); job and artifact details were not batch-resolved."
        }
        $newLines.Add((($header | ForEach-Object { Quote-CsvField $values[$_] }) -join ','))
        $existingIds[$id] = $true
    }

    if ($newLines.Count -gt 0) {
        [IO.File]::AppendAllLines($runLedgerPath, $newLines, $utf8NoBom)
    }

    Write-Output "observed_at_utc=$ObservedAtUtc"
    Write-Output "actions_json=$actionsJsonPath"
    Write-Output "actions_csv=$actionsCsvPath"
    Write-Output "git_audit=$gitAuditPath"
    Write-Output "visible_actions_runs=$($actions.Count)"
    Write-Output "run_ledger_rows_appended=$($newLines.Count)"
}
finally {
    Pop-Location
}
