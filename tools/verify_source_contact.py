"""Whole-RAM/register comparisons against actual $52AD/$537E/$5431 bytes.

Inputs/return frames are injected controls. No natural/raster parity claim.
"""
import ctypes,hashlib,itertools,json,random,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'
def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes()
    assert hashlib.sha256(source).hexdigest()==SHA
    code=(ROOT/'core/c64_rooms.c').read_text()
    if 'static void source_contact_classes(void)' in code:
        for flag,start,end in [(0x4f3c,0x545c,0x54ad),(0x4f3d,0x54b2,0x5503),(0x4f3e,0x5508,0x5547),(0x4f3f,0x554c,0x558b)]:
            line=next(s for s in code.splitlines() if s.strip().startswith(f'm[0x{flag:04x}]=(unsigned char)(('))
            operands=[int(x,16) for x in re.findall(r'm\[0x([0-9a-f]+)\]',line)][1:]
            assert operands==[int.from_bytes(source[pc+1:pc+3],'little') for pc in range(start,end,3)],hex(flag)
    lib=ctypes.CDLL(str(ROOT/'.tmp/source-contact-test/contact.dll'))
    buf=(ctypes.c_ubyte*65536)();regs=(ctypes.c_ubyte*10)()
    lib.bl_contact_run.argtypes=[ctypes.c_long]
    lib.bl_contact_return.restype=lib.bl_contact_fault.restype=ctypes.c_ulong
    rng=random.Random(2026102701);counts={};instructions=0;service_cases=0
    def check(m,entry,label,sp=253,decimal=None,trace=False):
        nonlocal instructions,service_cases
        # Full CPU status variation. Both helpers must preserve D/V/I.
        r=[rng.randrange(256) for _ in range(3)]+[rng.randrange(2) for _ in range(5)]+[sp,rng.randrange(2)]
        if decimal is not None:r[7]=decimal
        m[0x1fe:0x200]=b'\xfe\xff'
        if sp==251:m[0x1fc:0x1fe]=b'\x76\x52' # Actual nested row return frame; $542C discards it.
        lib.bl_contact_seed((ctypes.c_ubyte*65536).from_buffer_copy(m),(ctypes.c_ubyte*10)(*r))
        cpu=MPU(memory=m,pc=entry);cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=sp
        cpu.p=0x30|r[3]|(r[4]<<1)|(r[9]<<2)|(r[7]<<3)|(r[6]<<6)|(r[5]<<7)
        observed=[]
        if trace:lib.bl_contact_trace_enable()
        for _ in range(200000):
            if cpu.pc==0xffff:break
            if trace and cpu.pc==0x5380 and not(cpu.y&7):
                observed.append([cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1])
            cpu.step();instructions+=1
        else:raise AssertionError((label,'source escaped',hex(cpu.pc)))
        lib.bl_contact_run(entry);lib.bl_contact_copy(buf);lib.bl_contact_regs(regs)
        assert not lib.bl_contact_fault(),(label,'native fault',hex(lib.bl_contact_fault()))
        actual=bytes(buf);expected=bytes(m)
        assert actual==expected,(label,'RAM',[(hex(i),actual[i],expected[i]) for i in range(65536) if actual[i]!=expected[i]][:12])
        wanted=[cpu.a,cpu.x,cpu.y,cpu.p&1,(cpu.p>>1)&1,cpu.p>>7,(cpu.p>>6)&1,(cpu.p>>3)&1,cpu.sp,(cpu.p>>2)&1]
        assert list(regs)==wanted,(label,'registers',list(regs),wanted)
        assert lib.bl_contact_return()==0xffff,(label,'return',hex(lib.bl_contact_return()))
        if trace:
            service_cases+=1
            traced=(ctypes.c_ubyte*640)();count=lib.bl_contact_trace(traced)
            assert [list(traced[i*10:i*10+10]) for i in range(count)]==observed,(label,'service registers')
        key=f'${entry:04X}';counts[key]=counts.get(key,0)+1
    for phase,offset,pointer in itertools.product(range(4),range(8),(0x6800,0xcae0,0xcae1,0xcb00)):
        m=bytearray(source);m[0xcae0:0xcba0]=rng.randbytes(192)
        if pointer==0x6800:m[pointer:pointer+96]=rng.randbytes(96)
        m[0x1b]=phase;m[0x1c]=offset;m[0x52cc:0x52ce]=pointer.to_bytes(2,'little')
        check(m,0x52ad,f'align/{phase}/{offset}/{pointer:x}')
    for case in range(640):
        m=bytearray(source);m[0x4eed:0x4f40]=rng.randbytes(83);m[0x50]=case%3
        m[0xe6+case%3]=rng.choice([0,1,37,38,39,40,254,255]);m[0xe9+case%3]=case%24
        m[0x52]=rng.randrange(32);m[0x7c]=rng.randrange(256)
        if case%4==0:
            m[0x50e7:0x512f]=rng.randbytes(72)
        check(m,0x530a,f'pointers/{case}',decimal=0)
    for actor,pointer,yy in itertools.product(range(3),(0x0100,0x4eed,0x5370,0xfff0),(0,1,37,38,39,40,254,255)):
        m=bytearray(source);m[0x4eed:0x4f40]=rng.randbytes(83);m[0x50]=actor
        m[0xe6+actor]=yy;m[0xe9+actor]=10;m[0x52]=rng.randrange(32);m[0x7c]=rng.randrange(256)
        m[0x50e7+10]=pointer&255;m[0x50ff+10]=pointer>>8;m[0x5117+10]=0x4f
        check(m,0x530a,f'pointers/alias/{actor}/{pointer:x}/{yy}',decimal=0)
    for case in range(256):
        m=bytearray(source);m[0x4eed:0x4f40]=rng.randbytes(83)
        check(m,0x55ab,f'clear/{case}')
    for case in range(640):
        m=bytearray(source);m[0x4eed:0x4f40]=rng.randbytes(83);m[0x50]=case%3
        m[0xb6:0xb9]=rng.randbytes(3)
        # Include every on/off column-toggle combination, not just boolean flags.
        for i in range(3):m[0x4f32+i]=rng.choice([0,0,1,2,255])
        check(m,0x5431,f'classes/{case}')
    for index,toggles in itertools.product(range(69),range(8)):
        m=bytearray(source);m[0x4eed:0x4f40]=bytes(83);m[0x4eed+index]=1;m[0x50]=index%3
        for i in range(3):m[0x4f32+i]=(toggles>>i)&1
        check(m,0x5431,f'classes/single/{index}/{toggles}')
    for entry in [0x55e6,0x5658,0x56ca]:
        for case in range(96):
            m=bytearray(source);m[0x4eed:0x4f40]=rng.randbytes(83);m[0x50]=case%3
            check(m,entry,f'swap/{entry:x}/{case}')
    for case in range(640):
        m=bytearray(source);m[0xcae0:0xcb60]=rng.randbytes(128);m[0x4eed:0x4f40]=rng.randbytes(83)
        m[0x50]=case%3;m[0x95:0x98]=b'\0\0\0';start=(case%4)*8;m[0x52]=start
        m[0x4f38]=15+case%8;m[0x4f39]=21+case%8;m[0x4f3a]=start+8
        for i,operand in enumerate([0x5381,0x539b,0x53b5]):
            # The last group aliases glyph reads onto earlier column flag writes.
            pointer=0xa000+i*32 if case%5 else 0x4eed+i*23
            m[operand:operand+2]=pointer.to_bytes(2,'little')
            if pointer>=0xa000:m[pointer:pointer+32]=rng.randbytes(32)
        nested=start<m[0x4f39]<=m[0x4f3a]
        check(m,0x537e,f'rows/{case}',251 if nested else 253,trace=(start==0))
    # Cross multiple8-row services and the body/foot boundary in one call.
    # Actor0 makes the source non-local continuation return directly.
    for case in range(64):
        m=bytearray(source);m[0xcae0:0xcb60]=rng.randbytes(128);m[0x4eed:0x4f40]=rng.randbytes(83)
        m[0x50]=0;m[0x95:0x98]=b'\0\0\0';m[0x52]=0
        m[0x4f38]=15+case%8;m[0x4f39]=21+case%8;m[0x4f3a]=32
        for i,operand in enumerate([0x5381,0x539b,0x53b5]):
            pointer=0xa000+i*32 if case%2 else 0x4eed+i*23
            m[operand:operand+2]=pointer.to_bytes(2,'little')
            if pointer>=0xa000:m[pointer:pointer+32]=rng.randbytes(32)
        check(m,0x537e,f'rows/services/{case}',251,trace=True)
    files=['core/c64_rooms.c','core/c64_rooms.h','core/source_perf.h','core/c64_actor_programs.h',
        'tools/build_c64_rooms.py','tests/source_contact_bridge.c','tools/verify_source_contact.py','test-source-contact.ps1']
    report=dict(status='passed_original_byte_contact_controls',source_sha256=SHA,checks=sum(counts.values()),
        instructions=instructions,entries=counts,service_register_cases=service_cases,edition_verified=False,natural_playthrough=False,raster_exact=False,
        source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
    (ROOT/'reference/validation/source-contact-host.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report['checks'],'contact controls;',instructions,'original instructions;',counts)
if __name__=='__main__':main()
