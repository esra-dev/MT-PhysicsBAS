<#
.SYNOPSIS
    Runs the entire MT-Esra project end-to-end:
    Training → Benchmark Sweep → Analysis

.DESCRIPTION
    Phase 1  — Applies timing/episode parameters to ASL files and simulator flows
    Phase 2  — Starts all 6 weakness-lab Node-RED simulators (ports 1882–1887)
    Phase 3  — Trains Q-learning for every profile × 2 stereotype modes
    Phase 4  — Runs the full benchmark sweep (all profiles × all modes)
    Phase 5  — Runs the sweep analysis report
    Cleanup  — Stops simulators; restores structural ASL state (timing kept)

    All output is written to run_full_project.log in the project root.

.PARAMETER RunMode
    "dev"   — recommended safe config: tick=0.1s, 400 episodes, 20 steps, 115ms delays, 2 runs
              Expected total wall-clock: ~6–8 h (training dominates)
    "paper" — paper-quality:            tick=0.2s, 2500 episodes, 30 steps, 250ms delays, 5 runs
              Expected total wall-clock: ~50–60 h

.PARAMETER SkipTraining
    Skip Phase 3 (training).  Use this when Q-tables already exist and you
    only want to re-run benchmarking + analysis.

.PARAMETER SkipBenchmark
    Skip Phase 4 (benchmark sweep) and Phase 5 (analysis).

.EXAMPLE
    .\run_full_project.ps1
    .\run_full_project.ps1 -RunMode paper
    .\run_full_project.ps1 -SkipTraining

.NOTES
    Target shell: Windows PowerShell 5.1+ (also works under PowerShell 7+).
    Do not use PS7-only syntax here — no null-conditional (?.), null-coalescing (??),
    ternary (a ? b : c), or native command chaining (&&, ||).
#>

param(
    [ValidateSet("dev","paper")]
    [string]$RunMode = "dev",

    # Optional comma-separated subset of profiles to train and benchmark.
    # Used by run_full_project_parallel.ps1 so each clone runs only its own
    # profile. Empty (default) = all profiles.
    [string]$OnlyProfiles = "",

    # Optional filter for the Phase 3 stereotype loop. Used by CI matrices
    # (one job per profile x stereo cell). Default 'both' = unchanged behaviour.
    [ValidateSet("true","false","both")]
    [string]$OnlyStereo = "both",

    # Optional comma-separated subset of benchmark modes for Phase 4.
    # Used by CI matrices (one job per profile x mode cell). Default = all.
    [string]$OnlyModes = "",

    [switch]$SkipTraining,
    [switch]$SkipBenchmark,

    # Phase 12 #6: skip the gradlew preflight gate. Off by default — preflight
    # is a fast safety net (TTL parse, scenario JSON, simulator /health).
    [switch]$SkipPreflight,

    # Phase 12 #10: snapshot Q-tables / TTLs into the `results` branch after
    # Phase 4 completes. Push only when -PublishResults is also set.
    [switch]$VersionResults,
    [switch]$PublishResults,

    # Phase 12 #12: dry-run mode (set dry_run(true) belief; results written
    # under <mode>_dryrun/). Currently informational; the LabEnvironment
    # short-circuit lands in the follow-up Java change.
    [switch]$DryRun,

    # Research extension: per-run seed for CIs across independent replicas.
    # 0 (default) leaves QLearner's deterministic baseSeed unchanged. Any
    # non-zero integer is XORed (after SplitMix64) into baseSeed inside
    # QLearner.configureQLearner so the explore stream diverges per seed.
    [int]$RunSeed = 0
)

$ErrorActionPreference = "Stop"
$script:HadFatalError = $false
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# ─── Parameter sets ───────────────────────────────────────────────────────────
$Configs = @{
    dev = @{
        tick                  = "0.05"    # Node-RED repeat interval (seconds)
        num_episodes          = 50
        max_steps_per_episode = 20
        action_delay_ms       = 65      # must be > tick*1000 + jitter buffer
        exec_delay_ms_ql      = 65
        exec_max_steps_ql     = 20
        bench_runs            = 2
        exec_max_steps_bench  = 20
        exec_delay_ms_bench   = 65
    }
    paper = @{
        tick                  = "0.2"
        num_episodes          = 2500
        max_steps_per_episode = 30
        action_delay_ms       = 250
        exec_delay_ms_ql      = 500
        exec_max_steps_ql     = 30
        bench_runs            = 5
        exec_max_steps_bench  = 30
        exec_delay_ms_bench   = 250
    }
}

# ─── Externalised configuration (Phase 12 #1) ─────────────────────────────
# Prefer config/run_config.json when present; fall back to the inline
# $Configs hashtable above so legacy/offline runs still work.
$RunConfig = $null
$_readCfg  = Join-Path $ScriptRoot 'scripts\Read-RunConfig.ps1'
if (Test-Path -LiteralPath $_readCfg) {
    try {
        $RunConfig = & $_readCfg -RunMode $RunMode
    } catch {
        Write-Warning "Read-RunConfig failed; falling back to inline `\$Configs. Reason: $($_.Exception.Message)"
        $RunConfig = $null
    }
}
if ($RunConfig) {
    Write-Host "Loaded run config from: $($RunConfig.Path) (profile: $RunMode)" -ForegroundColor DarkCyan
    $P = $RunConfig.profile
} else {
    $P = $Configs[$RunMode]
}

