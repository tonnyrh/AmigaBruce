$ErrorActionPreference='Stop'
$taskRoot='C:\vscode\_EXT\AmigaBruceLee'
$env:TEMP=Join-Path $taskRoot '.tmp';$env:TMP=$env:TEMP
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/floor-walk';New-Item -ItemType Directory -Force $out | Out-Null
$source=Join-Path $PSScriptRoot 'bridge.c'
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\floor.dll" /Fo:"'+$out+'\\" "'+$source+'" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_fault /EXPORT:bl_floor_stop'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Floor walking bridge compilation failed'}
