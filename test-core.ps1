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
    $command='call "'+$vcvars+'" >nul && cl /nologo /W3 /O2 /Fe:"'+$testOut+'\c64-core.exe" /Fo"'+$testOut+'\\" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\core\source_wall.c" "'+$taskRoot+'\core\source_climb.c" "'+$taskRoot+'\core\presentation.c" "'+$taskRoot+'\core\c64_sprites.c" "'+$taskRoot+'\core\combat.c" "'+$taskRoot+'\core\rooms.c" "'+$taskRoot+'\core\session.c" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\core\source_audio.c" "'+$taskRoot+'\tests\c64_rooms_test.c"'
    & $env:ComSpec /d /s /c $command
    if($LASTEXITCODE){throw 'Source core compilation failed'}
    $checks=& (Join-Path $testOut 'c64-core.exe')
    if($LASTEXITCODE){throw 'Source core contracts failed'}
    $checks | Write-Output
    $identity=@('tests/spawn_fixture.h','tests/spawn_bridge.c','tools/audit_spawn.py','tools/audit_spawn_world.py','tools/build_spawn_fixture.py','test-spawn.ps1','tests/room8_blast_fixture.h','tools/audit_room8_blasts.py','test-room8-blasts.ps1','tests/bombs_entry_fixture.h','tools/audit_bombs_entry.py','test-bombs-entry.ps1','core/c64_hit_data.h','tools/build_c64_hit_masks.py','tools/audit_ninja_wall.py','tests/ninja_wall_fixture.h','tests/ninja_wall_bridge.c','test-ninja-wall.ps1','core/session.c','core/session.h','tests/cheat_progress_fixture.h','tests/session_fixture.h','tests/session_wall_fixture.h','tests/npc_recoil_fixture.h','tests/movement_fixture.h','tests/climb_fixture.h','tests/moving_net_fixture.h','tools/audit_moving_net.py','test-moving-net.ps1','tests/contact_fixture.h','core/source_wall.c','core/source_climb.c','core/source_climb.h','core/source_wall.h','core/game.c','core/game.h','core/presentation.c','core/c64_sprites.c','core/c64_sprites.h','core/c64_sprite_pose_data.h','core/presentation.h','core/combat.c','core/combat.h','core/rooms.c','core/rooms.h','core/room_data.h','core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h','core/c64_sfx.h','core/c64_sound_data.h','core/source_audio.c','core/source_audio.h','core/source_audio_data.h','tests/c64_rooms_test.c','test-core.ps1' | ForEach-Object {
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
