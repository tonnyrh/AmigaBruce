"""Read the PAL reports, exclude nested service cost and audit the fixed-state experiment."""
from pathlib import Path
import argparse, json, shutil, struct, sys
from audit import audit, sha, SOURCE_SHA, ROOT, HERE
sys.path.insert(0,str(ROOT/"tools"))
from audit_vic_native_kernels import sections

def kernel(obj,name):
    # Compare raw machine code AND its relocation targets; adding the bench
    # changes ELF symbol indices but not the names of the called routines.
    data,table=sections(obj); sec=dict(table)[".text."+name]
    rela=dict(table)[".rela.text."+name]
    syms=table[rela[6]][1]; strings=table[syms[6]][1]
    targets=[]
    for i in range(rela[4],rela[4]+rela[5],12):
        at,info,add=struct.unpack_from(">IIi",data,i)
        off=syms[4]+(info>>8)*16
        label=struct.unpack_from(">I",data,off)[0]
        if label:
            start=strings[4]+label;symbol=data[start:data.index(0,start)].decode()
        else:
            symbol=table[struct.unpack_from(">H",data,off+14)[0]][0]
        if symbol.startswith((".rodata.pointer_return.",".rodata.row_return.")):
            contents=dict(table)[symbol]
            symbol=symbol.rsplit(".",1)[0]+":"+sha(data[contents[4]:contents[4]+contents[5]])
        targets.append((at,info&255,symbol,add))
    return dict(size=sec[5],code_sha256=sha(data[sec[4]:sec[4]+sec[5]]),
                relocation_sha256=sha(json.dumps(targets).encode()))


WORK=ROOT/".tmp/op1-budget"
PARENT=ROOT/"reference/analysis/op2-vic-pairs-2026-10-31/measurements.json"
NAMES=("matched-control","timed2","repeat-timed","matched-sparse","state240","state400","replay240","replay400","keys240")
def read_report(path):
    return dict(line.split("=",1) for line in path.read_text().splitlines() if "=" in line)
