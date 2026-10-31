"""Verify measured color-store work without treating it as real-time acceptance."""
import argparse,hashlib,json
from pathlib import Path
from verify_renderer_delta_scope import effective_source_path
from verify_final_color_scope import verify as source_scope
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/final-colors-2026-10-30'
RUN='reference/analysis/optimization-2026-10-27'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(e,path=None):
 target=ROOT/(path or e['path'])
 if path is None and hashlib.sha256(target.read_bytes()).hexdigest()!=e['sha256']:
  target=effective_source_path(e['path'])
 assert hashlib.sha256(target.read_bytes()).hexdigest()==e['sha256'],path or e['path']
def verify():
 assert read(BASE+'/source-scope.json')==source_scope()
 paths=[BASE+'/source-scope.json',BASE+'/host.json',BASE+'/native-images.json',BASE+'/before/manifest.json','tools/verify_final_color_optimization.py','tools/verify_final_color_scope.py','docs/FINAL_COLOR_OPTIMIZATION.md']
 images=read(BASE+'/native-images.json');assert images['status']=='passed_original_writer_and_native_color_kernel_linkage'
 for e in images['builds']+images['artifacts']:check(e)
 tours=[]
 for label in ['final-colors-tour-before','final-colors-tour-v3']:
  folder=RUN+'/'+label;d=read(folder+'/identity.json');r=d['run']
  assert d['status']=='passed_scoped_20_room_timing_route' and not d['natural_playthrough'] and not d['realtime_accepted']
  raw=dict(s.split('=',1) for s in (ROOT/folder/'native.txt').read_text().splitlines() if '=' in s);assert raw==r
  assert r['source_tour_completed']=='20' and r['source_tour_error']=='0' and r['restored_os']=='1'
  assert r['contact_kernel_cases']=='710' and r['sprite_copy_cases']=='256'
  for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors']:assert r[key]=='0'
  for e in d['build']:check(e,folder+'/'+Path(e['path']).name)
  for e in d['source_files']:
   p=e['path']
   if p.startswith('.tmp/source-tour-'):
    p=folder+('/compiled-main.c' if p.endswith('/main.c') else '/build.ps1')
   elif label.endswith('before') and p.startswith(('core/','amiga/')):p=BASE+'/variant1/'+p
   check(e,None if p==e['path'] else p)
  for i,row in enumerate(d['rooms']):
   v=list(map(int,r['source_tour_'+str(i)].split(',')))
   assert len(v)==11 and row['room']==i+1 and row['steps']==v[0]==120 and v[7]==i+1
   assert [row[k] for k in ['fields','lines','missed','drawn','held','preparation_lines','chip_largest','slow_largest','animation_bytes']]==v[1:7]+v[8:]
   assert row['chip_largest']>=49152
  tours.append(d);paths += [folder+'/'+p for p in ['identity.json','native.txt','compiled-main.c','build.ps1','controller-generation.json']]
 assert item(RUN+'/final-colors-tour-before/compiled-main.c')['sha256']==item(RUN+'/final-colors-tour-v3/compiled-main.c')['sha256']
 rows=[dict(room=a['room'],before_lines=a['lines'],after_lines=b['lines'],delta_lines=b['lines']-a['lines'],before_missed=a['missed'],after_missed=b['missed']) for a,b in zip(tours[0]['rooms'],tours[1]['rooms'])]
 old=sum(x['before_lines'] for x in rows);new=sum(x['after_lines'] for x in rows);assert new<old
 assert rows[19]['after_lines']<rows[19]['before_lines'] and rows[14]['after_lines']<=rows[14]['before_lines']
 repeats=[]
 for label in ['final-colors-r01-v3','final-colors-r01-v3-repeat']:
  folder=RUN+'/'+label;d=read(folder+'/identity.json');r=d['run'];assert r['source_world_steps']==r['source_perf_steps']=='360'
  for e in d['source_files']:check(e)
  for e in d['build']:check(e,folder+'/'+Path(e['path']).name)
  assert r['drawn_image_fields']=='360' and int(r['max_held_image_streak'])<=3 and int(r['chip_largest_loaded'])>=49152
  assert int(r['source_clock_elapsed'])+int(r['source_clock_starts'])-int(r['source_clock_missed'])==int(r['source_audio_fields'])+int(r['source_music_fields'])
  repeats.append(d);paths += [folder+'/identity.json',folder+'/native.txt']
 assert repeats[0]['build']==repeats[1]['build']
 native=read('reference/validation/source-world-native.json');assert not native['failures'] and native['run']['source_actor_fixture_cases']=='53' and native['run']['frames']=='1200'
 for e in native['source_files']+native['build']:check(e)
 footprint=read(BASE+'/native-footprint.json');assert footprint['current_variant']==3
 for row in footprint['builds']:check(row['elf'])
 assert footprint['builds'][0]['sections']['.bss']==footprint['builds'][1]['sections']['.bss']
 paths += ['reference/validation/source-world-native.json',BASE+'/native-footprint.json',BASE+'/compiler-probes/report.json']
 return dict(status='measured_scoped_color_store_optimization_realtime_open',source_controls=7424,renderer_controls=192,native_controls=53,rooms=rows,before_lines=old,after_lines=new,work_reduction_percent=round((old-new)*100/old,3),r20_reduction_percent=round((rows[19]['before_lines']-rows[19]['after_lines'])*100/rows[19]['before_lines'],3),audio_misses=[sum(x[k] for x in rows) for k in ['before_missed','after_missed']],r01_elapsed=[int(x['run']['source_clock_elapsed']) for x in repeats],r01_missed=[int(x['run']['source_clock_missed']) for x in repeats],artifacts=[item(p) for p in paths],limits=['Continuous debug-jump source history; no isolated per-room initial-state equivalence or natural play claim','Some room intervals increase; R10+1.117 percent is the largest in this pair','R01 short counter includes title; repeated11 misses vs historical9 remain an open timing issue','No real-time, input/IRQ-phase, whole-call-stack or physical A500 acceptance'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/final-colors-optimization.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 else:assert read('reference/validation/final-colors-optimization.json')==r
 print('PASS scoped color-store work:',r['r20_reduction_percent'],'percent R20;',r['work_reduction_percent'],'percent across controlled20-room route; real-time remains open')
if __name__=='__main__':main()
