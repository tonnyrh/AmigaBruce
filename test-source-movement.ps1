#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_rooms.py')
if($LASTEXITCODE){throw 'Source room extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-movement-test'
New-Item -ItemType Directory -Force $out | Out-Null
$identity=@('core/source_wall.c','core/source_climb.c','core/source_climb.h','core/source_wall.h','core/game.c','core/game.h','core/c64_rooms.c','core/c64_rooms.h','core/c64_sfx.h','core/c64_sound_data.h','core/c64_room_data.h','core/c64_room_programs.h','tools/build_c64_rooms.py','tests/movement_bridge.c','tools/verify_source_movement.py','test-source-movement.ps1' | ForEach-Object {
    @{path=$_;sha256=(Get-FileHash (Join-Path $taskRoot $_) -Algorithm SHA256).Hash.ToLower()}
})
$identity | ConvertTo-Json | Set-Content (Join-Path $out 'compiled-sources.json') -Encoding UTF8
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\movement.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\core\source_wall.c" "'+$taskRoot+'\core\source_climb.c" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\tests\movement_bridge.c" /link /EXPORT:bl_recoil_prepare /EXPORT:bl_recoil_run /EXPORT:bl_source_wall_reset /EXPORT:bl_source_wall_record /EXPORT:bl_source_wall_step /EXPORT:bl_move_prepare /EXPORT:bl_move_run /EXPORT:bl_move_read /EXPORT:bl_jump_prepare /EXPORT:bl_jump_run /EXPORT:bl_c64_read'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source movement compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_movement.py')
if($LASTEXITCODE){throw 'Source movement comparison failed'}
