"""Build compact68000 controls from executed frozen6502 instructions."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/source-actor-test/actors.dll'))
    d.bl_actor_prepare.argtypes=[ctypes.c_long];d.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    buf=(ctypes.c_ubyte*65536)();d.bl_actor_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    cases=[(0,0,state,8,5,0) for state in range(28)]+[(room,0,0,0,0,1) for room in range(20)]+[(0,0,state,7,0,2) for state in (12,13,14,17,22)]
    rows=[]
    for room,actor,state,counter,contact,kind in cases:
        d.bl_actor_prepare(room);writes=[]
        if kind==0:writes=[(0x95,1),(0x9e,80),(0xa1,150),(0xa4,1),(0xbf,state),(0xce,counter),(0xc2,state),(0x106,0),(0xb6,contact),(0xa7,contact&1),(0x98,15),(0x9b,1),(0xd1,20)]
        elif kind==1:writes=[(0x98,15),(0x9b,1),(0x99,15),(0x9c,1),(0xdc00,255),(0xdc01,255),(0xd01e,0)]
        else:
            writes=[(0xd01e,15)]
            for i in range(3):writes += [(0x95+i,(1,0x81,0x41)[i]),(0x9e+i,60+i*8),(0xa1+i,150),(0xa4+i,1),(0xbf+i,state if i==0 else 0),(0xce+i,counter if i==0 else 0),(0xd1+i,20),(0x4f45+i,2)]
        for at,value in writes:d.bl_c64_test_write(at,value)
        d.bl_actor_copy(buf);m=list(buf);entry=(0x1c5b,0x1bc2,0x29c3)[kind];cpu=MPU(memory=m,pc=entry);cpu.a=cpu.y=0;cpu.x=actor;cpu.sp=253;cpu.p=0x30;m[0x1fe:0x200]=[0xfe,0xff];life=0
        stops={0xffff,0x0f47,0x1c32,0x050f,0x0584,0x1968,0x197d}
        if kind!=1:stops.add(0x1bc2)
        for _ in range(2000000):
            if cpu.pc in stops:break
            if cpu.pc==0x1818:life+=1
            cpu.step()
        else:raise AssertionError(hex(cpu.pc))
        h=2166136261
        for value in m:h=((h^value)*16777619)&0xffffffff
        regs=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,life,int(cpu.pc in (0x50f,0x584)),(cpu.p>>2)&1,1 if cpu.pc==0x1968 else 2 if cpu.pc==0x197d else 0]
        rows.append(dict(room=room,actor=actor,entry=entry,writes=writes,ram_fnv=h,registers=regs))
    text=['/* Generated from actual source instructions; injected RAM fixtures, not natural play. */',f'#define BL_SOURCE_ACTOR_CASES {len(rows)}',
        'typedef struct {unsigned short address;unsigned char value;} BlActorWrite;',
        'static const BlActorWrite source_actor_writes[]={']
    for row in rows:
        row['offset']=sum(len(r['writes']) for r in rows[:rows.index(row)])
        text += ['{'+str(at)+','+str(value)+'},' for at,value in row['writes']]
    text += ['};','typedef struct {unsigned char room,actor,count;unsigned short entry,offset;unsigned long hash;unsigned char registers[13];} BlActorControl;', 'static const BlActorControl source_actor_controls[]={']
    for row in rows:text.append('{'+','.join(map(str,[row['room'],row['actor'],len(row['writes']),row['entry'],row['offset']]))+f',{row["ram_fnv"]}UL,{{'+','.join(map(str,row['registers']))+'}},')
    text += ['};','static unsigned short source_actor_fixture_run(void){unsigned short i,j;unsigned char registers[13];',
        'for(i=0;i<BL_SOURCE_ACTOR_CASES;i++){const BlActorControl *q=&source_actor_controls[i];',
        'bl_c64_reset();bl_c64_actor_seed();bl_c64_actor_test_call(0x0f72,0);bl_c64_test_write(2,50);bl_c64_test_write(0x104,1);',
        'bl_c64_test_write(0xd1,36);bl_c64_test_write(0xd2,36);bl_c64_test_write(0xd3,36);',
        'bl_c64_actor_test_call(0x0763,0);bl_c64_load(q->room);bl_c64_actor_test_call(0x0b30,0);',
        'for(j=0;j<q->count;j++){const BlActorWrite *w=&source_actor_writes[q->offset+j];bl_c64_test_write(w->address,w->value);}',
        'bl_c64_actor_test_call(q->entry,q->actor);if(bl_c64_fault() || bl_c64_actor_ram_hash()!=q->hash)return i+1;',
        'bl_c64_actor_registers(registers);for(j=0;j<13;j++)if(registers[j]!=q->registers[j])return i+1;',
        '}return 0;}']
    out=ROOT/'tests/source_actor_fixture.h';out.write_text('\n'.join(text)+'\n')
    report=dict(source_sha256=hashlib.sha256((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()).hexdigest(),edition_verified=False,natural_playthrough=False,cases=rows,fixture=dict(path=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
    (ROOT/'reference/analysis/actor-chain-2026-10-26/native-fixture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built',len(rows),'native full-RAM/register controls from original instructions')
if __name__=='__main__':main()
