#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-irq-audit';New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\audit.dll" /Fo:"'+$out+'\\" "'+$taskRoot+'\tests\source_irq_audit_bridge.c" /link /EXPORT:bl_irq_audit_prepare /EXPORT:bl_irq_audit_seed /EXPORT:bl_irq_audit_field /EXPORT:bl_irq_audit_copy /EXPORT:bl_irq_audit_regs /EXPORT:bl_irq_audit_inputs'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'IRQ audit compilation failed'}
& python (Join-Path $taskRoot 'tools/audit_c64_irq_contract.py')
if($LASTEXITCODE){throw 'IRQ source audit failed; see raw trace/report'}
