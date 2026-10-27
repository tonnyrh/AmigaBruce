"""Current contact delivery, without reusing historical A500/actor passes."""
from pathlib import Path
from datetime import date
import argparse
import hashlib
import json
from verify_audio_delivery import verify as verify_audio

ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/contact-delivery.json'
OBJECTS='reference/analysis/contact-audit-2026-10-25/report.json'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def artifact(p):return dict(path=p,sha256=sha(p))
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

def controls():
    verify_audio()
    objects=read(OBJECTS);runtime=read('reference/validation/c64-room-runtime.json')
    audio=read('reference/validation/source-audio-delivery.json')
    assert objects['source_sha256']==runtime['source_sha256']==SHA
    assert len(objects['cases'])==runtime['object_pass_checks']==29
    assert runtime['contact_checks']==24860 and runtime['door_gate_checks']==640
    assert runtime['rooms']==20 and runtime['source_loop_calls']==2560
    assert not objects['edition_verified'] and not objects['natural_playthrough']
    assert not runtime['hardware_parity'] and not runtime['natural_playthrough']
    for row in audio['native_runs']:
        assert row['contact_fixture_cases']=='29' and row['contact_fixture_failure']=='0'
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    if source.exists():assert sha(source.relative_to(ROOT))==SHA
    return objects,runtime,audio

def record():
    objects,runtime,audio=controls()
    files=[OBJECTS,'reference/analysis/contact-audit-2026-10-25/source-disassembly.txt',
           'reference/validation/c64-room-runtime.json','reference/validation/c64-core.json',
           'reference/validation/source-audio-delivery.json','tools/verify_c64_contacts.py',
           'tests/contact_fixture.h','tests/contact_bridge.c','docs/C64_CONTACTS.md',
           'docs/ACTIVE_TESTS.md','docs/parity/register.csv','docs/TEST_AUDIT_2026-10-25.md',
           'docs/parity/evidence/ROOM-RUNTIME-0001.json','docs/parity/evidence/TEST-AUDIT-0001.json','README.md',
           'tools/verify_contact_delivery.py','tools/verify_c64_candidate.py']
    result=dict(date=str(date.today()),status='verified_scoped_source_contacts_and_room_edges',
                source_sha256=SHA,edition_verified=False,full_c64_game_parity=False,
                natural_playthrough=False,source_object_cases=29,pixel_contact_cases=24860,
                bruce_mask_count=35,source_rooms=20,native_fixture_launches=2,
                native_fixture_failure=0,all_source_rooms_rendered_on_native=False,
                object_pose_scope=['idle facing without net','punch state17','prone state26'],
                r01_east_min_x=300,r02_upper_arrival=[6,98],r02_lower_arrival=[8,146],
                native_replay='6000 fields per launch; original CPU object states injected separately',
                realtime_gate_passed=audio['realtime_gate_passed'],
                cli_chip_reserve_passed=audio['cli_chip_reserve_passed'],
                all_room_native_rerun=False,normal_build=audio['normal_build'],
                source_files=audio['source_files'],evidence=[artifact(p) for p in files],
                limitations=['Walk/reaction and NPC pose phases remain on the adapter; Bruce net motion/contact is audited separately',
                             'Full support/landing motor and actor/history bridge remain partial',
                             'Perceived exit presentation not measured in natural play',
                             'Strict A500 timing/Chip reserve reported independently'])
    save(REPORT,result)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(status=result['status'],date=result['date'],actor_logic_fully_ported=False,
                    full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
                    natural_playthrough_verified=False,primary_edition_verified=False,
                    all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
                    artifact=artifact(REPORT)))
    save('docs/parity/evidence/CONTACT-AUDIT-0001.json',dict(id='CONTACT-AUDIT-0001',date=result['date'],
         status='candidate_code_derived_partial',full_original_parity=False,
         summary='Actual6502 pose/pixel/object pipeline:29 injected fixtures;24860 contacts/35masks/20rooms; constant idle/punch/prone object masks and pickup sound corrected. R01 east minimumX300 retained; exact arrivals/returns checked. Two68000 fixture launches; phase-dependent actor and strict A500 gates remain open.',
         artifacts=[artifact(REPORT)]))
    verify()

def verify():
    r=read(REPORT)
    for item in r['source_files']+r['normal_build']+r['evidence']:
        assert sha(item['path'])==item['sha256'],f"Stale contact evidence: {item['path']}"
    _,runtime,audio=controls()
    assert r['pixel_contact_cases']==runtime['contact_checks']
    assert r['realtime_gate_passed']==audio['realtime_gate_passed']
    assert r['cli_chip_reserve_passed']==audio['cli_chip_reserve_passed']
    assert not r['full_c64_game_parity'] and not r['natural_playthrough']
    print('VERIFIED scoped contacts:29 source object cases,24860 pixel checks,2 native fixture launches; full actor port open')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    record() if args.record else verify()
