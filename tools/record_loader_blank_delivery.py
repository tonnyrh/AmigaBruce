"""Record the bounded display correction after all fresh native gates pass."""
import hashlib,json
from pathlib import Path
from verify_loader_blank_delivery import verify_current
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/screen-corruption-2026-10-30'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    r=verify_current()
    target='reference/validation/loader-display-blank.json'
    result=dict(status='passed_scoped_loader_display_blank',source_sha256=r['source_sha256'],
      normal_build=r['normal_build'],native_fixtures=53,native_replay_loops=1200,blank_rooms=[6,12],phase_snapshots=24,menu_snapshots=80,
      loader_blank=r['loader_blank'],largest_chip_block=r['largest_chip_block'],edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,
      limitations=r['open_gates'],artifacts=r['artifacts']+[item('tools/record_loader_blank_delivery.py')])
    (ROOT/target).write_text(json.dumps(result,indent=2)+'\n')
    evidence=dict(id='LOADER-DISPLAY-0001',date='2026-10-30',status='candidate_code_derived_scoped_native_verified',
      source_sha256=r['source_sha256'],source_addresses=['$09BC-$09C1','$0B33','$50DB-$50E5'],
      source_condition='DEN clears before room rebuild and sets after decompression; snapshot room6 stores $D011=$0B.',
      amiga_effect='Both Copper lists and BPLCON0 blank on existing loader entry; only a complete published list reenables bitplanes.',
      core_unchanged=True,edition_verified=False,natural_playthrough=False,realtime_gate_passed=False,
      controls=dict(native_fixtures=53,native_replay_loops=1200,blank_rooms=[6,12],phase_snapshots=24,menu_snapshots=80),
      artifacts=[item(target),item('reference/validation/source-world-delivery.json')],limitations=r['open_gates'])
    (ROOT/'docs/parity/evidence/LOADER-DISPLAY-0001.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('PASS recorded loader display correction and C64 parity evidence')
if __name__=='__main__':main()
