"""Budget/fairness stress control using the actual pre-fix copy function."""
import ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/scene-copy-test/copy.dll'))
    d.bl_copy_run.argtypes=[ctypes.c_long]*3;d.bl_copy_read.argtypes=[ctypes.c_long];d.bl_copy_read.restype=ctypes.c_ulong
    d.bl_present_probe.argtypes=[ctypes.c_long]*3;d.bl_present_probe.restype=ctypes.c_ulong
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
    r=dict(status='passed_budget_and_fairness_stress',natural_playthrough=False,controls=rows,presentation_controls=presentations,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (out/'copy-controls.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS copy/presentation fairness: rotating scan bounded; urgent strip first; persistent busy work cannot starve presentation')
if __name__=='__main__':main()
