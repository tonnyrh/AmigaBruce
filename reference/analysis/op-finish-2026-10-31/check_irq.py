"""Exercise the normal-field shortcut including the source publisher, input seam and VIC latch."""
import ctypes as ct
import json
import random
import sys
from check_images import ROOT,WORK,dll,frames,MPU
sys.path.insert(0,str(ROOT/"tools"))
from audit_c64_world import vic

def main():
    unit=(ROOT/"tests/source_contact_bridge.c").read_text().replace("../core/c64_rooms.c",(WORK/"irq/c64_rooms.c").as_posix())
    for n in ("bl_contact_seed","bl_contact_copy","bl_contact_regs"):
        unit=unit.replace("void "+n+"(","__declspec(dllexport) void "+n+"(")
    unit+="""
__declspec(dllexport) void tick(long joy,long joy2){
    actor_world_enabled=1;actor_input=joy;actor_yamo_input=joy2;source_actor_field();
}
"""
    lib=dll("field-irq-proof",unit)
    base=frames((ROOT/".reference/c64/work/op4-moving-audio-2026-10-31/combat168/combat.bin").read_bytes())[1][2]
    rnd=random.Random(0x15b8);byte=ct.c_ubyte
    direction=lambda j:15^((j&1)<<2|(j&2)<<2|(j&4)>>2|(j&8)>>2)
    hits=0
    for i in range(1024):
        m=bytearray(base);m[2]=0x32;m[0x42ca]=int(i>=960)
        m[0x277e]=(i>>3)&1;m[0x277d]=(i>>4)&1
        for a in range(3):
            m[0x95+a]=(m[0x95+a]&254)|((i>>a)&1)
            m[0x9e+a]=rnd.randrange(256);m[0xa1+a]=rnd.randrange(256)
        for address in (0x104,0x105,0x87,0x88,0x7f,0x80,0x82,0x4eec):
            m[address]=rnd.choice([0,1,127,128,255])
        if m[0x7f]==255 and m[0x82]==127:m[0x82]=126
        m[0x7a]=int(i>=960) # human-mode fallback leaves its idle counter alone
        before=bytes([*rnd.randbytes(3),*[rnd.randrange(2) for _ in range(5)],i&255,0])
        joy=i&31;joy2=(i>>4)&31
        lib.bl_contact_seed((byte*65536).from_buffer_copy(m),(byte*10)(*before))
        lib.tick(joy,joy2)
        m[0x44]=0;u=MPU(memory=m,pc=0x15b8)
        u.a,u.x,u.y=before[:3];u.sp=before[8];u.p=0x30|before[3]|(before[4]<<1)|(before[5]<<7)|(before[6]<<6)
        def advance(stop):
            for _ in range(2000):
                if u.pc==stop:return
                u.step()
            raise AssertionError(hex(u.pc))
        advance(0x169d)
        m[0x98]=direction(joy);m[0x9b]=int(not joy&16)
        if m[0x42ca]:m[0x99]=direction(joy2);m[0x9c]=int(not joy2&16)
        m[0xdc00]=m[0xdc01]=255;u.pc=0x1703;advance(0x179d)
        m[0xd01e]|=vic(m)
        mem=(byte*65536)();r=(byte*10)();lib.bl_contact_copy(mem);lib.bl_contact_regs(r)
        assert bytes(mem)==m and bytes(r)==before,(i,next((hex(j) for j,v in enumerate(mem) if v!=m[j]),None))
        hits+=int(not m[0x42ca])
    result=dict(cases=1024,common=hits,human_fallback=1024-hits,ram_bytes=65536)
    (WORK/"irq-proof.json").write_text(json.dumps(result,indent=2)+"\n")
    print(result)

if __name__=="__main__":main()
