"""Run the frozen 6502 driver to build RAM/register witnesses for the native A500 pilot."""
import ctypes, hashlib, json, random, struct, sys
from pathlib import Path
from build_pilot import ROOT, HERE, WORK
sys.path.insert(0,str(HERE.parent/"op1-contact-budget-2026-10-31"))
from audit import MPU, Disassembler, registers, records, SOURCE_SHA, sha
from functools import lru_cache
FROZEN=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
assert sha(FROZEN)==SOURCE_SHA
DIS=Disassembler(MPU(memory=FROZEN))
PATCHED={0x52cc,0x52cd,0x5381,0x5382,0x539b,0x539c,0x53b5,0x53b6}
@lru_cache(None)
def fixed_bytes(pc):
    size=DIS.instruction_at(pc)[0]
    return tuple((i,FROZEN[i]) for i in range(pc,pc+size) if i==pc or i not in PATCHED)

def entry(label):
    p=ROOT/".reference/c64/work/op1-contact-budget-2026-10-31"/label/"capture.bin"
    _,r,m=records(p.read_bytes())[0]
    return r,bytes(m)
def source_run(memory,regs,mutation):
    m=bytearray(memory);cpu=MPU(memory=m,pc=0x5212)
    r=regs;cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
    cpu.p=0x30|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
    count=steps=0;first=prefix_regs=None
    ret=1+(m[256+((r[8]+1)&255)]|m[256+((r[8]+2)&255)]<<8)
    while steps<150000:
        if cpu.pc==ret:break
        if cpu.pc==0x5214 or (cpu.pc==0x5380 and not(cpu.y&7)):
            count+=1
            if count==2:
                first=bytes(m);prefix_regs=registers(cpu)
                at,b=mutation;m[at]^=b
        for at,byte in fixed_bytes(cpu.pc):assert m[at]==byte,(hex(cpu.pc),hex(at))
        cpu.step();steps+=1
    else:raise AssertionError("Escaped source")
    assert cpu.pc==0x1c10 and first is not None
    return prefix_regs,first,registers(cpu),bytes(m),count,steps
def key(m):
    y=((m[0xa3]-29)&255)>>3;x=((m[0xa0]-12)&255)>>2
    ptr=m[0x1167+m[0x4f50]]|m[0x1239+m[0x4f50]]<<8
    tile=m[0x50e7+y]|m[0x50ff+y]<<8;attr=m[0x50e7+y]|m[0x5117+y]<<8
    if not(0<=y<24 and 0<=x<=37 and 0x8000<=tile<=0x9fd8 and 0xd800<=attr<=0xdbd8 and 0x6000<=ptr<=0xca80 and ptr%2==0):return None
    return (m[0xa0],m[0xa3],m[0x4f50],m[0x29],m[0x7c],ptr,tile,attr,m[ptr:ptr+96],m[tile+x:tile+x+3],m[attr+x:attr+x+3])
