"""Compare both original decimal score loops with native arithmetic."""
import ctypes,hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-score-test/score.dll'))
    buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)();rng=random.Random(2026102703)
    scores=sorted({0,1,9,10,99,100,255,256,999,1000,65535,65536,999999,1000000,9999999,10000000,0xfffffe,0xffffff}|{rng.randrange(0x1000000) for _ in range(1024)})
    instructions=checks=0
    cases=list(itertools.product(scores,[(0x31d5,0x31f4),(0x32ee,0x330d)]))
    cases += [(score,entries) for score,entries in itertools.product([0,1,99,100,999999,0xffffff],[(0x31d5,0x31f4),(0x32ee,0x330d)]) for _ in range(64)]
    for score,(entry,end) in cases:
        m=bytearray(source);m[0x4398:0x439b]=score.to_bytes(3,'big');m[0x439b:0x439f]=bytes(4)
        r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(5)]+[rng.choice([0,1,127,128,250,253,255]),rng.randrange(2)]
        # Repeated edge scores systematically cover all six entry status bits.
        if checks>=len(scores)*2:
            bits=(checks-len(scores)*2)%64;r[3:8]=[(bits>>i)&1 for i in range(5)];r[9]=(bits>>5)&1
        lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(m),(ctypes.c_ubyte*10)(*r))
        cpu=MPU(memory=m,pc=entry);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
        cpu.p=0x30|r[3]|(r[4]<<1)|(r[9]<<2)|(r[7]<<3)|(r[6]<<6)|(r[5]<<7)
        for _ in range(2000):
            if cpu.pc==end:break
            cpu.step();instructions+=1
        else:raise AssertionError(('escaped',score,hex(cpu.pc)))
        lib.bl_score_decimal();lib.bl_contact_copy(buf);lib.bl_contact_regs(regs)
        actual=bytes(buf)
        assert actual==bytes(m),(score,hex(entry),'RAM',[(hex(i),actual[i],m[i]) for i in range(65536) if actual[i]!=m[i]][:12])
        wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
        assert list(regs)==wanted,(score,hex(entry),'registers',list(regs),wanted)
        checks+=1
    files=['core/c64_rooms.c','core/c64_actor_programs.h','tools/build_c64_rooms.py','tools/build_c64_actors.py','tests/source_contact_bridge.c','tests/source_score_bridge.c','tools/verify_source_score.py','test-source-score.ps1']
    report=dict(status='passed_original_decimal_score_loops',source_sha256=SHA,checks=checks,instructions=instructions,score_values=len(scores),entry_status_patterns=64,edition_verified=False,natural_playthrough=False,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-score-host.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS',checks,'score controls;',instructions,'original instructions;',len(scores),'score values')
if __name__=='__main__':main()
