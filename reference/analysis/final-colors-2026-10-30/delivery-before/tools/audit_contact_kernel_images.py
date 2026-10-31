"""Compare contact primitives across separate reference, fixture and runtime images."""
import hashlib,json,struct
from pathlib import Path
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
def item(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def verify():
 native=json.loads((ROOT/'reference/validation/source-world-native.json').read_text(encoding='utf-8-sig'))
 paths=['amiga/out/bruce_amiga.elf',next(x['path'] for x in native['build'] if x['path'].endswith('.elf')),'reference/analysis/optimization-2026-10-27/vic-cache-wrapped-timing/bruce_test.elf','reference/analysis/optimization-2026-10-27/sprite-copy-final-timing/bruce_test.elf']
 kernels={};relocations={}
 for name in ['contact_rows','contact_align','contact_prepare']:
  data,ss=sections(ROOT/('amiga/out/'+name+'.o'))
  for index,(section,s) in enumerate(ss):
   if not (s[2]&2 and s[5]):continue
   function=section.removeprefix('.text.');kernels[function]=data[s[4]:s[4]+s[5]];relocations[function]=[]
   for rn,r in ss:
    if r[1]!=4 or r[7]!=index:continue
    table=ss[r[6]][1];strings=ss[table[6]][1];names=data[strings[4]:strings[4]+strings[5]]
    for at in range(r[4],r[4]+r[5],r[9]):
     offset,info,addend=struct.unpack_from('>IIi',data,at);assert info&255==1,'Only verified R_68K_32 relocations'
     n,value,size,info2,other,section_index=struct.unpack_from('>IIIBBH',data,table[4]+(info>>8)*table[9])
     target=names[n:names.index(0,n)].decode()
     if not target:
      target_section=ss[section_index][0];assert target_section.startswith('.text.bl_contact_')
      target=target_section.removeprefix('.text.')
     relocations[function].append([offset,target,value+addend])
 assert len(kernels)==8
 for path in paths:
  data,ss=sections(ROOT/path);_,sym=elf_symbols(ROOT/path)
  for name,wanted in kernels.items():
   at=sym[name];s=next(s for n,s in ss if s[1]==1 and s[3]<=at and at+len(wanted)<=s[3]+s[5]);off=s[4]+at-s[3]
   resolved=bytearray(wanted)
   for offset,target,addend in relocations[name]:struct.pack_into('>I',resolved,offset,sym[target]+addend)
   assert data[off:off+len(wanted)]==resolved,(path,name)
 return dict(status='passed_equivalent_relocated_contact_primitives_in_separate_images',kernels={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in kernels.items()},relocations=relocations,builds=[item(p) for p in paths],sources=[item(p) for p in ['amiga/contact_rows.s','amiga/contact_align.s','amiga/contact_prepare.s','tools/audit_contact_kernel_images.py']])
def main():
 r=verify();(ROOT/'reference/analysis/render-coherence-2026-10-29/contact-kernel-images.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS 8 contact primitives, identical instructions and resolved relocations in 4 native images')
if __name__=='__main__':main()
