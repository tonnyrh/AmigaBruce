#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-input-slot';New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\slot.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\source_input_slot_bridge.c" /link /EXPORT:bl_input_slot_seed /EXPORT:bl_input_slot_run /EXPORT:bl_input_slot_copy /EXPORT:bl_input_slot_regs'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Input slot candidate compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_input_slot.py')
if($LASTEXITCODE){throw 'Candidate differs from original input slot'}
