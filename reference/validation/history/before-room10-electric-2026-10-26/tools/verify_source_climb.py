"""Source net movement: actual6502 dispatch, contacts and sequential inputs.

Controlled source actor states and playfield fixtures, not natural playthrough.
The baseline USS supplies the room/symptom; original bytes supply the rules.
"""
from pathlib import Path
import ctypes
import hashlib
import itertools
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from c64_room_model import oracle_contact
from verify_source_movement import Actor,FIELDS,invoke
from build_fighter_dma import pack,unpack

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference/analysis/climb-audit-2026-10-25'
SOURCE=ROOT/'.reference/c64/work/untrained-memory.bin'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'


def artifact(p):
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def setup(dll,source,room,x,y,state=0,facing=0):
    dll.bl_climb_prepare(room,x,y,state,facing)
    m=[dll.bl_c64_read(i) for i in range(65536)]
    # Restore absent instruction bytes, preserving actual native source room
    # data, original masks and room-specific mutations.
    m[0x500:0x4300]=source[0x500:0x4300]
    m[0x5000:0x5800]=source[0x5000:0x5800]
    m[0x95:0x98]=[1,0,0];m[0x9e]=(x+24)//2;m[0xa1]=y;m[0xa4]=facing
    m[0xbf]=m[0xc2]=m[0xce]=m[0x106]=m[0x4fdb]=m[0xc8]=0;m[0xcb]=6
    m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0,0x3e:0xb8}[m[0xf2]]
    m[0x4f4e]=m[0x4f48]=2
    for i in range(132):m[0x4f57+i]=0
    return m


def raw_input(input):
    return 15^((1 if input&4 else 0)|(2 if input&8 else 0)|
               (4 if input&1 else 0)|(8 if input&2 else 0))


def ready_cases(dll,source):
    fixtures=[];seen=set();count=0
    for previous,animation,input,fire,xy,flags in itertools.product(
        range(5),(0,3,4,6),range(16),(0,1),((12,45),(13,46),(80,120),(162,198),(163,199)),(4,5,6,7)):
        px,py=xy
        a=Actor(x=px,y=py,facing=1,state=previous,counter=0,previous=previous,
                animation=animation,wait=0,pose_lock=0)
        initial=[getattr(a,k) for k in FIELDS]
        m=list(source)
        for field,address in FIELDS.items():m[address]=getattr(a,field)
        m[0x95]=1;m[0xb6]=flags;m[0xc8]=0;m[0x98]=raw_input(input);m[0x9b]=0 if fire else 1
        m[0x4f48]=10;m[0x4f4e]=10
        cpu=MPU(memory=m,pc=0x1dca);cpu.x=0;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
        source_sound=0
        for _ in range(20000):
            if cpu.pc==0xffff:break
            if cpu.pc==0x1fc4:source_sound+=1
            cpu.step()
        else:raise AssertionError('source net dispatch escaped')
        # Source calls the sound helper only for accepted direction entries.
        sound=dll.bl_source_climb_step(ctypes.byref(a),input,fire)
        assert sound==source_sound,('sound',input,xy,sound,source_sound)
        expected=[m[address] for address in FIELDS.values()]
        actual=[getattr(a,k) for k in FIELDS]
        assert actual==expected,('ready',initial,input,fire,flags,actual,expected)
        invoke(m,0x2780)
        pose=dll.bl_source_climb_pose(ctypes.byref(a),10)
        assert pose==m[0x4f4e],('pose',input,previous,animation,actual,pose,m[0x4f4e])
        count+=1
        # One example for each direction/fire/acceleration/state combination;
        # also retain boundary examples with no full-body displacement.
        key=(input,fire,animation==0,previous) if px==80 and flags==4 else None
        if key is not None and key not in seen and input in (1,2,4,8,5) and animation in (0,4):
            seen.add(key);fixtures.append(dict(input=initial,direction=input,fire=fire,expected=expected,pose=pose,sound=sound))
    return count,fixtures


