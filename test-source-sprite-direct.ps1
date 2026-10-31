#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_source_sprite_direct.py')
if($LASTEXITCODE){throw 'Direct-call generation failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-publish-direct-test';New-Item -ItemType Directory -Force $out | Out-Null
foreach($variant in @('before','candidate')){
 $source=if($variant -eq 'before'){Join-Path $taskRoot 'reference/analysis/sprite-publish-2026-10-30/direct-call/bridge-before.c'}else{Join-Path $taskRoot 'reference/analysis/sprite-publish-2026-10-30/direct-call/bridge.c'}
 $obj=Join-Path $out $variant;New-Item -ItemType Directory -Force $obj | Out-Null
 $command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$taskRoot+'\core" /Fe:"'+$out+'\'+$variant+'.dll" /Fo:"'+$obj+'\\" "'+$source+'" /link /EXPORT:bl_contact_prepare /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault'
 & $env:ComSpec /d /s /c $command
 if($LASTEXITCODE){throw 'Sprite-publish host compilation failed'}
}
& python (Join-Path $taskRoot 'tools/verify_source_sprite_direct.py')
if($LASTEXITCODE){throw 'Direct-call source comparison failed'}
