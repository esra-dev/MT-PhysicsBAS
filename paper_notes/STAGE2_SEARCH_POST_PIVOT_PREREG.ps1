param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$refs = @(
    'main',
    'feature/qlearning-stereotype-comparison',
    'kg-crosszone-coupling',
    'kg-crosszone-coupling-bump',
    'kg-crosszone-ablation',
    'phase2-fault-detection',
    'origin/results'
)

$lines = @()
$lines += '[COMMANDS]'
$lines += 'git log --all --after=2026-06-10T19:56:56Z --format=%H%x09%cI%x09%s -- docs/pre_registration.md'
$lines += 'git ls-tree -r --name-only <ref> | Select-String -Pattern (?i)pre.?reg|protocol'
$lines += 'git grep -n -I -E lab1|lab2|lab3|fault detection|blacklist|warm restart|re-learn|cross-zone|phase1_kg_only|phase1_baseline|phase2_ <ref> -- docs/pre_registration.md'
$lines += ''
$lines += '[POST_PIVOT_HISTORY]'
$history = @(git log --all --after='2026-06-10T19:56:56Z' --format='%H%x09%cI%x09%s' -- docs/pre_registration.md)
if ($history.Count -eq 0) {
    $lines += 'NOT FOUND'
} else {
    $lines += $history
}

foreach ($ref in $refs) {
    $sha = (git rev-parse $ref).Trim()
    $lines += ''
    $lines += "[REF] $ref@$sha"
    $lines += '[CANDIDATE_PATHS]'
    $paths = @(git ls-tree -r --name-only $ref | Select-String -Pattern '(?i)pre.?reg|protocol' | ForEach-Object { $_.Line })
    if ($paths.Count -eq 0) { $lines += 'NOT FOUND' } else { $lines += $paths }
    $lines += '[POST_PIVOT_TERMS_IN_PRE_REGISTRATION]'
    $matches = @(git grep -n -I -E 'lab1|lab2|lab3|fault detection|blacklist|warm restart|re-learn|cross-zone|phase1_kg_only|phase1_baseline|phase2_' $ref -- docs/pre_registration.md 2>$null)
    if ($matches.Count -eq 0) { $lines += 'NOT FOUND' } else { $lines += $matches }
}

[System.IO.File]::WriteAllLines($OutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
