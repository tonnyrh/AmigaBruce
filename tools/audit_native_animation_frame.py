"""Read-only front-buffer phase audit in an explicitly owned normal WinUAE."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from rip_c64_room_graphics import render
from source_flicker_contract import contract as flicker_contract, check as check_flicker
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
  registers=cmd('DBG c')
  executing=int(re.search(r'COPPTR: \$([0-9a-fA-F]+)',registers)[1],16)
  choices=struct.unpack('>II',read(hunks[3]+syms['copper']-bss,8))
  copper=next(base for base in choices if base<=executing<base+1024)
  words=struct.unpack('>34H',read(copper,68));return words[19]*65536+words[21]
 out=ROOT/'reference/analysis/render-coherence-2026-10-29'/a.label;out.mkdir(parents=True,exist_ok=True)
 rows=[];flicker_rules=flicker_contract(11)
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
  bank={0x38:0xa000,0x3a:0xa800,0x3c:0xb000}.get(m[0xf2],0xb800);flicker_codes=flicker_rules.get(bank,{})
  points=[];static_points=[];flicker_points={}
  for y in range(24,200):
   for col in range(40):
    code=m[0x8c00+(y//8)*40+col]
    animated=0x61<=code&127<=0x63
    for x in range(col*8,col*8+8):
     if any(l<=x<r and t<=y<b for l,t,r,b in skip):continue
     at=(y+32)*160+x//8
     pixel=sum(1<<p for p in range(4) if bitmap[at+p*40]&(128>>(x&7)))
     if code in flicker_codes and (y&7) in (2,3):flicker_points.setdefault(code,[]).append((x,y,pixel))
     else:(points if animated else static_points).append((x,y,pixel))
  bank={0x38:0xa000,0x3a:0xa800,0x3c:0xb000}.get(m[0xf2],0xb800);pattern=m[0x4309:0x4321]
  base_image=render(m,11)
  static_errors=sum(value!=base_image.getpixel((x,y)) for x,y,value in static_points)
  flickers={str(code):check_flicker(m,11,pixels,flicker_codes[code]) for code,pixels in flicker_points.items()}
  flicker_illegal=sum(v['illegal_pixels'] for v in flickers.values())
  errors=[]
  for candidate in range(8):
   for code in list(range(0x61,0x64))+list(range(0xe1,0xe4)):
    for r in range(8):m[bank+code*8+r]=pattern[((code&127)-0x61)*8+((candidate+r//2+(4 if code&128 else 0))&7)]
   expected=render(m,11)
   errors.append(sum(value!=expected.getpixel((x,y)) for x,y,value in points))
  row=dict(source_phase=phase&7,best_phase=errors.index(min(errors)),mismatched_animation_pixels=min(errors),checked_pixels=len(points),static_pixel_mismatches=static_errors,flicker_illegal_pixels=flicker_illegal,flickers=flickers)
  rows.append(row)
  if row['mismatched_animation_pixels'] or static_errors or flicker_illegal:
   for file in [sp,bp]:(out/('sample%d-'%(len(rows)-1)+file.name)).write_bytes(file.read_bytes())
  if len(rows)>=a.samples:break
  time.sleep(.07)
 assert rows
 motion={}
 for row in rows:
  for code,value in row.get('flickers',{}).items():
   q=motion.setdefault(code,dict(source=set(),visible=set()))
   if value.get('source_pair_complete'):q['source'].add(tuple(value['source_pair']))
   q['visible'].add(tuple(value['visible_pair']))
 motion_report={code:dict(source_variants=len(value['source']),visible_variants=len(value['visible'])) for code,value in motion.items()}
 stuck=[code for code,value in motion_report.items() if value['source_variants']>=2 and value['visible_variants']<2]
 report=dict(method='Owned normal WinUAE; invincible debug start in room12; actual C64 glyph phase candidates; no source-state injection',snapshots_paused=a.frozen,controlled_death=reload,room_roundtrip=a.roundtrip,edition_verified=False,natural_playthrough=False,elf=dict(path=str(a.elf),sha256=elf_hash),samples=rows,mixed_phase_samples=sum(bool(x['mismatched_animation_pixels']) for x in rows),max_pixel_mismatch=max(x['mismatched_animation_pixels'] for x in rows),max_static_pixel_mismatch=max(x['static_pixel_mismatches'] for x in rows),max_flicker_illegal_pixels=max(x['flicker_illegal_pixels'] for x in rows),flicker_motion=motion_report,flicker_stuck_codes=stuck,flicker_contract=dict(source='$40BC-$4132',rows=[2,3],source_sha256='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8',method='Every visible flicker glyph row pair must match a complete source AND/ORA/STA output or original initialization; no pixel tolerance'))
 if a.death:report['method']+='; injected terminal actor state follows the C64 world-control death fixture'
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
 if a.require_coherent:assert not report['mixed_phase_samples'] and not report['max_static_pixel_mismatch'] and not report['max_flicker_illegal_pixels'] and not report['flicker_stuck_codes']
if __name__=='__main__':main()
