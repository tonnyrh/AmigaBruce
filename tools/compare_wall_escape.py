"""Measure natural corner escape inputs on C64 and the current host core."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(executable):
    trace = ROOT/'reference/traces/WALL-0001.json'
    capture = json.loads(trace.read_text(encoding='utf-8'))
    clocks = json.loads((ROOT/'reference/timing-clocks.json').read_text(encoding='utf-8'))
    assert capture['repetitions'] == 2 and len(capture['scenarios']) == 4
    for source in capture['sources']:
        assert sha(ROOT/source['path']) == source['sha256']
    results = []
    prefix = None
    for name, rows in capture['scenarios'].items():
        assert len(rows) == 411
        if prefix is None:
            prefix = rows[:321]
        assert rows[:321] == prefix, 'Different pre-escape state'
        for a, b in zip(rows, rows[1:]):
            assert b['cycles']-a['cycles']-((b['raster_line']-a['raster_line'])*63+b['raster_cycle']-a['raster_cycle']) == 58968
        inputs = ''.join(f"{r['direction']},{r['fire']}\n" for r in rows[:-1])
        replay = subprocess.run([str(executable)], input=inputs, text=True,
                                capture_output=True, check=True)
        own = [[int(x) for x in line.split(',')][:4] for line in replay.stdout.splitlines()]
        assert len(own) == len(rows)
        native = [[int(bool(r['actors'][0]['active'] & 1)),
                   2*r['actors'][0]['x']-24, r['actors'][0]['y'],
                   r['actors'][0]['health']] for r in rows]
        def metrics(sequence, native_clock):
            escaped = next((i for i in range(321, 411)
                            if sequence[i][0] and sequence[i][1] >= 64), None)
            steps = None if escaped is None else escaped-320
            durations = None if steps is None else (
                [steps*58968*1000/clocks['c64_pal_cpu_hz']]*2 if native_clock else
                [steps*3*lines*clocks['amiga_cck_per_line']*1000/clocks['amiga_pal_cck_hz'] for lines in (312, 313)])
            return dict(start=sequence[320], end=sequence[-1],
                        first_x64_tick=escaped,
                        escape_logic_steps=steps, nominal_escape_ms_range=durations,
                        max_x=max(r[1] for r in sequence[320:]))
        result = dict(scenario=name, c64=metrics(native, True), amiga_core=metrics(own, False))
        results.append(result)
        print(name, json.dumps(result, separators=(',', ':')))
    jumping = next(r for r in results if r['scenario'] == 'wall-jump-right')
    assert jumping['c64']['first_x64_tick'] is not None, 'Native escape not observed'
    assert jumping['amiga_core']['first_x64_tick'] is not None, 'Candidate corner escape regression'
    report = dict(capture_id='WALL-0001', checks_passed=True,
                  full_combat_parity=False, primary_edition_verified=False,
                  setup='320 idle steps from frozen warmed baseline, then 90 escape steps; x>=64 is reporting threshold',
                  alignment='Previous boundary joystick sample -> one core step; one step equals three PAL fields',
                  limitations=['One left floor corner in room zero; other walls and enemy phases are untested',
                               'Amiga escape durations are nominal host-core step conversions, not new A500 route timer measurements',
                               'Identical input prefix does not produce identical C64/core health or actor trajectories',
                               'This demonstrates escape routes, not general immunity or full enemy parity'],
                  scenarios=results,
                  source_files=[dict(path=p, sha256=sha(ROOT/p)) for p in (
                      'reference/traces/WALL-0001.json', 'reference/timing-clocks.json', 'tools/compare_wall_escape.py',
                      'tests/combat_trace.c', 'core/game.c', 'core/room_geometry.h', 'core/game.h', 'core/combat.c', 'core/combat.h',
                      'core/rooms.c', 'core/rooms.h', 'core/room_data.h')])
    (ROOT/'reference/validation/candidate-wall-escape.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('executable', type=Path)
    compare(parser.parse_args().executable)
