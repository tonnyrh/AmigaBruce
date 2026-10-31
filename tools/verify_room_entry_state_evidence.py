"""Bind the room-entry diagnosis to actual source bytes and unchanged build."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='reference/analysis/room-entry-state-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 r=read(BASE+'/report.json');assert r['status']=='passed_source_room_entry_state_reset'
 assert (r['cases'],r['main_entries'],r['source_instructions'])==(36,252,2268645)
 assert not r['production_changed'] and not r['edition_verified'] and not r['natural_playthrough']
 source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==r['source_sha256']
 assert source[0xa6f:0xa83]==bytes.fromhex('a90485cea9008dde4f8ddf4f8de04f85bf8d0601')
 paths=[BASE+'/report.json',BASE+'/source-disassembly.txt','docs/ROOM_ENTRY_STATE.md','tools/verify_room_entry_state_evidence.py']
 for e in r['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 for e in read('reference/validation/loader-display-blank.json')['normal_build']:
  assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
 seen=set()
 for case in r['rows']:
  key=(case['exit'],case['kind'],case['input_after']);assert key not in seen;seen.add(key)
  entry=next(q['actor'] for q in case['checkpoints'] if q['pc']=='0x1bc2')
  assert entry['state']==0 and entry['counter']==4 and entry['wait']==0 and entry['facing']==case['before']['facing']
  assert [(q['actor']['state'],q['actor']['counter']) for q in case['steps'][:4]]==[(0,3),(0,2),(0,1),(0,0)]
  mode=case['steps'][4]['actor']['state'];right=case['before']['facing']
  assert mode==(0 if case['input_after']=='released' else (7 if right else 6) if case['input_after']=='diagonal-up' else (4 if right else 3))
 summary=dict(status='verified_normal_room_entry_resets_action',source_sha256=r['source_sha256'],cases=36,main_entries=252,source_instructions=2268645,
  production_changed=False,normal_action_reset=True,entry_state=0,entry_counter=4,facing_preserved_in_cases=True,
  edition_verified=False,natural_playthrough=False,raster_phase_verified=False,new_native_hardware_route_test=False,
  artifacts=[item(p) for p in sorted(set(paths))])
 (ROOT/BASE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('PASS 36 source room-entry cases; action resets; production unchanged')
if __name__=='__main__':main()
