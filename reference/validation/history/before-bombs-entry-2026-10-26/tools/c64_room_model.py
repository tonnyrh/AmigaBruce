"""Read-only C64 candidate room reconstruction, independent of Amiga blockouts.

Coordinates are the C64's320x200 active display, not raster coordinates.
Original pixels and maps belong in .reference only. No game files are written.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.reference/tools/python'))


def word(memory, address):
    return memory[address] | memory[address + 1] << 8


def decode(memory, room):
    start = memory[0x4b34 + room] | memory[0x4b49 + room] << 8
    cursor, cells = start, []
    while memory[cursor] != 128:
        count = memory[cursor]
        cursor += 1
        assert count & 127
        if count & 128:
            cells.extend(memory[cursor:cursor + (count & 127)])
            cursor += count & 127
        else:
            cells.extend([memory[cursor]] * count)
            cursor += 1
        assert len(cells) <= 442
    assert 440 <= len(cells) <= 442
    default = memory[0x47a0 + room] & 15
    bank = 0 if room < 10 else 2 if room == 18 else 1
    return dict(room=room + 1, start=start, end=cursor + 1, bank=bank,
                charset=(0xa000, 0xa800, 0xb000)[bank], default_color=default,
                cells=cells[:440], tail=cells[440:])


def room_memory(initial, room, stack_pointer=None):
    """Execute the actual loader through end of RLE; no init/IRQ/hardware claims."""
    from py65.devices.mpu6502 import MPU
    memory = list(initial)
    memory[0x29] = room
    # Loader $09DA-$09EF pre-fills this exact color RAM range.
    for base in (0xd878, 0xd900, 0xda00, 0xdb00):
        memory[base:base + 256] = [memory[0x47a0 + room]] * 256
    cpu = MPU(memory=memory, pc=0x0a9b)
    if stack_pointer is not None:cpu.sp=stack_pointer
    for instructions in range(100000):
        if cpu.pc == 0x0b30:
            return memory, instructions
        cpu.step()
    raise RuntimeError(f'Room{room+1}: loader escaped, PC=${cpu.pc:04X}')


def validate_loader(initial, room):
    model = decode(initial, room)
    memory, instructions = room_memory(initial, room)
    for index, raw in enumerate(model['cells'] + model['tail']):
        row, col = divmod(index, 40)
        top = 0x8c78 + row * 80 + col
        bottom = top + 40
        assert memory[top] == raw & 127
        assert memory[bottom] == (raw & 127) | 128
        for address in (top + 0x4c00, bottom + 0x4c00):
            if raw & 128:
                assert memory[address] & 15 == 8
            elif index < 440:
                assert memory[address] & 15 == model['default_color']
    assert memory[0xf2] == (0x38, 0x3a, 0x3c)[model['bank']]
    # Execute only the IRQ's pure charset selection block, not its timers.
    from py65.devices.mpu6502 import MPU
    cpu = MPU(memory=memory, pc=0x15d0)
    for _ in range(20):
        if cpu.pc == 0x15ee:
            break
        cpu.step()
    assert cpu.pc == 0x15ee and memory[0x7c] == model['charset'] >> 8
    model['loader_instructions'] = instructions
    return model, memory


def pixels(memory, model):
    """Exact glyph plane and per-pixel contact classes, before room init/loops."""
    glyphs, flags, colors = bytearray(320 * 200), bytearray(320 * 200), bytearray(320 * 200)
    for index, raw in enumerate(model['cells']):
        row, col = divmod(index, 40)
        color = 8 if raw & 128 else model['default_color']
        tile = raw & 127
        for dy in range(16):
            code = tile if dy < 8 else tile | 128
            bits = memory[model['charset'] + code * 8 + (dy & 7)]
            y = 24 + row * 16 + dy
            for pair in range(4):
                value = (bits >> (6 - pair * 2)) & 3
                flag = (0, 1, 2, 8 if color & 7 == 0 else 4)[value]
                address = y * 320 + col * 8 + pair * 2
                glyphs[address:address + 2] = bytes([value]) * 2
                flags[address:address + 2] = bytes([flag]) * 2
                colors[address:address + 2] = bytes([color]) * 2
    return glyphs, flags, colors


def oracle_contact(initial, x, y, pose=2):
    """Actual6502 $5212 for one actor. x is sprite-left; y is bottom+1."""
    from py65.devices.mpu6502 import MPU
    assert x % 2 == 0 and 0 <= x <= 302
    memory = list(initial)
    memory[0x95:0x98] = [1, 0, 0]
    memory[0x9e] = (x + 24) // 2
    memory[0xa1] = y
    memory[0x4f4e] = pose
    cpu = MPU(memory=memory, pc=0x5212)
    for _ in range(20000):
        if cpu.pc == 0x52ac:
            return memory[0xb6], memory[0xa7]
        cpu.step()
    raise RuntimeError(f'Contact kernel did not return: ${cpu.pc:04x}')


def model_contact(memory, flags, x, y, pose=2):
    pointer = memory[0x1167 + pose] | memory[0x1239 + pose] << 8
    all_flags = body_flags = 0
    for row in range(21):
        yy = y - 21 + row
        if not 0 <= yy < 200:
            continue
        for col in range(3):
            bits = memory[pointer + col * 32 + row]
            for pair in range(4):
                opaque = (bits >> (6 - pair * 2)) & 3
                xx = x + col * 8 + pair * 2
                if opaque and 0 <= xx < 320:
                    background = flags[yy * 320 + xx]
                    code = 3 if background in (4, 8) else background
                    # The original ANDs bitplanes, including partial pairs.
                    # Some442-cell streams write through the visible matrix
                    # into bytes also reached by the source mask0 fixture.
                    hit = code & opaque
                    flag = (0, 1, 2, 8 if background == 8 else 4)[hit]
                    all_flags |= flag
                    if row < 15:
                        body_flags |= flag
    return all_flags, body_flags


def uniform_probes(initial):
    results = []
    for color in (8, 14, 12, 9, 15):
        for value in range(4):
            memory = list(initial)
            memory[0x8c00:0x8fe8] = [6] * 1000
            memory[0xd800:0xdbe8] = [color] * 1000
            memory[0xa030:0xa038] = [value * 85] * 8
            memory[0x7c] = 0xa0
            result = oracle_contact(memory, 160, 100)
            expected = (0, 1, 2, 8 if color & 7 == 0 else 4)[value]
            assert result == (expected, expected), (color, value, result)
            results.append(dict(color=color, pixel_code=value, flags=result[0], body_flags=result[1]))
    return results
