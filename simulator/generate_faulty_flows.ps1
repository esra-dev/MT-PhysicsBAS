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

# ── Phase 2 EXTENSION — more well-posed lamp cells + blind (Mediates) faults ──
# (1) Symmetric Z2-lamp variants double the well-posed lab3 recovery sample.
# (2) Blind faults are a NEW class: the blind's lux is 0.50*sun (own) + 0.40*sun
#     (cross, lab3 only). DEAD zeros it; INVERTED negates it. The adapt agent
#     catches these on the OPEN action under sun rank >= 2 (QLearner IV-gate).

# lab3_f1dead_z2 - DEAD Z2Light (own 400 + cross-zone 150 spill), symmetric to f1dead
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1dead_z2.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1DEAD_Z2 (port 1894)' `
    @(@('z2l ? 400', 'z2l ? 0'), @('z2l ? 150', 'z2l ? 0'))

# lab3_f1inv_z2 - INVERTED Z2Light (negate own 400 + cross-zone 150), symmetric to f1inv
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1inv_z2.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1INV_Z2 (port 1894)' `
    @(@('z2l ? 400', 'z2l ? -400'), @('z2l ? 150', 'z2l ? -150'))

# lab3_f1bdead - DEAD Z1Blinds (kill own-zone 0.50*sun + cross-zone 0.40*sun)
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1bdead.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1BDEAD (port 1894)' `
    @(@('z1b ? 0.50 * sun', 'z1b ? 0'), @('z1b ? 0.40 * sun', 'z1b ? 0'))

# lab3_f1binv - INVERTED Z1Blinds (negate own-zone 0.50*sun + cross-zone 0.40*sun)
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f1binv.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F1BINV (port 1894)' `
    @(@('z1b ? 0.50 * sun', 'z1b ? -0.50 * sun'), @('z1b ? 0.40 * sun', 'z1b ? -0.40 * sun'))

# lab2_f1bdead - DEAD Z1Blinds in the Intermediate lab (own-zone 0.50*sun; no cross-zone)
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f1bdead.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F1BDEAD (port 1893)' `
    @(,@('z1b ? 0.50 * sun', 'z1b ? 0'))

# lab2_f1binv - INVERTED Z1Blinds in the Intermediate lab (negate own-zone 0.50*sun)
New-FaultyFlow 'simulator_flow_lab2.json' 'simulator_flow_lab2_f1binv.json' `
    'Lab_2_Intermediate (port 1893)' 'Lab_2_Intermediate_F1BINV (port 1893)' `
    @(,@('z1b ? 0.50 * sun', 'z1b ? -0.50 * sun'))

# ── Phase 2.5 — MONITOR emergency-fallback lab ───────────────────────────────
# labmon_f1dead - DEAD primary lamp (kill the +400 lux Z1Light contribution).
# The lamp is the ONLY rank-3 lever, so once it is blacklisted the goal (rank 3)
# is UNREACHABLE. The best achievable state is rank 2 via the monitor
# (25 + 260 = 285 lux). The KG-primed agent must recognise the monitor as a
# WEAK best-effort fallback, proof-gate the degraded goal, and notify the user.
New-FaultyFlow 'simulator_flow_labmon.json' 'simulator_flow_labmon_f1dead.json' `
    'Lab_Monitor_Emergency (port 1899)' 'Lab_Monitor_Emergency_F1DEAD (port 1899)' `
    @(,@('z1l   ? 400 : 0', 'z1l   ? 0 : 0'))

