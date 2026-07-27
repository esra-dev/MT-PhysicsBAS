[CmdletBinding()]
param(
    [string]$OutputPath = "analysis/out/phase1b_live_flow_smoke.json"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Specs = @(
    @{ Profile = "labrel0";    Port = 1904; Flow = "simulator_flow_labrel0.json" },
    @{ Profile = "labrel4";    Port = 1905; Flow = "simulator_flow_labrel4.json" },
    @{ Profile = "labrel8";    Port = 1906; Flow = "simulator_flow_labrel8.json" },
    @{ Profile = "labrel16";   Port = 1907; Flow = "simulator_flow_labrel16.json" },
    @{ Profile = "labrel8s";   Port = 1908; Flow = "simulator_flow_labrel8s.json" },
    @{ Profile = "labband";    Port = 1912; Flow = "simulator_flow_labband.json" },
    @{ Profile = "lab4chain3"; Port = 1913; Flow = "simulator_flow_lab4chain3.json" }
)

function Test-PortOpen {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(300)) { return $false }
        $client.EndConnect($pending)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

$node = Get-Command "node.exe" -ErrorAction SilentlyContinue
if (-not $node) { $node = Get-Command "node" -ErrorAction SilentlyContinue }
$npm = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
if (-not $npm) { $npm = Get-Command "npm" -ErrorAction SilentlyContinue }
if (-not $node -or -not $npm) {
    throw "node/npm not found; install Node.js and Node-RED 4"
}
$globalNodeModules = (& $npm.Source root -g).ToString().Trim()
$nodeRedScript = Join-Path $globalNodeModules "node-red/red.js"
if (-not (Test-Path -LiteralPath $nodeRedScript)) {
    throw "Node-RED runtime not found at $nodeRedScript; install with: npm install -g --unsafe-perm node-red@4"
}

$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command "python3" -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python 3 not found"
}

foreach ($spec in $Specs) {
    if (Test-PortOpen -Port $spec.Port) {
        throw "Port $($spec.Port) is already occupied; refusing to test an unidentified service"
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
    "phase1b-flow-smoke-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
$processes = @()

try {
    foreach ($spec in $Specs) {
        $flow = Join-Path $RepoRoot (Join-Path "simulator" $spec.Flow)
        $userDir = Join-Path $tempRoot $spec.Profile
        $stdout = Join-Path $tempRoot ($spec.Profile + ".stdout.log")
        $stderr = Join-Path $tempRoot ($spec.Profile + ".stderr.log")
        New-Item -ItemType Directory -Path $userDir | Out-Null

        $start = @{
            FilePath = $node.Source
            ArgumentList = "`"$nodeRedScript`" --userDir `"$userDir`" --port $($spec.Port) `"$flow`""
            RedirectStandardOutput = $stdout
            RedirectStandardError = $stderr
            PassThru = $true
        }
        if ($IsWindows -or ($null -eq $IsWindows -and $env:OS -eq "Windows_NT")) {
            $start.WindowStyle = "Hidden"
        }
        $processes += Start-Process @start
    }

    $version = (& $node.Source $nodeRedScript --version 2>&1 |
        Select-Object -First 1).ToString().Trim()
    Push-Location $RepoRoot
    try {
        & $python.Source analysis/phase1b_flow_smoke.py `
            --root $RepoRoot `
            --output $OutputPath `
            --node-red-version $version
        if ($LASTEXITCODE -ne 0) {
            throw "Phase-1b flow probe failed with exit code $LASTEXITCODE"
        }
    } finally {
        Pop-Location
    }
} finally {
    foreach ($process in $processes) {
        try {
            if (-not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction Stop
                $null = $process.WaitForExit(5000)
            }
        } catch {
            Write-Warning "Could not stop Node-RED process $($process.Id): $_"
        }
    }
    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
        $resolvedSystemTemp = [System.IO.Path]::GetFullPath(
            [System.IO.Path]::GetTempPath())
        $leaf = Split-Path -Leaf $resolvedTempRoot
        if (-not $resolvedTempRoot.StartsWith(
                $resolvedSystemTemp,
                [System.StringComparison]::OrdinalIgnoreCase) -or
            -not $leaf.StartsWith("phase1b-flow-smoke-")) {
            throw "Refusing to remove unexpected temporary path: $resolvedTempRoot"
        }
        $removed = $false
        for ($attempt = 1; $attempt -le 5 -and -not $removed; $attempt++) {
            try {
                Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force -ErrorAction Stop
                $removed = $true
            } catch {
                if ($attempt -lt 5) { Start-Sleep -Milliseconds 200 }
            }
        }
        if (-not $removed) {
            Write-Warning "Could not remove temporary smoke directory: $resolvedTempRoot"
        }
    }
}
