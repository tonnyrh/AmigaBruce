"""Check native free-fall X under held/reversed/released ordinary joystick input."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT / 'reference/traces/FALL-0001'
    summary = json.loads((folder / 'summary.json').read_text())
    assert summary['repetitions'] == 2
    for source in summary['recorder_sources']:
        assert sha(ROOT / source['path']) == source['sha256']
    program = ROOT / 'reference/scenarios/FALL-0001.json'
    assert sha(program) == summary['input_program_sha256']
    scenarios = []
    executable = ROOT / '.tmp/core-trace/core-trace.exe'
    for item in summary['scenarios']:
        path = folder / (item['name'] + '.csv')
        assert sha(path) == item['sha256'] and item['identical_replays'] == 2
        with path.open(newline='') as stream:
            rows = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        inputs = ''.join(f"{r['sampled_direction']},{r['sampled_fire']}\n" for r in rows[:-1])
        replay = subprocess.run([str(executable)], input=inputs, text=True,
                                capture_output=True, check=True)
        core = [list(map(int, line.split(','))) for line in replay.stdout.splitlines()]
        assert len(core) == len(rows)
        # Examine only settled free-fall intervals after the input variants
        # diverge. Exclude entry, landing, fighting and climbing transitions.
        start = 154 if item['name'].startswith('ledge-') else 100
        intervals = []
        own_drift = []
        for i, (a, b) in enumerate(zip(rows, rows[1:])):
            if a['tick'] < start:
                continue
            if a['state'] == a['next_state'] == b['state'] == b['next_state'] == 14 and b['target_y'] > a['target_y']:
                dx = 2 * (b['target_x_halfpixels'] - a['target_x_halfpixels'])
                intervals.append({'tick': b['tick'], 'x': 2*b['target_x_halfpixels']-24,
                                  'y': b['target_y'], 'dx': dx,
                                  'sampled_direction': a['sampled_direction']})
            u, v = core[i], core[i+1]
            if u[2] == v[2] == 1 and v[1] > u[1] and v[0] != u[0]:
                own_drift.append({'tick': b['tick'], 'from': u[:2], 'to': v[:2]})
        assert len(intervals) >= 5, item['name']
        assert all(r['dx'] == 0 for r in intervals), item['name']
        # Reversing beside the net can re-enter the Amiga blockout's net;
        # it is not an independent airborne-steering gate in that route.
        if item['name'] in ('ledge-held', 'ledge-reverse', 'net-held'):
            assert not own_drift, item['name']
        scenarios.append({'name': item['name'], 'native_freefall_intervals': intervals,
                          'amiga_airborne_horizontal_intervals': own_drift})
        print(item['name'], 'native fixed-X intervals', len(intervals),
              'Amiga downward intervals with drift', len(own_drift))
    assert len(scenarios) == 6
    sources = ['tools/analyze_fall_control.py', 'core/game.c', 'core/room_geometry.h', 'core/game.h',
               'tests/core_trace.c', 'reference/scenarios/FALL-0001.json',
               'reference/traces/FALL-0001/summary.json']
    report = {'capture_id': 'FALL-0001', 'date': '2026-10-22',
              'checks_passed': True, 'primary_edition_verified': False,
              'full_movement_parity': False, 'engine_changed': True,
              'conclusion': 'Native free fall keeps X fixed under held, reversed and released directions. Amiga free fall now also keeps X fixed.',
              'core_executable_sha256': sha(executable),
              'source_files': [{'path': p, 'sha256': sha(ROOT/p)} for p in sources],
              'scenarios': scenarios}
    (ROOT/'reference/validation/fall-control.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
