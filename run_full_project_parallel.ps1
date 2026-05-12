<#
.SYNOPSIS
    Parallel orchestrator for the MT-Esra project. Trains and benchmarks
    multiple profiles concurrently in isolated clone working copies.

.DESCRIPTION
    The single-process script run_full_project.ps1 runs all 12 training cells
    sequentially because every cell mutates shared files in the project root
    (lab_profiles.asl, illuminance_controller_agent_ql.asl, qtable_*.csv at
    root, the Gradle 'build/' tree). Two cells running in parallel inside the
    same working copy would corrupt those files.

    This orchestrator removes the contention by giving each profile its own
    clone of the project, and only running cells *across* clones in parallel.
    Within a clone, the two stereotype modes still run sequentially (which is
    safe — they share the same project root only with each other, and the
    original script already serializes them).

    Layout:

        <orchestrator>\         ← this script lives here. Runs simulators and
                                  the final analysis. Never trains in parallel
                                  with itself.
        ..\<orchestrator>-clones\
            custom2\            ← full clone, trains custom2 only
            custom3\
            ...
            custom7\

    Phases:
      A. Pre-flight + Phase 1 (timing patches) in orchestrator dir
      B. Phase 2: launch 6 Node-RED simulators in orchestrator dir
      C. Sync clones (robocopy /MIR with exclusions for build/, .gradle/,
         logs, qtable artefacts, .node-red-*, .git)
      D. Phase 3 — training: throttled parallel jobs, one per profile.
         Each job calls run_full_project.ps1 -OnlyProfiles <p> -SkipBenchmark
         inside its clone. The clone reuses the orchestrator's simulators
         (Wait-Simulator detects them on the standard ports).
      E. Pull training artefacts from clones back into orchestrator
         (benchmark/results/<profile>/training_stereo_*/)
      F. Phase 4 — benchmark sweep: throttled parallel jobs, one per profile,
         each running gradlew runFullSweep -Pprofiles=<p> -Pmodes=...
         inside its clone (with training artefacts pre-synced if missing).
      G. Pull benchmark results from clones back into orchestrator
         (benchmark/results/<profile>/<mode>/)
      H. Phase 5 — analysis (single Python invocation in orchestrator)
      I. Cleanup: stop simulators we launched.

.PARAMETER RunMode
    "dev" or "paper". Forwarded to each clone's run_full_project.ps1.

.PARAMETER MaxParallel
    How many clones to run concurrently. Default 3. Each parallel cell uses
    roughly 1.5–2 GB of RAM (Gradle daemon + Jason JVM + Node-RED traffic).

    Recommended values for a 12-core / 16 GB box:
      MaxParallel=2  : safest, ~10 GB peak, very comfortable headroom
      MaxParallel=3  : default, ~12 GB peak, recommended
      MaxParallel=4  : aggressive, ~14 GB peak, close swap risk if any
                       browser / IDE is also running. Watch it the first time.

    Going above 4 on 16 GB will start swapping and slow everything down. The
    upper bound is also capped at the number of profiles (6).

.PARAMETER SkipTraining
    Skip Phase D + E. Use when training artefacts already exist in the
    orchestrator (benchmark/results/<profile>/training_stereo_*/TRAINING_OK.json
    present for every cell).

.PARAMETER SkipBenchmark
    Skip Phase F + G + H.

.PARAMETER RefreshClones
    Force fresh /MIR sync of every clone, even if it already exists.
    Without this flag, robocopy /MIR still mirrors the source tree, but the
    flag also wipes the clone's build/ and .gradle/ first to guarantee a
    clean Gradle build.

.PARAMETER ClonesRoot
    Where to put the clones. Default: sibling of orchestrator named
    "<orchestrator-folder>-clones".

.EXAMPLE
    .\run_full_project_parallel.ps1
    .\run_full_project_parallel.ps1 -MaxParallel 4
    .\run_full_project_parallel.ps1 -RunMode paper -MaxParallel 2
    .\run_full_project_parallel.ps1 -SkipTraining   # only benchmark
#>

