"""R06 roof-tip source trace and full RAM/register host-port comparisons.

Injected routes, no IRQ/input scheduling or natural-play claim. Actual frozen
6502 code establishes the collision; the pixel overlay only explains it.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.reference/tools/python'),str(ROOT/'tools')]
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from rip_c64_room_graphics import source_room,render
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
OUT=ROOT/'reference/analysis/ceiling-r06-2026-10-28'

def artifact(path):return dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def state(m):
 return dict(screen_x=m[0x9e]*2-24,feet_y=m[0xa1],state=m[0xbf],counter=m[0xce],wait=m[0x106],pose=m[0x4f4e],contact=m[0xb6],body=m[0xa7])
def overlaps(m,px,py,pose):
 pointer=m[0x1167+pose]+256*m[0x1239+pose];bank=m[0x7c]<<8;hits=[]
 for row in range(21):
  yy=py-21+row
  for col in range(3):
   bits=m[pointer+col*32+row]
   for pair in range(4):
    mask=(bits>>(6-pair*2))&3;xx=px+col*8+pair*2
    if not mask or not (0<=xx<320 and 24<=yy<200):continue
    cell=yy//8*40+xx//8;code=m[0x8c00+cell];glyph=bank+code*8+yy%8
    background=(m[glyph]>>(6-(xx%8//2)*2))&3
    if mask&background==3 and not (m[0xd800+cell]&7):
     hits.append(dict(x=xx,y=yy,cell=cell,code=f'${code:02X}',glyph=f'${glyph:04X}',glyph_byte=m[glyph],mask=f'${pointer+col*32+row:04X}'))
 return hits

def main():
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
 initial=source_room(source,5);OUT.mkdir(parents=True,exist_ok=True)
 libpath=ROOT/'.tmp/r06-ceiling-test/contact.dll';lib=ctypes.CDLL(str(libpath))
 lib.bl_contact_run.argtypes=[ctypes.c_long];lib.bl_contact_fault.restype=lib.bl_contact_return.restype=ctypes.c_ulong
 buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)();calls=0;instructions=0
 sites=(0x1cc7,0x1cd0,0x1d66,0x2080,0x20f3,0x2504)
 def call(m,entry):
  nonlocal calls,instructions
  m[0x1fe:0x200]=[0xfe,0xff];r=[0]*8+[253,0]
  lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(bytes(m)),(ctypes.c_ubyte*10)(*r))
  cpu=MPU(memory=m,pc=entry);cpu.a=cpu.x=cpu.y=0;cpu.p=0x30;cpu.sp=253;trace=[]
  for count in range(100000):
   if cpu.pc==0xffff:break
   if cpu.pc in sites:trace.append(f'${cpu.pc:04X}')
   cpu.step()
  else:raise AssertionError(('source escaped',hex(cpu.pc)))
  instructions+=count;lib.bl_contact_run(entry);lib.bl_contact_copy(buf);lib.bl_contact_regs(regs)
  assert not lib.bl_contact_fault() and lib.bl_contact_return()==0xffff
  assert bytes(buf)==bytes(m),('RAM',hex(entry),[(hex(i),buf[i],m[i]) for i in range(65536) if buf[i]!=m[i]][:8])
  expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
  assert list(regs)==expected,('registers',hex(entry),list(regs),expected)
  calls+=1;return trace
 # Collect the upper-left lantern through the actual object handler. This
 # restores the original roof glyphs, as in the user's image. Do not mistake
 # the uncollected lantern's black pixels for the roof protrusion.
 prepared=list(initial);prepared[0x95:0x98]=[1,0,0];prepared[0x9e]=20;prepared[0xa1]=60
 prepared[0x4f4e]=0;prepared[0x7c]=0xa0;prepared[0xbf]=0
 collection_before=[prepared[0x8cca],prepared[0x8cf2]]
 call(prepared,0x5212);call(prepared,0x2e39)
 collection_after=[prepared[0x8cca],prepared[0x8cf2]]
 assert collection_before==[0x13,0x93] and collection_after==[0x1e,0x9e]
 initial=prepared
 routes=[];example=None
 # Contact -> objects -> actor update -> pose follows $1C0D/$1C10/$17BE.
 # Room loop, combat and IRQ are deliberately absent here.
 for px,raw in ((44,10),(48,10),(52,10),(32,14),(36,14),(40,14),(44,14)):
  m=list(initial);m[0x95:0x98]=[1,0,0];m[0x9e]=(px+24)//2;m[0xa1]=81;m[0xa4]=0
  for at in (0xbf,0xc2,0xce,0xcb,0x106,0x4fdb):m[at]=0
  m[0x4f4e]=0;m[0x7c]=0xa0;m[0x98]=raw;m[0x9b]=1;m[0x4f57:0x4fdb]=[0]*132
  call(m,0x2780);rows=[]
  for step in range(48):
   call(m,0x5212);before=state(m);hits=overlaps(m,before['screen_x'],before['feet_y'],before['pose'])
   if example is None and any(h['code']=='$D0' for h in hits) and px==32 and raw==14:example=(list(m),before,hits)
   call(m,0x2e39);trace=call(m,0x1c5b);after=state(m);call(m,0x2780)
   rows.append(dict(step=step,before=before,after=after,branches=trace,black_overlaps=hits))
  roof_hits=[row for row in rows if '$1CD0' in row['branches'] and any(h['code'] in ('$50','$D0') for h in row['black_overlaps'])]
  if raw==14:assert bool(roof_hits)==(px in (32,36)),(px,raw,'unexpected roof result')
  routes.append(dict(start_x=px,start_feet_y=81,raw_direction=raw,steps=rows))
 # Isolate the hanging source glyph in the selected vertical collision. The
 # modified glyph is a diagnostic control, never saved to the real game.
 m,before,hits=example;assert before['screen_x']==32 and before['feet_y']==67 and before['pose']==32
 assert any(h['x']==34 and h['y']==48 and h['code']=='$D0' for h in hits)
 actual=before['contact'];patched=list(m)
 for address in {int(h['glyph'][1:],16) for h in hits}:patched[address]=0
 call(patched,0x5212);assert actual&8 and not patched[0xb6]&8
 image=render(m,5).convert('RGB');overlay=image.copy();draw=ImageDraw.Draw(overlay)
 pointer=m[0x1167+before['pose']]+256*m[0x1239+before['pose']]
 for row in range(21):
  for col in range(3):
   bits=m[pointer+col*32+row]
   for pair in range(4):
    if (bits>>(6-pair*2))&3:
     xx=before['screen_x']+col*8+pair*2;yy=before['feet_y']-21+row
     draw.line((xx,yy,xx+1,yy),fill=(235,210,80))
 for h in hits:draw.line((h['x'],h['y'],h['x']+1,h['y']),fill=(255,70,70))
 crop=(0,24,64,88);left=image.crop(crop).resize((320,320),Image.Resampling.NEAREST);right=overlay.crop(crop).resize((320,320),Image.Resampling.NEAREST)
 plate=Image.new('RGB',(656,348),(18,18,18));plate.paste(left,(0,28));plate.paste(right,(336,28));draw=ImageDraw.Draw(plate)
 draw.text((8,8),'Source room glyphs',fill='white');draw.text((344,8),'Source contact mask; red = black hit',fill='white')
 plate.save(OUT/'roof-tip-contact.png')
 dis=Disassembler(MPU(memory=list(source)));lines=[]
 for first,end in ((0x1bc2,0x1c32),(0x17be,0x17e2),(0x1cc7,0x1d6f),(0x5431,0x543b),(0x5590,0x55ab)):
  pc=first
  while pc<end:
   n,s=dis.instruction_at(pc);lines.append('$%04X %s'%(pc,s));pc+=n
 (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
 report=dict(status='passed_original_r06_ceiling_trace_and_host_port',source_sha256=SHA,edition_verified=False,natural_playthrough=False,irq_raster_verified=False,
  calls=calls,instructions=instructions,lantern_collection=dict(before=collection_before,after=collection_after),routes=routes,example=dict(before=before,hits=hits,original_contact=actual,diagnostic_glyph_clear_contact=patched[0xb6]),
  method='Original room initialization and literal6502 contact/object/actor/pose calls; all64KiB and10 registers compared per call with current compiled host port; explicit controlled entry/input, no IRQ or wall-clock claim',
  source_files=[artifact(ROOT/p) for p in ['core/c64_rooms.c','core/c64_actor_programs.h','amiga/contact_prepare.s','amiga/contact_rows.s','amiga/contact_align.s','tests/source_contact_bridge.c','tools/audit_r06_ceiling.py','tools/rip_c64_room_graphics.py','test-r06-ceiling.ps1']],
  host_library_sha256=hashlib.sha256(libpath.read_bytes()).hexdigest(),artifacts=[artifact(OUT/p) for p in ['roof-tip-contact.png','source-disassembly.txt']],
  limitations=['No user snapshot/input history for this exact head bump','Injected controlled routes do not establish natural play or raster parity','No gameplay/geometry change is justified by this comparison'])
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS',len(routes),'R06 roof routes;',calls,'whole-RAM/register call comparisons;',instructions,'actual6502 instructions')
 print('Example:',json.dumps(report['example']))
if __name__=='__main__':main()
