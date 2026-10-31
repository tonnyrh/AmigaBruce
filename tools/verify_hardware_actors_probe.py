"""Bind the private three-actor experiment; never approve source collision parity."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/hardware-bruce-2026-10-31/v5'
PERF='reference/analysis/optimization-2026-10-27'
RUNS=[('bob/','hardware-actors-v5-bob-r01'),('sprite/','hardware-actors-v5-sprite-r02'),
      ('moving/bob/','hardware-actors-v5-moving-bob-r01'),('moving/sprite/','hardware-actors-v5-moving-sprite-r01'),
      ('moving/observe/','hardware-actors-v5-observe-r01')]

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(e):assert item(e['path'])['sha256']==e['sha256'],e['path']

def verify():
    paths=['tools/build_hardware_actors_probe.py','tools/hardware_actors_probe.h',
           'tools/audit_hardware_actors_frame.py','tools/check_hardware_actors_boot.py',
           'tools/verify_hardware_actors_probe.py','launch-hardware-actors.ps1','docs/HARDWARE_ACTORS_PROBE.md']
    paths += [BASE+'/'+p for p in ['run-private.ps1','test-perf-private.ps1','test-world-private.ps1']]
    for prefix in ['', 'moving/']:
        p=BASE+'/'+prefix+'scope.json';scope=read(p);paths.append(p)
        assert not scope['production_changed'] and scope['checkpoint']=='ccf9572be54db49a33638d52e73c74c9f5eec740'
        for e in scope['inputs']+scope['generated']:check(e);paths.append(e['path'])
    assert item('.reference/c64/work/untrained-memory.bin')['sha256']=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    rows=[]
    for variant,label in RUNS:
        folder=PERF+'/'+label;p=folder+'/identity.json';d=read(p);r=d['run'];paths += [p,folder+'/native.txt']
        sprite=not variant.endswith('bob/');observer=variant.endswith('observe/')
        assert d['enemy_mask']==3 and d['source_steps_target']==360 and not d['profile'] and not d['controlled']
        assert r['source_world_steps']==r['source_perf_steps']=='360' and r['restored_os']=='1'
        assert int(r['max_held_image_streak'])<=3
        if not variant.startswith('moving/'):assert r['drawn_image_fields']=='360'
        assert r['hw_actors']==('3' if sprite else '0') and r['hw_observer']==str(int(observer))
        assert r['hw_bruce_cases']==('456' if sprite else '0') and r['hw_bruce_extra_chip_bytes']=='0'
        assert r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
        for k in ['hw_bruce_errors','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:assert r[k]=='0',(label,k)
        for e in d['source_files']:check(e);paths.append(e['path'])
        assert BASE+'/'+variant+'main.c' in [e['path'] for e in d['source_files']]
        for e in d['build']:
            q=folder+'/'+Path(e['path']).name;check(dict(path=q,sha256=e['sha256']));paths.append(q)
        rows.append(dict(label=label,variant=variant,pal_fields=int(r['source_clock_elapsed']),missed_audio_ticks=int(r['source_clock_missed']),largest_chip_block=int(r['chip_largest_loaded']),observer=observer,drawn_images=int(r['drawn_image_fields'])))
    assert rows[1]['drawn_images']==rows[0]['drawn_images']==360
    assert rows[3]['drawn_images']>=rows[2]['drawn_images']
    obs=read(PERF+'/hardware-actors-v5-observe-r01/identity.json')['run']
    assert int(obs['hw_observer_samples'])>0 and int(obs['hw_observer_overlap_samples'])>0
    # Differences are observations, not an acceptance gate or a safe fallback
    # proof. Current original source collision code remains authoritative.
    observation={k:int(v) for k,v in obs.items() if k.startswith('hw_observer')}
    p=BASE+'/source-world-native.json';d=read(p);r=d['run'];paths += [p,BASE+'/native-final.txt']
    assert d['status']=='passed_scoped_native_source_contract' and not d['failures']
    assert d['compile_override']['actual']==BASE+'/sprite/main.c'
    assert r['source_actor_fixture_cases']=='53' and r['frames']=='1200' and r['source_world_steps']=='400' and r['restored_os']=='1'
    assert r['hw_bruce_cases']=='456' and int(r['chip_largest_loaded'])>=49152
    for k in ['hw_bruce_errors','source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','c64_render_mismatches','capture_fault','bad_presents']:assert r[k]=='0',k
    for e in d['source_files']+d['build']:check(e);paths.append(e['path'])
    native_audio_missed=int(r['source_clock_missed'])
    seen=set();buffers=set();columns=0
    for label in ['native-display','native-combat']:
        p=BASE+'/'+label+'/report.json';d=read(p);paths.append(p);check(d['elf'])
        assert d['status']=='passed_all_actor_native_sprite_dma_descriptors' and all(d['pause_stability_checks'])
        for s in d['samples']:
            assert s['pixel_errors']==0 and s['dma_enabled'] and s['copper_list_bytes']==252 and '2: $0024' in s['custom']
            buffers.add(s['buffer'])
            for a in s['actors']:seen.add(a['actor']);columns=max(columns,a['columns'])
        for e in d['artifacts']:check(e);paths.append(e['path'])
    assert seen=={'bruce','yamo','kage'} and buffers=={0,1} and columns>=2
    p=BASE+'/native-combat/video-window.json';video=read(p)
    assert video['bruceYellow'] and video['yamoGreen'] and video['noObviousSpriteSeams'] and 'no memory injection' in video['method']
    paths += [p,BASE+'/native-combat/video-window.jpg']
    for mode in ['cli','adf']:
        p=BASE+'/normal-ui/'+mode+'/report.json';d=read(p);paths.append(p)
        assert d['complete_menu'] and d['sprite_dma_off_on_menu'];check(d['elf'])
        assert d['normal_exe_sha256']==item(BASE+'/sprite/out/bruce_amiga.exe')['sha256']
        if mode=='adf':assert len(d['game_states'])==3 and d['game_states'][-1]['steps']>d['game_states'][0]['steps']
        for e in d['artifacts']:check(e);paths.append(e['path'])
    paths += [BASE+'/normal-ui/cli/menu-video.jpg',BASE+'/normal-ui/cli/menu-video.json']
    paths += [BASE+'/sprite/out/bruce_amiga.'+ext for ext in ['exe','elf','adf']]
    return dict(status='passed_scoped_all_actor_sprite_probe',production_changed=False,source_rule_changed=False,
        hardware_collision_replaces_source=False,observer_only=True,extra_chip_allocation=0,copper_list_bytes=252,
        dma_tail_range_in_each_existing_copper=[256,996],reserved_dma_bytes_two_buffers=1480,
        timings=rows,collision_observation=observation,native_fixture_cases=53,native_replay_loops=1200,native_controlled_audio_missed_ticks=native_audio_missed,
        edition_verified=False,natural_playthrough=False,raster_exact=False,realtime_gate_passed=False,
        limitations=['Small scoped timing gains; audio misses remain and rose by one in both measured pairs',
        'Four Amiga collision groups combine channels from different actors; not the original eight VIC components',
        'Observer compares rendered masks with CLXDAT, not source$D01E equivalence or original read phase',
        'Observer recorded extra group events; their cause remains unresolved; no collision rule replaced',
        'Same-group Bruce channel2 versus Yamo channel3 has no sprite-group collision bit; zero CLXDAT is not a safe actor-contact exclusion',
        'Observer timing includes software reference overhead and must not be compared as a performance gain',
        'All210 image encodings tested; not all poses naturally witnessed; physical A500 and fullPAL remain open'],
        artifacts=[item(p) for p in sorted(set(paths))])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();target=ROOT/BASE/'report.json'
    if a.record:target.write_text(json.dumps(r,indent=2)+'\n')
    else:assert read(BASE+'/report.json')==r,'Saved experiment identity is stale'
    print(r['status']);print('timings',[(v['variant'],v['pal_fields'],v['missed_audio_ticks']) for v in r['timings']]);print('collision observation',r['collision_observation'])
