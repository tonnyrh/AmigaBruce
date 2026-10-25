"""Gate Ninja's naturally observed departure and return, retaining route drift."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(executable):
    path=ROOT/'reference/traces/ENEMY-EDGE-0001.json'
    capture=json.loads(path.read_text())
    assert capture['repetitions']==2
    for source in capture['sources']:
        assert sha(ROOT/source['path'])==source['sha256']
    rows=capture['scenarios']['right-wall-then-left']
    inputs=''.join(f"{r['direction']},{r['fire']}\n" for r in rows[:-1])
    output=subprocess.run([str(executable)],input=inputs,text=True,capture_output=True,check=True)
    own=[list(map(int,s.split(',')))[8:11] for s in output.stdout.splitlines()]
    native=[[r['actors'][2]['active']&1,2*r['actors'][2]['x']-24,r['actors'][2]['y']] for r in rows]
    assert len(own)==len(native)==361
    def events(sequence):
        return [[i]+v for i,v in enumerate(sequence) if i and v[0]!=sequence[i-1][0]]
    expected=[[96,1,294,98],[114,0,302,98],[274,1,294,98]]
    assert events(native)==events(own)==expected
    assert native[290]==own[290]==[1,290,98]
    assert rows[274]['actors'][2]['facing']==0
    assert rows[114]['enemy_timers'][0]==160
    differences=[dict(tick=i,c64=a,amiga=b) for i,(a,b) in enumerate(zip(native,own)) if a!=b]
    files=['reference/traces/ENEMY-EDGE-0001.json','core/game.c', 'core/room_geometry.h','core/game.h',
           'core/combat.c','core/combat.h','core/rooms.c','core/rooms.h',
           'core/room_data.h','tests/combat_trace.c','test-parity.ps1',
           'tools/compare_enemy_edges.py']
    report=dict(checks_passed=True,primary_edition_verified=False,full_enemy_parity=False,
                events=expected,return_wait_steps=160,first_left_move_after_return=290,
                differences=differences,
                limitations=['Natural right-upper exit in R01 only; other exits are table-based',
                             'C64 can halve/randomize respawn waits in other contexts; full table counter used here',
                             'Remaining geometry, navigation, injured return health and full route parity remain open'],
                source_files=[dict(path=p,sha256=sha(ROOT/p)) for p in files])
    (ROOT/'reference/validation/enemy-room-edges.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Ninja spawn96, door exit114 at302/98, return274 after160steps, first left move290; full route differences',len(differences))


if __name__=='__main__':
    compare(Path(sys.argv[1]).resolve())
