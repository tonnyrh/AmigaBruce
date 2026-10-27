#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_rooms.py')
if($LASTEXITCODE){throw 'C64 source translation failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/bombs-entry-test'
New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/bombs_entry_bridge.c')
$quoted=($sources | ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}) -join ' '
$exports=@('bl_entry_prepare','bl_entry_run','bl_entry_read','bl_bomb_prepare','bl_bomb_contact','bl_bomb_step','bl_bomb_actor_step','bl_bomb_read','bl_c64_read','bl_c64_test_write','bl_c64_test_execute','bl_c64_contact','bl_c64_enemy_hazard','bl_c64_fault','bl_c64_audio_requests')
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$out+'\bombs.dll" /Fo"'+$out+'\\" '+$quoted+' /link /Brepro /INCREMENTAL:NO '+(($exports | ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Bomb/entry bridge compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_bombs_entry.py')
if($LASTEXITCODE){throw 'Original6502 bomb/entry controls failed'}
