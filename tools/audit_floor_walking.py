"""Actual frozen main-loop bytes versus the live native chain on static floors.

Explicit isolated input/field seams; no natural or original raster claim.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
from rip_c64_room_graphics import source_room
BASE=ROOT/'reference/analysis/floor-walk-2026-10-30'
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def call(mem,entry,stop=0xffff):
    cpu=MPU(memory=mem,pc=entry);cpu.p=0x30;cpu.sp=253;mem[0x1fe:0x200]=[0xfe,0xff]
    for _ in range(200000):
        if cpu.pc==stop:return cpu
        cpu.step()
    raise AssertionError(('Initialization escaped',hex(cpu.pc)))
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
    lib=ctypes.CDLL(str(ROOT/'.tmp/floor-walk/floor.dll'));U=ctypes.c_ubyte;A=U*65536;R=U*10
    lib.bl_contact_seed.argtypes=[ctypes.POINTER(U),ctypes.POINTER(U)];lib.bl_contact_run.argtypes=[ctypes.c_long]
    lib.bl_contact_copy.argtypes=[ctypes.POINTER(U)];lib.bl_contact_regs.argtypes=[ctypes.POINTER(U)]
    lib.bl_contact_fault.restype=lib.bl_floor_stop.restype=ctypes.c_ulong
    output=A();registers=R();rows=[];instructions=0;compared=0
    rooms={room:source_room(source,room) for room in range(20)}
    cases=[(r,'source-start',source[0x4bae+r]*2-24,source[0x4bc2+r],direction) for r in range(20) for direction in (-1,1)]
    cases += [(r,label,x,y,d) for r,label,x,y in [(0,'upper-left-roof',32,98),(0,'upper-right-roof',176,98),(1,'upper-roofs',24,98),(1,'middle-roofs',24,146)] for d in (-1,1)]
    stops={0x1c32,0xf47,0x1968,0x197d,0x050f,0x0584}
    for room,label,x,y,direction in cases:
        mem=list(rooms[room]);mem[0x95:0x98]=[1,0,0];mem[0x9e]=(x+24)//2;mem[0xa1]=y;mem[0xa4]=int(direction>0)
        for base in [0xbf,0xc2,0xc5,0xc8,0xcb,0xce,0x106,0x4fdb]:mem[base]=0
        mem[0xd1]=36;mem[0x48]=0;mem[0x4f57:0x4fdb]=[0]*132
        # Execute the original charset selection and pose/image initialization.
        call(mem,0x15d0,0x15ee);call(mem,0x2780);call(mem,0x2584)
        samples=[]
        for step in range(48):
            mem[0x48]=0;mem[0x95:0x98]=[1,0,0];mem[0xd015]&=3;mem[0xd01e]=0
            mem[0x98]=11 if direction<0 else 7;mem[0x9b]=1;mem[0xdc00]=mem[0xdc01]=255
            mem[0x1fe:0x200]=[0xfe,0xff];before=[mem[at] for at in [0x9e,0xa1,0xbf,0xce,0x106]]
            lib.bl_contact_seed(A.from_buffer_copy(bytes(mem)),R(0,0,0,0,0,0,0,0,253,0))
            cpu=MPU(memory=mem,pc=0x1bc2);cpu.p=0x30;cpu.sp=253;contact=None;black=[]
            for count in range(300000):
                if cpu.pc in stops:break
                if cpu.pc==0x1c10:contact=[mem[0xb6],mem[0xa7]]
                if cpu.pc in [0x1c68,0x1d60,0x1dc4,0x1dbc,0x1dfc]:black.append(hex(cpu.pc))
                cpu.step()
            else:raise AssertionError(('Main escaped',room+1,step,hex(cpu.pc)))
            instructions+=count;lib.bl_contact_run(0x1bc2);lib.bl_contact_copy(output);lib.bl_contact_regs(registers)
            expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
            assert not lib.bl_contact_fault(),('Native fault',room+1,step)
            assert bytes(output)==bytes(mem),('RAM',room+1,label,direction,step,[(hex(i),output[i],v) for i,v in enumerate(mem) if output[i]!=v][:12])
            assert list(registers)==expected,('Registers',room+1,step,list(registers),expected)
            expected_stop=0x1c32 if cpu.pc==0x1c32 else 0
            assert lib.bl_floor_stop()==expected_stop,('Wait boundary',room+1,step)
            after=[mem[at] for at in [0x9e,0xa1,0xbf,0xce,0x106]];compared+=1
            samples.append(dict(step=step,before=before,after=after,room_after=mem[0x29]+1,active_after=list(mem[0x95:0x98]),dx_pixels=(after[0]-before[0])*2,dy_pixels=after[1]-before[1],contact=contact,source_paths=black,stop=hex(cpu.pc)))
            if cpu.pc!=0x1c32:break
        rows.append(dict(room=room+1,case=label,start=[x,y],direction=direction,steps=samples))
        print('PASS floor',room+1,label,direction,len(samples),flush=True)
    dis=Disassembler(MPU(memory=list(source)));lines=[]
    for first,last in [(0x1c68,0x1d77),(0x1d77,0x1f1d),(0x15d0,0x15ee)]:
        pc=first
        while pc<last:
            n,text=dis.instruction_at(pc);lines.append('$%04X %s'%(pc,text));pc+=n
    (BASE/'source-disassembly.txt').write_text('\n'.join(lines)+'\n')
    paths=['core/c64_rooms.c','core/c64_actor_programs.h','tools/audit_floor_walking.py','tests/source_contact_bridge.c',
       'reference/analysis/floor-walk-2026-10-30/bridge.c','reference/analysis/floor-walk-2026-10-30/build.ps1']
    report=dict(status='passed_scoped_original_byte_floor_walk_controls',source_sha256=SHA,cases=len(cases),main_steps=compared,source_instructions=instructions,
      all_ram_registers_and_boundaries=True,production_changed=False,edition_verified=False,natural_playthrough=False,raster_exact=False,
      method='Actual frozen6502 main iterations and native live actor chain. Source-decoded room seeds; original bank/pose/image initialization. Active flags reset to Bruce only at each held left/right entry; 48 explicit ready steps per case, no interleaved IRQ. The original main loop still executes room routines, spawning and transition branches; resulting actor flags and room recorded.',
      limitations=['Static walking/control check, not the exact user-reported route.','No wall-clock or original interrupt-phase acceptance.','Does not prove native hardware kernels for a new spatial scenario; existing native primitive controls are separate.','Existing whole-game slowdown can lengthen an otherwise identical source pause.'],
      rows=rows,artifacts=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (BASE/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'floor cases;',compared,'main iterations;',instructions,'original instructions')
if __name__=='__main__':main()
