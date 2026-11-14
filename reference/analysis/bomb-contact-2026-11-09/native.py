import sys,re,struct,time
from pathlib import Path
sys.path.insert(0,'tools')
from winuae_ipc import command,tap_fire
from title_reference import reference
from capture_paula_stream import elf_symbols
from check_enhanced_mode import check_structure
from PIL import Image
q=Path('.tmp/bomb-contact-2026-11-09').resolve(); pid=int((q/'pid.txt').read_text())
pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",(q/'winuaebootlog.txt').read_text(errors='replace'))[-1]
def cmd(s):return command(pipe,s,timeout=10,expected_pid=pid)
def dump(n,at,size):
 p=q/n
 assert 'Wrote ' in cmd(f'DBG S {p} {at:x} {size:x}')
 return p.read_bytes()
def val(at,n):
 data=re.search(r'(?mi)^[0-9a-f]{8}\s+((?:[0-9a-f]{4}\s+){1,8})',cmd(f'DBG m {at:x} 1'))
 return int.from_bytes(bytes.fromhex(data[1])[:n],'big')
def front():
 at=int(re.search(r'COP1LC: \$([0-9a-f]+)',cmd('DBG c'),re.I)[1],16)
 w=struct.unpack('>66H',dump('copper.bin',at,132))
 if w[0:2]!=(0x100,0x4200) or w[18:26:2]!=(0xe0,0xe2,0xe4,0xe6):return b''
 return dump('front.bpl',w[19]*65536+w[21],40960)
def key(k):cmd('EVT KEY_'+k+' 1');time.sleep(.26);cmd('EVT KEY_'+k+' 0')
def wait(fn,t=120):
 end=time.monotonic()+t
 while time.monotonic()<end:
  if fn():return
  time.sleep(.15)
 raise AssertionError(fn)

if '--boot' in sys.argv:wait(lambda:front()==reference())
task=val(val(4,4)+276,4);cli=val(task+172,4)*4;node=val(cli+60,4)*4;h=[]
while node:h.append(node+4);node=val(node,4)*4;assert len(h)<=4
bss,sym=elf_symbols(q/'release.elf')
def addr(s):return h[3]+sym[s]-bss
ram=addr('m')
def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.05)
def put(at,v):cmd(f'DBG W {ram+at:x} {v:02x}')
def sample():
    pause()
    try:
        m=dump('ram.bin',ram,65536)
        step=val(addr('actor_logic_steps'),2)
        fault=val(addr('source_fault'),2)
    finally:pause()
    return m,step,fault
