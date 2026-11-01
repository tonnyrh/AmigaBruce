"""Compare only the decimal conversion against the published score build."""
import argparse
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-decimal"
PARENT="d44ef0d62710c93ff9cc954ee72e1c3f4727ac09"
sys.path.insert(0,str(HERE.parent/"op-score-2026-10-31"))
from build_score import make as make_meter, change, compile_program

def original(file):
    return subprocess.check_output(["git","show",PARENT+":"+file],cwd=ROOT).decode().replace("\r\n","\n")

def updated(core):
    candidate=(HERE/"decimal.c").read_text()
    if candidate in core:return core
    start=core.index("static void source_score_decimal(void){")
    end=core.index("/* $2E89-",start)
    return core[:start]+candidate+core[end:]

def link(folder):
    shared=ROOT/".tmp/op-score/rebuild/reference"
    if not (shared/"game.o").is_file():shared=WORK/"candidate"
    compile_program(folder,shared if (shared/"game.o").is_file() else None)

def build(mode,profile):
    meter=ROOT/".tmp/op-score/candidate"
    if not (meter/"main.c").is_file():make_meter("candidate")
    main=(meter/"main.c").read_text()
    audio=(meter/"source_audio.h").read_text()
    core=original("core/c64_rooms.c")
    actor=original("core/c64_actor_programs.h")
    if mode=="candidate":core=updated(core)
    if profile:
        main=change(main,"static void light_config(void){",'''unsigned long decimal_clock(void){return line_clock();}
unsigned short decimal_step;extern unsigned long decimal_lines[2],decimal_calls[2];
static void light_config(void){''')
        main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)decimal_step=(UWORD)(step-light_start_step);\n            if(light_started && step!=light_steps_begin){")
        core=change(core,'#include "c64_actor_programs.h"', '''extern unsigned long decimal_clock(void);
extern unsigned short decimal_step;
unsigned long decimal_lines[2],decimal_calls[2];
static void measure_decimal(void){
    if(decimal_step==168 || decimal_step==207){
        unsigned short slot=(decimal_step==207);unsigned long start=decimal_clock();
        source_score_decimal();decimal_lines[slot]+=(decimal_clock()-start)&0xffffffUL;
        ++decimal_calls[slot];
    }else source_score_decimal();
}
#include "c64_actor_programs.h"''')
        actor=change(actor,"source_score_decimal();goto L330d;","measure_decimal();goto L330d;")
        end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,end,'''append(&p,"\\ndecimal_calls=");number(&p,decimal_calls[0]);append(&p,",");number(&p,decimal_calls[1]);
        append(&p,"\\ndecimal_lines=");number(&p,decimal_lines[0]);append(&p,",");number(&p,decimal_lines[1]);
        '''+end)
    out=WORK/(mode+("-profile" if profile else ""))
    out.mkdir(parents=True,exist_ok=True)
    for name,text in (("main.c",main),("source_audio.h",audio),("c64_rooms.c",core),("c64_actor_programs.h",actor)):
        (out/name).write_text(text)
    link(out)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=("reference","candidate"));parser.add_argument("--profile",action="store_true")
    args=parser.parse_args();build(args.mode,args.profile)
