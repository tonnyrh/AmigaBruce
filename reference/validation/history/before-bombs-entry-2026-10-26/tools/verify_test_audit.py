"""Record/verify the bounded actor fixes; keep old A500 room evidence historical."""
from pathlib import Path
from datetime import date
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = 'reference/analysis/test-audit-2026-10-25/'
REPORT = 'reference/validation/test-audit.json'


def sha(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def read(p):
    return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))


def save(p, value):
    (ROOT/p).parent.mkdir(parents=True, exist_ok=True)
    (ROOT/p).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def artifact(p):
    return dict(path=p, sha256=sha(p), size_bytes=(ROOT/p).stat().st_size)


def identities(items):
    for item in items:
        assert sha(item['path']) == item['sha256'], f"Stale audit evidence: {item['path']}"


def prepare():
    # Same complete runtime/build input set as the previous runner record;
    # record current hashes, never refresh that historical report in place.
    old = read('reference/validation/a500-c64-combat-diagnostic.json')
    items = [artifact(i['path']) for i in old['source_files']]
    save(OUT+'native-inputs.json', dict(source_files=items,
        executable=artifact('amiga/out/bruce_test.exe'), adf=artifact('amiga/out/bruce_test.adf'),
        scope='Current compiled runtime inputs during owned test-amiga.ps1 run; runner also checks inputs before gates'))
    print('RECORDED current native build identities; no runtime pass recorded')


def record():
    inputs = read(OUT+'native-inputs.json')
    identities(inputs['source_files']+[inputs['executable'], inputs['adf']])
    host = read('reference/validation/c64-core.json')
    identities(host['source_files'])
    expected = dict(pair.split('=') for line in host['output']
                    if line.startswith('M3_6000 ') for pair in line.split()[1:])
    assert len(expected) == 7
    runs, raw = [], []
    for n in (1, 2):
        path = f'amiga/out/autotest-{n}.txt'
        run = dict(line.split('=', 1) for line in (ROOT/path).read_text().splitlines() if '=' in line)
        assert run['parity'] == 'PROVISIONAL' and run['frames'] == '6000'
        assert run['combat_mode'] == '1' and run['room_tour'] == '0'
        assert run['collect_frame_drops'] == '1' and run['source_profile'] == '0'
        for key in ('bad_presents', 'runtime_arithmetic_errors', 'canvas_residue_bytes',
                    'c64_room_fault', 'c64_render_mismatches'):
            assert run[key] == '0', (n,key)
        for key in ('restored_os', 'intro_finished', 'intro_silence_reload',
                    'intro_dma_stopped', 'intro_bitmap_restored'):
            assert run[key] == '1', (n,key)
        assert all(run[k] == v for k,v in expected.items()), (n,expected)
        assert run['sfx_variant_mask'] == '15' and run['sfx_played'] == run['sfx_silence_reloads']
        assert 300 <= int(run['present_min_line']) <= int(run['present_max_line']) <= 308
        dest = OUT+f'native-{n}.txt'
        shutil.copyfile(ROOT/path, ROOT/dest)
        raw.append(artifact(dest)); runs.append(run)
    for key in ('chip_available_before','expansion_available_before'):
        assert runs[0][key] == runs[1][key], key
    native = []
    for suffix in ('exe','adf'):
        dest = f'amiga/out/validated/test-audit-2026-10-25.{suffix}'
        shutil.copyfile(ROOT/f'amiga/out/bruce_test.{suffix}', ROOT/dest)
        native.append(artifact(dest))
    cpu = read(OUT+'report.json')
    identities(cpu['source_files']+[cpu['source'],cpu['disassembly']])
    assert cpu['fixture_count'] == 61 and not cpu['amiga_implementation_verified']
    source_files = [artifact(p) for p in ('core/game.c','core/game.h','core/combat.c','core/combat.h',
                    'tests/c64_rooms_test.c','test-core.ps1','test-parity.ps1','tools/audit_c64_tests.py',
                    'tools/verify_test_audit.py','tools/verify_c64_candidate.py')]
    timing = all(int(r['max_gap_excluding_framebuffer_capture']) <= 1 and
                 int(r['missed_frames']) == 0 for r in runs)
    reserve = all(int(r['chip_largest_loaded']) >= 49152 for r in runs)
    # Update restart command without interrupting the user's running emulator.
    start = ROOT/'.tmp/amiga-boot/c/start'
    if start.exists():
        old = ROOT/'amiga/out/validated/before-test-audit-normal.exe'
        if not old.exists(): shutil.copyfile(start, old)
        shutil.copyfile(ROOT/'amiga/out/bruce_amiga.exe', start)
    report = dict(date=str(date.today()), status='source_test_interpretations_corrected_scoped_actor_fixes_verified',
        source_sha256=cpu['source']['sha256'], primary_edition_verified=False,
        source_fixture_count=61, source_fixtures_are_controlled_not_natural=True,
        full_c64_combat_parity=False, actor_logic_fully_ported=False,
        natural_playthrough_verified=False, full_m2_parity=False, full_m4_parity=False,
        all_room_native_rerun_after_actor_changes=False,
        realtime_gate_passed=timing, cli_chip_reserve_passed=reserve,
        cli_chip_reserve_requirement=49152, expected_host_replay=expected,
        native_runs=runs, native_raw=raw, native_artifacts=native,
        native_inputs=artifact(OUT+'native-inputs.json'),
        source_cpu_report=artifact(OUT+'report.json'), host_report=artifact('reference/validation/c64-core.json'),
        normal_build=[artifact('amiga/out/bruce_amiga.exe'),artifact('amiga/out/bruce_amiga.adf')],
        cli_start_updated=start.exists(), running_interactive_instance_restarted=False,
        historical_delivery='reference/validation/history/before-test-audit-2026-10-25/reference/validation/c64-candidate.json',
        source_files=source_files,
        limitations=['Source VIC pixel masks and collect-all/apply-all combat kernel remain open',
                     'Terminal fall injected-state anomaly needs full-machine and edition investigation',
                     'Earlier all-room A500 results are historical after actor changes; timing/memory gates remain open',
                     'Native runner collection does not waive its strict Chip or timing requirements'])
    save(REPORT, report)
    summary = dict(date=report['date'],status=report['status'], actor_logic_fully_ported=False,
                  primary_edition_verified=False, full_m2_parity=False, full_m4_parity=False,
                  full_m5_complete=False, natural_playthrough_verified=False,
                  all_room_realtime_gate_passed=False, all_room_native_rerun_after_actor_changes=False,
                  cli_chip_reserve_passed=reserve, artifact=artifact(REPORT),
                  previous_delivery=report['historical_delivery'])
    save('reference/validation/c64-candidate.json',summary)
    save('reference/validation/visual-candidate.json',summary)
    save('docs/parity/evidence/TEST-AUDIT-0001.json',dict(id='TEST-AUDIT-0001',date=report['date'],
        status='candidate_code_derived_partial', full_original_parity=False,
        summary='T01-T18 reviewed against frozen C64 bytes.61 controlled CPU fixtures; targeted net/input and combat/actor-order fixes; two native replays agree with host. Full sprite/actor/life parity and strict A500 gates remain open.',
        artifacts=[artifact(REPORT),artifact(OUT+'report.json'),artifact('docs/TEST_AUDIT_2026-10-25.md')]))
    verify()


