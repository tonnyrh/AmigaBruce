$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$folder="$root/.tmp/op-score/candidate"
$bridge=(Get-Content "$root/tests/source_contact_bridge.c" -Raw).Replace('#include "../core/c64_rooms.c"','#include "c64_rooms.c"')
[IO.File]::WriteAllText("$folder/score_bridge.c",$bridge)
$vs=& "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe" -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /I"'+$root+'/core" /I"'+$root+'/amiga" /Fe:"'+$folder+'/score.dll" /Fo"'+$folder+'/score_bridge.obj" "'+$folder+'/score_bridge.c" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_return /EXPORT:bl_contact_fault'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Host bridge compilation failed'}
python "$PSScriptRoot/audit.py"
if($LASTEXITCODE){throw 'Score comparison failed'}
