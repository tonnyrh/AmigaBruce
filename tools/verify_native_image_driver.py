"""Whole64KiB/register/return comparisons with the actual frozen2584 bytes."""
import ctypes,hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
BASE=ROOT/'reference/analysis/enemy-cost-2026-10-30'
def main():
    raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    lib=ctypes.CDLL(str(ROOT/'.tmp/native-image-driver/candidate.dll'));U=ctypes.c_ubyte;A=U*65536;R=U*10;out=A();regs=R()
    lib.bl_contact_seed.argtypes=[ctypes.POINTER(U),ctypes.POINTER(U)];lib.bl_contact_run.argtypes=[ctypes.c_long];lib.bl_contact_copy.argtypes=[ctypes.POINTER(U)];lib.bl_contact_regs.argtypes=[ctypes.POINTER(U)]
    lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ctypes.c_ulong
    cases=list(itertools.product(range(8),[0,1],[0,1,2,127,253,254,255],[0,1,0xc0,0xc1],[0,2,20,44,68]))
    cases += [(7,bank,stack,(stack>>4)&0xc1,(stack%35)*2) for bank in [0,1] for stack in range(256)]
    rng=random.Random(20261030);cases += [(rng.randrange(8),rng.randrange(2),rng.randrange(256),rng.choice([0,1,0xc0,0xc1]),rng.randrange(70)) for _ in range(256)]
    standard=len(cases)
    mutations=list(itertools.product([0,0x0100,0x01f0,0x2770,0x8000,0x8140,0xc000,0xff00],[0,1,20,21,31],[0,1],[0,1,253,255]))
    cases += [(7,i&1,q[3],0xc1,0) for i,q in enumerate(mutations)]
    instructions=0
    for index,(mask,bank,stack,flags,pose) in enumerate(cases):
        mem=bytearray(raw);mem[0x277d]=bank
        for actor in range(3):mem[0x95+actor]=[1,0x81,0x41][actor] if mask&(1<<actor) else 0;mem[0x4f4e+actor]=(pose+actor*70)&255
        if index>=standard:
            pointer,height,width,_=mutations[index-standard]
            for actor in range(3):
                for part in [0,1]:
                    q=actor*70+part;mem[0x59bd+q]=pointer&255;mem[0x5a8f+q]=pointer>>8;mem[0x5b61+q]=height;mem[0x5cbf+q]=width
        # The source-selected destination tables and glyphs remain actual data.
        # Change scratch, SP/status, and one selected glyph byte every time.
        mem[0x277f]=(index*13)&255;mem[0x5d91+index%200]=(index*31)&255
        mem[0x100+((stack+1)&255)]=0xfe;mem[0x100+((stack+2)&255)]=0xff
        yy=(index*73)&255;p=0x20|(flags&0xc1);r=R(37,91,yy,p&1,0,p>>7,(p>>6)&1,0,stack,0)
        cpu=MPU(memory=bytearray(mem),pc=0x2584);cpu.a=37;cpu.x=91;cpu.y=yy;cpu.p=p;cpu.sp=stack
        lib.bl_contact_seed(A.from_buffer_copy(mem),r)
        for count in range(50000):
            at=cpu.pc;cpu.step()
            if at==0x25e1:break
            if cpu.pc==0x2703:raise AssertionError(('Unexpected source BRK',index))
        else:raise AssertionError(('Unfinished source',index,hex(cpu.pc)))
        instructions+=count+1;lib.bl_contact_run(0x2584);lib.bl_contact_copy(out);lib.bl_contact_regs(regs)
        expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,0]
        assert bytes(out)==bytes(cpu.memory),('RAM',index,mask,bank,stack,pose,[(hex(j),out[j],v) for j,v in enumerate(cpu.memory) if out[j]!=v][:12])
        assert list(regs)==expected,('Registers',index,list(regs),expected)
        assert lib.bl_contact_fault()==0 and lib.bl_contact_return()==cpu.pc,('Control',index)
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    report=dict(status='passed_native_image_driver_original_bytes',source_sha256=sha,cases=len(cases),alias_height_controls=len(mutations),instructions=instructions,all_ram_register_return=True,edition_verified=False,natural_playthrough=False,
        artifacts=[item(p) for p in [BASE/'image-driver/c64_rooms.c',BASE/'image-driver/c64_actor_programs.h',BASE/'image-driver/image_driver.h',BASE/'image-driver-bridge.c',Path(__file__),ROOT/'test-native-image-driver.ps1']])
    (BASE/'image-driver-source.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'complete RAM/register/return cases;',instructions,'actual source instructions')
if __name__=='__main__':main()
