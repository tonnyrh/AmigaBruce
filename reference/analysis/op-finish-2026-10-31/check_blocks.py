"""Differential test of the candidate C bodies against individual frozen instructions."""
import ctypes
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-finish/block-proof"
sys.path.insert(0,str(ROOT/".reference/tools/python"))
from py65.devices.mpu6502 import MPU

def compile_helpers():
    WORK.mkdir(parents=True,exist_ok=True)
    unit=WORK/"blocks.c"
    unit.write_text("""static unsigned char *m,a,x,y,c,z,n,v,d,sp;
static unsigned char index_ready,actor_loading_pending=1;
static unsigned short actor_return;
static unsigned short W(unsigned short p){return m[p]|(m[p+1]<<8);}
static void reset_contact_masks(void){}
#define NZ(q) do {z=((q)==0);n=(((q)&128)!=0);}while(0)
"""+(HERE/"field.c").read_text()+(HERE/"history.c").read_text()+(HERE/"room_run.c").read_text()+"""
__declspec(dllexport) void run(unsigned char *ram,unsigned char *r,int field){
    m=ram;a=r[0];x=r[1];y=r[2];c=r[3];z=r[4];n=r[5];v=r[6];d=r[7];sp=r[8];
    if(field==2)source_room_token();else if(field)source_field_timers();else source_shift_history();
    r[0]=a;r[1]=x;r[2]=y;r[3]=c;r[4]=z;r[5]=n;r[6]=v;r[7]=d;
    r[8]=sp;
}
""")
    vswhere=Path(os.environ["ProgramFiles(x86)"])/"Microsoft Visual Studio/Installer/vswhere.exe"
    vs=Path(subprocess.check_output([vswhere,"-latest","-products","*","-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],text=True).strip())
    batch=WORK/"compile.cmd"
    batch.write_text(f'@call "{vs}/VC/Auxiliary/Build/vcvars64.bat" >nul\n@cl /nologo /LD /O2 blocks.c /link /out:blocks.dll\n')
    subprocess.run([str(batch)],cwd=WORK,check=True)
    return ctypes.CDLL(str(WORK/"blocks.dll"))

def main():
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    digest=hashlib.sha256(frozen).hexdigest()
    assert digest=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    lib=compile_helpers()
    u8=ctypes.c_ubyte
    rng=random.Random(0x15bd1c79)
    for i in range(2048):
        field=i>=384
        start,end=(0x15bd,0x169d) if field else (0x1c79,0x1c8f)
        m=bytearray(frozen)
        cpu=MPU(memory=m,pc=start)
        cpu.a,cpu.x,cpu.y,cpu.sp=rng.randbytes(4)
        cpu.p=rng.randrange(256)
        if field:
            for addr in (0x4eec,0x104,0x105,0x42ca,0x42c9,0x1383,0x1384,0x87,0x88,0x7f,0x80,0x81,0x82,0x48,0x49,0x4a,0xdc02,0xdc03):
                m[addr]=rng.choice((0,1,126,127,128,254,255))
            if m[0x7f]==255 and m[0x82]==127:m[0x82]=126 # two original JSRs stay on fallback
            m[0xf2]=i&255
            m[0x47b4:0x47c8]=rng.randbytes(20)
        else:
            cpu.x=i%3;cpu.p&=~8
            m[0x4f57:0x4fdd]=rng.randbytes(134)
        native=(u8*65536).from_buffer_copy(m)
        def state():
            return [cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
        r=(u8*10)(*state())
        for _ in range(1000):
            if cpu.pc==end:break
            cpu.step()
        assert cpu.pc==end
        lib.run(native,r,int(field))
        assert bytes(native)==m and list(r)==state(),(i,start,list(r),state(),next((j for j,v in enumerate(native) if m[j]!=v),None))
    result=dict(frozen_sha256=digest,history_cases=384,field_cases=1664,bytes_per_case=65536)
    tokens=cells=0
    for room in range(20):
        m=bytearray(frozen)
        for zp,value in ((4,0x8c78),(8,0x8ca0),(16,0xd878),(18,0xd8a0),
                         (6,m[0x4b34+room]|m[0x4b49+room]<<8)):
            m[zp:zp+2]=value.to_bytes(2,"little")
        m[0xf3]=39
        cpu=MPU(memory=m,pc=0xad7);cpu.y=0;cpu.p=0x31;cpu.sp=room*13
        while m[int.from_bytes(m[6:8],"little")]!=128:
            code=m[int.from_bytes(m[6:8],"little")]
            native=(u8*65536).from_buffer_copy(m)
            r=(u8*10)(*state());lib.run(native,r,2)
            cpu.step()
            for _ in range(40000):
                if cpu.pc==0xad7:break
                cpu.step()
            assert cpu.pc==0xad7 and bytes(native)==m and list(r)==state(),(room,tokens,list(r),state(),next((j for j,v in enumerate(native) if m[j]!=v),None))
            tokens+=1;cells+=code&127
    skipped=0
    for sp in (0,1,254,255):
        for anomaly in ("end","zero","address","color","lower","row","decimal","y"):
            m=bytearray(frozen)
            for zp,value in ((4,0x8c78),(6,0x7000),(8,0x8ca0),(16,0xd878),(18,0xd8a0)):
                m[zp:zp+2]=value.to_bytes(2,"little")
            m[0xf3]=40 if anomaly=="row" else 39
            m[0x7000]={"end":128,"zero":0}.get(anomaly,1)
            if anomaly=="address":m[7]=1
            if anomaly=="lower":m[8]^=1
            if anomaly=="color":m[0x13]^=1
            regs=[171,72,int(anomaly=="y"),1,0,1,0,int(anomaly=="decimal"),sp,0]
            r=(u8*10)(*regs);native=(u8*65536).from_buffer_copy(m)
            lib.run(native,r,2)
            assert list(r)==regs and bytes(native)==m
            skipped+=1
    result.update(room_tokens=tokens,room_cells=cells,rooms=20,unchanged_fallbacks=skipped)
    print(result)
    (WORK/"result.json").write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":main()
