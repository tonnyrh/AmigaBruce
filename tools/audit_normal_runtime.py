"""Boundary-only counters from an owned, unmodified normal Amiga build.
No profiling, framebuffer recording, source-memory writes or IPC reads in
its measured interval. Debug invincibility/start-room are explicit controls.
"""
import argparse,hashlib,json,re,struct,time
from pathlib import Path
from winuae_ipc import command
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--room',type=int,required=True);p.add_argument('--label',required=True);p.add_argument('--seconds',type=int,default=140);a=p.parse_args()
 assert 1<=a.room<=20 and a.seconds>=125
 pipe=re.findall(r"IPC: Named Pipe '([^']+)' open",a.log.read_text(errors='replace'))[-1]
 def cmd(q):return command(pipe,q,expected_pid=a.pid)
 def read(at,n):
  reply=cmd('DBG m %x %x'%(at,(n+15)//16));data=bytearray()
  for line in reply.splitlines():
   m=re.match(r'^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{4}\s+){1,8})',line)
   if m:data.extend(bytes.fromhex(m[1]))
  assert len(data)>=n,(hex(at),reply);return bytes(data[:n])
 def long(at):return int.from_bytes(read(at,4),'big')
 def key(event):
  cmd('EVT KEY_'+event+' 1');time.sleep(.35);cmd('EVT KEY_'+event+' 0');time.sleep(.4)
 cmd('EVT KEY_SHIFT_LEFT 1');key('D');cmd('EVT KEY_SHIFT_LEFT 0');time.sleep(.3)
 for event in ['F1','F2']+['F4']*(a.room-1)+['RETURN']:key(event)
 time.sleep(15)
 task=long(long(4)+276);cli=long(task+172)*4;node=long(cli+60)*4;hunks=[]
 while node:hunks.append(node+4);node=long(node)*4;assert len(hunks)<=8
 assert len(hunks)==4
 elf=ROOT/'amiga/out/bruce_amiga.elf';exe=ROOT/'amiga/out/bruce_amiga.exe';elf_hash=hashlib.sha256(elf.read_bytes()).hexdigest();exe_hash=hashlib.sha256(exe.read_bytes()).hexdigest()
 bss,symbols=elf_symbols(elf)
 def addr(name):return hunks[3]+symbols[name]-bss
 def pause():cmd('EVT SPC_PAUSE 1');cmd('EVT SPC_PAUSE 0');time.sleep(.1)
 def sample():
  m=addr('m');fields=['source_clock_elapsed','source_clock_missed','source_audio_fields','source_clock_paused_fields','source_music_fields','game_field_last']
  result={name:long(addr(name)) for name in fields}
  for name in ['actor_logic_steps','actor_loading_epoch','source_fault','source_dma_faults']:
   result[name]=int.from_bytes(read(addr(name),2),'big')
  result['room']=read(m+0x29,1)[0]+1;result['active_actors']=list(read(m+0x95,3))
  result['source_age']=int.from_bytes(read(m+0x87,2),'little')
  result['menu_or_delay']=list(read(addr('actor_gameover_pending'),1))+list(read(addr('actor_delay_pending'),1))
  return result
 pause()
 try:before=sample()
 finally:pause()
 assert before['room']==a.room and not any(before['menu_or_delay']),before
 print('BEGIN normal room %d; no emulator reads/capture/profiling for %d seconds'%(a.room,a.seconds),flush=True)
 start=time.monotonic()
 while time.monotonic()-start<a.seconds:
  time.sleep(max(0,min(10,a.seconds-(time.monotonic()-start))))
  if int(time.monotonic()-start)%30<10:print('Normal interval still running: %ds'%(time.monotonic()-start),flush=True)
 pause()
 try:after=sample()
 finally:pause()
 assert hashlib.sha256(elf.read_bytes()).hexdigest()==elf_hash and hashlib.sha256(exe.read_bytes()).hexdigest()==exe_hash
 fields=(after['game_field_last']-before['game_field_last'])&0xffffff
 steps=(after['actor_logic_steps']-before['actor_logic_steps'])&65535
 missed=after['source_clock_missed']-before['source_clock_missed']
 assert fields>=6000,(fields,'Too short for required normal-run gate')
 assert after['room']==before['room'] and after['actor_loading_epoch']==before['actor_loading_epoch'],'Room reloaded during interval'
 assert not after['source_fault'] and not after['source_dma_faults']
 cadence=abs(fields-3*steps)<=6
 report=dict(status='measured_normal_runtime_gates_'+('passed' if missed==0 and cadence else 'not_met'),
  method='Unmodified normal EXE, boundary-only paused scalar counter reads. No IPC/profile/framebuffer capture/source writes during interval. Stationary debug invincible/infinite-lives session.',
  edition_verified=False,natural_playthrough=False,original_irq_phase_verified=False,physical_a500=False,
  pid=a.pid,room=a.room,wall_seconds=time.monotonic()-start,normal_exe_sha256=exe_hash,normal_elf_sha256=elf_hash,
  before=before,after=after,measured_fields=fields,source_steps=steps,fields_per_step=fields/steps if steps else None,missed_audio_ticks=missed,
  gate_no_missed_audio_ticks=missed==0,gate_three_field_cadence=cadence,requested_unobserved_wall_seconds=a.seconds,wall_seconds_includes_post_interval_boundary_reads=True,full_realtime_accepted=False)
 out=ROOT/'reference/analysis/normal-runtime-2026-10-30'/a.label;out.mkdir(parents=True,exist_ok=True)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
