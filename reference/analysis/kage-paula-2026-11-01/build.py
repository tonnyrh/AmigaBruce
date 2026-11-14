"""Private builds of the checkpoint's normal-scheduler OP0 route."""
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/kage-paula"
sys.path.insert(0,str(HERE.parent/"op1-contact-budget-2026-10-31"))
from build import change,compile_program

def insert(body,pc,statement):
    label=f"L{pc:04x}:; /* ${pc:04X} */"
    return change(body,label,label+"\n"+statement)

def make(mode):
    base=ROOT/".tmp/op-pipeline/candidate"
    main=(base/"main.c").read_text();audio=(base/"source_audio.h").read_text()
    core=(base/"c64_rooms.c").read_text();actor=(base/"c64_actor_programs.h").read_text()
    if mode=="long-gaps":
        core=change(core,'#include "c64_actor_programs.h"',(HERE/"kage.c").read_text()+'\n#include "c64_actor_programs.h"')
        actor=insert(actor,0x2bf9,"source_kage_award_pairs();")
        main=change(main,"if(light_started && step-light_start_step>=light_target){","if(light_started && ((field_clock()-light_fields)&0xffffffUL)>=6000){")
        main=change(main,'#include "source_audio.h"','''static ULONG gap_rows[36][5],gap_count,gap_step;
#include "source_audio.h"''')
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)gap_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
        audio=change(audio,"if(score_outputs){if(!gap)","if(score_outputs && gap!=1 && gap_count<36){ULONG *r=gap_rows[gap_count++];r[0]=gap_step;r[1]=gap;r[2]=source_audio_context;r[3]=stamp;r[4]=source_clock_last;}\n        if(score_outputs){if(!gap)")
        end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,end,'''for(k=0;k<gap_count;k++){UWORD j;append(&p,"\\ngap");number(&p,k);append(&p,"=");for(j=0;j<5;j++){if(j)append(&p,",");number(&p,gap_rows[k][j]);}}
        '''+end)
    elif mode=="trace":
        decl="""static ULONG ev[64][8],used,probe_origin,probe_step;
void probe_event(ULONG kind,ULONG arg,ULONG info,ULONG extra){
    if(score_meter && used<64){ULONG *p=ev[used++];
        p[0]=kind;p[1]=probe_step;p[2]=field_clock();p[3]=line_clock();
        p[4]=score_last;p[5]=arg;p[6]=info;p[7]=extra;}
}
"""
        main=change(main,'#include "source_audio.h"','void probe_event(ULONG,ULONG,ULONG,ULONG);\n#include "source_audio.h"')
        main=change(main,"static void light_config(void){",decl+"static void light_config(void){")
        main=change(main,"score_meter=1;light_started=1;","probe_origin=field_clock();score_meter=1;light_started=1;")
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)probe_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
        audio=change(audio,"if(score_outputs){if(!gap)", "if(score_outputs && gap!=1)probe_event(3,gap,source_audio_context,stamp);\n        if(score_outputs){if(!gap)")
        core=change(core,'#include "c64_actor_programs.h"', '''extern void probe_event(unsigned long,unsigned long,unsigned long,unsigned long);
static unsigned char probe_kage,probe_loops,probe_awards;
static unsigned long probe_score(void){return ((unsigned long)m[0x41]<<16)|((unsigned short)m[0x42]<<8)|m[0x43];}
#include "c64_actor_programs.h"''')
        actor=insert(actor,0x2bf9,"if(!probe_kage && x==2 && (m[0xbe]&0x90)==0x90 && ((m[0xd3]-5)&128)){probe_kage=1;probe_loops=probe_awards=0;probe_event(1,m[0xd3],probe_score(),m[0xbe]);}")
        actor=insert(actor,0x2c51,"if(probe_kage)++probe_loops;")
        actor=insert(actor,0x3175,"if(probe_kage)++probe_awards;")
        actor=insert(actor,0x2c1d,"if(probe_kage){probe_event(2,m[0xd3],probe_score(),((unsigned long)probe_loops<<8)|probe_awards);probe_kage=0;}")
        end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,end,'''append(&p,"\\ntrace_origin=");number(&p,probe_origin);
        for(k=0;k<used;k++){UWORD j;append(&p,"\\nevent");number(&p,k);append(&p,"=");for(j=0;j<8;j++){if(j)append(&p,",");number(&p,ev[k][j]);}}
        '''+end)
    elif mode in ("fold","long-fold","response","response-old","hud","long-hud","polled-hud","long-polled-hud","sliced-polled-hud","long-sliced-polled-hud","irq-polled-hud","long-irq-polled-hud","response-full","response-old-full") or (mode.startswith("response-") and mode.endswith("hud")):
        if not mode.startswith("response-old"):
            core=change(core,'#include "c64_actor_programs.h"',(HERE/"kage.c").read_text()+'\n#include "c64_actor_programs.h"')
            actor=insert(actor,0x2bf9,"source_kage_award_pairs();")
        if mode.endswith("hud"):
            first=main.index("static void draw_score(")
            end=main.index("\n}",first)+2
            main=main[:first]+(HERE/"hud.c").read_text()+main[end:]
        if "polled" in mode:
            for anchor in ("bl_c64_paint_animation_frame(buffers[back],SCENE_TOP);",
                           "draw_fighter(buffers[back],&world.enemy[n],&body,n,frame,back);",
                           "draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);"):
                main=change(main,anchor,anchor+"\n"+("                " if "&body" in anchor else "            ")+"source_audio_service();")
            main=change(main,"draw_lives(buffers[back],&world,&session);","draw_lives(buffers[back],&world,&session);\n                source_audio_service();")
        if "sliced" in mode:
            for anchor in ("restore_source_cells(buffers[back],back);","draw_source_projectiles(buffers[back],back);","draw_health(buffers[back],n,health);"):
                main=change(main,anchor,anchor+"\n"+("                    " if "draw_health" in anchor else "            ")+"source_audio_service();")
            main=change(main,"}x+=6;s++;}","}x+=6;s++;if(!(x&15))source_audio_service();}")
        if "irq-" in mode:
            audio=change(audio,"static void source_audio_service(void);","static void source_audio_service(void);\nstatic UBYTE source_pending_vblank;")
            audio=change(audio,"if(!source_audio_active || source_audio_busy)return;","""if(!source_audio_active || source_audio_busy)return;
    if(!source_pending_vblank){
        if(!(hw->intreqr&0x0020))return;
        hw->intreq=0x0020;source_pending_vblank=1;
    }""")
            audio=change(audio,"if(!gap)return;\n    source_clock_last","if(!gap)return;\n    source_pending_vblank=0;source_clock_last")
        if mode.startswith("response"):
            core=change(core,'#include "c64_actor_programs.h"','''extern unsigned char probe_pad,probe_hp,probe_active;
extern void probe_response(unsigned long,unsigned long,unsigned long,unsigned long);
static void probe_record(unsigned char pc){
    probe_response(pc,((unsigned long)m[0x9e]<<24)|((unsigned long)m[0xa1]<<16)|((unsigned short)m[0xa4]<<8)|m[0xbf],
        ((unsigned long)m[0xd3]<<24)|((unsigned long)m[0x41]<<16)|((unsigned short)m[0x42]<<8)|m[0x43],
        ((unsigned long)m[0x98]<<16)|((unsigned short)m[0xc2]<<8)|m[0xce]);
}
#include "c64_actor_programs.h"''')
            actor=insert(actor,0x2bf9,"if(!probe_active && probe_pad && x==2 && m[0xd3]==probe_hp && (m[0xbe]&0x90)==0x90){probe_active=1;actor_input=probe_pad;probe_record(1);}")
            actor=insert(actor,0x1c26,"if(probe_active==1){probe_record(2);probe_active=2;}")
            actor=insert(actor,0x17db,"if(probe_active==2 && !m[0x51])probe_record(4);")
            core=change(core,"PERF_BEGIN(BL_PERF_VIC);source_vic_latch();","if(probe_active)probe_record(3);\n    PERF_BEGIN(BL_PERF_VIC);source_vic_latch();")
            main=change(main,"static void light_config(void){",'''UBYTE probe_pad,probe_hp,probe_active;
static UBYTE probe_n,probe_latched,probe_moves;
static ULONG probe_rows[20][5];
void probe_response(ULONG kind,ULONG state,ULONG score,ULONG input){
    ULONG *r;
    if(kind==3 && probe_latched)return;
    if(kind==4 && probe_moves>=16)return;
    if(probe_n>=20)return;
    r=probe_rows[probe_n++];r[0]=kind;r[1]=line_clock();r[2]=state;r[3]=score;r[4]=input;
    if(kind==3)probe_latched=1;
    if(kind==4)++probe_moves;
}
static void light_config(void){''')
            main=change(main,"score_meter=1;light_started=1;","probe_hp=(light_route[3]&4)?3:2;probe_pad=(light_route[3]&1)?BL_LEFT:BL_RIGHT;score_meter=1;light_started=1;")
            main=change(main,"if(light_route[2]==2){","if(probe_active)return probe_pad;\n    if(light_route[2]==2){")
            end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
            if mode.endswith(("-full","hud")):
                main=main.replace("probe_rows[20][5]","probe_rows[65][5]").replace("probe_n>=20","probe_n>=65").replace("probe_moves>=16","probe_moves>=60")
            main=change(main,end,'''for(k=0;k<probe_n;k++){UWORD j;append(&p,"\\nresponse");number(&p,k);append(&p,"=");for(j=0;j<5;j++){if(j)append(&p,",");number(&p,probe_rows[k][j]);}}
        '''+end)
        if mode.startswith("long-"):
            main=change(main,"if(light_started && step-light_start_step>=light_target){","if(light_started && ((field_clock()-light_fields)&0xffffffUL)>=6000){")
    elif mode=="award":
        core=change(core,'#include "c64_actor_programs.h"',(HERE/"award.c").read_text()+'\n#include "c64_actor_programs.h"')
        actor=insert(actor,0x3175,"if(source_small_award()){sp+=2;actor_return=source_stack_return();goto actor_native_unwind;}")
    elif mode!="reference":raise ValueError(mode)
    dest=WORK/mode;dest.mkdir(parents=True,exist_ok=True)
    for name,value in (("main.c",main),("source_audio.h",audio),("c64_rooms.c",core),("c64_actor_programs.h",actor)):
        (dest/name).write_text(value)
    compile_program(dest,base)

if __name__=="__main__":make(sys.argv[1])
