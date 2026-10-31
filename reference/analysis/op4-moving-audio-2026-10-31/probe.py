"""Tag actual polls and time work between them in private OP0 builds."""
from pathlib import Path
import re,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op4-moving"
sys.path.insert(0,str(HERE.parent/"op1-kage-prefix-2026-10-31"))
from build_pilot import sources,compile_program,change

def wrap(s,call,scope):
    return change(s,call,"OP4_DO("+scope+","+call[:-1]+");")
def instrument(mode):
    main,core=sources("reference")
    actor=(ROOT/"core/c64_actor_programs.h").read_text()
    audio=(ROOT/"amiga/source_audio.h").read_text()
    main=change(main,'#include "source_audio.h"','#include "scope.h"\n#include "observer.h"\n#include "source_audio.h"')
    # Ground each tag in its enclosing statement. The two wait loops and
    # two blitter polls intentionally keep their original shared site.
    calls=[1,2,11,7,7,8,9,9,10,3,4,5,6]
    assert main.count("source_audio_service();")==len(calls)
    tags=iter(calls)
    main=re.sub(r"source_audio_service\(\);",lambda m:f"source_audio_service({next(tags)});",main)
    audio=audio.replace("source_audio_service(void)","source_audio_service(UWORD site)")
    audio=change(audio,"&0xffffffUL;if(!gap)return;","&0xffffffUL;op4_poll(now,gap,site,source_audio_context);if(!gap)return;")
    tick="source_audio_busy=1;source_audio_tick();source_audio_busy=0;"
    assert audio.count(tick)==2
    audio=audio.replace(tick,"source_audio_busy=1;OP4_DO(O_SOUND,source_audio_tick());source_audio_busy=0;")
    main=change(main,"while(gap--){bl_c64_field();source_audio_service(2);}","while(gap--){OP4_DO(O_FIELD,bl_c64_field());source_audio_service(2);}")
    main=change(main,"light_started=1;light_start_step=step;","op4_start();light_started=1;light_start_step=step;")
    main=change(main,"if(light_started && step!=light_steps_begin){","if(light_started)op4_step=step-light_start_step;\n            if(light_started && step!=light_steps_begin){")
    main=change(main,"light_steps=step-light_start_step;","op4_live=0;light_steps=step-light_start_step;")
    main=change(main,'append(&p,"\\nrestored_os=1\\nfinished=1\\n");','if(!op4_save())result=20;\n        append(&p,"\\nrestored_os=1\\nfinished=1\\n");')
    for scope,call in [
        ("O_STEP","bl_session_source_step(&session,&progress,&world,input,read_port((UBYTE)(session.current?1:0)));"),
        ("O_PREPARE","bl_c64_prepare_paint();"),("O_LOAD","load_room_background(&game,&progress,previous_room==progress.room);"),
        ("O_PATCH","room_paint_pending=(UBYTE)!update_lantern_background(&progress);"),
        ("O_RESTORE","restore_source_cells(buffers[back],back);"),
        ("O_ANIMATE","bl_c64_paint_animation_frame(buffers[back],SCENE_TOP);"),
        ("O_PROJECTILE","draw_source_projectiles(buffers[back],back);"),
        ("O_FIGHTER","draw_fighter(buffers[back],&world.enemy[n],&body,n,frame,back);"),
        ("O_FIGHTER","draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);"),
        ("O_HEALTH","draw_health(buffers[back],n,health);"),
        ("O_LIVES","draw_lives(buffers[back],&world,&session);"),
        ("O_SCORE","draw_score(buffers[back],&progress,options.debug);")]:
        main=wrap(main,call,scope)
    for scope,call in [("O_PREFIX","actor_code(0x15b8);"),("O_TAIL","actor_code(0x1703);"),("O_VIC","source_vic_latch();")]:
        core=wrap(core,call,scope)
    def origins(src, sequence):
        assert src.count("io_service();")==len(sequence)
        ids=iter(sequence)
        return re.sub(r"io_service\(\);",lambda _:f"{{unsigned short saved=op4_origin;op4_origin={next(ids)};io_service();op4_origin=saved;}}",src)
    core=origins(core,[1,2,3,4]);actor=origins(actor,[5,6])
    for perf,scope in [("CONTACT","O_CONTACT"),("OBJECTS","O_OBJECT"),("COMBAT","O_COMBAT"),("ACTORS","O_ACTOR"),("SPRITES","O_SPRITE")]:
        pattern=rf"(PERF_BEGIN\(BL_PERF_{perf}\);)(actor_code\(0x[0-9a-f]+\));(PERF_END\(BL_PERF_{perf}\);)"
        actor,n=re.subn(pattern,rf"\1OP4_DO({scope},\2);\3",actor);assert n>=1
    folder=WORK/mode;folder.mkdir(parents=True,exist_ok=True)
    (folder/"main.c").write_text(f"#define OP4_TIMED {int(mode=='timed')}\n"+main)
    (folder/"c64_rooms.c").write_text('#include "scope.h"\n'+core)
    (folder/"source_audio.h").write_text(audio);(folder/"c64_actor_programs.h").write_text(actor)
    for name in ("observer.h","scope.h"):shutil.copyfile(HERE/name,folder/name)
    compile_program(folder,ROOT/".tmp/op1-kage/reference")
def reference():
    import json,hashlib
    from build_pilot import build_mode
    parent=ROOT/".tmp/op1-kage/reference"
    if not (parent/"bruce_amiga.exe").is_file():build_mode("reference")
    bound=json.loads((HERE.parent/"op1-kage-prefix-2026-10-31/result.json").read_text())
    assert hashlib.sha256((parent/"bruce_amiga.exe").read_bytes()).hexdigest()==bound["builds"]["executables"]["moving-before"]
    out=WORK/"reference";out.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(parent/"bruce_amiga.exe",out/"bruce_amiga.exe")
if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="reference":reference()
    elif mode in ("sites","timed"):instrument(mode)
    else:raise ValueError(mode)
