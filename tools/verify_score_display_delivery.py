"""Check the measured score path against the normal build and native controls."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_vic_native_kernels import sections
from verify_vic_pair_delivery import linked_pair_hash

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"reference/analysis/op-score-2026-10-31"
PRIOR=STAGE.parent/"op2-vic-pairs-2026-10-31"

def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def digest(data):return hashlib.sha256(data).hexdigest()
def item(path):return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()))

def engine_hash(path):
    data,headers=sections(path)
    section=dict(headers)[".text.actor_code"]
    return digest(data[section[4]:section[4]+section[5]])

def record_build():
    prior=read(PRIOR/"measurements.json")
    probe=ROOT/".tmp/op-score/candidate"
    assert (probe/"c64_rooms.c").read_text()==(ROOT/"core/c64_rooms.c").read_text()
    assert (probe/"c64_actor_programs.h").read_text()==(ROOT/"core/c64_actor_programs.h").read_text()
    code=engine_hash(probe/"c64_rooms.o")
    assert code==engine_hash(ROOT/"amiga/out/c64_rooms.o")
    result=dict(parent_sha256=item(STAGE/"previous-delivery.json")["sha256"],
                engine_text_sha256=code,inputs=[item(ROOT/e["path"]) for e in prior["inputs"]],
                normal_build=[item(ROOT/e["path"]) for e in prior["normal_build"]])
    (STAGE/"build.json").write_text(json.dumps(result,indent=2)+"\n")

def verify_current():
    parent=read(STAGE/"previous-delivery.json");build=read(STAGE/"build.json")
    previous=read(PRIOR/"measurements.json")
    assert parent["normal_build"]==previous["normal_build"] and parent["source_sha256"]==previous["c64_sha256"]
    assert item(STAGE/"previous-delivery.json")["sha256"]==build["parent_sha256"]
    assert item(ROOT/".reference/c64/work/untrained-memory.bin")["sha256"]==parent["source_sha256"]
    for entry in build["inputs"]+build["normal_build"]:
        assert item(ROOT/entry["path"])==entry,entry["path"]
    changed={a["path"] for a,b in zip(build["inputs"],previous["inputs"]) if a!=b}
    assert [a["path"] for a in build["inputs"]]==[a["path"] for a in previous["inputs"]]
    assert changed=={"core/c64_rooms.c","core/c64_actor_programs.h"}
    assert build["normal_build"][0]["sha256"]==build["normal_build"][-1]["sha256"]
    assert build["normal_build"][0]["sha256"]!=parent["normal_build"][0]["sha256"]
    measured=read(STAGE/"measurements.json")
    pairs=[]
    for a,b in (("move-a","move-b"),("move-c","move-d"),("still-a","still-b"),("still-c","still-d")):
        first,last=(measured["runs"][k] for k in (a,b))
        if a.startswith("move"):
            assert last["paula_empty"]<first["paula_empty"] and last["max_step_lines"]<first["max_step_lines"]
            assert last["work_lines"]<first["work_lines"]
        else:
            assert not last["paula_empty"] and last["pal_fields"]<=first["pal_fields"]*1.01
        pairs.append([first["pal_fields"],last["pal_fields"],first["paula_empty"],last["paula_empty"]])
    for name,r in measured["runs"].items():
        assert item(STAGE/"runs"/(name+".txt"))["sha256"]==r["report_sha256"]
    assert struct.unpack(">III",(STAGE/"runs/proof.bin").read_bytes())==(2,0,1)
    assert measured["host_sha256"]==item(STAGE/"runs/source.json")["sha256"]
    reports=[ROOT/"reference/analysis/actor-chain-2026-10-26"/name for name in ("report.json","integrated-controls.json")]
    reports += [ROOT/"reference/validation"/name for name in ("source-world-native.json","source-score-host.json","source-vic-host.json")]
    actor,world,native,decimal,vic=map(read,reports)
    assert len(actor["rows"])==3034 and len(world["checks"])==5 and world["instructions"]==7055873
    assert decimal["checks"]==2852 and vic["calls"]==8741 and vic["pair_basis_cases"]==48**3
    for r in (actor,world,native,decimal,vic):
        for e in r["source_files"]:assert item(ROOT/e["path"])==e,e["path"]
    for e in native["build"]:assert item(ROOT/e["path"])==e
    run=native["run"]
    assert not native["failures"] and (run["frames"],run["source_actor_fixture_cases"],run["restored_os"])==("1200","53","1")
    assert int(run["chip_largest_loaded"])>=49152
    for elf in (ROOT/"amiga/out/bruce_amiga.elf",ROOT/next(e["path"] for e in native["build"] if e["path"].endswith(".elf"))):
        assert linked_pair_hash(elf,previous["kernel"])==previous["kernel"]["sha256"]
    proofs=reports+[PRIOR/"measurements.json",STAGE/"build.json",STAGE/"measurements.json",STAGE/"previous-delivery.json",
                    STAGE/"runs/source.json",STAGE/"runs/proof.bin",STAGE/"measure.py",Path(__file__).resolve()]
    for mode in ("cli","adf"):
        path=STAGE/"boot"/mode/"report.json";r=read(path)
        assert r["mode"]==mode and r["complete_menu"] and r["normal_exe_sha256"]==build["normal_build"][0]["sha256"]
        assert r["elf"]==item(ROOT/"amiga/out/bruce_amiga.elf")
        for e in r["artifacts"]:assert item(ROOT/e["path"])==e
        if mode=="adf":
            states=r["game_states"];assert len(states)>=2 and states[-1]["steps"]>states[0]["steps"]
            assert all(not s["fault"] and s["room"]==1 for s in states)
        proofs.append(path)
    return dict(parent,status="scoped_score_display_realtime_open",score_display=pairs,
                normal_build=build["normal_build"],largest_chip_block=int(run["chip_largest_loaded"]),
                artifacts=[item(p) for p in proofs])

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--record-build",action="store_true");args=p.parse_args()
    if args.record_build:record_build()
    else:verify_current();print("PASS source score display, PAL timing, native checks and normal boot")
