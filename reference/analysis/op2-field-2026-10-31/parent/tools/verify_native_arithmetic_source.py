"""Exhaustive binary arithmetic against two actual frozen instructions."""
import ctypes,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'reference/analysis/native-arithmetic-2026-10-31'
sys.path.insert(0,str(ROOT/'.reference/tools/python'))
from py65.devices.mpu6502 import MPU
SHA='092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8'

def main():
    source=(ROOT/'.reference/c64/work/untrained-memory.bin').read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
    assert source[0xa11:0xa13]==bytes([0x65,3]) and source[0x2de0:0x2de2]==bytes([0xe5,0xa1])
    lib=ctypes.CDLL(str(ROOT/'.tmp/native-arithmetic-host/math.dll'));lib.bl_math_host.argtypes=[ctypes.c_long]*4;lib.bl_math_host.restype=ctypes.c_ulong
    count=0
    for op,pc,operand in [(0,0xa11,3),(1,0x2de0,0xa1)]:
        cpu=MPU(memory=list(source))
        for old in range(256):
            for value in range(256):
                cpu.memory[operand]=value
                for carry in [0,1]:
                    cpu.pc=pc;cpu.a=old;cpu.p=0x30|carry|(((old^value)&7)<<1)|(((old+value)&1)<<6)|(((old>>1)&1)<<7)
                    # Force D=0; varying entry N/Z/V/I cannot leak into result.
                    cpu.p&=~8;before=cpu.p;cpu.step()
                    expected=cpu.a|((cpu.p&1)<<8)|(((cpu.p>>1)&1)<<9)|(((cpu.p>>7)&1)<<10)|(((cpu.p>>6)&1)<<11)
                    got=lib.bl_math_host(op,old,value,carry)
                    assert got==expected,(op,old,value,carry,hex(got),hex(expected))
                    assert not cpu.p&8 and cpu.p&4==before&4
                    count+=1
    def item(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    report=dict(status='passed_exhaustive_frozen_binary_arithmetic',cases=count,source_instructions=count,source_sha256=SHA,
        source_entries=['$0A11:65 03 ADC$03','$2DE0:E5 A1 SBC$A1'],mode='D=0 only; decimal path unchanged and not certified by this control',
        natural_playthrough=False,raster_exact=False,edition_verified=False,
        artifacts=[item(p) for p in [ROOT/'tools/verify_native_arithmetic_source.py',BASE/'math_bridge.c',BASE/'candidate/c64_rooms.c',ROOT/'.tmp/native-arithmetic-host/math.dll']])
    (BASE/'source-controls.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',count,'binary arithmetic inputs against actual frozen ADC/SBC instruction bytes')

if __name__=='__main__':main()
