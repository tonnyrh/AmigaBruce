"""Collect the paired A500 runs and verify the archived data independently."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-score"
GROUPS={"reference":("move-a","still-a","move-c","still-c"),
        "candidate":("move-b","still-b","move-d","still-d"),"profile":("timing-points",)}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def record():
    out=HERE/"runs";out.mkdir(exist_ok=True)
    hashes={}
    for mode,names in GROUPS.items():
        hashes[mode]=sha(WORK/mode/"bruce_amiga.exe")
        for name in names:
            assert sha(WORK/name/"bruce_amiga.exe")==hashes[mode]
            shutil.copyfile(WORK/name/"op0-light.txt",out/(name+".txt"))
    hashes["proof"]=sha(WORK/"native/bruce_amiga.exe")
    assert hashes["proof"]==sha(WORK/"proof/bruce_amiga.exe")
    assert sha(WORK/"native/cases.bin")==sha(ROOT/".tmp/op4-owner/proof1/cases.bin")
    shutil.copyfile(WORK/"native/proof.bin",out/"proof.bin")
    shutil.copyfile(WORK/"audit.json",out/"source.json")
    return hashes

def check():
    out=HERE/"runs"
    assert struct.unpack(">III",(out/"proof.bin").read_bytes())==(2,0,1)
    host=json.loads((out/"source.json").read_text())
    assert (host["display"],host["award"],host["extra_life"])==(256,30,12)
    rows={}
    for names in GROUPS.values():
        for name in names:
            path=out/(name+".txt")
            r=dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)
            moving=not name.startswith("still")
            for k,v in dict(room=1,enemy_mask=3,steps=240,warmup_steps=240,input_route=2 if moving else 0,
                            air_steps=96 if moving else 0,visited_rooms=1,source_fault=0,audio_fault=0,dma_fault=0,
                            finished=1,restored_os=1).items():
                assert int(r[k])==v,(name,k)
            active=list(map(int,r["active_loops"].split(",")))
            assert active==[0,0,0,int(r["loops"])] and int(r["chip_largest_loaded"])>=49152
            assert r["paula_publications"]==r["audio_ticks"]
            rows[name]={k:int(r[k]) for k in ("pal_fields","work_lines","max_step_lines","paula_empty","paula_double","audio_missed")}
            if name=="timing-points":
                assert int(r["award_events"])==106
                rows[name]["sections"]=list(map(int,r["award_sections"].split(",")))
            rows[name]["report_sha256"]=sha(path)
    return rows

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--collect",action="store_true");args=parser.parse_args()
    dest=HERE/"measurements.json"
    builds=record() if args.collect else json.loads(dest.read_text())["builds"]
    data=dict(builds=builds,runs=check(),host_sha256=sha(HERE/"runs/source.json"),proof_sha256=sha(HERE/"runs/proof.bin"))
    if args.collect:dest.write_text(json.dumps(data,indent=2)+"\n")
    else:assert json.loads(dest.read_text())==data
    print("PASS paired PAL timings, score boundaries and two native combat continuations")
