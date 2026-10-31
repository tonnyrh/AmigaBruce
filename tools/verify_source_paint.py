"""Regression for changed source cells that were painted earlier in a batch."""
import ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=ctypes.CDLL(str(ROOT/'.tmp/source-paint-test/paint.dll'));d.bl_paint_requeue_contract.restype=ctypes.c_long
 result=d.bl_paint_requeue_contract();assert result==0,('painter regression line',result)
 d.bl_paint_frame_contract.restype=ctypes.c_long
 result=d.bl_paint_frame_contract();assert result==0,('frame coherence regression line',result)
 files=['amiga/main.c','core/c64_rooms.c','core/c64_rooms.h','tests/source_paint_bridge.c','tools/verify_source_paint.py','test-source-paint.ps1']
 report=dict(status='passed_source_paint_requeue_controls',cases=['repaint_consumed_cell_after_source_mutation','full880_queue_repeated_mutation_coalescing','60_full_room_loads_exact_pixels','96_room12_source_steps_single_phase_overlay','source_ram_unchanged_by_overlay','changed_cell_invalidates_overlay_rectangle'],natural_playthrough=False,
  source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
 (ROOT/'reference/validation/source-paint-host.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS source painter requeue: deferred updates retained; full880-cell queue bounded; exact current source pixels')
if __name__=='__main__':main()
