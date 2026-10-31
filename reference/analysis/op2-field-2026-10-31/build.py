"""Build isolated site-only and VIC-timed programs from the measured OP0 inputs."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OP0=HERE.parent/"op0-light-2026-10-31"
OBJECTS=OP0/"light/out"
TOOLS=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
GCC=TOOLS/"opt/bin/m68k-amiga-elf-gcc.exe"
FLAGS=["-m68000","-O2","-g","-nostdlib","-ffreestanding","-fno-builtin","-fno-tree-loop-distribute-patterns","-fomit-frame-pointer","-ffunction-sections","-fdata-sections","-DBL_AUTOTEST=0"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def change(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)

def sources(out):
    main=(OP0/"main.c").read_text()
    audio=(ROOT/"amiga/source_audio.h").read_text()
    core=(ROOT/"core/c64_rooms.c").read_text(encoding="utf-8-sig")
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    audio=audio.replace("source_audio_service(void)","source_audio_service(UWORD site)")
    audio=change(audio,"&0xffffffUL;if(!gap)return;", "&0xffffffUL;op2_poll(now,gap,site,source_audio_context);if(!gap)return;")
    main=change(main,'#include "source_audio.h"','#include "observer.h"\n#include "source_audio.h"')
    # Tag actual existing calls in lexical order. Both wait-loop arms use
    # the same tag. Only the post-field poll consumes a field timing.
    sites=[1,2,7,7,8,9,9,10,3,4,5,6]
    assert main.count("source_audio_service();")==len(sites)
    tags=iter(sites)
    main=re.sub(r"source_audio_service\(\);",lambda _:f"source_audio_service({next(tags)});",main)
    main=change(main,"while(gap--){bl_c64_field();source_audio_service(2);}",
        "while(gap--){op2_before_field();bl_c64_field();op2_after_field();source_audio_service(2);}")
    main=change(main,"light_started=1;light_start_step=step;", "op2_start();light_started=1;light_start_step=step;")
    main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)op2_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
    main=change(main,"light_steps=step-light_start_step;", "op2_live=0;light_steps=step-light_start_step;")
    main=change(main,'append(&p,"\\nrestored_os=1\\nfinished=1\\n");',
                'if(!op2_save())result=20;\n        append(&p,"\\nrestored_os=1\\nfinished=1\\n");')
    # Core callback origin is restored across nested calls. Register/flag
    # updates and all original guest writes and calls stay at their sites.
    def tag_io(src,ids):
        ids=iter(ids)
        return re.sub(r"io_service\(\);",lambda _:f"{{unsigned short saved_origin=op2_origin;op2_origin={next(ids)};io_service();op2_origin=saved_origin;}}",src)
    assert core.count("io_service();")==4 and actor.count("io_service();")==2
    core=tag_io(core,[1,2,3,4])
    actor=tag_io(actor,[5,6])
    core="extern unsigned short op2_origin;\nextern unsigned char op2_kind,op2_builds;\nextern unsigned long op2_vic_lines,op2_cache_lines,op2_clock(void);\n"+core
    core=change(core,"if(bl_vic_repeat(m,&vic_repeat))return;",
                     "if(bl_vic_repeat(m,&vic_repeat)){if(OP2_FULL)op2_kind=1;return;}")
    core=change(core,"if(!candidates){vic_last_bits=0;","if(!candidates){if(OP2_FULL)op2_kind=2;vic_last_bits=0;")
    core=change(core,"if(same){m[0xd01e]|=vic_last_bits;return;}",
                     "if(same){if(OP2_FULL)op2_kind=3;m[0xd01e]|=vic_last_bits;return;}\n    if(OP2_FULL)op2_kind=4;")
    core=change(core,"unsigned char row,j,b,*raw=vic_bytes[sprite];",
                     "unsigned long cache_start=OP2_FULL?op2_clock():0;\n    unsigned char row,j,b,*raw=vic_bytes[sprite];")
    core=change(core,"vic_valid|=(unsigned char)(1<<sprite);\n}",
                     "vic_valid|=(unsigned char)(1<<sprite);\n    if(OP2_FULL){op2_kind=5;++op2_builds;op2_cache_lines+=(op2_clock()-cache_start)&0xffffffUL;}\n}")
    core=change(core,"PERF_BEGIN(BL_PERF_VIC);source_vic_latch();PERF_END(BL_PERF_VIC);",
              "{unsigned long vic_start=OP2_FULL?op2_clock():0;source_vic_latch();if(OP2_FULL)op2_vic_lines=(op2_clock()-vic_start)&0xffffffUL;}")
    for name,data in [("main.c",main),("source_audio.h",audio),("c64_rooms.c",core),("c64_actor_programs.h",actor)]:
        (out/name).write_text(data)
    shutil.copyfile(HERE/"observer.h",out/"observer.h")

def build(mode):
    assert mode in ("sites","timed")
    out=HERE/mode
    out.mkdir(exist_ok=True)
    sources(out)
    flags=FLAGS+[f"-DOP2_FULL={int(mode=='timed')}"]
    order=next(line for line in (ROOT/"amiga-build.ps1").read_text().splitlines() if line.startswith("$sources=@("))
    objects=[OBJECTS/(Path(p).stem+".o") for p in re.findall("'([^']+)'",order)]
    for name,extra in [("main",["-I",ROOT/"amiga"]),("c64_rooms",["-mshort","-Os","-I",ROOT/"core"])]:
        obj=out/(name+".o")
        subprocess.run([GCC,*flags,*extra,"-c",out/(name+".c"),"-o",obj],check=True)
        objects[objects.index(OBJECTS/obj.name)]=obj
    elf=out/"bruce_amiga.elf"
    subprocess.run([GCC,*flags,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([sys.executable,ROOT/"tools/verify_amiga_entry.py",elf],check=True)
    subprocess.run([TOOLS/"elf2hunk.exe",elf,out/"bruce_amiga.exe"],check=True)
    inputs=[Path(__file__),HERE/"observer.h",OP0/"main.c",ROOT/"core/c64_rooms.c",ROOT/"core/c64_actor_programs.h",
            ROOT/"amiga/source_audio.h",*out.glob("*.c"),*out.glob("*.h"),*objects,elf,out/"bruce_amiga.exe"]
    (out/"inputs.json").write_text(json.dumps({p.relative_to(ROOT).as_posix():sha(p) for p in inputs},indent=2)+"\n")

if __name__=="__main__":
    build(sys.argv[1])
