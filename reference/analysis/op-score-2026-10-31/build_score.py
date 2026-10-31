"""Private matched OP0 builds. The normal Amiga outputs are never written here."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-score"
sys.path.insert(0,str(HERE.parent/"op1-kage-prefix-2026-10-31"))
from build_pilot import sources,compile_program,change

def at(src,pc,code):
    label=f"L{pc:04x}:; /* ${pc:04X} */"
    return change(src,label,label+"\n"+code)

def make(mode):
    assert mode in ("reference","profile","candidate")
    out=WORK/mode
    out.mkdir(parents=True,exist_ok=True)
    main,core=sources("reference")
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    audio=(ROOT/"amiga/source_audio.h").read_text()
    hook="source_score_display();goto L1b28;\n"
    if mode!="candidate" and hook in actor:
        actor=change(actor,hook,"")
        core=change(core,(HERE/"display.h").read_text()+"\n","")
    main=change(main,'#include "source_audio.h"','''static UBYTE score_meter;
static ULONG score_outputs,score_last,score_holes,score_doubles;
#include "source_audio.h"''')
    audio=change(audio,"    for(c=0;c<3;c++){\n        const BlPaulaVoice",'''    if(score_meter){
        ULONG stamp=field_clock(),gap=(stamp-score_last)&0xffffffUL;
        if(score_outputs){if(!gap)++score_doubles;else score_holes+=gap-1;}
        ++score_outputs;score_last=stamp;
    }
    for(c=0;c<3;c++){
        const BlPaulaVoice''')
    main=change(main,"light_started=1;light_start_step=step;","score_meter=1;light_started=1;light_start_step=step;")
    main=change(main,"light_steps=step-light_start_step;","score_meter=0;light_steps=step-light_start_step;")
    end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    main=change(main,end,'''append(&p,"\\npaula_publications=");number(&p,score_outputs);
        append(&p,"\\npaula_empty=");number(&p,score_holes);
        append(&p,"\\npaula_double=");number(&p,score_doubles);
        '''+end)
    if mode=="profile":
        main=change(main,"static UBYTE score_meter;","static UBYTE score_meter;unsigned short probe_step;")
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)probe_step=(UWORD)(step-light_start_step);\n            if(light_started && step!=light_steps_begin){")
        main=change(main,"static void light_config(void){","unsigned long score_clock(void){return line_clock();}\nextern unsigned long score_sections[4], score_events;\nstatic void light_config(void){")
        core=change(core,'#include "c64_actor_programs.h"', '''extern unsigned long score_clock(void);
unsigned long score_sections[4],score_events;extern unsigned short probe_step;
static unsigned long segment_start;
static unsigned char track_award;
static void section_done(unsigned char i){
    if(track_award){unsigned long now=score_clock();score_sections[i]+=(now-segment_start)&0xffffffUL;segment_start=now;}
}
#include "c64_actor_programs.h"''')
        # Only the captured long-fall path. End the final phase at the tail RTS.
        actor=at(actor,0x3175,"if((probe_step==168 || probe_step==207) && x==2 && m[0x51]==2 && (m[0xbe]&16) && (a==50 || a==200)){track_award=1;++score_events;segment_start=score_clock();}")
        for pc,i in ((0x312c,0),(0x315a,1),(0x315d,2)):
            actor=at(actor,pc,f"section_done({i});")
        actor=at(actor,0x1b28,"if(track_award && y==0x34){section_done(3);track_award=0;}")
        main=change(main,end,'''append(&p,"\\naward_events=");number(&p,score_events);
        append(&p,"\\naward_sections=");for(k=0;k<4;k++){if(k)append(&p,",");number(&p,score_sections[k]);}
        '''+end)
    if mode=="candidate" and "source_score_display" not in core:
        core=change(core,'#include "c64_actor_programs.h"',(HERE/"display.h").read_text()+'\n#include "c64_actor_programs.h"')
        actor=at(actor,0x315d,"source_score_display();goto L1b28;")
    for name,data in (("main.c",main),("c64_rooms.c",core),("source_audio.h",audio),("c64_actor_programs.h",actor)):
        (out/name).write_text(data)
    shared=WORK/"reference"
    compile_program(out,shared if mode!="reference" and (shared/"game.o").is_file() else None)

if __name__=="__main__":
    make(sys.argv[1])
