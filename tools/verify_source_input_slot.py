"""All-RAM/register control for a candidate native $169D-$1702 slot.

Executes frozen original instructions at a controlled entry. This proves
neither a complete IRQ nor the physical input sampling phase.
"""
import ctypes,hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
BASE='reference/analysis/irq-input-2026-10-30'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-input-slot/slot.dll'))
    U=ctypes.c_ubyte;P=ctypes.POINTER(U);ram=(U*65536)();regs=(U*10)()
    lib.bl_input_slot_seed.argtypes=[P,P];lib.bl_input_slot_run.argtypes=[ctypes.c_long,ctypes.c_long]
    lib.bl_input_slot_copy.argtypes=[P];lib.bl_input_slot_regs.argtypes=[P]
    rng=random.Random(2026103004);cases=instructions=0;writes=set()
    def check(active,current,human,flag0,flag1,port0,port1,sp,status):
        nonlocal cases,instructions
        m=bytearray(source);m[0x100:0x200]=rng.randbytes(256)
        m[0x104]=active;m[3]=current;m[0x42ca]=human;m[0x1383]=flag0;m[0x1384]=flag1
        m[0xdc00]=port0;m[0xdc01]=port1
        m[0x98],m[0x9b],m[0x99],m[0x9c]=10,1,5,0
        before=bytes(m);r=[rng.randrange(256) for _ in range(3)]+[status&1,status>>1&1,status>>7&1,status>>6&1,status>>3&1,sp,status>>2&1]
        cpu=MPU(memory=m,pc=0x169d);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=sp;cpu.p=status
        for _ in range(100):
            if cpu.pc==0x1703:break
            cpu.step();instructions+=1
        else:raise AssertionError(('source escaped',hex(cpu.pc)))
        wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7&1,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
        lib.bl_input_slot_seed((U*65536).from_buffer_copy(before),(U*10)(*r));lib.bl_input_slot_run(port0,port1)
        lib.bl_input_slot_copy(ram);lib.bl_input_slot_regs(regs)
        assert bytes(ram)==bytes(m),('RAM',cases,active,current,human,flag0,flag1,port0,port1,sp,status)
        assert list(regs)==wanted,('registers',cases,list(regs),wanted)
        writes.update(i for i,(a,b) in enumerate(zip(before,m)) if a!=b)
        cases+=1
    for active,current,human,f0,f1 in itertools.product(range(2),repeat=5):
        for p0,p1 in itertools.product(range(32),repeat=2):
            check(active,current,human,f0,f1,p0,p1,rng.randrange(256),rng.randrange(256)|0x30)
    exhaustive=cases
    # All stack positions/status bytes, including PHP/PHA aliases in page1.
    for sp,status in itertools.product(range(256),repeat=2):
        check(1,status&1,1,(status>>1)&1,(status>>2)&1,(sp*19+status)&255,(status*37+sp)&255,sp,status)
    stack_status=cases-exhaustive
    # Preserve indexed reads even for deliberately nonstandard player bytes.
    for current in range(256):
        for human in [0,1,255]:
            check(255,current,human,255,255,rng.randrange(256),rng.randrange(256),rng.randrange(256),rng.randrange(256))
    report=dict(status='passed_candidate_source_input_slot_all_ram_and_registers',source_sha256=SHA,edition_verified=False,natural_playthrough=False,production_changed=False,
        source_entry='$169D',source_stop='$1703',exhaustive_input_cases=exhaustive,stack_status_cases=stack_status,nonstandard_player_cases=cases-exhaustive-stack_status,
        cases=cases,instructions=instructions,all_ram_and_registers=True,changed_addresses=['$%04X'%a for a in sorted(writes)],
        limits=['Fixed pin bytes, controlled source entry; not natural CIA sampling','No full IRQ, raster prologue or caller-PC equivalence claim','Candidate is not integrated into source_actor_field'],
        artifacts=[item(p) for p in [BASE+'/candidate/input_slot.h','tests/source_input_slot_bridge.c','tools/verify_source_input_slot.py','test-source-input-slot.ps1','core/c64_rooms.c']])
    (ROOT/BASE/'input-slot-candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS native input candidate:',cases,'whole-RAM/register cases;',instructions,'frozen instructions; production unchanged')
if __name__=='__main__':main()
