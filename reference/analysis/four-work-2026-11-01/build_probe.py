"""Rebuild the measured short or long game using the preceding route harness."""
import argparse
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    args = argparse.ArgumentParser()
    args.add_argument("route",choices=("short","long"))
    args.add_argument("output",type=Path)
    config = args.parse_args()
    dest = config.output.resolve()
    dest.mkdir(parents=True,exist_ok=False)
    last = ROOT / ".tmp/actor-draw"
    source = last / ("actors" if config.route=="short" else "long-actors")
    merged = subprocess.run(["git","merge-file","-p",source/"main.c",
                             last/"retail-actors/main.c",ROOT/"amiga/main.c"],
                            check=True,stdout=subprocess.PIPE)
    (dest/"main.c").write_bytes(merged.stdout)
    shutil.copyfile(source/"source_audio.h",dest/"source_audio.h")
    tools = sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    cc = tools/"opt/bin/m68k-amiga-elf-gcc.exe"
    flags = ["-m68000","-O2","-g","-nostdlib","-ffreestanding","-fno-builtin",
             "-fno-tree-loop-distribute-patterns","-fomit-frame-pointer","-ffunction-sections",
             "-fdata-sections","-Wno-array-bounds","-DBL_AUTOTEST=0",
             "-I"+str(ROOT/"amiga"),"-I"+str(ROOT/"core")]
    files = re.search(r"(?m)^\$sources=@\((.+)\)$",(ROOT/"amiga-build.ps1").read_text(encoding="utf-8-sig"))[1]
    objects = []
    for path in re.findall("'([^']+)'",files):
        name = Path(path).stem+".o"
        if path in ("amiga/main.c","core/session.c","amiga/contact_rows.s"):
            src = dest/"main.c" if path=="amiga/main.c" else ROOT/path
            obj = dest/name
            subprocess.run([cc,*flags,"-c",src,"-o",obj],check=True)
        elif path=="core/c64_rooms.c":
            obj = last/"actors"/name
        else:
            obj = ROOT/".tmp/field-work/release"/name
        objects.append(obj)
    elf = dest/"bruce_amiga.elf"
    subprocess.run([cc,*flags,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([tools/"elf2hunk.exe",elf,elf.with_suffix(".exe")],check=True)


if __name__=="__main__":
    main()
