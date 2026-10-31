from pathlib import Path
import build_pilot as b
p=b.WORK/"proof";p.mkdir(exist_ok=True)
core=(b.WORK/"candidate/c64_rooms.c").read_text()
(p/"c64_rooms.c").write_text(core+"\n"+(b.HERE/"witness.h").read_text())
(p/"main.c").write_text((b.HERE/"proof_main.c").read_text())
b.compile_program(p,b.WORK/"reference")
