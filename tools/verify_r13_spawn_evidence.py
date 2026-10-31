"""Bind R13 findings without treating a synthetic reader as natural play."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='reference/analysis/spawn-r13-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 r=read(BASE+'/report.json');assert r['status']=='passed_scoped_r13_spawn_service_and_field_controls'
 assert (r['cases'],r['service_ticks'],r['field_checks'],r['comparisons'],r['source_instructions'])==(12,1200,60,3697,267118)
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==r['source_sha256']
 assert [source[t+12] for t in [0x130b,0x131f,0x1347,0x135b]]==[4,4,32,32]
 assert r['table']==dict(initial_kage=4,initial_yamo=32,return_kage=4,return_yamo=32,standard_xy=[24,92],alternative_xy=[200,92])
 paths=[BASE+'/report.json',BASE+'/source-disassembly.txt','docs/R13_SPAWN_RATE.md','tools/verify_r13_spawn_evidence.py']
 for e in r['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 for e in read('reference/validation/loader-display-blank.json')['normal_build']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 for q in r['sequences']:
  assert len(q['steps'])==100
  expected=(2,16) if q['clock_high']==25 else (3,3) if q['round'] or q['clock_high']>=32 else (4,32)
  assert (q['kage_removal_counter'],q['yamo_removal_counter'])==expected
  first=[b for b in q['births'] if b['phase']=='first'];assert len(first)==2 and {b['actor'] for b in first}=={1,2}
  assert {b['actor']:b['step'] for b in first}==({2:4,1:32} if q['round']==0 else {1:3,2:3})
 assert all(q['timers']==[4,32] for q in r['field_trace']) and r['field_trace'][-1]['age']==[60,0]
 report=dict(status='verified_r13_short_source_spawn_counters_no_logic_difference_found',source_sha256=r['source_sha256'],
  cases=12,comparisons=3697,source_instructions=267118,field_checks=60,production_changed=False,
  exact_user_route_verified=False,natural_reader_distribution_verified=False,edition_verified=False,natural_playthrough=False,new_native_hardware_route_test=False,
  source_initial_and_base_return=dict(kage=4,yamo=32),spawn_countdown_unit='Main-loop service pass; not one PAL field',
  artifacts=[item(p) for p in sorted(set(paths))])
 (ROOT/BASE/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS R13 source spawn timers/gates; no production changes; actual user route remains open')
if __name__=='__main__':main()
