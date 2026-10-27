"""Current moving-net delivery, with source identities and bounded native evidence."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/moving-net-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for item in items:assert artifact(item['path'])['sha256']==item['sha256'],f"Stale moving-net evidence: {item['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n')
def host():
    h=read('reference/analysis/moving-net-2026-10-25/report.json');identities(h['source_files'])
    assert h['status']=='passed_controlled_source_checks' and h['dispatch_cases']==12800
    assert not h['natural_playthrough'] and not h['edition_verified']
    assert sum(len(t['steps']) for t in h['room5_routes'])==310
    paths=['reference/analysis/session-walls-2026-10-25/report.json',
        'reference/analysis/climb-audit-2026-10-25/report.json',
        'reference/analysis/movement-audit-2026-10-25/wall-report.json',
        'reference/validation/c64-core.json','reference/validation/c64-room-runtime.json',
        'reference/validation/c64-sprites-host.json','reference/validation/source-audio-host.json',
        'reference/validation/source-dma-host.json']
    for p in paths:identities(read(p)['source_files'])
    return h,paths
def record():
    h,checks=host()
    paths=list(dict.fromkeys([x['path'] for x in h['source_files']]+checks+[
        'reference/analysis/moving-net-2026-10-25/report.json',
        'reference/analysis/moving-net-2026-10-25/source-disassembly.txt',
        'amiga/main.c','amiga-build.ps1','amiga-run.ps1','test-amiga.ps1','test-parity.ps1',
        'tools/verify_moving_net_delivery.py','tools/verify_c64_candidate.py','docs/MOVING_NET.md']))
    r=dict(date='2026-10-25',status='source_checked_moving_net_native_pending',
        source_sha256=h['source_sha256'],edition_verified=False,natural_playthrough=False,
        full_c64_game_parity=False,native_validation_complete=False,realtime_gate_passed=False,
        source_files=[artifact(p) for p in paths],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        controls=dict(dispatch=12800,room5_steps=310,native_fixture_cases=h['native_fixture']['cases']),
        limits=['Controlled source/Amiga fixtures are not natural playthrough',
            'Full actor/combat/AI/contact parity remains open',
            'Candidate edition is not verified as pristine1984 release'])
    raw=read('reference/validation/source-audio-raw.json')
    try:
        identities(raw['source_files']);assert raw['executable_sha256']==r['native_build'][0]['sha256']
        assert raw['test_frames']==6000 and len(raw['runs'])==2
        for run in raw['runs']:
            assert run['frames']=='6000' and run['moving_net_fixture_failure']=='0'
            assert int(run['moving_net_fixture_cases'])==h['native_fixture']['cases']
            for key in ('session_fixture_failure','session_wall_fixture_failure','climb_fixture_failure',
                'movement_fixture_failure','npc_recoil_fixture_failure','source_dma_faults',
                'source_dma_fixture_failure','capture_fault','runtime_arithmetic_errors'):
                assert run[key]=='0',key
            assert int(run['chip_largest_loaded'])>=49152
        r['native_validation_complete']=True;r['native_capture']=artifact('reference/validation/source-audio-raw.json')
        r['native_runs']=raw['runs'];r['status']='verified_scoped_moving_net_controls_on_A500'
        r['realtime_gate_passed']=all(int(x['max_gap_excluding_framebuffer_capture'])==1 for x in raw['runs'])
    except (AssertionError,KeyError) as e:r['native_pending_reason']=str(e)
    save(REPORT,r)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=r['date'],status=r['status'],artifact=artifact(REPORT),
            native_validation_complete=r['native_validation_complete'],actor_logic_fully_ported=False,
            full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,natural_playthrough_verified=False,
            primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    host();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    assert not r['full_c64_game_parity'] and not r['natural_playthrough'] and not r['edition_verified']
    if r['native_validation_complete']:
        identities([r['native_capture']]);raw=read(r['native_capture']['path']);identities(raw['source_files'])
        assert raw['executable_sha256']==r['native_build'][0]['sha256'] and r['native_runs']==raw['runs']
    print(f"VERIFIED moving net:12800 source cases/310 R05 steps; native6000x2={r['native_validation_complete']}; strict cadence={r['realtime_gate_passed']}")
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    record() if a.record else verify()
