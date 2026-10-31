#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/verify_vic_cache.py') --prepare
if($LASTEXITCODE){throw 'Frozen cache extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/vic-cache-test'
$cmd='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$out+'" /Fe:"'+$out+'\cache.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\vic_cache_bridge.c" /link /EXPORT:bl_vic_cache_contract /EXPORT:bl_vic_cache_cases'
& $env:ComSpec /d /s /c $cmd
if($LASTEXITCODE){throw 'Cache host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_vic_cache.py')
if($LASTEXITCODE){throw 'Cache equivalence failed'}
