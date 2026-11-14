"""Bind timed route variants and functional controls to the normal A500 build."""
import json
import shutil
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = ROOT / ".tmp/four-work"
NORMAL = ROOT / "amiga/out"
sys.path.insert(0,str(HERE.parent / "actor-draw-2026-11-01"))
from record_draw import allocated, decimal_sections, item, normalized_hunk, read


def save(path, name):
    target = HERE / "runs" / name
    shutil.copyfile(path,target)
    return item(target)


def main(mode="all", prefix=""):
    parent_path = HERE.parent / "actor-draw-2026-11-01/delivery.json"
    parent = read(parent_path)
    parent_run=WORK/"before/source-world-native.json"
    assert item(parent_run)["sha256"]==next(r["sha256"] for r in parent["proofs"]
                                           if r["path"]=="reference/validation/source-world-native.json")
    for entry in read(parent_run)["source_files"]:
        if entry["path"] in ("amiga/main.c","amiga/contact_rows.s","core/session.c"):
            assert item(WORK/"before"/Path(entry["path"]).name)["sha256"]==entry["sha256"]
    (HERE / "runs").mkdir(exist_ok=True)
    retail = WORK / ("retail-"+mode)
    assert allocated(retail/"bruce_amiga.elf") == allocated(NORMAL/"bruce_amiga.elf")
    assert normalized_hunk(retail) == normalized_hunk(NORMAL)
    modules = {}
    for name in ("session","contact_rows"):
        modules[name] = decimal_sections(NORMAL/(name+".o"))
        for stage in (retail, WORK/mode, WORK/("long-"+mode)):
            assert modules[name]==decimal_sections(stage/(name+".o")), (stage,name)
    assert decimal_sections(NORMAL/"c64_rooms.o")==parent["engine_sections"]
    # The actual 68000 row proof and microbenchmark link this object.
    assert modules["contact_rows"]==decimal_sections(WORK/"all/contact_rows.o")
    assert struct.unpack(">HH",(WORK/"kernel-proof/proof-result.bin").read_bytes())==(192,0)
    vectors=read(HERE.parent/"op1-row-walk-2026-10-31/source-controls.json")
    assert item(WORK/"kernel-proof/vectors.bin")["sha256"]==vectors["fixture_sha256"]
    lamps=read(WORK/"lamps.json")
    assert lamps["switches"]==2 and lamps["deaths"]==3 and lamps["jumps"]==42
    evidence={key:save(WORK/path,name) for key,path,name in (
        ("lamps","lamps.json","lamp-checks.json"),("queue","queue.json","queue-checks.json"),
        ("rows","kernel-proof/proof-result.bin","rows.bin"),
        ("timings","kernel-micro/micro.bin","row-times.bin"))}
    runs={}
    for key, name in (("direct-a","a"),("direct-b","b"),("direct-still-a","still-a"),
                      ("direct-still-b","still-b"),("direct-stairs","stairs"),("direct-yamo","yamo"),
                      ("long-direct-a","long-a"),("long-direct-b","long-b")):
        directory=WORK/((mode+"-"+name) if mode=="all" and name in ("a","b") else prefix+name)
        raw=directory/"op0-light.txt"
        rows=dict(l.split("=",1) for l in raw.read_text().splitlines() if "=" in l)
        assert rows["finished"]==rows["restored_os"]=="1"
        assert rows["pal_fields"]==rows["paula_publications"] and all(rows[k]=="0" for k in
            ("paula_empty","paula_double","audio_missed","source_fault","dma_fault","audio_fault"))
        exe=item(directory/"bruce_amiga.exe")["sha256"]
        assert exe==item(WORK/(("long-" if key.startswith("long-") else "")+mode)/"bruce_amiga.exe")["sha256"]
        runs[key]=dict(raw=save(raw,name+".txt"),exe=exe,route=(directory/"op0-route.bin").read_bytes().hex())
    for label in ("lamp-a","paint-a","queue-a","rows-a","meter-lamp","meter-"+mode,"base-move","base-stairs"):
        evidence[label]=save(WORK/label/"op0-light.txt",label+".txt")
    for label in ("best-stairs","best-long-b","splitqueue-stairs","splitqueue-long-b"):
        evidence["pilot-"+label]=save(WORK/label/"op0-light.txt","pilot-"+label+".txt")
    ui={}
    for name in ("cli","adf"):
        path=ROOT/f".tmp/op-finish/four-{mode}-{name}/normal.json"
        result=read(path)
        assert result["normal_exe_sha256"]==item(retail/"bruce_amiga.exe")["sha256"]
        assert result["complete_menu"] and result["pause_preserved"] and result["fields"]>=6000 and not result["misses"]
        if name=="cli":assert result["joystick_crossings"]==[2,1]
        else:assert result["turn_after_death"]["player"]==2
        ui[name]=save(path,"normal-"+name+".json")
    field_evidence={}
    for scene in ("stairs","death"):
        path=ROOT/f"reference/analysis/render-coherence-2026-10-29/four-{mode}-render-{scene}/report.json"
        field_evidence[scene]=save(path,"render-"+scene+".json")
    field_evidence["alloc-release/allocation.json"]=save(ROOT/f".tmp/field-work/four-{mode}-alloc/allocation.json","allocation.json")
    world=read(ROOT/"reference/validation/source-world-native.json")
    assert not world["failures"] and world["run"]["frames"]=="1200"
    assert (NORMAL/"autotest-frame.bpl").read_bytes()==(WORK/"before/autotest-frame.bpl").read_bytes()
    for name in ("bruce_amiga.exe","bruce_amiga.adf"):
        shutil.copyfile(retail/name,NORMAL/name)
    shutil.copyfile(retail/"bruce_amiga.exe",ROOT/".tmp/amiga-boot/c/start")
    proof_paths={entry["path"] for entry in parent["proofs"]} | {
        "core/session.c","amiga/contact_rows.s","core/scene_copy.h",
        (HERE/"check_lamps.c").relative_to(ROOT).as_posix(),(HERE/"check_queue.c").relative_to(ROOT).as_posix()}
    result=dict(predecessor=item(parent_path),production_mode="direct",session_variant=mode,
                normal_build=[item(ROOT/r["path"]) for r in parent["normal_build"]],
                diagnostic_exe=item(WORK/mode/"bruce_amiga.exe")["sha256"],
                proofs=[item(ROOT/p) for p in sorted(proof_paths)],runs=runs,ui=ui,
                field_evidence=field_evidence,modules=modules,controls=evidence)
    manifest=HERE/"delivery.json"
    manifest.write_text(json.dumps(result,indent=2)+"\n")
    source=(ROOT/".reference/c64/work/untrained-memory.bin").read_bytes()
    for pc,code in ((0x331c,"a651b5e9"),(0x3361,"9114a629"),(0x5380,"b900e039e0ca"),
                    (0x539a,"b900e03900cb"),(0x53b4,"b900e03920cb"),(0x53ce,"c8cc384f")):
        assert source[pc:pc+len(code)//2].hex()==code
    capture=dict(capture_id="FOUR-WORK-0001",reference_id="c64-local-t64-remember-no-trainers",
                 source_sha256=item(ROOT/".reference/c64/work/untrained-memory.bin")["sha256"],
                 addresses=["$331C–$336D","$4CE2","$183B","$0FED","$5380–$53CE"],
                 status="candidate_code_and_scoped_amiga_measurements",edition_verified=False,
                 full_original_parity=False,artifacts=[item(manifest),evidence["lamps"],evidence["rows"]])
    (ROOT/"docs/parity/evidence/FOUR-WORK-0001.json").write_text(json.dumps(capture,indent=2)+"\n")


if __name__=="__main__":
    main(*sys.argv[1:])
