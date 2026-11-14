"""Check current OP measurements and source contracts. Failed cadence remains visible."""
import json
from pathlib import Path
from verify_score_display_delivery import decimal_sections,item
from verify_vic_pair_delivery import linked_pair_hash

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"reference/analysis/op-finish-2026-10-31"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def check(entries):
    for e in entries:assert item(ROOT/e["path"])==e,e["path"]

def verify_current():
    if (STAGE.parent/"kage-paula-2026-11-01/delivery.json").is_file():
        from verify_kage_delivery import verify_current as verify_kage
        return verify_kage()
    pipeline=(STAGE/"pipeline-result.json").is_file()
    manifest=STAGE/("pipeline-result.json" if pipeline else "result.json")
    record=read(manifest);parent=read(STAGE/"previous-delivery.json")
    ui=STAGE/("pipeline-runs" if pipeline else "runs")
    assert parent["normal_build"]==read(ROOT/"reference/analysis/op-score-decimal-2026-10-31/build.json")["normal_build"]
    check([record["previous_delivery"],*record["normal_build"],*record["inputs"],*record["evidence"]])
    assert decimal_sections(ROOT/"amiga/out/c64_rooms.o")==record["engine_sections"]
    runs={}
    for name,r in record["runs"].items():
        check([r["report"]]);v=dict(l.split("=",1) for l in (ROOT/r["report"]["path"]).read_text().splitlines() if "=" in l)
        assert all(v[k]=="0" for k in ("source_fault","audio_fault","dma_fault","source_profile"))
        assert v["restored_os"]==v["finished"]=="1"
        runs[name]=v
    assert all(runs[n]["tour_count"]=="24" and int(runs[n]["stack_untouched"])>0 for n in ("tour-a","tour-b","release-phases","tour-load-a2","tour-load-b2"))
    for base,opt in (("tour-a","tour-load-a2"),("tour-b","tour-load-b2")):
        rows=lambda n:[list(map(int,runs[n]["tour_"+str(i)].split(","))) for i in range(24)]
        old,new=rows(base),rows(opt);assert {r[0] for r in new}==set(range(1,21))
        assert all(a[0]==b[0] and b[4]<a[4] and 300<=b[5]<=308 for a,b in zip(old,new))
    sources=read(STAGE/"runs/source-blocks.json");images=read(STAGE/"runs/source-images.json")
    assert sources==dict(frozen_sha256=parent["source_sha256"],history_cases=384,field_cases=1664,bytes_per_case=65536,room_tokens=2056,room_cells=8812,rooms=20,unchanged_fallbacks=32)
    assert images==dict(cache_cases=60,sprite_cases=128,service_boundaries=384)
    core=(ROOT/"core/c64_rooms.c").read_text()
    for helper in ("field.c","history.c","component.c","room_run.c"):
        assert (STAGE/helper).read_text().strip() in core,helper
    kernel=read(STAGE/"runs/source-irq.json")
    assert kernel==dict(cases=1024,common=960,human_fallback=64,ram_bytes=65536)
    for mode in ("cli","adf"):
        game=read(ui/f"normal-{mode}.json")
        assert game["complete_menu"] and game["normal_exe_sha256"]==record["normal_build"][0]["sha256"]
        assert game["fields"]>=6000 and game["steps"]>0 and game["after"]["fault"]==0
        assert [s["section"] for s in game["layout"]]==[".text",".rodata",".data",".bss"]
        assert all(0xc00000<=s["base"]<s["base"]+s["bytes"]<=0xc80000 for s in game["layout"])
        assert len(game["dma"])==4 and all(0<at<0x80000 for at in game["dma"].values())
        if pipeline:assert game["pause_preserved"]
        if mode=="adf":assert game["turn_after_death"]["player"]==2 and not game["turn_after_death"]["fault"]
        else:assert game["joystick_crossings"]==[2,1]
    for scene in ("stairs","death"):
        v=read(ui/f"render-{scene}.json")
        assert len(v["samples"])==(36 if pipeline and scene=="stairs" else 12) and not any(v[k] for k in ("mixed_phase_samples","max_static_pixel_mismatch","max_flicker_illegal_pixels","flicker_stuck_codes"))
    for i in range(24):
        row=list(map(int,runs["release-phases"]["tour_"+str(i)].split(",")))
        phases=list(map(int,runs["release-phases"]["phases_"+str(i)].split(",")))
        assert len(phases)==9 and row[4]<phases[8]<=row[4]+120
    folder=ROOT/"reference/analysis/actor-chain-2026-10-26"
    proof=[folder/n for n in ("report.json","integrated-controls.json","translation.json")]
    proof += [ROOT/f"reference/validation/{name}.json" for name in ("source-world-native","source-score-host","source-vic-host","source-audio-host","source-dma-host","source-contact-host","source-sprite-copy-host","source-object-host","source-visibility-host","source-paint-host")]
    actor,world,trans,native,score,vic,audio,dma,contact,sprites,objects,visibility,paint=map(read,proof)
    for r in (actor,world,trans,native,score,vic,audio,dma,contact,sprites,objects,visibility,paint):
        check(r.get("source_files",[]));check(r.get("generated",[]))
    assert actor["checks"]==len(actor["rows"])==3034 and len(world["checks"])==5 and world["instructions"]==7055873
    assert (score["checks"],vic["calls"],audio["source_cpu_fields_compared"],dma["channel_images"])==(2852,8741,7540,4554)
    assert (contact["checks"],sprites["checks"],objects["checks"],visibility["checks"],len(paint["cases"]))==(4239,1536,65536,768,6)
    for name,count in (("vic-cache-host",25600),("view-mask-host",2293920)):
        path=ROOT/f"reference/validation/{name}.json";r=read(path)
        assert r["cases"]==count;check(r["source_files"]);proof.append(path)
    check(native["build"]);v=native["run"];assert not native["failures"] and (v["frames"],v["source_actor_fixture_cases"],v["restored_os"])==("1200","53","1")
    if pipeline:
        import struct
        assert struct.unpack(">III",(ui/"copy-proof.bin").read_bytes())==(96,0,1)
        assert item(ROOT/"amiga/sprite_copy.s")["sha256"]==record["copy_kernel_sha256"]
        assert v["bad_presents"]==v["bad_queue_windows"]=="0" and int(v["queued_presents"])>0
    assert int(v["chip_largest_loaded"])>=49152
    pair=read(ROOT/"reference/analysis/op2-vic-pairs-2026-10-31/measurements.json")["kernel"]
    for elf in (ROOT/"amiga/out/bruce_amiga.elf",ROOT/next(e["path"] for e in native["build"] if e["path"].endswith(".elf"))):
        assert linked_pair_hash(elf,pair)==pair["sha256"]
    tourfile=ROOT/("reference/analysis/optimization-2026-10-27/"+("pipeline" if pipeline else "finish")+"-source20-20261031/identity.json")
    tour=read(tourfile);assert len(tour["rooms"])==20 and all(r["steps"]==120 and r["chip_largest"]>=49152 for r in tour["rooms"])
    observed=("final-still","final-move","final-move2","final-stairs","final-yamo","long-release-a","long-release-b")
    cadence=all(abs(int(runs[k]["pal_fields"])-3*int(runs[k]["steps"]))<=2 and
                all(int(runs[k][f])==0 for f in ("audio_missed","paula_empty","paula_double")) for k in observed)
    assert all(int(runs[k]["pal_fields"])<int(runs["ref-move"]["pal_fields"]) for k in ("final-move","final-move2"))
    return dict(parent,status="scoped_op_room_actor_delivery_realtime_open",normal_build=record["normal_build"],largest_chip_block=int(v["chip_largest_loaded"]),
                realtime_gate_passed=cadence and native["realtime_contract_passed"],op_measured={k:[int(runs[k]["steps"]),int(runs[k]["pal_fields"]),int(runs[k]["paula_empty"])] for k in observed},
                open_gates=["Three PAL fields per ordinary step with both enemies and continuous Paula publication",
                            "Natural C64 IRQ/input phase and complete natural playthrough",
                            "Verified untouched 1984 edition"],
                artifacts=[item(p) for p in (manifest,STAGE/"previous-delivery.json",tourfile,*proof,Path(__file__).resolve())])

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--require-realtime",action="store_true")
    args=p.parse_args();report=verify_current()
    print("PASS current build, C64 comparisons, WinUAE controls and measurement identities")
    for name,(steps,fields,empty) in report["op_measured"].items():
        print(f"{name}: {fields} PAL fields / {steps} steps, {empty} fields without a Paula publication")
    if not report["realtime_gate_passed"]:
        if report.get("continuous_long_audio"):
            print("PASS continuous Paula publications in both long combat trials")
            print("OPEN three-field combat cadence")
        else:print("OPEN three-field cadence and continuous audio")
        if args.require_realtime:raise SystemExit(1)
