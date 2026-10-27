"""Check the projection against actual active-bit branches, not guessed AI."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU

def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    d=ctypes.CDLL(str(ROOT/'.tmp/source-visibility-test/visibility.dll'))
    d.bl_visibility_flag.argtypes=[ctypes.c_long,ctypes.c_long];d.bl_visibility_flag.restype=ctypes.c_long
    buf=(ctypes.c_ubyte*65536)();d.bl_visibility_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    def memory():d.bl_visibility_copy(buf);return bytes(buf)
    d.bl_visibility_prepare();before=memory();rows=[];instructions=0
    for actor in range(3):
        for flags in range(256):
            results=[]
            for entry,yes,no in ((0x17be,0x17c4,0x17de),(0x2588,0x258e,0x25d7),(0x25ef,0x25f5,0x2634)):
                m=list(source);m[0x95+actor]=flags;c=MPU(memory=m,pc=entry);c.x=actor
                while c.pc not in (yes,no):c.step();instructions+=1
                results.append(int(c.pc==yes))
            assert len(set(results))==1
            actual=d.bl_visibility_flag(actor,flags);assert actual==results[0],(actor,flags,actual,results)
            rows.append(dict(actor=actor,flags=flags,active=actual))
    after=memory();allowed={0x95,0x96,0x97}
    assert all(before[i]==after[i] for i in range(65536) if i not in allowed),'Projection changed source RAM'
    snapshot=json.loads((ROOT/'reference/analysis/yamo-r02-2026-10-27/snapshot.json').read_text())
    assert snapshot['actors'][1]['active']==128 and d.bl_visibility_flag(1,128)==0
    files=['core/session.c','core/c64_rooms.c','core/c64_rooms.h','tests/source_visibility_bridge.c','test-source-visibility.ps1','tools/audit_source_visibility.py']
    report=dict(status='passed_original_active_bit_projection',checks=len(rows),source_instructions=instructions,
        source_sha256=hashlib.sha256(source).hexdigest(),edition_verified=False,natural_playthrough=False,
        source_entries=['$17BE','$2588','$25EF'],snapshot_sha256=snapshot['snapshot_sha256'],snapshot_yamo_flags=128,
        source_ram_unchanged_except_injected_flags=True,rows=rows,
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-visibility-host.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(rows)} active-bit projections against {instructions} actual source instructions; snapshot Yamo $80 hidden')
if __name__=='__main__':main()
