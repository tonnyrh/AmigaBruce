"""Bind the isolated C64/native sprite experiment without changing delivery."""
import hashlib,json
from pathlib import Path
from probe_disjoint_sprite_copy import ASM,FAST_C
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/sprite-disjoint-2026-10-30'
PERF='reference/analysis/optimization-2026-10-27'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def check(entries):
    for e in entries:assert item(e['path'])['sha256']==e['sha256'],e['path']
def kernel(path,length):
    raw,ss=sections(ROOT/path);_,syms=elf_symbols(ROOT/path);at=syms['bl_sprite_copy']
    s=next(s for n,s in ss if s[1]==1 and s[3]<=at and at+length<=s[3]+s[5])
    off=s[4]+at-s[3];return raw[off:off+length]
def main():
    scope=read(BASE+'/scope.json');check(scope['artifacts'])
    assert item('.reference/c64/work/untrained-memory.bin')['sha256']==scope['source_sha256']=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    original=(ROOT/BASE/'before/sprite_copy.s').read_text()
    assert original==(ROOT/'amiga/sprite_copy.s').read_text()
    assert original.replace('    moveq #63,%d4\n',ASM+'    moveq #63,%d4\n')==(ROOT/BASE/'candidate/sprite_copy.s').read_text()
    core=(ROOT/BASE/'before/c64_rooms.c').read_text(encoding='utf-8-sig')
    assert core==(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig')
    expected=core.replace('static unsigned char source_sprite_copy(void){',FAST_C+'\nstatic unsigned char source_sprite_copy(void){')
    expected=expected.replace('    source_sprite_copy_c();return 1;','    if(!source_sprite_disjoint_c())source_sprite_copy_c();return 1;')
    expected=expected.replace('glyph=test<64?0xa200:','glyph=test<64?0x5d91:').replace('y=z?ys[(test>>3)&7]:(unsigned char)(height*3);','y=(test<64 || !z)?(unsigned char)(height*3):ys[(test>>3)&7];')
    assert expected==(ROOT/BASE/'candidate/c64_rooms.c').read_text(encoding='utf-8-sig')
    for variant in ['before','candidate']:assert (ROOT/BASE/variant/'c64_actor_programs.h').read_bytes()==(ROOT/'core/c64_actor_programs.h').read_bytes()
    proof=read(BASE+'/source-proof.json');check(proof['source_files'])
    assert proof['checks']==1872 and proof['instructions']==485136 and proof['brk_controls']==312 and proof['selected_fast_cases']==32
    assert not proof['edition_verified'] and not proof['natural_playthrough']
    paths=[e['path'] for e in scope['artifacts']]+[BASE+'/scope.json',BASE+'/source-proof.json',
        'tools/verify_disjoint_sprite_experiment.py','tools/probe_disjoint_sprite_copy.py','tools/verify_disjoint_sprite_copy.py',
        'tools/build_disjoint_sprite_benchmark.py','tools/build_disjoint_sprite_tour.py','test-sprite-disjoint.ps1','docs/SPRITE_DISJOINT_EXPERIMENT.md']
    shapes={}
    for variant,obj in [('before','amiga/out/sprite_copy.o'),('candidate',BASE+'/compiled-candidate/sprite_copy.o')]:
        raw,ss=sections(ROOT/obj);s=next(s for n,s in ss if n=='.text.bl_sprite_copy');shapes[variant]=raw[s[4]:s[4]+s[5]]
        paths.append(obj)
    pairs={}
    for suffix,tour in [('r02',False),('r03',False),('tour',True)]:
        rows=[]
        for variant in ['before','candidate']:
            folder=PERF+'/sprite-disjoint-'+variant+'-'+suffix
            identity=read(folder+'/identity.json');check(identity['source_files']);r=identity['run']
            assert r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256' and r['restored_os']=='1'
            for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors','bad_presents']:assert r[k]=='0',(variant,suffix,k)
            assert int(r['chip_largest_loaded'])>=49152
            for e in identity['build']:assert item(folder+'/'+Path(e['path']).name)['sha256']==e['sha256']
            assert kernel(folder+'/bruce_test.elf',len(shapes[variant]))==shapes[variant]
            paths += [folder+'/'+n for n in ['identity.json','native.txt','bruce_test.elf','bruce_test.exe','bruce_test.adf']]
            if tour:
                assert identity['status']=='passed_scoped_20_room_timing_route' and len(identity['rooms'])==20
                assert all(v['steps']==120 and v['chip_largest']>=49152 for v in identity['rooms'])
                rows.append(dict(variant=variant,fields=sum(v['fields'] for v in identity['rooms']),lines=sum(v['lines'] for v in identity['rooms']),missed=sum(v['missed'] for v in identity['rooms']),steps=2400))
            else:
                overrides=read(folder+'/compile-overrides.json');check(overrides['actual_inputs']);paths.append(folder+'/compile-overrides.json')
                assert r['source_world_steps']==r['source_perf_steps']=='360'
                rows.append(dict(variant=variant,fields=int(r['source_clock_elapsed']),missed=int(r['source_clock_missed']),steps=360))
        pairs[suffix]=rows
    footprints=[]
    for variant in ['before','candidate']:
        path=PERF+'/sprite-disjoint-'+variant+'-r02/bruce_test.elf'
        _,ss=sections(ROOT/path);footprints.append({n:s[5] for n,s in ss if n in ['.text','.rodata','.data','.bss']})
    delta={k:footprints[1][k]-footprints[0][k] for k in footprints[0]}
    assert delta=={'.text':222,'.rodata':0,'.data':0,'.bss':0}
    assert item('amiga/out/bruce_amiga.exe')['sha256']=='f1047de7ded0a9087abefcec46e963aa8369019bc700172c60a99529cbea533d'
    paths+=['amiga/out/bruce_amiga.exe','amiga/out/bruce_amiga.elf','amiga/out/bruce_amiga.adf']
    assert all(pairs[s][1]['missed']>pairs[s][0]['missed'] for s in ['r02','r03'])
    report=dict(status='measured_private_disjoint_sprite_experiment',production_changed=False,
        selected_for_production=False,
        selection_reason='Both R01 pairs increase missed audio ticks6->45 despite shorter time. Aggregate20-room improvement does not clear that observed regression.',
        source_sha256=scope['source_sha256'],source_cases=1872,native_controls=710,native_sprite_cases=256,
        native_kernel_bytes={k:len(v) for k,v in shapes.items()},pairs=pairs,loaded_section_delta=delta,
        realtime_accepted=False,natural_playthrough=False,edition_verified=False,
        artifacts=[item(p) for p in sorted(set(paths))])
    (ROOT/BASE/'experiment.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(native_kernel_bytes=report['native_kernel_bytes'],pairs=pairs),indent=2))
if __name__=='__main__':main()
