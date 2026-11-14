from native import *
from rip_c64_room_graphics import source_room
from verify_c64_room_runtime import invoke
from enhanced_architecture import foreground,masonry
from build_enhanced_art import RGB
import hashlib,json
raw=Path('.reference/c64/work/untrained-memory.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def expected(m,r,c,t):
    if look=='classic':
        from rip_c64_room_graphics import render
        return render(m,r).crop(((c-1)*8,(2*t-3)*8,(c+2)*8,(2*t-3)*8+32)).tobytes()
    pix=[]
    base=0xa000 if r<10 else 0xa800
    for dy in range(32):
        y=(2*t-3)*8+dy
        for dx in range(24):
            x=(c-1)*8+dx;cell=y//8*40+x//8;code=m[0x8c00+cell]
            bits=m[base+code*8+y%8];pair=(bits>>(6-2*((x%8)//2)))&3
            pen=foreground(r,code&127,x%8,(code>>7)*8+y%8,pair) if code&127 else None
            pix.append(masonry(x,y,False) if pen is None else pen)
    return bytes(pix)
def region(b,c,t):
    if len(b)!=40960:return b''
    return bytes(sum(((b[(32+y)*160+x//8+p*40]>>(7-x%8))&1)<<p for p in range(4))
                 for y in range((2*t-3)*8,(2*t-3)*8+32) for x in range((c-1)*8,(c-1)*8+24))

records=[]
look='enhanced' if val(addr('enhanced_active'),1) else 'classic'

for col,direction in ((21,1),(34,-1),(21,-1)):
    m=source_room(raw,10); expect={'idle':expected(m,10,col,9)}
    m[0xd800+17*40+col]=0xfd
    m[0x4fe1]=col-1;m[0x4fe4]=8
    for timer,label in ((8,'flash'),(12,'plume'),(20,'restored')):
        m[0x4fde]=timer;invoke(m,0x3228);expect[label]=expected(m,10,col,9)
    start=col*8-12-direction*32;target=max(8,min(290,start+direction*96))
    # Match source test placement. Actual movement/arming/detonation stays live.
    pause()
    try:
        for at,v in {0x9e:(target+24)//2,0xa1:140,0xbf:0,0xce:0,0x96:129,0x9f:(start+24)//2,0xa2:140,0xa5:int(direction>0),0xd2:20,0xc0:0,0xcf:0,0x4f4f:72,0x4f49:2,0x97:0,0x5d:255}.items():put(at,v)
    finally:pause()
    got={};events=[];end=time.monotonic()+40
    while time.monotonic()<end:
        pause()
        try:
            m=dump('ram.bin',ram,65536);step=val(addr('actor_logic_steps'),2);frame=dump('bg.bpl',val(addr('background'),4),40960)
        finally:pause()
        crop=region(frame,col,9)
        label=next((label for label in ('idle','flash','plume') if crop==expect[label]),'in_flight')
        if label not in got:
            got[label]=step
            (q/f'{look}-{col}-{direction}-{label}.bpl').write_bytes(frame)
            (q/f'{look}-{col}-{direction}-{label}.bin').write_bytes(m)
        events.append(dict(step=step,x=m[0x9f],y=m[0xa2],state=m[0xc0],contact=m[0xb7],timers=list(m[0x4fde:0x4fe7]),visible=label))
        if 'flash' in got and label=='idle':break
    print(col,direction,got,flush=True)
    records.append(dict(col=col,direction=direction,observed=got,events=events))
    (q/(look+'-confirmed.json')).write_text(json.dumps(records,indent=2))
    assert 'flash' in got,(col,got)
(q/(look+'-confirmed.json')).write_text(json.dumps(records,indent=2))
