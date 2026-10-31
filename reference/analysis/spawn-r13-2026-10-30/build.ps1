$ErrorActionPreference='Stop'
$taskRoot='C:\vscode\_EXT\AmigaBruceLee'
$env:TEMP=Join-Path $taskRoot '.tmp';$env:TMP=$env:TEMP
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/spawn-r13';New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /W3 /Fe:"'+$out+'\r13.dll" /Fo:"'+$out+'\\" "'+(Join-Path $PSScriptRoot 'bridge.c')+'" /link /EXPORT:bl_contact_seed /EXPORT:bl_contact_run /EXPORT:bl_contact_copy /EXPORT:bl_contact_regs /EXPORT:bl_contact_fault /EXPORT:bl_contact_return /EXPORT:bl_r13_field'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'R13 spawn comparison compilation failed'}
