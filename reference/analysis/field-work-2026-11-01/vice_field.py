"""Fork a naturally reached C64 input slot, with physical raster IRQs active."""
import hashlib
import json
import socket
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/".tmp/field-work"
sys.path.insert(0,str(ROOT/"tools"))
from vice_binary import Vice

def main(port):
    manifest=json.loads((ROOT/"reference/manifest.json").read_text())
    ref=manifest["analysis_candidate"]
    baseline=ROOT/ref["baseline_snapshot_path"]
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==ref["baseline_snapshot_sha256"]
    raw=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    source=hashlib.sha256(raw).hexdigest()
    assert source=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    v=Vice(port);v.socket.settimeout(45);v.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
    def next_stop(pc,points):
        if pc in points:v.toggle(points[pc],False)
        following=v.run_stopped(0x71,struct.pack("<BH",0,1))
        if pc in points:v.toggle(points[pc],True)
        return following if following in points else v.run_stopped()
    def clear(points):
        for cp in points.values():v.command(0x13,struct.pack("<I",cp))
    def joystick(direction):
        v.resource_int("JoyPort1Device",37);v.joystick(direction)
    result={}
    try:
        for pose in ("ground","air"):
            pc=v.restore(baseline);assert pc==0x1bce
            assert v.memory(0x169d,0x1702)==raw[0x169d:0x1703]
            points={0x169d:v.checkpoint(0x169d)}
            joystick(255 if pose=="ground" else 246)
            for _ in range(250):
                pc=next_stop(pc,points);m=v.memory(0,0x108)
                airborne=m[0xbf] in (5,6,7,12,13,14)
                if m[0x104] and not m[3] and airborne==(pose=="air"):break
            else:raise AssertionError(("pose",pose,m[0xbf]))
            assert pc==0x169d;clear(points)
            snap=WORK/f"slot-{pose}.vsf";v.snapshot(snap)
            scenes=[]
            for timing in ("before","after","before"):
                pc=v.restore(snap);assert pc==0x169d
                joystick(247 if timing=="before" else 255)
                points={at:v.checkpoint(at) for at in (0x169d,0x1703)}
                rows=[]
                for i in range(3):
                    pc=next_stop(pc,points);assert pc==0x1703
                    m=v.memory(0x95,0xd3);regs=v.registers()
                    rows.append(dict(direction=m[3],fire=m[6],state=m[0xbf-0x95],
                                     x=m[9],y=m[12],raster=regs[0x35],cycle=v.history_clock()[1]))
                    if timing=="after" and i==0:v.joystick(247)
                    if i!=2:
                        pc=next_stop(pc,points);assert pc==0x169d
                clear(points)
                origin=rows[0]["cycle"]
                for r in rows:r["cycle"]-=origin
                scenes.append(rows)
            assert scenes[0]==scenes[2]
            assert [r["direction"] for r in scenes[0]]==[7,7,7]
            assert [r["direction"] for r in scenes[1]]==[15,7,7]
            assert all(19000<rows[1]["cycle"]<20500 for rows in scenes)
            result[pose]=dict(before=scenes[0],after=scenes[1],snapshot_sha256=hashlib.sha256(snap.read_bytes()).hexdigest())
    finally:v.close()
    data=dict(source_sha256=source,baseline_sha256=ref["baseline_snapshot_sha256"],emulator_sha256=manifest["emulator"]["executable_sha256"],cases=result)
    (WORK/"vice-slots.json").write_text(json.dumps(data,indent=2)+"\n")
    print({p:(v["before"][0]["state"],v["after"][1]["cycle"]) for p,v in result.items()})

if __name__=="__main__":main(int(sys.argv[1]))
