"""Apply only the measured display changes to the ordinary Amiga entry point."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("kage_pilot",HERE/"build.py")
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)

def prepare(mode):
    root,work=pilot.ROOT,pilot.WORK
    base=root/".tmp/op-pipeline/candidate"
    out=work/("retail-"+mode);out.mkdir(exist_ok=True)
    main=subprocess.check_output(["git","show","5ed53f6:amiga/main.c"],cwd=root,text=True,encoding="utf-8")
    after=(work/mode/"main.c").read_text()
    if mode.endswith("hud"):
        first=after.index("/* The eight 5x7");end=after.index("\n}",after.index("static void draw_score(",first))+2
        first_old=main.index("static void draw_score(");end_old=main.index("\n}",first_old)+2
        main=main[:first_old]+after[first:end]+main[end_old:]
    starts=("bl_c64_paint_animation_frame(buffers[back],SCENE_TOP);","draw_fighter(buffers[back],&world.enemy[n],&body,n,frame,back);",
        "draw_fighter(buffers[back],&world.player,&render_game,2,frame,back);","draw_lives(buffers[back],&world,&session);",
        "restore_source_cells(buffers[back],back);","draw_source_projectiles(buffers[back],back);","draw_health(buffers[back],n,health);")
    for stmt in starts:
        following=after[after.index(stmt)+len(stmt):].splitlines()[1]
        if following.strip()=="source_audio_service();":main=pilot.change(main,stmt,stmt+"\n"+following)
    if "sliced" in mode:main=pilot.change(main,"}x+=6;s++;}","}x+=6;s++;if(!(x&15))source_audio_service();}")
    audio=subprocess.check_output(["git","show","5ed53f6:amiga/source_audio.h"],cwd=root,text=True,encoding="utf-8")
    if "irq-" in mode:
        tuned=(work/mode/"source_audio.h").read_text()
        needle="static void source_audio_service(void){"
        audio=audio[:audio.index(needle)]+tuned[tuned.index(needle):]
        audio=pilot.change(audio,"static void source_audio_service(void);","static void source_audio_service(void);\nstatic UBYTE source_pending_vblank;")
    (out/"main.c").write_text(main);(out/"source_audio.h").write_text(audio)
    for name in ("c64_rooms.c","c64_actor_programs.h"):shutil.copyfile(work/mode/name,out/name)
    pilot.compile_program(out,base)
    tools=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    subprocess.run([tools/"exe2adf.exe","-i",out/"bruce_amiga.exe","-l","Bruce","-a",out/"bruce_amiga.adf"],check=True)

if __name__=="__main__":prepare(sys.argv[1])
