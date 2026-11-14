"""Walk Yamo past each room 11 bomb and trace who arms it in the frozen code.

Uses the shipping world loop compiled for the host (test-c64-actors.ps1
-CompileOnly). The initial placement is controlled. IRQ and VIC sampling
use the same explicit boundaries as audit_c64_world.
"""
import ctypes
import hashlib
import json
from pathlib import Path

from audit_c64_world import Bus, MPU, vic
from rip_c64_room_graphics import source_room
from verify_source_object import SHA

ROOT = Path(__file__).resolve().parents[1]
ARM = {0x3081, 0x309C, 0x30B7}


def library():
    folder = ROOT / '.tmp/source-actor-test'
    for item in json.loads((folder / 'compiled-sources.json').read_text(encoding='utf-8-sig')):
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
    lib = ctypes.CDLL(str(folder / 'actors.dll'))
    for name, count in [('world_start', 2), ('world_jump', 1), ('world_step', 2),
                        ('world_input', 2), ('test_write', 2)]:
        getattr(lib, 'bl_c64_' + name).argtypes = [ctypes.c_long] * count
    lib.bl_c64_world_ready.restype = ctypes.c_ubyte
    lib.bl_c64_fault.restype = ctypes.c_ushort
    return lib


def walk(lib, raw, col, row, direction, human):
    lib.bl_c64_reset()
    lib.bl_c64_world_start(1, int(human))
    lib.bl_c64_world_jump(10)
    # Leave room for several genuine movement steps before reaching the tile.
    start = col * 8 - 12 - direction * 32
    target = max(8, min(290, start + direction * 96))
    height = row * 16 - 4
    for addr, value in [(0x9E, (target + 24) // 2), (0xA1, 60 if human else height),
                        (0x96, 129), (0x9F, (start + 24) // 2), (0xA2, height),
                        (0xA5, int(direction > 0)), (0xD2, 20), (0xC0, 0),
                        (0xCF, 0), (0x4F4F, 72), (0x4F49, 2), (0x5D, 255)]:
        lib.bl_c64_test_write(addr, value)
    memory = (ctypes.c_ubyte * 65536)()
    lib.bl_actor_copy(memory)
    bus = Bus(memory)
    bus.ram = bytearray(memory)
    m = bus.ram
    for a, b in [(0x1BC2, 0x1C39), (0x2E39, 0x30D4), (0x3228, 0x32CC),
                 (0x3C90, 0x3CC0), (0x5212, 0x52AD)]:
        assert m[a:b] == raw[a:b], hex(a)
    regs = (ctypes.c_ubyte * 13)()
    lib.bl_c64_actor_registers(regs)
    cpu = MPU(memory=bus)
    cpu.a, cpu.x, cpu.y = regs[:3]
    cpu.sp = regs[8]
    cpu.p = 0x30 | regs[3] | regs[4] << 1 | regs[11] << 2 | regs[7] << 3 | regs[6] << 6 | regs[5] << 7
    arms, blasts = [], []
    cell = (2 * row - 1) * 40 + col
    assert m[0x8C00 + cell] == 0x60 and m[0xD800 + cell] & 7 != 5

    def run(entry, end):
        cpu.pc = entry
        for _ in range(200000):
            pc = cpu.pc
            if pc in ARM and (cpu.y, m[0xE9 + cpu.x]) == (col, row):
                arms.append((field, m[0x51], m[0xC0]))
            if pc == 0x323D and (m[0x4FE1 + cpu.x] + 1, m[0x4FE4 + cpu.x] + 1) == (col, row):
                blasts.append(field)
            cpu.step()
            if cpu.pc == end:
                return
        raise AssertionError(('escaped', hex(cpu.pc), col, row, direction))

    def compare(stage):
        lib.bl_actor_copy(memory)
        assert not lib.bl_c64_fault()
        if m != bytes(memory):
            diffs = [(hex(i), a, b) for i, (a, b) in enumerate(zip(m, memory)) if a != b]
            raise AssertionError((stage, field, col, row, direction, diffs[:12]))

    hinput = (2 if direction > 0 else 1) if human else 0
    for field in range(180):
        lib.bl_c64_world_input(0, hinput)
        saved = (cpu.a, cpu.x, cpu.y, cpu.p, cpu.sp)
        m[0x44] = 0
        cpu.p &= ~8
        run(0x15B8, 0x169D)
        # Run the source joystick slot as the game does. In two-stick mode
        # it also pushes status on the stack before reading the second port.
        other = 31
        if human:
            other ^= 8 if direction > 0 else 4
        m[0xDC00], m[0xDC01] = (31, other) if m[3] else (other, 31)
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
            run(0x1BC2, 0x1C32)
            lib.bl_c64_world_step(0, 0)
            compare('game')
        if arms and field == arms[0][0]:
            assert m[0xD800 + cell] == 0xFD, 'Arming did not change bomb colour'
        if blasts:
            area = [m[0x8C00 + (2 * row - 3 + dy) * 40 + col - 1 + dx] & 127
                    for dy in range(4) for dx in range(3)]
            assert any(0x71 <= code <= 0x7C for code in area), 'Missing blast characters'
            break
    assert len(arms) == len(blasts) == 1, (col, row, direction, arms, blasts)
    arm_field, actor, state = arms[0]
    assert actor == 1 and state in (3, 4, 20, 21), (col, row, direction, arms)
    assert blasts[0] - arm_field == 24, (col, row, direction, arms, blasts)
    return arm_field, state, blasts[0]


def main():
    raw = (ROOT / '.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA
    room = source_room(raw, 10)
    bombs = [(i % 40, (i // 40 + 1) // 2) for i, code in enumerate(room[0x8C00:0x8C00 + 1000]) if code == 0x60]
    assert len(bombs) == 7
    # $30CA changes only the upper character's attribute. Only multicolour
    # pixel pairs 11 use it. Room 11's $60 does not contain that pair.
    assert room[0xF2] == 0x3A
    glyph = room[0xA800 + 0x60 * 8:0xA800 + 0x61 * 8]
    assert all((bits >> shift) & 3 != 3 for bits in glyph for shift in (6, 4, 2, 0))
    lib = library()
    print('control col row direction arm_field yamo_state blast_field')
    for human in (True, False):
        for col, row in bombs:
            for direction in (1, -1):
                result = walk(lib, raw, col, row, direction, human)
                print('joystick' if human else 'AI', col, row, direction, *result)
    print('PASS all seven bombs in both directions with joystick and AI, including detonation.')


if __name__ == '__main__':
    main()
