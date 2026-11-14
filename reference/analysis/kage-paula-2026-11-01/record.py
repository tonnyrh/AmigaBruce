"""Bind the scoped release to the normal executable and raw PAL output reports."""
import json
import shutil
import sys
from pathlib import Path
from compare import HERE,WORK

ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from verify_score_display_delivery import decimal_sections,item
sys.path.insert(0,str(HERE.parent/"op-finish-2026-10-31"))
from record_pipeline import normalized_hunk,sections

def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))

def record(mode, names, ui):
    dest=HERE/"runs";dest.mkdir(exist_ok=True)
    def copy(src,name):
        path=dest/name
        shutil.copyfile(src,path)
        return item(path)
    reports={}
    for label in names:
        folder=WORK/label
        reports[label]=dict(raw=copy(folder/"op0-light.txt",label+".txt"),
            exe=item(folder/"bruce_amiga.exe")["sha256"],route=(folder/"op0-route.bin").read_bytes().hex())
    witness={}
    comparison=read(WORK/"comparison.json")
    labels={"trace-a","trace-b","award-a","award-b","trace-long-1","old-still-a","old-still-b"}
    labels.update(name for pair in comparison["amiga"].values() for name in pair["files"])
    for mode_test in ("fold-long","long-hud","long-irq-polled-hud","long-sliced-polled-hud"):
        labels.update(mode_test+"-"+suffix for suffix in ("a","b"))
    for name in sorted(labels):
        folder=WORK/name
        witness[name]=dict(raw=copy(folder/"op0-light.txt",name+".txt"),route=(folder/"op0-route.bin").read_bytes().hex(),
            exe=item(folder/"bruce_amiga.exe")["sha256"])
    ui_reports={m:copy(ROOT/f".tmp/op-finish/{ui}-{m}/normal.json",f"normal-{m}.json") for m in ("cli","adf")}
    prior=HERE.parent/"op-finish-2026-10-31"
    parent=read(prior/"pipeline-result.json")
    normal=[item(ROOT/e["path"]) for e in parent["normal_build"]]
    actual=ROOT/"amiga/out";retail=WORK/("retail-"+mode)
    assert normalized_hunk(actual)==normalized_hunk(retail)
    def image(folder):
        raw,headers=sections(folder/"bruce_amiga.elf")
        return [(name,h[3],h[5],raw[h[4]:h[4]+h[5]] if h[1]!=8 else b"") for name,h in headers if h[2]&2]
    assert image(actual)==image(retail)
    assert (retail/"main.c").read_text()==(ROOT/"amiga/main.c").read_text()
    assert (retail/"source_audio.h").read_text()==(ROOT/"amiga/source_audio.h").read_text()
    assert (ROOT/"core/c64_rooms.c").read_text()==(WORK/mode/"c64_rooms.c").read_text()
    assert (ROOT/"core/c64_actor_programs.h").read_text()==(WORK/mode/"c64_actor_programs.h").read_text()
    engine=decimal_sections(ROOT/"amiga/out/c64_rooms.o")
    assert engine==decimal_sections(WORK/mode/"c64_rooms.o")
    result=dict(parent_commit="5ed53f670f0c434905b1d8eea1fd97e3739ea9bc",parent=item(prior/"pipeline-result.json"),
        production_mode=mode,diagnostic_exe=item(WORK/mode/"bruce_amiga.exe")["sha256"],engine_sections=engine,
        normal_build=normal,ui=ui_reports,runs=reports,witness=witness,
        comparison=copy(WORK/"comparison.json","input-and-combat.json"),
        cpu=copy(WORK/"proof/result.json","combat-cpu.json"),native=copy(WORK/"native-proof/proof.bin","combat-68000.bin"),
        proofs=[item(ROOT/f) for f in ("core/c64_rooms.c","core/c64_actor_programs.h","amiga/main.c","amiga/source_audio.h","tools/build_c64_rooms.py",
            "reference/analysis/actor-chain-2026-10-26/report.json","reference/analysis/actor-chain-2026-10-26/integrated-controls.json",
            "reference/analysis/actor-chain-2026-10-26/translation.json","reference/validation/source-world-native.json")])
    (HERE/"delivery.json").write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":
    record(sys.argv[1],sys.argv[3:],sys.argv[2])
