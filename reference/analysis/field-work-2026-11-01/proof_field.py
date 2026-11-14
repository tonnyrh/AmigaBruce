"""Compare complete integrated input slots to the frozen 6502 bytes."""
import ctypes as ct
import hashlib
import itertools
import json
import struct
import sys
from build_field import HERE,ROOT,WORK,compile_program
sys.path.insert(0,str(HERE.parent/"op-finish-2026-10-31"))
import check_images
sys.path.insert(0,str(ROOT/"tools"))
from audit_c64_irq_contract import Bus,decode,MPU,SHA,SOURCE

def run_input(engine):
    check_images.WORK=WORK
    exported=("prepare","seed","field","copy","regs","inputs")
    bridge=(ROOT/"tests/source_irq_audit_bridge.c").read_text().replace("../core/c64_rooms.c",(engine/"c64_rooms.c").as_posix())
    for name in exported:bridge=bridge.replace("void bl_irq_audit_"+name+"(","__declspec(dllexport) void bl_irq_audit_"+name+"(")
    bridge+='''
static unsigned long pads,calls;
static unsigned long read_pads(long player,long human){++calls;return player?(pads>>8)|((pads&255)<<8):pads;}
__declspec(dllexport) void test_pins(unsigned long pins){calls=0;pads=pins;bl_c64_set_control_reader(read_pads);}
__declspec(dllexport) unsigned long called(void){return calls;}
'''
    lib=check_images.dll("pad-host",bridge)
    mem=(ct.c_ubyte*65536)();r=(ct.c_ubyte*10)();out=(ct.c_ubyte*4)()
    lib.bl_irq_audit_prepare(0);lib.bl_irq_audit_copy(mem);lib.bl_irq_audit_regs(r)
    frozen=SOURCE.read_bytes();assert hashlib.sha256(frozen).hexdigest()==SHA
    assert bytes(mem[0x169d:0x1703])==frozen[0x169d:0x1703]
    cpu=MPU(memory=Bus(bytes(mem)),pc=0x169d)
    cases=reads=0
    for gate,player,human,selector0,selector1 in itertools.product(range(2),repeat=5):
        for p0,p1 in itertools.product(range(32),repeat=2):
            for at,value in ((0x104,gate),(3,player),(0x42ca,human),(0x1383,selector0),(0x1384,selector1),
                (0xdc00,p0),(0xdc01,p1),(0x98,10),(0x9b,1),(0x99,5),(0x9c,0),(0x7f,1),(0x82,0),(2,50)):
                mem[at]=value;cpu.memory.ram[at]=value
            cpu.pc=0x169d;cpu.p=0x24;cpu.sp=0xed
            while cpu.pc!=0x1703:cpu.step()
            expected=[cpu.memory.ram[k] for k in (0x98,0x9b,0x99,0x9c)]
            # Stale neutral values from a previous display loop. Change only the physical reader.
            lib.bl_irq_audit_seed(mem,r,0,0);lib.test_pins(decode(p1)|(decode(p0)<<8))
            lib.bl_irq_audit_field(0);lib.bl_irq_audit_inputs(out)
            assert list(out)==expected and lib.called()==gate,(gate,player,human,p0,p1)
            reads+=lib.called();cases+=1
    result=dict(source_sha256=SHA,cases=cases,slot_reads=reads,retained=cases-reads,
        addresses=["$169D-$1702","$4A85-$4A88"],natural_irq_phase=False)
    (WORK/"input-proof.json").write_text(json.dumps(result,indent=2)+"\n");print(result)

def build_dma_proof():
    out=WORK/"proof";out.mkdir(exist_ok=True)
    (out/"main.c").write_text((HERE/"check_dma.c").read_text())
    for name in ("c64_rooms.c","c64_actor_programs.h"):(out/name).write_bytes((WORK/"dma"/name).read_bytes())
    (out/"cases.bin").write_bytes(struct.pack(">I",128))
    compile_program(out,WORK/"dma")

if __name__=="__main__":
    if sys.argv[1]=="input":run_input(WORK/(sys.argv[2] if len(sys.argv)>2 else "pad"))
    else:build_dma_proof()
