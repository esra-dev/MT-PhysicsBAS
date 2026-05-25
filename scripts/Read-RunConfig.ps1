<#
.SYNOPSIS
    Loads MT-Esra runtime configuration from config/run_config.json.

.DESCRIPTION
    Returns a hashtable equivalent to the inline $Configs[$RunMode] hashtable
    historically used by run_full_project.ps1. Validates required keys and
    numeric ranges. If the config file is missing, returns $null so callers
    can fall back to their inline defaults — keeping the script
    backward-compatible during the rollout.

.PARAMETER RunMode
    Name of the profile inside config/run_config.json.profiles to load
    (e.g. "dev", "paper").

.PARAMETER ConfigPath
    Optional override of the config file path. Defaults to
    <repo>/config/run_config.json.

.EXAMPLE
    $cfg = & "$PSScriptRoot\Read-RunConfig.ps1" -RunMode dev
    if ($cfg) { $tick = $cfg.profile.tick }
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$RunMode,
    [string]$ConfigPath
)

$ErrorActionPreference = 'Stop'

if (-not $ConfigPath) {
    $repoRoot   = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $ConfigPath = Join-Path $repoRoot 'config\run_config.json'
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Write-Verbose "Read-RunConfig: config file not found at $ConfigPath; returning null"
    return $null
}

try {
    $raw = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8
    $cfg = $raw | ConvertFrom-Json
} catch {
    throw "Read-RunConfig: failed to parse '$ConfigPath' as JSON: $($_.Exception.Message)"
}

if (-not $cfg.profiles) {
    throw "Read-RunConfig: '$ConfigPath' missing required key 'profiles'."
}
if (-not $cfg.profiles.PSObject.Properties[$RunMode]) {
    $known = ($cfg.profiles.PSObject.Properties.Name) -join ', '
    throw "Read-RunConfig: profile '$RunMode' not found in '$ConfigPath'. Known: $known"
}
$profile = $cfg.profiles.$RunMode

# Required numeric keys (mirrors the historical $Configs schema).
$required = @(
    'tick','num_episodes','max_steps_per_episode','action_delay_ms',
    'exec_delay_ms_ql','exec_max_steps_ql','bench_runs',
    'exec_max_steps_bench','exec_delay_ms_bench'
)
foreach ($k in $required) {
    if (-not $profile.PSObject.Properties[$k]) {
        throw "Read-RunConfig: profile '$RunMode' missing required key '$k'."
    }
}

# Light range validation.
foreach ($k in @('num_episodes','max_steps_per_episode','action_delay_ms',
                 'exec_delay_ms_ql','exec_max_steps_ql','bench_runs',
                 'exec_max_steps_bench','exec_delay_ms_bench')) {
    $v = $profile.$k
    if ($v -lt 0) { throw "Read-RunConfig: profile '$RunMode'.$k must be >= 0 (got $v)." }
}

# Build hashtable that mirrors the historical inline shape so callers can
# do a drop-in replacement: $P = (Read-RunConfig).profile
$profileHt = @{}
foreach ($prop in $profile.PSObject.Properties) { $profileHt[$prop.Name] = $prop.Value }

return [pscustomobject]@{
    Path              = $ConfigPath
    RunMode           = $RunMode
    profile           = $profileHt
    profiles_to_run   = @($cfg.profiles_to_run)
    stereo_modes      = @($cfg.stereo_modes)
    bench_modes       = @($cfg.bench_modes)
    simulator_port_map  = $cfg.simulator_port_map
    simulator_flow_map  = $cfg.simulator_flow_map
    qtable_suffix_map   = $cfg.qtable_suffix_map
    expected_state_vec_dim = $cfg.expected_state_vec_dim
    http_client       = $cfg.http_client
    learning          = $cfg.learning
    dry_run           = [bool]$cfg.dry_run
    raw               = $cfg
}
