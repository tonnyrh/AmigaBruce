"""Compare folded and ordinary Kage results with the actual 6502 bytes."""
import ctypes
import json
import random
import struct
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/kage-paula"
sys.path.insert(0,str(HERE.parent/"op4-moving-audio-2026-10-31"))
from audit_combat import Bus,MPU,frames,regs,sha

def host(folder,engine):
    folder.mkdir(exist_ok=True)
    core=(engine/"c64_rooms.c").read_text()
    if engine==WORK/"fold":assert (HERE/"kage.c").read_text() in core
    actor=(engine/"c64_actor_programs.h").read_text()
    label="L2c1d:; /* $2C1D */"
    (folder/"c64_actor_programs.h").write_text(actor.replace(label,label+"\nif(stop_at_damage){actor_return=0x2c1d;return;}"))
    (folder/"c64_rooms.c").write_text("static int stop_at_damage;\n"+core)
    bridge=(ROOT/"tests/source_contact_bridge.c").read_text().replace("../core/c64_rooms.c","c64_rooms.c")
    bridge+='\nvoid damage_mode(int isolated){stop_at_damage=isolated;actor_world_enabled=1;actor_invincible=!isolated;}\n'
    (folder/"bridge.c").write_text(bridge)
    for c in ("c64_actor_programs.h","c64_rooms.c","bridge.c"):assert (folder/c).is_file()
    vs=Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    install=subprocess.check_output([vs,"-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],text=True).strip()
    exports="bl_contact_seed bl_contact_run bl_contact_copy bl_contact_regs bl_contact_return bl_contact_fault damage_mode".split()
    script=folder/"compile.cmd"
    script.write_text(f'@call "{install}/VC/Auxiliary/Build/vcvars64.bat" >nul\n@cl /nologo /LD /O2 /W3 /I"{ROOT}/core" /Fe:proof.dll bridge.c /link '+" ".join("/EXPORT:"+s for s in exports)+"\n")
    subprocess.run(["cmd","/d","/c","compile.cmd"],cwd=folder,check=True)
    return ctypes.CDLL(str(folder/"proof.dll"))

def main(folder=WORK/"proof",engine=WORK/"fold",actors=(2,)):
    lib=host(folder,engine);rng=random.Random(0x2bf9);buf=(ctypes.c_ubyte*65536)();out=(ctypes.c_ubyte*10)()
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    assert sha(frozen)=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    steps=count=awards=life=0
    vectors=bytearray(4)
    def run(r,ram,entry,stop):
        nonlocal steps,count,awards,life
        b=Bus(ram);cpu=MPU(memory=b,pc=entry);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
        cpu.p=0x30|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
        lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(ram),(ctypes.c_ubyte*10)(*r))
        lib.damage_mode(entry==0x2bf9)
        for i in range(200000):
            if cpu.pc==stop:break
            if cpu.pc==0x2b4e and entry==0x29c3:b.m[0xbc]&=1
            awards+=cpu.pc==0x3175;life+=cpu.pc==0x3146
            cpu.step()
        else:raise AssertionError((entry,count,hex(cpu.pc)))
        steps+=i;lib.bl_contact_run(entry);lib.bl_contact_copy(buf);lib.bl_contact_regs(out)
        assert lib.bl_contact_return()==stop and not lib.bl_contact_fault()
        assert bytes(buf)==b.m,(count,[(hex(j),buf[j],b.m[j]) for j in range(65536) if buf[j]!=b.m[j]][:12])
        assert bytes(out)==regs(cpu),(count,list(out),list(regs(cpu)))
        vectors.extend(bytes([entry==0x2bf9])+bytes(r)+regs(cpu)+bytes(ram)+bytes(b.m))
        count+=1
    for name in ("combat168","combat207"):
        data=(ROOT/".reference/c64/work/op4-moving-audio-2026-10-31"/name/"combat.bin").read_bytes()
        _,r,m=frames(data)[0];run(r,m,0x29c3,0x1c26)
    for actor in actors:
        for hp in [*range(0,256,5),1,2,3,4,128,132,133,254,255]:
            for j in range(2):
                m=bytearray(frozen);m[0xbc+actor]=0x90;m[0x51]=actor;m[0xd1+actor]=hp
                score=rng.choice([425,6975,0xfffefe,0x7fffff,rng.randrange(1<<24)])
                threshold=rng.choice([10000,0xffffff,(score+rng.choice([50,250,500,2500]))&0xffffff])
                m[0x41:0x44]=score.to_bytes(3,"big");m[0x4392:0x4395]=threshold.to_bytes(3,"big")
                m[0x438e:0x4391]=(10000).to_bytes(3,"big")
                r=bytes([rng.randrange(256),actor,rng.randrange(256),1,0,1,1,0,rng.choice([0,1,14,128,220,255]),j])
                run(r,m,0x2bf9,0x2c1d)
    report=dict(frozen_sha256=sha(frozen),cases=count,full_combats=2,ram_bytes=65536,registers=10,
                source_instructions=steps,source_awards=awards,source_extra_lives=life)
    struct.pack_into(">I",vectors,0,count)
    (folder/"cases.bin").write_bytes(vectors)
    (folder/"result.json").write_text(json.dumps(report,indent=2)+"\n");print(report)

if __name__=="__main__":main()
