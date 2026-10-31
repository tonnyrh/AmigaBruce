"""Budget/fairness stress control using the actual pre-fix copy function."""
import ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/scene-copy-test/copy.dll'))
    d.bl_copy_run.argtypes=[ctypes.c_long]*3;d.bl_copy_read.argtypes=[ctypes.c_long];d.bl_copy_read.restype=ctypes.c_ulong
    d.bl_present_probe.argtypes=[ctypes.c_long]*3;d.bl_present_probe.restype=ctypes.c_ulong
    d.bl_present_retry.argtypes=[ctypes.c_long]*4;d.bl_present_retry.restype=ctypes.c_ulong
    d.bl_present_retry_now.argtypes=[ctypes.c_long]*2;d.bl_present_retry_now.restype=ctypes.c_ulong
    retries=[]
    for pending in [0,1]:
        for cost in [100,160,260,800]:
            for age in range(5):
                for deferrals in range(5):
                    hold=d.bl_present_retry(cost,pending,age,deferrals)
                    if age>=3 or deferrals>=3:assert not hold
                    if cost<=140:assert not hold
    for held in [0,1]:
        for streak in range(6):assert bool(d.bl_present_retry_now(held,streak))==(bool(held) and streak==1)
    for cost in [160,260,800]:
        lines=streak=last=published=retry_count=max_streak=0
        for attempt in range(90):
            lines+=cost;age=lines//312-last
            hold=d.bl_present_retry(cost,1,age,streak)
            streak=streak+1 if hold else 0;max_streak=max(max_streak,streak)
            if d.bl_present_retry_now(hold,streak):retry_count+=1;continue
            phase=lines%312;lines+=(300-phase) if phase<300 else (612-phase)
            if not hold:published+=1;last=lines//312
        assert max_streak<=3 and published>=90//4
        retries.append(dict(cost=cost,attempts=90,published=published,immediate_retries=retry_count,max_deferrals=max_streak))
    presentations=[]
    for pending in [0,1]:
        assert not d.bl_present_probe(100,pending,0)
        for costs in [[260]*90,[800]*90,[160,240,600,100]*30]:
            stamp=last=0;published=[]
            for cost in costs:
                stamp+=max(1,(cost+312)//313)
                age=(stamp-last)&0xffffff
                hold=d.bl_present_probe(cost,pending,age)
                if age>=3:assert not hold
                if not hold:published.append(stamp);last=stamp
            assert len(published)>=len(costs)//3
            presentations.append(dict(pending=pending,decisions=len(costs),published=len(published),max_work_lines=max(costs)))
        assert not d.bl_present_probe(800,pending,((1-0xfffffe)&0xffffff)) # timer wrap
    rows=[]
    for legacy,urgent in ((1,0),(0,0),(0,1)):
        d.bl_copy_run(legacy,urgent,90);v=[d.bl_copy_read(i) for i in range(4)]
        assert v[1]<=5000
        if legacy:assert v[0]==90 and not v[2] and not v[3]
        else:assert v[0]<=7 and v[2]>=84 and v[3]>=84
        if urgent:assert v[2]==90
        rows.append(dict(legacy=bool(legacy),urgent=bool(urgent),max_pending_calls=v[0],max_bytes=v[1],row23_last_copy=v[2],row24_last_copy=v[3]))
    paths=['core/scene_copy.h','tests/scene_copy_bridge.c','test-scene-copy.ps1','tools/verify_scene_copy.py','reference/validation/history/before-room10-electric-2026-10-26/amiga/main.c']
    out=ROOT/'reference/analysis/room10-electric-2026-10-26';out.mkdir(parents=True,exist_ok=True)
    r=dict(status='passed_budget_and_fairness_stress',natural_playthrough=False,controls=rows,presentation_controls=presentations,retry_controls=retries,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (out/'copy-controls.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS copy/presentation fairness: rotating scan bounded; urgent strip first; persistent busy work cannot starve presentation')
if __name__=='__main__':main()
