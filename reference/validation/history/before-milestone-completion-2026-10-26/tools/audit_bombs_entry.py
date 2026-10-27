"""Actual6502 entry/object/death controls; explicit injected states, not play."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from audit_session_walls import run,SHA
from c64_room_model import oracle_contact
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
OUT=ROOT/'reference/analysis/bombs-entry-2026-10-26'
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def main():
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/bombs-entry-test/bombs.dll'))
    arities={'bl_entry_prepare':5,'bl_entry_run':1,'bl_entry_read':1,'bl_bomb_prepare':5,'bl_bomb_read':1,
        'bl_c64_read':1,'bl_c64_test_write':2,'bl_c64_test_execute':1,'bl_c64_contact':4,'bl_c64_enemy_hazard':1}
    for name,n in arities.items():getattr(d,name).argtypes=[ctypes.c_long]*n;getattr(d,name).restype=ctypes.c_long
    d.bl_c64_read.restype=ctypes.c_ubyte
    def memory():
        m=[d.bl_c64_read(i) for i in range(65536)]
        m[0x500:0x4300]=b[0x500:0x4300];m[0x5000:0x5800]=b[0x5000:0x5800]
        # $15D0-$15EE / native tick select the active charset before
        # $5212. An injected loader alone leaves $7C uninitialised.
        m[0x7c]=0xa0 if m[0xf2]==0x38 else 0xa8 if m[0xf2]==0x3a else 0xb0 if m[0xf2]==0x3c else 0xb8
        return m
    entries=[]
    for room in range(20):
        for actor in (1,2):
            for first in (0,191,192,255):
                for second in (0,1):
                    for saved in (0,1):
                        d.bl_entry_prepare(room,actor,first,second,saved);m=memory()
                        m[0xd1+actor]=20 if actor==1 else 7;m[0x51]=actor;m[0x52]=3-actor
                        cpu=MPU(memory=m,pc=0xbfa);cpu.x=actor;cpu.y=3-actor;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
                        for _ in range(10000):
                            if cpu.pc==0xffff:break
                            cpu.step()
                        assert cpu.pc==0xffff
                        expected=[m[0x9e+actor]*2-24,m[0xa1+actor],m[0xd1+actor]]
                        d.bl_entry_run(actor);actual=[d.bl_entry_read(i) for i in range(3)]
                        assert actual==expected,(room,actor,first,second,saved,actual,expected)
                        assert d.bl_c64_read(0x16)==m[0x16] and d.bl_c64_read(0x8a+actor)==m[0x8a+actor]
                        entries.append([room,actor,first,second,saved,*expected])
    # Find real source-mask contacts with the actual R07 bomb, not rectangles.
    contacts=[]
    for actor in (0,1,2):
        d.bl_bomb_prepare(6,actor,140,180,0);m=memory();pose=actor*70+2;point=None
        for y in range(168,192):
            for x in range(128,146,2):
                if (x//8<=18<=x//8+2 and (y-12)//16<=11<=(y-12)//16+1 and
                    oracle_contact(m,x,y,pose)[0]&2):point=(x,y);break
            if point:break
        assert point,actor
        x,y=point;d.bl_bomb_prepare(6,actor,x,y,0);m=memory()
        m[0x95:0x98]=[0,0,0];m[0x95+actor]=(1,0x81,0x41)[actor]
        m[0x9e+actor]=(x+24)//2;m[0xa1+actor]=y;m[0xbf+actor]=0
        m[0x4f4e+actor]=pose;m[0xb6+actor]=oracle_contact(m,x,y,pose)[0]
        run(m,0x2e39)
        if actor:d.bl_bomb_step()
        else:d.bl_bomb_contact()
        expected=[m[a] for a in range(0x4fde,0x4fe7)]
        actual=[d.bl_c64_read(a) for a in range(0x4fde,0x4fe7)]
        assert actual==expected,(actor,point,actual,expected)
        assert actual[0]==1
        contacts.append(dict(actor=actor,x=x,y=y,records=actual))
    # Source explosion stages generate hazardous71..7C tiles. Cold and
    # already fatal combat damage both enter BF25; old BF24 must not mask it.
    deaths=[]
    for dying in (0,1,2):
        x,y=124,170;d.bl_bomb_prepare(6,0,x,y,dying)
        for a,v in [(0x4fde,8),(0x4fe1,17),(0x4fe4,10)]:d.bl_c64_test_write(a,v)
        d.bl_c64_test_execute(0x3228);m=memory()
        m[0x95:0x98]=[1,0,0];m[0x9e]=(x+24)//2;m[0xa1]=y;m[0xbf]=(19 if dying==1 else 24 if dying==2 else 0)
        m[0xce]=12 if dying==1 else 64 if dying==2 else 0;m[0x4f4e]=2
        m[0xb6]=oracle_contact(m,x,y,2)[0];m[0xd1]=255 if dying==1 else 36
        run(m,0x2e39);assert m[0xbf]==25 and m[0xce]==16
        d.bl_bomb_contact();actual=[d.bl_bomb_read(i) for i in range(9)]
        assert actual[:4]==[-1,16,4,1] and actual[4:7]==[x,y,8],(dying,actual)
        assert d.bl_c64_audio_requests()&(1<<12)
        d.bl_c64_test_write(0x8b,44);d.bl_c64_test_write(0x8c,56)
        for step in range(16):
            cpu,_=run(m,0x1c5b,stops=(0xffff,0x1818));d.bl_bomb_actor_step()
            if step<15:
                assert cpu.pc==0xffff and m[0x9e]*2-24==x and m[0xa1]==y
                assert [d.bl_bomb_read(4),d.bl_bomb_read(5),d.bl_bomb_read(6)]==[x,y,8]
            else:
                assert cpu.pc==0x1818 and d.bl_bomb_read(7)==1 and d.bl_bomb_read(8)==3
                assert d.bl_c64_read(0x8b)==0 and d.bl_c64_read(0x8c)==0
        deaths.append(dict(previous=dying,after=actual,still_actor_updates=16,source_life_branch='$1818'))
    blast_contacts=[]
    for actor in (1,2):
        d.bl_bomb_prepare(6,actor,124,170,0)
        for a,v in [(0x4fde,8),(0x4fe1,17),(0x4fe4,10)]:d.bl_c64_test_write(a,v)
        d.bl_c64_test_execute(0x3228);point=None
        for y in range(160,187):
            for x in range(120,151,2):
                if x//8<=19 and x//8+2>=17 and (d.bl_c64_contact(x,y,actor*70+2,0)&2):point=(x,y);break
            if point:break
        assert point
        x,y=point;d.bl_bomb_prepare(6,actor,x,y,0)
        for a,v in [(0x4fde,8),(0x4fe1,17),(0x4fe4,10)]:d.bl_c64_test_write(a,v)
        d.bl_c64_test_execute(0x3228);m=memory()
        m[0x95:0x98]=[0,0,0];m[0x95+actor]=0x81 if actor==1 else 0x41
        m[0x9e+actor]=(x+24)//2;m[0xa1+actor]=y;m[0xbf+actor]=0
        m[0xb6+actor]=oracle_contact(m,x,y,actor*70+2)[0];assert m[0xb6+actor]&2
        run(m,0x2e39);assert not m[0x95+actor]&1
        expected=m[0x5e if actor==1 else 0x5d];d.bl_bomb_step()
        assert d.bl_bomb_read(8+actor)==0 and d.bl_bomb_read(10+actor)==expected
        blast_contacts.append([actor,x,y,expected])
    hazards=[]
    for room in (6,7,10,11,12,14,16):
        for actor in (1,2):
            for age in (0,25,32):
                d.bl_bomb_prepare(room,actor,140,180,0);d.bl_c64_test_write(0x88,age);m=memory()
                m[0x51]=actor;m[0x95+actor]=0x81 if actor==1 else 0x41
                run(m,0x304b,actor)
                expected=m[0x5e if actor==1 else 0x5d]
                assert d.bl_c64_enemy_hazard(actor)==expected,(room,actor,age,expected)
                assert not(d.bl_c64_read(0x95+actor)&1)
                hazards.append([room,actor,age,expected])
    assert d.bl_c64_fault()==0
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(b)));lines=[]
    for a,end in [(0xbfa,0xc4d),(0x2e39,0x2f07),(0x304b,0x30d4),(0x3228,0x32dc),(0x407d,0x4086)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {b[a:a+n].hex(" "):8} {t}');a+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    native=[row for row in entries if row[0] in (5,6,7,10) and (row[2:5] in ([0,0,0],[255,0,0],[255,1,0],[0,0,1]))]
    header=ROOT/'tests/bombs_entry_fixture.h'
    header.write_text('/* Generated entry expectations from actual6502 calls. */\n'+
        '#ifndef BRUCE_BOMBS_ENTRY_FIXTURE_H\n#define BRUCE_BOMBS_ENTRY_FIXTURE_H\n'+
        '#include "../core/rooms.h"\n#include "../core/c64_rooms.h"\n#include "../core/c64_sprites.h"\n'+
        'static const short source_entry_cases[][8]={\n'+',\n'.join('{'+','.join(map(str,row))+'}' for row in native)+'\n};\n'+
        'static const short source_bomb_contacts[][3]={'+','.join('{'+','.join(map(str,[c['actor'],c['x'],c['y']]))+'}' for c in contacts)+'};\n'+
        'static const short source_blast_contacts[][4]={'+','.join('{'+','.join(map(str,c))+'}' for c in blast_contacts)+'};\n'+
        '''static unsigned short bombs_entry_fixture_run(void){
    BlCombat w;BlProgress p;BlC64Sprite v;unsigned short i,j;long px,py,h;
    for(i=0;i<sizeof(source_entry_cases)/sizeof(source_entry_cases[0]);i++){
        const short *c=source_entry_cases[i];
        bl_c64_reset();bl_c64_load(c[0]);bl_c64_test_write(0x16,0x20);bl_c64_test_write(0x17,0x60);
        bl_c64_test_write(0x6021+3-c[1],c[2]);bl_c64_test_write(0x6022+3-c[1],c[3]);
        if(c[4])bl_c64_enemy_follow(c[1],1,44,81,6);
        h=c[1]==1?20:7;px=py=0;bl_c64_enemy_entry(c[1],&px,&py,&h);
        if(px!=c[5] || py!=c[6] || h!=c[7])return 1+i;
    }
    for(i=0;i<2;i++){
        const short *c=source_blast_contacts[i];BlFighter *f;
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        bl_c64_test_write(0x7a,1);for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=&w.enemy[c[0]-1];f->active=1;f->body.x=c[1]*16;f->body.y=c[2]*16;f->body.facing=1;f->ai=BL_AI_WAIT;f->timer=6;
        bl_c64_test_write(0x4fde,8);bl_c64_test_write(0x4fe1,17);bl_c64_test_write(0x4fe4,10);bl_c64_test_execute(0x3228);
        bl_progress_step(&p,&w,0);if(f->active || f->respawn!=c[3])return 90+i;
    }
    for(i=0;i<3;i++){
        const short *c=source_bomb_contacts[i];BlFighter *f;
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        bl_c64_test_write(0x7a,1);for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=0;}
        f=c[0]?&w.enemy[c[0]-1]:&w.player;f->active=1;f->body.x=c[1]*16;f->body.y=c[2]*16;
        f->body.facing=1;f->ai=BL_AI_WAIT;f->timer=6;
        if(c[0])bl_progress_step(&p,&w,0);else bl_progress_contacts(&p,&w,0);
        if(bl_c64_read(0x4fde)!=1 || bl_c64_read(0x4fe1)!=17 || bl_c64_read(0x4fe4)!=10)return 40+i;
    }
    for(i=0;i<3;i++){
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,6);
        bl_c64_test_write(0x7a,1);w.enemy[0].respawn=w.enemy[1].respawn=0;
        w.player.body.x=124*16;w.player.body.y=170*16;w.player.body.facing=1;
        if(i==1){w.player.health=-1;w.player.stun=12;w.player.reaction=BL_REACTION_DOWN;w.player_deaths=1;}
        if(i==2){w.player.body.wall.state=24;w.player.body.wall.counter=64;w.player.body.wall.pose=2;}
        bl_c64_test_write(0x4fde,8);bl_c64_test_write(0x4fe1,17);bl_c64_test_write(0x4fe4,10);bl_c64_test_execute(0x3228);
        bl_progress_contacts(&p,&w,0);v.initialized=0;bl_c64_sprite_step(&v,&w.player,2);
        if(w.player.reaction!=BL_REACTION_DEAD || w.player.stun!=16 || w.player_deaths!=1 || v.pose!=8 ||
           !(bl_c64_audio_requests()&4096))return 50+i;
        bl_c64_test_write(0x8b,44);bl_c64_test_write(0x8c,56);
        for(j=0;j<16;j++){
            bl_combat_step(&w,0);
            if(j<15 && (bl_x(&w.player.body)!=124 || bl_y(&w.player.body)!=170))return 60+i;
        }
        if(w.player_respawns!=1 || w.lives!=3 || bl_c64_read(0x8b) || bl_c64_read(0x8c))return 70+i;
    }
    /* Live spawn integration must not overwrite the decoded point later. */
    for(i=0;i<4;i++){
        BlFighter *f;unsigned char actor=(unsigned char)(i/2+1),alternate=(unsigned char)(i&1);
        bl_combat_reset(&w);bl_progress_reset(&p);bl_progress_inspect_room(&p,&w,7);
        for(j=0;j<2;j++){w.enemy[j].active=0;w.enemy[j].respawn=200;}
        f=&w.enemy[actor-1];f->respawn=1;
        bl_c64_test_write(0x16,0x20);bl_c64_test_write(0x17,0x60);
        bl_c64_test_write(0x6021+3-actor,255);bl_c64_test_write(0x6022+3-actor,alternate?1:0);
        bl_combat_spawn_service(&w);
        if(!f->active || bl_x(&f->body)!=(alternate?38:32) || bl_y(&f->body)!=(alternate?116:68))return 80+i;
    }
    return 0;
}
#endif
''',encoding='ascii')
    files=['core/combat.c','core/c64_rooms.c','core/c64_rooms.h','core/rooms.c','core/c64_room_data.h','core/c64_room_programs.h',
        'tools/build_c64_rooms.py','tests/bombs_entry_bridge.c','tests/bombs_entry_fixture.h','tools/audit_bombs_entry.py','test-bombs-entry.ps1']
    report=dict(status='passed_actual6502_entry_bomb_and_hazard_controls',source_sha256=SHA,edition_verified=False,
        natural_playthrough=False,full_actor_parity=False,entry_controls=entries,arm_controls=contacts,death_controls=deaths,
        npc_hazard_controls=hazards,npc_blast_contacts=blast_contacts,source_files=[artifact(p) for p in files],native_added_controls=len(native)+12,
        limits=['Original memory reader used; full IRQ/caller/read order still incomplete, no new RNG distribution',
            'Fixtures inject positions and prior states, not natural source play','NPC entry animations/timers and complete object/AI dispatch remain partial'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {len(entries)} original entry choices,3 source bomb contacts,3x16 death updates,{len(hazards)} NPC hazard branches')
if __name__=='__main__':main()
