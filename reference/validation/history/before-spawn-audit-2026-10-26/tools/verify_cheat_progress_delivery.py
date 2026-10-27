"""Source-record equivalence and actual68000 cheat session controls."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/cheat-progress-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale cheat evidence: {x['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def checks():
    r=read('reference/analysis/cheat-progress-2026-10-26/report.json');identities(r['source_files'])
    assert r['menu_start_cases']==20 and r['executed_source_pickups']==1075 and all(x['matched'] for x in r['rows'])
    assert r['cheat_is_amiga_extension'] and not r['natural_playthrough']
    assert artifact('.reference/c64/work/untrained-memory.bin')['sha256']==r['source_sha256']
    for p in ('reference/validation/c64-core.json','reference/analysis/session-walls-2026-10-25/report.json'):
        identities(read(p)['source_files'])
    n=read('reference/validation/a500-c64-combat-diagnostic.json');identities(n['source_files'])
    assert n['executable_sha256']==artifact('amiga/out/bruce_test.exe')['sha256']
    assert n['adf_sha256']==artifact('amiga/out/bruce_test.adf')['sha256']
    assert n['collection_only'] and len(n['runs'])==1
    for run in n['runs']:
        assert run['frames']=='900' and run['restored_os']=='1' and run['source_reader_page']=='104'
        for key in ('session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure',
            'movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure',
            'sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors',
            'c64_room_fault','c64_render_mismatches','source_audio_faults','capture_fault'):
            assert run[key]=='0',key
        assert int(run['chip_largest_loaded'])>=49152
    return r,n
def record():
    r,n=checks()
    paths=['core/session.c','core/session.h','core/c64_rooms.c','core/c64_rooms.h',
        'tests/cheat_progress_fixture.h','tests/session_fixture.h','tests/session_bridge.c',
        'test-session.ps1','test-core.ps1','test-amiga.ps1','tools/audit_session_walls.py',
        'tools/audit_cheat_progress.py','tools/verify_cheat_progress_delivery.py','tools/verify_c64_candidate.py',
        'docs/CHEAT_PROGRESS.md','reference/analysis/cheat-progress-2026-10-26/report.json',
        'reference/analysis/cheat-progress-2026-10-26/source-disassembly.txt',
        'reference/analysis/session-walls-2026-10-25/report.json','reference/validation/c64-core.json',
        'reference/validation/a500-c64-combat-diagnostic.json']
    out=dict(date='2026-10-26',status='verified_scoped_cheat_progress_preparation',source_files=[artifact(p) for p in paths],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        source_menu_starts=20,source_record_pickups=1075,native_validation_complete=True,native_runs=1,native_loop_iterations=900,
        natural_playthrough=False,edition_verified=False,full_actor_parity=False,full_m4_complete=False,
        realtime_gate_passed=n['realtime_contract_passed'],limits=['Cheat deliberately completes lower numbered rooms; not a C64 start rule',
            'Controlled source instructions and native fixtures, not natural play','Complete actor parity and strict field cadence remain open'])
    save(REPORT,out)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=out['date'],status=out['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    checks();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    print('VERIFIED cheat prefix progress:20 starts,1075 actual6502 pickups and native68000 session controls; ordinary play unchanged')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();record() if a.record else verify()
