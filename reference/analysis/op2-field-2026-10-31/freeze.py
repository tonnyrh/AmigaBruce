"""Certify and preserve the OP2 parent's measured inputs before switching builds."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
PARENT=BASE/"parent"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))

def main():
    assert not PARENT.exists(),"Existing parent must be preserved"
    for script in ["verify_source_world_delivery","verify_source_optimization","verify_light_op0",
                   "verify_op1_row_walk","verify_native_cpu_experiments","verify_hardware_actors_probe"]:
        subprocess.run([sys.executable,ROOT/"tools"/(script+".py")],check=True)
    sources=[ROOT/"reference/validation"/(name+".json") for name in [
        "source-world-delivery","compact-actor-delivery","source-optimization","source-world-native",
        "contact-unroll","op0-light","native-cpu-experiments"]]
    sources += [ROOT/"reference/analysis/op1-row-walk-2026-10-31/result.json"]
    bound={}
    for p in sources:
        bound[p.relative_to(ROOT).as_posix()]=sha(p)
        data=read(p)
        for key in ["artifacts","source_files","build","normal_build"]:
            items=data.get(key,[])
            if isinstance(items,dict):items=[dict(path=k,sha256=v) for k,v in items.items()]
            for e in items:
                assert sha(ROOT/e["path"])==e["sha256"],e["path"]
                bound[e["path"]]=e["sha256"]
    extra=[ROOT/"amiga-build.ps1",ROOT/"docs/AMIGA_OPTIMIZATION_PLAN.md",
           ROOT/"core/c64_rooms.c",ROOT/"tools/verify_compact_actor_delivery.py",ROOT/"tools/verify_source_optimization.py",
           ROOT/"docs/parity/evidence/ACTOR-CHAIN-0001.json"]
    extra+=list((ROOT/"amiga/out").glob("*.o"))
    extra+=list((ROOT/"reference/analysis/actor-chain-2026-10-26").glob("*.json"))
    extra+=[ROOT/"reference/analysis/actor-chain-2026-10-26/native-final.txt"]
    for p in extra:bound[p.relative_to(ROOT).as_posix()]=sha(p)
    for path in sorted(bound):
        if path.startswith(("core/","amiga/","tools/","docs/","reference/validation/",".tmp/amiga-boot/",
                            "reference/analysis/actor-chain-2026-10-26/")) or path.endswith(".ps1") and "/" not in path:
            target=PARENT/path
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/path,target)
    (PARENT/"manifest.json").write_text(json.dumps(bound,indent=2,sort_keys=True)+"\n")
    print("Verified parent, bound",len(bound),"inputs")
if __name__=="__main__":main()
