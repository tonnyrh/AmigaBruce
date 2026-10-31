"""Private OP1/OP5 experiment: native continuations for generated direct JSRs.

Retains guest stack stores and all control-boundary checks. Sixteen local
native frames, with the original recursive path on overflow. No guest
opcode fetch/decode and no production file is changed.
"""
import hashlib,json,re,subprocess
from pathlib import Path
from audit_vic_native_kernels import sections
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/flat-control-2026-10-30'
def main():
 BASE.mkdir(exist_ok=True);folder=BASE/'candidate';folder.mkdir(exist_ok=True)
 program=(ROOT/'core/c64_actor_programs.h').read_text(encoding='utf-8-sig')
 assert [(i+1,l) for i,l in enumerate(program.splitlines()) if 'entry' in l]==[(2,'static void actor_code(unsigned short entry){'),(4,'switch(entry){'),(784,'default:source_fault=entry;return;')]
 program=program.replace('unsigned short address;unsigned char q,old;','unsigned short address=0;unsigned char q=0,old=0;\nstruct NativeFrame{unsigned short ret,index,address;unsigned char q,old;};\nstruct NativeFrame native_frames[16];unsigned short native_depth=0,native_resume=0;')
 program=program.replace('return;','goto actor_native_unwind;')
 flags='transition_pending || actor_delay_pending || actor_gameover_pending || actor_reset_pending || actor_irq_stop || source_fault'
 pattern=re.compile(r'^m\[0x100 \+ sp--\]=0x([0-9a-f]+);m\[0x100 \+ sp--\]=0x([0-9a-f]+);actor_code\(0x([0-9a-f]+)\);if\('+re.escape(flags)+r' \|\| actor_return!=0x([0-9a-f]+)\)goto actor_native_unwind;',re.M)
 calls=[]
 def convert(m):
  hi,lo,target,ret=(int(q,16) for q in m.groups());assert (((hi<<8)|lo)+1)&65535==ret
  idx=len(calls);calls.append(dict(target=target,ret=ret,index=idx))
  return ('m[0x100 + sp--]=0x%02x;m[0x100 + sp--]=0x%02x;\n'%(hi,lo)+
   'if(native_depth<16){struct NativeFrame *f=&native_frames[native_depth++];f->ret=0x%04x;f->index=%d;f->address=address;f->q=q;f->old=old;goto L%04x;}\n'%(ret,idx,target)+
   'actor_code(0x%04x);if('%target+flags+' || actor_return!=0x%04x)goto actor_native_unwind;'%ret)
 program=pattern.sub(convert,program);assert len(calls)==444
 assert program.endswith('}\n')
 tail='actor_native_unwind:;\nwhile(native_depth){\nstruct NativeFrame *f=&native_frames[--native_depth];address=f->address;q=f->q;old=f->old;\nif('+flags+' || actor_return!=f->ret)continue;\nnative_resume=f->index;goto actor_native_resume;\n}\nreturn;\nactor_native_resume:;\nswitch(native_resume){\n'
 tail+=''.join('case %d:goto L%04x;\n'%(r['index'],r['ret']) for r in calls)
 tail+='default:source_fault=0xffff;return;\n}\n'
 program=program[:-2]+tail+'}\n';(folder/'c64_actor_programs.h').write_text(program,encoding='utf-8')
 (folder/'c64_rooms.c').write_bytes((ROOT/'core/c64_rooms.c').read_bytes())
 toolchains=sorted((Path.home()/'.vscode/extensions').glob('bartmanabyss.amiga-debug-*'));compiler=toolchains[-1]/'bin/win32/opt/bin/m68k-amiga-elf-gcc.exe'
 flags=['-m68000','-Os','-g','-nostdlib','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-fomit-frame-pointer','-ffunction-sections','-fdata-sections','-mshort','-DBL_AUTOTEST=0','-fstack-usage','-I'+str(ROOT/'core')]
 builds=[]
 for label,source in [('before',ROOT/'core/c64_rooms.c'),('candidate',folder/'c64_rooms.c')]:
  obj=BASE/(label+'.o');subprocess.run([str(compiler),*flags,'-c',str(source),'-o',str(obj)],check=True)
  _,ss=sections(obj);sums={}
  for name,q in ss:
   if not q[2]&2:continue
   kind=next((k for k in ['.text','.data','.bss','.rodata'] if name==k or name.startswith(k+'.')),None)
   if kind:sums[kind]=sums.get(kind,0)+q[5]
  builds.append(dict(label=label,sections=sums,actor_stack=[l for l in obj.with_suffix('.su').read_text().splitlines() if 'actor_code\t' in l]))
 def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 report=dict(status='private_native_continuation_compiler_probe',production_changed=False,converted_calls=calls,native_capacity=16,overflow='Original recursive call and original guards',builds=builds,artifacts=[item(ROOT/'core/c64_rooms.c'),item(ROOT/'core/c64_actor_programs.h'),item(folder/'c64_rooms.c'),item(folder/'c64_actor_programs.h'),item(Path(__file__))]+[item(BASE/(n+ext)) for n in ['before','candidate'] for ext in ['.o','.su']],limits=['Compiler probe only; source and native controls not yet run','Local frame size is not whole native stack high-water','Native continuation array is independent of the unchanged guest stack'])
 (BASE/'probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(builds,indent=2))
if __name__=='__main__':main()
