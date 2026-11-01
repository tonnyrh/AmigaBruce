"""Archive completed runs only, including actual executable and configured machine identities."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-finish"
sys.path.insert(0,str(ROOT/"tools"))
from verify_score_display_delivery import engine_hash,decimal_sections
from audit_vic_native_kernels import sections

def item(p):
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def main():
    runs=HERE/"runs";runs.mkdir(exist_ok=True)
    names=["actor-"+str(n) for n in range(4)]+["outer-0","outer-3","stairs","yamo13","ref-still","ref-move",
      "counts-still","counts-move","history-move","field-move","mix-still","mix-still-b","mix-move","mix-move-b","mix-r12","mix-r13",
      "comp-still","comp-move-a","comp-move-b","tour-a","tour-b","dma-a","dma-b","tour-rows-a2","tour-rows-b2",
      "tour-load-a2","tour-load-b2","release-phases","long-a","long-b","long-release-a","long-release-b"]
    names += [kind+"-"+route for kind in ("kernel","publisher") for route in ("move-a","move-b","still-a","stairs","yamo")]
    names += [kind+"-"+route for kind in ("final","irq","irq-active") for route in ("move","move2","still","stairs","yamo")]
    names += ["irq-copy-"+route for route in ("move","move2","still","stairs","yamo")]
    names += ["guard-still","guard-move","queue-still","queue-move","queue-move2","neutral-still","neutral-move"]
    names += ["queue-copy-"+route for route in ("move","still","stairs","yamo")]
    records={}
    for name in names:
        origin=WORK/name
        source=origin/"op0-light.txt";values=dict(l.split("=",1) for l in source.read_text().splitlines() if "=" in l)
        assert all(values[x]=="0" for x in ("source_fault","audio_fault","dma_fault","source_profile")),name
        assert values["finished"]==values["restored_os"]=="1"
        assert int(values["pal_fields"])>=6000 if name.startswith("long-") else int(values["steps"])==240
        conf=(origin/"a500.uae").read_text()
        assert all(c in conf.splitlines() for c in ("cpu_speed=real","cpu_model=68000","chipset=ocs","chipmem_size=1","bogomem_size=2","cycle_exact=true"))
        dst=runs/(name+".txt");shutil.copyfile(source,dst)
        records[name]=dict(report=item(dst),exe_sha256=item(origin/"bruce_amiga.exe")["sha256"],route=(origin/"op0-route.bin").read_bytes().hex())
    for src,name in ((WORK/"block-proof/result.json","source-blocks"),(WORK/"image-proof.json","source-images"),(WORK/"irq-proof.json","source-irq"),
                     (WORK/"normal-cli-b/normal.json","normal-cli"),(WORK/"normal-adf-a/normal.json","normal-adf")):
        shutil.copyfile(src,runs/(name+".json"))
    for mode in ("cli","adf"):
        assert (WORK/f"normal-{mode}-a/menu.bpl").read_bytes()==(ROOT/"reference/analysis/op-score-decimal-2026-10-31/boot"/mode/"menu.bpl").read_bytes()
    cross=json.loads((WORK/"cross-source/normal.json").read_text())
    assert cross["joystick_crossings"]==[2,1]
    cli=runs/"normal-cli.json";v=json.loads(cli.read_text())
    assert cross["normal_exe_sha256"]==v["normal_exe_sha256"]
    v.update(joystick_crossings=cross["joystick_crossings"],crossing_probe="separate normal CLI boot",
             trellis_entry=cross["trellis_entry"],trellis_exit=cross["trellis_exit"])
    cli.write_text(json.dumps(v,indent=2)+"\n")
    for label in ("stairs","death"):
        source=ROOT/f"reference/analysis/render-coherence-2026-10-29/op-finish-render-{label}/report.json"
        shutil.copyfile(source,runs/f"render-{label}.json")
    private=ROOT/"reference/analysis/render-coherence-2026-10-29/op-finish-queued-stairs/report.json"
    shutil.copyfile(private,runs/"queue-render-initial.json")
    shutil.copyfile(WORK/"object-row-proof/result.json",runs/"source-neutral-objects.json")
    parent=json.loads((ROOT/"reference/analysis/op-score-decimal-2026-10-31/build.json").read_text())
    normal=[item(ROOT/e["path"]) for e in parent["normal_build"]]
    assert (WORK/"final/c64_rooms.c").read_text()==(ROOT/"core/c64_rooms.c").read_text()
    assert (WORK/"final/c64_actor_programs.h").read_text()==(ROOT/"core/c64_actor_programs.h").read_text()
    assert engine_hash(WORK/"final/c64_rooms.o")==engine_hash(ROOT/"amiga/out/c64_rooms.o")
    assert decimal_sections(WORK/"final/c64_rooms.o")==decimal_sections(ROOT/"amiga/out/c64_rooms.o")
    measurement=dict(runs=records,normal_build=normal,inputs=[item(ROOT/e["path"]) for e in parent["inputs"]],
                     engine_sections=decimal_sections(WORK/"final/c64_rooms.o"),
                     previous_delivery=item(HERE/"previous-delivery.json"),
                     evidence=[item(p) for p in sorted(runs.glob("*.json"))])
    (HERE/"result.json").write_text(json.dumps(measurement,indent=2)+"\n")

if __name__=="__main__":main()
