$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_native_sprite_driver_v2.py')
if($LASTEXITCODE){throw 'Native image-driver generation failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/native-image-driver-v2';New-Item -ItemType Directory -Force $out | Out-Null
$source=Join-Path $taskRoot 'reference/analysis/enemy-cost-2026-10-30/image-driver-v2-bridge.c'
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$taskRoot+'\core" /Fe:"'+$out+'\candidate.dll" /Fo:"'+$out+'\\" "'+$source+'" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Native image-driver host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_native_image_driver_v2.py')
if($LASTEXITCODE){throw 'Native image-driver source comparison failed'}

