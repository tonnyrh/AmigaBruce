"""Isolated 68000 object probe: adjacent private guest CPU bytes.

No production mutation. This is a layout/compiler experiment, not an
accepted optimization or proof of native behavioral equivalence.
"""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'reference/analysis/cpu-register-layout-2026-10-30'
TOKEN=re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|->|\S',re.S)
REGS=set('a x y c z n v d sp'.split())
def rewrite(text):
 # Field declarations and member references are not private CPU variables.
 saved=[]
 def protect(m):
  saved.append(m.group());return 'PROTECTED_TYPE_%d'%(len(saved)-1)
 text=re.sub(r'typedef struct\s*\{.*?\}\s*\w+\s*;',protect,text,flags=re.S)
 # PLANAR_WORD's c is a macro parameter, not the CPU carry byte.
 text=re.sub(r'^#define PLANAR_WORD[^\n]*',protect,text,flags=re.M)
 last='';count=0
 def token(m):
  nonlocal last,count
  s=m.group()
  if s.startswith(('/*','//','"',"'")):return s
  prev=last;last=s
  if s in REGS and prev not in ('.','->'):
   count+=1;return 'CPU_R('+s+')'
  return s
 text=TOKEN.sub(token,text)
 for i,s in enumerate(saved):text=text.replace('PROTECTED_TYPE_%d'%i,s)
 return text,count

def main():
 BASE.mkdir(exist_ok=True);candidate=BASE/'candidate';candidate.mkdir(exist_ok=True)
 counts={}
 for name in ['c64_rooms.c','c64_actor_programs.h','c64_sfx.h']:
  text=(ROOT/'core'/name).read_text(encoding='utf-8-sig')
  if name=='c64_rooms.c':
   decl='static unsigned char a,x,y,c,z,n,v,d,sp,loaded=255,transition_pending;'
   assert text.count(decl)==1;text=text.replace(decl,'CPU_DECL_PLACEHOLDER')
  text,counts[name]=rewrite(text)
  if name=='c64_rooms.c':text=text.replace('CPU_DECL_PLACEHOLDER','typedef struct {unsigned char a,x,y,c,z,n,v,d,sp;} GuestCpu;\nstatic GuestCpu guest_cpu;\n#define CPU_R(field) guest_cpu.field\nstatic unsigned char loaded=255,transition_pending;')
  (candidate/name).write_text(text,encoding='utf-8')
 toolchains=sorted((Path.home()/'.vscode/extensions').glob('bartmanabyss.amiga-debug-*'))
 compiler=toolchains[-1]/'bin/win32/opt/bin/m68k-amiga-elf-gcc.exe'
 flags=['-m68000','-Os','-g','-nostdlib','-ffreestanding','-fno-builtin','-fno-tree-loop-distribute-patterns','-fomit-frame-pointer','-ffunction-sections','-fdata-sections','-mshort','-DBL_AUTOTEST=0','-fstack-usage','-I'+str(ROOT/'core')]
 outputs=[]
 for label,source in [('before',ROOT/'core/c64_rooms.c'),('candidate',candidate/'c64_rooms.c')]:
  obj=BASE/(label+'.o');subprocess.run([str(compiler),*flags,'-c',str(source),'-o',str(obj)],check=True)
  outputs.append(obj)
 sys_path=ROOT/'tools'
 import sys;sys.path.insert(0,str(sys_path))
 from audit_vic_native_kernels import sections
 sizes=[]
 for p in outputs:
  _,ss=sections(p);sums={}
  for name,q in ss:
   if not q[2]&2:continue
   kind=next((k for k in ['.text','.data','.bss','.rodata'] if name==k or name.startswith(k+'.')),None)
   if kind:sums[kind]=sums.get(kind,0)+q[5]
  sizes.append(dict(label=p.stem,sections=sums))
 def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 report=dict(status='isolated_compiler_layout_probe_only',production_changed=False,register_access_counts=counts,compiler=str(compiler),flags=flags,builds=sizes,artifacts=[item(p) for p in outputs]+[item(candidate/n) for n in counts]+[item(ROOT/'core'/n) for n in counts],limitations=['Unlinked object sizes; not normal linked game footprint','No native execution or timing yet','Lexically transformed scalar register accesses require source and target checks before acceptance'])
 (BASE/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(sizes,indent=2))
if __name__=='__main__':main()
