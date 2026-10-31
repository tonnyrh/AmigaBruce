"""Interleave original combat and source-selected IRQs at explicit test times."""
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / ".tmp/op4-owner"
sys.path.insert(0, str(HERE.parent / "op4-moving-audio-2026-10-31"))
from irq import IrqBus, frames, mpu, regs, sha
from py65.disassembler import Disassembler
from py65.devices.mpu6502 import MPU
from audit_c64_irq_contract import decode
from audit_c64_world import vic

def fixture():
    frozen = (ROOT / ".reference/c64/work/untrained-memory.bin").read_bytes()
    assert sha(frozen) == "092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    disassembler = Disassembler(MPU(memory=frozen))
    instructions = {}
    def check_instruction(ram, cpu):
        pc = cpu.pc
        if pc in (0xeb38,0xefa8,0xf0a8):
            # STA patches the BCC displacement four bytes earlier in each
            # SID stream. Validate both the opcode and its source-table value.
            assert ram[pc] == frozen[pc] == 0x90 and ram[pc+1] == frozen[0xec03+cpu.x]
            return
        if pc not in instructions:
            length, _ = disassembler.instruction_at(pc)
            instructions[pc] = frozen[pc:pc+length]
        expected = instructions[pc]
        assert ram[pc:pc+len(expected)] == expected, f"source instruction at ${pc:04X}"
    data = bytearray(struct.pack(">I", 2))
    results = []
    for idx, name in enumerate(("combat168", "combat207")):
        local = ROOT / ".reference/c64/work/op4-moving-audio-2026-10-31" / name / "combat.bin"
        capture = local.read_bytes()
        (_, initial_regs, initial_ram), _ = frames(capture)
        # The second controlled fixture exercises the physical port swap and human Yamo.
        if idx:
            initial_ram[3] = initial_ram[0x42ca] = initial_ram[0x1384] = 1
            initial_ram[0x1383] = 0
        bus = IrqBus(initial_ram, (31, 31), 0)
        cpu = mpu(bus, 0x29c3, initial_regs)
        field, previous_line, games, visits = 0xfffffe, 0, 0, 0
        published = bytes(26)
        events, payload = [], bytearray()
        for _ in range(150000):
            if cpu.pc == 0x1c26:
                break
            check_instruction(bus.ram,cpu)
            if cpu.pc == 0x2b4e:
                bus.ram[0xbc] &= 1  # Same enabled invincibility as the private route.
            if cpu.pc == 0x2c51:
                visits += 1
                if games < 3 and visits % 2:
                    assert cpu.x == 2 and bus.ram[0xbe] & 16 and bus.ram[0xd3] >= 133
                    before = regs(cpu)
                    assert not before[9] and not before[7]
                    vector = int.from_bytes(bus.ram[0x408:0x40a], "little")
                    line = bus.ram[0xd012] + 2 * (bus.ram[0xd011] & 128)
                    if line <= previous_line:
                        field = (field + 1) & 0xffffff
                    previous_line = line
                    bus.pins = ((31, 23), (15, 27), (30, 29))[games % 3]
                    bus.raster = (line + 3) & 255  # Source band wait has expired.
                    bus.gates = 0
                    cpu.irq()
                    assert cpu.pc == 0x1103
                    seen = []
                    for _ in range(50000):
                        seen.append(cpu.pc)
                        check_instruction(bus.ram,cpu)
                        cpu.step()
                        if cpu.pc == 0x2c51:
                            break
                    assert vector in seen and cpu.pc == 0x2c51 and regs(cpu) == before
                    if vector == 0x48c1:
                        order = [seen.index(pc) for pc in (0xeb03,0xef73,0xf073,0x15b8,0x169d,0x1703)]
                        assert order == sorted(order)
                        games += 1
                        published = bytes(bus.ram[0xd400:0xd419]) + bytes([bus.gates])
                        bus.ram[0xd01e] |= vic(bus.ram)  # Separate emulated VIC seam.
                    else:
                        assert vector in (0x491e, 0x4982) and not bus.gates
                    p0, p1 = map(decode, bus.pins)
                    bruce, yamo = (p0, p1) if bus.ram[3] else (p1, p0)
                    payload += struct.pack(">BIHHBB", visits, field, line, vector, bruce, yamo)
                    payload += before + published + bus.ram
                    events.append(dict(visit=visits, field=field, line=line, vector=f"{vector:04x}",
                                       pins=bus.pins, ram=sha(bus.ram), sid=published.hex()))
            cpu.step()
        assert cpu.pc == 0x1c26 and games == 3 and field == 0 and visits == 26
        data += bytes([len(events)]) + initial_regs + initial_ram + payload + regs(cpu) + bus.ram
        results.append(dict(capture=name, capture_sha256=sha(capture), events=events,
                            final_ram=sha(bus.ram), final_regs=regs(cpu).hex()))
    path = WORK / "proof"
    path.mkdir(parents=True, exist_ok=True)
    (path / "cases.bin").write_bytes(data)
    (path / "oracle.json").write_text(json.dumps(results, indent=2) + "\n")
    print([(r["capture"], len(r["events"]), r["final_ram"][:12]) for r in results])

if __name__ == "__main__":
    fixture()
