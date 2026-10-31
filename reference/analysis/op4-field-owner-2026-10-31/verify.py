"""Bind real-route and controlled source evidence to separate private executables."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / ".tmp/op4-owner"
DATA = HERE / "runs"
NORMAL = "e76c00f2a83b2871d85e7296e99b0f440f24debb5d9abf15311e3f8cbe17cd30"
GROUPS = {"reference": ("ref-move1","ref-move2","ref-still1","ref-still2"),
          "candidate": ("moving2","moving3","still2","still3"),
          "handoff": ("handoff-move1","handoff-move2","handoff-still1","handoff-still2"),
          "combat": ("combat-move1","combat-move2"), "meter": ("meter-move1","meter-move2")}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_run(path):
    return dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)

def save():
    DATA.mkdir(exist_ok=True)
    hashes = {}
    for mode, names in GROUPS.items():
        hashes[mode] = sha(WORK/mode/"bruce_amiga.exe")
        for name in names:
            out = DATA/name
            out.mkdir(exist_ok=True)
            assert sha(WORK/name/"bruce_amiga.exe") == hashes[mode]
            for filename in ("op0-light.txt","chain.bin"):
                if (WORK/name/filename).exists():
                    shutil.copyfile(WORK/name/filename,out/filename)
    hashes["proof"] = sha(WORK/"proof1/bruce_amiga.exe")
    assert hashes["proof"] == sha(WORK/"proof/bruce_amiga.exe")
    shutil.copyfile(WORK/"proof1/proof.bin",DATA/"proof.bin")
    shutil.copyfile(WORK/"proof/oracle.json",DATA/"oracle.json")
    return hashes

def check():
    summary = {}
    for mode,names in GROUPS.items():
        for name in names:
            r = read_run(DATA/name/"op0-light.txt")
            def num(key):return int(r[key])
            moving = "still" not in name
            assert (num("room"),num("enemy_mask"),num("input_route")) == (1,3,2 if moving else 0)
            assert num("warmup_steps") == num("steps") == 240 and num("visited_rooms")==1
            assert num("air_steps")== (96 if moving else 0) and r["active_loops"]=="0,0,0,240"
            assert num("source_fault")==num("audio_fault")==num("dma_fault")==0
            assert num("finished")==num("restored_os")==1 and num("chip_largest_loaded")>=49152
            metrics = ["pal_fields","pal_lines","work_lines","max_step_lines","audio_ticks","audio_missed"]
            if mode!="reference":
                assert num("owner_fault")==num("owner_slot_errors")==num("owner_legacy_ticks")==0
                assert num("owner_games")==num("owner_publications")==num("owner_voice_writes")//3
                assert num("owner_voice_writes")==3*num("owner_games")
                metrics += ["owner_games","owner_kage","owner_bands","owner_hw_duplicate",
                            "owner_hw_missing","owner_crossed_publish"]
                size = num("owner_records")
                trace = list(struct.iter_unpack(">8H",(DATA/name/"chain.bin").read_bytes()))
                assert len(trace)==size
                if trace:
                    assert trace[0][1:3]==(0x2c51,0x48c1) and trace[-1][2]==0x48c1
                    for a,b in zip(trace,trace[1:]):
                        assert (a[4],a[5])==(b[2],b[3])
                        assert (b[0]-a[0])%65536==int(b[3]<=a[3])
                if mode=="candidate":
                    assert bool(trace)==moving and num("audio_ticks")==num("owner_games")
                    assert (num("owner_last_due")-num("owner_first_due"))%0x1000000==num("owner_games")-1
                    span=(num("owner_last_hw")-num("owner_first_hw"))%0x1000000
                    assert span==num("owner_games")-1-num("owner_hw_duplicate")+num("owner_hw_missing")
                elif mode=="handoff":
                    assert num("owner_complete")==int(moving)
                    assert num("owner_games")==2*int(moving)
                elif mode=="meter":
                    assert num("owner_games")==num("owner_complete")==num("owner_records")==0
                else:
                    assert num("owner_complete")==2 and num("owner_games")>=2 and num("owner_kage")>0
                if mode in ("handoff","combat","meter"):
                    count=num("owner_all_count")
                    span=(num("owner_all_last")-num("owner_all_first"))%0x1000000
                    assert span==count-1-num("owner_all_duplicates")+num("owner_all_gaps")
                    assert num("audio_ticks")==count and num("audio_missed")==num("owner_all_gaps")
                    metrics += ["owner_complete","owner_all_count","owner_all_duplicates","owner_all_gaps"]
            summary[name] = {k:num(k) for k in metrics}
    assert struct.unpack(">III",(DATA/"proof.bin").read_bytes())==(2,0,1)
    oracle=json.loads((DATA/"oracle.json").read_text())
    assert [len(c["events"]) for c in oracle]==[9,9]
    for case in oracle:
        events=case["events"]
        assert sum(e["vector"]=="48c1" for e in events)==3
        assert {e["field"] for e in events}=={0xfffffe,0xffffff,0}
        assert all(len(bytes.fromhex(e["sid"]))==26 for e in events)
    return summary

if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--collect",action="store_true");args=p.parse_args()
    result=HERE/"result.json"
    hashes=save() if args.collect else json.loads(result.read_text())["private_executables"]
    data=dict(op2_normal_at_measurement=NORMAL,private_executables=hashes,routes=check(),
              evidence_sha256={p.relative_to(DATA).as_posix():sha(p) for p in sorted(DATA.rglob("*")) if p.is_file()})
    if args.collect:
        assert sha(ROOT/"amiga/out/bruce_amiga.exe")==NORMAL
        result.write_text(json.dumps(data,indent=2)+"\n")
    else:
        assert json.loads(result.read_text())==data
    print(f"PASS: {len(data['routes'])} routes, two full combat continuations, 18 controlled IRQ returns")
