"""Trace post-hit Yamo recovery in frozen C64 bytes and the current native port.

Positions, contact latch and health are controlled fixtures, not natural play.
The original instructions decide hit acceptance, recovery counters and falling.
"""
import ctypes
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler


def main():
    source=ROOT/'.reference/c64/work/untrained-memory.bin'
    frozen=source.read_bytes()
    digest=hashlib.sha256(frozen).hexdigest()
    assert digest=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    dll=ctypes.CDLL(str(ROOT/'.tmp/source-actor-test/actors.dll'))
    dll.bl_actor_prepare.argtypes=[ctypes.c_long]
    dll.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    dll.bl_c64_actor_test_call.argtypes=[ctypes.c_long]*2
    dll.bl_c64_fault.restype=ctypes.c_ushort
    buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*13)()
    def memory():dll.bl_actor_copy(buf);return list(buf)
    def put(at,value):dll.bl_c64_test_write(at,value)
    comparisons=0
    def check(entry,actor=0):
        nonlocal comparisons
        m=memory();cpu=MPU(memory=m,pc=entry)
        cpu.a=cpu.y=0;cpu.x=actor;cpu.p=0x30;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
        for _ in range(100000):
            if cpu.pc==0xffff:break
            cpu.step()
        else:raise AssertionError(('Source escaped',hex(cpu.pc)))
        dll.bl_c64_actor_test_call(entry,actor)
        assert not dll.bl_c64_fault(),hex(dll.bl_c64_fault())
        native=memory();dll.bl_c64_actor_registers(regs)
        assert native==m,('RAM mismatch',hex(entry),[(hex(i),a,b) for i,(a,b) in enumerate(zip(native,m)) if a!=b][:8])
        expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp]
        assert list(regs[:9])==expected
        comparisons+=1
        return m
    def actor(m):return dict(x=m[0x9f],y=m[0xa2],state=m[0xc0],counter=m[0xcf],wait=m[0x107],pose_lock=m[0x4fdc])
    cases=[]
    for human,victim,age,round_ in itertools.product((0,1),(0,2),(0,24,25,31,32),(0,1)):
        dll.bl_actor_prepare(0)
        put(0x42ca,human);put(0x88,age);put(0x40,round_)
        for i,v in enumerate((0,0,1,1,2)):put(0x4f40+i,v)
        for i in range(3):
            for at,v in {0x95+i:(1,0x81,0x41)[i],0x9e+i:150,0xa1+i:40,0xa4+i:1,
                         0xbf+i:0,0xc2+i:0,0xce+i:0,0x106+i:0,0x4fdb+i:0,
                         0xd1+i:36,0x4f45+i:2,0x98+i:15,0x9b+i:1,0xb6+i:0,0xa7+i:0}.items():put(at,v)
        for i in range(132):put(0x4f57+i,0)
        for at,v in {0x9f:60,0xa2:150,0xc0:13,0xc3:13,0xcf:7,
                     0x9e+victim:68,0xa1+victim:150,0xd01e:15 if victim==0 else 60}.items():put(at,v)
        m=check(0x29c3)
        assert m[0xd1+victim]==29,('Kick not accepted',human,victim,age,round_,m[0xd1+victim])
        after=actor(m);assert after['state']==0 and after['wait']==4
        steps=[after]
        for step in range(1,40):
            m=check(0x1c5b,1);steps.append(actor(m))
            if m[0xa2]!=150:break
        else:raise AssertionError('Yamo did not resume falling')
        cases.append(dict(human_yamo=bool(human),victim=victim,age=age,round=round_,
                          first_vertical_move_step=step,steps=steps))
    out=ROOT/'reference/analysis/yamo-kick-hold-2026-11-21';out.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(frozen)))
    lines=[]
    for start,end in ((0x10d0,0x10e0),(0x1c5b,0x1c6b),(0x1d6f,0x1d7e),(0x2008,0x2020),(0x24f4,0x2504),
                      (0x2ad4,0x2afa),(0x2b3e,0x2b9a)):
        pc=start
        while pc<end:
            size,text=dis.instruction_at(pc)
            lines.append(f'${pc:04X}: {frozen[pc:pc+size].hex(" "):8} {text}');pc+=size
        lines.append('')
    (out/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
    report=dict(source_sha256=digest,certified_original_edition=False,natural_playthrough=False,
                method=__doc__,cases=len(cases),ram_and_register_comparisons=comparisons,
                gameplay_changed=False,rows=cases,
                source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in
                              ('core/c64_rooms.c','core/c64_actor_programs.h','tests/source_actor_bridge.c','tools/audit_yamo_kick_hold.py')])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS',len(cases),'kick recovery cases;',comparisons,'full RAM/register comparisons')
    print('Post-hit counter -> first vertical move:',sorted({(r['steps'][0]['counter'],r['first_vertical_move_step']) for r in cases}))


if __name__=='__main__':main()
