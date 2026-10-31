"""Direct $15BA call candidate: compare original bytes to the full IRQ prefix.

Controlled source-derived room seeds. Stops at the existing $169D seam;
not a physical IRQ schedule or natural gameplay acceptance.
"""
import ctypes, hashlib, itertools, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
BASE=ROOT/'reference/analysis/sprite-publish-2026-10-30/direct-call'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
 raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==SHA
 # Raw-byte scan is a scope aid, not a control-flow proof for arbitrary code.
 assert [i for i in range(65534) if raw[i:i+3]==bytes([0x20,0xe2,0x25])]==[0x15ba]
 U=ctypes.c_ubyte;P=ctypes.POINTER(U);out=(U*65536)();regs=(U*10)();rng=random.Random(2026103011)
 libs=[ctypes.CDLL(str(ROOT/('.tmp/source-publish-direct-test/'+n+'.dll'))) for n in ['before','candidate']]
 for lib in libs:
  lib.bl_contact_prepare.argtypes=[ctypes.c_long]*2
  lib.bl_contact_seed.argtypes=[P,P];lib.bl_contact_run.argtypes=[ctypes.c_long]
  lib.bl_contact_copy.argtypes=[P];lib.bl_contact_regs.argtypes=[P]
  lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ctypes.c_ulong
 cases=instructions=fallback=0
 for room,human in itertools.product(range(20),range(2)):
  libs[0].bl_contact_prepare(room,human);libs[0].bl_contact_copy(out);seed=bytes(out)
  for active,guard in itertools.product(range(8),range(2)):
   m=bytearray(seed);m[0x277e]=guard;m[0x277d]=rng.randrange(256)
   for actor in range(3):
    m[0x95+actor]=(m[0x95+actor]&254)|((active>>actor)&1)
    m[0x9e+actor]=rng.randrange(256);m[0xa1+actor]=rng.randrange(256)
   r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(4)]+[0,rng.randrange(224,254),0]
   before=bytes(m);cpu=MPU(memory=m,pc=0x15b8);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
   cpu.p=0x20|r[3]|r[4]<<1|r[6]<<6|r[5]<<7
   for _ in range(10000):
    if cpu.pc==0x169d:break
    cpu.step();instructions+=1
   else:raise AssertionError(('Source prefix escaped',room,active,guard,hex(cpu.pc)))
   want=[cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7&1,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
   for li,lib in enumerate(libs):
    lib.bl_contact_seed((U*65536).from_buffer_copy(before),(U*10)(*r));lib.bl_contact_run(0x15b8);lib.bl_contact_copy(out);lib.bl_contact_regs(regs)
    if bytes(out)!=bytes(m):
     diff=[(hex(i),a,b) for i,(a,b) in enumerate(zip(out,m)) if a!=b]
     raise AssertionError(('RAM',li,room,active,guard,diff[:12]))
    assert list(regs)==want,('registers',li,room,list(regs),want)
    assert not lib.bl_contact_fault()
   cases+=1
   # D=1 follows literally the previous actor call, compare both builds.
   r[7]=1;images=[]
   for lib in libs:
    lib.bl_contact_seed((U*65536).from_buffer_copy(before),(U*10)(*r));lib.bl_contact_run(0x15b8);lib.bl_contact_copy(out);lib.bl_contact_regs(regs)
    images.append((bytes(out),bytes(regs),lib.bl_contact_return(),lib.bl_contact_fault()))
   assert images[0]==images[1];fallback+=1
 def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 scope=json.loads((BASE/'scope.json').read_text())
 for e in scope['inputs']+scope['generated']:assert item(ROOT/e['path'])==e
 report=dict(status='passed_isolated_direct_call_source_prefix',source_sha256=SHA,source_cases=cases,source_instructions=instructions,decimal_before_after_cases=fallback,all_ram_and_registers=True,entry='$15B8',stop='$169D',safe_stack_range='$E0-$FD',production_changed=False,natural_playthrough=False,realtime_accepted=False,artifacts=scope['inputs']+scope['generated']+[item(Path(__file__)),item(BASE/'scope.json'),item(ROOT/'tools/build_source_sprite_direct.py'),item(ROOT/'test-source-sprite-direct.ps1')],limitations=['Room seeds from current native loader; prefix executed from frozen original bytes','Fixed input memory, no natural IRQ/beam timing','Decimal fallbacks before/after only, not a source decimal parity claim'])
 (BASE/'host.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS direct publisher call:',cases,'source IRQ-prefix cases;',instructions,'original instructions;',fallback,'unchanged decimal cases')
if __name__=='__main__':main()
