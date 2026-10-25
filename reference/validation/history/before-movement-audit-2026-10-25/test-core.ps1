#Requires -Version 5.1
[CmdletBinding()]
param([switch]$LegacyBlockout)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(-not $vs){throw 'MSVC Build Tools required for host checks'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$testOut=Join-Path $taskRoot '.tmp/core-test'
New-Item -ItemType Directory -Force $testOut | Out-Null
if(-not $LegacyBlockout){
    $command='call "'+$vcvars+'" >nul && cl /nologo /W3 /O2 /Fe:"'+$testOut+'\c64-core.exe" /Fo"'+$testOut+'\\" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\core\presentation.c" "'+$taskRoot+'\core\combat.c" "'+$taskRoot+'\core\rooms.c" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\core\source_audio.c" "'+$taskRoot+'\tests\c64_rooms_test.c"'
    & $env:ComSpec /d /s /c $command
    if($LASTEXITCODE){throw 'Source core compilation failed'}
    $checks=& (Join-Path $testOut 'c64-core.exe')
    if($LASTEXITCODE){throw 'Source core contracts failed'}
    $checks | Write-Output
    $identity=@('tests/contact_fixture.h','core/game.c','core/game.h','core/presentation.c','core/presentation.h','core/combat.c','core/combat.h','core/rooms.c','core/rooms.h','core/room_data.h','core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h','core/c64_sfx.h','core/c64_sound_data.h','core/source_audio.c','core/source_audio.h','core/source_audio_data.h','tests/c64_rooms_test.c','test-core.ps1' | ForEach-Object {
        @{path=$_;sha256=(Get-FileHash (Join-Path $taskRoot $_) -Algorithm SHA256).Hash.ToLower()}
    })
    $report=[ordered]@{date='2026-10-25';status='passed_source_room_integration_and_host_combat_replay';natural_playthrough=$false;c64_combat_parity=$false;output=@($checks);source_files=$identity}
    $report | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $taskRoot 'reference/validation/c64-core.json') -Encoding UTF8
    $legacy=Join-Path $taskRoot 'reference/validation/m3-core.json'
    $archive=Join-Path $taskRoot 'reference/validation/history/before-c64-room-runtime-m3-core.json'
    if((Test-Path -LiteralPath $legacy) -and !(Test-Path -LiteralPath $archive)){Copy-Item -LiteralPath $legacy -Destination $archive}
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $legacy -Encoding UTF8
    return
}
throw 'LegacyBlockout fixtures are retired: their rectangles and immediate-recoil assertions do not describe the source motor. See docs/TEST_AUDIT_2026-10-25.md. Run test-core.ps1 without LegacyBlockout.'
