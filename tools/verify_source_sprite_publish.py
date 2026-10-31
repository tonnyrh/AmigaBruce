"""Whole-RAM/flags/SP/return controls for frozen $25E2 sprite publication."""
import ctypes,hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
BASE=ROOT/'reference/analysis/sprite-publish-2026-10-30'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
    U=ctypes.c_ubyte;P=ctypes.POINTER(U);ram=(U*65536)();regs=(U*10)();rng=random.Random(2026103006)
    libs=[ctypes.CDLL(str(ROOT/('.tmp/source-publish-test/'+n+'.dll'))) for n in ['before','candidate']]
    for lib in libs:
        lib.bl_contact_seed.argtypes=[P,P];lib.bl_contact_run.argtypes=[ctypes.c_long]
        lib.bl_contact_copy.argtypes=[P];lib.bl_contact_regs.argtypes=[P]
        lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ctypes.c_ulong
    cases=instructions=fallback=0
    for active,pos,yy,toggle,pose,guard in itertools.product(range(8),[0,7,8,64,127,128,255],[0,99,100,127,128,227,228,255],[0,1,128,255],[0,5,25,63,67,255],[0,1]):
        m=bytearray(raw);m[0x100:0x200]=rng.randbytes(256);m[0x277d]=toggle;m[0x277e]=guard
        for actor in range(3):
            m[0x95+actor]=(active>>actor)&1;m[0x9e+actor]=(pos+actor*13)&255;m[0xa1+actor]=(yy+actor*5)&255
            m[0xa4+actor]=rng.randrange(3);m[0xd4+actor]=rng.randrange(3);m[0x4f4b+actor]=pose
            m[0xda+actor]=rng.randrange(256);m[0xdd+actor]=rng.randrange(256)
            m[0x276d+actor]=[0,2,4][actor];m[0x2770+actor]=rng.choice([1,3,128,255])
        m[0xd010]=rng.randrange(256);sp=rng.randrange(256)
        m[0x100+((sp+1)&255)]=254;m[0x100+((sp+2)&255)]=255
        r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(4)]+[0,sp,rng.randrange(2)]
        before=bytes(m);cpu=MPU(memory=m,pc=0x25e2);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=sp
        cpu.p=0x20|r[3]|r[4]<<1|r[9]<<2|r[6]<<6|r[5]<<7
        for _ in range(2000):
            if cpu.pc==0xffff:break
            cpu.step();instructions+=1
        else:raise AssertionError(('Source publish escaped',cases,hex(cpu.pc)))
        wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7&1,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
        for lib in libs:
            lib.bl_contact_seed((U*65536).from_buffer_copy(before),(U*10)(*r));lib.bl_contact_run(0x25e2)
            lib.bl_contact_copy(ram);lib.bl_contact_regs(regs)
            if bytes(ram)!=bytes(m):
                diff=[(hex(i),a,b) for i,(a,b) in enumerate(zip(ram,m)) if a!=b]
                raise AssertionError(('RAM',cases,diff[:10]))
            assert list(regs)==wanted,('registers',cases,list(regs),wanted)
            assert lib.bl_contact_return()==0xffff and not lib.bl_contact_fault()
        cases+=1
    # Decimal mode retains the exact previous implementation, independently
    # of any wider claim about that implementation's decimal flag parity.
    for sp in range(256):
        m=bytearray(raw);m[0x100:0x200]=rng.randbytes(256);m[0x277e]=sp&1;m[0x277d]=sp
        m[0x100+((sp+1)&255)]=254;m[0x100+((sp+2)&255)]=255
        r=[37,23,41,1,0,1,1,1,sp,0];outputs=[]
        for lib in libs:
            lib.bl_contact_seed((U*65536).from_buffer_copy(m),(U*10)(*r));lib.bl_contact_run(0x25e2);lib.bl_contact_copy(ram);lib.bl_contact_regs(regs)
            outputs.append((bytes(ram),bytes(regs),lib.bl_contact_return(),lib.bl_contact_fault()))
        assert outputs[0]==outputs[1],('Decimal fallback changed',sp);fallback+=1
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    scope=json.loads((BASE/'scope.json').read_text(encoding='utf-8-sig'))
    for e in scope['inputs']+scope['generated']:assert item(ROOT/e['path'])==e
    report=dict(status='passed_isolated_binary_sprite_publish_source_controls',source_sha256=SHA,source_cases=cases,source_instructions=instructions,unchanged_decimal_fallback_cases=fallback,all_ram_and_registers=True,returned_pc_verified=True,production_changed=False,natural_playthrough=False,edition_verified=False,
        artifacts=scope['inputs']+scope['generated']+[item(ROOT/p) for p in ['tools/verify_source_sprite_publish.py','tools/build_sprite_publish_candidate.py','test-source-sprite-publish.ps1']],limits=['Controlled shadow-VIC inputs, not physical raster behavior','Decimal fallback compared before/after only, not certified against unknown decimal source states','No native execution or performance claim'])
    (BASE/'host.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS sprite publish:',cases,'source cases;',instructions,'original instructions;',fallback,'unchanged decimal fallbacks')
if __name__=='__main__':main()
