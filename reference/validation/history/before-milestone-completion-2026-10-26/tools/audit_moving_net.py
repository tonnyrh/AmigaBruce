"""Moving-net rules vs actual frozen6502 bytes. Controlled states, not playthrough."""
from pathlib import Path
import ctypes,hashlib,itertools,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from verify_source_movement import Actor,FIELDS,invoke,SHA
from verify_source_climb import raw_input
from c64_room_model import oracle_contact,word
OUT=ROOT/'reference/analysis/moving-net-2026-10-25'
SOURCES=['core/game.c','core/game.h','core/source_climb.c','core/source_climb.h','core/source_wall.c',
    'core/rooms.c','core/combat.c','core/c64_sprites.c','core/c64_rooms.c','core/c64_room_data.h',
    'core/c64_room_programs.h','tests/moving_net_bridge.c','tests/moving_net_fixture.h','tools/audit_moving_net.py','test-moving-net.ps1']
def artifact(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
def call(m,entry,actor=0):
    cpu=MPU(memory=m,pc=entry);cpu.x=actor;cpu.sp=253;m[0x1fe:0x200]=[254,255]
    sound=0
    for _ in range(200000):
        if cpu.pc==65535:return sound
        if cpu.pc==0x1fc4:sound+=1
        cpu.step()
    raise AssertionError(('escaped',hex(entry),hex(cpu.pc)))
def dispatch(dll,source):
    rows=[];count=0
    # All directions/diagonals, delay phases, scroll phases/directions and
    # source movement limits. Keep control flags and counter explicit.
    for xy,input,delay,phase,reverse,contact,previous in itertools.product(
        ((12,45),(13,46),(80,120),(162,198),(163,199)),range(16),range(5),
        (0,1,2,129),(0,1),(0,4),(0,23)):
        a=Actor(x=xy[0],y=xy[1],facing=0,state=23,counter=16,
            previous=previous,animation=6,wait=0,pose_lock=0)
        initial=[getattr(a,k) for k in FIELDS]
        m=list(source)
        for k,address in FIELDS.items():m[address]=getattr(a,k)
        for i in range(132):m[0x4f57+i]=0
        m[0x52]=16;m[0xb6]=contact;m[0xc8]=0;m[0xad]=delay;m[0xaa]=0
        m[0x98]=raw_input(input);m[0x9b]=0;m[0x60]=phase;m[0x65]=reverse
        m[0x4f48]=m[0x4f4e]=10
        expected_sound=call(m,0x2187)
        ad=ctypes.c_ubyte(delay);aa=ctypes.c_ubyte(0)
        sound=dll.bl_source_moving_net_step(ctypes.byref(a),ctypes.byref(ad),ctypes.byref(aa),
            input,contact,phase,reverse)
        actual=[getattr(a,k) for k in FIELDS]+[ad.value,aa.value,sound]
        expected=[m[v] for v in FIELDS.values()]+[m[0xad],m[0xaa],expected_sound]
        assert actual==expected,('dispatch',xy,input,delay,phase,reverse,contact,previous,actual,expected)
        count+=1
        if xy==(80,120) and previous==23 and contact==4 and phase in (1,2) and input in (0,1,2,4,8,5):
            rows.append(dict(before=initial,delay=delay,input=input,phase=phase,reverse=reverse,contact=contact,after=expected))
    return count,rows
def prepare(dll,source,x,y,facing,phase):
    dll.bl_net_prepare(x,y,facing,phase)
    m=[dll.bl_c64_read(i) for i in range(65536)]
    m[0x500:0x4300]=source[0x500:0x4300];m[0x5000:0x5800]=source[0x5000:0x5800]
    m[0x95:0x98]=[1,0,0];m[0x9e]=(x+24)//2;m[0xa1]=y;m[0xa4]=facing
    m[0xbf]=(7 if facing else 6) if phase else 0;m[0xc2]=0
    m[0xce]=16-phase if phase else 0;m[0xcb]=0;m[0x106]=m[0x4fdb]=m[0xc8]=m[0xad]=m[0xaa]=0
    m[0x4f48]=m[0x4f4e]=dll.bl_net_read(6);m[0x7c]=0xa0
    for i in range(132):m[0x4f57+i]=0
    return m
def route(dll,source,label,x,y,facing,phase,inputs):
    m=prepare(dll,source,x,y,facing,phase);rows=[];attaches=0
    for step,input in enumerate(inputs):
        # Source $1BEE/$1BFE-$1C29 order; all room code is executed by6502,
        # independently of the compiled room implementation under test.
        call(m,0x40bc);m[0x7b]=m[0x7b]-1 if m[0x7b] else 1
        call(m,word(m,0x4ec4+8)+1)
        flags,body=oracle_contact(m,m[0x9e]*2-24,m[0xa1],m[0x4f4e])
        m[0xb6]=flags;m[0xa7]=body
        call(m,0x2e39);selected=m[0xbf]
        m[0x98]=raw_input(input);m[0x9b]=0 if input&16 else 1
        call(m,0x1c5b);call(m,0x2780)
        dll.bl_net_step(input)
        actual=[dll.bl_net_read(i) for i in range(12)]
        expected=[m[0x9e]*2-24,m[0xa1],m[0xa4],m[0xbf],m[0xad],m[0xaa],m[0x4f4e],m[0xc2],m[0xcb]]
        # State23 and its release are checked with no actors nearby; recoil
        # must stay zero and health unchanged. Other AI/combat are separate.
        assert actual[:9]==expected,(label,step,input,flags,selected,actual,expected)
        assert actual[9:11]==[0,36],('spurious hit',label,step,actual)
        assert [dll.bl_c64_read(v) for v in (0x60,0x64,0x65,0x66)]==[m[v] for v in (0x60,0x64,0x65,0x66)]
        if selected==23:attaches+=1
        rows.append(dict(input=input,flags=flags,selected=selected,phase=m[0x60],reverse=m[0x65],after=actual[:9]))
    assert attaches,(label,'no moving-net contact')
    return dict(label=label,x=x,y=y,facing=facing,jump_phase=phase,steps=rows)
def native_fixture(vectors,traces):
    arr=lambda xs:'{'+','.join(str(v) for v in xs)+'}'
    rows=[v['before']+[v['delay'],v['input'],v['contact'],v['phase'],v['reverse']]+v['after'] for v in vectors]
    starts=[];steps=[]
    for t in traces:
        starts.append([len(steps),len(t['steps']),t['x'],t['y'],t['facing'],t['jump_phase']])
        steps.extend([[v['input']]+v['after'] for v in t['steps']])
    count=len(rows)+len(steps)
    lines=['/* GENERATED from actual6502 moving-net dispatch and R05 room loops. */',
        '#include "../core/rooms.h"','#include "../core/c64_rooms.h"','#include "../core/source_climb.h"',
        f'#define BL_MOVING_NET_CASES {count}',
        'static const unsigned char moving_net_vectors[][26]={'+','.join(arr(r) for r in rows)+'};',
        'static const signed short moving_net_starts[][6]={'+','.join(arr(s) for s in starts)+'};',
        'static const signed short moving_net_steps[][10]={'+','.join(arr(s) for s in steps)+'};',
        r'''static unsigned short moving_net_fixture_run(void){
    BlSourceActor a;unsigned short i,j;unsigned char delay,hold;long sound;
    BlCombat w;BlProgress p;BlGame *g=&w.player.body;
    for(i=0;i<sizeof(moving_net_vectors)/sizeof(moving_net_vectors[0]);i++){
        const unsigned char *v=moving_net_vectors[i];
        for(j=0;j<9;j++)((unsigned char*)&a)[j]=v[j];
        delay=v[9];hold=0;
        sound=bl_source_moving_net_step(&a,&delay,&hold,v[10],v[11],v[12],v[13]);
        for(j=0;j<9;j++)if(((unsigned char*)&a)[j]!=v[14+j])return i+1;
        if(delay!=v[23]||hold!=v[24]||sound!=v[25])return i+1;
    }
    for(i=0;i<sizeof(moving_net_starts)/sizeof(moving_net_starts[0]);i++){
        const signed short *s=moving_net_starts[i];
        bl_progress_reset(&p);bl_combat_reset(&w);bl_progress_inspect_room(&p,&w,4);
        w.enemy[0].active=w.enemy[1].active=0;w.enemy[0].respawn=w.enemy[1].respawn=0;
        bl_c64_test_write(0x7a,1); /* Isolated player/net contacts. */
        g->x=(BlCoord)(s[2]*16);g->y=(BlCoord)(s[3]*16);g->facing=(unsigned char)s[4];
        if(s[5]){g->state=BL_AIR;g->jump_phase=(unsigned char)s[5];g->jump_direction=(signed char)(s[4]?1:-1);}
        for(j=0;j<s[1];j++){
            const signed short *v=moving_net_steps[s[0]+j];unsigned char state;
            bl_progress_step(&p,&w,(unsigned char)v[0]);
            state=(unsigned char)(g->wall.state==24?24:g->state==BL_CLIMB?g->climb_state:
                g->state==BL_AIR?(g->jump_phase==255?14:g->jump_direction<0?6:g->jump_direction>0?7:5):0);
            if(bl_x(g)!=v[1]||bl_y(g)!=v[2]||g->facing!=v[3]||state!=v[4]||
                g->net_delay!=v[5]||g->net_hold!=v[6]||bl_c64_object_pose(g)!=v[7]||
                g->wall.previous!=v[8]||g->wall.animation!=v[9]||w.player.stun||w.player.health!=36)
                return (unsigned short)(sizeof(moving_net_vectors)/sizeof(moving_net_vectors[0])+s[0]+j+1);
        }
    }
    return 0;
}''']
    (ROOT/'tests/moving_net_fixture.h').write_text('\n'.join(lines)+'\n')
    return dict(cases=count,dispatch=len(rows),room5_steps=len(steps),artifact=artifact('tests/moving_net_fixture.h'))
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    dll=ctypes.CDLL(str(ROOT/'.tmp/moving-net-test/net.dll'))
    dll.bl_net_prepare.argtypes=[ctypes.c_long]*4;dll.bl_net_step.argtypes=[ctypes.c_long]
    dll.bl_net_read.argtypes=[ctypes.c_long];dll.bl_net_read.restype=ctypes.c_long
    dll.bl_c64_read.argtypes=[ctypes.c_long];dll.bl_c64_read.restype=ctypes.c_ubyte
    dll.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    dll.bl_source_moving_net_step.argtypes=[ctypes.POINTER(Actor),ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_ubyte)]+[ctypes.c_long]*4
    count,vectors=dispatch(dll,source)
    traces=[]
    specs=[('right-jump-catch',170,179,0,1,[1]*12+[0]*18),
        ('left-jump-catch',134,179,1,1,[2]*12+[0]*18),
        ('up-and-release',150,179,0,0,[4]*40+[0]*20),
        ('down-and-release',150,120,1,0,[8]*40+[0]*20),
        ('diagonal-carry',150,150,0,1,[5]*20+[0]*30),
        ('leave-left',150,150,0,0,[1]*30+[2]*10),
        ('leave-right',150,150,1,0,[2]*30+[1]*10)]
    for spec in specs:traces.append(route(dll,source,*spec))
    native=native_fixture(vectors,traces)
    assert dll.bl_net_native_contracts()==0,'Generated native fixture failed on host'
    OUT.mkdir(parents=True,exist_ok=True)
    d=Disassembler(MPU(memory=list(source)));lines=[]
    for start,end in [(0x2e10,0x2e1c),(0x2e39,0x2e68),(0x310c,0x312c),(0x2180,0x2235),(0x2c70,0x2d55)]:
        a=start
        while a<end:
            n,t=d.instruction_at(a);lines.append(f'{a:04X} {source[a:a+n].hex(" "):8} {t}');a+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
    report=dict(status='passed_controlled_source_checks',source_sha256=SHA,edition_verified=False,
        natural_playthrough=False,dispatch_cases=count,dispatch_vectors=vectors,room5_routes=traces,
        native_fixture=native,source_files=[artifact(p) for p in SOURCES])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS moving net: {count} source6502 dispatch cases; {sum(len(t["steps"]) for t in traces)} R05 steps')
if __name__=='__main__':main()
