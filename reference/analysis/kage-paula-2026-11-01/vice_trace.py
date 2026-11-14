"""Trace joystick-driven gameplay in PAL x64sc, with its own raster IRQs."""
import hashlib
import json
import socket
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/".tmp/kage-paula"
sys.path.insert(0,str(ROOT/"tools"))
from vice_binary import Vice

def main(mode,port):
    meta=json.loads((ROOT/"reference/manifest.json").read_text())
    base=ROOT/meta["analysis_candidate"]["baseline_snapshot_path"]
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(base)==meta["analysis_candidate"]["baseline_snapshot_sha256"]
    frozen=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    assert hashlib.sha256(frozen).hexdigest()=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    v=Vice(port);v.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);v.socket.settimeout(60);cp={}
    def clear():
        for identifier in cp.values():v.command(0x13,struct.pack("<I",identifier))
        cp.clear()
    def arm(points):
        for pc in points:cp[pc]=v.checkpoint(pc)
    def advance(pc):
        if pc in cp:v.toggle(cp[pc],False)
        nxt=v.run_stopped(0x71,struct.pack("<BH",0,1))
        if pc in cp:v.toggle(cp[pc],True)
        return nxt if nxt in cp else v.run_stopped()
    def row(pc):
        r=v.registers();m=v.memory(0,0x110)
        return dict(pc=pc,cycle=v.history_clock()[1],raster=r[0x35],subline=r[0x36],
                    xreg=r[1],acc=r[0],health=list(m[0xd1:0xd4]),score=int.from_bytes(m[0x41:0x44],"big"),
                    flag=m[0xbe],actor=m[0x51],joy=m[0x98],bruce=[m[i] for i in (0x9e,0xa1,0xa4,0xbf,0xc2,0xce)],falls=m[0x28])
    def trace(snap):
        results=[]
        for direction in (247,251,247):
            clear();pc=v.restore(snap);assert pc==0x2c03
            v.resource_int("JoyPort1Device",37);v.joystick(direction)
            arm((0x3175,0x2c51,0x48c1,0x169d,0x1703,0x1c26,0x17db,0x1bce))
            obs=[row(pc)]
            # CPU history is external to the snapshot. Execute the entry
            # instruction before using its recorded emulated clock.
            pc=v.run_stopped(0x71,struct.pack("<BH",0,1));assert pc==0x2c05
            last,origin=v.history_clock();assert last==0x2c03
            obs[0]["cycle"]=origin
            ret=False;moves=0
            for _ in range(3000):
                pc=advance(pc);event=row(pc)
                if pc==0x1c26:ret=True
                if pc==0x17db and v.memory(0x51,0x51)[0]==0 and ret:moves+=1
                obs.append(event)
                if moves>=16:break
            assert ret and moves==16
            start=obs[0]["cycle"]
            for e in obs:e["cycle"]-=start
            results.append(dict(input=direction,observations=obs))
            print("VICE input",direction,"return",next(e for e in obs if e["pc"]==0x1c26)["cycle"],"cycles",flush=True)
        (WORK/("vice-"+mode+"-routes.json")).write_text(json.dumps(results,indent=2))
        assert results[0]==results[2]
        return results
    try:
        snap=WORK/("vice-"+mode+".vsf");attempts=[]
        pc=v.restore(base);assert pc==0x1bce
        for a,b in ((0x2bf9,0x2c54),(0x169d,0x1703),(0x3175,0x3184)):
            assert v.memory(a,b-1)==frozen[a:b]
        v.resource_int("JoyPort1Device",37);v.resource_int("JoyPort2Device",1);v.joystick(255)
        if mode=="resume-play":
            mode="play";snap=WORK/"vice-play.vsf"
            found=json.loads((WORK/"vice-search.json").read_text())
            assert found["ticks"]==3047 and found["pc"]==0x2c03
            attempts=found["attempts"];assert v.restore(snap)==0x2c03
        elif mode=="play":
            arm((0x1bce,0x2c03,0x050f,0x0584))
            tick=0
            for _ in range(6000):
                if pc==0x1bce:
                    if tick%20==0:v.joystick((247,250,251,246)[(tick//20)%4])
                    tick+=1
                if pc==0x2c03:
                    e=row(pc);attempts.append(dict(tick=tick,actor=e["actor"],hp=e["health"]))
                    if e["actor"]==2 and (e["health"][2]-5)&128:break
                if pc in (0x050f,0x0584) or tick>=3200:break
                pc=advance(pc)
            print("joystick search",tick,hex(pc),attempts[-10:])
            (WORK/"vice-search.json").write_text(json.dumps(dict(ticks=tick,pc=pc,attempts=attempts),indent=2))
            if pc!=0x2c03:return
        elif mode in ("match168","match207"):
            # Reach Kage's ordinary contact test with the real game stack,
            # VIC, CIAs and raster phase. Set only the specified fixture
            # data at that test, then leave the CPU and IRQs to run.
            sys.path.insert(0,str(ROOT/"reference/analysis/op4-moving-audio-2026-10-31"))
            from audit_combat import frames,Bus,MPU
            file=ROOT/".reference/c64/work/op4-moving-audio-2026-10-31"/("combat"+mode[5:])/"combat.bin"
            _,r,ram=frames(file.read_bytes())[0];b=Bus(ram);u=MPU(memory=b,pc=0x29c3)
            u.a,u.x,u.y=r[:3];u.sp=r[8];u.p=0x30|r[3]|r[4]<<1|r[5]<<7|r[6]<<6|r[7]<<3|r[9]<<2
            for _ in range(10000):
                if u.pc==0x2b4e:b.m[0xbc]&=1 # captured Amiga debug option
                if u.pc==0x2c03 and u.x==2:break
                u.step()
            assert u.pc==0x2c03 and b.m[0xbe]==0x90
            arm((0x2bf9,0x1bce))
            for _ in range(3000):
                pc=advance(pc)
                if pc==0x2bf9 and v.registers()[1]==2:break
            assert pc==0x2bf9 and v.memory(0x51,0x51)==b"\x02"
            for lo,hi in ((0xd3,0xd3),(0xbe,0xbe),(0x41,0x43),(0x438e,0x4394),(0x28,0x28)):
                val=b.m[lo:hi+1];old=v.memory(lo,hi)
                v.command(2,struct.pack("<BHHBH",0,lo,hi,0,0)+val)
                assert v.memory(lo,hi)==val
                attempts.append(dict(address=lo,before=old.hex(),after=val.hex()))
            clear();arm((0x2c03,));pc=advance(pc);assert pc==0x2c03
        else:raise ValueError(mode)
        clear()
        if sys.argv[1]!="resume-play":v.snapshot(snap)
        out=dict(mode=mode,base_snapshot_sha256=digest(base),snapshot_sha256=digest(snap),attempts=attempts,
                 vice_sha256=meta["emulator"]["executable_sha256"],source_sha256=hashlib.sha256(frozen).hexdigest(),routes=trace(snap))
        (WORK/("vice-"+mode+".json")).write_text(json.dumps(out,indent=2)+"\n")
    finally:
        clear();v.close()

if __name__=="__main__":main(sys.argv[1],int(sys.argv[2]))
