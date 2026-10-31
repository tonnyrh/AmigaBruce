"""Compare native enemy costs using current production main/core, privately."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
def main():
    BASE.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
    guard='(BL_AUTOTEST&&(!capture||!tone))'
    assert source.count(allocation)==source.count(guard)==1
    private=source.replace(allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}').replace(guard,'(BL_AUTOTEST&&!tone)')
    (BASE/'main.c').write_text(private,encoding='utf-8')
    builder=(ROOT/'amiga-build.ps1').read_text(encoding='utf-8-sig')
    builder=builder.replace('$taskRoot=$PSScriptRoot',f"$taskRoot='{ROOT}'",1)
    anchor='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
    assert builder.count(anchor)==1
    replacement="    $actualPath=Join-Path $taskRoot $source\n    if($source -eq 'amiga/main.c'){$actualPath=Join-Path $taskRoot 'reference/analysis/enemy-cost-2026-10-30/main.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'amiga')}\n    & $compiler @sourceFlags -c $actualPath -o $obj"
    (BASE/'build.ps1').write_text(builder.replace(anchor,replacement),encoding='utf-8')
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    (BASE/'scope.json').write_text(json.dumps(dict(status='private_current_enemy_cost_profile',production_changed=False,
        masks={'0':'Bruce only','1':'Bruce and Yamo','2':'Bruce and Kage','3':'all three'},
        source_actors={'1':'Yamo','2':'Kage'},
        method='Identical source-step target; source AI unchanged for retained actors. Exclusion uses existing diagnostic flag/D015 gates, not a game rule. These profiles do not force actors stationary.',
        inputs=[item(ROOT/p) for p in ['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/source_audio.h','amiga-build.ps1']],
        generated=[item(BASE/'main.c'),item(BASE/'build.ps1')],
        limits=['Profiler overhead changes timing','Fixed source-step count does not equate to a natural playthrough','Static actor/field work requires a separate controlled probe']),indent=2)+'\n')
    print('Generated current-main enemy matrix; source behavior unchanged')
if __name__=='__main__':main()
