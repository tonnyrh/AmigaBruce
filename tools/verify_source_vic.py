"""Pixel/latch cache control, not original VIC raster/border certification."""
import ctypes,hashlib,json,random
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=256)
def rows(bitmap,multi,wide):
    result=[]
    for row in range(21):
        value=int.from_bytes(bitmap[row*3:row*3+3],'big');mask=0
        for col in range(24):
            on=(value>>(22-(col//2)*2))&3 if multi else (value>>(23-col))&1
            if on:mask|=((3 if wide else 1)<<(col*(2 if wide else 1)))
        result.append(mask)
    return result
def expected(m):
    active=m[0xd015];bank=((~m[0xdd00])&3)<<14;matrix=(bank+((m[0xd018]>>4)<<10))&65535;ss=[]
    for i in range(8):
        if not active&(1<<i):continue
        pointer=(bank+(m[(matrix+0x3f8+i)&65535]<<6))&65535
        bitmap=bytes(m[(pointer+j)&65535] for j in range(63))
        x=m[0xd000+2*i]+(256 if m[0xd010]&(1<<i) else 0);y=m[0xd001+2*i]
        image=rows(bitmap,bool(m[0xd01c]&(1<<i)),bool(m[0xd01d]&(1<<i)))
        tall=2 if m[0xd017]&(1<<i) else 1
        ss.append((i,x,y,tall,image))
    bits=0
    for a,(i,x,y,h,image) in enumerate(ss):
        for j,xx,yy,hh,other in ss[a+1:]:
            for dy in range(max(y,yy),min(y+21*h,yy+21*hh)):
                if (image[(dy-y)//h]<<x)&(other[(dy-yy)//hh]<<xx):bits|=(1<<i)|(1<<j);break
    return bits
def main():
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-vic-test/vic.dll'))
    lib.bl_vic_write.argtypes=[ctypes.c_long,ctypes.c_long]
    lib.bl_vic_sample.restype=lib.bl_vic_take.restype=ctypes.c_ubyte
    rng=random.Random(20261027);calls=0
    def seed(m):lib.bl_vic_seed((ctypes.c_ubyte*65536).from_buffer_copy(m))
    def write(m,at,value):m[at]=value;lib.bl_vic_write(at,value)
    def check(m,clear=True):
        nonlocal calls
        m[0xd01e]|=expected(m);assert lib.bl_vic_sample()==m[0xd01e],calls
        if clear:assert lib.bl_vic_take()==m[0xd01e];m[0xd01e]=0
        calls+=1
    for case in range(80):
        m=bytearray(rng.randbytes(65536));m[0xd01e]=0;m[0xdd00]=3;m[0xd018]=0x10
        # Dense sprite pairs plus all expansion/multicolor combinations.
        for i in range(8):
            m[0xd000+2*i]=rng.randrange(80,125);m[0xd001+2*i]=rng.randrange(90,115);m[0x7f8+i]=128+i
        m[0xd010]=0;seed(m)
        for step in range(40):
            check(m,step%3!=0);check(m) # unchanged content, including after latch clear
            kind=step%10
            if kind==0:write(m,0xd000+rng.randrange(16),rng.randrange(256))
            elif kind==1:write(m,rng.choice([0xd010,0xd015,0xd017,0xd01c,0xd01d]),rng.randrange(256))
            elif kind==2:write(m,0x2000+rng.randrange(8*64),rng.randrange(256))
            elif kind==3:write(m,0x7f8+rng.randrange(8),rng.randrange(128,136))
            elif kind==4:write(m,0xd018,rng.randrange(16)<<4)
            elif kind==5:write(m,0xdd00,rng.randrange(4))
            elif kind==6:write(m,0xd015,0) # disabled and reenabled must not retain stale collisions
            elif kind==7:write(m,0xd015,255)
            elif kind==8:write(m,0xd01e,rng.randrange(256)) # externally accumulated bits
            else:write(m,rng.randrange(65536),rng.randrange(256))
        check(m)
    # One opaque pair: content/alias changes, zero cache result, latch reaccumulation.
    m=bytearray(65536);m[0xdd00]=3;m[0xd018]=0x10;m[0xd015]=3
    m[0x7f8]=m[0x7f9]=128;m[0x2000]=128;seed(m);check(m);check(m)
    write(m,0x2000,0);check(m);check(m);write(m,0x2000,128);check(m)
    # Exact rectangle-cache key transitions. Cached zero/contact results
    # must respond to size/high-X changes; unchanged geometry must still
    # detect bitmap mutations and reaccumulate a cleared VIC latch.
    for first in range(8):
        second=(first+1)%8;left=1<<first;right=1<<second
        m=bytearray(65536);m[0xdd00]=3;m[0xd018]=0x10;m[0xd015]=left|right
        m[0x7f8+first]=m[0x7f8+second]=128;m[0x2000:0x203f]=bytes([255])*63
        m[0xd000+2*second]=24;seed(m);check(m);check(m)
        for address,value in [(0xd01d,left),(0xd01d,0),(0xd000+2*second,0),(0xd001+2*second,21),(0xd017,left),(0xd017,0),(0xd001+2*second,0),(0xd010,right),(0xd010,0),(0x2000,0),(0x2000,255),(0xd015,left),(0xd015,left|right)]:
            write(m,address,value);check(m);check(m)
    files=['core/c64_rooms.c','core/c64_rooms.h','core/source_perf.h','tests/source_vic_bridge.c','tools/verify_source_vic.py','test-source-vic.ps1']
    report=dict(status='passed_field_sampled_pixel_and_latch_controls',calls=calls,
        natural_playthrough=False,original_raster_verified=False,source_files=[dict(path=p,
        sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-vic-host.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {calls} pixel/latch/cache controls; all8 sprites, expansions, bank/pointer/bitmap mutations')
if __name__=='__main__':main()
