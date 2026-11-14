"""Verify the explicitly enabled Amiga bomb margin, not C64 parity.

Run test-c64-actors.ps1 -CompileOnly first. Pixel expectations use a separate
set-of-points calculation on frozen source masks and live charge glyphs.
"""
import ctypes
import hashlib
import json

from audit_r11_yamo_walk import ROOT, SHA, library


def main():
    raw = (ROOT / '.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    lib = library()
    lib.bl_c64_set_bomb_contact_margin.argtypes = [ctypes.c_long]
    lib.bl_c64_actor_test_call.argtypes = [ctypes.c_long, ctypes.c_long]
    buf = (ctypes.c_ubyte * 65536)()

    def memory():
        lib.bl_actor_copy(buf)
        return bytes(buf)

    def put(at, value):
        lib.bl_c64_test_write(at, value)

    cases = hits = extended = 0
    for room in (7, 10):
        lib.bl_c64_world_start(1, 0)
        lib.bl_c64_world_jump(room)
        lib.bl_c64_set_bomb_contact_margin(1)
        m = memory()
        # Room 11's reported middle charge; a central gallery charge in room 8.
        cell = 17 * 40 + 21 if room == 10 else next(i for i in range(120,1000) if m[0x8c00+i] == 0x60)
        col, row = cell % 40, (cell // 40 + 1) // 2
        bank = 0xa800 if room == 10 else 0xa000
        pixels = set()
        for yy in range(16):
            glyph = m[0x8c00 + cell + (40 if yy >= 8 else 0)]
            bits = m[bank + glyph*8 + yy%8]
            for xx in range(8):
                if (bits >> (6-(xx//2)*2)) & 3 == 2:
                    pixels.add((col*8+xx, row*16-8+yy))
        expanded = {(x+dx,y+dy) for x,y in pixels for dx in (-1,0,1) for dy in (-1,0)}
        assert pixels
        for actor in range(3):
            for i in range(3):
                put(0x95+i, int(i==actor))
                put(0xbf+i, 0)
                put(0xb6+i, 0)  # Exercise only the supplemental contact path.
            for pose in (2,14,16,36,40,68):
                pose += actor*70
                ptr = m[0x1167+pose] | m[0x1239+pose]<<8
                shape = {(xx,yy) for yy in range(21) for xx in range(24)
                         if m[ptr+(xx//8)*32+yy] & (128>>(xx%8))}
                put(0x4f4e+actor, pose)
                for dx in range(-24,12,2):
                    px = col*8+dx
                    if px < 0:
                        continue
                    for dy in (-2,-1,0,1,2,3,4,5,6,8,12,24,36):
                        py = row*16-8+dy
                        wanted = bool({(x+px,y+py-21) for x,y in shape} & expanded)
                        exact = bool({(x+px,y+py-21) for x,y in shape} & pixels)
                        put(0x9e+actor, (px+24)//2)
                        put(0xa1+actor, py)
                        for i in range(3): put(0x4fde+i, 0)
                        put(0xd800+cell, m[0xd800+cell])
                        lib.bl_c64_actor_test_call(0x2e39, actor)
                        got = memory()
                        assert not lib.bl_c64_fault()
                        armed = any(got[0x4fde+i] and got[0x4fe1+i]==col-1 and got[0x4fe4+i]==row-1 for i in range(3))
                        assert armed == wanted, (room+1, actor, pose, px, py, armed, wanted)
                        cases += 1
                        hits += armed
                        extended += wanted and not exact

    # Recreate the previously missed leftward walks with ordinary input.
    walks = []
    for room in (10,11,12,14,16):
        lib.bl_c64_world_start(1,0)
        lib.bl_c64_world_jump(room)
        m = memory()
        bombs = [(i%40,(i//40+1)//2) for i in range(120,1000) if m[0x8c00+i]==0x60]
        for col,row in bombs:
            for height in (row*16-5,row*16-4):
                lib.bl_c64_world_start(1,0)
                lib.bl_c64_world_jump(room)
                lib.bl_c64_set_bomb_contact_margin(1)
                for at,value in ((0x95,1),(0x96,0),(0x97,0),(0x5d,255),(0x5e,255),
                                 (0x9e,(col*8+20+24)//2),(0xa1,height),(0xa4,0),
                                 (0xbf,0),(0xce,0),(0x4f4e,2),(0x4f48,2)):
                    put(at,value)
                for field in range(90):
                    lib.bl_c64_world_input(1,0)
                    lib.bl_c64_field()
                    if lib.bl_c64_world_ready(): lib.bl_c64_world_step(0,0)
                    got=memory()
                    assert not lib.bl_c64_fault() and got[0x29]==room
                    if any(got[0x4fde+i] and got[0x4fe1+i]==col-1 and got[0x4fe4+i]==row-1 for i in range(3)):
                        walks.append(dict(room=room+1,column=col,row=row,height=height,armed_field=field))
                        break
                else:
                    raise AssertionError(('Walk missed',room,col,row,height))

    # Capacity, repeated contact, inactive and dying actors retain their limits.
    guards=[]
    for actor in range(3):
        for kind in ('active','inactive','dying','all_slots_busy','disabled'):
            lib.bl_c64_world_start(1,0)
            lib.bl_c64_world_jump(10)
            lib.bl_c64_set_bomb_contact_margin(kind!='disabled')
            for i in range(3):
                put(0x95+i,int(i==actor and kind!='inactive'))
                put(0xbf+i,25 if i==actor and kind=='dying' else 0)
                put(0xb6+i,0)
                put(0x4fde+i,1 if kind=='all_slots_busy' else 0)
            for at,value in ((0x9e+actor,96),(0xa1+actor,139),(0x4f4e+actor,14+70*actor)):
                put(at,value)
            before=memory()
            lib.bl_c64_actor_test_call(0x2e39,actor)
            got=memory()
            armed=got[0xd800+17*40+21]==0xfd
            assert armed==(kind=='active'),(actor,kind)
            if kind=='all_slots_busy': assert got[0x4fde:0x4fe7]==before[0x4fde:0x4fe7]
            if armed:
                lib.bl_c64_actor_test_call(0x2e39,actor)
                assert memory()[0x4fde:0x4fe7]==got[0x4fde:0x4fe7]
            guards.append(dict(actor=actor,case=kind,armed=armed))
    out=ROOT/'reference/analysis/bomb-margin-2026-11-09'
    out.mkdir(parents=True,exist_ok=True)
    report=dict(source_sha256=SHA,edition_verified=False,deliberate_amiga_rule=True,
                margin=dict(up=1,left=1,right=1,down=0),pixel_cases=cases,pixel_hits=hits,
                expanded_only_hits=extended,walks=walks,guards=guards,
                method='Injected starts; independent pixel-set oracle; host engine with the production bomb margin enabled. Not a natural C64 playthrough.',
                host_sources=json.loads((ROOT/'.tmp/source-actor-test/compiled-sources.json').read_text(encoding='utf-8-sig')))
    (out/'host.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',cases,'pixel cases;',extended,'expanded-only hits;',len(walks),'walks;',len(guards),'lifetime/capacity controls.')


if __name__=='__main__':
    main()
