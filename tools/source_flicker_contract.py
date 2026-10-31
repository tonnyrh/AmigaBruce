"""Actual $40BC-$4132 glyph writes, separate from stair animation.
Allowed complete row pairs follow the frozen AND/ORA/STA instructions.
"""
import hashlib,json
from pathlib import Path
from rip_c64_room_graphics import source_room
from c64_room_model import word
ROOT=Path(__file__).resolve().parents[1]
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def contract(room=11):
 raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
 for at,expected in [(0x40ce,'29308d9aac8d9bac09cc8d9aa48d9ba429b88d32a48d33a4'),(0x40f8,'29308d8aad8d8bad09cc8d8aa58d8ba5'),(0x411a,'290c8da2ac8da3ac09338da2a48da3a4292e8d3aa78d3ba7')]:
  assert raw[at:at+len(bytes.fromhex(expected))]==bytes.fromhex(expected),hex(at)
 initial=source_room(raw,room)
 result={0xa000:{0x93:[v|0xcc for v in [0,16,32,48]],0xb1:[v|0xcc for v in [0,16,32,48]],0x86:[(v|0xcc)&0xb8 for v in [0,16,32,48]],0x94:[v|0x33 for v in [0,4,8,12]],0xe7:[(v|0x33)&0x2e for v in [0,4,8,12]]},0xa800:{0x93:[0,16,32,48],0xb1:[0,16,32,48],0x94:[0,4,8,12]}}
 for bank,glyphs in result.items():
  for code,values in list(glyphs.items()):
   pairs=[(v,v) for v in values]
   # The actual source initialization can precede its first DEC-counter expiry.
   pair=tuple(initial[bank+code*8+2:bank+code*8+4])
   if pair not in pairs:pairs.append(pair)
   glyphs[code]=pairs
 return result

def pixel(m,room,x,y,bits):
 palette=word(m,0x480b+room*2);raster=word(m,0x4833+room*2);band=0
 for j in range(3):
  if m[raster+j]==253:break
  if y+51>=m[raster+j]+3:band+=1
  else:break
 values=[v&15 for v in m[palette+band*3:palette+band*3+3]]+[m[0xd800+(y//8)*40+x//8]&7]
 return values[(bits>>(6-((x&7)//2)*2))&3]

def check(m,room,points,pairs):
 errors=[sum(actual!=pixel(m,room,x,y,pair[(y&7)-2]) for x,y,actual in points) for pair in pairs]
 x,y,_=points[0];code=m[0x8c00+(y//8)*40+x//8];bank={0x38:0xa000,0x3a:0xa800,0x3c:0xb000}.get(m[0xf2],0xb800)
 source_pair=list(m[bank+code*8+2:bank+code*8+4])
 return dict(illegal_pixels=min(errors),visible_pair=list(pairs[errors.index(min(errors))]),equivalent_pairs=sum(e==min(errors) for e in errors),checked_pixels=len(points),source_pair=source_pair,source_pair_complete=tuple(source_pair) in pairs)
