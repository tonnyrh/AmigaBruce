"""Trace original combat bytes from an actual moving-route entry to its caller."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/".reference/tools/python"))
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
def sha(b):return hashlib.sha256(b).hexdigest()
def regs(cpu):
    p=cpu.p
    return bytes((cpu.a,cpu.x,cpu.y,p&1,(p>>1)&1,p>>7,p>>6&1,p>>3&1,cpu.sp,p>>2&1))
def frames(data):
    pos=65536;out=[]
    while pos<len(data):
        kind=data[pos];r=data[pos+1:pos+11];pos+=11;m=bytearray(data[:65536])
        last=0
        while True:
            at=int.from_bytes(data[pos:pos+2],"big");n=data[pos+2];pos+=3
            if n==0:break
            assert last<=at and at+n<=65536 and pos+n<=len(data)
            m[at:at+n]=data[pos:pos+n];pos+=n;last=at+n
        out.append((kind,r,m))
    assert pos==len(data) and [p[0] for p in out]==[0,3] and out[0][2]==data[:65536]
    return out
class Bus:
    def __init__(self,m):self.m=bytearray(m);self.latches=[];self.writes=collections.Counter()
    def __getitem__(self,i):
        v=self.m[i]
        if i==0xd01e:self.latches.append(v);self.m[i]=0
        return v
    def __setitem__(self,i,v):self.m[i]=v;self.writes[i]+=1
def audit(folder):
    data=(folder/"combat.bin").read_bytes();(_,r,m),(_,endregs,wanted)=frames(data)
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    assert sha(frozen)=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    dis=Disassembler(MPU(memory=frozen))
    variants=[]
    for cheat in (False,True):
        bus=Bus(m);cpu=MPU(memory=bus,pc=0x29c3)
        cpu.a,cpu.x,cpu.y=r[:3];cpu.sp=r[8]
        cpu.p=0x30|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
        ret=1+(m[0x100+((r[8]+1)&255)]|m[0x100+((r[8]+2)&255)]<<8)
        assert ret==0x1c26
        visited=collections.Counter();lengths={};scores=[];loops=[];edits=[];instructions=0;masked=0
        while cpu.pc!=ret:
            pc=cpu.pc
            masked+=int(bool(cpu.p&4))
            if pc not in lengths:lengths[pc]=dis.instruction_at(pc)[0]
            assert bus.m[pc:pc+lengths[pc]]==frozen[pc:pc+lengths[pc]],hex(pc)
            if pc==0x2b4e and cheat:
                edits.append([bus.m[0xbc],bus.m[0xbc]&1]);bus.m[0xbc]&=1
            if pc==0x3175:scores.append([cpu.a,cpu.x,bus.m[0x51],cpu.p>>2&1])
            if pc==0x2c51:
                x=cpu.x;loops.append([x,bus.m[0xbc+x],bus.m[0xd1+x],cpu.p>>2&1])
            visited[pc]+=1;cpu.step();instructions+=1
            assert instructions<2000000,(hex(pc),instructions)
        delta=sum(a!=b for a,b in zip(bus.m,wanted))
        variants.append(dict(invincibility=cheat,invincibility_writes=edits,instructions=instructions,
            ram_matches=delta==0,registers_match=regs(cpu)==endregs,different_bytes=delta,
            highest_visits=[(f"{k:04x}",v) for k,v in visited.most_common(12)],
            sid_requests=visited[0x2509],score_calls=scores,kill_reentries=loops,
            bit10_visits=visited[0x2bf9],decimal_visits=visited[0x32ee],vic_reads=bus.latches,
            score_before=int.from_bytes(m[0x41:0x44],"big"),score_after=int.from_bytes(bus.m[0x41:0x44],"big"),
            health_before=list(m[0xd1:0xd4]),health_after=list(bus.m[0xd1:0xd4]),i_entry=r[9],
            masked_instructions=masked,source_cycles=cpu.processorCycles))
    assert variants[1]["ram_matches"] and variants[1]["registers_match"],variants[1]
    return dict(source_sha256=sha(frozen),capture_sha256=sha(data),entry_sha256=sha(m),exit_sha256=sha(wanted),return_pc=f"{ret:04x}",variants=variants)
if __name__=="__main__":
    f=Path(sys.argv[1]);r=audit(f);(f/"audit.json").write_text(json.dumps(r,indent=2)+"\n")
    for v in r["variants"]:print(v["invincibility"],v["instructions"],v["ram_matches"],v["registers_match"],len(v["score_calls"]),len(v["kill_reentries"]),v["highest_visits"][:3])

