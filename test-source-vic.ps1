#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-vic-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\vic.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\tests\source_vic_bridge.c" /link /EXPORT:bl_vic_seed /EXPORT:bl_vic_write /EXPORT:bl_vic_sample /EXPORT:bl_vic_take'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'VIC seam compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_vic.py')
if($LASTEXITCODE){throw 'VIC seam/cache comparison failed'}
