"""Native C64 contact observations: no gameplay RAM/register writes."""
import json,hashlib,argparse
from pathlib import Path
from vice_binary import Vice
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(port):
 m=json.loads((ROOT/'reference/manifest.json').read_text());a=m['analysis_candidate'];snapshot=ROOT/a['baseline_snapshot_path']
 assert sha(snapshot)==a['baseline_snapshot_sha256']
 assert sha(ROOT/m['emulator']['executable_path'])==m['emulator']['executable_sha256']
 programs=json.loads((ROOT/'reference/scenarios/ENEMY-EDGE-0001.json').read_text())
 v=Vice(port);cp=None;result={}
 def observe(tick,origin):
  before=v.history_clock();ram=v.memory(0,0x10f);extra=v.memory(0x4f40,0x4f56);regs=v.registers();assert v.history_clock()==before and regs[3]==0x1bce and before[0]==0x1bcc
  actors=[dict(active=ram[0x95+i],x=ram[0x9e+i],y=ram[0xa1+i],next_state=ram[0xbf+i],state=ram[0xc2+i],health=ram[0xd1+i],hit=ram[0xbc+i],facing=ram[0xa4+i],wait=ram[0x106+i],counter=ram[0xce+i],raw_4f45=extra[5+i]) for i in range(3)]
  return dict(tick=tick,cycles=before[1]-origin,raster_line=regs[0x35],raster_cycle=regs[0x36],direction=ram[0x98],fire=ram[0x9b],room=ram[0x29],enemy_timers=[ram[0x5d],ram[0x5e]],lantern_counts=list(ram[0x2a:0x3e]),actors=actors)
 try:
  for name,segments in programs.items():
   repeats=[]
   for _ in range(2):
    if cp is not None:v.command(0x13,cp.to_bytes(4,'little'))
    assert v.restore(snapshot)==0x1bce
    v.resource_int('JoyPort1Device',37);v.resource_int('JoyPort2Device',1);v.joystick(255);cp=v.checkpoint(0x1bce)
    for _ in range(8):v.next_hit(cp,0x1bce)
    origin=v.history_clock()[1];rows=[observe(0,origin)];tick=0
    for value,count in segments:
     for _ in range(count):
      tick+=1;v.joystick(value);v.next_hit(cp,0x1bce);rows.append(observe(tick,origin))
    for old,new in zip(rows,rows[1:]):
     assert new['cycles']>old['cycles']
     # Room-loading stalls are measured, not forced to the movement cadence.
    repeats.append(rows)
   assert repeats[0]==repeats[1],name
   result[name]=rows
   output={'capture_id':'ENEMY-EDGE-0001','primary_edition_verified':False,'repetitions':2,'snapshot_sha256':sha(snapshot),'emulator_sha256':m['emulator']['executable_sha256'],'sources':[{'path':n,'sha256':sha(ROOT/n)} for n in ('tools/capture_c64_enemy_edges.py','tools/vice_binary.py','capture-c64-enemy-edges.ps1','reference/scenarios/ENEMY-EDGE-0001.json')],'scenarios':result}
   (ROOT/'reference/traces/ENEMY-EDGE-0001.json').write_text(json.dumps(output,indent=2)+'\n')
   hits=sum(any(a['hit'] for a in r['actors']) for r in rows)
   print('PASS',name,len(rows),'observations, contact rows',hits,flush=True)
 finally:
  if cp is not None:v.command(0x13,cp.to_bytes(4,'little'))
  v.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=6516);run(p.parse_args().port)
