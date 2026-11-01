"""Archive the matched target measurements, including physical publication gaps."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]/".tmp/op-decimal"
GROUPS={"reference":("move-a","move-d","still-a","still-d"),
        "candidate":("move-b","move-c","still-b","still-c"),
        "reference-profile":("profile-a",),"candidate-profile":("profile-b",)}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def collect():
    runs=HERE/"runs";runs.mkdir(exist_ok=True)
    builds={}
    for mode,names in GROUPS.items():
        builds[mode]=sha(WORK/mode/"bruce_amiga.exe")
        for name in names:
            assert sha(WORK/name/"bruce_amiga.exe")==builds[mode]
            shutil.copyfile(WORK/name/"op0-light.txt",runs/(name+".txt"))
    for mode,name,file in (("proof","native-decimal","decimal-proof.bin"),("combat-proof","native-combat","proof.bin")):
        builds[mode]=sha(WORK/mode/"bruce_amiga.exe")
        assert sha(WORK/name/"bruce_amiga.exe")==builds[mode]
        assert sha(WORK/name/"cases.bin")==sha(WORK/mode/"cases.bin")
        shutil.copyfile(WORK/name/"proof.bin",runs/file)
    oracle=json.loads((WORK/"oracle.json").read_text())
    assert sha(WORK/"proof/cases.bin")==oracle["fixture_sha256"]
    shutil.copyfile(WORK/"oracle.json",runs/"source.json")
    return builds

def check():
    runs=HERE/"runs";rows={}
    oracle=json.loads((runs/"source.json").read_text())
    assert oracle["cases"]==5809 and oracle["distinct_scores"]==5041
    assert struct.unpack(">III",(runs/"decimal-proof.bin").read_bytes())==(oracle["cases"],0,1)
    assert struct.unpack(">III",(runs/"proof.bin").read_bytes())==(2,0,1)
    for names in GROUPS.values():
        for name in names:
            p=runs/(name+".txt")
            r=dict(s.split("=",1) for s in p.read_text().splitlines() if "=" in s)
            moving=not name.startswith("still")
            for k,v in dict(room=1,enemy_mask=3,steps=240,warmup_steps=240,input_route=2 if moving else 0,
                            air_steps=96 if moving else 0,source_fault=0,audio_fault=0,dma_fault=0,
                            restored_os=1,visited_rooms=1,finished=1).items():assert int(r[k])==v,(name,k)
            assert list(map(int,r["active_loops"].split(",")))==[0,0,0,int(r["loops"])]
            assert int(r["chip_largest_loaded"])>=49152 and r["paula_publications"]==r["audio_ticks"]
            rows[name]={k:int(r[k]) for k in ("pal_fields","work_lines","max_step_lines","paula_publications","paula_empty","paula_double","audio_missed")}
            rows[name]["report_sha256"]=sha(p)
            if name.startswith("profile"):
                assert r["decimal_calls"]=="53,53"
                rows[name]["decimal_lines"]=list(map(int,r["decimal_lines"].split(",")))
    return rows

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--collect",action="store_true");args=parser.parse_args()
    p=HERE/"measurements.json"
    builds=collect() if args.collect else json.loads(p.read_text())["builds"]
    data=dict(builds=builds,runs=check(),host_sha256=sha(HERE/"runs/source.json"),
              proof_sha256=sha(HERE/"runs/proof.bin"),decimal_proof_sha256=sha(HERE/"runs/decimal-proof.bin"))
    if args.collect:p.write_text(json.dumps(data,indent=2)+"\n")
    else:assert json.loads(p.read_text())==data
    print("PASS paired room routes, decimal timings, native BCD cases and combat returns")
