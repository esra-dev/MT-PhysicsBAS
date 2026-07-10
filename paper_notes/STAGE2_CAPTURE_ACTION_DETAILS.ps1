param(
    [Parameter(Mandatory = $true)]
    [string]$ObservedAtUtc,

    [Parameter(Mandatory = $true)]
    [long[]]$RunIds
)

$stamp = ([datetimeoffset]::Parse($ObservedAtUtc)).UtcDateTime.ToString('yyyyMMddTHHmmssZ')
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repository = 'esra-dev/MT-PhysicsBAS'

$runs = @()
$jobs = @()
$artifacts = @()
$errors = @()

foreach ($runId in $RunIds) {
    try {
        $run = gh api "repos/$repository/actions/runs/$runId" | ConvertFrom-Json
        $runs += [pscustomobject]@{
            observedAtUtc = $ObservedAtUtc
            runId = $run.id
            workflowId = $run.workflow_id
            name = $run.name
            event = $run.event
            status = $run.status
            conclusion = $run.conclusion
            headBranch = $run.head_branch
            headSha = $run.head_sha
            runAttempt = $run.run_attempt
            createdAt = $run.created_at
            updatedAt = $run.updated_at
            url = $run.html_url
        }
    } catch {
        $errors += [pscustomobject]@{ runId = $runId; endpoint = 'run'; error = $_.Exception.Message }
    }

    try {
        $jobResponse = gh api "repos/$repository/actions/runs/$runId/jobs?per_page=100" | ConvertFrom-Json
        foreach ($job in @($jobResponse.jobs)) {
            if ($null -eq $job) { continue }
            foreach ($step in @($job.steps)) {
                $jobs += [pscustomobject]@{
                    observedAtUtc = $ObservedAtUtc
                    runId = $runId
                    jobId = $job.id
                    jobName = $job.name
                    jobStatus = $job.status
                    jobConclusion = $job.conclusion
                    jobUrl = $job.html_url
                    runnerName = $job.runner_name
                    stepNumber = $step.number
                    stepName = $step.name
                    stepStatus = $step.status
                    stepConclusion = $step.conclusion
                    startedAt = $step.started_at
                    completedAt = $step.completed_at
                }
            }
        }
    } catch {
        $errors += [pscustomobject]@{ runId = $runId; endpoint = 'jobs'; error = $_.Exception.Message }
    }

    try {
        $artifactResponse = gh api "repos/$repository/actions/runs/$runId/artifacts?per_page=100" | ConvertFrom-Json
        foreach ($artifact in @($artifactResponse.artifacts)) {
            if ($null -eq $artifact) { continue }
            $artifacts += [pscustomobject]@{
                observedAtUtc = $ObservedAtUtc
                runId = $runId
                artifactId = $artifact.id
                artifactName = $artifact.name
                sizeInBytes = $artifact.size_in_bytes
                digest = $artifact.digest
                expired = $artifact.expired
                createdAt = $artifact.created_at
                expiresAt = $artifact.expires_at
                archiveDownloadUrl = $artifact.archive_download_url
            }
        }
    } catch {
        $errors += [pscustomobject]@{ runId = $runId; endpoint = 'artifacts'; error = $_.Exception.Message }
    }
}

$runs | Sort-Object runId | Export-Csv -LiteralPath (Join-Path $root "ACTIONS_SELECTED_RUNS_$stamp.csv") -NoTypeInformation -Encoding utf8
$jobs | Sort-Object runId, jobId, stepNumber | Export-Csv -LiteralPath (Join-Path $root "ACTIONS_JOBS_$stamp.csv") -NoTypeInformation -Encoding utf8
$artifacts | Sort-Object runId, artifactId | Export-Csv -LiteralPath (Join-Path $root "ACTIONS_ARTIFACTS_$stamp.csv") -NoTypeInformation -Encoding utf8
$errors | Sort-Object runId, endpoint | Export-Csv -LiteralPath (Join-Path $root "ACTIONS_CAPTURE_ERRORS_$stamp.csv") -NoTypeInformation -Encoding utf8
