#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(!$vs){throw 'MSVC Build Tools required'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$reuseOut=Join-Path $taskRoot '.tmp/room-reuse-test'
New-Item -ItemType Directory -Force $reuseOut | Out-Null
$exports=@('bl_c64_reset','bl_c64_load','bl_c64_read','bl_c64_test_write','bl_c64_build_animation_cache','bl_c64_reuse_stat','bl_c64_reuse_reset','bl_c64_paint_room','bl_c64_check_interleaved','bl_c64_clear_dirty','bl_c64_paint_part','bl_c64_paint_done','bl_c64_test_execute','bl_c64_set_painter','bl_c64_set_block_painter')
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$reuseOut+'\reuse.dll" /Fo"'+$reuseOut+'\\" "'+$taskRoot+'\core\c64_rooms.c" /link /Brepro /INCREMENTAL:NO '+(($exports|ForEach-Object {'/EXPORT:'+$_}) -join ' ')
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Room reuse compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_room_reuse.py')
if($LASTEXITCODE){throw 'Room reuse controls failed'}
