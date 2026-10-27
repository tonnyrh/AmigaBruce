#Requires -Version 5.1
[CmdletBinding()]
param([switch]$CompileOnly)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(!$vs){throw 'MSVC Build Tools required'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$climbOut=Join-Path $taskRoot '.tmp/source-climb-test'
New-Item -ItemType Directory -Force $climbOut | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$climbOut+'\climb.dll" /Fo"'+$climbOut+'\\" "'+$taskRoot+'\core\source_wall.c" "'+$taskRoot+'\core\source_climb.c" "'+$taskRoot+'\core\game.c" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\tests\climb_bridge.c" /link /Brepro /INCREMENTAL:NO /EXPORT:bl_source_climb_step /EXPORT:bl_source_climb_pose /EXPORT:bl_climb_prepare /EXPORT:bl_climb_run /EXPORT:bl_climb_read /EXPORT:bl_c64_read /EXPORT:bl_c64_test_write'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Climb comparison compilation failed'}
if(!$CompileOnly){
    & python (Join-Path $taskRoot 'tools/verify_source_climb.py')
    if($LASTEXITCODE){throw 'Source climb comparison failed'}
}
