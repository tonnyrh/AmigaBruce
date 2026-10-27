"""Execute the frozen R10 floor/trap loop; injected controls, not natural play."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from verify_c64_room_runtime import invoke
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def main():
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    dll=ROOT/'.tmp/c64-room-test/rooms.dll';d=ctypes.CDLL(str(dll))
    d.bl_c64_load.argtypes=[ctypes.c_long];d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    d.bl_c64_tick.argtypes=[ctypes.c_long]*2;d.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    ranges=[(0x6e,0x79),(0x4e97,0x4e9c),(0x8c78,0x8fe8),(0xa000,0xa800),(0xd878,0xdbe8)]
    rows=[]
    for cleared in (False,True):
        d.bl_c64_reset()
        if cleared:
            for room in range(20):
                d.bl_c64_test_write(0x2a+room,0)
                p=b[0x4ce2+2*room]+256*b[0x4ce3+2*room]
                while not b[p]&128:d.bl_c64_test_write(p,0);p+=4
        d.bl_c64_load(9);d.bl_c64_test_write(0x17,0x68)
        m=[d.bl_c64_read(i) for i in range(65536)];m[0x500:0x4300]=b[0x500:0x4300]
        for step in range(240):
            for _ in range(3):
                d.bl_c64_field();m[0x16]=(m[0x16]+1)&255
                if m[0x49]:m[0x49]-=1
                elif m[0x4a]:m[0x4a]-=1;m[0x49]=255
            m[0x9e]=16;m[0xa1]=196;m[0x7c]=0xa0;m[2]=50;m[0x100]=0
            invoke(m,0x40bc);m[0x7b]=m[0x7b]-1 if m[0x7b] else 1;invoke(m,0x3bb2)
            d.bl_c64_tick(8,196)
            for lo,hi in ranges:
                for a in range(lo,hi):assert d.bl_c64_read(a)==m[a],(cleared,step,hex(a),d.bl_c64_read(a),m[a])
            rows.append(dict(cleared=cleared,step=step,old_column=m[0x70],new_column=m[0x6e],row=m[0x6f],upper_counters=m[0x77:0x79],floor_codes=m[0x8f98:0x8fb9]))
    out=ROOT/'reference/analysis/room10-electric-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(b)));lines=[]
    for a,end in [(0x348f,0x34c8),(0x3bb2,0x3c90),(0x404e,0x40bc),(0x5212,0x52ad)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {b[a:a+n].hex(" "):8} {t}');a+=n
    (out/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=['core/c64_rooms.c','core/c64_room_data.h','core/c64_room_programs.h','tools/audit_room10_electric.py','.tmp/c64-room-test/rooms.dll']
    r=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,source_loop_controls=len(rows),matched=True,
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths],rows=rows)
    (out/'source-controls.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {len(rows)} actual6502 R10 loop controls: floor, traps, charset and attributes')
if __name__=='__main__':main()
