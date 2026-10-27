#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_hit_masks.py')
if($LASTEXITCODE){throw 'VIC hit-mask extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/ninja-wall-test'
New-Item -ItemType Directory -Force $out | Out-Null
$sources=@('core/game.c','core/source_wall.c','core/source_climb.c','core/presentation.c','core/c64_sprites.c','core/combat.c','core/rooms.c','core/session.c','core/c64_rooms.c','core/source_audio.c','tests/ninja_wall_bridge.c')
$quoted=($sources | ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}) -join ' '
$exports=@('bl_ninja_prepare','bl_ninja_step','bl_ninja_read','bl_ninja_touch','bl_ninja_hit','bl_ninja_chain','bl_c64_read')
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$out+'\ninja.dll" /Fo"'+$out+'\\" '+$quoted+' /link /Brepro /INCREMENTAL:NO '+(($exports | ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Ninja wall fixture compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_ninja_wall.py')
if($LASTEXITCODE){throw 'Ninja source controls failed'}
