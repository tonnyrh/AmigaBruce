#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-object-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\objects.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\tests\source_object_bridge.c" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault /EXPORT:bl_object_classify'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Object dispatch host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_object.py')
if($LASTEXITCODE){throw 'Object dispatch source comparison failed'}
