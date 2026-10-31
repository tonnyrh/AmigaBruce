"""Install the exact measured pilot after the functional and timing gates pass."""
from pathlib import Path
import json,shutil,struct
from verify_diagnosis import read,sha,bound,verify_run
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
P=BASE/"pilot"
def promote():
    tests=read(P/"fixture/result.json")
    assert not tests["failures"] and tests["run"]["source_actor_fixture_cases"]=="53" and tests["run"]["frames"]=="1200"
    assert tests["run"]["restored_os"]=="1" and int(tests["run"]["chip_largest_loaded"])>=49152
    assert struct.unpack(">II",(P/"proof/wide-proof.bin").read_bytes())==(512,0)
    for ref,case in [("op2-reference-both-1","both-1"),("op2-reference-both-2","both-2"),("op2-reference-bare","both-bare")]:
        a=verify_run(BASE.parent/"op0-light-2026-10-31/runs"/ref)["run"]
        b=verify_run(P/"runs"/case)["run"]
        assert int(b["pal_fields"])<int(a["pal_fields"]) and int(b["audio_missed"])<int(a["audio_missed"])
    for e in tests["source_files"]+tests["build"]:bound(e["path"],e["sha256"])
    manifest=read(BASE/"parent/manifest.json")
    for path in ["core/c64_rooms.c","amiga-build.ps1","amiga/out/bruce_amiga.exe"]:assert sha(ROOT/path)==manifest[path]
    asm=ROOT/"amiga/vic_wide.s"
    assert not asm.exists(),"Review existing decoder before replacing"
    builder=ROOT/"amiga-build.ps1"
    raw=builder.read_bytes()
    old=b"'core/source_dma.c')"
    assert raw.count(old)==1
    shutil.copyfile(P/"vic_wide.s",asm)
    builder.write_bytes(raw.replace(old,b"'core/source_dma.c','amiga/vic_wide.s')"))
    shutil.copyfile(P/"c64_rooms.c",ROOT/"core/c64_rooms.c")
    print("Installed measured OP2 decoder")
if __name__=="__main__":promote()
