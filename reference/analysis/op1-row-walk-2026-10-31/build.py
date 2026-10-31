"""Build the OP1 pilot by relinking the measured OP0 objects with one new row kernel."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OP0 = HERE.parent / "op0-light-2026-10-31"
OBJECTS = OP0 / "light/out"
TOOLS = sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
GCC = TOOLS/"opt/bin/m68k-amiga-elf-gcc.exe"
FLAGS = ["-m68000", "-O2", "-nostdlib", "-ffreestanding", "-fno-builtin", "-fomit-frame-pointer", "-ffunction-sections", "-fdata-sections"]
MARKER = "/* GENERATED_CONTACT_CLASSES_BEGIN */"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(mode):
    parent = ROOT/"amiga/contact_rows.s"
    kernel = HERE/"contact_rows.s"
    kernel.write_text((HERE/"rows.s").read_text() + MARKER + parent.read_text().split(MARKER)[1])
    out = HERE/mode
    out.mkdir(exist_ok=True)
    def compile(src):
        obj = out / (src.stem+".o")
        subprocess.run([GCC, *FLAGS, "-c", src, "-o", obj], check=True)
        return obj
    rows = compile(kernel)
    if mode=="proof":
        objects = [OBJECTS/"start.o", compile(HERE/"proof.c"), rows, OBJECTS/"runtime.o"]
    else:
        source_line = next(line for line in (ROOT/"amiga-build.ps1").read_text().splitlines() if line.startswith("$sources=@("))
        objects = [OBJECTS/(Path(name).stem+".o") for name in re.findall("'([^']+)'",source_line)]
        objects[objects.index(OBJECTS/"contact_rows.o")] = rows
    elf = out/"bruce_amiga.elf"
    subprocess.run([GCC,*FLAGS,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([sys.executable,ROOT/"tools/verify_amiga_entry.py",elf],check=True)
    subprocess.run([TOOLS/"elf2hunk.exe",elf,out/"bruce_amiga.exe"],check=True)
    paths = [parent,HERE/"build.py",HERE/"rows.s",kernel,*objects,elf,out/"bruce_amiga.exe"]
    (out/"inputs.json").write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in paths},indent=2)+"\n")

if __name__=="__main__":
    build(sys.argv[1])
