#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
& python (Join-Path $taskRoot 'tools/build_c64_audio.py')
if($LASTEXITCODE){throw 'Source audio extraction failed'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/source-audio-test'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\audio.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\core\c64_rooms.c" "'+$taskRoot+'\core\source_audio.c" /link /EXPORT:bl_c64_reset /EXPORT:bl_c64_read /EXPORT:bl_c64_test_write /EXPORT:bl_c64_audio_reset /EXPORT:bl_c64_audio_request /EXPORT:bl_c64_audio_frame /EXPORT:bl_c64_audio_faults /EXPORT:bl_source_audio_reset /EXPORT:bl_source_audio_music /EXPORT:bl_source_audio_render /EXPORT:bl_source_audio_chip_bytes /EXPORT:bl_source_audio_copy /EXPORT:bl_source_audio_faults'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Source audio host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_source_audio.py')
if($LASTEXITCODE){throw 'Source audio comparison failed'}
