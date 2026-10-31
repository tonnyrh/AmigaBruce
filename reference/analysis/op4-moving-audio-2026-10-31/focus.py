from probe import HERE,ROOT,WORK,sources,compile_program,change
def build():
    main,core=sources("reference");f=WORK/"focused";f.mkdir(exist_ok=True)
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    core=change(core,'#include "c64_actor_programs.h"',(HERE/"focused.h").read_text()+'\n#include "c64_actor_programs.h"')
    actor=change(actor,"actor_code(0x29c3);PERF_END(BL_PERF_COMBAT);","f_begin();actor_code(0x29c3);f_end();PERF_END(BL_PERF_COMBAT);")
    for at in (0x2bbf,0x2be3,0x2c07,0x2c33,0x2c3a,0x2c44):
        for pc,func in ((at,"f_score_start"),(at+3,"f_score_end")):
            s=f"L{pc:04x}:; /* ${pc:04X} */"
            actor=change(actor,s,s+"\n"+func+"();")
    # A non-award branch may also reach a continuation. Disarm on the first return.
    core=core.replace("static unsigned char f_active;","static unsigned char f_active,f_open;").replace("++f_calls;f_award=", "f_open=1;++f_calls;f_award=").replace("if(f_active){unsigned long cost=", "if(f_active && f_open){unsigned long cost=").replace("f_award_lines+=cost;","f_open=0;f_award_lines+=cost;")
    anchor="L2c51:; /* $2C51 */";actor=change(actor,anchor,anchor+"\nif(f_active)++f_loops;")
    anchor="source_score_decimal();goto L330d;"
    actor=change(actor,anchor,"if(f_active)f_decimal=focus_clock();source_score_decimal();if(f_active)f_decimal_lines+=(focus_clock()-f_decimal)&0xffffffUL;goto L330d;")
    audio=(ROOT/"amiga/source_audio.h").read_text()
    audio=change(audio,"source_clock_missed+=gap-1;","source_clock_missed+=gap-1;if(focus_live){if(focus_ne<16){focus_late[focus_ne][0]=focus_step;focus_late[focus_ne][1]=gap;focus_late[focus_ne][2]=source_audio_context;}++focus_ne;}")
    main=change(main,'#include "source_audio.h"','unsigned long focus_step,focus_ne,focus_late[16][3];unsigned char focus_live;extern unsigned long focus_count,focus_slow[8][9];\n#include "source_audio.h"')
    main=change(main,"static void light_config(void){","unsigned long focus_clock(void){return line_clock();}\nstatic void light_config(void){")
    main=change(main,"light_started=1;light_start_step=step;","focus_live=1;light_started=1;light_start_step=step;")
    main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)focus_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
    main=change(main,"light_steps=step-light_start_step;","focus_live=0;light_steps=step-light_start_step;")
    anchor='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
    main=change(main,anchor,'''file=Open((CONST_STRPTR)"DH1:focus.bin",MODE_NEWFILE);
        if(file && focus_count<=8 && focus_ne<=16){Write(file,&focus_count,4);Write(file,&focus_ne,4);
            Write(file,focus_slow,focus_count*36);Write(file,focus_late,focus_ne*12);}else result=20;if(file)Close(file);
        '''+anchor)
    (f/"main.c").write_text(main);(f/"c64_rooms.c").write_text(core);(f/"c64_actor_programs.h").write_text(actor);(f/"source_audio.h").write_text(audio)
    compile_program(f,ROOT/".tmp/op1-kage/reference")
if __name__=="__main__":build()
