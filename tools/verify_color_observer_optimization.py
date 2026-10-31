"""Bind the small observer optimization to current runtime and native controls."""
import argparse,hashlib,json
from pathlib import Path
from verify_renderer_delta_scope import verify as scope,effective_source_path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/color-observer-2026-10-30'
RUN='reference/analysis/optimization-2026-10-27'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(e,p=None):
 target=ROOT/(p or e['path'])
 if p is None and hashlib.sha256(target.read_bytes()).hexdigest()!=e['sha256']:target=effective_source_path(e['path'])
 assert hashlib.sha256(target.read_bytes()).hexdigest()==e['sha256'],str(target)
def verify():
 derivation=scope();assert derivation['publication_applied'] and derivation['color_observer_applied']
 assert read(BASE+'/source-scope.json')==derivation
 paths=[BASE+'/'+p for p in ['host.json','source-scope.json','native-images.json','compiler-core.o']]
 paths+=['tools/verify_color_observer_optimization.py','tools/audit_color_observer_images.py','tools/verify_renderer_delta_scope.py','docs/COLOR_OBSERVER_OPTIMIZATION.md']
 host=read(BASE+'/host.json');assert host['source_cases']==7424 and host['renderer_cases']==192 and host['observer_domain_cases']==4096 and host['full_ram_and_registers']
 images=read(BASE+'/native-images.json');assert len(images['builds'])==6 and images['candidate_sha256']==item('core/c64_rooms.c')['sha256']
 for e in images['builds']:check(e)
 pairs=[]
 for suffix in ['', '-repeat']:
  both=[]
  for label in ['publication-guard-tour'+suffix,'color-observer-tour'+suffix]:
   folder=RUN+'/'+label;d=read(folder+'/identity.json');r=d['run']
   assert d['status']=='passed_scoped_20_room_timing_route' and not d['realtime_accepted'] and not d['natural_playthrough']
   raw=dict(s.split('=',1) for s in (ROOT/folder/'native.txt').read_text().splitlines() if '=' in s);assert raw==r
   assert r['source_tour_completed']=='20' and r['source_tour_error']=='0' and r['restored_os']=='1' and r['contact_kernel_cases']=='710'
   for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors','bad_presents']:assert r[k]=='0'
   for e in d['build']:check(e,folder+'/'+Path(e['path']).name)
   for e in d['source_files']:
    name=e['path'];target=None
    if name.startswith('.tmp/source-tour-'):target=folder+('/compiled-main.c' if name.endswith('/main.c') else '/build.ps1')
    check(e,target)
   assert len(d['rooms'])==20 and all(x['steps']==120 and x['chip_largest']>=49152 for x in d['rooms'])
   both.append(d);paths += [folder+'/'+p for p in ['identity.json','native.txt','compiled-main.c','build.ps1']]
  before,after=both
  assert item(RUN+'/publication-guard-tour'+suffix+'/compiled-main.c')['sha256']==item(RUN+'/color-observer-tour'+suffix+'/compiled-main.c')['sha256']
  old=sum(x['lines'] for x in before['rooms']);new=sum(x['lines'] for x in after['rooms']);assert new<old
  assert after['rooms'][19]['lines']<before['rooms'][19]['lines']
  pairs.append(dict(before_lines=old,after_lines=new,r20_before=before['rooms'][19]['lines'],r20_after=after['rooms'][19]['lines']))
 native=read('reference/validation/source-world-native.json');assert not native['failures'] and native['run']['source_actor_fixture_cases']=='53' and native['run']['frames']=='1200' and int(native['run']['chip_largest_loaded'])>=49152
 math=read(RUN+'/color-observer-r01/identity.json');assert math['run']['contact_kernel_cases']=='710' and math['run']['sprite_copy_cases']=='256'
 for d in [native,math]:
  for e in d['source_files']:check(e)
 paths+=['reference/validation/source-world-native.json',RUN+'/color-observer-r01/identity.json',RUN+'/color-observer-r01/native.txt']
 for label in ['room1-observer','room12-observer']:paths+=['reference/analysis/normal-runtime-2026-10-30/'+label+'/report.json']
 return dict(status='passed_scoped_observer_delivery_realtime_open',source_cases=7424,renderer_cases=192,observer_domain_cases=4096,native_cases=53,pairs=pairs,extra_production_bss=0,normal_binary=item('amiga/out/bruce_amiga.exe'),edition_verified=False,natural_playthrough=False,realtime_accepted=False,artifacts=[item(p) for p in paths])
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path=ROOT/'reference/validation/color-observer-optimization.json'
 if a.record:path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 else:assert read('reference/validation/color-observer-optimization.json')==r
 print('PASS scoped observer integration; 53 native fixtures, 710 separate controls; real-time remains open')
if __name__=='__main__':main()
