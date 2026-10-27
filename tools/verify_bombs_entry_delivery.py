"""Current source-bound entry/bomb repair; controlled evidence only."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/bombs-entry-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale bomb/entry evidence: {x['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def checks():
    r=read('reference/analysis/bombs-entry-2026-10-26/report.json');identities(r['source_files'])
    assert len(r['entry_controls'])==640 and len(r['arm_controls'])==3 and len(r['death_controls'])==3
    assert len(r['npc_hazard_controls'])==42 and len(r['npc_blast_contacts'])==2 and r['native_added_controls']==44
    n=read('reference/validation/a500-c64-combat-diagnostic.json');identities(n['source_files'])
    assert n['executable_sha256']==artifact('amiga/out/bruce_test.exe')['sha256']
    assert n['adf_sha256']==artifact('amiga/out/bruce_test.adf')['sha256']
    assert len(n['runs'])==2 and n['collection_only'] and n['c64_parity']=='not_certified'
    for run in n['runs']:
        assert run['frames']=='6000' and run['restored_os']=='1'
        assert run['source_reader_page']=='104'
        for k in ('session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure',
            'movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure',
            'sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors',
            'c64_room_fault','c64_render_mismatches','canvas_residue_bytes','source_audio_faults'):
            assert run[k]=='0',k
        assert int(run['chip_largest_loaded'])>=49152
    identities(read('reference/validation/c64-core.json')['source_files'])
    return r,n
def record():
    r,n=checks()
    paths=['core/combat.c','core/c64_rooms.c','core/c64_rooms.h','core/rooms.c','core/c64_room_data.h','core/c64_room_programs.h',
        'tools/build_c64_rooms.py','tests/bombs_entry_bridge.c','tests/bombs_entry_fixture.h','tests/session_fixture.h',
        'tools/audit_bombs_entry.py','tools/verify_bombs_entry_delivery.py','tools/verify_c64_candidate.py',
        'test-bombs-entry.ps1','test-amiga.ps1','test-core.ps1','test-parity.ps1','docs/BOMBS_ENTRY.md',
        'reference/analysis/bombs-entry-2026-10-26/report.json','reference/validation/a500-c64-combat-diagnostic.json',
        'reference/validation/c64-core.json','reference/validation/c64-room-runtime.json','reference/analysis/ai-audit-2026-10-25/report.json']
    out=dict(date='2026-10-26',status='verified_scoped_source_enemy_entry_and_bomb_repair',source_files=[artifact(p) for p in paths],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        native_validation_complete=True,natural_playthrough=False,edition_verified=False,full_actor_parity=False,
        full_m4_complete=False,realtime_gate_passed=n['realtime_contract_passed'],limits=r['limits'])
    save(REPORT,out)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=out['date'],status=out['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    checks();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    assert not r['natural_playthrough'] and not r['full_actor_parity']
    print('VERIFIED source enemy entry, NPC bomb activation and Bruce bomb death;44 native controls/run; full gameplay/cadence remain open')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();record() if a.record else verify()
