"""Verify the isolated sprite experiment, not production promotion."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/hardware-bruce-2026-10-31'
PERF='reference/analysis/optimization-2026-10-27'
RUNS=[('', 'bob','hardware-bruce-bob-r01'),('', 'sprite','hardware-bruce-sprite-r01'),
 ('v2/','bob','hardware-bruce-v2-bob-r01'),('v2/','sprite','hardware-bruce-v2-sprite-r01'),
 ('v3/','bob','hardware-bruce-v3-bob-r01'),('v3/','sprite','hardware-bruce-v3-sprite-r01'),
 ('v3/moving/','bob','hardware-bruce-v3-moving-bob-r01'),('v3/moving/','sprite','hardware-bruce-v3-moving-sprite-r01'),
 ('v4/','sprite','hardware-bruce-v4-sprite-r01'),('v4/moving/','sprite','hardware-bruce-v4-moving-sprite-r01')]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(e):assert item(e['path'])['sha256']==e['sha256'],e['path']
def verify(require_display=True):
    paths=['launch-hardware-bruce.ps1','tools/build_hardware_bruce_probe.py','tools/build_hardware_bruce_probe_v2.py','tools/build_hardware_bruce_probe_v3.py','tools/build_hardware_bruce_probe_v4.py','tools/check_hardware_bruce_boot.py','tools/build_hardware_bruce_moving.py','tools/audit_hardware_bruce_frame.py','tools/verify_hardware_bruce_probe.py','docs/HARDWARE_SPRITE_PROBE.md']
    scopes={}
    for version in ['', 'v2/','v3/','v3/moving/','v4/','v4/moving/']:
        p=BASE+'/'+version+'scope.json';scope=read(p);scopes[version]=scope;paths.append(p)
        assert not scope['production_changed'] and scope['checkpoint']=='ccf9572be54db49a33638d52e73c74c9f5eec740'
        for e in scope['inputs']+scope['generated']:check(e);paths.append(e['path'])
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    rows=[]
    for version,variant,label in RUNS:
        folder=PERF+'/'+label;identity=read(folder+'/identity.json');r=identity['run']
        assert not identity['profile'] and not identity['controlled'] and identity['source_steps_target']==360 and identity['enemy_mask']==3
        assert r['source_world_steps']==r['source_perf_steps']=='360' and r['restored_os']=='1' and r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
        for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors','hw_bruce_errors']:assert r[k]=='0',(label,k)
        assert r['hw_bruce_enabled']==('1' if variant=='sprite' else '0')
        assert r['hw_bruce_cases']==('176' if variant=='sprite' else '0') and int(r['chip_largest_loaded'])>=49152
        if variant=='sprite':assert int(r['hw_bruce_draws'])>0 and int(r['hw_bruce_builds'])>=2
        if version=='v3/moving/' and variant=='sprite':assert int(r['hw_bruce_builds'])>10
        for e in identity['source_files']:check(e)
        for e in identity['build']:check(dict(path=folder+'/'+Path(e['path']).name,sha256=e['sha256']))
        private=BASE+'/'+version+variant+'/main.c'
        assert (ROOT/private).is_file() and private in [e['path'] for e in scopes[version]['generated']]
        builder=(ROOT/BASE/version/(variant+'-build.ps1')).read_text()
        assert private in builder and "if($source -eq 'amiga/main.c')" in builder
        paths += [private,folder+'/identity.json',folder+'/native.txt']+[folder+'/'+Path(e['path']).name for e in identity['build']]
        rows.append(dict(version=version or 'v1/',variant=variant,label=label,actual_private_main=item(private),pal_fields=int(r['source_clock_elapsed']),missed_audio_ticks=int(r['source_clock_missed']),largest_chip_block=int(r['chip_largest_loaded']),sprite_builds=int(r['hw_bruce_builds']),sprite_draws=int(r['hw_bruce_draws'])))
    for version in ['v2','v3','v4']:
        p=BASE+'/'+version+'/source-world-native.json';native=read(p);r=native['run']
        assert native['status']=='passed_scoped_native_source_contract' and not native['failures'] and native['contact_reference_separate']
        assert native['compile_override']['actual']==BASE+'/'+version+'/sprite/main.c'
        for e in native['source_files']+native['build']:check(e);paths.append(e['path'])
        assert r['source_actor_fixture_cases']=='53' and r['frames']=='1200' and r['source_world_steps']=='400' and r['restored_os']=='1'
        assert r['hw_bruce_cases']=='176' and r['hw_bruce_errors']=='0' and int(r['hw_bruce_draws'])>100
        assert int(r['chip_largest_loaded'])>=49152 and r['capture_original_hash']==r['capture_decoded_hash']
        for k in ['source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','c64_render_mismatches','capture_fault','bad_presents']:assert r[k]=='0',k
        paths.append(p)
    if require_display:
        p=BASE+'/v4/native-display/report.json';display=read(p);check(display['elf'])
        assert display['status']=='passed_published_native_sprite_dma_descriptors' and len(display['samples'])>=5
        assert all(display['pause_stability_checks'])
        for s in display['samples']:assert s['pixel_errors']==0 and s['dma_enabled'] and s['copper_list_bytes']<512 and '2: $0024' in s['custom']
        for e in display['artifacts']:check(e);paths.append(e['path'])
        paths.append(p)
    if require_display:
        p=BASE+'/v4/native-punch/report.json';punch=read(p);check(punch['elf'])
        assert max(s['columns'] for s in punch['samples'])>=2
        assert all(s['pixel_errors']==0 and s['dma_enabled'] and '2: $0024' in s['custom'] for s in punch['samples'])
        for e in punch['artifacts']:check(e);paths.append(e['path'])
        paths.append(p)
        p=BASE+'/v4/bob-baseline-linkage.json';link=read(p)
        assert link['status']=='passed_identical_loaded_bob_sections' and len(link['rows'])==2
        for row in link['rows']:
            for k in ['current','baseline']:check(row[k]);paths.append(row[k]['path'])
            assert all(v['same_loaded_bytes'] or v['same_nobits_size'] for v in row['sections'].values())
        paths.append(p)
        for mode in ['cli','adf']:
            p=BASE+'/v4/normal-ui/'+mode+'/report.json';boot=read(p)
            assert boot['complete_menu'] and boot['sprite_dma_off_on_menu']
            if mode=='adf':assert len(boot['game_states'])==3 and boot['game_states'][-1]['steps']>boot['game_states'][0]['steps']
            check(boot['elf'])
            for e in boot['artifacts']:check(e);paths.append(e['path'])
            paths.append(p)
        p=BASE+'/v4/native-display/video-window.json';video=read(p)
        assert video['bruceVisible'] and video['noObviousSpriteSeams'] and 'no memory injection' in video['method']
        paths += [p,BASE+'/v4/native-display/video-window.jpg',BASE+'/v4/normal-ui/cli/menu-video.jpg',BASE+'/v4/normal-ui/cli/menu-video.json']
        assert rows[-2]['pal_fields']<next(r['pal_fields'] for r in rows if r['label']=='hardware-bruce-v3-bob-r01')
        assert rows[-1]['pal_fields']<next(r['pal_fields'] for r in rows if r['label']=='hardware-bruce-v3-moving-bob-r01')
    return dict(status='passed_scoped_hardware_bruce_probe' if require_display else 'passed_scoped_hardware_bruce_measurements_display_pending',checkpoint='ccf9572be54db49a33638d52e73c74c9f5eec740',
      production_changed=False,rows=rows,source_rule_changed=False,extra_chip_allocation_final=0,reserved_copper_tail_bytes=560,fresh_reference_controls_per_perf_image=710,hardware_format_controls_per_sprite_image=176,fresh_native_controls_per_full_image=53,native_replay_loops=1200,
      edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,limitations=['Only Bruce uses hardware sprites in this prototype','Single scoped before/after pair per route; no general frame-rate guarantee','Moving benchmark is scripted joystick input with diagnostic invincibility','Controlled full replay still has missed audio ticks; it is not the PAL timing benchmark','Original VIC/IRQ phase and physical A500 remain open','Descriptor PNGs are software reconstruction; emulator video inspection is separate'],artifacts=[item(p) for p in sorted(set(paths))])
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--measurements-only',action='store_true');a=p.parse_args()
    r=verify(not a.measurements_only);(ROOT/BASE/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status']);print([(x['label'],x['pal_fields'],x['missed_audio_ticks']) for x in r['rows']])