def cases():
    r,base=entry("state240");_,other=entry("state400")
    def case(label,m=base,regs=r,inject=(0,0)):return label,regs,bytes(m),inject
    def edit(label,at,mask):
        m=bytearray(base);m[at]^=mask;return case(label,m)
    yield case("cold");yield case("identical")
    for sp in (0,1,2,3,127,255):
        rr=bytearray(r);rr[8]=sp;m=bytearray(base);m[256+((sp+1)&255)]=0x0f;m[256+((sp+2)&255)]=0x1c
        yield case("stack-"+str(sp),m,rr)
    # Change destination bytes, including undisturbed slack and wrapping stack.
    rng=random.Random(0x5214);m=bytearray(base)
    for lo,hi in ((0x4eed,0x4f40),(0xcae0,0xcb68),(0x1f2,0x1fc)):
        m[lo:hi]=rng.randbytes(hi-lo)
    yield case("scratch-and-tail",m)
    ptr,screen,attr=key(base)[5:8];col=((base[0xa0]-12)&255)>>2
    for i in range(96):
        yield edit("mask-byte-"+str(i),ptr+i,128)
    yield case("mask-restored")
    for name,start in (("tile",screen+col),("attr",attr+col)):
        for i in range(3):
            yield edit(name+str(i),start+i,3);yield case(name+"-restore-"+str(i))
    for address in (0x29,0x7c,0x4f50,0x50e7+20,0x50ff+20,0x5117+20,0x1167+base[0x4f50],0x1239+base[0x4f50]):
        yield edit("key-"+hex(address),address,1);yield case("restore-"+hex(address))
    for dx in range(4):
        for dy in range(8):
            m=bytearray(base);m[0xa0]+=dx;m[0xa3]+=dy
            yield case(f"phase-{dx}-{dy}",m);yield case(f"hit-{dx}-{dy}",m)
    for addr,value in ((0xa0,255),(0xa0,7),(0xa3,3),(0x50ff+20,0x4e),(0x5117+20,1),
                       (0x1167+base[0x4f50],0xff),(0x1239+base[0x4f50],0xcb)):
        m=bytearray(base);m[addr]=value;yield case("fallback-"+hex(addr)+"-"+str(value),m)
    yield case("rebuild");yield case("second-capture",other);yield case("second-hit",other)
    # Changing glyph pixels, including after the guard in the row callback,
    # must feed the unmodified row scanner. Force a nonblank first glyph.
    m=bytearray(other);m[0xa3]-=7
    tile=key(m)[6]+col;glyph=(m[0x7c]<<8)+0xd0*8
    m[tile:tile+3]=bytes((0xd0,0xd1,0xd2));m[glyph:glyph+24]=bytes(24)
    yield case("glyph-setup",m)
    yield case("changed-at-service",m,inject=(glyph+11,255))
    m[glyph+11]=255
    yield case("animated-glyph",m)
    m=bytearray(base);m[0x97]&=254;yield case("inactive",m)
    # Use the project's decoded room and charset bytes, with Kage placed
    # explicitly on the room 1 central climbing area and the R12 stairs.
    lib=ctypes.CDLL(str(ROOT/".tmp/source-actor-test/actors.dll"))
    lib.bl_actor_prepare.argtypes=[ctypes.c_long]
    for room,px,py in ((0,86,144),(11,45,90),(0,35,196)):
        lib.bl_actor_prepare(room);buf=(ctypes.c_ubyte*65536)();lib.bl_actor_copy(buf);layout=bytes(buf)
        if room==0:layout=base
        assert layout[0x7c] in (0xa0,0xa8,0xb0,0xb8)
        m=bytearray(base);m[0x29]=room;m[0x7c]=layout[0x7c]
        for start,end in ((0x8c00,0x9000),(0xd800,0xdc00),(0x50e7,0x512f),(m[0x7c]<<8,(m[0x7c]<<8)+2048)):
            m[start:end]=layout[start:end]
        m[0xa0]=px;m[0xa3]=py
        yield case("room-"+str(room+1),m);yield case("room-hit-"+str(room+1),m)
def generate():
    assert sha((ROOT/".reference/c64/work/untrained-memory.bin").read_bytes())==SOURCE_SHA
    work=WORK/"proof";work.mkdir(exist_ok=True)
    dll=ctypes.CDLL(str(work/"prefix.dll"))
    dll.pilot_ram.restype=ctypes.c_void_p;dll.pilot_witness.restype=ctypes.c_uint32
    dll.pilot_witness.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p]
    details=[];prior=None
    with (work/"cases.bin").open("wb") as f:
        f.write(bytes(4));total=0
        for name,r,m,inject in cases():
            rk,first,rf,end,count,steps=source_run(m,r,inject)
            token=key(m)
            if not m[0x97]&1:path=3
            elif token is None:path=2;prior=None
            elif token==prior:path=0
            else:path=1;prior=token
            header=bytes(r)+rk+rf+struct.pack(">HBBB",*inject,path,count)
            ctypes.memmove(dll.pilot_ram(),m,65536);error=dll.pilot_witness(header,first,end)
            assert not error,(name,path,hex(error))
            details.append(dict(case=name,path=["hit","fill","bypass","inactive"][path],instructions=steps,
                                first_sha256=sha(first),return_sha256=sha(end),body=end[0xa9],foot=end[0xb8]))
            f.write(header+m+first+end);total+=1
        f.seek(0);f.write(struct.pack(">I",total))
    glyph=[(q["case"],q["path"],q["body"],q["foot"]) for q in details
           if q["case"] in ("glyph-setup","changed-at-service","animated-glyph")]
    assert glyph==[("glyph-setup","fill",0,2),("changed-at-service","hit",4,6),("animated-glyph","hit",4,6)]
    assert any(q["case"]=="room-hit-1" and q["foot"]&4 for q in details)
    (work/"oracle.json").write_text(json.dumps(dict(source_sha256=SOURCE_SHA,cases=details),indent=2)+"\n")
    print("PASS",total,"full memory/register controls at the service and at driver return;",
          sum(x["instructions"] for x in details),"source instructions")
if __name__=="__main__":generate()

