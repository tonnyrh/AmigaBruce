"""Exact candidate position checks at a documented game-logic seam.

No tolerance or fitted time shift. Sampled direction from boundary N feeds the
logic interval N..N+1. X conversion is 2 pixels/C64 unit and a fixed -24 anchor
offset from registered spawn. It is not fitted independently per scenario.
Reports all discrepancies; selected windows are regression gates, not full M2.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
# Windows end before known collision differences; all other rows still reported.
GATES={"idle":48,"right":48,"left":7,"standing-jump":48,
       "moving-jump":26,"reverse":48,"held-jump":48,
       "climb":48,"climb-down":48,"central-climb":80,"central-climb-down":80,
       "central-top-held":180,"central-top-release":132,
       "upper-jump-early":132,"upper-jump-edge":132,
       "prone-hold-release":48,"prone-direction":32,"prone-jump":40,"net-top-down":160,
       "fire-tap":48,"fire-hold":48,"up-fire":48,"down-fire":48,"right-fire":24}


def compare(executable, traces, output):
    summary=json.loads((traces/"summary.json").read_text(encoding="utf-8"))
    report={"capture_id":summary["capture_id"],"status":"candidate_position_regression",
        "primary_edition_verified":False,"full_m2_parity":False,
        "alignment":"previous boundary sampled_direction -> one core step; x=2*C64_x-24; y=C64_y",
        "comparison":"exact integer positions; no tolerance or fitted offset",
        "core_sha256":hashlib.sha256((ROOT/"core/game.c").read_bytes()).hexdigest(),
        "trace_summary_sha256":hashlib.sha256((traces/"summary.json").read_bytes()).hexdigest(),
        "source_files":[{"path":name,"sha256":hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}
            for name in ("core/game.c","core/room_geometry.h","core/game.h","tests/core_trace.c","tools/compare_movement.py","test-parity.ps1")],
        "scenarios":[]}
    failures=[]
    for scenario in summary["scenarios"]:
        name=scenario["name"]
        path=traces/f"{name}.csv"
        if hashlib.sha256(path.read_bytes()).hexdigest()!=scenario["sha256"]:
            raise ValueError(f"Trace hash mismatch: {name}")
        with path.open(newline="",encoding="utf-8") as stream:
            rows=[{key:int(value) for key,value in row.items()} for row in csv.DictReader(stream)]
        inputs="\n".join(str(row["sampled_direction"])+","+str(row["sampled_fire"]) for row in rows[:-1])+"\n"
        run=subprocess.run([str(executable.resolve())],input=inputs,text=True,capture_output=True,check=True)
        actual=[list(map(int,line.split(","))) for line in run.stdout.splitlines()]
        if len(actual)!=len(rows):
            raise ValueError(f"Wrong core sample count: {name}")
        differences=[]
        pose_differences=[]
        attack_differences=[]
        for row,position in zip(rows,actual):
            expected=[row["target_x_halfpixels"]*2-24,row["target_y"]]
            if position[:2]!=expected:
                differences.append({"tick":row["tick"],"expected":expected,"actual":position[:2]})
            if name.startswith("prone-"):
                expected_prone=int(row["next_state"]==26)
                if position[3]!=expected_prone:
                    pose_differences.append({"tick":row["tick"],"expected":expected_prone,"actual":position[3]})
            if summary['capture_id']=='MACHINE-0005':
                expected_attack=1 if row['next_state']==17 else 2 if row['next_state'] in (12,13) else 0
                if position[4]!=expected_attack:
                    attack_differences.append({'tick':row['tick'],'expected':expected_attack,'actual':position[4]})
        gate=GATES.get(name)
        gate_pass=(gate is None or not any(d["tick"]<=gate for d in differences+attack_differences)) and not pose_differences
        if not gate_pass:failures.append(name)
        item={"name":name,"samples":len(rows),"exact_position_matches":len(rows)-len(differences),
              "gate_through_tick":gate,"gate_passed":gate_pass if gate is not None else None,
              "differences":differences}
        if name.startswith("prone-"):
            item["target_posture_reference"]="C64 next_state == 26; target posture, not sprite-animation phase"
            item["pose_differences"]=pose_differences
        if summary['capture_id']=='MACHINE-0005':
            item['attack_differences']=attack_differences
            item['attack_reference']='C64 next_state 17 punch, 12/13 flying kick; logical targets, not sprite phase'
        report["scenarios"].append(item)
        print(f"{name}: {item['exact_position_matches']}/{len(rows)} exact; gate="+
              ("not claimed" if gate is None else ("PASS" if gate_pass else "FAIL")))
    report["regression_gates_passed"]=not failures
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if failures:raise SystemExit("Candidate regression failed: "+", ".join(failures))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable",type=Path)
    parser.add_argument("--traces",type=Path,default=ROOT/"reference/traces/MACHINE-0001")
    parser.add_argument("--output",type=Path,default=ROOT/"reference/validation/candidate-movement.json")
    args=parser.parse_args()
    compare(args.executable,args.traces,args.output)
