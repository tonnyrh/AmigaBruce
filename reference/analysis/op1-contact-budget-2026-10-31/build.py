"""Build R01 diagnostics in .tmp from current game sources and the existing OP0 route."""
import re, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/".tmp/op1-budget"
sys.path.insert(0,str(ROOT/"tools"))
import build_light_op0_probe as op
def change(s,old,new):
    if s.count(old)!=1:raise ValueError((old,s.count(old)))
    return s.replace(old,new)
def sources(folder):
    op.BASE=folder/"op0";op.main()
    main=(op.BASE/"main.c").read_text()
    core=(ROOT/"core/c64_rooms.c").read_text()
    main=change(main,"static void light_config(void){",(HERE/"clock.h").read_text()+"""
void probe_freeze(void){game_field_active=0;source_audio_active=0;}
static void light_config(void){""")
    anchor="    light_warmup=((UWORD)"
    main=change(main,anchor,"    probe_enabled=light_route[3]==1 || light_route[3]==2;probe_mask=light_route[3]==2?7:0;\n"+anchor)
    anchor="    intro_decode(buffers[1]);"
    main=change(main,anchor,"""    if(light_route[3]==3){
        probe_image=AllocMem(65536UL,MEMF_CHIP);probe_trace=AllocMem(16384UL,MEMF_PUBLIC);
        if(!probe_image || !probe_trace){result=20;goto cleanup;}
    }
"""+anchor)
    main=change(main,"light_started=1;light_start_step=step;","probe_live=1;probe_capture=(UBYTE)(light_route[3]==3);light_started=1;light_start_step=step;")
    main=change(main,"light_steps=step-light_start_step;","probe_live=0;light_steps=step-light_start_step;")
    main=change(main,"light_audio_fault=bl_source_audio_faults();\n                break;",
        "light_audio_fault=bl_source_audio_faults();\n                if(probe_enabled)probe_calibrate();\n                break;")
    anchor='        append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    main=change(main,anchor,"""        append(&p,"\\nprobe_mode=");number(&p,light_route[3]);
        append(&p,"\\ncontact_calls=");number(&p,probe_calls);
        append(&p,"\\nprofiled_calls=");number(&p,probe_picked);
        append(&p,"\\ncontact_lines=");for(k=0;k<6;k++){if(k)append(&p,",");number(&p,probe_bins[k]);}
        append(&p,"\\nactor_seams=");number(&p,probe_points[0]);
        append(&p,"\\nrow_seams=");number(&p,probe_points[1]);
        append(&p,"\\nempty_256_pairs_lines=");number(&p,probe_empty);
        append(&p,"\\nempty_work_lines=");number(&p,probe_empty_work);
        append(&p,"\\ncapture_records=");number(&p,probe_records);
        append(&p,"\\ncapture_overflow=");number(&p,probe_overflow);
        if(probe_records){
            file=Open((CONST_STRPTR)"DH1:capture.bin",MODE_NEWFILE);
            if(file){if(Write(file,probe_image,65536)!=65536 || Write(file,probe_trace,probe_used)!=(LONG)probe_used)result=20;Close(file);}
            else result=20;
        }
"""+anchor)
    main=change(main,"cleanup:\n","cleanup:\n    if(probe_image)FreeMem(probe_image,65536UL);if(probe_trace)FreeMem(probe_trace,16384UL);\n")
    # Finish the diagnostic immediately after the selected call. Its source
    # field clock was deliberately frozen, so another game step is not due.
    main=change(main,"if(light_started && step-light_start_step>=light_target){",
           "if(light_started && (probe_records || step-light_start_step>=light_target)){")
    anchor="/* Virtual registers remain local until a source helper, service or return. */"
    core=change(core,anchor,(HERE/"capture.h").read_text()+"\n"+anchor)
    core=change(core,"z=zz;n=nn;io_service();","z=zz;n=nn;probe_service(2);")
    core=change(core,"    unsigned char part,actor,pose;\n    x=2;","    unsigned char part,actor,pose;\n    probe_entry();probe_begin();x=2;")
    core=change(core,"if(actor_world_enabled && io_service)io_service();\n        m[0x50]","if(actor_world_enabled && io_service)probe_service(1);\n        m[0x50]")
    core=change(core,"if(n){sp+=2;return;}\n    }\n}\n#include \"c64_actor_programs.h\"","if(n){sp+=2;probe_finish();if(probe_collecting){probe_point(3);probe_collecting=0;}return;}\n    }\n}\n#include \"c64_actor_programs.h\"")
    (folder/"main.c").write_text(main);(folder/"c64_rooms.c").write_text(core)
def compile_program(folder,shared=None):
    tools=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    cc=tools/"opt/bin/m68k-amiga-elf-gcc.exe"
    flags="-m68000 -O2 -g -nostdlib -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns -fomit-frame-pointer -ffunction-sections -fdata-sections -Wno-array-bounds -DBL_AUTOTEST=0".split()
    flags+=["-I"+str(ROOT/"amiga"),"-I"+str(ROOT/"core")]
    files=re.search(r"(?m)^\$sources=@\((.+)\)$",(ROOT/"amiga-build.ps1").read_text(encoding="utf-8-sig")).group(1)
    objects=[]
    for name in re.findall("'([^']+)'",files):
        src=ROOT/name;obj=folder/(src.stem+".o");extra=[]
        if name in ("core/c64_rooms.c","amiga/main.c"):src=folder/src.name
        elif shared is not None:
            objects.append(shared/obj.name);continue
        if name=="core/c64_rooms.c":extra=["-mshort","-Os"]
        subprocess.run([cc,*flags,*extra,"-c",src,"-o",obj],check=True);objects.append(obj)
    elf=folder/"bruce_amiga.elf"
    subprocess.run([cc,*flags,"-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start",*objects,"-o",elf],check=True)
    subprocess.run([sys.executable,ROOT/"tools/verify_amiga_entry.py",elf],check=True)
    subprocess.run([tools/"elf2hunk.exe",elf,elf.with_suffix(".exe")],check=True)
if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True);sources(OUT);compile_program(OUT)

