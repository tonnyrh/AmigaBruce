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
DECIMAL=STAGE.parent/"op-score-decimal-2026-10-31"

def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def digest(data):return hashlib.sha256(data).hexdigest()
def item(path):return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()))

def engine_hash(path):
    data,headers=sections(path)
    section=dict(headers)[".text.actor_code"]
    return digest(data[section[4]:section[4]+section[5]])

def decimal_sections(path):
    data,headers=sections(path)
    # Include the lookup table and the chosen implementation even when GCC
    # inlines a helper. ELF debug records contain local build paths.
    h=hashlib.sha256()
    for name,s in sorted(headers):
        if s[2]&2 and s[1]!=8:
            h.update(name.encode()+b"\0");h.update(data[s[4]:s[4]+s[5]])
    return h.hexdigest()

def record_build(stage=STAGE):
    decimal=stage==DECIMAL
    prior=read(STAGE/"build.json" if decimal else PRIOR/"measurements.json")
    probe=ROOT/(".tmp/op-decimal/candidate" if decimal else ".tmp/op-score/candidate")
    assert (probe/"c64_rooms.c").read_text()==(ROOT/"core/c64_rooms.c").read_text()
    assert (probe/"c64_actor_programs.h").read_text()==(ROOT/"core/c64_actor_programs.h").read_text()
    code=engine_hash(probe/"c64_rooms.o")
    assert code==engine_hash(ROOT/"amiga/out/c64_rooms.o")
    result=dict(parent_sha256=item(stage/"previous-delivery.json")["sha256"],
                engine_text_sha256=code,inputs=[item(ROOT/e["path"]) for e in prior["inputs"]],
                normal_build=[item(ROOT/e["path"]) for e in prior["normal_build"]])
    if decimal:
        result["core_sections_sha256"]=decimal_sections(probe/"c64_rooms.o")
        assert result["core_sections_sha256"]==decimal_sections(ROOT/"amiga/out/c64_rooms.o")
    (stage/"build.json").write_text(json.dumps(result,indent=2)+"\n")

def verify_current():
    decimal_stage=(DECIMAL/"build.json").is_file()
    stage=DECIMAL if decimal_stage else STAGE
    parent=read(stage/"previous-delivery.json");build=read(stage/"build.json")
    vic_measurement=read(PRIOR/"measurements.json")
    previous=read(STAGE/"build.json") if decimal_stage else vic_measurement
    assert parent["normal_build"]==previous["normal_build"] and parent["source_sha256"]==vic_measurement["c64_sha256"]
    assert item(stage/"previous-delivery.json")["sha256"]==build["parent_sha256"]
    assert item(ROOT/".reference/c64/work/untrained-memory.bin")["sha256"]==parent["source_sha256"]
    for entry in build["inputs"]+build["normal_build"]:
        assert item(ROOT/entry["path"])==entry,entry["path"]
    changed={a["path"] for a,b in zip(build["inputs"],previous["inputs"]) if a!=b}
    assert [a["path"] for a in build["inputs"]]==[a["path"] for a in previous["inputs"]]
    assert changed==({"core/c64_rooms.c"} if decimal_stage else {"core/c64_rooms.c","core/c64_actor_programs.h"})
    assert build["normal_build"][0]["sha256"]==build["normal_build"][-1]["sha256"]
    assert build["normal_build"][0]["sha256"]!=parent["normal_build"][0]["sha256"]
    measured=read(stage/"measurements.json")
    pairs=[]
    for a,b in (("move-a","move-b"),("move-c","move-d"),("still-a","still-b"),("still-c","still-d")):
        if decimal_stage and a.endswith("-c"):a,b=b,a  # Second pair ran candidate first.
        first,last=(measured["runs"][k] for k in (a,b))
        if a.startswith("move"):
            assert last["paula_empty"]<first["paula_empty"] and last["max_step_lines"]<first["max_step_lines"]
            assert last["work_lines"]<first["work_lines"]
        else:
            assert not last["paula_empty"] and last["pal_fields"]<=first["pal_fields"]*1.01
        pairs.append([first["pal_fields"],last["pal_fields"],first["paula_empty"],last["paula_empty"]])
    for name,r in measured["runs"].items():
        assert item(stage/"runs"/(name+".txt"))["sha256"]==r["report_sha256"]
    assert struct.unpack(">III",(stage/"runs/proof.bin").read_bytes())==(2,0,1)
    assert measured["proof_sha256"]==item(stage/"runs/proof.bin")["sha256"]
    assert measured["host_sha256"]==item(stage/"runs/source.json")["sha256"]
    if decimal_stage:
        assert struct.unpack(">III",(stage/"runs/decimal-proof.bin").read_bytes())==(5809,0,1)
        assert measured["decimal_proof_sha256"]==item(stage/"runs/decimal-proof.bin")["sha256"]
        oracle=read(stage/"runs/source.json")
        assert (oracle["source_sha256"],oracle["cases"],oracle["distinct_scores"])==(parent["source_sha256"],5809,5041)
        assert all(b<a for a,b in zip(measured["runs"]["profile-a"]["decimal_lines"],measured["runs"]["profile-b"]["decimal_lines"]))
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
        assert linked_pair_hash(elf,vic_measurement["kernel"])==vic_measurement["kernel"]["sha256"]
    proofs=reports+[PRIOR/"measurements.json",stage/"build.json",stage/"measurements.json",stage/"previous-delivery.json",
                    stage/"runs/source.json",stage/"runs/proof.bin",stage/"measure.py",Path(__file__).resolve()]
    if decimal_stage:
        proofs.extend([STAGE/"build.json",stage/"runs/decimal-proof.bin",stage/"proof.py",
                       stage/"build_decimal.py",stage/"decimal.c",stage/"native_check.h",stage/"proof_main.c"])
    for mode in ("cli","adf"):
        path=stage/"boot"/mode/"report.json";r=read(path)
        assert r["mode"]==mode and r["complete_menu"] and r["normal_exe_sha256"]==build["normal_build"][0]["sha256"]
        assert r["elf"]==item(ROOT/"amiga/out/bruce_amiga.elf")
        for e in r["artifacts"]:assert item(ROOT/e["path"])==e
        if mode=="adf":
            states=r["game_states"];assert len(states)>=2 and states[-1]["steps"]>states[0]["steps"]
            assert all(not s["fault"] and s["room"]==1 for s in states)
        proofs.append(path)
    result=dict(parent,normal_build=build["normal_build"],largest_chip_block=int(run["chip_largest_loaded"]),
                artifacts=[item(p) for p in proofs])
    key="score_decimal" if decimal_stage else "score_display"
    result.update(status=f"scoped_{key}_realtime_open");result[key]=pairs
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--record-build",action="store_true");p.add_argument("--decimal",action="store_true");args=p.parse_args()
    if args.record_build:record_build(DECIMAL if args.decimal else STAGE)
    else:
        result=verify_current()
        print("PASS",result["status"],"with PAL timing, native checks and normal boot")
