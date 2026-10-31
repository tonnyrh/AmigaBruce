"""Current normal/reference/fixture primitive and loaded-footprint linkage."""
import hashlib,json
from pathlib import Path
from audit_contact_kernel_images import verify as contact_verify
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
from verify_amiga_entry import verify as entry_verify
ROOT=Path(__file__).resolve().parents[1]
BASE='reference/analysis/flat-control-compact-2026-10-30'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
 native=read('reference/validation/source-world-native.json')
 paths=['amiga/out/bruce_amiga.elf',next(e['path'] for e in native['build'] if e['path'].endswith('.elf')),'reference/analysis/optimization-2026-10-27/compact-call-r01/bruce_test.elf',BASE+'/delivery-before/amiga/out/bruce_amiga.elf']
 contact=contact_verify(paths);assert len(contact['kernels'])==8
 p=BASE+'/delivery-contact-kernels.json';(ROOT/p).write_text(json.dumps(contact,indent=2)+'\n');proofs=[p]+[e['path'] for e in contact['sources']]
 kernels={}
 for obj,names in [('sprite_copy',['bl_sprite_copy']),('vic_compare',['bl_vic_repeat','bl_vic_equal63'])]:
  raw,ss=sections(ROOT/('amiga/out/'+obj+'.o'))
  for name in names:
   s=next(s for n,s in ss if n=='.text.'+name);kernels[name]=raw[s[4]:s[4]+s[5]]
 for path in paths:
  data,ss=sections(ROOT/path);_,syms=elf_symbols(ROOT/path);entry_verify(ROOT/path)
  for name,wanted in kernels.items():
   at=syms[name];s=next(s for n,s in ss if s[1]==1 and s[3]<=at and at+len(wanted)<=s[3]+s[5]);off=s[4]+at-s[3];assert data[off:off+len(wanted)]==wanted,(path,name)
 bad='reference/analysis/optimization-2026-10-27/contact-run-scoped-controls/bruce_test.elf'
 try:entry_verify(ROOT/bad)
 except AssertionError:pass
 else:raise AssertionError('Entry gate failed to reject real counterexample')
 footprints=[]
 for path in [paths[-1],paths[0]]:
  _,ss=sections(ROOT/path);sizes={n:s[5] for n,s in ss if n in ['.text','.rodata','.data','.bss']};footprints.append(dict(path=path,sections=sizes))
 before,after=[r['sections'] for r in footprints]
 assert after['.data']==before['.data'] and after['.bss']==before['.bss']
 saving=before['.text']+before['.rodata']-after['.text']-after['.rodata'];assert saving>=12000
 proofs+=paths+[bad,'amiga/contact_rows.s','amiga/contact_align.s','amiga/contact_prepare.s','amiga/vic_compare.s','amiga/sprite_copy.s','tools/verify_amiga_entry.py','tools/verify_compact_kernel_linkage.py']
 r=dict(status='passed_current_compact_primitive_linkage',contact_kernels=8,sprite_vic_kernels={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in kernels.items()},entry_gate_rejects_real_counterexample=True,footprints=footprints,loaded_code_table_saving=saving,artifacts=[item(p) for p in sorted(set(proofs))])
 (ROOT/BASE/'delivery-kernels.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS current primitive linkage and unchanged DATA/BSS; loaded code/table saving',saving)
if __name__=='__main__':main()