def verify():
    report = read(REPORT)
    identities(report['source_files']+report['native_raw']+report['native_artifacts']+report['normal_build']+
               [report['source_cpu_report'],report['host_report'],report['native_inputs']])
    cpu = read(report['source_cpu_report']['path'])
    identities(cpu['source_files']+[cpu['source'],cpu['disassembly']])
    identities(read(report['host_report']['path'])['source_files'])
    inputs = read(report['native_inputs']['path']); identities(inputs['source_files'])
    assert report['source_fixture_count'] == cpu['fixture_count'] == 61
    assert len(report['native_runs']) == 2
    for n,run in enumerate(report['native_runs']):
        parsed = dict(line.split('=',1) for line in (ROOT/report['native_raw'][n]['path']).read_text().splitlines() if '=' in line)
        assert run == parsed and all(run[k] == v for k,v in report['expected_host_replay'].items())
    assert report['realtime_gate_passed'] == all(int(r['missed_frames']) == 0 and
        int(r['max_gap_excluding_framebuffer_capture']) <= 1 for r in report['native_runs'])
    assert report['cli_chip_reserve_passed'] == all(int(r['chip_largest_loaded']) >= 49152
        for r in report['native_runs'])
    assert not report['full_c64_combat_parity'] and not report['all_room_native_rerun_after_actor_changes']
    assert not report['natural_playthrough_verified'] and not report['primary_edition_verified']
    for p in ('reference/validation/c64-candidate.json','reference/validation/visual-candidate.json'):
        identities([read(p)['artifact']])
    print('VERIFIED bounded test audit:61 source CPU fixtures;2 native6000-field replays match host; '
          f"real-time gate={report['realtime_gate_passed']}; CLI Chip reserve={report['cli_chip_reserve_passed']}; "
          'full actor parity and fresh all-room A500 validation remain open')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare-native',action='store_true');p.add_argument('--record',action='store_true')
    args=p.parse_args()
    if args.prepare_native:prepare()
    elif args.record:record()
    else:verify()
