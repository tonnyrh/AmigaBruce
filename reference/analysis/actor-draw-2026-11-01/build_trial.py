"""Apply the ordinary display change to either of the timed field-work builds."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / ".tmp/field-work"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", choices=("release", "long-release"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    dest = args.output.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    source = BASE / args.probe
    merged = subprocess.run(["git", "merge-file", "-p", source / "main.c",
                             BASE / "retail-release/main.c", ROOT / "amiga/main.c"],
                            check=True, stdout=subprocess.PIPE)
    (dest / "main.c").write_bytes(merged.stdout)
    shutil.copyfile(source / "source_audio.h", dest / "source_audio.h")
    toolchain = sorted((Path.home() / ".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    cc = toolchain / "opt/bin/m68k-amiga-elf-gcc.exe"
    flags = ["-m68000", "-O2", "-g", "-nostdlib", "-ffreestanding", "-fno-builtin",
             "-fno-tree-loop-distribute-patterns", "-fomit-frame-pointer", "-ffunction-sections",
             "-fdata-sections", "-Wno-array-bounds", "-DBL_AUTOTEST=0",
             "-I"+str(ROOT / "amiga"), "-I"+str(ROOT / "core")]
    subprocess.run([cc, *flags, "-c", dest / "main.c", "-o", dest / "main.o"], check=True)
    subprocess.run([cc, *flags, "-mshort", "-Os", "-c", ROOT / "core/c64_rooms.c",
                    "-o", dest / "c64_rooms.o"], check=True)
    build_script = (ROOT / "amiga-build.ps1").read_text(encoding="utf-8-sig")
    sources = re.search(r"(?m)^\$sources=@\((.+)\)$", build_script)[1]
    objects = []
    for name in re.findall("'([^']+)'", sources):
        folder = dest if name in ("amiga/main.c","core/c64_rooms.c") else BASE / "release"
        objects.append(folder / (Path(name).stem+".o"))
    elf = dest / "bruce_amiga.elf"
    subprocess.run([cc, *flags, "-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",
                    *objects, "-o", elf], check=True)
    subprocess.run([sys.executable, ROOT / "tools/verify_amiga_entry.py", elf], check=True)
    subprocess.run([toolchain / "elf2hunk.exe", elf, elf.with_suffix(".exe")], check=True)


if __name__ == "__main__":
    main()
