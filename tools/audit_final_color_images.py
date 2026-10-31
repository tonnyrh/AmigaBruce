"""Bind the original generic writer and color kernel to linked68000 images."""
import hashlib,json,struct
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/final-colors-2026-10-30'
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def object_kernel(path,section_name):
 data,ss=sections(ROOT/path);idx=next(i for i,(name,s) in enumerate(ss) if name==section_name);q=ss[idx][1];code=data[q[4]:q[4]+q[5]];rel=[]
 for _,s in ss:
  if s[1]!=4 or s[7]!=idx:continue
  table=ss[s[6]][1];strings=ss[table[6]][1];names=data[strings[4]:strings[4]+strings[5]]
  for at in range(s[4],s[4]+s[5],s[9]):
   offset,info,addend=struct.unpack_from('>IIi',data,at);assert info&255==1,'Only R_68K_32 is expected'
   n,value,size,kind,other,index=struct.unpack_from('>IIIBBH',data,table[4]+(info>>8)*table[9]);target=names[n:names.index(0,n)].decode()
   if not target:
    name=ss[index][0]
    for prefix in ['.text.','.data.','.bss.','.rodata.']:
     if name.startswith(prefix):target=name[len(prefix):];break
    assert target,(section_name,name,index)
   target=target.replace('animation_cell_changed.part.0','animation_cell_changed_active')
   rel.append((offset,target,addend))
 return code,rel

def main():
 before=BASE+'/compiler-probes/before.o';current=BASE+'/compiler-probes/production.o'
 if not (ROOT/current).exists():(ROOT/current).write_bytes((ROOT/'amiga/out/c64_rooms.o').read_bytes())
 specs=[('source_written',before,'.text.source_written'),('animation_cell_changed_active',before,'.text.animation_cell_changed.part.0'),('source_final_colors',current,'.text.source_final_colors')]
 kernels={name:object_kernel(path,section) for name,path,section in specs}
 paths=json.loads((ROOT/BASE/'v3-image-paths.json').read_text(encoding='utf-8-sig'))
 rows=[]
 for path in paths:
  data,ss=sections(ROOT/path);_,symbols=elf_symbols(ROOT/path)
  for name,(code,rel) in kernels.items():
   at=symbols[name];s=next(s for _,s in ss if s[1]==1 and s[3]<=at and at+len(code)<=s[3]+s[5]);off=s[4]+at-s[3];wanted=bytearray(code)
   for offset,target,addend in rel:
    assert target in symbols,(name,target,path)
    struct.pack_into('>I',wanted,offset,(symbols[target]+addend)&0xffffffff)
   actual=data[off:off+len(wanted)];assert actual==wanted,(path,name,[(i,a,b) for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b][:8])
  rows.append(item(path))
 report=dict(status='passed_original_writer_and_native_color_kernel_linkage',builds=rows,kernels={name:dict(bytes=len(code),unlinked_sha256=hashlib.sha256(code).hexdigest(),relocations=len(rel)) for name,(code,rel) in kernels.items()},artifacts=[item(before),item(current),item('tools/audit_final_color_images.py'),item(BASE+'/v3-image-paths.json')],limits=['Original writer/active-metadata object bytes and resolved call/data references preserved','Historical V3 color kernel matched across its archived normal,53-fixture,710-control and20-room images; current renderer has a separate exact derivation','No original-edition, natural-play or real-time certification'])
 (ROOT/BASE/'native-images.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS original generic writer/active metadata and color kernel in four linked68000 images')
if __name__=='__main__':main()
