"""Owned normal CLI/ADF startup check; exact complete menu and source progress."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
from audit_native_menu_publication import reference
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--label',choices=['cli','adf'],required=True);p.add_argument('--start-game',action='store_true');p.add_argument('--output-root',type=Path,default=ROOT/'reference/analysis/contact-unroll-2026-10-31/normal-ui');a=p.parse_args()
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
 def cmd(s):return command(pipe,s,expected_pid=a.pid)
 def read(at,n):
  text=cmd('DBG m %x %x'%(at,(n+15)//16));out=bytearray()
  for line in text.splitlines():
   m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
   if m:out.extend(bytes.fromhex(m[1]))
  assert len(out)>=n;return bytes(out[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.06)
 folder=a.output_root/a.label;folder.mkdir(parents=True,exist_ok=True)
 deadline=time.monotonic()+180;hunks=[]
 while time.monotonic()<deadline:
  try:
   task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
   while node and len(hunks)<5:hunks.append(node+4);node=long(node)*4
   if len(hunks)!=4:raise AssertionError('Command not loaded')
   pause()
   try:
    copper=int(re.search(r'COP1LC: \$([0-9a-fA-f]+)',cmd('DBG c'))[1],16);words=struct.unpack('>34H',read(copper,68));front=words[19]*65536+words[21]
    path=folder/'menu.bpl';assert 'Wrote ' in cmd('DBG S %s %x a000'%(path,front))
    complete=path.read_bytes()==reference()
   finally:pause()
   if complete:break
  except (AssertionError,IndexError,TypeError):pass
  time.sleep(2)
 else:raise AssertionError('Normal complete menu did not appear')
 bss,syms=elf_symbols(ROOT/'amiga/out/bruce_amiga.elf')
 def addr(name):return hunks[3]+syms[name]-bss
 states=[]
 if a.start_game:
  cmd('EVT KEY_RETURN 1');time.sleep(.35);cmd('EVT KEY_RETURN 0');deadline=time.monotonic()+60
  while time.monotonic()<deadline:
   if read(addr('game_field_active'),1)[0] and int.from_bytes(read(addr('actor_logic_steps'),2),'big')>=5:break
   time.sleep(.3)
  else:raise AssertionError('ADF game did not start')
  for _ in range(3):
   states.append(dict(steps=int.from_bytes(read(addr('actor_logic_steps'),2),'big'),fault=int.from_bytes(read(addr('source_fault'),2),'big'),room=read(addr('m')+0x29,1)[0]+1));time.sleep(1)
  assert all(s['fault']==0 and s['room']==1 for s in states) and states[-1]['steps']>states[0]['steps']
 def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 (folder/'report.json').write_text(json.dumps(dict(status='passed_current_normal_boot',method='Owned paused complete menu against existing font/UI reference; optional source-main progression; no source-state writes',mode=a.label,normal_exe_sha256=item(ROOT/'amiga/out/bruce_amiga.exe')['sha256'],elf=item(ROOT/'amiga/out/bruce_amiga.elf'),complete_menu=True,game_states=states,artifacts=[item(folder/'menu.bpl')],natural_playthrough=False),indent=2)+'\n')
 print('PASS normal boot',a.label,'and game progress' if a.start_game else 'complete menu')
if __name__=='__main__':main()
