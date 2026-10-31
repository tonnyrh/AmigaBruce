"""Bind scoped source controls and native results to the delivered files."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/actor-chain-2026-10-26'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def artifact(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def identities(items):
    for item in items:assert artifact(item['path'])['sha256']==item['sha256'],f'Stale evidence: {item["path"]}'
def verify():
    from verify_compact_actor_delivery import enabled,verify as verify_compact
    if enabled():
        verify_compact()
        return (artifact('.reference/c64/work/untrained-memory.bin')['sha256'],read(FOLDER+'/report.json'),read(FOLDER+'/integrated-controls.json'),read('reference/validation/source-world-native.json'))
    source=artifact('.reference/c64/work/untrained-memory.bin')['sha256']
    assert source=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    controls=read(FOLDER+'/report.json');world=read(FOLDER+'/integrated-controls.json')
    translation=read(FOLDER+'/translation.json');fixture=read(FOLDER+'/native-fixture.json')
    for report in (controls,world,translation,fixture):
        assert report['source_sha256']==source and not report['edition_verified'] and not report['natural_playthrough']
        identities(report.get('source_files',[]));identities(report.get('generated',[]))
    assert controls['checks']==3034 and len(controls['rows'])==3034
    assert len(world['checks'])==5 and world['instructions']==7055873
    assert world['checks'][-1]['stop']=='$0584' and world['checks'][-1]['terminal_life']
    assert all(row['life_events']>=1 for row in world['checks'])
    vic=read('reference/validation/source-vic-host.json')
    assert vic['status']=='passed_field_sampled_pixel_and_latch_controls' and vic['calls']==8741
    assert not vic['original_raster_verified'];identities(vic['source_files'])
    contact=read('reference/validation/source-contact-host.json')
    assert contact['status']=='passed_original_byte_contact_controls' and contact['checks']==4239
    assert contact['service_register_cases']==489
    assert contact['source_sha256']==source and not contact['natural_playthrough'];identities(contact['source_files'])
    sprites=read('reference/validation/source-sprite-copy-host.json')
    assert sprites['status']=='passed_original_sprite_copy_bytes' and sprites['checks']==1536
    assert sprites['instructions']==373464 and sprites['brk_controls']==312
    assert sprites['source_sha256']==source and not sprites['natural_playthrough'];identities(sprites['source_files'])
    sprite_evidence=read('docs/parity/evidence/SPRITE-COPY-0001.json')
    assert sprite_evidence['source_sha256']==source and not sprite_evidence['realtime_accepted']
    identities(sprite_evidence['artifacts'])
    objects=read('reference/validation/source-object-host.json')
    assert objects['status']=='passed_original_object_handler_boundaries' and objects['checks']==65536
    assert objects['instructions']==2473160 and len(objects['targets'])==11
    assert objects['driver_checks']==480 and objects['driver_instructions']==194645
    scores=read('reference/validation/source-score-host.json')
    assert scores['status']=='passed_original_decimal_score_loops' and scores['checks']==2852
    assert scores['instructions']==1791056 and scores['entry_status_patterns']==64
    for report in (objects,scores):
        assert report['source_sha256']==source and not report['natural_playthrough'];identities(report['source_files'])
    visibility=read('reference/validation/source-visibility-host.json')
    assert visibility['status']=='passed_original_active_bit_projection' and visibility['checks']==768
    assert visibility['source_sha256']==source and visibility['source_ram_unchanged_except_injected_flags']
    identities(visibility['source_files'])
    boot=read('reference/validation/source-native-boot.json')
    assert boot['status']=='passed_owned_cli_adf_smoke' and not boot['natural_playthrough']
    assert boot['settings']==dict(cpu_model='68000',cpu_speed='real',chipset='ocs',chipmem_size='1',bogomem_size='2',fastmem_size='0',ntsc='false')
    identities([boot['binary'],boot['adf']]+boot['artifacts'])
    ready=read(boot['menu_readiness'])
    assert ready['source_audio_mode']==1 and ready['source_music_fields']>=10
    assert ready['normal_binary']==boot['binary']
    assert ready['artifacts'][0]['sha256']=='4100ef5dd7322650586771c52c40116a4d77cd16a212b6c5f3586d43b3edd79c'  # Complete initial menu, not audio readiness alone.
    native_visibility=read('reference/validation/source-visibility-native.json')
    assert native_visibility['status']=='passed_owned_native_visibility_lifecycle'
    assert native_visibility['controlled_injection'] and not native_visibility['natural_playthrough']
    identities([native_visibility['binary']]+native_visibility['source_files']+native_visibility['artifacts'])
    assert [x['flags']&1 for x in native_visibility['states']]==[1,0,1]
    assert all(not any(rect) for rect in native_visibility['states'][1]['buffer_dirty'])
    paint=read('reference/validation/source-paint-host.json')
    assert paint['status']=='passed_source_paint_requeue_controls' and len(paint['cases'])==6
    identities(paint['source_files'])
    from verify_render_coherence import verify as verify_render
    assert read('reference/validation/render-coherence.json')==verify_render()
    from verify_view_projection import verify as verify_view
    assert read('reference/validation/view-projection.json')==verify_view()
    from verify_vic_cache_optimization import verify as verify_cache
    assert read('reference/validation/vic-cache-optimization.json')==verify_cache()
    from verify_final_color_scope import verify as verify_colors
    assert read('reference/analysis/final-colors-2026-10-30/source-scope.json')==verify_colors()
    from verify_final_color_optimization import verify as verify_color_performance
    assert read('reference/validation/final-colors-optimization.json')==verify_color_performance()
    color_images=read('reference/analysis/final-colors-2026-10-30/native-images.json')
    assert color_images['status']=='passed_original_writer_and_native_color_kernel_linkage' and len(color_images['builds'])==4
    identities(color_images['builds']+color_images['artifacts'])
    from verify_color_observer_optimization import verify as verify_observer
    assert read('reference/validation/color-observer-optimization.json')==verify_observer()
    from verify_menu_publication import verify as verify_menu
    assert read('reference/validation/menu-publication.json')==verify_menu()
    trap=read('reference/validation/source-trap-native.json')
    assert trap['status']=='passed_owned_r06_negative_phase_trap_pixels'
    assert not trap['source_ram_injected'] and not trap['natural_playthrough']
    identities([trap['binary']]+trap['source_files']+trap['artifacts'])
    assert len(trap['samples'])==3
    for sample in trap['samples']:
        assert sample['background_mismatches']==0 and sample['phase_source']&128
        assert len(sample['buffers'])==2
        assert all(not v['actor_intersects_roi'] and v['mismatches']==0 for v in sample['buffers'])
    assert len(fixture['cases'])==53;identities([fixture['fixture']])
    native=read('reference/validation/source-world-native.json');identities(native['source_files']+native['build'])
    assert native['status']=='passed_scoped_native_source_contract' and not native['failures']
    assert native['run']['source_actor_fixture_cases']=='53' and native['run']['source_actor_fixture_failure']=='0'
    assert native['run']['vic_compare_errors']=='0'
    assert native['run']['vic_repeat_cases']=='0'
    assert native['contact_reference_separate'] and native['run']['contact_reference_separate']=='1'
    assert native['run']['contact_kernel_cases']=='0' and native['run']['contact_kernel_errors']=='0'
    separate='reference/analysis/optimization-2026-10-27/color-observer-r01'
    kernels_run=read(separate+'/identity.json')
    # Current710-control image uses the delivered core and unchanged normal
    # main, separately from the53-fixture image. All identities must match.
    identities(kernels_run['source_files'])
    for build in kernels_run['build']:
        entry=dict(path=separate+'/'+Path(build['path']).name,sha256=build['sha256']);identities([entry])
    assert kernels_run['run']['contact_kernel_cases']=='710' and kernels_run['run']['sprite_copy_cases']=='256'
    for key in ['contact_kernel_errors','vic_compare_errors','source_audio_faults','source_dma_faults','c64_room_fault']:
        assert kernels_run['run'][key]=='0'
    from audit_contact_kernel_images import verify as verify_contacts
    assert read('reference/analysis/render-coherence-2026-10-29/contact-kernel-images.json')==verify_contacts()

    assert native['run']['restored_os']=='1' and native['run']['c64_room_fault']=='0'
    assert int(native['run']['chip_largest_loaded'])>=49152
    kernels=read('reference/analysis/vic-repeat-2026-10-28/native-kernel-bytes.json')
    assert kernels['status']=='passed_identical_native_vic_kernel_bytes' and len(kernels['builds'])==4
    assert set(kernels['kernels'])=={'bl_vic_repeat','bl_vic_equal63'}
    identities(kernels['builds']+kernels['source_files'])
    assert next(x for x in native['build'] if x['path'].endswith('.elf')) in kernels['builds']
    sprite_kernel=read('reference/analysis/sprite-copy-2026-10-29/native-kernel-bytes.json')
    assert sprite_kernel['status']=='passed_identical_sprite_kernel_and_entry_gate' and len(sprite_kernel['builds'])==5
    assert sprite_kernel['entry_gate_rejects_real_counterexample']
    identities(sprite_kernel['builds']+sprite_kernel['source_files']+[sprite_kernel['rejected_entry_counterexample']])
    assert next(x for x in native['build'] if x['path'].endswith('.elf')) in sprite_kernel['builds']
    assert native['run']['sprite_copy_cases']=='0'
    clock=read(FOLDER+'/normal-clock.json');identities([clock['binary']])
    assert all(x['fault']==0 for x in clock['samples']) and len(clock['pairs'])==3
    assert all(x['source_fields']>0 and x['clock_min']-2<=x['source_fields']<=x['clock_max']+2 for x in clock['pairs'])
    return source,controls,world,native
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    from verify_compact_actor_delivery import enabled,verify as verify_compact
    if enabled():
        scoped=verify_compact();scoped_path='reference/validation/compact-actor-delivery.json'
        if args.record:(ROOT/scoped_path).write_text(json.dumps(scoped,indent=2)+'\n')
        else:assert read(scoped_path)==scoped
        report=dict(scoped,artifacts=scoped['artifacts']+[artifact(scoped_path)])
        target='reference/validation/source-world-delivery.json'
        if args.record:
            (ROOT/target).write_text(json.dumps(report,indent=2)+'\n')
            evidence=dict(id='ACTOR-CHAIN-0001',date='2026-10-30',status=scoped['status'],source_sha256=scoped['source_sha256'],primary_edition_verified=False,natural_playthrough=False,full_original_parity=False,condition='Complete source chain with byte-preserving native continuation plumbing; source RAM/register/return, forced recursive fallback, native primitives and normal image controls',controls=dict(source=3034,integrated=5,native=53,reference=710),artifacts=[artifact(scoped_path),artifact(target)],limitations=scoped['open_gates'])
            (ROOT/'docs/parity/evidence/ACTOR-CHAIN-0001.json').write_text(json.dumps(evidence,indent=2)+'\n')
        else:assert read(target)==report
        print('PASS current compact source-world delivery; original-parity and real-time acceptance remain open')
        return
    source,controls,world,native=verify()
    path='reference/validation/source-world-delivery.json'
    if args.record:
        proofs=[FOLDER+'/'+name for name in ('report.json','translation.json','integrated-controls.json','native-fixture.json','native-final.txt')]
        proofs += ['tools/audit_normal_source_clock.py',FOLDER+'/normal-clock.json','reference/validation/source-world-native.json','docs/MILESTONE_COMPLETION.md','docs/ACTIVE_TESTS.md','docs/PROJECT_PLAN.md','docs/parity/register.csv','tools/verify_source_world_delivery.py','test-parity.ps1','README.md']
        proofs += ['reference/validation/source-vic-host.json','docs/AMIGA_OPTIMIZATION_PLAN.md','docs/AMIGA_OPTIMIZATION_REPORT.md']
        proofs += ['reference/validation/source-native-boot.json']
        proofs += ['reference/validation/color-observer-optimization.json','tools/verify_color_observer_optimization.py','reference/analysis/color-observer-2026-10-30/native-images.json','reference/analysis/publication-2026-10-30/report.json','docs/BUFFER_PUBLICATION.md','tools/verify_publication_guard.py']
        proofs += ['reference/validation/menu-publication.json','tools/verify_menu_publication.py','tools/audit_native_menu_publication.py','docs/MENU_PUBLICATION.md','docs/parity/evidence/MENU-PUBLICATION-0001.json']
        proofs += ['reference/validation/vic-cache-optimization.json','reference/validation/vic-cache-host.json','tools/verify_vic_cache_optimization.py','tools/verify_vic_cache.py','tests/vic_cache_bridge.c','test-vic-cache.ps1','docs/VIC_CACHE_OPTIMIZATION.md','docs/parity/evidence/VIC-CACHE-0001.json']
        proofs += ['reference/validation/view-projection.json','reference/validation/view-mask-host.json','tools/verify_view_projection.py','docs/VIEW_PROJECTION_OPTIMIZATION.md','test-view-mask.ps1','docs/parity/evidence/VIEW-PROJECTION-0001.json']
        proofs += ['reference/validation/final-colors-optimization.json','tools/verify_final_color_optimization.py','docs/parity/evidence/FINAL-COLORS-0001.json','reference/analysis/final-colors-2026-10-30/source-scope.json','reference/analysis/final-colors-2026-10-30/native-images.json','tools/audit_final_color_images.py','reference/analysis/final-colors-2026-10-30/host.json','reference/analysis/final-colors-2026-10-30/tour-v3-comparison.json','tools/verify_final_color_scope.py','docs/FINAL_COLOR_OPTIMIZATION.md']
        proofs += ['docs/parity/evidence/RENDER-COHERENCE-0001.json','reference/validation/render-coherence.json','tools/verify_render_coherence.py','tools/audit_native_animation_frame.py','docs/RENDER_COHERENCE.md']
        proofs += ['tools/audit_contact_kernel_images.py','reference/analysis/render-coherence-2026-10-29/contact-kernel-images.json']
        proofs += ['reference/analysis/optimization-2026-10-27/color-observer-r01/'+name for name in ['identity.json','native.txt','native.json']]
        proofs += ['reference/validation/source-object-host.json','reference/validation/source-score-host.json','docs/NATIVE_ENGINE_OPTIMIZATION.md','docs/CONTACT_KERNEL_OPTIMIZATION.md','docs/PACKED_MASK_OPTIMIZATION.md']
        proofs += ['reference/validation/source-contact-host.json','docs/CONTACT_OPTIMIZATION.md','docs/VIC_NATIVE_OPTIMIZATION.md']
        proofs += ['reference/validation/source-visibility-native.json','reference/validation/source-visibility-host.json','reference/analysis/yamo-r02-2026-10-27/snapshot.json','reference/analysis/yamo-r02-2026-10-27/source-memory.bin','tools/inspect_source_snapshot.py','docs/YAMO_VISIBILITY_PERFORMANCE.md','docs/CONTACT_REGISTERS_OPTIMIZATION.md']
        proofs += ['docs/VIC_REPEAT_OPTIMIZATION.md','reference/analysis/vic-repeat-2026-10-28/baseline/manifest.json','reference/analysis/vic-repeat-2026-10-28/native-kernel-bytes.json','reference/analysis/vic-repeat-2026-10-28/source-register-seams.json']
        proofs += ['reference/validation/source-paint-host.json','reference/validation/source-trap-native.json',
            'docs/CONTACT_PREPARATION_OPTIMIZATION.md','docs/TRAP_R06_2026-10-28.md',
            'reference/analysis/trap-r06-2026-10-28/room-loop-controls.json',
            'reference/analysis/trap-r06-2026-10-28/trap-pixels.json',
            'reference/analysis/trap-r06-2026-10-28/requeue-before.json',
            'reference/analysis/trap-r06-2026-10-28/kage-r01-exit-gate.json']
        proofs += ['docs/parity/evidence/SPRITE-COPY-0001.json','reference/validation/source-sprite-copy-host.json','docs/SPRITE_COPY_OPTIMIZATION.md','tools/audit_sprite_native_kernel.py','tools/verify_source_sprite_copy.py','tools/verify_amiga_entry.py','amiga/sprite_copy.s','reference/analysis/sprite-copy-2026-10-29/source-contract.json','reference/analysis/sprite-copy-2026-10-29/source-copy-disassembly.txt','reference/analysis/sprite-copy-2026-10-29/native-kernel-bytes.json']
        normal=[artifact('amiga/out/bruce_amiga.'+suffix) for suffix in ('exe','elf','adf')]
        report=dict(date='2026-10-30',status='scoped_complete_source_chain_implemented_acceptance_open',source_sha256=source,
            edition_verified=False,natural_playthrough=False,raster_exact=False,full_original_parity=False,
            source_controls=3034,integrated_scenarios=5,source_instructions=world['instructions'],native_controls=53,
            native_replay_loops=int(native['run']['frames']),largest_chip_block=int(native['run']['chip_largest_loaded']),
            realtime_gate_passed=native['realtime_contract_passed'],artifacts=[artifact(x) for x in proofs],normal_build=normal,
            open_gates=['Verified untouched1984 edition','PAL real-time budget across all rooms','Natural VIC/IRQ phase and reader distribution','Complete natural playthrough and next round','Physical A500 and final distribution'])
        (ROOT/path).write_text(json.dumps(report,indent=2)+'\n')
        evidence=dict(id='ACTOR-CHAIN-0001',date='2026-10-30',status=report['status'],source_sha256=source,
            primary_edition_verified=False,natural_playthrough=False,full_original_parity=False,
            source_ranges=['$0743-$1100','$15A8-$1981','$1BC2-$33CA','$40BC','$5212-$56FF'],
            condition='Complete source main/actor/contact/object/combat/lifetime/score chain in shared RAM; explicit CIA/VIC/field-wait seams',
            controls=dict(source=3034,integrated=5,native=53),artifacts=[artifact(path),artifact('docs/MILESTONE_COMPLETION.md')],
            limitations=report['open_gates'])
        (ROOT/'docs/parity/evidence/ACTOR-CHAIN-0001.json').write_text(json.dumps(evidence,indent=2)+'\n')
    else:
        report=read(path);identities(report['artifacts']+report['normal_build']);assert report['source_sha256']==source
    print('PASS source-world delivery; original-parity and real-time acceptance remain open' if not native['realtime_contract_passed'] else 'PASS scoped source-world delivery')
if __name__=='__main__':main()
