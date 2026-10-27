#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/room8-blast-test'
New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/room8_blast_bridge.c')
$quoted=($sources | ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}) -join ' '
$exports=@('bl_r8_prepare','bl_r8_step','bl_r8_read','bl_c64_read','bl_c64_contact','bl_c64_fault')
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$out+'\room8.dll" /Fo"'+$out+'\\" '+$quoted+' /link /Brepro /INCREMENTAL:NO '+(($exports | ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Room8 blast compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_room8_blasts.py')
if($LASTEXITCODE){throw 'Room8 source/Amiga explosion differences remain'}
