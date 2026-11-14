"""Compare walking bomb contacts with the frozen C64 instructions.

Run test-c64-actors.ps1 -CompileOnly first. Starting positions are controlled.
All timers start free, both enemies are disabled, and Bruce uses normal input.
This is not a natural C64 playthrough or a raster-exact hardware test.
"""
import ctypes
import hashlib
import json
from pathlib import Path

from audit_c64_world import Bus, MPU, vic
from audit_r11_yamo_walk import ARM, ROOT, SHA, library
from rip_c64_room_graphics import source_room


def walk(lib, raw, room, col, row, offset, direction=-1):
    lib.bl_c64_reset()
    lib.bl_c64_world_start(1, 0)
    lib.bl_c64_world_jump(room)
    start = col * 8 - 12 - direction * 32
    height = row * 16 + offset
    for addr, value in [(0x95, 1), (0x96, 0), (0x97, 0), (0x5D, 255), (0x5E, 255),
                        (0x9E, (start + 24) // 2), (0xA1, height),
                        (0xA4, int(direction > 0)), (0xBF, 0), (0xCE, 0),
                        (0x4F4E, 2), (0x4F48, 2)]:
        lib.bl_c64_test_write(addr, value)
    memory = (ctypes.c_ubyte * 65536)()
    lib.bl_actor_copy(memory)
    bus = Bus(memory)
    bus.ram = bytearray(memory)
    m = bus.ram
    assert not any(m[0x4FDE:0x4FE1])
    for a, b in [(0x1BC2, 0x1C5B), (0x2E39, 0x30D4), (0x3228, 0x32CC),
                 (0x5212, 0x52AD)]:
        assert m[a:b] == raw[a:b], hex(a)
    regs = (ctypes.c_ubyte * 13)()
    lib.bl_c64_actor_registers(regs)
    cpu = MPU(memory=bus)
    cpu.a, cpu.x, cpu.y = regs[:3]
    cpu.sp = regs[8]
    cpu.p = (0x30 | regs[3] | regs[4] << 1 | regs[11] << 2 | regs[7] << 3 |
             regs[6] << 6 | regs[5] << 7)
    arms, blasts, trace = [], [], []
    instructions = boundaries = 0
    scanned = []
    cell = (2 * row - 1) * 40 + col
    assert m[0x8C00 + cell] == 0x60 and m[0xD800 + cell] & 7 != 5

    def run(entry, end):
        nonlocal instructions
        cpu.pc = entry
        for _ in range(200000):
            pc = cpu.pc
            if pc == 0x2E7C and m[0x51] == 0:
                scanned.append((m[0xE9], cpu.y))
            if pc in ARM and (cpu.y, m[0xE9 + cpu.x]) == (col, row):
                arms.append(dict(field=field, actor=m[0x51], state=m[0xBF]))
            if pc == 0x323D and (m[0x4FE1 + cpu.x] + 1, m[0x4FE4 + cpu.x] + 1) == (col, row):
                blasts.append(field)
            cpu.step()
            instructions += 1
            if cpu.pc == end:
                return
        raise AssertionError(('source escaped', hex(cpu.pc), room, col, row, direction))

    def compare(stage):
        nonlocal boundaries
        lib.bl_actor_copy(memory)
        assert not lib.bl_c64_fault()
        if m != bytes(memory):
            diffs = [(hex(i), a, b) for i, (a, b) in enumerate(zip(m, memory)) if a != b]
            raise AssertionError((stage, field, room, col, row, direction, diffs[:12]))
        boundaries += 1

    input_ = 2 if direction > 0 else 1
    for field in range(180):
        lib.bl_c64_world_input(input_, 0)
        saved = (cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp)
        m[0x44] = 0
        cpu.p &= ~8
        run(0x15B8, 0x169D)
        pins = 31 ^ (8 if direction > 0 else 4)
        m[0xDC00], m[0xDC01] = (pins, 31) if m[3] else (31, pins)
        run(0x169D, 0x1703)
        m[0xDC00] = m[0xDC01] = 255
        run(0x1703, 0x179D)
        m[0xD01E] |= vic(m)
        cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp = saved
        lib.bl_c64_field()
        compare('IRQ')
        assert bool(lib.bl_c64_world_ready()) == (m[0x48] == 0)
        if not m[0x48]:
            cpu.a, cpu.p = 0, (cpu.p & ~0x80) | 2
            scanned.clear()
            run(0x1BC2, 0x1C32)
            lib.bl_c64_world_step(0, 0)
            compare('game')
            assert m[0x29] == room, 'Control left the requested room'
            trace.append(dict(field=field, x=m[0x9E] * 2 - 24, y=m[0xA1],
                              state=m[0xBF], pose=m[0x4F4E], contact=m[0xB6],
                              scanned_rows=sorted({r for r, c in scanned}),
                              target_scanned=(row, col) in scanned,
                              timers=list(m[0x4FDE:0x4FE1])))
        if not arms and trace:
            if ((direction < 0 and trace[-1]['x'] < col * 8 - 40) or
                    (direction > 0 and trace[-1]['x'] > col * 8 + 24)):
                break
        if arms and field == arms[0]['field']:
            assert m[0xD800 + cell] == 0xFD
        if blasts:
            assert len(arms) == len(blasts) == 1 and arms[0]['actor'] == 0
            assert blasts[0] - arms[0]['field'] == 24
            break
    else:
        raise AssertionError(('control did not finish', room, col, row, offset, direction))
    return dict(room=room + 1, column=col, object_row=row, initial_y=height,
                direction=direction, arms=arms, blasts=blasts, trace=trace,
                original_instructions=instructions, full_ram_comparisons=boundaries)


def main():
    raw = (ROOT / '.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    lib = library()
    checks = []
    for room in (10, 11, 12, 14, 16):
        m = source_room(raw, room)
        bombs = [(i % 40, (i // 40 + 1) // 2)
                 for i, code in enumerate(m[0x8C00:0x8FE8]) if code == 0x60]
        for col, row in bombs:
            for offset in (-5, -4):
                result = walk(lib, raw, room, col, row, offset)
                assert bool(result['arms']) == (offset == -4), (room, col, row, offset)
                checks.append(result)
        print('Room', room + 1, 'verified', len(bombs), 'paired height controls.')
    out = ROOT / 'reference/analysis/bomb-contact-2026-11-09'
    out.mkdir(parents=True, exist_ok=True)
    report = dict(source_sha256=SHA, edition_verified=False,
                  method='Controlled starts; actual 6502 instructions versus host game engine; all RAM compared after every modeled field and main step.',
                  natural_playthrough=False, raster_exact=False, checks=checks,
                  host_sources=json.loads((ROOT / '.tmp/source-actor-test/compiled-sources.json').read_text(encoding='utf-8-sig')))
    (out / 'source-walks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', len(checks), 'walks;', sum(r['full_ram_comparisons'] for r in checks),
          'full-RAM comparisons;', sum(r['original_instructions'] for r in checks), 'original instructions.')


if __name__ == '__main__':
    main()
