"""Check the source-room delivery; CPU fixtures are not natural-play parity."""
from datetime import date
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def artifact(path):
    p=ROOT/path
    return dict(path=path,size_bytes=p.stat().st_size,sha256=sha(p))
def sources(report):
    for item in report['source_files']:
        assert sha(ROOT/item['path'])==item['sha256'],f"Stale source evidence: {item['path']}"

def verify(write=False):
    if (ROOT/'reference/analysis/ai-audit-2026-10-25/report.json').exists():
        from audit_c64_ai import verify as verify_ai
        verify_ai()
    if (ROOT/'reference/validation/npc-recoil-delivery.json').exists():
        from verify_npc_recoil_delivery import verify as verify_recoil
        verify_recoil()
        return
    if (ROOT/'reference/validation/climb-delivery.json').exists():
        from verify_climb_delivery import verify as verify_climb
        verify_climb()
        return
    if (ROOT/'reference/validation/c64-sprites-delivery.json').exists():
        from verify_sprite_delivery import verify as verify_sprites
        verify_sprites()
        return
    if (ROOT/'reference/validation/movement-delivery.json').exists():
        from verify_movement_delivery import verify as verify_movement
        verify_movement()
        return
    if (ROOT/'reference/validation/contact-delivery.json').exists():
        from verify_contact_delivery import verify as verify_contacts
        verify_contacts()
        return
    if (ROOT/'reference/validation/source-audio-delivery.json').exists():
        from verify_audio_delivery import verify as verify_audio
        verify_audio()
        return
    # Actor changes supersede the earlier all-room build. Its measurements
    # remain historical; the new bounded audit never reuses their native pass.
    if (ROOT/'reference/validation/test-audit.json').exists():
        from verify_test_audit import verify as verify_audit
        verify_audit()
        return
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    if source.exists():assert sha(source)==SOURCE_SHA,'Frozen candidate changed'
    extraction=read('assets/c64/rooms-v1/manifest.json')
    assert extraction['source']['sha256']==SOURCE_SHA and not extraction['edition_verified']
    assert extraction['room_count']==20
    for item in extraction['generated_outputs']+extraction['assets']:
        assert sha(ROOT/item['path'])==item['sha256'],item['path']
    graphics=read('assets/c64/rooms-v1/graphics-validation.json')
    assert graphics['room_count']==20 and graphics['source_sha256']==SOURCE_SHA
    for index,item in enumerate(graphics['images'],1):
        assert sha(ROOT/item['path'])==item['sha256']
        fmt=read(f'reference/validation/c64-graphics-format/room-{index:02}.json')
        assert fmt['valid'] and not fmt['errors']
        assert (fmt['width'],fmt['height'],fmt['colors'])==(320,200,16)
        assert (fmt.get('output_sha256') or fmt['input_sha256'])==item['sha256']
    cpu=read('reference/validation/c64-room-runtime.json');sources(cpu)
    assert cpu['source_sha256']==SOURCE_SHA and cpu['rooms']==20
    assert cpu['source_loop_calls']==2560 and cpu['contact_checks']>=1860
    assert cpu['source_animation_calls']==160
    assert len(cpu['animation_cache_checks'])==20
    assert all(v['max_presentation_parts']<=2 for v in cpu['animation_cache_checks'])
    assert cpu['door_gate_checks']==640 and cpu['dynamic_room_images_compared']==40
    assert not cpu['natural_playthrough'] and not cpu['hardware_parity']
    host=read('reference/validation/c64-core.json');sources(host)
    assert not host['natural_playthrough'] and not host['c64_combat_parity']
    combat_expected=dict(part.split('=') for line in host['output'] if line.startswith('M3_6000 ') for part in line.split()[1:])
    runs=[];strict_realtime=True
    room_report='a500-c64-rooms.json' if (ROOT/'reference/validation/a500-c64-rooms.json').exists() else 'a500-c64-rooms-diagnostic.json'
    combat_report='a500-c64-combat.json' if (ROOT/'reference/validation/a500-c64-combat.json').exists() else 'a500-c64-combat-diagnostic.json'
    for name,frames in [(room_report,7200),(combat_report,6000)]:
        report=read('reference/validation/'+name);sources(report)
        prefix='source-rooms' if frames==7200 else 'source-combat'
        assert sha(ROOT/f'amiga/out/validated/{prefix}.exe')==report['executable_sha256']
        assert sha(ROOT/f'amiga/out/validated/{prefix}.adf')==report['adf_sha256']
        assert report['c64_parity']=='not_certified'
        assert len(report['runs'])==(1 if frames==7200 else 2)
        if report.get('preview'):
            assert sha(ROOT/report['preview']['path'])==report['preview']['sha256']
        for run in report['runs']:
            assert int(run['frames'])==frames and run['restored_os']=='1'
            assert run['bad_presents']=='0' and run['source_profile']=='0'
            collecting=report.get('collection_only',False)
            assert run['collect_frame_drops']==str(int(collecting))
            if collecting:
                strict_realtime=False
            else:
                assert run['missed_frames']=='0'
                assert int(run['max_gap_excluding_framebuffer_capture'])<=1
            headroom=65536 if report['execution']=='ADF boot' else 49152
            assert report['chip_headroom_requirement']==headroom
            headroom_met=int(run['chip_largest_loaded'])>=headroom
            if not collecting:assert headroom_met
            else:assert int(run['chip_largest_loaded'])>0
            assert run['canvas_residue_bytes']=='0' and run['c64_room_fault']=='0'
            assert run['c64_render_mismatches']=='0'
            assert run['runtime_arithmetic_errors']=='0'
            assert int(run['sfx_played'])==int(run['sfx_silence_reloads'])
            if frames==7200:
                assert run['visited_rooms_mask']=='1048575' and int(run['c64_render_checks'])>=20
            else:
                assert combat_expected and all(run[key]==value for key,value in combat_expected.items())
            runs.append(dict(report=name,frames=frames,max_work_lines=int(run['max_work_lines']),
                             chip_largest_loaded=int(run['chip_largest_loaded']),
                             room_load_max_gap=int(run['room_load_max_gap']),
                             held_image_fields=int(run['held_image_fields']),
                             drawn_image_fields=int(run['drawn_image_fields']),
                             max_held_image_streak=int(run['max_held_image_streak'])))
            runs[-1].update(collection_only=collecting,missed_fields=int(run['missed_frames']),
                            chip_reserve_target=headroom,chip_reserve_target_met=headroom_met,
                            max_period_gap=int(run['max_gap_excluding_framebuffer_capture']))
            assert int(run['held_image_fields'])+int(run['drawn_image_fields'])==frames
    normal=read('reference/validation/interactive-build.json');sources(normal)
    assert normal['build']=='c64_source_rooms_v1' and not normal['test_control']
    assert normal['launcher_process_and_config_verified']
    assert normal['cli_start_sha256']==sha(ROOT/'amiga/out/bruce_amiga.exe')
    assert normal['cli_stack_bytes']==16384
    sources(read('reference/validation/c64-stack-frames.json'))
    for item in normal['artifacts']:assert sha(ROOT/item['path'])==item['sha256']
    names=['assets/c64/rooms-v1/manifest.json','assets/c64/rooms-v1/graphics-validation.json',
           'reference/validation/c64-room-runtime.json','reference/validation/c64-core.json',
           'reference/validation/'+room_report,'reference/validation/'+combat_report,
           'reference/validation/interactive-build.json','tools/verify_c64_candidate.py',
           'reference/validation/c64-stack-frames.json',
           'tools/collect_c64_native_replay.py','reference/validation/c64-replay-1.txt','reference/validation/c64-replay-2.txt',
           'amiga/out/validated/source-rooms.exe','amiga/out/validated/source-rooms.adf',
           'amiga/out/validated/source-combat.exe','amiga/out/validated/source-combat.adf',
           'amiga/out/bruce_amiga.exe','amiga/out/bruce_amiga.adf']
    candidate=dict(date=str(date.today()),status=('passed_scoped_c64_source_room_delivery' if strict_realtime else 'source_rooms_implemented_a500_realtime_gate_open'),
        source_sha256=SOURCE_SHA,primary_edition_verified=False,room_count=20,
        original_room_pixels_shipped=True,existing_amiga_actor_art_present=True,
        full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,natural_playthrough_verified=False,
        all_room_realtime_gate_passed=strict_realtime,
        all_chip_reserve_targets_passed=all(v['chip_reserve_target_met'] for v in runs),
        every_field_has_new_image=all(v['held_image_fields']==0 for v in runs),
        presentation_policy='Retain the displayed image when rendering would delay the next PAL field; source logic continues. Room loads are measured separately.',
        actor_logic_fully_ported=False,source_cpu_loop_calls=2560,source_contact_checks=cpu['contact_checks'],
        native_runs=runs,artifacts=[artifact(p) for p in names])
    if write:
        def save(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        save('reference/validation/c64-candidate.json',candidate)
        save('reference/validation/visual-candidate.json',candidate)
        save('docs/parity/evidence/ROOM-RUNTIME-0001.json',dict(id='ROOM-RUNTIME-0001',
            date=str(date.today()),status='candidate_code_derived_partial',
            summary='All20 source room init/loop routines, ripped room characters, pixel contact and original door gates; source CPU fixtures and A500 inspection checked. A500 real-time and CLI Chip reserve gates, full actor logic and natural completion remain open.' if not strict_realtime else 'All20 source room programs and ripped characters checked against source CPU fixtures and scoped A500 runtime. Full actor/natural-play parity remains open.',
            full_original_parity=False,artifacts=[artifact('reference/validation/c64-candidate.json')]))
    else:
        saved=read('reference/validation/c64-candidate.json')
        for item in saved['artifacts']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    print('VERIFIED scoped records:20 source rooms and ripped OCS graphics; strict real-time gate='+str(strict_realtime)+'; Chip reserve targets='+str(candidate['all_chip_reserve_targets_passed'])+'; actor/natural-play parity remains open')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true')
    verify(parser.parse_args().write)
