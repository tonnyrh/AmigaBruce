"""Private normal-scheduler measurements for the OP acceptance gates."""
import shutil
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-finish"
sys.path.insert(0,str(HERE.parent/"op-sprite-cost-2026-10-31"))
from build_probe import inject,change,compile_program
from build_decimal import build as build_decimal, original, updated

def build(mode):
    p=ROOT/".tmp/op-decimal/candidate"
    if not (p/"main.c").exists():build_decimal("candidate",False)
    main=(p/"main.c").read_text()
    core=updated(original("core/c64_rooms.c"))
    actor=original("core/c64_actor_programs.h")
    current=(ROOT/"core/c64_rooms.c").read_text()
    if mode in ("tour-rows","tour-load"):
        start=current.index("static void copy_animation_line(")
        stop=current.index("static unsigned char animation_reusable(", start)
        core=change(core,"static unsigned char animation_reusable(",current[start:stop]+"static unsigned char animation_reusable(")
        start=core.index("        if(BL_ROOM_REUSE){\n            unsigned char *dest=animation_cache")
        stop=core.index("        }else for(phase=0;",start)
        core=core[:start]+"        if(BL_ROOM_REUSE){\n            build_animation_rectangle(rect,left,right);\n"+core[stop:]
    if mode in ("final","long-final","tour-final","irq","irq-copy","irq-active","guard","queue","queue-copy","neutral"):
        core=current;actor=(ROOT/"core/c64_actor_programs.h").read_text()
        game=(ROOT/"amiga/main.c").read_text()
        for beg,stop in (("static void draw_room(","static void load_room_background("),
                         ("static void menu_paint(","static ")):
            at=main.index(beg);end=main.index(stop,at+len(beg))
            src=game.index(beg);finish=game.index(stop,src+len(beg))
            main=main[:at]+game[game.index("/* D-only zero") if "draw_room" in beg else src:finish]+main[end:]
    audio=(p/"source_audio.h").read_text()
    end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    if mode in ("actor","outer"):
        detail=mode=="actor"
        main=change(main,"static void light_config(void){",'''unsigned char actor_meter_on;
unsigned long actor_meter_clock(void){return line_clock();}
extern unsigned long actor_measure[11],actor_hits[11],actor_checks,actor_total,actor_calibration;
extern void actor_calibrate(void);
static void light_config(void){''')
        main=change(main,"score_meter=1;light_started=1;","actor_meter_on=1;score_meter=1;light_started=1;")
        main=change(main,"light_audio_fault=bl_source_audio_faults();\n                break;","light_audio_fault=bl_source_audio_faults();\n                actor_meter_on=0;actor_calibrate();break;")
        c='''extern unsigned char actor_meter_on;extern unsigned long actor_meter_clock(void);
unsigned long actor_measure[11],actor_hits[11],actor_checks,actor_total,actor_calibration;
static unsigned long op_stamp,op_previous;static unsigned char op_phase,op_role,op_sample;
static void actor_mark(unsigned char phase){unsigned long now=actor_meter_clock();
    actor_measure[op_phase]+=(now-op_previous)&0xffffffUL;op_previous=now;op_phase=phase;++actor_hits[phase];}
void actor_calibrate(void){unsigned short i;for(i=0;i<240;i++){unsigned long stamp=actor_meter_clock();actor_calibration+=(actor_meter_clock()-stamp)&0xffffffUL;}}
'''
        core=change(core,'#include "c64_actor_programs.h"',c+'\n#include "c64_actor_programs.h"')
        a="PERF_BEGIN(BL_PERF_ACTORS);actor_code(0x179e);PERF_END(BL_PERF_ACTORS);"
        anchor="m[0x100 + sp--]=0x1c;m[0x100 + sp--]=0x2b;"+a
        begin="if(actor_meter_on){op_sample=1;op_phase=0;op_stamp=op_previous=actor_meter_clock();}"
        finish="if(op_sample){unsigned long stamp=actor_meter_clock();actor_total+=(stamp-op_stamp)&0xffffffUL;actor_measure[op_phase]+=(stamp-op_previous)&0xffffffUL;++actor_checks;op_sample=0;}"
        actor=change(actor,anchor,anchor.replace(a,begin+a+finish))
        if detail:
            for pc,what in ((0x179e,"actor_mark(1);"),(0x17a1,"actor_mark(0);"),
                            (0x17d8,"op_role=x;actor_mark(2+op_role);"),(0x17db,"actor_mark(5+op_role);"),
                            (0x17de,"if(op_phase!=0)actor_mark(0);")):
                actor=inject(actor,pc,"if(op_sample){"+what+"}")
        main=change(main,end,'''append(&p,"\\nactor_calls=");number(&p,actor_checks);append(&p,"\\nactor_total=");number(&p,actor_total);
append(&p,"\\nclock_pairs=");number(&p,actor_calibration);
append(&p,"\\nactor_lines=");for(k=0;k<8;k++){if(k)append(&p,",");number(&p,actor_measure[k]);}
append(&p,"\\nactor_hits=");for(k=0;k<8;k++){if(k)append(&p,",");number(&p,actor_hits[k]);}
'''+end)
    elif mode in ("history","field","combined","counts","component","kernel","publisher"):
        if mode=="publisher":
            publish=(HERE.parent/"sprite-publish-2026-10-30/candidate/publish.h").read_text()
            core=change(core,'#include "c64_actor_programs.h"',publish+'\n#include "c64_actor_programs.h"')
            actor=inject(actor,0x25e2,"if(!d && !m[0x277e]){source_sprite_publish();actor_return=source_stack_return();goto actor_native_unwind;}")
        if mode in ("component","kernel","publisher"):
            core=change(core,'#include "c64_actor_programs.h"',(HERE/"component.c").read_text()+'\n#include "c64_actor_programs.h"')
            actor=inject(actor,0x2591,"if(source_image_component(0))goto L25ae;")
            actor=inject(actor,0x25b9,"if(source_image_component(1))goto L25d7;")
        if mode in ("history","combined","kernel","publisher"):
            core=change(core,'#include "c64_actor_programs.h"',(HERE/"history.c").read_text()+'\n#include "c64_actor_programs.h"')
            actor=inject(actor,0x1c79,"if(!d && x<3){source_shift_history();goto L1c8f;}")
        if mode in ("field","combined","kernel","publisher"):
            core=change(core,'#include "c64_actor_programs.h"',(HERE/"field.c").read_text()+'\n#include "c64_actor_programs.h"')
            actor=inject(actor,0x15bd,"if(m[0x7f]!=255 || m[0x82]!=127){source_field_timers();goto L169d;}")
        if mode=="counts":
            core=change(core,'#include "c64_actor_programs.h"','unsigned long history_calls[3];extern unsigned char history_enabled;\n#include "c64_actor_programs.h"')
            main=change(main,"static void light_config(void){","unsigned char history_enabled;extern unsigned long history_calls[3];\nstatic void light_config(void){")
            main=change(main,"score_meter=1;light_started=1;","history_enabled=1;score_meter=1;light_started=1;")
            actor=inject(actor,0x1c79,"if(history_enabled && !d && x<3)++history_calls[x];")
            main=change(main,end,'append(&p,"\\nhistory_calls=");for(k=0;k<3;k++){if(k)append(&p,",");number(&p,history_calls[k]);}\n'+end)
    elif mode in ("tour","tour-dma","tour-rows","tour-load","tour-final"):
        if mode=="tour-load":
            core=change(core,'#include "c64_actor_programs.h"',(HERE/"room_run.c").read_text()+'\n#include "c64_actor_programs.h"')
            actor=inject(actor,0x0ad7,"if(source_room_token())goto L0ad7;")
        if mode in ("tour-dma","tour-rows","tour-load"):
            main=change(main,"for(i=0;i<BITMAP_BYTES;i++)background[i]=0;",(HERE/"clear.c").read_text().strip())
        main=change(main,"int main(void) {",(HERE/"tour.h").read_text()+"\nint main(void) {")
        main=change(main,"SysBase=*(struct ExecBase**)4;","SysBase=*(struct ExecBase**)4;op_stack_arm();")
        main=change(main,"static void source_game_load(long loading){","static void op_load(long);\nstatic void source_game_load(long loading){\n    op_load(loading);")
        main=change(main,"hw->cop1lc=(ULONG)list;\n    return line;","hw->cop1lc=(ULONG)list;op_present(line,list[1]);\n    return line;")
        main=change(main,"static UWORD present_frame(UWORD *list){","static void op_present(UWORD,UWORD);\nstatic UWORD present_frame(UWORD *list){")
        main=change(main,"score_meter=1;light_started=1;","op_touring=1;score_meter=1;light_started=1;")
        main=change(main,"light_steps=step-light_start_step;","op_touring=0;light_steps=step-light_start_step;")
        main=change(main,"if(room_request<20){\n                    if(!BL_AUTOTEST",'''if(op_touring && op_index<sizeof(op_route) && step_for_tour()>=8+(ULONG)op_index*8 && !op_pending){
                    room_request=op_route[op_index];op_request();
                }
                if(room_request<20){
                    if(!BL_AUTOTEST''')
        main=change(main,end,'''op_report(&p);
'''+end)
        if mode=="tour-final":
            # Take the detailed phase timings only in this separate run.
            main=change(main,"static void op_load(long);","static void op_phase_mark(unsigned short);\nstatic void op_load(long);")
            main=change(main,"static void op_request(void){",'''static ULONG op_stamps[8],op_details[sizeof(op_route)][9];
static void op_phase_mark(unsigned short n){if(op_pending)op_stamps[n]=line_clock();}
static void op_request(void){''')
            core=change(core,'static void source_actor_loading_end(void){','extern void op_phase_bridge(unsigned short);\nstatic void source_actor_loading_end(void){')
            core=change(core,'prepare_palette();index_screen();paint_count=paint_cursor=0;',
                        'op_phase_bridge(0);prepare_palette();op_phase_bridge(1);index_screen();op_phase_bridge(2);paint_count=paint_cursor=0;')
            # long arguments are shared across mshort and the ordinary ABI.
            core=core.replace('op_phase_bridge(unsigned short)','op_phase_bridge(long)')
            main=change(main,"static void op_request(void){","void op_phase_bridge(long n){op_phase_mark((unsigned short)n);}\nstatic void op_request(void){")
            for i,target in enumerate(("clear_bitmap(background);","bl_c64_paint_room(background,SCENE_TOP);wait_blitter();",
                                       "bl_c64_clear_dirty();\n    (void)bl_c64_build_animation_cache(tile_dma,TILE_DMA_BYTES);",
                                       'text(background,240,248,"P PAUSE",12);'),3):
                main=change(main,target,("op_phase_mark(3);"+target+"op_phase_mark(4);") if i==3 else target+f"op_phase_mark({i+1});")
            # After publication the next Copper restart fetches this buffer.
            # DIW starts at $2c. The first playfield cell is row 3.
            main=change(main,"row[4]=line;",'''row[4]=line;
    {ULONG prev=op_beg;UWORD i;
     for(i=0;i<8;i++){op_details[op_index-1][i]=(op_stamps[i]-prev)&0xffffffUL;prev=op_stamps[i];
                       if(i==2)prev=op_end;}
     while(raster()>=300)source_audio_service();
     while(raster()<0x2c+SCENE_TOP+24)source_audio_service();
     op_details[op_index-1][8]=(line_clock()-op_start)&0xffffffUL;}''')
            main=change(main,"for(j=0;j<5;j++){append(p,\",\");number(p,op_events[i][j]);}",
                        'for(j=0;j<5;j++){append(p,",");number(p,op_events[i][j]);}\n'
                        '        append(p,"\\nphases_");number(p,i);append(p,"=");for(j=0;j<9;j++){if(j)append(p,",");number(p,op_details[i][j]);}')
    elif mode in ("irq","irq-copy","irq-active","guard","queue","queue-copy","neutral"):
        anchor="    actor_irq_stop=0;actor_code(0x15b8);"
        stop="    actor_irq_stop=0;actor_code(0x1703);actor_irq_stop=0;"
        pos=core.index(anchor);last=core.index(stop,pos)+len(stop)
        fast=(HERE/"irq.c").read_text()
        if mode=="irq-active":fast=fast.replace("if(m[2]","if(((m[0x96]|m[0x97])&1) && m[2]")
        core=core[:pos]+fast+"else{\n"+core[pos:last]+"\n    }"+core[last:]
        core=change(core,"static void source_actor_field(void){",(HERE.parent/"sprite-publish-2026-10-30/candidate/publish.h").read_text()+"\nstatic void source_actor_field(void){")
        if mode=="neutral":
            marker="static unsigned char source_object_row(void){"
            core=change(core,marker,(HERE/"neutral.c").read_text()+"\n"+marker)
            anchor="x=m[0x51];NZ(x);y=m[(unsigned char)(0xe6+x)];NZ(y);a=2;m[0x4c]=a;NZ(a);"
            core=change(core,anchor,anchor+"\n    if(source_neutral_row())return 1;")
        if mode in ("queue","queue-copy","neutral"):
            main=change(main,"static void blank_game_display(void);","static void blank_game_display(void);\nstatic void wait_display_owner(void);")
            main=change(main,"static ULONG field_clock(void){",(HERE/"queue.h").read_text()+"\nstatic ULONG field_clock(void){")
            main=change(main,"        back^=1;\n","        wait_display_owner();back^=1;\n")
            main=change(main,"{UWORD line=present_frame(copper[back]);","{UWORD line=room_load_this_frame?present_frame(copper[back]):queue_game_frame(copper[back]);")
            for label in ("static void blank_game_display(void){","static UBYTE pause_game(UBYTE *front){",
                          "static void menu_paint(const BlOptions *o,UBYTE debug,UBYTE game_over,int *front){",
                          "static void show_interlude(int *front,const BlSession *session){"):
                main=change(main,label,label+"\n    wait_display_owner();")
            main=change(main,end,'append(&p,"\\nqueued=");number(&p,op_queued);append(&p,"\\nowner_waits=");number(&p,op_owner_waits);\n'+end)
        if mode=="guard":
            for a,b in (("loaded=255,transition_pending;","loaded=255;"),("revision,source_fault;","revision;"),
                        ("actor_life_pending,actor_reset_pending,actor_preparing","actor_life_pending,actor_preparing"),
                        ("char actor_gameover_pending,actor_legacy_load","char actor_legacy_load"),
                        ("char actor_irq_stop,actor_world_enabled","char actor_world_enabled"),("static unsigned char actor_delay_pending;","")):
                core=change(core,a,b)
            flags=["transition_pending","actor_delay_pending","actor_gameover_pending","actor_reset_pending","actor_irq_stop"]
            decl="static union { struct { unsigned char "+",".join(flags)+",pad;unsigned short source_fault;} f;unsigned long word[2];} native_control;\n"
            decl+="typedef char ControlSize[sizeof(native_control)==8 ? 1 : -1];\n"
            decl+="".join(f"#define {name} (native_control.f.{name})\n" for name in [*flags,"source_fault"])
            core=change(core,"static unsigned char m[65536]",decl+"static unsigned char m[65536]")
            condition=" || ".join([*flags,"source_fault"])
            assert actor.count(condition)==8
            actor=actor.replace(condition,"(native_control.word[0] || native_control.word[1])")
    elif mode in ("long","long-final"):
        main=change(main,"if(light_started && step-light_start_step>=light_target){","if(light_started && ((field_clock()-light_fields)&0xffffffUL)>=6000){")
    elif mode not in ("reference","final"):raise ValueError(mode)
    f=WORK/mode;f.mkdir(parents=True,exist_ok=True)
    for name,s in (("main.c",main),("c64_rooms.c",core),("c64_actor_programs.h",actor),("source_audio.h",audio)):
        (f/name).write_text(s)
    shared=ROOT/".tmp/op-score/rebuild/reference"
    if mode in ("irq-copy","queue-copy","neutral"):
        for obj in shared.glob("*.o"):
            if obj.name not in ("sprite_copy.o","main.o","c64_rooms.o"):shutil.copyfile(obj,f/obj.name)
        gcc=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32/opt/bin/m68k-amiga-elf-gcc.exe"))[-1]
        subprocess.run([gcc,"-m68000","-c",HERE.parent/"sprite-disjoint-2026-10-30/candidate/sprite_copy.s","-o",f/"sprite_copy.o"],check=True)
        shared=f
    compile_program(f,shared)

if __name__=="__main__":
    build(sys.argv[1])
