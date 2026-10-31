"""Audit the measured live-record projection change and its rejected pilot."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/view-mask-2026-10-29'
RUN='reference/analysis/optimization-2026-10-27'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(entry,p=None):assert item(p or entry['path'])['sha256']==entry['sha256'],p or entry['path']
def verify():
 paths=[]
 raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
 assert hashlib.sha256(raw).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
 for name in ['baseline','bulk-pilot','final']:
  path=BASE+'/'+name+'/manifest.json';paths.append(path)
  for entry in read(path)['files']:check(entry,BASE+'/'+name+'/'+entry['path'])
 stages={'render-coherence-kernels':'baseline','view-mask-before-profile':'baseline','view-mask-after-profile':'mask-only','view-bulk-pilot-profile':'bulk-pilot','view-bulk-final-profile':'final','view-bulk-final-timing':'final'}
 identities={};profiles={}
 for label,variant in stages.items():
  folder=RUN+'/'+label;d=read(folder+'/identity.json');identities[label]=d;r=d['run']
  for entry in d['source_files']:
   archived=BASE+'/'+variant+'/'+entry['path']
   if variant=='mask-only' and entry['path']=='core/c64_rooms.c':archived=BASE+'/mask-only/c64_rooms.c'
   if not (ROOT/archived).exists():archived=BASE+'/baseline/'+entry['path']
   check(entry,archived)
  for entry in d['build']:check(entry,folder+'/'+Path(entry['path']).name)
  for key in ['source_audio_faults','source_dma_faults','runtime_arithmetic_errors','c64_room_fault','vic_compare_errors','contact_kernel_errors']:assert r[key]=='0',(label,key)
  assert r['source_perf_steps']==r['source_world_steps']=='360'
  assert int(r['chip_largest_loaded'])>=49152 and r['restored_os']=='1'
  assert int(r['drawn_image_fields'])+int(r['held_image_fields'])==int(r['frames'])
  assert int(r['max_held_image_streak'])<=3
  if d['profile']:
   assert r['contact_kernel_cases']=='454' and r['perf_errors']=='0'
  else:assert r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
  profiles[label]={row['name']:row for row in read(folder+'/native.json')['profile']}
  paths += [folder+'/'+name for name in ['identity.json','native.txt','native.json']]
 before=profiles['view-mask-before-profile']['view'];after=profiles['view-bulk-final-profile']['view'];rejected=profiles['view-mask-after-profile']['view']
 assert before['calls']==after['calls']==360 and after['exclusive_lines']<before['exclusive_lines']<rejected['exclusive_lines']
 old=identities['render-coherence-kernels']['run'];new=identities['view-bulk-final-timing']['run']
 assert int(new['source_clock_elapsed'])<int(old['source_clock_elapsed'])
 assert int(new['source_clock_missed'])<=int(old['source_clock_missed'])
 assert old['drawn_image_fields']==new['drawn_image_fields']=='360'
 host=read('reference/validation/view-mask-host.json')
 assert host['source_sha256']==hashlib.sha256(raw).hexdigest()
 assert host['cases']==2293920 and host['bulk_vectors']==1280 and host['bulk_mask_checks']==25600
 for entry in host['source_files']:check(entry)
 for entry in identities['view-bulk-final-timing']['source_files']:check(entry,'reference/analysis/vic-cache-2026-10-29/before/'+entry['path'])
 paths += ['reference/validation/view-mask-host.json','tools/verify_view_projection.py','docs/VIEW_PROJECTION_OPTIMIZATION.md',BASE+'/mask-only/manifest.json',BASE+'/source-record-disassembly.txt']
 return dict(status='measured_live_projection_cpu_reduction',edition_verified=False,natural_playthrough=False,realtime_accepted=False,source_steps=360,view_mean_before=before['average_exclusive'],view_mean_after=after['average_exclusive'],view_cpu_reduction_percent=round((before['exclusive_lines']-after['exclusive_lines'])*100/before['exclusive_lines'],3),unprofiled_fields_before=int(old['source_clock_elapsed']),unprofiled_fields_after=int(new['source_clock_elapsed']),audio_misses_before=int(old['source_clock_missed']),audio_misses_after=int(new['source_clock_missed']),artifacts=[item(p) for p in paths],limits=['One unprofiled pair; two final bulk profiles support local CPU result','R01 idle/invincible diagnostic route, not a whole-game speed claim','13-bit cap is the existing projection limit; no new C64 rule or temporal cache'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/view-projection.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n')
 else:assert read(path)==r
 print('PASS live projection:',r['view_mean_before'],'->',r['view_mean_after'],'lines/call;',r['unprofiled_fields_before'],'->',r['unprofiled_fields_after'],'PAL fields/360 source steps')
if __name__=='__main__':main()
