"""Execute frozen source bytes against the complete native actor-chain port.

RAM, controller signals and entry registers are explicit injected seams.
All64KiB, registers and control boundaries are checked, not a guessed model.
"""
import argparse,ctypes,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(r'C:\vscode\_EXT\AmigaBruceLee')
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
OUT=ROOT/'reference/analysis/flat-control-compact-2026-10-30/capacity1'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--section',choices=('actors','combat','world','all'),default='all');section=parser.parse_args().section
    b=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
    d=ctypes.CDLL(str(ROOT/'.tmp/flat-control-compact-cap1/actors.dll'))
    d.bl_c64_actor_test_call.argtypes=[ctypes.c_long]*2
    d.bl_actor_prepare.argtypes=[ctypes.c_long];d.bl_c64_load.argtypes=[ctypes.c_long]
    d.bl_c64_test_write.argtypes=[ctypes.c_long]*2
    d.bl_c64_fault.restype=ctypes.c_ushort;d.bl_c64_actor_return.restype=ctypes.c_ushort
    buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*13)()
    d.bl_actor_copy.argtypes=[ctypes.POINTER(ctypes.c_ubyte)];d.bl_c64_actor_registers.argtypes=[ctypes.POINTER(ctypes.c_ubyte)]
    def memory():d.bl_actor_copy(buf);return list(buf)
    def check(entry,actor=0,label=''):
        m=memory();cpu=MPU(memory=m,pc=entry);cpu.a=cpu.y=0;cpu.x=actor;cpu.p=0x30;cpu.sp=253;m[0x1fe:0x200]=[0xfe,0xff]
        stops={0xffff,0x0f47,0x1c32,0x050f,0x0584,0x1968,0x197d};life_events=0
        if entry not in (0x1bc2,0x1bee):stops.add(0x1bc2)
        for instructions in range(2000000):
            if cpu.pc in stops:break
            if cpu.pc==0x1818:life_events+=1
            cpu.step()
        else:raise AssertionError(('source escaped',label,hex(cpu.pc)))
        d.bl_c64_actor_test_call(entry,actor);native=memory();d.bl_c64_actor_registers(regs)
        actual=list(regs[:9]);expected=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp]
        diffs=[(hex(a),native[a],m[a]) for a in range(65536) if native[a]!=m[a]]
        assert not d.bl_c64_fault(),('native fault',label,hex(d.bl_c64_fault()),hex(cpu.pc),diffs[:10])
        assert not diffs,('RAM',label,hex(entry),hex(cpu.pc),diffs[:20])
        assert actual==expected,('registers',label,hex(entry),hex(cpu.pc),actual,expected)
        assert regs[9]==life_events and bool(regs[10])==(cpu.pc in (0x050f,0x0584)),('control boundary',label)
        assert regs[11]==((cpu.p>>2)&1),('interrupt flag',label)
        assert regs[12]==(1 if cpu.pc==0x1968 else 2 if cpu.pc==0x197d else 0),('Game Over boundary',label)
        return dict(label=label,entry=f'${entry:04X}',actor=actor,stop=f'${cpu.pc:04X}',instructions=instructions,
            ram_sha256=hashlib.sha256(bytes(m)).hexdigest(),registers=expected)
    rows=[]
    if section in ('actors','all'):
        d.bl_c64_reset();d.bl_c64_actor_seed();rows.append(check(0xf72,label='cold source init'))
        for room in range(20):
            d.bl_c64_load(room);rows.append(check(0xb30,label=f'R{room+1:02} post-loader'))
        for actor,state,counter,contact in itertools.product(range(3),range(28),(0,1,8,16),(0,1,4,5,8,12)):
            d.bl_actor_prepare(0)
            for a,v in [(0x95+actor,(1,0x81,0x41)[actor]),(0x9e+actor,80),(0xa1+actor,150),
                (0xa4+actor,1),(0xbf+actor,state),(0xce+actor,counter),(0xc2+actor,state),
                (0x106+actor,0),(0xb6+actor,contact),(0xa7+actor,contact&1),(0x98+actor,15),
                (0x9b+actor,1),(0xd1+actor,20)]:d.bl_c64_test_write(a,v)
            rows.append(check(0x1c5b,actor,label=f'actor{actor}/state{state}/counter{counter}/contact{contact}'))
    def fight(actors,latch,age=0,round_=0,mapping=(0,0,1,1,2)):
        d.bl_actor_prepare(0)
        for i,value in enumerate(mapping):d.bl_c64_test_write(0x4f40+i,value)
        d.bl_c64_test_write(0xd01e,latch);d.bl_c64_test_write(0x88,age);d.bl_c64_test_write(0x40,round_)
        for i,actor in enumerate(actors):
            d.bl_c64_test_write(0x95+i,(1,0x81,0x41)[i]);d.bl_c64_test_write(0x106+i,0);d.bl_c64_test_write(0x4fdb+i,0)
            for key,base in dict(x=0x9e,y=0xa1,state=0xbf,facing=0xa4,counter=0xce,health=0xd1,allowance=0x4f45).items():
                d.bl_c64_test_write(base+i,actor[key])
    if section in ('combat','all'):
        old=json.loads((ROOT/'reference/analysis/test-audit-2026-10-25/report.json').read_text())
        for case in old['fixtures']:
            if case['entry']!='$29C3':continue
            x=case['inputs'];fight(x['actors'],x['vic_d01e'],x['age_0088'],x['round_0040'],x['actor_mapping'])
            rows.append(check(0x29c3,label=case['name']))
        def f(x=60,y=150,state=0,counter=0,health=36):return dict(x=x,y=y,state=state,counter=counter,health=health,facing=1,allowance=2)
        for state,counter,age,health,front in itertools.product((12,13,14,17,22),(0,1,7,8,9,10,12,19),(0,25,32),(2,20),(False,True)):
            fight([f(state=state,counter=counter),f(x=68 if front else 52,health=health),f(x=150,y=40,health=7)],15,age)
            rows.append(check(0x29c3,label=f'fight/{state}/{counter}/{age}/{health}/{front}'))
    if section in ('world','all'):
        for room in range(20):
            d.bl_actor_prepare(room)
            for step in range(24):
                raw=15^(8 if step<8 else 1 if step<16 else 4)
                for _ in range(3):d.bl_c64_field()
                for a,v in [(0x98,raw),(0x9b,1),(0x99,15),(0x9c,1),(0xdc00,255),(0xdc01,255),(0xd01e,0)]:d.bl_c64_test_write(a,v)
                r=check(0x1bc2,label=f'R{room+1:02}/step{step}')
                rows.append(r)
                if r['stop']!='$1C32':break
    identity=json.loads((ROOT/'.tmp/flat-control-compact-cap1/compiled-sources.json').read_text(encoding='utf-8-sig'))
    for x in identity:assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(source_sha256=SHA,edition_verified=False,natural_playthrough=False,production_enabled=False,
        source_files=identity,section=section,checks=len(rows),rows=rows)
    (OUT/('report.json' if section=='all' else section+'-controls.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS complete source actor-chain controls:',len(rows),'all RAM/registers/boundaries')
if __name__=='__main__':main()
