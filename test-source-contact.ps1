#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-contact-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\contact.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\tests\source_contact_bridge.c" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault /EXPORT:bl_contact_trace_enable /EXPORT:bl_contact_trace'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Contact kernel host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_contact.py')
if($LASTEXITCODE){throw 'Contact kernel source comparison failed'}
