"""Report every combat mismatch; entry/health gates do not certify M3 parity."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(executable):
    path = ROOT / 'reference/traces/COMBAT-0001.json'
    capture = json.loads(path.read_text(encoding='utf-8'))
    for source in capture['sources']:
        assert sha(ROOT / source['path']) == source['sha256']
    scenarios = []
    for name, reference in capture['scenarios'].items():
        inputs = ''.join(f"{r['direction']},{r['fire']}\n" for r in reference[:-1])
        replay = subprocess.run([str(executable)], input=inputs, text=True,
                                capture_output=True, check=True)
        rows = [[list(map(int, row.split(',')))[i:i+4] for i in (0, 4, 8)]
                for row in replay.stdout.splitlines()]
        assert len(rows) == len(reference)
        actors = []
        for actor in range(3):
            first_ref = next((i for i, r in enumerate(reference) if r['actors'][actor]['active'] & 1), None)
            first_own = next((i for i, r in enumerate(rows) if r[actor][0]), None)
            first_health_ref = reference[first_ref]['actors'][actor]['health'] if first_ref is not None else None
            first_health_own = rows[first_own][actor][3] if first_own is not None else None
            differences = []
            for tick, (ref, own) in enumerate(zip(reference, rows)):
                a = ref['actors'][actor]
                expected = [int(bool(a['active'] & 1)), 2*a['x']-24, a['y'], a['health']]
                actual = own[actor]
                # Inactive C64 actor coordinates/health are intentionally irrelevant.
                if actual[0] != expected[0] or (expected[0] and actual != expected):
                    differences.append({'tick': tick, 'reference': expected, 'amiga_core': actual})
            def first_motion(sequence, native):
                first = first_ref if native else first_own
                if first is None:
                    return None
                def xy(row):
                    return (row['actors'][actor]['x'], row['actors'][actor]['y']) if native else row[actor][1:3]
                return next((i for i in range(first+1, len(sequence))
                             if xy(sequence[i]) != xy(sequence[first])), None)
            motion_ref, motion_own = first_motion(reference, True), first_motion(rows, False)
            # Room exits are M4. Bound the initial-walk check at a native exit;
            # keep the exit mismatch and every later difference in the report.
            walk_end = min(motion_ref+10, len(reference)) if motion_ref is not None else 0
            if motion_ref is not None:
                walk_end = next((i for i in range(motion_ref, walk_end)
                                 if not (reference[i]['actors'][actor]['active'] & 1)), walk_end)
            walk_gate = actor == 0 or (motion_ref == motion_own and motion_ref is not None and
                not any(motion_ref <= d['tick'] < walk_end for d in differences))
            actors.append({'actor': ('bruce', 'yamo', 'ninja')[actor],
                           'first_active_tick': {'c64': first_ref, 'amiga_core': first_own},
                           'first_health': {'c64': first_health_ref, 'amiga_core': first_health_own},
                           'first_motion_tick': {'c64': motion_ref, 'amiga_core': motion_own},
                           'initial_walk_gate': walk_gate,
                           'initial_walk_window': None if actor == 0 else {'from_tick': motion_ref, 'through_tick': walk_end-1,
                               'boundary': 'ten observations or earlier native room exit; exits remain open'},
                           'entry_health_gate': first_ref == first_own and first_health_ref == first_health_own,
                           'differences': differences})
        scenarios.append({'scenario': name, 'samples': len(rows), 'actors': actors})
    report = {'capture_id': 'COMBAT-0001', 'primary_edition_verified': False,
              'full_m3_parity': False, 'reference_sha256': sha(path),
              'alignment': 'Previous boundary direction/fire -> one core step; no fitted offset; x=2*C64x-24',
              'time_basis': 'One logic tick is three PAL fields; differing machine clocks remain documented in movement-timing.json',
              'limitations': ['Sampled input only; no late-fire phase probes in COMBAT-0001',
                             'Enemy navigation, collision, recovery and respawn remain provisional',
                             'Passing entry/health gates does not close recorded trajectory/damage mismatches'],
              'entry_health_gates_passed': all(a['entry_health_gate'] for s in scenarios for a in s['actors']),
              'initial_walk_gates_passed': all(a['initial_walk_gate'] for s in scenarios for a in s['actors']),
              'scenarios': scenarios,
              'source_files': [{'path': p, 'sha256': sha(ROOT/p)} for p in
                               ('core/game.c', 'core/room_geometry.h', 'core/game.h', 'core/combat.c', 'core/combat.h',
                                'core/rooms.c', 'core/rooms.h', 'core/room_data.h',
                                'tests/combat_trace.c', 'tools/compare_combat.py', 'test-parity.ps1')]}
    (ROOT/'reference/validation/candidate-combat.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for scenario in scenarios:
        print(scenario['scenario'], ':', sum(len(a['differences']) for a in scenario['actors']),
              'actor mismatches recorded; entry/health gates',
              'PASS' if all(a['entry_health_gate'] for a in scenario['actors']) else 'FAIL')
    assert report['entry_health_gates_passed'], 'Entry/health regression; inspect candidate-combat.json'
    assert report['initial_walk_gates_passed'], 'Initial enemy motion regression; inspect candidate-combat.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    compare(parser.parse_args().executable)
