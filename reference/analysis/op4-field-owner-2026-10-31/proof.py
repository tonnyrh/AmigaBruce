"""Reuse the private route's exact generated engine and scheduler for proof."""
import shutil
from oracle import fixture
from build_owner import HERE, WORK, ROOT, compile_program

def build():
    fixture()
    out = WORK / "proof"
    for name in ("c64_actor_programs.h", "irq_context.h", "input_slot.h"):
        shutil.copyfile(WORK / "candidate" / name, out / name)
    shutil.copyfile(HERE / "clock.h", out / "clock.h")
    shutil.copyfile(HERE / "proof_main.c", out / "main.c")
    core = (WORK / "candidate/c64_rooms.c").read_text() + (HERE / "proof_core.h").read_text()
    (out / "c64_rooms.c").write_text(core)
    compile_program(out, ROOT / ".tmp/op1-kage/reference")

if __name__ == "__main__":
    build()
