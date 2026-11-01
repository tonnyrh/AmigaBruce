"""Validate the route, disjoint time intervals, empty pass and independent outer timer."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-sprite-cost"
MASKS={"solo":0,"yamo":1,"kage":2,"both":3}
LABELS=[f"{build}-{role}-{repeat}" for build in ("ref","detail") for role in MASKS
        for repeat in ("ab" if role in ("solo","both") else "a")]+["outer-solo","outer-both"]
PHASES=["setup","service","destination","pose","copy"]
MACHINE=dict(cpu_model="68000",cpu_speed="real",cycle_exact="true",cpu_cycle_exact="true",
             cpu_memory_cycle_exact="true",blitter_cycle_exact="true",ntsc="false",chipset="ocs",
             chipmem_size="1",bogomem_size="2",fastmem_size="0")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def collect():
    runs=HERE/"runs";runs.mkdir(exist_ok=True)
    builds={name:sha(WORK/name/"bruce_amiga.exe") for name in ("reference","profile","outer")}
    for label in LABELS:
        kind,role,*_=label.split("-")
        assert sha(WORK/label/"bruce_amiga.exe")==builds[{"ref":"reference","detail":"profile","outer":"outer"}[kind]]
        assert (WORK/label/"op0-route.bin").read_bytes()==bytes([0,MASKS[role],0,0,0,240,0,240])
        cfg=dict(line.split("=",1) for line in (WORK/label/"a500.uae").read_text().splitlines() if "=" in line)
        assert all(cfg.get(k)==v for k,v in MACHINE.items()),label
        shutil.copyfile(WORK/label/"op0-light.txt",runs/(label+".txt"))
    shutil.copyfile(WORK/"source.json",runs/"source.json")
    return builds

def route(label):
    path=HERE/"runs"/(label+".txt")
    r=dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)
    num=lambda k:int(r[k])
    array=lambda k:list(map(int,r[k].split(",")))
    kind,role,*_=label.split("-");mask=MASKS[role]
    for k,v in dict(room=1,enemy_mask=mask,input_route=0,steps=240,warmup_steps=240,air_steps=0,
                    climb_steps=0,visited_rooms=1,finished=1,restored_os=1,source_fault=0,
                    dma_fault=0,audio_fault=0,source_profile=0).items():assert num(k)==v,(label,k)
    active=[0]*4;active[mask]=num("loops")
    assert array("active_loops")==active and num("chip_largest_loaded")>=49152
    assert num("restriction_writesets")==num("loops")*(2-(mask&1)-(mask>>1))
    assert num("paula_publications")==num("audio_ticks")
    out={k:num(k) for k in ("pal_fields","work_lines","pal_lines","wait_lines","loops","paula_empty","paula_double")}
    out["report_sha256"]=sha(path)
    if kind=="ref":return out
    if kind=="outer":
        assert num("outer_calls")==240 and num("outer_lines")>=num("outer_blank") and num("outer_awards")==0
        out["due"]=num("outer_due");out["paid"]=num("outer_paid")
        out["driver_lines_per_step"]=(num("outer_lines")-num("outer_blank"))/240
        return out
    assert num("sprite_steps")==240 and num("sprite_samples")==60
    assert num("sprite_awards")==num("sprite_score_changes")==num("sprite_errors")==0
    assert array("sprite_active")==[240,240*(mask&1),240*(mask>>1)]
    sample=num("sprite_samples")
    raw=[array(f"sprite_lines_0_{i}") for i in range(3)]
    blank=[array(f"sprite_lines_1_{i}") for i in range(3)]
    assert sum(map(sum,raw))==num("sprite_outer") and sum(map(sum,blank))==num("sprite_blank")
    for i,parts in enumerate((2,2*(mask&1),mask>>1)):
        count=array(f"sprite_calls_0_{i}")
        assert count==array(f"sprite_calls_1_{i}"),(label,i)
        assert count==[sample*(1+3*parts),sample,sample*parts,sample*parts,sample*parts],(label,i,count)
    out["phases_per_step"]=[sum(a[k]-b[k] for a,b in zip(raw,blank))/sample for k in range(5)]
    out["actor_phase_lines_per_step"]=[[ (v-w)/sample for v,w in zip(a,b)] for a,b in zip(raw,blank)]
    out["raw_sample_per_step"]=num("sprite_outer")/sample
    out["empty_sample_per_step"]=num("sprite_blank")/sample
    out["other_steps_per_step"]=num("sprite_plain")/(240-sample)
    for k in ("active","still","same_pose","due","paid"):out[k]=array("sprite_"+k)
    return out

def verify(builds):
    rows={label:route(label) for label in LABELS}
    parent=HERE.parent/"op-score-decimal-2026-10-31"
    normal=json.loads((parent/"build.json").read_text())["normal_build"][0]["sha256"]
    assert builds["reference"]==json.loads((parent/"measurements.json").read_text())["builds"]["candidate"]
    source=json.loads((HERE/"runs/source.json").read_text())
    assert source["source_sha256"]=="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
    assert len(source["cases"])==8 and {(c["mask"],c["bank"]) for c in source["cases"]}=={(m,b) for m in range(4) for b in range(2)}
    work_delta=sum(rows[f"ref-both-{k}"]["work_lines"]-rows[f"ref-solo-{k}"]["work_lines"] for k in "ab")/480
    driver_delta=rows["outer-both"]["driver_lines_per_step"]-rows["outer-solo"]["driver_lines_per_step"]
    phases=[sum(rows[f"detail-both-{k}"]["phases_per_step"][i]-rows[f"detail-solo-{k}"]["phases_per_step"][i] for k in "ab")/2 for i in range(5)]
    return dict(normal_sha256=normal,machine=MACHINE,builds=builds,source_report_sha256=sha(HERE/"runs/source.json"),
                runs=rows,phase_names=PHASES,extra_work_lines_per_step=work_delta,extra_driver_lines_per_step=driver_delta,
                estimated_work_share=driver_delta/work_delta,detailed_extra_lines_per_step=phases)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--collect",action="store_true");args=parser.parse_args()
    result=HERE/"result.json"
    builds=collect() if args.collect else json.loads(result.read_text())["builds"]
    data=verify(builds)
    if args.collect:
        assert data["normal_sha256"]==sha(ROOT/"amiga/out/bruce_amiga.exe")
        result.write_text(json.dumps(data,indent=2)+"\n")
    else:assert json.loads(result.read_text())==data
    print("PASS 14 A500 routes, eight source comparisons and disjoint sprite timings")
