"""Compare the integrated source world to actual candidate instructions.

CIA input, field boundaries and VIC pixel occupancy are explicit I/O seams.
This is not raster-exact emulation or a natural C64 playthrough.
"""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU

class Bus:
    def __init__(self,data):self.ram=list(data)
    def __getitem__(self,key):
        value=self.ram[key]
        if key==0xd01e:self.ram[key]=0
        return value
    def __setitem__(self,key,value):self.ram[key]=value

def vic(m):
    bank=((~m[0xdd00])&3)<<14;screen=bank+((m[0xd018]>>4)<<10);sprites=[]
    for i in range(8):
        if not m[0xd015]&(1<<i):sprites.append(set());continue
        x=m[0xd000+2*i]+(256 if m[0xd010]&(1<<i) else 0);y=m[0xd001+2*i]
        wide=2 if m[0xd01d]&(1<<i) else 1;tall=2 if m[0xd017]&(1<<i) else 1
        pointer=bank+m[screen+0x3f8+i]*64;pixels=set()
        for row in range(21):
            value=int.from_bytes(bytes(m[pointer+row*3:pointer+row*3+3]),'big')
            for col in range(24):
                opaque=(value>>(22-(col//2)*2))&3 if m[0xd01c]&(1<<i) else (value>>(23-col))&1
                if opaque:
                    for dx in range(wide):
                        for dy in range(tall):pixels.add((x+col*wide+dx,y+row*tall+dy))
        sprites.append(pixels)
    latch=0
    for i in range(7):
        for j in range(i+1,8):
            if sprites[i]&sprites[j]:latch|=(1<<i)|(1<<j)
    return latch

def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/source-actor-test/actors.dll'))
    for name,n in [('bl_c64_world_start',2),('bl_c64_world_input',2),('bl_c64_world_step',2),('bl_c64_test_write',2)]:getattr(d,name).argtypes=[ctypes.c_long]*n
    d.bl_c64_fault.restype=ctypes.c_ushort;d.bl_c64_world_stat.argtypes=[ctypes.c_long];d.bl_c64_world_stat.restype=ctypes.c_ulong
    buf=(ctypes.c_ubyte*65536)();d.bl_actor_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    def native():d.bl_actor_copy(buf);return list(buf)
    rows=[];instructions=0
    for players,human,terminal in ((1,0,False),(2,0,False),(1,1,False),(2,1,False),(1,0,True)):
        d.bl_c64_reset();bus=Bus(native());m=bus.ram;cpu=MPU(memory=bus,pc=0x743);cpu.a=cpu.x=cpu.y=0;cpu.p=0x30;cpu.sp=253
        m[0x42c9]=m[0x42cb]=players==2;m[0x42ca]=m[0x42cc]=human
        stops={0x1bc2,0x1c32,0xf47,0x1968,0x197d,0x050f,0x0584}
        def run(pc,boundaries):
            nonlocal instructions
            cpu.pc=pc
            for _ in range(2000000):
                cpu.step();instructions+=1
                if cpu.pc in boundaries:return
            raise AssertionError(('source escaped',players,human,hex(cpu.pc)))
        def compare(label):
            actual=native();diffs=[(hex(i),actual[i],m[i]) for i in range(65536) if actual[i]!=m[i]]
            assert not d.bl_c64_fault(),(label,'fault',hex(d.bl_c64_fault()))
            assert not diffs,(players,human,label,hex(cpu.pc),diffs[:20])
        run(0x743,stops);d.bl_c64_world_start(players,human);compare('cold')
        for field in range(1080 if terminal else 720):
            # Controlled route, then an explicitly injected terminal life.
            input_=2 if field<90 else 4 if field<240 else 16 if field<400 else 0
            if field in (420,640):
                if terminal:m[0x28]=0;d.bl_c64_test_write(0x28,0)
                for address,value in ((0xd1,255),(0xbf,25),(0xce,1)):
                    m[address]=value;d.bl_c64_test_write(address,value)
            d.bl_c64_world_input(input_,0)
            stopped=cpu.pc
            if stopped in (0xf47,0x1968,0x197d):
                if m[0x48]:m[0x48]-=1
            else:
                saved=(cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp,cpu.pc);m[0x44]=0;cpu.p&=~8
                run(0x15b8,{0x169d})
                pins=31^((1 if input_&4 else 0)|(2 if input_&8 else 0)|(4 if input_&1 else 0)|
                         (8 if input_&2 else 0)|(16 if input_&16 else 0))
                m[0xdc00],m[0xdc01]=(pins,31) if m[3] else (31,pins)
                run(0x169d,{0x1703})
                m[0xdc00]=m[0xdc01]=255
                run(0x1703,{0x179d});m[0xd01e]|=vic(m)
                cpu.a,cpu.x,cpu.y,cpu.p,cpu.sp,cpu.pc=saved
            d.bl_c64_field();compare(f'field{field}/IRQ')
            if not m[0x48] and cpu.pc not in (0x050f,0x0584):
                cpu.a=0;cpu.p=(cpu.p&~0x80)|2
                # $0F47 exits immediately when its actual IRQ counter is0.
                pc=cpu.pc if cpu.pc in (0xf47,0x1968,0x197d) else 0x1bc2
                run(pc,stops-{0x1bc2})
                d.bl_c64_world_step(0,0);compare(f'field{field}/main')
            if cpu.pc in (0x050f,0x0584):break
        rows.append(dict(players=players,human_yamo=human,terminal_life=terminal,fields=field+1,stop=f'${cpu.pc:04X}',
            source_steps=d.bl_c64_world_stat(0),life_events=d.bl_c64_world_stat(2),
            ram_sha256=hashlib.sha256(bytes(m)).hexdigest()))
    identity=json.loads((ROOT/'.tmp/source-actor-test/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for item in identity:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    report=dict(source_sha256=hashlib.sha256((ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()).hexdigest(),
        edition_verified=False,natural_playthrough=False,raster_exact=False,checks=rows,instructions=instructions,source_files=identity,
        seams=['Fixed external CIA pins; original $169D-$1702 executes in each game field','Field-sampled VIC opaque pixels and read-cleared latch','Main/announcement/Game Over field waits; CPU delay loops and raster IRQ stack phase are not certified'])
    out=ROOT/'reference/analysis/actor-chain-2026-10-26/integrated-controls.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS integrated source world:',len(rows),'modes;',instructions,'original instructions; all RAM at field/main boundaries')
if __name__=='__main__':main()
