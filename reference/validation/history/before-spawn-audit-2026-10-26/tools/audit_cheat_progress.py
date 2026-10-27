"""Cheat setup is intentional; lamp state is checked with actual $331C."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def collect(m,col,row):
    m[0x51]=0;m[0xe9]=row;m[0x1fe:0x200]=[0xfe,0xff]
    cpu=MPU(memory=m,pc=0x331c);cpu.y=col;cpu.sp=253
    for _ in range(10000):
        if cpu.pc==0xffff:assert not cpu.p&1;return
        cpu.step()
    raise AssertionError('Source lamp pickup did not return')
def main():
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    dll=ROOT/'.tmp/session-test/session.dll';d=ctypes.CDLL(str(dll))
    d.bl_cheat_start.argtypes=[ctypes.c_long];d.bl_cheat_room_contract.argtypes=[ctypes.c_long]
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    d.bl_cheat_start(0);base=[d.bl_c64_read(i) for i in range(65536)];base[0x500:0x4300]=b[0x500:0x4300]
    rows=[];pickups=0
    for target in range(20):
        assert d.bl_cheat_room_contract(target)==0,('native host cheat case',target+1)
        m=list(base);executed=0
        for room in range(target):
            p=m[0x4ce2+room*2]+256*m[0x4ce3+room*2];m[0x29]=room
            while m[0x2a+room] and not m[p]&128:
                if m[p]:collect(m,m[p+2],m[p+3]);executed+=1
                p+=4
            assert m[0x2a+room]==0
        d.bl_cheat_start(target)
        for room in range(20):
            assert d.bl_c64_read(0x2a+room)==m[0x2a+room],(target+1,room+1,'counter')
            p=m[0x4ce2+room*2]+256*m[0x4ce3+room*2]
            while not m[p]&128:
                for a in range(p,p+4):assert d.bl_c64_read(a)==m[a],(target+1,room+1,hex(a))
                p+=4
        rows.append(dict(start_room=target+1,executed_source_pickups=executed,matched=True));pickups+=executed
    out=ROOT/'reference/analysis/cheat-progress-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(b)));lines=[]
    for a,end in [(0xfed,0x104b),(0x331c,0x33bd),(0x2f04,0x2f39)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {b[a:a+n].hex(" "):8} {t}');a+=n
    (out/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=['core/session.c','core/c64_rooms.c','core/c64_rooms.h','tests/cheat_progress_fixture.h','tests/session_fixture.h','tests/session_bridge.c','test-session.ps1','tools/audit_cheat_progress.py','.tmp/session-test/session.dll']
    r=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,cheat_is_amiga_extension=True,menu_start_cases=20,
        executed_source_pickups=pickups,rows=rows,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (out/'report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(f'PASS all20 cheat starts vs {pickups} actual6502 record pickups; target/later records and zero-count placeholders retained')
if __name__=='__main__':main()
