#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-visibility-test'
New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/source_visibility_bridge.c')
$quoted=($sources|ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}) -join ' '
$exports=@('bl_visibility_prepare','bl_visibility_flag','bl_visibility_copy')
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\visibility.dll" /Fo"'+$out+'\\" '+$quoted+' /link '+(($exports | ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source visibility compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_source_visibility.py')
if($LASTEXITCODE){throw 'Original-byte source visibility control failed'}
