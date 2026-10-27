"""Actual6502 black-contact/history branch vs decoded C; injected states."""
from pathlib import Path
import ctypes, hashlib, json, random, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

class Wall(ctypes.Structure):
    _fields_=[('moves',(ctypes.c_ubyte*4)*11)]+[(k,ctypes.c_ubyte) for k in ('state','counter','previous','animation','pose','tracked','contact')]
class Actor(ctypes.Structure):
    _fields_=[(k,ctypes.c_ubyte) for k in ('x','y','facing','state','counter','previous','animation','wait','pose_lock')]
FIELDS=dict(x=0x9e,y=0xa1,facing=0xa4,state=0xbf,counter=0xce,previous=0xc2,animation=0xcb,wait=0x106,pose_lock=0x4fdb)

def invoke(m,entry,stops=(0xffff,)):
    cpu=MPU(memory=m,pc=entry);cpu.x=0;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
    for i in range(100000):
        if cpu.pc in stops:return cpu
        cpu.step()
    raise AssertionError((hex(entry),hex(cpu.pc)))

def kick_controls(dll,source):
    dll.bl_move_prepare.argtypes=[ctypes.c_long]*5;dll.bl_move_read.argtypes=[ctypes.c_long];dll.bl_move_read.restype=ctypes.c_long
    dll.bl_c64_read.argtypes=[ctypes.c_long];dll.bl_c64_read.restype=ctypes.c_ubyte
    rows=[]
    # Fixed room-relative anchors include floors, nets, black glyphs and edges.
    # Their classifications come from $5212, never an invented wall rectangle.
    for room in range(20):
        for px,py in ((0,178),(160,150),(294,98)):
            for facing in (0,1):
                for counter in (12,9,2,1):
                    dll.bl_move_prepare(room,px,py,facing,counter)
                    m=[dll.bl_c64_read(i) for i in range(65536)]
                    m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
                    m[0x95:0x98]=[1,0,0];m[0x9e]=(px+24)//2;m[0xa1]=py;m[0xa4]=facing
                    m[0xbf]=m[0xc2]=13 if facing else 12;m[0xce]=counter;m[0xcb]=m[0x106]=m[0xc8]=0
                    m[0x98]=15;m[0x9b]=1;m[0x7c]={0x38:0xa0,0x3a:0xa8,0x3c:0xb0}[m[0xf2]]
                    m[0x4fdb]=0;invoke(m,0x2780)
                    pose=m[0x4f4e];assert pose==dll.bl_move_read(7)
                    m[0xd4]=source[0x5cbf+pose];m[0xd7]=source[0x5cc0+pose]
                    invoke(m,0x5212,(0x52ac,));flags=m[0xb6]
                    for i in range(132):m[0x4f57+i]=0
                    cpu=invoke(m,0x1c5b,(0xffff,0x2f8e));assert cpu.pc==0xffff
                    invoke(m,0x2780)
                    dll.bl_move_run()
                    actual=[dll.bl_move_read(i) for i in range(8)]
                    expected=[m[0x9e]*2-24,m[0xa1],m[0xa4],2 if m[0xbf] in (12,13) else 0,
                              m[0xce] if m[0xbf] in (12,13) else 12,
                              24 if m[0xbf]==24 else 0,m[0xce] if m[0xbf]==24 else 0]
                    assert actual[:7]==expected,(room+1,px,py,facing,counter,flags,actual,expected,m[0xbf])
                    if m[0xbf] in (12,13,24):assert actual[7]==m[0x4f4e],('pose',room+1,px,py,counter,actual[7],m[0x4f4e])
                    history=[m[0x4f57+i*12+d*3] for i in range(11) for d in range(4)]
                    assert [dll.bl_move_read(i) for i in range(8,52)]==history,('kick history',room+1,px,py,counter)
                    rows.append(dict(room=room+1,x=px,y=py,facing=facing,counter=counter,contact=flags,
                                     after=actual,source_state=m[0xbf],source_pose=m[0x4f4e]))
    return rows

