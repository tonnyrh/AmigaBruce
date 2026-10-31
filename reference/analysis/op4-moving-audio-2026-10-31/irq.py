"""Controlled IRQ at the actual repeated combat PC; distinguish both native seams."""
import ctypes,json,sys
from pathlib import Path
from audit_combat import ROOT,Bus,MPU,regs,frames,sha
sys.path.insert(0,str(ROOT/"tools"))
from verify_source_irq_context import Bus as IrqBus
from audit_c64_irq_contract import decode
def mpu(bus,pc,r):
    cpu=MPU(memory=bus,pc=pc)
    cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
    cpu.p=0x20|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
    return cpu
def checkpoints(folder):
    (_,r,m),_=frames((folder/"combat.bin").read_bytes());bus=Bus(m);cpu=mpu(bus,0x29c3,r)
    visits=0
    for _ in range(100000):
        if cpu.pc==0x1c26:break
        if cpu.pc==0x2b4e:bus.m[0xbc]&=1
        if cpu.pc==0x2c51:
            visits+=1
            if visits in (1,13,25):yield visits,bytes(bus.m),regs(cpu)
        cpu.step()
    assert visits==26
def category(a):
    if 0x153<=a<0x15f:return "palette_buffer"
    if 0x100<=a<0x200:return "stack_page"
    if 0xa<=a<=0xd:return "palette_pointers"
    if a in (0x408,0x409) or 0x47f5<=a<0x47f9:return "raster_schedule"
    if 0xd000<=a<0xe000:return "hardware"
    return "other"
def finish(memory,r):
    bus=Bus(memory);cpu=mpu(bus,0x2c51,r)
    for _ in range(100000):
        if cpu.pc==0x1c26:return {"score":int.from_bytes(bus.m[0x41:0x44],"big"),"health":list(bus.m[0xd1:0xd4]),"registers":regs(cpu).hex()}
        cpu.step()
    raise AssertionError("combat escaped after field")
def check(write_fixture=True):
    work=ROOT/".tmp/op4-moving";U=ctypes.c_ubyte;P=ctypes.POINTER(U)
    old=ctypes.CDLL(str(work/"audit.dll"));new=ctypes.CDLL(str(work/"context.dll"))
    old.bl_irq_audit_seed.argtypes=[P,P,ctypes.c_long,ctypes.c_long];old.bl_irq_audit_field.argtypes=[ctypes.c_long]
    new.bl_irq_context_seed.argtypes=[P,P];new.bl_irq_context_run.argtypes=[ctypes.c_long,ctypes.c_long,ctypes.c_long]
    rows=[];fixtures=bytearray()
    for capture in ("combat168","combat207"):
        for visit,m,r in checkpoints(work/capture):
            pins=(31,m[0x98]|(m[0x9b]<<4))
            assert m[3]==0 and m[0x1383]==1 and not r[9] and not r[7]
            bus=IrqBus(m,pins,253);cpu=mpu(bus,0x2c51,r);cpu.irq();pcs=[]
            for _ in range(50000):
                pcs.append(cpu.pc);cpu.step()
                if cpu.pc==0x2c51:break
            assert cpu.pc==0x2c51 and regs(cpu)==r and pcs[0]==0x1103 and 0x48c1 in pcs and pcs[-1]==0x491d
            assert [pcs.index(x) for x in (0xeb03,0xef73,0xf073,0x15b8,0x169d,0x1703)]==sorted(pcs.index(x) for x in (0xeb03,0xef73,0xf073,0x15b8,0x169d,0x1703))
            ram=(U*65536).from_buffer_copy(m);before=(U*10)(*r);out=(U*65536)();reg=(U*10)()
            old.bl_irq_audit_seed(ram,before,decode(pins[1]),decode(pins[0]));old.bl_irq_audit_field(1)
            old.bl_irq_audit_copy(out);old.bl_irq_audit_regs(reg);assert bytes(reg)==r
            native=bytes(out);diffs=[(a,b,n) for a,(b,n) in enumerate(zip(bus.ram,native)) if b!=n]
            expected=finish(bus.ram,r);after=finish(native,r)
            new.bl_irq_context_seed(ram,before);new.bl_irq_context_run(0x2c51,*pins)
            new.bl_irq_context_copy(out);new.bl_irq_context_regs(reg)
            assert bytes(out)==bytes(bus.ram) and bytes(reg)==r and new.bl_irq_context_pc()==0x2c51 and not new.bl_irq_context_fault() and new.bl_irq_context_gates()==bus.gates
            fixtures.extend(r+bytes((*pins,bus.gates))+m+bus.ram)
            rows.append(dict(capture=capture,visit=visit,pc="2c51",i=r[9],decimal=r[7],pins=pins,
                irq_instructions=len(pcs),irq_ram_sha256=sha(bytes(bus.ram)),irq_regs=r.hex(),caller_restored=True,
                existing_seam_diffs=[dict(at=f"{a:04x}",source=b,native=n,kind=category(a)) for a,b,n in diffs],
                original_continuation=expected,existing_continuation=after,isolated_context_exact=True))
    if write_fixture:
        (work/"proof").mkdir(exist_ok=True)
        (work/"proof/cases.bin").write_bytes(len(rows).to_bytes(4,"big")+fixtures)
    return rows
if __name__=="__main__":
    result=check();(ROOT/".tmp/op4-moving/irq.json").write_text(json.dumps(result,indent=2)+"\n")
    for r in result:print(r["capture"],r["visit"],len(r["existing_seam_diffs"]),r["existing_continuation"]==r["original_continuation"])
