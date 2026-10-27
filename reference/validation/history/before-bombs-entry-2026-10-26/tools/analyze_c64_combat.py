"""Summarize actual C64 enemy contacts separately from provisional Amiga lab rules."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze():
 p=ROOT/'reference/traces/COMBAT-0001.json';capture=json.loads(p.read_text());assert capture['repetitions']==2 and not capture['primary_edition_verified']
 for source in capture['sources']:assert sha(ROOT/source['path'])==source['sha256']
 contacts=[];health={i:set() for i in range(3)}
 for name,rows in capture['scenarios'].items():
  for actor in range(3):
   active=[r['actors'][actor] for r in rows if r['actors'][actor]['active']&1]
   if active:health[actor].add(active[0]['health'])
  for before,row in zip(rows,rows[1:]):
   for i,a in enumerate(row['actors']):
    if a['hit']&30:
     damage=(before['actors'][i]['health']-a['health'])&255
     kind=a['hit']&30
     if kind==2:assert damage==2
     if kind==8:assert damage==7
     contacts.append({'scenario':name,'tick':row['tick'],'victim':i,'flags':a['hit'],'damage':damage})
 assert health=={0:{36},1:{20},2:{7}}
 assert len(contacts)>=10 and any(c['flags']&8 for c in contacts)
 report={'capture_id':'COMBAT-0001','primary_edition_verified':False,'full_combat_parity':False,'trace_sha256':sha(p),'repetitions':2,'observations':sum(len(r) for r in capture['scenarios'].values()),'first_active_health':{'bruce':36,'yamo':20,'ninja':7},'contacts':contacts,'fall_hits_observed':sum(bool(c['flags']&16) for c in contacts),'passed':True,'limitations':['No natural falling-contact hit observed in these four routes','Jumping alone did not damage enemies in held-up route','Amiga passive target keeps provisional damage and geometry','Ninja/Yamo AI exists as an unverified M3 candidate; see candidate-combat.json'],'source_files':[{'path':'tools/analyze_c64_combat.py','sha256':sha(ROOT/'tools/analyze_c64_combat.py')}]}
 (ROOT/'reference/validation/candidate-enemy-contacts.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS:',report['observations'],'native combat observations;',len(contacts),'health-changing contacts; health36/20/7')
if __name__=='__main__':analyze()
