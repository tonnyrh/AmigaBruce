"""Disassemble frozen room code and verify instruction sites; executes no6502 code."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))


def main():
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    memory=source.read_bytes()
    facts=json.loads((ROOT/'reference/validation/candidate-rooms.json').read_text())
    assert hashlib.sha256(memory).hexdigest()==facts['source_files'][0]['sha256']
    checks=[
        (0x09dc,'bda047','Room-dependent initial attribute table'),
        (0x0aaf,'bd344b','Room pointer low table'),
        (0x0ab4,'bd494b','Room pointer high table'),
        (0x0aea,'910409809108','Upper character; OR80; lower character'),
        (0x0b5f,'48a9f89110911268297f60','Black attribute written to both halves; strip attribute from ID'),
        (0x1c42,'a529c90dd007b5a1186904d002b5a1','R14 object-coordinate Y exception'),
        (0x33bd,'a5290aaabd9d4e48bd9c4e4860','Init dispatch by pushing table address then RTS'),
        (0x3a6f,'a5290aaabdc54e48bdc44e4860','Room loop dispatch by pushing table address then RTS'),
        (0x55d7,'b1122907f060','Per-character color low3 bits select classification'),
        (0x5590,'a650a90095b64e3f4f36b64e3e4f36b64e3d4f36b64e3c4f36b660','Four class bits assembled into actor B6'),
        (0x304b,'a529c912d00160','R19 exception in hazard dispatch'),
    ]
    checked=[]
    for address,expected,meaning in checks:
        code=bytes.fromhex(expected)
        assert memory[address:address+len(code)]==code,hex(address)
        checked.append(dict(address=f'${address:04X}',size=len(code),sha256=hashlib.sha256(code).hexdigest(),meaning=meaning))
    ranges=[(0x09da,0x09f0),(0x0a9b,0x0ab9),(0x0ad7,0x0b30),(0x0b5f,0x0b6a),
            (0x15d0,0x15ee),(0x1c39,0x1c5b),(0x2e89,0x2f04),
            (0x304b,0x3052),(0x310c,0x312c),(0x33bd,0x33ca),(0x3a6f,0x3a7c),
            (0x5212,0x52ad),(0x537e,0x53e4),(0x5431,0x55ab),(0x55d7,0x55e6)]
    decoder=Disassembler(MPU(memory=list(memory)))
    lines=['Frozen candidate room-code listing. Disassembly only; no instructions executed.','']
    for start,end in ranges:
        lines.append(f'${start:04X}-${end-1:04X}')
        address=start
        while address<end:
            length,instruction=decoder.instruction_at(address)
            assert address+length<=end,(hex(address),hex(end))
            raw=memory[address:address+length].hex(' ')
            lines.append(f'{address:04X}  {raw:9}  {instruction}')
            address+=length
        lines.append('')
    output=ROOT/'.reference/c64/room-reconstruction/room-code.txt'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def rec(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    report=dict(date='2026-10-24',status='passed_frozen_binary_instruction_checks',
                instructions_executed=0,primary_edition_verified=False,full_room_logic_reconstructed=False,
                checks=checked,room_programs=[dict(room=r['index']+1,init_entry=hex(int(r['init_address'],16)+1),loop_entry=hex(int(r['loop_address'],16)+1)) for r in facts['rooms']],
                source_files=[rec(source),rec(Path(__file__).resolve())],listing=rec(output),
                next_work='Trace all room init/loop branches and mutations before replacing provisional Amiga geometry')
    (ROOT/'reference/validation/c64-room-code.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS:{len(checks)} instruction-site checks;20 init/loop address pairs; no6502 instructions executed')
    print(output)


if __name__=='__main__':main()
