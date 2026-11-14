"""Trace shared bomb capacity and release against the frozen candidate bytes.

Run test-c64-actors.ps1 -CompileOnly first. No running emulator is needed.
The source original and game binaries are never changed by this test.
"""
import ctypes,hashlib,json
from pathlib import Path
from audit_r11_yamo_walk import library,ROOT,SHA
from verify_c64_room_runtime import invoke
raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
assert hashlib.sha256(raw).hexdigest()==SHA
lib=library();lib.bl_c64_actor_test_call.argtypes=[ctypes.c_long]*2
buf=(ctypes.c_ubyte*65536)()
def memory():lib.bl_actor_copy(buf);return bytearray(buf)
def put(m,at,v):m[at]=v;lib.bl_c64_test_write(at,v)
def call(m,entry):
    invoke(m,entry);lib.bl_c64_actor_test_call(entry,0)
    actual=memory()
    assert not lib.bl_c64_fault()
    assert actual==m,(hex(entry),[(hex(i),a,b) for i,(a,b) in enumerate(zip(actual,m)) if a!=b][:12])
checks=[]
for actor in range(3):
 for col in (21,34):
  for occupancy in range(8):
   lib.bl_c64_reset();lib.bl_c64_world_start(1,0);lib.bl_c64_world_jump(10);m=memory()
   for i in range(3):put(m,0x95+i,int(actor==i));put(m,0xbf+i,0)
   for at,v in ((0x9e+actor,col*4+12),(0xa1+actor,140),(0x4f4e+actor,2+70*actor)):
    put(m,at,v)
   for i in range(3):
    put(m,0x4fde+i,(1 if occupancy&(1<<i) else 0));put(m,0x4fe1+i,(8,20,33)[i]);put(m,0x4fe4+i,11)
    if occupancy&(1<<i):put(m,0xd800+23*40+(9,21,34)[i],0xfd)
   call(m,0x5212);contact=m[0xb6+actor]
   call(m,0x2e39)
   cell=17*40+col
   if occupancy==7:
    assert m[0xd800+cell]==0xf8 and list(m[0x4fe4:0x4fe7])==[11]*3
    slot=None
   else:
    slot=next(i for i in range(3) if not occupancy&(1<<i))
    assert m[0xd800+cell]==0xfd and m[0x4fe1+slot]==col-1 and m[0x4fe4+slot]==8,(actor,col,occupancy,contact)
   for i in range(3):put(m,0x95+i,0)
   for step in range(1,25):call(m,0x3228)
   assert list(m[0x4fde:0x4fe1])==[0]*3
   assert m[0xd800+cell]==0xf8 and m[0x8c00+cell]==0x60
   checks.append(dict(actor=actor,column=col,object_row=9,occupied_mask=occupancy,contact=contact,allocated_slot=slot,released_after_calls=24))
out=ROOT/'reference/analysis/r11-yamo-enhanced-2026-11-09/capacity.json'
out.write_text(json.dumps(dict(source_sha256=SHA,edition_verified=False,method='Controlled host engine compared with actual 6502 instructions, all 65536 RAM bytes at each call boundary. This is not a natural C64 playthrough.',checks=checks),indent=2)+'\n')
print('PASS',len(checks),'actor/bomb/capacity cases and',24*len(checks),'bomb timer calls; full RAM matches the original instructions.')
