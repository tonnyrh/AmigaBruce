#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/session-test'
New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/session_bridge.c')
$quoted=($sources | ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}) -join ' '
$exports=@('bl_cheat_room_contract','bl_cheat_start','bl_session_contracts','bl_audit_prepare','bl_audit_step','bl_audit_read','bl_life_prepare','bl_life_step','bl_life_read','bl_c64_read','bl_c64_contact')
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\session.dll" /Fo"'+$out+'\\" '+$quoted+' /link '+(($exports | ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Session fixture compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_session_walls.py')
if($LASTEXITCODE){throw 'Session/source wall audit failed'}
& python (Join-Path $taskRoot 'tools/audit_cheat_progress.py')
if($LASTEXITCODE){throw 'Cheat lamp progress comparison failed'}
