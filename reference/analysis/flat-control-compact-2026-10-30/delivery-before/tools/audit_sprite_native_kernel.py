"""Bind the actual68000 sprite-copy primitive across all tested images."""
from pathlib import Path
import hashlib,json,sys
from audit_vic_native_kernels import sections
from capture_paula_stream import elf_symbols
ROOT=Path(__file__).resolve().parents[1]
FOLDER='reference/analysis/optimization-2026-10-27'

def artifact(path):return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def main():
    sys.path.insert(0,str(ROOT/'.reference/tools/python'))
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    source_hash=hashlib.sha256(source).hexdigest()
    assert source_hash=='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for first,end in [(0x2584,0x25e2),(0x26a0,0x2704),(0x2719,0x274f)]:
        pc=first
        while pc<end:
            count,text=dis.instruction_at(pc);lines.append(f'${pc:04X} {text}');pc+=count
    assert (ROOT/'reference/analysis/sprite-copy-2026-10-29/source-copy-disassembly.txt').read_text().splitlines()==lines
    data,ss=sections(ROOT/'amiga/out/sprite_copy.o');s=next(s for n,s in ss if n=='.text.bl_sprite_copy')
    wanted=data[s[4]:s[4]+s[5]]
    native=json.loads((ROOT/'reference/validation/source-world-native.json').read_text(encoding='utf-8-sig'))
    paths=['amiga/out/bruce_amiga.elf',FOLDER+'/vic-cache-wrapped-timing/bruce_test.elf',
           FOLDER+'/sprite-copy-final-timing/bruce_test.elf',FOLDER+'/sprite-copy-final2-profile/bruce_test.elf',
           next(x['path'] for x in native['build'] if x['path'].endswith('.elf'))]
    builds=[]
    for path in paths:
        data,ss=sections(ROOT/path);_,sym=elf_symbols(ROOT/path);at=sym['bl_sprite_copy']
        assert sym['main']==0 or sym['_start']==0,('AmigaDOS entry',path)
        s=next(s for n,s in ss if s[1]==1 and s[3]<=at and at+len(wanted)<=s[3]+s[5]);off=s[4]+at-s[3]
        assert data[off:off+len(wanted)]==wanted,path
        builds.append(artifact(path))
    bad=FOLDER+'/contact-run-scoped-controls/bruce_test.elf';_,sym=elf_symbols(ROOT/bad)
    assert sym['main']!=0 and sym['_start']!=0 and sym['source_contact_rows_c']==0
    report=dict(status='passed_identical_sprite_kernel_and_entry_gate',source_sha256=source_hash,bytes=len(wanted),sha256=hashlib.sha256(wanted).hexdigest(),builds=builds,
        rejected_entry_counterexample=artifact(bad),entry_gate_rejects_real_counterexample=True,
        scope='Same linked68000 helper in normal, separate256-control, timing, profile and full53-fixture images',natural_playthrough=False,
        source_files=[artifact(p) for p in ['amiga/sprite_copy.s','tools/verify_amiga_entry.py','tools/audit_sprite_native_kernel.py']])
    out=ROOT/'reference/analysis/sprite-copy-2026-10-29/native-kernel-bytes.json'
    out.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print('PASS identical sprite kernel in five images,',len(wanted),'bytes; AmigaDOS entry gate checked')
if __name__=='__main__':main()
