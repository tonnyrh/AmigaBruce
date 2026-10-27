"""Bind the measured OP2 pilot to archived A/B builds and current controls."""
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
    for label in ['before-profile','before-timing','after-profile','after-timing']:
        folder=FOLDER+'/'+label;ident=read(folder+'/identity.json');identities[label]=ident
        for binary in ident['build']:check(binary,folder+'/'+Path(binary['path']).name)
        for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors']:assert ident['run'][key]=='0'
        assert ident['run']['frames']=='360' and ident['run']['source_world_steps']=='360'
        assert ident['run']['source_perf_test']=='1' and not ident['controlled']
        if ident['profile']:assert ident['run']['perf_errors']=='0'
        reports[label]=read(folder+'/native.json')
        paths += [folder+'/'+name for name in ['identity.json','native.txt','native.json']]
    before={x['path']:x['sha256'] for x in identities['before-timing']['source_files']}
    after={x['path']:x['sha256'] for x in identities['after-timing']['source_files']}
    assert before.keys()==after.keys()
    assert [k for k in before if before[k]!=after[k]]==['core/c64_rooms.c']
    assert item('core/c64_rooms.c')['sha256']==after['core/c64_rooms.c']
    for label in ['before-profile','before-timing']:
        path=FOLDER+'/'+label+'/c64_rooms.c'
        expected=next(x for x in identities[label]['source_files'] if x['path']=='core/c64_rooms.c')
        check(expected,path);paths.append(path)
    old=int(identities['before-timing']['run']['source_clock_elapsed'])
    new=int(identities['after-timing']['run']['source_clock_elapsed']);assert new<old
    old_vic=next(x for x in reports['before-profile']['profile'] if x['name']=='vic')
    new_vic=next(x for x in reports['after-profile']['profile'] if x['name']=='vic')
    paths += ['docs/AMIGA_OPTIMIZATION_REPORT.md','docs/AMIGA_OPTIMIZATION_PLAN.md',
        'reference/validation/source-world-delivery.json','reference/validation/source-world-native.json',
        'reference/validation/source-vic-host.json','core/source_perf.h',
        'tools/verify_source_optimization.py','tools/summarize_source_performance.py','test-source-performance.ps1']
    path='reference/validation/source-optimization.json'
    if a.record:
        report=dict(date='2026-10-27',status='first_measured_pilot_completed_realtime_open',
            method='One unprofiled actual-PAL A/B pair and separate nested profile pair, idle-input invincible source-world room1',
            old_active_fields=old,new_active_fields=new,active_time_reduction_percent=round((old-new)*100/old,3),
            old_vic_mean_lines=old_vic['average_exclusive'],new_vic_mean_lines=new_vic['average_exclusive'],
            edition_verified=False,natural_playthrough=False,all_rooms_profiled=False,realtime_accepted=False,
            artifacts=[item(x) for x in paths],
            limits=['Single benchmark pair; source-field/input phases differ as actual execution time changes',
                'Held new frames, missing audio ticks and33 unexplained scene bytes remain open',
                'No original-raster or physical-A500 acceptance'])
        (ROOT/path).write_text(json.dumps(report,indent=2)+'\n')
    else:
        report=read(path)
        for entry in report['artifacts']:check(entry)
        assert report['new_active_fields']==new and not report['realtime_accepted']
    print(f'PASS measured pilot: {old}->{new} active PAL fields; real-time acceptance remains open')
if __name__=='__main__':main()
