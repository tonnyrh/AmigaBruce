"""Audit one-pass raw/opaque VIC cache, preserving historical before/after identities."""
import json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/vic-cache-2026-10-29'
RUN='reference/analysis/optimization-2026-10-27'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(entry,p=None):assert item(p or entry['path'])['sha256']==entry['sha256'],p or entry['path']
def verify():
 paths=[]
 for variant in ['before','candidate']:
  p=BASE+'/'+variant+'/manifest.json';paths.append(p)
  for entry in read(p)['files']:check(entry,BASE+'/'+variant+'/'+entry['path'])
 identities={};profiles={}
 for label in ['view-bulk-final-profile','view-bulk-final-timing','vic-cache-wrapped-profile','vic-cache-wrapped-timing','vic-cache-repeat-timing']:
  folder=RUN+'/'+label;d=read(folder+'/identity.json');identities[label]=d;r=d['run']
  for entry in d['source_files']:
   archived=BASE+('/before/' if label.startswith('view-') or entry['path']!='core/c64_rooms.c' else '/candidate/')+entry['path'];check(entry,archived)
  for entry in d['build']:check(entry,folder+'/'+Path(entry['path']).name)
  for key in ['source_audio_faults','source_dma_faults','runtime_arithmetic_errors','c64_room_fault','vic_compare_errors','contact_kernel_errors']:assert r[key]=='0',(label,key)
  assert r['source_perf_steps']==r['source_world_steps']=='360'
  assert int(r['chip_largest_loaded'])>=49152 and r['restored_os']=='1'
  assert int(r['drawn_image_fields'])+int(r['held_image_fields'])==int(r['frames'])
  assert int(r['max_held_image_streak'])<=3
  if d['profile']:assert r['contact_kernel_cases']=='454' and r['perf_errors']=='0'
  else:assert r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
  profiles[label]={x['name']:x for x in read(folder+'/native.json')['profile']}
  paths += [folder+'/'+p for p in ['identity.json','native.txt','native.json']]
 before=profiles['view-bulk-final-profile']['vic'];after=profiles['vic-cache-wrapped-profile']['vic'];assert after['average_exclusive']<before['average_exclusive']
 old=identities['view-bulk-final-timing']['run'];new=identities['vic-cache-wrapped-timing']['run'];repeat=identities['vic-cache-repeat-timing']['run']
 for r in [new,repeat]:
  assert int(r['source_clock_elapsed'])<int(old['source_clock_elapsed'])
  assert int(r['source_clock_missed'])<=int(old['source_clock_missed'])
 assert identities['vic-cache-wrapped-timing']['build']==identities['vic-cache-repeat-timing']['build']
 for entry in identities['vic-cache-wrapped-timing']['source_files']:check(entry,'reference/analysis/menu-publication-2026-10-29/before/'+entry['path'])
 host=read('reference/validation/vic-cache-host.json');assert host['cases']==25600 and host['full_ram_preservation_cases']==1024
 for entry in host['source_files']:check(entry)
 paths += ['reference/analysis/menu-publication-2026-10-29/before/manifest.json','reference/validation/vic-cache-host.json','tools/verify_vic_cache_optimization.py','docs/VIC_CACHE_OPTIMIZATION.md',BASE+'/rejected-unrolled/result.json',BASE+'/rejected-postincrement/result.json']
 return dict(status='measured_one_pass_vic_cache',edition_verified=False,natural_playthrough=False,realtime_accepted=False,vic_mean_before=before['average_exclusive'],vic_mean_after=after['average_exclusive'],unprofiled_fields=[int(r['source_clock_elapsed']) for r in [old,new,repeat]],audio_misses=[int(r['source_clock_missed']) for r in [old,new,repeat]],minimum_chip_block=min(int(r['chip_largest_loaded']) for r in [new,repeat]),artifacts=[item(p) for p in paths],limits=['R01 diagnostic route; no whole-game speed or original raster certification','Allocator largest blocks vary across boots; only minimum margin accepted','No temporal cache/version assumption; same63 raw bytes and21 opaque rows'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/vic-cache-optimization.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n')
 else:assert read(path)==r
 print('PASS one-pass VIC cache:',r['unprofiled_fields'],'fields;',r['audio_misses'],'misses')
if __name__=='__main__':main()
