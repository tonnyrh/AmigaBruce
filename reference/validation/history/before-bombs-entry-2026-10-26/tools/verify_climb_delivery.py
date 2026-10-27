"""Bind bounded source climbing rules to current host/native builds."""
from datetime import date
from pathlib import Path
import argparse
import hashlib
import json
from verify_sprite_delivery import verify as verify_sprites

ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/climb-delivery.json'
CPU='reference/analysis/climb-audit-2026-10-25/report.json'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'


def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def artifact(p):return dict(path=p,sha256=sha(p),size_bytes=(ROOT/p).stat().st_size)
def save(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def identities(items):
    for item in items:assert sha(item['path'])==item['sha256'],f"Stale climb evidence: {item['path']}"


def controls():
    verify_sprites()
    source=read(CPU);snapshot=read('reference/analysis/climb-audit-2026-10-25/snapshot.json')
    identities(source['source_files']+[source['native_fixture'],snapshot['frame']])
    assert source['source_sha256']==snapshot['source_sha256']==SHA
    assert source['status']=='passed_source_net_dispatch_and_sequential_contact'
    assert source['dispatch_cases']==12800 and source['sequential_steps']==866
    assert source['native_fixture']['cases']==390
    assert source['native_fixture']['dispatch']==100 and source['native_fixture']['sequential']==288
    assert source['native_fixture']['projection_checks']==2
    assert source['native_fixture']['raw_bytes']==4504 and source['native_fixture']['packed_bytes']==577
    assert source['native_fixture']['native_raw_fnv']==492911978
    assert source['native_fixture']['temporary_storage_freed']
    assert not source['full_actor_fsm_ported'] and not source['natural_playthrough']
    assert snapshot['snapshot_unchanged'] and snapshot['room']==5
    assert snapshot['source_room_tick_anchor']==[218,179]
    if (ROOT/snapshot['snapshot']['path']).exists():identities([snapshot['snapshot']])
    raw=read('reference/validation/source-audio-raw.json')
    for run in raw['runs']:
        assert run['climb_fixture_cases']=='390' and run['climb_fixture_failure']=='0'
    return source,snapshot,raw,read('reference/validation/c64-sprites-delivery.json')


def record():
    source,snapshot,raw,sprites=controls()
    files=[CPU,'reference/analysis/climb-audit-2026-10-25/snapshot.json',
           'reference/analysis/climb-audit-2026-10-25/source-disassembly.txt',
           'reference/analysis/climb-audit-2026-10-25/baseline.json',
           'reference/validation/c64-sprites-delivery.json','reference/validation/c64-core.json',
           'tools/inspect_climb_snapshot.py','tools/verify_climb_delivery.py',
           'tools/verify_c64_candidate.py','docs/C64_CLIMB.md','docs/ACTIVE_TESTS.md',
           'docs/C64_SPRITES.md','docs/SOURCE_AUDIO.md','docs/parity/register.csv','README.md']
    result=dict(date=str(date.today()),status='verified_source_climbing_and_scoped_room5_regression',
        source_sha256=SHA,edition_verified=False,full_c64_game_parity=False,
        complete_actor_fsm_ported=False,natural_playthrough=False,
        source_dispatch_cases=12800,source_sequential_steps=866,native_fixture_cases=390,
        native_fixture_raw_bytes=4504,native_fixture_packed_bytes=577,native_fixture_raw_fnv=492911978,
        native_fixture_failure=0,native_fixture_launches=2,source_snapshot=snapshot['snapshot'],
        snapshot_resumed_in_emulator=False,original_snapshot_unchanged=True,
        room5_contact_pose_corrected=True,horizontal_pixels_per_ready_step=[4,6],
        horizontal_wait_steps=0,vertical_pixels_per_ready_step=[3,4],vertical_wait_steps=3,
        source_addresses=['1C5F-1CB3','1DCA-1ED5','1F89-1F9F','4A8C','2780-29C2','5212-52AC'],
        source_files=raw['source_files'],normal_build=sprites['normal_build'],
        native_binaries=sprites['native_binaries'],native_captures=sprites['native_captures'],
        native_runs=raw['runs'],realtime_gate_passed=sprites['realtime_gate_passed'],
        cli_chip_reserve_passed=sprites['cli_chip_reserve_passed'],
        all_room_native_rerun=False,interactive_process_restarted=False,
        evidence=[artifact(p) for p in files],
        limitations=['USS identifies room5 and prior code/RAM; exact failed input sequence is not reconstructed',
                     'CPU sequences use controlled actor states/source room phases, not natural gameplay',
                     'Full floor/landing, walk/reaction, NPC, combat and life state machines remain partial',
                     'Current corrected code must start fresh; restoring old USS also restores old program memory',
                     'Strict PAL timing and normal-build memory measurements remain independent'])
    save(REPORT,result)
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(p,dict(status=result['status'],date=result['date'],actor_logic_fully_ported=False,
            full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,
            all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
            enhanced_art_active=False,artifact=artifact(REPORT)))
    save('docs/parity/evidence/CLIMB-0001.json',dict(id='CLIMB-0001',date=result['date'],
        status='candidate_code_derived_partial',full_original_parity=False,
        summary='Bruce net dispatch/contact poses follow frozen code:12800 ready-input cases and866 sequential contact/history steps; room5 grip and horizontal4/6px with no wait corrected.390 controls on two68000 launches. Original USS retained; natural play/full actor/timing parity remain open.',
        artifacts=[artifact(REPORT)]))
    verify()


def verify():
    result=read(REPORT)
    identities(result['source_files']+result['normal_build']+result['native_binaries']+
               result['native_captures']+result['evidence'])
    source,snapshot,raw,sprites=controls()
    assert result['native_runs']==raw['runs']
    assert result['realtime_gate_passed']==sprites['realtime_gate_passed']
    assert result['cli_chip_reserve_passed']==sprites['cli_chip_reserve_passed']
    assert not result['full_c64_game_parity'] and not result['complete_actor_fsm_ported']
    print('VERIFIED climbing:12800 source dispatch/866 sequential contact steps; '
          f"390 fixtures on two A500 launches. Strict timing={result['realtime_gate_passed']}, CLI reserve={result['cli_chip_reserve_passed']}; full actor port open")


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    record() if args.record else verify()
