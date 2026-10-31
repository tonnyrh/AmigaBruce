"""Verify private sprite-publisher experiment artifacts; never approve delivery."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/sprite-publish-2026-10-30'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 proofs=[]
 def check(items):
  for e in items:assert item(ROOT/e['path'])==e,e['path']
 for label in ['host.json','direct-call/host.json']:
  p=BASE/label;r=read(p);check(r['artifacts']);assert r['all_ram_and_registers'] and not r['production_changed'];proofs.append(item(p))
 assert read(BASE/'host.json')['source_cases']==21504
 assert read(BASE/'direct-call/host.json')['source_cases']==640
 native=read(BASE/'native-fixture.json');assert not native['production_core_compiled'] and not native['failures']
 assert int(native['run']['frames'])==1200 and int(native['run']['chip_largest_loaded'])>=49152
 proofs.append(item(BASE/'native-fixture.json'))
 tours=[]
 for label in ['sprite-publish-heap-before','sprite-publish-heap-candidate','sprite-publish-direct-tour','sprite-publish-direct-before-repeat','sprite-publish-direct-tour-repeat']:
  folder=ROOT/'reference/analysis/optimization-2026-10-27'/label
  p=folder/'identity.json'
  if not p.exists():continue
  r=read(p);assert len(r['rooms'])==20 and r['status']=='passed_scoped_20_room_timing_route'
  for e in r['build']:assert hashlib.sha256((folder/e['path']).read_bytes()).hexdigest()==e['sha256']
  assert all(row['steps']==120 and row['chip_largest']>=49152 for row in r['rooms'])
  run=r['run'];assert int(run['source_tour_stats_bytes'])==880 and int(run['source_tour_stats_memory'])&2 and int(run['source_tour_stats_address'])<524288
  assert int(run['bad_presents'])==0 and 300<=int(run['present_min_line'])<=int(run['present_max_line'])<=308
  for key in ['source_tour_error','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:assert int(run[key])==0,key
  assert int(run['contact_kernel_cases'])==710 and int(run['sprite_copy_cases'])==256
  main=folder/'compiled-main.c';proofs.extend([item(p),item(main),item(folder/'controller-generation.json')])
  tours.append(dict(label=label,main_sha256=item(main)['sha256'],totals={k:sum(int(a[k]) for a in r['rooms']) for k in ['fields','lines','missed']},room12=r['rooms'][11],chip_min=min(a['chip_largest'] for a in r['rooms'])))
 assert len({r['main_sha256'] for r in tours})==1,'Timing controllers differ'
 perf=ROOT/'reference/analysis/optimization-2026-10-27/sprite-publish-direct-r01';r=read(perf/'identity.json');overrides=read(perf/'compile-overrides.json');check(overrides['actual_inputs']);check([overrides['main'],overrides['builder']]);assert not overrides['production_core_compiled']
 assert int(r['run']['source_world_steps'])==360 and int(r['run']['contact_kernel_cases'])==710
 proofs.extend([item(perf/'identity.json'),item(perf/'compile-overrides.json')])
 production=[item(ROOT/p) for p in ['core/c64_rooms.c','amiga/main.c','amiga/out/bruce_amiga.exe']]
 assert production[0]['sha256']=='2d3692711dfd57cd2e108e697df2c01a958e47657e3d85069ee1930dec00efc1'
 assert production[1]['sha256']=='4e23ed811856545f437887033a085216099130848f6ad8d951d0741086e56185'
 assert production[2]['sha256']=='4a397cc5be9663cc92d5b44749d1bd63df6119621f61c2e63e78941b29859811'
 report=dict(status='verified_private_sprite_publication_experiments',production_changed=False,promoted=False,realtime_accepted=False,natural_playthrough=False,tours=tours,direct_r01=dict(fields=int(r['run']['source_clock_elapsed']),missed=int(r['run']['source_clock_missed']),chip_largest=int(r['run']['chip_largest_loaded'])),normal=production,artifacts=proofs,limits=['Small workload changes require paired repeated target measurements before promotion','Diagnostic stats allocation differs from production; original field and reserve gates unchanged','Source equality controls do not establish physical beam timing or natural input phase'])
 (BASE/'experiment.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS private sprite experiments; tours',len(tours),'; production unchanged; promotion and real-time gates open')
if __name__=='__main__':main()
