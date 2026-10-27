"""Bind historical pilots and the measured 68000 VIC round to builds."""
import argparse,hashlib,json
from pathlib import Path
from verify_source_world_delivery import verify
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/optimization-2026-10-27'
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
                  'native-object-pass-final-timing','native-object-pass-final-profile','native-object-pass-equal-steps-timing']:
        folder=FOLDER+'/'+label;ident=read(folder+'/identity.json');identities[label]=ident
        for binary in ident['build']:check(binary,folder+'/'+Path(binary['path']).name)
        for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors']:assert ident['run'][key]=='0'
        if label in ('contact-breakdown-profile','vic-final-timing'):assert ident['run']['vic_compare_errors']=='0'
        expected_frames='370' if label=='native-object-pass-equal-steps-timing' else '360'
        expected_steps='350' if label=='native-object-pass-final-timing' else '360'
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
    for source_file in native['source_files']:check(source_file)
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
    snapshot=FOLDER+'/rows-baseline'
    for entry in read(snapshot+'/manifest.json')['files']:check(entry,snapshot+'/'+entry['path'])
    paths.append(snapshot+'/manifest.json')
    paths += ['docs/AMIGA_OPTIMIZATION_REPORT.md','docs/AMIGA_OPTIMIZATION_PLAN.md',
        'reference/validation/source-world-delivery.json','reference/validation/source-world-native.json',
        'reference/validation/source-vic-host.json','reference/validation/source-contact-host.json',
        'docs/CONTACT_OPTIMIZATION.md','docs/VIC_NATIVE_OPTIMIZATION.md',
        'docs/NATIVE_ENGINE_OPTIMIZATION.md','reference/validation/source-object-host.json','reference/validation/source-score-host.json',
        'core/source_perf.h','amiga/vic_compare.s','docs/YAMO_VISIBILITY_PERFORMANCE.md','docs/CONTACT_REGISTERS_OPTIMIZATION.md',
        'reference/validation/source-visibility-host.json',
        FOLDER+'/actor-o2-candidate-timing/rejected.json',
        'tools/verify_source_optimization.py','tools/summarize_source_performance.py','test-source-performance.ps1']
    path='reference/validation/source-optimization.json'
    if a.record:
        report=dict(date='2026-10-27',status='measured_native_contact_objects_score_realtime_open',
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
    print(f'PASS native motor round: {rr["source_clock_elapsed"]}->{nr["source_clock_elapsed"]} measured PAL fields; real-time remains open')
if __name__=='__main__':main()
