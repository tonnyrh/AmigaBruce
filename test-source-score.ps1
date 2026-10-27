#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-score-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\score.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\tests\source_score_bridge.c" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault /EXPORT:bl_score_decimal'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Score conversion host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_score.py')
if($LASTEXITCODE){throw 'Score conversion source comparison failed'}
