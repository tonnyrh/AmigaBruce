"""Exact attack comparison using recorded CPU input reads, with seam cross-checks."""
import csv,hashlib,json,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def compare(executable,capture='PHASE-0001'):
 path=ROOT/f'reference/traces/{capture}.json';phase=json.loads(path.read_text());baseline_id=phase['baseline_capture']
 for source in phase['sources']:assert digest(ROOT/source['path'])==source['sha256']
 summary=json.loads((ROOT/f'reference/traces/{baseline_id}/summary.json').read_text())
 assert phase['snapshot_sha256']==summary['snapshot_sha256']
 report={'capture_id':capture,'baseline_capture':baseline_id,'primary_edition_verified':False,'full_combat_parity':False,
  'alignment':'Same numbered game interval; direction A after $1DD0 LDA, fire A after actual $9B read; no fitted shifts',
  'phase_sha256':digest(path),'baseline_summary_sha256':digest(ROOT/f'reference/traces/{baseline_id}/summary.json'),
  'source_files':[{'path':n,'sha256':digest(ROOT/n)} for n in ('core/game.c', 'core/room_geometry.h','core/game.h','tests/core_trace.c','tools/compare_attack_phase.py','test-parity.ps1')], 'scenarios':[]}
 failed=False;all_exact=True;all_attacks=True
 for name,events in phase['scenarios'].items():
  with (ROOT/f'reference/traces/{baseline_id}/{name}.csv').open(newline='') as f:baseline=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
  seams=[e for e in events if e['point']=='seam'];assert len(seams)==len(baseline)
  for seam,row in zip(seams,baseline):
   assert seam['tick']==row['tick']
   assert [seam[k] for k in ('x','y','next_state','state','direction','fire','animation_timer')]==[row[k] for k in ('target_x_halfpixels','target_y','next_state','state','sampled_direction','sampled_fire','animation_timer')]
   assert seam['cycles']-seams[0]['cycles']==row['cycles']
  inputs=[]
  for tick in range(1,len(seams)):
   step=[e for e in events if e['tick']==tick and e['point']!='seam']
   move=[e for e in step if e['point']=='movement'];assert len(move)==1
   direction=move[0]['direction'];fire=move[0]['fire']
   read=[e for e in step if e['point']=='direction_read']
   if read:assert len(read)==1;direction=read[0]['a_register']
   reads=[e['a_register'] for e in step if e['point'] in ('right_fire_read','left_fire_read','standing_fire_read')]
   if reads:assert len(set(reads))==1,'Multiple fire values in one interval need finer modelling'
   late_fire=reads[-1] if reads else fire
   assert 0<=direction<=15 and fire in (0,1) and late_fire in (0,1)
   inputs.append(f'{direction},{fire},{late_fire}')
  run=subprocess.run([str(executable.resolve())],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True)
  actual=[list(map(int,s.split(','))) for s in run.stdout.splitlines()];assert len(actual)==len(seams)
  differences=[]
  for e,a in zip(seams,actual):
   attack=1 if e['next_state']==17 else 2 if e['next_state'] in (12,13) else 0
   expected=[2*e['x']-24,e['y'],attack];observed=[a[0],a[1],a[4]]
   if expected!=observed:differences.append({'tick':e['tick'],'expected':expected,'actual':observed})
  # Same known moving-jump landing window as MACHINE-0001 (26 minus ten walk steps).
  position_gate=16 if name=='diagonal-fire-from-idle' else len(seams)-1
  attack_pass=not any(d['expected'][2]!=d['actual'][2] for d in differences)
  gate_pass=attack_pass and not any(d['tick']<=position_gate for d in differences)
  report['scenarios'].append({'name':name,'samples':len(seams),'differences':differences,'passed':not differences,'all_attack_targets_passed':attack_pass,'position_gate_through_tick':position_gate,'gate_passed':gate_pass})
  failed|=not gate_pass;all_exact&=not differences;all_attacks&=attack_pass;print(name, len(seams)-len(differences),'/',len(seams),'exact positions and attack targets')
 report['regression_gates_passed']=not failed
 report['all_samples_passed']=bool(all_exact)
 report['all_attack_targets_passed']=all_attacks
 (ROOT/('reference/validation/candidate-attacks-phased'+('' if capture=='PHASE-0001' else '-edges')+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 if failed:raise SystemExit('Phased attack comparison failed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('executable',type=Path);p.add_argument('--capture-id',default='PHASE-0001');args=p.parse_args();compare(args.executable,args.capture_id)
