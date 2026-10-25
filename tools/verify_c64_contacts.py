"""Actual frozen 6502 object pass vs native integration, with injected states.

The original code selects the pose, computes pixels, scans cells and records
pickups. Stop at its transition boundary, before IRQ takeover/stack reset.
No natural gameplay, VIC timing or pristine 1984 identity is claimed.
"""
from pathlib import Path
import ctypes
import hashlib
import json
from datetime import date
from c64_room_model import oracle_contact, word
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

ROOT = Path(__file__).resolve().parents[1]


def run(memory, entry, stops=(0xffff,), trace=None):
    cpu = MPU(memory=memory, pc=entry)
    cpu.sp = 0xfd
    memory[0x1fe:0x200] = [0xfe, 0xff]
    for _ in range(100000):
        if cpu.pc in stops:
            return cpu
        if trace is not None:
            trace(cpu)
        cpu.step()
    raise AssertionError(f'Original ${entry:04X} escaped at ${cpu.pc:04X}')


def verify_objects(native, source):
    native.bl_contact_fixture_count.restype = ctypes.c_long
    native.bl_contact_fixture_value.argtypes = [ctypes.c_long, ctypes.c_long]
    native.bl_contact_fixture_value.restype = ctypes.c_long
    native.bl_contact_prepare.argtypes = [ctypes.c_long]
    native.bl_contact_result.argtypes = [ctypes.c_long]
    native.bl_contact_result.restype = ctypes.c_long
    cases = []
    for index in range(native.bl_contact_fixture_count()):
        values = [native.bl_contact_fixture_value(index, f) for f in range(10)]
        room, px, py, dx, action, facing = values[:6]
        native.bl_contact_prepare(index)
        memory = [native.bl_c64_read(i) for i in range(65536)]
        # Restore instructions absent from the native data-only shadow.
        memory[0x500:0x4300] = source[0x500:0x4300]
        memory[0x5000:0x5800] = source[0x5000:0x5800]
        memory[0x95:0x98] = [1, 0, 0]
        memory[0x9e], memory[0xa1] = (px + 24) // 2, py
        memory[0xa4] = facing
        memory[0xbf] = (0, 17, 26)[action]
        memory[0x4fdb] = 0
        memory[0xb6] = 0
        memory[0x7c] = {0x38: 0xa0, 0x3a: 0xa8, 0x3c: 0xb0}[memory[0xf2]]
        memory[0x4f57] = 0
        memory[0x4f5d], memory[0x4f60] = int(dx < 0), int(dx > 0)
        run(memory, 0x2780)  # Real pose selection, no native-pose oracle.
        pose = memory[0x4f4e]
        assert pose == native.bl_contact_result(5), (index, 'pose')
        run(memory, 0x5212, (0x52ac,))
        flags = memory[0xb6]
        lamps_before = memory[0x2a + room]
        sound, score = [], []

        def trace(cpu):
            if cpu.pc == 0x2509:
                sound.append(cpu.y)
            if cpu.pc == 0x3175:
                score.append(cpu.a)

        cpu = run(memory, 0x2e39, (0xffff, 0x2f8e, 0x407d), trace)
        assert cpu.pc != 0x407d, (index, 'unexpected source death')
        transition = cpu.pc == 0x2f8e
        target = [memory[0x4e], cpu.a * 2 - 24, cpu.y] if transition else [room, px, py]
        pickups = lamps_before - memory[0x2a + room]
        expected = target + [pickups, sum(score)]
        assert expected == values[6:] + [values[9] * 125], (index, 'fixture disagrees with source', expected, values)
        native.bl_contact_run()
        actual = [native.bl_contact_result(f) for f in range(5)]
        assert actual == expected, (index, actual, expected)
        assert bool(native.bl_contact_result(6) & 16384) == (0x8e in sound), (index, 'pickup sound')
        if not transition:
            for lo, hi in ((0x2a, 0x3e), (0x4d0a, 0x4e97), (0x8c78, 0x8fe8),
                           (0xeb00, 0xeb03), (0xef70, 0xef73), (0xf070, 0xf073)):
                for address in range(lo, hi):
                    assert native.bl_c64_read(address) == memory[address], (index, hex(address), 'lamp/cell/audio state')
            if pickups:
                # A second contact must not score/play a second pickup.
                native.bl_contact_run()
                assert [native.bl_contact_result(f) for f in (3, 4)] == [pickups, 125 * pickups]
        cases.append(dict(case=index + 1, room=room + 1, x=px, y=py,
                          movement_x=dx, source_state=memory[0xbf], facing=facing,
                          source_pose=pose, contact=flags, transition=transition,
                          result=expected, sound_requests=sound))
    assert native.bl_contact_result(7) == 0, 'C/68000 shared fixture expectations'
    dest = ROOT / 'reference/analysis/contact-audit-2026-10-25'
    dest.mkdir(parents=True, exist_ok=True)
    dis = Disassembler(MPU(memory=list(source)))
    lines = []
    ranges = [(0x1c0a, 0x1c5b), (0x27a6, 0x27b8), (0x282f, 0x2841),
              (0x2996, 0x29c3), (0x2e39, 0x2f9a), (0x30d4, 0x310c),
              (0x330e, 0x336e), (0x5212, 0x52ac)]
    for lo, hi in ranges:
        pc = lo
        while pc < hi:
            length, text = dis.instruction_at(pc)
            lines.append(f'{pc:04X} {source[pc:pc+length].hex(" "):<9} {text}')
            pc += length
    (dest / 'source-disassembly.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    report = dict(date=str(date.today()), status='passed_original_cpu_vs_native_object_pass',
                  source_sha256=hashlib.sha256(source).hexdigest(), cases=cases,
                  edition_verified=False, natural_playthrough=False,
                  source_order=['$2780 pose', '$5212 pixel contact', '$2E39 objects', '$2F8E transition boundary'],
                  limitations=['Actor states, coordinates and direction latches are injected',
                               'Only constant idle/punch/prone poses integrated in this change',
                               'Walk/jump/climb/reaction pose timing and full movement history remain open'])
    (dest / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    # The room wrapper records every compiled source, including this verifier.
    identity = json.loads((ROOT/'.tmp/c64-room-test/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for item in identity:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
    dll = ctypes.CDLL(str(ROOT/'.tmp/c64-room-test/rooms.dll'))
    dll.bl_c64_read.restype = ctypes.c_ubyte
    report = verify_objects(dll, (ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes())
    print(f"PASS {len(report['cases'])} actual 6502 object passes vs native progression")
