"""Original $42A1-$42BA bytes, full virtual RAM/registers and old renderer state."""
import ctypes,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
 libs=[ctypes.CDLL(str(ROOT/('.tmp/color-observer-test/'+p+'.dll'))) for p in ['before','candidate']]
 ram=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)();meta=(ctypes.c_ubyte*200000)();rng=random.Random(20261030)
 for lib in libs:lib.bl_fc_metadata.restype=ctypes.c_ulong
 instructions=cases=0
 for value in range(256):
  for column in range(29):
   m=bytearray(source);m[0xd800:0xdc00]=rng.randbytes(1024);m[0x100:0x200]=rng.randbytes(256)
   r=[value,column,rng.randrange(256)]+[rng.randrange(2) for _ in range(5)]+[rng.randrange(256),rng.randrange(2)]
   initial=bytes(m)
   cpu=MPU(memory=m,pc=0x42a1);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8];cpu.p=0x30|r[3]|r[4]<<1|r[9]<<2|r[7]<<3|r[6]<<6|r[5]<<7
   for _ in range(400):
    if cpu.pc==0x42bc:break
    cpu.step();instructions+=1
   else:raise AssertionError(('source escaped',value,column,hex(cpu.pc)))
   wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
   for lib in libs:
    lib.bl_fc_seed((ctypes.c_ubyte*65536).from_buffer_copy(initial),(ctypes.c_ubyte*10)(*r));lib.bl_fc_slice();lib.bl_fc_copy(ram);lib.bl_fc_regs(regs)
    assert bytes(ram)==bytes(m),('source RAM',value,column)
    assert list(regs)==wanted,('source registers',value,column,list(regs),wanted)
   cases+=1
 for variant in range(192):
  states=[]
  for lib in libs:
   errors=lib.bl_fc_renderer(variant);assert not errors,('render pixels',variant,errors)
   length=lib.bl_fc_metadata(meta);assert length<len(meta);states.append(bytes(meta[:length]))
  assert states[0]==states[1],('private renderer state',variant,[(i,x,y) for i,(x,y) in enumerate(zip(*states)) if x!=y][:8])
 for lib in libs:assert not lib.bl_fc_observer_start()
 for variant in range(4096):
  states=[];memories=[]
  for lib in libs:
   lib.bl_fc_observer_case(variant);lib.bl_fc_copy(ram)
   length=lib.bl_fc_metadata(meta);assert length<len(meta)
   states.append(bytes(meta[:length]));memories.append(bytes(ram))
  assert states[0]==states[1] and memories[0]==memories[1],('observer glyph/member/dirty/mismatch domain',variant)
 files=['core/c64_rooms.c','core/c64_actor_programs.h','tools/build_c64_rooms.py','tests/final_colors_bridge.c','tools/verify_final_colors.py','test-color-observer.ps1','tests/color_observer_bridge.c','tools/verify_color_observer.py','reference/analysis/color-observer-2026-10-30/candidate/c64_rooms.c']
 report=dict(status='passed_scoped_original_color_loop_and_renderer_state',source_sha256=SHA,source_entry='$42A1',source_stop='$42BC',source_cases=cases,source_instructions=instructions,renderer_cases=192,observer_domain_cases=4096,renderer_reference='reference/analysis/final-colors-2026-10-30/before/core/c64_rooms.c',full_ram_and_registers=True,natural_playthrough=False,edition_verified=False,source_files=[item(p) for p in files])
 (ROOT/'reference/analysis/color-observer-2026-10-30/host.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS final color loop:',cases,'original-byte RAM/register cases,',instructions,'instructions,192 old/new renderer-state cases,4096 observer-domain cases')
if __name__=='__main__':main()
