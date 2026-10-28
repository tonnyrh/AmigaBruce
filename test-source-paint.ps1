#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-paint-test';New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\paint.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\source_paint_bridge.c" /link /EXPORT:bl_paint_requeue_contract'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Paint regression compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_paint.py')
if($LASTEXITCODE){throw 'Paint regression failed'}
