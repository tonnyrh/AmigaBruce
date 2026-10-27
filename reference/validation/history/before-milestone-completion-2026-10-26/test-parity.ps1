#Requires -Version 5.1
[CmdletBinding()]
param([switch]$LegacyBlockout)
$ErrorActionPreference='Stop'
if(!$LegacyBlockout){
    & (Join-Path $PSScriptRoot 'test-c64-sprites.ps1')
    & (Join-Path $PSScriptRoot 'test-ninja-wall.ps1')
    & (Join-Path $PSScriptRoot 'test-bombs-entry.ps1')
    & (Join-Path $PSScriptRoot 'test-room8-blasts.ps1')
    & (Join-Path $PSScriptRoot 'test-source-climb.ps1')
    & (Join-Path $PSScriptRoot 'test-moving-net.ps1')
    & (Join-Path $PSScriptRoot 'test-room-reuse.ps1')
    & (Join-Path $PSScriptRoot 'test-c64-ai.ps1')
    & (Join-Path $PSScriptRoot 'test-spawn.ps1')
    & (Join-Path $PSScriptRoot 'test-source-movement.ps1')
    & (Join-Path $PSScriptRoot 'test-source-audio.ps1')
    & (Join-Path $PSScriptRoot 'test-source-dma.ps1')
    & (Join-Path $PSScriptRoot 'test-session.ps1')
    & python (Join-Path $PSScriptRoot 'tools/audit_c64_tests.py')
    if($LASTEXITCODE){throw 'C64 source test audit failed'}
    & (Join-Path $PSScriptRoot 'test-c64-rooms.ps1')
    & python (Join-Path $PSScriptRoot 'tools/audit_room10_electric.py')
    if($LASTEXITCODE){throw 'R10 source trap loop comparison failed'}
    & (Join-Path $PSScriptRoot 'test-scene-copy.ps1')
    & (Join-Path $PSScriptRoot 'test-core.ps1')
    Write-Output 'PASS scoped source test audit and room/actor adapter controls; full actor/natural-play parity remains open'
    return
}
throw 'LegacyBlockout comparisons are historical. Use test-parity.ps1 without LegacyBlockout; see docs/TEST_AUDIT_2026-10-25.md.'
