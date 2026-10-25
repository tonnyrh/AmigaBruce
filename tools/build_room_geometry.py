"""Build explicitly provisional room blockouts from local candidate tiles.

This is an inspection build, not a port of the C64 pixel collision routine.
Rooms 1/2 retain their measured hand blockouts until collision work replaces
them. New rooms use tile top edges and connected net regions. No original
pixel artwork is exported into the game's own prototype renderer.
"""
import hashlib
import json
from pathlib import Path
from extract_c64_art import room_cells, tile_rows

ROOT = Path(__file__).resolve().parents[1]
NET = {0x20,0x21,0x24,0x2b,0x2c,0x3a,0x3d,0x61,0x62,0x63}


def bank_for(room):
    return 0 if room < 10 else 2 if room == 18 else 1


def geometry(memory, room):
    cells = room_cells(memory, room)
    bank = bank_for(room)
    levels = {}
    for row in range(11):
        for col in range(40):
            tile = cells[row*40+col]&127
            if tile in NET or tile in (0,2,3,4,5,0x13,0x14,0x31):
                continue
            rows = tile_rows(memory,bank,tile)
            # Broad horizontal tops only. The full C64 collision masks,
            # coloured surfaces and room loops need a later measured pass.
            first = next((i for i,v in enumerate(rows)
                          if sum(((v >> (2*j))&3)==3 for j in range(4)) >= 3), None)
            if first is None:
                continue
            y = (row+2)*16+first-10
            if not 50 <= y <= 200:
                continue
            if first == 0 and row:
                above = cells[(row-1)*40+col]&127
                if above == tile:
                    continue
            levels.setdefault(y,set()).add(col)
    platforms = []
    for y,columns in sorted(levels.items()):
        for col in sorted(columns):
            if platforms and platforms[-1][2]==y and platforms[-1][1]==col*8:
                platforms[-1][1] += 8
            else:
                platforms.append([col*8,(col+1)*8,y])
    # Static net groups. Keep each connected component as a separate region.
    remaining = {(i%40,i//40+2) for i,t in enumerate(cells) if (t&127) in NET}
    nets = []
    while remaining:
        pending = [remaining.pop()]
        group = []
        while pending:
            col,row = pending.pop(); group.append((col,row))
            for neighbour in ((col-1,row),(col+1,row),(col,row-1),(col,row+1)):
                if neighbour in remaining:
                    remaining.remove(neighbour);pending.append(neighbour)
        x0=min(c for c,r in group)*8;x1=(max(c for c,r in group)+1)*8
        y0=min(r for c,r in group)*16-8;y1=(max(r for c,r in group)+1)*16-8
        candidates=[p[2] for p in platforms if p[0]<x1 and p[1]>x0 and y0-12<=p[2]<=y0+3]
        exit_y=max(candidates) if candidates else y0
        nets.append([x0,x1,y0,min(y1,198),exit_y])
    return platforms,nets


def main():
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    memory=source.read_bytes()
    result=[]
    header=['/* Generated provisional blockouts; tools/build_room_geometry.py. */',
            '#ifndef BRUCE_ROOM_GEOMETRY_H','#define BRUCE_ROOM_GEOMETRY_H']
    for room in range(2,20):
        platforms,nets=geometry(memory,room)
        assert platforms and len(platforms)<180 and len(nets)<24,(room,len(platforms),len(nets))
        header.append('static const BlPlatform room%d_platforms[]={%s};' %
                      (room+1,','.join('{%d,%d,%d}'%tuple(p) for p in platforms)))
        header.append('static const BlClimbable room%d_climbables[]={%s};' %
                      (room+1,','.join('{%d,%d,%d,%d,%d}'%tuple(n) for n in nets) or '{0,0,0,0,0}'))
        result.append(dict(room=room+1,platforms=platforms,nets=nets,
                           status='provisional_tile_top_blockout_not_collision_parity'))
    header += ['static const BlGeometry extra_geometries[18]={']
    for room,data in enumerate(result,3):
        header.append('{room%d_platforms,room%d_climbables,%d,%d},' %
                      (room,room,len(data['platforms']),len(data['nets'])))
    header += ['};','#endif','']
    target=ROOT/'core/room_geometry.h';target.write_text('\n'.join(header),encoding='utf-8')
    report=dict(source_sha256=hashlib.sha256(memory).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                full_m4_parity=False,rooms=result)
    (ROOT/'reference/validation/room-blockouts.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for r in result:print('R%02d'%r['room'],len(r['platforms']),'platform spans',len(r['nets']),'net groups')


if __name__=='__main__':
    main()
