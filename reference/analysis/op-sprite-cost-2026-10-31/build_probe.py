"""Instrument the delivered engine privately. Use the same OP0/Paula meter for both builds."""
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-sprite-cost"
sys.path.insert(0,str(HERE.parent/"op-score-decimal-2026-10-31"))
from build_decimal import build as build_decimal,change,compile_program

def inject(actor,pc,statement):
    label=f"L{pc:04x}:; /* ${pc:04X} */"
    return change(actor,label,label+"\n"+statement)

def build(mode="profile"):
    assert mode in ("reference","profile","outer")
    parent=ROOT/".tmp/op-decimal/candidate"
    if not (parent/"main.c").is_file():build_decimal("candidate",False)
    main=(parent/"main.c").read_text();core=(parent/"c64_rooms.c").read_text()
    actor=(parent/"c64_actor_programs.h").read_text()
    assert core==(ROOT/"core/c64_rooms.c").read_text() and actor==(ROOT/"core/c64_actor_programs.h").read_text()
    call="PERF_BEGIN(BL_PERF_SPRITES);actor_code(0x2584);PERF_END(BL_PERF_SPRITES);"
    anchor="m[0x100 + sp--]=0x1c;m[0x100 + sp--]=0x2e;"+call
    if mode=="outer":
        core=change(core,'#include "c64_actor_programs.h"', '''extern unsigned long sprite_clock(void);
extern unsigned char outer_on,outer_inside;unsigned long outer_calls,outer_lines,outer_start,outer_awards;
#include "c64_actor_programs.h"''')
        actor=change(actor,anchor,anchor.replace(call,"if(outer_on){outer_inside=1;outer_start=sprite_clock();}"+call+
                     "if(outer_on){outer_lines+=(sprite_clock()-outer_start)&0xffffffUL;outer_inside=0;++outer_calls;}"))
        actor=inject(actor,0x3175,"if(outer_on)++outer_awards;")
        main=change(main,"static void source_game_service(void){","unsigned char outer_inside;static ULONG outer_due,outer_paid;\nstatic void source_game_service(void){")
        main=change(main,"game_field_busy=1;while(gap--)","if(outer_inside && gap){outer_due+=gap;++outer_paid;}\n    game_field_busy=1;while(gap--)")
        main=change(main,"static void light_config(void){",'''unsigned char outer_on;extern unsigned long outer_calls,outer_lines,outer_awards;
static ULONG outer_blank;unsigned long sprite_clock(void){return line_clock();}
static void light_config(void){''')
        main=change(main,"score_meter=1;light_started=1;","outer_on=1;score_meter=1;light_started=1;")
        main=change(main,"light_audio_fault=bl_source_audio_faults();\n                break;",'''light_audio_fault=bl_source_audio_faults();
                outer_on=0;{ULONG i;for(i=0;i<outer_calls;i++){ULONG stamp=sprite_clock();outer_blank+=(sprite_clock()-stamp)&0xffffffUL;}}
                break;''')
        end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,end,'''append(&p,"\\nouter_calls=");number(&p,outer_calls);
        append(&p,"\\nouter_lines=");number(&p,outer_lines);
        append(&p,"\\nouter_blank=");number(&p,outer_blank);
        append(&p,"\\nouter_awards=");number(&p,outer_awards);
        append(&p,"\\nouter_due=");number(&p,outer_due);
        append(&p,"\\nouter_paid=");number(&p,outer_paid);
        '''+end)
    if mode!="profile":
        write_build(mode,main,core,actor,parent)
        return
    core=change(core,'#include "c64_actor_programs.h"',(HERE/"profile.h").read_text()+'\n#include "c64_actor_programs.h"')
    actor=change(actor,anchor,anchor.replace(call,"sprite_begin();"+call+"sprite_end();"))
    actor=inject(actor,0x3175,"if(probe_enabled)++sprite_awards;")
    service="if(actor_world_enabled && io_service)io_service();"
    label='L2586:; /* $2586 */\n'
    actor=change(actor,label+service,label+"if(sprite_detail)sprite_mark(SERVICE,x);\n"+service+
                 "\nif(sprite_detail)sprite_mark(SETUP,sprite_actor);")
    for entry,ret,kind in [(0x2591,0x2594,"DESTINATION"),(0x25b9,0x25bc,"DESTINATION"),
                           (0x2598,0x259b,"POSE"),(0x25c1,0x25c4,"POSE"),
                           (0x25ab,0x25ae,"COPY"),(0x25d4,0x25d7,"COPY")]:
        extra="++parts[sprite_samples][sprite_actor];" if kind=="COPY" else ""
        actor=inject(actor,entry,f"if(sprite_detail){{{extra}sprite_mark({kind},sprite_actor);}}")
        # $25D7 is also reached when the secondary component is absent.
        actor=inject(actor,ret,f"if(sprite_detail && sprite_phase=={kind})sprite_mark(SETUP,sprite_actor);")
    decl='''extern void sprite_arm(void),sprite_finish(void);
extern unsigned char sprite_detail,sprite_actor,sprite_phase;
extern unsigned long sprite_steps,sprite_samples,sprite_outer,sprite_plain,sprite_blank,sprite_awards,sprite_score_changes,sprite_errors;
extern unsigned long sprite_active[3],sprite_still[3],sprite_same_pose[3],sprite_due[3],sprite_paid[3];
extern unsigned long sprite_lines[2][3][5],sprite_calls[2][3][5];
'''
    main=change(main,"static void source_game_service(void){",decl+"static void source_game_service(void){")
    main=change(main,"game_field_busy=1;while(gap--)", "if(sprite_detail && sprite_phase==1 && gap){sprite_due[sprite_actor]+=gap;++sprite_paid[sprite_actor];}\n    game_field_busy=1;while(gap--)")
    main=change(main,"static void light_config(void){","unsigned long sprite_clock(void){return line_clock();}\nstatic void light_config(void){")
    main=change(main,"score_meter=1;light_started=1;","sprite_arm();score_meter=1;light_started=1;")
    main=change(main,"light_audio_fault=bl_source_audio_faults();\n                break;","light_audio_fault=bl_source_audio_faults();\n                sprite_finish();break;")
    end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    fields="steps samples outer plain blank awards score_changes errors".split()
    report=[f'append(&p,"\\nsprite_{key}=");number(&p,sprite_{key});' for key in fields]
    for key in ("active","still","same_pose","due","paid"):
        report.append(f'append(&p,"\\nsprite_{key}=");for(k=0;k<3;k++){{if(k)append(&p,",");number(&p,sprite_{key}[k]);}}')
    for key in ("lines","calls"):
        for group in range(2):
            for role in range(3):
                report.append(f'append(&p,"\\nsprite_{key}_{group}_{role}=");for(k=0;k<5;k++){{if(k)append(&p,",");number(&p,sprite_{key}[{group}][{role}][k]);}}')
    main=change(main,end,"\n".join(report)+"\n"+end)
    write_build(mode,main,core,actor,parent)

def write_build(mode,main,core,actor,parent):
    out=WORK/mode;out.mkdir(parents=True,exist_ok=True)
    for name,s in (("main.c",main),("c64_rooms.c",core),("c64_actor_programs.h",actor),("source_audio.h",(parent/"source_audio.h").read_text())):
        (out/name).write_text(s)
    shared=ROOT/".tmp/op-score/rebuild/reference"
    compile_program(out,shared if (shared/"game.o").is_file() else None)

if __name__=="__main__":build(*sys.argv[1:])
