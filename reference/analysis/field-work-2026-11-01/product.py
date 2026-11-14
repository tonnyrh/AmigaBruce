"""Link a normal (unmetered) game with the same selected kernels as a trial."""
import shutil
import subprocess
import sys
from pathlib import Path
from build_field import ROOT,WORK,LAST,blits,change,compile_program,only_slot,early_queue
from clock_pair import apply
from input_field import sample_main

def build(family):
    stage=WORK/("retail-"+family);stage.mkdir(exist_ok=True)
    baseline=LAST/"retail-polled-hud"
    main=sample_main((baseline/"main.c").read_text())
    audio=(baseline/"source_audio.h").read_text()
    main=change(blits(main),"|DMAF_BLITHOG;",";")
    if family in ("clock","falls","native","candidate","early","release"):main,audio=apply(main,audio)
    if family in ("native","candidate","early","release"):main=only_slot(main)
    if family in ("early","release"):main=early_queue(main)
    for name,value in (("main.c",main),("source_audio.h",audio)):(stage/name).write_text(value)
    for name in ("c64_rooms.c","c64_actor_programs.h"):shutil.copyfile(WORK/family/name,stage/name)
    compile_program(stage,WORK/family)
    tools=sorted((Path.home()/".vscode/extensions").glob("bartmanabyss.amiga-debug-*/bin/win32"))[-1]
    subprocess.run([tools/"exe2adf.exe","-i",stage/"bruce_amiga.exe","-l","Bruce","-a",stage/"bruce_amiga.adf"],check=True)

if __name__=="__main__":build(sys.argv[1])
