"""Bind this bounded stab repair to current host and native evidence."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/ninja-wall-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale ninja evidence: {x['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def checks():
    r=read('reference/analysis/ninja-wall-2026-10-26/report.json');identities(r['source_files'])
    assert r['native_wall_cases']==56 and r['native_hit_cases']==96
    assert r['occupancy_checks']==2450 and r['source_combat_checks']==1080
    assert len(r['aggregate_controls'])==20 and not r['full_combat_parity']
    n=read('reference/validation/a500-c64-combat-diagnostic.json');identities(n['source_files'])
    assert n['executable_sha256']==artifact('amiga/out/bruce_test.exe')['sha256']
    assert n['adf_sha256']==artifact('amiga/out/bruce_test.adf')['sha256']
    assert len(n['runs'])==2 and n['collection_only'] and n['c64_parity']=='not_certified'
    for run in n['runs']:
        assert run['frames']=='6000' and run['restored_os']=='1' and run['combat_mode']=='1'
        for key in ['session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure',
            'movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure',
            'sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors',
            'c64_room_fault','c64_render_mismatches','canvas_residue_bytes','source_audio_faults']:
            assert run[key]=='0',key
        assert int(run['chip_largest_loaded'])>=49152
    identities(read('reference/validation/c64-core.json')['source_files'])
    return r,n
def record():
    r,n=checks()
    paths=['core/game.c','core/game.h','core/combat.c','core/combat.h','core/source_wall.c','core/source_wall.h',
        'core/c64_rooms.c','core/c64_rooms.h','core/c64_hit_data.h','tools/build_c64_hit_masks.py',
        'tools/audit_ninja_wall.py','tools/verify_ninja_wall_delivery.py','tools/verify_c64_candidate.py',
        'tests/ninja_wall_fixture.h','tests/ninja_wall_bridge.c','tests/session_fixture.h',
        'test-ninja-wall.ps1','test-amiga.ps1','amiga-build.ps1','test-parity.ps1',
        'reference/analysis/ninja-wall-2026-10-26/report.json','reference/analysis/ninja-wall-2026-10-26/masks.json',
        'reference/validation/a500-c64-combat-diagnostic.json','reference/validation/c64-core.json',
        'reference/analysis/ai-audit-2026-10-25/report.json','docs/NINJA_WALL.md']
    out=dict(date='2026-10-26',status='verified_scoped_ninja_stab_wall_and_sprite_contact_repair',
        source_files=[artifact(p) for p in paths],normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        native_validation_complete=True,natural_playthrough=False,edition_verified=False,full_combat_parity=False,
        full_m4_complete=False,realtime_gate_passed=n['realtime_contract_passed'],
        native_fixture_cases=r['native_wall_cases']+r['native_hit_cases'],
        limits=r['limits']+['Punch/kick/fall geometry, collect-all/apply-all combat and complete pose/FSM remain open',
            'Current combat replay is controlled; user wall incident still needs a natural retest'])
    save(REPORT,out)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=out['date'],status=out['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    checks();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    assert r['native_fixture_cases']==152 and not r['full_combat_parity'] and not r['natural_playthrough']
    print('VERIFIED Ninja state22 wall/history and sprite contact;152 native controls per run; full combat/cadence remain open')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    record() if a.record else verify()
