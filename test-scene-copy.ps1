#Requires -Version 5.1
$ErrorActionPreference='Stop'
$env:TEMP=Join-Path $PSScriptRoot '.tmp/compiler-temp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
$out=Join-Path $PSScriptRoot '.tmp/scene-copy-test'
New-Item -ItemType Directory -Force $out | Out-Null
$before=Join-Path $PSScriptRoot 'reference/validation/history/before-room10-electric-2026-10-26/amiga/main.c'
$text=Get-Content -LiteralPath $before -Raw
$start=$text.IndexOf('static void restore_source_cells(')
$end=$text.IndexOf('static void draw_player(',$start)
if($start -lt 0 -or $end -lt 0){throw 'Historical copy function missing'}
[IO.File]::WriteAllText((Join-Path $out 'scene_copy_legacy.h'),$text.Substring($start,$end-$start).Replace('restore_source_cells','legacy_restore_source_cells'))
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$cmd='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$out+'" /Fe:"'+$out+'\copy.dll" /Fo"'+$out+'\\" "'+$PSScriptRoot+'\tests\scene_copy_bridge.c" /link /EXPORT:bl_copy_run /EXPORT:bl_copy_read /EXPORT:bl_present_probe'
& $env:ComSpec /d /s /c $cmd
if($LASTEXITCODE){throw 'Scene-copy host compilation failed'}
& python (Join-Path $PSScriptRoot 'tools/verify_scene_copy.py')
if($LASTEXITCODE){throw 'Scene-copy controls failed'}
