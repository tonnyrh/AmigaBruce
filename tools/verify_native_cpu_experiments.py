"""Verify rejected CPU probes without changing or approving production."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PERF='reference/analysis/optimization-2026-10-27'
REPORT='reference/validation/native-cpu-experiments.json'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
PAIRS=[
 ('contact-zero-baseline-r01','contact-zero-candidate-r01'),
 ('contact-zero-baseline-r01','contact-zero-summary-r01'),
 ('contact-zero-baseline-r01','contact-zero-combined-r01'),
 ('contact-memo-baseline-r01','contact-memo-candidate-r01'),
 ('contact-memo-baseline-r01','contact-memo-hashed-r01'),
 ('contact-memo-baseline-r01','contact-memo-hashed2-r01'),
 ('contact-empty-baseline-r01','contact-empty-candidate-r03'),
 ('native-arithmetic-baseline-r01','native-arithmetic-candidate-r01'),
 ('native-arithmetic-baseline-r01','native-arithmetic-packed-r01'),
 ('native-arithmetic-baseline-r01','native-arithmetic-union-r01'),
 ('native-arithmetic-baseline-r01','native-arithmetic-union-nz-r01'),
 ('native-d7-baseline-r01','native-d7-candidate-r01'),
 ('native-d7-baseline-r01','native-a4-candidate-r01'),
]

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(q):assert item(q['path'])['sha256']==q['sha256'],q['path']

def verify():
    assert item('.reference/c64/work/untrained-memory.bin')['sha256']==SHA
    assert item('core/c64_rooms.c')['sha256']=='2d3692711dfd57cd2e108e697df2c01a958e47657e3d85069ee1930dec00efc1'
    assert item('amiga/main.c')['sha256']=='6150ad3145c02756035e492f08247b98f5c8cc3394c68f8d0ef942b8c0b06de3'
    assert item('amiga/out/bruce_amiga.exe')['sha256']=='4229148ac5b324d8d5296594fd1364439a90550577796b913c1d9e6b559fa561'
    paths={'docs/NATIVE_CPU_EXPERIMENTS.md','docs/AMIGA_OPTIMIZATION_PLAN.md','tools/verify_native_cpu_experiments.py',
      'core/c64_rooms.c','core/c64_actor_programs.h','amiga/main.c','amiga/out/bruce_amiga.exe'}
    labels={name for pair in PAIRS for name in pair};runs={}
    for label in sorted(labels):
        folder=PERF+'/'+label;d=read(folder+'/identity.json');r=d['run']
        assert d['source_steps_target']==360 and d['enemy_mask']==3
        assert not d['controlled'] and not d['profile']
        assert r['source_world_steps']==r['source_perf_steps']=='360'
        assert r['restored_os']=='1' and r['contact_kernel_cases']=='710'
        for key in ['contact_kernel_errors','c64_room_fault','source_audio_faults',
                    'source_dma_faults','runtime_arithmetic_errors','vic_compare_errors']:
            assert r[key]=='0',(label,key,r[key])
        if label.startswith('native-arithmetic'):
            assert r['math_cases']=='262144' and r['math_errors']=='0'
        if label.startswith('native-d7'):
            assert r['d7_abi_cases']=='256' and r['d7_abi_errors']=='0'
        for e in d['source_files']+d['build']:check(e);paths.add(e['path'])
        paths.update([folder+'/identity.json',folder+'/native.txt'])
        runs[label]=dict(pal_fields=int(r['source_clock_elapsed']),
          audio_missed=int(r['source_clock_missed']),largest_chip=int(r['chip_largest_loaded']))
    for folder,name in [('contact-zero','host-contact.json'),('contact-empty','source-controls.json'),('native-arithmetic','source-controls.json')]:
        p=f'reference/analysis/{folder}-2026-10-31/{name}';d=read(p)
        assert d['source_sha256']==SHA;paths.add(p)
        for e in d.get('artifacts',[]):check(e);paths.add(e['path'])
    p='reference/analysis/native-d7-2026-10-31/source-world-native.json';d=read(p);r=d['run'];paths.add(p)
    assert d['status']=='passed_scoped_native_source_contract' and not d['failures']
    assert r['source_actor_fixture_cases']=='53' and r['source_actor_fixture_failure']=='0'
    assert r['frames']=='1200' and r['restored_os']=='1'
    assert not d['realtime_contract_passed']
    for e in d['source_files']+d['build']:check(e);paths.add(e['path'])
    paths.add('reference/analysis/native-d7-2026-10-31/native-final.txt')
    for folder in ['contact-zero','contact-memo','contact-empty','native-arithmetic','native-d7','native-a4']:
        base=ROOT/f'reference/analysis/{folder}-2026-10-31'
        for p in base.rglob('*'):
            if p.is_file() and p.suffix in ['.py','.ps1','.c','.h','.s'] and 'out' not in p.parts and 'fixture-out' not in p.parts:
                paths.add(p.relative_to(ROOT).as_posix())
    for name in ['build_contact_zero_probe','build_contact_memo_probe','build_contact_empty_probe',
                 'verify_contact_empty_source','build_native_arithmetic_probe','verify_native_arithmetic_source',
                 'build_native_d7_probe','generate_native_d7_wrappers','build_native_a4_probe','generate_native_a4_wrappers']:
        paths.add('tools/'+name+'.py')
    paths.add('tools/contact_align_memo.s')
    return dict(date='2026-10-31',status='rejected_isolated_cpu_probes',production_changed=False,
      source_sha256=SHA,edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,
      pairs=[dict(reference=a,candidate=b,reference_run=runs[a],candidate_run=runs[b]) for a,b in PAIRS],
      d7_full_native=dict(fixtures=53,loops=1200,largest_chip=int(r['chip_largest_loaded']),
        audio_missed=int(r['source_clock_missed']),realtime_gate_passed=False),
      artifacts=[item(p) for p in sorted(paths)],
      limits=['Fixed diagnostic route, not FPS or natural playthrough',
              'A4 pilot has no separate ABI canary before measured period',
              'No new normal EXE/ADF approved; performance problem remains open'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args();report=verify()
    if args.record:(ROOT/REPORT).write_text(json.dumps(report,indent=2)+'\n')
    else:assert read(REPORT)==report,'Evidence changed; inspect before re-recording'
    print('PASS',len(PAIRS),'bounded CPU comparisons; production unchanged; no real-time acceptance')

if __name__=='__main__':main()
