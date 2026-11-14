"""Full source NPC services plus bounded entry-phase/clock controls.

Actual frozen6502 instructions; work RAM and register seams are injected.
No natural play, uniform-RNG assumption or complete actor-port claim.
"""
import ctypes,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from c64_room_model import oracle_contact
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
OUT=ROOT/'reference/analysis/spawn-audit-2026-10-26'

def compiled_identity():
    rows=json.loads((ROOT/'.tmp/spawn-test/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for item in rows:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],('stale spawn DLL',item['path'])
    return rows

def invoke(m,entry,x=0,y=0,stop=0xffff):
    cpu=MPU(memory=m,pc=entry);cpu.x=x;cpu.y=y;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
    for _ in range(100000):
        if cpu.pc in (stop,0xffff,0x2f8e):return cpu
        cpu.step()
    raise AssertionError(('source did not finish',hex(entry),hex(cpu.pc)))

def services(m):
    m[0x9e]=52;m[0xa1]=196
    if m[0x7a]:return
    # $10C5, used by the native setup, leaves X=$FF/Y=0. Preserve registers
    # between these real JSRs, particularly Y across Yamo -> Kage's reader.
    cpu=MPU(memory=m);cpu.a=6;cpu.x=255;cpu.y=0;cpu.p=0xb0;cpu.sp=255
    for entry,ret in ((0xda4,0x1bf7),(0xd0f,0x1bfa),(0xdb1,0x1bfd)):
        cpu.stPushWord(ret);cpu.pc=entry
        for _ in range(100000):
            if cpu.pc==ret+1:break
            cpu.step()
        else:raise AssertionError(('service did not finish',hex(entry),hex(cpu.pc)))

def main():
    compiled=compiled_identity()
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/spawn-test/spawn.dll'))
    for name,count in (('bl_spawn_prepare',9),('bl_spawn_entry_prepare',5),('bl_spawn_entry_step',1),('bl_spawn_entry_read',1),('bl_c64_load',1),('bl_c64_read',1),('bl_c64_test_write',2),('bl_c64_enemy_remove',1)):
        getattr(d,name).argtypes=[ctypes.c_long]*count
    d.bl_c64_read.restype=ctypes.c_ubyte;d.bl_spawn_entry_read.restype=ctypes.c_long
    d.bl_spawn_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    buf=(ctypes.c_ubyte*65536)()
    def memory():
        d.bl_spawn_copy(buf);m=list(buf)
        mutable={a:m[a] for a in (0x42ca,0x1166,0x2581,0x2582,0x2583,0x0d56,0x0d57,0x0d86,0x0d87,0x2d2c,0x2d2d)}
        m[0x500:0x4300]=b[0x500:0x4300]
        m[0x5000:0x5800]=b[0x5000:0x5800]
        for a,value in mutable.items():m[a]=value
        return m
    initial=[];service_rows=[];remove=[];entries=[];clock=[]
    for room,round_,mode in itertools.product(range(20),(0,1),(0,1)):
        d.bl_c64_reset();d.bl_c64_test_write(0x40,round_);d.bl_c64_test_write(0x42ca,mode)
        d.bl_c64_test_write(0x87,255);d.bl_c64_test_write(0x88,31)
        d.bl_c64_test_write(0x8b,50);d.bl_c64_test_write(0x8c,60)
        m=memory();m[0x29]=room;invoke(m,0xa2a,stop=0xa6b);d.bl_c64_load(room)
        for a in (0x5d,0x5e,0x7a,0x87,0x88,0x8b,0x8c):assert d.bl_c64_read(a)==m[a],('initial',room,round_,mode,hex(a))
        initial.append(dict(room=room,round=round_,mode=mode,counters=m[0x5d:0x5f],disabled=m[0x7a]))
    # active bitmask, Kage delay, Yamo delay, read byte, saved-arrival mask.
    patterns=[(0,1,2,0,0),(0,2,1,191,0),(0,1,1,192,3),(1,1,0,24,0),
        (1,1,0,25,0),(1,0,0,255,0),(2,1,1,255,0),(3,0,0,25,0),(0,0,0,255,3)]
    watch=list(range(0x5d,0x5f))+list(range(0x8a,0xf3))+list(range(0x106,0x109))+list(range(0x4f40,0x4f57))
    watch += [0x16,0x17,0x51,0x52,0x1166,0xd010,0xd015,0x2581,0x2582,0x2583,0xeb00,0xef70,0xf070]
    for room,age,round_,mode,pattern in itertools.product(range(20),(0,24,25,31,32,128),(0,1),(0,1),patterns):
        active,kdelay,ydelay,data,saved=pattern
        d.bl_spawn_prepare(room,age,round_,mode,active,kdelay,ydelay,data,saved)
        m=memory();services(m);d.bl_spawn_run()
        for a in watch:assert d.bl_c64_read(a)==m[a],('service',room,age,round_,mode,pattern,hex(a),d.bl_c64_read(a),m[a])
        output=[]
        for actor in (1,2):output.extend(m[a+actor] for a in (0x95,0x9e,0xa1,0xa4,0xbf,0xce,0xd1,0x4f48,0x4f4e,0x106))
        service_rows.append(dict(inputs=[room,age,round_,mode,*pattern],output=output,counters=m[0x5d:0x5f],saved_x=m[0x8b:0x8d]))
    for room,actor,age,round_,mode in itertools.product(range(20),(1,2),(0,24,25,31,32,128),(0,1),(0,1)):
        d.bl_spawn_prepare(room,age,round_,mode,3,5,7,25,0);m=memory()
        invoke(m,0x3001,x=actor);actual=d.bl_c64_enemy_remove(actor);expected=m[0x5e if actor==1 else 0x5d]
        assert actual==expected and d.bl_c64_read(0x95+actor)==m[0x95+actor]
        remove.append(dict(room=room,actor=actor,age=age,round=round_,mode=mode,delay=actual))
    for active,paused,low,high in itertools.product((0,1),(0,128),(0,254,255),(0,24,31,127,128)):
        d.bl_c64_reset()
        for a,v in ((0x104,active),(0x105,paused),(0x87,low),(0x88,high)):d.bl_c64_test_write(a,v)
        m=memory();invoke(m,0x1614,stop=0x1628);d.bl_c64_field()
        assert [d.bl_c64_read(0x87),d.bl_c64_read(0x88)]==m[0x87:0x89]
        clock.append([active,paused,low,high,*m[0x87:0x89]])
    for actor,bits,color,cross,history in itertools.product((1,2),(0,0x55,0xff),(0,1),(False,True),(0,1)):
        player=80;d.bl_spawn_entry_prepare(actor,bits,color,player,history);m=memory()
        stages=[]
        for step in range(28 if actor==1 else 17):
            if cross and step==9:player=320
            m[0x9e]=(player+24)//2
            pose=m[0x4f4e+actor];flags,_=oracle_contact(m,m[0x9e+actor]*2-24,m[0xa1+actor],pose)
            m[0xb6+actor]=flags
            # Only idle/counter0 is promoted; entry states16/18 are not AI.
            invoke(m,0x2d7c);cpu=invoke(m,0x1c5b,x=actor)
            transition=cpu.pc==0x2f8e
            if not transition:invoke(m,0x2780,x=actor)
            d.bl_spawn_entry_step(player);requested=bool(d.bl_spawn_entry_transition())
            assert requested==transition,('entry transition',actor,bits,color,cross,step)
            if transition:break
            actual=[d.bl_spawn_entry_read(i) for i in (0,1,2)]
            expected=[m[0x9e+actor],m[0xa1+actor],m[0xa4+actor]]
            assert actual==expected,('entry movement',actor,bits,color,cross,history,step,actual,expected,flags)
            if d.bl_spawn_entry_read(5):
                assert [d.bl_spawn_entry_read(i) for i in (3,4,6,7)]==[m[a+actor] for a in (0xbf,0xce,0x4f48,0x4f4e)],('entry stage',actor,bits,color,cross,step)
            stages.append(dict(step=step+1,contact=flags,position=actual,state=m[0xbf+actor],counter=m[0xce+actor]))
        entries.append(dict(actor=actor,bits=bits,color=color,cross=cross,history=history,transition=transition,stages=stages))
    OUT.mkdir(parents=True,exist_ok=True)
    dis=Disassembler(MPU(memory=list(b)));lines=[]
    for a,end in ((0xa2a,0xa6b),(0xb8e,0xe2e),(0x1614,0x1628),(0x2235,0x226a),(0x3001,0x304b),(0x1bee,0x1c0d)):
        while a<end:
            n,t=dis.instruction_at(a);lines.append(f'{a:04X} {b[a:a+n].hex(" "):8} {t}');a+=n
    (OUT/'source-disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    rows=['| Room | Default X/Y | Alternate X/Y | First spawn (Kage/Yamo) | Respawn (Kage/Yamo) | Closed |','| --- | --- | --- | --- | --- | --- |']
    for room in range(20):
        rows.append(f'| {room+1} | {b[0x4bae+room]*2-24}, {b[0x4bc2+room]} | {b[0x4bd6+room]*2-24}, {b[0x4bea+room]} | {b[0x130b+room]}/{b[0x1347+room]} | {b[0x131f+room]}/{b[0x135b+room]} | {b[0x4c9e+room]} |')
    (OUT/'room-table.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    paths=['core/combat.c','core/combat.h','core/game.c','core/game.h','core/rooms.c','core/c64_rooms.c','core/c64_rooms.h','core/c64_sprites.c','core/source_wall.c','core/c64_room_data.h','core/c64_room_programs.h','tools/build_c64_rooms.py','tests/spawn_bridge.c','test-spawn.ps1','tools/audit_spawn.py']
    report=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,initial=initial,services=service_rows,removal=remove,clock=clock,entry=entries,
        compiled_sources=compiled,dll_sha256=hashlib.sha256((ROOT/'.tmp/spawn-test/spawn.dll').read_bytes()).hexdigest(),
        checks=dict(initial=len(initial),services=len(service_rows),removal=len(remove),clock=len(clock),entry_steps=sum(len(x['stages']) for x in entries)),
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS original6502 spawn audit',report['checks'])
if __name__=='__main__':main()
