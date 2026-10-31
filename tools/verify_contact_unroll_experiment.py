"""Verify private 68000 alignment trials and their actual linked inputs."""
import hashlib,json
from pathlib import Path
from build_contact_unroll_probe import candidate
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/contact-unroll-2026-10-31'
PERF='reference/analysis/optimization-2026-10-27'
RUNS=[('baseline','contact-unroll-baseline-r01'),('candidate','contact-unroll-candidate-r01'),
      ('candidate-byte','contact-unroll-byte-r01'),('candidate-compact','contact-unroll-compact-r01')]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def kernel(elf,wanted):
    data,ss=sections(ROOT/elf);_,syms=elf_symbols(ROOT/elf);at=syms['bl_contact_align4']
    s=next(s for n,s in ss if s[1]==1 and s[3]<=at and at+len(wanted)<=s[3]+s[5])
    off=s[4]+at-s[3];assert data[off:off+len(wanted)]==wanted,elf
def verify():
    scope=read(BASE+'/scope.json');paths=[BASE+'/scope.json',BASE+'/source-align-disassembly.txt','tools/build_contact_unroll_probe.py','tools/verify_contact_unroll_experiment.py']
    old=(ROOT/BASE/'baseline/contact_align.s').read_text()
    from build_stationary_enemy_probe import HELPER
    assert (ROOT/BASE/'baseline/c64_rooms.c').read_text()==(ROOT/BASE/'parent/core/c64_rooms.c').read_text(encoding='utf-8-sig')+HELPER
    import sys
    sys.path.insert(0,str(ROOT/'.reference/tools/python'))
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    dis=Disassembler(MPU(memory=list(source)));pc=0x52ad;lines=[]
    while pc<0x530a:
        count,text=dis.instruction_at(pc);lines.append(f'{pc:04X}: '+source[pc:pc+count].hex(' ')+f'  {text}');pc+=count
    assert (ROOT/BASE/'source-align-disassembly.txt').read_text().splitlines()==lines
    parent=read(BASE+'/parent/manifest.json');expected={e['path']:e['sha256'] for e in parent['files']}
    for e in scope['inputs']:
        assert e['sha256']==expected[e['path']],e['path']
        # Normal builds may subsequently be promoted; the frozen parent
        # retains the exact pre-experiment identities.
        assert item(BASE+'/parent/'+e['path'])['sha256']==e['sha256']
    for e in scope['generated']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    rows=[]
    for variant,label in RUNS:
        folder=BASE+'/'+variant;runfolder=PERF+'/'+label;ident=read(runfolder+'/identity.json');r=ident['run']
        text=(ROOT/folder/'contact_align.s').read_text()
        assert text==(old if variant=='baseline' else candidate(old,variant in ['candidate-byte','candidate-compact'],variant!='candidate-compact'))
        assert (ROOT/folder/'main.c').read_bytes()==(ROOT/BASE/'baseline/main.c').read_bytes()
        assert (ROOT/folder/'c64_rooms.c').read_bytes()==(ROOT/BASE/'baseline/c64_rooms.c').read_bytes()
        assert (ROOT/folder/'c64_actor_programs.h').read_bytes()==(ROOT/BASE/'baseline/c64_actor_programs.h').read_bytes()
        assert not ident['profile'] and not ident['controlled'] and ident['enemy_mask']==3 and ident['source_steps_target']==360
        assert r['source_world_steps']==r['source_perf_steps']=='360' and r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
        for k in ['contact_kernel_errors','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors']:assert r[k]=='0', (label,k)
        assert r['restored_os']=='1' and r['enemy_stationary_ram_type']=='5' and int(r['chip_largest_loaded'])>=49152
        stationary=[list(map(int,r['enemy_stationary_'+str(i)].split(','))) for i in range(8)]
        assert all(v[3]==0 for v in stationary)
        obj=folder+('/contact_align.o' if variant=='baseline' else '/out/contact_align.o')
        raw,ss=sections(ROOT/obj);s=dict(ss)['.text.bl_contact_align4'];wanted=raw[s[4]:s[4]+s[5]]
        kernel(runfolder+'/bruce_test.elf',wanted)
        for e in ident['build']:assert item(runfolder+'/'+Path(e['path']).name)['sha256']==e['sha256']
        paths += [obj,runfolder+'/identity.json',runfolder+'/native.txt',runfolder+'/bruce_test.elf',runfolder+'/bruce_test.exe',runfolder+'/bruce_test.adf']
        rows.append(dict(variant=variant,label=label,pal_fields=int(r['source_clock_elapsed']),missed_audio_ticks=int(r['source_clock_missed']),largest_chip_block=int(r['chip_largest_loaded']),kernel_bytes=len(wanted),stationary=stationary))
    baseline=rows[0]
    for row in rows[1:]:
        row['untouched_kernel_timing_deltas']=[]
        for before,after in zip(baseline['stationary'],row['stationary']):
            assert before[4]==after[4]
            row['untouched_kernel_timing_deltas'].append(dict(field=after[0]-before[0],image=after[2]-before[2]))
    result=dict(status='measured_private_contact_alignment_unroll',source_sha256=read(BASE+'/parent/verified-report.json')['source_sha256'],rows=rows,
      controls_per_image=710,align_controls_per_image=256,production_promotion_requires_separate_delivery=True,edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,
      limits=['Stationary layout uses phase0 with odd destination; other phases covered by native differential controls, not this isolated timing','PAL count includes startup and diagnostic work','Host original-byte contact controls reused only through unchanged C reference and frozen prior proof','No claim of full PAL budget, natural IRQ phases, or physical A500 acceptance'],artifacts=[item(p) for p in sorted(set(paths))])
    return result
if __name__=='__main__':
    r=verify();(ROOT/BASE/'report.json').write_text(json.dumps(r,indent=2)+'\n')
    print('PASS private contact alignment trials:',[(q['variant'],q['pal_fields'],q['missed_audio_ticks']) for q in r['rows']])