def trajectory(dll,source,room,x,y,inputs,label,uniform=None):
    m=setup(dll,source,room,x,y);rows=[]
    if uniform:
        # Controlled solid net with a vertical right edge, not a natural room.
        dll.bl_c64_test_write.argtypes=[ctypes.c_long,ctypes.c_long]
        for cell in range(1000):
            code=6 if cell%40<20 or uniform=='full' else 0
            for address,value in ((0x8c00+cell,code),(0xd800+cell,14)):
                m[address]=value;dll.bl_c64_test_write(address,value)
        for i in range(8):
            for address,value in ((0xa000+i,0),(0xa030+i,255)):
                m[address]=value;dll.bl_c64_test_write(address,value)
    for step,input in enumerate(inputs):
        px,py=m[0x9e]*2-24,m[0xa1]
        flags,body=oracle_contact(m,px,py,m[0x4f4e])
        m[0xb6]=flags;m[0xa7]=body;m[0x98]=raw_input(input);m[0x9b]=0 if input&16 else 1
        invoke(m,0x1c5b);invoke(m,0x2780)
        dll.bl_climb_run(input)
        a=[dll.bl_climb_read(i) for i in range(17)]
        expected=[m[0x9e]*2-24,m[0xa1],m[0xa4],m[0x106],m[0xcb],m[0xc2],m[0x4f4e]]
        actual=[a[i] for i in (0,1,3,4,6,7,8)]
        assert actual==expected,(label,step,input,flags,actual,expected,m[0xbf],m[0xce])
        rows.append(dict(step=step,input=input,contact_before=flags,after=expected,
                         source_state=m[0xbf],source_counter=m[0xce]))
    return dict(label=label,room=room,x=x,y=y,steps=rows)


