"""Use the score candidate inside the same interleaved combat witness as OP4."""
import shutil
from build_score import HERE,ROOT,WORK,at,change,compile_program

def build():
    base=ROOT/".tmp/op4-owner/proof"
    out=WORK/"proof"
    out.mkdir(exist_ok=True)
    for name in ("cases.bin","main.c","clock.h","irq_context.h","input_slot.h"):
        shutil.copyfile(base/name,out/name)
    core=(base/"c64_rooms.c").read_text()
    actor=(base/"c64_actor_programs.h").read_text()
    if "source_score_display" not in core:
        core=change(core,'#include "c64_actor_programs.h"',(HERE/"display.h").read_text()+'\n#include "c64_actor_programs.h"')
        actor=at(actor,0x315d,"source_score_display();goto L1b28;")
    (out/"c64_rooms.c").write_text(core)
    (out/"c64_actor_programs.h").write_text(actor)
    compile_program(out,ROOT/".tmp/op1-kage/reference")

if __name__=="__main__":
    build()