# ── Phase 2.5B — lab3 MULTI-SURVIVOR DEGRADED cell (KG recovery-speed contrast) ─
# lab3_f2dead_lowsun - BOTH task lamps dead (own 400 + cross-zone 150 spill) AND
# the episode sun PINNED to rank-1 (100 lux) instead of being sampled from
# {0,100,400,900}. Rationale:
#   * Killing both lamps alone is NOT robustly degraded: at high sun the blinds
#     (0.50*sun) reach rank 3 on their own (0.50*900 = 450 > 300), so plain
#     lab3_f2dead is degraded only on low-sun episodes — a muddied, sun-conditional
#     cell. Pinning sun low makes the goal UNREACHABLE every episode.
#   * With both lamps gone and sun = 100 the per-zone ceiling is
#     25 + spotlight(150) + own_blind(0.50*100=50) + cross_blind(0.40*100=40)
#     = 265 lux = rank 2. Both zones DEGRADE to rank 2 (nominal rank 3).
#   * Survivors after the two lamps are blacklisted = Z1Blinds, Z2Blinds,
#     Spotlight -> 2^3 = 8 reachability-probe combos, and BOTH zones must be probed.
#   * The Spotlight is REDUNDANT in the clean lab (150 < 300, never sufficient
#     alone, so the agent learns to AVOID it). The fault INVERTS its value: it
#     becomes the ESSENTIAL best-effort lever. Both arms warm-start from the same
#     "avoid-spotlight" clean policy; the KG arm's structural prior (Spotlight
#     Causes light) lets it re-value and reconverge on the spotlight faster than
#     vanilla, which must unlearn by exploration. This is the KG recovery-speed
#     contrast INSIDE a degradation that the single-survivor labmon lab could not
#     show.
New-FaultyFlow 'simulator_flow_lab3.json' 'simulator_flow_lab3_f2dead_lowsun.json' `
    'Lab_3_Complex (port 1894)' 'Lab_3_Complex_F2DEAD_LOWSUN (port 1894)' `
    @(@('z1l ? 400', 'z1l ? 0'), @('z1l ? 150', 'z1l ? 0'), `
      @('z2l ? 400', 'z2l ? 0'), @('z2l ? 150', 'z2l ? 0'), `
      @('sunRanks[Math.floor(Math.random() * sunRanks.length)]', '100'))

# ── Phase 2.5 — labmon2 DUAL-ZONE MULTI-SURVIVOR MONITOR fallback ───────────
# labmon2_f2dead_lowsun - BOTH primary task lamps dead (kill each +400 lux
# contribution) AND the episode sun PINNED to rank-1 (100 lux) instead of being
# sampled from {0,100,400,900}. Rationale:
#   * With both lamps gone and sun = 100 the per-zone ceiling is
#     25 + monitor(200) + blind(0.50*100=50) = 275 lux = rank 2. The nominal
#     rank-3 goal is UNREACHABLE in BOTH zones on EVERY episode.
#   * Survivors after the two lamps are blacklisted = Z1Monitor, Z2Monitor,
#     Z1Blinds, Z2Blinds -> 2^4 = 16 reachability-probe combos, and BOTH zones
#     must be probed. This is the MULTI-SURVIVOR triage the single-zone labmon
#     lab could not show, WITHOUT a spotlight.
#   * The MONITOR (Causes light, rank 2 alone) is the ESSENTIAL best-effort
#     lever in each zone. Both arms warm-start from the same clean policy (which
#     uses the lamp at low sun); the KG arm's structural prior (Monitor Causes
#     light) lets it re-value and reconverge on the monitor faster than vanilla.
New-FaultyFlow 'simulator_flow_labmon2.json' 'simulator_flow_labmon2_f2dead_lowsun.json' `
    'Labmon2_DualMonitor (port 1900)' 'Labmon2_DualMonitor_F2DEAD_LOWSUN (port 1900)' `
    @(@('z1l ? 400', 'z1l ? 0'), `
      @('z2l ? 400', 'z2l ? 0'), `
      @('sunRanks[Math.floor(Math.random() * sunRanks.length)]', '100'))

Write-Host "`n--- verify each faulty flow is valid JSON ---"
Get-ChildItem simulator_flow_lab*_f*.json | ForEach-Object {
    $null = Get-Content -Raw $_.FullName | ConvertFrom-Json
    Write-Host ("OK  {0}  ({1} bytes)" -f $_.Name, $_.Length)
}