def read_json(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def key_counts(data):
    assert len(data)==7*720
    results=[]
    for actor in range(3):
        rows=[tuple(data[i:i+7]) for i in range((2-actor)*7,len(data),21)]
        assert len(rows)==240 and all(row[0]==actor and row[4] in (0,1) for row in rows)
        last=None;repeats=0;distinct=set();outputs={}
        for _,x,y,pose,active,body,foot in rows:
            if not active:
                last=None;continue
            key=(x,y,pose);repeats+=int(key==last);last=key;distinct.add(key)
            outputs.setdefault(key,set()).add((body,foot))
        results.append(dict(actor=actor,active=sum(row[4] for row in rows),distinct=len(distinct),consecutive_repeats=repeats,
                    different_outputs_same_key=sum(len(out)>1 for out in outputs.values())))
    return results
def main(record):
    data_dir=HERE/"runs"
    if record:
        data_dir.mkdir(exist_ok=True)
        for name in NAMES:shutil.copyfile(WORK/name/"op0-light.txt",data_dir/(name+".txt"))
        for name in ("state240","state400"):
            checked=audit(WORK/name)
            (data_dir/(name+".json")).write_text(json.dumps(checked,indent=2)+"\n")
        shutil.copyfile(WORK/"keys240/actor-keys.bin",data_dir/"actor-keys.bin")
    parent=read_json(PARENT)
    inputs={p:sha((ROOT/p).read_bytes()) for p in ("core/c64_rooms.c","core/c64_actor_programs.h","amiga/main.c","tools/build_light_op0_probe.py","amiga-build.ps1")}
    parent_inputs={q["path"]:q["sha256"] for q in parent["inputs"]}
    assert all(value==parent_inputs[p] for p,value in inputs.items())
    normal=sha((ROOT/"amiga/out/bruce_amiga.exe").read_bytes())
    assert normal==parent["normal_build"][0]["sha256"]
    for artifact in parent["normal_build"]:
        assert sha((ROOT/artifact["path"]).read_bytes())==artifact["sha256"],artifact["path"]
    assert sha((ROOT/".reference/c64/work/untrained-memory.bin").read_bytes())==SOURCE_SHA
    raw={name:read_report(data_dir/(name+".txt")) for name in NAMES}
    for name,r in raw.items():
        assert r["finished"]==r["restored_os"]=="1"
        assert all(r[key]=="0" for key in ("source_fault","dma_fault","audio_fault","source_profile"))
        if name not in ("state240","state400","replay240","replay400"):
            assert r["steps"]==r["warmup_steps"]=="240" and r["active_loops"]=="0,0,0,240"
            assert r["visited_rooms"]=="1" and int(r["audio_ticks"])+int(r["audio_missed"])==int(r["pal_fields"])
    budget=[]
    for name in ("timed2","repeat-timed","matched-sparse"):
        r=raw[name];bins=list(map(int,r["contact_lines"].split(",")))
        calls=int(r["profiled_calls"]);seams=int(r["actor_seams"])+int(r["row_seams"])
        assert calls==(30 if name=="matched-sparse" else 240) and int(r["actor_seams"])==calls*3
        assert 0<int(r["empty_work_lines"])<int(r["empty_256_pairs_lines"])<2048
        work=sum(bins[:4]);service=sum(bins[4:]);correction=seams*int(r["empty_work_lines"])/256
        budget.append(dict(run=name,fields=int(r["pal_fields"]),calls=calls,checkpoints=seams,
             gross_exclusive_lines_per_call=round(work/calls,2),
             estimated_exclusive_lines_per_call=round((work-correction)/calls,2),
             service_window_lines_per_call=round(service/calls,2),
             actor_work_before_correction=[round(v/calls,2) for v in bins[1:4]]))
    states=[]
    for offset in (240,400):
        capture="state"+str(offset);replay="replay"+str(offset)
        proof=read_json(data_dir/(capture+".json"));r=raw[capture]
        assert r["capture_overflow"]=="0" and proof["source_sha256"]==SOURCE_SHA
        local=ROOT/".reference/c64/work"/HERE.name/capture
        if (local/"capture.bin").is_file():assert audit(local,write_replay=False)==proof,capture
        seams=len(proof["checkpoints"])-1
        assert int(r["capture_records"])==seams+2 and proof["return_pc"]=="1c10"
        real,lookup,errors,checks,real_calls,lookup_calls,rounds=map(int,raw[replay]["replay_benchmark"].split(","))
        assert errors==0 and rounds==64 and checks==(seams+1)*2 and real_calls==lookup_calls==seams*rounds
        assert 0<lookup and 0<real
        states.append(dict(warmup=offset,services=seams,source_instructions=proof["source_instructions"],
                native_lines_per_call=round(real/rounds,2),recorded_lines_per_call=round(lookup/rounds,2),
                difference_percent=round(100*(real-lookup)/real,2),tape_bytes=proof["replay_bytes"]))
    gates={name:int(raw[name]["pal_fields"]) for name in ("matched-control","timed2","repeat-timed","matched-sparse","keys240")}
    runs={p.name:sha(p.read_bytes()) for p in sorted(data_dir.iterdir()) if p.is_file()}
    report=dict(source_sha256=SOURCE_SHA,normal_sha256=normal,production_inputs=inputs,
        prior_run_fields=[int(read_report(PARENT.parent/(n+".txt"))["pal_fields"]) for n in ("trial1","trial2")],
        fields=gates,contact=budget,isolated_replays=states,actor_key_upper_bounds=key_counts((data_dir/"actor-keys.bin").read_bytes()),
        raw_sha256=runs,natural_playthrough=False,production_change=False)
    out=HERE/"result.json"
    if record:
        binaries={name:sha((WORK/name/"bruce_amiga.exe").read_bytes()) for name in NAMES}
        assert len({binaries[n] for n in ("matched-control","timed2","repeat-timed","matched-sparse")})==1
        assert binaries["replay240"]==binaries["replay400"]
        report["probe_binaries"]=binaries
        helpers={}
        for name in ("source_contact_driver","source_contact_rows_inner","source_contact_pointers"):
            measured=kernel(WORK/"replay/c64_rooms.o",name)
            assert measured==kernel(ROOT/"amiga/out/c64_rooms.o",name),name
            helpers[name]=measured
        report["native_reference_helpers"]=helpers
        out.write_text(json.dumps(report,indent=2)+"\n")
    else:
        saved=read_json(out);binaries=saved.pop("probe_binaries");helpers=saved.pop("native_reference_helpers")
        assert all(len(row["code_sha256"])==64 and row["size"]>0 for row in helpers.values())
        assert saved==report and len(set(binaries[n] for n in NAMES[:4]))==1
    print(json.dumps({k:report[k] for k in ("fields","contact","isolated_replays","actor_key_upper_bounds")},indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--record",action="store_true");main(p.parse_args().record)
