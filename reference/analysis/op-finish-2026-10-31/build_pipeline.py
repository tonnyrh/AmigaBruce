"""Build the ordinary source path with OP0 counters and the actual final publisher."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-pipeline"
sys.path.insert(0,str(HERE.parent/"op-score-2026-10-31"))
import build_score

def main(mode):
    build_score.WORK=WORK
    if mode=="candidate":
        build_score.make("candidate")
        return
    base=WORK/"candidate";dest=WORK/mode;dest.mkdir(exist_ok=True)
    for name in ("c64_rooms.c","c64_actor_programs.h","source_audio.h"):
        (dest/name).write_bytes((base/name).read_bytes())
    main=(base/"main.c").read_text()
    if mode=="long":
        main=build_score.change(main,"if(light_started && step-light_start_step>=light_target){",
                                "if(light_started && ((field_clock()-light_fields)&0xffffffUL)>=6000){")
    elif mode=="tour":
        change=build_score.change
        main=change(main,"int main(void) {",(HERE/"tour.h").read_text()+"\nint main(void) {")
        main=change(main,"SysBase=*(struct ExecBase**)4;","SysBase=*(struct ExecBase**)4;op_stack_arm();")
        main=change(main,"static void source_game_load(long loading){","static void op_load(long);\nstatic void source_game_load(long loading){op_load(loading);")
        main=change(main,"static UWORD present_frame(UWORD *list){","static void op_present(UWORD,UWORD);\nstatic UWORD present_frame(UWORD *list){")
        main=change(main,"hw->cop1lc=(ULONG)list;\n    return line;","hw->cop1lc=(ULONG)list;op_present(line,list[1]);\n    return line;")
        main=change(main,"score_meter=1;light_started=1;","op_touring=1;score_meter=1;light_started=1;")
        main=change(main,"light_steps=step-light_start_step;","op_touring=0;light_steps=step-light_start_step;")
        main=change(main,"if(room_request<20){\n                    if(!BL_AUTOTEST",'''if(op_touring && op_index<sizeof(op_route) && step_for_tour()>=8+(ULONG)op_index*8 && !op_pending){
                    room_request=op_route[op_index];op_request();
                }
                if(room_request<20){
                    if(!BL_AUTOTEST''')
        end='append(&p,"\\nrestored_os=1\\nfinished=1\\n");'
        main=change(main,end,"op_report(&p);"+end)
    else:raise ValueError(mode)
    (dest/"main.c").write_text(main)
    build_score.compile_program(dest,base)

if __name__=="__main__":main(sys.argv[1])
