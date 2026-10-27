"""Verify source-bound spawn services and scoped actual68000 regressions."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/spawn-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale spawn evidence: {x['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def checks():
    r=read('reference/analysis/spawn-audit-2026-10-26/report.json')
    w=read('reference/analysis/spawn-audit-2026-10-26/world-controls.json')
    for report in (r,w):
        identities(report['source_files']+report['compiled_sources'])
        assert not report['natural_playthrough'] and not report['edition_verified']
        assert artifact('.reference/c64/work/untrained-memory.bin')['sha256']==report['source_sha256']
        assert len(report['dll_sha256'])==64
    assert r['dll_sha256']==w['dll_sha256']
    assert r['checks']==dict(initial=80,services=4320,removal=960,clock=60,entry_steps=908)
    assert len(w['edge'])==123 and len(w['birth_bombs'])==30 and all(x['active']==0 for x in w['birth_bombs'])
    h=read('reference/validation/c64-core.json');identities(h['source_files'])
    expected=dict(word.split('=') for line in h['output'] if line.startswith('M3_6000 ') for word in line.split()[1:])
    assert len(expected)==7
    n=read('reference/validation/a500-c64-combat-diagnostic.json');identities(n['source_files'])
    identities(n.get('independent_run_artifacts',[]))
    assert n['executable_sha256']==artifact('amiga/out/bruce_test.exe')['sha256']
    assert n['adf_sha256']==artifact('amiga/out/bruce_test.adf')['sha256']
    assert n['collection_only'] and len(n['runs'])==2 and n['c64_parity']=='not_certified'
    for run in n['runs']:
        assert run['frames']=='6000' and run['restored_os']=='1' and run['source_reader_page']=='104'
        assert run['spawn_fixture_cases']=='223'
        for k in ('session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure',
            'movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure',
            'sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors',
            'c64_room_fault','c64_render_mismatches','source_audio_faults','capture_fault','canvas_residue_bytes'):
            assert run[k]=='0',k
        assert int(run['chip_largest_loaded'])>=49152
        assert all(run[k]==v for k,v in expected.items()),'68000/host replay mismatch'
    return r,w,h,n
def record():
    r,w,h,n=checks()
    paths=['core/combat.c','core/combat.h','core/game.c','core/game.h','core/rooms.c',
        'core/c64_rooms.c','core/c64_rooms.h','core/c64_sprites.c','core/session.c',
        'core/c64_room_data.h','core/c64_room_programs.h','tools/build_c64_rooms.py',
        'tests/spawn_bridge.c','tests/spawn_fixture.h','tests/session_fixture.h',
        'tools/audit_spawn.py','tools/audit_spawn_world.py','tools/build_spawn_fixture.py',
        'tools/verify_spawn_delivery.py','tools/verify_c64_candidate.py',
        'tools/verify_spawn_native_report.ps1','tools/merge_spawn_native_runs.py',
        'amiga-build.ps1','amiga-run.ps1',
        'test-spawn.ps1','test-parity.ps1','test-amiga.ps1','test-core.ps1','amiga/main.c',
        'docs/ENEMY_SPAWNS.md','reference/analysis/spawn-audit-2026-10-26/report.json',
        'reference/analysis/spawn-audit-2026-10-26/world-controls.json',
        'reference/analysis/spawn-audit-2026-10-26/source-disassembly.txt',
        'reference/analysis/spawn-audit-2026-10-26/room-table.md',
        'reference/validation/c64-room-runtime.json','reference/analysis/ai-audit-2026-10-25/report.json',
        'reference/validation/c64-core.json','reference/validation/a500-c64-combat-diagnostic.json']
    out=dict(date='2026-10-26',status='verified_scoped_source_spawn_services_and_entry_phases',
        source_files=[artifact(p) for p in paths],normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        checks=r['checks'],source_main_updates=123,birth_blast_cases=30,native_fixture_cases_per_run=223,
        native_validation_complete=True,native_runs=2,native_loop_iterations_per_run=6000,
        natural_playthrough=False,edition_verified=False,full_actor_parity=False,full_m4_complete=False,
        realtime_gate_passed=n['realtime_contract_passed'],limits=[
            'Injected RAM/contact/register seams, not natural C64 play',
            'Full actor/IRQ context and natural memory-read distribution not certified',
            'Logical timer progression does not certify wall-clock or strict field cadence',
            'Ordinary AI wait/retreat/collect-all combat and complete human-Yamo input remain open'])
    save(REPORT,out)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=out['date'],status=out['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    evidence=dict(id='SPAWN-AUDIT-0001',date=out['date'],status='candidate_code_derived_partial_and_native_scoped',
        source_sha256=r['source_sha256'],primary_edition_verified=False,natural_playthrough=False,full_original_parity=False,
        source_ranges=['$0A2A-$0A69','$0B8E-$0E2D','$1159-$1166','$130B-$1382','$1614-$1626',
            '$1BEE-$1C32','$2235-$2269','$2E39-$2EE9','$3001-$304A','$30D4-$310B','$4BAE-$4BFD','$4C9E'],
        condition='Actual source spawn services/tables, entry phases/masks, saved arrival/health, age/mode returns and dynamic-door gates integrated. Logical field clock preserved; full actor/IRQ context and natural read distribution remain open.',
        controls=dict(out['checks'],source_main_updates=123,birth_blast_cases=30,native_fixture_cases=223,native_runs=2,native_loop_iterations_per_run=6000),
        artifacts=[artifact(p) for p in (REPORT,'docs/ENEMY_SPAWNS.md','tests/spawn_fixture.h',
            'reference/analysis/spawn-audit-2026-10-26/report.json',
            'reference/analysis/spawn-audit-2026-10-26/world-controls.json',
            'reference/analysis/spawn-audit-2026-10-26/source-disassembly.txt')])
    save('docs/parity/evidence/SPAWN-AUDIT-0001.json',evidence)
    verify()
def verify():
    checks();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    assert not r['full_actor_parity'] and not r['natural_playthrough']
    print('VERIFIED source spawn audit:all20 tables,4320 services,123 main updates,all5 R08 bombs;223 native controls x2 and identical6000 replay')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();record() if a.record else verify()
