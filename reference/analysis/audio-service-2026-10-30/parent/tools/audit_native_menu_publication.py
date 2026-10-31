"""Owned paused-frame menu publication controls. Amiga UI, not C64 gameplay authority."""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/menu-publication-2026-10-29'
def sha(b):return hashlib.sha256(b).hexdigest()
def reference(debug=False,players=1,human=False,infinite=False,invincible=False,room=0,loading=False):
 source=(ROOT/BASE/'before/amiga/main.c').read_text(encoding='utf-8')
 def glyphs(name):return [list(map(int,re.findall(r'\d+',r))) for r in re.findall(r'\{([^{}]+)\}',re.search(name+r'\[\d+\]\[7\]=\{(.*?)\};',source,re.S)[1])]
 letters=glyphs('glyphs');digits=glyphs('digits');out=bytearray(40960)
 def pixel(x,y,color):
  for p in range(4):
   if color&(1<<p):out[y*160+p*40+x//8]|=128>>(x&7)
 def text(x,y,s,color):
  for c in s:
   glyph=letters[ord(c)-65] if 'A'<=c<='Z' else digits[int(c)] if c.isdigit() else [0]*7
   for row,bits in enumerate(glyph):
    for col in range(5):
     if bits&(16>>col):pixel(x+col,y+row,color)
   x+=6
 if loading:
  for i,c in enumerate('BRUCE'):
   for row,bits in enumerate(letters[ord(c)-65]):
    for col in range(5):
     if bits&(16>>col):
      for yy in range(6):
       for xx in range(6):pixel(73+i*36+col*6+xx,88+row*6+yy,13)
  text(139,166,'LOADING',5);return bytes(out)
 text(142,38,'BRUCE',7)
 if debug:
  for x,y,s,c in [(94,78,'TEST OPTIONS',13),(58,100,'F1 INFINITE FALLS '+('ON' if infinite else 'OFF'),1),(58,116,'F2 INVINCIBLE '+('ON' if invincible else 'OFF'),1),(58,132,'F3 F4 START ROOM %02d'%(room+1),1),(58,152,'F5 BACK  FIRE START TEST',5),(34,194,'IN GAME F1 F2 CHANGE ROOM',12),(34,210,'TEST FLAGS CHANGE C64 RULES',12)]:text(x,y,s,c)
 else:
  for x,y,s,c in [(64,96,'F3 PLAYERS '+str(players),1),(64,116,'F5 YAMO '+('JOYSTICK 1' if human else 'COMPUTER'),1),(64,146,'FIRE OR RETURN START',5),(64,172,'SHIFT D TEST OPTIONS',12),(34,200,'2 PLAYERS TAKE TURNS AS BRUCE',12),(34,216,'1P JOYSTICK 2  2P JOYSTICK 1',12)]:text(x,y,s,c)
 text(100,238,'ESC AMIGADOS',12);return bytes(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--label',default='native-menu');p.add_argument('--elf',type=Path,default=ROOT/'amiga/out/bruce_amiga.elf');a=p.parse_args()
 assert sha(reference())=='4100ef5dd7322650586771c52c40116a4d77cd16a212b6c5f3586d43b3edd79c'
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
 folder=ROOT/BASE/a.label;folder.mkdir(parents=True,exist_ok=True);elf_hash=sha(a.elf.read_bytes());rows=[];partial_work=0;changed_work=0;ram_states=[]
 def cmd(s):return command(pipe,s,expected_pid=a.pid)
 def read(at,n):
  data=bytearray()
  for off in range(0,n,16):
   reply=cmd('DBG m %x 1'%(at+off))
   for line in reply.splitlines():
    m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
    if m:data.extend(bytes.fromhex(m[1]))
  assert len(data)>=n;return bytes(data[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0')
 task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
 while node:hunks.append(node+4);node=long(node)*4
 assert len(hunks)==4;bss,syms=elf_symbols(a.elf)
 def addr(name):return hunks[3]+syms[name]-bss
 buffers=[long(addr('buffers')+4*i) for i in range(2)]
 def dump(at,path,n=40960):
  assert 'Wrote ' in cmd('DBG S %s %x %x'%(path,at,n));return path.read_bytes()
 def snap(label,allowed=None):
  nonlocal partial_work,changed_work
  pause()
  try:
   state=cmd('DBG c');cop=int(re.search(r'COP1LC: \$([0-9a-fA-F]+)',state)[1],16)
   words=struct.unpack('>34H',read(cop,68));front=words[19]*65536+words[21];assert front in buffers
   data=dump(front,folder/'front.bpl');other=dump(buffers[1-buffers.index(front)],folder/'hidden.bpl')
   valid=allowed is None or data in allowed
   partial=allowed is not None and other not in allowed
   if partial:partial_work+=1
   row=dict(label=label,front_index=buffers.index(front),front_sha256=sha(data),hidden_sha256=sha(other),complete_front=valid,hidden_not_a_complete_transition_image=partial)
   if partial and rows and rows[-1]['front_index']==row['front_index'] and rows[-1]['hidden_sha256']!=row['hidden_sha256']:changed_work+=1
   number=len(rows)
   (folder/('sample%03d-front.bpl'%number)).write_bytes(data);(folder/('sample%03d-hidden.bpl'%number)).write_bytes(other)
   rows.append(row)
   if not valid:
    for name,b in [('front',data),('hidden',other)]:(folder/('failure-'+label+'-'+name+'.bpl')).write_bytes(b)
   assert valid,row
   return data,row['front_index']
  finally:pause()
 def ram_hash():
  pause()
  try:
   path=folder/('menu-source-%d.bin'%len(ram_states));value=sha(dump(addr('m'),path,65536));ram_states.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=value));return value
  finally:pause()
 def event(key,on):
  if key=='SHIFT_D':
   if on:cmd('EVT KEY_SHIFT_LEFT 1');time.sleep(.03)
   cmd('EVT KEY_D '+str(on))
   if not on:cmd('EVT KEY_SHIFT_LEFT 0')
  else:cmd('EVT KEY_'+key+' '+str(on))
 def settled(expected,label,seconds=25):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   got,index=snap(label)
   if got==expected:return index
   time.sleep(.15)
  raise AssertionError(('Menu did not finish',label,sha(got),sha(expected)))
 conf=dict(debug=False,players=1,human=False,infinite=False,invincible=False,room=0)
 settled(reference(), 'initial')
 original_ram=ram_hash();transitions=[]
 def change(key,**updates):
  previous=reference(**conf);conf.update(updates);expected=reference(**conf);label='change%02d'%len(transitions)
  event(key,1)
  try:
   time.sleep(.018)
   snap(label+'-early',[previous,expected])
  finally:event(key,0)
  for delay in [.005,.02,.08]:
   time.sleep(delay);snap(label+'-work',[previous,expected])
  index=settled(expected,label+'-done');(folder/(label+'-complete.bpl')).write_bytes(expected)
  transitions.append(dict(key=key,config=dict(conf),front_index=index,expected_sha256=sha(expected)))
 change('F3',players=2);change('F3',players=1);change('F5',human=True);change('F5',human=False)
 change('SHIFT_D',debug=True);change('F1',infinite=True);change('F2',invincible=True);change('F4',room=1);change('F3',room=0);change('F5',debug=False)
 assert ram_hash()==original_ram,'Menu choices mutated source RAM before start'
 starts=[]
 for wanted in [1,0]:
  index=settled(reference(**conf),'before-start')
  if index!=wanted:change('F3',players=3-conf['players'])
  assert settled(reference(**conf),'start-parity')==wanted
  event('RETURN',1);time.sleep(.35);event('RETURN',0)
  end=time.monotonic()+40
  while time.monotonic()<end:
   if read(addr('game_field_active'),1)[0] and int.from_bytes(read(addr('actor_logic_steps'),2),'big')>=5:break
   time.sleep(.15)
  else:raise AssertionError('Game did not start')
  fault=int.from_bytes(read(addr('source_fault'),2),'big');assert fault==0
  _,game_index=snap('game-start')
  starts.append(dict(menu_front=wanted,game_buffer_sample=game_index,source_fault=fault,players=conf['players']))
  if wanted==1:
   event('F10',1);time.sleep(.35);event('F10',0);conf['debug']=False
   settled(reference(**conf),'f10-return');original_ram=ram_hash()
 assert changed_work>0,'No changing in-progress hidden construction sampled; repeat with earlier sample'
 report=dict(status='passed_scoped_native_menu_publication',elf=dict(path=str(a.elf),sha256=elf_hash),snapshots_paused=True,natural_playthrough=False,source_ram_preserved_during_choices=True,partial_hidden_samples=partial_work,changed_partial_hidden_samples=changed_work,ram_states=ram_states,transitions=transitions,starts=starts,samples=rows,source_files=[dict(path=p,sha256=sha((ROOT/p).read_bytes())) for p in ['amiga/main.c','tools/audit_native_menu_publication.py']],method='Paused actual front/hidden bitmaps; complete before/after UI images reconstructed from frozen previous font and menu text; no gameplay model; explicit menu options and F10 return; two starting buffer parities')
 (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS menu publication:',len(rows),'samples;',partial_work,'in-progress hidden images; both menu start parities')
if __name__=='__main__':main()
