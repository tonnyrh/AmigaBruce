"""Compare every cached byte with the scalar renderer and the sprite driver with C64."""
import ctypes as ct
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-finish"
sys.path.insert(0,str(HERE.parent/"op4-moving-audio-2026-10-31"))
from audit_combat import Bus,MPU,frames,regs

def dll(name,code,defines=""):
    base=WORK/name;base.mkdir(exist_ok=True)
    (base/"bridge.c").write_text(code)
    vswhere=Path(os.environ["ProgramFiles(x86)"])/"Microsoft Visual Studio/Installer/vswhere.exe"
    vs=Path(subprocess.check_output([vswhere,"-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],text=True).strip())
    cmd=base/"build.cmd"
    cmd.write_text(f'@call "{vs}/VC/Auxiliary/Build/vcvars64.bat" >nul\n@cl /nologo /w /LD /O2 {defines} /I"{ROOT}/core" bridge.c /link /out:bridge.dll\n')
    subprocess.run([str(cmd)],cwd=base,check=True)
    return ct.CDLL(str(base/"bridge.dll"))

def main():
    byte=ct.c_ubyte
    image_cases=0
    source=(ROOT/"core/c64_rooms.c").as_posix()
    wrapper=f'#include "{source}"\n'+'''
__declspec(dllexport) long picture(unsigned char *out,long room,long variant){
    bl_c64_reset();bl_c64_load(room);
    if(variant){ /* Band changes, different per-cell colors and patterns. */
        unsigned short p=W(0x4833+2*room);
        m[p]=63+variant; m[(room<10?0x42f1:0x4309)+3]^=0xf0;
        for(unsigned short i=120;i<1000;i+=7)m[0xd800+i]^=3;
        prepare_palette();
    }
    return bl_c64_build_animation_cache(out,106496);
}
'''
    libs=[dll("image-"+str(i),wrapper,"/DBL_ROOM_REUSE="+str(i)) for i in range(2)]
    for room in range(20):
        for variant in range(3):
            expected=None
            for lib in libs:
                out=(byte*106512)()
                ct.memset(out,0xa5,len(out));offset=variant+2
                count=lib.picture(ct.byref(out,offset),room,variant)
                assert 0<=count<=106496
                assert bytes(out[:offset])==b"\xa5"*offset and bytes(out[offset+count:])==b"\xa5"*(len(out)-offset-count)
                picture=(count,bytes(out[offset:offset+count]))
                if expected is None:expected=picture
                else:assert picture==expected,(room,variant,count)
            image_cases+=1
    code=(ROOT/"tests/source_contact_bridge.c").read_text().replace("../core/c64_rooms.c",(WORK/"component/c64_rooms.c").as_posix())
    for func in ("bl_contact_seed","bl_contact_run","bl_contact_copy","bl_contact_regs","bl_contact_trace_enable","bl_contact_trace"):
        code=code.replace("void "+func+"(","__declspec(dllexport) void "+func+"(").replace("long "+func+"(","__declspec(dllexport) long "+func+"(")
    lib=dll("image-driver-proof",code)
    sprite_cases=0
    for cap in ("combat168","combat207"):
        path=ROOT/".reference/c64/work/op4-moving-audio-2026-10-31"/cap/"combat.bin"
        _,r,m=frames(path.read_bytes())[1]
        bus=Bus(m);cpu=MPU(memory=bus,pc=0x1c26);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
        cpu.p=0x30|r[3]|(r[4]<<1)|(r[5]<<7)|(r[6]<<6)|(r[7]<<3)|(r[9]<<2)
        while cpu.pc!=0x2584:cpu.step()
        for mask in range(8):
            for pose in (None,1,6,12,25,64,77,128):
                ram=Bus(bytes(bus.m));u=MPU(memory=ram,pc=cpu.pc)
                u.a,u.x,u.y,u.sp,u.p=cpu.a,cpu.x,cpu.y,cpu.sp,cpu.p
                for actor in range(3):
                    ram.m[0x95+actor]=(ram.m[0x95+actor]&254)|((mask>>actor)&1)
                    if pose is not None:ram.m[0x4f4e+actor]=pose+actor
                lib.bl_contact_seed((byte*65536).from_buffer_copy(ram.m),(byte*10)(*regs(u)))
                lib.bl_contact_trace_enable();trace=bytearray()
                for _ in range(30000):
                    if u.pc==0x1c2f:break
                    if u.pc==0x2586:trace.extend(regs(u))
                    u.step()
                assert u.pc==0x1c2f
                lib.bl_contact_run(0x2584)
                mem=(byte*65536)();actual=(byte*10)();calls=(byte*640)()
                lib.bl_contact_copy(mem);lib.bl_contact_regs(actual)
                assert bytes(mem)==ram.m and bytes(actual)==regs(u),(cap,mask,pose)
                assert lib.bl_contact_trace(calls)==3 and bytes(calls[:30])==trace
                sprite_cases+=1
    result=dict(cache_cases=image_cases,sprite_cases=sprite_cases,service_boundaries=sprite_cases*3)
    (WORK/"image-proof.json").write_text(json.dumps(result,indent=2)+"\n")
    print(result)

if __name__=="__main__":main()
