"""Budget/fairness stress control using the actual pre-fix copy function."""
import ctypes,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    d=ctypes.CDLL(str(ROOT/'.tmp/scene-copy-test/copy.dll'))
    d.bl_copy_run.argtypes=[ctypes.c_long]*3;d.bl_copy_read.argtypes=[ctypes.c_long];d.bl_copy_read.restype=ctypes.c_ulong
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
    r=dict(status='passed_budget_and_fairness_stress',natural_playthrough=False,controls=rows,source_files=[dict(path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths])
    (out/'copy-controls.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('PASS copy budget/fairness: legacy bottom rows starve; rotating scan bounded; urgent strip copied first')
if __name__=='__main__':main()
