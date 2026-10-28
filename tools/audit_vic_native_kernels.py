"""Bind actual68000 VIC kernel bytes across diagnostic/normal images."""
from pathlib import Path
import hashlib,json,struct
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/optimization-2026-10-27'

def sections(path):
 b=path.read_bytes();assert b[:6]==b'\x7fELF\x01\x02';off=struct.unpack_from('>I',b,32)[0];size,count,names=struct.unpack_from('>HHH',b,46)
 ss=[struct.unpack_from('>10I',b,off+i*size) for i in range(count)];q=ss[names];strings=b[q[4]:q[4]+q[5]]
 return b,[(strings[s[0]:strings.index(0,s[0])].decode(),s) for s in ss]
def main():
 b,ss=sections(ROOT/'amiga/out/vic_compare.o');kernels={}
 for name in ('bl_vic_repeat','bl_vic_equal63'):
  s=next(s for label,s in ss if label=='.text.'+name);kernels[name]=b[s[4]:s[4]+s[5]]
 native=json.loads((ROOT/'reference/validation/source-world-native.json').read_text(encoding='utf-8-sig'))
 paths=['amiga/out/bruce_amiga.elf',FOLDER+'/vic-repeat-scoped-final-timing/bruce_test.elf',FOLDER+'/vic-repeat-scoped-final-profile/bruce_test.elf',next(x['path'] for x in native['build'] if x['path'].endswith('.elf'))]
 rows=[]
 for path in paths:
  p=ROOT/path;data,ss=sections(p);_,symbols=elf_symbols(p)
  for name,wanted in kernels.items():
   at=symbols[name];s=next(s for label,s in ss if s[1]==1 and s[3]<=at and at+len(wanted)<=s[3]+s[5]);off=s[4]+at-s[3]
   assert data[off:off+len(wanted)]==wanted,(path,name)
  rows.append(dict(path=path,sha256=hashlib.sha256(data).hexdigest()))
 report=dict(status='passed_identical_native_vic_kernel_bytes',kernels={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in kernels.items()},builds=rows,
  natural_playthrough=False,scope='Exact linked helper machine code in normal, timing, profile and full fixture images; diagnostic reference code is separate',source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in ['amiga/vic_compare.s','tools/audit_vic_native_kernels.py']])
 (ROOT/'reference/analysis/vic-repeat-2026-10-28/native-kernel-bytes.json').write_bytes((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('PASS identical linked VIC helper code in four image variants:',{k:len(v) for k,v in kernels.items()})
if __name__=='__main__':main()
