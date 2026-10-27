"""Original-byte controls for death/lives and R06 jump/wall regressions.

Original USS is inspected read-only. CPU cases use injected states and real
room glyphs; they are not a recording of natural C64 play.
"""
from pathlib import Path
import ctypes, hashlib, json, struct, sys, zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.reference/tools/python'),str(ROOT/'tools')]
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from c64_room_model import oracle_contact
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
OUT=ROOT/'reference/analysis/session-walls-2026-10-25'

def run(m,entry,actor=0,stops=(0xffff,)):
    cpu=MPU(memory=m,pc=entry);cpu.x=actor;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
    for n in range(100000):
        if cpu.pc in stops:return cpu,n
        cpu.step()
    raise AssertionError(('unfinished',hex(cpu.pc)))

def snapshot(source):
    path=ROOT/'.tmp/25.10.2026II.uss'
    if not path.exists():return dict(status='local_snapshot_not_installed')
    data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();at=0;chunks={}
    assert data[:4]==b'ASF '
    while at+12<=len(data):
        tag=data[at:at+4];size,flags=struct.unpack_from('>II',data,at+4)
        if tag==b'END ':break
        assert size>=12 and at+size<=len(data)
        raw=data[at+12:at+size]
        if tag in (b'CRAM',b'BRAM'):
            if flags&1:
                expected=struct.unpack_from('>I',raw)[0];decoder=zlib.decompressobj()
                raw=decoder.decompress(raw[4:])+decoder.flush()
                assert decoder.eof and not decoder.unused_data and len(raw)==expected
            assert len(raw)==524288
            chunks[tag]=raw
        at+=size+4-size%4
    slow=chunks[b'BRAM'];at=0;found=[]
    while True:
        p=slow.find(source[0x1167:0x1187],at)
        if p<0:break
        at=p+1;base=p-0x1167
        if 0<=base<=len(slow)-65536:
            m=slow[base:base+65536]
            if m[0x29]<20 and 12<=m[0x9e]<=163 and 45<=m[0xa1]<=199 and m[0xf2] in (0x38,0x3a,0x3c,0x3e):
                found.append((base,m))
    assert len(found)==1
    base,m=found[0];assert m[0x29]==5
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest,unchanged=True,
                room=6,source_ram_address=f'${base+0xc00000:06X}',
                room_tick_anchor=[m[0x9e]*2-24,m[0xa1]],
                limitation='Stored Amiga state; no failed input history or natural C64 play is inferred')

