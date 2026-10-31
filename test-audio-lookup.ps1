#Requires -Version 5.1
param([ValidateSet('candidate','candidate2')][string]$Candidate='candidate')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
foreach($variant in @('before',$Candidate)){
 $out=Join-Path $taskRoot ('.tmp/audio-lookup-test/'+$variant);New-Item -ItemType Directory -Force $out | Out-Null
 $source=Join-Path $taskRoot ('reference/analysis/audio-lookup-2026-10-30/'+$variant+$(if($variant -eq 'before'){'/core/source_audio.c'}else{'/source_audio.c'}))
 $command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$taskRoot+'/core" /Fe:"'+$out+'/audio.dll" /Fo:"'+$out+'/audio.obj" "'+$source+'" /link /EXPORT:bl_source_audio_render /EXPORT:bl_source_audio_reset /EXPORT:bl_source_audio_faults'
 & $env:ComSpec /d /s /c $command
 if($LASTEXITCODE){throw "Audio lookup compile failed: $variant"}
}
& python (Join-Path $taskRoot 'tools/verify_audio_lookup.py') --candidate $Candidate
if($LASTEXITCODE){throw 'Audio lookup equivalence failed'}
