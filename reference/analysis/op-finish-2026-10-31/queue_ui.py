"""Build a menu-driven isolated queue candidate and check the executing Copper list."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WORK=ROOT/".tmp/op-finish"
sys.path.insert(0,str(HERE.parent/"op1-contact-budget-2026-10-31"))
from build import change,compile_program

def main():
    f=WORK/"queue-ui";f.mkdir(exist_ok=True)
    for name in ("c64_rooms.c","c64_actor_programs.h"):
        (f/name).write_bytes((WORK/"queue-copy"/name).read_bytes())
    main=(ROOT/"amiga/main.c").read_text()
    main=change(main,"static void blank_game_display(void);","static void blank_game_display(void);\nstatic void wait_display_owner(void);")
    main=change(main,"static ULONG field_clock(void){",(HERE/"queue.h").read_text()+"\nstatic ULONG field_clock(void){")
    main=change(main,"        back^=1;\n","        wait_display_owner();back^=1;\n")
    main=change(main,"{UWORD line=present_frame(copper[back]);","{UWORD line=room_load_this_frame?present_frame(copper[back]):queue_game_frame(copper[back]);")
    for signature in ("static void blank_game_display(void){","static UBYTE pause_game(UBYTE *front){",
                      "static void menu_paint(const BlOptions *o,UBYTE debug,UBYTE game_over,int *front){",
                      "static void show_interlude(int *front,const BlSession *session){"):
        main=change(main,signature,signature+"\n    wait_display_owner();")
    (f/"main.c").write_text(main);(f/"source_audio.h").write_bytes((ROOT/"amiga/source_audio.h").read_bytes())
    compile_program(f,WORK/"queue-copy")
    audit=(ROOT/"tools/audit_native_animation_frame.py").read_text()
    audit=change(audit,"from winuae_ipc import command",f"import sys\nsys.path.insert(0,{str(ROOT/'tools')!r})\nfrom winuae_ipc import command")
    audit=change(audit,"ROOT=Path(__file__).resolve().parents[1]",f"ROOT=Path({str(ROOT)!r})")
    line=next(l for l in audit.splitlines() if "copper=int(re.search(" in l)
    audit=change(audit,line,'''  reg=cmd("DBG c")
  pc=int(re.search(r"COPPTR: \\$([0-9a-fA-F]+)",reg)[1],16)
  choices=struct.unpack(">II",read(hunks[3]+syms["copper"]-bss,8))
  copper=next(base for base in choices if base<=pc<base+1024)''')
    (f/"audit.py").write_text(audit)

if __name__=="__main__":main()
