"""Actual candidate bytes: object dispatch handler boundaries, all A/$53 values."""
import ctypes,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-object-test/objects.dll'))
    lib.bl_object_classify.restype=ctypes.c_ulong
    targets={0x2ee9,0x2eea,0x2ef7,0x2efa,0x2f01,0x2f04,0x2f3c,0x2f51,0x2f66,0x2f7b,0x310c}
    buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)();rng=random.Random(2026102702)
    instructions=0;counts={}
    for aa in range(256):
        for mask in range(256):
            m=bytearray(source);m[0x53]=mask
            r=[aa,rng.randrange(256),rng.randrange(256)]+[rng.randrange(2) for _ in range(5)]+[253,rng.randrange(2)]
            lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(m),(ctypes.c_ubyte*10)(*r))
            cpu=MPU(memory=m,pc=0x2e89);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
            cpu.p=0x30|r[3]|(r[4]<<1)|(r[9]<<2)|(r[7]<<3)|(r[6]<<6)|(r[5]<<7)
            for _ in range(100):
                if cpu.pc in targets:break
                cpu.step();instructions+=1
            else:raise AssertionError(('escaped',aa,mask,hex(cpu.pc)))
            target=lib.bl_object_classify();lib.bl_contact_copy(buf);lib.bl_contact_regs(regs)
            assert target==cpu.pc,(aa,mask,'handler',hex(target),hex(cpu.pc))
            assert bytes(buf)==bytes(m),(aa,mask,'RAM')
            wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
            assert list(regs)==wanted,(aa,mask,'registers',list(regs),wanted)
            key=f'${target:04X}';counts[key]=counts.get(key,0)+1
    driver_checks=driver_instructions=0
    lib.bl_contact_run.argtypes=[ctypes.c_long]
    lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ctypes.c_ulong
    for room in range(20):
        for active in range(8):
            for kind in range(3):
                m=bytearray(source);m[0x29]=room;m[0x1fe:0x200]=b'\xfe\xff'
                pool=[0,1,6,7,8,9,10,11,12,13,14,16,17,18,21,22,23,24,25,26,27,28,29]
                if kind==1 and room!=11:pool=[2,3,4,5] # Interior gate probes are rejected by $30D4.
                if kind==2:pool=[0x62] # Net handler and its original continuation through $2EA9.
                m[0x8c00:0x9000]=bytes(rng.choice(pool) for _ in range(1024))
                for actor in range(3):
                    m[0x95+actor]=((active>>actor)&1)|[0,0x80,0x40][actor]
                    m[0x9e+actor]=60+actor*24;m[0xa1+actor]=80+actor*32
                    m[0xbf+actor]=25 if (room+active+kind+actor)%7==0 else 0
                    m[0xb6+actor]=rng.randrange(16)
                r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(5)]+[253,rng.randrange(2)]
                r[7]=0 # Game-facing CLD entry, no synthetic decimal arithmetic claim.
                lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(m),(ctypes.c_ubyte*10)(*r))
                cpu=MPU(memory=m,pc=0x2e39);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
                cpu.p=0x30|r[3]|(r[4]<<1)|(r[9]<<2)|(r[7]<<3)|(r[6]<<6)|(r[5]<<7)
                for _ in range(20000):
                    if cpu.pc==0xffff:break
                    cpu.step();driver_instructions+=1
                else:raise AssertionError(('driver escaped',room,active,kind,hex(cpu.pc)))
                lib.bl_contact_run(0x2e39);lib.bl_contact_copy(buf);lib.bl_contact_regs(regs)
                assert not lib.bl_contact_fault(),('driver fault',room,active,kind,hex(lib.bl_contact_fault()))
                actual=bytes(buf)
                assert actual==bytes(m),('driver RAM',room,active,kind,[(hex(i),actual[i],m[i]) for i in range(65536) if actual[i]!=m[i]][:12])
                wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
                assert list(regs)==wanted,('driver registers',room,active,kind,list(regs),wanted)
                assert lib.bl_contact_return()==0xffff
                driver_checks+=1
    files=['core/c64_rooms.c','core/c64_actor_programs.h','tools/build_c64_rooms.py','tools/build_c64_actors.py','tests/source_contact_bridge.c','tests/source_object_bridge.c','tools/verify_source_object.py','test-source-object.ps1']
    report=dict(status='passed_original_object_handler_boundaries',source_sha256=SHA,checks=65536,instructions=instructions,targets=counts,driver_checks=driver_checks,driver_instructions=driver_instructions,edition_verified=False,natural_playthrough=False,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-object-host.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS',report['checks'],'object handler controls;',instructions,'original instructions;',driver_checks,'whole-driver cases;',driver_instructions,'driver instructions')
if __name__=='__main__':main()
