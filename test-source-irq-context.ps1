#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-irq-context';New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\context.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\source_irq_context_bridge.c" /link /EXPORT:bl_irq_context_prepare /EXPORT:bl_irq_context_seed /EXPORT:bl_irq_context_run /EXPORT:bl_irq_context_copy /EXPORT:bl_irq_context_regs /EXPORT:bl_irq_context_pc /EXPORT:bl_irq_context_fault /EXPORT:bl_irq_context_gates'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'IRQ context candidate compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_irq_context.py')
if($LASTEXITCODE){throw 'IRQ context candidate differs from original instructions'}
