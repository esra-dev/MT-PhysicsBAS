param(
    [Parameter(Mandatory = $true)]
    [string]$InputCsv,

    [Parameter(Mandatory = $true)]
    [string]$OutputCsv
)

$runs = @(Import-Csv -LiteralPath $InputCsv)
$rows = @(
    [pscustomobject]@{
        workflow = 'ALL'
        conclusion = 'ALL'
        run_count = $runs.Count
    }
)

$rows += $runs |
    Group-Object -Property workflowName, conclusion |
    Sort-Object -Property Name |
    ForEach-Object {
        [pscustomobject]@{
            workflow = $_.Group[0].workflowName
            conclusion = if ([string]::IsNullOrWhiteSpace($_.Group[0].conclusion)) {
                'IN_PROGRESS'
            } else {
                $_.Group[0].conclusion
            }
            run_count = $_.Count
        }
    }

$rows | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding utf8