def native_fixtures(fixtures,traces):
    # Bounded native contracts: source dispatch edge cases and ordinary room5
    # movement/contact sequences. Avoid injecting the user's OS/RAM image.
    fixtures=fixtures[:100]
    arr=lambda xs:'{'+','.join(str(v) for v in xs)+'}'
    vectors=[f['input']+[f['direction'],f['fire']]+f['expected']+[f['pose'],f['sound']] for f in fixtures]
    step_rows=[]
    chosen=[t for t in traces if t['label'] in ('r05-up-x172','r05-up-x148','r05-horizontal-turns')]
    starts=[]
    for t in chosen:
        starts.append((sum(len(s['steps']) for s in chosen[:len(starts)]),len(t['steps']),t['room'],t['x'],t['y']))
        for row in t['steps']:step_rows.append([row['input']]+row['after'])
    steps=sum(len(t['steps']) for t in chosen)
    raw=bytes(x for rows in (vectors,step_rows) for row in rows for x in row)
    delta=bytearray()
    for rows,width in ((vectors,22),(step_rows,8)):
        previous=[0]*width
        for row in rows:delta.extend(a^b for a,b in zip(row,previous));previous=row
    packed=pack(delta);assert unpack(packed)==delta
    rebuilt=bytearray(unpack(packed));vector_bytes=len(vectors)*22
    for i in range(22,vector_bytes):rebuilt[i]^=rebuilt[i-22]
    for i in range(vector_bytes+8,len(rebuilt)):rebuilt[i]^=rebuilt[i-8]
    assert rebuilt==raw
    fnv=2166136261
    for value in raw:fnv=((fnv^value)*16777619)&0xffffffff
    lines=['/* GENERATED actual6502 fixtures. Packed data, freed before runtime allocations. */',
           '#include "../core/source_climb.h"','#include "../core/c64_sprites.h"',
           '#if defined(__m68k__)','#include <exec/memory.h>','#include <proto/exec.h>',
           '#define BL_CLIMB_ALLOC(n) AllocMem((n),MEMF_PUBLIC)',
           '#define BL_CLIMB_FREE(p,n) FreeMem((p),(n))','#else','#include <stdlib.h>',
           '#define BL_CLIMB_ALLOC(n) malloc(n)','#define BL_CLIMB_FREE(p,n) free(p)','#endif',
           f'#define BL_CLIMB_DISPATCH_CASES {len(fixtures)}',
           f'#define BL_CLIMB_VECTOR_BYTES {vector_bytes}',f'#define BL_CLIMB_RAW_BYTES {len(raw)}',
           f'#define BL_CLIMB_RAW_FNV {fnv}UL',
           'static const unsigned char source_climb_packed[]={'+','.join(str(v) for v in packed)+'};',
           'static const signed short source_climb_starts[][5]={'+','.join(arr(s) for s in starts)+'};',
            f'#define BL_CLIMB_FIXTURE_CASES {len(fixtures)+steps+2}',
            r'''static unsigned short climb_fixture_data(const unsigned char *raw){
    unsigned short i,j,at;BlSourceActor a;BlGame g;BlFighter f;BlC64Sprite visual;
    for(i=0;i<BL_CLIMB_DISPATCH_CASES;i++){
        const unsigned char *v=raw+i*22;
        for(j=0;j<9;j++)((unsigned char*)&a)[j]=v[j];
        if(bl_source_climb_step(&a,v[9],v[10])!=v[21])return i+1;
        for(j=0;j<9;j++)if(((unsigned char*)&a)[j]!=v[11+j])return i+1;
        if(bl_source_climb_pose(&a,10)!=v[20])return i+1;
    }
    for(i=0;i<sizeof(source_climb_starts)/sizeof(source_climb_starts[0]);i++){
        const signed short *s=source_climb_starts[i];
        bl_c64_reset();bl_c64_load(s[2]);bl_reset(&g);g.room=(unsigned char)s[2];
        g.x=(BlCoord)(s[3]*16);g.y=(BlCoord)(s[4]*16);g.facing=0;
        for(j=0;j<s[1];j++){
            const unsigned char *v=raw+BL_CLIMB_VECTOR_BYTES+(s[0]+j)*8;at=(unsigned short)(BL_CLIMB_DISPATCH_CASES+s[0]+j+1);
            bl_step(&g,(unsigned char)v[0]);
            if(bl_x(&g)!=v[1]||bl_y(&g)!=v[2]||g.facing!=v[3]||g.climb_wait!=v[4]||
               g.wall.animation!=v[5]||g.wall.previous!=v[6]||bl_c64_object_pose(&g)!=v[7])return at;
        }
    }
    /* Net display/contact must not hide the existing prone/reaction states.
     * Pose66=source26/facing1; pose58=source19/counter9/facing1. */
    bl_reset(&f.body);f.active=1;f.sai=0;f.timer=0;
    f.body.state=BL_CLIMB;f.body.wall.pose=10;f.body.prone=1;f.body.facing=1;
    f.reaction=BL_REACTION_DOWN;f.stun=9;
    visual.initialized=0;
    if(bl_c64_object_pose(&f.body)!=66)return BL_CLIMB_FIXTURE_CASES-1;
    bl_c64_sprite_step(&visual,&f,2);
    if(visual.pose!=58)return BL_CLIMB_FIXTURE_CASES;
    return 0;
}
static unsigned short climb_fixture_run(void){
    unsigned char *raw=BL_CLIMB_ALLOC(BL_CLIMB_RAW_BYTES),*dest=raw,count;
    const unsigned char *source=source_climb_packed;
    unsigned short i,distance,result=65535;unsigned long hash=2166136261UL;
    if(!raw)return result;
    while((count=*source++)!=128){
        if(!count){distance=(unsigned short)((source[0]<<8)|source[1]);count=source[2];source+=3;
            if(!distance || distance>dest-raw || dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--){*dest=*(dest-distance);++dest;}
        }else if(count&128){count&=127;if(dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--)*dest++=*source++;
        }else{unsigned char value=*source++;if(dest+count>raw+BL_CLIMB_RAW_BYTES)goto done;
            while(count--)*dest++=value;}
    }
    if(dest!=raw+BL_CLIMB_RAW_BYTES)goto done;
    for(i=22;i<BL_CLIMB_VECTOR_BYTES;i++)raw[i]^=raw[i-22];
    for(i=BL_CLIMB_VECTOR_BYTES+8;i<BL_CLIMB_RAW_BYTES;i++)raw[i]^=raw[i-8];
    for(i=0;i<BL_CLIMB_RAW_BYTES;i++)hash=((hash^raw[i])*16777619UL)&0xffffffffUL;
    if(hash!=BL_CLIMB_RAW_FNV)goto done;
    result=climb_fixture_data(raw);
done:
    BL_CLIMB_FREE(raw,BL_CLIMB_RAW_BYTES);return result;
}
#undef BL_CLIMB_ALLOC
#undef BL_CLIMB_FREE''']
    header=ROOT/'tests/climb_fixture.h';header.write_text('\n'.join(lines)+'\n')
    return dict(**artifact(header),cases=len(fixtures)+steps+2,dispatch=len(fixtures),sequential=steps,projection_checks=2,
                raw_bytes=len(raw),packed_bytes=len(packed),native_raw_fnv=fnv,temporary_storage_freed=True)


