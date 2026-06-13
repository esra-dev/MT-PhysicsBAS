$ErrorActionPreference = 'Stop'
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

function New-FaultyFlow($srcFile, $dstFile, $labelOld, $labelNew, $replacements) {
    $txt = Get-Content -Raw $srcFile
    foreach ($r in $replacements) {
        $old = $r[0]; $new = $r[1]
        if ($txt.IndexOf($old) -lt 0) { throw "PATTERN NOT FOUND in ${srcFile}: '$old'" }
        $txt = $txt.Replace($old, $new)
    }
    $txt = $txt.Replace($labelOld, $labelNew)
    Set-Content -Path $dstFile -Value $txt -NoNewline -Encoding UTF8
    Write-Host "wrote $dstFile"
}

# lab1_f1dead - DEAD Z1Light (kill 400 lux contribution)
New-FaultyFlow 'simulator_flow_lab1.json' 'simulator_flow_lab1_f1dead.json' `
    'Lab_1_Trivial (port 1892)' 'Lab_1_Trivial_F1DEAD (port 1892)' `
    @(,@('z1light ? 400', 'z1light ? 0'))

# lab2_f1dead - DEAD Z1Light
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f1dead.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F1DEAD (port 1893)' `
    @(,@('z1l ? 400', 'z1l ? 0'))

# lab2_f1inv - INVERTED Z1Light
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f1inv.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F1INV (port 1893)' `
    @(,@('z1l ? 400', 'z1l ? -400'))

# lab3_f1dead - DEAD Z1Light (kill BOTH own-zone 400 and cross-zone 150 spill)
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1dead.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1DEAD (port 1894)' `
    @(@('z1l ? 400', 'z1l ? 0'), @('z1l ? 150', 'z1l ? 0'))

# lab3_f1inv - INVERTED Z1Light (negate BOTH contributions)
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1inv.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1INV (port 1894)' `
    @(@('z1l ? 400', 'z1l ? -400'), @('z1l ? 150', 'z1l ? -150'))

# ── MULTI-FAULT variants (several lamps broken at once) ──────────────────────
# Only CAUSES lamps are injected; the healthy blinds (Mediates) stay untouched.

# lab2_f2dead - BOTH task lamps dead (Z1Light + Z2Light kill their 400 lux)
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f2dead.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F2DEAD (port 1893)' `
    @(@('z1l ? 400', 'z1l ? 0'), @('z2l ? 400', 'z2l ? 0'))

# lab2_f2inv - BOTH task lamps inverted (Z1Light + Z2Light negate their 400 lux)
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f2inv.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F2INV (port 1893)' `
    @(@('z1l ? 400', 'z1l ? -400'), @('z2l ? 400', 'z2l ? -400'))

# lab3_f2dead - BOTH task lamps dead (own 400 + cross-zone 150 spill, both lamps).
# Spotlight (+150 both zones) and blinds survive as recovery levers.
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f2dead.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F2DEAD (port 1894)' `
    @(@('z1l ? 400', 'z1l ? 0'), @('z1l ? 150', 'z1l ? 0'), `
      @('z2l ? 400', 'z2l ? 0'), @('z2l ? 150', 'z2l ? 0'))

# lab3_f2inv - BOTH task lamps inverted (own 400 + cross-zone 150 spill, both lamps)
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f2inv.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F2INV (port 1894)' `
    @(@('z1l ? 400', 'z1l ? -400'), @('z1l ? 150', 'z1l ? -150'), `
      @('z2l ? 400', 'z2l ? -400'), @('z2l ? 150', 'z2l ? -150'))

Write-Host "`n--- verify each faulty flow is valid JSON ---"
Get-ChildItem simulator_flow_lab*_f*.json | ForEach-Object {
    $null = Get-Content -Raw $_.FullName | ConvertFrom-Json
    Write-Host ("OK  {0}  ({1} bytes)" -f $_.Name, $_.Length)
}
