"""Current compact backend delivery, with frozen preceding-stage provenance.

Checks current source-byte domains, actual target controls, unchanged
renderer/data, generated-code derivation, primitives and normal UI images.
No real-time, original-edition or natural-playthrough gate is relaxed.
"""
import argparse,hashlib,json,re
from pathlib import Path
from native_actor_continuations import compact_actor_calls
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/flat-control-compact-2026-10-30'
ARCHIVE=BASE+'/delivery-before'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def check(entries,historical=False):
 for e in entries:
  p=e['path']
  if historical and (not (ROOT/p).exists() or item(p)['sha256']!=e['sha256']):p=ARCHIVE+'/'+p
  assert item(p)['sha256']==e['sha256'],p

def enabled():
 p=ROOT/'reference/analysis/actor-chain-2026-10-26/translation.json'
 return p.exists() and read(p.relative_to(ROOT).as_posix()).get('native_continuations',{}).get('version')==1

def verify():
 if not globals().get('_contact_parent_replay',False):
  from verify_contact_unroll_delivery import enabled as contact_enabled,verify_current as verify_contact
  if contact_enabled():return verify_contact()
 if not globals().get('_display_parent_replay',False):
  from verify_loader_blank_delivery import enabled as display_enabled,verify_current as verify_display
  if display_enabled():return verify_display()
 if not globals().get('_audio_parent_replay',False):
  from verify_audio_boundary_delivery import enabled as audio_enabled,verify_current
  if audio_enabled():return verify_current()
 assert enabled() and item('.reference/c64/work/untrained-memory.bin')['sha256']==SHA
 archive=read(ARCHIVE+'/manifest.json')
 for e in archive['files']:assert item(ARCHIVE+'/'+e['path'])['sha256']==e['sha256']
 parent=read(ARCHIVE+'/reference/validation/source-world-delivery.json')
 assert parent['source_sha256']==SHA and parent['source_controls']==3034 and parent['native_controls']==53
 assert not parent['full_original_parity'] and not parent['realtime_gate_passed']
 prior=read(ARCHIVE+'/parent-artifacts.json')
 for e in prior['artifacts']:assert item(ARCHIVE+'/'+e['path'])['sha256']==e['sha256']
 for e in archive['files']:
  if e['path'].startswith('core/') and e['path']!='core/c64_actor_programs.h':assert item(e['path'])['sha256']==e['sha256'],e['path']
 for p in ['amiga/main.c','amiga-build.ps1']:assert item(p)['sha256']==item(ARCHIVE+'/'+p)['sha256']
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
 original=(ROOT/ARCHIVE/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
 generated,meta=compact_actor_calls(original,source)
 assert generated==(ROOT/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
 assert generated==(ROOT/BASE/'candidate/c64_actor_programs.h').read_text(encoding='utf-8-sig')
 translation=read('reference/analysis/actor-chain-2026-10-26/translation.json');assert translation['native_continuations']==meta
 old=(ROOT/ARCHIVE/'tools/build_c64_actors.py').read_text(encoding='utf-8-sig')
 expected=old.replace('from build_fighter_dma import pack,unpack','from build_fighter_dma import pack,unpack\nfrom native_actor_continuations import compact_actor_calls').replace('    code,meta=translate(b,roots,actors=True)','    code,meta=translate(b,roots,actors=True)\n    code,native_calls=compact_actor_calls(code,b)\n    meta[\'native_continuations\']=native_calls')
 assert expected==(ROOT/'tools/build_c64_actors.py').read_text(encoding='utf-8-sig')
 proofs=[ARCHIVE+'/manifest.json',ARCHIVE+'/parent-artifacts.json',ARCHIVE+'/reference/validation/source-world-delivery.json','tools/native_actor_continuations.py','tools/build_c64_actors.py','tools/verify_compact_actor_delivery.py','tools/verify_source_world_delivery.py','tools/verify_source_optimization.py','tools/check_compact_boot.py','tools/audit_native_animation_frame.py','tools/audit_native_menu_publication.py','tools/audit_normal_source_clock.py','docs/NATIVE_CONTINUATION_EXPERIMENT.md','docs/AMIGA_OPTIMIZATION_PLAN.md','docs/ACTIVE_TESTS.md','docs/parity/register.csv']
 actors=read('reference/analysis/actor-chain-2026-10-26/report.json');world=read('reference/analysis/actor-chain-2026-10-26/integrated-controls.json')
 assert actors['checks']==3034 and len(actors['rows'])==3034
 assert len(world['checks'])==5 and world['instructions']==7055873 and world['checks'][-1]['stop']=='$0584' and world['checks'][-1]['terminal_life']
 for r in [actors,world,translation]:
  assert r['source_sha256']==SHA and not r['edition_verified'] and not r['natural_playthrough'];check(r.get('source_files',[]));check(r.get('generated',[]))
 for p in ['report.json','integrated-controls.json','translation.json']:proofs.append('reference/analysis/actor-chain-2026-10-26/'+p)
 domains={
 'source-contact-host':('checks',4239),'source-sprite-copy-host':('checks',1536),'source-object-host':('checks',65536),'source-score-host':('checks',2852),'source-visibility-host':('checks',768),'source-vic-host':('calls',8741),'vic-cache-host':('cases',25600),'source-audio-host':('source_cpu_fields_compared',7540),'source-dma-host':('channel_images',4554),'view-mask-host':('cases',2293920)}
 for name,(key,value) in domains.items():
  p='reference/validation/'+name+'.json';r=read(p);assert r[key]==value,(name,key);check(r['source_files']);proofs.append(p)
  if 'source_sha256' in r:assert r['source_sha256']==SHA
  assert not r.get('edition_verified',False) and not r.get('natural_playthrough',False)
 assert read('reference/validation/source-contact-host.json')['service_register_cases']==489
 assert read('reference/validation/source-sprite-copy-host.json')['brk_controls']==312
 assert read('reference/validation/source-object-host.json')['driver_checks']==480
 assert read('reference/validation/source-dma-host.json')['fields']==1518
 paint=read('reference/validation/source-paint-host.json');assert len(paint['cases'])==6;check(paint['source_files']);proofs.append('reference/validation/source-paint-host.json')
 irq=read('reference/analysis/irq-input-2026-10-30/irq-context-candidate.json');check(irq['artifacts']);assert irq['cases']==3352 and irq['instructions']==479308 and irq['all_ram_and_registers'] and irq['returned_pc_verified'] and irq['sid_gate_edges_verified'];proofs.append('reference/analysis/irq-input-2026-10-30/irq-context-candidate.json')
 for name,folder in [('fallback',BASE+'/capacity1')]:
  r=read(folder+'/report.json');assert r['checks']==3034;check(r['source_files'],historical=True)
  r=read(folder+'/integrated-controls.json');assert len(r['checks'])==5 and r['instructions']==7055873;check(r['source_files'],historical=True);proofs.extend([folder+'/report.json',folder+'/integrated-controls.json'])
 native=read('reference/validation/source-world-native.json');check(native['source_files']+native['build']);r=native['run'];assert native['failures']==[] and native['status']=='passed_scoped_native_source_contract'
 assert r['source_actor_fixture_cases']=='53' and r['source_actor_fixture_failure']=='0' and r['frames']=='1200' and r['restored_os']=='1'
 assert r['contact_kernel_cases']==r['sprite_copy_cases']==r['vic_repeat_cases']=='0' and native['contact_reference_separate'] and int(r['chip_largest_loaded'])>=49152
 assert int(r['max_held_image_streak'])<=3 and r['presentation_hold_fields']=='3'
 for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors']:assert r[k]=='0',k
 proofs.append('reference/validation/source-world-native.json')
 folder='reference/analysis/optimization-2026-10-27/compact-call-r01';math=read(folder+'/identity.json');check(math['source_files'])
 for e in math['build']:assert item(folder+'/'+Path(e['path']).name)['sha256']==e['sha256']
 assert math['run']['contact_kernel_cases']=='710' and math['run']['sprite_copy_cases']=='256' and math['run']['source_world_steps']=='360'
 for k in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors']:assert math['run'][k]=='0'
 normal=(ROOT/'amiga/main.c').read_text(encoding='utf-8-sig');allocation='if(BL_AUTOTEST){capture=AllocMem(BL_CAPTURE_BYTES,MEMF_PUBLIC|MEMF_CLEAR);tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}'
 expected=normal.replace(allocation,'if(BL_AUTOTEST){tone=AllocMem(32,MEMF_CHIP|MEMF_CLEAR);}').replace('(BL_AUTOTEST&&(!capture||!tone))','(BL_AUTOTEST&&!tone)')
 assert expected==(ROOT/folder/'compiled-main.c').read_text(encoding='utf-8-sig')
 assert read(folder+'/compile-overrides.json')['production_core_compiled']
 proofs.extend([folder+'/'+n for n in ['identity.json','native.txt','compiled-main.c','compiled-build.ps1','compile-overrides.json']])
 pairs=[]
 for before,after in [('sprite-publish-direct-before-repeat','flat-control-compact-tour'),('flat-control-compact-before-repeat','flat-control-compact-tour-repeat')]:
  runs=[]
  for label in [before,after]:
   path='reference/analysis/optimization-2026-10-27/'+label;data=read(path+'/identity.json');check(data['source_files'],historical=True)
   assert len(data['rooms'])==20 and data['status']=='passed_scoped_20_room_timing_route' and all(x['steps']==120 and x['chip_largest']>=49152 for x in data['rooms'])
   assert data['run']['bad_presents']=='0' and data['run']['contact_kernel_cases']=='710' and data['run']['sprite_copy_cases']=='256'
   for k in ['source_tour_error','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','vic_compare_errors']:assert data['run'][k]=='0'
   for e in data['build']:assert item(path+'/'+Path(e['path']).name)['sha256']==e['sha256']
   runs.append(data);proofs.extend([path+'/identity.json',path+'/compiled-main.c'])
  b,a=runs;assert sum(x['fields'] for x in a['rooms'])<sum(x['fields'] for x in b['rooms']) and sum(x['missed'] for x in a['rooms'])<=sum(x['missed'] for x in b['rooms'])
  assert min(x['slow_largest'] for x in a['rooms'])>min(x['slow_largest'] for x in b['rooms'])
  pairs.append(dict(before_fields=sum(x['fields'] for x in b['rooms']),after_fields=sum(x['fields'] for x in a['rooms']),before_missed=sum(x['missed'] for x in b['rooms']),after_missed=sum(x['missed'] for x in a['rooms']),slow_gain=min(x['slow_largest'] for x in a['rooms'])-min(x['slow_largest'] for x in b['rooms'])))
 # Fresh normal-image and primitive linkage proof is mandatory.
 links=read(BASE+'/delivery-kernels.json');assert links['status']=='passed_current_compact_primitive_linkage';check(links['artifacts']);proofs.append(BASE+'/delivery-kernels.json')
 normal_elf=item('amiga/out/bruce_amiga.elf')['sha256']
 for label in ['compact-clean-native','compact-clean-native-death']:
  p='reference/analysis/render-coherence-2026-10-29/'+label+'/report.json';r=read(p);assert r['elf']['sha256']==normal_elf and r['snapshots_paused'] and len(r['samples'])>=12
  for k in ['mixed_phase_samples','max_pixel_mismatch','max_static_pixel_mismatch','max_flicker_illegal_pixels']:assert r[k]==0
  assert not r['flicker_stuck_codes'];proofs.append(p)
  proofs += [q.relative_to(ROOT).as_posix() for q in sorted((ROOT/Path(p).parent).glob('*')) if q.suffix in ['.bin','.bpl']]
  if label.endswith('-death'):assert r['room_roundtrip'] and r['controlled_death']['loader_epoch_after']!=r['controlled_death']['loader_epoch_before']
 menu='reference/analysis/menu-publication-2026-10-29/compact-menu/report.json';r=read(menu);assert r['elf']['sha256']==normal_elf and r['status']=='passed_scoped_native_menu_publication' and r['source_ram_preserved_during_choices'] and r['changed_partial_hidden_samples']>0 and len(r['transitions'])>=10 and len(r['starts'])==2 and {v['menu_front'] for v in r['starts']}=={0,1} and all(v['complete_front'] for v in r['samples']);proofs.append(menu)
 proofs += [q.relative_to(ROOT).as_posix() for q in sorted((ROOT/Path(menu).parent).glob('*')) if q.suffix in ['.bin','.bpl']]
 clock=read('reference/analysis/actor-chain-2026-10-26/normal-clock.json');check([clock['binary']]);assert len(clock['pairs'])==3 and all(x['fault']==0 for x in clock['samples']) and all(x['source_fields']>0 and x['clock_min']-2<=x['source_fields']<=x['clock_max']+2 for x in clock['pairs']);proofs.append('reference/analysis/actor-chain-2026-10-26/normal-clock.json')
 boot=read(BASE+'/normal-boot.json');assert boot['cli_passed'] and boot['adf_passed'] and boot['normal_exe_sha256']==item('amiga/out/bruce_amiga.exe')['sha256'];check(boot['artifacts']);proofs.append(BASE+'/normal-boot.json')
 assert item('.tmp/amiga-boot/c/start')['sha256']==item('amiga/out/bruce_amiga.exe')['sha256']
 outputs=['amiga/out/bruce_amiga.exe','amiga/out/bruce_amiga.elf','amiga/out/bruce_amiga.adf','.tmp/amiga-boot/c/start']
 return dict(date='2026-10-30',status='scoped_complete_compact_backend_acceptance_open',source_sha256=SHA,source_controls=3034,integrated_scenarios=5,source_instructions=7055873,native_controls=53,native_replay_loops=1200,largest_chip_block=int(native['run']['chip_largest_loaded']),realtime_gate_passed=False,edition_verified=False,natural_playthrough=False,raster_exact=False,full_original_parity=False,converted_jsrs=444,pairs=pairs,normal_build=[item(p) for p in outputs],artifacts=[item(p) for p in sorted(set(proofs))],open_gates=['Verified untouched 1984 edition','Full PAL real-time cadence and natural IRQ/input phase','Whole native stack high-water','Complete natural playthrough and physical A500'])

def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();r=verify();path='reference/validation/compact-actor-delivery.json'
 if a.record:(ROOT/path).write_text(json.dumps(r,indent=2)+'\n')
 else:assert read(path)==r
 print('PASS compact actor backend delivery; full original-parity and real-time gates remain open')
if __name__=='__main__':main()
