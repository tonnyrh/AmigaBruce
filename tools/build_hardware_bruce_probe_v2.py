"""Second private trial: preserve render audio polls and controlled display."""
import hashlib,json
from pathlib import Path
import build_hardware_bruce_probe as original
ROOT=original.ROOT
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31/v2'
def main():
    BASE.mkdir(exist_ok=True)
    header=(BASE.parent/'bruce_hw.h').read_text()
    header=header.replace('static UWORD bruce_hw_key[2]', 'static UBYTE bruce_hw_game;\nstatic UWORD bruce_hw_key[2]')
    (BASE/'bruce_hw.h').write_text(header,encoding='utf-8')
    original.BASE=BASE;original.main()
    for variant in ['bob','sprite']:
        p=BASE/variant/'main.c';text=p.read_text()
        old='    if(BL_HW_BRUCE && kind==2)bruce_hw_update(buffer,index,left,top,f->active);'
        new='''    if(BL_HW_BRUCE && kind==2){
        if(f->active && height>0)source_audio_service();
        bruce_hw_update(buffer,index,left,top,f->active);
        if(f->active && height>0)source_audio_service();
    }'''
        assert text.count(old)==1;text=text.replace(old,new)
        text=text.replace('game_field_active && !game_field_loading','bruce_hw_game && !game_field_loading')
        old='    game_field_active=0;';assert text.count(old)==1
        text=text.replace(old,old+'\n    if(BL_HW_BRUCE)bruce_hw_game=0;')
        old='    game_field_last=field_clock();game_field_active=(UBYTE)(!BL_AUTOTEST || BL_SOURCE_PERF_TEST);'
        assert text.count(old)==1;text=text.replace(old,old+'\n    if(BL_HW_BRUCE)bruce_hw_game=1;')
        old='    if(BL_HW_BRUCE)bruce_hw_data=AllocMem(BRUCE_HW_BYTES,MEMF_CHIP|MEMF_CLEAR);\n'
        assert text.count(old)==1;text=text.replace(old,'')
        anchor='    if(((!BL_AUTOTEST || BL_COMBAT_TEST)&&(!fighter_dma||!room_backgrounds[1]))'
        assert text.count(anchor)==1;text=text.replace(anchor,old+anchor)
        # The separate full-fixture replay needs its capture allocation;
        # performance probes retain the same unused-capture omission.
        old='if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
        assert text.count(old)==1
        text=text.replace(old,'if(BL_AUTOTEST){if(!BL_SOURCE_PERF_TEST)capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}')
        text=text.replace('(BL_AUTOTEST&&!tone)','(BL_AUTOTEST&&((!BL_SOURCE_PERF_TEST&&!capture)||!tone))')
        p.write_text(text,encoding='utf-8')
    scope=json.loads((BASE/'scope.json').read_text())
    for e in scope['generated']:e['sha256']=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()
    scope['scope']+=' V2: preserve the two original draw audio polling opportunities; allocate small sprite buffer after large display allocations; display-enabled flag separate from PAL IRQ scheduler; full-fixture capture retained.'
    (BASE/'scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    print('Generated separate v2 private inputs; v1 preserved')
if __name__=='__main__':main()
