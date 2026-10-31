"""Evidence for enemy-dependent cost; this is not a delivery acceptance gate."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/enemy-cost-2026-10-30'
PERF='reference/analysis/optimization-2026-10-27'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def verify():
    expected={'.reference/c64/work/untrained-memory.bin':'092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8',
      'core/c64_rooms.c':'2d3692711dfd57cd2e108e697df2c01a958e47657e3d85069ee1930dec00efc1',
      'core/c64_actor_programs.h':'a85c42da6af9e042fa903e9c1d6927144e50cce2ba3480edbe3ae13f78b53f2e',
      'amiga/main.c':'7e2ee65e342803dfd711a6fc0513ec080666aee82841b4a7b63073b1e6ef0f99',
      'amiga/out/bruce_amiga.exe':'79c09ce3150db6d61ffd0eb78ff3de31bfc27166f3d604512e21478e518a6697'}
    paths=set(expected)
    paths.update([BASE+'/main.c',BASE+'/build.ps1',BASE+'/scope.json',BASE+'/run-matrix.ps1',
      'tools/build_enemy_cost_probe.py','tools/build_stationary_enemy_probe.py',
      'tools/build_native_sprite_driver.py','tools/build_native_sprite_driver_v2.py',
      'tools/build_native_sprite_driver_v3.py','tools/build_stationary_image_probe.py',
      'tools/archive_enemy_cost_run.py','tools/verify_enemy_cost.py','docs/ENEMY_COST.md'])
    historical=[]
    for p,sha in expected.items():
        if item(p)['sha256']==sha:continue
        # A later, separately verified display correction changes main/EXE.
        # Keep the experiment bound to its actual pre-correction inputs.
        assert p in ['amiga/main.c','amiga/out/bruce_amiga.exe'],p
        archived='reference/analysis/screen-corruption-2026-10-30/parent/'+p
        assert item(archived)['sha256']==sha,p
        paths.remove(p);paths.add(archived);historical.append(archived)
    runs={}
    for label in ['enemy-cost-none-timing','enemy-cost-both-timing','enemy-cost-stationary-r01','enemy-cost-image-driver-r01','enemy-cost-image-driver-v2-r02','enemy-cost-stationary-image-v2-r01','enemy-cost-image-driver-v3-r01']:
        folder=PERF+'/'+label;report=read(folder+'/identity.json');r=report['run']
        assert r['source_world_steps']=='360' and r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256' and r['restored_os']=='1'
        for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors']:assert r[k]=='0',(label,k)
        assert int(r['chip_largest_loaded'])>=49152
        for e in report['build']:
            p=folder+'/'+Path(e['path']).name;assert item(p)['sha256']==e['sha256'];paths.add(p)
        paths.update([folder+'/identity.json',folder+'/native.txt'])
        runs[label]=dict(fields=int(r['source_clock_elapsed']),missed=int(r['source_clock_missed']),chip_largest=int(r['chip_largest_loaded']))
        if 'enemy_stationary_0' in r:
            assert r['enemy_stationary_ram_type']=='5'
            rows=[list(map(int,r['enemy_stationary_'+str(i)].split(','))) for i in range(8)]
            assert all(q[3]==0 and q[4]==[3,15,19,31][i%4] for i,q in enumerate(rows))
            runs[label]['stationary_lines_64_calls']=rows
        override=ROOT/folder/'compile-overrides.json'
        if override.exists():
            paths.add(folder+'/compile-overrides.json')
            meta=read(folder+'/compile-overrides.json')
            for e in meta.get('actual_private_inputs',[]):
                assert item(e['archived'])['sha256']==e['sha256'];paths.add(e['archived'])
    for variant in ['image-driver','image-driver-v2','image-driver-v3']:
        p=BASE+'/'+variant+'-source.json';q=read(p)
        assert q['cases']==3328 and q['instructions']==3836708 and q['all_ram_register_return']
        assert q['source_sha256']==expected['.reference/c64/work/untrained-memory.bin']
        for e in q['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.add(e['path'])
        paths.add(p)
    baseline=runs['enemy-cost-stationary-r01']['stationary_lines_64_calls']
    after=runs['enemy-cost-stationary-image-v2-r01']['stationary_lines_64_calls']
    assert all(b[2]<a[2] and abs(b[0]-a[0])<=2 and abs(b[1]-a[1])<=2 for a,b in zip(baseline,after))
    result=dict(status='diagnosed_private_candidates_not_delivered',production_changed=False,edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,historical_baseline_inputs=historical,
      source_routines=dict(contact='$5212-$52AC; rows $5380-$542D',image_build='$2584-$25E1; glyph $2719-$274E; pointer $2704-$2718',copy='$26A0-$2702'),
      method='Fixed actor poses, two controlled layouts, 8 warm-up + 64 measured calls per kernel; original source bytes compared separately. Stationary microprobe excludes AI and Amiga actor drawing. Actual PAL/OCS/68000/512+512 timing run retains normal scheduler and diagnostic overhead.',
      runs=runs,sprite_kernel_reduction_both=1-after[3][2]/baseline[3][2],
      limitations=['Injected stationary controls do not establish natural C64 behavior.','Elapsed PAL counters include startup and diagnostic overhead.','Source comparison validates the portable native driver; existing 256 target controls validate its assembly copy primitive.','Private candidates have missed audio ticks; no performance or audio acceptance is claimed.','Contact computation remains the dominant fixed-actor cost; enemy AI is not the primary explanation for stationary slowdown.'],
      artifacts=[item(p) for p in sorted(paths)])
    (ROOT/BASE/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS original enemy-cost experiment and frozen baseline; private candidates remain undelivered')
    return result
if __name__=='__main__':verify()
