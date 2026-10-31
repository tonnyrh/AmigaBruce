"""Derive paired20-room diagnostics; only the sprite assembly changes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-disjoint-2026-10-30'
def main():
    original=(ROOT/'test-source-room-tour.ps1').read_text(encoding='utf-8-sig')
    anchor="    if($source -eq ''amiga/main.c''){$actualPath='''+$generated+''';$sourceFlags+=''-I'+(Join-Path $taskRoot 'amiga')+'''}'"
    assert original.count(anchor)==1
    for variant in ['before','candidate']:
        text=original.replace('$taskRoot=$PSScriptRoot\n',"$taskRoot='"+str(ROOT)+"'\n",1)
        # Extend the generated builder's exact compiler override, retaining
        # the same diagnostic main, allocations, gates and measurements.
        extra="\n$override+=\"`n\"+'    if($source -eq ''core/c64_rooms.c''){$actualPath=Join-Path $taskRoot ''reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c'';$sourceFlags+=''-I''+(Join-Path $taskRoot ''core'')}'"
        extra+="\n$override+=\"`n\"+'    if($source -eq ''amiga/sprite_copy.s''){$actualPath=Join-Path $taskRoot ''reference/analysis/sprite-disjoint-2026-10-30/"+variant+"/sprite_copy.s''}'"
        text=text.replace(anchor,anchor+extra)
        anchor2="$identity=@($files | Sort-Object"
        assert text.count(anchor2)==1
        text=text.replace(anchor2,"$files+=@('reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c','reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_actor_programs.h','reference/analysis/sprite-disjoint-2026-10-30/"+variant+"/sprite_copy.s') | ForEach-Object {Join-Path $taskRoot $_}\n"+anchor2)
        text=text.replace("else{'core/c64_rooms.c'}", "else{'reference/analysis/sprite-disjoint-2026-10-30/candidate/c64_rooms.c'}")
        (BASE/(variant+'-tour.ps1')).write_text(text,encoding='utf-8')
    print('Paired20-room native controllers generated')
if __name__=='__main__':main()
