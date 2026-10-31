#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/final-colors-test';New-Item -ItemType Directory -Force $out | Out-Null
$bridge=Get-Content -LiteralPath (Join-Path $taskRoot 'tests/final_colors_bridge.c') -Raw
foreach($kind in @('before','candidate')){
 $core=if($kind -eq 'before'){'reference/analysis/final-colors-2026-10-30/before/core/c64_rooms.c'}else{'core/c64_rooms.c'}
 $fast=if($kind -eq 'before'){0}else{1}
 $include=(Join-Path $taskRoot $core).Replace('\','/')
 $inputPath=Join-Path $out ($kind+'.c')
 [IO.File]::WriteAllText($inputPath,$bridge.Replace('../core/c64_rooms.c',$include))
 $command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /DFINAL_COLORS_FAST='+$fast+' /Fe:"'+$out+'\'+$kind+'.dll" /Fo:"'+$out+'\\" "'+$inputPath+'" /link /EXPORT:bl_fc_seed /EXPORT:bl_fc_slice /EXPORT:bl_fc_copy /EXPORT:bl_fc_regs /EXPORT:bl_fc_renderer /EXPORT:bl_fc_metadata'
 & $env:ComSpec /d /s /c $command
 if($LASTEXITCODE){throw 'Final color control compilation failed'}
}
& python (Join-Path $taskRoot 'tools/verify_final_colors.py')
if($LASTEXITCODE){throw 'Final color source controls failed'}
