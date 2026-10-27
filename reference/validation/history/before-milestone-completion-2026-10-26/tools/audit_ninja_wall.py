"""Controlled $1C5B/$2780/$29C3 checks, not natural VIC/raster play."""
import ctypes,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from build_c64_sprites import source_frame,SHA
from audit_c64_tests import actor,combat
from audit_session_walls import run
from c64_room_model import oracle_contact
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
OUT=ROOT/'reference/analysis/ninja-wall-2026-10-26'
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def occupied(source,who,pose,face):
    pixels,_=source_frame(source,who,pose,face)
    return {(i%48-16,i//48-22) for i,p in enumerate(pixels) if p is not None}
def fnv(data):
    h=2166136261
    for b in data:h=((h^b)*16777619)&0xffffffff
    return h
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/ninja-wall-test/ninja.dll'))
    for name,n in [('prepare',5),('read',1),('touch',6),('hit',6),('chain',2)]:
        f=getattr(d,'bl_ninja_'+name);f.argtypes=[ctypes.c_long]*n;f.restype=ctypes.c_long
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    rows=[];native=[]
    for facing in (0,1):
        for x in (188,220,234,254):
            for counter in (19,12,11,8,7,2,1):
                seed=1;d.bl_ninja_prepare(x,196,facing,counter,seed)
                m=[d.bl_c64_read(i) for i in range(65536)]
                m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
                m[0x95:0x98]=[0,0,0x41];m[0xa0]=(x+24)//2;m[0xa3]=196;m[0xa6]=facing
                m[0xc1]=m[0xc4]=22;m[0xd0]=counter;m[0xcd]=6;m[0x108]=m[0x4fdd]=m[0xc8]=0
                m[0x88]=m[0x40]=m[0x42ca]=m[0x87]=0;m[0x7c]=0xa0
                m[0x4f57:0x4fdb]=[0]*132;m[0x4f57+3*(3 if facing else 2)+2]=seed
                pose=(52 if counter>=11 else 54) if facing else (48 if counter>=11 else 50)
                m[0x4f4a]=pose;m[0x4f50]=pose+140;m[0xd6]=source[0x5cbf+pose+140];m[0xd9]=source[0x5cc0+pose+140]
                flags,body=oracle_contact(m,x,196,pose+140);m[0xb8]=flags;m[0xa9]=body
                cpu,_=run(m,0x1c5b,2,stops=(0xffff,0x2f8e));assert cpu.pc==0xffff
                run(m,0x2780,2);d.bl_ninja_step()
                expected=[m[0xa0]*2-24,m[0xa3],m[0xa6],m[0xc1],m[0xd0] if m[0xc1] else 0,
                    m[0x4f50],flags,m[0xc4],m[0xcd]]
                history=[m[0x4f57+12*i+3*j+2] for i in range(11) for j in range(4)]
                actual=[d.bl_ninja_read(i) for i in range(53)]
                assert actual==expected+history,(x,facing,counter,actual,expected+history)
                rows.append(dict(x=x,y=196,facing=facing,counter=counter,seed=seed,contact=flags,
                    after=expected,history=history))
                native.append([x,facing,counter,seed,*expected[:7],fnv(history)])
    # Hardware occupancy is independently checked against executed $2584/$25E2
    # composites, including opaque black and both positional directions.
    shapes={(a,p,f):occupied(source,a,p,f) for a in (0,1,2) for p in range(0,70,2) for f in (0,1)}
    rng=random.Random(0x29c3);touch_checks=0
    for p in range(0,70,2):
        for f in (0,1):
            for q in range(0,70,2):
                tf=q&2!=0;dx=rng.randrange(-24,25)*2;dy=rng.randrange(-22,23)
                expected=bool(shapes[2,p,f]&{(x+dx,y+dy) for x,y in shapes[0,q,int(tf)]})
                assert bool(d.bl_ninja_touch(p,f,q,int(tf),dx,dy))==expected,(p,f,q,tf,dx,dy)
                touch_checks+=1
    hit_checks=0;hits=[]
    for face in (0,1):
        for counter in (0,1,7,8,12,19):
            for state in (0,17,26,14,1):
                for tf in (0,1):
                    pose=(66 if tf else 64) if state==26 else (6 if tf else 4) if state==17 else 68 if state==14 else 10 if state==1 else 2 if tf else 0
                    kp=(52 if counter>=11 else 54) if face else (48 if counter>=11 else 50)
                    for forward in (6,8,12,18,20,22,24,28,32):
                        dx=forward if face else -forward;dy=0
                        overlap=bool(shapes[2,kp,face]&{(x+dx,y+dy) for x,y in shapes[0,pose,tf]})
                        latch=0x11 if overlap else 0
                        actors=[actor((160+dx+24)//2,150,state,tf,1),actor(30,80),actor(92,150,22,face,counter,7)]
                        result=combat('ninja',actors,latch)
                        expected=36-result['after']['health'][0]
                        actual=d.bl_ninja_hit(face,counter,dx,dy,state,tf)
                        assert actual==expected,(face,counter,dx,state,tf,actual,expected)
                        hits.append([face,counter,dx,dy,state,tf,expected]);hit_checks+=1
    # The old box reports damage at22px against the facing-towards idle
    # Bruce; actual source component pixels do not overlap in either direction.
    for face in (0,1):
        assert d.bl_ninja_hit(face,7,22 if face else -22,0,0,1-face)==0
        assert d.bl_ninja_hit(face,7,20 if face else -20,0,0,1-face)==2
    chains=[]
    for bx in (180,194,196,198,202):
        for yx in (180,182,184,220):
            positions=[bx,yx,160];poses=[0,0,54];faces=[0,0,1];groups=[3,12,16];latch=0
            parts=[{(x+positions[a],y) for x,y in shapes[a,poses[a],faces[a]]} for a in range(3)]
            for a in range(3):
                for v in range(a):
                    if parts[a]&parts[v]:latch|=groups[a]|groups[v]
            result=combat('aggregate-chain',[actor((bx+24)//2,150,facing=0),actor((yx+24)//2,150,facing=0),actor(92,150,22,1,7,36)],latch)
            expected=36-result['after']['health'][0]
            assert d.bl_ninja_chain(bx,yx)==expected,(bx,yx,latch,expected)
            chains.append(dict(bruce_x=bx,yamo_x=yx,latch=latch,direct_ninja_bruce=bool(parts[2]&parts[0]),damage=expected))
    assert any(c['damage'] and not c['direct_ninja_bruce'] for c in chains)
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for a,end in [(0x22bd,0x22f3),(0x29c3,0x2aa5),(0x2c54,0x2c70)]:
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {source[a:a+n].hex(" "):8} {t}');a+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    header=ROOT/'tests/ninja_wall_fixture.h'
    native_hits=[row for row in hits if row[1] in (7,8) and abs(row[2]) in (8,20,22,28) and row[4] in (0,17,26)]
    header.write_text('/* Generated from controlled original6502 calls; not natural play. */\n'+
        '#ifndef BRUCE_NINJA_WALL_FIXTURE_H\n#define BRUCE_NINJA_WALL_FIXTURE_H\n'+
        '#include "../core/combat.h"\n#include "../core/c64_rooms.h"\n'+
        'static const long ninja_wall_cases[][12]={\n'+',\n'.join('{'+','.join(str(v)+('UL' if j==11 else '') for j,v in enumerate(row))+'}' for row in native)+'\n};\n'+
        'static const short ninja_hit_cases[][7]={\n'+',\n'.join('{'+','.join(map(str,row))+'}' for row in native_hits)+ '\n};\n'+
        '''static unsigned short ninja_wall_fixture_run(void){
    BlGame g;unsigned short i,j;unsigned long h;
    bl_c64_reset();bl_c64_load(5);
    for(i=0;i<sizeof(ninja_wall_cases)/sizeof(ninja_wall_cases[0]);i++){
        const long *c=ninja_wall_cases[i];unsigned char state,counter;
        bl_reset(&g);g.room=5;g.source_actor=2;g.x=(BlCoord)(c[0]*16);g.y=196*16;
        g.facing=(unsigned char)c[1];g.attack=BL_SAI;g.attack_phase=(unsigned char)c[2];
        g.wall.previous=22;g.wall.animation=6;g.wall.tracked=1;g.wall.moves[0][g.facing?3:2]=(unsigned char)c[3];
        bl_step_npc(&g,0);state=(unsigned char)(g.wall.state==24?24:g.attack==BL_SAI?22:0);
        counter=(unsigned char)(state==24?g.wall.counter:g.attack_phase);
        h=2166136261UL;for(j=0;j<44;j++)h=(h^g.wall.moves[j/4][j%4])*16777619UL;
        if(bl_x(&g)!=c[4] || bl_y(&g)!=c[5] || g.facing!=c[6] || state!=c[7] ||
           counter!=c[8] || bl_c64_object_pose(&g)!=c[9] || g.wall.contact!=c[10] || h!=(unsigned long)c[11])return i+1;
    }
    for(i=0;i<sizeof(ninja_hit_cases)/sizeof(ninja_hit_cases[0]);i++){
        const short *c=ninja_hit_cases[i];BlFighter a={0},b={0};
        bl_reset(&a.body);bl_reset(&b.body);a.body.source_actor=2;a.body.room=b.body.room=5;
        a.body.x=160*16;b.body.x=(BlCoord)((160+c[2])*16);a.body.y=b.body.y=150*16;
        a.body.facing=(unsigned char)c[0];b.body.facing=(unsigned char)c[5];
        a.active=b.active=1;a.health=b.health=36;a.stun=b.stun=0;a.reaction=b.reaction=0;
        a.sai=1;b.sai=0;a.timer=(unsigned char)c[1];a.body.attack=BL_SAI;a.body.attack_phase=a.timer;
        if(c[4]==17){b.body.attack=BL_PUNCH;b.body.attack_phase=1;}
        if(c[4]==26)b.body.prone=1;
        if(c[4]==14){b.body.state=BL_AIR;b.body.jump_phase=255;}
        if(c[4]==1){b.body.state=BL_CLIMB;b.body.climb_state=1;b.body.wall.pose=10;}
        if(bl_combat_contact(&a,&b,1)!=c[6])return 100+i;
    }
    return 0;
}
#endif
''',encoding='ascii')
    paths=['core/game.c','core/game.h','core/combat.c','core/combat.h','core/source_wall.c','core/source_wall.h',
        'core/c64_rooms.c','core/c64_rooms.h','core/c64_hit_data.h','tools/build_c64_hit_masks.py',
        'tools/build_c64_sprites.py','tools/audit_ninja_wall.py','tests/ninja_wall_bridge.c','tests/ninja_wall_fixture.h','test-ninja-wall.ps1']
    report=dict(source_sha256=SHA,status='passed_controlled_source_stab_wall_and_sprite_checks',edition_verified=False,
        natural_playthrough=False,full_combat_parity=False,wall_controls=rows,occupancy_checks=touch_checks,
        source_combat_checks=hit_checks,source_files=[artifact(p) for p in paths],native_wall_cases=len(native),
        native_hit_cases=len(native_hits),aggregate_controls=chains,limits=['Current actor-pose bridge and sequential pair application remain incomplete',
            'Sprite geometry is from executed writer; D01E inputs are calculated/injected, not a VIC raster capture',
            'State22 idle wait clock/mode and complete actor FSM remain open','No new wall line-of-sight rule'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {len(rows)} original6502 wall/history entries,{touch_checks} sprite checks,{hit_checks} source combat entries')
if __name__=='__main__':main()
