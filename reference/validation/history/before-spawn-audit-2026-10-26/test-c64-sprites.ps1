#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_sprites.py')
if($LASTEXITCODE){throw 'C64 sprite extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if(!$vs){throw 'MSVC Build Tools required'}
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$spriteOut=Join-Path $taskRoot '.tmp/c64-sprites-test'
New-Item -ItemType Directory -Force $spriteOut | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /Brepro /LD /O2 /W3 /Fe:"'+$spriteOut+'\sprites.dll" /Fo"'+$spriteOut+'\\" "'+$taskRoot+'\core\c64_sprites.c" /link /Brepro /INCREMENTAL:NO /EXPORT:bl_source_pose'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source pose compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_c64_sprites.py')
if($LASTEXITCODE){throw 'C64 sprite verification failed'}
