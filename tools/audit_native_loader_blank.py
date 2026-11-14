"""Controlled native death: inspect display-off and first complete publication."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command, tap_fire
from capture_paula_stream import elf_symbols
from audit_vic_native_kernels import sections
from rip_c64_room_graphics import render as source_render
from preview_planar import render
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/screen-corruption-2026-10-30'
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--start',action='store_true');p.add_argument('--room',type=int,default=6);p.add_argument('--label',default='native-blank');p.add_argument('--next-rooms',type=int,default=0);p.add_argument('--previous-rooms',type=int,default=0);a=p.parse_args()
 runtime=ROOT/'.tmp/corrupt-screen-ui';pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(runtime/'winuaebootlog.txt').read_text(errors='replace'))[-1]
 def cmd(q):return command(pipe,q,expected_pid=a.pid)
 def read(at,n):
  if n>16:
   temp=runtime/('audit-read-%x-%x.bin'%(at,n))
   assert 'Wrote ' in cmd('DBG S %s %x %x'%(temp,at,n))
   data=temp.read_bytes();assert len(data)==n;return data
  out=bytearray()
  for off in range(0,n,128):
   reply=cmd('DBG m %x %x'%(at+off,min(8,(n-off+15)//16)))
   for line in reply.splitlines():
    m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
    if m:out.extend(bytes.fromhex(m[1]))
  assert len(out)>=n;return bytes(out[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 def key(k):cmd('EVT KEY_'+k+' 1');time.sleep(.5);cmd('EVT KEY_'+k+' 0');time.sleep(.3)
 if a.start:
  cmd('EVT KEY_SHIFT_LEFT 1');key('D');cmd('EVT KEY_SHIFT_LEFT 0')
  for k in ['F1','F2','F3']+['F10']*(a.room-1):key(k)
  tap_fire(cmd)
  time.sleep(8)
 for _ in range(a.next_rooms):key('F10');tap_fire(cmd);time.sleep(3)
 for _ in range(a.previous_rooms):key('F9');tap_fire(cmd);time.sleep(3)
 elf=ROOT/'amiga/out/bruce_amiga.elf';_,ss=sections(elf);_,syms=elf_symbols(elf);labels=['.text','.rodata','.data','.bss'];s=[next(q for k,q in ss if k==name) for name in labels]
 task=long(long(4)+276);node=long(long(task+172)*4+60)*4;hunks=[]
 while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
 def addr(name):
  v=syms[name];i=next(i for i,q in enumerate(s) if q[3]<=v<q[3]+q[5]);return hunks[i]+v-s[i][3]
 maddr=addr('m');actual_room=read(maddr+0x29,1)[0]+1;assert actual_room==a.room,('Expected room',a.room,'actual',actual_room)
 out=BASE/a.label;out.mkdir(exist_ok=True)
 def save(at,n,name):
  p=out/name;assert 'Wrote ' in cmd('DBG S %s %x %x'%(p,at,n));data=p.read_bytes();assert len(data)==n;return data
 def status():
  copper=struct.unpack('>2I',read(addr('copper'),8))
  return dict(loading=read(addr('game_field_loading'),1)[0],epoch=int.from_bytes(read(addr('actor_loading_epoch'),2),'big'),
   source_den=read(maddr+0xd011,1)[0]&16,copper=list(copper),modes=[int.from_bytes(read(v+2,2),'big') for v in copper],
   fault=int.from_bytes(read(addr('source_fault'),2),'big'),cpu=cmd('DBG r'),custom=cmd('DBG c'))
 before=status();assert before['source_den'] and not before['loading'] and before['fault']==0
 # Poll the scalar loader flag, then pause the owned emulator. Debugger
 # watchpoints enter a modal debugger in this WinUAE build and block IPC.
 paused=False;pause_checks=[]
 def pause():
  nonlocal paused
  cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.03);paused=not paused
  if paused:
   first=cmd('DBG r');time.sleep(.05);second=cmd('DBG r');assert first==second,'Paused CPU/custom state moved'
   pause_checks.append(True)
 pause()
 for at,val in [(0xd1,255),(0xbf,25),(0xce,1)]:cmd('DBG W %x %02x'%(maddr+at,val))
 pause()
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  if read(addr('game_field_loading'),1)[0]:
   pause();blank=status();break
  time.sleep(.01)
 else:raise AssertionError('No loader flag observed')
 assert blank['loading'] and not blank['source_den'],blank
 assert blank['modes']==[0,0] and blank['fault']==0,blank
 save(maddr,65536,'blank-source.bin')
 pause()
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  modes=[int.from_bytes(read(v+2,2),'big') for v in before['copper']]
  if 0x4200 in modes:
   pause();after=status()
   selected=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',after['custom'])[1],16)
   if selected in after['copper'] and after['modes'][after['copper'].index(selected)]==0x4200:break
   pause()
  time.sleep(.01)
 else:raise AssertionError('No complete publication after loader')
 assert after['epoch']!=before['epoch'] and after['fault']==0
 copper=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',after['custom'])[1],16)
 words=struct.unpack('>34H',read(copper,68));assert words[:2]==(0x100,0x4200)
 front=words[19]*65536+words[21]
 m=save(maddr,65536,'published-source.bin');background=save(long(addr('background')),40960,'published-background.bpl');save(front,40960,'published-front.bpl')
 queued=save(addr('paint_queued'),1000,'published-queue.bin')
 pending={i for i in range(120,1000) if queued[i] in (1,3)}
 # The scalar poll can observe the next source step after publication.
 # Only cells already pending in the existing 160-cell painter queue
 # may differ; all other room pixels must match the current source.
 assert len(pending)<=160
 expected=source_render(m,a.room-1);errors=0;pending_errors=0
 for y in range(24,200):
  for x in range(320):
   at=(y+32)*160+x//8;value=sum(1<<plane for plane in range(4) if background[at+plane*40]&(128>>(x&7)))
   if value!=expected.getpixel((x,y)):
    if (y//8)*40+x//8 in pending:pending_errors+=1
    else:errors+=1
 assert errors==0,('Incomplete source room background at first publication',errors)
 render(out/'published-background.bpl',out/'published-background.png',interleaved=True);render(out/'published-front.bpl',out/'published-front.png',interleaved=True)
 pause()
 artifacts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.iterdir()) if p.name!='report.json']
 report=dict(status='passed_native_loader_blank_then_complete_publication',room=a.room,pid=a.pid,normal_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
  method='Owned fresh normal build; debug room/infinite/invincible; injected terminal death state from existing C64 death fixture. Loader flag and Copper list modes polled, then emulator paused for complete captures; no source state writes after death injection. Sampling does not prove every raster position.',
  natural_playthrough=False,edition_verified=False,source_behavior='$09BC-$09C1 clears DEN; $0B33 calls $50DB-$50E5 to set DEN after decompression; room init continues before native publication.',before=before,blank=blank,publication=after,background_pixel_errors=errors,checked_pixels=320*176,pending_source_cells=sorted(pending),pending_pixel_errors=pending_errors,pause_stability_checks=pause_checks,artifacts=artifacts)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS room',a.room,'both Copper lists blank at source DEN-off; all non-pending replacement pixels exact',flush=True)
if __name__=='__main__':main()
