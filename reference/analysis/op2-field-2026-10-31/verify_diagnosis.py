"""Check event accounting and bind the field diagnosis to the programs that ran."""
import argparse
import hashlib
import json
from pathlib import Path
from decode import decode,text_report

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OP0=HERE.parent/"op0-light-2026-10-31"
SOURCE_SHA="092c50dbc997e301c75c7860a3c84026a93a7aaf543968ae36f1ffa19d0800b8"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def bound(path,digest):
    # Reference runs keep their exact inputs across subsequent deliveries.
    frozen=HERE/"parent"/path
    p=frozen if frozen.is_file() and sha(frozen)==digest else ROOT/path
    assert sha(p)==digest,path
def verify_run(folder):
    d=read(folder/"identity.json")
    for e in d["source_files"]:bound(e["path"],e["sha256"])
    r=text_report(folder/"op0-light.txt")
    assert d["run"]==r and d["autotest"] is False
    assert r["steps"]==r["warmup_steps"]=="240" and r["visited_rooms"]=="1"
    assert r["source_fault"]==r["dma_fault"]==r["audio_fault"]=="0"
    assert r["restored_os"]==r["finished"]=="1"
    assert int(r["chip_largest_loaded"])>=49152
    active=list(map(int,r["active_loops"].split(",")))
    assert active[d["enemy_mask"]]==sum(active)==int(r["loops"])
    cfg=(folder/"a500.uae").read_text(encoding="utf-8-sig")
    for setting in ["cpu_model=68000","cpu_speed=real","cpu_cycle_exact=true","chipset=ocs","chipmem_size=1","bogomem_size=2","fastmem_size=0"]:
        assert setting in cfg
    return d

def diagnose():
    frozen=ROOT/".reference/c64/work/untrained-memory.bin"
    assert sha(frozen)==SOURCE_SHA
    code=frozen.read_bytes()
    contract={0x29ce:"ad1ed0",0x3d20:"ad1ed0",0x07ea:"a9008d15d08d17d08d1bd08d1cd0a9ff8d1dd0",0x361a:"a9ff8d1dd0",0x4915:"20a815"}
    for at,h in contract.items():assert code[at:at+len(bytes.fromhex(h))].hex()==h
    refs={}
    paths=[Path(__file__),HERE/"observer.h",HERE/"decode.py",HERE/"build.py"]
    for label in ["op2-reference-both-1","op2-reference-both-2"]:
        folder=OP0/"runs"/label
        d=verify_run(folder)
        refs[label]={k:int(d["run"][k]) for k in ["steps","pal_fields","audio_ticks","audio_missed","work_lines","wait_lines"]}
        paths += [folder/"identity.json",folder/"op0-light.txt",folder/"bruce_amiga.exe"]
    traces={}
    for label in ["sites-both","timed-both-1","timed-both-2","timed-bruce"]:
        folder=HERE/"runs"/label
        run=verify_run(folder)
        manifest=read(HERE/run["variant"]/"inputs.json")
        for path,digest in manifest.items():bound(path,digest)
        assert sha(folder/"bruce_amiga.exe")==sha(HERE/run["variant"]/"bruce_amiga.exe")
        d=decode(folder)
        assert d["timed"]==(run["variant"]=="timed")
        if label!="timed-bruce":
            assert d["missed"]>0
            assert all(e["site"]=="post_field" and e["origin"]=="outer_loop" and e["gap"]==2 and e["previous_tick_observed"] for e in d["events"])
            if d["timed"]:
                assert all(e["kind"]=="pixel_rebuild" and e["rebuilds"]>0 for e in d["events"])
        else:assert d["missed"]==0 and set(d["paths"])=={"repeat"}
        traces[label]=d
        paths+=[folder/"op2-fields.bin",folder/"op0-light.txt",folder/"identity.json",folder/"a500.uae",HERE/run["variant"]/"inputs.json"]
    return dict(date="2026-10-31",source_sha256=SOURCE_SHA,reference=refs,traces=traces,source_bytes={hex(k):v for k,v in contract.items()},
                edition_verified=False,natural_playthrough=False,raster_exact=False,realtime_accepted=False,
                limits=["240 measured steps following 240 warmup, stationary invincible diagnostic Bruce",
                        "Labels and timers alter field phase. Only reference builds provide reference throughput.",
                        "Post-field events bound a completed field call. Its VIC and cache costs are nested.",
                        "Game audio service gaps count missed source ticks, not recorded host audio glitches."],
                artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in paths})

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--record",action="store_true")
    args=parser.parse_args()
    report=diagnose()
    p=HERE/"diagnosis.json"
    if args.record:p.write_text(json.dumps(report,indent=2)+"\n")
    else:assert read(p)==report
    print("Verified reference, site-only and timed field/audio traces")
