"""Actual frozen body/class instructions against unchanged portable helpers.

Injected snippet controls, not a natural playthrough or original raster proof.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
BASE=ROOT/'reference/analysis/contact-empty-2026-10-31'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/contact-empty-host/contact.dll'))
    lib.bl_empty_host_run.argtypes=[ctypes.c_long]
    buf=(ctypes.c_ubyte*65536)();got=(ctypes.c_ubyte*10)();instructions=0;cases=0
    for t in range(768):
        for body in [False,True]:
            m=bytearray(source)
            for i in range(512):m[i]=(t+i*7)&255
            for i in range(85):m[0x4eec+i]=(i*11+t)&255
            m[0x4eed:0x4f32]=bytes(69)
            if t&1:m[0x4eed+t%69]=1+(t&127)
            m[0x50]=t%3
            for bit,div,at in [(2,5,0x4f32),(4,7,0x4f33),(8,11,0x4f34)]:m[at]=(255 if t%div==0 else 2 if t%div==1 else 1) if t&bit else 0
            sp=t//3;r=[(t*3)&255,(t*7)&255,(t*11)&255,t&1,(t>>1)&1,(t>>2)&1,(t>>3)&1,(t>>4)&1,sp,(t>>5)&1]
            if not body:m[0x100+((sp+1)&255)]=254;m[0x100+((sp+2)&255)]=255
            lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(m),(ctypes.c_ubyte*10)(*r))
            cpu=MPU(memory=m,pc=0x53e4 if body else 0x5431);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=sp
            cpu.p=0x30|r[3]|(r[4]<<1)|(r[9]<<2)|(r[7]<<3)|(r[6]<<6)|(r[5]<<7)
            stop=0x53d4 if body else 0xffff
            for _ in range(3000):
                if cpu.pc==stop:break
                cpu.step();instructions+=1
            else:raise AssertionError((t,body,'Source snippet escaped',hex(cpu.pc)))
            lib.bl_empty_host_run(int(body));lib.bl_contact_copy(buf);lib.bl_contact_regs(got)
            actual=bytes(buf)
            assert actual==bytes(m),(t,body,'RAM',[(hex(i),actual[i],m[i]) for i in range(65536) if actual[i]!=m[i]][:12])
            expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
            assert list(got)==expected,(t,body,'registers',list(got),expected)
            cases+=1
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    report=dict(status='passed_original_body_class_bytes',cases=cases,source_instructions=instructions,source_sha256=SHA,
        entries={'body':'$53E4 to$53D4 after body branch; no foot/part check executed','classes':'$5431 through actual RTS'},
        whole_ram=True,registers=True,all256_stack_positions_each_actor=True,natural_playthrough=False,raster_exact=False,edition_verified=False,
        artifacts=[item(p) for p in [ROOT/'tools/verify_contact_empty_source.py',BASE/'empty_bridge.c',ROOT/'.tmp/contact-empty-host/contact.dll',ROOT/'core/c64_rooms.c',ROOT/'amiga/contact_prepare.s']])
    (BASE/'source-controls.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',cases,'whole-RAM/register body/class controls;',instructions,'actual frozen source instructions')

if __name__=='__main__':main()
