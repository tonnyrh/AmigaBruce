"""Bind the session/wall delivery; never promote historical native evidence."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/session-walls-delivery.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale session evidence: {x['path']}"
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n')
def native_sources(raw):
    archive='reference/validation/history/session-before-infinity-label-2026-10-25'
    if raw['executable_sha256']==artifact('amiga/out/bruce_test.exe')['sha256']:
        identities(raw['source_files']);return None
    from verify_native_equivalence import compare
    proof=compare(ROOT/'amiga/out/bruce_test.exe',ROOT/archive/'bruce_test.exe',ROOT/'amiga/out/bruce_test.elf',ROOT)
    assert proof['tested']['sha256']==raw['executable_sha256']
    for x in raw['source_files']:
        if x['path']=='amiga/main.c':
            assert artifact(archive+'/main.c')['sha256']==x['sha256']
        else:identities([x])
    proof['captured_main_source']=artifact(archive+'/main.c')
    return proof
def host():
    r=read('reference/analysis/session-walls-2026-10-25/report.json');identities(r['source_files'])
    assert r['status']=='passed_controlled_source_checks' and not r['natural_playthrough'] and not r['edition_verified']
    assert len(r['death_steps'])==160 and sum(len(t['steps']) for t in r['room6_trajectories'])==140
    assert sum(len(t['steps']) for t in r['npc_wall_trajectories'])==120 and len(r['npc_contact_cases'])==1280
    for p in ('reference/validation/c64-core.json','reference/validation/c64-room-runtime.json',
              'reference/validation/source-audio-host.json','reference/validation/source-dma-host.json'):
        identities(read(p)['source_files'])
    return r
def record():
    h=host()
    paths=['amiga/main.c','amiga/source_audio.h','core/source_audio.c','core/source_dma.c','core/source_dma.h',
        'amiga-build.ps1','amiga-run.ps1','test-amiga.ps1','test-core.ps1','test-parity.ps1',
        'tools/verify_session_delivery.py','tools/verify_native_equivalence.py','tools/inspect_native_menu.py','tools/verify_c64_candidate.py','docs/SESSION_WALLS.md',
        'reference/analysis/session-walls-2026-10-25/report.json','reference/analysis/session-walls-2026-10-25/source-disassembly.txt',
        'reference/validation/c64-core.json','reference/validation/c64-room-runtime.json',
        'reference/validation/source-audio-host.json','reference/validation/source-dma-host.json']
    paths+= [x['path'] for x in h['source_files']]
    r=dict(date='2026-10-25',status='source_checked_session_and_wall_fixes_native_pending',
        source_sha256=h['source_sha256'],edition_verified=False,natural_playthrough=False,full_c64_game_parity=False,
        native_validation_complete=False,realtime_gate_passed=False,cli_chip_reserve_passed=False,
        source_files=[artifact(p) for p in dict.fromkeys(paths)],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        controls=dict(death_life_steps=160,room6_jump_steps=140,npc_wall_steps=120,npc_pixel_contacts=1280),
        limits=['Controlled fixture states are not natural C64 play',
                'Full combat, AI, score/bonus and actor-state parity remains open',
                'Debug options intentionally override normal rules',
                'SID timbre and new native audio recordings remain separate work'])
    p='reference/validation/source-audio-raw.json'
    if (ROOT/p).exists():
        raw=read(p)
        try:
            equivalent=native_sources(raw)
            assert raw['test_frames']==6000
            assert len(raw['runs'])==2
            for run in raw['runs']:
                assert run['frames']=='6000' and run['session_fixture_failure']=='0'
                assert run['session_wall_fixture_cases']=='324' and run['session_wall_fixture_failure']=='0'
                assert run['source_dma_fixture_failure']=='0' and run['source_dma_faults']=='0'
                assert run['capture_fault']=='0' and run['runtime_arithmetic_errors']=='0'
            r['native_validation_complete']=True;r['native_runs']=raw['runs'];r['native_capture']=artifact(p)
            r['realtime_gate_passed']=all(int(x['max_gap_excluding_framebuffer_capture'])==1 for x in raw['runs'])
            r['cli_chip_reserve_passed']=all(int(x['chip_largest_loaded'])>=49152 for x in raw['runs'])
            r['status']='verified_scoped_session_and_wall_controls_on_A500'
            if equivalent:r['native_rebuild_equivalence']=equivalent
        except (AssertionError,KeyError) as error:r['native_pending_reason']=str(error)
    qa='reference/analysis/session-walls-2026-10-25/menu-native.json'
    if (ROOT/qa).exists():
        q=read(qa);identities(q['artifacts']+q['source_files'])
        assert q['normal_binary']==r['normal_build'][0]
        r['menu_native']=artifact(qa)
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
        identities([r['native_capture']]);assert r['native_runs']==read(r['native_capture']['path'])['runs']
        proof=native_sources(read(r['native_capture']['path']))
        assert proof==r.get('native_rebuild_equivalence')
    if 'menu_native' in r:
        identities([r['menu_native']]);q=read(r['menu_native']['path']);identities(q['artifacts']+q['source_files'])
    print('VERIFIED source/session controls; current native6000x2='+str(r['native_validation_complete'])+
          '; strict cadence='+str(r['realtime_gate_passed'])+'; CLI Chip reserve='+str(r['cli_chip_reserve_passed']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
    record() if a.record else verify()
