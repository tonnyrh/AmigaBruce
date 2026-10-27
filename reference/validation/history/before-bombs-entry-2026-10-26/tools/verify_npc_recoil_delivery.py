"""Bind the bounded NPC recoil repair to source controls and A500 executions."""
from pathlib import Path
import argparse
import hashlib
import json
from verify_climb_delivery import verify as verify_climb

ROOT=Path(__file__).resolve().parents[1]
REPORT='reference/validation/npc-recoil-delivery.json'
SOURCE='reference/analysis/npc-recoil-2026-10-25/source-controls.json'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def artifact(path):
    p=ROOT/path
    return dict(path=path,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def identities(items):
    for item in items:assert artifact(item['path'])['sha256']==item['sha256'],f"Stale NPC recoil evidence: {item['path']}"
def save(path,value):(ROOT/path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def controls():
    verify_climb()
    source=read(SOURCE);identities(source['source_files'])
    assert source['helpers_compared']==192 and source['npc_histories_compared']==1000
    assert source['source_emergency_reentry_retained']
    assert not source['edition_verified'] and not source['natural_playthrough']
    raw=read('reference/validation/source-audio-raw.json')
    for run in raw['runs']:
        assert run['npc_recoil_fixture_cases']=='24' and run['npc_recoil_fixture_failure']=='0'
    return source,raw,read('reference/validation/climb-delivery.json')


def record():
    source,raw,prior=controls()
    files=[SOURCE,'reference/analysis/npc-recoil-2026-10-25/baseline.json',
        'reference/analysis/npc-recoil-2026-10-25/npc-recoil-before.txt',
        'reference/analysis/npc-recoil-2026-10-25/npc_recoil_probe.c',
        'reference/analysis/npc-recoil-2026-10-25/source-disassembly.txt',
        'reference/validation/climb-delivery.json','reference/validation/c64-core.json',
        'docs/NPC_RECOIL.md','docs/ACTIVE_TESTS.md','docs/SOURCE_AUDIO.md','docs/AUDIO_PLAYBACK.md',
        'README.md','tools/audit_npc_recoil.py','tools/verify_npc_recoil_delivery.py',
        'tools/verify_c64_candidate.py']
    result=dict(date='2026-10-25',status='verified_scoped_npc_recoil_history_and_room2_regression',
        source_sha256=source['source_sha256'],edition_verified=False,full_c64_game_parity=False,
        natural_playthrough=False,complete_npc_actor_machine=False,
        source_recoil_helper_cases=192,source_npc_wall_cases=1000,
        native_regression_cases_per_launch=24,native_regression_launches=2,
        native_regression_failures=0,source_emergency_reentry_retained=True,
        normal_build=prior['normal_build'],native_binaries=prior['native_binaries'],
        native_captures=prior['native_captures'],native_runs=raw['runs'],
        source_files=raw['source_files'],evidence=[artifact(p) for p in files],
        realtime_gate_passed=prior['realtime_gate_passed'],
        cli_chip_reserve_passed=prior['cli_chip_reserve_passed'],
        interactive_process_restarted=False,
        limitations=['Controlled R02 hits/positions, not a natural input recording',
            'Full NPC collision poses, ordinary wall dispatch, AI, combat and life state machines remain partial',
            'C64 zero-history emergency room re-entry remains; initially embedded fixtures may legitimately reach it',
            'Strict A500 field timing remains a separate open gate'])
    save(REPORT,result)
    for path in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        save(path,dict(status=result['status'],date=result['date'],actor_logic_fully_ported=False,
            full_m2_parity=False,full_m4_parity=False,full_m5_complete=False,
            natural_playthrough_verified=False,primary_edition_verified=False,
            all_room_realtime_gate_passed=False,all_room_native_rerun_after_actor_changes=False,
            enhanced_art_active=False,artifact=artifact(REPORT)))
    save('docs/parity/evidence/NPC-RECOIL-0001.json',dict(id='NPC-RECOIL-0001',date=result['date'],
        status='candidate_code_derived_partial',full_original_parity=False,
        summary='NPC motion/recoil history and recovery ownership corrected;192 original6502 helper cases,1000 NPC wall histories,24 native R02 regressions on two A500 launches. Full actor/contact/AI and timing parity remain open.',
        artifacts=[artifact(REPORT)]))
    verify()


def verify():
    source,raw,prior=controls();report=read(REPORT)
    identities(report['source_files']+report['normal_build']+report['native_binaries']+
               report['native_captures']+report['evidence'])
    assert report['native_runs']==raw['runs']
    assert not report['full_c64_game_parity'] and report['source_emergency_reentry_retained']
    assert report['realtime_gate_passed']==prior['realtime_gate_passed']
    assert report['cli_chip_reserve_passed']==prior['cli_chip_reserve_passed']
    print('VERIFIED NPC recoil:192 source helper cases,1000 NPC wall histories,24 R02 cases on two A500 launches; full actor parity open')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    record() if args.record else verify()
