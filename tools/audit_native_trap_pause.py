"""Owned normal R06 negative-phase trap pixel control. No source injection."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from rip_c64_room_graphics import render,RGB
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference/analysis/trap-r06-2026-10-28/native'
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);args=p.parse_args()
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",args.log.read_text(errors='replace'))[-1]
 def cmd(q):return command(pipe,q,expected_pid=args.pid)
 def read(at,n):
  data=bytearray()
  for off in range(0,n,128):
   reply=cmd('DBG m %x %x'%(at+off,min(8,(n-off+15)//16)))
   for line in reply.splitlines():
    match=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
    if match:data.extend(bytes.fromhex(match[1]))
  assert len(data)>=n;return bytes(data[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
 while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
 assert len(hunks)==4;bss,syms=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
 def addr(name):return hunks[3]+syms[name]-bss
 maddr=addr('m');assert read(maddr+0x29,1)==b'\x05','Use room6 in the owned normal game'
 background=long(addr('background'));buffers=struct.unpack('>2I',read(addr('buffers'),8));OUT.mkdir(parents=True,exist_ok=True)
 accepted=[];deadline=time.monotonic()+90
 while len(accepted)<3 and time.monotonic()<deadline:
  phase=read(maddr+0x79,1)[0]
  if not 0xe3<=phase<=0xea:time.sleep(.05);continue
  number=len(accepted);mpath=OUT/('sample%d-source.bin'%number);bpath=OUT/('sample%d-background.bpl'%number)
  for at,n,path in ((maddr,65536,mpath),(background,40960,bpath)):
   reply=cmd('DBG S %s %x %x'%(path,at,n));assert 'Wrote ' in reply
  m=mpath.read_bytes();after=read(maddr+0x79,1)[0]
  if not phase<=m[0x79]<=after<128+128 or not (m[0x79]&128 and after&128):continue
  source=render(m,5).convert('RGB');blob=bpath.read_bytes();diff=0
  def compare(data):
   mismatch=0
   for y in range(80,96):
    for x in range(24,40):
     value=sum(1<<plane for plane in range(4) if data[(y+32)*160+plane*40+x//8]&(128>>(x&7)))
     if RGB[value]!=source.getpixel((x,y)):mismatch+=1
   return mismatch
  diff=compare(blob);assert diff==0,('stale trap background',phase,m[0x79],after,diff)
  dirty=struct.unpack('>40h',read(addr('actor_dirty'),80));views=[]
  for index,ptr in enumerate(buffers):
   overlaps=False
   for i in range(5):
    left,top,right,bottom=dirty[index*20+i*4:index*20+i*4+4]
    if left<40 and right>24 and top<128 and bottom>112:overlaps=True
   path=OUT/('sample%d-buffer%d.bpl'%(number,index));reply=cmd('DBG S %s %x a000'%(path,ptr));assert 'Wrote ' in reply
   mismatch=compare(path.read_bytes());views.append(dict(buffer=index,actor_intersects_roi=overlaps,mismatches=mismatch))
   if not overlaps:assert mismatch==0,('stale trap display',number,index,mismatch)
  accepted.append(dict(phase_before=phase,phase_source=m[0x79],phase_after=after,source_column=m[0x73],background_mismatches=diff,buffers=views))
  time.sleep(.10)
 assert len(accepted)==3,'No complete stable negative-phase observations'
 files=sorted(OUT.glob('sample*'));artifacts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
 report=dict(status='passed_owned_r06_negative_phase_trap_pixels',binary=dict(path='amiga/out/bruce_amiga.exe',sha256=hashlib.sha256((ROOT/'amiga/out/bruce_amiga.exe').read_bytes()).hexdigest()),
  source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in ['tools/audit_native_trap_pause.py','core/c64_rooms.c','amiga/main.c']],
  samples=accepted,roi=[24,80,40,96],artifacts=artifacts,natural_playthrough=False,source_ram_injected=False,
  method='Owned normal game reached room6 via debug room navigation; actual source phase and raw background/both display buffers; no source state injected')
 (ROOT/'reference/validation/source-trap-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
