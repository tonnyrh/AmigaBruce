"""Keep the original generic color writer and active observer byte exact."""
import hashlib,json,struct
from pathlib import Path
from audit_final_color_images import object_kernel
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/color-observer-2026-10-30'
def main():
 before='reference/analysis/final-colors-2026-10-30/compiler-probes/before.o'
 kernels={name:object_kernel(before,section) for name,section in [('source_written','.text.source_written'),('animation_cell_changed_active','.text.animation_cell_changed.part.0')]}
 kernels['source_final_colors']=object_kernel('reference/analysis/color-observer-2026-10-30/compiler-core.o','.text.source_final_colors')
 paths=['amiga/out/bruce_amiga.elf','reference/analysis/optimization-2026-10-27/publication-guard-tour/bruce_test.elf','reference/analysis/optimization-2026-10-27/color-observer-tour/bruce_test.elf']
 fixture=json.loads((BASE/'native-fixture.json').read_text(encoding='utf-8-sig'));paths.append(next(e['path'] for e in fixture['build'] if e['path'].endswith('.elf')))
 native=json.loads((ROOT/'reference/validation/source-world-native.json').read_text(encoding='utf-8-sig'));paths.append(next(e['path'] for e in native['build'] if e['path'].endswith('.elf')))
 paths.append('reference/analysis/optimization-2026-10-27/color-observer-r01/bruce_test.elf')
 rows=[]
 for path in paths:
  data,ss=sections(ROOT/path);_,symbols=elf_symbols(ROOT/path)
  for name,(code,rel) in kernels.items():
   if name=='source_final_colors' and '/publication-guard-tour/' in path:continue
   at=symbols[name];section=next(q for _,q in ss if q[1]==1 and q[3]<=at and at+len(code)<=q[3]+q[5]);off=section[4]+at-section[3];wanted=bytearray(code)
   for offset,target,addend in rel:struct.pack_into('>I',wanted,offset,(symbols[target]+addend)&0xffffffff)
   actual=data[off:off+len(wanted)];assert actual==wanted,(path,name)
  rows.append(dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()))
 report=dict(status='passed_unchanged_generic_writer_and_active_observer',builds=rows,kernels={name:dict(bytes=len(code),relocations=len(rel),unlinked_sha256=hashlib.sha256(code).hexdigest()) for name,(code,rel) in kernels.items()},candidate_sha256=hashlib.sha256((BASE/'candidate/c64_rooms.c').read_bytes()).hexdigest(),production_changed=True,compiler_object_sha256=hashlib.sha256((BASE/'compiler-core.o').read_bytes()).hexdigest())
 (BASE/'native-images.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
