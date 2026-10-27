#Requires -Version 5.1
[CmdletBinding()]
param([switch]$ObjectsOnly)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_rooms.py')
if($LASTEXITCODE){throw 'Source extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/c64-room-test'
New-Item -ItemType Directory -Force $out | Out-Null
$identity=@('core/source_wall.c','core/source_climb.c','core/source_climb.h','core/source_wall.h','core/game.c','core/game.h','core/combat.c','core/combat.h','core/rooms.c','core/rooms.h','core/room_data.h','tests/contact_bridge.c','tests/contact_fixture.h','tools/verify_c64_contacts.py','core/c64_rooms.c','core/c64_rooms.h','core/c64_sfx.h','core/c64_sound_data.h','core/c64_room_data.h','core/c64_room_programs.h','tools/build_c64_rooms.py','tools/verify_c64_room_runtime.py','tools/c64_room_model.py','tools/rip_c64_room_graphics.py','test-c64-rooms.ps1' | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $taskRoot $_) -Algorithm SHA256).Hash.ToLower()}
})
$identity | ConvertTo-Json | Set-Content (Join-Path $out 'compiled-sources.json') -Encoding UTF8
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\rooms.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\core\source_wall.c" "'+$taskRoot+'\core\source_climb.c" "'+$taskRoot+'\core\combat.c" "'+$taskRoot+'\core\rooms.c" "'+$taskRoot+'\tests\contact_bridge.c" /link /EXPORT:bl_contact_fixture_count /EXPORT:bl_contact_fixture_value /EXPORT:bl_contact_prepare /EXPORT:bl_contact_run /EXPORT:bl_contact_result /EXPORT:bl_c64_reset /EXPORT:bl_c64_load /EXPORT:bl_c64_tick /EXPORT:bl_c64_read /EXPORT:bl_c64_test_write /EXPORT:bl_c64_fault /EXPORT:bl_c64_field /EXPORT:bl_c64_contact /EXPORT:bl_c64_collect /EXPORT:bl_c64_door /EXPORT:bl_c64_transition /EXPORT:bl_c64_colors /EXPORT:bl_c64_screen /EXPORT:bl_c64_screen_color /EXPORT:bl_c64_glyph /EXPORT:bl_c64_planar /EXPORT:bl_c64_paint_room /EXPORT:bl_c64_paint_changes /EXPORT:bl_c64_paint_part /EXPORT:bl_c64_paint_done /EXPORT:bl_c64_changed_rows /EXPORT:bl_c64_clear_dirty /EXPORT:bl_c64_set_painter /EXPORT:bl_c64_set_block_painter /EXPORT:bl_c64_build_animation_cache /EXPORT:bl_c64_test_execute /EXPORT:bl_c64_check_interleaved'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Native host room compilation failed'}
if($ObjectsOnly){& python (Join-Path $taskRoot 'tools/verify_c64_contacts.py')}
else{& python (Join-Path $taskRoot 'tools/verify_c64_room_runtime.py')}
if($LASTEXITCODE){throw 'Source room comparison failed'}
