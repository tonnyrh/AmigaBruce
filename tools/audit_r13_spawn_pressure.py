"""Room13 spawn/return rates from actual bytes and the live translated core."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from rip_c64_room_graphics import source_room
BASE=ROOT/'reference/analysis/spawn-r13-2026-10-30'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
 raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA
 lib=ctypes.CDLL(str(ROOT/'.tmp/spawn-r13/r13.dll'));U=ctypes.c_ubyte;A=U*65536;R=U*10
 lib.bl_contact_seed.argtypes=[ctypes.POINTER(U),ctypes.POINTER(U)];lib.bl_contact_run.argtypes=[ctypes.c_long]
 lib.bl_contact_copy.argtypes=[ctypes.POINTER(U)];lib.bl_contact_regs.argtypes=[ctypes.POINTER(U)]
 lib.bl_contact_fault.restype=lib.bl_contact_return.restype=ctypes.c_ulong
 output=A();regs=R();comparisons=0;instructions=0
 def reg(cpu):return [cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
 def compare(cpu,label,registers=True):
  nonlocal comparisons
  lib.bl_contact_copy(output);assert not lib.bl_contact_fault(),('Native fault',label)
  assert bytes(output)==bytes(cpu.memory),('RAM',label,[(hex(i),output[i],v) for i,v in enumerate(cpu.memory) if output[i]!=v][:12])
  if registers:lib.bl_contact_regs(regs);assert list(regs)==reg(cpu),('Registers',label,list(regs),reg(cpu))
  comparisons+=1
 def run(cpu,stop):
  nonlocal instructions
  for count in range(250000):
   if cpu.pc==stop:instructions+=count;return
   cpu.step()
  raise AssertionError(('Source escaped',hex(cpu.pc),hex(stop)))
 def invoke(cpu,entry,ret=0xfffe,actor=None):
  if actor is not None:cpu.x=actor
  cpu.stPushWord(ret);cpu.pc=entry
  lib.bl_contact_seed(A.from_buffer_copy(bytes(cpu.memory)),R(*reg(cpu)))
  run(cpu,(ret+1)&65535);lib.bl_contact_run(entry);compare(cpu,hex(entry))
  assert lib.bl_contact_return()==cpu.pc
 def seed(round_=0,read_value=0):
  m=source_room(raw,12);m[0x40]=round_;m[0x42ca]=0;m[0x95:0x98]=[0,0,0];m[0x104]=1;m[0x105]=0
  m[0x9e]=raw[0x4bae+12];m[0xa1]=raw[0x4bc2+12];m[0x47]=m[0xd015]=0
  m[0x16]=0;m[0x17]=0x60;m[0x6000:0x6200]=[read_value]*512;m[0xdc00]=m[0xdc01]=255
  cpu=MPU(memory=m);cpu.p=0x30;cpu.sp=255;invoke(cpu,0xa2a)
  return cpu
 def actors(m):
  return [dict(actor=i,active=bool(m[0x95+i]&1),x=m[0x9e+i]*2-24,y=m[0xa1+i],state=m[0xbf+i],counter=m[0xce+i],timer=m[0x5e if i==1 else 0x5d]) for i in (1,2)]
 def tick(cpu):
  # Retain registers between the actual service JSRs, including the reader's Y.
  for entry,ret in [(0xda4,0x1bf7),(0xd0f,0x1bfa),(0xdb1,0x1bfd)]:invoke(cpu,entry,ret)
  return actors(cpu.memory)
 traces=[]
 for round_ in (0,1):
  for age in (0,25,32):
   for read_value in (0,25):
    cpu=seed(round_,read_value);m=cpu.memory;initial=list(m[0x5d:0x5f]);assert initial==([4,32] if round_==0 else [3,3])
    m[0x88]=age;m[0x87]=0;rows=[];births=[];prior=[False,False]
    for step in range(1,41):
     pair=tick(cpu);rows.append(dict(phase='first',step=step,actors=pair))
     for i,q in enumerate(pair):
      if q['active'] and not prior[i]:births.append(dict(phase='first',step=step,**q))
      prior[i]=q['active']
    # Common original removal, not a fabricated respawn rule or death shortcut
    # in production. Entry/death animations are intentionally not timed here.
    invoke(cpu,0x3001,actor=2);kage_return=m[0x5d];prior=[bool(m[0x96]&1),bool(m[0x97]&1)]
    for step in range(1,25):
     pair=tick(cpu);rows.append(dict(phase='remove-kage-yamo-active',step=step,actors=pair))
     for i,q in enumerate(pair):
      if q['active'] and not prior[i]:births.append(dict(phase='remove-kage-yamo-active',step=step,**q))
      prior[i]=q['active']
    invoke(cpu,0x3001,actor=1);yamo_return=m[0x5e];prior=[bool(m[0x96]&1),bool(m[0x97]&1)]
    for step in range(1,37):
     pair=tick(cpu);rows.append(dict(phase='remove-yamo',step=step,actors=pair))
     for i,q in enumerate(pair):
      if q['active'] and not prior[i]:births.append(dict(phase='remove-yamo',step=step,**q))
      prior[i]=q['active']
    traces.append(dict(round=round_,clock_high=age,controlled_read_byte=read_value,initial_counters=initial,kage_removal_counter=kage_return,yamo_removal_counter=yamo_return,births=births,steps=rows))
    print('PASS R13 round',round_,'age',age,'reader',read_value,'return',kage_return,yamo_return,flush=True)
 # Actual field path: the spawn countdown must not also run per PAL field.
 cpu=seed();m=cpu.memory;clock=[]
 for field in range(60):
  saved=(cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp,cpu.pc);lib.bl_contact_seed(A.from_buffer_copy(bytes(m)),R(*reg(cpu)))
  m[0x44]=0;cpu.p&=~8;cpu.pc=0x15b8;run(cpu,0x169d)
  m[0x98]=15;m[0x9b]=1;m[0xdc00]=m[0xdc01]=255
  cpu.pc=0x1703;run(cpu,0x179d)
  assert m[0xd015]==0  # No active actors; VIC latch is necessarily zero.
  cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp,cpu.pc=saved
  lib.bl_r13_field();compare(cpu,'field'+str(field))
  assert list(m[0x5d:0x5f])==[4,32];clock.append(dict(field=field+1,timers=list(m[0x5d:0x5f]),age=list(m[0x87:0x89])))
 BASE.mkdir(parents=True,exist_ok=True);dis=Disassembler(MPU(memory=list(raw)));lines=[]
 for first,last in [(0xa3f,0xa6b),(0xda4,0xdf8),(0xd0f,0xd42),(0xd42,0xda4),(0x1159,0x1166)]:
  pc=first
  while pc<last:
   n,text=dis.instruction_at(pc);lines.append('$%04X %s'%(pc,text));pc+=n
 (BASE/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
 paths=['tools/audit_r13_spawn_pressure.py','core/c64_rooms.c','core/c64_actor_programs.h','tests/source_contact_bridge.c',
   'reference/analysis/spawn-r13-2026-10-30/bridge.c','reference/analysis/spawn-r13-2026-10-30/build.ps1']
 report=dict(status='passed_scoped_r13_spawn_service_and_field_controls',source_sha256=SHA,cases=len(traces),service_ticks=1200,field_checks=60,comparisons=comparisons,source_instructions=instructions,
  production_changed=False,edition_verified=False,natural_playthrough=False,raster_exact=False,
  method='Actual frozen loader/spawn/removal JSRs preserve source registers and return frames; all64KiB/registers/returns versus current native chain. 12 isolated R13 sequences, no actor AI/combat/death-animation updates. Controlled reader page6000..61FF values0/25 are branch inputs, not natural random distributions. Separate 60 full native field calls compared with actual source IRQ fragments, decoded idle joystick seam and no active actors/VIC collisions.',
  table=dict(initial_kage=raw[0x130b+12],initial_yamo=raw[0x1347+12],return_kage=raw[0x131f+12],return_yamo=raw[0x135b+12],standard_xy=[raw[0x4bae+12]*2-24,raw[0x4bc2+12]],alternative_xy=[raw[0x4bd6+12]*2-24,raw[0x4bea+12]]),
  sequences=traces,field_trace=clock,artifacts=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
 (BASE/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',comparisons,'whole-RAM/register comparisons;',instructions,'source instructions')
if __name__=='__main__':main()
