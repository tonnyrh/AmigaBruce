"""Observe input at movement/attack decisions without changing C64 game memory."""
import json,hashlib,struct,argparse
from pathlib import Path
from vice_binary import Vice
ROOT=Path(__file__).resolve().parents[1]
POINTS={0x1bce:'seam',0x1c5b:'movement',0x1ebd:'walking_fire',0x1dd2:'direction_read',0x1ebf:'right_fire_read',0x1e7e:'left_fire_read',0x1f7c:'standing_fire_read',0x1f6d:'kick_right'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(port,baseline,capture):
 m=json.loads((ROOT/'reference/manifest.json').read_text());snap=ROOT/m['analysis_candidate']['baseline_snapshot_path']
 assert sha(ROOT/m['emulator']['executable_path'])==m['emulator']['executable_sha256']
 assert sha(snap)==m['analysis_candidate']['baseline_snapshot_sha256']
 program_path=ROOT/f'reference/scenarios/{baseline}.json'
 programs=json.loads(program_path.read_text())
 v=Vice(port);checkpoints={};result={}
 def observation(tick,address):
  ram=v.memory(0,0x10f);regs=v.registers()
  return dict(tick=tick,point=POINTS[address],pc=address,x_register=regs[1],cycles=v.history_clock()[1],a_register=regs[0],direction=ram[0x98],fire=ram[0x9b],x=ram[0x9e],y=ram[0xa1],next_state=ram[0xbf],state=ram[0xc2],animation_timer=ram[0xcb])
 def advance(address):
  v.toggle(checkpoints[address],False);v.run_stopped(0x71,struct.pack('<BH',0,1));v.toggle(checkpoints[address],True)
  return v.run_stopped()
 try:
  for name in programs:
   repeats=[]
   for repetition in range(2):
    for cp in checkpoints.values():v.command(0x13,cp.to_bytes(4,'little'))
    checkpoints={}
    assert v.restore(snap)==0x1bce
    v.resource_int('JoyPort1Device',37);v.resource_int('JoyPort2Device',1);v.joystick(255)
    checkpoints[0x1bce]=v.checkpoint(0x1bce)
    for _ in range(8):v.next_hit(checkpoints[0x1bce],0x1bce)
    for address in POINTS:
     if address!=0x1bce:checkpoints[address]=v.checkpoint(address)
    rows=[observation(0,0x1bce)]
    inputs=[value for value,count in programs[name] for _ in range(count)]
    for tick,value in enumerate(inputs,1):
     v.joystick(value);address=advance(0x1bce)
     for _ in range(40):
      if address==0x1bce:rows.append(observation(tick,address));break
      obs=observation(tick,address)
      if obs['x_register']==0:rows.append(obs)
      address=advance(address)
     else:raise RuntimeError('No seam reached')
    repeats.append(rows)
   assert repeats[0]==repeats[1],name
   result[name]=repeats[0];print('PASS phase probe',name,len(rows),flush=True)
  out=ROOT/f'reference/traces/{capture}.json'
  out.write_text(json.dumps({'capture_id':capture,'baseline_capture':baseline,'primary_edition_verified':False,'repetitions':2,'snapshot_sha256':sha(snap),'sources':[{'path':n,'sha256':sha(ROOT/n)} for n in ('tools/capture_c64_phase.py','tools/vice_binary.py','capture-c64-phase.ps1',str(program_path.relative_to(ROOT)).replace('\\','/'))],'scenarios':result},indent=2)+'\n')
 finally:
  for cp in checkpoints.values():v.command(0x13,cp.to_bytes(4,'little'))
  v.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=6515);p.add_argument('--baseline',default='MACHINE-0005');p.add_argument('--capture-id',default='PHASE-0001');args=p.parse_args();run(args.port,args.baseline,args.capture_id)
