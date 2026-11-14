"""Record ordinary game artifacts, source controls and measured field routes."""
import json
import shutil
import sys
from build_field import ROOT,WORK,HERE
sys.path.insert(0,str(ROOT/"tools"))
from verify_score_display_delivery import decimal_sections,item
sys.path.insert(0,str(HERE.parent/"op-finish-2026-10-31"))
from record_pipeline import normalized_hunk,sections

def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))

def main():
    prior=HERE.parent/"kage-paula-2026-11-01/delivery.json"
    data=read(prior);out=HERE/"runs";out.mkdir(exist_ok=True)
    def copy(source,name):
        dest=out/name;shutil.copyfile(source,dest);return item(dest)
    mode="release";normal=ROOT/"amiga/out";retail=WORK/("retail-"+mode);probe=WORK/mode
    assert normalized_hunk(retail)==normalized_hunk(normal)
    def image(folder):
        raw,headers=sections(folder/"bruce_amiga.elf")
        return [(n,h[3],h[5],raw[h[4]:h[4]+h[5]] if h[1]!=8 else b"") for n,h in headers if h[2]&2]
    assert image(normal)==image(retail)
    for name,folder in (("main.c","amiga"),("source_audio.h","amiga"),("c64_rooms.c","core"),("c64_actor_programs.h","core")):
        assert (retail/name).read_text()==(ROOT/folder/name).read_text()
    for obj in ("c64_rooms.o","source_dma.o"):assert decimal_sections(probe/obj)==decimal_sections(normal/obj),obj
    routes={}
    for label in ("release-a","release-b","release-still-a","release-still-b","long-release-a","long-release-b","release-stairs","release-yamo"):
        folder=WORK/label
        routes[label]=dict(raw=copy(folder/"op0-light.txt",label+".txt"),exe=item(folder/"bruce_amiga.exe")["sha256"],
                           route=(folder/"op0-route.bin").read_bytes().hex())
    evidence={}
    for name in ("input-proof.json","vice-slots.json","fall-proof/result.json","native-fall-proof/proof.bin","dma-proof/proof.bin",
                 "ports-confirm/ports.bin","long-hits-a/op0-light.txt","alloc-replay/allocation.json","alloc-replay/failure.txt",
                 "alloc-release/allocation.json"):
        evidence[name]=copy(WORK/name,name.replace("/","-"))
    for scene in ("stairs","death"):
        p=ROOT/f"reference/analysis/render-coherence-2026-10-29/fields-qualified-render-{scene}/report.json"
        evidence[scene]=copy(p,"render-"+scene+".json")
    ui={m:copy(ROOT/f".tmp/op-finish/fields-qualified-{m}/normal.json","normal-"+m+".json") for m in ("cli","adf")}
    for m,entry in ui.items():
        result=read(ROOT/entry["path"])
        assert result["normal_exe_sha256"]==item(retail/"bruce_amiga.exe")["sha256"]
        assert result["fields"]>=6000 and result["pause_preserved"] and not result["after"]["fault"]
        if m=="cli":assert result["joystick_crossings"]==[2,1]
        else:assert result["turn_after_death"]["player"]==2
    # elf2hunk may leave different padding. Publish the exact boot-tested files.
    for name in ("bruce_amiga.exe","bruce_amiga.adf"):shutil.copyfile(retail/name,normal/name)
    shutil.copyfile(retail/"bruce_amiga.exe",ROOT/".tmp/amiga-boot/c/start")
    files={e["path"] for e in data["proofs"]}|{"core/c64_rooms.h","core/source_dma.c","tools/audit_c64_world.py",
        "reference/validation/source-input-slot.json","reference/analysis/irq-input-2026-10-30/report.json"}
    report=dict(predecessor=item(prior),normal_build=[item(ROOT/e["path"]) for e in data["normal_build"]],
        engine_sections=decimal_sections(normal/"c64_rooms.o"),dma_sections=decimal_sections(normal/"source_dma.o"),
        diagnostic_exe=item(probe/"bruce_amiga.exe")["sha256"],production_mode=mode,ui=ui,runs=routes,
        field_evidence=evidence,proofs=[item(ROOT/name) for name in sorted(files)])
    manifest=HERE/"delivery.json"
    manifest.write_text(json.dumps(report,indent=2)+"\n")
    parity=dict(capture_id="FIELD-WORK-0001",date="2026-11-01",
        reference_id="c64-local-t64-remember-no-trainers",source_ids=["SRC-007","SRC-008"],
        source_sha256=read(WORK/"fall-proof/result.json")["frozen_sha256"],
        addresses=["$169D-$1702","$4A85-$4A88","$2BF9-$2C51","$312C-$3183"],
        status="candidate_code_vice_and_scoped_a500_measurements",
        limits=["The VICE joystick trials start at the frozen snapshot and control the input boundary.",
                "Visible response latency on a physical controller and the complete IRQ raster schedule remain open.",
                "The Amiga combat routes and publication counts cover the recorded configurations and durations."],
        artifacts=[item(manifest),evidence["vice-slots.json"],evidence["fall-proof/result.json"],evidence["dma-proof/proof.bin"]])
    (ROOT/"docs/parity/evidence/FIELD-WORK-0001.json").write_text(json.dumps(parity,indent=2)+"\n")

if __name__=="__main__":main()
