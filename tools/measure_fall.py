"""Gate measured free-fall rate, without claiming full route/collision parity."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def measure():
 capture='MACHINE-0007';folder=ROOT/'reference/traces'/capture
 summary=json.loads((folder/'summary.json').read_text());record=next(s for s in summary['scenarios'] if s['name']=='mid-net-left-fall')
 p=folder/'mid-net-left-fall.csv';assert sha(p)==record['sha256']
 with p.open(newline='') as f:rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(f)]
 samples=[{'tick':b['tick'],'dy':b['target_y']-a['target_y']} for a,b in zip(rows,rows[1:]) if a['next_state']==14 and b['next_state']==14 and b['target_y']>a['target_y']]
 assert len(samples)>=20 and all(r['dy']==2 for r in samples)
 report={'capture_id':capture,'status':'candidate_free_fall_rate_only','full_route_parity':False,'primary_edition_verified':False,'trace_sha256':sha(p),'summary_sha256':sha(folder/'summary.json'),'pixels_per_logic_step':2,'pal_fields_per_logic_step':3,'pixels_per_second_at_50hz':100/3,'positive_free_fall_intervals':samples,'passed':True,'limitations':['Net exit horizontal geometry differs from prototype','Upper-ledge route does not fall in candidate; it stops on collision geometry at y102','No death/landing mask certification'],'source_files':[{'path':n,'sha256':sha(ROOT/n)} for n in ('tools/measure_fall.py','core/game.c', 'core/room_geometry.h','tests/core_test.c','test-parity.ps1')]}
 (ROOT/'reference/validation/candidate-fall-rate.json').write_text(json.dumps(report,indent=2)+'\n')
 print(f'PASS: {len(samples)} consecutive positive free-fall intervals at two pixels / three PAL fields')
if __name__=='__main__':measure()
