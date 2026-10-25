#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-dma-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\dma.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\core\source_audio.c" "'+$taskRoot+'\core\source_dma.c" /link /EXPORT:bl_source_audio_reset /EXPORT:bl_source_audio_render /EXPORT:bl_source_audio_copy /EXPORT:bl_source_audio_chip_bytes /EXPORT:bl_source_audio_faults /EXPORT:bl_source_dma_reset /EXPORT:bl_source_dma_update'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source DMA host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_dma.py')
if($LASTEXITCODE){throw 'Source DMA image comparison failed'}
