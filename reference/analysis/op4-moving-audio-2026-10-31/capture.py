"""Stop source services for one selected combat call and export exact entry and exit."""
import sys
from probe import HERE,ROOT,WORK,sources,change,compile_program

def build():
    main,core=sources("reference");actor=(ROOT/"core/c64_actor_programs.h").read_text()
    cap=(HERE.parent/"op1-contact-budget-2026-10-31/capture.h").read_text()
    cap=cap[cap.index("extern volatile"):cap.index("static void probe_entry")]
    cap=cap.replace("extern volatile unsigned char probe_capture,probe_live;","extern unsigned char combat_arm;")
    core=change(core,'#include "c64_actor_programs.h"',cap+'\n#include "c64_actor_programs.h"')
    start="""if(combat_arm){
        unsigned long j;combat_arm=0;probe_collecting=1;probe_freeze();
        for(j=0;j<65536UL;j++)probe_image[j]=m[j];probe_point(0);
    }
    """
    actor=change(actor,"L29c3:; /* $29C3 */","L29c3:; /* $29C3 */\n"+start)
    actor=change(actor,"actor_code(0x29c3);PERF_END(BL_PERF_COMBAT);","actor_code(0x29c3);if(probe_collecting){probe_point(3);probe_collecting=0;}PERF_END(BL_PERF_COMBAT);")
    main=change(main,"static void light_config(void){","""unsigned char *probe_image,*probe_trace,combat_arm;
unsigned long probe_used,probe_records,probe_overflow;
void probe_freeze(void){game_field_active=source_audio_active=0;}
static void light_config(void){""")
    main=change(main,"    intro_decode(buffers[1]);","""    probe_image=AllocMem(65536UL,MEMF_CHIP);probe_trace=AllocMem(16384UL,MEMF_PUBLIC);
    if(!probe_image || !probe_trace){result=20;goto cleanup;}
    intro_decode(buffers[1]);""")
    main=change(main,"light_started=1;light_start_step=step;","combat_arm=1;light_started=1;light_start_step=step;")
    main=change(main,"if(light_started && step-light_start_step>=light_target){","if(light_started && probe_records){")
    anchor='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    main=change(main,anchor,'''append(&p,"\\ncapture_overflow=");number(&p,probe_overflow);
        append(&p,"\\ncapture_records=");number(&p,probe_records);
        file=Open((CONST_STRPTR)"DH1:combat.bin",MODE_NEWFILE);
        if(!file)result=20;
        else{if(Write(file,probe_image,65536)!=65536 || Write(file,probe_trace,probe_used)!=(LONG)probe_used)result=20;Close(file);}
        '''+anchor)
    main=change(main,"cleanup:\n","cleanup:\n    if(probe_image)FreeMem(probe_image,65536UL);if(probe_trace)FreeMem(probe_trace,16384UL);\n")
    f=WORK/"capture";f.mkdir(exist_ok=True)
    (f/"main.c").write_text(main);(f/"c64_rooms.c").write_text(core);(f/"c64_actor_programs.h").write_text(actor)
    compile_program(f,ROOT/".tmp/op1-kage/reference")
if __name__=="__main__":build()
