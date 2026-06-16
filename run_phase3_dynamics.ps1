<#
.SYNOPSIS
    Phase 3 - Response-Delay Learning / Time-Bounded Exploitation orchestrator.

.DESCRIPTION
    For each slow dynamics-profile x mode cell:
      1. Starts the matching SLOW Node-RED simulator flow on the profile's
         dedicated port (lab2_slow -> 1895, lab3_slow -> 1896). These ports and
         ontologies are dedicated so Phase 1/2 stay untouched.
      2. Waits for the simulator /health endpoint.
      3. Runs `gradlew taskDynamics -Pprofile=<slow> -Pmode=<ql_true|ql_false>`,
         which probes every actuator to learn its response delay (fast lamp ~0
         ticks; slow motorized blind ~blind_delay_ticks), writes the learned
         ws:responseDelay back to the Knowledge Graph, then runs a time-bounded
         benchmark choosing actuators with (ql_true) or without (ql_false) the
         learned delay knowledge.
      4. Watches the run to completion (timebounded results CSV written ->
         .stopMAS) with a heartbeat + idle watchdog.
      5. Parses the delay table (learned blind ticks vs ground truth) and the
         time-bounded results (deadline-compliance rate + energy).
      6. Stops the slow flow before moving to the next profile.

    Headline Phase-3 metrics:
      * delay-learning accuracy: learned blind delay (ticks) vs the simulator's
        ground-truth blind_delay_ticks.
      * deadline compliance: the KG-primed arm (ql_true) should meet the tight
        deadlines (lamp) AND save energy on the loose ones (blind), while the
        tabula-rasa arm (ql_false) misses the tight deadlines (it grabs the
        cheap-but-slow blind, unaware of its delay).

    Per-profile/mode maps are read from config/run_config.json (phase3 block).
    This script modifies no .asl source; probe cadence + sample budget are
    forwarded purely via -P system properties.

.PARAMETER DynamicsProfiles
    Comma-separated subset of slow profiles to run. Empty (default) = all
    profiles listed in config phase3.dynamics_profiles.

.PARAMETER Modes
    Comma-separated subset of {ql_true, ql_false}. Default = both.

.PARAMETER Probes
    Explicit per-actuator delay-sample budget (-Pprobe.count). 0 (default) =
    use config phase3.probe.probes_per_actuator.

.PARAMETER Smoke
    Fast pipeline check: overrides Probes with config phase3.smoke_probes
    (default 3) unless -Probes is given. Verifies the full probe -> KG-writeback
    -> exploit -> results-CSV -> stopMAS path quickly.

.EXAMPLE
    .\run_phase3_dynamics.ps1 -Smoke -DynamicsProfiles lab2_slow -Modes ql_true
    .\run_phase3_dynamics.ps1
    .\run_phase3_dynamics.ps1 -DynamicsProfiles lab2_slow,lab3_slow

.NOTES
    Target shell: Windows PowerShell 5.1+ (also works under PowerShell 7+).
    Do not use PS7-only syntax here - no null-conditional (?.), null-coalescing
    (??), ternary (a ? b : c), or native command chaining (&&, ||).
    ASCII-only by design (no BOM dependency).
#>