def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    dll=ctypes.CDLL(str(ROOT/'.tmp/session-test/session.dll'))
    dll.bl_session_contracts.restype=ctypes.c_long
    failure=dll.bl_session_contracts();assert not failure,('session fixture line',failure)
    for name,args in (('bl_audit_prepare',5),('bl_audit_step',2),('bl_audit_read',1),('bl_life_prepare',1),('bl_life_read',1),('bl_c64_read',1)):
        getattr(dll,name).argtypes=[ctypes.c_long]*args
    dll.bl_c64_read.restype=ctypes.c_ubyte
    dll.bl_c64_contact.argtypes=[ctypes.c_long]*4;dll.bl_c64_contact.restype=ctypes.c_ubyte
    life=[]
    for lives in range(10):
        dll.bl_life_prepare(lives)
        m=list(source);m[0xbf]=m[0xc2]=25;m[0xce]=16;m[0x106]=0
        m[0x9e]=26;m[0xa1]=196;m[0x28]=lives;m[0x104]=1
        for step in range(16):
            cpu,n=run(m,0x1c5b,stops=(0xffff,0x1818))
            actual=dll.bl_life_step()
            if step<15:
                assert cpu.pc==0xffff and actual==m[0xce]==15-step
                assert (dll.bl_life_read(3),dll.bl_life_read(4))==(28,196)
            else:
                assert cpu.pc==0x1818
                cpu,n=run(m,0x1826,stops=(0x182a,0x188e))
                expected=m[0x28] if m[0x28]<128 else m[0x28]-256
                assert dll.bl_life_read(0)==expected
                assert bool(dll.bl_life_read(1))==(cpu.pc==0x188e)
            life.append(dict(initial_spare_falls=lives,step=step+1,counter=actual,source_pc=f'${cpu.pc:04X}'))
    defaults=[]
    for human in (0,1):
        m=list(source);m[0x42ca]=human;run(m,0x0fbc,stops=(0x0fc9,))
        assert m[0x28]==(9 if human else 4);defaults.append(dict(human_yamo=human,spare_falls=m[0x28]))
    ports=[];turns=[]
    for player in (0,1):
        for human in (0,1):
            m=list(source);m[3]=player;m[0x42ca]=human;m[0x104]=1
            m[0x1383]=m[0x1384]=1;m[0xdc00]=0x17;m[0xdc01]=0x0e
            run(m,0x16a2,stops=(0x1703,))
            assert m[0x98]==(14 if player==0 else 7) and m[0x9b]==player
            if human:assert m[0x99]==(7 if player==0 else 14) and m[0x9c]==1-player
            ports.append(dict(current_player=player,human_yamo=human,bruce_direction=m[0x98],bruce_fire=m[0x9b],yamo_direction=m[0x99] if human else None))
        for players in (1,2):
            for other_alive in (0,1):
                m=list(source);m[3]=player;m[0x42c9]=players-1;m[0x439f]=0 if other_alive else 255
                run(m,0x183b,stops=(0x184b,))
                assert m[3]==(player^1 if players==2 and other_alive else player)
                turns.append(dict(before=player,players=players,other_alive=bool(other_alive),after=m[3]))
    trajectories=[]
    for px,py,facing in ((44,81,0),(64,78,0),(88,78,0),(44,81,1)):
        dll.bl_audit_prepare(5,px,py,facing,0)
        m=[dll.bl_c64_read(i) for i in range(65536)]
        m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
        m[0x95:0x98]=[1,0,0];m[0x9e]=(px+24)//2;m[0xa1]=py;m[0xa4]=facing
        m[0xbf]=m[0xc2]=m[0xce]=m[0xcb]=m[0x106]=0
        m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0,0x3e:0xb8}[m[0xf2]]
        m[0x4f4e]=2 if facing else 0
        for i in range(132):m[0x4f57+i]=0
        rows=[]
        for step in range(35):
            input=(4|(2 if facing else 1)) if step<16 else 0
            flags,body=oracle_contact(m,m[0x9e]*2-24,m[0xa1],m[0x4f4e])
            m[0xb6]=flags;m[0xa7]=body
            m[0x98]=15^(1 if input&4 else 0)^(8 if input&2 else 0)^(4 if input&1 else 0)
            m[0x9b]=1;m[0xdc00]=255
            cpu,n=run(m,0x1c5b,stops=(0xffff,0x2f8e));assert cpu.pc==0xffff
            run(m,0x2780)
            dll.bl_audit_step(input,0)
            actual=[dll.bl_audit_read(i) for i in range(9)]
            expected=[m[0x9e]*2-24,m[0xa1],m[0xa4]]
            assert actual[:3]==expected,('R06 jump',px,py,facing,step,actual,expected,m[0xbf],m[0xce],flags,body,rows[-3:])
            rows.append(dict(step=step,input=input,source_state=m[0xbf],counter=m[0xce],pose=m[0x4f4e],contact=flags,actual=actual))
        trajectories.append(dict(start=[px,py],facing=facing,steps=rows))
    npc=[]
    for actor in (1,2):
        for px,facing in ((150,1),(60,0)):
            dll.bl_audit_prepare(5,px,196,facing,0)
            m=[dll.bl_c64_read(i) for i in range(65536)]
            m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
            m[0x95:0x98]=[1,0,0];m[0x95+actor]=129 if actor==1 else 65
            m[0x9e]=(302+24)//2 if facing else 12;m[0xa1]=196
            m[0x9e+actor]=(px+24)//2;m[0xa1+actor]=196;m[0xa4+actor]=facing
            # Isolate source retreat gait21 from attack decisions. Both
            # actors must still execute the common black/history prefix.
            m[0xbf+actor]=m[0xc2+actor]=21;m[0xce+actor]=128
            m[0xcb+actor]=6;m[0x106+actor]=0;m[0xd1+actor]=20 if actor==1 else 7
            m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0,0x3e:0xb8}[m[0xf2]]
            m[0x4f48+actor]=2 if facing else 0
            m[0x4f4e+actor]=(2 if facing else 0)+actor*70
            for i in range(132):m[0x4f57+i]=0
            rows=[]
            for step in range(30):
                flags,body=oracle_contact(m,m[0x9e+actor]*2-24,m[0xa1+actor],m[0x4f4e+actor])
                m[0xb6+actor]=flags;m[0xa7+actor]=body
                m[0x98+actor]=7 if facing else 11;m[0x9b+actor]=1;m[0xdc00]=255
                cpu,n=run(m,0x1c5b,actor,stops=(0xffff,0x2f8e))
                assert cpu.pc==0xffff,('NPC emergency re-entry',actor,px,step)
                # Width bytes used by $27C1 after state24. The walking source
                # poses in these controls are single-width for both NPCs.
                pose=m[0x4f4e+actor]
                m[0xd4+actor]=source[0x5cbf+pose];m[0xd7+actor]=source[0x5cc0+pose]
                run(m,0x2780,actor)
                dll.bl_audit_step(2 if facing else 1,actor)
                actual=[dll.bl_audit_read(i) for i in range(9)]
                expected=[m[0x9e+actor]*2-24,m[0xa1+actor],m[0xa4+actor]]
                assert actual[:3]==expected,('NPC wall',actor,px,step,actual,expected,m[0xbf+actor],flags,m[0x4f4e+actor],m[0x4f48+actor],m[0x95+actor],rows[-2:])
                assert actual[5]==m[0x4f4e+actor],('NPC contact pose',actor,step,actual[5],m[0x4f4e+actor])
                rows.append(dict(step=step,contact=flags,source_state=m[0xbf+actor],source_pose=m[0x4f4e+actor],actual=actual))
            assert any(r['contact']&8 for r in rows),'Fixture must exercise a real black wall'
            npc.append(dict(actor=actor,start=[px,196],steps=rows))
    contacts=[]
    for room in range(20):
        dll.bl_audit_prepare(room,0,196,1,0)
        m=[dll.bl_c64_read(i) for i in range(65536)]
        m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
        m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0,0x3e:0xb8}[m[0xf2]]
        for actor in (1,2):
            for base in (0,2,8,14,16,18,20,68):
                for px,py in ((0,81),(186,196),(230,81),(244,174)):
                    pose=actor*70+base;expected=oracle_contact(m,px,py,pose)
                    actual=tuple(dll.bl_c64_contact(px,py,pose,b) for b in (0,1))
                    assert actual==expected,('NPC mask',room,actor,base,px,py,actual,expected)
                    contacts.append([room,px,py,pose,*expected])
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for lo,hi in ((0x0fbc,0x0fc9),(0x16a2,0x1703),(0x1818,0x1891),(0x1c5b,0x1d77),(0x2008,0x217d),(0x2d55,0x2d7c),(0x304b,0x306b),(0x407d,0x4086)):
        at=lo
        while at<hi:
            size,s=dis.instruction_at(at);lines.append(f'{at:04X} {source[at:at+size].hex(" "):<9} {s}');at+=size
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
    # Original-CPU expected coordinates and mask results, also checked on
    # the 68000 test build. These fixture states are intentionally injected.
    lines=['/* Generated original6502 R06 controls; not natural play. */',
        '#ifndef BRUCE_SESSION_WALL_FIXTURE_H','#define BRUCE_SESSION_WALL_FIXTURE_H',
        '#include "../core/game.h"','#include "../core/c64_rooms.h"',
        '#define BL_SESSION_WALL_CASES 324',
        'static const short session_contacts[][6]={']
    selected=[r for r in contacts if r[0] in (0,5) and r[3]%70 in (0,18,20,68)]
    assert len(selected)==64
    lines += ['{'+','.join(map(str,r))+'},' for r in selected]+['};']
    flat=[];starts=[]
    for t in trajectories:
        starts.append([0,*t['start'],t['facing'],len(flat),len(t['steps'])])
        flat += [[r['input'],*r['actual'][:3]] for r in t['steps']]
    for t in npc:
        starts.append([t['actor'],*t['start'],int(t['start'][0]==150),len(flat),len(t['steps'])])
        flat += [[2 if t['start'][0]==150 else 1,*r['actual'][:3]] for r in t['steps']]
    for name,rows in (('session_routes',starts),('session_steps',flat)):
        lines += [f'static const short {name}[][{len(rows[0])}]={{']+['{'+','.join(map(str,r))+'},' for r in rows]+['};']
    lines += ['static unsigned short session_wall_fixture_run(void){',
        'BlGame g;unsigned short i,j,index=0;unsigned char actor;',
        'for(i=0;i<sizeof(session_contacts)/sizeof(session_contacts[0]);i++){',
        'const short *v=session_contacts[i];if(!i || session_contacts[i-1][0]!=v[0]){bl_c64_reset();bl_c64_load(v[0]);}++index;',
        'if(bl_c64_contact(v[1],v[2],v[3],0)!=v[4] || bl_c64_contact(v[1],v[2],v[3],1)!=v[5])return index;}',
        'for(i=0;i<sizeof(session_routes)/sizeof(session_routes[0]);i++){',
        'const short *r=session_routes[i];bl_c64_reset();bl_c64_load(5);bl_reset(&g);g.room=5;',
        'g.x=r[1]*16;g.y=r[2]*16;g.previous_x=g.x;g.previous_y=g.y;g.facing=(unsigned char)r[3];actor=(unsigned char)r[0];g.source_actor=actor;',
        'for(j=0;j<r[5];j++){const short *v=session_steps[r[4]+j];++index;',
        'if(actor)bl_step_npc(&g,(unsigned char)v[0]);else bl_step(&g,(unsigned char)v[0]);',
        'if(bl_x(&g)!=v[1] || bl_y(&g)!=v[2] || g.facing!=v[3])return index;}}',
        'return 0;}','#endif']
    (ROOT/'tests/session_wall_fixture.h').write_text('\n'.join(lines)+'\n')
    report=dict(status='passed_controlled_source_checks',source_sha256=SHA,edition_verified=False,natural_playthrough=False,
        snapshot=snapshot(source),death_steps=life,menu_defaults=defaults,port_controls=ports,turn_controls=turns,room6_trajectories=trajectories,npc_wall_trajectories=npc,npc_contact_cases=contacts,
        native_validation_complete=False,limitations=['Full NPC AI/contact timing remains a separate port','Debug options intentionally override original rules'])
    files=('core/game.c','core/game.h','core/source_wall.c','core/source_wall.h','core/source_climb.c','core/source_climb.h',
        'core/combat.c','core/combat.h','core/rooms.c','core/rooms.h','core/session.c','core/session.h',
        'core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h','core/c64_sprites.c',
        'core/c64_sprites.h','tests/session_fixture.h','tests/session_wall_fixture.h','tests/session_bridge.c',
        'test-session.ps1','tools/audit_session_walls.py','tools/build_c64_rooms.py')
    report['source_files']=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files]
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS session/cheat/two-player contracts, {len(life)} original6502 death/life steps, {sum(len(t["steps"]) for t in trajectories)} R06 jump steps, {sum(len(t["steps"]) for t in npc)} NPC wall steps, {len(contacts)} NPC pixel contacts')

if __name__=='__main__':main()
