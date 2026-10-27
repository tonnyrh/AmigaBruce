"""Room8 contact chain through actual6502 routines; controlled actor poses."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from audit_session_walls import run,SHA
from c64_room_model import oracle_contact
OUT=ROOT/'reference/analysis/room8-blasts-2026-10-26'
def main():
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/room8-blast-test/room8.dll'))
    d.bl_r8_prepare.argtypes=[ctypes.c_long]*8;d.bl_r8_read.argtypes=[ctypes.c_long]*2;d.bl_r8_read.restype=ctypes.c_long
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    rows=[];differences=[]
    for col,row in [(7,4),(29,4),(3,7),(17,7),(21,7)]:
        for actor in (1,2):
            for phase in (8,12,16):
                for kind in range(11):
                    for face in (0,1):
                        for dx in (-12,4,12):
                            x=col*8+dx;y=row*16+4
                            d.bl_r8_prepare(actor,col,row,phase,x,y,face,kind)
                            m=[d.bl_c64_read(i) for i in range(65536)]
                            m[0x500:0x4300]=b[0x500:0x4300];m[0x5000:0x5800]=b[0x5000:0x5800]
                            # $1C0A room pass before $5212/$2E39. $7C is
                            # set by the source IRQ/current native tick, not
                            # left at zero from the injected loader state.
                            m[0x7c]=0xa0;m[2]=50;m[0x100]=0
                            run(m,0x40bc);m[0x7b]=m[0x7b]-1 if m[0x7b] else 1
                            run(m,m[0x4ed2]+m[0x4ed3]*256+1)
                            pose=d.bl_r8_read(actor,4)
                            m[0x95:0x98]=[0,0,0];m[0x95+actor]=0x81 if actor==1 else 0x41
                            m[0x9e+actor]=(x+24)//2;m[0xa1+actor]=y;m[0xbf+actor]=d.bl_r8_read(actor,2);m[0xce+actor]=d.bl_r8_read(actor,3)
                            m[0x4f4e+actor]=pose;flags,_=oracle_contact(m,x,y,pose);m[0xb6+actor]=flags
                            run(m,0x2e39);expected=bool(m[0x95+actor]&1)
                            d.bl_r8_step();actual=bool(d.bl_r8_read(actor,0))
                            r=dict(bomb=[col,row],actor=actor,phase=phase,kind=kind,facing=face,x=x,y=y,
                                pose=pose,source_contact=flags,source_active=expected,amiga_active=actual)
                            rows.append(r)
                            if actual!=expected:differences.append(r)
    OUT.mkdir(parents=True,exist_ok=True)
    paths=['core/rooms.c','core/combat.c','core/c64_rooms.c','core/c64_room_data.h','core/c64_room_programs.h','core/c64_sprites.c',
        'tests/room8_blast_bridge.c','test-room8-blasts.ps1','tools/audit_room8_blasts.py']
    report=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,room=8,checks=len(rows),
        differences=differences,rows=rows,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths],
        limits=['Injected single actor poses and bomb stages; not natural C64 play','Complete actor/AI timing not asserted'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Room8: {len(rows)} entries, {len(differences)} differences; '+str({k:sum(r['kind']==k for r in differences) for k in range(11)}))
    for r in differences[:10]:print(r)
    assert not differences,'Source contact/state differences must be resolved or explicitly left open'
if __name__=='__main__':main()
