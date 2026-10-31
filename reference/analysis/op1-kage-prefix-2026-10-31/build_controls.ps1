# Build the native witness without counters and the host witness with path counters.
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Push-Location $root
try{
    python (Join-Path $PSScriptRoot build_proof.py)
    if($LASTEXITCODE){throw 'Native witness build failed'}
    $vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
    $vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    $vcvars=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
    $compile='call "'+$vcvars+'" >nul && cl /nologo /LD /O2 /w /DKAGE_COUNTS=1 /Icore /Fe:.tmp/op1-kage/proof/prefix.dll /Fo.tmp/op1-kage/proof/host.obj .tmp/op1-kage/proof/c64_rooms.c /link /EXPORT:pilot_ram /EXPORT:pilot_witness'
    & $env:ComSpec /d /s /c $compile
    if($LASTEXITCODE){throw 'Host witness build failed'}
    python (Join-Path $PSScriptRoot oracle.py)
    if($LASTEXITCODE){throw '6502/host comparison failed'}
}finally{Pop-Location}
