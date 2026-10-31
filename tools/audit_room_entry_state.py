"""Ordinary C64 door crossings: source bytes versus the live native chain."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from rip_c64_room_graphics import source_room
from audit_floor_walking import call
BASE=ROOT/'reference/analysis/room-entry-state-2026-10-30'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
FIELDS={'room':0x29,'x':0x9e,'y':0xa1,'facing':0xa4,'state':0xbf,'previous':0xc2,'counter':0xce,'animation':0xcb,'wait':0x106,'fall_push':0xb0,'pose':0x4f48,'mask':0x4f4e}
def state(mem):return {k:mem[v]+(1 if k=='room' else 0) for k,v in FIELDS.items()}
def main():
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
 # This bridge was compiled from the unchanged current core in the floor audit.
 previous=json.loads((ROOT/'reference/analysis/floor-walk-2026-10-30/report.json').read_text())
 for e in previous['artifacts']:
  if e['path'].endswith(('.c','.h','.ps1')):assert hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
 lib=ctypes.CDLL(str(ROOT/'.tmp/floor-walk/floor.dll'));U=ctypes.c_ubyte;A=U*65536;R=U*10
 lib.bl_contact_seed.argtypes=[ctypes.POINTER(U),ctypes.POINTER(U)];lib.bl_contact_run.argtypes=[ctypes.c_long]
 lib.bl_contact_copy.argtypes=[ctypes.POINTER(U)];lib.bl_contact_regs.argtypes=[ctypes.POINTER(U)]
 lib.bl_contact_fault.restype=lib.bl_floor_stop.restype=ctypes.c_ulong
 output=A();regs=R();rows=[];instructions=0;comparisons=0
 boundaries={0x1c32,0xf47,0x1968,0x197d,0x050f,0x0584}
 for room,direction,x,y,label in [(0,1,300,98,'R01-upper-right'),(0,1,300,146,'R01-lower-right'),(1,-1,6,98,'R02-upper-left'),(1,-1,6,146,'R02-lower-left')]:
  for kind in ['run','jump','fall']:
   for hold in ['released','direction','diagonal-up']:
    mem=source_room(source,room);mem[0x95:0x98]=[1,0,0];mem[0x9e]=(x+24)//2;mem[0xa1]=y;mem[0xa4]=int(direction>0)
    mode=(4 if direction>0 else 3) if kind=='run' else (7 if direction>0 else 6) if kind=='jump' else 14
    for at in [0xc5,0xc8,0xcb,0x106,0x4fdb]:mem[at]=0
    mem[0xbf]=mem[0xc2]=mode;mem[0xce]=10 if kind=='jump' else 0;mem[0xb0]=2;mem[0xd1]=36
    mem[0x4f57:0x4fdb]=[0]*132;mem[0x4f60 if direction>0 else 0x4f5d]=1
    mem[0x48]=0;mem[0x98]=(6 if direction>0 else 10) if hold=='diagonal-up' else (7 if direction>0 else 11);mem[0x9b]=1;mem[0xdc00]=mem[0xdc01]=255;mem[0xd01e]=0
    call(mem,0x15d0,0x15ee);call(mem,0x2780);call(mem,0x2584)
    cpu=MPU(memory=mem,pc=0x1bc2);cpu.p=0x30;cpu.sp=253;mem[0x1fe:0x200]=[0xfe,0xff]
    before=state(mem);checkpoints=[];steps=[]
    for step in range(7):
     if step:
      mem[0x48]=0;mem[0x98]=15 if hold=='released' else (6 if direction>0 else 10) if hold=='diagonal-up' else (7 if direction>0 else 11)
      cpu.a=0;cpu.p=(cpu.p&~128)|2;cpu.pc=0x1bc2
     r=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
     lib.bl_contact_seed(A.from_buffer_copy(bytes(mem)),R(*r))
     for count in range(300000):
      if count and cpu.pc in boundaries:break
      if cpu.pc in [0x2f8e,0xa83] or (cpu.pc==0x1bc2 and mem[0x29]!=room):checkpoints.append(dict(step=step,pc=hex(cpu.pc),actor=state(mem)))
      cpu.step()
     else:raise AssertionError(('Source escaped',label,kind,step,hex(cpu.pc)))
     instructions+=count;lib.bl_contact_run(0x1bc2);lib.bl_contact_copy(output);lib.bl_contact_regs(regs)
     want=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
     assert not lib.bl_contact_fault(),('Native fault',label,kind,step)
     assert bytes(output)==bytes(mem),('RAM',label,kind,hold,step,[(hex(i),output[i],v) for i,v in enumerate(mem) if output[i]!=v][:10])
     assert list(regs)==want,('Registers',label,kind,step,list(regs),want)
     assert lib.bl_floor_stop()==(0x1c32 if cpu.pc==0x1c32 else 0)
     comparisons+=1;steps.append(dict(step=step,actor=state(mem),stop=hex(cpu.pc)))
     if cpu.pc!=0x1c32:break
    assert any(c['pc']=='0x2f8e' for c in checkpoints),(label,kind,'Did not use actual door path')
    reset=next(c['actor'] for c in checkpoints if c['pc']=='0xa83')
    entry=next(c['actor'] for c in checkpoints if c['pc']=='0x1bc2')
    assert (reset['state'],reset['counter'],reset['wait'])==(0,4,0)
    assert (entry['state'],entry['counter'],entry['wait'])==(0,4,0)
    assert entry['facing']==before['facing'] and entry['room']==(2 if room==0 else 1)
    assert steps[0]['actor']['state']==0 and steps[0]['actor']['counter']==3
    rows.append(dict(exit=label,kind=kind,input_after=hold,before=before,checkpoints=checkpoints,steps=steps))
    print('PASS',label,kind,hold,flush=True)
 BASE.mkdir(parents=True,exist_ok=True);dis=Disassembler(MPU(memory=list(source)));lines=[]
 for first,last in [(0x2f8e,0x2fd6),(0xa6b,0xa83),(0xb30,0xb43),(0x1d77,0x1d84),(0x208d,0x20a0)]:
  pc=first
  while pc<last:
   n,text=dis.instruction_at(pc);lines.append('$%04X %s'%(pc,text));pc+=n
 (BASE/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
 paths=['tools/audit_room_entry_state.py','core/c64_rooms.c','core/c64_actor_programs.h','core/session.c',
  'reference/analysis/floor-walk-2026-10-30/report.json','reference/analysis/floor-walk-2026-10-30/bridge.c','reference/analysis/floor-walk-2026-10-30/build.ps1']
 report=dict(status='passed_source_room_entry_state_reset',source_sha256=SHA,cases=len(rows),main_entries=comparisons,source_instructions=instructions,
  production_changed=False,edition_verified=False,natural_playthrough=False,raster_exact=False,
  method='Source-decoded room seeds; explicit run/jump/fall states at four real R01/R02 door triggers with matching movement history. Actual original $1BC2->$2E39->$2F8E->$09BC chain and seven main iterations compared with live native C: whole RAM, CPU flags/registers and wait boundaries. Released, held direction or held diagonal-up input after crossing; no interleaved IRQ. Not F1/F2 debug room jump.',
  findings=dict(loader_state=0,loader_counter=4,loader_wait=0,facing_preserved=True,first_main_counter=3),
  rows=rows,artifacts=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
 (BASE/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(rows),'room transitions;',comparisons,'main comparisons;',instructions,'source instructions')
if __name__=='__main__':main()
