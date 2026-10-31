"""Exhaustive renderer-mask query compatibility, with a frozen C reference."""
import argparse,ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/view-mask-2026-10-29/baseline/core/c64_rooms.c'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');a=p.parse_args()
 if a.prepare:
  text=(ROOT/BASE).read_text(encoding='utf-8');start=text.index('unsigned short bl_c64_collected(');at=text.index('{',start);depth=1;at+=1
  while depth:
   depth+=(text[at]=='{')-(text[at]=='}');at+=1
  reference=text[start:at].replace('bl_c64_collected','bl_view_mask_reference',1)
  out=ROOT/'.tmp/view-mask-test';out.mkdir(parents=True,exist_ok=True);(out/'baseline_collected.h').write_text(reference+'\n');return
 d=ctypes.CDLL(str(ROOT/'.tmp/view-mask-test/view.dll'));d.bl_view_mask_contract.restype=ctypes.c_long;d.bl_view_mask_case_count.restype=ctypes.c_ulong;d.bl_view_bulk_case_count.restype=ctypes.c_ulong
 result=d.bl_view_mask_contract();assert not result,('query regression',result)
 count=d.bl_view_mask_case_count();assert count==20*14*8192+20*8
 bulk=d.bl_view_bulk_case_count();assert bulk==20*14*4+20*8
 report=dict(status='passed_exhaustive_view_query_compatibility',source_sha256=item('.reference/c64/work/untrained-memory.bin')['sha256'],edition_verified=False,natural_playthrough=False,method='All13-bit masks and record lengths, plus wrapped/aliased pointers; previous C query and independent expected masks; selected full64KiB unchanged checks. This query is presentation metadata, not original6502 execution.',cases=count,bulk_vectors=bulk,bulk_mask_checks=bulk*20,full_ram_compares=bulk,source_files=[item(f) for f in ['core/c64_rooms.c','core/c64_rooms.h','tests/view_mask_bridge.c','tools/verify_view_mask.py','test-view-mask.ps1',BASE]])
 (ROOT/'reference/validation/view-mask-host.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS view mask compatibility:',count,'queries, selected full-RAM preservation')
if __name__=='__main__':main()
