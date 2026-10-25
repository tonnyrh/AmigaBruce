"""Report full room-route differences and gate the first measured interactions."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compare(executable):
    results = []
    sources = []
    for capture_id, name in [('ROOM-0002', 'jump-lanterns'), ('ROOM-0003', 'first-room-return')]:
        path = ROOT/'reference/traces'/f'{capture_id}.json'
        capture = json.loads(path.read_text(encoding='utf-8'))
        assert capture['repetitions'] == 2
        for source in capture['sources']:
            assert sha(ROOT/source['path']) == source['sha256']
        sources.append(path)
        rows = capture['scenarios'][name]
        inputs = ''.join(f"{r['direction']},{r['fire']}\n" for r in rows[:-1])
        out = subprocess.run([str(executable)], input=inputs, text=True, capture_output=True, check=True)
        own = [[int(v) for v in row.split(',')] for row in out.stdout.splitlines()]
        assert len(own) == len(rows)
        native = [[r['room'], 2*r['actors'][0]['x']-24, r['actors'][0]['y'],
                   6-r['lantern_counts'][0]] for r in rows]
        changes_ref = [(i, row[0], row[1], row[2]) for i, row in enumerate(native)
                       if i and row[0] != native[i-1][0]]
        changes_own = [(i, row[0], row[1], row[2]) for i, row in enumerate(own)
                       if i and row[0] != own[i-1][0]]
        pickup_ref = next((i for i, row in enumerate(native) if row[3]), None)
        pickup_own = next((i for i, row in enumerate(own) if row[4]), None)
        differences = [dict(tick=i, reference=a, amiga_core=[b[0], b[1], b[2], b[4]])
                       for i, (a, b) in enumerate(zip(native, own))
                       if a != [b[0], b[1], b[2], b[4]]]
        gaps = [dict(tick=b['tick'], from_room=a['room'], to_room=b['room'],
                     corrected_cycles=b['cycles']-a['cycles']-
                     ((b['raster_line']-a['raster_line'])*63+b['raster_cycle']-a['raster_cycle']))
                for a, b in zip(rows, rows[1:])
                if b['cycles']-a['cycles']-
                ((b['raster_line']-a['raster_line'])*63+b['raster_cycle']-a['raster_cycle']) != 58968]
        if name == 'jump-lanterns':
            gate = pickup_ref == pickup_own == 13 and own[13][3] == 4 and own[14][4] == 1
        else:
            gate = [r[1:] for r in changes_ref] == [r[1:] for r in changes_own] == [(1, 6, 98), (0, 298, 98)]
        result = dict(capture_id=capture_id, scenario=name, gate_passed=gate,
                      first_pickup_tick=dict(c64=pickup_ref, amiga_core=pickup_own),
                      room_changes=dict(c64=changes_ref, amiga_core=changes_own),
                      native_nonstandard_gaps=gaps, differences=differences)
        results.append(result)
        print(name, 'gate', gate, 'pickups', pickup_ref, pickup_own,
              'transitions', changes_ref, changes_own, 'differences', len(differences))
    report = dict(regression_gates_passed=all(r['gate_passed'] for r in results),
                  full_m4_parity=False, primary_edition_verified=False, scenarios=results,
                  limitations=['Pickup gate covers first lamp only; all later count and trajectory differences are retained',
                               'Room change gates compare destination/arrival; exact transition tick differences stay open',
                               'Only R01 and R02 playable; other room links are extracted facts, not a playable completion claim',
                               'Original trap/bridge logic, cross-room enemies, modes and completion remain open'],
                  source_files=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'), sha256=sha(p))
                                for p in sources+[ROOT/p for p in (
                                    'core/game.c', 'core/room_geometry.h', 'core/game.h', 'core/combat.c', 'core/combat.h',
                                    'core/rooms.c', 'core/rooms.h', 'core/room_data.h',
                                    'tests/rooms_trace.c', 'tools/compare_rooms.py', 'test-parity.ps1')]])
    (ROOT/'reference/validation/candidate-room-routes.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    assert report['regression_gates_passed'], 'Room interaction regression'


if __name__ == '__main__':
    compare(Path(sys.argv[1]))
