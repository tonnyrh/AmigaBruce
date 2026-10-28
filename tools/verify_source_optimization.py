"""Bind historical pilots and the measured 68000 VIC round to builds."""
import argparse,hashlib,json
from pathlib import Path
from verify_source_world_delivery import verify
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/optimization-2026-10-27'
HELPER_STAGES=['contact-helper-before-fixed-timing', 'contact-helper-before-fixed-profile', 'contact-helper-o2-fixed-timing', 'contact-helper-o2-fixed-profile', 'contact-helper-registers-fixed-timing', 'contact-helper-registers-fixed-profile', 'contact-vic-geometry-fixed-timing', 'contact-rows8-native-fixed-timing', 'contact-rows8-native-fixed-profile', 'contact-class-groups-fixed-timing', 'contact-class-groups-fixed-profile']
ALIGN_STAGES=['align4-even-clear-fixed-timing','align4-even-clear-fixed-profile']
FINAL_ALIGN_STAGES=['align4-compact-controls-final-timing','align4-compact-controls-final-profile']
PREPARE_STAGES=['contact-prepare-native-fixed-timing','contact-rest-body-native-timing','contact-rest-final2-timing','contact-rest-final2-profile','contact-rest-requeue-final-timing','contact-rest-requeue-final-profile']
VIC_REPEAT_STAGES=['vic-repeat-native-fixed-timing','vic-repeat-native-final-timing','vic-repeat-native-memory-final-timing','vic-repeat-native-memory-final-profile','vic-repeat-delivery-final-timing','vic-repeat-delivery-final-profile','vic-repeat-scoped-final-timing','vic-repeat-scoped-final-profile']

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def item(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def check(entry,path=None):assert item(path or entry['path'])['sha256']==entry['sha256'],path or entry['path']
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    verify()
    baseline=read(FOLDER+'/baseline/manifest.json')
    for entry in baseline['files']:check(entry,FOLDER+'/baseline/'+entry['path'])
    reports={};identities={};paths=[FOLDER+'/baseline/manifest.json']
    for label in ['before-profile','before-timing','after-profile','after-timing',
                  'contact-before-profile','contact-before-timing','contact-after-profile','contact-after-timing','present-after-timing',
                  'contact-breakdown-profile','vic-final-timing','visibility-final-all-timing','visibility-final-none-timing','rows-before-profile','rows-after-profile','rows-local-o2-timing',
                  'native-driver-object-final-timing','native-score-final-timing','native-score-final-profile',
                  'native-object-pass-final-timing','native-object-pass-final-profile','native-object-pass-equal-steps-timing']+HELPER_STAGES+ALIGN_STAGES+FINAL_ALIGN_STAGES+PREPARE_STAGES+VIC_REPEAT_STAGES:
        folder=FOLDER+'/'+label;ident=read(folder+'/identity.json');identities[label]=ident
        for binary in ident['build']:check(binary,folder+'/'+Path(binary['path']).name)
        for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors']:assert ident['run'][key]=='0'
        if label in ('contact-breakdown-profile','vic-final-timing'):assert ident['run']['vic_compare_errors']=='0'
        expected_frames='370' if label=='native-object-pass-equal-steps-timing' else '360'
        expected_steps='350' if label=='native-object-pass-final-timing' else '360'
        if label in HELPER_STAGES+ALIGN_STAGES+FINAL_ALIGN_STAGES+PREPARE_STAGES+VIC_REPEAT_STAGES:
            assert ident['source_steps_target']==360 and ident['outer_loop_limit']==1200
            assert ident['run']['source_perf_steps']=='360' and ident['run']['source_world_steps']=='360'
            assert 0<int(ident['run']['frames'])<1200 and ident['run']['vic_compare_errors']=='0'
            assert int(ident['run']['drawn_image_fields'])+int(ident['run']['held_image_fields'])==int(ident['run']['frames'])
            assert int(ident['run']['max_held_image_streak'])<=3 and int(ident['run']['chip_largest_loaded'])>=49152
            cases=454 if label in ALIGN_STAGES+FINAL_ALIGN_STAGES else 198 if label.startswith('contact-class-groups-') else 128 if label.startswith('contact-rows8-') else 0
            if label in PREPARE_STAGES:cases=454 if ident['profile'] else 934 if label=='contact-prepare-native-fixed-timing' else 1046
            if label in VIC_REPEAT_STAGES:
                cases=454 if ident['profile'] else 1046
                assert ident['run']['vic_repeat_cases']==('0' if ident['profile'] else '1536')
            if cases:assert ident['run']['contact_kernel_cases']==str(cases) and ident['run']['contact_kernel_errors']=='0'
        else:
            assert ident['run']['frames']==expected_frames and ident['run']['source_world_steps']==expected_steps
        if label=='native-object-pass-final-timing':
            rejected=folder+'/rejected-comparison.json';paths.append(rejected)
            assert read(rejected)['status']=='excluded_unequal_source_step_comparison'
        assert ident['run']['source_perf_test']=='1' and not ident['controlled']
        if ident['profile']:assert ident['run']['perf_errors']=='0'
        reports[label]=read(folder+'/native.json')
        paths += [folder+'/'+name for name in ['identity.json','native.txt','native.json']]
    before={x['path']:x['sha256'] for x in identities['before-timing']['source_files']}
    after={x['path']:x['sha256'] for x in identities['after-timing']['source_files']}
    assert before.keys()==after.keys()
    assert [k for k in before if before[k]!=after[k]]==['core/c64_rooms.c']
    snapshot=FOLDER+'/contact-baseline'
    for entry in read(snapshot+'/manifest.json')['files']:check(entry,snapshot+'/'+entry['path'])
    assert item(snapshot+'/core/c64_rooms.c')['sha256']==after['core/c64_rooms.c']
    paths.append(snapshot+'/manifest.json')
    for label in ['before-profile','before-timing']:
        path=FOLDER+'/'+label+'/c64_rooms.c'
        expected=next(x for x in identities[label]['source_files'] if x['path']=='core/c64_rooms.c')
        check(expected,path);paths.append(path)
    old=int(identities['before-timing']['run']['source_clock_elapsed'])
    new=int(identities['after-timing']['run']['source_clock_elapsed']);assert new<old
    old_vic=next(x for x in reports['before-profile']['profile'] if x['name']=='vic')
    new_vic=next(x for x in reports['after-profile']['profile'] if x['name']=='vic')
    cb={x['path']:x['sha256'] for x in identities['contact-before-timing']['source_files']}
    ca={x['path']:x['sha256'] for x in identities['contact-after-timing']['source_files']}
    pa={x['path']:x['sha256'] for x in identities['present-after-timing']['source_files']}
    assert cb.keys()==ca.keys()==pa.keys()
    assert sorted(k for k in cb if cb[k]!=ca[k])==['core/c64_actor_programs.h','core/c64_rooms.c']
    assert sorted(k for k in ca if ca[k]!=pa[k])==['amiga/main.c','core/scene_copy.h']
    for name in ['core/scene_copy.h']:
        assert item(name)['sha256']==pa[name],name
    for name in ['core/c64_rooms.c','core/c64_actor_programs.h']:assert item(snapshot+'/'+name)['sha256']==cb[name]
    contact_old=int(identities['contact-before-timing']['run']['source_clock_elapsed'])
    contact_new=int(identities['contact-after-timing']['run']['source_clock_elapsed']);assert contact_new<contact_old
    visible=identities['present-after-timing']['run']
    assert visible['drawn_image_fields']=='360' and visible['held_changed']=='0' and visible['presentation_hold_fields']=='3'
    old_align=next(x for x in reports['contact-before-profile']['profile'] if x['name']=='align')
    new_align=next(x for x in reports['contact-after-profile']['profile'] if x['name']=='align')
    final=identities['vic-final-timing'];fr=final['run']
    assert fr['drawn_image_fields']=='360' and fr['held_changed']=='0'
    assert fr['presentation_hold_fields']=='3' and fr['vic_compare_errors']=='0'
    assert int(fr['source_clock_elapsed'])<int(visible['source_clock_elapsed'])
    assert int(fr['source_clock_missed'])<int(visible['source_clock_missed'])
    assert reports['contact-breakdown-profile']['profile']
    latest=identities['visibility-final-all-timing'];lr=latest['run'];solo=identities['visibility-final-none-timing']
    assert latest['enemy_mask']==3 and solo['enemy_mask']==0
    assert lr['perf_enemy_mask']=='3' and solo['run']['perf_enemy_mask']=='0'
    assert lr['vic_compare_errors']=='0' and lr['drawn_image_fields']=='360'
    assert int(lr['source_clock_elapsed'])<int(fr['source_clock_elapsed'])
    assert latest['source_files']==solo['source_files']
    rows=identities['rows-local-o2-timing'];rr=rows['run']
    # Rows are a historical stage; current source identity is bound below to
    # the final native pass, while its measured binaries remain hash checked.
    assert rr['vic_compare_errors']=='0' and rr['drawn_image_fields']=='360'
    assert int(rr['source_clock_elapsed'])<int(lr['source_clock_elapsed'])
    assert int(rr['source_clock_missed'])<int(lr['source_clock_missed'])
    rb=next(x for x in reports['rows-before-profile']['profile'] if x['name']=='rows')
    ra=next(x for x in reports['rows-after-profile']['profile'] if x['name']=='rows')
    assert ra['average_exclusive']<rb['average_exclusive']
    for label in ('rows-before-profile','rows-after-profile'):
        assert all(row['calls']==0 for row in reports[label]['profile'] if row['name'].startswith('contact_'))
    native=identities['native-object-pass-equal-steps-timing'];nr=native['run']
    driver=identities['native-driver-object-final-timing']['run']
    score=identities['native-score-final-timing']['run']
    # Historical native-engine source is superseded by the fixed-step kernel stage below.
    assert native['source_files']==identities['native-object-pass-final-profile']['source_files']
    assert int(driver['source_clock_elapsed'])<int(rr['source_clock_elapsed'])
    assert int(score['source_clock_elapsed'])<int(driver['source_clock_elapsed'])
    assert int(nr['source_clock_elapsed'])<int(score['source_clock_elapsed'])
    assert int(nr['source_clock_missed'])<int(score['source_clock_missed'])<int(rr['source_clock_missed'])
    for run in (driver,score,nr):
        assert run['presentation_hold_fields']=='3' and run['vic_compare_errors']=='0'
        assert int(run['drawn_image_fields'])+int(run['held_image_fields'])==int(run['frames'])
        assert int(run['max_held_image_streak'])<=3 and int(run['chip_largest_loaded'])>=49152
    nb={x['name']:x for x in reports['rows-after-profile']['profile']}
    na={x['name']:x for x in reports['native-object-pass-final-profile']['profile']}
    assert na['game']['average_exclusive']<nb['game']['average_exclusive']
    assert na['objects']['average_exclusive']<nb['objects']['average_exclusive']
    helper=identities['contact-class-groups-fixed-timing'];hr=helper['run']
    helper_before=identities['contact-helper-before-fixed-timing'];hbr=helper_before['run']
    packed=identities['align4-compact-controls-final-timing'];pr=packed['run']
    assert packed['source_files']==identities['align4-compact-controls-final-profile']['source_files']
    assert int(pr['source_clock_elapsed'])<int(hr['source_clock_elapsed'])
    pp={x['name']:x for x in reports['align4-compact-controls-final-profile']['profile']}
    assert pp['align']['average_exclusive']<next(x for x in reports['contact-class-groups-fixed-profile']['profile'] if x['name']=='align')['average_exclusive']
    assert helper['source_files']==identities['contact-class-groups-fixed-profile']['source_files']
    assert int(hr['source_clock_elapsed'])<int(hbr['source_clock_elapsed'])
    def stage_sources(label):return {x['path']:x['sha256'] for x in identities[label]['source_files']}
    hs0=stage_sources('contact-helper-before-fixed-timing');hs1=stage_sources('contact-helper-o2-fixed-timing')
    assert hs0.keys()==hs1.keys() and [k for k in hs0 if hs0[k]!=hs1[k]]==['core/c64_rooms.c']
    hp0={x['name']:x for x in reports['contact-helper-before-fixed-profile']['profile']}
    hp1={x['name']:x for x in reports['contact-class-groups-fixed-profile']['profile']}
    assert hp1['rows']['average_exclusive']<hp0['rows']['average_exclusive']
    assert hp1['vic']['average_exclusive']<hp0['vic']['average_exclusive']
    assert hp1['contact']['average_exclusive']<hp0['contact']['average_exclusive']
    prepared=identities['contact-rest-requeue-final-timing'];cr=prepared['run']
    assert prepared['source_files']==identities['contact-rest-requeue-final-profile']['source_files']
    assert int(cr['source_clock_elapsed'])<int(pr['source_clock_elapsed'])
    cp={x['name']:x for x in reports['contact-rest-requeue-final-profile']['profile']}
    assert cp['contact']['average_exclusive']<pp['contact']['average_exclusive']
    for label in ('contact-prepare-driver-clear-fixed-timing','contact-rest-body-native-profile'):
        paths.append(FOLDER+'/'+label+'/rejected.json')
    repeated=identities['vic-repeat-scoped-final-timing'];vr=repeated['run']
    assert repeated['source_files']==identities['vic-repeat-scoped-final-profile']['source_files']
    for source_file in repeated['source_files']:check(source_file)
    assert int(vr['source_clock_elapsed'])<int(cr['source_clock_elapsed'])
    vp={x['name']:x for x in reports['vic-repeat-scoped-final-profile']['profile']}
    assert vp['vic']['average_exclusive']<cp['vic']['average_exclusive']
    assert vp['vic']['calls']>360
    vb='reference/analysis/vic-repeat-2026-10-28/baseline'
    for entry in read(vb+'/manifest.json')['files']:check(entry,vb+'/'+entry['path'])
    paths += ['tools/audit_vic_native_kernels.py','reference/analysis/vic-repeat-2026-10-28/native-kernel-bytes.json','reference/analysis/vic-repeat-2026-10-28/full-diagnostic-placement.json','reference/analysis/vic-repeat-2026-10-28/source-register-seams.json',vb+'/manifest.json',FOLDER+'/vic-repeat-pilot-timing/rejected.json',FOLDER+'/vic-repeat-native-final-profile/rejected.json',FOLDER+'/vic-repeat-native-final-profile/allocation-failure.txt','docs/VIC_REPEAT_OPTIMIZATION.md']
    snapshot=FOLDER+'/rows-baseline'
    for entry in read(snapshot+'/manifest.json')['files']:check(entry,snapshot+'/'+entry['path'])
    paths.append(snapshot+'/manifest.json')
    paths += ['docs/AMIGA_OPTIMIZATION_REPORT.md','docs/AMIGA_OPTIMIZATION_PLAN.md',
        'reference/validation/source-world-delivery.json','reference/validation/source-world-native.json',
        'reference/validation/source-vic-host.json','reference/validation/source-contact-host.json',
        'docs/CONTACT_OPTIMIZATION.md','docs/VIC_NATIVE_OPTIMIZATION.md',
        'docs/NATIVE_ENGINE_OPTIMIZATION.md','docs/CONTACT_KERNEL_OPTIMIZATION.md','docs/PACKED_MASK_OPTIMIZATION.md','amiga/contact_align.s','tools/build_contact_class_kernel.py','reference/validation/source-object-host.json','reference/validation/source-score-host.json',
        'core/source_perf.h','amiga/vic_compare.s','docs/YAMO_VISIBILITY_PERFORMANCE.md','docs/CONTACT_REGISTERS_OPTIMIZATION.md',
        'reference/validation/source-visibility-host.json',
        FOLDER+'/actor-o2-candidate-timing/rejected.json',FOLDER+'/align4-native-fixed-timing/rejected.json',
        FOLDER+'/packed-allocation-probe/probe.json',FOLDER+'/packed-allocation-probe/autotest-1.txt',
        FOLDER+'/packed-allocation-probe/diagnostic.json',FOLDER+'/packed-fixture-layout.json',FOLDER+'/align4-native-allocation-rejected/rejected.json',
        FOLDER+'/align4-native-allocation-rejected/probe.json',FOLDER+'/align4-native-allocation-rejected/memory-diagnostic.json',
        FOLDER+'/align4-native-allocation-rejected/source-world-native.json',FOLDER+'/align4-native-allocation-rejected/native-final.txt',
        'tools/verify_source_optimization.py','tools/summarize_source_performance.py','test-source-performance.ps1']
    paths += ['amiga/contact_prepare.s','docs/CONTACT_PREPARATION_OPTIMIZATION.md','docs/TRAP_R06_2026-10-28.md',
        'reference/validation/source-paint-host.json','reference/validation/source-trap-native.json',
        'tools/verify_source_paint.py','tools/audit_native_trap_pause.py','test-source-paint.ps1','tests/source_paint_bridge.c']
    path='reference/validation/source-optimization.json'
    if a.record:
        report=dict(date='2026-10-28',status='measured_vic_repeat_realtime_open',
            method='Separate native actual-PAL source-contact/VIC/presentation pilots; idle-input invincible room1, historical pairs preserved',
            first_pilot=dict(old_active_fields=old,new_active_fields=new,active_time_reduction_percent=round((old-new)*100/old,3),
                old_vic_mean_lines=old_vic['average_exclusive'],new_vic_mean_lines=new_vic['average_exclusive']),
            contact_pilot=dict(old_active_fields=contact_old,new_active_fields=contact_new,
                active_time_reduction_percent=round((contact_old-contact_new)*100/contact_old,3),
                old_align_mean_lines=old_align['average_exclusive'],new_align_mean_lines=new_align['average_exclusive']),
            presentation=dict(old_drawn_images=2,new_drawn_images=int(visible['drawn_image_fields']),active_fields=int(visible['source_clock_elapsed']),
                decision_deadline_fields=3,hard_realtime_deadline_met=False),
            m68k_vic_round=dict(old_active_fields=int(visible['source_clock_elapsed']),new_active_fields=int(fr['source_clock_elapsed']),
                active_time_reduction_percent=round((int(visible['source_clock_elapsed'])-int(fr['source_clock_elapsed']))*100/int(visible['source_clock_elapsed']),3),
                old_audio_missed=int(visible['source_clock_missed']),new_audio_missed=int(fr['source_clock_missed']),
                drawn_images=int(fr['drawn_image_fields']),vic_compare_errors=int(fr['vic_compare_errors'])),
            visibility_contact_round=dict(old_active_fields=int(fr['source_clock_elapsed']),new_active_fields=int(lr['source_clock_elapsed']),
                solo_active_fields=int(solo['run']['source_clock_elapsed']),drawn_images=int(lr['drawn_image_fields']),
                old_audio_missed=int(fr['source_clock_missed']),new_audio_missed=int(lr['source_clock_missed'])),
            local_contact_registers=dict(old_active_fields=int(lr['source_clock_elapsed']),new_active_fields=int(rr['source_clock_elapsed']),
                old_row_mean_lines=rb['average_exclusive'],new_row_mean_lines=ra['average_exclusive'],
                old_audio_missed=int(lr['source_clock_missed']),new_audio_missed=int(rr['source_clock_missed'])),
            native_engine_round=dict(checkpoint='26fb6d1724640d53fd84160fa55b65dafd1c7f38',
                old_active_fields=int(rr['source_clock_elapsed']),new_active_fields=int(nr['source_clock_elapsed']),
                measured_elapsed_reduction_percent=round((int(rr['source_clock_elapsed'])-int(nr['source_clock_elapsed']))*100/int(rr['source_clock_elapsed']),3),
                old_outer_loops=int(rr['frames']),new_outer_loops=int(nr['frames']),source_steps=360,
                old_audio_missed=int(rr['source_clock_missed']),new_audio_missed=int(nr['source_clock_missed']),
                drawn_images=int(nr['drawn_image_fields']),held_images=int(nr['held_image_fields']),
                old_game_mean_lines=nb['game']['average_exclusive'],new_game_mean_lines=na['game']['average_exclusive'],
                old_objects_mean_lines=nb['objects']['average_exclusive'],new_objects_mean_lines=na['objects']['average_exclusive']),
            contact_kernel_round=dict(checkpoint='3b90e04',source_steps=360,
                before_outer_loops=int(hbr['frames']),after_outer_loops=int(hr['frames']),
                old_active_fields=int(hbr['source_clock_elapsed']),new_active_fields=int(hr['source_clock_elapsed']),
                measured_elapsed_reduction_percent=round((int(hbr['source_clock_elapsed'])-int(hr['source_clock_elapsed']))*100/int(hbr['source_clock_elapsed']),3),
                before_drawn_images=int(hbr['drawn_image_fields']),after_drawn_images=int(hr['drawn_image_fields']),
                old_audio_missed=int(hbr['source_clock_missed']),new_audio_missed=int(hr['source_clock_missed']),
                old_contact_mean=hp0['contact']['average_exclusive'],new_contact_mean=hp1['contact']['average_exclusive'],
                old_row_mean=hp0['rows']['average_exclusive'],new_row_mean=hp1['rows']['average_exclusive'],
                old_vic_mean=hp0['vic']['average_exclusive'],new_vic_mean=hp1['vic']['average_exclusive'],native_kernel_cases=198),
            packed_mask_round=dict(checkpoint='c77404b',source_steps=360,
                old_active_fields=int(hr['source_clock_elapsed']),new_active_fields=int(pr['source_clock_elapsed']),
                measured_elapsed_reduction_percent=round((int(hr['source_clock_elapsed'])-int(pr['source_clock_elapsed']))*100/int(hr['source_clock_elapsed']),3),
                old_audio_missed=int(hr['source_clock_missed']),new_audio_missed=int(pr['source_clock_missed']),
                old_align_mean=next(x for x in reports['contact-class-groups-fixed-profile']['profile'] if x['name']=='align')['average_exclusive'],
                new_align_mean=pp['align']['average_exclusive'],native_kernel_cases=454),
            contact_preparation_round=dict(checkpoint='b003d04',source_steps=360,
                old_active_fields=int(pr['source_clock_elapsed']),new_active_fields=int(cr['source_clock_elapsed']),
                measured_elapsed_reduction_percent=round((int(pr['source_clock_elapsed'])-int(cr['source_clock_elapsed']))*100/int(pr['source_clock_elapsed']),3),
                old_audio_missed=int(pr['source_clock_missed']),new_audio_missed=int(cr['source_clock_missed']),
                old_contact_mean=pp['contact']['average_exclusive'],new_contact_mean=cp['contact']['average_exclusive'],
                native_kernel_cases=1046,full_native_kernel_cases=454,trap_requeue_fixed=True),
            vic_repeat_round=dict(checkpoint='cb7224a',source_steps=360,
                old_active_fields=int(cr['source_clock_elapsed']),new_active_fields=int(vr['source_clock_elapsed']),
                measured_elapsed_reduction_percent=round((int(cr['source_clock_elapsed'])-int(vr['source_clock_elapsed']))*100/int(cr['source_clock_elapsed']),3),
                old_audio_missed=int(cr['source_clock_missed']),new_audio_missed=int(vr['source_clock_missed']),
                old_vic_mean=cp['vic']['average_exclusive'],new_vic_mean=vp['vic']['average_exclusive'],native_repeat_cases=1536,separate_reference_build=True,full_native_repeat_cases=0),
            edition_verified=False,natural_playthrough=False,all_rooms_profiled=False,realtime_accepted=False,
            artifacts=[item(x) for x in paths],
            limits=['Single benchmark pair; source-field/input phases differ as actual execution time changes',
                'Rendering more images costs time; sound gaps, scene residue and hard real-time acceptance remain open',
                'No original-raster or physical-A500 acceptance'])
        (ROOT/path).write_text(json.dumps(report,indent=2)+'\n')
    else:
        report=read(path)
        for entry in report['artifacts']:check(entry)
        assert report['contact_pilot']['new_active_fields']==contact_new and not report['realtime_accepted']
        assert report['m68k_vic_round']['new_active_fields']==int(fr['source_clock_elapsed'])
        assert report['visibility_contact_round']['new_active_fields']==int(lr['source_clock_elapsed'])
        assert report['local_contact_registers']['new_active_fields']==int(rr['source_clock_elapsed'])
        assert report['native_engine_round']['new_active_fields']==int(nr['source_clock_elapsed'])
        assert report['contact_kernel_round']['new_active_fields']==int(hr['source_clock_elapsed'])
        assert report['packed_mask_round']['new_active_fields']==int(pr['source_clock_elapsed'])
        assert report['contact_preparation_round']['new_active_fields']==int(cr['source_clock_elapsed'])
        assert report['vic_repeat_round']['new_active_fields']==int(vr['source_clock_elapsed'])
    print(f'PASS VIC repeat: {cr["source_clock_elapsed"]}->{vr["source_clock_elapsed"]} measured PAL fields/360 source steps; real-time remains open')
if __name__=='__main__':main()
