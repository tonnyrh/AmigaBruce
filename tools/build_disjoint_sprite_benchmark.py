"""Private native benchmark: identical core/main, only sprite assembly differs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-disjoint-2026-10-30'
def main():
    build=(ROOT/'.tmp/compact-delivery/math-build.ps1').read_text(encoding='utf-8-sig')
    anchor='    & $compiler @sourceFlags -c $actualPath -o $obj'
    assert build.count(anchor)==1
    for variant in ['before','candidate']:
        override="    if($source -eq 'core/c64_rooms.c'){$actualPath=Join-Path $taskRoot 'reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'core')}\n"
        override+="    if($source -eq 'amiga/sprite_copy.s'){$actualPath=Join-Path $taskRoot 'reference/analysis/sprite-disjoint-2026-10-30/"+variant+"/sprite_copy.s'}\n"
        (BASE/(variant+'-build.ps1')).write_text(build.replace(anchor,override+anchor),encoding='utf-8')
    run='''param([ValidateSet('before','candidate')][string]$Variant,[ValidatePattern('^[a-z0-9-]+$')][string]$Suffix='r02')
$ErrorActionPreference='Stop'
Set-Location 'C:\\vscode\\_EXT\\AmigaBruceLee'
$base='reference/analysis/sprite-disjoint-2026-10-30'
$inputs=@("$base/candidate/c64_rooms.c","$base/candidate/c64_actor_programs.h","$base/$Variant/sprite_copy.s","$base/$Variant-build.ps1",'.tmp/compact-delivery/math-main.c')
$frozen=@($inputs | ForEach-Object {@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower()}})
& ("./$base/$Variant-build.ps1") -Autotest -SourcePerfTest -SpriteCopyTest -PerfSourceSteps 360 -TestFrames 1800
if($LASTEXITCODE){throw 'Private sprite build failed'}
& ./test-source-performance.ps1 -Label ("sprite-disjoint-"+$Variant+"-"+$Suffix) -SpriteCopy -SourceSteps 360 -TestFrames 1800 -SkipBuild
if($LASTEXITCODE){throw 'Private sprite benchmark failed'}
$folder="reference/analysis/optimization-2026-10-27/sprite-disjoint-$Variant-$Suffix"
foreach($entry in $frozen){if((Get-FileHash -LiteralPath $entry.path).Hash.ToLower() -ne $entry.sha256){throw ('Input changed: '+$entry.path)}}
@{production_changed=$false;actual_inputs=$frozen;variant=$Variant;only_measured_difference='sprite_copy.s';native_test_difference='First64 of256 controls now use source glyph region and Y=3*height; other192 alias/tail cases retained'} | ConvertTo-Json -Depth 8 | Set-Content ($folder+'/compile-overrides.json') -Encoding utf8
'''
    (BASE/'run.ps1').write_text(run,encoding='utf-8')
    print('Private paired benchmark runners generated')
if __name__=='__main__':main()
