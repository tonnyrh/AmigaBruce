"""Follow the frozen $2584 driver for four actor masks and both image banks."""
import ctypes as ct
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/"op4-moving-audio-2026-10-31"))
from audit_combat import Bus,Disassembler,MPU,frames,regs

def cpu_at(bus,pc,r):
    cpu=MPU(memory=bus,pc=pc)
    cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
    cpu.p=0x30|r[3]|(r[4]<<1)|(r[5]<<7)|(r[6]<<6)|(r[7]<<3)|(r[9]<<2)
    return cpu

def trace():
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    assert sha(frozen)=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    dis=Disassembler(MPU(memory=frozen));lengths={}
    lib=ct.CDLL(str(ROOT/".tmp/source-score-test/score.dll"))
    byte=ct.c_ubyte;ptr=ct.POINTER(byte)
    lib.bl_contact_seed.argtypes=[ptr,ptr];lib.bl_contact_run.argtypes=[ct.c_long]
    lib.bl_contact_copy.argtypes=lib.bl_contact_regs.argtypes=[ptr]
    lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ct.c_ulong
    cases=[]
    for capture in ("combat168","combat207"):
        file=ROOT/".reference/c64/work/op4-moving-audio-2026-10-31"/capture/"combat.bin"
        _,r,m=frames(file.read_bytes())[1]
        # Continue the original main program to its next JSR $2584.
        bus=Bus(m);cpu=cpu_at(bus,0x1c26,r)
        for _ in range(100000):
            if cpu.pc==0x2584:break
            cpu.step()
        assert cpu.pc==0x2584 and [v&1 for v in bus.m[0x95:0x98]]==[1,1,1]
        entry,initial=bytes(bus.m),regs(cpu)
        for mask in range(4):
            bus=Bus(entry);cpu=cpu_at(bus,0x2584,initial)
            for actor in (1,2):
                if not mask & (1<<(actor-1)):bus.m[0x95+actor]&=0xfe
            lib.bl_contact_seed((byte*65536).from_buffer_copy(bus.m),(byte*10)(*initial))
            order=[];parts=[];calls=[];instructions=0
            while cpu.pc!=0x1c2f:
                pc=cpu.pc;instructions+=1
                assert instructions<20000 and (0x2584<=pc<=0x25e1 or 0x26a0<=pc<=0x274e)
                if pc not in lengths:lengths[pc]=dis.instruction_at(pc)[0]
                n=lengths[pc]
                if pc in (0x26aa,0x26e3,0x26ed):
                    assert bus.m[pc]==frozen[pc] and bus.m[pc+1:pc+3]==bus.m[0x26ab:0x26ad]
                else:assert bus.m[pc:pc+n]==frozen[pc:pc+n],hex(pc)
                if pc==0x2586:order.append(cpu.x)
                if pc in (0x2704,0x2719,0x26a0):calls.append(pc)
                if pc==0x26a0:
                    actor=bus.m[0x51];dest=int.from_bytes(bus.m[0x0e:0x10],"little")
                    slot=bus.m[0x276d+actor] if not parts or parts[-1]["actor"]!=actor else bus.m[0x2770+actor]
                    offset=slot*2+(10 if bus.m[0x277d] else 0)
                    assert dest==int.from_bytes(bus.m[0x274f+offset:0x2751+offset],"little")
                    parts.append(dict(actor=actor,slot=slot,destination=f"{dest:04x}",wide=not bool(cpu.p&2)))
                cpu.step()
            expected=[a for a in (2,1,0) if a==0 or mask&(1<<(a-1)) for _ in range(1 if a==2 else 2)]
            assert order==[2,1,0] and [p["actor"] for p in parts]==expected
            assert calls==[0x2704,0x2719,0x26a0]*len(expected) and bus.m[0x277e]==0
            lib.bl_contact_run(0x2584);ram=(byte*65536)();r=(byte*10)()
            lib.bl_contact_copy(ram);lib.bl_contact_regs(r)
            assert bytes(ram)==bus.m and bytes(r)==regs(cpu) and lib.bl_contact_return()==cpu.pc and not lib.bl_contact_fault()
            cases.append(dict(capture=capture,capture_sha256=sha(file.read_bytes()),mask=mask,bank=entry[0x277d],
                              order=order,parts=parts,source_instructions=instructions,final_ram_sha256=sha(bus.m)))
    assert {c["bank"] for c in cases}=={0,1}
    return dict(source_sha256=sha(frozen),cases=cases)

if __name__=="__main__":
    evidence=trace()
    (ROOT/".tmp/op-sprite-cost/source.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("PASS",len(evidence["cases"]),"source/host full-RAM, registers and return-PC comparisons")