param(
    [ValidateSet("dev","paper")]
    [string]$RunMode = "dev",

    [ValidateRange(1,6)]
    [int]$MaxParallel = 3,

    [switch]$SkipTraining,
    [switch]$SkipBenchmark,
    [switch]$RefreshClones,

    [string]$ClonesRoot = ""
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

if (-not $ClonesRoot) {
    $parent      = Split-Path -Parent $ScriptRoot
    $myName      = Split-Path -Leaf   $ScriptRoot
    $ClonesRoot  = Join-Path $parent "$myName-clones"
}

# ─── Project layout (must match run_full_project.ps1) ─────────────────────────
$Profiles = @("custom2","custom3","custom4","custom5","custom6","custom7")
$BenchModes = "rule_based,ql_false,ql_true"
$StereoModes = @("true","false")

$Simulators = @(
    [pscustomobject]@{ Profile="custom2"; Port=1882; Flow="simulator_flow_custom2.json" }
    [pscustomobject]@{ Profile="custom3"; Port=1883; Flow="simulator_flow_custom3.json" }
    [pscustomobject]@{ Profile="custom4"; Port=1884; Flow="simulator_flow_custom4.json" }
    [pscustomobject]@{ Profile="custom5"; Port=1885; Flow="simulator_flow_custom5.json" }
    [pscustomobject]@{ Profile="custom6"; Port=1886; Flow="simulator_flow_custom6.json" }
    [pscustomobject]@{ Profile="custom7"; Port=1887; Flow="simulator_flow_custom7.json" }
)

# ─── Logging ─────────────────────────────────────────────────────────────────
$LogFile = Join-Path $ScriptRoot "run_full_project_parallel.log"
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Open with FileShare.ReadWrite so external tools can tail the log without
# blocking us, but no other code in this script writes to $LogFile so there
# is no contention to worry about (unlike the sequential script's earlier bug).
$_logFs    = [System.IO.FileStream]::new(
    $LogFile,
    [System.IO.FileMode]::Create,
    [System.IO.FileAccess]::Write,
    [System.IO.FileShare]::ReadWrite)
$LogStream = [System.IO.StreamWriter]::new($_logFs, $Utf8NoBom)

function Write-Log {
    param([string]$msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    if ($LogStream) { $LogStream.WriteLine($line); $LogStream.Flush() }
    Write-Host $line
}
function Write-Header { param([string]$msg)
    $bar = "═" * 60
    Write-Log ""; Write-Log $bar; Write-Log "  $msg"; Write-Log $bar
}
function Write-OK   { param([string]$msg) Write-Log "  [OK]  $msg" }
function Write-Info { param([string]$msg) Write-Log "  [..] $msg" }
function Write-Warn { param([string]$msg) Write-Log "  [!!] $msg" }
function Write-Fail { param([string]$msg) Write-Log "  [XX] $msg" }

# ─── Health check ────────────────────────────────────────────────────────────
function Wait-Simulator {
    param([int]$Port, [int]$TimeoutSec = 90)
    # Prefer /health (lightweight). Fall back to /was/rl/status for flows
    # that pre-date the /health endpoint.
    $healthUrl = "http://127.0.0.1:$Port/health"
    $statusUrl = "http://127.0.0.1:$Port/was/rl/status"
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
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

# ─── Robocopy clone sync ─────────────────────────────────────────────────────
# Robocopy returns:
#   0    nothing copied (no changes)
#   1    files copied
#   2    extra files/dirs detected
#   3    1+2
#   4-7  warnings, still successful
#   >=8  failure
function Invoke-Robocopy {
    param([string]$Src, [string]$Dst, [string[]]$ExcludeDirs, [string[]]$ExcludeFiles)
    $rcArgs = @($Src, $Dst, "/MIR", "/R:2", "/W:2", "/NFL", "/NDL", "/NP", "/NJH", "/NJS", "/MT:8")
    if ($ExcludeDirs -and $ExcludeDirs.Count -gt 0) {
        $rcArgs += "/XD"
        $rcArgs += $ExcludeDirs
    }
    if ($ExcludeFiles -and $ExcludeFiles.Count -gt 0) {
        $rcArgs += "/XF"
        $rcArgs += $ExcludeFiles
    }
    & robocopy @rcArgs | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed: src=$Src dst=$Dst exit=$LASTEXITCODE"
    }
    # Robocopy uses 0-7 as success codes; reset so callers don't see a benign 1/3 as error.
    $global:LASTEXITCODE = 0
}

function Sync-CloneFromOrchestrator {
    param([string]$Profile, [string]$CloneDir, [bool]$Refresh)

    if ($Refresh -and (Test-Path $CloneDir)) {
        # Wipe build state so Gradle starts clean. Source tree is re-mirrored
        # by the robocopy below.
        foreach ($d in @("build", ".gradle")) {
            $p = Join-Path $CloneDir $d
            if (Test-Path $p) { Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }
    New-Item -ItemType Directory -Force -Path $CloneDir | Out-Null

    $excludeDirs = @(
        (Join-Path $ScriptRoot "build"),
        (Join-Path $ScriptRoot ".gradle"),
        (Join-Path $ScriptRoot ".git"),
        (Join-Path $ScriptRoot "log"),
        (Join-Path $ScriptRoot "bin"),
        (Join-Path $ScriptRoot "benchmark\results"),
        (Join-Path $ScriptRoot ".node-red-custom2"),
        (Join-Path $ScriptRoot ".node-red-custom3"),
        (Join-Path $ScriptRoot ".node-red-custom4"),
        (Join-Path $ScriptRoot ".node-red-custom5"),
        (Join-Path $ScriptRoot ".node-red-custom6"),
        (Join-Path $ScriptRoot ".node-red-custom7"),
        (Join-Path $ScriptRoot "dashboard\node_modules")
    )
    # Files at root that are training/benchmark artefacts of previous runs;
    # excluding them keeps clones small and avoids stale Q-tables polluting
    # a fresh run inside the clone.
    $excludeFiles = @(
        "qtable_*.csv",
        "metrics_*.csv",
        "iv_stats_*.json",
        "coverage_*.csv",
        "first_goal_*.csv",
        "learned_*.ttl",
        "benchmark_results_*.csv",
        "bench_step_log_*.csv",
        "java_pid*.hprof",
        "*.hprof",
        ".stop___MAS",
        "run_full_project*.log",
        "nr_*_out.txt",
        "nr_*_err.txt"
    )
    Invoke-Robocopy -Src $ScriptRoot -Dst $CloneDir -ExcludeDirs $excludeDirs -ExcludeFiles $excludeFiles
}

# ─── Manifest helpers (mirror run_full_project.ps1) ──────────────────────────
function Test-ProfileFullyTrained {
    param([string]$Root, [string]$Profile)
    foreach ($s in $StereoModes) {
        $m = Join-Path $Root "benchmark\results\$Profile\training_stereo_$s\TRAINING_OK.json"
        if (-not (Test-Path $m)) { return $false }
    }
    return $true
}

# ─── Pre-flight ──────────────────────────────────────────────────────────────
Write-Header "MT-Esra parallel run  |  mode=$RunMode  |  parallel=$MaxParallel  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-OK "Orchestrator : $ScriptRoot"
Write-OK "Clones root  : $ClonesRoot"

# Verify node-red, python, robocopy, gradlew
$_nrCmd = Get-Command "node-red.cmd" -ErrorAction SilentlyContinue
if (-not $_nrCmd) { $_nrCmd = Get-Command "node-red" -ErrorAction SilentlyContinue }
if (-not $_nrCmd) {
    Write-Fail "node-red not found in PATH. Install with: npm install -g node-red"
    $LogStream.Close(); exit 1
}
$NodeRedCmd = $_nrCmd.Source

$PythonCmd = if (Get-Command "py" -ErrorAction SilentlyContinue) { "py" }
             elseif (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" }
             elseif (Get-Command "python" -ErrorAction SilentlyContinue) { "python" }
             else { $null }
if (-not $PythonCmd) { Write-Fail "Python 3 not found in PATH"; $LogStream.Close(); exit 1 }

if (-not (Get-Command "robocopy" -ErrorAction SilentlyContinue)) {
    Write-Fail "robocopy not found (it ships with Windows by default)."
    $LogStream.Close(); exit 1
}
if (-not (Test-Path (Join-Path $ScriptRoot "gradlew.bat"))) {
    Write-Fail "gradlew.bat not found in orchestrator dir."
    $LogStream.Close(); exit 1
}
if (-not (Test-Path (Join-Path $ScriptRoot "run_full_project.ps1"))) {
    Write-Fail "run_full_project.ps1 not found alongside this script."
    $LogStream.Close(); exit 1
}

Write-OK "node-red : $NodeRedCmd"
Write-OK "python   : $PythonCmd"
Write-OK "RAM cap  : MaxParallel=$MaxParallel  (≈ $($MaxParallel * 2) GB peak JVM RSS)"

$SimProcs = @{}

try {

    # ════════════════════════════════════════════════════════════════════════
    # Phase A — Apply timing parameters in orchestrator dir
    # We delegate to run_full_project.ps1 with -SkipTraining -SkipBenchmark
    # so it only does Phase 1 + Phase 2 + Cleanup. But Cleanup stops the
    # simulators *we* would need running. Easier: do Phase 1 inline here by
    # having the existing script's Phase 1 code... actually, simplest of all
    # is to just call run_full_project.ps1 -OnlyProfiles <single> in each
    # clone, which does its own Phase 1 internally (idempotent).
    #
    # So Phase A here just needs to start the simulators. Phase 1 happens
    # inside each clone (same patches applied identically). The clones then
    # reuse our simulators because Phase 2 of the clone's script detects
    # them on the standard ports and skips re-launching.
    # ════════════════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════════════════
    # Phase B — Start Node-RED simulators in orchestrator dir
    # ════════════════════════════════════════════════════════════════════════
    Write-Header "Phase B — Starting Node-RED simulators in orchestrator"

    # Pre-patch simulator flow JSONs so the simulators we launch use the
    # right tick (mirrors run_full_project.ps1's Phase 1a logic). This is a
    # one-shot patch in the orchestrator dir; clones get their own copy on
    # sync and patch it again themselves (idempotent).
    $tick = if ($RunMode -eq "paper") { "0.2" } else { "0.05" }
    foreach ($sim in $Simulators) {
        $flowPath = Join-Path $ScriptRoot "simulator\$($sim.Flow)"
        if (-not (Test-Path $flowPath)) {
            Write-Warn "Flow file missing: $($sim.Flow)"
            continue
        }
        $content = [System.IO.File]::ReadAllText($flowPath, $Utf8NoBom)
        $patched = $content -replace '(?<="repeat"\s*:\s*)"[0-9.]+"', "`"$tick`""
        if ($patched -ne $content) {
            [System.IO.File]::WriteAllText($flowPath, $patched, $Utf8NoBom)
        }
    }

    foreach ($sim in $Simulators) {
        $flowAbs = Join-Path $ScriptRoot "simulator\$($sim.Flow)"
        $userDir = Join-Path $ScriptRoot ".node-red-$($sim.Profile)"

        if (Wait-Simulator -Port $sim.Port -TimeoutSec 3) {
            Write-OK "$($sim.Profile)  :$($sim.Port)  already running — reusing"
            continue
        }
        if (-not (Test-Path $flowAbs)) {
            Write-Warn "Flow missing — skipping: $($sim.Flow)"
            continue
        }
        New-Item -ItemType Directory -Force -Path $userDir | Out-Null
        $proc = Start-Process `
            -FilePath $NodeRedCmd `
            -ArgumentList "--userDir `"$userDir`" --port $($sim.Port) `"$flowAbs`"" `
            -PassThru -WindowStyle Hidden
        $SimProcs[$sim.Port] = $proc
        Write-Info "Launched $($sim.Profile)  port=$($sim.Port)  PID=$($proc.Id)"
    }

    Write-Info "Waiting for newly-launched simulators (up to 90 s each)..."
    foreach ($sim in $Simulators) {
        if (-not $SimProcs.ContainsKey($sim.Port)) { continue }
        if (Wait-Simulator -Port $sim.Port -TimeoutSec 90) {
            Write-OK "$($sim.Profile)  :$($sim.Port)  ready"
        } else {
            throw "Simulator $($sim.Profile) did not start within 90 s on port $($sim.Port)"
        }
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase C — Sync clones
    # ════════════════════════════════════════════════════════════════════════
    if ((-not $SkipTraining) -or (-not $SkipBenchmark)) {
        Write-Header "Phase C — Syncing $($Profiles.Count) clones to $ClonesRoot"
        New-Item -ItemType Directory -Force -Path $ClonesRoot | Out-Null
        foreach ($profile in $Profiles) {
            $cloneDir = Join-Path $ClonesRoot $profile
            $syncStart = Get-Date
            Sync-CloneFromOrchestrator -Profile $profile -CloneDir $cloneDir -Refresh:$RefreshClones

            # Force --no-daemon for every gradlew invocation in the clone.
            # Parallel daemons across clones would contend on the shared
            # ~/.gradle daemon registry, occasionally producing flaky build
            # failures. Disabling the daemon adds ~5 s startup per invocation,
            # negligible against multi-hour training cells.
            $gp = Join-Path $cloneDir "gradle.properties"
            $gpContent = if (Test-Path $gp) { Get-Content -Raw -Path $gp } else { "" }
            if ($gpContent -notmatch '(?m)^\s*org\.gradle\.daemon\s*=') {
                $gpContent = ($gpContent.TrimEnd() + "`norg.gradle.daemon=false`n").TrimStart()
                [System.IO.File]::WriteAllText($gp, $gpContent, $Utf8NoBom)
            }

            $secs = [int](New-TimeSpan -Start $syncStart -End (Get-Date)).TotalSeconds
            Write-OK "Synced clone: $cloneDir  (${secs}s)"
        }
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase D — Training (parallel across profiles, sequential within)
    #
    # Each job runs run_full_project.ps1 inside its clone with
    #   -OnlyProfiles <p> -SkipBenchmark
    # so the clone's script does Phase 1 + Phase 2 (reuses our simulators) +
    # Phase 3 for that one profile (2 stereo cells, sequential within).
    # ════════════════════════════════════════════════════════════════════════
    if (-not $SkipTraining) {
        Write-Header "Phase D — Training  ($($Profiles.Count) profiles in parallel, max $MaxParallel concurrent)"

        # Skip profiles that are already fully trained at orchestrator level.
        $toTrain = @()
        foreach ($p in $Profiles) {
            if (Test-ProfileFullyTrained -Root $ScriptRoot -Profile $p) {
                Write-OK "Already trained at orchestrator level — skipping: $p"
            } else {
                $toTrain += $p
            }
        }

        if ($toTrain.Count -gt 0) {
            $jobScript = {
                param($CloneDir, $Profile, $RunMode)
                Set-Location $CloneDir
                # Pipe both streams; capture exit code in clone's exit code.
                & ".\run_full_project.ps1" `
                    -RunMode $RunMode `
                    -OnlyProfiles $Profile `
                    -SkipBenchmark *>&1
                # PowerShell jobs return whatever was emitted; we additionally
                # surface the exit code via a marker line the parent can grep.
                "PARALLEL_JOB_EXIT_CODE=$LASTEXITCODE"
            }

            $jobs = @{}    # jobId -> @{Profile=...; LogPath=...}
            $queue = New-Object System.Collections.Queue
            foreach ($p in $toTrain) { $queue.Enqueue($p) }

            $logDir = Join-Path $ScriptRoot "log\parallel"
            New-Item -ItemType Directory -Force -Path $logDir | Out-Null

            $startCloneJob = {
                param($Profile)
                $cloneDir = Join-Path $ClonesRoot $Profile
                $logPath  = Join-Path $logDir "train_${Profile}.log"
                Write-Info "Launching training job: profile=$Profile  log=$logPath"
                $j = Start-Job -ScriptBlock $jobScript -ArgumentList $cloneDir, $Profile, $RunMode
                $jobs[$j.Id] = @{ Profile=$Profile; LogPath=$logPath; CloneDir=$cloneDir }
                return $j
            }

            # Prime the pool
            $primeCount = [Math]::Min($MaxParallel, $queue.Count)
            for ($i = 0; $i -lt $primeCount; $i++) {
                & $startCloneJob $queue.Dequeue() | Out-Null
            }

            $failures = @()
            while ($jobs.Count -gt 0) {
                $jobIds = @($jobs.Keys | ForEach-Object { [int]$_ })
                $finished = Wait-Job -Job (Get-Job -Id $jobIds) -Any
                $info = $jobs[$finished.Id]
                # Drain output to log file
                $output = Receive-Job -Job $finished -Keep -ErrorAction SilentlyContinue
                $output | Out-File -FilePath $info.LogPath -Encoding utf8 -Append
                $exitLine = $output | Where-Object { $_ -is [string] -and $_ -match '^PARALLEL_JOB_EXIT_CODE=' } | Select-Object -Last 1
                $exitCode = if ($exitLine) { [int]($exitLine -replace '^PARALLEL_JOB_EXIT_CODE=','') } else { -1 }

                if ($finished.State -ne 'Completed' -or $exitCode -ne 0) {
                    Write-Fail "Training FAILED for $($info.Profile)  state=$($finished.State)  exit=$exitCode  log=$($info.LogPath)"
                    $failures += $info.Profile
                } else {
                    Write-OK "Training done : $($info.Profile)  log=$($info.LogPath)"
                }
                Remove-Job -Job $finished -Force
                $jobs.Remove($finished.Id)

                # Refill the pool
                if ($queue.Count -gt 0) {
                    & $startCloneJob $queue.Dequeue() | Out-Null
                }
            }

            if ($failures.Count -gt 0) {
                throw "Training failed for: $($failures -join ', '). See log\parallel\ for details."
            }
        } else {
            Write-OK "All profiles already trained — nothing to do in Phase D."
        }

        # ════════════════════════════════════════════════════════════════════
        # Phase E — Pull training artefacts from clones into orchestrator
        # ════════════════════════════════════════════════════════════════════
        Write-Header "Phase E — Collecting training artefacts from clones"

        foreach ($p in $Profiles) {
            $cloneDir = Join-Path $ClonesRoot $p
            $srcDir   = Join-Path $cloneDir "benchmark\results\$p"
            $dstDir   = Join-Path $ScriptRoot "benchmark\results\$p"
            if (-not (Test-Path $srcDir)) {
                # Profile may have been skipped because already trained at
                # orchestrator level. Verify and continue.
                if (Test-ProfileFullyTrained -Root $ScriptRoot -Profile $p) {
                    Write-OK "$p : artefacts already in orchestrator (skipped clone)"
                    continue
                }
                throw "Clone for $p has no training results dir: $srcDir"
            }
            New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
            # Mirror only the training_stereo_* subtrees; do not delete other
            # subdirs in dst (e.g. ql_true) that may exist from earlier runs.
            foreach ($s in $StereoModes) {
                $src = Join-Path $srcDir "training_stereo_$s"
                $dst = Join-Path $dstDir "training_stereo_$s"
                if (Test-Path $src) {
                    Invoke-Robocopy -Src $src -Dst $dst
                    Write-OK "$p : training_stereo_$s -> orchestrator"
                } else {
                    throw "Missing training output for $p stereo=$s : $src"
                }
            }
        }
    } else {
        Write-Header "Phase D + E — Training SKIPPED (-SkipTraining)"
        # Make sure orchestrator has all 12 manifests before benchmarking
        foreach ($p in $Profiles) {
            if (-not (Test-ProfileFullyTrained -Root $ScriptRoot -Profile $p)) {
                throw "-SkipTraining was set but profile '$p' is not fully trained in orchestrator (missing TRAINING_OK manifests)."
            }
        }
        Write-OK "Orchestrator has TRAINING_OK manifests for all 12 cells."
    }

    # ════════════════════════════════════════════════════════════════════════
    # Phase F — Benchmark sweep (parallel across profiles)
    #
    # Each job runs in its clone:
    #   gradlew runFullSweep -Pprofiles=<p> -Pmodes=rule_based,ql_false,ql_true
    #
    # Pre-step: sync orchestrator's training artefacts into the clone in
    # case the clone was wiped or only partially has them. The Q-tables that
    # runFullSweep reads live at the clone's project root after training,
    # so we also restore those root-level CSVs.
    # ════════════════════════════════════════════════════════════════════════
    if (-not $SkipBenchmark) {
        Write-Header "Phase F — Benchmark sweep  ($($Profiles.Count) profiles in parallel, max $MaxParallel concurrent)"

        # Ensure each clone has its training artefacts (root-level qtables and
        # benchmark/results/<p>/training_stereo_*).
        Write-Info "Pre-syncing training artefacts orchestrator -> clones..."
        foreach ($p in $Profiles) {
            $cloneDir = Join-Path $ClonesRoot $p
            if (-not (Test-Path $cloneDir)) {
                throw "Clone missing for $p (run without -SkipTraining first or remove -SkipTraining): $cloneDir"
            }

            # 1. Mirror training_stereo_* archives
            $orchTrainDir = Join-Path $ScriptRoot "benchmark\results\$p"
            $cloneTrainDir = Join-Path $cloneDir   "benchmark\results\$p"
            New-Item -ItemType Directory -Force -Path $cloneTrainDir | Out-Null
            foreach ($s in $StereoModes) {
                $src = Join-Path $orchTrainDir  "training_stereo_$s"
                $dst = Join-Path $cloneTrainDir "training_stereo_$s"
                if (-not (Test-Path $src)) {
                    throw "Orchestrator missing training_stereo_$s for $p — cannot benchmark"
                }
                Invoke-Robocopy -Src $src -Dst $dst
            }

            # 2. Restore root-level qtable CSVs (taskBench reads these from
            # project root). Copy from the archived training_stereo_*/ dirs.
            foreach ($s in $StereoModes) {
                $arch = Join-Path $cloneTrainDir "training_stereo_$s"
                Get-ChildItem -Path $arch -Filter "qtable_*.csv" -ErrorAction SilentlyContinue | ForEach-Object {
                    Copy-Item -Path $_.FullName -Destination (Join-Path $cloneDir $_.Name) -Force
                }
                # Also stereotype TTL & metrics, harmless and useful for clone-side analysis
                Get-ChildItem -Path $arch -Filter "learned_*.ttl" -ErrorAction SilentlyContinue | ForEach-Object {
                    Copy-Item -Path $_.FullName -Destination (Join-Path $cloneDir $_.Name) -Force
                }
            }
        }
        Write-OK "Pre-sync complete."

        $benchScript = {
            param($CloneDir, $Profile, $Modes)
            Set-Location $CloneDir
            # --no-daemon avoids cross-clone Gradle daemon registry contention.
            & ".\gradlew.bat" "runFullSweep" `
                "-Pprofiles=$Profile" `
                "-Pmodes=$Modes" `
                "--no-daemon" `
                "--console=plain" *>&1
            "PARALLEL_JOB_EXIT_CODE=$LASTEXITCODE"
        }

        $bjobs  = @{}
        $bqueue = New-Object System.Collections.Queue
        foreach ($p in $Profiles) { $bqueue.Enqueue($p) }

        $blogDir = Join-Path $ScriptRoot "log\parallel"
        New-Item -ItemType Directory -Force -Path $blogDir | Out-Null

        $startBenchJob = {
            param($Profile)
            $cloneDir = Join-Path $ClonesRoot $Profile
            $logPath  = Join-Path $blogDir "bench_${Profile}.log"
            Write-Info "Launching benchmark job: profile=$Profile  log=$logPath"
            $j = Start-Job -ScriptBlock $benchScript -ArgumentList $cloneDir, $Profile, $BenchModes
            $bjobs[$j.Id] = @{ Profile=$Profile; LogPath=$logPath; CloneDir=$cloneDir }
            return $j
        }

        $primeCount = [Math]::Min($MaxParallel, $bqueue.Count)
        for ($i = 0; $i -lt $primeCount; $i++) {
            & $startBenchJob $bqueue.Dequeue() | Out-Null
        }

        $bfailures = @()
        while ($bjobs.Count -gt 0) {
            $jobIds = @($bjobs.Keys | ForEach-Object { [int]$_ })
            $finished = Wait-Job -Job (Get-Job -Id $jobIds) -Any
            $info = $bjobs[$finished.Id]
            $output = Receive-Job -Job $finished -Keep -ErrorAction SilentlyContinue
            $output | Out-File -FilePath $info.LogPath -Encoding utf8 -Append
            $exitLine = $output | Where-Object { $_ -is [string] -and $_ -match '^PARALLEL_JOB_EXIT_CODE=' } | Select-Object -Last 1
            $exitCode = if ($exitLine) { [int]($exitLine -replace '^PARALLEL_JOB_EXIT_CODE=','') } else { -1 }

            if ($finished.State -ne 'Completed' -or $exitCode -ne 0) {
                Write-Fail "Benchmark FAILED for $($info.Profile)  state=$($finished.State)  exit=$exitCode  log=$($info.LogPath)"
                $bfailures += $info.Profile
            } else {
                Write-OK "Benchmark done : $($info.Profile)  log=$($info.LogPath)"
            }
            Remove-Job -Job $finished -Force
            $bjobs.Remove($finished.Id)

            if ($bqueue.Count -gt 0) {
                & $startBenchJob $bqueue.Dequeue() | Out-Null
            }
        }

        if ($bfailures.Count -gt 0) {
            throw "Benchmark failed for: $($bfailures -join ', '). See log\parallel\ for details."
        }

        # ════════════════════════════════════════════════════════════════════
        # Phase G — Pull benchmark results from clones into orchestrator
        # ════════════════════════════════════════════════════════════════════
        Write-Header "Phase G — Collecting benchmark results from clones"

        $modeDirs = $BenchModes -split ','
        foreach ($p in $Profiles) {
            $cloneDir   = Join-Path $ClonesRoot $p
            $srcRoot    = Join-Path $cloneDir   "benchmark\results\$p"
            $dstRoot    = Join-Path $ScriptRoot "benchmark\results\$p"
            New-Item -ItemType Directory -Force -Path $dstRoot | Out-Null
            foreach ($m in $modeDirs) {
                $src = Join-Path $srcRoot $m.Trim()
                $dst = Join-Path $dstRoot $m.Trim()
                if (Test-Path $src) {
                    Invoke-Robocopy -Src $src -Dst $dst
                    Write-OK "$p : $($m.Trim()) -> orchestrator"
                } else {
                    Write-Warn "$p : $($m.Trim()) missing in clone — runFullSweep may have skipped it"
                }
            }
        }

        # ════════════════════════════════════════════════════════════════════
        # Phase H — Analysis (orchestrator)
        # ════════════════════════════════════════════════════════════════════
        Write-Header "Phase H — Sweep analysis report"

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
    } else {
        Write-Header "Phase F + G + H — Benchmark + Analysis SKIPPED (-SkipBenchmark)"
    }

    Write-Header "All phases complete  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-OK "Training artefacts : benchmark/results/<profile>/training_stereo_<bool>/"
    Write-OK "Benchmark results  : benchmark/results/<profile>/<mode>/"
    Write-OK "Per-profile logs   : log\parallel\{train,bench}_<profile>.log"
    Write-OK "Orchestrator log   : $LogFile"

} catch {
    Write-Fail "Fatal error: $_"
    Write-Fail $_.ScriptStackTrace

} finally {
    Write-Header "Cleanup"

    # Stop any orphaned jobs
    Get-Job -ErrorAction SilentlyContinue | ForEach-Object {
        try { Stop-Job -Job $_ -ErrorAction SilentlyContinue; Remove-Job -Job $_ -Force -ErrorAction SilentlyContinue } catch {}
    }

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

    if ($LogStream) {
        Write-Log "Script exited  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        $LogStream.Flush(); $LogStream.Dispose()
    }
    if ($_logFs) { $_logFs.Dispose() }
}
