"""Injected room-loop continuation from a read-only Amiga snapshot.
Actual frozen6502 bytes versus native translation; not natural play timing.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.reference/tools/python'),str(ROOT/'tools')]
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from rip_c64_room_graphics import render
OUT=ROOT/'reference/analysis/trap-r06-2026-10-28'
def main():
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();initial=(OUT/'source-memory.bin').read_bytes()
 assert hashlib.sha256(source).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
 assert initial[0x29]==5 and initial[0x38ab:0x39aa]==source[0x38ab:0x39aa]
 d=ctypes.CDLL(str(ROOT/'.tmp/source-contact-test/contact.dll'));d.bl_contact_run.argtypes=[ctypes.c_long];d.bl_contact_fault.restype=d.bl_contact_return.restype=ctypes.c_ulong
 buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)();r=[0,0,0,0,0,0,0,0,253,0];m=list(initial);rows=[]
 render(m,5).save(OUT/'source-before.png')
 for step in range(64):
  before={hex(at):m[at] for at in (0x71,0x72,0x73,0x77,0x78,0x79)};m[0x1fe:0x200]=[0xfe,0xff]
  d.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(bytes(m)),(ctypes.c_ubyte*10)(*r))
  cpu=MPU(memory=m,pc=0x38ab);cpu.a=cpu.x=cpu.y=0;cpu.p=0x30;cpu.sp=253;draw=[]
  for instructions in range(200000):
   if cpu.pc==0xffff:break
   if cpu.pc==0x17e2:draw.append(dict(tile=cpu.a,row=cpu.x,column=cpu.y))
   cpu.step()
  else:raise AssertionError(('escaped',step,hex(cpu.pc)))
  d.bl_contact_run(0x38ab);d.bl_contact_copy(buf);d.bl_contact_regs(regs)
  assert not d.bl_contact_fault() and d.bl_contact_return()==0xffff,(step,'native fault')
  assert bytes(buf)==bytes(m),(step,'RAM',[(hex(i),buf[i],m[i]) for i in range(65536) if buf[i]!=m[i]][:12])
  wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
  assert list(regs)==wanted,(step,'registers',list(regs),wanted)
  rows.append(dict(step=step+1,before=before,after={hex(at):m[at] for at in (0x71,0x72,0x73,0x77,0x78,0x79)},draws=draw,instructions=instructions))
  if step in (0,26,27,28,30,34,35):render(m,5).save(OUT/('source-step-%02d.png'%(step+1)))
 dis=Disassembler(MPU(memory=source));lines=[]
 for first,end in ((0x3978,0x39aa),(0x40b4,0x40bc)):
  pc=first
  while pc<end:
   n,s=dis.instruction_at(pc);lines.append('$%04X %s'%(pc,s));pc+=n
 (OUT/'trap-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 report=dict(status='passed_original_room_loop_continuation',source_sha256=hashlib.sha256(source).hexdigest(),snapshot_sha256=json.loads((OUT/'snapshot.json').read_text())['snapshot_sha256'],steps=rows,
   edition_verified=False,natural_playthrough=False,observed_wall_time=False,method='64 injected room-loop entries from stored room6 RAM; whole64KiB and all registers compared with actual frozen6502 bytes',
   limits=['No failed input history or natural timing can be inferred from one snapshot','No IRQ/actor updates injected between isolated room-loop calls','Source rendering compared separately from stored Amiga framebuffer'])
 (OUT/'room-loop-controls.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS64 room6 room-loop continuations, all RAM/registers')
 print('Counter79 initial:',initial[0x79],'; first wraps to0:',next(x['step'] for x in rows if x['after']['0x79']==0))
if __name__=='__main__':main()
