<#
.SYNOPSIS
    Phase 2 — Fault-Detection / Blacklist / Re-learn orchestrator.

.DESCRIPTION
    For each faulty adapt-profile x mode cell:
      1. Starts the matching FAULTY Node-RED simulator flow on the parent lab's
         port (faulty variants reuse the clean parent's TD + port; only one runs
         at a time).
      2. Waits for the simulator /health endpoint.
      3. Runs `gradlew taskAdapt -Pprofile=<faulty> -Pmode=<ql_true|ql_false>`,
         which warm-loads the clean Phase-1 Q-table, detects the injected fault
         via the KG Expected-vs-Actual check, blacklists the defective component
         (both polarities), and re-learns over the survivors.
      4. Watches the run to completion (recovery CSV written -> .stopMAS) with a
         heartbeat + idle watchdog, then parses the recovery metric.
      5. Stops the faulty flow before moving to the next profile.

    The headline Phase-2 metric is RecoveryEpisodes = ReconvergeEpisode -
    DetectEpisode (lower = faster re-alignment). The thesis claim is that the
    KG-primed arm (ql_true) recovers faster than tabula-rasa (ql_false).

    Per-profile/mode maps are read from config/run_config.json (phase2 block).
    This script does NOT modify the Phase-1 runner or any .asl source; the
    re-learn budget is overridden purely via -Padapt.episodes (consumed
    numerically by tools.jia.system_prop_num in the adapt agent).

.PARAMETER AdaptProfiles
    Comma-separated subset of faulty profiles to run. Empty (default) = all
    profiles listed in config phase2.adapt_profiles.

.PARAMETER Modes
    Comma-separated subset of {ql_true, ql_false}. Default = both.

.PARAMETER Episodes
    Explicit re-learn budget (episodes) for every cell. 0 (default) = use each
    profile's training_params value from lab_profiles.asl. Any value > 0 is
    forwarded as -Padapt.episodes.

.PARAMETER Smoke
    Fast pipeline check: overrides Episodes with config phase2.smoke_episodes
    (default 200) unless -Episodes is given explicitly. Verifies the full
    detect -> blacklist -> warm-restart -> re-learn -> recovery-CSV -> stopMAS
    path without waiting for full convergence.

.EXAMPLE
    .\run_phase2_adapt.ps1 -Smoke -AdaptProfiles lab2_f1dead -Modes ql_true
    .\run_phase2_adapt.ps1
    .\run_phase2_adapt.ps1 -AdaptProfiles lab2_f1dead,lab2_f1inv

.NOTES
    Target shell: Windows PowerShell 5.1+ (also works under PowerShell 7+).
    Do not use PS7-only syntax here — no null-conditional (?.), null-coalescing
    (??), ternary (a ? b : c), or native command chaining (&&, ||).
#>

