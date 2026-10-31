#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/verify_view_mask.py') --prepare
if($LASTEXITCODE){throw 'Baseline query extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/view-mask-test'
$cmd='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$out+'" /Fe:"'+$out+'\view.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\view_mask_bridge.c" /link /EXPORT:bl_view_mask_contract /EXPORT:bl_view_mask_case_count /EXPORT:bl_view_bulk_case_count'
& $env:ComSpec /d /s /c $cmd
if($LASTEXITCODE){throw 'View query host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_view_mask.py')
if($LASTEXITCODE){throw 'View query verification failed'}
