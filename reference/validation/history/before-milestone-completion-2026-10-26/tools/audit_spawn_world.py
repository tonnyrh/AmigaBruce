"""Original main-loop window against actual native spawn/object/actor calls."""
import ctypes,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'.reference/tools/python')]
from py65.devices.mpu6502 import MPU
from audit_spawn import invoke,SHA,OUT,compiled_identity

def main():
    compiled=compiled_identity()
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/spawn-test/spawn.dll'))
    d.bl_spawn_world_read.argtypes=[ctypes.c_long]*2;d.bl_spawn_world_read.restype=ctypes.c_long
    d.bl_spawn_bomb_prepare.argtypes=[ctypes.c_long]*4
    d.bl_c64_read.argtypes=[ctypes.c_long];d.bl_c64_read.restype=ctypes.c_ubyte
    buf=(ctypes.c_ubyte*65536)();d.bl_spawn_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    def memory():
        d.bl_spawn_copy(buf);m=list(buf);keep={a:m[a] for a in (0x42ca,0x1166,0x2581,0x2582,0x2583)}
        m[0x500:0x4300]=b[0x500:0x4300];m[0x5000:0x5800]=b[0x5000:0x5800]
        for a,v in keep.items():m[a]=v
        return m
    def main_window(m,stop):
        # Modeled PAL seam and fixed controller/reader data, not natural play.
        m[0x7c]=0xa0;m[2]=50;m[0x100]=0
        cpu=MPU(memory=m,pc=0x1bee);cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
        for _ in range(200000):
            if cpu.pc==stop:return
            if cpu.pc==0x2f8e and not m[0x51]:raise AssertionError(('Unexpected player room transition',step,m[0x9e:0xa7],m[0xbf:0xc2],m[0x4f5b:0x4f67]))
            cpu.step()
        raise AssertionError(('main window escaped',hex(cpu.pc)))
    d.bl_spawn_world_prepare();m=memory();edge=[]
    for step in range(1,124):
        for _ in range(3):
            m[0x16]=(m[0x16]+1)&255;invoke(m,0x1614,stop=0x1628)
            if m[0x49]:m[0x49]-=1
            elif m[0x4a]:m[0x4a]-=1;m[0x49]=255
        main_window(m,0x1c32);d.bl_spawn_world_step()
        actors=[]
        for actor in (1,2):
            actual=[d.bl_spawn_world_read(actor,i) for i in range(5)]
            expected=[m[0x95+actor]&1,m[0x9e+actor],m[0xa1+actor],m[0xa4+actor],m[0x5e if actor==1 else 0x5d]]
            assert actual[0]==expected[0] and actual[4]==expected[4],('edge flags/time',step,actor,actual,expected)
            if actual[0]:assert actual==expected,('edge placement',step,actor,actual,expected)
            actors.append(expected)
        edge.append(dict(step=step,actors=actors))
    bombs=[]
    for actor,(col,row),phase in itertools.product((1,2),((7,4),(29,4),(3,7),(17,7),(21,7)),(8,12,16)):
        d.bl_spawn_bomb_prepare(actor,col,row,phase);m=memory()
        main_window(m,0x1c13);d.bl_spawn_bomb_step()
        actual=[d.bl_spawn_world_read(actor,i) for i in (0,4)]
        expected=[m[0x95+actor]&1,m[0x5e if actor==1 else 0x5d]]
        assert actual==expected,('birth blast',actor,col,row,phase,actual,expected)
        bombs.append(dict(actor=actor,bomb=[col,row],phase=phase,active=actual[0],delay=actual[1],initial_mask=m[0x4f4e+actor]))
    paths=['core/combat.c','core/combat.h','core/rooms.c','core/c64_rooms.c','core/c64_rooms.h','core/game.c','core/game.h','tests/spawn_bridge.c','tools/audit_spawn_world.py','test-spawn.ps1']
    r=dict(source_sha256=SHA,natural_playthrough=False,edition_verified=False,source_main_window='$1BEE..$1C32 or$1C13',
        source_caller_registers='Injected A/X/Y/flags=0 at $1BEE; immutable controlled read data1 at$6000',edge=edge,birth_bombs=bombs,
        compiled_sources=compiled,dll_sha256=hashlib.sha256((ROOT/'.tmp/spawn-test/spawn.dll').read_bytes()).hexdigest(),
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'world-controls.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS123 source main-loop spawn/exit updates and30 birth/explosion cases over all5 R08 bombs')
if __name__=='__main__':main()