param(
    [string]$AdaptProfiles = "",
    [string]$Modes = "ql_true,ql_false",
    [int]$Episodes = 0,
    [switch]$Smoke,
    [int]$WatchdogIdleSec = 1200,
    [int]$SimReadyTimeoutSec = 90,
    # Per-run RNG seed forwarded as -Prun.seed (XORed into QLearner's baseSeed).
    # -1 (default) leaves the seed unset so the JVM uses its built-in default;
    # CI passes distinct seeds for paired multi-replica statistics.
    [int]$RunSeed = -1
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

# ─── Logging ──────────────────────────────────────────────────────────────────
$LogFile   = Join-Path $ScriptRoot "run_phase2_adapt.log"
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

# ─── Tool resolution ──────────────────────────────────────────────────────────
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

# ─── Config ───────────────────────────────────────────────────────────────────
$CfgPath = Join-Path $ScriptRoot "config\run_config.json"
if (-not (Test-Path $CfgPath)) { Write-Fail "Missing config: $CfgPath"; exit 1 }
$Cfg = Get-Content -Raw $CfgPath | ConvertFrom-Json
$P2  = $Cfg.phase2
if ($null -eq $P2) { Write-Fail "config/run_config.json has no 'phase2' block"; exit 1 }

# Resolve the smoke budget (config-driven, with a safe fallback).
$SmokeEpisodes = 200
if ($P2.smoke_episodes) { $SmokeEpisodes = [int]$P2.smoke_episodes }

# Effective per-cell episode override (-Padapt.episodes). 0 => profile default.
$EffEpisodes = $Episodes
if ($Smoke -and $Episodes -le 0) { $EffEpisodes = $SmokeEpisodes }

# Profile / mode selection.
if ($AdaptProfiles.Trim() -ne "") {
    $ProfileList = $AdaptProfiles.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
} else {
    $ProfileList = @($P2.adapt_profiles)
}
$ModeList = $Modes.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

# ─── Simulator health check ───────────────────────────────────────────────────
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

# Read any new key marker lines from a gradle cell log and echo them.
$TailFilter = '\[FAULT\]|DEFECTIVE|Blacklisted|Warm restart|Warm-loaded|Re-CONVERGED|Recovery metric|action space now|BUILD (FAILED|SUCCESSFUL)|All done'
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

# ─── State ────────────────────────────────────────────────────────────────────
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
    Write-Header "MT-Esra Phase 2 — Fault-Detection / Blacklist / Re-learn  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    Write-OK   "node-red : $NodeRedCmd"
    Write-OK   "gradle   : $GradleExe"
    Write-OK   "profiles : $($ProfileList -join ', ')"
    Write-OK   "modes    : $($ModeList -join ', ')"
    if ($EffEpisodes -gt 0) {
        Write-OK "episodes : $EffEpisodes (override via -Padapt.episodes)"
    } else {
        Write-OK "episodes : per-profile training_params default"
    }

    $cellLogDir = Join-Path $ScriptRoot "log"
    New-Item -ItemType Directory -Force -Path $cellLogDir | Out-Null

    foreach ($profile in $ProfileList) {
        $port       = Map-Get $P2.simulator_port_map  $profile
        $flow       = Map-Get $P2.simulator_flow_map   $profile
        $qtSuffix   = Map-Get $P2.qtable_suffix_map     $profile
        $cleanSfx   = Map-Get $P2.clean_source_suffix   $profile
        $parentName = Map-Get $P2.parent_profile        $profile

        if ($null -eq $port -or $null -eq $flow -or $null -eq $qtSuffix -or $null -eq $cleanSfx) {
            Write-Warn "Skipping '$profile' — incomplete phase2 config (port/flow/qtable_suffix/clean_source_suffix)."
            continue
        }
        $port = [int]$port

        Write-Header "Profile $profile  (parent=$parentName  port=$port  flow=$flow)"

        # ── Start the FAULTY Node-RED flow (reuse if already answering) ──
        $flowAbs = Join-Path $ScriptRoot "simulator\$flow"
        $userDir = Join-Path $ScriptRoot ".node-red-$profile"
        $weLaunched = $false

        if (Wait-Simulator -Port $port -TimeoutSec 3) {
            Write-Warn "Port $port already answering — reusing the running simulator (NOT killed on cleanup)."
            Write-Warn "         Ensure it is the FAULTY flow for $profile, not the clean lab."
        } elseif (-not (Test-Path $flowAbs)) {
            Write-Fail "Flow file missing — skipping $profile : $flowAbs"
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
            Write-Info "Launched faulty flow  port=$port  PID=$($proc.Id)"
            if (-not (Wait-Simulator -Port $port -TimeoutSec $SimReadyTimeoutSec)) {
                Write-Fail "Simulator $profile did not become ready within $SimReadyTimeoutSec s on port $port — skipping."
                continue
            }
            Write-OK "Simulator $profile ready on port $port"
        }

        foreach ($mode in $ModeList) {
            $bool = Mode-Bool $mode
            Write-Header "Cell  $profile / $mode  (stereo=$bool)"

            # Warm-load source sanity check (cold start is tolerated but warned).
            $cleanZone1 = Join-Path $ScriptRoot ("qtable_final_stereotypes_{0}{1}_zone1.csv" -f $bool, $cleanSfx)
            if (-not (Test-Path $cleanZone1)) {
                Write-Warn "Clean Phase-1 Q-table not found ($([System.IO.Path]::GetFileName($cleanZone1)))."
                Write-Warn "         The adapt agent will COLD-START (zero Q-table). For a proper warm-restart"
                Write-Warn "         result, train the parent lab '$parentName' first (Phase 1)."
            }

            # Output artefacts for this cell (recovery CSV is APPEND-mode, so we
            # must delete a stale one to read a clean single-row result).
            $recoveryFile = Join-Path $ScriptRoot ("recovery_stereotypes_{0}{1}.csv"        -f $bool, $qtSuffix)
            $adaptedFile  = Join-Path $ScriptRoot ("qtable_adapted_stereotypes_{0}{1}.csv"  -f $bool, $qtSuffix)
            $metricsFile  = Join-Path $ScriptRoot ("metrics_adapted_stereotypes_{0}{1}.csv" -f $bool, $qtSuffix)
            foreach ($stale in @($recoveryFile, $adaptedFile, $metricsFile)) {
                if (Test-Path $stale) { Remove-Item $stale -Force -ErrorAction SilentlyContinue }
            }

            $cellLog = Join-Path $cellLogDir "adapt_${profile}_${mode}.log"
            $cellErr = Join-Path $cellLogDir "adapt_${profile}_${mode}.err.log"
            if (Test-Path $cellLog) { Remove-Item $cellLog -Force -ErrorAction SilentlyContinue }
            if (Test-Path $cellErr) { Remove-Item $cellErr -Force -ErrorAction SilentlyContinue }
            Write-Info "Gradle output -> $cellLog"

            $gArgs = @("taskAdapt", "-Pprofile=$profile", "-Pmode=$mode")
            if ($EffEpisodes -gt 0) { $gArgs += "-Padapt.episodes=$EffEpisodes" }
            if ($RunSeed -ge 0)     { $gArgs += "-Prun.seed=$RunSeed" }
            $gArgs += "--console=plain"

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

            # ── Watchdog: recovery CSV appearing == logically done (the agent
            #    writes it immediately before .stopMAS). JaCaMo can hang in its
            #    post-run event loop, so once the CSV exists and the JVM has been
            #    idle for a grace window we terminate it and continue. ──
            $tailPos             = 0L
            $heartbeatEverySec   = 60
            $postCompleteIdleSec = 90
            $lastHeartbeat = Get-Date
            $lastLogGrowth = Get-Date
            $lastLogLength = 0
            $completedGracefully = $false

            while (-not $gProc.HasExited) {
                Start-Sleep -Seconds 10
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

                # Completion: recovery CSV written and JVM idle since.
                if (Test-Path $recoveryFile) {
                    $idleNow = (New-TimeSpan -Start $lastLogGrowth -End $now).TotalSeconds
                    if ($idleNow -ge $postCompleteIdleSec) {
                        Write-Warn "Recovery CSV present and JVM idle ${postCompleteIdleSec}s — terminating JaCaMo and continuing."
                        try { if (-not $gProc.HasExited) { Stop-Process -Id $gProc.Id -Force -ErrorAction Stop } } catch { }
                        $completedGracefully = $true
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

            # ── Parse the recovery metric ──
            $status     = "FAIL"
            $detectEp   = ""
            $reconvEp   = ""
            $recovery   = ""
            $defectComp = ""
            if (Test-Path $recoveryFile) {
                try {
                    $row = Import-Csv $recoveryFile | Select-Object -Last 1
                    if ($row) {
                        $defectComp = $row.DefectComponent
                        $detectEp   = $row.DetectEpisode
                        $reconvEp   = $row.ReconvergeEpisode
                        $recovery   = $row.RecoveryEpisodes
                        $status     = "OK"
                    }
                } catch {
                    Write-Warn "Could not parse $recoveryFile : $_"
                }
            }

            $elapsedMin = [int](New-TimeSpan -Start $cellStart -End (Get-Date)).TotalMinutes
            if ($status -eq "OK") {
                $detPretty = "none"; if ([int]$detectEp -ge 0) { $detPretty = [string]([int]$detectEp + 1) }
                $recPretty = $recovery; if ([int]$recovery -lt 0) { $recPretty = "N/A" }
                Write-OK "Done in ${elapsedMin}m  defect=$defectComp  detect=$detPretty  reconverge=$reconvEp  recovery=$recPretty"
            } else {
                Write-Fail "No recovery CSV produced for $profile/$mode (see $cellLog)"
                $script:HadFatalError = $true
            }

            $Summary += [pscustomobject]@{
                Profile   = $profile
                Mode      = $mode
                Defect    = $defectComp
                DetectEp  = $detectEp
                ReconvEp  = $reconvEp
                Recovery  = $recovery
                Status    = $status
                Minutes   = $elapsedMin
            }
        }

        # ── Stop the faulty flow for this profile (only if we launched it) ──
        if ($weLaunched -and $SimProcs.ContainsKey($port)) {
            try {
                if (-not $SimProcs[$port].HasExited) {
                    Stop-Process -Id $SimProcs[$port].Id -Force -ErrorAction Stop
                    Write-OK "Stopped faulty flow on port $port"
                }
            } catch { Write-Warn "Could not stop port $port : $_" }
            $SimProcs.Remove($port)
        }
    }

    # ─── Summary ──────────────────────────────────────────────────────────────
    Write-Header "Phase 2 summary"
    if ($Summary.Count -gt 0) {
        $tbl = $Summary | Format-Table Profile, Mode, Defect, DetectEp, ReconvEp, Recovery, Status, Minutes -AutoSize | Out-String
        foreach ($l in ($tbl -split "`r?`n")) { if ($l.Trim() -ne "") { Write-Log $l } }
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
        Write-Fail "Phase 2 run finished WITH errors — review $LogFile"
    } else {
        Write-OK "Phase 2 run finished cleanly."
    }
    if ($LogStream) { $LogStream.Flush(); $LogStream.Close() }
}

if ($script:HadFatalError) { exit 1 } else { exit 0 }
