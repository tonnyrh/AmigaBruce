"""Read-only front-buffer phase audit in an explicitly owned normal WinUAE."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from rip_c64_room_graphics import render
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--elf',type=Path,default=ROOT/'amiga/out/bruce_amiga.elf');p.add_argument('--label',required=True);p.add_argument('--start',action='store_true');p.add_argument('--samples',type=int,default=24);p.add_argument('--frozen',action='store_true');p.add_argument('--death',action='store_true');p.add_argument('--roundtrip',action='store_true');p.add_argument('--require-coherent',action='store_true');a=p.parse_args()
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
 def cmd(q):return command(pipe,q,expected_pid=a.pid)
 def read(at,n):
  data=bytearray()
  for off in range(0,n,16):
   reply=cmd('DBG m %x 1'%(at+off))
   for line in reply.splitlines():
    m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
    if m:data.extend(bytes.fromhex(m[1]))
  assert len(data)>=n,(hex(at),n,reply);return bytes(data[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 if a.start:
  for key in ['SHIFT_D','F1','F2']+['F4']*11+['RETURN']:
   if key=='SHIFT_D':cmd('EVT KEY_SHIFT_LEFT 1');time.sleep(.3)
   event='D' if key=='SHIFT_D' else key
   cmd('EVT KEY_'+event+' 1');time.sleep(.35);cmd('EVT KEY_'+event+' 0');time.sleep(.4)
   if key=='SHIFT_D':cmd('EVT KEY_SHIFT_LEFT 0');time.sleep(.3)
  time.sleep(15)
 task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
 while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
 assert len(hunks)==4;elf_hash=hashlib.sha256(a.elf.read_bytes()).hexdigest();bss,syms=elf_symbols(a.elf)
 maddr=hunks[3]+syms['m']-bss
 reload=None
 if a.roundtrip:
  for key in ['F2','F1']:
   cmd('EVT KEY_'+key+' 1');time.sleep(.35);cmd('EVT KEY_'+key+' 0');time.sleep(8)
 if a.death:
  epoch=hunks[3]+syms['actor_loading_epoch']-bss
  old=int.from_bytes(read(epoch,2),'big')
  for at,value in [(0xd1,255),(0xbf,25),(0xce,1)]:cmd('DBG W %x %02x'%(maddr+at,value))
  deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   time.sleep(1)
   if int.from_bytes(read(epoch,2),'big')!=old:break
  new=int.from_bytes(read(epoch,2),'big');assert new!=old,'Controlled death did not reload room'
  reload=dict(injected_source_fields={'$D1':255,'$BF':25,'$CE':1},loader_epoch_before=old,loader_epoch_after=new)
  time.sleep(8)
 def front():
  copper=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',cmd('DBG c'))[1],16)
  words=struct.unpack('>34H',read(copper,68));return words[19]*65536+words[21]
 out=ROOT/'reference/analysis/render-coherence-2026-10-29'/a.label;out.mkdir(parents=True,exist_ok=True)
 rows=[]
 def pause():
  cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.06)
 for attempt in range(a.samples*5):
  if a.frozen:pause()
  try:
   first=front();phase=read(maddr+0x64,1)[0]
   sp=out/'source.bin';bp=out/'front.bpl'
   assert 'Wrote ' in cmd('DBG S %s %x 10000'%(sp,maddr))
   assert 'Wrote ' in cmd('DBG S %s %x a000'%(bp,first))
   m=bytearray(sp.read_bytes());bitmap=bp.read_bytes()
   stable=front()==first and read(maddr+0x64,1)[0]==phase and m[0x64]==phase
  finally:
   if a.frozen:pause()
  if not stable:continue
  assert m[0x29]==11,('Use room12',m[0x29])
  skip=[]
  for actor in range(3):
   if m[0x95+actor]&1:
    x=m[0x9e+actor]*2-24;y=m[0xa1+actor];skip.append((x-20,y-30,x+40,y+10))
  points=[];static_points=[]
  for y in range(24,200):
   for col in range(40):
    code=m[0x8c00+(y//8)*40+col]
    animated=0x61<=code&127<=0x63
    for x in range(col*8,col*8+8):
     if any(l<=x<r and t<=y<b for l,t,r,b in skip):continue
     at=(y+32)*160+x//8
     pixel=sum(1<<p for p in range(4) if bitmap[at+p*40]&(128>>(x&7)))
     (points if animated else static_points).append((x,y,pixel))
  bank={0x38:0xa000,0x3a:0xa800,0x3c:0xb000}.get(m[0xf2],0xb800);pattern=m[0x4309:0x4321]
  base_image=render(m,11)
  static_errors=sum(value!=base_image.getpixel((x,y)) for x,y,value in static_points)
  errors=[]
  for candidate in range(8):
   for code in list(range(0x61,0x64))+list(range(0xe1,0xe4)):
    for r in range(8):m[bank+code*8+r]=pattern[((code&127)-0x61)*8+((candidate+r//2+(4 if code&128 else 0))&7)]
   expected=render(m,11)
   errors.append(sum(value!=expected.getpixel((x,y)) for x,y,value in points))
  row=dict(source_phase=phase&7,best_phase=errors.index(min(errors)),mismatched_animation_pixels=min(errors),checked_pixels=len(points),static_pixel_mismatches=static_errors)
  rows.append(row)
  if row['mismatched_animation_pixels'] or static_errors:
   for file in [sp,bp]:(out/('sample%d-'%(len(rows)-1)+file.name)).write_bytes(file.read_bytes())
  if len(rows)>=a.samples:break
  time.sleep(.07)
 assert rows
 report=dict(method='Owned normal WinUAE; invincible debug start in room12; actual C64 glyph phase candidates; no source-state injection',snapshots_paused=a.frozen,controlled_death=reload,room_roundtrip=a.roundtrip,edition_verified=False,natural_playthrough=False,elf=dict(path=str(a.elf),sha256=elf_hash),samples=rows,mixed_phase_samples=sum(bool(x['mismatched_animation_pixels']) for x in rows),max_pixel_mismatch=max(x['mismatched_animation_pixels'] for x in rows),max_static_pixel_mismatch=max(x['static_pixel_mismatches'] for x in rows))
 if a.death:report['method']+='; injected terminal actor state follows the C64 world-control death fixture'
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
 if a.require_coherent:assert not report['mixed_phase_samples'] and not report['max_static_pixel_mismatch']
if __name__=='__main__':main()
