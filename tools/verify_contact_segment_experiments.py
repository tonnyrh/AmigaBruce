"""Verify rejected68000 row experiments and the restored production baseline."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/contact-segments-2026-10-29'
PERF='reference/analysis/optimization-2026-10-27'
OUTPUT='reference/validation/contact-segment-experiments.json'
RULES=[
 ('contact-segment-before-detail','baseline',True,454),
 ('contact-segment-native-pilot2-timing','selector-pilot',False,1558),
 ('contact-segment-after-detail','selector-pilot',True,454),
 ('contact-live-pilot-timing','live-pilot',False,1558),
 ('contact-flags-pilot-timing','final-candidate',False,1558),
 ('contact-flags-final-detail','final-candidate',True,454)]

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(entry,path=None):assert item(path or entry['path'])['sha256']==entry['sha256'],path or entry['path']

def verify():
    paths=['tools/verify_contact_segment_experiments.py','docs/CONTACT_SEGMENT_OPTIMIZATION.md',BASE+'/source-row-disassembly.txt']
    source=item('.reference/c64/work/untrained-memory.bin')['sha256']
    assert source=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    sys.path.insert(0,str(ROOT/'.reference/tools/python'))
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    dis=Disassembler(MPU(memory=list((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes())))
    pc=0x537e;lines=[]
    while pc<0x5431:
        count,text=dis.instruction_at(pc);lines.append(f'${pc:04X} {text}');pc+=count
    actual=(ROOT/BASE/'source-row-disassembly.txt').read_text().splitlines()
    assert actual==lines,'Source-row disassembly does not match frozen bytes'
    for variant in ['baseline','selector-pilot','live-pilot','final-candidate']:
        manifest=BASE+'/'+variant+'/manifest.json';paths.append(manifest)
        for entry in read(manifest)['files']:
            path=BASE+'/'+variant+'/'+entry['path'];check(entry,path);paths.append(path)
    baseline=read(PERF+'/vic-repeat-scoped-final-timing/identity.json')
    for entry in baseline['source_files']:
        archived=BASE+'/baseline/'+entry['path'];check(entry,archived if (ROOT/archived).exists() else None)
    old=baseline['run'];assert old['source_clock_elapsed']=='1428' and old['source_clock_missed']=='21'
    paths += [PERF+'/vic-repeat-scoped-final-timing/identity.json',PERF+'/vic-repeat-scoped-final-profile/identity.json']
    rows=[]
    for label,variant,detail,cases in RULES:
        folder=PERF+'/'+label;ident=read(folder+'/identity.json')
        assert ident['profile']==detail and ident['detail_profile']==detail
        assert ident['source_steps_target']==360 and ident['outer_loop_limit']==1200
        assert ident['enemy_mask']==3 and not ident['controlled']
        assert not ident['edition_verified'] and not ident['natural_playthrough']
        for entry in ident['source_files']:
            archived=BASE+'/'+variant+'/'+entry['path']
            fallback=BASE+'/baseline/'+entry['path']
            check(entry,archived if (ROOT/archived).exists() else fallback if (ROOT/fallback).exists() else None)
        for entry in ident['build']:
            path=folder+'/'+Path(entry['path']).name;check(entry,path);paths.append(path)
        run=ident['run']
        assert run['source_perf_steps']==run['source_world_steps']=='360'
        assert run['contact_kernel_cases']==str(cases) and run['vic_repeat_cases']==('0' if detail else '1536')
        for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:
            assert run[key]=='0',(label,key)
        assert run['restored_os']=='1' and int(run['chip_largest_loaded'])>=49152
        if detail:assert run['perf_errors']=='0'
        profile=read(folder+'/native.json')['profile']
        by_name={x['name']:x for x in profile}
        rows.append(dict(label=label,variant=variant,detail_profile=detail,source_steps=360,
            pal_fields=int(run['source_clock_elapsed']),missed_audio_ticks=int(run['source_clock_missed']),
            contact_kernel_cases=cases,contact_kernel_errors=0,
            row_inclusive_lines=by_name['rows']['average_inclusive'] if detail else None,
            row_exclusive_lines=by_name['rows']['average_exclusive'] if detail else None,
            lane_exclusive_lines=by_name['contact_lanes']['average_exclusive'] if detail else None))
        paths += [folder+'/'+name for name in ['identity.json','native.txt','native.json']]
    for row in rows:
        if not row['detail_profile']:assert row['pal_fields']>=int(old['source_clock_elapsed'])
    # The later complete-row attempt was also rejected, not promoted.
    run_base='reference/analysis/contact-run-2026-10-29'
    for variant,key in [('baseline','files'),('candidate','files'),('rejected-combined-diagnostic','source_files'),('rejected-cold-entry','source_files')]:
        name='manifest.json' if variant in ('baseline','candidate') else 'rejected.json'
        manifest=run_base+'/'+variant+'/'+name;paths.append(manifest)
        for entry in read(manifest)[key]:
            path=run_base+'/'+variant+'/'+entry['path'];check(entry,path);paths.append(path)
    contact_run=[]
    for label,cases in [('contact-run-scoped3-controls',710),('contact-run-final-timing',1046),('contact-run-final-profile',454)]:
        folder=PERF+'/'+label;ident=read(folder+'/identity.json');run=ident['run']
        assert run['contact_kernel_cases']==str(cases) and run['contact_kernel_errors']=='0'
        assert run['source_world_steps']=='360' and run['source_perf_steps']=='360'
        for entry in ident['source_files']:
            path=run_base+'/candidate/'+entry['path'];fallback=BASE+'/baseline/'+entry['path']
            check(entry,path if (ROOT/path).exists() else fallback if (ROOT/fallback).exists() else None)
        for entry in ident['build']:
            path=folder+'/'+Path(entry['path']).name;check(entry,path);paths.append(path)
        paths += [folder+'/'+name for name in ['identity.json','native.txt','native.json']]
        contact_run.append(dict(label=label,fields=int(run['source_clock_elapsed']),kernel_cases=cases,errors=0))
    assert contact_run[1]['fields']==1440
    restored=[]
    for suffix in ['exe','elf','adf']:
        path=BASE+'/baseline/bruce_amiga.'+suffix
        restored.append(item(path))
    return dict(status='historical_rejected_no_total_speed_gain',date='2026-10-29',
        checkpoint='71cb4c6',source_sha256=source,baseline_pal_fields=1428,baseline_missed_audio_ticks=21,
        measurements=rows,rejected_complete_row_run=contact_run,production_runtime_changed_in_round=False,archived_baseline_build=restored,
        edition_verified=False,natural_playthrough=False,realtime_accepted=False,
        limits=['Single deterministic idle-input room1 route per variant; not all-room timing',
                'Detailed profiler overhead changes timing and call attribution',
                'Candidate512 extra tests passed separately; candidate53-fixture/full acceptance was not claimed',
                'Historical baseline restored after this rejected round; subsequent production work is verified separately'],
        artifacts=[item(p) for p in dict.fromkeys(paths)])

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    report=verify()
    if a.record:(ROOT/OUTPUT).write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'))
    else:assert read(OUTPUT)==report,'Experiment evidence is stale'
    print('PASS3 historical rejected row variants; archived baseline and measured binaries verified')
if __name__=='__main__':main()
