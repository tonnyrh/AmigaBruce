"""Compare identical native inspection routes; bind renderer work and limits."""
import argparse,hashlib,json
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/room-load-2026-10-25'
REPORT='reference/validation/room-load-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale room-load evidence: {x['path']}"
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def controls(report,reuse):
    identities(report['source_files']);assert report['collection_only'] and report['c64_parity']=='not_certified'
    for r in report['runs']:
        assert r['frames']=='900' and r['room_load_test']=='1' and r['room_reuse']==str(reuse)
        assert r['room_load_events']=='29' and r['visited_rooms_mask']=='1048575'
        for k in ['moving_net_fixture_failure','climb_fixture_failure','movement_fixture_failure',
            'npc_recoil_fixture_failure','session_fixture_failure','session_wall_fixture_failure',
            'contact_fixture_failure','sprite_fixture_failure','source_dma_fixture_failure',
            'source_dma_faults','runtime_arithmetic_errors','c64_room_fault','c64_render_mismatches','canvas_residue_bytes']:
            assert r[k]=='0',k
        assert int(r['chip_largest_loaded'])>=49152 and int(r['c64_render_checks'])>=30
        if reuse:assert int(r['room_reuse_stat_0'])>0 and int(r['room_reuse_stat_2'])>0
    return report['runs']
def comparison(before,after):
    rows=[]
    for run in after:
        base=before[0]
        for i in range(29):assert base[f'room_event_{i}_id']==run[f'room_event_{i}_id']
        old=sum(int(base[f'room_event_{i}_work']) for i in range(29))
        new=sum(int(run[f'room_event_{i}_work']) for i in range(29))
        assert new<old,('No measured room-work improvement',new,old)
        rows.append(dict(baseline_hsync=old,optimized_hsync=new,reduction_percent=round((1-new/old)*100,2),
            baseline_mean_hsync=round(old/29,2),optimized_mean_hsync=round(new/29,2),
            baseline_max_hsync=max(int(base[f'room_event_{i}_work']) for i in range(29)),
            optimized_max_hsync=max(int(run[f'room_event_{i}_work']) for i in range(29)),
            estimated_ms_per_hsync=20/int(run['timing_pal_lines']) if int(run.get('timing_pal_lines',0)) in (312,313) else None))
    return rows
def captures():
    from PIL import Image
    b=Image.open(ROOT/'docs/images/room-load-baseline.png').convert('RGB')
    a=Image.open(ROOT/'docs/images/room-load.png').convert('RGB')
    assert a.size==b.size and a.tobytes()==b.tobytes(),'Native before/after capture differs'
def host():
    from verify_moving_net_delivery import host as previous_controls
    previous_controls()
    r=read(FOLDER+'/host-reuse.json');identities(r['source_files'])
    assert r['status']=='passed_cache_invalidation_and_source_pixel_controls' and len(r['cache_controls'])==23
def record():
    host();b=read('reference/validation/a500-room-load-baseline.json');a=read('reference/validation/a500-room-load.json')
    before=controls(b,0);after=controls(a,1);assert len(before)==1 and len(after)==2
    results=comparison(before,after);captures()
    assert artifact('amiga/out/bruce_test.exe')['sha256']==a['executable_sha256']
    assert artifact(FOLDER+'/baseline/bruce_test.exe')['sha256']==b['executable_sha256']
    paths=['core/c64_rooms.c','core/c64_rooms.h','amiga/main.c','amiga-build.ps1','amiga-run.ps1',
        'test-amiga.ps1','test-parity.ps1','test-room-reuse.ps1','tools/verify_room_reuse.py',
        'tools/verify_room_load_delivery.py','tools/verify_c64_candidate.py','docs/ROOM_LOAD_PERFORMANCE.md',
        'docs/PROJECT_PLAN.md','docs/ACTIVE_TESTS.md',FOLDER+'/host-reuse.json',
        'docs/images/room-load-baseline.png','docs/images/room-load.png',
        'reference/validation/a500-room-load-baseline.json','reference/validation/a500-room-load.json',
        'reference/validation/c64-room-runtime.json','reference/validation/c64-core.json',
        'reference/analysis/moving-net-2026-10-25/report.json']
    r=dict(date=str(date.today()),status='verified_scoped_room_load_work_improvement',
        native_validation_complete=True,natural_playthrough=False,edition_verified=False,full_c64_game_parity=False,
        full_m4_complete=False,realtime_gate_passed=False,inspection_cadence_passed=a['realtime_contract_passed'],comparison=results,
        source_files=[artifact(p) for p in paths],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        baseline_build=[artifact(FOLDER+'/baseline/bruce_test.exe'),artifact(FOLDER+'/baseline/bruce_test.adf')],
        limits=['29 controlled room inspections; not natural transitions or a full playthrough',
            'Work excludes diagnostic pixel checks; presentation copy/blanking and other frame work are additional',
            'No measured C64 load-duration comparison and no certified original edition',
            'Full actor/combat/AI, sound approval and strict whole-game cadence remain open'])
    save(REPORT,r)
    for p in ['reference/validation/c64-candidate.json','reference/validation/visual-candidate.json']:
        save(p,dict(date=r['date'],status=r['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    host();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build']+r['baseline_build'])
    assert not r['natural_playthrough'] and not r['edition_verified'] and not r['full_c64_game_parity'] and not r['full_m4_complete']
    b=read('reference/validation/a500-room-load-baseline.json');a=read('reference/validation/a500-room-load.json')
    assert comparison(controls(b,0),controls(a,1))==r['comparison']
    captures()
    print('VERIFIED room load work; reductions='+str([x['reduction_percent'] for x in r['comparison']])+'%; full M4/cadence remain open')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    record() if a.record else verify()
