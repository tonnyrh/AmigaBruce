"""Bind source rules, real pre/post A500 pixels and the shipped renderer."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/room10-electric-delivery.json'
BASE='reference/analysis/room10-electric-2026-10-26'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def identities(items):
    for x in items:assert artifact(x['path'])['sha256']==x['sha256'],f"Stale R10 evidence: {x['path']}"
def save(p,r):(ROOT/p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def checks():
    assert hashlib.sha256((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    identities(read('reference/validation/c64-core.json')['source_files'])
    source=read(BASE+'/source-controls.json');identities(source['source_files'])
    assert source['source_loop_controls']==480 and source['matched'] and not source['natural_playthrough']
    copy=read(BASE+'/copy-controls.json');identities(copy['source_files']);assert len(copy['controls'])==3
    before=read(BASE+'/baseline/report.json');identities(before['source_files']);b=before['runs'][0]
    assert b['electric_checks']=='900' and b['electric_mismatch_fields']=='614' and b['electric_max_streak']=='60'
    after=read(BASE+'/updated/report.json');identities(after['source_files']);assert len(after['runs'])==2
    for label,report in (('baseline',before),('updated',after)):
        image=(ROOT/BASE/label/'frame.bpl').read_bytes();assert len(image)==40960
        h=2166136261
        for value in image:h=((h^value)*16777619)&0xffffffff
        assert all(n['capture_fault']=='0' and str(h)==n['capture_decoded_hash']==n['capture_original_hash'] for n in report['runs'])
    for n in after['runs']:
        assert n['frames']==n['electric_checks']=='900' and n['source_reader_page']=='104'
        assert n['restored_os']=='1' and n['c64_render_checks']=='2'
        assert int(n['electric_mismatch_fields'])<int(b['electric_mismatch_fields'])
        assert int(n['electric_max_streak'])<int(b['electric_max_streak'])
        for key in ('session_fixture_failure','session_wall_fixture_failure','npc_recoil_fixture_failure','movement_fixture_failure','climb_fixture_failure','moving_net_fixture_failure','contact_fixture_failure','sprite_fixture_failure','source_dma_fixture_failure','source_dma_faults','runtime_arithmetic_errors','c64_room_fault','c64_render_mismatches','source_audio_faults'):
            assert n[key]=='0',key
        for key in ('final_x','final_y','enemy_spawns','combat_hits','player_deaths','player_respawns','c64_room_revision'):
            assert n[key]==b[key],(key,n[key],b[key])
        assert int(n['chip_largest_loaded'])>=49152
    return b,after
def record():
    b,after=checks()
    paths=['amiga/main.c','amiga-build.ps1','core/c64_rooms.c','core/c64_rooms.h','core/scene_copy.h',
        'test-amiga.ps1','test-parity.ps1','test-room10-electric.ps1','test-scene-copy.ps1','tests/scene_copy_bridge.c',
        'tools/audit_room10_electric.py','tools/verify_scene_copy.py','tools/verify_room10_electric_delivery.py',
        'tools/verify_c64_candidate.py','docs/ROOM10_ELECTRIC.md','reference/validation/c64-core.json',
        BASE+'/source-controls.json',BASE+'/source-disassembly.txt',BASE+'/copy-controls.json',
        BASE+'/baseline/report.json',BASE+'/baseline/frame.bpl',BASE+'/updated/report.json',BASE+'/updated/frame.bpl']
    r=dict(date='2026-10-26',status='verified_scoped_room10_presentation_repair',source_files=[artifact(p) for p in paths],
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        native_build=[artifact('amiga/out/bruce_test.exe'),artifact('amiga/out/bruce_test.adf')],
        source_loop_controls=480,native_validation_complete=True,native_fields_per_run=900,native_runs=2,
        baseline_mismatch_fields=int(b['electric_mismatch_fields']),baseline_max_streak=int(b['electric_max_streak']),
        updated_mismatch_fields=[int(n['electric_mismatch_fields']) for n in after['runs']],
        updated_max_streak=[int(n['electric_max_streak']) for n in after['runs']],
        natural_playthrough=False,edition_verified=False,full_actor_parity=False,full_m4_complete=False,
        realtime_gate_passed=all(int(n['max_gap_excluding_framebuffer_capture'])<=1 for n in after['runs']))
    save(REPORT,r)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(date=r['date'],status=r['status'],artifact=artifact(REPORT),native_validation_complete=True,
            actor_logic_fully_ported=False,full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,all_room_realtime_gate_passed=False,enhanced_art_active=False))
    verify()
def verify():
    checks();r=read(REPORT);identities(r['source_files']+r['normal_build']+r['native_build'])
    assert not r['natural_playthrough'] and not r['full_actor_parity']
    print('VERIFIED R10 source loops and A500 floor presentation improvement; complete cadence/gameplay remain open')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();record() if a.record else verify()
