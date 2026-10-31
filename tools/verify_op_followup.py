"""Current-source bounds for OP0 profile, OP1 inline trial and OP4 candidate.
These are controlled experiments, not delivery or real-time acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_vic_native_kernels import sections
from audit_final_color_images import object_kernel
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/contact-fusion-2026-10-30'
RUN='reference/analysis/optimization-2026-10-27'
IRQ='reference/analysis/irq-input-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(e):assert item(e['path'])==e,e['path']
def verify():
    paths=[BASE+'/scope.json',BASE+'/compiler-probe.json',BASE+'/candidate.c',IRQ+'/input-slot-candidate.json',IRQ+'/controller-select.txt','docs/INPUT_SLOT_CANDIDATE.md','docs/OP_FOLLOWUP_2026_10_30.md','tools/verify_op_followup.py']
    inp=read(IRQ+'/input-slot-candidate.json')
    assert inp['cases']==99072 and inp['instructions']==3803993 and inp['all_ram_and_registers'] and not inp['production_changed']
    assert inp['exhaustive_input_cases']==32768 and inp['stack_status_cases']==65536 and inp['nonstandard_player_cases']==768
    for e in inp['artifacts']:check(e)
    paths += [e['path'] for e in inp['artifacts']]
    source=(ROOT/'core/c64_rooms.c').read_text(encoding='utf-8-sig');scope=read(BASE+'/scope.json')
    assert scope['before_sha256']==item('core/c64_rooms.c')['sha256']
    for before,after in scope['changes']:
        assert source.count(before)==1;source=source.replace(before,after)
    assert source==(ROOT/BASE/'candidate.c').read_text(encoding='utf-8-sig')
    kernels={}
    for name in ['contact_rows','contact_align','contact_prepare']:
        obj='amiga/out/'+name+'.o';_,ss=sections(ROOT/obj)
        for section,q in ss:
            if section.startswith('.text.') and q[2]&2 and q[5]:kernels[section[6:]]=object_kernel(obj,section)
    assert len(kernels)==8
    pairs=[];sizes=[]
    for suffix in ['','-repeat']:
        rows=[];builds=[]
        for variant in ['before','candidate']:
            folder=RUN+'/contact-inline-'+variant+suffix;d=read(folder+'/identity.json');r=d['run']
            raw=dict(line.split('=',1) for line in (ROOT/folder/'native.txt').read_text().splitlines() if '=' in line);assert r==raw
            assert d['source_steps_target']==360 and not d['profile'] and not d['controlled']
            assert r['source_world_steps']==r['source_perf_steps']=='360' and r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
            assert int(r['chip_largest_loaded'])>=49152 and r['restored_os']=='1'
            for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:assert r[key]=='0'
            for e in d['source_files']:check(e)
            for e in d['build']:check(dict(path=folder+'/'+Path(e['path']).name,sha256=e['sha256']))
            check(d['compile_overrides']);overrides=read(d['compile_overrides']['path'])
            for e in overrides['overrides']:check(e['actual'])
            check(overrides['compiled_build'])
            elf=ROOT/folder/'bruce_test.elf';data,ss=sections(elf);_,syms=elf_symbols(elf)
            for function,(code,relocs) in kernels.items():
                at=syms[function];q=next(q for _,q in ss if q[1]==1 and q[3]<=at and at+len(code)<=q[3]+q[5]);off=q[4]+at-q[3];wanted=bytearray(code)
                for offset,target,addend in relocs:struct.pack_into('>I',wanted,offset,(syms[target]+addend)&0xffffffff)
                assert data[off:off+len(wanted)]==wanted,(variant,function)
            if not suffix:sizes.append({name:q[5] for name,q in ss if name in ['.text','.data','.rodata','.bss']})
            rows.append(dict(elapsed=int(r['source_clock_elapsed']),missed=int(r['source_clock_missed'])))
            builds.append([e['sha256'] for e in d['build']]);paths += [folder+'/'+p for p in ['identity.json','native.txt','native.json','compile-overrides.json','compiled-main.c','compiled-build.ps1']]
        pairs.append(dict(before=rows[0],candidate=rows[1],build_hashes=builds))
    assert pairs[0]['build_hashes']==pairs[1]['build_hashes'],'Repeats did not use the same binaries'
    assert all(p['candidate']['missed']>p['before']['missed'] for p in pairs),'Review experiment decision again'
    assert sizes[0]['.bss']==sizes[1]['.bss'] and sizes[0]['.data']==sizes[1]['.data']
    profile=RUN+'/observer-r01-profile-bounded';d=read(profile+'/identity.json');r=d['run'];assert d['profile'] and r['perf_errors']=='0' and r['source_perf_steps']=='360' and r['contact_kernel_cases']=='454'
    for e in d['source_files']:check(e)
    check(d['compile_overrides']);overrides=read(d['compile_overrides']['path'])
    for e in overrides['overrides']:check(e)
    for e in d['build']:check(dict(path=profile+'/'+Path(e['path']).name,sha256=e['sha256']))
    paths += [profile+'/'+p for p in ['identity.json','native.txt','native.json','compile-overrides.json','compiled-main.c','compiled-build.ps1']]
    delivery=read('reference/validation/source-world-delivery.json')
    for e in delivery['normal_build']:check(e)
    return dict(status='completed_scoped_op_followup_production_unchanged',input_candidate_cases=99072,input_candidate_integrated=False,inline_decision='rejected_small_time_change_with_repeatable_audio_regression_and_code_growth',pairs=pairs,native_helpers_byte_exact=8,footprint=sizes,normal_build=delivery['normal_build'],realtime_accepted=False,natural_playthrough=False,physical_a500=False,artifacts=[item(p) for p in sorted(set(paths))])
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path='reference/validation/op-followup.json'
    if a.record:(ROOT/path).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    else:assert read(path)==r
    print('PASS OP followup: input candidate 99072 controls; 2 native inline pairs rejected; normal build unchanged')
if __name__=='__main__':main()
