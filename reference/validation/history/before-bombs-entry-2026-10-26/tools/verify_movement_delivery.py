"""Bind the bounded movement audit to actual source controls and fresh A500 runs."""
from datetime import date
from pathlib import Path
import argparse
import hashlib
import json
from verify_contact_delivery import verify as verify_contacts

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'reference/validation/movement-delivery.json'
CPU = 'reference/analysis/movement-audit-2026-10-25/wall-report.json'
SHA = '092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'


def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def artifact(p): return dict(path=p, sha256=sha(p), size_bytes=(ROOT/p).stat().st_size)
def save(p, v): (ROOT/p).write_text(json.dumps(v, indent=2)+'\n', encoding='utf-8')


def identities(items):
    for item in items:
        assert sha(item['path']) == item['sha256'], f"Stale movement evidence: {item['path']}"


def controls():
    verify_contacts()
    audio = read('reference/validation/source-audio-delivery.json')
    cpu = read(CPU)
    identities(cpu['source_files']+[cpu['generated']])
    assert cpu['source_sha256'] == SHA
    assert cpu['status'] == 'passed_decoded_wall_kernel_vs_actual6502'
    assert cpu['cases'] == len(cpu['results']) == 500
    assert cpu['kick_cases'] == len(cpu['kick_results']) == 480
    assert cpu['jump_cases'] == len(cpu['jump_results']) == 54
    assert cpu['native_fixture_checks'] == 70
    assert cpu['injected_contact_and_history']
    assert not cpu['edition_verified'] and not cpu['natural_playthrough']
    assert len(audio['native_runs']) == 2
    for run in audio['native_runs']:
        assert run['movement_fixture_cases'] == '70' and run['movement_fixture_failure'] == '0'
        assert run['frames'] == '6000' and run['restored_os'] == '1'
    start = '.tmp/amiga-boot/c/start'
    assert (ROOT/start).exists() and sha(start) == sha('amiga/out/bruce_amiga.exe')
    return cpu, audio


def record():
    cpu, audio = controls()
    files = [CPU, 'reference/analysis/movement-audit-2026-10-25/source-disassembly.txt',
             'reference/validation/contact-delivery.json', 'reference/validation/source-audio-delivery.json',
             'tools/verify_movement_delivery.py', 'tools/verify_source_movement.py',
             'tests/movement_fixture.h', 'tests/movement_bridge.c', 'test-source-movement.ps1',
             'docs/C64_MOVEMENT.md', 'docs/ACTIVE_TESTS.md', 'docs/parity/register.csv',
             'docs/parity/evidence/ROOM-RUNTIME-0001.json',
             'docs/parity/evidence/TEST-AUDIT-0001.json', 'README.md']
    if (ROOT/'docs/parity/evidence/AI-AUDIT-0001.json').exists():
        files += ['docs/parity/evidence/AI-AUDIT-0001.json', 'docs/C64_AI.md',
                  'reference/analysis/ai-audit-2026-10-25/report.json']
    result = dict(date=str(date.today()), status='verified_scoped_source_movement_and_contacts',
                  source_sha256=SHA, edition_verified=False, full_c64_game_parity=False,
                  complete_actor_fsm_ported=False, natural_playthrough=False,
                  source_wall_history_cases=500, source_pixel_kick_cases=480,
                  sequential_source_jump_steps=54, native_fixture_cases=70,
                  native_fixture_launches=2, native_fixture_failure=0,
                  native_replay='6000 fields per launch; injected movement fixtures run before title',
                  source_addresses=['1C5B-1D6E', '1DF2-1FC3', '2008-216A', '24B7-24EA',
                                    '2780-28B2', '5212', '5CBF-5D04'],
                  source_files=audio['source_files'], cpu_sources=cpu['source_files'],
                  normal_build=audio['normal_build'], native_binaries=audio['native_binaries'],
                  native_captures=audio['native_captures'], native_runs=audio['native_runs'],
                  realtime_gate_passed=audio['realtime_gate_passed'],
                  cli_chip_reserve_passed=audio['cli_chip_reserve_passed'],
                  all_room_native_rerun=False, cli_start_updated=True,
                  evidence=[artifact(p) for p in files],
                  limitations=['History kernel exact for controlled inputs; native actor/history bridge remains partial',
                               'Full support/landing and walk/reaction pose sequences remain open; Bruce net phases audited separately',
                               'Combat sprite-latch/collect-apply and full life/NPC state machines remain open',
                               'No natural wall-route or all-room A500 certification',
                               'Strict A500 timing and memory gates reported independently'])
    save(REPORT, result)
    for p in ('reference/validation/c64-candidate.json', 'reference/validation/visual-candidate.json'):
        save(p, dict(status=result['status'], date=result['date'], actor_logic_fully_ported=False,
                     full_m2_parity=False, full_m4_parity=False, full_m5_complete=False,
                     natural_playthrough_verified=False, primary_edition_verified=False,
                     all_room_realtime_gate_passed=False,
                     all_room_native_rerun_after_actor_changes=False, artifact=artifact(REPORT)))
    save('docs/parity/evidence/MOVEMENT-AUDIT-0001.json',
         dict(id='MOVEMENT-AUDIT-0001', date=result['date'], status='candidate_code_derived_partial',
              full_original_parity=False,
              summary='Source black-contact/history kernel, kick phases/masks, open jump/fall phases and Bruce helper bounds corrected.500 actual6502 history fixtures,480 pixel/kick fixtures over20rooms,54 sequential jump steps;70 small fixtures pass on two68000 launches. Full actor/history bridge, landing, combat and strict A500 gates remain open.',
              artifacts=[artifact(REPORT)]))
    verify()


def verify():
    r = read(REPORT)
    identities(r['source_files']+r['cpu_sources']+r['normal_build']+r['native_binaries']+
               r['native_captures']+r['evidence'])
    cpu, audio = controls()
    assert r['source_wall_history_cases'] == cpu['cases']
    assert r['source_pixel_kick_cases'] == cpu['kick_cases']
    assert r['sequential_source_jump_steps'] == cpu['jump_cases']
    assert r['native_runs'] == audio['native_runs']
    assert r['realtime_gate_passed'] == audio['realtime_gate_passed']
    assert r['cli_chip_reserve_passed'] == audio['cli_chip_reserve_passed']
    assert not r['full_c64_game_parity'] and not r['complete_actor_fsm_ported']
    assert not r['natural_playthrough'] and not r['edition_verified']
    print('VERIFIED movement:500 source history/480 kick/54 jump steps;70 fixtures on2 A500 launches. '
          f"Strict timing={r['realtime_gate_passed']}, CLI reserve={r['cli_chip_reserve_passed']}; complete actor port open")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--record', action='store_true')
    args = p.parse_args()
    record() if args.record else verify()