param(
    [string]$DynamicsProfiles = "",
    [string]$Modes = "ql_true,ql_false",
    [int]$Probes = 0,
    [switch]$Smoke,
    [int]$WatchdogIdleSec = 600,
    [int]$SimReadyTimeoutSec = 90
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# --- Logging ----------------------------------------------------------------
$LogFile   = Join-Path $ScriptRoot "run_phase3_dynamics.log"
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
$LogStream = New-Object System.IO.StreamWriter(
    [System.IO.FileStream]::new($LogFile,
        [System.IO.FileMode]::Append,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite), $Utf8NoBom)

function Write-Log {
    param([string]$msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    if ($LogStream) { $LogStream.WriteLine($line); $LogStream.Flush() }
    Write-Host $line
}
function Write-Header { param([string]$msg)
    $bar = "=" * 64
    Write-Log ""; Write-Log $bar; Write-Log "  $msg"; Write-Log $bar
}
function Write-OK   { param([string]$msg) Write-Log "  [OK]  $msg" }
function Write-Info { param([string]$msg) Write-Log "  [..] $msg" }
function Write-Warn { param([string]$msg) Write-Log "  [!!] $msg" }
function Write-Fail { param([string]$msg) Write-Log "  [XX] $msg" }

# --- Tool resolution --------------------------------------------------------
if ($env:OS -eq 'Windows_NT') {
    $GradleExe = Join-Path $ScriptRoot 'gradlew.bat'
} else {
    $GradleExe = Join-Path $ScriptRoot 'gradlew'
}

# On Windows, node-red.ps1 is NOT in PATHEXT so Start-Process would open it as
# text. Resolve node-red.cmd explicitly (runs via cmd.exe, stays alive for the
# child node process lifetime).
$_nrCmd = Get-Command "node-red.cmd" -ErrorAction SilentlyContinue
if (-not $_nrCmd) { $_nrCmd = Get-Command "node-red" -ErrorAction SilentlyContinue }
if (-not $_nrCmd) {
    Write-Fail "node-red not found in PATH. Install it with:  npm install -g node-red"
    if ($LogStream) { $LogStream.Close() }
    exit 1
}
$NodeRedCmd = $_nrCmd.Source

# --- Config -----------------------------------------------------------------
$CfgPath = Join-Path $ScriptRoot "config\run_config.json"
if (-not (Test-Path $CfgPath)) { Write-Fail "Missing config: $CfgPath"; exit 1 }
$Cfg = Get-Content -Raw $CfgPath | ConvertFrom-Json
$P3  = $Cfg.phase3
if ($null -eq $P3) { Write-Fail "config/run_config.json has no 'phase3' block"; exit 1 }

# Probe cadence / budget (config-driven, with safe fallbacks).
$SecondsPerTick = 5.0
if ($P3.seconds_per_tick) { $SecondsPerTick = [double]$P3.seconds_per_tick }
$GroundTruthTicks = 12
if ($P3.blind_delay_ticks) { $GroundTruthTicks = [int]$P3.blind_delay_ticks }
$SmokeProbes = 3
if ($P3.smoke_probes) { $SmokeProbes = [int]$P3.smoke_probes }

$ProbesDefault = 8; $SettleMs = 400; $PollMs = 50; $MaxWaitTicks = 60
if ($P3.probe) {
    if ($P3.probe.probes_per_actuator) { $ProbesDefault = [int]$P3.probe.probes_per_actuator }
    if ($P3.probe.settle_ms)           { $SettleMs      = [int]$P3.probe.settle_ms }
    if ($P3.probe.poll_ms)             { $PollMs        = [int]$P3.probe.poll_ms }
    if ($P3.probe.max_wait_ticks)      { $MaxWaitTicks  = [int]$P3.probe.max_wait_ticks }
}

# Effective per-cell probe budget (-Pprobe.count). 0 => config default.
$EffProbes = $Probes
if ($EffProbes -le 0) { $EffProbes = $ProbesDefault }
if ($Smoke -and $Probes -le 0) { $EffProbes = $SmokeProbes }

# Profile / mode selection.
if ($DynamicsProfiles.Trim() -ne "") {
    $ProfileList = $DynamicsProfiles.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
} else {
    $ProfileList = @($P3.dynamics_profiles)
}
if ($Modes.Trim() -ne "") {
    $ModeList = $Modes.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
} else {
    $ModeList = @($P3.dynamics_modes)
}

# --- Simulator health check -------------------------------------------------
function Wait-Simulator {
    param([int]$Port, [int]$TimeoutSec = 90)
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

# Read new key marker lines from a gradle cell log and echo them.
$TailFilter = '\[Probe\]|\[Dynamics\]|\[Exploit\]|\[RuntimeOverride\]|first-effect delay|wrote |PHASE 3 DYNAMICS COMPLETE|BUILD (FAILED|SUCCESSFUL)'
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
            if ($tLine -match $TailFilter) { Write-Info "  >> $($tLine.Trim())" }
        }
        $PosRef.Value = [long]$fs.Position
        $sr.Dispose(); $fs.Dispose()
    } catch { }
}

# --- State ------------------------------------------------------------------
$SimProcs = @{}   # port -> process (only flows WE launched, so cleanup is safe)
$Summary  = @()   # result rows for the final table
$script:HadFatalError = $false