def main():
    source=SOURCE.read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
    dll=ctypes.CDLL(str(ROOT/'.tmp/source-climb-test/climb.dll'))
    dll.bl_climb_prepare.argtypes=[ctypes.c_long]*5
    dll.bl_climb_run.argtypes=[ctypes.c_long]
    dll.bl_climb_read.argtypes=[ctypes.c_long];dll.bl_climb_read.restype=ctypes.c_long
    dll.bl_c64_read.argtypes=[ctypes.c_long];dll.bl_c64_read.restype=ctypes.c_ubyte
    dll.bl_source_climb_step.argtypes=[ctypes.POINTER(Actor),ctypes.c_long,ctypes.c_long]
    dll.bl_source_climb_step.restype=ctypes.c_long
    dll.bl_source_climb_pose.argtypes=[ctypes.POINTER(Actor),ctypes.c_long];dll.bl_source_climb_pose.restype=ctypes.c_ubyte
    count,fixtures=ready_cases(dll,source)
    traces=[]
    for x in (132,140,148,156,164,172):
        traces.append(trajectory(dll,source,4,x,179,[4]*120,f'r05-up-x{x}'))
    # Vertical reversals and side reversals while wholly on source class4.
    traces.append(trajectory(dll,source,4,148,150,[4]*12+[8]*12+[4]*12,'r05-vertical-turns'))
    traces.append(trajectory(dll,source,4,148,150,([2]*3+[1]*3)*8,'r05-horizontal-turns'))
    traces.append(trajectory(dll,source,0,148,130,[2]*30,'controlled-net-exit','edge'))
    traces.append(trajectory(dll,source,0,148,48,[4]*20,'controlled-net-top','full'))
    traces.append(trajectory(dll,source,0,148,197,[8]*12,'controlled-net-bottom','full'))
    native=native_fixtures(fixtures,traces)
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));text=[]
    for lo,hi in ((0x1c5b,0x1cc7),(0x1dca,0x1fc4),(0x2780,0x29c3),(0x4a8c,0x4aa8)):
        p=lo
        while p<hi:
            n,t=dis.instruction_at(p);text.append(f'${p:04X} {source[p:p+n].hex(" "):8} {t}');p+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(text)+'\n')
    report=dict(status='passed_source_net_dispatch_and_sequential_contact',source_sha256=SHA,
                edition_verified=False,natural_playthrough=False,full_actor_fsm_ported=False,
                dispatch_cases=count,sequential_steps=sum(len(t['steps']) for t in traces),
                traces=traces,native_fixture=native,
                source_files=[artifact(ROOT/p) for p in ('core/game.c','core/game.h','core/source_wall.c','core/source_wall.h','core/source_climb.c','core/source_climb.h','core/c64_rooms.c','core/c64_rooms.h','core/c64_room_data.h','core/c64_room_programs.h','tests/climb_bridge.c','tools/verify_source_climb.py','test-source-climb.ps1')])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {count} actual6502 net dispatch cases; {report["sequential_steps"]} contact/history/pose steps; {native["cases"]} native fixtures')


if __name__=='__main__':main()
