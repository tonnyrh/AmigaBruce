"""Bind paired PAL runs, the frozen source witnesses and the tested 68000 code."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import struct
import sys
from build_pilot import HERE, ROOT, WORK
from check import kernel
sys.path.insert(0,str(ROOT/"tools"))
from audit_vic_native_kernels import sections
import hashlib

PAIRS=(("before1","after1",1,3,0),("before2","after2",1,3,0),
       ("moving-before","moving-after",1,3,2),("yamo-before","yamo-after",13,1,0),
       ("stairs-before","stairs-after",12,3,1))
FILES=HERE/"runs"
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def report(name):
    return dict(line.split("=",1) for line in (FILES/(name+".txt")).read_text().splitlines() if "=" in line)
def bind(record):
    labels=[name for left,right,*_ in PAIRS for name in (left,right)]+["hits"]
    if record:
        FILES.mkdir(exist_ok=True)
        for name in labels:shutil.copyfile(WORK/name/"op0-light.txt",FILES/(name+".txt"))
        for name in ("oracle.json","proof.bin"):shutil.copyfile(WORK/"proof"/name,FILES/name)
    old=load(HERE.parent/"op2-vic-pairs-2026-10-31/measurements.json")
    for artifact in old["normal_build"]:
        assert digest(ROOT/artifact["path"])==artifact["sha256"],artifact["path"]
    for artifact in old["inputs"]:
        assert digest(ROOT/artifact["path"])==artifact["sha256"],artifact["path"]
    witness=load(FILES/"oracle.json")
    assert witness["source_sha256"]==digest(ROOT/".reference/c64/work/untrained-memory.bin")==old["c64_sha256"]
    cases=witness["cases"]
    assert len(cases)==218 and struct.unpack(">III",(FILES/"proof.bin").read_bytes())==(len(cases),0,1)
    assert {c["case"] for c in cases}>={f"mask-byte-{i}" for i in range(96)}
    assert [c["foot"] for c in cases if c["case"] in ("glyph-setup","changed-at-service","animated-glyph")]==[2,6,6]
    assert any(c["case"]=="room-hit-1" and c["foot"]&4 for c in cases)
    assert set(c["path"] for c in cases)=={"hit","fill","bypass","inactive"}
    pairs=[]
    for left,right,room,mask,route in PAIRS:
        row=dict(room=room,mask=mask,input=route)
        for name,side in ((left,"before"),(right,"after")):
            r=report(name)
            for key,wanted in dict(finished=1,restored_os=1,steps=240,warmup_steps=240,room=room,
                    enemy_mask=mask,input_route=route,source_profile=0,source_fault=0,audio_fault=0,
                    dma_fault=0,visited_rooms=1<<(room-1)).items():
                assert int(r[key])==wanted,(name,key)
            active=list(map(int,r["active_loops"].split(",")))
            assert active[0 if room==12 else mask]==sum(active)==int(r["loops"])
            assert int(r["chip_largest_loaded"])>=49152
            assert int(r["audio_ticks"])+int(r["audio_missed"])==int(r["pal_fields"])
            if route==2:assert int(r["air_steps"])>0
            if route==1:assert int(r["climb_steps"])==240
            row[side]=dict(fields=int(r["pal_fields"]),work_lines=int(r["work_lines"]),
                           audio_missed=int(r["audio_missed"]),air_steps=int(r["air_steps"]))
        pairs.append(row)
    hit=report("hits")
    counts=list(map(int,hit["kage_hit_fill_bypass"].split(",")))
    assert sum(counts)==int(hit["steps"])==240 and counts[0]>0 and hit["finished"]=="1"
    status="rejected_no_repeated_whole_route_gain"
    assert not all(pair["after"]["fields"]<pair["before"]["fields"] for pair in pairs[:2])
    result=dict(status=status,source_sha256=witness["source_sha256"],normal_build=old["normal_build"],
        comparisons=pairs,observed_hit_fill_bypass=counts,native_controls=len(cases),host_paths=dict(Counter(c["path"] for c in cases)),
        source_instructions=sum(c["instructions"] for c in cases),raw={p.name:digest(p) for p in sorted(FILES.iterdir())},
        pilot_inputs={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.suffix in (".c",".h",".ps1",".py")},
        production_changed=False,natural_playthrough=False,original_edition_verified=False)
    if record:
        binaries={name:digest(WORK/name/"bruce_amiga.exe") for name in labels}
        assert len({binaries[left] for left,*_ in PAIRS})==len({binaries[right] for _,right,*_ in PAIRS})==1
        assert binaries["hits"] not in (binaries["before1"],binaries["after1"])
        code={}
        for name in ("source_contact_driver","source_contact_rows_inner","first_part","kage_first_part"):
            timing=kernel(WORK/"candidate/c64_rooms.o",name)
            assert timing==kernel(WORK/"proof/c64_rooms.o",name)
            code[name]=timing
        def copy_kernel(folder):
            data,table=sections(WORK/folder/"c64_rooms.o");s=dict(table)[".text.prefix_copy"]
            assert ".rela.text.prefix_copy" not in dict(table)
            return hashlib.sha256(data[s[4]:s[4]+s[5]]).hexdigest()
        assert copy_kernel("candidate")==copy_kernel("proof")
        result["builds"]=dict(executables=binaries,proof_executable=digest(WORK/"proof/bruce_amiga.exe"),
            case_file=digest(WORK/"proof/cases.bin"),unrelocated_copy=copy_kernel("proof"),kernels=code)
        (HERE/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    else:
        stored=load(HERE/"result.json");builds=stored.pop("builds")
        assert stored==result and len(builds["kernels"])==4
    print(status,"pairs",[(r["before"]["fields"],r["after"]["fields"]) for r in pairs],
          "hit/fill/bypass",counts,"native controls",len(cases))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--record",action="store_true");bind(p.parse_args().record)