# Phase 12 #1: build -P pass-through args for simulator HTTP tuning.
# These are read by build.gradle (tasks.withType(JavaExec).configureEach)
# and forwarded as -Dsim.http.* to JaCaMoLauncher; LabEnvironment.init
# picks them up at startup.
$HttpArgs = @()
if ($RunConfig -and $RunConfig.http_client) {
    $hc = $RunConfig.http_client
    if ($hc.connect_timeout_ms  -ne $null) { $HttpArgs += "-Psim.http.connectMs=$($hc.connect_timeout_ms)" }
    if ($hc.response_timeout_ms -ne $null) { $HttpArgs += "-Psim.http.responseMs=$($hc.response_timeout_ms)" }
    if ($hc.max_retries         -ne $null) { $HttpArgs += "-Psim.http.maxRetries=$($hc.max_retries)" }
    if ($hc.backoff_base_ms     -ne $null) { $HttpArgs += "-Psim.http.backoffMs=$($hc.backoff_base_ms)" }
}
# Learning hyperparameters (Phase A/C fixes): forwarded as -Dreward.clip etc.
if ($RunConfig -and $RunConfig.learning) {
    $ln = $RunConfig.learning
    if ($ln.reward_clip                 -ne $null) { $HttpArgs += "-Preward.clip=$($ln.reward_clip)" }
    if ($ln.stereo_prior_scale          -ne $null) { $HttpArgs += "-Pstereo.priorScale=$($ln.stereo_prior_scale)" }
    if ($ln.stereo_prior_decay_episodes -ne $null) { $HttpArgs += "-Pstereo.priorDecayEpisodes=$($ln.stereo_prior_decay_episodes)" }
    if ($ln.stereo_prior_decay_floor    -ne $null) { $HttpArgs += "-Pstereo.priorDecayFloor=$($ln.stereo_prior_decay_floor)" }
    # Research extensions: PBRS reward shaping + adaptive stereotype trust.
    if ($ln.reward_shaping              -ne $null) { $HttpArgs += "-Preward.shaping=$($ln.reward_shaping)" }
    if ($ln.adaptive_trust              -ne $null) { $HttpArgs += "-Pstereo.adaptiveTrust=$($ln.adaptive_trust)" }
    if ($ln.adaptive_trust_min_samples  -ne $null) { $HttpArgs += "-Pstereo.adaptiveTrust.minSamples=$($ln.adaptive_trust_min_samples)" }
    if ($ln.adaptive_trust_floor        -ne $null) { $HttpArgs += "-Pstereo.adaptiveTrust.floor=$($ln.adaptive_trust_floor)" }
}
# Per-run seed (-RunSeed N). Overrides any RunConfig.learning.run_seed if set.
if ($RunSeed -ne 0) {
    $HttpArgs += "-Prun.seed=$RunSeed"
}

# ─── Project layout ───────────────────────────────────────────────────────────
# Profiles to train/benchmark (4-zone weakness labs only).
$TrainProfiles = @(
    "custom2", "custom3", "custom4", "custom5", "custom6", "custom7", "custom8"
)

