"""Compare each complete result to execution of the frozen score instructions."""
import ctypes as ct
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/"op4-moving-audio-2026-10-31"))
from audit_combat import Bus,Disassembler,MPU,frames,regs

class ScoreBus(Bus):
    def __init__(self,memory):
        super().__init__(memory)
        self.digits=[]

    def __setitem__(self,at,value):
        if 0x8c30<=at<=0x8c35:self.digits.append((at,value))
        super().__setitem__(at,value)

def verify():
    work=ROOT/".tmp/op-score"
    lib=ct.CDLL(str(work/"candidate/score.dll"))
    byte=ct.c_ubyte
    ptr=ct.POINTER(byte)
    lib.bl_contact_seed.argtypes=[ptr,ptr]
    lib.bl_contact_run.argtypes=[ct.c_long]
    lib.bl_contact_copy.argtypes=lib.bl_contact_regs.argtypes=[ptr]
    for f in (lib.bl_contact_return,lib.bl_contact_fault):f.restype=ct.c_ulong
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    digest=hashlib.sha256(frozen).hexdigest()
    assert digest=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    dis=Disassembler(MPU(memory=frozen))
    lengths={}
    capture=ROOT/".reference/c64/work/op4-moving-audio-2026-10-31/combat168/combat.bin"
    (_,_,base),_=frames(capture.read_bytes())
    counts={"display":0,"award":0,"extra_life":0}
    for i in range(256+30):
        memory=bytearray(base)
        pc=0x315d if i<256 else 0x3175
        sp=i&255
        memory[0x100+((sp+1)&255)]=0x34
        memory[0x100+((sp+2)&255)]=0x12
        bus=ScoreBus(memory)
        cpu=MPU(memory=bus,pc=pc)
        cpu.sp=sp;cpu.a=200 if i&1 else 50;cpu.x=2;cpu.y=255-sp
        cpu.p=0x20|(i&3)|((i&12)<<4)|((i&48)>>2)
        if i<256:
            bus.m[0x439c:0x439f]=bytes([sp,sp^0xa5,255-sp])
        else:
            j=i-256
            score=(0,50,255,0xfffe,0xff00ff,0xfffffe)[j%6]
            threshold=(0,0xffffff,score,max(0,score-1),min(0xffffff,score+199))[j//6]
            bus.m[0x41:0x44]=score.to_bytes(3,"big")
            bus.m[0x4392:0x4395]=threshold.to_bytes(3,"big")
            cpu.p&=~8
        before=bytes(bus.m)
        lib.bl_contact_seed((byte*65536).from_buffer_copy(before),(byte*10)(*regs(cpu)))
        stops=[]
        for _ in range(10000):
            if cpu.pc==0x1235:break
            at=cpu.pc
            if at not in lengths:lengths[at]=dis.instruction_at(at)[0]
            n=lengths[at];assert bus.m[at:at+n]==frozen[at:at+n],hex(at)
            if at in (0x3157,0x1b17):stops.append(at)
            cpu.step()
        assert cpu.pc==0x1235
        lib.bl_contact_run(pc);after=(byte*65536)();flags=(byte*10)()
        lib.bl_contact_copy(after);lib.bl_contact_regs(flags)
        assert bytes(after)==bus.m and bytes(flags)==regs(cpu), (i,hex(pc))
        assert lib.bl_contact_return()==cpu.pc and not lib.bl_contact_fault()
        assert stops.count(0x1b17)>=3
        assert bus.digits==[(at,bus.m[at]) for at in range(0x8c30,0x8c36)]
        counts["display" if i<256 else "award"]+=1
        counts["extra_life"]+=stops.count(0x3157)
    assert 0<counts["extra_life"]<counts["award"]
    report=dict(source_sha256=digest,**counts)
    (work/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print(report)

if __name__=="__main__":verify()
