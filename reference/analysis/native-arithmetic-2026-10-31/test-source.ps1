#Requires -Version 5.1
$ErrorActionPreference='Stop'
$taskRoot='C:\vscode\_EXT\AmigaBruceLee'
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$out=Join-Path $taskRoot '.tmp/native-arithmetic-host'
New-Item -ItemType Directory -Force $out | Out-Null
$command='call "'+$vcvars+'" >nul && cl /nologo /I"'+$taskRoot+'\core" /LD /O2 /W3 /Fe:"'+$out+'\math.dll" /Fo"'+$out+'\\" "'+$taskRoot+'\reference\analysis\native-arithmetic-2026-10-31\math_bridge.c" /link /EXPORT:bl_math_host'
& $env:ComSpec /d /s /c $command
if($LASTEXITCODE){throw 'Contact kernel host compilation failed'}
& python (Join-Path $taskRoot 'tools/verify_native_arithmetic_source.py')
if($LASTEXITCODE){throw 'Contact kernel source comparison failed'}
