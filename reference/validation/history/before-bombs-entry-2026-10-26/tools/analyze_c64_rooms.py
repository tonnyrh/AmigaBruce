"""Extract room facts from the frozen candidate, never from editor defaults.

Exports semantic coordinates and links only; no character art or 6502 code.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract():
    source = ROOT/'.reference/c64/work/untrained-memory.bin'
    mem = source.read_bytes()
    assert len(mem) == 65536
    rooms = []
    for room in range(20):
        start = mem[0x4b34+room]+256*mem[0x4b49+room]
        ptr = start
        cells = []
        while mem[ptr] != 0x80:
            count = mem[ptr]
            ptr += 1
            if count & 128:
                count &= 127
                cells.extend(mem[ptr:ptr+count])
                ptr += count
            else:
                assert count
                cells.extend([mem[ptr]]*count)
                ptr += 1
            assert len(cells) <= 480
        assert 440 <= len(cells) <= 442
        lp = mem[0x4ce2+room*2]+256*mem[0x4ce3+room*2]
        lanterns = []
        while mem[lp] < 128:
            record = list(mem[lp:lp+4])
            if record[1] != 0:  # Two rooms carry a dummy record.
                lanterns.append(dict(column=record[2], row=record[3]))
            lp += 4
            assert len(lanterns) <= 13
        assert len(lanterns) == mem[0x4cce+room]
        assert [a['row'] for a in lanterns] == sorted(a['row'] for a in lanterns)
        doors = []
        for door in range(2, 6):
            slot = door-2
            positions = [dict(column=i % 40, row=i//40+2)
                         for i, tile in enumerate(cells[:440]) if tile & 127 == door]
            x = mem[0x4bfe+slot*40+room]
            y = mem[0x4c12+slot*40+room]
            target = mem[0x4b5e+slot*20+room]
            assert target < 20
            doors.append(dict(id=door, target=target, entry_x=2*x-24,
                              entry_y=y, valid=bool(x and y and positions), cells=positions))
        rooms.append(dict(index=room, room_id=f'R{room+1:02}',
                          packed_address=hex(start), packed_bytes=ptr-start+1,
                          decoded_cells=len(cells), lanterns=lanterns, doors=doors,
                          entry_x=2*mem[0x4bae+room]-24, entry_y=mem[0x4bc2+room],
                          enemy_x=2*mem[0x4bd6+room]-24, enemy_y=mem[0x4bea+room],
                          enemies_enabled=mem[0x4c9e+room] == 0,
                          enemy_exit_wait=[mem[0x135b+room],mem[0x131f+room]],
                          init_address=hex(mem[0x4e9c+room*2]+256*mem[0x4e9d+room*2]),
                          loop_address=hex(mem[0x4ec4+room*2]+256*mem[0x4ec5+room*2])))
    report = dict(checks_passed=True, primary_edition_verified=False,
                  full_m4_parity=False, rooms=rooms,
                  limits=['Static table extraction does not certify reachable exits or room-specific gates',
                          'Editor defaults differ and are not used as original room links',
                          'Original init/loop code, traps, gates and completion require native measurements'],
                  source_files=[dict(path=str(p.relative_to(ROOT)).replace('\\', '/'), sha256=sha(p))
                                for p in (source, Path(__file__).resolve())])
    (ROOT/'reference/validation/candidate-rooms.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    header = ['/* Generated semantic facts; python tools/analyze_c64_rooms.py. */',
              '#ifndef BRUCE_ROOM_DATA_H', '#define BRUCE_ROOM_DATA_H',
              'static const BlRoomFacts bl_room_facts[20]={']
    for r in rooms:
        lamps = ','.join('{%d,%d}' % (a['column'], a['row']) for a in r['lanterns']) or '{0,0}'
        ds = []
        for d in r['doors']:
            cell = d['cells'][0] if d['cells'] else dict(column=0, row=0)
            ds.append('{%d,%d,%d,%d,%d,%d}' % (d['target'], d['entry_x'], d['entry_y'],
                                              cell['column'], cell['row'], d['valid']))
        header.append(' {%d,%d,%d,%d,%d,%d,{%s},{%s},{%d,%d}},' % (
            r['entry_x'], r['entry_y'], r['enemy_x'], r['enemy_y'],
            r['enemies_enabled'], len(r['lanterns']), lamps, ','.join(ds),
            r['enemy_exit_wait'][0],r['enemy_exit_wait'][1]))
    header += ['};', '#endif', '']
    (ROOT/'core/room_data.h').write_text('\n'.join(header), encoding='utf-8')
    report['generated_header_sha256']=sha(ROOT/'core/room_data.h')
    (ROOT/'reference/validation/candidate-rooms.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PASS: 20 candidate room streams, lantern counts and four-link tables; semantic header generated')


if __name__ == '__main__':
    extract()
