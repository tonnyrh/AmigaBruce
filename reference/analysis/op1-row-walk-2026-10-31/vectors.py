"""Create sparse input and expected RAM from the frozen $537E row instructions."""
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
from build import HERE, ROOT
sys.path.insert(0,str(ROOT/".reference/tools/python"))
from py65.devices.mpu6502 import MPU

source = (ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
sha = hashlib.sha256(source).hexdigest()
assert sha=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
rng=random.Random(0x537e)
vectors=bytearray()
instructions=0
def encode(changes):
    return struct.pack(">H",len(changes))+b"".join(struct.pack(">HB",i,value) for i,value in changes)
for test in range(192):
    count=test%9
    y=rng.randrange(257-max(count,1))
    if test%4==0:
        y=(256-count)&255
    x,a=rng.randrange(256),rng.randrange(256)
    bases=[rng.choice((0,0x4e,0x4ee0,0xff00,0xa001,0xcae0)) for k in range(3)]
    if test%4==1:
        y=0
        bases=[0xa001,0x4ef0,0x004e]
    ram=bytearray(65536)
    ram[0x537e:0x53e4]=source[0x537e:0x53e4]
    for j,base in enumerate(bases):
        for k in range(count):
            ram[base+y+k]=rng.randrange(256)
            ram[0xcae0+j*32+y+k]=0 if test%4==2 else rng.randrange(256)
    for i in range(69):
        ram[0x4eed+i]=rng.randrange(256)
    if test%4==1 and count:
        ram[0xa001]=0xf3
        ram[0xcae0]=ram[0xcb00]=ram[0xcb20]=255
    for at,base in zip((0x5381,0x539b,0x53b5),bases):
        ram[at:at+2]=struct.pack("<H",base)
    end=(y+count)&255
    ram[0x52]=y
    ram[0x4f38:0x4f3b]=bytes([end])*3
    initial=bytes(ram)
    cpu=MPU(memory=ram,pc=0x537e)
    cpu.a,cpu.x,cpu.y=a,x,y
    ticks=0
    if count:
        while cpu.pc!=0x53cf or cpu.y!=end:
            assert 0x537e<=cpu.pc<=0x53e3 and ticks<1000
            cpu.step()
            ticks+=1
    instructions+=ticks
    before=struct.pack(">3H4B",*bases,a,x,y,count)
    after=struct.pack(">3H4B",*bases,cpu.a,cpu.x,cpu.y,count)
    writes=[(i,v) for i,v in enumerate(ram) if v!=initial[i]]
    assert all(i==0x4e or 0x4eed<=i<0x4eed+69 for i,_ in writes)
    case=before+after+encode([(i,v) for i,v in enumerate(initial) if v])+encode(writes)
    assert len(case)<2048
    vectors+=struct.pack(">H",len(case))+case

out=HERE/"proof"
out.mkdir(exist_ok=True)
(out/"vectors.bin").write_bytes(vectors)
(HERE/"source-controls.json").write_text(json.dumps(dict(source_sha256=sha,entry="$537E",stop="$53CF after last INY",cases=192,empty_abi_cases=22,executed_instructions=instructions,fixture_sha256=hashlib.sha256(vectors).hexdigest()),indent=2)+"\n")
