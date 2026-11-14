"""Reduce matched VICE and WinUAE observations without conflating their clocks."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]/".tmp/kage-paula"

def vice(mode):
    data=json.loads((WORK/f"vice-{mode}.json").read_text())
    assert data["routes"][0]==data["routes"][2]
    runs=[]
    for branch in data["routes"][:2]:
        rows=branch["observations"];ret=next(i for i,e in enumerate(rows) if e["pc"]==0x1c26)
        combat=rows[:ret+1]
        moves=[r for r in rows[ret:] if r["pc"]==0x17db and not r["actor"]]
        runs.append((combat,moves))
    c,m=runs[0];other=runs[1][1]
    first=next(([u["cycle"],v["cycle"]] for u,v in zip(m,other) if u["bruce"]!=v["bruce"]),None)
    assert all([e["score"] for e in branch if e["pc"]==0x3175]==[e["score"] for e in c if e["pc"]==0x3175] for branch,_ in runs)
    return dict(source=data["source_sha256"],base=data["base_snapshot_sha256"],fork=data["snapshot_sha256"],
        vice=data["vice_sha256"],fixture_writes_or_play_contacts=data["attempts"],
        begin=c[0]["health"],end=c[-1]["health"],score=[c[0]["score"],c[-1]["score"]],falls=[c[0]["falls"],c[-1]["falls"]],
        awards=sum(e["pc"]==0x3175 for e in c),reentries=sum(e["pc"]==0x2c51 for e in c),
        raster_game_irqs=sum(e["pc"]==0x48c1 for e in c),return_cycles=c[-1]["cycle"],
        first_joystick_slot_cycles=[next(e["cycle"] for e in combat if e["pc"]==0x1703) for combat,_ in runs],
        first_distinct_bruce_cycles=first,observations_per_direction=len(m),same_right_replay=True)

def response(left,right):
    def rows(folder):
        return [list(map(int,s.split("=")[1].split(","))) for s in (WORK/folder/"op0-light.txt").read_text().splitlines() if s.startswith("response")]
    a,b=rows(left),rows(right)
    def of(r,kind):return [x for x in r if x[0]==kind]
    assert a[0][2:]==b[0][2:] and a[0][0]==1
    ret=of(a,2)[0];assert ret[3]==of(b,2)[0][3]
    pos=lambda row:(row[2],row[4]&65535)
    first=next(([x[1]-a[0][1],y[1]-b[0][1]] for x,y in zip(of(a,4),of(b,4)) if pos(x)!=pos(y)),None)
    return dict(files=[left,right],health=[a[0][3]>>24,ret[3]>>24],
        score=[a[0][3]&0xffffff,ret[3]&0xffffff],bruce_at_entry=pos(a[0]),
        return_lines=[of(r,2)[0][1]-r[0][1] for r in (a,b)],
        first_joystick_slot_lines=[of(r,3)[0][1]-r[0][1] for r in (a,b)],
        first_distinct_bruce_lines=first,observations_per_direction=[len(of(r,4)) for r in (a,b)])

if __name__=="__main__":
    report=dict(vice={mode:vice(mode) for mode in ("match168","match207","play")},amiga={})
    for mode in ("response-old","response"):
        for step in (168,207):
            pair=([f"{mode}-full-{side}" for side in ("a","b")] if step==207 else [f"{mode}-{step}-{side}" for side in ("left","right")])
            report["amiga"][f"{mode}-{step}"]=response(*pair)
    for step in (168,207):
        report["amiga"][f"production-{step}"]=response(f"published-{step}-left",f"published-{step}-right")
    (WORK/"comparison.json").write_text(json.dumps(report,indent=2)+"\n")
