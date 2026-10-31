"""Reexecute a captured native $5212 call and compare every stopped seam."""
import argparse, hashlib, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/".reference/tools/python"))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler

SOURCE_SHA="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
def sha(data):return hashlib.sha256(data).hexdigest()
def registers(cpu):
    p=cpu.p
    return bytes((cpu.a,cpu.x,cpu.y,p&1,(p>>1)&1,p>>7,(p>>6)&1,(p>>3)&1,cpu.sp,(p>>2)&1))
def records(data):
    base=data[:65536];pos=65536;out=[]
    while pos<len(data):
        kind=data[pos];regs=data[pos+1:pos+11];pos+=11;ram=bytearray(base);last=0
        while True:
            assert pos+3<=len(data)
            start=int.from_bytes(data[pos:pos+2],"big");count=data[pos+2];pos+=3
            if not count:break
            assert last<=start and start+count<=65536 and pos+count<=len(data)
            ram[start:start+count]=data[pos:pos+count];pos+=count;last=start+count
        out.append((kind,regs,ram))
    assert len(out)>4 and out[0][0]==0 and out[-1][0]==3 and out[0][2]==base
    return out
def delta(before,after):
    """Runs of changed bytes, joining adjacent edits with up to two gap bytes."""
    changes=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    data=bytearray();i=0
    while i<len(changes):
        start=end=changes[i];i+=1
        while i<len(changes) and changes[i]-end<=3 and changes[i]-start<255:
            end=changes[i];i+=1
        data.extend(start.to_bytes(2,"big")+bytes([end-start+1])+after[start:end+1])
    return data+bytes(3)
def audit(folder, write_replay=True):
    source=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    assert sha(source)==SOURCE_SHA
    dump=(folder/"capture.bin").read_bytes();points=records(dump)
    report=dict(line.split("=",1) for line in (folder/"op0-light.txt").read_text().splitlines() if "=" in line)
    assert report["capture_overflow"]=="0" and int(report["capture_records"])==len(points)
    assert report["room"]=="1" and report["source_fault"]=="0" and report["finished"]=="1"
    kind,r,entry=points[0];cpu=MPU(memory=bytearray(entry),pc=0x5212)
    cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
    cpu.p=0x30|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
    ret=1+(entry[0x100+((r[8]+1)&255)]|(entry[0x100+((r[8]+2)&255)]<<8))
    assert ret==0x1c10 and not r[7]
    regs0=registers(cpu)
    assert regs0==r
    index=0;instructions=0;visited=set();checks=[]
    dis=Disassembler(cpu)
    operands={0x52cc,0x52cd,0x5381,0x5382,0x539b,0x539c,0x53b5,0x53b6}
    modified=set()
    while instructions<100000:
        pc=cpu.pc
        event=1 if pc==0x5214 else 2 if pc==0x5380 and not cpu.y&7 else 3 if pc==ret else None
        if event:
            index+=1;kind,regs,wanted=points[index]
            assert kind==event and registers(cpu)==regs,(index,hex(pc),registers(cpu),regs)
            assert cpu.memory==wanted,(index,hex(pc),next((hex(i),x,y) for i,(x,y) in enumerate(zip(cpu.memory,wanted)) if x!=y))
            checks.append(dict(pc=f"{pc:04x}",actor=cpu.x if kind==1 else cpu.memory[0x50],
                               y=cpu.y,registers=regs.hex(),memory_sha256=sha(wanted)))
            if kind==3:break
        # Source modifies absolute operand bytes during this call. The opcode
        # itself at every executed PC must still be the frozen instruction.
        length,_=dis.instruction_at(pc)
        for at in range(pc,pc+length):
            if cpu.memory[at]!=source[at]:
                assert at!=pc and at in operands,hex(at)
                modified.add(at)
        visited.add(pc);cpu.step();instructions+=1
    else:raise AssertionError("source did not return")
    assert index==len(points)-1 and [p["actor"] for p in checks if p["pc"]=="5214"]==[2,1,0]
    # First record restores the final image to entry for repeated timing.
    tape=bytearray(entry);last=points[-1][2]
    for kind,regs,ram in points:
        tape.extend(bytes([kind])+regs+delta(last,ram));last=ram
    if write_replay:(folder/"replay.bin").write_bytes(tape)
    return dict(source_sha256=SOURCE_SHA,entry_sha256=sha(entry),capture_sha256=sha(dump),
        replay_sha256=sha(tape),replay_bytes=len(tape)-65536,return_pc=f"{ret:04x}",
        source_instructions=instructions,distinct_instruction_addresses=len(visited),patched_operands=sorted(map(hex,modified)),checkpoints=checks,
        actor_positions=list(entry[0x9e:0xa4]),poses=list(entry[0x4f4e:0x4f51]),
        body=list(cpu.memory[0xa7:0xaa]),feet=list(cpu.memory[0xb6:0xb9]))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("folder",type=Path);args=p.parse_args()
    report=audit(args.folder);(args.folder/"audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS",report["source_instructions"],"6502 instructions,",len(report["checkpoints"]),"whole-RAM/register boundaries,",report["replay_bytes"],"replay bytes")

