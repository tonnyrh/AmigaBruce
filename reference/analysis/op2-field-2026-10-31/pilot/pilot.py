"""Link OP0 with one guarded replacement for opaque-row expansion."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
PILOT=Path(__file__).resolve().parent
sys.path.insert(0,str(PILOT.parent))
from build import ROOT,OP0,OBJECTS,GCC,FLAGS,TOOLS,change,sha

def core_text():
    text=(ROOT/"core/c64_rooms.c").read_text(encoding="utf-8-sig")
    decl="static void source_vic_cache("
    text=change(text,decl,"#if defined(__m68k__)\nextern void bl_vic_decode_wide(const unsigned char *, unsigned char *, unsigned long *, unsigned long *);\n#endif\n"+decl)
    anchor="    /* One read per source byte;"
    return change(text,anchor,'''#if defined(__m68k__)
    if(wide && !multi && pointer<=0xffc1){
        bl_vic_decode_wide(m+pointer,raw,out_high,out_low);
        vic_layout[sprite]=2;
        vic_valid|=(unsigned char)(1<<sprite);
        return;
    }
#endif
'''+anchor)

def build(mode):
    out=PILOT/mode
    out.mkdir(exist_ok=True)
    core=PILOT/"c64_rooms.c"
    core.write_text(core_text())
    order=next(l for l in (ROOT/"amiga-build.ps1").read_text().splitlines() if l.startswith("$sources=@("))
    parent_objects=OP0/"bare/out" if mode=="bare" else OBJECTS
    objects=[parent_objects/(Path(p).stem+".o") for p in re.findall("'([^']+)'",order)]
    asm=out/"vic_wide.o"
    subprocess.run([GCC,*FLAGS,"-c",PILOT/"vic_wide.s","-o",asm],check=True)
    if mode=="proof":
        main=out/"proof.o"
        subprocess.run([GCC,*FLAGS,"-c",PILOT/"proof.c","-o",main],check=True)
        objects=[parent_objects/"start.o",main,asm,parent_objects/"runtime.o"]
    else:
        obj=out/"c64_rooms.o"
        subprocess.run([GCC,*FLAGS,"-mshort","-Os","-I",ROOT/"core","-c",core,"-o",obj],check=True)
        objects[objects.index(parent_objects/obj.name)]=obj
        objects.append(asm)
    elf=out/"bruce_amiga.elf"
    subprocess.run([GCC,*FLAGS,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([sys.executable,ROOT/"tools/verify_amiga_entry.py",elf],check=True)
    subprocess.run([TOOLS/"elf2hunk.exe",elf,out/"bruce_amiga.exe"],check=True)
    paths=[Path(__file__),PILOT/"vic_wide.s",core,*objects,elf,out/"bruce_amiga.exe"]
    if mode=="proof":paths.append(PILOT/"proof.c")
    (out/"inputs.json").write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in paths},indent=2)+"\n")

if __name__=="__main__":build(sys.argv[1])
