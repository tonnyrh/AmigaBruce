#Requires -Version 5.1
$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot '.tmp/enhanced-audio-test'
New-Item -ItemType Directory -Force $out | Out-Null
& python (Join-Path $PSScriptRoot 'tools/build_enhanced_audio.py')
if($LASTEXITCODE){throw 'Enhanced sample packing failed'}
$finder=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $finder -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vc=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$compile='call "'+$vc+'" >nul && cl /nologo /O2 /Fe:"'+$out+'/foley.exe" /Fo:"'+$out+'/foley.obj" "'+$PSScriptRoot+'/tests/enhanced_audio_test.c"'
& $env:ComSpec /d /s /c $compile
if($LASTEXITCODE){throw 'Enhanced audio fixture failed to compile'}
& "$out/foley.exe"
if($LASTEXITCODE){throw 'Enhanced audio fixture failed'}