def jump_controls(dll,source):
    dll.bl_jump_prepare.argtypes=[ctypes.c_long];dll.bl_jump_run.argtypes=[ctypes.c_long]
    results=[]
    for direction in (-1,0,1):
        dll.bl_jump_prepare(direction)
        m=[dll.bl_c64_read(i) for i in range(65536)]
        m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
        m[0x95:0x98]=[1,0,0];m[0x9e]=72;m[0xa1]=130;m[0xa4]=int(direction>=0)
        m[0xbf]=m[0xc2]=6 if direction<0 else 7 if direction>0 else 5;m[0xce]=15
        m[0xcb]=m[0x106]=m[0xc8]=0;m[0x98]=7 if direction<0 else 11;m[0x9b]=1;m[0x7c]=0xa0
        for i in range(132):m[0x4f57+i]=0
        for frame in range(18):
            m[0x4fdb]=0;invoke(m,0x2780)
            assert dll.bl_move_read(7)==m[0x4f4e],('jump pose',direction,frame,dll.bl_move_read(7),m[0x4f4e])
            invoke(m,0x5212,(0x52ac,));assert m[0xb6]==0
            invoke(m,0x1c5b)
            dll.bl_jump_run(2 if direction<0 else 1)
            actual=[dll.bl_move_read(i) for i in (0,1,2)]
            expected=[m[0x9e]*2-24,m[0xa1],m[0xa4]]
            assert actual==expected,('jump step',direction,frame,actual,expected,m[0xbf],m[0xce])
            results.append(dict(direction=direction,frame=frame,after=actual,source_state=m[0xbf],counter=m[0xce],pose_before=m[0x4f4e]))
    return results

