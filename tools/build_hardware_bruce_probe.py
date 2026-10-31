"""Derive private BOB/sprite mains; production source and core untouched."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31'
def main():
    original=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
    allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
    guard='(BL_AUTOTEST&&(!capture||!tone))'
    for variant,enabled in [('bob',0),('sprite',1)]:
        folder=BASE/variant;folder.mkdir(parents=True,exist_ok=True)
        text=original
        pairs=[
         ('static void blank_game_display(void);','static void blank_game_display(void);\nstatic void bruce_hw_blank(void);'),
         ('    hw->bplcon0=0;','    hw->bplcon0=0;\n    if(BL_HW_BRUCE)bruce_hw_blank();'),
         ('/* Existing AI actors, recolored to the source room palette at load time. */','#include "../bruce_hw.h"\n/* Existing AI actors, recolored to the source room palette at load time. */'),
         ('    if(!f->active || height<=0)return;',
          '    if(BL_HW_BRUCE && kind==2)bruce_hw_update(buffer,index,left,top,f->active);\n    if(!f->active || height<=0)return;'),
         ('    dirty->left=(short)left;','    if(BL_HW_BRUCE && kind==2)return;\n    dirty->left=(short)left;'),
         ('    *p++=0xffff;*p++=0xfffe;',
          '    if(BL_HW_BRUCE)bruce_hw_copper(&p,list==copper[1]);\n    *p++=0xffff;*p++=0xfffe;'),
         ('    hw->cop1lc=(ULONG)list;',
          '    if(BL_HW_BRUCE)hw->dmacon=(UWORD)((game_field_active && !game_field_loading)?(DMAF_SETCLR|DMAF_SPRITE):DMAF_SPRITE);\n    hw->cop1lc=(ULONG)list;'),
         ('    background=AllocMem(BITMAP_BYTES,MEMF_CHIP|MEMF_CLEAR);',
          '    if(BL_HW_BRUCE)bruce_hw_data=AllocMem(BRUCE_HW_BYTES,MEMF_CHIP|MEMF_CLEAR);\n    background=AllocMem(BITMAP_BYTES,MEMF_CHIP|MEMF_CLEAR);'),
         ('       !tile_dma||!sfx_pcm||', '       (BL_HW_BRUCE&&!bruce_hw_data)||!tile_dma||!sfx_pcm||'),
         ('    prepare_target();if(!BL_AUTOTEST || BL_COMBAT_TEST)prepare_fighters();',
          '    prepare_target();if(!BL_AUTOTEST || BL_COMBAT_TEST)prepare_fighters();\n    if(BL_HW_BRUCE && BL_AUTOTEST)bruce_hw_selftest();'),
         ('    if(fighter_dma)FreeMem(fighter_dma,FIGHTER_DMA_BYTES);',
          '    if(bruce_hw_data)FreeMem(bruce_hw_data,BRUCE_HW_BYTES);\n    if(fighter_dma)FreeMem(fighter_dma,FIGHTER_DMA_BYTES);')]
        for old,new in pairs:
            assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
        anchor='        append(&p,"\\nsource_clock_elapsed=");number(&p,source_clock_elapsed);'
        assert text.count(anchor)==1
        report='''        append(&p,"\\nhw_bruce_enabled=");number(&p,BL_HW_BRUCE);
        append(&p,"\\nhw_bruce_bytes=");number(&p,BL_HW_BRUCE?BRUCE_HW_BYTES:0);
        append(&p,"\\nhw_bruce_cases=");number(&p,bruce_hw_cases);
        append(&p,"\\nhw_bruce_errors=");number(&p,bruce_hw_errors);
        append(&p,"\\nhw_bruce_builds=");number(&p,bruce_hw_builds);
        append(&p,"\\nhw_bruce_draws=");number(&p,bruce_hw_draws);
'''
        text=text.replace(anchor,report+anchor)
        # Same existing unused-capture omission as the established PAL probes.
        assert text.count(allocation)==text.count(guard)==1
        text=text.replace(allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}').replace(guard,'(BL_AUTOTEST&&!tone)')
        text=f'#define BL_HW_BRUCE {enabled}\n'+text
        (folder/'main.c').write_text(text,encoding='utf-8')
        builder=(ROOT/'amiga-build.ps1').read_text(encoding='utf-8-sig').replace('$taskRoot=$PSScriptRoot',f"$taskRoot='{ROOT}'",1)
        builder=builder.replace("'amiga/out'",f"'{folder.relative_to(ROOT).as_posix()}/out'")
        anchor='    & $compiler @sourceFlags -c (Join-Path $taskRoot $source) -o $obj'
        assert builder.count(anchor)==1
        replace=f"    $actualPath=Join-Path $taskRoot $source\n    if($source -eq 'amiga/main.c'){{$actualPath=Join-Path $taskRoot '{folder.relative_to(ROOT).as_posix()}/main.c';$sourceFlags+='-I'+(Join-Path $taskRoot 'amiga')}}\n    & $compiler @sourceFlags -c $actualPath -o $obj"
        (BASE/(variant+'-build.ps1')).write_text(builder.replace(anchor,replace),encoding='utf-8')
    def item(p):return dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    sources=['amiga/main.c','core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_align.s','amiga/out/bruce_amiga.exe','amiga/out/bruce_amiga.elf','amiga-build.ps1','assets/c64/sprites-v1/manifest.json']
    report=dict(status='private_bruce_hardware_sprite_probe',checkpoint='ccf9572be54db49a33638d52e73c74c9f5eec740',production_changed=False,inputs=[item(ROOT/p) for p in sources],generated=[item(BASE/v/'main.c') for v in ['bob','sprite']]+[item(BASE/(v+'-build.ps1')) for v in ['bob','sprite']]+[item(BASE/'bruce_hw.h')],
      harrier=dict(path='C:/vscode/_EXT/harrierattackreloaded/amiga/main.c',sha256=hashlib.sha256(Path('C:/vscode/_EXT/harrierattackreloaded/amiga/main.c').read_bytes()).hexdigest(),routines=['setHardwareSpritePosition','copSetSprites','updateHardwareProjectileChain']),
      scope='Only Bruce presentation changes; current ripped two-colour pixels, three16px channels, two DMA buffers556bytes. No extra service seam or game/core changes. Channel reuse documented from Harrier; not needed for this first actor.')
    (BASE/'scope.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built private BOB and hardware-sprite Bruce inputs')
if __name__=='__main__':main()