# Apply -OnlyProfiles filter (parallel orchestrator passes one profile per clone).
if ($OnlyProfiles) {
    $requested = @($OnlyProfiles -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($requested.Count -eq 0) {
        throw "-OnlyProfiles supplied but parsed to empty list: '$OnlyProfiles'"
    }
    $unknown = @($requested | Where-Object { $_ -notin $TrainProfiles })
    if ($unknown.Count -gt 0) {
        throw "Unknown profile(s) in -OnlyProfiles: $($unknown -join ', '). Valid: $($TrainProfiles -join ', ')"
    }
    $TrainProfiles = $requested
}

$BenchProfiles = $TrainProfiles -join ","
$BenchModes    = "rule_based,ql_false,ql_true"
$StereoModes   = @("true", "false")

# Apply -OnlyStereo filter (CI matrices pass one stereo per job).
if ($OnlyStereo -ne "both") {
    $StereoModes = @($OnlyStereo)
}

# Apply -OnlyModes filter (CI matrices pass one mode per job).
if ($OnlyModes) {
    $_validModes = @("rule_based","ql_false","ql_true")
    $requestedModes = @($OnlyModes -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($requestedModes.Count -eq 0) {
        throw "-OnlyModes supplied but parsed to empty list: '$OnlyModes'"
    }
    $unknownModes = @($requestedModes | Where-Object { $_ -notin $_validModes })
    if ($unknownModes.Count -gt 0) {
        throw "Unknown mode(s) in -OnlyModes: $($unknownModes -join ', '). Valid: $($_validModes -join ', ')"
    }
    $BenchModes = $requestedModes -join ','
}

# Cross-platform gradlew lookup. PS 5.1 always sets $env:OS = 'Windows_NT';
# pwsh on Linux/macOS leaves it empty, so we fall back to the POSIX wrapper.
# The CI workflows chmod +x ./gradlew before invoking this script.
if ($env:OS -eq 'Windows_NT') {
    $GradleExe = Join-Path $ScriptRoot 'gradlew.bat'
} else {
    $GradleExe = Join-Path $ScriptRoot 'gradlew'
}

$ProfileQtableSuffix = @{
    custom2 = "_custom2"
    custom3 = "_custom3"
    custom4 = "_custom4"
    custom5 = "_custom5"
    custom6 = "_custom6"
    custom7 = "_custom7"
    custom8 = "_custom8"
}

# Simulator map: each entry is a profile → (port, flow file) binding
$Simulators = @(
    [pscustomobject]@{ Profile="custom2"; Port=1882; Flow="simulator_flow_custom2.json" }
    [pscustomobject]@{ Profile="custom3"; Port=1883; Flow="simulator_flow_custom3.json" }
    [pscustomobject]@{ Profile="custom4"; Port=1884; Flow="simulator_flow_custom4.json" }
    [pscustomobject]@{ Profile="custom5"; Port=1885; Flow="simulator_flow_custom5.json" }
    [pscustomobject]@{ Profile="custom6"; Port=1886; Flow="simulator_flow_custom6.json" }
    [pscustomobject]@{ Profile="custom7"; Port=1887; Flow="simulator_flow_custom7.json" }
    [pscustomobject]@{ Profile="custom8"; Port=1888; Flow="simulator_flow_custom8.json" }
)

# ASL file paths (relative; resolved via Set-Location above)
$QlAslPath       = "src\agt\illuminance_controller_agent_ql.asl"
$BenchAslPath    = "src\agt\illuminance_controller_agent_bench.asl"
$ProfilesAslPath = "src\agt\lab_profiles.asl"

# ─── Logging setup ────────────────────────────────────────────────────────────
$LogFile    = Join-Path $ScriptRoot "run_full_project.log"
$LogStream  = $null

function Write-Log {
    param([string]$msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    if ($LogStream) { $LogStream.WriteLine($line) ; $LogStream.Flush() }
    Write-Host $line
}

function Write-Header {
    param([string]$msg)
    $bar = "═" * 60
    Write-Log ""
    Write-Log $bar
    Write-Log "  $msg"
    Write-Log $bar
}
function Write-OK   { param([string]$msg) Write-Log "  [OK]  $msg" }
function Write-Info { param([string]$msg) Write-Log "  [..] $msg" }
function Write-Warn { param([string]$msg) Write-Log "  [!!] $msg" }
function Write-Fail { param([string]$msg) Write-Log "  [XX] $msg" }

# ─── File I/O helpers (UTF-8 without BOM, matching Java/Gradle expectation) ───
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function ReadFile  { param([string]$path)
    [System.IO.File]::ReadAllText((Resolve-Path $path), $Utf8NoBom)
}
function WriteFile { param([string]$path, [string]$content)
    $abs = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($path)
    [System.IO.File]::WriteAllText($abs, $content, $Utf8NoBom)
}

# ─── Simulator health check ───────────────────────────────────────────────────
function Wait-Simulator {
    param([int]$Port, [int]$TimeoutSec = 90)
    # Prefer /health (lightweight, no flow state mutation). Fall back to
    # /was/rl/status for older flows that pre-date the /health endpoint.
    $healthUrl = "http://127.0.0.1:$Port/health"
    $statusUrl = "http://127.0.0.1:$Port/was/rl/status"
    $deadline  = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        foreach ($url in @($healthUrl, $statusUrl)) {
            try {
                $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
                if ($r.StatusCode -eq 200) { return $true }
            } catch { }
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

# ─── State tracking ───────────────────────────────────────────────────────────
$OrigFiles = @{}   # absolute path → original file text (saved before any edit)
$SimProcs  = @{}   # port (int) → System.Diagnostics.Process

function Save-Orig { param([string]$path)
    $abs = (Resolve-Path $path).Path
    if (-not $OrigFiles.ContainsKey($abs)) {
        $OrigFiles[$abs] = ReadFile $abs
    }
}

function Get-ExpectedTrainingArtifacts {
    param(
        [string]$Profile,
        [string]$Stereo
    )
    if (-not $ProfileQtableSuffix.ContainsKey($Profile)) {
        throw "No qtable suffix mapping found for profile '$Profile'"
    }
    $suffix = $ProfileQtableSuffix[$Profile]
    return @(
        "qtable_final_stereotypes_${Stereo}${suffix}.csv",
        "qtable_initial_stereotypes_${Stereo}${suffix}.csv",
        "metrics_stereotypes_${Stereo}${suffix}.csv",
        "iv_stats_stereotypes_${Stereo}${suffix}.json",
        "coverage_stereotypes_${Stereo}${suffix}.csv",
        "first_goal_stereotypes_${Stereo}${suffix}.csv",
        "learned_stereotypes_${Stereo}${suffix}.ttl"
    )
}

function Assert-TrainingManifestsComplete {
    $missing = @()
    foreach ($profile in $TrainProfiles) {
        foreach ($stereo in $StereoModes) {
            $archiveDir = Join-Path $ScriptRoot "benchmark\\results\\$profile\\training_stereo_$stereo"
            $manifestPath = Join-Path $archiveDir "TRAINING_OK.json"
            if (-not (Test-Path $manifestPath)) {
                $missing += "Missing manifest: $manifestPath"
                continue
            }

            try {
                $manifest = Get-Content -Raw -Path $manifestPath | ConvertFrom-Json
            } catch {
                $missing += "Invalid manifest JSON: $manifestPath"
                continue
            }

            if ($manifest.status -ne "ok") {
                $missing += "Manifest status not ok: $manifestPath"
                continue
            }

            if (-not $manifest.artifacts -or $manifest.artifacts.Count -eq 0) {
                $missing += "Manifest has no artifacts list: $manifestPath"
                continue
            }

            foreach ($fname in $manifest.artifacts) {
                $fpath = Join-Path $archiveDir $fname
                if (-not (Test-Path $fpath)) {
                    $missing += "Missing archived artifact: $fpath"
                }
            }
        }
    }

    if ($missing.Count -gt 0) {
        throw "SkipTraining validation failed.`n - " + ($missing -join "`n - ")
    }
}

# ─── Pre-flight checks ────────────────────────────────────────────────────────
# Open log file early so all output is captured.
# IMPORTANT: open with FileShare.ReadWrite so that `Tee-Object -Append` calls
# inside the training/benchmark phases can also open the file.  A plain
# [StreamWriter]::new($path, ...) call takes an exclusive write lock, which
# causes Tee-Object to throw "process cannot access the file" mid-run.
$_logFs     = [System.IO.FileStream]::new(
    $LogFile,
    [System.IO.FileMode]::Create,
    [System.IO.FileAccess]::Write,
    [System.IO.FileShare]::ReadWrite)
$LogStream  = [System.IO.StreamWriter]::new($_logFs, $Utf8NoBom)

Write-Header "MT-Esra full-project run  |  mode=$RunMode  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

# Verify node-red is on PATH
# On Windows, node-red.ps1 is NOT in PATHEXT so Start-Process would open it
# as a text file.  Resolve node-red.cmd explicitly; it runs via cmd.exe and
# stays alive for the lifetime of the node process.
$_nrCmd = Get-Command "node-red.cmd" -ErrorAction SilentlyContinue
if (-not $_nrCmd) { $_nrCmd = Get-Command "node-red" -ErrorAction SilentlyContinue }
if (-not $_nrCmd) {
    Write-Fail "node-red not found in PATH.  Install it with:  npm install -g node-red"
    $LogStream.Close()
    exit 1
}
$NodeRedCmd = $_nrCmd.Source

# Verify Python
$PythonCmd = if (Get-Command "py" -ErrorAction SilentlyContinue) { "py" }
             elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command "python" -ErrorAction SilentlyContinue) { "python" }
             else { $null }
if (-not $PythonCmd) {
    Write-Fail "Python 3 not found in PATH.  Install Python 3 and add it to PATH."
    $LogStream.Close()
    exit 1
}

Write-OK "node-red : $NodeRedCmd"
Write-OK "python   : $PythonCmd"
Write-OK "RunMode  : $RunMode (tick=$($P.tick)s, episodes=$($P.num_episodes), delay=$($P.action_delay_ms)ms)"
Write-OK "Log file : $LogFile"

# ─────────────────────────────────────────────────────────────────────────────
try {

    # ════════════════════════════════════════════════════════════════════════
    # Phase 1 — Apply parameters to source files
    # ════════════════════════════════════════════════════════════════════════
    Write-Header "Phase 1 — Applying $RunMode parameters"

    # 1a. Simulator tick in all flow JSON files
    foreach ($sim in $Simulators) {
        $flowPath = "simulator\$($sim.Flow)"
        if (-not (Test-Path $flowPath)) {
            Write-Warn "Flow file not found — skipping: $flowPath"
            continue
        }
        Save-Orig $flowPath
        # The repeat inject node stores the interval as a quoted string, e.g. "repeat": "0.2"
        $patched = (ReadFile $flowPath) -replace '(?<="repeat"\s*:\s*)"[0-9.]+"', "`"$($P.tick)`""
        WriteFile $flowPath $patched
        Write-OK "Tick $($P.tick)s  →  $($sim.Flow)"
    }

    # 1b. Q-learning agent parameters
    Save-Orig $QlAslPath
    $ql = ReadFile $QlAslPath
    $ql = $ql -replace '(?m)^num_episodes\(\d+\)\.',            "num_episodes($($P.num_episodes))."
    $ql = $ql -replace '(?m)^max_steps_per_episode\(\d+\)\.',   "max_steps_per_episode($($P.max_steps_per_episode))."
    $ql = $ql -replace '(?m)^action_delay_ms\(\d+\)\.',         "action_delay_ms($($P.action_delay_ms))."
    $ql = $ql -replace '(?m)^exec_delay_ms\(\d+\)\.',           "exec_delay_ms($($P.exec_delay_ms_ql))."
    $ql = $ql -replace '(?m)^exec_max_steps\(\d+\)\.',          "exec_max_steps($($P.exec_max_steps_ql))."
    WriteFile $QlAslPath $ql
    Write-OK "QL agent   : episodes=$($P.num_episodes)  steps=$($P.max_steps_per_episode)  delay=$($P.action_delay_ms)ms"

    # 1c. Benchmark agent parameters
    Save-Orig $BenchAslPath
    $bench = ReadFile $BenchAslPath
    $bench = $bench -replace '(?m)^bench_runs\(\d+\)\.',        "bench_runs($($P.bench_runs))."
    $bench = $bench -replace '(?m)^exec_max_steps\(\d+\)\.',    "exec_max_steps($($P.exec_max_steps_bench))."
    $bench = $bench -replace '(?m)^exec_delay_ms\(\d+\)\.',     "exec_delay_ms($($P.exec_delay_ms_bench))."
    WriteFile $BenchAslPath $bench
    Write-OK "Bench agent: runs=$($P.bench_runs)  steps=$($P.exec_max_steps_bench)  delay=$($P.exec_delay_ms_bench)ms"

    # Patch lab_profiles.asl — two mutations, both restored after Phase 3
    # (and in the finally block on error):
    #   (a) training_params episode count: replace the hardcoded per-profile
    #       paper-run budget (10 000) with the run-mode value from run_config.json
    #       so !profile_training_params in !start returns the correct budget.
    #       Epsilon-decay (the value after the comma) is profile-specific and kept.
    #   (b) active_profile: patched per-cell in Phase 3 on top of this snapshot.
    Save-Orig $ProfilesAslPath
    $lp = ReadFile $ProfilesAslPath
    $lp = $lp -replace '(?m)(training_params\()\d+(,)', "`${1}$($P.num_episodes)`${2}"
    WriteFile $ProfilesAslPath $lp
    Write-OK "lab_profiles.asl : training_params episodes → $($P.num_episodes)  (run_mode=$RunMode)"

    # ════════════════════════════════════════════════════════════════════════
    # Phase 2 — Start Node-RED simulators
    # ════════════════════════════════════════════════════════════════════════
    Write-Header "Phase 2 — Starting Node-RED simulators"

    # CI optimisation: when -OnlyProfiles narrows the run to one (or a few)
    # profile(s), only start the simulators we actually need. Local full runs
    # (no -OnlyProfiles) still start all 7, matching original behaviour.
    $ActiveSims = $Simulators | Where-Object { $_.Profile -in $TrainProfiles }

    foreach ($sim in $ActiveSims) {
        $flowAbs = Join-Path $ScriptRoot "simulator\$($sim.Flow)"
        $userDir = Join-Path $ScriptRoot ".node-red-$($sim.Profile)"

        # If the simulator is already answering (e.g. manually deployed in Node-RED),
        # reuse it and skip launching a new instance.
        if (Wait-Simulator -Port $sim.Port -TimeoutSec 3) {
            Write-OK "$($sim.Profile)  :$($sim.Port)  already running — reusing"
            # Do NOT add to $SimProcs so cleanup will not kill this external instance.
            continue
        }

        if (-not (Test-Path $flowAbs)) {
            Write-Warn "Flow file missing — skipping: $($sim.Flow)"
            continue
        }
        New-Item -ItemType Directory -Force -Path $userDir | Out-Null
        $spArgs = @{
            FilePath     = $NodeRedCmd
            ArgumentList = "--userDir `"$userDir`" --port $($sim.Port) `"$flowAbs`""
            PassThru     = $true
        }
        # -WindowStyle is Windows-only; PowerShell Core on Linux/macOS does not support it.
        if ($IsWindows -or ($null -eq $IsWindows -and $env:OS -eq 'Windows_NT')) {
            $spArgs.WindowStyle = 'Hidden'
        }
        $proc = Start-Process @spArgs
        $SimProcs[$sim.Port] = $proc
        Write-Info "Launched $($sim.Profile)  port=$($sim.Port)  PID=$($proc.Id)"
    }

    Write-Info "Waiting for newly-launched simulators to respond (up to 90 s each)..."
    foreach ($sim in $ActiveSims) {
        if (-not $SimProcs.ContainsKey($sim.Port)) { continue }   # already-running sims were skipped above
        if (Wait-Simulator -Port $sim.Port -TimeoutSec 90) {
            Write-OK "$($sim.Profile)  :$($sim.Port)  ready"
        } else {
            throw "Simulator $($sim.Profile) did not start within 90 s on port $($sim.Port)"
        }
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase 2.5 — Preflight (Phase 12 #6)
    # Validates TTL files, scenario JSONs, and that all simulator /health
    # endpoints respond. Bypass with -SkipPreflight when iterating locally.
    # ════════════════════════════════════════════════════════════════════════
    if (-not $SkipPreflight) {
        Write-Header "Phase 2.5 — Preflight"
        $pfArgs = @("preflight", "-Pprofiles=$($TrainProfiles -join ',')", "--console=plain")
        & $GradleExe @pfArgs *>&1 | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -ne 0) {
            throw "Preflight failed (exit $LASTEXITCODE). Re-run with -SkipPreflight to bypass."
        }
        Write-OK "Preflight passed"
    } else {
        Write-Log "Phase 2.5 — Preflight SKIPPED (-SkipPreflight)"
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase 3 — Training
    # Each profile has a unique qtable_suffix (e.g. _custom2), so Q-tables
    # from different profiles never overwrite each other.
    # ════════════════════════════════════════════════════════════════════════
    if (-not $SkipTraining) {
        $totalCells = $TrainProfiles.Count * $StereoModes.Count
        $cellsDone  = 0
        Write-Header "Phase 3 — Training  ($totalCells cells:  $($TrainProfiles.Count) profiles × $($StereoModes.Count) stereotype modes)"

        foreach ($profile in $TrainProfiles) {
            foreach ($stereo in $StereoModes) {
                $cellsDone++
                $cellStart = Get-Date
                Write-Header "Training [$cellsDone/$totalCells]  profile=$profile  use_stereotypes=$stereo"

                # Resume support: if this cell was already trained successfully
                # in a previous (possibly killed) run, skip it. The TRAINING_OK
                # manifest is only written after artefacts are validated and
                # archived, so its presence guarantees the cell is complete.
                $archiveDirPre   = "benchmark\results\$profile\training_stereo_$stereo"
                $manifestPathPre = Join-Path $archiveDirPre "TRAINING_OK.json"
                if (Test-Path $manifestPathPre) {
                    Write-OK "Already trained (manifest present) — skipping  profile=$profile  stereo=$stereo"
                    continue
                }

                # active_profile is now passed to taskQl via -Pprofile (system
                # property active.profile, consumed by apply_runtime_overrides_ql
                # in the QL agent at startup — #7). No .asl mutation required.

                # Patch use_stereotypes on top of the already-timing-patched ql.asl
                $ql = ReadFile $QlAslPath
                $ql = $ql -replace '(?m)^use_stereotypes\((true|false)\)\.', "use_stereotypes($stereo)."
                WriteFile $QlAslPath $ql

                # Belt-and-suspenders: also patch active_profile in lab_profiles.asl.
                # This guarantees the correct profile even if the tools.jia.system_prop
                # JIA fails to load (e.g. due to a class-loader race in parallel builds).
                # The original is already saved via Save-Orig $ProfilesAslPath above.
                $lp = ReadFile $ProfilesAslPath
                $lp = $lp -replace '(?m)^active_profile\(".*?"\)\.', "active_profile(`"$profile`")."
                WriteFile $ProfilesAslPath $lp

                $expectedArtefacts = Get-ExpectedTrainingArtifacts -Profile $profile -Stereo $stereo
                # Optional deterministic cleanup: remove only this cell's expected outputs.
                foreach ($fname in $expectedArtefacts) {
                    $fpath = Join-Path $ScriptRoot $fname
                    if (Test-Path $fpath) {
                        Remove-Item -Path $fpath -Force
                    }
                }

                # Run training (taskQl depends on 'classes' so compilation is automatic).
                # Gradle stdout/stderr go to dedicated per-cell log files.
                # We launch Gradle via Start-Process (non-blocking, file-based
                # redirection — no PS pipeline, so no back-pressure risk on the JVM)
                # and then poll the cell log every 15 s to echo [Training] progress
                # lines through Write-Info, giving real-time episode visibility in
                # the parallel training log (log\parallel\train_<profile>.log).
                $cellLogDir = Join-Path $ScriptRoot "log"
                New-Item -ItemType Directory -Force -Path $cellLogDir | Out-Null
                $cellLogFile = Join-Path $cellLogDir "train_${profile}_stereo_${stereo}.log"
                $cellErrFile = Join-Path $cellLogDir "train_${profile}_stereo_${stereo}.err.log"
                Write-Info "Gradle output -> $cellLogFile"
                $gArgs     = @("taskQl", "-Pprofile=$profile") + $HttpArgs + @("--console=plain")
                $gradleExe = $GradleExe
                # -WindowStyle is Windows-only; PowerShell Core on Linux/macOS does not support it.
                $gpArgs = @{
                    FilePath               = $gradleExe
                    ArgumentList           = $gArgs
                    WorkingDirectory       = $ScriptRoot
                    RedirectStandardOutput = $cellLogFile
                    RedirectStandardError  = $cellErrFile
                    PassThru               = $true
                }
                if ($IsWindows -or ($null -eq $IsWindows -and $env:OS -eq 'Windows_NT')) {
                    $gpArgs.WindowStyle = 'Hidden'
                }
                $gProc = Start-Process @gpArgs
                # Helper: read any new [Training] / key lines from $cellLogFile and
                # echo them via Write-Info (appears in the parallel progress log).
                $tailPos = 0L
                $tailFilter = '\[Training\]|\[QL\]\s+Final|BUILD (FAILED|SUCCESSFUL)'
                function Invoke-TailLog {
                    param([string]$LogPath, [ref]$PosRef)
                    if (-not (Test-Path $LogPath)) { return }
                    try {
                        $fs = [System.IO.FileStream]::new($LogPath,
                            [System.IO.FileMode]::Open,
                            [System.IO.FileAccess]::Read,
                            [System.IO.FileShare]::ReadWrite)
                        [void]$fs.Seek($PosRef.Value, [System.IO.SeekOrigin]::Begin)
                        $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8)
                        while (($tLine = $sr.ReadLine()) -ne $null) {
                            if ($tLine -match $tailFilter) {
                                Write-Info "  >> $($tLine.Trim())"
                            }
                        }
                        $PosRef.Value = [long]$fs.Position
                        $sr.Dispose(); $fs.Dispose()
                    } catch { }
                }
                # Detect completion markers directly from the training log.
                # Used only as a fallback when process exit code is unavailable.
                function Test-TrainingCompletionMarkers {
                    param([string]$LogPath, [int]$ExpectedEpisodes)
                    if (-not (Test-Path -LiteralPath $LogPath)) { return $false }
                    try {
                        $tail = Get-Content -LiteralPath $LogPath -Tail 600 -ErrorAction SilentlyContinue
                        if (-not $tail) { return $false }
                        $epPattern = "\\[Training\\]\\s+ep\\s+${ExpectedEpisodes}/${ExpectedEpisodes}\\b"
                        $joined = ($tail -join "`n")
                        return ($joined -match $epPattern) -or ($joined -match 'BUILD SUCCESSFUL') -or ($joined -match 'Training complete after')
                    } catch {
                        return $false
                    }
                }
                $heartbeatEverySec = 60
                $watchdogNoGrowthSec = 1200
                $lastHeartbeat = Get-Date
                $lastLogGrowth = Get-Date
                $lastLogLength = if (Test-Path $cellLogFile) {
                    (Get-Item -LiteralPath $cellLogFile -ErrorAction SilentlyContinue).Length
                } else {
                    0
                }
                while (-not $gProc.HasExited) {
                    Start-Sleep -Seconds 15
                    Invoke-TailLog -LogPath $cellLogFile -PosRef ([ref]$tailPos)

                    $now = Get-Date
                    $logLength = if (Test-Path $cellLogFile) {
                        (Get-Item -LiteralPath $cellLogFile -ErrorAction SilentlyContinue).Length
                    } else {
                        0
                    }
                    if ($logLength -gt $lastLogLength) {
                        $lastLogGrowth = $now
                        $lastLogLength = $logLength
                    }

                    if ((New-TimeSpan -Start $lastHeartbeat -End $now).TotalSeconds -ge $heartbeatEverySec) {
                        $elapsedMin = [int](New-TimeSpan -Start $cellStart -End $now).TotalMinutes
                        $idleSec = [int](New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds
                        Write-Info "[Heartbeat] training still running: profile=$profile stereo=$stereo elapsed=${elapsedMin}m idle=${idleSec}s pid=$($gProc.Id)"
                        $lastHeartbeat = $now
                    }

                    if ((New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds -ge $watchdogNoGrowthSec) {
                        try {
                            if (-not $gProc.HasExited) {
                                Stop-Process -Id $gProc.Id -Force -ErrorAction Stop
                            }
                        } catch { }
                        throw "Training watchdog timeout for profile=$profile stereo=${stereo}: no log growth for $watchdogNoGrowthSec s (see $cellLogFile)"
                    }
                }
                # Final tail pass: capture any lines written after the last poll
                # The process is expected to be exited here, but refresh + wait
                # defensively to ensure ExitCode is populated.
                try { $gProc.Refresh() } catch {}
                try { [void]$gProc.WaitForExit(120000) } catch {}
                Invoke-TailLog -LogPath $cellLogFile -PosRef ([ref]$tailPos)
                # ExitCode can still be temporarily unavailable on Windows even
                # after HasExited due to process handle timing. Retry briefly.
                $gExitCode = $null
                for ($exitTry = 1; $exitTry -le 20; $exitTry++) {
                    try { $gProc.Refresh() } catch {}
                    if ($null -ne $gProc.ExitCode) {
                        $gExitCode = [int]$gProc.ExitCode
                        break
                    }
                    Start-Sleep -Milliseconds 250
                }
                if ($null -eq $gExitCode) { $gExitCode = -999 }
                # Merge stderr into main log if non-empty
                if ((Test-Path $cellErrFile) -and
                    (Get-Item $cellErrFile -ErrorAction SilentlyContinue).Length -gt 0) {
                    "`n--- STDERR ---`n" | Out-File -FilePath $cellLogFile -Encoding utf8 -Append
                    Get-Content $cellErrFile -ErrorAction SilentlyContinue |
                        Out-File -FilePath $cellLogFile -Encoding utf8 -Append
                }
                if ($gExitCode -ne 0) {
                    $logLooksComplete = Test-TrainingCompletionMarkers -LogPath $cellLogFile -ExpectedEpisodes ([int]$P.num_episodes)
                    if (($gExitCode -eq -999) -and $logLooksComplete) {
                        Write-Warn "taskQl exit code unavailable (profile=$profile stereo=$stereo); completion markers found in log, continuing."
                        $elapsed = [int](New-TimeSpan -Start $cellStart -End (Get-Date)).TotalMinutes
                        Write-OK "Done in ${elapsed} min  profile=$profile  stereo=$stereo"
                        $gExitCode = 0
                    } else {
                        throw "taskQl failed with exit code $gExitCode for profile=$profile stereo=$stereo (see $cellLogFile)"
                    }
                } else {
                    $elapsed = [int](New-TimeSpan -Start $cellStart -End (Get-Date)).TotalMinutes
                    Write-OK "Done in ${elapsed} min  profile=$profile  stereo=$stereo"
                }

                $missingNow = @()
                foreach ($fname in $expectedArtefacts) {
                    $fpath = Join-Path $ScriptRoot $fname
                    if (-not (Test-Path $fpath)) {
                        $missingNow += $fname
                    }
                }
                if ($missingNow.Count -gt 0) {
                    throw "Training artifacts missing for profile=$profile stereo=${stereo}: $($missingNow -join ', ')"
                }

                # Archive training artefacts for this cell
                $archiveDir = "benchmark\results\$profile\training_stereo_$stereo"
                New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
                foreach ($fname in $expectedArtefacts) {
                    Copy-Item -Path (Join-Path $ScriptRoot $fname) -Destination (Join-Path $archiveDir $fname) -Force
                }

                $manifestPath = Join-Path $archiveDir "TRAINING_OK.json"
                $manifest = [ordered]@{
                    status = "ok"
                    profile = $profile
                    stereotype = $stereo
                    run_mode = $RunMode
                    timestamp = (Get-Date).ToString("o")
                    artifacts = $expectedArtefacts
                } | ConvertTo-Json -Depth 4
                WriteFile $manifestPath $manifest
                Write-Info "Artefacts archived → $archiveDir"
            }
        }

        # Restore use_stereotypes/timing in the QL ASL.  active_profile is
        # now also restored from its original snapshot.
        $restoredQl = $OrigFiles[(Resolve-Path $QlAslPath).Path]
        $restoredQl = $restoredQl -replace '(?m)^num_episodes\(\d+\)\.',           "num_episodes($($P.num_episodes))."
        $restoredQl = $restoredQl -replace '(?m)^max_steps_per_episode\(\d+\)\.',  "max_steps_per_episode($($P.max_steps_per_episode))."
        $restoredQl = $restoredQl -replace '(?m)^action_delay_ms\(\d+\)\.',        "action_delay_ms($($P.action_delay_ms))."
        $restoredQl = $restoredQl -replace '(?m)^exec_delay_ms\(\d+\)\.',          "exec_delay_ms($($P.exec_delay_ms_ql))."
        $restoredQl = $restoredQl -replace '(?m)^exec_max_steps\(\d+\)\.',         "exec_max_steps($($P.exec_max_steps_ql))."
        WriteFile $QlAslPath $restoredQl
        Write-OK "QL ASL restored (timing params preserved)"

        $restoredLp = $OrigFiles[(Resolve-Path $ProfilesAslPath).Path]
        WriteFile $ProfilesAslPath $restoredLp
        Write-OK "lab_profiles.asl restored"

    } else {
        Write-Header "Phase 3 — Training SKIPPED (-SkipTraining)"
        Write-Info "Validating training completion manifests before benchmark..."
        Assert-TrainingManifestsComplete
        Write-OK "SkipTraining validation passed for all profile × stereotype cells."
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase 4 — Benchmark sweep
    # runFullSweep handles active_profile / bench_mode patching and restore
    # internally.  Results land in benchmark/results/<profile>/<mode>/.
    # ════════════════════════════════════════════════════════════════════════
    if (-not $SkipBenchmark) {
        Write-Header "Phase 4 — Benchmark sweep  ($($TrainProfiles.Count) profiles × 3 modes)"
        $sweepStart = Get-Date

        $sweepLogDir = Join-Path $ScriptRoot "log"
        New-Item -ItemType Directory -Force -Path $sweepLogDir | Out-Null
        $sweepLogFile = Join-Path $sweepLogDir "benchmark_sweep.log"
        Write-Info "Gradle output → $sweepLogFile"
        # Same reason as Phase 3: do NOT tee into $LogFile (held open by $LogStream).
        & $GradleExe "runFullSweep" `
            "-Pprofiles=$BenchProfiles" `
            "-Pmodes=$BenchModes" `
            @HttpArgs `
            "--console=plain" *>&1 |
            Tee-Object -FilePath $sweepLogFile |
            ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -ne 0) {
            throw "runFullSweep failed with exit code $LASTEXITCODE (see $sweepLogFile)"
        } else {
            $elapsed = [int](New-TimeSpan -Start $sweepStart -End (Get-Date)).TotalMinutes
            Write-OK "Benchmark sweep complete in ${elapsed} min"
        }

        # ════════════════════════════════════════════════════════════════════
        # Phase 5 — Analysis
        # ════════════════════════════════════════════════════════════════════
        Write-Header "Phase 5 — Sweep analysis report"

        if ($PythonCmd -eq "py") {
            & py -3 "analysis\sweep_report.py"
        } else {
            & $PythonCmd "analysis\sweep_report.py"
        }

        if ($LASTEXITCODE -eq 0) {
            Write-OK "Analysis complete"
        } else {
            Write-Warn "Analysis script returned non-zero — review output above"
        }

        # ════════════════════════════════════════════════════════════════════
        # Phase 6 — Version artifacts (Phase 12 #10, opt-in)
        # ════════════════════════════════════════════════════════════════════
        if ($VersionResults) {
            Write-Header "Phase 6 — Version artifacts"
            $vaScript = Join-Path $ScriptRoot "scripts\version_artifacts.ps1"
            if (Test-Path -LiteralPath $vaScript) {
                $vaArgs = @(
                    "-RunMode", $RunMode,
                    "-Profiles", $BenchProfiles,
                    "-Modes",    $BenchModes
                )
                if ($PublishResults) { $vaArgs += "-PublishResults" }
                try {
                    & $vaScript @vaArgs
                    Write-OK "Versioning complete"
                } catch {
                    Write-Warn "version_artifacts.ps1 failed: $($_.Exception.Message)"
                }
            } else {
                Write-Warn "scripts\version_artifacts.ps1 not found; skipping versioning."
            }
        }

    } else {
        Write-Header "Phases 4 & 5 — Benchmark + Analysis SKIPPED (-SkipBenchmark)"
    }

    Write-Header "All phases complete  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-OK "Training artefacts : benchmark/results/<profile>/training_stereo_<bool>/"
    Write-OK "Benchmark results  : benchmark/results/<profile>/<mode>/"
    Write-OK "Log                : run_full_project.log"

} catch {
    $script:HadFatalError = $true
    Write-Fail "Fatal error: $_"
    Write-Fail $_.ScriptStackTrace

} finally {

    # ════════════════════════════════════════════════════════════════════════
    # Cleanup — always runs regardless of success or failure
    # ════════════════════════════════════════════════════════════════════════
    Write-Header "Cleanup"

    # Stop all simulator processes
    foreach ($entry in $SimProcs.GetEnumerator()) {
        try {
            if (-not $entry.Value.HasExited) {
                Stop-Process -Id $entry.Value.Id -Force -ErrorAction Stop
                Write-OK "Stopped simulator on port $($entry.Key)"
            }
        } catch {
            Write-Warn "Could not stop port $($entry.Key): $_"
        }
    }

    # Restore ASL files:
    #   - bench ASL         → original structure with new timing params
    #   - QL ASL            → original structure with new timing params
    #     (use_stereotypes reverts to its original value)
    # lab_profiles.asl is no longer modified — active_profile is now passed
    # to taskQl / runFullSweep via system properties (#7).
    # Simulator flow JSON tick changes are intentionally kept so future
    # standalone Node-RED runs use the same safe configuration.

    $absBench = (Resolve-Path $BenchAslPath).Path
    if ($OrigFiles.ContainsKey($absBench)) {
        $r = $OrigFiles[$absBench]
        $r = $r -replace '(?m)^bench_runs\(\d+\)\.',        "bench_runs($($P.bench_runs))."
        $r = $r -replace '(?m)^exec_max_steps\(\d+\)\.',    "exec_max_steps($($P.exec_max_steps_bench))."
        $r = $r -replace '(?m)^exec_delay_ms\(\d+\)\.',     "exec_delay_ms($($P.exec_delay_ms_bench))."
        WriteFile $BenchAslPath $r
        Write-OK "Restored: $BenchAslPath  (timing params preserved)"
    }

    $absQl = (Resolve-Path $QlAslPath).Path
    if ($OrigFiles.ContainsKey($absQl)) {
        $r = $OrigFiles[$absQl]
        $r = $r -replace '(?m)^num_episodes\(\d+\)\.',           "num_episodes($($P.num_episodes))."
        $r = $r -replace '(?m)^max_steps_per_episode\(\d+\)\.',  "max_steps_per_episode($($P.max_steps_per_episode))."
        $r = $r -replace '(?m)^action_delay_ms\(\d+\)\.',        "action_delay_ms($($P.action_delay_ms))."
        $r = $r -replace '(?m)^exec_delay_ms\(\d+\)\.',          "exec_delay_ms($($P.exec_delay_ms_ql))."
        $r = $r -replace '(?m)^exec_max_steps\(\d+\)\.',         "exec_max_steps($($P.exec_max_steps_ql))."
        WriteFile $QlAslPath $r
        Write-OK "Restored: $QlAslPath  (timing params preserved)"
    }

    # Restore lab_profiles.asl (modified in Phase 1 for training_params and
    # per-cell in Phase 3 for active_profile).  Must run in finally so the file
    # is always left clean even when the script exits via a thrown exception.
    # NOTE: avoid the PS7 null-conditional (?.) — keep this compatible with Windows PowerShell 5.1.
    $resolvedProfiles = Resolve-Path $ProfilesAslPath -ErrorAction SilentlyContinue
    $absProfiles = if ($resolvedProfiles) { $resolvedProfiles.Path } else { $null }
    if ($absProfiles -and $OrigFiles.ContainsKey($absProfiles)) {
        WriteFile $ProfilesAslPath $OrigFiles[$absProfiles]
        Write-OK "Restored: $ProfilesAslPath"
    }

    Write-Info "Note: simulator tick=$($P.tick) kept in all flow JSONs."
    Write-Info "      Re-run simulator\generate_flows.ps1 only if you need to regenerate from scratch."

    if ($LogStream) {
        Write-Log "Script exited  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        $LogStream.Flush()
        $LogStream.Dispose()
    }
    if ($_logFs) {
        $_logFs.Dispose()
    }
    if ($script:HadFatalError) {
        exit 1
    } else {
        exit 0
    }
}
