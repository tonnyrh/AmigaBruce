"""Bind the diagnostic timing records to actual compiled private inputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/audio-service-2026-10-30'
PERF='reference/analysis/optimization-2026-10-27'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def check(entries):
    for e in entries:
        p=ROOT/e['path']
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=e['sha256']:p=ROOT/BASE/'parent'/e['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],e['path']
def main():
    raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    sha=hashlib.sha256(raw).hexdigest();assert sha=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    assert raw[0x15a8:0x15b8]==bytes.fromhex('d8 a9 00 85 44 a6 29 20 03 eb 20 73 ef 20 73 f0')
    assert raw[0x4915:0x4918]==bytes.fromhex('20 a8 15')
    assert raw[0x1bc2:0x1bc6]==bytes.fromhex('a9 03 85 48') and raw[0x1676:0x1678]==bytes.fromhex('c6 48')
    contract=dict(source_sha256=sha,edition_verified=False,
        rules=[dict(address='$4915',bytes='20 A8 15',effect='Game raster handler calls $15A8'),
            dict(address='$15A8-$15B7',bytes=raw[0x15a8:0x15b8].hex(),effect='CLD; clear$44; X=room; drivers$EB03,$EF73,$F073 in that order'),
            dict(address='$1BC2/$1676',effect='Main step sets$48=3; existing field tail decrements$48. Candidate does not alter those writes or field-call count')],
        limits=['SID slot is source-derived; natural interrupt PC/phase and mask distribution remain open','Complete-field poll reuses existing Amiga active/busy/same-field guards; it is not a full source IRQ integration'])
    (ROOT/BASE/'source-audio-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    proofs=[BASE+'/source-audio-contract.json','tools/build_audio_service_probe.py','tools/audit_audio_service_probe.py']
    runs=[]
    for variant,scope_path,label,words in [('probe','scope.json','audio-service-probe-r01',10),('split','split-scope.json','audio-service-split-r01',16)]:
        scope=read(BASE+'/'+scope_path);check(scope['inputs']+scope['generated'])
        folder=PERF+'/'+label;identity=read(folder+'/identity.json');check(identity['source_files']);r=identity['run']
        for e in identity['build']:assert item(folder+'/'+Path(e['path']).name)['sha256']==e['sha256']
        assert r['source_world_steps']=='360' and r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
        for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors','bad_presents']:assert r[k]=='0',k
        assert int(r['chip_largest_loaded'])>=49152 and r['restored_os']=='1'
        events=[]
        for i in range(16):
            key='audio_probe_'+str(i)
            if key not in r:break
            v=list(map(int,r[key].split(',')));assert len(v)==words and v[4]>1
            event=dict(index=i,previous_audio_lines=(v[1]-v[0])&0xffffff,
                tick_end_to_next_start_lines=(v[2]-v[1])&0xffffff,
                current_audio_lines=(v[3]-v[2])&0xffffff,field_gap=v[4],
                previous_poll_site=v[5],current_site=v[6],previous_context=v[7],current_context=v[8],row=v[9])
            if words==16:
                event['last_field_call_lines']=(v[11]-v[10])&0xffffff
                event['field_call_inside_tick_interval']=v[1]<=v[10]<=v[11]<=v[2]
                event['source_prefix_sections_lines']=[(v[j+1]-v[j])&0xffffff for j in range(12,15)]
                event['prefix_inside_tick_interval']=v[1]<=v[12]<=v[13]<=v[14]<=v[15]<=v[2]
            events.append(event)
        assert events and all(e['current_audio_lines']<=int(r['source_tick_max_lines']) for e in events)
        runs.append(dict(variant=variant,elapsed=int(r['source_clock_elapsed']),missed=int(r['source_clock_missed']),events=events))
        proofs += [BASE+'/'+scope_path,folder+'/identity.json',folder+'/native.txt']+[e['path'] for e in scope['generated']]+[folder+'/bruce_test.'+s for s in ['exe','elf','adf']]
    report=dict(status='passed_scoped_native_audio_starvation_diagnostics',source_sha256=sha,production_changed=False,
        edition_verified=False,natural_playthrough=False,diagnostics_change_cpu_cost_and_field_phase=True,
        record_semantics='Audio-end-to-next-start includes healthy polling/waiting; it is not all unpolled CPU time. Recorded last field/prefix intervals are classified only when inside the same observed interval.',
        runs=runs,artifacts=[item(p) for p in sorted(set(proofs))])
    (ROOT/BASE/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS frozen SID call order and two710-control diagnostic runs; instrumentation is not delivery')
if __name__=='__main__':main()
