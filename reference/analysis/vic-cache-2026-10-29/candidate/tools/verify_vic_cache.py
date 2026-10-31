"""Compare cache representation with frozen pre-optimization C; no gameplay model."""
import argparse,ctypes,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/vic-cache-2026-10-29/before/core/c64_rooms.c'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');args=p.parse_args()
 if args.prepare:
  source=(ROOT/BASE).read_text(encoding='utf-8');chunks=[]
  for name in ['source_vic_row','source_vic_cache']:
   start=source.index('static void '+name+'(');at=source.index('{',start)+1;depth=1
   while depth:depth+=(source[at]=='{')-(source[at]=='}');at+=1
   chunks.append(source[start:at])
  ref='\n'.join(chunks).replace('source_vic_row','reference_vic_row').replace('source_vic_cache','reference_vic_cache')
  out=ROOT/'.tmp/vic-cache-test';out.mkdir(exist_ok=True,parents=True);(out/'baseline_cache.h').write_text(ref+'\n');return
 lib=ctypes.CDLL(str(ROOT/'.tmp/vic-cache-test/cache.dll'));lib.bl_vic_cache_contract.restype=ctypes.c_long;lib.bl_vic_cache_cases.restype=ctypes.c_ulong
 result=lib.bl_vic_cache_contract();assert result==0,result
 count=lib.bl_vic_cache_cases();assert count==25600,count
 report=dict(status='passed_cache_representation_equivalence',cases=count,full_ram_preservation_cases=1024,natural_playthrough=False,original_raster_verified=False,scope='All256 bytes in each of3 positions and4 opacity/width modes for8 sprites; dense/wrapped pointers; all rows/raw bytes/pad/metadata/other sprites unchanged against frozen C',source_files=[item(p) for p in ['core/c64_rooms.c','tests/vic_cache_bridge.c','tools/verify_vic_cache.py','test-vic-cache.ps1',BASE]])
 (ROOT/'reference/validation/vic-cache-host.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cache equivalence:',count,'cases;1024 full RAM preservation checks')
if __name__=='__main__':main()
