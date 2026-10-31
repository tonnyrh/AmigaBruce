"""Replay the timed diagnosis with the pilot decoder, preserving its counters."""
import subprocess
from pilot import PILOT,ROOT,OBJECTS,GCC,FLAGS,TOOLS,change,sha
from pathlib import Path
import json,re
out=PILOT/"timed"
out.mkdir(exist_ok=True)
base=PILOT.parent/"timed"
text=(base/"c64_rooms.c").read_text()
decl="static void source_vic_cache("
text=change(text,decl,"extern void bl_vic_decode_wide(const unsigned char *, unsigned char *, unsigned long *, unsigned long *);\n"+decl)
text=change(text,"    /* One read per source byte;",'''    if(wide && !multi && pointer<=0xffc1){
        bl_vic_decode_wide(m+pointer,raw,out_high,out_low);
        goto publish;
    }
    /* One read per source byte;''')
text=change(text,"    vic_layout[sprite]=(unsigned char)((multi?1:0)|(wide?2:0));","publish:\n    vic_layout[sprite]=(unsigned char)((multi?1:0)|(wide?2:0));")
src=out/"c64_rooms.c";src.write_text(text)
obj=out/"c64_rooms.o"
subprocess.run([GCC,*FLAGS,"-DOP2_FULL=1","-mshort","-Os","-I",base,"-I",ROOT/"core","-c",src,"-o",obj],check=True)
order=next(l for l in (ROOT/"amiga-build.ps1").read_text().splitlines() if l.startswith("$sources=@("))
objects=[OBJECTS/(Path(p).stem+".o") for p in re.findall("'([^']+)'",order)]
objects[objects.index(OBJECTS/"main.o")]=base/"main.o"
objects[objects.index(OBJECTS/"c64_rooms.o")]=obj
objects.append(PILOT/"light/vic_wide.o")
elf=out/"bruce_amiga.elf"
subprocess.run([GCC,*FLAGS,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
subprocess.run([TOOLS/"elf2hunk.exe",elf,out/"bruce_amiga.exe"],check=True)
inputs=[src,Path(__file__),*objects,elf,out/"bruce_amiga.exe",base/"inputs.json"]
(out/"inputs.json").write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in inputs},indent=2)+"\n")
