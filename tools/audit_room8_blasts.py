"""Room8 contact chain through actual6502 routines; controlled actor poses."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from audit_session_walls import run,SHA
from c64_room_model import oracle_contact
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
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
                for kind in range(12):
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
                            m[0x95:0x98]=[0,0,0];m[0x95+actor]=0x81 if actor==1 else 0x41
                            m[0x9e+actor]=(x+24)//2;m[0xa1+actor]=y;m[0xbf+actor]=d.bl_r8_read(actor,2);m[0xce+actor]=d.bl_r8_read(actor,3)
                            previous=(20 if face else 16) if kind==1 else (18 if face else 14)
                            m[0xa4+actor]=face;m[0x4f48+actor]=previous;m[0x4f4e+actor]=previous+actor*70
                            m[0x4fdb+actor]=0;m[0xb6+actor]=0;m[0xaa+actor]=0
                            run(m,0x2780,actor);pose=m[0x4f4e+actor]
                            assert pose==d.bl_r8_read(actor,4),(actor,kind,face,pose,d.bl_r8_read(actor,4))
                            m[0x4f4e+actor]=pose;flags,_=oracle_contact(m,x,y,pose);m[0xb6+actor]=flags
                            run(m,0x2e39);expected=bool(m[0x95+actor]&1)
                            d.bl_r8_step();actual=bool(d.bl_r8_read(actor,0))
                            delay=m[0x5e if actor==1 else 0x5d] if not expected else 0
                            if not expected:assert d.bl_r8_read(actor,1)==delay
                            r=dict(bomb=[col,row],actor=actor,phase=phase,kind=kind,facing=face,x=x,y=y,
                                pose=pose,source_contact=flags,source_active=expected,amiga_active=actual,source_delay=delay)
                            rows.append(r)
                            if actual!=expected:differences.append(r)
    OUT.mkdir(parents=True,exist_ok=True)
    before=ROOT/'reference/validation/history/before-room8-blasts-2026-10-26/reference/analysis/room8-blasts-2026-10-26/report.json'
    old=json.loads(before.read_text(encoding='utf-8-sig'))
    keys={(tuple(x['bomb']),x['actor'],x['phase'],x['kind'],x['facing'],x['x'],x['y']) for x in old['differences']}
    native=[r for r in rows if (tuple(r['bomb']),r['actor'],r['phase'],r['kind'],r['facing'],r['x'],r['y']) in keys or
        (r['kind']==0 and r['phase']==8 and r['facing']==1 and r['x']==r['bomb'][0]*8+4) or
        (r['kind']==11 and r['phase']==12 and r['facing']==1 and r['x']==r['bomb'][0]*8+4)]
    header=ROOT/'tests/room8_blast_fixture.h'
    values=[[r['actor'],*r['bomb'],r['phase'],r['x'],r['y'],r['facing'],r['kind'],int(r['source_active']),r['source_delay']] for r in native]
    header.write_text('/* Actual6502 $2780/$5212/$2E39 controls; not natural play. */\n'+
        '#ifndef BRUCE_ROOM8_BLAST_FIXTURE_H\n#define BRUCE_ROOM8_BLAST_FIXTURE_H\n'+
        '#include "../core/rooms.h"\n#include "../core/c64_rooms.h"\n'+
        'static const short room8_blast_cases[][10]={\n'+',\n'.join('{'+','.join(map(str,v))+'}' for v in values)+'\n};\n'+
        '''static unsigned short room8_blast_fixture_run(void){
    BlCombat w;BlProgress p;unsigned short i,j;
    for(i=0;i<sizeof(room8_blast_cases)/sizeof(room8_blast_cases[0]);i++){
        const short *c=room8_blast_cases[i];BlFighter *f;
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,7);
        bl_c64_test_write(0x7a,1);for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=&w.enemy[c[0]-1];f->active=1;f->body.x=c[4]*16;f->body.y=c[5]*16;f->body.facing=(unsigned char)c[6];
        f->ai=BL_AI_WAIT;f->timer=6;
        if(c[7]==9){f->reaction=BL_REACTION_HURT;f->stun=3;}
        if(c[7]==10){f->reaction=BL_REACTION_DOWN;f->stun=12;f->body.prone=1;}
        if(c[7]==11){f->reaction=BL_REACTION_DOWN;f->stun=9;f->body.prone=1;}
        bl_c64_test_write(0x4fde,c[3]);bl_c64_test_write(0x4fe1,c[1]-1);bl_c64_test_write(0x4fe4,c[2]-1);
        bl_c64_test_execute(0x3228);bl_progress_step(&p,&w,0);
        if(f->active!=c[8] || (!f->active && f->respawn!=c[9]))return i+1;
    }
    return 0;
}
#endif
''',encoding='ascii')
    dis=Disassembler(MPU(memory=list(b)));lines=[]
    for a,end in [(0x2780,0x29c3),(0x2e39,0x2f07),(0x304b,0x306b),(0x5212,0x52ad)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {b[a:a+n].hex(" "):8} {t}');a+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paths=['core/rooms.c','core/combat.c','core/combat.h','core/c64_rooms.c','core/c64_room_data.h','core/c64_room_programs.h','core/c64_sprites.c',
        'tests/room8_blast_bridge.c','tests/room8_blast_fixture.h','test-room8-blasts.ps1','tools/audit_room8_blasts.py']
    report=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,room=8,checks=len(rows),
        differences=differences,rows=rows,native_cases=len(native),before_differences=len(keys),source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths],
        limits=['Injected single actor poses and bomb stages; not natural C64 play','Complete actor/AI timing not asserted'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Room8: {len(rows)} entries, {len(differences)} differences; '+str({k:sum(r['kind']==k for r in differences) for k in range(12)}))
    for r in differences[:10]:print(r)
    assert not differences,'Source contact/state differences must be resolved or explicitly left open'
if __name__=='__main__':main()
