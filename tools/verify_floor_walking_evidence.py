"""Check this bounded walking diagnosis without claiming natural/raster parity."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/floor-walk-2026-10-30'
TIMING='reference/analysis/normal-runtime-2026-10-30/floor-walk-room12-current/report.json'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    proof=read(BASE+'/report.json');assert proof['status']=='passed_scoped_original_byte_floor_walk_controls'
    assert (proof['cases'],proof['main_steps'],proof['source_instructions'])==(48,2271,14565502)
    assert proof['all_ram_registers_and_boundaries'] and not proof['production_changed']
    paths=[BASE+'/report.json',BASE+'/source-disassembly.txt',BASE+'/source-wait-disassembly.txt',TIMING,'docs/FLOOR_WALK_AUDIT.md',
      'tools/verify_floor_walking_evidence.py','tools/audit_normal_runtime.py','tools/rip_c64_room_graphics.py','tools/c64_room_model.py','tools/verify_c64_room_runtime.py']
    for e in proof['artifacts']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==proof['source_sha256']
    assert source[0x1bc2:0x1bc6]==bytes.fromhex('a9038548')
    old=read('reference/validation/loader-display-blank.json')
    for e in old['normal_build']:assert item(e['path'])['sha256']==e['sha256'];paths.append(e['path'])
    timing=read(TIMING);assert timing['normal_exe_sha256']==item('amiga/out/bruce_amiga.exe')['sha256']
    assert timing['normal_elf_sha256']==item('amiga/out/bruce_amiga.elf')['sha256']
    assert timing['room']==12 and timing['measured_fields']>=6000 and timing['source_steps']>0 and timing['requested_unobserved_wall_seconds']==140
    assert timing['before']['room']==timing['after']['room']==12 and timing['before']['actor_loading_epoch']==timing['after']['actor_loading_epoch']
    for endpoint in [timing['before'],timing['after']]:assert endpoint['source_fault']==endpoint['source_dma_faults']==0 and not any(endpoint['menu_or_delay'])
    assert timing['fields_per_step']==timing['measured_fields']/timing['source_steps'] and not timing['full_realtime_accepted']
    example=next(r for r in proof['rows'] if r['room']==12 and r['direction']==-1)
    assert [(r['after'][0]*2-24,r['after'][1],r['after'][2]) for r in example['steps'][:5]]==[(100,76,3),(96,76,3),(96,77,14),(96,77,0),(92,77,3)]
    rate=timing['fields_per_step'];result=dict(status='scoped_walking_logic_matches_timing_target_not_met',source_sha256=proof['source_sha256'],
      cases=48,main_entries=2271,source_instructions=14565502,production_changed=False,exact_user_route_verified=False,edition_verified=False,natural_playthrough=False,
      original_irq_phase_verified=False,physical_a500=False,realtime_accepted=False,fields_per_step=rate,target_fields_per_step=3,mean_step_duration_increase_percent=(rate/3-1)*100,
      conclusion='No extra walking/main-operator difference in controlled cases. Original code contains short fall/landing pauses. Current stationary R12 cadence can lengthen pauses in time; this does not settle the unspecified user route.',
      enemy_activations_after_entry=sum(bool(s['active_after'][1]&1 or s['active_after'][2]&1) for r in proof['rows'] for s in r['steps']),
      artifacts=[item(p) for p in sorted(set(paths))])
    (ROOT/BASE/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS walking diagnosis;',proof['main_steps'],'controlled source comparisons;',round((rate/3-1)*100,2),'percent longer mean step; exact route remains open')
if __name__=='__main__':main()