# Helper: map mode -> the boolean string used in artefact filenames.
function Mode-Bool { param([string]$mode)
    if ($mode -eq 'ql_true') { return 'true' } else { return 'false' }
}

# Helper: look up a value on a PSCustomObject map by dynamic key (or $null).
function Map-Get { param($map, [string]$key)
    if ($null -eq $map) { return $null }
    $prop = $map.PSObject.Properties[$key]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}

try {
    Write-Header "MT-Esra Phase 3 - Response-Delay Learning / Time-Bounded Exploitation  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-OK   "node-red : $NodeRedCmd"
    Write-OK   "gradle   : $GradleExe"
    Write-OK   "profiles : $($ProfileList -join ', ')"
    Write-OK   "modes    : $($ModeList -join ', ')"
    Write-OK   "probes   : $EffProbes per actuator  (seconds/tick=$SecondsPerTick, ground-truth blind=$GroundTruthTicks ticks)"

    $cellLogDir = Join-Path $ScriptRoot "log"
    New-Item -ItemType Directory -Force -Path $cellLogDir | Out-Null

    foreach ($profile in $ProfileList) {
        $port = Map-Get $P3.simulator_port_map $profile
        $flow = Map-Get $P3.simulator_flow_map $profile

        if ($null -eq $port -or $null -eq $flow) {
            Write-Warn "Skipping '$profile' - incomplete phase3 config (port/flow)."
            continue
        }
        $port = [int]$port

        Write-Header "Profile $profile  (port=$port  flow=$flow)"

        # -- Start the SLOW Node-RED flow (reuse if already answering) --
        $flowAbs = Join-Path $ScriptRoot "simulator\$flow"
        $userDir = Join-Path $ScriptRoot ".node-red-$profile"
        $weLaunched = $false

        if (Wait-Simulator -Port $port -TimeoutSec 3) {
            Write-Warn "Port $port already answering - reusing the running simulator (NOT killed on cleanup)."
            Write-Warn "         Ensure it is the SLOW flow for $profile."
        } elseif (-not (Test-Path $flowAbs)) {
            Write-Fail "Flow file missing - skipping $profile : $flowAbs"
            continue
        } else {
            New-Item -ItemType Directory -Force -Path $userDir | Out-Null
            $spArgs = @{
                FilePath     = $NodeRedCmd
                ArgumentList = "--userDir `"$userDir`" --port $port `"$flowAbs`""
                PassThru     = $true
            }
            if ($IsWindows -or ($null -eq $IsWindows -and $env:OS -eq 'Windows_NT')) {
                $spArgs.WindowStyle = 'Hidden'
            }
            $proc = Start-Process @spArgs
            $SimProcs[$port] = $proc
            $weLaunched = $true
            Write-Info "Launched slow flow  port=$port  PID=$($proc.Id)"
            if (-not (Wait-Simulator -Port $port -TimeoutSec $SimReadyTimeoutSec)) {
                Write-Fail "Simulator $profile did not become ready within $SimReadyTimeoutSec s on port $port - skipping."
                continue
            }
            Write-OK "Simulator $profile ready on port $port"
        }

        foreach ($mode in $ModeList) {
            $bool = Mode-Bool $mode
            Write-Header "Cell  $profile / $mode  (planner KG-primed=$bool)"

            # Output artefacts for this cell. The results CSV is the completion
            # marker (written last, immediately before .stopMAS).
            $ttlFile     = Join-Path $ScriptRoot ("learned_dynamics_{0}_{1}.ttl"    -f $bool, $profile)
            $delayFile   = Join-Path $ScriptRoot ("dynamics_delays_{0}_{1}.csv"     -f $bool, $profile)
            $resultsFile = Join-Path $ScriptRoot ("timebounded_results_{0}_{1}.csv" -f $bool, $profile)
            foreach ($stale in @($ttlFile, $delayFile, $resultsFile)) {
                if (Test-Path $stale) { Remove-Item $stale -Force -ErrorAction SilentlyContinue }
            }

            $cellLog = Join-Path $cellLogDir "dynamics_${profile}_${mode}.log"
            $cellErr = Join-Path $cellLogDir "dynamics_${profile}_${mode}.err.log"
            if (Test-Path $cellLog) { Remove-Item $cellLog -Force -ErrorAction SilentlyContinue }
            if (Test-Path $cellErr) { Remove-Item $cellErr -Force -ErrorAction SilentlyContinue }
            Write-Info "Gradle output -> $cellLog"

            $gArgs = @("taskDynamics", "-Pprofile=$profile", "-Pmode=$mode",
                       "-Pseconds.per.tick=$SecondsPerTick",
                       "-Pprobe.count=$EffProbes",
                       "-Pprobe.settle.ms=$SettleMs",
                       "-Pprobe.poll.ms=$PollMs",
                       "-Pprobe.max.wait.ticks=$MaxWaitTicks",
                       "--console=plain")

            $gpArgs = @{
                FilePath               = $GradleExe
                ArgumentList           = $gArgs
                WorkingDirectory       = $ScriptRoot
                RedirectStandardOutput = $cellLog
                RedirectStandardError  = $cellErr
                PassThru               = $true
            }
            if ($IsWindows -or ($null -eq $IsWindows -and $env:OS -eq 'Windows_NT')) {
                $gpArgs.WindowStyle = 'Hidden'
            }
            $cellStart = Get-Date
            $gProc = Start-Process @gpArgs

            # -- Watchdog: results CSV appearing == logically done (the agent
            #    writes it immediately before .stopMAS). JaCaMo can hang in its
            #    post-run event loop, so once the CSV exists and the JVM has been
            #    idle for a grace window we terminate it and continue. --
            $tailPos             = 0L
            $heartbeatEverySec   = 60
            $postCompleteIdleSec = 60
            $lastHeartbeat = Get-Date
            $lastLogGrowth = Get-Date
            $lastLogLength = 0

            while (-not $gProc.HasExited) {
                Start-Sleep -Seconds 5
                Invoke-TailLog -LogPath $cellLog -PosRef ([ref]$tailPos)
                $now = Get-Date

                $logLength = 0
                if (Test-Path $cellLog) {
                    $gi = Get-Item -LiteralPath $cellLog -ErrorAction SilentlyContinue
                    if ($gi) { $logLength = $gi.Length }
                }
                if ($logLength -gt $lastLogLength) { $lastLogGrowth = $now; $lastLogLength = $logLength }

                if ((New-TimeSpan -Start $lastHeartbeat -End $now).TotalSeconds -ge $heartbeatEverySec) {
                    $elapsedMin = [int](New-TimeSpan -Start $cellStart -End $now).TotalMinutes
                    $idleSec    = [int](New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds
                    Write-Info "[Heartbeat] $profile/$mode elapsed=${elapsedMin}m idle=${idleSec}s pid=$($gProc.Id)"
                    $lastHeartbeat = $now
                }

                # Completion: results CSV written and JVM idle since.
                if (Test-Path $resultsFile) {
                    $idleNow = (New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds
                    if ($idleNow -ge $postCompleteIdleSec) {
                        Write-Warn "Results CSV present and JVM idle ${postCompleteIdleSec}s - terminating JaCaMo and continuing."
                        try { if (-not $gProc.HasExited) { Stop-Process -Id $gProc.Id -Force -ErrorAction Stop } } catch { }
                        break
                    }
                }

                $idleNow = (New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds
                if ($idleNow -ge $WatchdogIdleSec) {
                    try { if (-not $gProc.HasExited) { Stop-Process -Id $gProc.Id -Force -ErrorAction Stop } } catch { }
                    Write-Fail "Watchdog timeout for $profile/${mode}: no log growth for $WatchdogIdleSec s (see $cellLog)"
                    break
                }
            }

            try { $gProc.Refresh() } catch { }
            try { [void]$gProc.WaitForExit(60000) } catch { }
            Invoke-TailLog -LogPath $cellLog -PosRef ([ref]$tailPos)

            # Merge stderr tail into the cell log for post-mortem.
            if ((Test-Path $cellErr) -and (Get-Item $cellErr -ErrorAction SilentlyContinue).Length -gt 0) {
                "`n--- STDERR ---`n" | Out-File -FilePath $cellLog -Encoding utf8 -Append
                Get-Content $cellErr -ErrorAction SilentlyContinue | Out-File -FilePath $cellLog -Encoding utf8 -Append
            }

            # -- Parse the time-bounded results + delay table --
            $status     = "FAIL"
            $metStr     = ""
            $energyStr  = ""
            $blindStr   = ""
            if (Test-Path $resultsFile) {
                try {
                    $rows = @(Import-Csv $resultsFile)
                    if ($rows.Count -gt 0) {
                        $met   = ($rows | Where-Object { $_.met -eq '1' }).Count
                        $total = $rows.Count
                        $metStr = "$met/$total"
                        $energySum = 0.0
                        foreach ($r in $rows) {
                            $e = 0.0
                            if ([double]::TryParse($r.energy_cost, [ref]$e)) { $energySum += $e }
                        }
                        $energyStr = "{0:N1}" -f $energySum
                        $status = "OK"
                    }
                } catch {
                    Write-Warn "Could not parse $resultsFile : $_"
                }
            }
            if (Test-Path $delayFile) {
                try {
                    $drows = @(Import-Csv $delayFile)
                    $maxTicks = -1.0
                    foreach ($d in $drows) {
                        $t = -1.0
                        if ([double]::TryParse($d.delay_ticks, [ref]$t)) {
                            if ($t -gt $maxTicks) { $maxTicks = $t }
                        }
                    }
                    if ($maxTicks -ge 0) {
                        $blindStr = ("{0:N1}/{1}" -f $maxTicks, $GroundTruthTicks)
                    }
                } catch {
                    Write-Warn "Could not parse $delayFile : $_"
                }
            }

            $elapsedMin = [int](New-TimeSpan -Start $cellStart -End (Get-Date)).TotalMinutes
            if ($status -eq "OK") {
                Write-OK "Done in ${elapsedMin}m  met=$metStr  energy=$energyStr  blindTicks(learned/truth)=$blindStr"
            } else {
                Write-Fail "No time-bounded results CSV produced for $profile/$mode (see $cellLog)"
                $script:HadFatalError = $true
            }

            $Summary += [pscustomobject]@{
                Profile    = $profile
                Mode       = $mode
                Met        = $metStr
                Energy     = $energyStr
                BlindTicks = $blindStr
                Status     = $status
                Minutes    = $elapsedMin
            }
        }

        # -- Stop the slow flow for this profile (only if we launched it) --
        if ($weLaunched -and $SimProcs.ContainsKey($port)) {
            try {
                if (-not $SimProcs[$port].HasExited) {
                    Stop-Process -Id $SimProcs[$port].Id -Force -ErrorAction Stop
                    Write-OK "Stopped slow flow on port $port"
                }
            } catch { Write-Warn "Could not stop port $port : $_" }
            $SimProcs.Remove($port)
        }
    }

    # --- Summary ----------------------------------------------------------------
    Write-Header "Phase 3 summary"
    if ($Summary.Count -gt 0) {
        $tbl = $Summary | Format-Table Profile, Mode, Met, Energy, BlindTicks, Status, Minutes -AutoSize | Out-String
        foreach ($l in ($tbl -split "`r?`n")) { if ($l.Trim() -ne "") { Write-Log $l } }
        Write-Log ""
        Write-Log "  Met = time-bounded goals met / total (deadline compliance)."
        Write-Log "  BlindTicks = learned slowest-actuator delay / ground-truth blind_delay_ticks."
        Write-Log "  Expectation: ql_true meets MORE tight-deadline goals than ql_false."
    } else {
        Write-Warn "No cells ran."
    }

} catch {
    $script:HadFatalError = $true
    Write-Fail "Fatal error: $_"
    Write-Fail $_.ScriptStackTrace
} finally {
    Write-Header "Cleanup"
    foreach ($entry in $SimProcs.GetEnumerator()) {
        try {
            if (-not $entry.Value.HasExited) {
                Stop-Process -Id $entry.Value.Id -Force -ErrorAction Stop
                Write-OK "Stopped simulator on port $($entry.Key)"
            }
        } catch { Write-Warn "Could not stop port $($entry.Key): $_" }
    }
    if ($script:HadFatalError) {
        Write-Fail "Phase 3 run finished WITH errors - review $LogFile"
    } else {
        Write-OK "Phase 3 run finished cleanly."
    }
    if ($LogStream) { $LogStream.Flush(); $LogStream.Close() }
}

if ($script:HadFatalError) { exit 1 } else { exit 0 }
