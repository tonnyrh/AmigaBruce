"""Native DIVU witnesses from both actual NMOS decimal loops."""
import hashlib
import json
import random
import shutil
import struct
import sys
from build_decimal import HERE,ROOT,WORK,link,updated

sys.path.insert(0,str(ROOT/".reference/tools/python"))
from py65.devices.mpu6502 import MPU

def registers(cpu):
    p=cpu.p
    return bytes((cpu.a,cpu.x,cpu.y,p&1,p>>1&1,p>>7,p>>6&1,p>>3&1,cpu.sp,p>>2&1))

def vectors(out):
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    digest=hashlib.sha256(frozen).hexdigest()
    assert digest=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    rng=random.Random(0x32ee)
    edges={0,1,9,10,99,100,255,256,9999999,10000000,0xfffffe,0xffffff}
    # Exercise every possible quotient either side of the native DIVU split.
    for q in range(1,1678):
        edges.update((q*10000-1,q*10000,q*10000+1))
    cases=[(value,i&1,rng.randrange(64),i&255) for i,value in enumerate(sorted(edges))]
    for v in (0,9999,10000,9999999,10000000,0xffffff):
        for loop in range(2):
            for bits in range(64):cases.append((v,loop,bits,(bits*13)&255))
    ram=bytearray(frozen);cpu=MPU(memory=ram);data=bytearray();instructions=0
    for value,loop,bits,sp in cases:
        pc,end=((0x31d5,0x31f4),(0x32ee,0x330d))[loop]
        raw=value.to_bytes(3,"big");ram[0x4398:0x439f]=raw+bytes(4)
        cpu.pc=pc;cpu.sp=sp;cpu.a,cpu.x,cpu.y=(rng.randrange(256) for _ in range(3))
        cpu.p=0x30|(bits&3)|((bits&4)<<5)|((bits&8)<<3)|((bits&16)>>1)|((bits&32)>>3)
        initial=registers(cpu)
        while cpu.pc!=end:
            assert pc<=cpu.pc<end
            cpu.step();instructions+=1
        assert bytes(ram[0x439b:0x439f])==bytes.fromhex(f"{value:08d}")
        data.extend(raw+initial+ram[0x4398:0x439f]+bytes([ram[0x100+sp]])+registers(cpu))
    (out/"cases.bin").write_bytes(struct.pack(">I",len(cases))+data)
    report=dict(source_sha256=digest,cases=len(cases),distinct_scores=len(edges),source_instructions=instructions,
                php_plp_entries=["31d5","32ee"],divisor=10000,maximum_quotient=1677,
                fixture_sha256=hashlib.sha256((out/"cases.bin").read_bytes()).hexdigest())
    (WORK/"oracle.json").write_text(json.dumps(report,indent=2)+"\n")
    print(report,flush=True)

def prove():
    out=WORK/"proof";out.mkdir(exist_ok=True)
    vectors(out)
    core=(WORK/"candidate/c64_rooms.c").read_text()+(HERE/"native_check.h").read_text()
    (out/"c64_rooms.c").write_text(core)
    (out/"main.c").write_text((HERE/"proof_main.c").read_text())
    link(out)

def combat():
    prior=ROOT/".tmp/op-score/proof"
    out=WORK/"combat-proof";out.mkdir(exist_ok=True)
    for name in ("main.c","clock.h","input_slot.h","irq_context.h","c64_actor_programs.h","cases.bin"):
        shutil.copyfile(prior/name,out/name)
    (out/"c64_rooms.c").write_text(updated((prior/"c64_rooms.c").read_text()))
    link(out)

if __name__=="__main__":
    if sys.argv[1:]==["combat"]:combat()
    else:prove()
