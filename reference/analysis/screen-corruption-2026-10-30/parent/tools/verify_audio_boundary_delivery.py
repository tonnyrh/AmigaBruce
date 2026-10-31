"""Complete-field audio poll delivery, preserving strict prior-stage proof."""
import hashlib,json
from pathlib import Path
from audio_boundary_parent import verify_parent
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/audio-service-2026-10-30'
PERF='reference/analysis/optimization-2026-10-27'
OLD='game_field_busy=1;while(gap--)bl_c64_field();game_field_busy=0;'
NEW='game_field_busy=1;while(gap--){bl_c64_field();source_audio_service();}game_field_busy=0;'
DISPATCH="def verify():\n if not globals().get('_audio_parent_replay',False):\n  from verify_audio_boundary_delivery import enabled as audio_enabled,verify_current\n  if audio_enabled():return verify_current()\n"
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def enabled():return NEW in (ROOT/'amiga/main.c').read_text(encoding='utf-8-sig')
def check(entries,historical=False):
    for e in entries:
        p=e['path']
        if historical and (not (ROOT/p).exists() or item(p)['sha256']!=e['sha256']):p=BASE+'/parent/'+p
        assert item(p)['sha256']==e['sha256'],p
def verify_current():
    assert enabled();parent=verify_parent();manifest=read(BASE+'/parent/manifest.json')
    for e in manifest['files']:
        p=e['path']
        if (p.startswith('core/') or p.startswith('amiga/')) and '/out/' not in p and p!='amiga/main.c':assert item(p)['sha256']==e['sha256'],p
    old=(ROOT/BASE/'parent/amiga/main.c').read_text(encoding='utf-8-sig');assert old.count(OLD)==1
    normal=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig');assert normal==old.replace(OLD,NEW)
    old_validator=(ROOT/BASE/'parent/tools/verify_compact_actor_delivery.py').read_text(encoding='utf-8-sig')
    assert (ROOT/'tools/verify_compact_actor_delivery.py').read_text(encoding='utf-8-sig')==old_validator.replace('def verify():\n',DISPATCH)
    scope=read(BASE+'/boundary-scope.json');check(scope['inputs'],True);check(scope['generated'])
    allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
    def diagnostic(text):return text.replace(allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}').replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
    assert diagnostic(normal)==(ROOT/BASE/'boundary/main.c').read_text(encoding='utf-8-sig')
    assert diagnostic(old)==(ROOT/'.tmp/compact-delivery/math-main.c').read_text(encoding='utf-8-sig')
    proof=read(BASE+'/diagnosis.json');assert proof['status']=='passed_scoped_native_audio_starvation_diagnostics';check(proof['artifacts'])
    paths=[BASE+'/parent/manifest.json',BASE+'/parent/reference/validation/compact-actor-delivery.json',BASE+'/boundary-scope.json',BASE+'/diagnosis.json',BASE+'/source-audio-contract.json','tools/audio_boundary_parent.py','tools/freeze_audio_boundary_parent.py','tools/verify_audio_boundary_delivery.py','tools/verify_compact_actor_delivery.py','docs/AUDIO_SERVICE_BOUNDARY.md']
    pairs={}
    for suffix,tour in [('r01',False),('tour',True)]:
        rows=[]
        for variant in ['before','after']:
            folder=PERF+'/audio-boundary-'+variant+'-'+suffix;r=read(folder+'/identity.json');check(r['source_files'],True)
            for e in r['build']:assert item(folder+'/'+Path(e['path']).name)['sha256']==e['sha256']
            values=r['run'];assert values['contact_kernel_cases']=='710' and values['sprite_copy_cases']=='256' and values['restored_os']=='1'
            assert int(values['source_clock_elapsed'])+int(values['source_clock_starts'])==int(values['source_audio_fields'])+int(values['source_music_fields'])+int(values['source_clock_missed'])
            for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors','bad_presents']:assert values[k]=='0',k
            assert int(values['chip_largest_loaded'])>=49152
            paths += [folder+'/'+p for p in ['identity.json','native.txt','bruce_test.elf','bruce_test.exe','bruce_test.adf']]
            if tour:
                assert len(r['rooms'])==20 and all(q['steps']==120 and q['chip_largest']>=49152 for q in r['rooms'])
                main=(ROOT/folder/'compiled-main.c').read_text(encoding='utf-8-sig');assert (NEW in main)==(variant=='after')
                rows.append(dict(fields=sum(q['fields'] for q in r['rooms']),missed=sum(q['missed'] for q in r['rooms']),source_steps=2400))
                paths += [folder+'/'+p for p in ['compiled-main.c','build.ps1','controller-generation.json']]
            else:assert values['source_world_steps']=='360';rows.append(dict(fields=int(values['source_clock_elapsed']),missed=int(values['source_clock_missed']),source_steps=360))
        pairs[suffix]=rows
    assert pairs['r01'][1]['missed']==0 and pairs['r01'][0]['missed']>0
    assert pairs['tour'][1]['missed']<=pairs['tour'][0]['missed']
    folder=PERF+'/audio-boundary-delivered-r01';current=read(folder+'/identity.json');check(current['source_files'])
    for e in current['build']:assert item(folder+'/'+Path(e['path']).name)['sha256']==e['sha256']
    cr=current['run'];assert cr['contact_kernel_cases']=='710' and cr['sprite_copy_cases']=='256' and cr['source_world_steps']=='360' and cr['source_clock_missed']=='0'
    for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors','bad_presents']:assert cr[k]=='0',k
    assert int(cr['chip_largest_loaded'])>=49152
    paths += [folder+'/'+p for p in ['identity.json','native.txt','bruce_test.elf','bruce_test.exe','bruce_test.adf']]
    native=read('reference/validation/source-world-native.json');check(native['source_files']+native['build']);r=native['run']
    assert not native['failures'] and r['source_actor_fixture_cases']=='53' and r['source_actor_fixture_failure']=='0' and r['frames']=='1200' and r['restored_os']=='1'
    assert native['contact_reference_separate'] and r['contact_kernel_cases']==r['sprite_copy_cases']==r['vic_repeat_cases']=='0'
    assert int(r['chip_largest_loaded'])>=49152 and int(r['max_held_image_streak'])<=3 and r['presentation_hold_fields']=='3'
    assert r['capture_original_hash']==r['capture_decoded_hash']
    for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors']:assert r[k]=='0',k
    paths.append('reference/validation/source-world-native.json')
    link='reference/analysis/flat-control-compact-2026-10-30/delivery-kernels.json';links=read(link);assert links['status']=='passed_current_compact_primitive_linkage' and links['contact_kernels']==8;check(links['artifacts']);paths.append(link)
    elf=item('amiga/out/bruce_amiga.elf')['sha256']
    for label in ['audio-boundary-native','audio-boundary-native-death']:
        p='reference/analysis/render-coherence-2026-10-29/'+label+'/report.json';q=read(p)
        assert q['elf']['sha256']==elf and q['snapshots_paused'] and len(q['samples'])>=12
        for k in ['mixed_phase_samples','max_pixel_mismatch','max_static_pixel_mismatch','max_flicker_illegal_pixels']:assert q[k]==0,k
        assert not q['flicker_stuck_codes']
        if label.endswith('death'):assert q['room_roundtrip'] and q['controlled_death']['loader_epoch_after']!=q['controlled_death']['loader_epoch_before']
        paths.append(p);paths += [f.relative_to(ROOT).as_posix() for f in (ROOT/Path(p).parent).glob('*') if f.suffix in ['.bpl','.bin']]
    p='reference/analysis/menu-publication-2026-10-29/audio-boundary-menu/report.json';q=read(p)
    assert q['elf']['sha256']==elf and q['status']=='passed_scoped_native_menu_publication' and q['source_ram_preserved_during_choices'] and q['changed_partial_hidden_samples']>0
    assert len(q['transitions'])>=10 and len(q['starts'])==2 and {s['menu_front'] for s in q['starts']}=={0,1} and all(s['complete_front'] for s in q['samples'])
    paths.append(p);paths += [f.relative_to(ROOT).as_posix() for f in (ROOT/Path(p).parent).glob('*') if f.suffix in ['.bpl','.bin']]
    p='reference/analysis/actor-chain-2026-10-26/normal-clock.json';q=read(p);check([q['binary']])
    assert len(q['pairs'])==3 and all(s['fault']==0 for s in q['samples']) and all(s['source_fields']>0 and s['clock_min']-2<=s['source_fields']<=s['clock_max']+2 for s in q['pairs']);paths.append(p)
    boot=read(BASE+'/normal-boot.json');check(boot['artifacts']);assert boot['cli_passed'] and boot['adf_passed'] and boot['normal_exe_sha256']==item('amiga/out/bruce_amiga.exe')['sha256'];paths.append(BASE+'/normal-boot.json')
    assert item('.tmp/amiga-boot/c/start')['sha256']==item('amiga/out/bruce_amiga.exe')['sha256']
    outputs=['amiga/out/bruce_amiga.'+s for s in ['exe','elf','adf']]+['.tmp/amiga-boot/c/start']
    result=dict(parent,status='scoped_complete_audio_boundary_acceptance_open',largest_chip_block=int(r['chip_largest_loaded']),normal_build=[item(p) for p in outputs],
        audio_boundary=dict(pairs=pairs,method='Existing audio service polled after complete field calls; same game-field count; SID guards/order/data unchanged'),
        artifacts=[item(p) for p in sorted(set(paths))])
    return result