def native_fixtures(results,kick,jump):
    # Small original-CPU-derived vectors for the constrained A500 test build.
    selected=[0,1,2,3,24,25]
    for condition in (lambda r:r['dispatch']==2,lambda r:r['input']['state']==24 and r['after']['counter']==0):
        selected.append(next(i for i,r in enumerate(results) if condition(r) and i not in selected))
    ks=[]
    for predicate in (lambda r:r['source_state']==24,lambda r:r['contact']&4,
                      lambda r:r['counter']==1 and r['source_state']==0,lambda r:not r['contact']):
        for facing in (0,1):
            ks.append(next(r for r in kick if predicate(r) and r['facing']==facing))
    flat=lambda rows:[x for row in rows for x in row]
    arr=lambda xs:'{'+','.join(str(v) for v in xs)+'}'
    fields=list(FIELDS)
    lines=['/* GENERATED after actual6502 comparison. Injected fixtures, not natural play. */',
           '#ifndef BRUCE_MOVEMENT_FIXTURE_H','#define BRUCE_MOVEMENT_FIXTURE_H',
           '#include "../core/game.h"','#include "../core/c64_rooms.h"',
           'typedef struct {BlSourceActor input,expected;unsigned char before[44],after[44],flags,result;} BlWallVector;',
           'static const BlWallVector source_wall_vectors[8]={']
    for i in selected:
        r=results[i]
        # Expected history comes from the original bytes after the step.
        h=r['history'];a=Actor(**r['input']);w=Wall()
        for n,row in enumerate(h):w.moves[n][:]=row
        m=list((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes());m[0xb6]=r['contact'];m[0x29]=0
        for k,address in FIELDS.items():m[address]=r['input'][k]
        for n,row in enumerate(h):
            for d,value in enumerate(row):m[0x4f57+n*12+d*3]=value
        invoke(m,0x1c5b,(0xffff,0x1d6f,0x2f8e))
        after=[m[0x4f57+n*12+d*3] for n in range(11) for d in range(4)]
        lines.append('{'+','.join((arr(r['input'][k] for k in fields),arr(m[a] for a in FIELDS.values()),arr(flat(h)),arr(after),str(r['contact']),str(r['dispatch'])))+'},')
    lines+=['};','static const signed short source_kick_vectors[8][14]={']
    for r in ks:
        lines.append(arr([r['room']-1,r['x'],r['y'],r['facing'],r['counter']]+r['after'][:7]+[r['source_state'],r['source_pose']])+',')
    lines+=['};','static const signed short source_jump_vectors[54][4]={']
    for r in jump:lines.append(arr(r['after']+[r['pose_before']])+',')
    lines+=['};','#define BL_MOVEMENT_CASE_COUNT 70',r'''
static unsigned short movement_fixture_run(void){
    unsigned short i,j,k;BlGame g;BlSourceActor a;BlSourceWall w;
    for(i=0;i<8;i++){
        const BlWallVector *v=&source_wall_vectors[i];
        bl_source_wall_reset(&w);a=v->input;
        for(j=0;j<44;j++)w.moves[j/4][j%4]=v->before[j];
        if(bl_source_wall_step(&w,&a,v->flags)!=v->result)return (unsigned short)(i+1);
        for(j=0;j<sizeof(a);j++)if(((unsigned char*)&a)[j]!=((const unsigned char*)&v->expected)[j])return (unsigned short)(i+1);
        for(j=0;j<44;j++)if(w.moves[j/4][j%4]!=v->after[j])return (unsigned short)(i+1);
    }
    for(i=0;i<8;i++){
        const signed short *v=source_kick_vectors[i];
        bl_c64_reset();bl_c64_load(v[0]);bl_reset(&g);g.room=(unsigned char)v[0];
        g.x=(BlCoord)(v[1]*16);g.y=(BlCoord)(v[2]*16);g.previous_x=g.x;g.previous_y=g.y;
        g.facing=(unsigned char)v[3];g.state=BL_AIR;g.attack=BL_FLYING_KICK;
        g.attack_phase=(unsigned char)(12-v[4]);g.wall.previous=(unsigned char)(g.facing?13:12);
        bl_step(&g,0);
        if(bl_x(&g)!=v[5]||bl_y(&g)!=v[6]||g.facing!=v[7]||g.attack!=v[8]||12-g.attack_phase!=v[9]||
           g.wall.state!=v[10]||g.wall.counter!=v[11])return (unsigned short)(9+i);
        if((v[12]==12||v[12]==13||v[12]==24)&&bl_c64_object_pose(&g)!=v[13])return (unsigned short)(9+i);
    }
    for(i=0;i<3;i++){
        int direction=(int)i-1;
        bl_c64_reset();bl_c64_load(0);bl_reset(&g);
        for(j=0;j<1000;j++){bl_c64_test_write(0x8c00+j,6);bl_c64_test_write(0xd800+j,14);}
        for(j=0;j<8;j++)bl_c64_test_write(0xa030+j,0);
        g.x=120*16;g.y=130*16;g.previous_x=g.x;g.previous_y=g.y;
        g.state=BL_AIR;g.jump_phase=1;g.jump_direction=(signed char)direction;g.facing=(unsigned char)(direction>=0);
        g.wall.previous=(unsigned char)(direction<0?6:direction>0?7:5);
        for(k=0;k<18;k++){
            const signed short *v=source_jump_vectors[i*18+k];
            if(bl_c64_object_pose(&g)!=v[3])return (unsigned short)(17+i*18+k);
            bl_step(&g,(unsigned char)(direction<0?BL_RIGHT:BL_LEFT));
            if(bl_x(&g)!=v[0]||bl_y(&g)!=v[1]||g.facing!=v[2])return (unsigned short)(17+i*18+k);
        }
    }
    return 0;
}
#endif
''']
    path=ROOT/'tests/movement_fixture.h';path.write_text('\n'.join(lines)+'\n')
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    identity=json.loads((ROOT/'.tmp/source-movement-test/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for item in identity:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    dll=ctypes.CDLL(str(ROOT/'.tmp/source-movement-test/movement.dll'))
    dll.bl_source_wall_step.argtypes=[ctypes.POINTER(Wall),ctypes.POINTER(Actor),ctypes.c_long]
    dll.bl_source_wall_step.restype=ctypes.c_long
    fixtures=[];rng=random.Random(6502)
    for state in (0,3,4,5,6,7,12,13,14,17,19,24,26):
        for direction in range(4):
            h=[[0]*4 for _ in range(11)];h[0][direction]=2
            fixtures.append((f'state{state}_undo_direction{direction}',Actor(60,150,1,state,12,state,3,0),h,8))
    for i in range(448):
        state=rng.choice((0,3,4,12,13,14,19,24,26))
        a=Actor(rng.choice((12,13,15,60,161,162,163)),rng.choice((45,46,100,150,198,199)),rng.randrange(2),
                state,64 if state==24 else rng.randrange(13),rng.choice((0,3,13,24,26)),rng.randrange(7),0)
        h=[[rng.randrange(3) if rng.randrange(5)==0 else 0 for _ in range(4)] for _ in range(11)]
        if i%13==0:h=[[0]*4 for _ in range(11)]
        fixtures.append((f'history_{i}',a,h,rng.choice((8,9,10,12,13,14,15,0 if state==24 else 8))))
    results=[]
    for name,a,history,flags in fixtures:
        m=list(source);m[0xb6]=flags;m[0xc8]=0;m[0x29]=0
        for k,address in FIELDS.items():m[address]=getattr(a,k)
        for i,row in enumerate(history):
            for d,value in enumerate(row):m[0x4f57+i*12+d*3]=value
        w=Wall()
        for i,row in enumerate(history):w.moves[i][:]=row
        before={k:getattr(a,k) for k in FIELDS}
        result=dll.bl_source_wall_step(ctypes.byref(w),ctypes.byref(a),flags)
        cpu=MPU(memory=m,pc=0x1c5b);cpu.x=0;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
        for count in range(100000):
            if cpu.pc in (0xffff,0x1d6f,0x2f8e):break
            cpu.step()
        else:raise AssertionError((name,hex(cpu.pc)))
        expected_result=0 if cpu.pc==0x1d6f else 2 if cpu.pc==0x2f8e else 1
        assert result==expected_result,(name,'dispatch',result,expected_result)
        for k,address in FIELDS.items():
            assert getattr(a,k)==m[address],(name,k,getattr(a,k),m[address],before,history,flags)
        actual=[list(row) for row in w.moves]
        expected=[[m[0x4f57+i*12+d*3] for d in range(4)] for i in range(11)]
        assert actual==expected,(name,'history',actual,expected)
        results.append(dict(name=name,input=before,contact=flags,history=history,dispatch=result,
                            after={k:getattr(a,k) for k in FIELDS},instructions=count))
    out=ROOT/'reference/analysis/movement-audit-2026-10-25';out.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for lo,hi in ((0x1c5b,0x1fc4),(0x2008,0x216b),(0x24b7,0x2509),(0x288b,0x28b3)):
        p=lo
        while p<hi:
            n,t=dis.instruction_at(p);lines.append(f'{p:04X} {source[p:p+n].hex(" "):<9} {t}');p+=n
    (out/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
    kick=kick_controls(dll,source)
    jump=jump_controls(dll,source)
    generated=native_fixtures(results,kick,jump)
    files=('core/source_wall.c','core/source_wall.h','core/game.c','core/game.h','core/c64_rooms.c','core/c64_rooms.h',
           'core/c64_room_data.h','core/c64_room_programs.h','tests/movement_bridge.c','tools/verify_source_movement.py','test-source-movement.ps1')
    report=dict(status='passed_decoded_wall_kernel_vs_actual6502',source_sha256=SHA,edition_verified=False,
                natural_playthrough=False,injected_contact_and_history=True,cases=len(results),results=results,kick_cases=len(kick),kick_results=kick,
                jump_cases=len(jump),jump_results=jump,native_fixture_checks=70,generated=generated,source_files=identity)
    for item in identity:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    (out/'wall-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(results)} actual6502 wall/history fixtures; {len(kick)} source-pixel kick cases in20rooms; {len(jump)} jump/fall steps')

if __name__=='__main__':main()
