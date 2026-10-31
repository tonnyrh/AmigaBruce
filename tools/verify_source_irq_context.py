"""Actual IRQ vector/raster handlers, fixed pins/raster and explicit context.

All source RAM, physical register bits and returned PC are compared. This
is not a natural interrupt schedule, VIC model or physical timing test.
"""
import ctypes,hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
BASE=ROOT/'reference/analysis/irq-input-2026-10-30'
class Bus:
    def __init__(self,ram,pins,raster):self.ram=bytearray(ram);self.pins=pins;self.raster=raster;self.gates=0
    def __getitem__(self,at):
        if at==0xdc00:return self.pins[0]
        if at==0xdc01:return self.pins[1]
        if at==0xd012:return self.raster
        value=self.ram[at]
        if at==0xd01e:self.ram[at]=0
        return value
    def __setitem__(self,at,value):
        if at in [0xd404,0xd40b,0xd412] and value&1 and not self.ram[at]&1:self.gates|=1<<((at-0xd404)//7)
        self.ram[at]=value
def main():
    original=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==SHA
    U=ctypes.c_ubyte;P=ctypes.POINTER(U);ram=(U*65536)();regs=(U*10)()
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-irq-context/context.dll'))
    lib.bl_irq_context_prepare.argtypes=[ctypes.c_long,ctypes.c_long];lib.bl_irq_context_seed.argtypes=[P,P]
    lib.bl_irq_context_run.argtypes=[ctypes.c_long]*3;lib.bl_irq_context_copy.argtypes=[P];lib.bl_irq_context_regs.argtypes=[P]
    lib.bl_irq_context_pc.restype=lib.bl_irq_context_fault.restype=ctypes.c_long
    lib.bl_irq_context_gates.restype=ctypes.c_long
    rng=random.Random(2026103005);cases=instructions=0;handlers={};commands={};coverage=set();seeded_rooms=[]
    def baseline(room,human):
        lib.bl_irq_context_prepare(room,human);lib.bl_irq_context_copy(ram)
        b=bytearray(ram);assert b[0x29]==room
        return b
    def check(before,pins=(31,31),r=None,pc=0x1c32,raster_override=None):
        nonlocal cases,instructions
        handler=before[0x408]|before[0x409]<<8
        assert handler in [0x48c1,0x491e,0x4982,0x14a4,0x1574],hex(handler)
        raster=110 if handler==0x14a4 else 66 if handler==0x491e else (before[0x47f5+before[0x44]]+3)&255 if handler==0x4982 else 253
        if raster_override is not None:raster=raster_override
        if r is None:r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(5)]+[rng.randrange(224,254),0]
        bus=Bus(before,pins,raster);cpu=MPU(memory=bus,pc=pc)
        cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8];cpu.p=0x20|r[3]|r[4]<<1|r[9]<<2|r[7]<<3|r[6]<<6|r[5]<<7
        cpu.irq();trace=[]
        if not r[9]:
            for _ in range(50000):
                at=cpu.pc;trace.append(at)
                for delta in [0,0x470,0x570]:
                    if 0xeb3a+delta<=at<=0xeb4f+delta and (at-0xeb3a-delta)%3==0:
                        key=str((at-0xeb3a-delta)//3);commands[key]=commands.get(key,0)+1
                cpu.step();instructions+=1
                if at in [0x491d,0x4974,0x1525,0x15a7]:break
            else:raise AssertionError(('original IRQ escaped',cases,hex(cpu.pc),[hex(x) for x in trace[-15:]]))
        wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,cpu.p>>1&1,cpu.p>>7&1,cpu.p>>6&1,cpu.p>>3&1,cpu.sp,cpu.p>>2&1]
        lib.bl_irq_context_seed((U*65536).from_buffer_copy(before),(U*10)(*r));lib.bl_irq_context_run(pc,*pins)
        lib.bl_irq_context_copy(ram);lib.bl_irq_context_regs(regs)
        actual=bytes(ram);expected=bytes(bus.ram)
        if actual!=expected:
            diffs=[dict(address='$%04X'%i,source=b,native=a) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
            (BASE/'irq-context-failure.json').write_text(json.dumps(dict(case=cases,handler=hex(handler),pc=hex(pc),regs=r,pins=pins,source_regs=wanted,native_regs=list(regs),source_pc=hex(cpu.pc),native_pc=hex(lib.bl_irq_context_pc()),fault=hex(lib.bl_irq_context_fault()),differences=diffs,trace=[hex(p) for p in trace]),indent=2)+'\n',encoding='utf-8')
            raise AssertionError(('RAM',cases,hex(handler),diffs[:8]))
        assert not lib.bl_irq_context_fault(),('fault',cases,hex(lib.bl_irq_context_fault()))
        assert list(regs)==wanted,('registers',cases,list(regs),wanted)
        assert lib.bl_irq_context_pc()==cpu.pc,('return PC',cases,hex(lib.bl_irq_context_pc()),hex(cpu.pc))
        assert lib.bl_irq_context_gates()==bus.gates,('SID rising gates',cases,lib.bl_irq_context_gates(),bus.gates)
        cases+=1;handlers[hex(handler)]=handlers.get(hex(handler),0)+1;coverage.add(before[0x29])
        return bytearray(actual)
    # Complete source-selected raster chains from each of the 20 room states.
    for room,human,current in itertools.product(range(20),range(2),range(2)):
        m=baseline(room,human);m[3]=current;m[0x1383]=current;m[0x1384]=1-current
        seeded_rooms.append(room)
        for tick in range(12):
            pc=[0x1c32,0x5214,0x5380,0x2586][tick%4]
            m=check(m,(rng.randrange(32),rng.randrange(32)),pc=pc)
    room_chain_cases=cases
    # Active/pause/control gates, across all current-player and selector pairs.
    base=baseline(0,0)
    for active,paused,human,current,f0,f1 in itertools.product(range(2),repeat=6):
        m=bytearray(base);m[0x104]=active;m[0x105]=128*paused;m[0x42ca]=human;m[3]=current;m[0x1383]=f0;m[0x1384]=f1
        check(m,(rng.randrange(256),rng.randrange(256)))
    gate_cases=cases-room_chain_cases
    # All eight documented dispatch commands for each voice; injected data
    # supplies operands, while branches/JSR sites execute original bytes.
    for voice,command in itertools.product(range(3),range(8)):
        m=baseline(0,1);queue=[0xeb00,0xef70,0xf070][voice];zp=0xf6+voice*2
        for q in [0xeb00,0xef70,0xf070]:m[q]=0
        m[queue]=m[queue+2]=1;m[queue+1]=0;m[zp]=0;m[zp+1]=0x90
        m[0x9000:0x900a]=bytes([command,3,17,0,0,0,0,0,0,0])
        check(m)
    injected_commands=cases-room_chain_cases-gate_cases
    # Actual source SFX streams, with raster state carried between IRQs.
    for effect in range(128,143):
        m=baseline(0,effect&1)
        for voice,q in enumerate([0xeb00,0xef70,0xf070]):m[q]=128+(effect-128+voice)%15
        for tick in range(128):m=check(m,(31,31),pc=0x1c32)
    stream_cases=cases-room_chain_cases-gate_cases-injected_commands
    extra_start=cases
    for room,wait in itertools.product(range(20),[0,1,2,127,128,255]):
        for raster in [109,110]:
            m=baseline(room,0);m[0x408]=0xa4;m[0x409]=0x14;m[0x48]=wait
            check(m,raster_override=raster)
        m=baseline(room,0);m[0x408]=0x74;m[0x409]=0x15;m[0x48]=wait
        check(m)
    announcement_and_gameover_tail_cases=cases-extra_start
    # Both terminating branches in $4991-$499E, without timing inference.
    m=baseline(0,0);m=check(m);m=check(m)
    check(m,raster_override=(m[0x47f5+m[0x44]]+2)&255)
    check(m,raster_override=(m[0x47f5+m[0x44]]+3)&255)
    # Hardware-masked IRQs perform no work and keep the source context.
    for room in range(20):
        m=baseline(room,0);r=[17,23,31,1,0,1,0,1,253,1];check(m,r=r)
    assert coverage==set(range(20)) and set(commands)==set(map(str,range(8)))
    def item(p):return dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
    paths=['core/c64_rooms.c','core/c64_actor_programs.h','core/c64_sfx.h','tests/source_irq_context_bridge.c','tools/verify_source_irq_context.py','test-source-irq-context.ps1','reference/analysis/irq-input-2026-10-30/candidate/irq_context.h','reference/analysis/irq-input-2026-10-30/candidate/input_slot.h']
    report=dict(status='passed_candidate_original_game_irq_context',source_sha256=SHA,cases=cases,instructions=instructions,room_chain_cases=room_chain_cases,gate_cases=gate_cases,injected_command_cases=injected_commands,source_stream_cases=stream_cases,announcement_and_gameover_tail_cases=announcement_and_gameover_tail_cases,handlers=handlers,commands=commands,all_ram_and_registers=True,returned_pc_verified=True,sid_gate_edges_verified=True,production_changed=False,original_raster_phase_verified=False,natural_playthrough=False,edition_verified=False,
        limitations=['Explicit caller PCs and safe stack range $E0-$FD, not a natural PC/stack distribution','Fixed CIA pins and chosen raster reads to exit polling; no cycle/raster model','No VIC collision generation or physical A500 acceptance','Three game handlers, $14A4 announcement and $1574 tail only; $152C/title music state and other IRQs remain open','Native candidate only; production field/audio scheduling remains unchanged'],artifacts=[item(p) for p in paths])
    (BASE/'irq-context-candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS complete controlled game IRQ candidate:',cases,'all-RAM/register/PC cases;',instructions,'original instructions; production unchanged')
if __name__=='__main__':main()
