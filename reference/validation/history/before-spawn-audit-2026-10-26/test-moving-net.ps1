#Requires -Version 5.1
[CmdletBinding()]
param([switch]$CompileOnly)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(!$vs){throw 'MSVC Build Tools required'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$netOut=Join-Path $taskRoot '.tmp/moving-net-test'
New-Item -ItemType Directory -Force $netOut | Out-Null
$files=@('core/source_wall.c','core/source_climb.c','core/game.c','core/combat.c','core/rooms.c','core/c64_rooms.c','tests/moving_net_bridge.c')
$quoted=$files | ForEach-Object {'"'+(Join-Path $taskRoot $_)+'"'}
$exports=@('bl_source_moving_net_step','bl_source_climb_pose','bl_net_prepare','bl_net_step','bl_net_read','bl_net_native_contracts','bl_c64_read','bl_c64_test_write')
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$netOut+'\net.dll" /Fo"'+$netOut+'\\" '+($quoted -join ' ')+' /link /Brepro /INCREMENTAL:NO '+(($exports|ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Moving-net comparison compilation failed'}
if(!$CompileOnly){
    & python (Join-Path $taskRoot 'tools/audit_moving_net.py')
    if($LASTEXITCODE){throw 'Moving-net source comparison failed'}
}
