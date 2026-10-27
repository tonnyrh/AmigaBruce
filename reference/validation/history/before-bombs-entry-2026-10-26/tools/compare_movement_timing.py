"""Compare durations between equal movement events using emulated hardware time."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def compare():
 clock_path=ROOT/'reference/timing-clocks.json';clocks=read(clock_path)
 runtime_path=ROOT/'reference/validation/a500-soak.json';runtime=read(runtime_path)
 for item in runtime['source_files']:assert sha(ROOT/item['path'])==item['sha256'],'Stale A500 timing measurement'
 sources=[]
 def trace(capture,name):
  folder=ROOT/'reference/traces'/capture;summary=read(folder/'summary.json')
  expected=next(s for s in summary['scenarios'] if s['name']==name)['sha256'];p=folder/f'{name}.csv'
  assert sha(p)==expected
  sources.extend([{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)},{'path':str((folder/'summary.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(folder/'summary.json')}])
  with p.open(newline='') as f:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
 walk=trace('MACHINE-0001','right');jump=trace('MACHINE-0001','standing-jump');fall=trace('MACHINE-0007','mid-net-left-fall')
 wa=next(r for r in walk if 2*r['target_x_halfpixels']-24==32)
 wb=next(r for r in walk if r['tick']>wa['tick'] and 2*r['target_x_halfpixels']-24==98)
 ja=next(r for r in jump if r['next_state']==5)
 lift=next(r for r in jump if r['tick']>ja['tick'] and r['target_y']<196)
 jb=next(r for r in jump if r['tick']>lift['tick'] and r['target_y']==196)
 fa=next(r for r in fall if r['next_state']==14 and r['target_y']==138)
 fb=next(r for r in fall if r['tick']>fa['tick'] and r['target_y']==196)
 specs=[('walk','Gange x32 til x98',wa,wb),('jump','Stående hopp: satsvalg til første retur til y196',ja,jb),('fall','Fritt fall y138 til y196',fa,fb)]
 report={'status':'movement_duration_comparison','primary_edition_verified':False,'full_movement_parity':False,'clock_config_sha256':sha(clock_path),'runtime_sha256':sha(runtime_path),'reference_sources':sources,'source_files':[{'path':n,'sha256':sha(ROOT/n)} for n in ('tools/compare_movement_timing.py','amiga/main.c','test-amiga.ps1')],'method':'C64 CPU-history cycles between logical target events; A500 CIA TOD ticks read at equal events; no debugger/host wall time or fitted time shift','limitations':['A500 CIA time resolution is one video field','This is logical movement timing, not measured controller-to-screen latency','Known collision and moving-jump landing discrepancies remain open'],'actions':[]}
 passed=True
 for name,label,a,b in specs:
  cycles=b['cycles']-a['cycles'];c64_ms=cycles*1000/clocks['c64_pal_cpu_hz']
  runs=[]
  for run in runtime['runs']:
   assert run['timing_seen']=='63' and run['timing_mode_changes']=='0'
   lines=int(run['timing_pal_lines']);assert lines in (312,313)
   field_ms=1000*lines*clocks['amiga_cck_per_line']/clocks['amiga_pal_cck_hz']
   fields=int(run[f'timing_{name}_fields']);amiga_ms=fields*field_ms
   delta=amiga_ms-c64_ms;budget=clocks['allowed_quantization_fields']*field_ms
   okay=abs(delta)<=budget;passed&=okay
   runs.append({'hardware_fields':fields,'pal_lines_per_field':lines,'duration_ms_from_fields':amiga_ms,'delta_ms_from_c64':delta,'timer_resolution_ms':field_ms,'within_one_field_resolution':okay})
  report['actions'].append({'id':name,'description':label,'c64_start_tick':a['tick'],'c64_end_tick':b['tick'],'c64_cpu_cycles':cycles,'c64_duration_ms':c64_ms,'amiga_runs':runs})
  print(f'{name}: C64 {c64_ms:.1f} ms; A500 '+', '.join(f"{r['duration_ms_from_fields']:.1f} ms ({r['hardware_fields']} fields)" for r in runs))
 report['all_within_timer_resolution']=bool(passed)
 c64_step_ms=3*clocks['c64_cycles_per_line']*clocks['c64_lines_per_field']*1000/clocks['c64_pal_cpu_hz']
 rate_models=[]
 for lines in sorted({int(r['timing_pal_lines']) for r in runtime['runs']}):
  amiga_step_ms=3*lines*clocks['amiga_cck_per_line']*1000/clocks['amiga_pal_cck_hz']
  ratio=amiga_step_ms/c64_step_ms-1
  rate_models.append({'amiga_pal_lines':lines,'c64_logic_step_ms':c64_step_ms,'amiga_logic_step_ms':amiga_step_ms,'relative_duration_difference_percent':ratio*100,'estimated_duration_difference_ms_per_reference_minute':ratio*60000})
 report['clock_rate_models']=rate_models
 report['exact_clock_rate_parity']=False
 out=ROOT/'reference/validation/movement-timing.json';out.write_text(json.dumps(report,indent=2)+'\n')
 lines=['# Varighet av bevegelse — 2026-10-20','', 'Samme logiske start- og sluttpunkter sammenlignes. C64-tiden kommer fra CPU-klokken; A500-tiden fra CIA TOD målt ved hendelsene. Debuggerpauser teller ikke.','', '| Handling | C64 | A500, kjøring 1 | A500, kjøring 2 |','| --- | ---: | ---: | ---: |']
 for a in report['actions']:lines.append('| '+a['description']+' | '+f"{a['c64_duration_ms']/1000:.3f} s"+' | '+' | '.join(f"{r['duration_ms_from_fields']/1000:.3f} s" for r in a['amiga_runs'])+' |')
 lines+=['','A500-timeren har omtrent 20 ms oppløsning. De viste tidene er omregnet med maskinens nominelle klokke og målt kort/lang PAL-feltmodus. Små forskjeller under ett felt kan ikke avgjøres som nøyaktige millisekundavvik med denne målingen.','', 'Dette godkjenner de tre handlingsvarighetene innen timeroppløsningen. Kollisjonsgeometri, løpshoppets kjente landing og fysisk input-til-skjerm-latens er fortsatt egne åpne tester. Spillfarten er ikke endret.','', 'Hele tallgrunnlaget og filidentiteter: [movement-timing.json](../reference/validation/movement-timing.json).','', 'Klokkedefinisjoner: [VICE C64](https://github.com/VICE-Team/svn-mirror/blob/main/vice/src/c64/c64.h), [WinUAE PAL-konstanter](https://github.com/tonioni/WinUAE/blob/master/include/custom.h), [WinUAE feltberegning](https://github.com/tonioni/WinUAE/blob/master/custom.cpp).']
 lines+=['', '## Klokkeavvik over lengre tid', '']
 for model in rate_models:
  lines.append(f"Med {model['amiga_pal_lines']} linjer per A500-felt varer tre felt {model['amiga_logic_step_ms']:.3f} ms, mot {model['c64_logic_step_ms']:.3f} ms på C64. Modellen gir {model['relative_duration_difference_percent']:.3f}% lengre A500-varighet, omtrent {model['estimated_duration_difference_ms_per_reference_minute']:.0f} ms per C64-minutt dersom alt fortsetter med tre felt per steg. Dette er en klokkeutledning, ikke en målt gjennomspilling. Eksakt langtidsparitet er fortsatt åpen.")
 (ROOT/'docs/MOVEMENT_TIMING.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 if not passed:raise SystemExit('Movement durations differ beyond timer resolution')
if __name__=='__main__':compare()
