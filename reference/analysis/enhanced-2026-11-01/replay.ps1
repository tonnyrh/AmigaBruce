# Compare the two live painters under the same field clock and joystick input.
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
$out=Join-Path $root '.tmp/enhanced-replay'
New-Item -ItemType Directory -Force $out | Out-Null
@'
from pathlib import Path
import re, sys
root,out = map(Path,sys.argv[1:])
sys.path.insert(0,str(root/'tools'))
from build_fighter_dma import unpack
art=(root/'amiga/enhanced_art.h').read_text()
impl=(root/'amiga/enhanced.h').read_text()
start=impl.index('static void paint_enhanced_tile(')
(out/'paint.h').write_text(impl[start:])
layout='\n'.join(re.findall(r'^#define ENHANCED_.+$',art,re.M))
tables=re.findall(r'static const unsigned char enhanced_arch\w+\[\][^=]*=\{[^}]+\};',art)
(out/'layout.h').write_text('#define ENHANCED_STORAGE\n'+layout+'\n'+'\n'.join(tables)+'\n')
data=re.search(r'enhanced_packed\[\][^=]*=\{([^}]+)\}',art)[1]
decoded=bytes(unpack(bytes(map(int,re.findall(r'\d+',data)))))
offset=int(re.search(r'#define ENHANCED_NIBBLES (\d+)',art)[1])
(out/'tiles.bin').write_bytes(decoded[offset:])
'@ | python - $root $out
if($LASTEXITCODE){throw 'Unable to prepare current painter and graphics'}
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
$vc=Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
$compile='call "'+$vc+'" >nul && cl /nologo /O2 /I"'+$root+'/core" /I"'+$out+'" /Fo:"'+$out+'\\" /Fe:"'+$out+'/replay.exe" "'+$root+'/core/c64_rooms.c" "'+$PSScriptRoot+'/replay.c"'
& $env:ComSpec /d /s /c $compile
if($LASTEXITCODE){throw 'Unable to build the host replay'}
foreach($look in 'classic','enhanced'){
    & "$out/replay.exe" $look "$out/tiles.bin" "$out/state.bin"
    if($LASTEXITCODE){throw "$look replay failed"}
}
