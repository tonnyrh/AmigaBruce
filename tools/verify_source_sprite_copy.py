"""Compare sprite expansion with the frozen6502 bytes, including aliases."""
import ctypes,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SOURCE='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SOURCE
    dll=ctypes.CDLL(str(ROOT/'.tmp/source-contact-test/contact.dll'))
    arr=ctypes.c_ubyte*65536;regarr=ctypes.c_ubyte*10
    dll.bl_contact_seed.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(ctypes.c_ubyte)]
    dll.bl_contact_run.argtypes=[ctypes.c_long];dll.bl_contact_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)];dll.bl_contact_regs.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    dll.bl_contact_return.restype=ctypes.c_ulong;dll.bl_contact_fault.restype=ctypes.c_ulong
    out=arr();regs=regarr();checks=0;instructions=0;faults=0;aliases=0
    heights=[0,1,2,3,7,12,15,20,21,31]
    patterns=[(0xa000,0xa200),(0xa001,0xa200),(0xa000,0xa000),(0xa001,0x2770),(0xa000,0xfff0),(0x0100,0xa200)]
    cases=list(itertools.product([0,1],heights,[0,1,62,63,127,255],patterns,[0,0xc9]))
    cases=list(dict.fromkeys(cases+[(1,h,h*3,pattern,flags) for h in heights for pattern in patterns for flags in [0,0xc9]]))
    for index,(wide,height,yy,(dest,glyph),flags) in enumerate(cases):
        mem=list(source)
        for i in range(1024):mem[0xa000+i]=(i*37+index*19)&255
        for i in range(256):mem[0xff00+i]=(i*23+index)&255
        xx=index&7;mem[0xe0+xx]=height
        for at,pointer in [(0x0e,dest),(0x26ab,glyph),(0x26e4,glyph),(0x26ee,(glyph+1)&65535)]:mem[at]=pointer&255;mem[at+1]=pointer>>8
        stack=(index*17)&255;mem[0x100+((stack+1)&255)]=0xfe;mem[0x100+((stack+2)&255)]=0xff
        z=0 if wide else 1;p=0x20|(flags&0xc9)|(z<<1)
        rr=regarr(37,xx,yy,p&1,(p>>1)&1,p>>7,(p>>6)&1,(p>>3)&1,stack,0)
        dll.bl_contact_seed(arr(*mem),rr)
        cpu=MPU(memory=mem,pc=0x26a0);cpu.a=37;cpu.x=xx;cpu.y=yy;cpu.p=p;cpu.sp=stack
        fault=False
        for step in range(20000):
            if cpu.pc==0x2703:fault=True;break
            at=cpu.pc;cpu.step()
            if at==0x26d6:break
        else:raise AssertionError(('Source did not terminate',index,hex(cpu.pc)))
        instructions+=step+1
        dll.bl_contact_run(0x26a0);dll.bl_contact_copy(out);dll.bl_contact_regs(regs)
        assert list(out)==mem,('RAM',index,wide,height,yy,hex(dest),hex(glyph),[(hex(i),out[i],v) for i,v in enumerate(mem) if out[i]!=v][:8])
        expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,0]
        assert list(regs)==expected,('Registers',index,list(regs),expected)
        assert dll.bl_contact_fault()==(0x2703 if fault else 0),('Fault',index)
        if not fault:assert dll.bl_contact_return()==cpu.pc,('Return',index)
        faults+=int(fault);aliases+=int(glyph in (dest,0x2770));checks+=1
    paths=['core/c64_rooms.c','core/c64_actor_programs.h','tools/build_c64_rooms.py','tools/verify_source_sprite_copy.py','tests/source_contact_bridge.c']
    report=dict(status='passed_original_sprite_copy_bytes',source_sha256=SOURCE,checks=checks,instructions=instructions,brk_controls=faults,alias_controls=aliases,
        edition_verified=False,natural_playthrough=False,scope='Full64KiB/register/return comparisons; injected widths/heights, byte Y/SP, source/count/destination aliases and wrapping sources',
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (ROOT/'reference/validation/source-sprite-copy-host.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print('PASS',checks,'sprite copy controls;',instructions,'actual source instructions;',faults,'BRK boundaries')
if __name__=='__main__':main()
