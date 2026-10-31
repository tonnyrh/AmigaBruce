"""Separate all-actor OCS presentation and diagnostic-only CLXDAT observer.

Production engine/core and previous Bruce-only trials remain untouched.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/hardware-bruce-2026-10-31'

def item(p):
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def main():
    out=BASE/'v5';out.mkdir(exist_ok=True)
    header=(ROOT/'tools/hardware_actors_probe.h').read_text()
    for moving in ['', 'moving/']:
        src=BASE/'v4'/moving;dst=out/moving;dst.mkdir(exist_ok=True)
        (dst/'bruce_hw.h').write_text(header)
        generated=[dst/'bruce_hw.h']
        for variant in ['bob','sprite','observe']:
            parent='bob' if variant=='bob' else 'sprite'
            folder=dst/variant;folder.mkdir(exist_ok=True)
            text=(src/parent/'main.c').read_text()
            text=text.replace('#define BL_HW_BRUCE ',f'#define BL_HW_OBSERVE {int(variant=="observe")}\n#define BL_HW_BRUCE ',1)
            assert text.count('BL_HW_BRUCE && kind==2')==2
            text=text.replace('BL_HW_BRUCE && kind==2','BL_HW_BRUCE')
            text=text.replace('bruce_hw_update(buffer,index,left,top,f->active);','bruce_hw_update(buffer,index,left,top,f->active);')
            text=text.replace('bruce_hw_data[n]=copper[n]+256','bruce_hw_data[n]=copper[n]+128')
            anchor='    list[1]=(game_field_active && game_field_loading)?0:0x4200;'
            assert text.count(anchor)==1
            text=text.replace(anchor,'    if(BL_HW_BRUCE && BL_HW_OBSERVE)bruce_hw_observe();\n'+anchor)
            anchor='    hw->cop1lc=(ULONG)list;'
            assert text.count(anchor)==1
            text=text.replace(anchor,'    if(BL_HW_BRUCE)bruce_hw_published=(bruce_hw_game && !game_field_loading)?(list==copper[1]):-1;\n'+anchor)
            anchor='        append(&p,"\\nhw_bruce_cases=");number(&p,bruce_hw_cases);'
            assert text.count(anchor)==1
            fields=''
            for name,value in [('hw_actors','BL_HW_BRUCE?3:0'),('hw_observer','BL_HW_OBSERVE'),('hw_observer_samples','bruce_hw_samples'),('hw_observer_expected','bruce_hw_expected_seen'),('hw_observer_actual','bruce_hw_actual_seen'),('hw_observer_missing','bruce_hw_missing'),('hw_observer_extra','bruce_hw_extra'),('hw_observer_overlap_samples','bruce_hw_overlap_samples')]:
                fields+=f'        append(&p,"\\n{name}=");number(&p,{value});\n'
            text=text.replace(anchor,fields+anchor)
            (folder/'main.c').write_text(text)
            build=(src/(parent+'-build.ps1')).read_text().replace('/v4/','/v5/').replace('/'+parent+'/', '/'+variant+'/')
            (dst/(variant+'-build.ps1')).write_text(build)
            generated += [folder/'main.c',dst/(variant+'-build.ps1')]
        scope=json.loads((src/'scope.json').read_text())
        scope['status']='private_all_actor_hardware_sprite_probe'
        scope['generated']=[item(p) for p in generated]
        scope['scope']='Three actors only: Bruce0..2, Yamo3..5, Kage6..7; shared opaque black/yellow/green palette. Existing Copper1024-byte blocks hold248-byte lists and740-byte DMA tails at256..995. No extra Chip allocation. Identical game/core. Observe variant reads CLXDAT at publication and compares a rendered-mask reference, never changes source RAM or gameplay; not a replacement for source collision or raster certification.'
        (dst/'scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    # The private runners are versioned separately and mount only v5 outputs.
    print('Generated isolated v5 all actors, moving route and observer')

if __name__=='__main__':main()
