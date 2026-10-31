"""Bind original-byte, native-call-control and compiler experiment evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/flat-control-compact-2026-10-30'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def check(items):
 for e in items:assert item(ROOT/e['path'])==e,e['path']
def main():
 p=BASE/'probe.json';probe=read(p);check(probe['artifacts']);proofs=[item(p)]
 raw=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
 assert len(probe['converted_calls'])==444 and probe['native_capacity']==16 and probe['scratch_locals_killed_at_every_source_instruction']
 original=(ROOT/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
 for block in re.split(r'(?m)^L[0-9a-f]+:;[^\n]*\n',original)[1:]:
  for name in ['address','q','old']:
   match=re.search(r'\b'+name+r'\b',block)
   assert not match or re.match(r'\s*=',block[match.end():]),(name,block[:100])
 for name in ['address','q','old']:
  for rhs in re.findall(r'\b'+name+r'\s*=([^;]+)',original):assert not re.search(r'\b'+name+r'\b',rhs),(name,rhs)

 for row in probe['converted_calls']:
  assert raw[row['ret']-3:row['ret']]==bytes([32,row['target']&255,row['target']>>8]),row
 summaries=[];controls=BASE/'controls';controls.mkdir(exist_ok=True)
 for variant,folder,work in [('default',BASE,ROOT/'.tmp/flat-control-compact'),('capacity1',BASE/'capacity1',ROOT/'.tmp/flat-control-compact-cap1')]:
  host=read(folder/'report.json');world=read(folder/'integrated-controls.json');check(host['source_files']);check(world['source_files'])
  assert host['checks']==3034 and not host['production_enabled'] and len(world['checks'])==5 and world['instructions']==7055873
  snapshots=controls/variant;snapshots.mkdir(exist_ok=True)
  for n in ['build.ps1','audit.py','world.py']:
   (snapshots/n).write_bytes((work/n).read_bytes());proofs.append(item(snapshots/n))
  proofs.extend([item(folder/'report.json'),item(folder/'integrated-controls.json'),item(work/'actors.dll'),item(work/'compiled-sources.json')])
  summaries.append(dict(variant=variant,actor_cases=3034,integrated_modes=5,original_instructions=world['instructions']))
 irq=read(BASE/'irq-context-candidate.json');check(irq['artifacts']);assert irq['cases']==3352 and irq['instructions']==479308 and irq['all_ram_and_registers'] and irq['returned_pc_verified'] and irq['sid_gate_edges_verified'];proofs.append(item(BASE/'irq-context-candidate.json'))
 native=None
 folder=ROOT/'reference/analysis/optimization-2026-10-27/flat-control-compact-r01'
 if (folder/'compile-overrides.json').exists():
  native=read(folder/'identity.json');override=read(folder/'compile-overrides.json');check(override['actual_inputs']);run=native['run'];assert run['source_world_steps']=='360' and run['contact_kernel_cases']=='710' and run['sprite_copy_cases']=='256' and int(run['chip_largest_loaded'])>=49152
  for key in ['c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:assert run[key]=='0',key
  proofs.extend([item(folder/'identity.json'),item(folder/'compile-overrides.json')])
  native=dict(fields=int(run['source_clock_elapsed']),missed=int(run['source_clock_missed']),chip_largest=int(run['chip_largest_loaded']),source_steps=360)
 native_fixture=None
 if (BASE/'native-fixture.json').exists():
  fixture=read(BASE/'native-fixture.json');check(fixture['source_files']);check(fixture['build']);run=fixture['run']
  assert not fixture['production_core_compiled'] and fixture['failures']==[]
  assert run['source_actor_fixture_cases']=='53' and run['frames']=='1200' and run['restored_os']=='1'
  assert int(run['chip_largest_loaded'])>=49152
  for key in ['source_actor_fixture_failure','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','contact_kernel_errors','c64_render_mismatches','capture_fault','vic_compare_errors']:assert run[key]=='0',key
  proofs.extend([item(BASE/'native-fixture.json'),item(BASE/'native-fixture.txt')])
  native_fixture=dict(cases=53,loops=1200,chip_largest=int(run['chip_largest_loaded']),realtime_accepted=fixture['realtime_contract_passed'])
 native_tour=None
 tour=ROOT/'reference/analysis/optimization-2026-10-27/flat-control-compact-tour'
 if (tour/'identity.json').exists():
  result=read(tour/'identity.json');check(result['source_files']);run=result['run']
  assert len(result['rooms'])==20 and all(r['steps']==120 and r['chip_largest']>=49152 for r in result['rooms'])
  assert run['contact_kernel_cases']=='710' and run['sprite_copy_cases']=='256' and run['bad_presents']=='0'
  for key in ['source_tour_error','c64_room_fault','source_audio_faults','source_dma_faults','runtime_arithmetic_errors','vic_compare_errors','contact_kernel_errors']:assert run[key]=='0',key
  for e in result['build']:assert hashlib.sha256((tour/e['path']).read_bytes()).hexdigest()==e['sha256']
  before=ROOT/'reference/analysis/optimization-2026-10-27/sprite-publish-direct-before-repeat'
  assert (before/'compiled-main.c').read_bytes()==(tour/'compiled-main.c').read_bytes()
  native_tour=dict(rooms=20,steps=2400,totals={k:sum(r[k] for r in result['rooms']) for k in ['fields','lines','missed']},chip_min=min(r['chip_largest'] for r in result['rooms']),room12=result['rooms'][11])
  proofs.extend([item(tour/'identity.json'),item(tour/'compiled-main.c'),item(before/'identity.json')])
 wide=read(ROOT/'reference/analysis/flat-control-2026-10-30/probe.json');assert wide['builds'][1]['sections']['.text']-wide['builds'][0]['sections']['.text']==21424
 proofs.append(item(ROOT/'reference/analysis/flat-control-2026-10-30/probe.json'))
 report=dict(status='verified_private_native_continuation_experiment',production_changed=False,promoted=False,realtime_accepted=False,converted_source_jsrs=444,source_hash=hashlib.sha256(raw).hexdigest(),controls=summaries,irq_cases=3352,irq_instructions=479308,compiler_builds=probe['builds'],first_wide_shape='rejected_before_runtime_due_code_growth_21424_bytes',native_r01=native,native_fixture=native_fixture,native_tour=native_tour,artifacts=proofs,limits=['Native array handles C continuations only; original guest stack bytes retained','One-slot test deliberately exercises recursive fallback; no original source rule changed','Unlinked footprint and local stack frames do not prove loaded memory or full native stack margin','Host equality is not natural beam/input timing; full target tests and repeated performance still required'])
 report['artifacts'] += [item(Path(__file__)),item(ROOT/'docs/NATIVE_CONTINUATION_EXPERIMENT.md')]
 (BASE/'binding.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS private native continuations: 444 original JSRs, 2x3034 actor cases, 2x5 world modes,3352 IRQ cases; promoted=False')
if __name__=='__main__':main()
