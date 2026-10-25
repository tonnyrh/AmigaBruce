#Requires -Version 5.1
[CmdletBinding()]
param([switch]$LegacyBlockout)
$ErrorActionPreference='Stop'
if(!$LegacyBlockout){
    & (Join-Path $PSScriptRoot 'test-source-movement.ps1')
    & (Join-Path $PSScriptRoot 'test-source-audio.ps1')
    & python (Join-Path $PSScriptRoot 'tools/audit_c64_tests.py')
    if($LASTEXITCODE){throw 'C64 source test audit failed'}
    & (Join-Path $PSScriptRoot 'test-c64-rooms.ps1')
    & (Join-Path $PSScriptRoot 'test-core.ps1')
    Write-Output 'PASS scoped source test audit and room/actor adapter controls; full actor/natural-play parity remains open'
    return
}
throw 'LegacyBlockout comparisons are historical. Use test-parity.ps1 without LegacyBlockout; see docs/TEST_AUDIT_2026-10-25.md.'
